-- konten_aufraeumen_2026-11-17.sql – DiesDasDüsseldorf
-- Hilfsfunktion für den Aufräumjob der Nutzerkonten (Plan 4.6, 9.3, Schritt 7): Nutzer-IDs, die im
-- Anmeldeprotokoll (auth.audit_log_entries) vorkommen, aber kein Konto mehr haben. Der Job ruft für jede davon
-- konto_protokoll_loeschen auf. Die Tabelle auth ist über die Supabase-API nicht erreichbar, deshalb diese Funktion.
--
-- Laut Schritt 1 schreibt Supabase heute keine Zeilen in diese Tabelle; die Funktion liefert dann nichts und
-- schadet nicht. Sie greift, falls Supabase künftig doch Zeilen schreibt.
--
-- VORAUSSETZUNG: konten_2026-11-16.sql ist gelaufen. Wiederholbar. Ausführen als postgres im SQL-Editor.

CREATE OR REPLACE FUNCTION public.konto_protokoll_waisen()
RETURNS TABLE (nutzer UUID)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT DISTINCT k.id::uuid
    FROM (
        SELECT a.payload ->> 'actor_id' AS id FROM auth.audit_log_entries a
        UNION
        SELECT a.payload -> 'traits' ->> 'user_id' FROM auth.audit_log_entries a
    ) k
    WHERE k.id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
      AND NOT EXISTS (SELECT 1 FROM auth.users u WHERE u.id = k.id::uuid)
    LIMIT 1000;
$$;

REVOKE ALL ON FUNCTION public.konto_protokoll_waisen() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.konto_protokoll_waisen() TO service_role;

-- Kontrolle: nur service_role darf aufrufen, Ergebnis heute erwartungsgemäß leer
SELECT has_function_privilege('anon', 'public.konto_protokoll_waisen()', 'EXECUTE')          AS anon_darf,
       has_function_privilege('authenticated', 'public.konto_protokoll_waisen()', 'EXECUTE') AS authenticated_darf,
       has_function_privilege('service_role', 'public.konto_protokoll_waisen()', 'EXECUTE')  AS service_role_darf,
       (SELECT count(*) FROM public.konto_protokoll_waisen())                                AS waisen_heute;
