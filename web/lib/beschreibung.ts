// Event-Beschreibungen: längere Texte mit Absätzen und „• “-Listen (aus Veranstalter-Quellen umgeschrieben).
// Für die Detailseite in Blöcke zerlegt, für Teaser, Meta-Description und JSON-LD als kurzer Fließtext.

export type BeschreibungsBlock = { art: "absatz"; zeilen: string[] } | { art: "liste"; punkte: string[] };

const LISTENPUNKT = /^\s*[•\-–*]\s+/;

/** Zerlegt den Text an Leerzeilen in Absätze; Zeilen mit „• “ werden zu Listen. */
export function beschreibungsBloecke(text: string | null | undefined): BeschreibungsBlock[] {
  const bloecke: BeschreibungsBlock[] = [];
  for (const roh of (text ?? "").replace(/\r\n?/g, "\n").split(/\n\s*\n/)) {
    const zeilen = roh.split("\n").map((z) => z.trim()).filter(Boolean);
    let absatz: string[] = [];
    let liste: string[] = [];
    const absatzAbschliessen = () => {
      if (absatz.length) bloecke.push({ art: "absatz", zeilen: absatz });
      absatz = [];
    };
    const listeAbschliessen = () => {
      if (liste.length) bloecke.push({ art: "liste", punkte: liste });
      liste = [];
    };
    for (const zeile of zeilen) {
      if (LISTENPUNKT.test(zeile)) {
        absatzAbschliessen();
        liste.push(zeile.replace(LISTENPUNKT, ""));
      } else {
        listeAbschliessen();
        absatz.push(zeile);
      }
    }
    absatzAbschliessen();
    listeAbschliessen();
  }
  return bloecke;
}

/** Fließtext ohne Umbrüche und Listenzeichen, an einer Wortgrenze gekürzt („…“). */
export function kurzBeschreibung(text: string | null | undefined, max = 160): string | null {
  const flach = (text ?? "")
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .map((z) => z.trim().replace(LISTENPUNKT, ""))
    .filter(Boolean)
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
  if (!flach) return null;
  if (flach.length <= max) return flach;
  const schnitt = flach.slice(0, max - 1);
  const wortgrenze = schnitt.lastIndexOf(" ");
  return `${(wortgrenze > max * 0.6 ? schnitt.slice(0, wortgrenze) : schnitt).replace(/[\s,;:.–-]+$/, "")}…`;
}
