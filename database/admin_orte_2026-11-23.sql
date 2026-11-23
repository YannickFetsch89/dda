-- admin_orte_2026-11-23.sql – DiesDasDüsseldorf
-- Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitt 4.7 und 5 (S4), Stufe 3a: Orte im Admin-Bereich.
--
-- Im Supabase-SQL-Editor ausführen, VOR dem Deploy von Stufe 3a. Wiederholbar (CREATE OR REPLACE, DROP POLICY IF EXISTS).
-- Voraussetzung: schema_orte.sql, orte_spielstaetten_2026-11-19.sql (ort_weiterleitungen, Trigger orte_schutz),
-- admin_grundlagen_2026-11-23.sql (ist_admin, admin_protokoll), admin_events_2026-11-23.sql (events.redaktion_felder),
-- admin_magazin_2026-11-23.sql (admin_pflicht).
--
-- Rechte (Cursor-Befund 12): orte_lesen zeigt nur aktive Zeilen, orte_admin_alles prüft service_role. Neu:
--   - orte_admin_lesen (SELECT) und orte_admin_aendern (UPDATE) mit ist_admin() – für Liste und Stammdaten.
--     Welche Spalten geändert werden, begrenzt die Route (Whitelist); slug, typ und das Abschalten laufen NICHT
--     über das UPDATE, sondern über die Funktionen unten (der Trigger orte_schutz bleibt in jedem Fall wirksam).
--   - Zusammenlegen, Schließen/Löschen, Text speichern/freigeben, Zuordnung lösen, Score festsetzen als
--     SECURITY-DEFINER-Funktionen (Eigentümer postgres, zuerst ist_admin(), fester search_path, EXECUTE nur für
--     authenticated, Protokoll). ort_weiterleitungen wird nur über diese Funktionen geschrieben.

BEGIN;

-- ── 1. Policies auf orte ─────────────────────────────────────────────────────

DROP POLICY IF EXISTS orte_admin_lesen ON public.orte;
CREATE POLICY orte_admin_lesen ON public.orte
    FOR SELECT TO authenticated
    USING (public.ist_admin());

DROP POLICY IF EXISTS orte_admin_aendern ON public.orte;
CREATE POLICY orte_admin_aendern ON public.orte
    FOR UPDATE TO authenticated
    USING (public.ist_admin())
    WITH CHECK (public.ist_admin());

-- Das UPDATE braucht das Tabellenrecht; RLS begrenzt es auf Admins. Kein INSERT/DELETE für authenticated.
GRANT SELECT, UPDATE ON public.orte TO authenticated;


-- ── 2. Hilfe: Schreibweisen-Liste einer Zeile (event_orte) ───────────────────
-- Clubs: extras.club.event_orte, Spielstätten: extras.spielstaette.event_orte (pipeline/ort_zuordnung.py).

CREATE OR REPLACE FUNCTION public.admin_ort_schreibweisen_schluessel(p_typ TEXT)
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
SET search_path = public, pg_temp
AS $$
    SELECT CASE p_typ WHEN 'spielstaette' THEN 'spielstaette' WHEN 'club' THEN 'club' ELSE NULL END;
$$;


-- ── 3. Zusammenlegen: Ort A (p_von) in Ort B (p_nach) ────────────────────────
-- Reihenfolge wie database/orte_balletthaus_zusammen_2026-11-20.sql (Schutz-Trigger):
-- Weiterleitung A → B, ältere Weiterleitungen auf A umhängen, Säle umhängen, Events umhängen, Schreibweisen von A
-- (und A's Name) bei B ergänzen, A löschen. B muss aktiv sein (sonst endete die Weiterleitung auf /orte).

CREATE OR REPLACE FUNCTION public.admin_ort_zusammenlegen(p_von UUID, p_nach UUID, p_grund TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    a public.orte%ROWTYPE;
    b public.orte%ROWTYPE;
    k TEXT;
    schreibweisen JSONB;
    events_umgehaengt INTEGER;
    weiter_umgehaengt INTEGER;
    saele_umgehaengt INTEGER;
BEGIN
    PERFORM public.admin_pflicht();
    IF p_von = p_nach THEN RAISE EXCEPTION 'admin_ort_gleich: Ort kann nicht mit sich selbst zusammengelegt werden'; END IF;
    IF length(btrim(coalesce(p_grund, ''))) < 3 THEN RAISE EXCEPTION 'admin_grund_fehlt: Bitte einen Grund angeben'; END IF;

    SELECT * INTO a FROM public.orte WHERE id = p_von FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_ort_fehlt: Ort A existiert nicht'; END IF;
    SELECT * INTO b FROM public.orte WHERE id = p_nach FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_ort_fehlt: Ort B existiert nicht'; END IF;
    IF NOT coalesce(b.aktiv, false) THEN
        RAISE EXCEPTION 'admin_ziel_inaktiv: „%“ ist nicht aktiv – zuerst freischalten oder ein aktives Ziel wählen', b.name;
    END IF;
    IF b.parent_id = a.id THEN
        RAISE EXCEPTION 'admin_ziel_ist_saal: „%“ ist ein Saal von „%“ – zuerst den Saal lösen', b.name, a.name;
    END IF;

    INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
    VALUES (a.slug, b.id, left(btrim(p_grund), 300))
    ON CONFLICT (alter_slug) DO UPDATE SET ziel_ort_id = EXCLUDED.ziel_ort_id, grund = EXCLUDED.grund;

    UPDATE public.ort_weiterleitungen SET ziel_ort_id = b.id WHERE ziel_ort_id = a.id;
    GET DIAGNOSTICS weiter_umgehaengt = ROW_COUNT;

    UPDATE public.orte SET parent_id = b.id WHERE parent_id = a.id AND id <> b.id;
    GET DIAGNOSTICS saele_umgehaengt = ROW_COUNT;

    UPDATE public.events SET ort_id = b.id WHERE ort_id = a.id;
    GET DIAGNOSTICS events_umgehaengt = ROW_COUNT;

    k := public.admin_ort_schreibweisen_schluessel(b.typ);
    IF k IS NOT NULL THEN
        SELECT coalesce(jsonb_agg(DISTINCT s ORDER BY s), '[]'::jsonb) INTO schreibweisen FROM (
            SELECT jsonb_array_elements_text(coalesce(b.extras->k->'event_orte', '[]'::jsonb)) AS s
            UNION SELECT jsonb_array_elements_text(coalesce(a.extras->'spielstaette'->'event_orte', '[]'::jsonb))
            UNION SELECT jsonb_array_elements_text(coalesce(a.extras->'club'->'event_orte', '[]'::jsonb))
            UNION SELECT a.name
        ) x WHERE btrim(s) <> '';
        UPDATE public.orte
        SET extras = jsonb_set(coalesce(extras, '{}'::jsonb), ARRAY[k],
                               coalesce(extras->k, '{}'::jsonb) || jsonb_build_object('event_orte', schreibweisen))
        WHERE id = b.id;
    END IF;

    DELETE FROM public.orte WHERE id = a.id;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('ort_zusammenlegen', 'orte', a.id::text, to_jsonb(a),
            jsonb_build_object('nach', b.id, 'nach_slug', b.slug, 'grund', p_grund, 'events', events_umgehaengt,
                               'weiterleitungen', weiter_umgehaengt, 'saele', saele_umgehaengt));

    RETURN jsonb_build_object('ok', true, 'nach_slug', b.slug, 'events', events_umgehaengt,
                              'weiterleitungen', weiter_umgehaengt, 'saele', saele_umgehaengt);
END;
$$;


-- ── 4. Schließen / Löschen mit Pflicht-Weiterleitung ─────────────────────────
-- p_ziel: Ort, auf den die alte Adresse zeigt (NULL → /orte). p_loeschen = false: Zeile bleibt (aktiv = false),
-- lässt sich später wieder freischalten; true: Zeile weg (wie orte_gertrudenhof_weglassen_2026-11-20.sql),
-- events.ort_id wird per Fremdschlüssel NULL. Aktive Säle → Abbruch durch den Trigger (zuerst umhängen).

CREATE OR REPLACE FUNCTION public.admin_ort_schliessen(p_id UUID, p_ziel UUID, p_grund TEXT, p_loeschen BOOLEAN DEFAULT false)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    o public.orte%ROWTYPE;
    z public.orte%ROWTYPE;
    weiter_umgehaengt INTEGER;
BEGIN
    PERFORM public.admin_pflicht();
    IF length(btrim(coalesce(p_grund, ''))) < 3 THEN RAISE EXCEPTION 'admin_grund_fehlt: Bitte einen Grund angeben'; END IF;
    SELECT * INTO o FROM public.orte WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_ort_fehlt: Ort existiert nicht'; END IF;
    IF p_ziel IS NOT NULL THEN
        IF p_ziel = p_id THEN RAISE EXCEPTION 'admin_ort_gleich: Ziel ist der Ort selbst'; END IF;
        SELECT * INTO z FROM public.orte WHERE id = p_ziel;
        IF NOT FOUND OR NOT coalesce(z.aktiv, false) THEN
            RAISE EXCEPTION 'admin_ziel_inaktiv: Ziel existiert nicht oder ist nicht aktiv';
        END IF;
    END IF;

    INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
    VALUES (o.slug, p_ziel, left(btrim(p_grund), 300))
    ON CONFLICT (alter_slug) DO UPDATE SET ziel_ort_id = EXCLUDED.ziel_ort_id, grund = EXCLUDED.grund;

    -- Weiterleitungen, die auf diesen Ort zeigen, folgen dem neuen Ziel (eine Stufe, keine Ketten)
    UPDATE public.ort_weiterleitungen SET ziel_ort_id = p_ziel WHERE ziel_ort_id = o.id AND alter_slug <> o.slug;
    GET DIAGNOSTICS weiter_umgehaengt = ROW_COUNT;

    IF p_loeschen THEN
        DELETE FROM public.orte WHERE id = o.id;
    ELSE
        UPDATE public.orte SET aktiv = false WHERE id = o.id;
    END IF;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES (CASE WHEN p_loeschen THEN 'ort_loeschen' ELSE 'ort_schliessen' END, 'orte', o.id::text,
            CASE WHEN p_loeschen THEN to_jsonb(o) ELSE jsonb_build_object('aktiv', o.aktiv) END,
            jsonb_build_object('ziel', p_ziel, 'grund', p_grund, 'weiterleitungen', weiter_umgehaengt));

    RETURN jsonb_build_object('ok', true, 'geloescht', p_loeschen, 'weiterleitungen', weiter_umgehaengt);
END;
$$;


-- ── 5. Text einer Spielstätte: Entwurf speichern oder freigeben ──────────────
-- Ersetzt die Dateien orte_texte_*.sql. Entwurf: extras.spielstaette.text_entwurf {text, quellen, datum}.
-- Freigabe: beschreibung = Text, extras.spielstaette.text_freigegeben {datum, quellen}, Entwurf weg.
-- Ohne text_freigegeben zeigt die Ortsseite keinen Text (scraper/orte/spielstaetten_texte.py). Jede Freigabe braucht
-- mindestens eine Quelle (https).

CREATE OR REPLACE FUNCTION public.admin_ort_text_speichern(p_id UUID, p_text TEXT, p_quellen TEXT[], p_freigeben BOOLEAN)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    o public.orte%ROWTYPE;
    text_neu TEXT := btrim(coalesce(p_text, ''));
    quellen JSONB;
    heute TEXT := to_char(now() AT TIME ZONE 'Europe/Berlin', 'YYYY-MM-DD');
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO o FROM public.orte WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_ort_fehlt: Ort existiert nicht'; END IF;
    IF o.typ <> 'spielstaette' THEN RAISE EXCEPTION 'admin_text_nur_spielstaetten: Texte mit Freigabe gibt es nur bei Spielstätten'; END IF;
    IF length(text_neu) < 200 OR length(text_neu) > 4000 THEN
        RAISE EXCEPTION 'admin_text_laenge: Text 200 bis 4000 Zeichen (jetzt %)', length(text_neu);
    END IF;
    SELECT coalesce(jsonb_agg(btrim(q)), '[]'::jsonb) INTO quellen
    FROM unnest(coalesce(p_quellen, '{}'::text[])) q WHERE btrim(q) <> '';
    IF EXISTS (SELECT 1 FROM jsonb_array_elements_text(quellen) q WHERE q !~ '^https://[^\s]+$') THEN
        RAISE EXCEPTION 'admin_text_quelle: Quellen müssen mit https:// beginnen';
    END IF;
    IF p_freigeben AND jsonb_array_length(quellen) = 0 THEN
        RAISE EXCEPTION 'admin_text_quelle: Zur Freigabe mindestens eine Quelle angeben';
    END IF;

    IF p_freigeben THEN
        UPDATE public.orte
        SET beschreibung = text_neu,
            extras = jsonb_set(coalesce(extras, '{}'::jsonb), '{spielstaette}',
                       (coalesce(extras->'spielstaette', '{}'::jsonb) - 'text_entwurf')
                       || jsonb_build_object('text_freigegeben', jsonb_build_object('datum', heute, 'quellen', quellen)))
        WHERE id = o.id;
    ELSE
        UPDATE public.orte
        SET extras = jsonb_set(coalesce(extras, '{}'::jsonb), '{spielstaette}',
                       coalesce(extras->'spielstaette', '{}'::jsonb)
                       || jsonb_build_object('text_entwurf', jsonb_build_object('text', text_neu, 'quellen', quellen, 'datum', heute)))
        WHERE id = o.id;
    END IF;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES (CASE WHEN p_freigeben THEN 'ort_text_freigeben' ELSE 'ort_text_entwurf' END, 'orte', o.id::text,
            jsonb_build_object('beschreibung', o.beschreibung, 'text_freigegeben', o.extras->'spielstaette'->'text_freigegeben'),
            jsonb_build_object('laenge', length(text_neu), 'quellen', quellen));

    RETURN jsonb_build_object('ok', true, 'freigegeben', p_freigeben);
END;
$$;


-- ── 6. Zuordnung eines Events zu einem Ort lösen ─────────────────────────────
-- Ersetzt orte_koe_loesen_*.sql für Einzelfälle: events.ort_id = NULL und 'ort_id' in redaktion_felder, damit der
-- nächste Lauf sie nicht wieder setzt (database/client.py, Feldschutz). Eine Schreibweise ganz zu lösen
-- (event_orte) bleibt Teil der Guide-Pflege (Stufe 3b), weil clubs_profil.py die Liste neu berechnet.

CREATE OR REPLACE FUNCTION public.admin_ort_zuordnung_loesen(p_event UUID, p_ort UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    n INTEGER;
BEGIN
    PERFORM public.admin_pflicht();
    UPDATE public.events
    SET ort_id = NULL,
        redaktion_felder = CASE WHEN 'ort_id' = ANY(redaktion_felder) THEN redaktion_felder
                                ELSE array_append(redaktion_felder, 'ort_id') END
    WHERE id = p_event AND ort_id = p_ort;
    GET DIAGNOSTICS n = ROW_COUNT;
    IF n = 0 THEN RAISE EXCEPTION 'admin_zuordnung_fehlt: Event ist diesem Ort nicht zugeordnet'; END IF;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('ort_zuordnung_loesen', 'events', p_event::text, jsonb_build_object('ort_id', p_ort), jsonb_build_object('ort_id', NULL));

    RETURN jsonb_build_object('ok', true);
END;
$$;


-- ── 7. Score festsetzen (qualitaets_score + extras.score_manuell) ────────────
-- extras.score_manuell = Begründung; scraper/orte/flaechensuche.py lässt solche Scores stehen. p_grund NULL/leer
-- → Score wieder frei (Schlüssel weg). Spielplätze und Weihnachtsmärkte haben eigene Scores (Stufe 3b).

CREATE OR REPLACE FUNCTION public.admin_ort_score_setzen(p_id UUID, p_score INTEGER, p_grund TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    o public.orte%ROWTYPE;
    grund TEXT := nullif(btrim(coalesce(p_grund, '')), '');
BEGIN
    PERFORM public.admin_pflicht();
    IF p_score IS NOT NULL AND (p_score < 1 OR p_score > 10) THEN RAISE EXCEPTION 'admin_score: Score 1 bis 10'; END IF;
    SELECT * INTO o FROM public.orte WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_ort_fehlt: Ort existiert nicht'; END IF;
    IF o.typ IN ('spielplatz', 'weihnachtsmarkt') THEN
        RAISE EXCEPTION 'admin_score_guide: Spielplätze und Weihnachtsmärkte haben eigene Scores (Guide-Pflege)';
    END IF;

    UPDATE public.orte
    SET qualitaets_score = p_score,
        extras = CASE WHEN grund IS NULL THEN coalesce(extras, '{}'::jsonb) - 'score_manuell'
                      ELSE coalesce(extras, '{}'::jsonb) || jsonb_build_object('score_manuell', left(grund, 300)) END
    WHERE id = o.id;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('ort_score', 'orte', o.id::text,
            jsonb_build_object('qualitaets_score', o.qualitaets_score, 'score_manuell', o.extras->'score_manuell'),
            jsonb_build_object('qualitaets_score', p_score, 'score_manuell', grund));

    RETURN jsonb_build_object('ok', true);
END;
$$;


-- ── 8. Rechte ────────────────────────────────────────────────────────────────
DO $$
DECLARE
    f TEXT;
BEGIN
    FOREACH f IN ARRAY ARRAY[
        'admin_ort_zusammenlegen(uuid, uuid, text)',
        'admin_ort_schliessen(uuid, uuid, text, boolean)',
        'admin_ort_text_speichern(uuid, text, text[], boolean)',
        'admin_ort_zuordnung_loesen(uuid, uuid)',
        'admin_ort_score_setzen(uuid, integer, text)'
    ] LOOP
        EXECUTE format('ALTER FUNCTION public.%s OWNER TO postgres', f);
        EXECUTE format('REVOKE EXECUTE ON FUNCTION public.%s FROM PUBLIC, anon', f);
        EXECUTE format('GRANT EXECUTE ON FUNCTION public.%s TO authenticated', f);
    END LOOP;
END $$;

COMMIT;


-- ── Kontrolle ────────────────────────────────────────────────────────────────
-- Erwartet: 5 Funktionen, alle definer, anon_darf = false, authenticated_darf = true
SELECT p.proname AS funktion,
       CASE WHEN p.prosecdef THEN 'definer' ELSE 'invoker' END AS sicherheit,
       has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_darf,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') AS authenticated_darf
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND p.proname LIKE 'admin_ort\_%' AND p.proname <> 'admin_ort_schreibweisen_schluessel'
ORDER BY 1;

-- Erwartet: orte_admin_aendern (UPDATE) und orte_admin_lesen (SELECT)
SELECT policyname, cmd FROM pg_policies WHERE tablename = 'orte' AND policyname LIKE 'orte_admin_%' ORDER BY 1;
