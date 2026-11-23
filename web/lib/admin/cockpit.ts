// Admin-Bereich – Daten fürs Cockpit (Plan Admin-Dashboard 4.2). Alles parallel, jede Quelle einzeln abgesichert:
// Fällt eine aus, zeigt das Cockpit dort grau statt gar nichts.
import "server-only";
import type { SupabaseClient } from "@supabase/supabase-js";
import { eventPoolLaden } from "../daten";
import { BEREICH_KOPF } from "./konfig";
import { eventLuecken, scraperAmpel, tokenAmpel, workflowAmpel, type Ampel, type EventLuecken, type Farbe } from "./ampeln";
import { letzterLauf } from "./github";
import { warnungenBerechnen, type ErgebnisZeile, type LaufZeile, type Warnung } from "./warnregeln";

export interface Aufgabe {
  schluessel: string;
  titel: string;
  anzahl: number | null;
  farbe: Farbe;
  link: string | null;
  hinweis?: string;
}

export interface CockpitDaten {
  jetzt: string;
  ampeln: Ampel[];
  warnungen: Warnung[];
  aufgaben: Aufgabe[];
  kennzahlen: { eventsHeute: number | null; events7Tage: number | null; neuSeitLauf: number | null; konten: number | null };
  luecken: EventLuecken | null;
}

function website(): string {
  return (process.env.SITE_URL ?? "https://diesdas.events").replace(/\/+$/, "");
}

async function sicher<T>(f: () => Promise<T>, ersatz: T): Promise<T> {
  try {
    return await f();
  } catch (e) {
    console.error("Cockpit-Quelle fehlgeschlagen:", e);
    return ersatz;
  }
}

async function scraperLaden(db: SupabaseClient) {
  const { data: laeufe, error } = await db
    .from("scraper_laeufe")
    .select("id, gestartet_am, beendet_am, status, speicher_fehler, github_run_url")
    .order("gestartet_am", { ascending: false })
    .limit(8);
  if (error) throw new Error(error.message);
  const ids = (laeufe ?? []).map((l) => l.id as string);
  if (!ids.length) return { laeufe: [] as (LaufZeile & { github_run_url: string | null })[], ergebnisse: [] as ErgebnisZeile[] };
  const { data: ergebnisse, error: f2 } = await db
    .from("scraper_ergebnisse")
    .select("lauf_id, quelle, status, anzahl, meldung")
    .in("lauf_id", ids)
    .limit(2000);
  if (f2) throw new Error(f2.message);
  return { laeufe: (laeufe ?? []) as (LaufZeile & { github_run_url: string | null })[], ergebnisse: (ergebnisse ?? []) as ErgebnisZeile[] };
}

/** Antwortet die Website? (robots.txt) */
async function websiteAmpel(): Promise<Ampel> {
  const basis = { schluessel: "website", titel: "Website", link: website(), zeitpunkt: new Date().toISOString() };
  try {
    const r = await fetch(`${website()}/robots.txt`, { cache: "no-store", signal: AbortSignal.timeout(6000) });
    return { ...basis, farbe: r.ok ? "gruen" : "rot", text: r.ok ? "antwortet" : `antwortet mit ${r.status}` };
  } catch {
    return { ...basis, farbe: "grau", text: "Vom Server aus nicht prüfbar." };
  }
}

/**
 * Host-Trennung (Plan 4.2 und 8): Die öffentliche Website muss /admin auch mit selbst gesetztem Admin-Kopf
 * verweigern. Sonst fehlt `proxy_set_header X-DDD-Bereich web;` in nginx. Ob der Server sich selbst über die
 * öffentliche Adresse erreicht, zeigt erst der Betrieb – sonst grau.
 */
async function trennungAmpel(): Promise<Ampel> {
  const basis = { schluessel: "trennung", titel: "Trennung Website/Admin", link: null, zeitpunkt: new Date().toISOString() };
  try {
    const r = await fetch(`${website()}/admin`, {
      headers: { [BEREICH_KOPF]: "admin" },
      redirect: "manual",
      cache: "no-store",
      signal: AbortSignal.timeout(6000),
    });
    return r.status === 404
      ? { ...basis, farbe: "gruen", text: "diesdas.events/admin bleibt gesperrt." }
      : { ...basis, farbe: "rot", text: `diesdas.events/admin antwortet mit ${r.status} – nginx-Kopf auf diesdas.events prüfen!` };
  } catch {
    return { ...basis, farbe: "grau", text: "Vom Server aus nicht prüfbar." };
  }
}

export async function cockpitLaden(db: SupabaseClient): Promise<CockpitDaten> {
  const jetzt = new Date();
  const [scraper, pool, meldungen, vorschlaege, zahlen, deploy, waechter, geburtstag, magazin, web, trennung] = await Promise.all([
    sicher(() => scraperLaden(db), null),
    sicher(() => eventPoolLaden(), null),
    sicher(async () => {
      const { count, error } = await db.from("event_meldungen").select("id", { count: "exact", head: true }).eq("status", "neu");
      if (error) throw new Error(error.message);
      return count ?? 0;
    }, null),
    sicher(async () => {
      const { data, error } = await db.from("admin_vorschlaege").select("art").eq("status", "offen").limit(5000);
      if (error) throw new Error(error.message);
      return (data ?? []).length;
    }, null),
    sicher(async () => {
      const { data, error } = await db.rpc("admin_cockpit_zahlen");
      if (error) throw new Error(error.message);
      return data as { magazin_in_pruefung: number; magazin_naechste: string | null; magazin_entwurf: number; konten: number };
    }, null),
    letzterLauf("deploy"),
    letzterLauf("waechter"),
    letzterLauf("geburtstag"),
    letzterLauf("magazin"),
    websiteAmpel(),
    trennungAmpel(),
  ]);

  const warnungen = scraper ? warnungenBerechnen(scraper.laeufe, scraper.ergebnisse, jetzt) : [];
  const ampeln: Ampel[] = [
    scraper
      ? scraperAmpel(scraper.laeufe, warnungen, jetzt, "/admin/scraper")
      : { schluessel: "scraper", titel: "Scraper-Lauf", farbe: "grau", text: "Protokoll nicht lesbar.", zeitpunkt: null, link: null },
    workflowAmpel("deploy", "Deploy", deploy, jetzt, null),
    // GitHub führt den 15-Minuten-Zeitplan nur alle paar Stunden aus (gemessen 20.–23.11.: Abstände 4–8 h); der
    // eigentliche Wächter ist der Cron auf dem Server. Gelb erst ab 12 Stunden ohne Lauf.
    workflowAmpel("waechter", "Website-Wächter", waechter, jetzt, 12),
    workflowAmpel("geburtstag", "Geburtstagsmails", geburtstag, jetzt, 26),
    workflowAmpel("magazin", "Magazin-Job", magazin, jetzt, 3),
    web,
    trennung,
  ];
  if (pool?.quelle === "beispiel") {
    ampeln.push({ schluessel: "events", titel: "Event-Datenbank", farbe: "rot", text: `Events nicht ladbar: ${pool.fehler}`, zeitpunkt: null, link: null });
  }
  const ablauf = [deploy, waechter, geburtstag, magazin].find((g) => g.art === "ok" && g.tokenAblauf);
  const token = tokenAmpel(ablauf && ablauf.art === "ok" ? ablauf.tokenAblauf : null, jetzt);
  if (token) ampeln.push(token);

  const luecken = pool && pool.quelle === "supabase" ? eventLuecken(pool.events, pool.heute) : null;
  const zweiTage = new Date(jetzt.getTime() + 2 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  const aufgaben: Aufgabe[] = [
    { schluessel: "meldungen", titel: "Offene Meldungen", anzahl: meldungen, farbe: meldungen ? "gelb" : "gruen", link: "/alt/" },
    {
      schluessel: "magazin",
      titel: "Magazin-Entwürfe zur Prüfung",
      anzahl: zahlen?.magazin_in_pruefung ?? null,
      farbe: !zahlen ? "grau" : zahlen.magazin_in_pruefung === 0 ? "gruen" : zahlen.magazin_naechste && zahlen.magazin_naechste <= zweiTage ? "rot" : "gelb",
      link: null,
      hinweis: zahlen?.magazin_naechste ? `nächste Ausgabe ab ${zahlen.magazin_naechste}` : undefined,
    },
    { schluessel: "vorschlaege", titel: "Offene Vorschläge", anzahl: vorschlaege, farbe: vorschlaege ? "gelb" : "gruen", link: null, hinweis: "ab Stufe 1d" },
    {
      schluessel: "tipps",
      titel: "Tage ohne Redaktions-Tipp (14 Tage)",
      anzahl: luecken?.tageOhneTipp.length ?? null,
      farbe: !luecken ? "grau" : luecken.tageOhneTipp.length ? "gelb" : "gruen",
      link: null,
      hinweis: luecken?.tageOhneTipp.length
        ? luecken.tageOhneTipp.slice(0, 5).map((t) => `${t.slice(8, 10)}.${t.slice(5, 7)}.`).join(", ") + (luecken.tageOhneTipp.length > 5 ? " …" : "")
        : undefined,
    },
    { schluessel: "ohne_bild", titel: "Events ohne Bild (7 Tage)", anzahl: luecken?.ohneBild ?? null, farbe: luecken ? (luecken.ohneBild ? "gelb" : "gruen") : "grau", link: null },
    { schluessel: "ohne_stadtteil", titel: "Events ohne Stadtteil (7 Tage)", anzahl: luecken?.ohneStadtteil ?? null, farbe: luecken ? (luecken.ohneStadtteil ? "gelb" : "gruen") : "grau", link: null },
    { schluessel: "ohne_adresse", titel: "Events ohne Adresse (7 Tage)", anzahl: luecken?.ohneAdresse ?? null, farbe: luecken ? (luecken.ohneAdresse ? "gelb" : "gruen") : "grau", link: null },
  ];

  const letzterStart = scraper?.laeufe[0]?.gestartet_am ?? null;
  const neuSeitLauf = pool && letzterStart ? pool.alle.filter((e) => (e.erstellt_am ?? "") >= letzterStart).length : null;

  return {
    jetzt: jetzt.toISOString(),
    ampeln,
    warnungen,
    aufgaben,
    kennzahlen: {
      eventsHeute: luecken?.eventsHeute ?? null,
      events7Tage: luecken?.events7Tage ?? null,
      neuSeitLauf,
      konten: zahlen?.konten ?? null,
    },
    luecken,
  };
}
