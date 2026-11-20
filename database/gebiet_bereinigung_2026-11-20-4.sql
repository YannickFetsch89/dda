-- gebiet_bereinigung_2026-11-20-4.sql – DiesDasDüsseldorf
-- Events außerhalb von Düsseldorf, Neuss und Ratingen löschen (Plan Locations E3, 18.11.2026).
-- ERZEUGT von pipeline/gebiet.py (python -m pipeline.gebiet --sql). Abhängige Zeilen (Merkliste,
-- Sensibel-Kennzeichnung, SEO-Entscheidungen) löschen sich mit (ON DELETE CASCADE), Meldungen behalten
-- ihre Daten (SET NULL). Ausführen als postgres im Supabase-SQL-Editor, nicht während eines Pipeline-Laufs.
-- Anzahl: 4 Events. Gründe: {'auswärtiger': 2, 'Stadt': 2}
--
--   2026-11-18 | Grefrather EisSport & EventPark | Grefrather EisSport & EventPark | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-20 | Bürgerhaus Telgte | Bürgerhaus Telgte | Stadt Telgte | PRINZ.de Düsseldorf
--   2026-11-20 | Grefrather EisSport & EventPark | Grefrather EisSport & EventPark | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-06 | Bürgerhaus Telgte | Bürgerhaus Telgte | Stadt Telgte | PRINZ.de Düsseldorf

BEGIN;

DELETE FROM public.events WHERE id IN (
    'd63b4463-93d9-4cbc-836a-826f7256b4ab',
    '09f2dba6-6460-44f9-b1a5-ac56eb15d229',
    'a6ffc6fd-c3c2-486c-adf0-8bf3da8f4d08',
    '2f830627-32cc-4d8e-a5f8-bb64d706470e'
);

COMMIT;

-- Kontrolle: Zahl der gelöschten Events steht oben; danach sollte diese Abfrage 0 ergeben
SELECT count(*) AS noch_da FROM public.events WHERE id IN ('d63b4463-93d9-4cbc-836a-826f7256b4ab', '09f2dba6-6460-44f9-b1a5-ac56eb15d229', 'a6ffc6fd-c3c2-486c-adf0-8bf3da8f4d08', '2f830627-32cc-4d8e-a5f8-bb64d706470e');
