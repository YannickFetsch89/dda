-- einwilligungstexte_2026-11-17-2.sql – DiesDasDüsseldorf
-- Freigegebene Wortlaute der Einwilligungen und Hinweise für Nutzerkonten (Plan 4.4, Schritt 6).
-- Neue Fassung(en), die schriftliche Freigabe des Anwalts holt der Auftraggeber ein. ERZEUGT von web/scripts/einwilligungstexte-sql.mjs
-- aus web/lib/konto/texte.ts – nicht von Hand ändern. Neue Fassungen bekommen eine neue Version (neue Zeile).
--
-- VORAUSSETZUNG: database/konten_2026-11-16.sql ist gelaufen (Tabelle einwilligungstexte existiert).
-- Wiederholbar: Eine schon vorhandene Version wird nicht überschrieben (die Tabelle ist ohnehin unveränderlich).
-- Die Kontrollabfrage am Ende vergleicht jede gespeicherte Fassung mit der Prüfsumme aus dem Code.
-- Erwartet: eine Zeile mit „ok“. Steht dort „FEHLER“, bitte an Claude geben.
--
-- Prüfsummen (SHA-256 über den Text in UTF-8), vom Test tests/konto-texte.test.ts gegen den Code geprüft:
-- sha256 geburtstagsmail-2026-11-2 f254e2b83171f35f08522ebc8ee5ed7242aa3e679ee65ee727db87037206883d

INSERT INTO public.einwilligungstexte (version, art, zweck, sprache, text)
VALUES
    ('geburtstagsmail-2026-11-2', 'geburtstagsmail', 'Einwilligung (d) nach Art. 6 Abs. 1 lit. a DSGVO und § 7 Abs. 2 UWG: Geburtstagsmail (Geburtsdatum ist Pflichtangabe, E16)', 'de',
     'Ich möchte an meinem Geburtstag eine Mail von dies.das bekommen, mit Glückwünschen und Event-Tipps für den Tag. Dafür nutzt dies.das mein Geburtsdatum aus meinem Konto. Ich kann das jederzeit im Konto oder über den Abmeldelink in jeder Mail widerrufen.')
ON CONFLICT (version) DO NOTHING;

-- Kontrolle: Fassung vorhanden und Wortlaut identisch mit dem Code?
WITH erwartet (version, pruefsumme) AS (
    VALUES
    ('geburtstagsmail-2026-11-2', 'f254e2b83171f35f08522ebc8ee5ed7242aa3e679ee65ee727db87037206883d')
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
