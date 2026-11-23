-- newsletter_doi_2026-11-23.sql – DiesDasDüsseldorf
-- Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitt 4.9, Stufe 4: Newsletter mit Double-Opt-in.
--
-- Im Supabase-SQL-Editor ausführen, VOR dem Deploy von Stufe 4. Wiederholbar.
-- Voraussetzung: meldungen_newsletter_2026-11-05.sql, meldungen_haertung_2026-11-05.sql (anon ohne Rechte,
-- Admins lesen/ändern/löschen per ist_admin()).
--
-- Ablauf (E9): Die Website legt die Anmeldung an (Service-Schlüssel, serverseitig). Der Job
-- pipeline/newsletter_bestaetigung.py (alle 15 Minuten, .github/workflows/newsletter.yml, nur mit NEWSLETTER_AKTIV=1)
-- beansprucht offene Anmeldungen und schickt die Bestätigungsmail. Bestätigen und Abmelden laufen über HMAC-Tokens
-- (eigener Schlüssel NEWSLETTER_TOKEN_SCHLUESSEL) auf der Website. Abmelden löscht die Zeile sofort – so verspricht es
-- die Datenschutzerklärung (Abschnitt 11). Unbestätigte Anmeldungen löscht der Job 30 Tage nach der Bestätigungsmail.
-- Bestehende Anmeldungen (ohne Double-Opt-in) bekommen einmal die Bestätigungsmail, wie in der Datenschutzerklärung
-- angekündigt.

BEGIN;

-- ── 1. Spalten ───────────────────────────────────────────────────────────────
ALTER TABLE public.newsletter_anmeldungen
    ADD COLUMN IF NOT EXISTS bestaetigung_gesendet_am TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS bestaetigung_zugestellt_am TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS mails_gesendet INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN public.newsletter_anmeldungen.bestaetigung_gesendet_am IS
    'Zeitpunkt, zu dem der Job die Anmeldung für die Bestätigungsmail beansprucht hat; NULL = Mail steht aus.';
COMMENT ON COLUMN public.newsletter_anmeldungen.bestaetigung_zugestellt_am IS
    'Zeitpunkt, zu dem der Mailserver die letzte Bestätigungsmail angenommen hat (Cursor-Prüfung 4, Befund 3).';
COMMENT ON COLUMN public.newsletter_anmeldungen.mails_gesendet IS
    'Anzahl der zugestellten Bestätigungsmails an diese Adresse (höchstens 3, Schutz vor Missbrauch des Formulars).';

CREATE INDEX IF NOT EXISTS newsletter_offen_idx ON public.newsletter_anmeldungen (erstellt_am)
    WHERE bestaetigt_am IS NULL AND bestaetigung_gesendet_am IS NULL;


-- ── 2. Job: Anmeldungen für die Bestätigungsmail beanspruchen ────────────────
-- Gegen Doppelversand bei überlappenden Läufen (SKIP LOCKED). Nur service_role. Cursor-Prüfung 4, Befund 3: Ein
-- Anspruch ohne Zustellung, der älter als 30 Minuten ist (Lauf abgebrochen), wird wieder aufgenommen. Gezählt wird erst
-- die Zustellung (newsletter_bestaetigung_versandt).

CREATE OR REPLACE FUNCTION public.newsletter_bestaetigung_beanspruchen(p_anzahl INTEGER)
RETURNS TABLE (id UUID, email TEXT)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    UPDATE public.newsletter_anmeldungen n
    SET bestaetigung_gesendet_am = now(), bestaetigung_zugestellt_am = NULL
    WHERE n.id IN (
        SELECT o.id FROM public.newsletter_anmeldungen o
        WHERE o.bestaetigt_am IS NULL AND o.abgemeldet_am IS NULL AND o.mails_gesendet < 3
          AND (o.bestaetigung_gesendet_am IS NULL
               OR (o.bestaetigung_zugestellt_am IS NULL AND o.bestaetigung_gesendet_am < now() - interval '30 minutes'))
        ORDER BY o.erstellt_am
        LIMIT greatest(1, least(p_anzahl, 200))
        FOR UPDATE SKIP LOCKED
    )
    RETURNING n.id, n.email;
$$;

-- Mailserver hat die Mail angenommen → zugestellt, zählt
CREATE OR REPLACE FUNCTION public.newsletter_bestaetigung_versandt(p_id UUID)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    UPDATE public.newsletter_anmeldungen
    SET bestaetigung_zugestellt_am = now(), mails_gesendet = mails_gesendet + 1
    WHERE id = p_id;
$$;

-- Versand gescheitert → wieder offen (der nächste Lauf versucht es erneut)
CREATE OR REPLACE FUNCTION public.newsletter_bestaetigung_freigeben(p_id UUID)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
    UPDATE public.newsletter_anmeldungen
    SET bestaetigung_gesendet_am = NULL
    WHERE id = p_id AND bestaetigt_am IS NULL AND bestaetigung_zugestellt_am IS NULL;
$$;

-- Unbestätigte Anmeldungen 30 Tage nach der (letzten) zugestellten Bestätigungsmail löschen. Rückgabe: Anzahl.
CREATE OR REPLACE FUNCTION public.newsletter_aufraeumen()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    n INTEGER;
BEGIN
    DELETE FROM public.newsletter_anmeldungen
    WHERE bestaetigt_am IS NULL AND bestaetigung_zugestellt_am < now() - interval '30 days';
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN n;
END;
$$;


-- ── 3. Admin: Zahlen für die Übersicht ───────────────────────────────────────
CREATE OR REPLACE FUNCTION public.admin_newsletter_zahlen()
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    PERFORM public.admin_pflicht();
    RETURN jsonb_build_object(
        'bestaetigt', (SELECT count(*) FROM public.newsletter_anmeldungen WHERE bestaetigt_am IS NOT NULL),
        'wartet_auf_bestaetigung', (SELECT count(*) FROM public.newsletter_anmeldungen
                                    WHERE bestaetigt_am IS NULL AND bestaetigung_zugestellt_am IS NOT NULL),
        'mail_steht_aus', (SELECT count(*) FROM public.newsletter_anmeldungen
                           WHERE bestaetigt_am IS NULL AND bestaetigung_zugestellt_am IS NULL AND mails_gesendet < 3),
        'neu_7_tage', (SELECT count(*) FROM public.newsletter_anmeldungen WHERE erstellt_am > now() - interval '7 days')
    );
END;
$$;


-- ── 4. Rechte ────────────────────────────────────────────────────────────────
DO $$
DECLARE
    f TEXT;
BEGIN
    FOREACH f IN ARRAY ARRAY[
        'newsletter_bestaetigung_beanspruchen(integer)',
        'newsletter_bestaetigung_freigeben(uuid)',
        'newsletter_bestaetigung_versandt(uuid)',
        'newsletter_aufraeumen()'
    ] LOOP
        EXECUTE format('ALTER FUNCTION public.%s OWNER TO postgres', f);
        EXECUTE format('REVOKE EXECUTE ON FUNCTION public.%s FROM PUBLIC, anon, authenticated', f);
        EXECUTE format('GRANT EXECUTE ON FUNCTION public.%s TO service_role', f);
    END LOOP;
    ALTER FUNCTION public.admin_newsletter_zahlen() OWNER TO postgres;
    REVOKE EXECUTE ON FUNCTION public.admin_newsletter_zahlen() FROM PUBLIC, anon;
    GRANT EXECUTE ON FUNCTION public.admin_newsletter_zahlen() TO authenticated;
END $$;

COMMIT;


-- ── Kontrolle ────────────────────────────────────────────────────────────────
-- Erwartet: 3 Spalten; 4 newsletter_*-Funktionen nur service_role (anon/authenticated false), admin_newsletter_zahlen
-- authenticated true; dazu die Zahl der Anmeldungen, die nach dem Einschalten die Bestätigungsmail bekommen.
SELECT 'spalte' AS art, column_name AS name, NULL::boolean AS anon_darf, NULL::boolean AS authenticated_darf
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'newsletter_anmeldungen'
  AND column_name IN ('bestaetigung_gesendet_am', 'bestaetigung_zugestellt_am', 'mails_gesendet')
UNION ALL
SELECT 'funktion', p.proname, has_function_privilege('anon', p.oid, 'EXECUTE'), has_function_privilege('authenticated', p.oid, 'EXECUTE')
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname IN ('newsletter_bestaetigung_beanspruchen', 'newsletter_bestaetigung_freigeben', 'newsletter_bestaetigung_versandt',
                    'newsletter_aufraeumen', 'admin_newsletter_zahlen')
UNION ALL
SELECT 'mail_steht_aus', count(*)::text, NULL, NULL FROM public.newsletter_anmeldungen
WHERE bestaetigt_am IS NULL AND bestaetigung_zugestellt_am IS NULL
ORDER BY 1, 2;
