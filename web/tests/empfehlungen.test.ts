// Tests zum Plan docs/plan-empfehlungen-2026-11-13.md, Abschnitt 12 (Stufen, Serien, Fokustag, Plätze, Flaggen)
import { describe, expect, it } from "vitest";
import {
  ZUGPFERD_ORTE,
  amFokustag,
  beliebtAuswahl,
  breite,
  filtern,
  fokustag,
  highlightGilt,
  highlights,
  istHeimspiel,
  istSzene,
  istZugpferdOrt,
  serienErkennen,
  startPlaetze,
  startrasterKlasse,
  stufenKontext,
  topGilt,
  wochenendProgramm,
} from "@/lib/ableitungen";
import { istLanglaeufer, plusTage } from "@/lib/datum";
import type { DddEvent, EventPool } from "@/lib/typen";
import { ev } from "./hilfen";

const HEUTE = "2026-11-12"; // Donnerstag
const BILD = "https://x/bild.jpg";

/** Stufe eines Events, Serien aus `pool` (Standard: nur das Event selbst). */
function stufe(e: DddEvent, pool: DddEvent[] = [e], heute = HEUTE) {
  return breite(e, stufenKontext(pool, heute));
}

/** Event, dessen Fokustag `ziel` ist (ID wird so lange variiert, bis es passt). */
function mitFokustag(teil: Partial<DddEvent> & { id: string }, ziel: string): DddEvent {
  for (let i = 0; i < 2000; i++) {
    const e = ev({ ...teil, id: `${teil.id}-${i}` });
    if (fokustag(e) === ziel) return e;
  }
  throw new Error(`kein Fokustag ${ziel} gefunden`);
}

/** Event, dessen Fokustag nicht in `tage` liegt. */
function ohneFokustagIn(teil: Partial<DddEvent> & { id: string }, tage: string[]): DddEvent {
  for (let i = 0; i < 2000; i++) {
    const e = ev({ ...teil, id: `${teil.id}-${i}` });
    if (!tage.includes(fokustag(e))) return e;
  }
  throw new Error("kein passender Fokustag gefunden");
}

function plaetzeAm(events: DddEvent[], tag: string | null, heute = HEUTE) {
  const k = stufenKontext(events, heute);
  const von = tag ?? heute;
  return startPlaetze(filtern(events, { von, bis: tag ?? plusTage(heute, 6), mitLanglaeufern: true }), k, tag);
}

describe("Sprachhinweis (Abschnitt 5)", () => {
  it("Führung „auf Französisch“ → 0, zweisprachig nicht abgestuft", () => {
    expect(stufe(ev({ id: "f", titel: "Altstadtführung auf Französisch", kategorie: "stadtfuehrung", ort: "Burgplatz" }))).toBe(0);
    expect(stufe(ev({ id: "d", titel: "Altstadtführung auf Deutsch und Englisch", kategorie: "stadtfuehrung", ort: "Burgplatz" }))).toBe(2);
    expect(stufe(ev({ id: "e", titel: "Führung in Englisch und Deutsch", kategorie: "stadtfuehrung", ort: "Burgplatz" }))).toBe(2);
  });

  it("„in englischer Sprache“ → 0; Audioguide im selben Satz nicht, in einem anderen Satz schon", () => {
    const fuehrung = { titel: "Führung durch die Sammlung", kategorie: "kultur" as const, ort: "Stadtmuseum" };
    expect(stufe(ev({ id: "a", ...fuehrung, beschreibung: "Die Führung findet in englischer Sprache statt." }))).toBe(0);
    expect(stufe(ev({ id: "b", ...fuehrung, beschreibung: "Ein Audioguide auf Englisch ist an der Kasse erhältlich." }))).toBe(2);
    expect(stufe(ev({ id: "c", ...fuehrung, beschreibung: "Die Führung ist auf Englisch. Ein Audioguide liegt bereit." }))).toBe(0);
  });

  it("„Audioguide auf Englisch“ in der Beschreibung einer Ausstellung stuft nicht ab", () => {
    expect(stufe(ev({ id: "a", titel: "Ausstellung: Neue Malerei", kategorie: "kultur", ort: "Galerie X", beschreibung: "Die Texte gibt es auf Englisch." }))).toBe(2);
  });

  it("Musik, Film und OmU werden nicht abgestuft; Bandname mit „Language“ auch nicht", () => {
    expect(stufe(ev({ id: "j", titel: "French Jazz Night", kategorie: "musik", ort: "Jazz-Schmiede" }))).toBe(2);
    expect(stufe(ev({ id: "s", titel: "Todo sobre mi madre – auf Spanisch (OmU)", kategorie: "kultur", ort: "Bambi Kino" }))).toBe(2);
    expect(stufe(ev({ id: "f", titel: "Volver – auf Spanisch", kategorie: "kultur", unterkategorie: "film", ort: "Metropol Kino" }))).toBe(2);
    expect(stufe(ev({ id: "l", titel: "The Language of Birds – live", kategorie: "musik", ort: "zakk" }))).toBe(2);
  });
});

describe("Stamm (Abschnitt 3, Schritt 1)", () => {
  it("Sprachcafé und Meetup → 0", () => {
    expect(stufe(ev({ id: "a", titel: "Sprachcafé Englisch", kategorie: "community", ort: "Café Muggel" }))).toBe(0);
    expect(stufe(ev({ id: "b", titel: "Python Meetup Düsseldorf", kategorie: "community", ort: "STARTPLATZ" }))).toBe(0);
  });

  it("Kurse → 0, auch im NRW-Forum; Diskurs und Exkursion nicht", () => {
    expect(stufe(ev({ id: "a", titel: "Reisesprachkurs – Koreanisch", kategorie: "community", ort: "NRW-Forum" }))).toBe(0);
    expect(stufe(ev({ id: "b", titel: "Einsteigerkurs Bouldern", kategorie: "sport", ort: "Bouldergarten" }))).toBe(0);
    expect(stufe(ev({ id: "c", titel: "Diskurs über Stadtplanung", kategorie: "kultur", ort: "Haus der Universität" }))).toBe(2);
    expect(stufe(ev({ id: "d", titel: "Exkursion in den Nordpark", kategorie: "outdoor", ort: "Nordpark" }))).toBe(2);
  });

  it("Beschreibung zählt nur im Satz mit einem Wort für Regelmäßigkeit (ohne Rücksicht auf Großschreibung)", () => {
    expect(stufe(ev({ id: "m", titel: "Move it!", kategorie: "sport", ort: "Hofgarten", beschreibung: "Yoga für alle Generationen, Jeden Mittwoch im Park." }))).toBe(0);
    expect(stufe(ev({ id: "e", titel: "ENGLISH COMEDY NIGHT", kategorie: "kultur", ort: "Pitcher", beschreibung: "Veranstaltet von YogArt. Einlass ab 19 Uhr." }))).toBe(2);
    expect(stufe(ev({ id: "w", titel: "Wanderung im Grafenberger Wald", kategorie: "outdoor", ort: "Grafenberger Wald", beschreibung: "Hier findest du deinen Tandem-Partner fürs Wandern." }))).toBe(2);
    expect(stufe(ev({ id: "s", titel: "Speed tasting", kategorie: "food", ort: "Weinbar Rheinblick", beschreibung: "Wie beim Speed-Dating, nur mit Wein." }))).toBe(2);
    expect(stufe(ev({ id: "a", titel: "AfterWorkOut", kategorie: "sport", ort: "Rheinwiesen", beschreibung: "Workout nach Feierabend mit Musik." }))).toBe(2);
  });

  it("„Repair Café“ und „Speed Dating“ auch mit Leerzeichen → 0", () => {
    expect(stufe(ev({ id: "r", titel: "Repair Café Bilk", kategorie: "community", ort: "Stadtteilladen" }))).toBe(0);
    expect(stufe(ev({ id: "c", titel: "Repair-Cafe Flingern", kategorie: "community", ort: "Stadtteilladen" }))).toBe(0);
    expect(stufe(ev({ id: "s", titel: "Speed Dating 30+", kategorie: "dating", ort: "Bar Alto" }))).toBe(0);
    expect(stufe(ev({ id: "d", titel: "Speed-Dating", kategorie: "dating", ort: "Bar Alto" }))).toBe(0);
    expect(stufe(ev({ id: "m", titel: "Repair-Cafés im Stadtteil", kategorie: "community", ort: "Stadtteilladen" }))).toBe(0);
    expect(stufe(ev({ id: "ab", titel: "Repair Caféabend", kategorie: "community", ort: "Stadtteilladen" }))).toBe(0);
    // Ein Speed-Datingabend ist Speed-Dating – die offene rechte Seite ist gewollt
    expect(stufe(ev({ id: "sa", titel: "Speed-Datingabend 25–35", kategorie: "dating", ort: "Bar Alto" }))).toBe(0);
  });

  it("„Repair Cafeteria“ und „Highspeed Dating“ sind kein Stamm", () => {
    expect(stufe(ev({ id: "r", titel: "Repair Cafeteria – Kunstaktion", kategorie: "kultur", ort: "Atelierhaus" }))).toBe(2);
    expect(stufe(ev({ id: "a", titel: "Repair Caféteria", kategorie: "kultur", ort: "Atelierhaus" }))).toBe(2);
    expect(stufe(ev({ id: "t", titel: "Repair Cafetaria", kategorie: "kultur", ort: "Atelierhaus" }))).toBe(2);
    expect(stufe(ev({ id: "b", titel: "Repair Cafe-teria", kategorie: "kultur", ort: "Atelierhaus" }))).toBe(2);
    expect(stufe(ev({ id: "h", titel: "Highspeed Dating mit KI – Lesung", kategorie: "kultur", ort: "Literaturhaus" }))).toBe(2);
  });

  it("Wöchentliches Yoga → 0", () => {
    expect(stufe(ev({ id: "y", titel: "Yoga im Hofgarten", kategorie: "sport", ort: "Hofgarten" }))).toBe(0);
  });
});

describe("Zugpferd-Orte (Abschnitt 4)", () => {
  const FEHLTREFFER: Record<string, string[]> = {
    tonhalle: ["Denkmal vor dem Restaurant Tonhalle in Düsseldorf Kaiserswerth", "Tonhalle Terrace"],
    "deutsche oper am rhein": ["Treffpunkt Social Night Out … Deutsche Oper am Rhein"],
    "opernhaus düsseldorf": ["Opernhaus Dortmund", "Opernhaus Wuppertal"],
    "kunsthalle düsseldorf": ["G2 Kunsthalle"],
    "psd bank dome": ["Tiefgarage PSD Bank Dome"],
    "capitol theater": ["Capitol Club", "Club im Capitol-Theater", "Capitol Theater - Club Saal"],
  };

  for (const eintrag of ZUGPFERD_ORTE) {
    it(`${eintrag}: Treffer am Anfang, kein Treffer in der Mitte`, () => {
      expect(istZugpferdOrt(eintrag)).toBe(true);
      expect(istZugpferdOrt(`${eintrag} Düsseldorf`)).toBe(true);
      const negativ = FEHLTREFFER[eintrag] ?? [`Treffpunkt vor dem ${eintrag}`];
      for (const ort of negativ) expect(istZugpferdOrt(ort), ort).toBe(false);
    });
  }

  it("Tonhalle → 3, Fehltreffer nicht 3", () => {
    expect(stufe(ev({ id: "a", titel: "Sinfoniekonzert", ort: "Tonhalle" }))).toBe(3);
    expect(stufe(ev({ id: "b", titel: "Sinfoniekonzert", ort: "Tonhalle Düsseldorf" }))).toBe(3);
    expect(stufe(ev({ id: "c", titel: "Führung am Denkmal", ort: "Denkmal vor dem Restaurant Tonhalle in Düsseldorf Kaiserswerth" }))).not.toBe(3);
    expect(stufe(ev({ id: "d", titel: "Afterwork", ort: "Tonhalle Terrace" }))).not.toBe(3);
    expect(stufe(ev({ id: "e", titel: "Clubnacht", ort: "Capitol Theater - Club Saal" }))).not.toBe(3);
  });

  it("Fünf verschiedene Tonhalle-Konzerte in 14 Tagen bleiben 3", () => {
    const konzerte = [0, 2, 5, 9, 13].map((t, i) => ev({ id: `t${i}`, titel: `Konzert Nr. ${i + 1}`, ort: "Tonhalle", datum: plusTage(HEUTE, t) }));
    const k = stufenKontext(konzerte, HEUTE);
    for (const e of konzerte) expect(breite(e, k)).toBe(3);
  });

  it("Rheinkirmes über 10 Tage → 3 (Langläufer, aber Zugpferd-Titel)", () => {
    const kirmes = ev({ id: "k", titel: "Größte Kirmes am Rhein – Rheinkirmes", kategorie: "outdoor", ort: "Rheinwiesen Oberkassel", datum: "2026-07-10", datum_bis: "2026-07-19" });
    expect(istLanglaeufer(kirmes)).toBe(true);
    expect(stufe(kirmes)).toBe(3);
  });

  it("Zugpferd-Titel: Japan-Tag, Nacht der Museen, CSD – nicht „Pride and Prejudice“", () => {
    expect(stufe(ev({ id: "j", titel: "Japan-Tag Düsseldorf/NRW", kategorie: "outdoor", ort: "Rheinuferpromenade" }))).toBe(3);
    expect(stufe(ev({ id: "n", titel: "Nacht der Museen", kategorie: "kultur", ort: "Altstadt" }))).toBe(3);
    expect(stufe(ev({ id: "c", titel: "CSD Düsseldorf – Parade", kategorie: "sonstiges", ort: "Johannes-Rau-Platz" }))).toBe(3);
    expect(stufe(ev({ id: "p", titel: "Pride and Prejudice – Lesung", kategorie: "kultur", ort: "Zentralbibliothek" }))).toBe(2);
  });

  it("Fortuna-Heimspiel → 3, auswärts nicht", () => {
    const heim = ev({ id: "h", titel: "Fortuna Düsseldorf – Hertha BSC", kategorie: "sport", ort: "Düsseldorf" });
    const aus = ev({ id: "a", titel: "Auswärtsspiel: 1. FC Köln – Fortuna Düsseldorf", kategorie: "sport", ort: "RheinEnergieStadion" });
    expect(istHeimspiel(heim)).toBe(true);
    expect(stufe(heim)).toBe(3);
    expect(istHeimspiel(aus)).toBe(false);
    expect(stufe(aus)).not.toBe(3);
  });

  it("Public Viewing und Fanshop in der Arena heben nicht über den Ort auf 3", () => {
    expect(stufe(ev({ id: "pv", titel: "Public Viewing: Deutschland – Spanien", kategorie: "sport", ort: "Merkur Spiel-Arena" }))).toBe(2);
    expect(stufe(ev({ id: "fs", titel: "Fanshop-Verkauf", kategorie: "sport", ort: "PSD Bank Dome" }))).toBe(2);
    expect(stufe(ev({ id: "hs", titel: "Düsseldorfer EG – Kölner Haie", kategorie: "sport", ort: "PSD Bank Dome" }))).toBe(3);
  });

  it("Ausschluss greift auch für Auswärts an der Arena, Schreibvarianten und das Wort nur im Ort; Zugpferd-Titel bleibt 3", () => {
    expect(stufe(ev({ id: "aw", titel: "Auswärtsfahrt nach Köln – Treffpunkt", kategorie: "sport", ort: "Merkur Spiel-Arena" }))).toBe(2);
    expect(stufe(ev({ id: "pv", titel: "Public-Viewing: EM-Finale", kategorie: "sport", ort: "Merkur Spiel-Arena" }))).toBe(2);
    expect(stufe(ev({ id: "fs", titel: "Fan Shop geöffnet", kategorie: "sport", ort: "PSD Bank Dome" }))).toBe(2);
    expect(stufe(ev({ id: "or", titel: "Trikotverkauf", kategorie: "sport", ort: "Merkur Spiel-Arena Fanshop" }))).toBe(2);
    expect(stufe(ev({ id: "kt", titel: "Rheinkirmes Public Viewing", kategorie: "outdoor", ort: "Rheinwiesen Oberkassel" }))).toBe(3);
    expect(stufe(ev({ id: "pz", titel: "PublicViewing EM", kategorie: "sport", ort: "Merkur Spiel-Arena" }))).toBe(2);
    expect(stufe(ev({ id: "p2", titel: "Public  Viewing", kategorie: "sport", ort: "Merkur Spiel-Arena" }))).toBe(2);
  });

  it("„Fan Shopping“ löst den Ausschluss nicht aus, „Fortuna-Fanshop“ schon", () => {
    expect(stufe(ev({ id: "sh", titel: "Fan Shopping Night", kategorie: "sport", ort: "Merkur Spiel-Arena" }))).toBe(3);
    expect(stufe(ev({ id: "ff", titel: "Fortuna-Fanshop: Weihnachtsverkauf", kategorie: "sport", ort: "Merkur Spiel-Arena" }))).toBe(2);
  });

  it("„Republic“ und „profan“ lösen den Ausschluss nicht aus", () => {
    expect(stufe(ev({ id: "rv", titel: "Republic Viewing – Filmabend", kategorie: "kultur", ort: "Capitol Theater" }))).toBe(3);
    expect(stufe(ev({ id: "pf", titel: "Profan shop talk – Lesung", kategorie: "kultur", ort: "Kom(m)ödchen" }))).toBe(3);
  });

  it("Premiere im Kunstpalast → 3; Workshop oder Foyer dort höchstens 2", () => {
    expect(stufe(ev({ id: "p", titel: "Premiere: Lichtspiele", kategorie: "kultur", ort: "Kunstpalast" }))).toBe(3);
    expect(stufe(ev({ id: "w", titel: "Workshop Drucktechnik", kategorie: "kultur", ort: "Kunstpalast" }))).toBe(2);
    expect(stufe(ev({ id: "f", titel: "Foyerkonzert", kategorie: "musik", ort: "Tonhalle" }))).toBe(2);
    expect(stufe(ev({ id: "o", titel: "Einführung zur Premiere", kategorie: "kultur", ort: "Opernhaus Düsseldorf Foyer" }))).toBe(2);
    expect(stufe(ev({ id: "c", titel: "Netzwerkabend", kategorie: "community", ort: "Kunstpalast" }))).toBe(2);
  });
});

describe("Szene und Serien (Abschnitt 3 und 6)", () => {
  it("Jazz-Jam → 1", () => {
    const jam = ev({ id: "j", titel: "Jazz-Jam", kategorie: "musik", ort: "Café Unikat" });
    expect(istSzene(jam)).toBe(true);
    expect(stufe(jam)).toBe(1);
  });

  it("Führung Montag, Dienstag, Mittwoch → alle drei Termine höchstens 1", () => {
    const termine = ["2026-11-16", "2026-11-17", "2026-11-18"].map((d, i) =>
      ev({ id: `f${i}`, titel: "Altstadtführung", kategorie: "stadtfuehrung", ort: "Marktplatz", datum: d }),
    );
    const k = stufenKontext(termine, HEUTE);
    for (const e of termine) expect(breite(e, k)).toBeLessThanOrEqual(1);
  });

  it("Wöchentliche Reihe mit drei Terminen über 14 Tage (Grenzen eingeschlossen) ist Serie, zwei Termine nicht", () => {
    const reihe = [0, 7, 14].map((t, i) => ev({ id: `r${i}`, titel: "Lesekreis am Abend", kategorie: "kultur", ort: `Ort ${i}`, datum: plusTage(HEUTE, t) }));
    const serien = serienErkennen(reihe);
    expect(reihe.every((e) => serien.has(e.id))).toBe(true);
    const zwei = [0, 14].map((t, i) => ev({ id: `z${i}`, titel: "Lesekreis am Abend", kategorie: "kultur", ort: `Ort ${i}`, datum: plusTage(HEUTE, t) }));
    expect(serienErkennen(zwei).size).toBe(0);
    const zuWeit = [0, 8, 15].map((t, i) => ev({ id: `w${i}`, titel: "Lesekreis am Abend", kategorie: "kultur", ort: `Ort ${i}`, datum: plusTage(HEUTE, t) }));
    expect(serienErkennen(zuWeit).size).toBe(0);
  });

  it("Gleicher Ort und gleiche Kategorie in 14 Tagen ist Serie, an Sammelorten nicht", () => {
    const ort = [0, 3, 6].map((t, i) => ev({ id: `o${i}`, titel: `Lesung ${i}`, kategorie: "kultur", ort: "Buchhandlung Müller", datum: plusTage(HEUTE, t) }));
    expect(serienErkennen(ort).size).toBe(3);
    const buecherei = [0, 3, 6].map((t, i) =>
      ev({ id: `b${i}`, titel: `Lesung ${i}`, kategorie: "kultur", ort: "Stadtbüchereien Düsseldorf", datum: plusTage(HEUTE, t) }),
    );
    expect(serienErkennen(buecherei).size).toBe(0);
  });

  it("Feld `reihe` macht ein Event zur Serie", () => {
    const e = ev({ id: "r", titel: "Konzertreihe", ort: "zakk", reihe: { slug: "konzertreihe", titel: "Konzertreihe" } });
    expect(stufe(e)).toBe(1);
  });

  it("Ausstellung über 20 Tage → keine Serie, Stufe 2", () => {
    const a = ev({ id: "a", titel: "Ausstellung: Farbräume", kategorie: "kultur", ort: "Kunstpalast", datum: "2026-11-05", datum_bis: "2026-11-25" });
    expect(serienErkennen([a]).size).toBe(0);
    expect(stufe(a)).toBe(2);
  });
});

describe("Fokustag (Abschnitt 7)", () => {
  const tage = Array.from({ length: 21 }, (_, i) => plusTage("2026-11-05", i));

  it("Ausstellung über 20 Tage: genau ein Fokustag, heute und morgen gerechnet derselbe", () => {
    const a = ev({ id: "aus", titel: "Ausstellung: Farbräume", kategorie: "kultur", ort: "Kunstpalast", datum: "2026-11-05", datum_bis: "2026-11-25", bild_url: BILD });
    expect(fokustag(a)).toBe(fokustag({ ...a }));
    expect(tage.filter((t) => amFokustag(a, t))).toEqual([fokustag(a)]);
  });

  it("Ausstellung, die vor heute begann: am Fokustag Tipp-Kandidat, an anderen Tagen nicht; Fund nur am Fokustag", () => {
    const fokus = "2026-11-14";
    const a = mitFokustag({ id: "aus", titel: "Ausstellung: Farbräume", kategorie: "kultur", ort: "Kunstpalast", datum: "2026-11-05", datum_bis: "2026-11-25", bild_url: BILD }, fokus);
    const konzert = (tag: string, bild: string | null = BILD) => ev({ id: `k-${tag}`, titel: "Konzert", kategorie: "musik", ort: "zakk", datum: tag, bild_url: bild });
    // Am Fokustag Kandidat: gewinnt gegen ein Event ohne Bild
    expect(plaetzeAm([a, konzert(fokus, null)], fokus).tipp?.id).toBe(a.id);
    const anderer = "2026-11-13";
    expect(plaetzeAm([a, konzert(anderer, null)], anderer).tipp?.id).not.toBe(a.id);
    const p = plaetzeAm([a, konzert(anderer)], anderer);
    expect(p.tipp?.id).not.toBe(a.id);
    expect(p.plaetze[3]?.id).not.toBe(a.id);
    // ohne anderes Event: an anderen Tagen kein Tipp
    expect(plaetzeAm([a], anderer).tipp).toBeNull();
  });

  it("Party-Reihe über 30 Tage in nightlife: kein Langläufer, Tipp und Fund nur am Fokustag", () => {
    const fokus = "2026-11-20";
    const party = mitFokustag({ id: "p", titel: "Saturday Club Night", kategorie: "nightlife", ort: "Club X", datum: "2026-11-05", datum_bis: "2026-12-04", uhrzeit: "23:00", bild_url: BILD }, fokus);
    expect(istLanglaeufer(party)).toBe(false);
    expect(plaetzeAm([party], fokus).tipp?.id).toBe(party.id);
    const anderer = "2026-11-21";
    const p = plaetzeAm([party], anderer);
    expect(p.tipp).toBeNull();
    expect(p.plaetze[3]).toBeNull();
  });

  it("Pick groß: mehrtägiges Event außerhalb des Fokustags verliert gegen ein eintägiges derselben Stufe mit Bild", () => {
    const tag = "2026-11-13";
    const party = ohneFokustagIn({ id: "p", titel: "Club Night", kategorie: "nightlife", ort: "Club X", datum: "2026-11-05", datum_bis: "2026-12-04", bild_url: BILD, beschreibung: "x".repeat(100), stadtteil: "Altstadt" }, [tag]);
    const tipp = ev({ id: "t", titel: "Sinfoniekonzert", kategorie: "musik", ort: "Tonhalle", datum: tag, bild_url: BILD });
    const eintaegig = ev({ id: "e", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", datum: tag, bild_url: BILD });
    expect(plaetzeAm([party, tipp, eintaegig], tag).plaetze[0]?.id).toBe("e");
  });
});

describe("Die fünf Plätze (Abschnitt 9)", () => {
  const TAG = "2026-11-13";
  const e = (teil: Partial<DddEvent> & { id: string }) => ev({ datum: TAG, bild_url: BILD, ...teil });

  it("Wöchentliche Jam-Session steht auf Platz 4, nur einmal am Tag; tägliche Führung nicht auf Platz 4", () => {
    const jamA = [0, 7, 14].map((t, i) => e({ id: `ja${i}`, titel: "Jazz-Jam", kategorie: "musik", ort: "Café Unikat", datum: plusTage(TAG, t) }));
    const jamB = [0, 7, 14].map((t, i) => e({ id: `jb${i}`, titel: "Open Stage", kategorie: "musik", ort: "Pitcher", datum: plusTage(TAG, t) }));
    const fuehrung = [-1, 0, 1].map((t, i) => e({ id: `f${i}`, titel: "Altstadtführung", kategorie: "stadtfuehrung", ort: "Marktplatz", datum: plusTage(TAG, t) }));
    const rest = [
      e({ id: "t", titel: "Sinfoniekonzert", kategorie: "musik", ort: "Tonhalle", stadtteil: "Pempelfort" }),
      e({ id: "a", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", stadtteil: "Carlstadt" }),
      e({ id: "b", titel: "Flohmarkt", kategorie: "food", ort: "Aachener Platz", stadtteil: "Bilk" }),
    ];
    const alle = [...jamA, ...jamB, ...fuehrung, ...rest];
    const k = stufenKontext(alle, HEUTE);
    expect(breite(fuehrung[1], k)).toBe(1);
    expect(istSzene(fuehrung[1])).toBe(false);
    const p = plaetzeAm(alle, TAG);
    const gezeigt = [p.tipp, ...p.picks];
    expect(istSzene(p.plaetze[2]!)).toBe(true);
    // dieselbe Jam-Serie höchstens einmal am Tag
    expect(gezeigt.filter((x) => x && x.titel === "Jazz-Jam").length).toBeLessThanOrEqual(1);
    expect(gezeigt.filter((x) => x && x.titel === "Open Stage").length).toBeLessThanOrEqual(1);
    expect(p.plaetze[2]?.id).not.toBe("f1");
  });

  it("Platz 4 ohne Szene-Event: Stufe 2 oder 3, keine nur über die Serie gedeckelte Stufe 1", () => {
    const fuehrung = [-1, 0, 1].map((t, i) => e({ id: `f${i}`, titel: "Altstadtführung", kategorie: "stadtfuehrung", ort: "Marktplatz", datum: plusTage(TAG, t) }));
    const rest = [
      e({ id: "t", titel: "Sinfoniekonzert", kategorie: "musik", ort: "Tonhalle", stadtteil: "Pempelfort" }),
      e({ id: "a", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", stadtteil: "Carlstadt" }),
      e({ id: "b", titel: "Flohmarkt", kategorie: "food", ort: "Aachener Platz", stadtteil: "Bilk" }),
    ];
    const p = plaetzeAm([...fuehrung, ...rest], TAG);
    expect(p.plaetze[2]).toBeNull();
    expect(p.picks.map((x) => x.id)).toContain("f1"); // erst als Fund, nicht auf Platz 4
    expect(p.plaetze[3]?.id).toBe("f1");
  });

  it("Platz 3: ohne anderen Stadtteil rückt die nächste Stufe nach, nicht dieselbe Stufe aus demselben Stadtteil", () => {
    const p = plaetzeAm(
      [
        e({ id: "t", titel: "Sinfoniekonzert", kategorie: "musik", ort: "Tonhalle", stadtteil: "Pempelfort" }),
        e({ id: "a", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", stadtteil: "Carlstadt" }),
        e({ id: "b", titel: "Flohmarkt", kategorie: "food", ort: "Markthalle", stadtteil: "Carlstadt", beschreibung: "x".repeat(100) }),
        e({ id: "j", titel: "Jazz-Jam", kategorie: "musik", ort: "Café Unikat", stadtteil: "Carlstadt" }),
      ],
      TAG,
    );
    expect(p.tipp?.id).toBe("t");
    expect(p.plaetze[0]?.id).toBe("b"); // Platz 2: andere Kategorie, Stufe 2
    expect(p.plaetze[1]?.id).toBe("j"); // Platz 3: kein Stufe-2-Event aus anderem Stadtteil → Stufe 1 ohne Regel
  });

  it("Platz 3: Stufe ≥ 2 aus einem dritten Stadtteil kommt vor Stufe 1", () => {
    const p = plaetzeAm(
      [
        e({ id: "t", titel: "Sinfoniekonzert", kategorie: "musik", ort: "Tonhalle", stadtteil: "Pempelfort" }),
        e({ id: "a", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", stadtteil: "Carlstadt", beschreibung: "x".repeat(100) }),
        e({ id: "c", titel: "Flohmarkt", kategorie: "food", ort: "Aachener Platz", stadtteil: "Bilk" }),
        e({ id: "j", titel: "Jazz-Jam", kategorie: "musik", ort: "Café Unikat", stadtteil: "Flingern", beschreibung: "x".repeat(100) }),
      ],
      TAG,
    );
    expect(p.plaetze[0]?.id).toBe("a");
    expect(p.plaetze[1]?.id).toBe("c");
  });

  it("Platz 3: Stufe 1 mit Bild kommt vor Stufe ≥ 2 aus anderem Stadtteil ohne Bild", () => {
    const p = plaetzeAm(
      [
        e({ id: "t", titel: "Sinfoniekonzert", kategorie: "musik", ort: "Tonhalle", stadtteil: "Pempelfort" }),
        e({ id: "a", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", stadtteil: "Carlstadt" }),
        e({ id: "o", titel: "Flohmarkt", kategorie: "food", ort: "Aachener Platz", stadtteil: "Bilk", bild_url: null }),
        e({ id: "j", titel: "Jazz-Jam", kategorie: "musik", ort: "Café Unikat", stadtteil: "Carlstadt" }),
      ],
      TAG,
    );
    expect(p.plaetze[0]?.id).toBe("a");
    expect(p.plaetze[1]?.id).toBe("j");
  });

  it("Zwei Events mit Ort „Düsseldorf“ dürfen beide in den Plätzen stehen, zwei am selben echten Ort nicht", () => {
    const p = plaetzeAm([e({ id: "a", titel: "Stadtfest", kategorie: "outdoor", ort: "Düsseldorf" }), e({ id: "b", titel: "Lichterlauf", kategorie: "sport", ort: "Düsseldorf" })], TAG);
    expect([p.tipp?.id, ...p.picks.map((x) => x.id)].sort()).toEqual(["a", "b"]);
    const q = plaetzeAm([e({ id: "a", titel: "Konzert A", kategorie: "musik", ort: "zakk" }), e({ id: "b", titel: "Party B", kategorie: "nightlife", ort: "zakk" })], TAG);
    expect(q.picks).toHaveLength(0);
  });

  it("Ohne Bild Stufe 2 gegen mit Bild Stufe 1: das mit Bild gewinnt für Tipp und Picks", () => {
    const jam = e({ id: "j", titel: "Jazz-Jam", kategorie: "musik", ort: "Café Unikat" });
    const ohne = e({ id: "o", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", bild_url: null });
    expect(plaetzeAm([jam, ohne], TAG).tipp?.id).toBe("j");
    const tipp = e({ id: "t", titel: "Sinfoniekonzert", kategorie: "kultur", ort: "Tonhalle" });
    expect(plaetzeAm([jam, ohne, tipp], TAG).plaetze[0]?.id).toBe("j");
  });

  it("Zwei Events derselben Stufe mit Bild: höheres beliebtheit() ohne Flaggen gewinnt", () => {
    const voll = e({ id: "v", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", beschreibung: "x".repeat(100), uhrzeit: "19:00" });
    for (let i = 0; i < 20; i++) {
      const knapp = e({ id: `k${i}`, titel: "Konzert", kategorie: "musik", ort: "zakk" });
      expect(plaetzeAm([knapp, voll], TAG).tipp?.id).toBe("v");
    }
  });

  it("Abgesagtes Event mit Tipp-Flagge → kein Platz", () => {
    const abgesagt = e({ id: "x", titel: "Konzert", ort: "Tonhalle", tipp_des_tages: true, abgesagt: true });
    const p = plaetzeAm([abgesagt, e({ id: "a", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus" })], TAG);
    expect(p.tipp?.id).toBe("a");
    expect(p.picks.map((x) => x.id)).not.toContain("x");
  });

  it("Wöchentliches Yoga mit geltender Tipp-Flagge → Tipp, nie Pick", () => {
    const yoga = e({ id: "y", titel: "Yoga im Hofgarten", kategorie: "sport", ort: "Hofgarten", tipp_des_tages: true });
    const andere = [e({ id: "t", titel: "Sinfoniekonzert", kategorie: "musik", ort: "Tonhalle" }), e({ id: "a", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus" })];
    expect(plaetzeAm([yoga, ...andere], TAG).tipp?.id).toBe("y");
    // Gewinnt eine andere Flagge den Tipp, steht Yoga trotzdem nicht in den Picks
    const konkurrenz = e({ id: "k", titel: "Premiere", kategorie: "kultur", ort: "Schauspielhaus", tipp_des_tages: true });
    const p = plaetzeAm([yoga, konkurrenz, ...andere], TAG);
    expect(p.tipp?.id).toBe("k");
    expect(p.picks.map((x) => x.id)).not.toContain("y");
  });

  it("Geltende Tipp-Flagge ohne Bild gegen Stufe 3 mit Bild → das mit Bild", () => {
    const flagge = e({ id: "f", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", tipp_des_tages: true, bild_url: null });
    const zugpferd = e({ id: "z", titel: "Sinfoniekonzert", kategorie: "musik", ort: "Tonhalle" });
    expect(plaetzeAm([flagge, zugpferd], TAG).tipp?.id).toBe("z");
  });

  it("Zwei geltende Tipp-Flaggen am selben Tag → höhere Stufe, dann beliebtheit() ohne Flaggen", () => {
    const zwei = e({ id: "a", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", tipp_des_tages: true, beschreibung: "x".repeat(100) });
    const drei = e({ id: "b", titel: "Sinfoniekonzert", kategorie: "musik", ort: "Tonhalle", tipp_des_tages: true });
    expect(plaetzeAm([zwei, drei], TAG).tipp?.id).toBe("b");
    const auchZwei = e({ id: "c", titel: "Konzert", kategorie: "musik", ort: "zakk", tipp_des_tages: true });
    expect(plaetzeAm([auchZwei, zwei], TAG).tipp?.id).toBe("a");
  });

  it("Tag, an dem nur Stamm-Events ein Bild haben → kein Tipp, Klasse startraster--ohne-tipp", () => {
    const yoga = e({ id: "y", titel: "Yoga im Hofgarten", kategorie: "sport", ort: "Hofgarten" });
    const ohneBild = e({ id: "o", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", bild_url: null });
    const p = plaetzeAm([yoga, ohneBild], TAG);
    expect(p.tipp).toBeNull();
    expect(startrasterKlasse(p.tipp)).toContain("startraster--ohne-tipp");
    expect(startrasterKlasse(ohneBild)).not.toContain("startraster--ohne-tipp");
    // Platz 2 an einem Tag ohne Tipp: die Kategorie-Regel entfällt
    expect(p.plaetze[0]?.id).toBe("o");
  });

  it("Platz 2 mit Tipp: andere Kategorie als der Tipp", () => {
    const p = plaetzeAm(
      [
        e({ id: "t", titel: "Sinfoniekonzert", kategorie: "musik", ort: "Tonhalle" }),
        e({ id: "m", titel: "Konzert", kategorie: "musik", ort: "zakk", beschreibung: "x".repeat(100) }),
        e({ id: "k", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus" }),
      ],
      TAG,
    );
    expect(p.tipp?.id).toBe("t");
    expect(p.plaetze[0]?.id).toBe("k");
  });

  it("Zeitraum Wochenende: derselbe Ort und dieselbe Serie nur einmal, Fokustag gilt nicht", () => {
    const heute = HEUTE; // Do → Wochenende 13.–15.11.
    const jam = ["2026-11-13", "2026-11-14", "2026-11-15"].map((d, i) => ev({ id: `j${i}`, titel: "Jazz-Jam", kategorie: "musik", ort: `Bar ${i}`, datum: d, bild_url: BILD }));
    const zakk = ["2026-11-13", "2026-11-14"].map((d, i) => ev({ id: `z${i}`, titel: `Konzert ${i}`, kategorie: "musik", ort: "zakk", datum: d, bild_url: BILD }));
    const party = ohneFokustagIn({ id: "p", titel: "Club Night", kategorie: "nightlife", ort: "Club X", datum: "2026-11-01", datum_bis: "2026-11-30", bild_url: BILD }, ["2026-11-13", "2026-11-14", "2026-11-15"]);
    const alle = [...jam, ...zakk, party];
    const k = stufenKontext(alle, heute);
    const p = startPlaetze(filtern(alle, { von: "2026-11-13", bis: "2026-11-15", mitLanglaeufern: true }), k, null);
    const ids = [p.tipp, ...p.picks].map((x) => x!.id);
    expect(ids.filter((id) => id.startsWith("j"))).toHaveLength(1);
    expect(ids.filter((id) => id.startsWith("z"))).toHaveLength(1);
    expect(ids).toContain(party.id);
  });

  it("Zeitraum „Woche“: eine Ausstellung darf Tipp sein, auch wenn ihr Fokustag nicht in der Woche liegt", () => {
    const woche = Array.from({ length: 7 }, (_, i) => plusTage(HEUTE, i));
    const a = ohneFokustagIn({ id: "a", titel: "Ausstellung: Farbräume", kategorie: "kultur", ort: "Kunstpalast", datum: "2026-11-01", datum_bis: "2026-12-20", bild_url: BILD }, woche);
    const k = stufenKontext([a], HEUTE);
    expect(startPlaetze(filtern([a], { von: HEUTE, bis: plusTage(HEUTE, 6), mitLanglaeufern: true }), k, null).tipp?.id).toBe(a.id);
  });
});

describe("Wochenend-Box (wochenendProgramm)", () => {
  const pool = (events: DddEvent[]) => ({ heute: HEUTE, jetzt: `${HEUTE}T10:00:00Z`, events, alle: events, quelle: "beispiel", fehler: null }) as EventPool;
  const WE = ["2026-11-13", "2026-11-14", "2026-11-15"];

  it("Party über 30 Tage mit Uhrzeit nur an ihrem Fokustag, nur wenn der Fr–So ist; ohne Uhrzeit fehlt sie", () => {
    const party = mitFokustag({ id: "p", titel: "Club Night", kategorie: "nightlife", ort: "Club X", datum: "2026-11-01", datum_bis: "2026-11-30", uhrzeit: "23:00", bild_url: BILD }, "2026-11-14");
    const box = wochenendProgramm(pool([party]));
    expect(box.map((t) => t.events.map((x) => x.id))).toEqual([[], [party.id], []]);

    const ausserhalb = ohneFokustagIn({ id: "q", titel: "Club Night", kategorie: "nightlife", ort: "Club X", datum: "2026-11-01", datum_bis: "2026-11-30", uhrzeit: "23:00", bild_url: BILD }, WE);
    expect(wochenendProgramm(pool([ausserhalb])).every((t) => t.events.length === 0)).toBe(true);

    const ohneUhrzeit = { ...party, uhrzeit: null };
    expect(wochenendProgramm(pool([ohneUhrzeit])).every((t) => t.events.length === 0)).toBe(true);
  });

  it("Ausstellung mit Uhrzeit, Start vor dem Wochenende, Fokustag Samstag → am Samstag in der Box", () => {
    const a = mitFokustag({ id: "a", titel: "Ausstellung: Farbräume", kategorie: "kultur", ort: "Kunstpalast", datum: "2026-11-05", datum_bis: "2026-11-25", uhrzeit: "11:00", bild_url: BILD }, "2026-11-14");
    expect(wochenendProgramm(pool([a])).map((t) => t.events.map((x) => x.id))).toEqual([[], [a.id], []]);
  });

  it("Stamm bleibt draußen", () => {
    const yoga = ev({ id: "y", titel: "Yoga im Hofgarten", kategorie: "sport", ort: "Hofgarten", datum: "2026-11-14", uhrzeit: "10:00", bild_url: BILD });
    expect(wochenendProgramm(pool([yoga]))[1].events).toHaveLength(0);
  });
});

describe("„Beliebt“ in der Tagesansicht", () => {
  it("Party-Reihe über 30 Tage in nightlife steht nur am Fokustag in der Liste", () => {
    const fokus = "2026-11-20";
    const party = mitFokustag({ id: "p", titel: "Club Night", kategorie: "nightlife", ort: "Club X", datum: "2026-11-05", datum_bis: "2026-12-04", bild_url: BILD }, fokus);
    const k = stufenKontext([party], HEUTE);
    const liste = (tag: string) => beliebtAuswahl(filtern([party], { von: tag, bis: tag }), [], k, tag).map((x) => x.id);
    expect(liste(fokus)).toEqual([party.id]);
    expect(liste("2026-11-21")).toEqual([]);
    // Kategoriezeilen (bisheriges filtern) zeigen sie weiter an jedem Tag
    expect(filtern([party], { von: "2026-11-21", bis: "2026-11-21" })).toHaveLength(1);
  });

  it("Stamm bleibt draußen, die Liste wird kürzer statt aufzufüllen", () => {
    const yoga = ev({ id: "y", titel: "Yoga im Hofgarten", ort: "Hofgarten", bild_url: BILD });
    const lesung = ev({ id: "l", titel: "Lesung", ort: "Literaturhaus" });
    const k = stufenKontext([yoga, lesung], HEUTE);
    expect(beliebtAuswahl([yoga, lesung], [], k, null).map((x) => x.id)).toEqual(["l"]);
  });
});

describe("Flaggen mit Zeitpunkt (Abschnitt 8)", () => {
  it("Highlight-Flagge älter als sieben Tage → auf der Website ignoriert, Wahrheitswert unverändert", () => {
    const frisch = ev({ id: "f", titel: "Konzert", ort: "zakk", highlight_der_woche: true, highlight_gesetzt_am: "2026-11-06T09:00:00Z" });
    const alt = ev({ id: "a", titel: "Konzert", ort: "zakk", highlight_der_woche: true, highlight_gesetzt_am: "2026-11-05T09:00:00Z" });
    expect(highlightGilt(frisch, HEUTE)).toBe(true); // Tag 7 (06. bis 12.)
    expect(highlightGilt(alt, HEUTE)).toBe(false);
    expect(stufe(frisch)).toBe(3);
    expect(stufe(alt)).toBe(2);
    expect(alt.highlight_der_woche).toBe(true);
  });

  it("Highlight- oder Top-Flagge ohne Zeitpunkt gilt nicht", () => {
    expect(highlightGilt(ev({ id: "h", highlight_der_woche: true }), HEUTE)).toBe(false);
    expect(topGilt(ev({ id: "t", top_event_des_monats: true }), HEUTE)).toBe(false);
  });

  it("Top-Flagge gilt bis Monatsende in Europe/Berlin", () => {
    const top = ev({ id: "t", top_event_des_monats: true, top_gesetzt_am: "2026-11-01T08:00:00Z" });
    expect(topGilt(top, "2026-11-30")).toBe(true);
    expect(topGilt(top, "2026-12-01")).toBe(false);
    // 31.10. 23:30 UTC ist in Berlin schon der 01.11.
    const spaet = ev({ id: "s", top_event_des_monats: true, top_gesetzt_am: "2026-10-31T23:30:00Z" });
    expect(topGilt(spaet, "2026-11-15")).toBe(true);
  });

  it("Tipp-Flagge: bis 7 Tage Laufzeit an jedem Tag, darüber nur am Fokustag", () => {
    const kurz = ev({ id: "k", titel: "Festival", kategorie: "musik", ort: "Festwiese", datum: "2026-11-13", datum_bis: "2026-11-19", tipp_des_tages: true, bild_url: BILD });
    for (const tag of ["2026-11-13", "2026-11-16", "2026-11-19"]) expect(plaetzeAm([kurz], tag).tipp?.id).toBe("k");
    // Genau 8 Tage (13.–20., einschließlich gezählt) gelten schon als lang: Flagge nur am Fokustag
    const acht = ev({ id: "acht", titel: "Festival", kategorie: "musik", ort: "Festwiese", datum: "2026-11-13", datum_bis: "2026-11-20", tipp_des_tages: true, bild_url: BILD });
    const achtTage = Array.from({ length: 8 }, (_, i) => plusTage("2026-11-13", i));
    expect(achtTage.filter((tag) => plaetzeAm([acht], tag).tipp?.id === "acht")).toEqual([fokustag(acht)]);
    const lang = mitFokustag({ id: "l", titel: "Ausstellung", kategorie: "kultur", ort: "Galerie", datum: "2026-11-05", datum_bis: "2027-02-05", tipp_des_tages: true, bild_url: BILD }, "2026-11-20");
    expect(plaetzeAm([lang], "2026-11-20").tipp?.id).toBe(lang.id);
    expect(plaetzeAm([lang], "2026-11-21").tipp).toBeNull();
  });

  it("highlights(): geltende Flagge mit Bild vor dem besten Zugpferd, abgelaufene Flagge zählt nicht", () => {
    const zugpferd = ev({ id: "z", titel: "Sinfoniekonzert", ort: "Tonhalle", datum: "2026-11-14", bild_url: BILD });
    const markiert = ev({ id: "m", titel: "Lesung", kategorie: "kultur", ort: "Literaturhaus", datum: "2026-11-15", bild_url: BILD, highlight_der_woche: true, highlight_gesetzt_am: "2026-11-10T10:00:00Z" });
    const pool = { heute: HEUTE, events: [zugpferd, markiert] } as unknown as EventPool;
    expect(highlights(pool).highlight?.id).toBe("m");
    expect(highlights(pool).top?.id).toBe("z");
    const abgelaufen = { ...markiert, highlight_gesetzt_am: "2026-10-01T10:00:00Z" };
    expect(highlights({ heute: HEUTE, events: [zugpferd, abgelaufen] } as unknown as EventPool).highlight?.id).toBe("z");
  });
});
