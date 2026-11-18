-- datenfehler_2026-11-18.sql – DiesDasDüsseldorf
-- Korrekturen aus der Bestandsaufnahme für die Ortsseiten (Plan docs/plan-locations-2026-11-18.md, Abschnitt 6).
--
-- REIHENFOLGE (alle drei im Supabase-SQL-Editor als postgres, nicht während eines Pipeline-Laufs):
--   1. database/gebiet_bereinigung_2026-11-18.sql   – löscht Events außerhalb von Düsseldorf/Neuss/Ratingen
--   2. diese Datei                                   – Adressen und Stadtteile korrigieren
--   3. database/ortsnamen_2026-11-18.sql            – Namensvarianten vereinheitlichen
-- Wiederholbar. Die Pipeline schreibt die Fehler ab dem nächsten Deploy nicht mehr (Scraper korrigiert).

BEGIN;

-- 1) Meetup: Platzhalter-Postleitzahlen („meetup9“, „meetup162“) aus den Adressen entfernen
UPDATE public.events
   SET adresse = nullif(btrim(regexp_replace(regexp_replace(adresse, '\s*meetup\d+', '', 'gi'), '\s{2,}', ' ', 'g'), ' ,'), '')
 WHERE adresse ~* 'meetup\d+';

-- 2) Kulturschlachthof R25: richtige Adresse (Rather Straße 25, Derendorf) statt der des Stahlwerks
UPDATE public.events
   SET adresse = 'Rather Straße 25, 40476 Düsseldorf',
       stadtteil = 'Derendorf'
 WHERE ort IN ('R25 Kulturschlachthof', 'Kulturschlachthof R25', 'R25-Kulturschlachthof', 'R25 - Kulturschlachthof');

-- 3) Deutsche Oper am Rhein: Die Opern-Adresse galt bisher für jeden Spielort. Richtig ist sie nur im Opernhaus.
--    (Duisburger Spielorte sind nach Schritt 1 schon gelöscht.)
UPDATE public.events
   SET adresse = 'Schulstraße 11, 40213 Düsseldorf', stadtteil = 'Altstadt'
 WHERE quelle_name = 'Deutsche Oper am Rhein' AND ort = 'Maxhaus' AND adresse ILIKE 'Heinrich-Heine-Allee 16%';

UPDATE public.events
   SET adresse = NULL, stadtteil = 'Rath'
 WHERE quelle_name = 'Deutsche Oper am Rhein' AND ort ILIKE 'UFO am Rather Carr%';

UPDATE public.events
   SET adresse = NULL, stadtteil = NULL
 WHERE quelle_name = 'Deutsche Oper am Rhein'
   AND adresse ILIKE 'Heinrich-Heine-Allee 16%'
   AND ort NOT ILIKE '%Opernhaus Düsseldorf%'
   AND ort <> 'Deutsche Oper am Rhein';

COMMIT;

-- Kontrolle: alle Zeilen 0 bzw. wie erwartet
SELECT 'meetup-Platzhalter übrig' AS pruefung, count(*)::text AS wert FROM public.events WHERE adresse ~* 'meetup\d+'
UNION ALL
SELECT 'R25 mit falscher Adresse', count(*)::text FROM public.events
 WHERE ort IN ('R25 Kulturschlachthof', 'Kulturschlachthof R25', 'R25-Kulturschlachthof') AND adresse <> 'Rather Straße 25, 40476 Düsseldorf'
UNION ALL
SELECT 'Oper: fremder Spielort mit Opern-Adresse', count(*)::text FROM public.events
 WHERE quelle_name = 'Deutsche Oper am Rhein' AND adresse ILIKE 'Heinrich-Heine-Allee 16%'
   AND ort NOT ILIKE '%Opernhaus Düsseldorf%' AND ort <> 'Deutsche Oper am Rhein'
UNION ALL
SELECT 'Events mit Duisburg/Leipzig im Ort (nach Schritt 1: 0)', count(*)::text FROM public.events
 WHERE ort ~* '\m(duisburg|leipzig)\M';
