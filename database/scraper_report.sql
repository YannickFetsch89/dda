-- scraper_report.sql – DiesDasDüsseldorf
-- Protokoll der Pipeline-Läufe und der Ergebnisse jeder einzelnen Quelle.
-- Grundlage für den Tab "Scraper-Report" im Admin-Dashboard.
-- Erstellt: 2026-11-04
--
-- Ausführen im Supabase SQL Editor. Das Skript ist wiederholbar (idempotent).
-- Voraussetzung: auth_rollen.sql (Funktion public.ist_admin()) wurde bereits ausgeführt.
--
-- Solange die Tabellen fehlen, läuft die Pipeline normal weiter und meldet nur eine Warnung.


-- ── Ein Eintrag pro Pipeline-Lauf ────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.scraper_laeufe (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gestartet_am        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    beendet_am          TIMESTAMPTZ,
    status              TEXT NOT NULL DEFAULT 'laeuft' CHECK (status IN ('laeuft', 'erfolgreich', 'fehler')),
    ausloeser           TEXT,                 -- zeitplan | manuell | lokal
    github_run_url      TEXT,                 -- Link zum GitHub-Actions-Lauf (Log)
    events_gesammelt    INTEGER,              -- Summe aller Scraper vor der Deduplizierung
    events_nach_dedup   INTEGER,
    neu_gespeichert     INTEGER,
    duplikate           INTEGER,
    angereichert        INTEGER,
    speicher_fehler     INTEGER,
    kategorisiert       INTEGER,
    captions            INTEGER,
    gepostet            INTEGER,
    fehlermeldung       TEXT                  -- nur wenn der Lauf abgebrochen ist
);

CREATE INDEX IF NOT EXISTS idx_scraper_laeufe_gestartet ON public.scraper_laeufe (gestartet_am DESC);


-- ── Ein Eintrag pro Quelle und Lauf ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.scraper_ergebnisse (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lauf_id             UUID NOT NULL REFERENCES public.scraper_laeufe (id) ON DELETE CASCADE,
    quelle              TEXT NOT NULL,        -- Anzeigename, z.B. "zakk"
    tier                SMALLINT,
    status              TEXT NOT NULL CHECK (status IN ('ok', 'leer', 'saisonal', 'uebersprungen', 'fehler')),
    anzahl              INTEGER NOT NULL DEFAULT 0,   -- vom Scraper geliefert
    neu_gespeichert     INTEGER,              -- davon neu in der Datenbank
    dauer_sekunden      NUMERIC(7,1),
    warnungen           INTEGER NOT NULL DEFAULT 0,
    fehler              INTEGER NOT NULL DEFAULT 0,
    meldung             TEXT,                 -- letzte Warnung/Fehlermeldung bzw. Hinweis
    erstellt_am         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scraper_ergebnisse_lauf   ON public.scraper_ergebnisse (lauf_id);
CREATE INDEX IF NOT EXISTS idx_scraper_ergebnisse_quelle ON public.scraper_ergebnisse (quelle, erstellt_am DESC);


-- ── RLS: Lesen nur für Admins, Schreiben nur Pipeline (service_role umgeht RLS) ──

ALTER TABLE public.scraper_laeufe     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scraper_ergebnisse ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Admins lesen Läufe" ON public.scraper_laeufe;
CREATE POLICY "Admins lesen Läufe" ON public.scraper_laeufe
    FOR SELECT TO authenticated
    USING (public.ist_admin());

DROP POLICY IF EXISTS "Admins lesen Ergebnisse" ON public.scraper_ergebnisse;
CREATE POLICY "Admins lesen Ergebnisse" ON public.scraper_ergebnisse
    FOR SELECT TO authenticated
    USING (public.ist_admin());
