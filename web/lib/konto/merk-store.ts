// Merkliste im Browser – Gerätemodus und Kontomodus (Plan 5.4, 5.5, 5.6, 5.8).
// Nur in Client-Komponenten benutzen (greift auf window, localStorage, document.cookie und fetch zu).
//
// Schlüssel in localStorage:
//   ddd-merkliste               Geräteliste (abgemeldet, wie bisher)
//   ddd-merkliste-konto         Spiegel der Konto-Liste (Kontomodus)
//   ddd-merkliste-warteschlange Herz-Klicks, die noch zum Server müssen
//   ddd-merkliste-geraet        Merkungen, die nur auf diesem Gerät liegen dürfen (neutral benannt, E13)
// Kontomodus = Hinweis-Cookie ddd_konto=1 (vom Server gesetzt, Plan 3.2).
import {
  geraetelisteNachUebernahme, herzAntwortEinordnen, herzImKonto, offeneLoeschungen, sichtbareListe,
  uebernahmeEntscheiden, vereinigen, warteschlangeAnwenden, type UebernahmeAntwort, type WarteEintrag,
} from "./merk-logik";

export const SCHLUESSEL = {
  geraet: "ddd-merkliste",
  spiegel: "ddd-merkliste-konto",
  schlange: "ddd-merkliste-warteschlange",
  nurGeraet: "ddd-merkliste-geraet",
  sperre: "ddd-merkliste-sperre",
  hinweis: "ddd-konto-hinweis",
  entfernenOffen: "ddd-merkliste-entfernen-offen",
} as const;
export const MERK_EVENT = "ddd-merkliste-geaendert";
const STATUS_EVENT = "ddd-merkliste-status";

// ── Speicher ─────────────────────────────────────────────────────────────────
function roh(schluessel: string): string | null {
  try {
    return window.localStorage.getItem(schluessel);
  } catch {
    return null;
  }
}
function liste(schluessel: string): string[] {
  try {
    const w = JSON.parse(roh(schluessel) ?? "[]");
    return Array.isArray(w) ? w.filter((x): x is string => typeof x === "string") : [];
  } catch {
    return [];
  }
}
function schlangeLesen(): WarteEintrag[] {
  try {
    const w = JSON.parse(roh(SCHLUESSEL.schlange) ?? "[]");
    return Array.isArray(w)
      ? w.filter((e) => e && (e.op === "merken" || e.op === "entfernen") && typeof e.id === "string")
      : [];
  } catch {
    return [];
  }
}
function schreiben(schluessel: string, wert: unknown[]) {
  try {
    if (wert.length) window.localStorage.setItem(schluessel, JSON.stringify(wert));
    else window.localStorage.removeItem(schluessel);
  } catch {
    // Speicher nicht verfügbar (privater Modus) – Merken bleibt dann wirkungslos
  }
}
const geaendert = () => window.dispatchEvent(new Event(MERK_EVENT));

// ── Kontomodus (Hinweis-Cookie) ──────────────────────────────────────────────
export function kontomodus(): boolean {
  return /(?:^|;\s*)ddd_konto=1(?:;|$)/.test(document.cookie);
}
export function angemeldetOhneAlter(): boolean {
  return /(?:^|;\s*)ddd_konto=0(?:;|$)/.test(document.cookie);
}
function hinweisSetzen(wert: "0" | null) {
  const secure = location.protocol === "https:" ? "; Secure" : "";
  document.cookie = wert === null
    ? `ddd_konto=; Path=/; Max-Age=0; SameSite=Lax${secure}`
    : `ddd_konto=${wert}; Path=/; Max-Age=${30 * 24 * 3600}; SameSite=Lax${secure}`;
}

// ── Snapshot für useSyncExternalStore ────────────────────────────────────────
let cache: { schluessel: string; liste: string[] } = { schluessel: "", liste: [] };
export function merkSnapshot(): string[] {
  const k = kontomodus();
  const s = [
    k ? "1" : "0", roh(SCHLUESSEL.geraet), roh(SCHLUESSEL.spiegel), roh(SCHLUESSEL.schlange), roh(SCHLUESSEL.nurGeraet),
    roh(SCHLUESSEL.entfernenOffen),
  ].join("|");
  if (s !== cache.schluessel) {
    const sichtbar = sichtbareListe({
      kontomodus: k,
      geraet: liste(SCHLUESSEL.geraet),
      spiegel: liste(SCHLUESSEL.spiegel),
      schlange: schlangeLesen(),
      nurGeraet: liste(SCHLUESSEL.nurGeraet),
    });
    // Offene Löschungen eines früheren Abmeldens im Konto nicht wieder anzeigen
    const offen = k ? liste(SCHLUESSEL.entfernenOffen) : [];
    cache = { schluessel: s, liste: offen.length ? sichtbar.filter((id) => !offen.includes(id)) : sichtbar };
  }
  return cache.liste;
}
export function merkAbonnieren(callback: () => void) {
  window.addEventListener(MERK_EVENT, callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener(MERK_EVENT, callback);
    window.removeEventListener("storage", callback);
  };
}

// ── Status für die Oberfläche (Nachfrage, Meldungen) ─────────────────────────
export interface MerkStatus {
  /** IDs, die nur auf dem Gerät liegen und nach Nachfrage übernommen oder verworfen werden (5.4 Schritt 3) */
  nachfrage: string[];
  meldung: string | null;
  /** nach drei Fehlschlägen hintereinander (5.5) */
  nichtGespeichert: boolean;
}
let status: MerkStatus = { nachfrage: [], meldung: null, nichtGespeichert: false };
function statusSetzen(teil: Partial<MerkStatus>) {
  status = { ...status, ...teil };
  window.dispatchEvent(new Event(STATUS_EVENT));
}
export const statusSnapshot = () => status;
export const STATUS_LEER: MerkStatus = { nachfrage: [], meldung: null, nichtGespeichert: false };
export function statusAbonnieren(callback: () => void) {
  window.addEventListener(STATUS_EVENT, callback);
  return () => window.removeEventListener(STATUS_EVENT, callback);
}

// ── Sperre über alle Tabs (5.4 Schritt 0) ────────────────────────────────────
async function mitSperre(arbeit: () => Promise<void>): Promise<void> {
  if (typeof navigator !== "undefined" && navigator.locks?.request) {
    try {
      await navigator.locks.request("ddd-merkliste", { signal: AbortSignal.timeout(30_000) }, arbeit);
    } catch {
      // Nach 30 s ohne Sperre tut dieser Tab nichts; der nächste Auslöser versucht es erneut
    }
    return;
  }
  // Ersatz ohne Web Locks: Merker mit Zufalls-Token und 30 s Ablauf. Hält ein anderer Tab ihn, wartet dieser Tab
  // bis zum Ablauf und versucht es genau einmal erneut (Plan 5.4 Schritt 0), danach gibt er auf.
  const token = Math.random().toString(36).slice(2);
  const merkerLesen = () => JSON.parse(roh(SCHLUESSEL.sperre) ?? "null") as { token: string; bis: number } | null;
  let erhalten = false;
  for (let versuch = 0; versuch < 2 && !erhalten; versuch++) {
    try {
      const vorhanden = merkerLesen();
      if (vorhanden && vorhanden.bis > Date.now() && vorhanden.token !== token) {
        if (versuch === 1) return;
        await new Promise((fertig) => setTimeout(fertig, Math.min(30_000, vorhanden.bis - Date.now()) + 50));
        continue;
      }
      window.localStorage.setItem(SCHLUESSEL.sperre, JSON.stringify({ token, bis: Date.now() + 30_000 }));
      erhalten = merkerLesen()?.token === token;
    } catch {
      return;
    }
  }
  if (!erhalten) return;
  try {
    await arbeit();
  } finally {
    try {
      if ((JSON.parse(roh(SCHLUESSEL.sperre) ?? "null") as { token: string } | null)?.token === token) {
        window.localStorage.removeItem(SCHLUESSEL.sperre);
      }
    } catch {
      // ignorieren
    }
  }
}

async function abruf(pfad: string, init: RequestInit = {}): Promise<{ status: number | null; daten: Record<string, unknown> }> {
  try {
    const r = await fetch(pfad, { ...init, signal: AbortSignal.timeout(15_000), credentials: "same-origin" });
    let daten: Record<string, unknown> = {};
    try {
      daten = await r.json();
    } catch {
      // kein JSON
    }
    return { status: r.status, daten };
  } catch {
    return { status: null, daten: {} };
  }
}
const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

// ── Abmelden lokal (401, Abmelden, 403 ohne Alter): nichts geht verloren (5.5, 5.6) ──
// „merken“ aus der Warteschlange landet auf der Geräteliste. Ein noch nicht gesendetes „entfernen“ wird als
// offene Löschung gemerkt und beim nächsten Anmelden auf diesem Gerät nachgeschickt; bis dahin blendet die
// Konto-Ansicht diese IDs aus (Cursor-Prüfung 16.11.2026, Befund 2).
export function lokalAbmelden(ohneAlter = false) {
  const schlange = schlangeLesen();
  schreiben(SCHLUESSEL.geraet, warteschlangeAnwenden(liste(SCHLUESSEL.geraet), schlange));
  schreiben(SCHLUESSEL.entfernenOffen, vereinigen(liste(SCHLUESSEL.entfernenOffen), offeneLoeschungen(schlange)));
  schreiben(SCHLUESSEL.schlange, []);
  schreiben(SCHLUESSEL.spiegel, []);
  hinweisSetzen(ohneAlter ? "0" : null);
  statusSetzen({ nachfrage: [], nichtGespeichert: false });
  geaendert();
}

/** Offene Löschungen eines früheren Abmeldens in die Warteschlange legen (nur im Kontomodus). */
function offeneLoeschungenEinreihen() {
  const offen = liste(SCHLUESSEL.entfernenOffen);
  if (!offen.length || !kontomodus()) return;
  const jetzt = Date.now();
  schreiben(SCHLUESSEL.schlange, [...schlangeLesen(), ...offen.map((id, i) => ({ op: "entfernen" as const, id, zeit: jetzt + i }))]);
  schreiben(SCHLUESSEL.entfernenOffen, []);
  geaendert();
}

/**
 * Abmelden über den Knopf (Plan 5.6, Cursor-Prüfung 16.11.2026, Befund 1): erst die Warteschlange senden, solange
 * die Sitzung gilt, dann den Server abmelden. Lokal abgemeldet wird nur, wenn der Server das bestätigt (oder die
 * Sitzung ohnehin nicht mehr gilt). Sonst bleibt alles, wie es ist, und die Oberfläche meldet den Fehler.
 */
export async function abmelden(ueberall: boolean): Promise<boolean> {
  if (kontomodus()) await mitSperre(schlangeSenden);
  const r = await abruf("/api/konto/abmelden", json({ ueberall }));
  if (r.status === 200 || r.status === 401 || r.status === 404) {
    lokalAbmelden();
    return true;
  }
  return false;
}

// ── Herz ─────────────────────────────────────────────────────────────────────
/** Herz-Klick. Gibt zurück, ob danach gemerkt ist. */
export function merkenUmschalten(id: string): boolean {
  const nurGeraet = liste(SCHLUESSEL.nurGeraet);
  const warGemerkt = merkSnapshot().includes(id);
  if (nurGeraet.includes(id)) {
    // Liegt nur auf diesem Gerät: lokal entfernen; ein Löschauftrag an den Server schadet nicht
    schreiben(SCHLUESSEL.nurGeraet, nurGeraet.filter((x) => x !== id));
    if (kontomodus()) schreiben(SCHLUESSEL.schlange, [...schlangeLesen(), { op: "entfernen", id, zeit: Date.now() }]);
  } else if (kontomodus()) {
    const { schlange } = herzImKonto(liste(SCHLUESSEL.spiegel), schlangeLesen(), id, Date.now());
    schreiben(SCHLUESSEL.schlange, schlange);
  } else {
    const g = liste(SCHLUESSEL.geraet);
    schreiben(SCHLUESSEL.geraet, g.includes(id) ? g.filter((x) => x !== id) : [...g, id]);
    // Abgemeldet neu gemerkt: eine offene Löschung derselben ID gilt nicht mehr
    if (!g.includes(id)) schreiben(SCHLUESSEL.entfernenOffen, liste(SCHLUESSEL.entfernenOffen).filter((x) => x !== id));
  }
  geaendert();
  if (kontomodus()) void abarbeiten();
  return !warGemerkt;
}

// ── Arbeiter: Warteschlange in Reihenfolge an den Server (5.5) ───────────────
let laeuft = false;
let letzterFehler = 0;
let fehlerInFolge = 0;

async function schlangeSenden(): Promise<void> {
  for (;;) {
    const schlange = schlangeLesen();
    const e = schlange[0];
    if (!e || !kontomodus()) return;
    const r = await abruf(`/api/konto/merkliste/${encodeURIComponent(e.id)}`, { method: e.op === "merken" ? "PUT" : "DELETE" });
    const art = herzAntwortEinordnen(r.status, r.daten.code as string | undefined, r.daten.gespeichert as string | undefined);
    if (art.art === "spaeter") {
      letzterFehler = Date.now();
      fehlerInFolge += 1;
      if (fehlerInFolge >= 3) statusSetzen({ nichtGespeichert: true });
      return;
    }
    fehlerInFolge = 0;
    if (status.nichtGespeichert) statusSetzen({ nichtGespeichert: false });
    if (art.art === "abgemeldet") return lokalAbmelden();
    if (art.art === "mindestalter") return lokalAbmelden(true);

    // Eintrag erledigt (ok oder verworfen) – erst jetzt aus der Schlange nehmen
    const rest = schlangeLesen();
    const i = rest.findIndex((x) => x.id === e.id && x.op === e.op && x.zeit === e.zeit);
    if (i >= 0) rest.splice(i, 1);
    if (art.art === "ok") {
      const spiegel = liste(SCHLUESSEL.spiegel).filter((x) => x !== e.id);
      if (e.op === "merken" && art.gespeichert === "geraet") {
        schreiben(SCHLUESSEL.nurGeraet, vereinigen(liste(SCHLUESSEL.nurGeraet), [e.id]));
        schreiben(SCHLUESSEL.spiegel, spiegel);
      } else {
        schreiben(SCHLUESSEL.spiegel, e.op === "merken" ? [...spiegel, e.id] : spiegel);
      }
    }
    schreiben(SCHLUESSEL.schlange, rest);
    geaendert();
  }
}

export async function abarbeiten(): Promise<void> {
  if (laeuft || !kontomodus() || !schlangeLesen().length) return;
  if (Date.now() - letzterFehler < 10_000) return;
  laeuft = true;
  try {
    await mitSperre(schlangeSenden);
  } finally {
    laeuft = false;
  }
}

// ── Abgleich mit dem Konto (5.5): beim Öffnen der Merkliste und beim Fokus, höchstens alle 60 s ──
let letzterAbgleich = 0;
async function spiegelLaden(): Promise<string[] | null> {
  const r = await abruf("/api/konto/merkliste");
  if (r.status === 401) {
    lokalAbmelden();
    return null;
  }
  if (r.status === 403 && r.daten.code === "mindestalter_fehlt") {
    lokalAbmelden(true);
    return null;
  }
  if (r.status !== 200 || !Array.isArray(r.daten.ids)) return null;
  const ids = (r.daten.ids as unknown[]).filter((x): x is string => typeof x === "string");
  schreiben(SCHLUESSEL.spiegel, ids);
  geaendert();
  return ids;
}
export async function abgleichen(sofort = false): Promise<void> {
  if (!kontomodus()) return;
  if (!sofort && Date.now() - letzterAbgleich < 60_000) return;
  letzterAbgleich = Date.now();
  await spiegelLaden();
  void abarbeiten();
}

// ── Übernahme der Geräteliste (5.4) ──────────────────────────────────────────
async function uebernahmeSenden(ids: string[]): Promise<UebernahmeAntwort | null> {
  const r = await abruf("/api/konto/merkliste/uebernehmen", json({ ids }));
  if (r.status === 401) {
    lokalAbmelden();
    return null;
  }
  if (r.status === 403 && r.daten.code === "mindestalter_fehlt") {
    lokalAbmelden(true);
    return null;
  }
  if (r.status === 413) {
    statusSetzen({ meldung: "Zu viele Einträge auf diesem Gerät." });
    return null;
  }
  if (r.status !== 200) return null;
  const a = r.daten as unknown as UebernahmeAntwort;
  // Geräteliste nur um das Nachgewiesene kürzen (Schritt 8)
  const neu = geraetelisteNachUebernahme(liste(SCHLUESSEL.geraet), liste(SCHLUESSEL.nurGeraet), a);
  schreiben(SCHLUESSEL.geraet, neu.geraet);
  schreiben(SCHLUESSEL.nurGeraet, neu.nurGeraet.filter((id) => !a.konto.includes(id)));
  schreiben(SCHLUESSEL.spiegel, a.konto);
  geaendert();
  const n = a.uebernommen;
  const draussen = a.nicht_uebernommen.length;
  statusSetzen({
    nachfrage: [],
    meldung:
      (n ? `${n} ${n === 1 ? "Event" : "Events"} von diesem Gerät übernommen.` : "") +
      (draussen ? ` ${draussen} passen nicht mehr ins Konto (höchstens 500) und bleiben auf diesem Gerät.` : "") || null,
  });
  return a;
}

/**
 * Nach dem Anmelden bzw. beim Seitenaufruf im Kontomodus (5.4 Schritte 1–3): automatisch in ein Konto, das nie
 * eine Merkliste hatte, sonst Nachfrage. Danach die Warteschlange (Schritt 9: Herz-Klicks erst nach der Übernahme).
 */
export async function uebernahmePruefen(): Promise<void> {
  if (!kontomodus()) return;
  await mitSperre(async () => {
    offeneLoeschungenEinreihen();
    const geraet = liste(SCHLUESSEL.geraet);
    const konto = await spiegelLaden();
    if (konto === null) return;
    if (geraet.length) {
      const ich = await abruf("/api/konto/ich");
      if (ich.status !== 200) return;
      const e = uebernahmeEntscheiden(geraet, konto, (ich.daten.merkliste_begonnen_am as string | null) ?? null);
      if (e.art === "automatisch") await uebernahmeSenden(geraet);
      else if (e.art === "nachfrage") statusSetzen({ nachfrage: e.nurAufGeraet });
      else {
        // Alles liegt schon im Konto – nachweislich, also darf es vom Gerät
        schreiben(SCHLUESSEL.geraet, []);
        geaendert();
      }
    }
    await schlangeSenden();
  });
}

/** Button „Ins Konto übernehmen“ (5.4 Schritt 4). */
export async function nachfrageUebernehmen(): Promise<void> {
  await mitSperre(async () => {
    await uebernahmeSenden(liste(SCHLUESSEL.geraet));
    await schlangeSenden();
  });
}

/** Button „Auf diesem Gerät verwerfen“: nur die gefragten IDs vom Gerät löschen. */
export function nachfrageVerwerfen(ids: string[]) {
  schreiben(SCHLUESSEL.geraet, liste(SCHLUESSEL.geraet).filter((id) => !ids.includes(id)));
  statusSetzen({ nachfrage: [] });
  geaendert();
}

/** Einwilligung (b) erteilt: lokal gehaltene Events einmal hochladen (5.8). */
export async function nurGeraetHochladen(): Promise<void> {
  const ids = liste(SCHLUESSEL.nurGeraet);
  if (!ids.length || !kontomodus()) return;
  await mitSperre(async () => {
    const r = await abruf("/api/konto/merkliste/uebernehmen", json({ ids }));
    if (r.status !== 200) return;
    const a = r.daten as unknown as UebernahmeAntwort;
    schreiben(SCHLUESSEL.nurGeraet, liste(SCHLUESSEL.nurGeraet).filter((id) => !a.konto.includes(id) && !a.ungueltig.includes(id)));
    schreiben(SCHLUESSEL.spiegel, a.konto);
    geaendert();
  });
}

/** Einwilligung (b) widerrufen: zurückgegebene IDs bleiben auf diesem Gerät (5.8). */
export function zurueckAufsGeraet(ids: string[]) {
  if (!ids.length) return;
  schreiben(SCHLUESSEL.nurGeraet, vereinigen(liste(SCHLUESSEL.nurGeraet), ids));
  schreiben(SCHLUESSEL.spiegel, liste(SCHLUESSEL.spiegel).filter((id) => !ids.includes(id)));
  geaendert();
}

/** Status-Meldung schließen. */
export const meldungSchliessen = () => statusSetzen({ meldung: null });

/** Anzahl der IDs, die nur in der Geräteliste stehen (für Hinweise). */
export const geraeteAnzahl = () => liste(SCHLUESSEL.geraet).length;
