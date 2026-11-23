-- admin_magazin_2026-11-23.sql – DiesDasDüsseldorf
-- Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitt 4.6 und 5 (S3), Stufe 2: Magazin im Admin-Bereich.
--
-- Im Supabase-SQL-Editor ausführen, VOR dem Deploy von Stufe 2. Wiederholbar (CREATE OR REPLACE).
-- Voraussetzung: magazin_2026-11-19.sql, magazin_rubriken_autoren_2026-11-19.sql, admin_grundlagen_2026-11-23.sql.
--
-- Der Admin-Token bekommt KEINE neuen Tabellenrechte auf magazin_*. Alles läuft über SECURITY-DEFINER-Funktionen
-- (Eigentümer postgres, zuerst ist_admin(), fester search_path, EXECUTE nur für authenticated, Protokoll).
-- In diesen Funktionen ist current_user = postgres: Die Sperre „Veröffentlichen nur Redaktion“ im Trigger
-- magazin_status_pruefen öffnet sich damit gewollt (der Admin IST die Redaktion, Plan D3). Die Pflichtprüfungen des
-- Triggers bleiben: nur aus in_pruefung, Pflichtfelder, pruefung.ergebnis = gruen, Slug-Eindeutigkeit.
-- Damit nichts am Trigger vorbei geht, ändert nur _veroeffentlichen und _zurueckziehen den Status, und
-- _speichern nimmt nur Entwürfe und nur Felder aus der Whitelist.

BEGIN;

-- ── Hilfe: Admin-Prüfung ─────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.admin_pflicht()
RETURNS VOID
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    IF NOT public.ist_admin() THEN
        RAISE EXCEPTION 'admin_nur_fuer_admins' USING ERRCODE = '42501';
    END IF;
END;
$$;


-- ── Lesen ────────────────────────────────────────────────────────────────────

-- Liste ohne Text (für Redaktionsplan und Entwürfe). p_status NULL = alle.
CREATE OR REPLACE FUNCTION public.admin_magazin_liste(p_status TEXT DEFAULT NULL)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    PERFORM public.admin_pflicht();
    RETURN coalesce((
        SELECT jsonb_agg(jsonb_build_object(
            'id', b.id, 'slug', b.slug, 'rubrik', b.rubrik, 'autor_slug', b.autor_slug, 'titel', b.titel,
            'status', b.status, 'gueltig_von', b.gueltig_von, 'gueltig_bis', b.gueltig_bis,
            'veroeffentlicht_am', b.veroeffentlicht_am, 'aktualisiert_am', b.aktualisiert_am,
            'erstellt_am', b.erstellt_am, 'pruefung_ergebnis', b.pruefung ->> 'ergebnis',
            'korrektur_hinweis', b.korrektur_hinweis
        ) ORDER BY coalesce(b.gueltig_von, b.veroeffentlicht_am::date, b.erstellt_am::date) DESC, b.erstellt_am DESC)
        FROM public.magazin_beitraege b
        WHERE p_status IS NULL OR b.status = p_status
    ), '[]'::jsonb);
END;
$$;

-- Ein Beitrag mit allen Spalten außer dem Vorschau-Hash
CREATE OR REPLACE FUNCTION public.admin_magazin_beitrag(p_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    ergebnis JSONB;
BEGIN
    PERFORM public.admin_pflicht();
    SELECT to_jsonb(b) - 'vorschau_hash' INTO ergebnis FROM public.magazin_beitraege b WHERE b.id = p_id;
    IF ergebnis IS NULL THEN RAISE EXCEPTION 'admin_magazin_fehlt'; END IF;
    RETURN ergebnis;
END;
$$;

-- KI-Kosten: Summe gesamt und je Monat ab p_von
CREATE OR REPLACE FUNCTION public.admin_magazin_kosten(p_von DATE)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    PERFORM public.admin_pflicht();
    RETURN jsonb_build_object(
        'summe_usd', (SELECT coalesce(sum(kosten_usd), 0) FROM public.magazin_ki_kosten WHERE art = 'gemessen' AND zeitpunkt >= p_von),
        'je_monat', coalesce((
            SELECT jsonb_agg(jsonb_build_object('monat', m.monat, 'usd', m.usd, 'laeufe', m.laeufe) ORDER BY m.monat DESC)
            FROM (SELECT to_char(zeitpunkt AT TIME ZONE 'Europe/Berlin', 'YYYY-MM') AS monat, sum(kosten_usd) AS usd, count(*) AS laeufe
                  FROM public.magazin_ki_kosten WHERE art = 'gemessen' AND zeitpunkt >= p_von GROUP BY 1) m
        ), '[]'::jsonb)
    );
END;
$$;


-- ── Anlegen ──────────────────────────────────────────────────────────────────
-- Leerer Entwurf; Slug aus dem Titel (Umlaute umgeschrieben, reservierte Wörter vermieden, bei Kollision -2, -3 …)

CREATE OR REPLACE FUNCTION public.admin_magazin_anlegen(p_rubrik TEXT, p_autor TEXT, p_titel TEXT)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    basis TEXT;
    kandidat TEXT;
    n INTEGER := 1;
    neue_id UUID;
BEGIN
    PERFORM public.admin_pflicht();
    IF p_titel IS NULL OR length(trim(p_titel)) NOT BETWEEN 1 AND 90 THEN RAISE EXCEPTION 'admin_magazin_titel_ungueltig'; END IF;

    basis := lower(trim(p_titel));
    basis := replace(replace(replace(replace(basis, 'ä', 'ae'), 'ö', 'oe'), 'ü', 'ue'), 'ß', 'ss');
    basis := regexp_replace(basis, '[^a-z0-9]+', '-', 'g');
    basis := regexp_replace(basis, '(^-+|-+$)', '', 'g');
    basis := left(basis, 80);
    basis := regexp_replace(basis, '-+$', '', 'g');
    IF basis = '' THEN basis := 'beitrag'; END IF;
    IF basis IN ('rubrik', 'autor', 'vorschau', 'seite', 'redaktion') THEN basis := basis || '-beitrag'; END IF;

    kandidat := basis;
    WHILE EXISTS (SELECT 1 FROM public.magazin_beitraege WHERE slug = kandidat OR kandidat = ANY (alte_slugs)) LOOP
        n := n + 1;
        kandidat := basis || '-' || n;
    END LOOP;

    INSERT INTO public.magazin_beitraege (slug, rubrik, autor_slug, titel, status, ki_entwurf)
    VALUES (kandidat, p_rubrik, p_autor, trim(p_titel), 'entwurf', jsonb_build_object('angelegt', 'admin'))
    RETURNING id INTO neue_id;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, nachher)
    VALUES ('magazin_anlegen', 'magazin_beitraege', neue_id::text, jsonb_build_object('slug', kandidat, 'rubrik', p_rubrik, 'titel', p_titel));
    RETURN neue_id;
END;
$$;


-- ── Speichern (nur Entwürfe, nur Whitelist) ──────────────────────────────────
-- p_felder: titel, seo_titel, teaser, inhalt_md, kurzfassung (Array), faq (Array), hero_bild, hero_alt, hero_nachweis,
--           gueltig_von, gueltig_bis, naechste_pruefung, autor_slug, event_ids (Array), ort_slugs (Array), quellen (Array)
-- p_pruefung: Ergebnis der Prüfung nach der Bearbeitung (rechnet der Admin-Bereich, web/lib/admin/magazin-pruefung.ts).
--             Bei rot geht der Beitrag auf „entwurf“, bei grün auf „in_pruefung“ – wie die Pipeline.

CREATE OR REPLACE FUNCTION public.admin_magazin_speichern(p_id UUID, p_felder JSONB, p_pruefung JSONB)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    b public.magazin_beitraege%ROWTYPE;
    erlaubt TEXT[] := ARRAY['titel', 'seo_titel', 'teaser', 'inhalt_md', 'kurzfassung', 'faq', 'hero_bild', 'hero_alt',
                            'hero_nachweis', 'gueltig_von', 'gueltig_bis', 'naechste_pruefung', 'autor_slug',
                            'event_ids', 'ort_slugs', 'quellen'];
    schluessel TEXT;
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO b FROM public.magazin_beitraege WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_magazin_fehlt'; END IF;
    IF b.status NOT IN ('entwurf', 'in_pruefung') THEN
        RAISE EXCEPTION 'admin_magazin_nur_entwuerfe'
            USING HINT = 'Veröffentlichte Beiträge nur über admin_magazin_korrektur ändern.';
    END IF;
    IF jsonb_typeof(p_felder) <> 'object' OR jsonb_typeof(p_pruefung) <> 'object'
       OR coalesce(p_pruefung ->> 'ergebnis', '') NOT IN ('gruen', 'rot') THEN
        RAISE EXCEPTION 'admin_magazin_eingabe_ungueltig';
    END IF;
    FOR schluessel IN SELECT jsonb_object_keys(p_felder) LOOP
        IF NOT (schluessel = ANY (erlaubt)) THEN
            RAISE EXCEPTION 'admin_magazin_feld_nicht_erlaubt: %', schluessel;
        END IF;
    END LOOP;

    UPDATE public.magazin_beitraege SET
        titel             = CASE WHEN p_felder ? 'titel'             THEN p_felder ->> 'titel'             ELSE titel END,
        seo_titel         = CASE WHEN p_felder ? 'seo_titel'         THEN nullif(p_felder ->> 'seo_titel', '') ELSE seo_titel END,
        teaser            = CASE WHEN p_felder ? 'teaser'            THEN nullif(p_felder ->> 'teaser', '') ELSE teaser END,
        inhalt_md         = CASE WHEN p_felder ? 'inhalt_md'         THEN coalesce(p_felder ->> 'inhalt_md', '') ELSE inhalt_md END,
        kurzfassung       = CASE WHEN p_felder ? 'kurzfassung'       THEN (SELECT array_agg(x) FROM jsonb_array_elements_text(p_felder -> 'kurzfassung') x) ELSE kurzfassung END,
        faq               = CASE WHEN p_felder ? 'faq'               THEN nullif(p_felder -> 'faq', 'null'::jsonb) ELSE faq END,
        hero_bild         = CASE WHEN p_felder ? 'hero_bild'         THEN nullif(p_felder ->> 'hero_bild', '') ELSE hero_bild END,
        hero_alt          = CASE WHEN p_felder ? 'hero_alt'          THEN nullif(p_felder ->> 'hero_alt', '') ELSE hero_alt END,
        hero_nachweis     = CASE WHEN p_felder ? 'hero_nachweis'     THEN nullif(p_felder ->> 'hero_nachweis', '') ELSE hero_nachweis END,
        gueltig_von       = CASE WHEN p_felder ? 'gueltig_von'       THEN (nullif(p_felder ->> 'gueltig_von', ''))::date ELSE gueltig_von END,
        gueltig_bis       = CASE WHEN p_felder ? 'gueltig_bis'       THEN (nullif(p_felder ->> 'gueltig_bis', ''))::date ELSE gueltig_bis END,
        naechste_pruefung = CASE WHEN p_felder ? 'naechste_pruefung' THEN (nullif(p_felder ->> 'naechste_pruefung', ''))::date ELSE naechste_pruefung END,
        autor_slug        = CASE WHEN p_felder ? 'autor_slug'        THEN p_felder ->> 'autor_slug' ELSE autor_slug END,
        event_ids         = CASE WHEN p_felder ? 'event_ids'         THEN coalesce((SELECT array_agg(x::uuid) FROM jsonb_array_elements_text(p_felder -> 'event_ids') x), '{}') ELSE event_ids END,
        ort_slugs         = CASE WHEN p_felder ? 'ort_slugs'         THEN coalesce((SELECT array_agg(x) FROM jsonb_array_elements_text(p_felder -> 'ort_slugs') x), '{}') ELSE ort_slugs END,
        quellen           = CASE WHEN p_felder ? 'quellen'           THEN coalesce(p_felder -> 'quellen', '[]'::jsonb) ELSE quellen END,
        pruefung          = p_pruefung || jsonb_build_object('lauf', 'admin', 'zeitpunkt', now()),
        status            = CASE WHEN p_pruefung ->> 'ergebnis' = 'gruen' THEN 'in_pruefung' ELSE 'entwurf' END
    WHERE id = p_id;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('magazin_speichern', 'magazin_beitraege', p_id::text,
            (SELECT jsonb_object_agg(k, to_jsonb(b) -> k) FROM jsonb_object_keys(p_felder) k),
            p_felder || jsonb_build_object('pruefung', p_pruefung ->> 'ergebnis'));
    RETURN jsonb_build_object('ok', true, 'status', CASE WHEN p_pruefung ->> 'ergebnis' = 'gruen' THEN 'in_pruefung' ELSE 'entwurf' END);
END;
$$;


-- ── Veröffentlichen ──────────────────────────────────────────────────────────
-- Der Trigger prüft weiter: nur aus in_pruefung, Pflichtfelder, pruefung = grün; setzt freigegeben_am, leert vorschau_hash.

CREATE OR REPLACE FUNCTION public.admin_magazin_veroeffentlichen(p_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    b public.magazin_beitraege%ROWTYPE;
    wer TEXT := coalesce(auth.jwt() ->> 'email', auth.uid()::text);
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO b FROM public.magazin_beitraege WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_magazin_fehlt'; END IF;
    UPDATE public.magazin_beitraege
    SET status = 'veroeffentlicht',
        veroeffentlicht_am = coalesce(veroeffentlicht_am, now()),
        freigegeben_von = wer
    WHERE id = p_id;
    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('magazin_veroeffentlichen', 'magazin_beitraege', p_id::text,
            jsonb_build_object('status', b.status), jsonb_build_object('status', 'veroeffentlicht', 'slug', b.slug));
    RETURN jsonb_build_object('ok', true, 'slug', b.slug, 'rubrik', b.rubrik);
END;
$$;


-- ── Zurückziehen ─────────────────────────────────────────────────────────────
-- Veröffentlicht → zurueckgezogen (Seite verschwindet); Entwurf/in_pruefung → zurueckgezogen (verworfen).

CREATE OR REPLACE FUNCTION public.admin_magazin_zurueckziehen(p_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    b public.magazin_beitraege%ROWTYPE;
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO b FROM public.magazin_beitraege WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_magazin_fehlt'; END IF;
    IF b.status = 'zurueckgezogen' THEN RAISE EXCEPTION 'admin_magazin_schon_zurueckgezogen'; END IF;
    UPDATE public.magazin_beitraege SET status = 'zurueckgezogen', vorschau_hash = NULL WHERE id = p_id;
    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('magazin_zurueckziehen', 'magazin_beitraege', p_id::text,
            jsonb_build_object('status', b.status), jsonb_build_object('status', 'zurueckgezogen'));
    RETURN jsonb_build_object('ok', true, 'slug', b.slug, 'rubrik', b.rubrik);
END;
$$;


-- ── Korrektur eines veröffentlichten Beitrags ────────────────────────────────
-- Einziger Weg, einen veröffentlichten Text zu ändern: setzt immer korrektur_hinweis und aktualisiert_am.

CREATE OR REPLACE FUNCTION public.admin_magazin_korrektur(p_id UUID, p_hinweis TEXT, p_inhalt_md TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    b public.magazin_beitraege%ROWTYPE;
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO b FROM public.magazin_beitraege WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_magazin_fehlt'; END IF;
    IF b.status <> 'veroeffentlicht' THEN RAISE EXCEPTION 'admin_magazin_nur_veroeffentlicht'; END IF;
    IF p_hinweis IS NULL OR length(trim(p_hinweis)) NOT BETWEEN 5 AND 500 THEN RAISE EXCEPTION 'admin_magazin_hinweis_noetig'; END IF;
    UPDATE public.magazin_beitraege
    SET korrektur_hinweis = trim(p_hinweis),
        inhalt_md = coalesce(p_inhalt_md, inhalt_md),
        aktualisiert_am = now()
    WHERE id = p_id;
    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('magazin_korrektur', 'magazin_beitraege', p_id::text,
            jsonb_build_object('korrektur_hinweis', b.korrektur_hinweis, 'inhalt_md', b.inhalt_md),
            jsonb_build_object('korrektur_hinweis', trim(p_hinweis), 'inhalt_geaendert', p_inhalt_md IS NOT NULL));
    RETURN jsonb_build_object('ok', true, 'slug', b.slug, 'rubrik', b.rubrik);
END;
$$;


-- ── Autoren ──────────────────────────────────────────────────────────────────
-- Felder: name, kurzbeschreibung, schwerpunkt, rubriken (Array), bild, bild_ki, aktiv. Neue Autoren legt dieser Weg
-- nicht an (Pseudonyme sind eine Redaktionsentscheidung, Plan Redaktion 2.3).

CREATE OR REPLACE FUNCTION public.admin_magazin_autor_speichern(p_slug TEXT, p_felder JSONB)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    a public.magazin_autoren%ROWTYPE;
    schluessel TEXT;
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO a FROM public.magazin_autoren WHERE slug = p_slug FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_magazin_autor_fehlt'; END IF;
    FOR schluessel IN SELECT jsonb_object_keys(p_felder) LOOP
        IF NOT (schluessel = ANY (ARRAY['name', 'kurzbeschreibung', 'schwerpunkt', 'rubriken', 'bild', 'bild_ki', 'aktiv'])) THEN
            RAISE EXCEPTION 'admin_magazin_feld_nicht_erlaubt: %', schluessel;
        END IF;
    END LOOP;
    UPDATE public.magazin_autoren SET
        name             = CASE WHEN p_felder ? 'name'             THEN p_felder ->> 'name' ELSE name END,
        kurzbeschreibung = CASE WHEN p_felder ? 'kurzbeschreibung' THEN p_felder ->> 'kurzbeschreibung' ELSE kurzbeschreibung END,
        schwerpunkt      = CASE WHEN p_felder ? 'schwerpunkt'      THEN p_felder ->> 'schwerpunkt' ELSE schwerpunkt END,
        rubriken         = CASE WHEN p_felder ? 'rubriken'         THEN coalesce((SELECT array_agg(x) FROM jsonb_array_elements_text(p_felder -> 'rubriken') x), '{}') ELSE rubriken END,
        bild             = CASE WHEN p_felder ? 'bild'             THEN nullif(p_felder ->> 'bild', '') ELSE bild END,
        bild_ki          = CASE WHEN p_felder ? 'bild_ki'          THEN (p_felder ->> 'bild_ki')::boolean ELSE bild_ki END,
        aktiv            = CASE WHEN p_felder ? 'aktiv'            THEN (p_felder ->> 'aktiv')::boolean ELSE aktiv END
    WHERE slug = p_slug;
    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('magazin_autor_speichern', 'magazin_autoren', p_slug, to_jsonb(a), p_felder);
    RETURN jsonb_build_object('ok', true);
END;
$$;

-- Autoren lesen (alle, auch inaktive)
CREATE OR REPLACE FUNCTION public.admin_magazin_autoren()
RETURNS JSONB
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
    PERFORM public.admin_pflicht();
    RETURN coalesce((SELECT jsonb_agg(to_jsonb(a) ORDER BY a.name) FROM public.magazin_autoren a), '[]'::jsonb);
END;
$$;


-- ── Rechte ───────────────────────────────────────────────────────────────────
DO $$
DECLARE
    f TEXT;
BEGIN
    FOREACH f IN ARRAY ARRAY[
        'admin_pflicht()',
        'admin_magazin_liste(text)',
        'admin_magazin_beitrag(uuid)',
        'admin_magazin_kosten(date)',
        'admin_magazin_anlegen(text, text, text)',
        'admin_magazin_speichern(uuid, jsonb, jsonb)',
        'admin_magazin_veroeffentlichen(uuid)',
        'admin_magazin_zurueckziehen(uuid)',
        'admin_magazin_korrektur(uuid, text, text)',
        'admin_magazin_autor_speichern(text, jsonb)',
        'admin_magazin_autoren()'
    ] LOOP
        EXECUTE format('ALTER FUNCTION public.%s OWNER TO postgres', f);
        EXECUTE format('REVOKE EXECUTE ON FUNCTION public.%s FROM PUBLIC, anon', f);
        EXECUTE format('GRANT EXECUTE ON FUNCTION public.%s TO authenticated', f);
    END LOOP;
END $$;

COMMIT;


-- ── Kontrolle (erwartet: 11 Zeilen, alle definer, anon_darf = false, authenticated_darf = true) ──
SELECT p.proname AS funktion,
       CASE WHEN p.prosecdef THEN 'definer' ELSE 'invoker' END AS sicherheit,
       has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_darf,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') AS authenticated_darf
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public' AND (p.proname = 'admin_pflicht' OR p.proname LIKE 'admin_magazin_%')
ORDER BY 1;
