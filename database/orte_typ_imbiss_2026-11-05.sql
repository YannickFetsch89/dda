-- Neuer Ort-Typ "imbiss" (Schnellimbiss: Döner, Gyros, Kebap, Imbiss-Pizzerien, Smash-Burger …)
-- Stand: 2026-11-05 · Im Supabase SQL-Editor ausführen, BEVOR die Orte umgestellt werden
-- (scraper/orte/imbiss_einteilen.py --ausfuehren) bzw. die angepasste Website live geht.
-- Wiederholbar: alte Typ-Regel suchen, entfernen und mit der erweiterten Liste neu anlegen.

DO $$
DECLARE
  regel TEXT;
BEGIN
  FOR regel IN
    SELECT con.conname
    FROM pg_constraint con
    WHERE con.conrelid = 'public.orte'::regclass
      AND con.contype = 'c'
      AND pg_get_constraintdef(con.oid) ILIKE '%typ%'
      AND pg_get_constraintdef(con.oid) ILIKE '%wochenendtipp%'
  LOOP
    EXECUTE format('ALTER TABLE public.orte DROP CONSTRAINT %I', regel);
    RAISE NOTICE 'Alte Regel entfernt: %', regel;
  END LOOP;
END $$;

ALTER TABLE public.orte DROP CONSTRAINT IF EXISTS orte_typ_check;

ALTER TABLE public.orte
  ADD CONSTRAINT orte_typ_check CHECK (typ IN (
    'restaurant', 'imbiss', 'cafe', 'kneipe', 'club',
    'spielplatz', 'ausflug', 'wochenendtipp'
  ));

-- Kontrolle: muss 'imbiss' enthalten
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.orte'::regclass AND contype = 'c' AND conname = 'orte_typ_check';
