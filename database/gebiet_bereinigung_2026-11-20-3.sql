-- gebiet_bereinigung_2026-11-20-3.sql – DiesDasDüsseldorf (Nachtrag: Köln-Meetups, Online-Gruppen, STARTPLATZ Köln)
-- Events außerhalb von Düsseldorf, Neuss und Ratingen löschen (Plan Locations E3, 18.11.2026).
-- ERZEUGT von pipeline/gebiet.py (python -m pipeline.gebiet --sql). Abhängige Zeilen (Merkliste,
-- Sensibel-Kennzeichnung, SEO-Entscheidungen) löschen sich mit (ON DELETE CASCADE), Meldungen behalten
-- ihre Daten (SET NULL). Ausführen als postgres im Supabase-SQL-Editor, nicht während eines Pipeline-Laufs.
-- Anzahl: 52 Events. Gründe: {'Stadt': 50, 'Online-Gruppe': 2}
--
--   2026-11-15 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-18 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-13 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-12-05 | Glühgarten ehrenfeld | Widdersdorfer Str. 198 Köln | Stadt Köln | Meetup.com
--   2026-11-13 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-10-30 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-18 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-10-28 | Kölner Tattoo Community (Online) |  | Online-Gruppe Kölner | Meetup.com
--   2026-11-03 | Rudel Köln - Gemeinschaft, Austausch & Aktionen unter Männer |  | Stadt Köln | Meetup.com
--   2026-11-26 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-01 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-10-28 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-12-03 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-12-02 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-25 | Kölner Tattoo Community (Online) |  | Online-Gruppe Kölner | Meetup.com
--   2026-11-03 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-06 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-08 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-12-02 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-21 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-23 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-18 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-19 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-04-08 | Azure Cologne Meetup (Online) |  | Stadt Cologne | Meetup.com
--   2026-04-13 | Eckankar Köln (Online) |  | Stadt Köln | Meetup.com
--   2026-04-07 | No More Mr. Nice Guy-Gruppe Köln + Online (Online) |  | Stadt Köln | Meetup.com
--   2026-04-08 | Cologne Social Media Creators and Influencer Meetups (Online |  | Stadt Cologne | Meetup.com
--   2026-11-03 | Power Platform & Fabric User Group Cologne (Online) |  | Stadt Cologne | Meetup.com
--   2026-10-31 | Köln Japanese Language Community (Online) |  | Stadt Köln | Meetup.com
--   2026-10-28 | Power Platform & Fabric User Group Cologne (Online) |  | Stadt Cologne | Meetup.com
--   2026-11-25 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-30 | Cologne Men's Circle (Online) |  | Stadt Cologne | Meetup.com
--   2026-11-11 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-12 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-04 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-10 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-11 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-05 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-04-12 | English Comedy Fans of Cologne (Online) |  | Stadt Cologne | Meetup.com
--   2026-11-05 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-08 | English Comedy Fans of Cologne (Online) |  | Stadt Cologne | Meetup.com
--   2026-11-04 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-10-27 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-10-29 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-11 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-10-29 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-10-28 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-20 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-18 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-12 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-27 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com
--   2026-11-25 | ✅ Köln Meetup | Daily Events! (Online) |  | Stadt Köln | Meetup.com

BEGIN;

DELETE FROM public.events WHERE id IN (
    '592e65fe-aa25-470f-a27c-16ffcdab3f8a',
    '97f06f4f-063f-4173-9ad9-688375cea7c3',
    'f55d815e-a90d-4866-bca6-94a7ceb3fbfb',
    '71f1970b-c1f6-4ba7-9026-e6e1649a9e72',
    '1e0841a6-6d13-4943-bd91-a07008c92bb1',
    'a50ecd2d-7f92-46d7-89ad-512c0eb9271d',
    'e6aa24fb-47d2-43bb-bba3-b1aa450d020b',
    '35d8da44-acf0-4117-9b8c-d9a79995a8b6',
    'a4f91f14-9c32-4b52-be8d-6b80175e3bb6',
    'adf24c3b-572a-43c0-8a96-7015d41d6e93',
    '77f4b2e8-6e37-47ea-99e7-f2dc6e51173d',
    '7a4ffc46-cc84-45ab-9d7d-6ba173cf0458',
    '0c8cd270-325c-4093-8f9c-405d5df6aae6',
    '4581a8ff-ab0d-458e-9c9a-ddb5ca8b874d',
    '371f80d9-6dbb-4f9b-959b-be340c9b7232',
    'af6d041e-8968-4c35-bf34-72c8a453b2dd',
    'e997a8f7-19fd-4512-a7ed-1e19c0fffa84',
    'b2bdf23c-2d5c-4b33-ba85-1f00c357aa45',
    '1c6de054-fd02-459c-97de-d125388a21a4',
    'c73f2238-168b-4ff2-b43b-2b909eeff89e',
    '67e0ad4b-8b41-4140-8c11-1f5e57e143e7',
    '55f85b8b-1c4d-4b5a-8ace-f42bf0980b11',
    'a2bc0dc1-4722-4d21-ac80-a4f06799e363',
    '0f3a2184-0daf-4858-907f-6e1b85d12e62',
    'f7b5d220-3ba2-42a4-8a7c-0057bfc6f753',
    'e354f395-2442-41cb-b16a-821a6f4a9769',
    '2327674b-a979-4fd7-b195-c37dfc56b131',
    '9ffa0639-af64-47bb-911c-af1c9ba42ec4',
    'a6015fa7-8dbd-456b-a725-9e58353967a3',
    'ac9d5486-7cc3-41c1-b9ff-3c52d20c31fb',
    '4753ba64-6367-48ae-afc7-19b1534ad1a7',
    '056702db-0cb5-4a8c-a273-61a15d607317',
    'f2928414-4010-4d97-b920-a08945ef8895',
    'c154aa32-5b4c-42b2-b7cc-381c6fdff9f6',
    'd9f217c5-d634-41c0-b223-2de83a7fd462',
    '294d8299-5993-4764-8ac1-6a802ea8d6a3',
    'fe767385-c860-425b-8b09-159b65994422',
    '43dbc11d-ca62-4581-8b8a-023ce85383f3',
    '31b83a69-f529-4770-be84-1d1ed4bded71',
    '4f1884a4-d334-45af-b1e8-c8dbd2b0a9f2',
    'adcfc7ce-af6e-41e8-b92e-75f20b4a19e1',
    'ec151093-d388-4294-8529-a8272a2b926a',
    '432fdd2c-2b65-408c-b2f6-646c415ff150',
    '82435fb8-5709-49fd-86fd-14a859c7d7c6',
    'ab91bdcc-b027-4826-801f-acd534ca83bd',
    'cf565ab1-7f4a-40da-9f79-c93cd583f4c0',
    '3f7c48e9-d24f-4b33-85ac-5c77ade013f1',
    'd212dbfd-93fe-49b3-a5df-1b921facf2d5',
    '285cb53d-0ffb-4015-9269-848e3061a51d',
    '77943a00-7cf8-4956-8a90-e712632b1e16',
    '089839f1-f6f5-40e5-862f-c25948079cd8',
    '4d0e2bff-1212-42dd-87dd-69644640a9c9'
);

-- STARTPLATZ-Events am Kölner Standort (mit Düsseldorfer Adresse gespeichert)
DELETE FROM public.events WHERE id IN ('1488db47-00ff-4c33-953a-fbd185739138');

COMMIT;

-- Kontrolle: Zahl der gelöschten Events steht oben; danach sollte diese Abfrage 0 ergeben
SELECT count(*) AS noch_da FROM public.events WHERE id IN ('592e65fe-aa25-470f-a27c-16ffcdab3f8a', '97f06f4f-063f-4173-9ad9-688375cea7c3', 'f55d815e-a90d-4866-bca6-94a7ceb3fbfb', '71f1970b-c1f6-4ba7-9026-e6e1649a9e72', '1e0841a6-6d13-4943-bd91-a07008c92bb1', 'a50ecd2d-7f92-46d7-89ad-512c0eb9271d', 'e6aa24fb-47d2-43bb-bba3-b1aa450d020b', '35d8da44-acf0-4117-9b8c-d9a79995a8b6', 'a4f91f14-9c32-4b52-be8d-6b80175e3bb6', 'adf24c3b-572a-43c0-8a96-7015d41d6e93', '77f4b2e8-6e37-47ea-99e7-f2dc6e51173d', '7a4ffc46-cc84-45ab-9d7d-6ba173cf0458', '0c8cd270-325c-4093-8f9c-405d5df6aae6', '4581a8ff-ab0d-458e-9c9a-ddb5ca8b874d', '371f80d9-6dbb-4f9b-959b-be340c9b7232', 'af6d041e-8968-4c35-bf34-72c8a453b2dd', 'e997a8f7-19fd-4512-a7ed-1e19c0fffa84', 'b2bdf23c-2d5c-4b33-ba85-1f00c357aa45', '1c6de054-fd02-459c-97de-d125388a21a4', 'c73f2238-168b-4ff2-b43b-2b909eeff89e', '67e0ad4b-8b41-4140-8c11-1f5e57e143e7', '55f85b8b-1c4d-4b5a-8ace-f42bf0980b11', 'a2bc0dc1-4722-4d21-ac80-a4f06799e363', '0f3a2184-0daf-4858-907f-6e1b85d12e62', 'f7b5d220-3ba2-42a4-8a7c-0057bfc6f753', 'e354f395-2442-41cb-b16a-821a6f4a9769', '2327674b-a979-4fd7-b195-c37dfc56b131', '9ffa0639-af64-47bb-911c-af1c9ba42ec4', 'a6015fa7-8dbd-456b-a725-9e58353967a3', 'ac9d5486-7cc3-41c1-b9ff-3c52d20c31fb', '4753ba64-6367-48ae-afc7-19b1534ad1a7', '056702db-0cb5-4a8c-a273-61a15d607317', 'f2928414-4010-4d97-b920-a08945ef8895', 'c154aa32-5b4c-42b2-b7cc-381c6fdff9f6', 'd9f217c5-d634-41c0-b223-2de83a7fd462', '294d8299-5993-4764-8ac1-6a802ea8d6a3', 'fe767385-c860-425b-8b09-159b65994422', '43dbc11d-ca62-4581-8b8a-023ce85383f3', '31b83a69-f529-4770-be84-1d1ed4bded71', '4f1884a4-d334-45af-b1e8-c8dbd2b0a9f2', 'adcfc7ce-af6e-41e8-b92e-75f20b4a19e1', 'ec151093-d388-4294-8529-a8272a2b926a', '432fdd2c-2b65-408c-b2f6-646c415ff150', '82435fb8-5709-49fd-86fd-14a859c7d7c6', 'ab91bdcc-b027-4826-801f-acd534ca83bd', 'cf565ab1-7f4a-40da-9f79-c93cd583f4c0', '3f7c48e9-d24f-4b33-85ac-5c77ade013f1', 'd212dbfd-93fe-49b3-a5df-1b921facf2d5', '285cb53d-0ffb-4015-9269-848e3061a51d', '77943a00-7cf8-4956-8a90-e712632b1e16');
