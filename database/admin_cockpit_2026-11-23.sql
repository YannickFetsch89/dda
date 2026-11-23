-- admin_cockpit_2026-11-23.sql – DiesDasDüsseldorf
-- Plan docs/plan-admin-dashboard-2026-11-23.md, Stufe 1b (Cockpit, 4.2): Zahlen, die der Admin-Token über RLS nicht
-- sehen darf, als eine SECURITY-DEFINER-Funktion (Muster aus Abschnitt 5). Liefert NUR Zahlen, keine Inhalte und
-- keine Personen.
--   magazin_in_pruefung:   Entwürfe mit status = 'in_pruefung'
--   magazin_naechste:      frühestes gueltig_von dieser Entwürfe (rot im Cockpit, wenn in ≤ 2 Tagen)
--   magazin_entwurf:       Entwürfe mit status = 'entwurf'
--   konten:                Anzahl Profile (alle Konten)
--
-- Im Supabase-SQL-Editor ausführen, VOR dem Deploy von Stufe 1b. Wiederholbar.
-- Voraussetzung: auth_rollen.sql (ist_admin()), magazin_2026-11-19.sql.

CREATE OR REPLACE FUNCTION public.admin_cockpit_zahlen()
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    ergebnis JSONB;
BEGIN
    IF NOT public.ist_admin() THEN
        RAISE EXCEPTION 'admin_nur_fuer_admins' USING ERRCODE = '42501';
    END IF;

    SELECT jsonb_build_object(
        'magazin_in_pruefung', (SELECT count(*) FROM public.magazin_beitraege WHERE status = 'in_pruefung'),
        'magazin_naechste',    (SELECT min(gueltig_von) FROM public.magazin_beitraege WHERE status = 'in_pruefung'),
        'magazin_entwurf',     (SELECT count(*) FROM public.magazin_beitraege WHERE status = 'entwurf'),
        'konten',              (SELECT count(*) FROM public.profiles)
    ) INTO ergebnis;
    RETURN ergebnis;
END;
$$;

ALTER FUNCTION public.admin_cockpit_zahlen() OWNER TO postgres;
REVOKE EXECUTE ON FUNCTION public.admin_cockpit_zahlen() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_cockpit_zahlen() TO authenticated;


-- ── Kontrolle (erwartet: 1 Zeile, sicherheit = definer, anon_darf = false) ────
SELECT p.proname AS funktion,
       CASE WHEN p.prosecdef THEN 'definer' ELSE 'invoker' END AS sicherheit,
       has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_darf,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') AS authenticated_darf
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.proname = 'admin_cockpit_zahlen';
