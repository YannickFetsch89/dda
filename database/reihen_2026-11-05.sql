-- Reihen (wiederkehrende Events) – DiesDasDüsseldorf, 05.11.2026
-- Eine Reihe fasst Termine mit gleichem (bereinigtem) Titel am gleichen Ort zusammen. Sie hat eine
-- dauerhafte URL /reihe/<slug>, die immer den nächsten und alle kommenden Termine zeigt.
-- Die Zuordnung macht die Pipeline (pipeline/reihen_zuordnen.py, Service-Key). Der Slug wird beim
-- Anlegen festgelegt und danach nie mehr geändert (dauerhafte URL).
--
-- REIHENFOLGE: Dieses SQL VOR dem Deploy der Website ausführen (die Website liest events.reihe_id
-- und die Tabelle reihen).

CREATE TABLE IF NOT EXISTS public.reihen (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        TEXT NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
    -- Vergleichsschlüssel „titel|ort“ (normalisiert), daran erkennt die Pipeline die Reihe wieder
    schluessel  TEXT NOT NULL UNIQUE,
    titel       TEXT NOT NULL,
    ort         TEXT NOT NULL,
    kategorie   TEXT,
    erstellt_am TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.events ADD COLUMN IF NOT EXISTS reihe_id UUID REFERENCES public.reihen(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS events_reihe_id_idx ON public.events (reihe_id);

-- Lesen darf jeder (Website), schreiben nur der Service-Key (umgeht RLS)
ALTER TABLE public.reihen ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Reihen lesen" ON public.reihen;
CREATE POLICY "Reihen lesen" ON public.reihen FOR SELECT TO anon, authenticated USING (true);

-- Kontrolle
SELECT
    (SELECT count(*) FROM information_schema.columns
      WHERE table_schema = 'public' AND table_name = 'events' AND column_name = 'reihe_id') AS spalte_reihe_id,
    (SELECT count(*) FROM pg_policies WHERE tablename = 'reihen') AS policies_reihen,
    (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.reihen'::regclass) AS rls_aktiv;
