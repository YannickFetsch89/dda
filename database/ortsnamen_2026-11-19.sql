-- Ortsnamen vereinheitlichen – DiesDasDüsseldorf, erzeugt am 2026-11-19 von pipeline/ortsnamen.py
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

UPDATE public.events SET ort = 'Ratinger Hof' WHERE id IN ('49210880-fb07-440e-ba38-6fab01d9163b', '8d1855ca-d392-411e-b87a-378ac4077e19', 'bde1f768-ae06-426b-bc89-e2d777a17f2e');

UPDATE public.reihen SET ort = 'Ratinger Hof' WHERE ort IN ('Stone im Ratinger Hof');

COMMIT;

-- Kontrolle 1: alte Schreibweisen – erwartet: KEINE Zeile außer den 10 oben genannten Einträgen
SELECT ort, abgelehnt, COUNT(*) AS anzahl FROM public.events WHERE ort IN ('Stone im Ratinger Hof') GROUP BY ort, abgelehnt;

-- Kontrolle 2: neue Namen mit Anzahl
SELECT ort, COUNT(*) AS anzahl FROM public.events WHERE ort IN ('Ratinger Hof') GROUP BY ort ORDER BY anzahl DESC;
