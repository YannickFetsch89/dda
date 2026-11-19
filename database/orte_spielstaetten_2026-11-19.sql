-- Ortsseiten (/orte): Typ „spielstaette“, Säle (parent_id), Zuordnung events.ort_id, Weiterleitungen, Schutz-Trigger
-- Plan docs/plan-locations-2026-11-18.md (freigegeben 19.11.2026), Abschnitt 3.3, Schritt 2, Deploy-Punkt 1.
-- Stand: 2026-11-19 · Im Supabase SQL-Editor ausführen, BEVOR der Pipeline-Code mit Schritt 1d deployt wird
-- (sonst scheitert das Speichern an der fehlenden Spalte events.ort_id).
-- Wiederholbar. Danach: database/orte_spielstaetten_trigger_probe_2026-11-19.sql ausführen (erwartet „alle ok“).
-- schema_orte.sql bleibt unverändert.

-- ── 1) Typ „spielstaette“ ────────────────────────────────────────────────────────────────────────────────────────
-- Vorab-Prüfung: Jeder vorhandene Typ muss in der neuen Liste vorkommen – sonst Abbruch, nichts geändert
DO $$
DECLARE
  fremd TEXT;
BEGIN
  SELECT string_agg(DISTINCT typ, ', ') INTO fremd
  FROM public.orte
  WHERE typ NOT IN (
    'restaurant', 'imbiss', 'cafe', 'kneipe', 'club',
    'spielplatz', 'ausflug', 'wochenendtipp', 'weihnachtsmarkt', 'spielstaette'
  );
  IF fremd IS NOT NULL THEN
    RAISE EXCEPTION 'Abbruch: unbekannte Typen in public.orte: % – Liste ergänzen, nichts geändert', fremd;
  END IF;
END $$;

-- Alte Typ-Regel(n) entfernen (auch unter anderem Namen)
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
    'spielplatz', 'ausflug', 'wochenendtipp', 'weihnachtsmarkt', 'spielstaette'
  ));

-- ── 2) Säle und Standorte: orte.parent_id ────────────────────────────────────────────────────────────────────────
ALTER TABLE public.orte ADD COLUMN IF NOT EXISTS parent_id UUID;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'orte_parent_id_fkey') THEN
    ALTER TABLE public.orte
      ADD CONSTRAINT orte_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.orte(id) ON DELETE SET NULL;
  END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_orte_parent_id ON public.orte (parent_id) WHERE parent_id IS NOT NULL;

-- ── 3) Zuordnung Event → Ort: events.ort_id (für jeden Treffer, auch Guides und Clubs; B4 „Folgen“) ─────────────
ALTER TABLE public.events ADD COLUMN IF NOT EXISTS ort_id UUID;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'events_ort_id_fkey') THEN
    ALTER TABLE public.events
      ADD CONSTRAINT events_ort_id_fkey FOREIGN KEY (ort_id) REFERENCES public.orte(id) ON DELETE SET NULL;
  END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_events_ort_id ON public.events (ort_id) WHERE ort_id IS NOT NULL;

-- ── 4) Weiterleitungen alter Slugs: Ziel ist eine Zeile, die URL bildet der Proxy zur Laufzeit (Plan 3.3 Punkt 4) ─
CREATE TABLE IF NOT EXISTS public.ort_weiterleitungen (
  alter_slug   TEXT PRIMARY KEY,
  ziel_ort_id  UUID REFERENCES public.orte(id) ON DELETE SET NULL,   -- leer → /orte
  grund        TEXT,
  erstellt_am  TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ort_weiterleitungen_ziel ON public.ort_weiterleitungen (ziel_ort_id);

-- Lesen für alle (auch der anonyme Schlüssel des Proxys), Schreiben nur mit dem Service-Schlüssel
ALTER TABLE public.ort_weiterleitungen ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ort_weiterleitungen_lesen ON public.ort_weiterleitungen;
CREATE POLICY ort_weiterleitungen_lesen ON public.ort_weiterleitungen FOR SELECT USING (true);
DROP POLICY IF EXISTS ort_weiterleitungen_admin ON public.ort_weiterleitungen;
CREATE POLICY ort_weiterleitungen_admin ON public.ort_weiterleitungen FOR ALL USING (auth.role() = 'service_role');

-- ── 5) Schutz-Trigger (Plan 3.3 Punkt 8) ────────────────────────────────────────────────────────────────────────
-- Eine ausgelieferte URL endet nie als 404:
--   a) Spielstätte gelöscht, abgeschaltet, Slug geändert oder Typ weg von 'spielstaette' → nur mit Weiterleitung
--      (alter_slug = OLD.slug). Erst die Weiterleitung einfügen, dann ändern.
--   b) Zeile JEDES Typs gelöscht oder abgeschaltet, die noch aktive Kinder hat (Säle, auch bei Guide-Häusern wie zakk)
--      → Abbruch; Kinder vorher umhängen oder selbst mit Weiterleitung abschalten.
--   c) Zeile JEDES Typs gelöscht oder abgeschaltet, auf die noch eine Weiterleitung zeigt (ziel_ort_id = OLD.id)
--      → Abbruch; Einträge vorher umhängen (UPDATE ort_weiterleitungen SET ziel_ort_id = … WHERE ziel_ort_id = …).
CREATE OR REPLACE FUNCTION public.orte_schutz()
RETURNS TRIGGER AS $$
DECLARE
  geloescht   BOOLEAN := TG_OP = 'DELETE';
  abgeschaltet BOOLEAN := TG_OP = 'UPDATE' AND COALESCE(OLD.aktiv, false) AND NOT COALESCE(NEW.aktiv, false);
  slug_neu    BOOLEAN := TG_OP = 'UPDATE' AND NEW.slug IS DISTINCT FROM OLD.slug;
  typ_weg     BOOLEAN := TG_OP = 'UPDATE' AND NEW.typ IS DISTINCT FROM OLD.typ;
BEGIN
  -- a) Weiterleitungspflicht für den eigenen Slug, nur bei Spielstätten
  IF OLD.typ = 'spielstaette' AND (geloescht OR abgeschaltet OR slug_neu OR typ_weg)
     AND NOT EXISTS (SELECT 1 FROM public.ort_weiterleitungen w WHERE w.alter_slug = OLD.slug) THEN
    RAISE EXCEPTION 'orte_schutz: Spielstätte „%“ (%) – zuerst Weiterleitung für den alten Slug anlegen',
      OLD.name, OLD.slug;
  END IF;
  -- b) und c) bei jeder Zeile
  IF geloescht OR abgeschaltet THEN
    IF EXISTS (SELECT 1 FROM public.orte k WHERE k.parent_id = OLD.id AND k.aktiv) THEN
      RAISE EXCEPTION 'orte_schutz: „%“ (%) hat noch aktive Säle – zuerst umhängen oder mit Weiterleitung abschalten',
        OLD.name, OLD.slug;
    END IF;
    IF EXISTS (SELECT 1 FROM public.ort_weiterleitungen w WHERE w.ziel_ort_id = OLD.id) THEN
      RAISE EXCEPTION 'orte_schutz: auf „%“ (%) zeigen noch Weiterleitungen – zuerst umhängen', OLD.name, OLD.slug;
    END IF;
  END IF;
  IF geloescht THEN
    RETURN OLD;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_orte_schutz ON public.orte;
CREATE TRIGGER trg_orte_schutz
  BEFORE DELETE OR UPDATE OF aktiv, slug, typ ON public.orte
  FOR EACH ROW
  EXECUTE FUNCTION public.orte_schutz();

-- ── 6) Kontrolle ────────────────────────────────────────────────────────────────────────────────────────────────
SELECT
  (SELECT pg_get_constraintdef(oid) ILIKE '%spielstaette%' FROM pg_constraint
    WHERE conrelid = 'public.orte'::regclass AND conname = 'orte_typ_check')                       AS typ_ok,
  EXISTS (SELECT 1 FROM information_schema.columns
          WHERE table_name = 'orte' AND column_name = 'parent_id')                                  AS parent_id_ok,
  EXISTS (SELECT 1 FROM information_schema.columns
          WHERE table_name = 'events' AND column_name = 'ort_id')                                   AS ort_id_ok,
  EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ort_weiterleitungen')         AS weiterleitungen_ok,
  EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_orte_schutz')                                AS trigger_ok;
