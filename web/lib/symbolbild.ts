// Symbolbilder für Events ohne eigenes Foto (siehe docs/fallback-bilder.md).
// Reihenfolge: saisonales Motiv (nur im Zeitfenster) → Motiv per Stichwort im Titel → in der Beschreibung
// → Motiv nach Quelle → Kategorie-Fallback. Es zählen nur Motive, für die es Bilder gibt (lib/symbolbilder.json).
// Die Variante hängt an der Event-ID: zufällig verteilt, aber stabil über Reloads und Server/Client.
import vorhanden from "./symbolbilder.json";
import type { DddEvent } from "./typen";

const ANZAHL: Record<string, number> = vorhanden;

// ---------- Saisonale Motive ----------

/** Ostersonntag (gregorianisch, Gauß/Meeus) als YYYY-MM-DD. */
function ostersonntag(jahr: number): string {
  const a = jahr % 19, b = Math.floor(jahr / 100), c = jahr % 100, d = Math.floor(b / 4), e = b % 4;
  const f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451);
  const monat = Math.floor((h + l - 7 * m + 114) / 31), tag = ((h + l - 7 * m + 114) % 31) + 1;
  return `${jahr}-${String(monat).padStart(2, "0")}-${String(tag).padStart(2, "0")}`;
}

function plus(datum: string, tage: number): string {
  const d = new Date(`${datum}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + tage);
  return d.toISOString().slice(0, 10);
}

/** Liegt MM-DD des Datums im Bereich (Grenzen inklusive)? */
const zwischen = (datum: string, von: string, bis: string) => datum.slice(5) >= von && datum.slice(5) <= bis;

interface Saison {
  motiv: string;
  stichworte: RegExp;
  zeitfenster: (datum: string) => boolean;
}

const SAISON: Saison[] = [
  { motiv: "halloween", stichworte: /hallo?ween|spooky|grusel|samhain|kürbis/i, zeitfenster: (d) => zwischen(d, "10-01", "10-31") },
  { motiv: "sankt-martin", stichworte: /sankt martin|st\.? martin|martinszug|laterne|weckmann/i, zeitfenster: (d) => zwischen(d, "11-01", "11-15") },
  {
    motiv: "karneval",
    stichworte: /karneval|helau|sessionser[öo]ffnung|altweiber|rosenmontag|jeck|prunksitzung|11\.11/i,
    zeitfenster: (d) => zwischen(d, "11-01", "11-15") || (d.slice(5) >= "01-01" && d <= plus(ostersonntag(Number(d.slice(0, 4))), -46)),
  },
  { motiv: "nikolaus", stichworte: /nikolaus/i, zeitfenster: (d) => zwischen(d, "12-01", "12-06") },
  { motiv: "advent-weihnachtsmarkt", stichworte: /weihnachtsmarkt|advent|glühwein|eisbahn|winterwelt/i, zeitfenster: (d) => zwischen(d, "11-15", "12-23") },
  { motiv: "weihnachten", stichworte: /weihnacht|christmas|krippenspiel|christmette|xmas/i, zeitfenster: (d) => zwischen(d, "12-01", "12-26") },
  { motiv: "silvester", stichworte: /silvester|new year|neujahr|jahreswechsel/i, zeitfenster: (d) => zwischen(d, "12-27", "12-31") || zwischen(d, "01-01", "01-01") },
  { motiv: "valentinstag", stichworte: /valentin/i, zeitfenster: (d) => zwischen(d, "02-01", "02-14") },
  {
    motiv: "ostern",
    stichworte: /oster|easter/i,
    zeitfenster: (d) => {
      const o = ostersonntag(Number(d.slice(0, 4)));
      return d >= plus(o, -21) && d <= plus(o, 1);
    },
  },
  {
    motiv: "tanz-in-den-mai",
    stichworte: /tanz in den mai|maifest|maibaum|vatertag|bollerwagen/i,
    zeitfenster: (d) => zwischen(d, "04-25", "05-01") || d === plus(ostersonntag(Number(d.slice(0, 4))), 39),
  },
  { motiv: "nacht-der-museen", stichworte: /nacht der museen|museumsnacht/i, zeitfenster: (d) => zwischen(d, "03-01", "05-31") },
  { motiv: "japan-tag", stichworte: /japan-?tag/i, zeitfenster: (d) => zwischen(d, "05-01", "06-30") },
  { motiv: "csd-pride", stichworte: /\bcsd\b|pride|christopher street/i, zeitfenster: (d) => zwischen(d, "05-01", "08-31") },
  { motiv: "rheinkirmes", stichworte: /kirmes|schützenfest|riesenrad/i, zeitfenster: (d) => zwischen(d, "06-01", "08-31") },
  { motiv: "sommer-openair", stichworte: /open[- ]?air|biergarten|sommerfest|sommerkino/i, zeitfenster: (d) => zwischen(d, "06-01", "08-31") },
  { motiv: "oktoberfest", stichworte: /oktoberfest|wiesn/i, zeitfenster: (d) => zwischen(d, "09-15", "10-15") },
];

// ---------- Ganzjährige Motive (Reihenfolge = Vorrang) ----------

const MOTIVE: [string, RegExp][] = [
  ["speed-dating", /speed ?dating|singles?[- ]?(party|abend|event)|\bdating\b/i],
  ["tanzkurs", /tango|salsa|bachata|kizomba|tanzkurs|swing ?dance|noche de la/i],
  ["laufen", /\brun\b|running|lauftreff|\blauf\b|parkrun|\d+ ?km\b|marathon|jogging/i],
  ["wandern", /\bhike|hiking|wanderung|wandern|day trip|tagesausflug/i],
  ["ballsport", /football|fußball|kicker|cageball|badminton|padel|cricket|volleyball|basketball|tischtennis/i],
  ["fitness-yoga", /yoga|pilates|\bbarre\b|hiit|workout|\bgym\b|meditation|achtsamkeit|fitness/i],
  ["gaming", /gaming|nintendo|switch to play|\bswitch\b|zocken|e-?sport/i],
  ["spieleabend", /game night|board ?game|spieleabend|spielenachmittag|spieletreff|spielezeit|brettspiel|pen (and|&) paper|rollenspiel|werw[öo]lf|botc|escape ?room|eskape|quiz|trivia|billard|\bpool\b|kartenspiel|coffee & games/i],
  ["sprachcafe", /sprachcaf|sprachenabend|language|english (meeting|speaking|conversation)|german (language|conversation|practice)|conversation|stammtisch|bonjour|francophon|discorsi|gesprächsrunde|tandem/i],
  ["tech-meetup", /azure|c\+\+|power bi|\bai\b|\bki\b|ki-|machine learning|\bml\b|\bsql\b|\bdata|agentic|computer vision|\bux\b|wordpress|jimdo|programmier|coding|hackathon|developer|devops|cloud|python|javascript/i],
  ["business-networking", /founder|gründer|startup|business|networking|summit|konferenz|conference|toastmaster|expat|freelancer|unternehmer|webinar|seminar/i],
  ["kinder-geschichten", /geschichtenzeit|vorlese|kamishibai|kuscheltier|bilderbuch|für kinder|kids|familienführung|familientag|lego|beebot/i],
  ["maker-workshop", /3d-|3d druck|bastel|basteln|fablab|repair ?caf|handarbeit|nähen|stricken|häkel|makerspace|musikstudio|librarylab|turing tumble|workshop/i],
  ["bibliothek-beratung", /onleihe|pressreader|filmfriend|sprechstunde|digitalhäppchen|bücherflohmarkt|flohmarkt|verbraucherzentrale|i-punkt|zentrum plus|bürgersprechstunde/i],
  ["lesung-vortrag", /lesung|lesenswert|liest|vortrag|vorlesung|gedichte|poetry|book ?club|lesekreis|bücherclub|reading|lectura|shortstory|creative writing|schreibwerkstatt|stadtschreiben|podiumsdiskussion/i],
  ["comedy", /comedy|stand[- ]?up|kabarett|joke|improv|impro-?theater|slam/i],
  ["fuehrung-ausstellung", /führung|guided tour|public tour|visita guiada|ausstellung|vernissage|finissage|eröffnung|atelier|open studio|kunstgespräch|kuratoren|museum/i],
  ["film", /\bfilm|kino|screening|stummfilm|trickfilm|movie/i],
  ["oper-musiktheater", /\boper\b|opern|zauberflöte|musical|musiktheater|operette|ballett/i],
  ["candlelight-klassik", /candlelight|klassik|sinfonie|symphon|kammermusik|orchester|\btrio\b|quartett|klavierabend|orgel|chor|big band|rezitation|meisterklasse/i],
  ["jazz", /jazz|jam session/i],
  ["clubnacht", /party|rave|club ?night|clubnacht|\bdj\b|techno|house music/i],
  ["live-konzert", /konzert|concert|live\b|tour 20|band/i],
  ["theater", /theater|theatre|schauspiel|bühne|drama|premiere|inszenierung/i],
  ["food-wein", /wein|wine|tasting|dinner|brunch|kulinar|street ?food|essen|kochkurs|potluck/i],
];

// Quellen, deren Events fast immer zu einem Motiv passen
const NACH_QUELLE: Record<string, string> = {
  "Düsseldorfer Schauspielhaus": "theater",
  "FFT Düsseldorf": "theater",
  "Kom(m)ödchen Düsseldorf": "comedy",
  "Filmmuseum Düsseldorf": "film",
  "Deutsche Oper am Rhein": "oper-musiktheater",
  "Tonhalle Düsseldorf": "candlelight-klassik",
  "Jazz-Schmiede Düsseldorf": "jazz",
  "Tanzhaus NRW": "tanz-performance",
  "Kunstpalast Düsseldorf": "fuehrung-ausstellung",
  "Kunsthalle Düsseldorf": "fuehrung-ausstellung",
  "Kunstsammlung NRW (K20/K21)": "fuehrung-ausstellung",
  "NRW-Forum Düsseldorf": "fuehrung-ausstellung",
  "Stadtbüchereien Düsseldorf": "bibliothek-beratung",
};

const gibt = (motiv: string) => (ANZAHL[motiv] ?? 0) > 0;

/** Ermittelt das passende Motiv mit vorhandenen Bildern, sonst null. */
export function symbolMotiv(e: Pick<DddEvent, "titel" | "beschreibung" | "datum" | "quelle_name" | "kategorie">): string | null {
  const titel = e.titel ?? "";
  const text = `${titel} ${e.beschreibung ?? ""}`;

  for (const s of SAISON) if (gibt(s.motiv) && s.zeitfenster(e.datum) && s.stichworte.test(text)) return s.motiv;
  for (const [motiv, re] of MOTIVE) if (gibt(motiv) && re.test(titel)) return motiv;
  for (const [motiv, re] of MOTIVE) if (gibt(motiv) && re.test(text)) return motiv;

  const q = e.quelle_name ? NACH_QUELLE[e.quelle_name] : undefined;
  if (q && gibt(q)) return q;

  const kat = `kat-${e.kategorie}`;
  return gibt(kat) ? kat : null;
}

/** FNV-1a mit Murmur3-Finalizer – stabiler Hash, gleichmäßig auch bei kleinem Modulo. */
function hash(text: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) h = Math.imul(h ^ text.charCodeAt(i), 0x01000193);
  h = Math.imul(h ^ (h >>> 16), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}

/** Pfad des Symbolbilds für ein Event (unabhängig davon, ob es ein eigenes Bild hat), sonst null. */
export function symbolbild(e: Pick<DddEvent, "id" | "titel" | "beschreibung" | "datum" | "quelle_name" | "kategorie">): string | null {
  const motiv = symbolMotiv(e);
  if (!motiv) return null;
  return `/fallback/${motiv}-${(hash(e.id) % ANZAHL[motiv]) + 1}.webp`;
}
