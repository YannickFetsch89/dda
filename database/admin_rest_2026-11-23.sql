-- admin_rest_2026-11-23.sql – DiesDasDüsseldorf
-- Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitt 4.10, Stufe 5a: Konten in Zahlen und Sensibel-Treffer.
--
-- Im Supabase-SQL-Editor ausführen, VOR dem Deploy von Stufe 5a. Wiederholbar (CREATE OR REPLACE).
-- Voraussetzung: konten_2026-11-16.sql (profiles-Spalten, einwilligungen, merkliste, event_sensibel, -_ausnahmen,
-- sensibel_grund), konten_stammdaten_2026-11-17.sql, admin_magazin_2026-11-23.sql (admin_pflicht).
--
-- Der Admin-Token bekommt KEINE Tabellenrechte auf profiles, merkliste, event_sensibel. Alles über SECURITY-DEFINER-
-- Funktionen (Eigentümer postgres, zuerst admin_pflicht(), fester search_path, EXECUTE nur für authenticated).
-- Konten: bewusst nur Zahlen, nie Personen und keine Suche (Plan 4.10, Datenschutz). Löschung und Auskunft bleiben im
-- Supabase-Dashboard. Interessen: nur Werte mit mindestens 3 Konten; kleinere Gruppen fehlen ganz, gezählt wird nur,
-- wie viele Werte weggelassen sind (Cursor-Prüfung 5a, Befund 1).
-- Cursor-Prüfung 5a, Befund 2: Die Policies „Eigenes Profil lesen/ändern“ (auth_rollen.sql) ließen ein Admin-JWT ALLE
-- Profile lesen (Geburtsdatum, Interessen, Name). Sie gelten jetzt nur für die eigene Zeile. Wer sonst profiles liest:
-- die Rollenprüfung (eigene Zeile: web/lib/admin/sitzung.ts, dashboard/auth.py) und die Pipeline-Jobs (Service-Schlüssel,
-- umgeht RLS). ist_admin() ist SECURITY DEFINER und hängt nicht an dieser Policy.

BEGIN;

-- ── 1. Konten in Zahlen ──────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.admin_konten_kennzahlen()
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    jahr_beginn DATE := date_trunc('year', now() AT TIME ZONE 'Europe/Berlin')::date;
BEGIN
    PERFORM public.admin_pflicht();
    RETURN jsonb_build_object(
        'konten', (SELECT count(*) FROM public.profiles),
        'onboarding_fertig', (SELECT count(*) FROM public.profiles WHERE onboarding_fertig_am IS NOT NULL),
        'aktiv_30_tage', (SELECT count(*) FROM public.profiles WHERE letzte_aktivitaet_am > now() - interval '30 days'),
        'unter16_gesperrt', (SELECT count(*) FROM public.profiles WHERE unter16_gesperrt_am IS NOT NULL),
        'neu_je_woche', coalesce((
            SELECT jsonb_agg(jsonb_build_object('woche', w.woche, 'anzahl', w.anzahl) ORDER BY w.woche DESC)
            FROM (
                SELECT to_char(date_trunc('week', erstellt_am AT TIME ZONE 'Europe/Berlin'), 'YYYY-MM-DD') AS woche, count(*) AS anzahl
                FROM public.profiles
                WHERE erstellt_am > now() - interval '8 weeks'
                GROUP BY 1
            ) w), '[]'::jsonb),
        'einwilligungen', jsonb_build_object(
            'personalisierung', (SELECT count(*) FROM public.profiles WHERE personalisierung),
            'sensible_events', (SELECT count(*) FROM public.profiles WHERE sensible_events_erlaubt),
            'analyse', (SELECT count(*) FROM public.profiles WHERE analyse_erlaubt),
            'geburtstagsmail', (SELECT count(*) FROM public.profiles WHERE geburtstagsmail)
        ),
        'interessen', coalesce((
            SELECT jsonb_agg(jsonb_build_object('wert', i.wert, 'anzahl', i.anzahl) ORDER BY i.anzahl DESC, i.wert)
            FROM (
                SELECT k AS wert, count(*) AS anzahl
                FROM public.profiles p, jsonb_array_elements_text(coalesce(p.praeferenzen->'kategorien', '[]'::jsonb)) k
                WHERE p.personalisierung
                GROUP BY k
                HAVING count(*) >= 3
            ) i), '[]'::jsonb),
        'interessen_ausgeblendet', (
            SELECT count(*) FROM (
                SELECT k FROM public.profiles p, jsonb_array_elements_text(coalesce(p.praeferenzen->'kategorien', '[]'::jsonb)) k
                WHERE p.personalisierung GROUP BY k HAVING count(*) < 3
            ) x),
        'merkliste', jsonb_build_object(
            'konten_mit_eintraegen', (SELECT count(DISTINCT nutzer_id) FROM public.merkliste),
            'eintraege', (SELECT count(*) FROM public.merkliste)
        ),
        'geburtstagsmails_dieses_jahr', (SELECT count(*) FROM public.profiles WHERE geburtstagsmail_zuletzt >= jahr_beginn)
    );
END;
$$;


-- ── 2. Sensibel-Treffer ──────────────────────────────────────────────────────
-- Liste der Kennzeichnungen der letzten p_tage Tage (gesetzt_am) mit Event-Daten; dazu die Ausnahmen derselben Zeit.

CREATE OR REPLACE FUNCTION public.admin_sensibel_liste(p_tage INTEGER)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    tage INTEGER := greatest(1, least(coalesce(p_tage, 30), 400));
BEGIN
    PERFORM public.admin_pflicht();
    RETURN jsonb_build_object(
        'treffer', coalesce((
            SELECT jsonb_agg(jsonb_build_object(
                'event_id', s.event_id, 'grund', s.grund, 'quelle', s.quelle, 'gesetzt_am', s.gesetzt_am,
                'titel', e.titel, 'datum', e.datum, 'ort', e.ort, 'abgelehnt', e.abgelehnt,
                'gemerkt', (SELECT count(*) FROM public.merkliste m WHERE m.event_id = s.event_id))
                ORDER BY s.gesetzt_am DESC)
            FROM public.event_sensibel s JOIN public.events e ON e.id = s.event_id
            WHERE s.gesetzt_am > now() - make_interval(days => tage)), '[]'::jsonb),
        'ausnahmen', coalesce((
            SELECT jsonb_agg(jsonb_build_object('event_id', a.event_id, 'notiz', a.notiz, 'gesetzt_am', a.gesetzt_am,
                                                'titel', e.titel, 'datum', e.datum) ORDER BY a.gesetzt_am DESC)
            FROM public.event_sensibel_ausnahmen a JOIN public.events e ON e.id = a.event_id
            WHERE a.gesetzt_am > now() - make_interval(days => tage)), '[]'::jsonb)
    );
END;
$$;

-- Fehltreffer: Ausnahme eintragen und Kennzeichnung entfernen (Trigger events_sensibel_pruefen überspringt das Event
-- danach). Lockert nur: Ohne Kennzeichnung gilt für die Merkliste keine Sonderregel mehr.
CREATE OR REPLACE FUNCTION public.admin_sensibel_ausnahme(p_event UUID, p_notiz TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    s public.event_sensibel%ROWTYPE;
    notiz TEXT := left(nullif(btrim(coalesce(p_notiz, '')), ''), 300);
BEGIN
    PERFORM public.admin_pflicht();
    IF notiz IS NULL OR length(notiz) < 3 THEN RAISE EXCEPTION 'admin_grund_fehlt: Bitte kurz begründen (z. B. Theaterstück)'; END IF;
    IF NOT EXISTS (SELECT 1 FROM public.events WHERE id = p_event) THEN RAISE EXCEPTION 'admin_event_fehlt'; END IF;
    SELECT * INTO s FROM public.event_sensibel WHERE event_id = p_event;
    INSERT INTO public.event_sensibel_ausnahmen (event_id, notiz) VALUES (p_event, 'Admin: ' || notiz)
    ON CONFLICT (event_id) DO UPDATE SET notiz = EXCLUDED.notiz, gesetzt_am = now();
    DELETE FROM public.event_sensibel WHERE event_id = p_event;
    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('sensibel_ausnahme', 'event_sensibel', p_event::text,
            CASE WHEN s.event_id IS NULL THEN NULL ELSE jsonb_build_object('grund', s.grund, 'quelle', s.quelle) END,
            jsonb_build_object('notiz', notiz));
    RETURN jsonb_build_object('ok', true);
END;
$$;

-- Ausnahme zurücknehmen: Regeln neu anwenden (wie der Trigger), Treffer wird wieder gekennzeichnet
CREATE OR REPLACE FUNCTION public.admin_sensibel_ausnahme_aufheben(p_event UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    e public.events%ROWTYPE;
    gefunden TEXT;
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO e FROM public.events WHERE id = p_event;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_event_fehlt'; END IF;
    DELETE FROM public.event_sensibel_ausnahmen WHERE event_id = p_event;
    gefunden := public.sensibel_grund(e.titel, e.beschreibung, e.ort);
    IF gefunden IS NOT NULL THEN
        INSERT INTO public.event_sensibel (event_id, grund, quelle) VALUES (p_event, gefunden, 'regel')
        ON CONFLICT (event_id) DO NOTHING;
    END IF;
    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, nachher)
    VALUES ('sensibel_ausnahme_aufheben', 'event_sensibel', p_event::text, jsonb_build_object('grund', gefunden));
    RETURN jsonb_build_object('ok', true, 'grund', gefunden);
END;
$$;


-- ── 3. profiles: Lesen und Ändern nur die eigene Zeile (Cursor-Prüfung 5a, Befund 2) ──
DROP POLICY IF EXISTS "Eigenes Profil lesen" ON public.profiles;
CREATE POLICY "Eigenes Profil lesen" ON public.profiles
    FOR SELECT TO authenticated
    USING (id = (SELECT auth.uid()));

DROP POLICY IF EXISTS "Eigenes Profil ändern" ON public.profiles;
CREATE POLICY "Eigenes Profil ändern" ON public.profiles
    FOR UPDATE TO authenticated
    USING (id = (SELECT auth.uid()))
    WITH CHECK (id = (SELECT auth.uid()));


-- ── 4. Rechte ────────────────────────────────────────────────────────────────
DO $$
DECLARE
    f TEXT;
BEGIN
    FOREACH f IN ARRAY ARRAY[
        'admin_konten_kennzahlen()',
        'admin_sensibel_liste(integer)',
        'admin_sensibel_ausnahme(uuid, text)',
        'admin_sensibel_ausnahme_aufheben(uuid)'
    ] LOOP
        EXECUTE format('ALTER FUNCTION public.%s OWNER TO postgres', f);
        EXECUTE format('REVOKE EXECUTE ON FUNCTION public.%s FROM PUBLIC, anon', f);
        EXECUTE format('GRANT EXECUTE ON FUNCTION public.%s TO authenticated', f);
    END LOOP;
END $$;

COMMIT;


-- ── Kontrolle 1 (erwartet: 4 Zeilen, alle definer, anon_darf = false, authenticated_darf = true) ──
SELECT p.proname AS funktion,
       CASE WHEN p.prosecdef THEN 'definer' ELSE 'invoker' END AS sicherheit,
       has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_darf,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') AS authenticated_darf
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname IN ('admin_konten_kennzahlen', 'admin_sensibel_liste', 'admin_sensibel_ausnahme', 'admin_sensibel_ausnahme_aufheben')
ORDER BY 1;

-- ── Kontrolle 2 (erwartet: beide Policies nur mit „id = auth.uid()“, ohne ist_admin) ──
SELECT policyname, cmd, qual, with_check FROM pg_policies
WHERE schemaname = 'public' AND tablename = 'profiles' AND policyname IN ('Eigenes Profil lesen', 'Eigenes Profil ändern')
ORDER BY 1;
