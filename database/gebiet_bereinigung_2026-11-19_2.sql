-- gebiet_bereinigung_2026-11-19_2.sql – DiesDasDüsseldorf
-- Events außerhalb von Düsseldorf, Neuss und Ratingen löschen (Plan Locations E3, 18.11.2026).
-- ERZEUGT von pipeline/gebiet.py (python -m pipeline.gebiet --sql). Abhängige Zeilen (Merkliste,
-- Sensibel-Kennzeichnung, SEO-Entscheidungen) löschen sich mit (ON DELETE CASCADE), Meldungen behalten
-- ihre Daten (SET NULL). Ausführen als postgres im Supabase-SQL-Editor, nicht während eines Pipeline-Laufs.
-- Anzahl: 2 Events. Gründe: {'Stadt': 2}
--
--   2026-10-31 | Lufre Event & Gastronomie | Lufre Event & Gastronomie, Kamp-Lintfort | Stadt Kamp-Lintfort | PRINZ.de Düsseldorf
--   2026-10-31 | Lufre Event & Gastronomie | Lufre Event & Gastronomie, Kamp-Lintfort | Stadt Kamp-Lintfort | PRINZ.de Düsseldorf

BEGIN;

DELETE FROM public.events WHERE id IN (
    '71f65821-519e-4f34-a50e-7aeebe982671',
    'bed2cc9c-94a3-4c39-968e-195df118410c'
);

COMMIT;

-- Kontrolle: Zahl der gelöschten Events steht oben; danach sollte diese Abfrage 0 ergeben
SELECT count(*) AS noch_da FROM public.events WHERE id IN ('71f65821-519e-4f34-a50e-7aeebe982671', 'bed2cc9c-94a3-4c39-968e-195df118410c');
