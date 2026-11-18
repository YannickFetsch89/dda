// Liefert das Foto eines Ortes über den eigenen Server aus (Bild-Proxy, siehe lib/bild-proxy.ts).
//
// - Eigenes Bild (orte.bild_url): wird geholt, auf der Platte gecached und durchgereicht.
//   Liegt es in web/public/ort-bilder/… (lib/orte.ts lokalesBild), verweist die Route nur per 308 dorthin.
// - Google-Foto (orte.extras.google_foto.name): Die Bildadresse wird serverseitig bei der Places API
//   abgefragt (skipHttpRedirect → photoUri, ohne Key) und das Bild durchgereicht. Der Browser spricht
//   dabei nie mit Google, der API-Key verlässt nie den Server. Google-Bilder werden nicht dauerhaft
//   gespeichert (Nutzungsbedingungen); nur die Bildadresse wird gecached, weil jeder Abruf kostet:
//     Treffer 30 Tage · dauerhaft kein Foto 1 Tag · vorübergehender Fehler 5 Minuten
//   Lehnt Google eine gecachte Bildadresse ab (abgelaufen), wird sie verworfen (max. 1×/Stunde je Ort).
import { cacheLife, cacheTag, revalidateTag } from "next/cache";
import type { NextRequest } from "next/server";
import { bildAntwort, bildHolen } from "@/lib/bild-proxy";
import { clubLaden } from "@/lib/clubs-daten";
import { istSichtbarerClub } from "@/lib/clubs";
import { lokalesBild, ortLaden, slugDekodieren } from "@/lib/orte";
import { spielplatzLaden } from "@/lib/spielplaetze-daten";
import { weihnachtsmarktLaden } from "@/lib/weihnachtsmaerkte-daten";

const FOTO_BREITE = 1200;
// Nur echte Ressourcennamen zulassen ("places/<id>/photos/<id>"), nichts anderes an Google weiterreichen
const FOTO_NAME = /^places\/[A-Za-z0-9_-]+\/photos\/[A-Za-z0-9_-]+$/;
const TAG = 24 * 3600;

type Ergebnis = { adresse: string | null; voruebergehend?: boolean };

const fotoTag = (slug: string) => `ort-foto:${slug}`.slice(0, 256);
const zuletztVerworfen = new Map<string, number>();

/** Abgelaufene Google-Bildadresse verwerfen – höchstens einmal pro Stunde je Ort (jeder Neuabruf kostet). */
function adresseVerwerfen(slug: string): void {
  const jetzt = Date.now();
  if (jetzt - (zuletztVerworfen.get(slug) ?? 0) < 3600_000) return;
  zuletztVerworfen.set(slug, jetzt);
  revalidateTag(fotoTag(slug), { expire: 0 });
}

/** Nur Bildadressen von Google ohne Key verwenden. */
function gueltigeGoogleAdresse(wert: unknown): string | null {
  if (typeof wert !== "string") return null;
  try {
    const url = new URL(wert);
    const googleHost = url.hostname === "googleusercontent.com" || url.hostname.endsWith(".googleusercontent.com");
    return url.protocol === "https:" && googleHost && !/[?&]key=/i.test(url.search) ? wert : null;
  } catch {
    return null;
  }
}

async function googleFotoAdresse(name: string, slug: string): Promise<Ergebnis> {
  const key = process.env.GOOGLE_PLACES_API_KEY;
  if (!key) {
    console.warn("GOOGLE_PLACES_API_KEY fehlt in .env.local – Ort-Fotos können nicht geladen werden");
    return { adresse: null, voruebergehend: true };
  }
  try {
    const antwort = await fetch(
      `https://places.googleapis.com/v1/${name}/media?maxWidthPx=${FOTO_BREITE}&skipHttpRedirect=true`,
      { headers: { "X-Goog-Api-Key": key } },
    );
    if (!antwort.ok) {
      // 400/403/404: Foto-Name abgelaufen o.ä. → mit "google_places --aktualisieren" erneuern
      console.warn(`Ort-Foto für '${slug}' nicht geladen: HTTP ${antwort.status}`);
      return { adresse: null, voruebergehend: antwort.status === 429 || antwort.status >= 500 };
    }
    const adresse = gueltigeGoogleAdresse(((await antwort.json()) as { photoUri?: unknown }).photoUri);
    return { adresse, voruebergehend: false };
  } catch (err) {
    console.warn(`Ort-Foto für '${slug}' nicht geladen: ${err instanceof Error ? err.message : err}`);
    return { adresse: null, voruebergehend: true };
  }
}

/** Ort zum Slug, wie die Website ihn zeigt (Daten aus dem gecachten Pool – kein Google-Abruf). */
async function fotoOrt(slug: string) {
  // Club-Hub: Orte mit auch_club (z. B. Konvex) sind im Club-Hub sichtbar, auch wenn ihr Score im Haupt-Hub < 7 ist.
  // Club-Zeilen (typ = club) nur, wenn sie im Hub sichtbar sind (Freigabe!) – ortLaden kennt die Freigabe nicht.
  const geladen = await ortLaden(slug);
  // Spielplätze haben keinen qualitaets_score: eigener Zweig, nur aktive (abgeschaltete → 404, keine Weiterleitung)
  // Weihnachtsmärkte ebenso ohne Score: eigener Zweig, nur aktive
  return (geladen && (geladen.typ !== "club" || istSichtbarerClub(geladen)) ? geladen : null) ?? (await clubLaden(slug))
    ?? (await spielplatzLaden(slug)) ?? (await weihnachtsmarktLaden(slug));
}

/** Welches Foto gilt gerade? Eigenes Bild, sonst gültiger Google-Fotoname, sonst keins. */
function fotoKennung(ort: Awaited<ReturnType<typeof fotoOrt>>): { eigenes: string | null; google: string | null } {
  if (ort?.bild_url && !ort.bild_url.includes("key=")) return { eigenes: ort.bild_url, google: null };
  const foto = ort?.extras?.google_foto as { name?: unknown } | undefined;
  return { eigenes: null, google: typeof foto?.name === "string" && FOTO_NAME.test(foto.name) ? foto.name : null };
}

/**
 * Bildquelle eines Ortes: { adresse, google } – gecached nach Ergebnis (siehe Kopfkommentar).
 * Schlüssel ist das gerade gespeicherte Foto selbst (Google-Fotoname bzw. eigene Bildadresse): Ein getauschtes Foto
 * bekommt sofort einen eigenen Eintrag statt bis zu 30 Tage die gemerkte Adresse des alten. ?v= aus der URL zählt dafür
 * nicht – so kann niemand von außen neue Einträge und damit Google-Abrufe erzwingen (Cursor-Prüfung 16.11.2026).
 */
async function bildQuelle(slug: string, eigenes: string | null, google: string | null, hoechstens30Tage = false): Promise<{ adresse: string | null; google: boolean }> {
  "use cache";
  cacheTag(fotoTag(slug));
  if (eigenes) {
    cacheLife({ stale: 3600, revalidate: TAG, expire: 7 * TAG });
    return { adresse: eigenes, google: false };
  }
  const ergebnis: Ergebnis = google ? await googleFotoAdresse(google, slug) : { adresse: null };
  // Genau ein cacheLife-Aufruf je Durchlauf, abhängig vom Ergebnis
  // Weihnachtsmärkte: gemerkte Google-Bildadresse höchstens 30 Tage (Plan Weihnachtsmärkte E12); übrige Hubs: Folgepunkt
  if (ergebnis.adresse) cacheLife(hoechstens30Tage ? { stale: TAG, revalidate: 20 * TAG, expire: 30 * TAG } : { stale: TAG, revalidate: 30 * TAG, expire: 45 * TAG });
  else if (ergebnis.voruebergehend) cacheLife({ stale: 60, revalidate: 300, expire: 600 });
  else cacheLife({ stale: 3600, revalidate: TAG, expire: 2 * TAG });
  return { adresse: ergebnis.adresse, google: true };
}

export async function GET(_req: NextRequest, ctx: RouteContext<"/ort-foto/[slug]">) {
  const slug = slugDekodieren((await ctx.params).slug);
  const ort = slug ? await fotoOrt(slug) : null;
  // Bild aus web/public (z. B. vom Veranstalter): direkt dorthin verweisen, nicht durch den Proxy holen
  const lokal = lokalesBild(ort?.bild_url);
  if (lokal) return new Response(null, { status: 308, headers: { Location: lokal, "Cache-Control": `public, max-age=${TAG}` } });
  const kennung = slug ? fotoKennung(ort) : null;
  // Ohne Foto gar nicht erst in den Cache bzw. zu Google
  const quelle = slug && kennung && (kennung.eigenes || kennung.google)
    ? await bildQuelle(slug, kennung.eigenes, kennung.google, ort?.typ === "weihnachtsmarkt")
    : null;
  // Google-Fotos nur durchreichen (nicht auf der Platte speichern), eigene Bilder cachen
  if (!slug || !quelle?.adresse) return bildAntwort(null, TAG);
  const { bild, status } = await bildHolen(quelle.adresse, !quelle.google);
  // 400/403/404/410 von Google = Bildadresse abgelaufen oder ungültig → beim nächsten Aufruf neu abfragen
  if (!bild && quelle.google && status !== undefined && [400, 403, 404, 410].includes(status)) adresseVerwerfen(slug);
  // Google-Fotos: nur der Browser darf cachen (keine geteilten Caches)
  return bildAntwort(bild, TAG, quelle.google);
}
