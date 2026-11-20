-- gebiet_bereinigung_2026-11-20-2.sql – DiesDasDüsseldorf (Nachtrag: Städte im Titel, Hanau, „… Köln“)
-- Events außerhalb von Düsseldorf, Neuss und Ratingen löschen (Plan Locations E3, 18.11.2026).
-- ERZEUGT von pipeline/gebiet.py (python -m pipeline.gebiet --sql). Abhängige Zeilen (Merkliste,
-- Sensibel-Kennzeichnung, SEO-Entscheidungen) löschen sich mit (ON DELETE CASCADE), Meldungen behalten
-- ihre Daten (SET NULL). Ausführen als postgres im Supabase-SQL-Editor, nicht während eines Pipeline-Laufs.
-- Anzahl: 10 Events. Gründe: {'Stadt': 2, 'Titel': 8}
--
--   2026-11-25 | Lanxess Arena Köln |  | Stadt Köln | AllEvents.in Düsseldorf
--   2026-04-02 | SPECIAL EVENTS |  | Titel nennt Hagen | PRINZ.de Düsseldorf
--   2026-04-04 | BÜHNE |  | Titel nennt Hagen | PRINZ.de Düsseldorf
--   2026-10-27 | Konzerte & Livemusik |  | Titel nennt Hagen | PRINZ.de Düsseldorf
--   2026-04-04 | SPECIAL EVENTS |  | Titel nennt Krefeld | PRINZ.de Düsseldorf
--   2026-10-28 | Friends in Dusseldorf |  | Titel nennt meerbusch | Meetup.com
--   2026-12-12 | Leipziger Marktplatz | Leipziger Marktplatz | Titel nennt Leipzig | PRINZ.de Düsseldorf
--   2026-12-12 | Stadthof Hanau | Stadthof Hanau | Stadt Hanau | PRINZ.de Düsseldorf
--   2026-04-03 | Düsseldorf Hbf | Düsseldorf Hbf Düsseldorf | Titel nennt Bonn | Meetup.com
--   2026-11-20 | Königstraße |  | Titel nennt Duisburg | Rausgegangen

BEGIN;

DELETE FROM public.events WHERE id IN (
    '13e4ac78-f871-4c81-bc55-5aaa4175d7b3',
    'b1b8ff7a-1f4f-4494-9523-eae43a628765',
    'd3667996-cc68-4795-a350-bb0319fbf7dd',
    '89f1831a-bdfd-4f79-9fe7-41d170e2d8f5',
    '166e6039-b9f2-4793-b938-f92db9dfe7ce',
    '5687fdc9-761a-4b14-87b0-12484620213e',
    '4c738855-0945-4f6c-8598-cbcdbbeb58a0',
    '42aff59c-d603-4320-ad11-c00e20fbd7c3',
    'ffb5fdec-cd28-4ac4-858a-3b87b6faae99',
    '52c351d8-a7fe-4fb6-86ca-ce8c72726a52'
);

COMMIT;

-- Kontrolle: Zahl der gelöschten Events steht oben; danach sollte diese Abfrage 0 ergeben
SELECT count(*) AS noch_da FROM public.events WHERE id IN ('13e4ac78-f871-4c81-bc55-5aaa4175d7b3', 'b1b8ff7a-1f4f-4494-9523-eae43a628765', 'd3667996-cc68-4795-a350-bb0319fbf7dd', '89f1831a-bdfd-4f79-9fe7-41d170e2d8f5', '166e6039-b9f2-4793-b938-f92db9dfe7ce', '5687fdc9-761a-4b14-87b0-12484620213e', '4c738855-0945-4f6c-8598-cbcdbbeb58a0', '42aff59c-d603-4320-ad11-c00e20fbd7c3', 'ffb5fdec-cd28-4ac4-858a-3b87b6faae99', '52c351d8-a7fe-4fb6-86ca-ce8c72726a52');
