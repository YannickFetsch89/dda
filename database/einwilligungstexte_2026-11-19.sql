-- einwilligungstexte_2026-11-19.sql – DiesDasDüsseldorf
-- Freigegebene Wortlaute der Einwilligungen und Hinweise für Nutzerkonten (Plan 4.4, Schritt 6).
-- Neue Fassung(en), die schriftliche Freigabe des Anwalts holt der Auftraggeber ein. ERZEUGT von web/scripts/einwilligungstexte-sql.mjs
-- aus web/lib/konto/texte.ts – nicht von Hand ändern. Neue Fassungen bekommen eine neue Version (neue Zeile).
--
-- VORAUSSETZUNG: database/konten_2026-11-16.sql ist gelaufen (Tabelle einwilligungstexte existiert).
-- Wiederholbar: Eine schon vorhandene Version wird nicht überschrieben (die Tabelle ist ohnehin unveränderlich).
-- Die Kontrollabfrage am Ende vergleicht jede gespeicherte Fassung mit der Prüfsumme aus dem Code.
-- Erwartet: 3 Zeilen mit „ok“. Steht dort „FEHLER“, bitte an Claude geben.
--
-- Prüfsummen (SHA-256 über den Text in UTF-8), vom Test tests/konto-texte.test.ts gegen den Code geprüft:
-- sha256 interessen-2026-11-2 148a07bce6e190c2579ecf09806e94b46328c0e0c74eae7b7a0ac13567bb337a
-- sha256 sensible-events-2026-11-2 e03f22aeb4e48b291712563b73bee47436443721f1178f8a12a06604e72bb8c8
-- sha256 geburtstagsmail-2026-11-3 a71131d3a9cb107703ec45013ca42852d255827fbe350d5657d88aeb849d0c69

INSERT INTO public.einwilligungstexte (version, art, zweck, sprache, text)
VALUES
    ('interessen-2026-11-2', 'personalisierung', 'Einwilligung (a): Interessen speichern und persönliche Vorschläge', 'de',
     'Ich willige ein, dass dies.das meine Antworten in meinem Konto speichert und zusammen mit meiner Merkliste nutzt, um mir passende Events vorzuschlagen. Sensible Events (siehe unten) fließen nie in Empfehlungen ein. Du kannst das jederzeit im Konto widerrufen. Dann werden deine Antworten sofort gelöscht.'),
    ('sensible-events-2026-11-2', 'sensible_events', 'Ausdrückliche Einwilligung (b) nach Art. 9 Abs. 2 lit. a DSGVO: sensible Events im Konto speichern', 'de',
     E'Datenschutz ist uns hier besonders wichtig. Manche Events lassen Rückschlüsse auf sehr persönliche Dinge zu: Gesundheit, Religion oder Weltanschauung, sexuelle Orientierung oder geschlechtliche Identität, politische Meinung, Gewerkschaftszugehörigkeit oder ethnische Herkunft. Merkst du dir solche Events, speichern wir sie ohne deine ausdrückliche Einwilligung nur auf dem Gerät, auf dem du sie gemerkt hast, und nicht in deinem Konto. Auf anderen Geräten siehst du sie dann nicht. Für Empfehlungen und Statistiken nutzen wir sie nie, auch nicht mit Einwilligung.\n\nIch willige ausdrücklich ein, dass dies.das auch solche Events, die ich mir merke, in meinem Konto speichert, damit sie auf allen meinen Geräten verfügbar sind. Du kannst das jederzeit im Konto widerrufen. Dann werden sie aus deinem Konto entfernt.'),
    ('geburtstagsmail-2026-11-3', 'geburtstagsmail', 'Einwilligung (d) nach Art. 6 Abs. 1 lit. a DSGVO und § 7 Abs. 2 UWG: Geburtstagsmail (Geburtsdatum ist Pflichtangabe, E16)', 'de',
     'Ich möchte an meinem Geburtstag eine Mail von dies.das bekommen, mit Glückwünschen und Event-Tipps für den Tag. Dafür nutzt dies.das mein Geburtsdatum aus meinem Konto. Du kannst das jederzeit im Konto oder über den Abmeldelink in jeder Mail widerrufen.')
ON CONFLICT (version) DO NOTHING;

-- Kontrolle: Fassung vorhanden und Wortlaut identisch mit dem Code?
WITH erwartet (version, pruefsumme) AS (
    VALUES
    ('interessen-2026-11-2', '148a07bce6e190c2579ecf09806e94b46328c0e0c74eae7b7a0ac13567bb337a'),
    ('sensible-events-2026-11-2', 'e03f22aeb4e48b291712563b73bee47436443721f1178f8a12a06604e72bb8c8'),
    ('geburtstagsmail-2026-11-3', 'a71131d3a9cb107703ec45013ca42852d255827fbe350d5657d88aeb849d0c69')
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
