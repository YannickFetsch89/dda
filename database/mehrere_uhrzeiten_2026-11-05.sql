-- Mehrere Termine desselben Events am selben Tag erlauben (z.B. Führungen um 11 und 14 Uhr).
-- Stand: 2026-11-05 · Im Supabase SQL-Editor ausführen, BEVOR die angepasste Pipeline deployt wird.
--
-- Bisher: UNIQUE (titel, datum, ort) → ein zweiter Termin mit gleichem Titel am selben Tag ging verloren.
-- Neu:    UNIQUE NULLS NOT DISTINCT (titel, datum, ort, uhrzeit)
--         → je Uhrzeit ein Eintrag; zwei Einträge ohne Uhrzeit gelten weiterhin als Duplikat.
-- Die Website fasst die Termine in Listen wieder zu einem Eintrag „Diverse Uhrzeiten“ zusammen.

DO $$
DECLARE
  regel TEXT;
BEGIN
  -- Alte Eindeutigkeitsregel(n) auf genau (titel, datum, ort) finden und entfernen
  FOR regel IN
    SELECT con.conname
    FROM pg_constraint con
    WHERE con.conrelid = 'public.events'::regclass
      AND con.contype = 'u'
      AND (
        SELECT array_agg(att.attname::text ORDER BY att.attname)
        FROM unnest(con.conkey) AS k(attnum)
        JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = k.attnum
      ) = ARRAY['datum', 'ort', 'titel']
  LOOP
    EXECUTE format('ALTER TABLE public.events DROP CONSTRAINT %I', regel);
    RAISE NOTICE 'Alte Regel entfernt: %', regel;
  END LOOP;
END $$;

-- Wiederholbar: neue Regel vorher entfernen, falls das Skript schon einmal gelaufen ist
ALTER TABLE public.events DROP CONSTRAINT IF EXISTS events_titel_datum_ort_uhrzeit_key;

ALTER TABLE public.events
  ADD CONSTRAINT events_titel_datum_ort_uhrzeit_key UNIQUE NULLS NOT DISTINCT (titel, datum, ort, uhrzeit);

-- Kontrolle: muss genau die neue Regel zeigen
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.events'::regclass AND contype = 'u';
