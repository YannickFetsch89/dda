-- admin_events_2026-11-23.sql – DiesDasDüsseldorf
-- Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitt 5, S2 (Stufe 1d: Events).
--
-- Im Supabase-SQL-Editor ausführen, VOR dem Deploy von Stufe 1d (die Pipeline liest redaktion_felder ab dann bei
-- jedem Lauf). Wiederholbar (idempotent). Voraussetzung: auth_rollen.sql, event_seo_2026-11-05.sql,
-- konten_2026-11-16.sql (merkliste), admin_grundlagen_2026-11-23.sql.
--
-- 1. Spalten: redaktion_felder (Feldschutz, 4.4 Teil A) und abgleich_* (Werte der Quelle, 4.4 Teil B)
-- 2. SECURITY-DEFINER-Funktionen (Muster aus Abschnitt 5: Eigentümer postgres, zuerst ist_admin(), fester
--    search_path, EXECUTE nur für authenticated, Protokoll in derselben Transaktion):
--      admin_dublette_zusammenlegen, admin_gebiet_entfernen, admin_vorschlag_annehmen, admin_vorschlag_ablehnen

BEGIN;

-- ── 1. Spalten ───────────────────────────────────────────────────────────────

ALTER TABLE public.events
    ADD COLUMN IF NOT EXISTS redaktion_felder TEXT[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS abgleich_titel   TEXT,
    ADD COLUMN IF NOT EXISTS abgleich_datum   DATE,
    ADD COLUMN IF NOT EXISTS abgleich_uhrzeit TIME,
    ADD COLUMN IF NOT EXISTS abgleich_ort     TEXT;

COMMENT ON COLUMN public.events.redaktion_felder IS
    'Im Admin-Bereich geänderte Felder; die Pipeline überschreibt sie nie (Plan Admin-Dashboard 4.4).';
COMMENT ON COLUMN public.events.abgleich_titel IS
    'Titel laut Quelle, gesetzt beim ersten Ändern von Titel/Datum/Uhrzeit/Ort im Admin-Bereich (Schritt 0 der Pipeline).';

-- Schritt 0 der Pipeline sucht über diese Spalten (nur Zeilen, die die Redaktion umbenannt oder verschoben hat)
CREATE INDEX IF NOT EXISTS events_abgleich_idx ON public.events (abgleich_datum, abgleich_titel)
    WHERE abgleich_datum IS NOT NULL;


-- ── 2a. Dublette zusammenlegen ───────────────────────────────────────────────
-- Wie pipeline/dubletten_sql.py für ein Paar: behaltenes Event ergänzen (Felder aus redaktion_felder bleiben),
-- Dublette ausblenden, 301 per event_seo_entscheidungen. NEU: Merkliste zieht auf das behaltene Event um.
-- p_ziel: Pfad der behaltenen Seite (/event/<kategorie>/<slug>), rechnet der Aufrufer (Kategorie-Segment der Website).

CREATE OR REPLACE FUNCTION public.admin_dublette_zusammenlegen(
    p_behalten UUID,
    p_dublette UUID,
    p_ziel TEXT,
    p_uhrzeit_uebernehmen BOOLEAN DEFAULT false,
    p_absage BOOLEAN DEFAULT false
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    k public.events%ROWTYPE;
    d public.events%ROWTYPE;
    g TEXT[];
    umgezogen INTEGER;
BEGIN
    IF NOT public.ist_admin() THEN
        RAISE EXCEPTION 'admin_nur_fuer_admins' USING ERRCODE = '42501';
    END IF;
    IF p_behalten IS NULL OR p_dublette IS NULL OR p_behalten = p_dublette THEN
        RAISE EXCEPTION 'admin_dublette_paar_ungueltig';
    END IF;
    IF p_ziel IS NULL OR p_ziel !~ '^/event/[a-z]+/[a-z0-9][a-z0-9-]*$' OR length(p_ziel) > 500 THEN
        RAISE EXCEPTION 'admin_dublette_ziel_ungueltig';
    END IF;

    SELECT * INTO k FROM public.events WHERE id = p_behalten FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_dublette_behalten_fehlt'; END IF;
    SELECT * INTO d FROM public.events WHERE id = p_dublette FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_dublette_fehlt'; END IF;
    g := coalesce(k.redaktion_felder, '{}');

    UPDATE public.events SET
        bild_url     = CASE WHEN 'bild_url'     = ANY(g) THEN bild_url     ELSE coalesce(nullif(bild_url, ''), d.bild_url) END,
        beschreibung = CASE WHEN 'beschreibung' = ANY(g) THEN beschreibung ELSE coalesce(nullif(beschreibung, ''), d.beschreibung) END,
        preis        = CASE WHEN 'preis'        = ANY(g) THEN preis        ELSE coalesce(nullif(preis, ''), d.preis) END,
        adresse      = CASE WHEN 'adresse'      = ANY(g) THEN adresse      ELSE coalesce(nullif(adresse, ''), d.adresse) END,
        uhrzeit      = CASE
                           WHEN 'uhrzeit' = ANY(g) THEN uhrzeit
                           WHEN d.uhrzeit IS NOT NULL AND (uhrzeit IS NULL OR p_uhrzeit_uebernehmen) THEN d.uhrzeit
                           ELSE uhrzeit
                       END,
        abgesagt     = CASE
                           WHEN 'abgesagt' = ANY(g) THEN abgesagt
                           WHEN coalesce(d.abgesagt, false) OR p_absage THEN true
                           ELSE abgesagt
                       END
    WHERE id = p_behalten;

    UPDATE public.events SET abgelehnt = true WHERE id = p_dublette;

    IF d.slug IS NOT NULL THEN
        INSERT INTO public.event_seo_entscheidungen (event_id, slug, aktion, ziel, entschieden_von)
        VALUES (d.id, d.slug, 'weiterleiten', p_ziel, auth.uid())
        ON CONFLICT (event_id) DO UPDATE
            SET aktion = 'weiterleiten', ziel = EXCLUDED.ziel, entschieden_am = now(), entschieden_von = EXCLUDED.entschieden_von;
    END IF;

    -- Merkliste: wer beide gemerkt hat, behält eine Zeile; der Rest zieht um (kein INSERT, daher ohne merkliste_vor_insert)
    DELETE FROM public.merkliste m
    WHERE m.event_id = d.id
      AND EXISTS (SELECT 1 FROM public.merkliste x WHERE x.nutzer_id = m.nutzer_id AND x.event_id = k.id);
    UPDATE public.merkliste SET event_id = k.id WHERE event_id = d.id;
    GET DIAGNOSTICS umgezogen = ROW_COUNT;

    UPDATE public.admin_vorschlaege
    SET status = 'angenommen', entschieden_von = auth.uid(), entschieden_am = now()
    WHERE art = 'dublette' AND schluessel = k.id::text || ':' || d.id::text AND status = 'offen';

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('dublette_zusammenlegen', 'events', d.id::text,
            jsonb_build_object('behalten', to_jsonb(k), 'dublette', to_jsonb(d)),
            jsonb_build_object('behalten', k.id, 'ziel', p_ziel, 'merkliste_umgezogen', umgezogen));

    RETURN jsonb_build_object('ok', true, 'merkliste_umgezogen', umgezogen);
END;
$$;


-- ── 2b. Event außerhalb des Gebiets entfernen ────────────────────────────────
-- Ohne Merklisten-Zeile: löschen wie bisher (abhängige Zeilen per ON DELETE CASCADE, Meldungen SET NULL).
-- Mit Merklisten-Zeile: nur ausblenden (abgelehnt), damit keine Merkliste still schrumpft.

CREATE OR REPLACE FUNCTION public.admin_gebiet_entfernen(p_event UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    e public.events%ROWTYPE;
    aktion TEXT;
BEGIN
    IF NOT public.ist_admin() THEN
        RAISE EXCEPTION 'admin_nur_fuer_admins' USING ERRCODE = '42501';
    END IF;
    SELECT * INTO e FROM public.events WHERE id = p_event FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_event_fehlt'; END IF;

    IF EXISTS (SELECT 1 FROM public.merkliste WHERE event_id = p_event) THEN
        UPDATE public.events SET abgelehnt = true WHERE id = p_event;
        aktion := 'ausgeblendet';
    ELSE
        DELETE FROM public.events WHERE id = p_event;
        aktion := 'geloescht';
    END IF;

    UPDATE public.admin_vorschlaege
    SET status = 'angenommen', entschieden_von = auth.uid(), entschieden_am = now()
    WHERE art = 'gebiet' AND schluessel = p_event::text AND status = 'offen';

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('gebiet_entfernen', 'events', p_event::text, to_jsonb(e), jsonb_build_object('aktion', aktion));

    RETURN jsonb_build_object('ok', true, 'aktion', aktion);
END;
$$;


-- ── 2c. Vorschläge annehmen / ablehnen ───────────────────────────────────────

CREATE OR REPLACE FUNCTION public.admin_vorschlag_annehmen(p_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v public.admin_vorschlaege%ROWTYPE;
    ergebnis JSONB;
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
    ELSE
        RAISE EXCEPTION 'admin_vorschlag_art_unbekannt: %', v.art;
    END IF;

    UPDATE public.admin_vorschlaege
    SET status = 'angenommen', entschieden_von = auth.uid(), entschieden_am = now()
    WHERE id = p_id;
    RETURN ergebnis;
END;
$$;

CREATE OR REPLACE FUNCTION public.admin_vorschlag_ablehnen(p_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    IF NOT public.ist_admin() THEN
        RAISE EXCEPTION 'admin_nur_fuer_admins' USING ERRCODE = '42501';
    END IF;
    UPDATE public.admin_vorschlaege
    SET status = 'abgelehnt', entschieden_von = auth.uid(), entschieden_am = now()
    WHERE id = p_id AND status = 'offen';
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_vorschlag_fehlt_oder_entschieden'; END IF;
    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id) VALUES ('vorschlag_ablehnen', 'admin_vorschlaege', p_id::text);
    RETURN jsonb_build_object('ok', true);
END;
$$;


-- ── 3. Rechte ────────────────────────────────────────────────────────────────

ALTER FUNCTION public.admin_dublette_zusammenlegen(UUID, UUID, TEXT, BOOLEAN, BOOLEAN) OWNER TO postgres;
ALTER FUNCTION public.admin_gebiet_entfernen(UUID) OWNER TO postgres;
ALTER FUNCTION public.admin_vorschlag_annehmen(UUID) OWNER TO postgres;
ALTER FUNCTION public.admin_vorschlag_ablehnen(UUID) OWNER TO postgres;

REVOKE EXECUTE ON FUNCTION public.admin_dublette_zusammenlegen(UUID, UUID, TEXT, BOOLEAN, BOOLEAN) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.admin_gebiet_entfernen(UUID) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.admin_vorschlag_annehmen(UUID) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.admin_vorschlag_ablehnen(UUID) FROM PUBLIC, anon;

GRANT EXECUTE ON FUNCTION public.admin_dublette_zusammenlegen(UUID, UUID, TEXT, BOOLEAN, BOOLEAN) TO authenticated;
GRANT EXECUTE ON FUNCTION public.admin_gebiet_entfernen(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.admin_vorschlag_annehmen(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.admin_vorschlag_ablehnen(UUID) TO authenticated;

COMMIT;


-- ── Kontrolle ────────────────────────────────────────────────────────────────
-- Erwartet: 5 Spalten und 4 Funktionen, alle „definer“, anon_darf = false, authenticated_darf = true
SELECT 'spalte' AS art, column_name AS name, data_type AS info, NULL::boolean AS anon_darf, NULL::boolean AS authenticated_darf
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'events'
  AND column_name IN ('redaktion_felder', 'abgleich_titel', 'abgleich_datum', 'abgleich_uhrzeit', 'abgleich_ort')
UNION ALL
SELECT 'funktion', p.proname, CASE WHEN p.prosecdef THEN 'definer' ELSE 'invoker' END,
       has_function_privilege('anon', p.oid, 'EXECUTE'), has_function_privilege('authenticated', p.oid, 'EXECUTE')
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname IN ('admin_dublette_zusammenlegen', 'admin_gebiet_entfernen', 'admin_vorschlag_annehmen', 'admin_vorschlag_ablehnen')
ORDER BY 1, 2;
