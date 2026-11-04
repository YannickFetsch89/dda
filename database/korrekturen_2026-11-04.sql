-- korrekturen_2026-11-04.sql – DiesDasDüsseldorf
-- Einmalige Prüfungen/Korrekturen. Im Supabase SQL Editor Abschnitt für Abschnitt ausführen.


-- ── 1. Alt-Events mit Bildnachweis als Ort ("© Eventim", "Quelle: Reservix") ──
-- Der PRINZ-Scraper ist korrigiert, die Website blendet solche Orte aus.
-- Über den öffentlichen Key ist kein solches Event mehr sichtbar – diese Abfrage zeigt,
-- ob noch (abgelehnte) Reste in der Tabelle liegen:

SELECT ort, abgelehnt, abgesagt, COUNT(*) AS anzahl, MIN(datum) AS von, MAX(datum) AS bis
FROM public.events
WHERE ort LIKE '©%' OR ort ILIKE 'quelle:%'
GROUP BY ort, abgelehnt, abgesagt
ORDER BY anzahl DESC;

-- Falls Zeilen erscheinen: vergangene Reste können gelöscht werden (rein kosmetisch):
-- DELETE FROM public.events
-- WHERE (ort LIKE '©%' OR ort ILIKE 'quelle:%') AND datum < CURRENT_DATE;


-- ── 2. Orte-Slugs: "Café" wurde zu "caf" ──────────────────────────────────────
-- Der alte Slug-Generator hat Akzente verschluckt (Café Hüftgold → caf-hueftgold-…).
-- Gefahrlos, solange die Orte noch nicht aktiv sind (keine öffentlichen URLs).
-- Erst ansehen:

SELECT name, slug,
       regexp_replace(slug, '(^|-)caf(-|$)', '\1cafe\2', 'g') AS neuer_slug
FROM public.orte
WHERE slug ~ '(^|-)caf(-|$)';

-- Dann korrigieren:
-- UPDATE public.orte
-- SET slug = regexp_replace(slug, '(^|-)caf(-|$)', '\1cafe\2', 'g')
-- WHERE slug ~ '(^|-)caf(-|$)' AND aktiv = false;
