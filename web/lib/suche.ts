// Fehlertolerante Event-Suche für /entdecken?q=… (Auftraggeber 18.11.2026).
// „jugendkriche“ fand die Jugendkirche nicht, „veihnachten“ nicht den „Veihnachtsmarkt“: Die Suche verlangte die exakte
// Zeichenfolge. Jetzt gilt wortweise (jedes Suchwort muss passen), Groß-/Kleinschreibung und Umlaute egal,
// mit einfachem Wortstamm („weihnachten“ → „weihnacht“) und einem Tippfehler je Wort (zwei ab 9 Buchstaben).

/** Vergleichsform eines Textes: klein, Umlaute ausgeschrieben, Akzente weg, nur Buchstaben/Ziffern und Leerzeichen. */
export function suchText(text: string): string {
  return text
    .toLowerCase()
    .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
    .normalize("NFKD").replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

/** Wörter der Suche (mindestens 2 Zeichen). */
export function suchWoerter(text: string): string[] {
  return suchText(text).split(" ").filter((w) => w.length >= 2);
}

/** Einfacher Wortstamm: eine typische Endung ab, wenn mindestens 4 Buchstaben bleiben. */
export function wortstamm(w: string): string {
  for (const endung of ["en", "er", "es", "e", "n", "s"]) {
    if (w.endsWith(endung) && w.length - endung.length >= 4) return w.slice(0, -endung.length);
  }
  return w;
}

/** Tippfehler-Abstand (Einfügen, Löschen, Ersetzen, zwei Nachbarn vertauscht); bricht ab, sobald er `max` übersteigt. */
export function tippAbstand(a: string, b: string, max: number): number {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  let vorvor: number[] = [];
  let vor = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const jetzt = [i];
    let zeilenMin = i;
    for (let j = 1; j <= b.length; j++) {
      const kosten = a[i - 1] === b[j - 1] ? 0 : 1;
      let d = Math.min(vor[j] + 1, jetzt[j - 1] + 1, vor[j - 1] + kosten);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d = Math.min(d, vorvor[j - 2] + 1);
      jetzt.push(d);
      if (d < zeilenMin) zeilenMin = d;
    }
    if (zeilenMin > max) return max + 1;
    vorvor = vor;
    vor = jetzt;
  }
  return vor[b.length];
}

/** Passt ein Suchwort zum Text? Erst exakt, dann über den Wortstamm, dann mit Tippfehlern gegen einzelne Wörter. */
function wortPasst(q: string, text: string, woerter: string[]): boolean {
  if (text.includes(q)) return true;
  const stamm = wortstamm(q);
  if (stamm !== q && text.includes(stamm)) return true;
  if (q.length < 5) return false;
  const max = q.length >= 9 ? 2 : 1;
  // Ganzes Wort oder Wortanfang gleicher Länge („jugendkriche“ ≈ „jugendkirche“, „wihnachts“ ≈ „weihnachtsmarkt“)
  return woerter.some((w) => tippAbstand(q, w, max) <= max || (w.length > q.length && tippAbstand(q, w.slice(0, q.length), max) <= max));
}

/** Findet die Suche `suche` im Text? Alle Suchwörter müssen passen; ohne Suchwörter immer ja. */
export function sucheTrifft(heuhaufen: string, suche: string | undefined): boolean {
  const qs = suchWoerter(suche ?? "");
  if (!qs.length) return true;
  const text = suchText(heuhaufen);
  const woerter = text.split(" ");
  return qs.every((q) => wortPasst(q, text, woerter));
}
