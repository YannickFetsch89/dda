-- admin_quellen_2026-11-24.sql – DiesDasDüsseldorf
-- Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitt 4.10, Stufe 5b: Quellen an/aus.
--
-- Im Supabase-SQL-Editor ausführen, VOR dem Deploy von Stufe 5b. Wiederholbar.
-- Voraussetzung: auth_rollen.sql (ist_admin).
--
-- Eine Zeile je abgeschalteter (oder wieder eingeschalteter) Quelle; der Name ist der Anzeigename aus QUELLEN in
-- main.py. Fehlt eine Quelle in der Tabelle, läuft sie (Standard: an). main.py liest die Tabelle zu Beginn des Laufs
-- mit dem Service-Schlüssel und überspringt abgeschaltete Quellen. Die Events einer abgeschalteten Quelle bleiben.

BEGIN;

CREATE TABLE IF NOT EXISTS public.quellen_einstellungen (
    quelle        TEXT PRIMARY KEY CHECK (char_length(quelle) BETWEEN 1 AND 120),
    aktiv         BOOLEAN NOT NULL DEFAULT true,
    grund         TEXT CHECK (grund IS NULL OR char_length(grund) <= 300),
    geaendert_am  TIMESTAMPTZ NOT NULL DEFAULT now(),
    geaendert_von UUID DEFAULT auth.uid()
);

COMMENT ON TABLE public.quellen_einstellungen IS
    'Quellen an/aus (Plan Admin-Dashboard 4.10). Nicht aufgeführte Quellen laufen. main.py liest die Tabelle.';

ALTER TABLE public.quellen_einstellungen ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.quellen_einstellungen FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.quellen_einstellungen TO authenticated;

DROP POLICY IF EXISTS quellen_admin_lesen ON public.quellen_einstellungen;
CREATE POLICY quellen_admin_lesen ON public.quellen_einstellungen
    FOR SELECT TO authenticated USING (public.ist_admin());

DROP POLICY IF EXISTS quellen_admin_anlegen ON public.quellen_einstellungen;
CREATE POLICY quellen_admin_anlegen ON public.quellen_einstellungen
    FOR INSERT TO authenticated WITH CHECK (public.ist_admin());

DROP POLICY IF EXISTS quellen_admin_aendern ON public.quellen_einstellungen;
CREATE POLICY quellen_admin_aendern ON public.quellen_einstellungen
    FOR UPDATE TO authenticated USING (public.ist_admin()) WITH CHECK (public.ist_admin());

COMMIT;


-- ── Kontrolle (erwartet: Tabelle da, drei Policies, anon ohne Rechte) ──
SELECT 'tabelle' AS art, to_regclass('public.quellen_einstellungen')::text AS wert
UNION ALL
SELECT 'policy', policyname FROM pg_policies WHERE schemaname = 'public' AND tablename = 'quellen_einstellungen'
UNION ALL
SELECT 'anon_darf_lesen', has_table_privilege('anon', 'public.quellen_einstellungen', 'SELECT')::text
ORDER BY 1, 2;
