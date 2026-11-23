-- admin_guides_2026-11-23.sql – DiesDasDüsseldorf
-- Plan docs/plan-admin-dashboard-2026-11-23.md, Abschnitt 4.7, Stufe 3b: Bilder und Guide-Pflege im Admin-Bereich.
--
-- Im Supabase-SQL-Editor ausführen, VOR dem Deploy von Stufe 3b. Wiederholbar (CREATE OR REPLACE).
-- Voraussetzung: admin_orte_2026-11-23.sql (Stufe 3a), admin_magazin_2026-11-23.sql (admin_pflicht).
--
-- Entscheidungen des Auftraggebers (23.11.2026, Q6):
--   - Weihnachtsmärkte: Top-5-Rang, Ausschließen und Freischalten pflegt das Dashboard. Der Import
--     (scraper/weihnachtsmaerkte/import_maerkte.py) übernimmt top5_rang und ausgeschlossen bei vorhandenen Zeilen
--     aus der Datenbank. Saisonzeiten und Ruhetage bleiben in den CSV-Dateien.
--   - Spielplätze: Prüf-Codes bestätigen, Ausschließen und Freischalten im Dashboard. Jede Änderung trägt das Feld in
--     extras.spielplatz.redaktion ein; die Importe (stadt_import.py, abenteuer_import.py) lassen diese Felder stehen.
--   - Bilder: Google-Fotos als Kandidaten auf Knopfdruck; jede Auswahl setzt foto_manuell (schützt vor Skript-Läufen).
--
-- Alle Funktionen: SECURITY DEFINER, Eigentümer postgres, zuerst admin_pflicht(), fester search_path,
-- EXECUTE nur für authenticated, Protokoll in admin_protokoll.

BEGIN;

-- ── Hilfe: heutiges Datum (Berlin) als Text ──────────────────────────────────
CREATE OR REPLACE FUNCTION public.admin_heute()
RETURNS TEXT
LANGUAGE sql
STABLE
SET search_path = public, pg_temp
AS $$
    SELECT to_char(now() AT TIME ZONE 'Europe/Berlin', 'YYYY-MM-DD');
$$;


-- ── 1. Bild wählen ───────────────────────────────────────────────────────────
-- p_bild.art:
--   'google' → google_foto {name, breite, hoehe, autor, autor_url}, bild_url NULL, bild_attribution = autor
--              (nicht bei Spielstätten: dort keine Google-Fotos, scraper/orte/ortsbilder.py)
--   'eigen'  → bild_url = Datei unter /ort-bilder/…, bild_attribution und bild_link (https) frei
--   'keins'  → kein Bild (bild_url, google_foto, Nachweis weg)
-- Immer: foto_manuell = heute, foto_version + 1 (neue Bildadresse, kein alter Browser-Cache), bild_fokus weg.

CREATE OR REPLACE FUNCTION public.admin_ort_bild_setzen(p_id UUID, p_bild JSONB)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    o public.orte%ROWTYPE;
    art TEXT := p_bild->>'art';
    g JSONB := p_bild->'google_foto';
    url TEXT := nullif(btrim(coalesce(p_bild->>'bild_url', '')), '');
    nachweis TEXT := nullif(btrim(coalesce(p_bild->>'bild_attribution', '')), '');
    link TEXT := nullif(btrim(coalesce(p_bild->>'bild_link', '')), '');
    basis JSONB;
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO o FROM public.orte WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_ort_fehlt: Ort existiert nicht'; END IF;

    basis := (coalesce(o.extras, '{}'::jsonb) - 'bild_fokus')
             || jsonb_build_object('foto_manuell', public.admin_heute(),
                                   'foto_version', coalesce((o.extras->>'foto_version')::int, 0) + 1);

    IF art = 'google' THEN
        IF o.typ = 'spielstaette' THEN RAISE EXCEPTION 'admin_bild_google: Spielstätten bekommen keine Google-Fotos'; END IF;
        IF jsonb_typeof(g) <> 'object' OR coalesce(g->>'name', '') !~ '^places/[A-Za-z0-9_-]+/photos/[A-Za-z0-9_-]+$' THEN
            RAISE EXCEPTION 'admin_bild_google: ungültiger Foto-Name';
        END IF;
        IF coalesce(g->>'autor_url', '') <> '' AND g->>'autor_url' !~ '^https://' THEN
            RAISE EXCEPTION 'admin_bild_google: Urheber-Link muss https sein';
        END IF;
        UPDATE public.orte
        SET bild_url = NULL,
            bild_attribution = left(nullif(btrim(coalesce(g->>'autor', '')), ''), 200),
            extras = (basis - 'bild_link') || jsonb_build_object('google_foto', jsonb_build_object(
                'name', g->>'name', 'breite', (g->>'breite')::int, 'hoehe', (g->>'hoehe')::int,
                'autor', g->>'autor', 'autor_url', nullif(g->>'autor_url', '')))
        WHERE id = o.id;
    ELSIF art = 'eigen' THEN
        IF url IS NULL OR url !~ '^/ort-bilder/[a-z0-9][a-z0-9/_-]*\.(webp|jpg|jpeg|png)$' OR url LIKE '%..%' THEN
            RAISE EXCEPTION 'admin_bild_eigen: Bild muss unter /ort-bilder/ liegen (webp, jpg, png)';
        END IF;
        IF link IS NOT NULL AND link !~ '^https://[^\s]+$' THEN RAISE EXCEPTION 'admin_bild_eigen: Link muss https sein'; END IF;
        UPDATE public.orte
        SET bild_url = url,
            bild_attribution = left(nachweis, 200),
            extras = CASE WHEN link IS NULL THEN basis - 'bild_link' ELSE basis || jsonb_build_object('bild_link', link) END
        WHERE id = o.id;
    ELSIF art = 'keins' THEN
        UPDATE public.orte
        SET bild_url = NULL, bild_attribution = NULL, extras = basis - 'google_foto' - 'bild_link'
        WHERE id = o.id;
    ELSE
        RAISE EXCEPTION 'admin_bild_art: unbekannte Art';
    END IF;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('ort_bild', 'orte', o.id::text,
            jsonb_build_object('bild_url', o.bild_url, 'bild_attribution', o.bild_attribution,
                               'google_foto', o.extras->'google_foto', 'bild_link', o.extras->'bild_link'),
            p_bild);
    RETURN jsonb_build_object('ok', true, 'slug', o.slug);
END;
$$;


-- ── 2. Bildausschnitt ────────────────────────────────────────────────────────
-- „35%“ (senkrechte Lage, 0 % oben), „oben“, „unten“ oder NULL (Mitte) – wie ortBildFokus in web/lib/orte.ts.

CREATE OR REPLACE FUNCTION public.admin_ort_bild_fokus(p_id UUID, p_fokus TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    o public.orte%ROWTYPE;
    f TEXT := nullif(btrim(coalesce(p_fokus, '')), '');
BEGIN
    PERFORM public.admin_pflicht();
    IF f IS NOT NULL AND f !~ '^(100|[1-9]?[0-9])%$' AND f NOT IN ('oben', 'unten') THEN
        RAISE EXCEPTION 'admin_bild_fokus: 0%% bis 100%%, oben oder unten';
    END IF;
    SELECT * INTO o FROM public.orte WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_ort_fehlt: Ort existiert nicht'; END IF;
    UPDATE public.orte
    SET extras = CASE WHEN f IS NULL THEN coalesce(extras, '{}'::jsonb) - 'bild_fokus'
                      ELSE coalesce(extras, '{}'::jsonb) || jsonb_build_object('bild_fokus', f) END
    WHERE id = o.id;
    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('ort_bild_fokus', 'orte', o.id::text, jsonb_build_object('bild_fokus', o.extras->'bild_fokus'), jsonb_build_object('bild_fokus', f));
    RETURN jsonb_build_object('ok', true);
END;
$$;


-- ── 3. Clubs ↔ Bar ───────────────────────────────────────────────────────────
-- 'freigeben'          → club_freigegeben = heute (Top-Empfehlung, Stufe A), nur mit Club-Profil
-- 'freigabe_entziehen' → club_freigegeben weg (Stufe B/C)
-- 'aus_hub'            → kein_club = Grund (clubs.py markiert den Ort nie wieder). Zeile vom Typ club wird zur Bar:
--                        typ kneipe, vorher_typ club, unterart bar (falls leer); sonst nur auch_club weg.
--                        Die alte Club-URL leitet auf den Bar-Hub, sobald der Ort dort sichtbar ist (Score ≥ 7).
-- 'in_hub'             → kein_club weg; bei Nicht-Clubs auch_club = true (sichtbar mit Club-Profil und Club-Score)

CREATE OR REPLACE FUNCTION public.admin_club_setzen(p_id UUID, p_aktion TEXT, p_grund TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    o public.orte%ROWTYPE;
    x JSONB;
    grund TEXT := nullif(btrim(coalesce(p_grund, '')), '');
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO o FROM public.orte WHERE id = p_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'admin_ort_fehlt: Ort existiert nicht'; END IF;
    IF o.typ NOT IN ('club', 'kneipe', 'restaurant', 'cafe', 'imbiss') THEN
        RAISE EXCEPTION 'admin_club_typ: nur Clubs, Bars/Kneipen, Restaurants, Cafés und Imbisse';
    END IF;
    x := coalesce(o.extras, '{}'::jsonb);

    IF p_aktion = 'freigeben' THEN
        IF jsonb_typeof(x->'club') IS DISTINCT FROM 'object' THEN
            RAISE EXCEPTION 'admin_club_profil: kein Club-Profil (zuerst clubs_profil.py laufen lassen)';
        END IF;
        UPDATE public.orte SET extras = x || jsonb_build_object('club_freigegeben', public.admin_heute()) WHERE id = o.id;
    ELSIF p_aktion = 'freigabe_entziehen' THEN
        UPDATE public.orte SET extras = x - 'club_freigegeben' WHERE id = o.id;
    ELSIF p_aktion = 'aus_hub' THEN
        IF grund IS NULL OR length(grund) < 3 THEN RAISE EXCEPTION 'admin_grund_fehlt: Bitte einen Grund angeben'; END IF;
        IF o.typ = 'club' THEN
            UPDATE public.orte
            SET typ = 'kneipe',
                extras = (x - 'auch_club')
                         || jsonb_build_object('kein_club', left(grund, 300), 'vorher_typ', 'club',
                                               'unterart', coalesce(nullif(x->>'unterart', ''), 'bar'))
            WHERE id = o.id;
        ELSE
            UPDATE public.orte SET extras = (x - 'auch_club') || jsonb_build_object('kein_club', left(grund, 300)) WHERE id = o.id;
        END IF;
    ELSIF p_aktion = 'in_hub' THEN
        IF o.typ = 'club' THEN
            UPDATE public.orte SET extras = x - 'kein_club' WHERE id = o.id;
        ELSE
            UPDATE public.orte SET extras = (x - 'kein_club') || jsonb_build_object('auch_club', true) WHERE id = o.id;
        END IF;
    ELSE
        RAISE EXCEPTION 'admin_club_aktion: unbekannte Aktion';
    END IF;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('club_' || p_aktion, 'orte', o.id::text,
            jsonb_build_object('typ', o.typ, 'auch_club', x->'auch_club', 'kein_club', x->'kein_club',
                               'club_freigegeben', x->'club_freigegeben', 'unterart', x->'unterart'),
            jsonb_build_object('grund', grund));
    RETURN jsonb_build_object('ok', true);
END;
$$;


-- ── 4. Weihnachtsmärkte ──────────────────────────────────────────────────────
-- 'rang'           → top5_rang 1–5 (p_wert) oder leer; derselbe Rang wird bei anderen Märkten gelöscht
-- 'ausschliessen'  → ausgeschlossen = Grund, aktiv = false (mit freigeschaltet_am leitet die URL auf den Hub)
-- 'einschliessen'  → ausgeschlossen weg (Freischalten danach extra)
-- 'freischalten'   → wie database/weihnachtsmaerkte_freischalten.sql: nicht ausgeschlossen, mindestens eine Saison mit
--                    von, bis und Wochenzeiten; freigeschaltet_am nur beim ersten Mal

CREATE OR REPLACE FUNCTION public.admin_wm_setzen(p_id UUID, p_aktion TEXT, p_wert TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    o public.orte%ROWTYPE;
    wm JSONB;
    wert TEXT := nullif(btrim(coalesce(p_wert, '')), '');
    rang INTEGER;
    verdraengt INTEGER := 0;
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO o FROM public.orte WHERE id = p_id FOR UPDATE;
    IF NOT FOUND OR o.typ <> 'weihnachtsmarkt' THEN RAISE EXCEPTION 'admin_wm_fehlt: kein Weihnachtsmarkt'; END IF;
    wm := coalesce(o.extras->'weihnachtsmarkt', '{}'::jsonb);

    IF p_aktion = 'rang' THEN
        IF wert IS NOT NULL THEN
            IF wert !~ '^[1-5]$' THEN RAISE EXCEPTION 'admin_wm_rang: Rang 1 bis 5 oder leer'; END IF;
            rang := wert::int;
            UPDATE public.orte
            SET extras = jsonb_set(extras, '{weihnachtsmarkt,top5_rang}', 'null'::jsonb)
            WHERE typ = 'weihnachtsmarkt' AND id <> o.id AND (extras->'weihnachtsmarkt'->>'top5_rang')::int = rang;
            GET DIAGNOSTICS verdraengt = ROW_COUNT;
        END IF;
        UPDATE public.orte
        SET extras = jsonb_set(coalesce(extras, '{}'::jsonb), '{weihnachtsmarkt}', wm || jsonb_build_object('top5_rang', rang))
        WHERE id = o.id;
    ELSIF p_aktion = 'ausschliessen' THEN
        IF wert IS NULL OR length(wert) < 3 THEN RAISE EXCEPTION 'admin_grund_fehlt: Bitte einen Grund angeben'; END IF;
        UPDATE public.orte
        SET aktiv = false,
            extras = jsonb_set(coalesce(extras, '{}'::jsonb), '{weihnachtsmarkt}', wm || jsonb_build_object('ausgeschlossen', left(wert, 300)))
        WHERE id = o.id;
    ELSIF p_aktion = 'einschliessen' THEN
        UPDATE public.orte
        SET extras = jsonb_set(coalesce(extras, '{}'::jsonb), '{weihnachtsmarkt}', wm || jsonb_build_object('ausgeschlossen', NULL))
        WHERE id = o.id;
    ELSIF p_aktion = 'freischalten' THEN
        IF coalesce(wm->>'ausgeschlossen', '') <> '' THEN RAISE EXCEPTION 'admin_wm_ausgeschlossen: Markt ist ausgeschlossen'; END IF;
        IF NOT EXISTS (
            SELECT 1 FROM jsonb_each(coalesce(wm->'saisons', '{}'::jsonb)) s
            WHERE coalesce(s.value->>'von', '') <> '' AND coalesce(s.value->>'bis', '') <> ''
              AND jsonb_typeof(s.value->'zeiten') = 'array' AND jsonb_array_length(s.value->'zeiten') > 0
        ) THEN
            RAISE EXCEPTION 'admin_wm_saison: keine Saison mit Zeitraum und Öffnungszeiten (saison-CSV + Import)';
        END IF;
        UPDATE public.orte
        SET aktiv = true,
            extras = jsonb_set(coalesce(extras, '{}'::jsonb), '{weihnachtsmarkt}',
                       wm || jsonb_build_object('freigeschaltet_am', coalesce(nullif(wm->>'freigeschaltet_am', ''), public.admin_heute())))
        WHERE id = o.id;
    ELSE
        RAISE EXCEPTION 'admin_wm_aktion: unbekannte Aktion';
    END IF;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('wm_' || p_aktion, 'orte', o.id::text,
            jsonb_build_object('aktiv', o.aktiv, 'top5_rang', wm->'top5_rang', 'ausgeschlossen', wm->'ausgeschlossen'),
            jsonb_build_object('wert', wert, 'verdraengt', verdraengt));
    RETURN jsonb_build_object('ok', true, 'verdraengt', verdraengt);
END;
$$;


-- ── 5. Spielplätze ───────────────────────────────────────────────────────────
-- 'bestaetigen' / 'bestaetigung_entziehen' (p_wert = Prüf-Code; name_unklar und kein_stadtteil lassen sich nicht
--                                           bestätigen – sie sperren immer, Korrektur über korrekturen.csv)
-- 'ausschliessen' (p_wert = Grund; aktiv = false) / 'einschliessen'
-- 'freischalten' → wie database/spielplaetze_freischalten.sql (freischaltbar() in scraper/spielplaetze/score.py)
-- bestaetigt/ausgeschlossen kommen in extras.spielplatz.redaktion: die Importe lassen sie danach stehen.

CREATE OR REPLACE FUNCTION public.admin_spielplatz_setzen(p_id UUID, p_aktion TEXT, p_wert TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    o public.orte%ROWTYPE;
    sp JSONB;
    wert TEXT := nullif(btrim(coalesce(p_wert, '')), '');
    pruefung JSONB;
    bestaetigt JSONB;
    feld TEXT;
BEGIN
    PERFORM public.admin_pflicht();
    SELECT * INTO o FROM public.orte WHERE id = p_id FOR UPDATE;
    IF NOT FOUND OR o.typ <> 'spielplatz' THEN RAISE EXCEPTION 'admin_spielplatz_fehlt: kein Spielplatz'; END IF;
    sp := coalesce(o.extras->'spielplatz', '{}'::jsonb);
    pruefung := coalesce(sp->'pruefung', '[]'::jsonb);
    bestaetigt := coalesce(sp->'bestaetigt', '[]'::jsonb);

    IF p_aktion IN ('bestaetigen', 'bestaetigung_entziehen') THEN
        feld := 'bestaetigt';
        IF wert IS NULL OR NOT pruefung ? wert THEN RAISE EXCEPTION 'admin_spielplatz_code: Code steht nicht in der Prüfung'; END IF;
        IF wert IN ('name_unklar', 'kein_stadtteil') THEN
            RAISE EXCEPTION 'admin_spielplatz_code: % sperrt immer – Korrektur über data/spielplaetze/korrekturen.csv', wert;
        END IF;
        SELECT coalesce(jsonb_agg(DISTINCT c ORDER BY c), '[]'::jsonb) INTO bestaetigt FROM (
            SELECT jsonb_array_elements_text(bestaetigt) AS c
            UNION SELECT wert WHERE p_aktion = 'bestaetigen'
        ) x WHERE NOT (p_aktion = 'bestaetigung_entziehen' AND c = wert);
        sp := sp || jsonb_build_object('bestaetigt', bestaetigt);
    ELSIF p_aktion = 'ausschliessen' THEN
        feld := 'ausgeschlossen';
        IF wert IS NULL OR length(wert) < 3 THEN RAISE EXCEPTION 'admin_grund_fehlt: Bitte einen Grund angeben'; END IF;
        sp := sp || jsonb_build_object('ausgeschlossen', left(wert, 300));
    ELSIF p_aktion = 'einschliessen' THEN
        feld := 'ausgeschlossen';
        sp := sp || jsonb_build_object('ausgeschlossen', NULL);
    ELSIF p_aktion = 'freischalten' THEN
        IF coalesce(sp->>'ausgeschlossen', '') <> '' THEN RAISE EXCEPTION 'admin_spielplatz_ausgeschlossen: Spielplatz ist ausgeschlossen'; END IF;
        IF pruefung ?| array['name_unklar', 'kein_stadtteil']
           OR (pruefung ? 'access_private' AND NOT bestaetigt ? 'access_private')
           OR (pruefung ? 'gruppe_gemischt' AND NOT bestaetigt ? 'gruppe_gemischt') THEN
            RAISE EXCEPTION 'admin_spielplatz_sperre: ein Prüf-Code sperrt die Freischaltung';
        END IF;
        sp := sp || jsonb_build_object('freigeschaltet_am', coalesce(nullif(sp->>'freigeschaltet_am', ''), public.admin_heute()));
    ELSE
        RAISE EXCEPTION 'admin_spielplatz_aktion: unbekannte Aktion';
    END IF;

    IF feld IS NOT NULL THEN
        sp := sp || jsonb_build_object('redaktion', (
            SELECT jsonb_agg(DISTINCT f ORDER BY f) FROM (
                SELECT jsonb_array_elements_text(coalesce(sp->'redaktion', '[]'::jsonb)) AS f UNION SELECT feld) y));
    END IF;

    UPDATE public.orte
    SET aktiv = CASE WHEN p_aktion = 'freischalten' THEN true WHEN p_aktion = 'ausschliessen' THEN false ELSE aktiv END,
        extras = jsonb_set(coalesce(extras, '{}'::jsonb), '{spielplatz}', sp)
    WHERE id = o.id;

    INSERT INTO public.admin_protokoll (aktion, tabelle, ziel_id, vorher, nachher)
    VALUES ('spielplatz_' || p_aktion, 'orte', o.id::text,
            jsonb_build_object('aktiv', o.aktiv, 'bestaetigt', o.extras->'spielplatz'->'bestaetigt',
                               'ausgeschlossen', o.extras->'spielplatz'->'ausgeschlossen'),
            jsonb_build_object('wert', wert));
    RETURN jsonb_build_object('ok', true);
END;
$$;


-- ── 6. Rechte ────────────────────────────────────────────────────────────────
DO $$
DECLARE
    f TEXT;
BEGIN
    FOREACH f IN ARRAY ARRAY[
        'admin_ort_bild_setzen(uuid, jsonb)',
        'admin_ort_bild_fokus(uuid, text)',
        'admin_club_setzen(uuid, text, text)',
        'admin_wm_setzen(uuid, text, text)',
        'admin_spielplatz_setzen(uuid, text, text)'
    ] LOOP
        EXECUTE format('ALTER FUNCTION public.%s OWNER TO postgres', f);
        EXECUTE format('REVOKE EXECUTE ON FUNCTION public.%s FROM PUBLIC, anon', f);
        EXECUTE format('GRANT EXECUTE ON FUNCTION public.%s TO authenticated', f);
    END LOOP;
END $$;

COMMIT;


-- ── Kontrolle (erwartet: 5 Zeilen, alle definer, anon_darf = false, authenticated_darf = true) ──
SELECT p.proname AS funktion,
       CASE WHEN p.prosecdef THEN 'definer' ELSE 'invoker' END AS sicherheit,
       has_function_privilege('anon', p.oid, 'EXECUTE') AS anon_darf,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') AS authenticated_darf
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.proname IN ('admin_ort_bild_setzen', 'admin_ort_bild_fokus', 'admin_club_setzen', 'admin_wm_setzen', 'admin_spielplatz_setzen')
ORDER BY 1;
