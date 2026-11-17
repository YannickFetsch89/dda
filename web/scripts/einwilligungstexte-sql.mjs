// Erzeugt database/einwilligungstexte_<datum>.sql aus den freigegebenen Wortlauten im Code (Plan Nutzerkonten 4.4).
// Aufruf im Ordner web: node scripts/einwilligungstexte-sql.mjs
// Nur neue Fassungen in eine eigene Datei (die schon ausgeführte bleibt unverändert):
//   node scripts/einwilligungstexte-sql.mjs <kennung> <art> [<art> …]
//   z. B. node scripts/einwilligungstexte-sql.mjs 2026-11-17-2 geburtstagsmail → einwilligungstexte_2026-11-17-2.sql
// Jede Version darf nur in einer Datei stehen (Test tests/konto-texte.test.ts).
// Node lädt die beiden TypeScript-Dateien direkt (Type Stripping, ab Node 23.6). Sie haben deshalb keine Imports.
// Jede Zeile bekommt einen Kommentar mit der SHA-256-Prüfsumme; tests/konto-texte.test.ts vergleicht sie mit dem Code.
import { createHash } from "node:crypto";
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { NACHWEIS_TEXT } from "../lib/konto/texte.ts";
import { TEXTVERSIONEN } from "../lib/konto/konfig.ts";

const [kennung, ...nurArten] = process.argv.slice(2);
const DATUM = kennung ?? "2026-11-17";
const ZIEL = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "database", `einwilligungstexte_${DATUM}.sql`);
for (const a of nurArten) if (!(a in NACHWEIS_TEXT)) throw new Error(`Unbekannte Art: ${a}`);

const sha = (t) => createHash("sha256").update(t, "utf8").digest("hex");
// Zeilenumbrüche nie roh in die Datei schreiben: Beim Kopieren in den SQL-Editor unter Windows werden sie sonst
// zu \r\n, und der gespeicherte Wortlaut weicht vom Code ab (17.11.2026). Daher E'…' mit \n-Escape.
const sqlText = (t) =>
  t.includes("\n") || t.includes("\\")
    ? `E'${t.replaceAll("\\", "\\\\").replaceAll("'", "''").replaceAll("\n", "\\n")}'`
    : `'${t.replaceAll("'", "''")}'`;

const zeilen = Object.entries(NACHWEIS_TEXT)
  .filter(([art]) => !nurArten.length || nurArten.includes(art))
  .map(([art, { zweck, text }]) => ({ art, version: TEXTVERSIONEN[art], zweck, text, pruefsumme: sha(text) }));

const sql = `-- einwilligungstexte_${DATUM}.sql – DiesDasDüsseldorf
-- Freigegebene Wortlaute der Einwilligungen und Hinweise für Nutzerkonten (Plan 4.4, Schritt 6).
-- ${nurArten.length ? "Neue Fassung(en), die schriftliche Freigabe des Anwalts holt der Auftraggeber ein." : "Vom Anwalt freigegeben (Mitteilung des Auftraggebers vom 17.11.2026)."} ERZEUGT von web/scripts/einwilligungstexte-sql.mjs
-- aus web/lib/konto/texte.ts – nicht von Hand ändern. Neue Fassungen bekommen eine neue Version (neue Zeile).
--
-- VORAUSSETZUNG: database/konten_2026-11-16.sql ist gelaufen (Tabelle einwilligungstexte existiert).
-- Wiederholbar: Eine schon vorhandene Version wird nicht überschrieben (die Tabelle ist ohnehin unveränderlich).
-- Die Kontrollabfrage am Ende vergleicht jede gespeicherte Fassung mit der Prüfsumme aus dem Code.
-- Erwartet: ${zeilen.length === 1 ? "eine Zeile" : `${zeilen.length} Zeilen`} mit „ok“. Steht dort „FEHLER“, bitte an Claude geben.
--
-- Prüfsummen (SHA-256 über den Text in UTF-8), vom Test tests/konto-texte.test.ts gegen den Code geprüft:
${zeilen.map((z) => `-- sha256 ${z.version} ${z.pruefsumme}`).join("\n")}

INSERT INTO public.einwilligungstexte (version, art, zweck, sprache, text)
VALUES
${zeilen.map((z) => `    (${sqlText(z.version)}, ${sqlText(z.art)}, ${sqlText(z.zweck)}, 'de',\n     ${sqlText(z.text)})`).join(",\n")}
ON CONFLICT (version) DO NOTHING;

-- Kontrolle: Fassung vorhanden und Wortlaut identisch mit dem Code?
WITH erwartet (version, pruefsumme) AS (
    VALUES
${zeilen.map((z) => `    (${sqlText(z.version)}, ${sqlText(z.pruefsumme)})`).join(",\n")}
)
SELECT e.version,
       t.art,
       t.gueltig_ab,
       CASE
           WHEN t.version IS NULL THEN 'FEHLER: fehlt'
           WHEN encode(sha256(convert_to(t.text, 'UTF8')), 'hex') = e.pruefsumme THEN 'ok'
           ELSE 'FEHLER: Wortlaut weicht vom Code ab'
       END AS ergebnis
FROM erwartet e
LEFT JOIN public.einwilligungstexte t ON t.version = e.version
ORDER BY e.version;
`;

writeFileSync(ZIEL, sql, "utf8");
console.log(`geschrieben: ${ZIEL}`);
if (nurArten.length) {
  for (const z of zeilen) console.log(`  ${z.version}  ${z.pruefsumme.slice(0, 12)}…`);
  process.exit(0); // Reparatur-Datei nur beim vollständigen Lauf
}

// Reparatur: ersetzt gespeicherte Fassungen, deren Wortlaut vom Code abweicht – aber nur, solange noch kein
// Nachweis (einwilligungen) auf sie verweist. Der Schutz-Trigger wird dafür kurz abgeschaltet (nur postgres darf das).
const REPARATUR = join(dirname(ZIEL), `einwilligungstexte_reparatur_${DATUM}.sql`);
const erwartet = zeilen.map((z) => `    (${sqlText(z.version)}, ${sqlText(z.pruefsumme)})`).join(",\n");
const reparatur = `-- einwilligungstexte_reparatur_${DATUM}.sql – DiesDasDüsseldorf
-- ERZEUGT von web/scripts/einwilligungstexte-sql.mjs – nicht von Hand ändern.
--
-- WARUM: Beim ersten Eintragen am 17.11.2026 wichen zwei Fassungen mit Absatz (sensible-events-2026-11,
-- analyse-hinweis-2026-11) vom Code ab. Vermutlich wurden die Zeilenumbrüche beim Kopieren zu Windows-Umbrüchen.
-- Diese Datei schreibt Umbrüche als \\n-Escape, das ist gegen Kopieren unempfindlich.
--
-- WAS PASSIERT (eine Transaktion):
--   1. Der Schutz-Trigger von einwilligungstexte wird kurz abgeschaltet.
--   2. Gelöscht werden NUR Fassungen, deren Wortlaut vom Code abweicht UND auf die noch kein Nachweis verweist
--      (heute gibt es keine Konten, also auch keine Nachweise).
--   3. Die richtigen Fassungen werden eingetragen, der Trigger wieder eingeschaltet.
--   4. Kontrolle: erwartet sechs Zeilen „ok“, Spalte zeilenumbruch_cr überall false.
-- Wiederholbar. Ausführen als postgres im Supabase-SQL-Editor.

BEGIN;

ALTER TABLE public.einwilligungstexte DISABLE TRIGGER einwilligungstexte_schuetzen;

WITH erwartet (version, pruefsumme) AS (
    VALUES
${erwartet}
)
DELETE FROM public.einwilligungstexte t
USING erwartet e
WHERE t.version = e.version
  AND encode(sha256(convert_to(t.text, 'UTF8')), 'hex') <> e.pruefsumme
  AND NOT EXISTS (SELECT 1 FROM public.einwilligungen n WHERE n.textversion = t.version);

INSERT INTO public.einwilligungstexte (version, art, zweck, sprache, text)
VALUES
${zeilen.map((z) => `    (${sqlText(z.version)}, ${sqlText(z.art)}, ${sqlText(z.zweck)}, 'de',\n     ${sqlText(z.text)})`).join(",\n")}
ON CONFLICT (version) DO NOTHING;

ALTER TABLE public.einwilligungstexte ENABLE TRIGGER einwilligungstexte_schuetzen;

COMMIT;

WITH erwartet (version, pruefsumme) AS (
    VALUES
${erwartet}
)
SELECT e.version,
       t.art,
       strpos(t.text, chr(13)) > 0 AS zeilenumbruch_cr,
       CASE
           WHEN t.version IS NULL THEN 'FEHLER: fehlt'
           WHEN encode(sha256(convert_to(t.text, 'UTF8')), 'hex') = e.pruefsumme THEN 'ok'
           ELSE 'FEHLER: Wortlaut weicht vom Code ab'
       END AS ergebnis,
       (SELECT tgenabled <> 'D' FROM pg_trigger WHERE tgname = 'einwilligungstexte_schuetzen') AS schutz_trigger_an
FROM erwartet e
LEFT JOIN public.einwilligungstexte t ON t.version = e.version
ORDER BY e.version;
`;
writeFileSync(REPARATUR, reparatur, "utf8");
console.log(`geschrieben: ${REPARATUR}`);
for (const z of zeilen) console.log(`  ${z.version}  ${z.pruefsumme.slice(0, 12)}…`);
