-- Neuer Ort-Typ "weihnachtsmarkt" (Saison-Guide Weihnachtsmärkte, Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, Schritt 1)
-- Stand: 2026-11-17 · Im Supabase SQL-Editor ausführen, BEVOR scraper/weihnachtsmaerkte/import_maerkte.py läuft.
-- Wiederholbar: prüft vorab alle vorhandenen Typen, entfernt die alte Typ-Regel und legt sie mit der vollständigen,
-- erweiterten Liste neu an (dieselbe Liste wie database/orte_typ_imbiss_2026-11-05.sql plus 'weihnachtsmarkt').

-- 1) Vorab-Prüfung: Jeder Typ, der in der Tabelle steht, muss in der neuen Liste vorkommen – sonst Abbruch,
--    damit die neue Regel keine bestehende Zeile ablehnt.
DO $$
DECLARE
  fremd TEXT;
BEGIN
  SELECT string_agg(DISTINCT typ, ', ') INTO fremd
  FROM public.orte
  WHERE typ NOT IN (
    'restaurant', 'imbiss', 'cafe', 'kneipe', 'club',
    'spielplatz', 'ausflug', 'wochenendtipp', 'weihnachtsmarkt'
  );
  IF fremd IS NOT NULL THEN
    RAISE EXCEPTION 'Abbruch: unbekannte Typen in public.orte: % – Liste ergänzen, nichts geändert', fremd;
  END IF;
END $$;

-- 2) Alte Typ-Regel(n) entfernen (auch unter anderem Namen)
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

-- 3) Neue Regel: vollständige Liste plus 'weihnachtsmarkt'
ALTER TABLE public.orte
  ADD CONSTRAINT orte_typ_check CHECK (typ IN (
    'restaurant', 'imbiss', 'cafe', 'kneipe', 'club',
    'spielplatz', 'ausflug', 'wochenendtipp', 'weihnachtsmarkt'
  ));

-- 4) Kontrolle: muss 'weihnachtsmarkt' enthalten
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'public.orte'::regclass AND contype = 'c' AND conname = 'orte_typ_check';
