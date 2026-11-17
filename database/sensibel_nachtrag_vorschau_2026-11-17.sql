-- sensibel_nachtrag_vorschau_2026-11-17.sql – DiesDasDüsseldorf
-- Sensibel-Nachtrag, Teil 1: VORSCHAU (Plan Nutzerkonten 5.8, Schritt 7). NUR LESEND, ändert nichts.
--
-- WARUM: Der Trigger auf events kennzeichnet seit der Migration (konten_2026-11-16.sql) jedes NEUE oder geänderte
-- Event. Events, die schon vorher in der Datenbank standen, sind noch nicht geprüft. Diese Abfrage zeigt, welche
-- vorhandenen Events die Regeln treffen würden – zur Sichtprüfung, bevor Teil 2 sie einträgt.
--
-- Geprüft werden Events ab heute minus 400 Tage (auch mehrtägige mit späterem datum_bis), die noch nicht
-- gekennzeichnet und nicht als Ausnahme bestätigt sind.
--
-- SO GEHT ES WEITER:
--   1. Ergebnis als CSV exportieren oder durchsehen.
--   2. Fehltreffer (z. B. ein Theaterstück mit „Demenz“ im Titel, eine Band namens „SPD“) an Claude geben,
--      mit Titel oder ID. Claude schreibt daraus die Ausnahmen für Teil 2.
--   3. „Im Zweifel sensibel“: Ist unklar, ob ein Treffer sensibel ist, bleibt er gekennzeichnet (Plan 5.8).
--   4. Danach Teil 2 ausführen: sensibel_nachtrag_2026-11-17.sql.
--
-- VORAUSSETZUNG: konten_2026-11-16.sql ist gelaufen. Ausführen im Supabase-SQL-Editor als postgres.

WITH kandidaten AS (
    SELECT e.id,
           e.datum,
           e.titel,
           e.ort,
           e.abgelehnt,
           public.sensibel_grund(e.titel, e.beschreibung, e.ort) AS grund
    FROM public.events e
    WHERE coalesce(e.datum_bis, e.datum) >= current_date - 400
      AND NOT EXISTS (SELECT 1 FROM public.event_sensibel s WHERE s.event_id = e.id)
      AND NOT EXISTS (SELECT 1 FROM public.event_sensibel_ausnahmen a WHERE a.event_id = e.id)
)
SELECT grund,
       count(*) OVER (PARTITION BY grund) AS treffer_je_grund,
       datum,
       titel,
       ort,
       CASE WHEN abgelehnt THEN 'abgelehnt' ELSE '' END AS hinweis,
       id
FROM kandidaten
WHERE grund IS NOT NULL
ORDER BY grund, datum DESC, titel;
