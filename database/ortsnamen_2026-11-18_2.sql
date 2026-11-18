-- Ortsnamen vereinheitlichen – DiesDasDüsseldorf, erzeugt am 2026-11-18 von pipeline/ortsnamen.py
-- Eine Schreibweise pro Spielstätte (Liste: SPIELSTAETTEN in pipeline/ortsnamen.py). Räume im selben Haus,
-- Treffpunkte und allgemeine Angaben bleiben, wie sie sind. Event-Slugs (URLs) ändern sich nicht.
-- Reihen behalten ihren Slug; nur ihr interner Schlüssel wird an den neuen Ortsnamen angepasst.
-- Im Supabase-SQL-Editor als Ganzes ausführen.

BEGIN;

-- 10 Einträge behalten ihren alten Namen, weil sie sonst mit einem anderen Termin
-- (gleicher Titel, Tag, Ort und Uhrzeit) zusammenfielen – meist ausgeblendete Dubletten mit Weiterleitung:
--   2026-11-07 20:00:00 „THE BEATLES by LUCY AND THE TAXMEN“ @ Pitcher
--   2026-11-06 20:00:00 „Red Hot Chili Peppers by Psycho Sexy“ @ Pitcher
--   2026-11-08 17:00:00 „The Cloverhearts“ @ Pitcher
--   2026-11-07 22:00:00 „Effekt X pres. Loraw / ARES /“ @ Kulturschlachthof R25
--   2026-10-31 23:00:00 „RAVEMANIA // HALLOWEEN RAVE SPECIAL 2026“ @ Kulturschlachthof R25
--   2026-10-30 20:00:00 „Bülbül Club“ @ tanzhaus nrw
--   2026-10-31 23:00:00 „RAVEMANIA // HALLOWEEN RAVE SPECIAL 2026“ @ R25-Kulturschlachthof
--   2026-04-11 22:00:00 „AREA51RULEZ - Resident Night at Schlachthof Düssel“ @ Kulturschlachthof R25
--   2026-10-31 21:00:00 „mesh:project Halloween Session @Kulturschlachthof “ @ Kulturschlachthof R25
--   2026-11-11 20:30:00 „D.Now: Genevieve O’Driscoll“ @ Jazz Schmiede (ausgeblendet)

UPDATE public.events SET ort = 'Drachental Games' WHERE id IN ('0e44a10a-fcd5-4f3d-9bc6-0531cce092f6', '3a9a3705-d9d4-4cf6-8387-211982400675', '8b2e90ac-aa64-4be8-aae2-f7624f76abb9');
UPDATE public.events SET ort = 'FFT Düsseldorf – Bühne I' WHERE id IN ('18d71195-1921-4b2e-b34e-9b18af07e23c', '28b13d16-0bc9-4d74-a9a8-3db94acd0558', '2e825a9c-e926-40e3-9d6d-c02b03643dab', '6293a5b2-9c90-4fad-89d0-e278c59191ff', '649a4608-c408-4495-9cb6-26c30dd83a88', '883cdfbd-e9f4-4df3-aad2-6035331ae721', '8f7ce586-2d6a-4ae0-9e8b-f6e50ce714a0', 'a76782b5-c2e4-42b7-9dba-dd40fde933b7', 'a9e625ab-a258-4d24-824a-07fb62378114', 'afe2376d-5b3c-4d18-8ac8-68574f543331', 'ca7834bc-5b8e-4807-8313-6c561ece655b', 'e39ed811-8cba-4aeb-950e-1012a7e9f38d', 'e6afb0f5-0ada-4803-a700-17435f2c1048', 'e6cbf08e-0cb0-4674-af8c-b6e7528a929a', 'e8d1334b-6639-46d0-8805-5939f26977bd', 'ea0236ea-63f5-4ad4-92c6-24dadb3431f4', 'eb42ea5c-7514-4256-8112-dc55365f9792', 'ed1c9a7d-9d84-421e-8259-85c5ffe784d5', 'fe491952-4589-4b8a-ab80-1f28cb687db6');
UPDATE public.events SET ort = 'FFT Düsseldorf – Bühne II' WHERE id IN ('0aa926cb-3a03-40b5-82d5-01d03fc9ba94', '180378fd-7376-4fff-a4cf-ebb77b2a9223', '2972d351-f2a8-4a2d-902f-40565d1a88de', '2b9eb547-66b3-4c71-9b02-0e8925bfc857', '2fdc919b-ba16-4e3f-9621-267c4e4e3f77', '309e3fc2-b824-414b-9772-fa9a6366c683', '482aa8a1-8393-4feb-942e-d589c3159521', '69e126c5-a300-4a40-aec4-7c5647523f54', '72ebfdcb-05ac-492e-88be-e8b8650fc8da', '7391365a-5c9f-4515-b183-c84a64f61ef3', '75680218-88c4-45ac-9d80-af9da9ce0374', 'a92de0d7-e4ff-4a08-921a-c7fb1108928e', 'aafea75e-b646-4e8f-9414-de5b5b2ed59d', 'ada57c50-c529-429a-9662-7fc9674323cf', 'b0eb12b9-cff9-4388-be07-4881e3cca558', 'baf2a2ca-248a-4dce-b2b6-74c263c2df40', 'c83556e9-7408-40c4-bba6-5ff9b418be69', 'd164b370-3c9e-44bb-8946-3d6938ea9ce7', 'db28beab-a730-4b87-bb87-fdd0421181e7', 'edecb6fd-a6e0-47a5-a8ee-a6cca06874d1', 'f211a0b8-90e2-435d-a231-3eb6f3e4ff98', 'f8f462ce-4c1c-469c-8f00-38da57a05df7');
UPDATE public.events SET ort = 'Metropol Kino' WHERE id IN ('20abbabb-c091-4cdd-b67d-2f013a24e1d3', '98c6219d-dcdd-42dc-9d61-ee19cb23b283');
UPDATE public.events SET ort = 'Salon des Amateurs' WHERE id IN ('5b1d7771-bee0-4f08-90ac-d887eb7fabb8', 'db8e607e-4eb4-497a-881b-667c001245c9', 'f56c48eb-6652-451c-a172-fd6555141941');

UPDATE public.reihen SET ort = 'Drachental Games' WHERE ort IN ('Drachental');
UPDATE public.reihen SET ort = 'FFT Düsseldorf – Bühne I' WHERE ort IN ('Bühne I');
UPDATE public.reihen SET ort = 'FFT Düsseldorf – Bühne II' WHERE ort IN ('Bühne II');
UPDATE public.reihen SET ort = 'Metropol Kino' WHERE ort IN ('Metropol');
UPDATE public.reihen SET ort = 'Salon des Amateurs' WHERE ort IN ('salon des amateurs');

-- Reihen-Schlüssel (titel|ort) an die neuen Ortsnamen anpassen – Slugs bleiben
UPDATE public.reihen SET schluessel = 'board game night drachental|drachental games' WHERE id = 'f19405ba-0f4e-43a0-810e-e44b37e49014';

COMMIT;

-- Kontrolle 1: alte Schreibweisen – erwartet: KEINE Zeile außer den 10 oben genannten Einträgen
SELECT ort, abgelehnt, COUNT(*) AS anzahl FROM public.events WHERE ort IN ('Bühne I', 'Bühne II', 'Drachental', 'Metropol', 'salon des amateurs') GROUP BY ort, abgelehnt;

-- Kontrolle 2: neue Namen mit Anzahl
SELECT ort, COUNT(*) AS anzahl FROM public.events WHERE ort IN ('Drachental Games', 'FFT Düsseldorf – Bühne I', 'FFT Düsseldorf – Bühne II', 'Metropol Kino', 'Salon des Amateurs') GROUP BY ort ORDER BY anzahl DESC;
