-- Neue Event-Kategorie "stadtfuehrung" (Stadt-, Viertel-, kulinarische und Kneipenführungen)
-- Stand: 2026-11-05 · Im Supabase SQL-Editor ausführen, BEVOR die neuen Scraper deployt werden
-- (sonst lehnt die Datenbank Events mit kategorie = 'stadtfuehrung' ab).
--
-- Die bisherige CHECK-Regel auf events.kategorie wird gesucht (Name kann je nach Anlage abweichen),
-- entfernt und mit der erweiterten Liste neu angelegt.

DO $$
DECLARE
  regel TEXT;
BEGIN
  FOR regel IN
    SELECT con.conname
    FROM pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
    WHERE nsp.nspname = 'public'
      AND rel.relname = 'events'
      AND con.contype = 'c'
      AND pg_get_constraintdef(con.oid) ILIKE '%kategorie%'
  LOOP
    EXECUTE format('ALTER TABLE public.events DROP CONSTRAINT %I', regel);
    RAISE NOTICE 'Alte Regel entfernt: %', regel;
  END LOOP;
END $$;

ALTER TABLE public.events
  ADD CONSTRAINT events_kategorie_check CHECK (kategorie IN (
    'kultur', 'musik', 'food', 'sport',
    'outdoor', 'stadtfuehrung', 'community', 'nightlife',
    'family', 'dating', 'sonstiges'
  ));

-- Kontrolle: muss 'stadtfuehrung' enthalten
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.events'::regclass AND contype = 'c' AND conname = 'events_kategorie_check';
