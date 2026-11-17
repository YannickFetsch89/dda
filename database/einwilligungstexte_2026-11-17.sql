-- einwilligungstexte_2026-11-17.sql – DiesDasDüsseldorf
-- Freigegebene Wortlaute der Einwilligungen und Hinweise für Nutzerkonten (Plan 4.4, Schritt 6).
-- Vom Anwalt freigegeben (Mitteilung des Auftraggebers vom 17.11.2026). ERZEUGT von web/scripts/einwilligungstexte-sql.mjs
-- aus web/lib/konto/texte.ts – nicht von Hand ändern. Neue Fassungen bekommen eine neue Version (neue Zeile).
--
-- VORAUSSETZUNG: database/konten_2026-11-16.sql ist gelaufen (Tabelle einwilligungstexte existiert).
-- Wiederholbar: Eine schon vorhandene Version wird nicht überschrieben (die Tabelle ist ohnehin unveränderlich).
-- Die Kontrollabfrage am Ende vergleicht jede gespeicherte Fassung mit der Prüfsumme aus dem Code.
-- Erwartet: sechs Zeilen mit „ok“. Steht dort „FEHLER“, bitte an Claude geben.
--
-- Prüfsummen (SHA-256 über den Text in UTF-8), vom Test tests/konto-texte.test.ts gegen den Code geprüft:
-- sha256 mindestalter-2026-11 01fd4fe3b3f03b0727110046edc8997c48a6b2104d36184ec26bc2ba52fd2948
-- sha256 nutzungsbedingungen-2026-11 3a7db2142ae9233e537a28cf61fcca78f263ab8c266bdaa0d6d84e2fc54ba976
-- sha256 interessen-2026-11 95a2bd635403b5d4d1648771047300e233e537a0e7048d58ea1d7649ceaa7a8d
-- sha256 sensible-events-2026-11 568c358c964aa709b2d68d5a39e6c9d33e0dd50fe7dabc3e35d8d607dadd1df2
-- sha256 analyse-hinweis-2026-11 d8d7339acb74d66edaeb5796c0846eb5f3bb5607e7a856ccd13fc090b22c25e5
-- sha256 geburtstagsmail-2026-11 2b09a4d8362648419d27dc3a281f38ee31d23fcb5cfe5c58a03272fb21fe6d32

INSERT INTO public.einwilligungstexte (version, art, zweck, sprache, text)
VALUES
    ('mindestalter-2026-11', 'mindestalter', 'Bestätigung des Mindestalters von 16 Jahren (Registrierung bzw. /konto/willkommen)', 'de',
     'Ich bin mindestens 16 Jahre alt.'),
    ('nutzungsbedingungen-2026-11', 'nutzungsbedingungen', 'Annahme der Nutzungsbedingungen bei der Registrierung', 'de',
     'Mit „Konto anlegen“ akzeptierst du unsere Nutzungsbedingungen (mit Widerrufsbelehrung). Wie wir deine Daten verarbeiten, steht in der Datenschutzerklärung.'),
    ('interessen-2026-11', 'personalisierung', 'Einwilligung (a): Interessen speichern und persönliche Vorschläge', 'de',
     'Ich willige ein, dass dies.das meine Antworten in meinem Konto speichert und zusammen mit meiner Merkliste nutzt, um mir passende Events vorzuschlagen. Sensible Events (siehe unten) fließen nie in Empfehlungen ein. Ich kann das jederzeit im Konto widerrufen. Dann werden meine Antworten sofort gelöscht.'),
    ('sensible-events-2026-11', 'sensible_events', 'Ausdrückliche Einwilligung (b) nach Art. 9 Abs. 2 lit. a DSGVO: sensible Events im Konto speichern', 'de',
     E'Datenschutz ist uns hier besonders wichtig. Manche Events lassen Rückschlüsse auf sehr persönliche Dinge zu: Gesundheit, Religion oder Weltanschauung, sexuelle Orientierung oder geschlechtliche Identität, politische Meinung, Gewerkschaftszugehörigkeit oder ethnische Herkunft. Merkst du dir solche Events, speichern wir sie ohne deine ausdrückliche Einwilligung nur auf dem Gerät, auf dem du sie gemerkt hast, und nicht in deinem Konto. Auf anderen Geräten siehst du sie dann nicht. Für Empfehlungen und Statistiken nutzen wir sie nie, auch nicht mit Einwilligung.\n\nIch willige ausdrücklich ein, dass dies.das auch solche Events, die ich mir merke, in meinem Konto speichert, damit sie auf allen meinen Geräten verfügbar sind. Ich kann das jederzeit im Konto widerrufen. Dann werden sie aus meinem Konto entfernt.'),
    ('analyse-hinweis-2026-11', 'analyse', 'Hinweis (c) auf das Widerspruchsrecht nach Art. 21 Abs. 4 DSGVO zur anonymen Beliebtheits-Zählung', 'de',
     E'Dein Widerspruchsrecht: Wir zählen anonym, wie oft Events gemerkt werden, um zu sehen, was in Düsseldorf beliebt ist (berechtigtes Interesse, Art. 6 Abs. 1 lit. f DSGVO). Wer was gemerkt hat, sieht dabei niemand, und sensible Events zählen nie mit. Du kannst dem jederzeit widersprechen:\n\nMeine Merkliste nicht mitzählen. (Auch später im Konto.)'),
    ('geburtstagsmail-2026-11', 'geburtstagsmail', 'Einwilligung (d) nach Art. 6 Abs. 1 lit. a DSGVO und § 7 Abs. 2 UWG: Geburtstagsmail', 'de',
     'Ich möchte an meinem Geburtstag eine Mail von dies.das bekommen, mit Glückwünschen und Event-Tipps für den Tag. Dafür speichert dies.das mein Geburtsdatum. Ich kann das jederzeit im Konto oder über den Abmeldelink in jeder Mail widerrufen. Dann wird mein Geburtsdatum gelöscht.')
ON CONFLICT (version) DO NOTHING;

-- Kontrolle: Fassung vorhanden und Wortlaut identisch mit dem Code?
WITH erwartet (version, pruefsumme) AS (
    VALUES
    ('mindestalter-2026-11', '01fd4fe3b3f03b0727110046edc8997c48a6b2104d36184ec26bc2ba52fd2948'),
    ('nutzungsbedingungen-2026-11', '3a7db2142ae9233e537a28cf61fcca78f263ab8c266bdaa0d6d84e2fc54ba976'),
    ('interessen-2026-11', '95a2bd635403b5d4d1648771047300e233e537a0e7048d58ea1d7649ceaa7a8d'),
    ('sensible-events-2026-11', '568c358c964aa709b2d68d5a39e6c9d33e0dd50fe7dabc3e35d8d607dadd1df2'),
    ('analyse-hinweis-2026-11', 'd8d7339acb74d66edaeb5796c0846eb5f3bb5607e7a856ccd13fc090b22c25e5'),
    ('geburtstagsmail-2026-11', '2b09a4d8362648419d27dc3a281f38ee31d23fcb5cfe5c58a03272fb21fe6d32')
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
