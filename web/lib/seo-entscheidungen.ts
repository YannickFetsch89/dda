// SEO-Entscheidungen für lange abgelaufene Events (Tabelle event_seo_entscheidungen, gepflegt im
// Dashboard-Tab „SEO-Aufräumen“). Standard ist: Seite bleibt online. Nur ausdrücklich entschiedene
// Events bekommen eine 301-Weiterleitung oder 410 Gone (siehe proxy.ts).

export type SeoAktion = { aktion: "weiterleiten"; ziel: string } | { aktion: "gone" };
export type SeoTabelle = Map<string, SeoAktion>;

/** Slug aus einem Eventpfad /event/<kategorie>/<slug> (sonst null). */
export function eventSlugAusPfad(pfad: string): string | null {
  const m = pfad.match(/^\/event\/[^/]+\/([^/]+)\/?$/);
  if (!m) return null;
  try {
    return decodeURIComponent(m[1]);
  } catch {
    return null;
  }
}

/**
 * Nur interne Ziele, nie die Startseite und nie eine fremde Domain. Browser und URL-Parser entfernen
 * Tab/Zeilenumbruch und lesen „\“ wie „/“ – „/\t/evil.com“ würde so zu „//evil.com“. Deshalb sind
 * Steuerzeichen, Leerraum und Backslash im Ziel ganz verboten. Im Pfad (vor „?“) außerdem „//“,
 * Punkt-Segmente („/.“, „/..“) und kodierte Punkte/Schrägstriche – „/.//evil.com“ löst sich sonst
 * zu „//evil.com“ auf. Gleiche Regel als CHECK in der DB (database/event_seo_ziel_2026-11-05.sql).
 */
export function zielErlaubt(ziel: string): boolean {
  const pfad = ziel.split("?")[0];
  return (
    /^\/[^/]/.test(ziel) &&
    !/[\u0000- \u007f\\]/.test(ziel) &&
    !/\/\/|\/\.|%2e|%2f|%5c/i.test(pfad)
  );
}

/** Letzte Sicherung: das aufgelöste Ziel muss auf derselben Domain bleiben und darf nicht mit „//“ beginnen. */
export function zielAufloesen(ziel: string, basis: string): URL | null {
  if (!zielErlaubt(ziel)) return null;
  try {
    const url = new URL(ziel, basis);
    const ok = url.origin === new URL(basis).origin && url.pathname !== "/" && !url.pathname.startsWith("//");
    return ok ? url : null;
  } catch {
    return null;
  }
}

/** Was soll für diesen Pfad passieren? null = normal ausliefern. */
export function seoAktionFuer(pfad: string, tabelle: SeoTabelle): SeoAktion | null {
  const slug = eventSlugAusPfad(pfad);
  if (!slug) return null;
  const a = tabelle.get(slug);
  if (!a) return null;
  if (a.aktion === "weiterleiten" && !zielErlaubt(a.ziel)) return null;
  return a;
}

/** Zeilen aus der DB in die Nachschlagetabelle übernehmen („behalten“ braucht keinen Eintrag). */
export function tabelleAus(zeilen: { slug: unknown; aktion: unknown; ziel: unknown }[]): SeoTabelle {
  const t: SeoTabelle = new Map();
  for (const z of zeilen) {
    if (typeof z.slug !== "string") continue;
    if (z.aktion === "gone") t.set(z.slug, { aktion: "gone" });
    else if (z.aktion === "weiterleiten" && typeof z.ziel === "string" && zielErlaubt(z.ziel)) {
      t.set(z.slug, { aktion: "weiterleiten", ziel: z.ziel });
    }
  }
  return t;
}

// ---------- Laden mit Zwischenspeicher (pro Server-Prozess) ----------

const GUELTIG_MS = 10 * 60 * 1000;
let stand: { tabelle: SeoTabelle; geladen: number } | null = null;
let laufend: Promise<void> | null = null;

async function neuLaden(): Promise<void> {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;
  if (!url || !key) return;
  const zeilen: { slug: unknown; aktion: unknown; ziel: unknown }[] = [];
  for (let seite = 0; seite < 50; seite++) {
    const r = await fetch(
      `${url}/rest/v1/event_seo_entscheidungen?select=slug,aktion,ziel&aktion=neq.behalten&order=slug&offset=${seite * 1000}&limit=1000`,
      { headers: { apikey: key, Authorization: `Bearer ${key}` }, signal: AbortSignal.timeout(5000) },
    );
    if (!r.ok) throw new Error(`HTTP ${r.status}`); // z.B. Tabelle fehlt noch → alte Tabelle behalten
    const daten = (await r.json()) as typeof zeilen;
    zeilen.push(...daten);
    if (daten.length < 1000) break;
  }
  stand = { tabelle: tabelleAus(zeilen), geladen: Date.now() };
}

/**
 * Aktuelle Tabelle. Beim ersten Aufruf wird gewartet; danach wird im Hintergrund aufgefrischt und
 * bis dahin die bisherige Tabelle benutzt. Fehler → leere/bisherige Tabelle (Seiten bleiben online).
 */
export async function seoTabelle(): Promise<SeoTabelle> {
  const veraltet = !stand || Date.now() - stand.geladen > GUELTIG_MS;
  if (veraltet && !laufend) {
    laufend = neuLaden()
      .catch((err) => {
        console.warn(`SEO-Entscheidungen nicht geladen: ${err instanceof Error ? err.message : err}`);
        // Erneuter Versuch frühestens nach einer Minute
        stand = { tabelle: stand?.tabelle ?? new Map(), geladen: Date.now() - GUELTIG_MS + 60_000 };
      })
      .finally(() => {
        laufend = null;
      });
  }
  if (!stand && laufend) await laufend;
  return stand?.tabelle ?? new Map();
}
