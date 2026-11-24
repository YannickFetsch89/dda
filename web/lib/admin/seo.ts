// Admin-Bereich – SEO-Aufräumen (Plan Admin-Dashboard 4.10, Stufe 5b; Umzug aus dashboard/seo_aufraeumen.py,
// unverändert). Events, deren letzter Tag mehr als 12 Monate zurückliegt; je Event behalten, 301 (Reihe, Ortssuche,
// Kategorie – nie die Startseite) oder 410. Gespeichert in event_seo_entscheidungen, ausgeliefert von web/proxy.ts.
// Rein, getestet in web/tests/admin-seo.test.ts.
import { plusTage } from "../datum";

export const ABGELAUFEN_SEIT_TAGE = 365;

export const SEO_AKTIONEN = {
  behalten: "Behalten (Seite bleibt, HTTP 200)",
  reihe: "301 → Reihenseite (nur Events mit Reihe)",
  ort: "301 → Ortssuche (/entdecken?q=<Ort>)",
  kategorie: "301 → Kategorie (/entdecken?kategorie=…)",
  gone: "410 Gone",
} as const;
export type SeoArt = keyof typeof SEO_AKTIONEN;

export interface SeoEvent {
  id: string;
  slug: string;
  titel: string;
  datum: string;
  datum_bis: string | null;
  ort: string | null;
  kategorie: string | null;
  reihe: { slug?: string } | { slug?: string }[] | null;
}

/** DB-Kategorie → Website-Slug (family → familie) */
export function webKategorie(k: string | null | undefined): string {
  const w = (k ?? "sonstiges").trim().toLowerCase();
  return w === "family" ? "familie" : w;
}

export function reiheSlug(e: SeoEvent): string | null {
  const r = Array.isArray(e.reihe) ? e.reihe[0] : e.reihe;
  return r && typeof r.slug === "string" ? r.slug : null;
}

export function eventPfadSeo(e: SeoEvent): string {
  return `/event/${encodeURIComponent(webKategorie(e.kategorie))}/${encodeURIComponent(e.slug)}`;
}

/** Internes Ziel der Weiterleitung oder null (z. B. keine Reihe) – wie ziel_fuer im Dashboard */
export function zielFuer(e: SeoEvent, art: SeoArt): string | null {
  if (art === "reihe") {
    const s = reiheSlug(e);
    return s ? `/reihe/${encodeURIComponent(s)}` : null;
  }
  if (art === "ort") {
    const ort = (e.ort ?? "").trim();
    return ort ? `/entdecken?q=${encodeURIComponent(ort)}&datum=alle` : null;
  }
  if (art === "kategorie") return `/entdecken?kategorie=${encodeURIComponent(webKategorie(e.kategorie))}&datum=alle`;
  return null;
}

/** Zeilen für event_seo_entscheidungen und übersprungene Events (ohne passendes Ziel) */
export function entscheidungenBauen(events: SeoEvent[], art: SeoArt, adminId: string | null, jetzt: string): { zeilen: Record<string, unknown>[]; uebersprungen: SeoEvent[] } {
  const zeilen: Record<string, unknown>[] = [];
  const uebersprungen: SeoEvent[] = [];
  for (const e of events) {
    let aktion: string;
    let ziel: string | null = null;
    if (art === "behalten" || art === "gone") aktion = art;
    else {
      aktion = "weiterleiten";
      ziel = zielFuer(e, art);
      if (!ziel) {
        uebersprungen.push(e);
        continue;
      }
    }
    zeilen.push({ event_id: e.id, slug: e.slug, aktion, ziel, entschieden_am: jetzt, entschieden_von: adminId });
  }
  return { zeilen, uebersprungen };
}

/** PostgREST-Filter: letzter Tag (datum_bis, sonst datum) liegt mehr als 12 Monate zurück */
export function abgelaufenFilter(heute: string): string {
  const grenze = plusTage(heute, -ABGELAUFEN_SEIT_TAGE);
  return `datum_bis.lt.${grenze},and(datum_bis.is.null,datum.lt.${grenze})`;
}

/** CSV-Feld mit Schutz vor Formeln (Titel/Orte kommen von Scrapern) */
export function csvFeld(w: unknown): string {
  const s = String(w ?? "");
  const sicher = /^[=+\-@\t\r]/.test(s) ? `'${s}` : s;
  return /[;"\n]/.test(sicher) ? `"${sicher.replace(/"/g, '""')}"` : sicher;
}
