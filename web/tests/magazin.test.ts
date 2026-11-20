// Magazin (Plan docs/plan-redaktion-2026-11-19.md, Abschnitt 7.1): Renderer, Proxy, Auswahl, Metadaten, JSON-LD,
// Feed, Bilder, Sitemap. Keine echten Netzaufrufe: Supabase-Client und fetch sind ersetzt.
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import sharp from "sharp";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ev } from "./hilfen";

// ---------- Ersatz für Schalter und Supabase ----------
const zustand = vi.hoisted(() => ({
  magazinVerlinkt: false,
  abfragen: [] as { tabelle: string; schritte: [string, unknown[]][] }[],
  eventZeilen: [] as Record<string, unknown>[],
  fehler: null as { message: string } | null,
}));

vi.mock("@/lib/schalter", async (original) => {
  const echt = await original<typeof import("@/lib/schalter")>();
  return {
    ...echt,
    get MAGAZIN_VERLINKT() {
      return zustand.magazinVerlinkt;
    },
  };
});

/** Kettenfähiger Ersatz-Client: merkt sich jeden Schritt, liefert Events seitenweise (eine Seite). */
function ersatzClient() {
  return {
    from(tabelle: string) {
      const eintrag = { tabelle, schritte: [] as [string, unknown[]][] };
      zustand.abfragen.push(eintrag);
      const kette: Record<string, unknown> = {};
      for (const name of ["select", "eq", "or", "lte", "gte", "lt", "order", "in", "limit", "maybeSingle"]) {
        kette[name] = (...args: unknown[]) => {
          eintrag.schritte.push([name, args]);
          return kette;
        };
      }
      kette.range = (...args: unknown[]) => {
        eintrag.schritte.push(["range", args]);
        return Promise.resolve({ data: zustand.fehler ? null : zustand.eventZeilen, error: zustand.fehler });
      };
      kette.then = (ok: (x: unknown) => unknown) => ok({ data: zustand.fehler ? null : [], error: zustand.fehler });
      return kette;
    },
  };
}
vi.mock("@/lib/supabase-server", () => ({ leseClient: () => ersatzClient(), dienstClient: () => ersatzClient() }));

import { highlights, highlightsImZeitraum, breite, filtern, highlightGilt, nachEmpfehlung, stufenKontext, topGilt } from "@/lib/ableitungen";
import { magazinPoolLaden, poolGrenzen } from "@/lib/daten";
import {
  beitragPfad, entstehungsHinweis, istArchiviert, istVorbei, RUBRIKEN, saisonVorbei, type MagazinAutor, type MagazinBeitrag,
} from "@/lib/magazin";
import { auswahlRechnen, schluesselOk, zeitraumPassend } from "@/lib/magazin-auswahl";
import { imErlaubtenOrdner } from "@/lib/magazin-bild-pfad";
import { ERLAUBTE_FALLBACK_HEROS, heroErlaubt, heroFuer, RUBRIK_ERSATZ, zuschnittPruefen } from "@/lib/magazin-bilder";
import { ortZiel } from "@/lib/magazin-daten";
import { feedXml, FEED_MAX, rfc822, xml } from "@/lib/magazin-feed";
import { artikelJsonLd, autorJsonLd } from "@/lib/magazin-json-ld";
import { einbettungPruefen, inhaltsverzeichnis, linkZiel, parsen } from "@/lib/magazin-markdown";
import {
  magazinBeitragEntscheidung, pfadPruefen, routeVon, sha256Hex, speicherLeeren, vorschauPruefen,
} from "@/lib/pfad-pruefung";
import { seitenAlternates, seitenMetadaten } from "@/lib/seo";
import { AutorZeile, MagazinOrtKarte, MagazinText } from "@/components/magazin";
import { erwaehntIn, lesetippFuer, startAuswahl, wochenvorschauFuer } from "@/components/magazin-verweise";
import { config as proxyConfig } from "@/proxy";
import { magazinEintraege } from "@/app/sitemap";
import type { DddEvent, EventPool } from "@/lib/typen";

const SITE = "https://diesdas.events";

function beitrag(teil: Partial<MagazinBeitrag> = {}): MagazinBeitrag {
  return {
    id: "11111111-1111-4111-8111-111111111111",
    slug: "events-duesseldorf-30-november-bis-6-dezember-2026",
    rubrik: "wochenvorschau",
    autor_slug: "lena-test",
    titel: "Was ist los in Düsseldorf? 30. November bis 6. Dezember 2026",
    seo_titel: null,
    teaser: "Die Woche in Düsseldorf: Konzerte, Bühne, Weihnachtsmärkte und mehr – unsere Auswahl für euch.",
    inhalt_md: "Text",
    kurzfassung: null,
    faq: null,
    hero_bild: "/fallback/theater-1.webp",
    hero_alt: "Bühne",
    hero_nachweis: "Symbolbild",
    hero_ki: true,
    veroeffentlicht_am: "2026-11-29T07:00:00Z",
    aktualisiert_am: null,
    korrektur_hinweis: null,
    gueltig_von: "2026-11-30",
    gueltig_bis: "2026-12-06",
    event_ids: [],
    ort_slugs: [],
    quellen: [],
    ...teil,
  };
}
const AUTOR: MagazinAutor = { slug: "lena-test", name: "Lena Rheinblick", kurzbeschreibung: "x", schwerpunkt: "Events", rubriken: ["wochenvorschau"], bild: null, bild_ki: true };

// ---------- Renderer (Befund 6) ----------
describe("Renderer", () => {
  it("Überschriften, Listen, Fett, Links und alle vier Einbettungen", () => {
    const b = parsen(
      [
        "## Am Montag", "Ein **starker** Abend mit [Link](/heute) und [extern](https://www.duesseldorf.de/x).", "",
        "- eins", "- zwei", "", "1. erst", "2. dann", "", "### Unterpunkt",
        "{{event:c9f25a3d-1506-4c59-80ae-5c536fde5ad3}}", "{{ort:zakk-flingern}}", "{{guide:weihnachtsmaerkte}}", "{{tag:2026-11-30}}",
      ].join("\n"),
    );
    expect(b.map((x) => x.art)).toEqual(["h2", "absatz", "liste", "liste", "h3", "einbettung", "einbettung", "einbettung", "einbettung"]);
    expect(b[0]).toMatchObject({ art: "h2", id: "am-montag" });
    expect(b[2]).toMatchObject({ nummeriert: false });
    expect(b[3]).toMatchObject({ nummeriert: true });
    const absatz = b[1] as Extract<(typeof b)[number], { art: "absatz" }>;
    expect(absatz.inhalt.map((t) => t.art)).toEqual(["text", "fett", "text", "link", "text", "link", "text"]);
  });

  it("unsichere Linkziele werden Text", () => {
    for (const ziel of ["//beispiel.de", "/../x", "/%2e%2e/x", "/%2f%2fbeispiel.de", "%zz", "javascript:alert(1)", "data:text/html,x", "http://unsicher.de", "/a\\b"]) {
      expect(linkZiel(ziel), ziel).toBeNull();
    }
    expect(linkZiel("/guides/clubs")).toEqual({ href: "/guides/clubs", extern: false });
    expect(linkZiel("/event/musik/a%20b")).toEqual({ href: "/event/musik/a%20b", extern: false });
    expect(linkZiel("https://www.duesseldorf.de/x")?.extern).toBe(true);
  });

  it("rohes HTML und ungültige Einbettungen erscheinen nie als HTML", () => {
    const html = renderToStaticMarkup(
      createElement(MagazinText, {
        bloecke: parsen('<script>alert(1)</script>\n\n{{event:<img src=x>}}\n\n{{ort:a"b}}\n\n[böse](javascript:alert(1)) [gut](https://www.duesseldorf.de/x)'),
        events: [], orte: [], heute: "2026-11-30",
      }),
    );
    expect(html).not.toContain("<script");
    expect(html).not.toContain("<img src=x");
    expect(html).not.toContain('href="javascript');
    expect(html).toContain('rel="noopener"');
    expect(einbettungPruefen("event", "<img src=x>")).toBeNull();
    expect(einbettungPruefen("ort", 'a"b')).toBeNull();
    expect(einbettungPruefen("tag", "2026-02-30")).toBeNull();
  });

  it("Inhaltsverzeichnis erst ab drei ##-Überschriften, Anker eindeutig", () => {
    expect(inhaltsverzeichnis(parsen("## A\n\n## B"))).toEqual([]);
    expect(inhaltsverzeichnis(parsen("## Tipp\n\n## Tipp\n\n## Märkte")).map((t) => t.id)).toEqual(["tipp", "tipp-2", "maerkte"]);
  });
});

// ---------- Proxy (Befunde 1 und 2) ----------
describe("Proxy: Routen", () => {
  it("erkennt alle Magazin-Typen", () => {
    expect(routeVon("/magazin")).toEqual({ typ: "magazin-fest" });
    expect(routeVon("/magazin/feed.xml")).toEqual({ typ: "magazin-fest" });
    expect(routeVon("/magazin/redaktion")).toEqual({ typ: "magazin-fest" });
    expect(routeVon("/feed.xml")).toEqual({ typ: "feed-alt" });
    expect(routeVon("/magazin/rubrik/saison")).toEqual({ typ: "magazin-rubrik", rubrik: "saison" });
    expect(routeVon("/magazin/autor/lena")).toEqual({ typ: "magazin-autor", slug: "lena" });
    expect(routeVon("/magazin/vorschau/x")).toEqual({ typ: "magazin-vorschau", id: "x" });
    expect(routeVon("/magazin/ein-beitrag")).toEqual({ typ: "magazin-beitrag", slug: "ein-beitrag" });
    expect(routeVon("/magazin/autor/x/y")).toEqual({ typ: "ungueltig" });
    expect(routeVon("/magazin/x/y")).toEqual({ typ: "ungueltig" });
    expect(routeVon("/magazin/rubrik")).toEqual({ typ: "ungueltig" });
  });

  it("matcher enthält /magazin/:path* und /feed.xml", () => {
    expect(proxyConfig.matcher).toEqual(expect.arrayContaining(["/magazin/:path*", "/feed.xml"]));
  });

  it("Beitrags-Entscheidung rechnet die Sichtbarkeit zur Prüfzeit", () => {
    const jetzt = Date.parse("2026-11-29T08:00:00Z");
    const sichtbar = { slug: "a", status: "veroeffentlicht", veroeffentlicht_am: "2026-11-29T07:00:00Z" };
    expect(magazinBeitragEntscheidung(sichtbar, null, jetzt)).toEqual({ art: "weiter" });
    expect(magazinBeitragEntscheidung({ ...sichtbar, veroeffentlicht_am: "2026-11-29T09:00:00Z" }, null, jetzt)).toEqual({ art: "fehlt" });
    expect(magazinBeitragEntscheidung({ ...sichtbar, status: "zurueckgezogen" }, null, jetzt)).toEqual({ art: "fehlt" });
    expect(magazinBeitragEntscheidung({ ...sichtbar, status: "entwurf" }, null, jetzt)).toEqual({ art: "fehlt" });
    expect(magazinBeitragEntscheidung(null, sichtbar, jetzt)).toEqual({ art: "umleiten", ziel: "/magazin/a" });
    expect(magazinBeitragEntscheidung(null, null, jetzt)).toEqual({ art: "fehlt" });
  });
});

describe("Proxy: Abfragen mit dem Service-Schlüssel", () => {
  const schluessel: string[] = [];
  let antwort: (url: string) => unknown[] | "fehler" = () => [];
  beforeEach(() => {
    speicherLeeren();
    schluessel.length = 0;
    vi.stubEnv("SUPABASE_URL", "https://db.example");
    vi.stubEnv("SUPABASE_KEY", "anon-schluessel");
    vi.stubEnv("SUPABASE_SERVICE_KEY", "dienst-schluessel");
    vi.stubGlobal("fetch", async (url: string, init?: { headers?: Record<string, string> }) => {
      schluessel.push(init?.headers?.apikey ?? "");
      const a = antwort(decodeURIComponent(url));
      return a === "fehler" ? new Response("x", { status: 500 }) : new Response(JSON.stringify(a), { status: 200 });
    });
  });
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("unbekannter Slug → 404, alter Slug → 308, nur mit Service-Schlüssel abgefragt", async () => {
    antwort = (u) => (u.includes("alte_slugs=cs.{alt}") ? [{ slug: "neu", status: "veroeffentlicht", veroeffentlicht_am: "2026-01-01T00:00:00Z" }] : []);
    expect(await pfadPruefen("/magazin/gibt-es-nicht")).toEqual({ art: "fehlt" });
    expect(await pfadPruefen("/magazin/alt")).toEqual({ art: "umleiten", ziel: "/magazin/neu" });
    expect(schluessel.length).toBeGreaterThan(0);
    expect(schluessel.every((s) => s === "dienst-schluessel")).toBe(true);
  });

  it("Zukunft und zurückgezogen → 404; Abfragefehler → weiter", async () => {
    antwort = (u) =>
      u.includes("slug=eq.zukunft")
        ? [{ slug: "zukunft", status: "veroeffentlicht", veroeffentlicht_am: "2099-01-01T00:00:00Z" }]
        : u.includes("slug=eq.weg")
          ? [{ slug: "weg", status: "zurueckgezogen", veroeffentlicht_am: "2026-01-01T00:00:00Z" }]
          : "fehler";
    expect(await pfadPruefen("/magazin/zukunft")).toEqual({ art: "fehlt" });
    expect(await pfadPruefen("/magazin/weg")).toEqual({ art: "fehlt" });
    expect(await pfadPruefen("/magazin/fehler-beim-laden")).toEqual({ art: "weiter" });
  });

  it("Rubrik, Autor, Feed, feste Seiten", async () => {
    antwort = (u) => (u.includes("magazin_autoren") && u.includes("slug=eq.lena") ? [{ slug: "lena" }] : []);
    expect(await pfadPruefen("/magazin/rubrik/saison")).toEqual({ art: "weiter" });
    expect(await pfadPruefen("/magazin/rubrik/unbekannt")).toEqual({ art: "fehlt" });
    expect(await pfadPruefen("/magazin/autor/lena")).toEqual({ art: "weiter" });
    expect(await pfadPruefen("/magazin/autor/niemand")).toEqual({ art: "fehlt" });
    expect(await pfadPruefen("/feed.xml")).toEqual({ art: "umleiten", ziel: "/magazin/feed.xml" });
    expect(await pfadPruefen("/magazin")).toEqual({ art: "weiter" });
    expect(await pfadPruefen("/magazin/feed.xml")).toEqual({ art: "weiter" });
  });

  it("Vorschau: nur mit passendem Schlüssel; Fehler und veröffentlichte Beiträge → 404", async () => {
    const id = "11111111-1111-4111-8111-111111111111";
    const hash = await sha256Hex("geheim-123");
    antwort = (u) => (u.includes(`id=eq.${id}`) && u.includes("status=in.(entwurf,in_pruefung)") ? [{ vorschau_hash: hash }] : []);
    expect(await vorschauPruefen(id, "geheim-123")).toEqual({ art: "weiter" });
    expect(await pfadPruefen(`/magazin/vorschau/${id}`, new URLSearchParams("s=geheim-123"))).toEqual({ art: "weiter" });
    expect(await vorschauPruefen(id, null)).toEqual({ art: "fehlt" });
    expect(await vorschauPruefen(id, "falsch")).toEqual({ art: "fehlt" });
    expect(await vorschauPruefen("keine-uuid", "geheim-123")).toEqual({ art: "fehlt" });
    antwort = () => []; // veröffentlicht: Statusfilter liefert nichts
    expect(await vorschauPruefen(id, "geheim-123")).toEqual({ art: "fehlt" });
    antwort = () => "fehler";
    expect(await vorschauPruefen(id, "geheim-123")).toEqual({ art: "fehlt" });
  });
});

// ---------- Auswahl (Plan 4.2, T11) ----------
const bild = "https://example.com/b.jpg";
function pool(events: DddEvent[], heute: string): EventPool {
  return { heute, jetzt: `${heute}T08:00:00Z`, events, alle: events, quelle: "supabase", fehler: null };
}

describe("Auswahl", () => {
  it("Wochenvorschau: Highlight liegt in der Zielwoche, auch wenn am 28.11. ein stärkeres Event ist", () => {
    const p = pool(
      [
        ev({ id: "vorher", datum: "2026-11-28", ort: "Tonhalle", bild_url: bild, titel: "Großes Konzert" }),
        ev({ id: "woche", datum: "2026-12-02", ort: "zakk", bild_url: bild, titel: "Konzert" }),
        ev({ id: "ende", datum: "2026-12-06", ort: "FFT", bild_url: bild, titel: "Theater", kategorie: "kultur" }),
      ],
      "2026-11-30",
    );
    const h = highlightsImZeitraum(p, { von: "2026-11-30", bis: "2026-12-06" }, "highlight");
    expect(["woche", "ende"]).toContain(h?.id);
    const a = auswahlRechnen(p, "wochenvorschau", "2026-11-30", "2026-12-06");
    expect(a.kandidaten.map((k) => k.id)).toContain("ende");
    expect(a.kandidaten.map((k) => k.id)).not.toContain("vorher");
  });

  it("Monats-Tipps: Top am 31.12. wird gefunden, Ende November nie", () => {
    const p = pool(
      [
        ev({ id: "nov", datum: "2026-11-29", ort: "Tonhalle", bild_url: bild }),
        ev({ id: "silvester", datum: "2026-12-31", ort: "Tonhalle", bild_url: bild, titel: "Silvesterkonzert" }),
      ],
      "2026-12-01",
    );
    expect(highlightsImZeitraum(p, { von: "2026-12-01", bis: "2026-12-31" }, "top")?.id).toBe("silvester");
    const a = auswahlRechnen(p, "monats-tipps", "2026-12-01", "2026-12-31");
    expect(a.top).toBe("silvester");
    expect(a.kandidaten.map((k) => k.id)).not.toContain("nov");
  });

  it("Monats-Tipps: das beste Event des Monats wird Top-Event (kein Highlight-Ausschluss)", () => {
    const p = pool(
      [
        ev({ id: "bester", datum: "2026-12-03", ort: "Tonhalle", bild_url: bild }),
        ev({ id: "zweiter", datum: "2026-12-10", ort: "zakk", bild_url: bild }),
      ],
      "2026-12-01",
    );
    expect(highlightsImZeitraum(p, { von: "2026-12-01", bis: "2026-12-31" }, "top")?.id).toBe("bester");
  });

  it("highlights(): unverändert gegenüber der alten Regelkette, Ausschluss bleibt, Stamm nie", () => {
    const heute = "2026-11-30";
    const events = [
      ev({ id: "zugpferd", datum: "2026-12-01", ort: "Tonhalle", bild_url: bild }),
      ev({ id: "normal", datum: "2026-12-03", ort: "zakk", bild_url: bild }),
      ev({ id: "monat", datum: "2026-12-20", ort: "FFT", bild_url: bild, kategorie: "kultur" }),
      ev({ id: "yoga", datum: "2026-12-02", titel: "Yoga im Park", bild_url: bild, ort: "Hofgarten" }),
    ];
    const p = pool(events, heute);
    // Alte Implementierung (vor dem Umbau, Plan 4.2) als Vergleich
    const alt = () => {
      const aktiv = p.events.filter((e) => !e.abgesagt);
      const k = stufenKontext(aktiv, heute);
      const vergleich = nachEmpfehlung(k);
      const ohneStamm = (l: DddEvent[]) => l.filter((e) => (breite(e, k) ?? 0) >= 1);
      const woche = ohneStamm(filtern(aktiv, { von: heute, bis: "2026-12-06", mitLanglaeufern: true }));
      const monat = ohneStamm(filtern(aktiv, { von: heute, bis: "2026-12-29", mitLanglaeufern: true }));
      const waehle = (liste: DddEvent[], flagge: (e: DddEvent) => boolean, ohne?: string) => {
        const frei = liste.filter((e) => e.id !== ohne);
        const regeln: ((e: DddEvent) => boolean)[] = [
          (e) => flagge(e) && !!e.bild_url, (e) => breite(e, k) === 3 && !!e.bild_url, (e) => breite(e, k) === 2 && !!e.bild_url,
          (e) => flagge(e), () => true,
        ];
        for (const r of regeln) {
          const t = frei.filter(r);
          if (t.length) return t.sort(vergleich)[0];
        }
        return null;
      };
      const highlight = waehle(woche, (e) => highlightGilt(e, heute));
      return { highlight, top: waehle(monat, (e) => topGilt(e, heute), highlight?.id) };
    };
    const neu = highlights(p);
    expect(neu.highlight?.id).toBe(alt().highlight?.id);
    expect(neu.top?.id).toBe(alt().top?.id);
    expect(neu.highlight?.id).toBe("zugpferd");
    expect(neu.top?.id).not.toBe("zugpferd");
    expect([neu.highlight?.id, neu.top?.id]).not.toContain("yoga");
    expect(highlightsImZeitraum(pool([events[3]], heute), { von: heute, bis: "2026-12-06" }, "highlight")).toBeNull();
  });

  it("magazinPoolLaden: ab von, Ende max(bis, von + 60 Tage), buendeln; Fehler wirft", async () => {
    expect(poolGrenzen("2026-11-30", "2026-12-06")).toEqual({ von: "2026-11-30", bis: "2027-01-29" });
    expect(poolGrenzen("2026-11-30", "2027-03-01")).toEqual({ von: "2026-11-30", bis: "2027-03-01" });
    expect(poolGrenzen("2026-11-19")).toEqual({ von: "2026-11-19", bis: "2027-01-18" });
    zustand.abfragen.length = 0;
    zustand.fehler = null;
    zustand.eventZeilen = [
      { id: "a", titel: "Konzert", datum: "2026-12-04", uhrzeit: "18:00", ort: "zakk", kategorie: "musik" },
      { id: "b", titel: "Konzert", datum: "2026-12-04", uhrzeit: "21:00", ort: "zakk", kategorie: "musik" },
    ];
    const p = await magazinPoolLaden("2026-11-30", "2026-12-06");
    const schritte = zustand.abfragen.find((a) => a.tabelle === "events")!.schritte;
    expect(schritte).toContainEqual(["or", ["datum.gte.2026-11-30,datum_bis.gte.2026-11-30"]]);
    expect(schritte).toContainEqual(["lte", ["datum", "2027-01-29"]]);
    expect(p.heute).toBe("2026-11-30");
    expect(p.alle).toHaveLength(2);
    expect(p.events).toHaveLength(1); // zwei Uhrzeiten desselben Tages gebündelt
    zustand.fehler = { message: "kaputt" };
    await expect(magazinPoolLaden("2026-11-30", "2026-12-06")).rejects.toThrow();
    zustand.fehler = null;
  });

  it("Zeitraum muss zur Rubrik passen", () => {
    expect(zeitraumPassend("wochenvorschau", "2026-11-30", "2026-12-06")).toBe(true);
    expect(zeitraumPassend("wochenvorschau", "2026-11-27", "2026-12-03")).toBe(false); // Freitag
    expect(zeitraumPassend("monats-tipps", "2026-12-01", "2026-12-31")).toBe(true);
    expect(zeitraumPassend("monats-tipps", "2027-02-01", "2027-02-28")).toBe(true);
    expect(zeitraumPassend("monats-tipps", "2026-12-01", "2026-12-30")).toBe(false);
    expect(zeitraumPassend("saison", "2026-12-01", "2026-12-31")).toBe(false);
  });

  it("Schlüssel der Auswahl-Route: SHA-256-Vergleich, nie ein Fehler", () => {
    expect(schluesselOk("richtig", "richtig")).toBe(true);
    for (const falsch of [null, undefined, "", "falsch", "r", "richtig-und-viel-zu-lang"]) expect(schluesselOk(falsch, "richtig")).toBe(false);
    expect(schluesselOk("richtig", undefined)).toBe(false);
  });

  it("Auswahl-Route: 404 ohne Schlüssel, 400 bei falschem Zeitraum, 200 mit no-store", async () => {
    const { POST, GET } = await import("@/app/api/magazin/auswahl/route");
    const anfrage = (kopf: Record<string, string>, body: unknown) =>
      new Request("https://x/api/magazin/auswahl", { method: "POST", headers: kopf, body: JSON.stringify(body) }) as never;
    vi.stubEnv("MAGAZIN_JOB_SCHLUESSEL", "geheim");
    expect((await GET()).status).toBe(404);
    expect((await POST(anfrage({}, {}))).status).toBe(404);
    expect((await POST(anfrage({ "x-magazin-schluessel": "falsch" }, {}))).status).toBe(404);
    const falsch = await POST(anfrage({ "x-magazin-schluessel": "geheim" }, { rubrik: "wochenvorschau", von: "2026-11-27", bis: "2026-12-03" }));
    expect(falsch.status).toBe(400);
    zustand.eventZeilen = [{ id: "a", titel: "Konzert", datum: "2026-12-02", ort: "Tonhalle", kategorie: "musik", bild_url: bild }];
    const ok = await POST(anfrage({ "x-magazin-schluessel": "geheim" }, { rubrik: "wochenvorschau", von: "2026-11-30", bis: "2026-12-06" }));
    expect(ok.status).toBe(200);
    expect(ok.headers.get("cache-control")).toBe("no-store");
    expect((await ok.json()).kandidaten.map((k: { id: string }) => k.id)).toEqual(["a"]);
    zustand.fehler = { message: "kaputt" };
    expect((await POST(anfrage({ "x-magazin-schluessel": "geheim" }, { rubrik: "wochenvorschau", von: "2026-11-30", bis: "2026-12-06" }))).status).toBe(503);
    zustand.fehler = null;
    vi.unstubAllEnvs();
    expect((await POST(anfrage({ "x-magazin-schluessel": "geheim" }, {}))).status).toBe(404);
  });
});

// ---------- Metadaten (Befund 5, Prüfung 3 Befund 4) ----------
describe("Metadaten", () => {
  afterEach(() => {
    zustand.magazinVerlinkt = false;
  });

  it("Feed-Link nur mit Schalter, im indexierbaren Zweig; noindex ohne alternates", () => {
    expect(seitenAlternates("/x")).toEqual({ canonical: "/x" });
    zustand.magazinVerlinkt = true;
    expect(seitenAlternates("/x")).toEqual({
      canonical: "/x", types: { "application/rss+xml": [{ url: "/magazin/feed.xml", title: "dies.das.düsseldorf – Magazin" }] },
    });
    expect(seitenMetadaten({ pfad: "/heute" }).alternates).toMatchObject({ canonical: "/heute", types: expect.anything() });
    expect(seitenMetadaten({ pfad: "/x", noindex: true }).alternates).toBeUndefined();
  });

  it("Guide-Übersicht und Seiten mit eigenem alternates behalten den Feed-Link", async () => {
    zustand.magazinVerlinkt = true;
    vi.resetModules();
    const { metadata } = await import("@/app/guides/page");
    expect(metadata.alternates).toMatchObject({ canonical: "/guides", types: { "application/rss+xml": expect.anything() } });
  });

  it("Artikel: og:type article und Autor = Redaktion (nie das Pseudonym)", () => {
    const m = seitenMetadaten({ pfad: "/magazin/x", titel: "T", artikel: { veroeffentlicht: "2026-11-29T07:00:00Z", rubrik: "Wochenvorschau" } });
    expect(m.openGraph).toMatchObject({ type: "article", publishedTime: "2026-11-29T07:00:00Z", authors: ["Redaktion dies.das.düsseldorf"], section: "Wochenvorschau" });
    expect(m.authors).toEqual([{ name: "Redaktion dies.das.düsseldorf", url: "/magazin/redaktion" }]);
    expect(seitenMetadaten({ pfad: "/x" }).openGraph).toMatchObject({ type: "website" });
    expect(seitenMetadaten({ pfad: "/x" }).authors).toBeUndefined();
  });
});

// ---------- JSON-LD und sichtbare Kennzeichnung ----------
describe("JSON-LD und Kennzeichnung", () => {
  it("Article mit Redaktion als Autor, echte Person nur als accountablePerson, kein Pseudonym, kein Event-Markup", () => {
    const e = ev({ id: "e1", kategorie: "musik", slug: "konzert-2026-12-02" });
    const daten = artikelJsonLd(SITE, beitrag({ aktualisiert_am: "2026-11-30T10:00:00Z" }), [e]);
    const text = JSON.stringify(daten);
    const graph = (daten["@graph"] as Record<string, unknown>[]);
    const artikel = graph.find((g) => g["@type"] === "Article")!;
    expect(artikel.author).toMatchObject({ "@type": "Organization", name: "Redaktion dies.das.düsseldorf" });
    expect(artikel.accountablePerson).toMatchObject({ "@type": "Person", name: "Yannick Fetsch" });
    expect(text.match(/"@type":"Person"/g)).toHaveLength(1);
    expect(text).not.toContain(AUTOR.name);
    expect(text).not.toContain('"@type":"Event"');
    expect(artikel.dateModified).toBe("2026-11-30T11:00:00+01:00");
    expect(artikel.image).toEqual([
      `${SITE}/magazin-bild/16x9/fallback/theater-1.webp`, `${SITE}/magazin-bild/4x3/fallback/theater-1.webp`, `${SITE}/magazin-bild/1x1/fallback/theater-1.webp`,
    ]);
    expect(artikel.mentions).toEqual([{ "@id": `${SITE}/event/musik/konzert-2026-12-02` }]);
  });

  it("Autorenseite: kein Pseudonym-Name im JSON-LD, keine Person, kein ProfilePage", () => {
    const text = JSON.stringify(autorJsonLd(SITE, "/magazin/autor/lena-test"));
    expect(text).not.toContain(AUTOR.name);
    expect(text).toContain("Redaktionelles Pseudonym");
    expect(text).not.toContain('"@type":"Person"');
    expect(text).not.toContain("ProfilePage");
  });

  it("Quellen-Links: nur geprüftes https (javascript:, Steuerzeichen → Text)", () => {
    expect(linkZiel("javascript:alert(1)")).toBeNull();
    expect(linkZiel("https://example.com/%07x")).toBeNull();
    expect(linkZiel("https://example.com/quelle")?.extern).toBe(true);
  });

  it("mailto nur auf Adressen von diesdas.events, ohne Zusätze (20.11.2026)", () => {
    expect(linkZiel("mailto:hallo@diesdas.events")).toEqual({ href: "mailto:hallo@diesdas.events", extern: false });
    expect(linkZiel("mailto:x@example.com")).toBeNull();
    expect(linkZiel("mailto:hallo@diesdas.events?subject=x")).toBeNull();
    expect(linkZiel("mailto:hallo@diesdas.events.example.com")).toBeNull();
  });

  it("Autorenzeile ohne Pseudonym-Zusatz und ohne Redaktions-Link; Hinweis am Ende wählt die Datenart (E4a)", () => {
    const zeile = renderToStaticMarkup(createElement(AutorZeile, { autor: AUTOR }));
    expect(zeile).toContain(`>${AUTOR.name}</a>`);
    expect(zeile).not.toContain("Pseudonym");
    expect(zeile).not.toContain("/magazin/redaktion");
    expect(entstehungsHinweis({ event_ids: ["a"], ort_slugs: [] })).toContain("aus unseren Eventdaten");
    expect(entstehungsHinweis({ event_ids: [], ort_slugs: ["x"] })).toContain("aus unseren Ortsdaten");
    expect(entstehungsHinweis({ event_ids: ["a"], ort_slugs: ["x"] })).toContain("aus unseren Event- und Ortsdaten");
    expect(entstehungsHinweis({ event_ids: [], ort_slugs: [] })).toContain("Redaktionell verantwortlich: Yannick Fetsch.");
  });

  it("Ort-Einbettung ohne Google-Foto und -Bewertung (Befund 7)", () => {
    const html = renderToStaticMarkup(createElement(MagazinOrtKarte, { ort: { slug: "zakk", name: "zakk", typ: "club", stadtteil: "Flingern", pfad: "/guides/clubs/zakk" } }));
    expect(html).not.toContain("/ort-foto/");
    expect(html).not.toMatch(/★|google/i);
    expect(html).toContain('href="/guides/clubs/zakk"');
  });

  it("Ort-Link folgt der Proxy-Regel", () => {
    const kopf = { typ: "restaurant", aktiv: true, qualitaets_score: 8, club: null, club_score: null, club_freigegeben: null, auch_club: null };
    expect(ortZiel("pizza", kopf)).toBe("/guides/restaurants-cafes/pizza");
    expect(ortZiel("pizza", { ...kopf, qualitaets_score: 5 })).toBeNull();
  });
});

// ---------- Bilder ----------
describe("Bilder", () => {
  it("ERLAUBTE_FALLBACK_HEROS = alle Fallback-Dateien mit mindestens 1200×675 (84)", async () => {
    const ordner = path.resolve(__dirname, "../public/fallback");
    const dateien = readdirSync(ordner).filter((d) => d.endsWith(".webp")).sort();
    const hoch: string[] = [];
    for (const d of dateien) {
      const m = await sharp(path.join(ordner, d)).metadata();
      if ((m.width ?? 0) >= 1200 && (m.height ?? 0) >= 675) hoch.push(`/fallback/${d}`);
    }
    expect([...ERLAUBTE_FALLBACK_HEROS].sort()).toEqual(hoch);
    expect(hoch).toHaveLength(84);
    for (const ersatz of Object.values(RUBRIK_ERSATZ)) expect(ERLAUBTE_FALLBACK_HEROS).toContain(ersatz);
  });

  it("heroFuer: zu flaches oder fremdes Bild → Rubrik-Ersatz; erlaubtes bleibt", () => {
    expect(heroFuer(beitrag({ hero_bild: "/fallback/theater-1.webp" }))).toMatchObject({ pfad: "/fallback/theater-1.webp", ersatz: false, ki: true });
    expect(heroFuer(beitrag({ hero_bild: "/fallback/sprachcafe-2.webp" }))).toMatchObject({ pfad: RUBRIK_ERSATZ.wochenvorschau, ersatz: true });
    expect(heroFuer(beitrag({ hero_bild: "/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp" })).ersatz).toBe(true);
    // Eigene Fotos ohne sichtbaren Nachweis, fremde mit (Auftraggeber, 20.11.2026)
    expect(heroFuer(beitrag({ hero_bild: "/ort-bilder/weihnachtsmaerkte/maerchen-markt.webp", hero_ki: false, hero_nachweis: "Foto: dies.das.düsseldorf" })))
      .toMatchObject({ ersatz: false, ki: false, nachweis: "" });
    expect(heroFuer(beitrag({ hero_bild: "/ort-bilder/weihnachtsmaerkte/maerchen-markt.webp", hero_ki: false, hero_nachweis: "dies.das.düsseldorf" })).nachweis).toBe("");
    expect(heroFuer(beitrag({ hero_bild: "/magazin-bilder/x/hero.webp", hero_ki: false, hero_nachweis: "Foto: Stadt Düsseldorf" })).nachweis)
      .toBe("Foto: Stadt Düsseldorf");
    expect(heroErlaubt("/magazin-bilder/x/hero.webp")).toBe(true);
    expect(heroErlaubt("/ort-bilder/events/further-nikolausmarkt.webp")).toBe(false);
  });

  it("Zuschnitt-Route: nur erlaubte Ordner, Formate und Endungen (Befund 8)", () => {
    expect(zuschnittPruefen(["16x9", "fallback", "theater-1.webp"])).toEqual({ zuschnitt: "16x9", relativ: "fallback/theater-1.webp" });
    expect(zuschnittPruefen(["1x1", "magazin-bilder", "mein-beitrag", "hero.jpg"])?.relativ).toBe("magazin-bilder/mein-beitrag/hero.jpg");
    for (const falsch of [
      ["16x9", "..", "geheim.webp"], ["16x9", "%2e%2e", "geheim.webp"], ["16x9", "fallback", "..%2f..%2fx.webp"], ["2x1", "fallback", "theater-1.webp"],
      ["16x9", "events", "x.webp"], ["16x9", "fallback", "theater-1.gif"], ["16x9", "ort-bilder", "weihnachtsmaerkte", "koe-on-ice.webp"],
      ["16x9", "fallback"], ["16x9", "%zz", "x.webp"],
    ]) {
      expect(zuschnittPruefen(falsch), falsch.join("/")).toBeNull();
    }
    const pub = path.resolve("/srv/web/public");
    expect(imErlaubtenOrdner("fallback/theater-1.webp", pub)).toBe(path.join(pub, "fallback", "theater-1.webp"));
    expect(imErlaubtenOrdner("fallback/../../geheim.webp", pub)).toBeNull();
    expect(imErlaubtenOrdner("bilder/x.webp", pub)).toBeNull();
  });
});

// ---------- Feed (Befund 13) ----------
describe("Feed", () => {
  it("gültiges RSS mit Namensräumen, escaped, höchstens 20, ohne archivierte, Bild über heroFuer", () => {
    const viele = Array.from({ length: 25 }, (_, i) =>
      beitrag({ id: `id-${i}`, slug: `b-${i}`, titel: `Titel & <${i}>`, rubrik: "stadtleben", gueltig_bis: null, hero_bild: "/fallback/sprachcafe-2.webp" }),
    );
    const archiv = beitrag({ id: "alt", slug: "alt", gueltig_bis: "2026-10-01" });
    const x = feedXml(SITE, [archiv, ...viele], [AUTOR], "2026-12-01");
    expect(x).toContain('xmlns:atom="http://www.w3.org/2005/Atom"');
    expect(x).toContain('xmlns:dc="http://purl.org/dc/elements/1.1/"');
    expect(x).toContain('xmlns:media="http://search.yahoo.com/mrss/"');
    expect(x).toContain("Titel &amp; &lt;0&gt;");
    expect(x).not.toContain("<0>");
    expect(x.match(/<item>/g)).toHaveLength(FEED_MAX);
    expect(x).not.toContain("/magazin/alt<");
    expect(x).toContain(`${SITE}/magazin-bild/16x9${RUBRIK_ERSATZ.stadtleben}`);
    expect(rfc822("2026-11-29T07:00:00Z")).toBe("Sun, 29 Nov 2026 07:00:00 GMT");
    expect(xml(`"'`)).toBe("&quot;&apos;");
  });

  it("Route antwortet bei Schalter aus mit 404", async () => {
    zustand.magazinVerlinkt = false;
    const { GET } = await import("@/app/magazin/feed.xml/route");
    expect((await GET()).status).toBe(404);
  });
});

// ---------- Archiv, Sitemap, Rubriken ----------
describe("Archiv, Sitemap und Rubriken", () => {
  it("Archiv-Regeln (E12) und Hinweisboxen", () => {
    const b = beitrag({ gueltig_bis: "2026-12-06" });
    expect(istVorbei(b, "2026-12-06")).toBe(false);
    expect(istVorbei(b, "2026-12-07")).toBe(true);
    expect(istArchiviert(b, "2027-01-05")).toBe(false);
    expect(istArchiviert(b, "2027-01-06")).toBe(true);
    expect(istArchiviert(beitrag({ rubrik: "saison", gueltig_bis: "2026-12-30" }), "2027-06-01")).toBe(false);
    expect(saisonVorbei(beitrag({ rubrik: "saison", gueltig_bis: "2026-12-30" }), "2026-12-31")).toBe(true);
  });

  it("Sitemap: aus ohne Schalter; mit Schalter ohne archivierte, Bild über heroFuer", () => {
    const aktuell = beitrag({ hero_bild: "/fallback/sprachcafe-2.webp" });
    const alt = beitrag({ id: "alt", slug: "alt", gueltig_bis: "2026-10-01" });
    expect(magazinEintraege(SITE, false, [aktuell], [AUTOR], "2026-12-01")).toEqual([]);
    const e = magazinEintraege(SITE, true, [aktuell, alt], [AUTOR], "2026-12-01");
    const urls = e.map((x) => x.url);
    expect(urls).toContain(`${SITE}${beitragPfad(aktuell)}`);
    expect(urls).not.toContain(`${SITE}/magazin/alt`);
    expect(urls).toContain(`${SITE}/magazin/autor/lena-test`);
    expect(e.find((x) => x.url.endsWith(aktuell.slug))?.images).toEqual([`${SITE}${RUBRIK_ERSATZ.wochenvorschau}`]);
  });

  it("Rubrik-Werte = URL-Segmente = Werte der Datenbank", () => {
    expect([...RUBRIKEN]).toEqual(["wochenvorschau", "monats-tipps", "saison", "nachtleben", "genuss", "familie", "stadtleben"]);
    // Dieselben Werte wie im CHECK der Datenbank (database/magazin_rubriken_autoren_2026-11-19.sql)
    const sql = readFileSync(path.resolve(__dirname, "../../database/magazin_rubriken_autoren_2026-11-19.sql"), "utf8");
    const check = sql.match(/CONSTRAINT magazin_rubrik_werte\s+CHECK \(rubrik IN \(([^)]*)\)\)/)?.[1] ?? "";
    expect(check.split(",").map((s) => s.trim().replace(/'/g, ""))).toEqual([...RUBRIKEN]);
  });
});


// ---------- Verweise aufs Magazin (Schritt 7, Plan 5.9) ----------
describe("Verweise aufs Magazin", () => {
  const woche = beitrag({ id: "a", slug: "woche", veroeffentlicht_am: "2026-11-29T07:00:00Z", event_ids: ["e1"] });
  const alt = beitrag({ id: "b", slug: "alt", gueltig_von: "2026-11-23", gueltig_bis: "2026-11-29", veroeffentlicht_am: "2026-11-22T07:00:00Z", event_ids: ["e1", "e2"] });
  const wm = beitrag({ id: "c", slug: "wm", rubrik: "saison", gueltig_von: "2026-11-19", gueltig_bis: "2027-01-10", veroeffentlicht_am: "2026-11-20T09:00:00Z",
    inhalt_md: "{{guide:weihnachtsmaerkte}}", ort_slugs: ["a", "b"] });
  const launch = beitrag({ id: "d", slug: "launch", rubrik: "stadtleben", gueltig_von: null, gueltig_bis: null, veroeffentlicht_am: "2026-11-19T09:00:00Z",
    inhalt_md: "{{guide:weihnachtsmaerkte}}" });
  const liste = [woche, alt, wm, launch];

  it("Startseite: neueste aktuelle Beiträge, abgelaufene Ausgaben fallen raus", () => {
    expect(startAuswahl(liste, "2026-12-01").map((b) => b.slug)).toEqual(["woche", "wm", "launch"]);
    expect(startAuswahl(liste, "2026-11-25", 2).map((b) => b.slug)).toEqual(["woche", "alt"]);
  });

  it("Lesetipp: Beitrag mit den meisten Orten gewinnt, nur wenn er den Guide einbettet und die Saison läuft", () => {
    expect(lesetippFuer(liste, "weihnachtsmaerkte", "2026-12-01")?.slug).toBe("wm");
    expect(lesetippFuer(liste, "weihnachtsmaerkte", "2027-01-11")?.slug).toBe("launch");
    expect(lesetippFuer(liste, "clubs", "2026-12-01")).toBeNull();
  });

  it("Wochenvorschau fürs Wochenende: Zeitraum muss Fr–So berühren", () => {
    expect(wochenvorschauFuer(liste, "2026-12-04", "2026-12-06")?.slug).toBe("woche");
    expect(wochenvorschauFuer(liste, "2026-11-27", "2026-11-29")?.slug).toBe("alt");
    expect(wochenvorschauFuer(liste, "2026-12-11", "2026-12-13")).toBeNull();
  });

  it("Erwähnt im Magazin: höchstens zwei, neueste zuerst", () => {
    expect(erwaehntIn(liste, "e1").map((b) => b.slug)).toEqual(["woche", "alt"]);
    expect(erwaehntIn(liste, "e2").map((b) => b.slug)).toEqual(["alt"]);
    expect(erwaehntIn(liste, "x")).toEqual([]);
  });
});
