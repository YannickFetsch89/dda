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

UPDATE public.events SET ort = 'R25 Kulturschlachthof' WHERE id IN ('3439e687-34ba-4854-9c82-22c05761fde1', '4bfa30d1-fae8-49f3-a06c-7871f6649bb5', '5f596d69-466c-4e30-a83c-968c65a67ccc', '6686e4d9-91e4-47d4-93c8-e2c0c9907e31', '7a9410b8-fec1-4558-b508-7564fde1df0c', 'ab34ec39-225f-48ad-84db-b9865442f6dd', 'd001e285-d5a6-4562-ae49-f62652528577');
UPDATE public.events SET ort = 'Roncalli''s Apollo Varieté' WHERE id IN ('8e46c446-f6ba-42de-82bf-2d28f991adf5', '908d844f-d30d-472e-bcf4-8961a5f76c3a', 'c3763dbd-8a8d-40b8-88fb-bf1786669054', 'd1cff447-c727-4101-b833-48887d1bcbe3', 'e1573a0e-61fa-448f-ab3f-d41f2c6ddaba', 'fb271020-204b-4c0a-8d40-48c31333bf4f');
UPDATE public.events SET ort = 'Rudas Studios' WHERE id IN ('0fce62ca-14ec-40c2-83a3-3cb666082938', '2d74d599-49ab-4d3d-868b-587d6cc339d9', '5a2bd0c7-e3d2-4d70-ab5e-0b6705b48635', '71e3abaf-422e-43de-bed7-a87756d86dd7', 'bdaa399b-a27f-4552-a88b-94c1048134a6');
UPDATE public.events SET ort = 'Rundum Yoga' WHERE id IN ('127dcddb-3b10-43de-8890-94a16db7b22c', '365f0763-d37a-49fc-8916-ea9b001c4139', '5c9ff57f-3572-48d6-b58b-ddb7f4651715', 'a94c2c91-da81-4ebb-aa68-b38bbed189e7');

UPDATE public.reihen SET ort = 'R25 Kulturschlachthof' WHERE ort IN ('Kulturschlachthof R25');
UPDATE public.reihen SET ort = 'Roncalli''s Apollo Varieté' WHERE ort IN ('Roncalli''s Apollo Variete');
UPDATE public.reihen SET ort = 'Rudas Studios' WHERE ort IN ('Rudas Studios Club');
UPDATE public.reihen SET ort = 'Rundum Yoga' WHERE ort IN ('Rundum Yoga Studio Pempelfort', 'Rundum Yoga-Studio');

-- Reihen-Schlüssel (titel|ort) an die neuen Ortsnamen anpassen – Slugs bleiben
UPDATE public.reihen SET schluessel = 'leise rieselt der schmäh 2026 roncallis apollo varieté|roncallis apollo varieté' WHERE id = '454314d4-1715-475e-b6bc-dc821a55f31d';

COMMIT;

-- Kontrolle 1: alte Schreibweisen – erwartet: KEINE Zeile außer den 10 oben genannten Einträgen
SELECT ort, abgelehnt, COUNT(*) AS anzahl FROM public.events WHERE ort IN ('Kulturschlachthof R25', 'Roncalli''s Apollo Variete', 'Rudas Studios Club', 'Rundum Yoga Studio Pempelfort', 'Rundum Yoga-Studio') GROUP BY ort, abgelehnt;

-- Kontrolle 2: neue Namen mit Anzahl
SELECT ort, COUNT(*) AS anzahl FROM public.events WHERE ort IN ('R25 Kulturschlachthof', 'Roncalli''s Apollo Varieté', 'Rudas Studios', 'Rundum Yoga') GROUP BY ort ORDER BY anzahl DESC;
