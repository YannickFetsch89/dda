-- SEO-Entscheidungen für lange abgelaufene Events – DiesDasDüsseldorf, 05.11.2026
-- Abgelaufene Eventseiten bleiben grundsätzlich online (HTTP 200). Erst für Events, die seit mehr als
-- 12 Monaten vorbei sind, kann ein Admin im Dashboard (Tab „SEO-Aufräumen“) entscheiden:
--   behalten      → Seite bleibt wie sie ist
--   weiterleiten  → 301 auf eine interne Seite (Reihe, Ortssuche oder Kategorie – nie die Startseite)
--   gone          → 410 Gone
-- Nichts passiert automatisch. Die Website (web/proxy.ts) liest die Entscheidungen mit dem anon-Key.

CREATE TABLE IF NOT EXISTS public.event_seo_entscheidungen (
    event_id        UUID PRIMARY KEY REFERENCES public.events(id) ON DELETE CASCADE,
    slug            TEXT NOT NULL UNIQUE,      -- Slug der Eventseite (/event/<kategorie>/<slug>)
    aktion          TEXT NOT NULL CHECK (aktion IN ('behalten', 'weiterleiten', 'gone')),
    -- Ziel nur als interner Pfad, nie die Startseite („/“ allein) und nie eine fremde Domain („//…“)
    ziel            TEXT CHECK (ziel IS NULL OR (ziel ~ '^/[^/]' AND length(ziel) <= 500)),
    entschieden_am  TIMESTAMPTZ NOT NULL DEFAULT now(),
    entschieden_von UUID,
    CHECK ((aktion = 'weiterleiten') = (ziel IS NOT NULL))
);

ALTER TABLE public.event_seo_entscheidungen ENABLE ROW LEVEL SECURITY;

-- Website (anon) liest die Entscheidungen, um 301/410 auszuliefern – enthält nur öffentliche URLs
DROP POLICY IF EXISTS "SEO-Entscheidungen lesen" ON public.event_seo_entscheidungen;
CREATE POLICY "SEO-Entscheidungen lesen" ON public.event_seo_entscheidungen
    FOR SELECT TO anon, authenticated USING (true);

-- Nur Admins entscheiden
DROP POLICY IF EXISTS "Admins entscheiden SEO" ON public.event_seo_entscheidungen;
CREATE POLICY "Admins entscheiden SEO" ON public.event_seo_entscheidungen
    FOR INSERT TO authenticated WITH CHECK (public.ist_admin());
DROP POLICY IF EXISTS "Admins ändern SEO" ON public.event_seo_entscheidungen;
CREATE POLICY "Admins ändern SEO" ON public.event_seo_entscheidungen
    FOR UPDATE TO authenticated USING (public.ist_admin()) WITH CHECK (public.ist_admin());
DROP POLICY IF EXISTS "Admins löschen SEO" ON public.event_seo_entscheidungen;
CREATE POLICY "Admins löschen SEO" ON public.event_seo_entscheidungen
    FOR DELETE TO authenticated USING (public.ist_admin());

-- Kontrolle
SELECT policyname, cmd, roles FROM pg_policies WHERE tablename = 'event_seo_entscheidungen' ORDER BY policyname;
