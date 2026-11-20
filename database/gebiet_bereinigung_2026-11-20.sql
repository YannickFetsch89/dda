-- gebiet_bereinigung_2026-11-20.sql – DiesDasDüsseldorf
-- Events außerhalb von Düsseldorf, Neuss und Ratingen löschen (Plan Locations E3, 18.11.2026).
-- ERZEUGT von pipeline/gebiet.py (python -m pipeline.gebiet --sql). Abhängige Zeilen (Merkliste,
-- Sensibel-Kennzeichnung, SEO-Entscheidungen) löschen sich mit (ON DELETE CASCADE), Meldungen behalten
-- ihre Daten (SET NULL). Ausführen als postgres im Supabase-SQL-Editor, nicht während eines Pipeline-Laufs.
-- Anzahl: 9 Events. Gründe: {'auswärtiger': 9}
--
--   2026-11-21 | Erlebnisbauernhof Gertrudenhof |  | auswärtiger Ort | Rausgegangen
--   2026-04-09 | Erlebnisbauernhof Gertrudenhof |  | auswärtiger Ort | Rausgegangen
--   2026-11-07 | Erlebnisbauernhof Gertrudenhof |  | auswärtiger Ort | Rausgegangen
--   2026-10-31 | Erlebnisbauernhof Gertrudenhof |  | auswärtiger Ort | Rausgegangen
--   2026-11-19 | Erlebnisbauernhof Gertrudenhof |  | auswärtiger Ort | Rausgegangen
--   2026-11-13 | Erlebnisbauernhof Gertrudenhof |  | auswärtiger Ort | Rausgegangen
--   2026-10-30 | Erlebnisbauernhof Gertrudenhof |  | auswärtiger Ort | Rausgegangen
--   2026-04-02 | Erlebnisbauernhof Gertrudenhof |  | auswärtiger Ort | Rausgegangen
--   2026-11-15 | Erlebnisbauernhof Gertrudenhof |  | auswärtiger Ort | Rausgegangen

BEGIN;

DELETE FROM public.events WHERE id IN (
    'a2d04972-d475-4e44-9788-771eed40146d',
    '9dab4a7c-3cfe-47b1-9963-0e64e6e9be8c',
    'c721028d-b118-48e6-8cf0-d29acde04d5c',
    '24fd7c45-79a7-4de6-944c-1279b7916ea4',
    '2c6a7650-d5fe-4efc-a90e-adcf43b04ad6',
    '28e1c9a3-9436-4ca5-8a06-676547f0b769',
    '92d2b141-98e1-4b0e-94af-82e6feb643a1',
    '1587c31c-cacd-430d-a96b-35b0b50e676b',
    '6f6bb1ca-92d2-46e6-9762-fcb1776442ce'
);

COMMIT;

-- Kontrolle: Zahl der gelöschten Events steht oben; danach sollte diese Abfrage 0 ergeben
SELECT count(*) AS noch_da FROM public.events WHERE id IN ('a2d04972-d475-4e44-9788-771eed40146d', '9dab4a7c-3cfe-47b1-9963-0e64e6e9be8c', 'c721028d-b118-48e6-8cf0-d29acde04d5c', '24fd7c45-79a7-4de6-944c-1279b7916ea4', '2c6a7650-d5fe-4efc-a90e-adcf43b04ad6', '28e1c9a3-9436-4ca5-8a06-676547f0b769', '92d2b141-98e1-4b0e-94af-82e6feb643a1', '1587c31c-cacd-430d-a96b-35b0b50e676b', '6f6bb1ca-92d2-46e6-9762-fcb1776442ce');
