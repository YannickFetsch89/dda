-- gebiet_bereinigung_2026-11-19.sql – DiesDasDüsseldorf
-- Events außerhalb von Düsseldorf, Neuss und Ratingen löschen (Plan Locations E3, 18.11.2026).
-- ERZEUGT von pipeline/gebiet.py (python -m pipeline.gebiet --sql). Abhängige Zeilen (Merkliste,
-- Sensibel-Kennzeichnung, SEO-Entscheidungen) löschen sich mit (ON DELETE CASCADE), Meldungen behalten
-- ihre Daten (SET NULL). Ausführen als postgres im Supabase-SQL-Editor, nicht während eines Pipeline-Laufs.
-- Anzahl: 2 Events. Gründe: {'auswärtiger': 2}
--
--   2026-11-03 | Mayersche Essen | Mayersche Essen | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-18 | Mayersche Essen | Mayersche Essen | auswärtiger Ort | PRINZ.de Düsseldorf

BEGIN;

DELETE FROM public.events WHERE id IN (
    '972e70eb-9047-453d-a63c-ad07791f395e',
    '08f5a5fb-b79a-442f-bc1a-4b157ded26e1'
);

COMMIT;

-- Kontrolle: Zahl der gelöschten Events steht oben; danach sollte diese Abfrage 0 ergeben
SELECT count(*) AS noch_da FROM public.events WHERE id IN ('972e70eb-9047-453d-a63c-ad07791f395e', '08f5a5fb-b79a-442f-bc1a-4b157ded26e1');
