// Admin-Bereich – Warnregeln W1–W7 für die Scraper-Läufe (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.3).
// Reine Funktionen ohne Datenbank. Dieselben Regeln rechnet ab Stufe 1c auch Python (Warn-Mail nach dem Lauf);
// beide prüfen gegen tests/fixtures/lauf_warnungen.json.
//
// Quellen-Status (scraper_ergebnisse.status): ok | leer | saisonal | uebersprungen | fehler
// Lauf-Status (scraper_laeufe.status): laeuft | erfolgreich | fehler

export interface LaufZeile {
  id: string;
  gestartet_am: string;
  beendet_am: string | null;
  status: "laeuft" | "erfolgreich" | "fehler";
  speicher_fehler: number | null;
  /** W7: {Ort: Anzahl} Rausgegangen-Events an direkt abgefragten Häusern ohne Treffer (Plan Quellen-Ausbau 4.5) */
  luecken?: Record<string, number> | null;
}

export interface ErgebnisZeile {
  lauf_id: string;
  quelle: string;
  status: "ok" | "leer" | "saisonal" | "uebersprungen" | "fehler";
  anzahl: number;
  meldung?: string | null;
}

export type Regel = "W1" | "W2" | "W3" | "W4" | "W5" | "W6" | "W7";

export interface Warnung {
  regel: Regel;
  stufe: "rot" | "gelb";
  /** null bei Regeln für den ganzen Lauf (W5, W6) */
  quelle: string | null;
  text: string;
}

const STUNDE_MS = 60 * 60 * 1000;
/** W5: Rhythmus ist alle 3 Tage, ab 4 Tagen ohne Lauf stimmt etwas nicht */
export const LAUF_ALT_TAGE = 4;
/** W5: ein Lauf, der so lange „laeuft“, hängt (CI-Timeout ist 75 min) */
export const LAUF_HAENGT_MINUTEN = 90;
/** W7: ab wie vielen Lücken an einem Ort gewarnt wird (mehr als 3) */
export const LUECKEN_GRENZE = 3;

function median(werte: number[]): number {
  const s = [...werte].sort((a, b) => a - b);
  if (!s.length) return 0;
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/**
 * Warnungen für den Stand `jetzt`. `laeufe` in beliebiger Reihenfolge; die Regeln je Quelle (W1–W4) gelten für den
 * letzten BEENDETEN Lauf (ein laufender zählt dort noch nicht), W5 für den neuesten Lauf überhaupt.
 */
export function warnungenBerechnen(laeufe: LaufZeile[], ergebnisse: ErgebnisZeile[], jetzt: Date): Warnung[] {
  const warnungen: Warnung[] = [];
  const sortiert = [...laeufe].sort((a, b) => b.gestartet_am.localeCompare(a.gestartet_am));
  const neuester = sortiert[0];

  // W5: kein Lauf seit 4 Tagen oder ein Lauf hängt
  if (!neuester) {
    warnungen.push({ regel: "W5", stufe: "rot", quelle: null, text: "Es gibt noch keinen Scraper-Lauf." });
  } else {
    const alterMs = jetzt.getTime() - new Date(neuester.gestartet_am).getTime();
    if (neuester.status === "laeuft" && alterMs > LAUF_HAENGT_MINUTEN * 60 * 1000) {
      warnungen.push({ regel: "W5", stufe: "rot", quelle: null, text: `Der Lauf läuft seit über ${LAUF_HAENGT_MINUTEN} Minuten.` });
    } else if (alterMs > LAUF_ALT_TAGE * 24 * STUNDE_MS) {
      warnungen.push({ regel: "W5", stufe: "rot", quelle: null, text: `Seit über ${LAUF_ALT_TAGE} Tagen kein Scraper-Lauf.` });
    }
  }

  const beendet = sortiert.filter((l) => l.status !== "laeuft");
  const letzter = beendet[0];
  if (!letzter) return warnungen;

  // W6: Speicherfehler im letzten beendeten Lauf
  if ((letzter.speicher_fehler ?? 0) > 0) {
    warnungen.push({ regel: "W6", stufe: "gelb", quelle: null, text: `${letzter.speicher_fehler} Events konnten nicht gespeichert werden.` });
  }

  // W7 (Plan Quellen-Ausbau 4.5): mehr als LUECKEN_GRENZE Rausgegangen-Events an einem Ort, dessen Haus wir direkt
  // abfragen, ohne Treffer der Direktquelle – Hinweis auf eine Lücke im Venue-Scraper. Gelb, keine Mail.
  for (const [ort, anzahl] of Object.entries(letzter.luecken ?? {}).sort(([a], [b]) => a.localeCompare(b))) {
    if (typeof anzahl === "number" && anzahl > LUECKEN_GRENZE) {
      warnungen.push({ regel: "W7", stufe: "gelb", quelle: ort, text: `${anzahl} Termine nur bei Rausgegangen – fehlen im Scraper des Hauses?` });
    }
  }

  // Ergebnisse je Quelle, neueste zuerst (Reihenfolge der beendeten Läufe)
  const position = new Map(beendet.map((l, i) => [l.id, i]));
  const jeQuelle = new Map<string, ErgebnisZeile[]>();
  for (const e of ergebnisse) {
    if (!position.has(e.lauf_id)) continue;
    const liste = jeQuelle.get(e.quelle) ?? [];
    liste.push(e);
    jeQuelle.set(e.quelle, liste);
  }

  for (const [quelle, liste] of [...jeQuelle].sort(([a], [b]) => a.localeCompare(b))) {
    liste.sort((a, b) => position.get(a.lauf_id)! - position.get(b.lauf_id)!);
    const aktuell = liste[0];
    if (aktuell.lauf_id !== letzter.id) continue; // Quelle war im letzten Lauf nicht dabei
    // Im letzten Lauf übersprungen (z. B. im Admin abgeschaltet): keine Regel, auch nicht W4 (Cursor-Prüfung 5b, Befund 2)
    if (aktuell.status === "uebersprungen") continue;
    const frueher = liste.slice(1);

    // W1: Fehler im letzten Lauf
    if (aktuell.status === "fehler") {
      warnungen.push({ regel: "W1", stufe: "rot", quelle, text: aktuell.meldung ? `Fehler: ${aktuell.meldung}` : "Fehler im letzten Lauf." });
    }

    // W2: leer, obwohl in 2 der 3 Läufe davor ok mit Events
    if (aktuell.status === "leer") {
      const gut = frueher.slice(0, 3).filter((e) => e.status === "ok" && e.anzahl > 0).length;
      if (gut >= 2) warnungen.push({ regel: "W2", stufe: "rot", quelle, text: "Keine Events, obwohl die Quelle zuletzt welche hatte." });
    }

    // W3: deutlich weniger als üblich (Median der 5 Läufe davor mit ok/leer, nur ab Median 10)
    if (aktuell.status === "ok") {
      const basis = frueher.filter((e) => e.status === "ok" || e.status === "leer").slice(0, 5).map((e) => e.anzahl);
      const m = median(basis);
      if (basis.length && m >= 10 && aktuell.anzahl < 0.4 * m) {
        warnungen.push({ regel: "W3", stufe: "gelb", quelle, text: `Nur ${aktuell.anzahl} Events statt üblicher ${Math.round(m)}.` });
      }
    }

    // W4: in den letzten 3 zählenden Läufen kein ok (saisonal und uebersprungen zählen nicht)
    const zaehlend = liste.filter((e) => e.status !== "saisonal" && e.status !== "uebersprungen").slice(0, 3);
    if (zaehlend.length === 3 && zaehlend.every((e) => e.status !== "ok")) {
      warnungen.push({ regel: "W4", stufe: "rot", quelle, text: "Seit 3 Läufen ohne Erfolg." });
    }
  }
  return warnungen;
}
