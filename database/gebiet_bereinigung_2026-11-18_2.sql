-- gebiet_bereinigung_2026-11-18_2.sql – DiesDasDüsseldorf
-- Events außerhalb von Düsseldorf, Neuss und Ratingen löschen (Plan Locations E3, 18.11.2026).
-- ERZEUGT von pipeline/gebiet.py (python -m pipeline.gebiet --sql). Abhängige Zeilen (Merkliste,
-- Sensibel-Kennzeichnung, SEO-Entscheidungen) löschen sich mit (ON DELETE CASCADE), Meldungen behalten
-- ihre Daten (SET NULL). Ausführen als postgres im Supabase-SQL-Editor, nicht während eines Pipeline-Laufs.
-- Anzahl: 26 Events. Gründe: {'Stadt': 15, 'auswärtiger': 11}
--
--   2026-11-07 | Lise-Meitner-Gymnasium Geldern |  | Stadt Geldern | Rausgegangen
--   2026-10-31 | LUTZ, theaterhagen | LUTZ, theaterhagen | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-10-31 | Wuppertaler Miniaturland | Wuppertaler Miniaturland | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-10-31 | Grugahalle Essen | Grugahalle Essen | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-12 | Stadthalle Kleve | Stadthalle Kleve | Stadt Kleve | PRINZ.de Düsseldorf
--   2026-10-31 | Moya Club Kleve | Moya Club Kleve | Stadt Kleve | PRINZ.de Düsseldorf
--   2026-11-03 | Theater Gütersloh - Haupteingang | Theater Gütersloh - Haupteingang | Stadt Gütersloh | PRINZ.de Düsseldorf
--   2026-11-03 | Grugahalle Essen | Grugahalle Essen | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-06 | Bürgerhaus Rees | Bürgerhaus Rees | Stadt Rees | PRINZ.de Düsseldorf
--   2026-11-06 | Bürgerhaus Rees | Bürgerhaus Rees | Stadt Rees | PRINZ.de Düsseldorf
--   2026-11-06 | Stadthalle Kleve | Stadthalle Kleve | Stadt Kleve | PRINZ.de Düsseldorf
--   2026-11-05 | Treffpunkt: Im Café der Stadtbiblio Stadtbibliothek | Treffpunkt: Im Café der Stadtbiblio Stadtbibliothe | Stadt Gütersloh | PRINZ.de Düsseldorf
--   2026-11-05 | Theater Essen-Süd | Theater Essen-Süd | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-06 | Studiobühne max. 140 | Studiobühne max. 140, Gütersloh | Stadt Gütersloh | PRINZ.de Düsseldorf
--   2026-11-06 | theaterhagen, Großes Haus | theaterhagen, Großes Haus | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-06 | Theater Essen-Süd | Theater Essen-Süd | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-06 | Kultur-Haus Zach e.V. | Kultur-Haus Zach e.V., Hückeswagen | Stadt Hückeswagen | PRINZ.de Düsseldorf
--   2026-11-15 | Wuppertaler Miniaturland | Wuppertaler Miniaturland | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-15 | LUTZ, theaterhagen | LUTZ, theaterhagen | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-12-13 | Stadthalle Winsen | Stadthalle Winsen | Stadt Winsen | PRINZ.de Düsseldorf
--   2026-11-15 | Theater Essen-Süd | Theater Essen-Süd | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-15 | theaterhagen, Großes Haus | theaterhagen, Großes Haus | auswärtiger Ort | PRINZ.de Düsseldorf
--   2026-11-15 | Theater Gütersloh | Theater Gütersloh | Stadt Gütersloh | PRINZ.de Düsseldorf
--   2026-11-21 | Stadthalle Winsen | Stadthalle Winsen | Stadt Winsen | PRINZ.de Düsseldorf
--   2026-10-31 | Theater Gütersloh - Haupteingang | Theater Gütersloh - Haupteingang | Stadt Gütersloh | PRINZ.de Düsseldorf
--   2026-11-12 | Aula im Lise Meitner Gymnasium | Aula im Lise Meitner Gymnasium, Geldern | Stadt Geldern | PRINZ.de Düsseldorf

BEGIN;

DELETE FROM public.events WHERE id IN (
    'd3c29921-db5f-4dfc-951a-472616b8d00f',
    '51282457-1b64-406d-81d6-723800ad415f',
    '1e2ceddb-aed7-485e-b8f0-c63d420a8f72',
    '34fd01df-797e-46eb-9809-937bbc9491f8',
    '3bedd0b6-a699-4fbf-96ad-26aa9d5185d3',
    '1b1733e1-075c-47f9-8f87-8af1b10f5dca',
    '85974bf3-793f-4fa9-a5d8-f55e34641358',
    'ff5afad6-52b6-43d1-a49f-39831bdd4d6c',
    'c38afac4-5d07-4610-87a0-cb91e18d1509',
    'ca0bb111-3e84-4c85-a4ae-2b13847c93f9',
    '5352b430-8db2-4063-a091-e0bed437442c',
    'cd3bf0bf-6658-4f5c-941a-93ee65fc4340',
    'bfc8a5a7-d23d-470e-a656-278a6a26dde5',
    '04d260af-22ab-4671-a025-69a85b5ba73b',
    'b9f28086-dc8e-4a92-b9ed-9b99723e578b',
    '2416b788-00f7-40df-8dc2-1b25ff6d5bfb',
    'f4001f8b-dad3-421c-8ce6-d7690268cd3d',
    '1a011733-bd4a-4295-a6a4-26860fadac59',
    '528812bd-860f-4c09-ba9e-124a1488e86f',
    '91b89e15-c1bd-493f-b61a-0566aabd6091',
    'b7bd48b8-fca0-4ca0-91ad-79d60101f2a5',
    '99fa77fe-8f06-40eb-aae9-840ee3ec67fc',
    '80f31993-64c8-462b-83f7-32418b65dd18',
    '4a7d1c79-0917-4c28-b748-518032eb7bf5',
    'a4449515-3e4e-4bec-b9e0-ae8b235d1c01',
    '89ef3bca-a86a-40c1-82c7-43559e1bd13e'
);

COMMIT;

-- Kontrolle: Zahl der gelöschten Events steht oben; danach sollte diese Abfrage 0 ergeben
SELECT count(*) AS noch_da FROM public.events WHERE id IN ('d3c29921-db5f-4dfc-951a-472616b8d00f', '51282457-1b64-406d-81d6-723800ad415f', '1e2ceddb-aed7-485e-b8f0-c63d420a8f72', '34fd01df-797e-46eb-9809-937bbc9491f8', '3bedd0b6-a699-4fbf-96ad-26aa9d5185d3', '1b1733e1-075c-47f9-8f87-8af1b10f5dca', '85974bf3-793f-4fa9-a5d8-f55e34641358', 'ff5afad6-52b6-43d1-a49f-39831bdd4d6c', 'c38afac4-5d07-4610-87a0-cb91e18d1509', 'ca0bb111-3e84-4c85-a4ae-2b13847c93f9', '5352b430-8db2-4063-a091-e0bed437442c', 'cd3bf0bf-6658-4f5c-941a-93ee65fc4340', 'bfc8a5a7-d23d-470e-a656-278a6a26dde5', '04d260af-22ab-4671-a025-69a85b5ba73b', 'b9f28086-dc8e-4a92-b9ed-9b99723e578b', '2416b788-00f7-40df-8dc2-1b25ff6d5bfb', 'f4001f8b-dad3-421c-8ce6-d7690268cd3d', '1a011733-bd4a-4295-a6a4-26860fadac59', '528812bd-860f-4c09-ba9e-124a1488e86f', '91b89e15-c1bd-493f-b61a-0566aabd6091', 'b7bd48b8-fca0-4ca0-91ad-79d60101f2a5', '99fa77fe-8f06-40eb-aae9-840ee3ec67fc', '80f31993-64c8-462b-83f7-32418b65dd18', '4a7d1c79-0917-4c28-b748-518032eb7bf5', 'a4449515-3e4e-4bec-b9e0-ae8b235d1c01', '89ef3bca-a86a-40c1-82c7-43559e1bd13e');
