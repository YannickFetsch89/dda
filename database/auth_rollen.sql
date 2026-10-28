-- auth_rollen.sql – DiesDasDüsseldorf
-- Benutzer, Rollen (admin | user) und Zugriffsregeln (Row Level Security)
-- Erstellt: 2026-10-28
--
-- Ausführen im Supabase SQL Editor. Das Skript ist wiederholbar (idempotent).
--
-- VORAUSSETZUNG: Die Pipeline muss vorher auf den service_role-Key umgestellt sein
-- (SUPABASE_SERVICE_KEY in der .env auf dem Server). Ab hier darf der anon-Key
-- Events nur noch lesen – Schreiben geht nur noch als Admin oder mit service_role.
--
-- Rollen:
--   admin – Zugang zu admin.diesdas.events, darf Events freigeben/ablehnen/featuren
--   user  – Website-/App-Nutzer mit eigenem Profil und Präferenzen (Standard bei Registrierung)


-- ── Rollen-Typ ───────────────────────────────────────────────────────────────

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'app_rolle') THEN
        CREATE TYPE public.app_rolle AS ENUM ('admin', 'user');
    END IF;
END $$;


-- ── Profile (1:1 zu auth.users) ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.profiles (
    id              UUID PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
    rolle           public.app_rolle NOT NULL DEFAULT 'user',
    anzeigename     TEXT,
    -- Präferenzen bewusst flexibel (z.B. {"kategorien": ["musik"], "stadtteile": ["Bilk"]})
    praeferenzen    JSONB NOT NULL DEFAULT '{}'::jsonb,
    erstellt_am     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    aktualisiert_am TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_profiles_rolle ON public.profiles (rolle);


-- ── Hilfsfunktion: Ist der angemeldete Nutzer Admin? ─────────────────────────
-- SECURITY DEFINER, damit die Prüfung selbst nicht an der RLS von profiles hängt.

CREATE OR REPLACE FUNCTION public.ist_admin()
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = (SELECT auth.uid()) AND rolle = 'admin'
    );
$$;

REVOKE EXECUTE ON FUNCTION public.ist_admin() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ist_admin() TO anon, authenticated;


-- ── Profil automatisch bei Registrierung anlegen (Rolle immer 'user') ────────

CREATE OR REPLACE FUNCTION public.profil_anlegen()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.profiles (id, anzeigename)
    VALUES (NEW.id, NEW.raw_user_meta_data ->> 'anzeigename')
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS profil_bei_registrierung ON auth.users;
CREATE TRIGGER profil_bei_registrierung
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.profil_anlegen();

-- Profile für bereits vorhandene Nutzer nachziehen
INSERT INTO public.profiles (id)
SELECT id FROM auth.users
ON CONFLICT (id) DO NOTHING;


-- ── Rolle schützen: Nutzer dürfen sich nicht selbst zum Admin machen ─────────
-- Über die API (Rolle "authenticated") dürfen nur Admins Rollen ändern.
-- Im SQL Editor (postgres) und mit service_role ist es erlaubt.

CREATE OR REPLACE FUNCTION public.profil_vor_update()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    IF NEW.rolle IS DISTINCT FROM OLD.rolle
       AND current_user IN ('authenticated', 'anon')
       AND NOT public.ist_admin() THEN
        RAISE EXCEPTION 'Nur Admins dürfen Rollen ändern';
    END IF;
    NEW.aktualisiert_am := NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS profil_vor_update ON public.profiles;
CREATE TRIGGER profil_vor_update
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.profil_vor_update();


-- ── RLS: profiles ────────────────────────────────────────────────────────────

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Eigenes Profil lesen" ON public.profiles;
CREATE POLICY "Eigenes Profil lesen" ON public.profiles
    FOR SELECT TO authenticated
    USING (id = (SELECT auth.uid()) OR public.ist_admin());

DROP POLICY IF EXISTS "Eigenes Profil ändern" ON public.profiles;
CREATE POLICY "Eigenes Profil ändern" ON public.profiles
    FOR UPDATE TO authenticated
    USING (id = (SELECT auth.uid()) OR public.ist_admin())
    WITH CHECK (id = (SELECT auth.uid()) OR public.ist_admin());

-- Kein INSERT/DELETE über die API: Anlegen per Trigger, Löschen über auth.users (CASCADE)


-- ── RLS: events ──────────────────────────────────────────────────────────────
-- Bisherige Policies entfernen, damit keine alte "alles erlaubt"-Regel übrig bleibt.

DO $$
DECLARE
    p RECORD;
BEGIN
    FOR p IN SELECT policyname FROM pg_policies WHERE schemaname = 'public' AND tablename = 'events' LOOP
        EXECUTE format('DROP POLICY %I ON public.events', p.policyname);
    END LOOP;
END $$;

ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

-- Öffentlich (Website/App): nur nicht abgelehnte Events. Admins sehen alles.
CREATE POLICY "Events lesen" ON public.events
    FOR SELECT TO anon, authenticated
    USING (abgelehnt = FALSE OR public.ist_admin());

-- Nur Admins dürfen Events ändern (Dashboard: ablehnen, Featured-Tiers)
CREATE POLICY "Admins ändern Events" ON public.events
    FOR UPDATE TO authenticated
    USING (public.ist_admin())
    WITH CHECK (public.ist_admin());

-- INSERT/DELETE nur mit service_role (Pipeline), die RLS umgeht.


-- ── Ersten Admin festlegen ───────────────────────────────────────────────────
-- 1. Supabase → Authentication → Users → "Add user" (E-Mail + Passwort, "Auto Confirm")
-- 2. Dann hier die E-Mail eintragen und nur diese Zeile ausführen:
--
-- UPDATE public.profiles SET rolle = 'admin'
-- WHERE id = (SELECT id FROM auth.users WHERE email = 'name@example.com');
