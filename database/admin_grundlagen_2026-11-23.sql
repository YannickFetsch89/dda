-- admin_grundlagen_2026-11-23.sql – DiesDasDüsseldorf
-- Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitt 5, S1 (Stufe 1a): Protokoll und Vorschläge für den neuen
-- Admin-Bereich unter admin.diesdas.events.
--
-- Im Supabase-SQL-Editor ausführen, VOR dem Deploy von Stufe 1a. Wiederholbar (idempotent).
-- Voraussetzung: auth_rollen.sql (public.ist_admin()).
--
-- admin_protokoll:   jede schreibende Admin-Aktion mit Vorher/Nachher. Nur lesen und anhängen, nie ändern/löschen.
-- admin_vorschlaege: Vorschläge der Pipeline statt SQL-Dateien (Plan 3.5). Die Pipeline schreibt als service_role,
--                    der Admin liest. Entschieden wird erst ab Stufe 1d über eigene Funktionen (S2).

BEGIN;

-- ── 1. Protokoll ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.admin_protokoll (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zeitpunkt   TIMESTAMPTZ NOT NULL DEFAULT now(),
    admin_id    UUID NOT NULL DEFAULT auth.uid(),
    aktion      TEXT NOT NULL CHECK (char_length(aktion) BETWEEN 1 AND 80),
    tabelle     TEXT CHECK (tabelle IS NULL OR char_length(tabelle) <= 80),
    ziel_id     TEXT CHECK (ziel_id IS NULL OR char_length(ziel_id) <= 200),
    vorher      JSONB,
    nachher     JSONB
);

CREATE INDEX IF NOT EXISTS admin_protokoll_zeit_idx ON public.admin_protokoll (zeitpunkt DESC);
CREATE INDEX IF NOT EXISTS admin_protokoll_ziel_idx ON public.admin_protokoll (tabelle, ziel_id);

ALTER TABLE public.admin_protokoll ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.admin_protokoll FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON public.admin_protokoll TO authenticated;
GRANT ALL ON public.admin_protokoll TO service_role;

DROP POLICY IF EXISTS admin_protokoll_lesen ON public.admin_protokoll;
CREATE POLICY admin_protokoll_lesen ON public.admin_protokoll FOR SELECT TO authenticated
    USING (public.ist_admin());

-- Anhängen nur als Admin und nur unter der eigenen ID (admin_id kommt aus auth.uid(), nicht aus dem Body)
DROP POLICY IF EXISTS admin_protokoll_anhaengen ON public.admin_protokoll;
CREATE POLICY admin_protokoll_anhaengen ON public.admin_protokoll FOR INSERT TO authenticated
    WITH CHECK (public.ist_admin() AND admin_id = auth.uid());
-- Kein UPDATE, kein DELETE: keine Policy, kein GRANT.


-- ── 2. Vorschläge ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.admin_vorschlaege (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    art             TEXT NOT NULL CHECK (art ~ '^[a-z_]{2,40}$'),
    ziel_tabelle    TEXT NOT NULL CHECK (char_length(ziel_tabelle) <= 80),
    ziel_id         TEXT CHECK (ziel_id IS NULL OR char_length(ziel_id) <= 200),
    -- je Art festgelegt (Plan 5, S1): z. B. dublette „<behalten-id>:<dubletten-id>“, gebiet „<event-id>“
    schluessel      TEXT NOT NULL CHECK (char_length(schluessel) BETWEEN 1 AND 300),
    vorschlag       JSONB NOT NULL DEFAULT '{}'::jsonb,
    begruendung     TEXT CHECK (begruendung IS NULL OR char_length(begruendung) <= 2000),
    status          TEXT NOT NULL DEFAULT 'offen' CHECK (status IN ('offen', 'angenommen', 'abgelehnt')),
    quelle_lauf     UUID,                 -- scraper_laeufe.id, falls aus einem Lauf
    erstellt_am     TIMESTAMPTZ NOT NULL DEFAULT now(),
    entschieden_von UUID,
    entschieden_am  TIMESTAMPTZ,
    -- Doppelvorschläge verhindern; die Pipeline schreibt mit ON CONFLICT DO NOTHING, abgelehnte bleiben liegen
    CONSTRAINT admin_vorschlaege_eindeutig UNIQUE (art, schluessel)
);

CREATE INDEX IF NOT EXISTS admin_vorschlaege_offen_idx ON public.admin_vorschlaege (art, erstellt_am DESC)
    WHERE status = 'offen';

ALTER TABLE public.admin_vorschlaege ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.admin_vorschlaege FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.admin_vorschlaege TO authenticated;
GRANT ALL ON public.admin_vorschlaege TO service_role;

DROP POLICY IF EXISTS admin_vorschlaege_lesen ON public.admin_vorschlaege;
CREATE POLICY admin_vorschlaege_lesen ON public.admin_vorschlaege FOR SELECT TO authenticated
    USING (public.ist_admin());
-- Entscheiden (UPDATE) nur über SECURITY-DEFINER-Funktionen aus S2 (Stufe 1d), daher hier kein UPDATE-Recht.

COMMIT;


-- ── Kontrolle (erwartet: 2 Tabellen, RLS an, 3 Policies) ──────────────────────
SELECT c.relname AS tabelle, c.relrowsecurity AS rls_an,
       (SELECT count(*) FROM pg_policies p WHERE p.schemaname = 'public' AND p.tablename = c.relname) AS policies
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relname IN ('admin_protokoll', 'admin_vorschlaege')
ORDER BY c.relname;
