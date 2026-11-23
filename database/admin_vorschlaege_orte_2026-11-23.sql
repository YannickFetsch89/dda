-- admin_vorschlaege_orte_2026-11-23.sql – DiesDasDüsseldorf
-- Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitte 3.5 (E5), 4.4 (Stufe 3) und 4.7, Stufe 3c: Vorschläge zu Orten.
--
-- Im Supabase-SQL-Editor ausführen, VOR dem Deploy von Stufe 3c. Wiederholbar (CREATE OR REPLACE).
-- Voraussetzung: admin_events_2026-11-23.sql (admin_vorschlag_annehmen, redaktion_felder), admin_magazin_2026-11-23.sql
-- (admin_pflicht).
--
-- Drei neue Arten aus pipeline/vorschlaege.py (statt der SQL-Dateien von ortsnamen.py, ort_zuordnung.py und
-- adressen_ergaenzen.py):
--   ortsname → events.ort einer Schreibweise vereinheitlichen (+ Reihen-Ort und -Schlüssel wie ortsnamen.py)
--   ort_id   → events.ort_id setzen (Zuordnung Event → Ort)
--   adresse  → events.adresse (und stadtteil, wenn leer) setzen
-- Plan 4.4: Geschrieben wird ein Feld nur, wenn es NICHT in redaktion_felder steht; abgleich_ort bleibt unverändert.
-- Ist bei der Annahme nichts mehr zu tun (Feld geschützt, schon gesetzt), gilt der Vorschlag trotzdem als angenommen;
-- das Ergebnis nennt die Zahl der geänderten Events.
-- admin_vorschlag_annehmen wird hier vollständig neu angelegt (Dublette und Gebiet unverändert übernommen).

BEGIN;

-- ── 1. Ortsname ──────────────────────────────────────────────────────────────
-- vorschlag: {alt, neu, events: [uuid], reihen: [{id, schluessel}]}
-- Jedes Event einzeln: fiele es mit einem anderen Termin zusammen (Eindeutigkeit titel, datum, ort, uhrzeit), bleibt
-- es beim alten Namen (wie ortsnamen.py umbenennungen). Reihen (Cursor-Prüfung 3c, Befund 2): nur die aufgeführten,
-- Ort und Schlüssel immer zusammen (schluessel NULL = bleibt gleich); ist der neue Schlüssel schon vergeben, bleibt die
-- Reihe ganz beim alten Namen. Reihen mit geschützten Events stehen gar nicht im Vorschlag. Slugs bleiben.

CREATE OR REPLACE FUNCTION public.admin_ortsname_anwenden(p_vorschlag JSONB)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    alt TEXT := p_vorschlag->>'alt';
    neu TEXT := p_vorschlag->>'neu';
    eid TEXT;
    r JSONB;
    k TEXT;
    n INTEGER;
    geaendert INTEGER := 0;
    uebersprungen INTEGER := 0;
    reihen INTEGER := 0;
BEGIN
    PERFORM public.admin_pflicht();
    IF coalesce(alt, '') = '' OR coalesce(neu, '') = '' OR alt = neu THEN RAISE EXCEPTION 'admin_ortsname: alt und neu fehlen'; END IF;
    FOR eid IN SELECT jsonb_array_elements_text(coalesce(p_vorschlag->'events', '[]'::jsonb)) LOOP
        BEGIN
            UPDATE public.events SET ort = neu
            WHERE id = eid::uuid AND ort = alt AND NOT ('ort' = ANY(redaktion_felder));
            GET DIAGNOSTICS n = ROW_COUNT;
            geaendert := geaendert + n;
        EXCEPTION WHEN unique_violation THEN
            uebersprungen := uebersprungen + 1;
        END;
    END LOOP;
    FOR r IN SELECT jsonb_array_elements(coalesce(p_vorschlag->'reihen', '[]'::jsonb)) LOOP
        k := nullif(r->>'schluessel', '');
        IF k IS NULL OR NOT EXISTS (SELECT 1 FROM public.reihen WHERE schluessel = k) THEN
            UPDATE public.reihen SET ort = neu, schluessel = coalesce(k, schluessel)
            WHERE id = (r->>'id')::uuid AND ort = alt;
            GET DIAGNOSTICS n = ROW_COUNT;
            reihen := reihen + n;
        END IF;
    END LOOP;
    RETURN jsonb_build_object('ok', true, 'geaendert', geaendert, 'uebersprungen', uebersprungen, 'reihen', reihen);
END;
$$;


-- ── 2. Vorschlag annehmen (alle Arten) ───────────────────────────────────────

CREATE OR REPLACE FUNCTION public.admin_vorschlag_annehmen(p_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v public.admin_vorschlaege%ROWTYPE;
    ergebnis JSONB;
    ev UUID;
    ziel UUID;
    n INTEGER;
    m INTEGER := 0;
BEGIN
    IF NOT public.ist_admin() THEN
        RAISE EXCEPTION 'admin_nur_fuer_admins' USING ERRCODE = '42501';
    END IF;
    SELECT * INTO v FROM public.admin_vorschlaege WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_vorschlag_fehlt'; END IF;
    IF v.status <> 'offen' THEN RAISE EXCEPTION 'admin_vorschlag_schon_entschieden'; END IF;

    IF v.art = 'dublette' THEN
        ergebnis := public.admin_dublette_zusammenlegen(
            (v.vorschlag->>'behalten')::uuid,
            (v.vorschlag->>'dublette')::uuid,
            v.vorschlag->>'ziel',
            coalesce((v.vorschlag->>'uhrzeit_uebernehmen')::boolean, false),
            coalesce((v.vorschlag->>'absage')::boolean, false)
        );
    ELSIF v.art = 'gebiet' THEN
        ergebnis := public.admin_gebiet_entfernen((v.vorschlag->>'event')::uuid);
    ELSIF v.art = 'ortsname' THEN
        ergebnis := public.admin_ortsname_anwenden(v.vorschlag);
        INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
        VALUES ('vorschlag_ortsname', 'events', left(v.schluessel, 200),
                jsonb_build_object('ort', v.vorschlag->>'alt'), jsonb_build_object('ort', v.vorschlag->>'neu') || ergebnis);
    ELSIF v.art = 'ort_id' THEN
        ev := (v.vorschlag->>'event')::uuid;
        ziel := (v.vorschlag->>'ort_id')::uuid;
        IF NOT EXISTS (SELECT 1 FROM public.orte WHERE id = ziel AND aktiv) THEN
            RAISE EXCEPTION 'admin_vorschlag_ort_fehlt: Ort existiert nicht mehr oder ist inaktiv – bitte ablehnen';
        END IF;
        UPDATE public.events SET ort_id = ziel
        WHERE id = ev AND ort_id IS DISTINCT FROM ziel AND NOT ('ort_id' = ANY(redaktion_felder));
        GET DIAGNOSTICS n = ROW_COUNT;
        ergebnis := jsonb_build_object('ok', true, 'geaendert', n);
        INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
        VALUES ('vorschlag_ort_id', 'events', ev::text, jsonb_build_object('ort_id', v.vorschlag->'bisher'),
                jsonb_build_object('ort_id', ziel, 'geaendert', n));
    ELSIF v.art = 'adresse' THEN
        ev := (v.vorschlag->>'event')::uuid;
        IF coalesce(btrim(v.vorschlag->>'adresse'), '') = '' THEN RAISE EXCEPTION 'admin_vorschlag_adresse_leer'; END IF;
        UPDATE public.events SET adresse = left(btrim(v.vorschlag->>'adresse'), 300)
        WHERE id = ev AND adresse IS NULL AND NOT ('adresse' = ANY(redaktion_felder));
        GET DIAGNOSTICS n = ROW_COUNT;
        IF coalesce(v.vorschlag->>'stadtteil', '') <> '' THEN
            UPDATE public.events SET stadtteil = v.vorschlag->>'stadtteil'
            WHERE id = ev AND stadtteil IS NULL AND NOT ('stadtteil' = ANY(redaktion_felder));
            GET DIAGNOSTICS m = ROW_COUNT;
        END IF;
        ergebnis := jsonb_build_object('ok', true, 'geaendert', n, 'stadtteil', m);
        INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
        VALUES ('vorschlag_adresse', 'events', ev::text, NULL,
                jsonb_build_object('adresse', v.vorschlag->>'adresse', 'stadtteil', v.vorschlag->>'stadtteil', 'geaendert', n));
    ELSE
        RAISE EXCEPTION 'admin_vorschlag_art_unbekannt: %', v.art;
    END IF;

    UPDATE public.admin_vorschlaege
    SET status = 'angenommen', entschieden_von = auth.uid(), entschieden_am = now()
    WHERE id = p_id;
    RETURN ergebnis;
END;
$$;


-- ── 3. Rechte ────────────────────────────────────────────────────────────────
ALTER FUNCTION public.admin_ortsname_anwenden(JSONB) OWNER TO postgres;
ALTER FUNCTION public.admin_vorschlag_annehmen(UUID) OWNER TO postgres;
REVOKE EXECUTE ON FUNCTION public.admin_ortsname_anwenden(JSONB) FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON FUNCTION public.admin_vorschlag_annehmen(UUID) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_vorschlag_annehmen(UUID) TO authenticated;

COMMIT;


-- ── Kontrolle ────────────────────────────────────────────────────────────────
-- Erwartet: admin_ortsname_anwenden definer, anon_darf = false, authenticated_darf = false (nur über annehmen);
--           admin_vorschlag_annehmen definer, anon_darf = false, authenticated_darf = true
SELECT p.proname AS funktion,
       CASE WHEN p.prosecdef THEN 'definer' ELSE 'invoker' END AS sicherheit,
       has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_darf,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') AS authenticated_darf
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.proname IN ('admin_ortsname_anwenden', 'admin_vorschlag_annehmen')
ORDER BY 1;
