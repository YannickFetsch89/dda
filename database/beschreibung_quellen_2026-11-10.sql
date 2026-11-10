-- Event-Beschreibungen aus Veranstalter-Quellen (pipeline/beschreibung_quellen.py)
-- Im Supabase-SQL-Editor ausführen – VOR dem Deploy (die Pipeline liest beschreibung_quelle).

-- 1) Längengrenze der Beschreibung entfernen (früher CHECK char_length(beschreibung) <= 300)
DO $$
DECLARE c record;
BEGIN
  FOR c IN SELECT conname FROM pg_constraint
           WHERE conrelid = 'public.events'::regclass AND contype = 'c'
             AND pg_get_constraintdef(oid) ILIKE '%beschreibung%'
  LOOP
    EXECUTE format('ALTER TABLE public.events DROP CONSTRAINT %I', c.conname);
  END LOOP;
END $$;

-- 2) Herkunft der Beschreibung und Zeitpunkt der Suche
ALTER TABLE events ADD COLUMN IF NOT EXISTS beschreibung_quelle text;
ALTER TABLE events ADD COLUMN IF NOT EXISTS beschreibung_gesucht_am timestamptz;
COMMENT ON COLUMN events.beschreibung_quelle IS 'URL der Veranstalter-Seite, aus der die Beschreibung umgeschrieben wurde';
COMMENT ON COLUMN events.beschreibung_gesucht_am IS 'Wann nach einer Beschreibungsquelle gesucht wurde (auch ohne Fund) – verhindert erneute Suche';
