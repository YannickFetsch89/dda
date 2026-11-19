-- magazin_tests_2026-11-19.sql – DiesDasDüsseldorf
-- SQL-Tests zu database/magazin_2026-11-19.sql (Plan docs/plan-redaktion-2026-11-19.md, 3.1 und 7.3).
--
-- WAS PASSIERT: Der Block legt einen Test-Autor und Test-Beiträge an, prüft Prüfbedingungen, den Workflow-Trigger
-- und die Rechte als die jeweilige Rolle (postgres, service_role, anon, authenticated) und bricht am Ende
-- ABSICHTLICH mit einer Fehlermeldung ab. Durch den Abbruch wird ALLES zurückgerollt: Es bleibt nichts in der
-- Datenbank.
--
-- ERWARTET: Eine rote Fehlermeldung, die mit „TESTLAUF (alles zurückgerollt)“ beginnt, dann eine Zeile je Test:
-- „ok“ oder „FEHLER“ mit Grund. Bitte die Meldung vollständig an Claude geben.
--
-- Voraussetzung: magazin_2026-11-19.sql ist gelaufen. Ausführen im Supabase-SQL-Editor als postgres.
-- Hinweis: Tests über die REST-Schnittstelle (PostgREST, z. B. select=* mit dem anon-Schlüssel) folgen in Schritt 2
-- (Plan 7.3); hier wird direkt in SQL mit SET LOCAL ROLE geprüft.

CREATE OR REPLACE FUNCTION pg_temp.zeile(ok BOOLEAN, name TEXT, detail TEXT DEFAULT '')
RETURNS TEXT LANGUAGE sql AS $$
    SELECT E'\n' || CASE WHEN ok THEN 'ok     | ' ELSE 'FEHLER | ' END || name
           || CASE WHEN ok OR coalesce(detail, '') = '' THEN '' ELSE ' | ' || detail END
$$;

DO $$
DECLARE
    t_autor  TEXT := 'test-autor-magazin';
    b1     UUID := gen_random_uuid();   -- wird veröffentlicht
    b2     UUID := gen_random_uuid();   -- bleibt Entwurf
    b3     UUID := gen_random_uuid();   -- in_pruefung, Veröffentlichung in der Zukunft
    log    TEXT := '';
    n      INTEGER;
    x      TEXT;
    gruen  JSONB := '{"ergebnis": "gruen"}'::jsonb;
    t_teaser TEXT := 'Testteaser für den Magazin-Testlauf, lang genug für die Prüfbedingung von achtzig Zeichen mindestens.';
BEGIN
    INSERT INTO public.magazin_autoren (slug, name, kurzbeschreibung, schwerpunkt, rubriken, bild)
    VALUES (t_autor, 'Test Pseudonym', 'Nur für den Testlauf.', 'Test', ARRAY['wochenvorschau'], '/magazin-autoren/test.webp');
    INSERT INTO public.magazin_autoren (slug, name, kurzbeschreibung, schwerpunkt, aktiv)
    VALUES (t_autor || '-inaktiv', 'Inaktiv', 'Nur für den Testlauf.', 'Test', FALSE);

    -- ── Prüfbedingungen (als postgres) ───────────────────────────────────────
    INSERT INTO public.magazin_beitraege (id, slug, rubrik, autor_slug, titel, teaser, hero_bild)
    VALUES (b1, 'test-magazin-eins', 'wochenvorschau', t_autor, 'Testbeitrag eins', t_teaser, '/fallback/theater-1.webp');
    log := log || pg_temp.zeile((SELECT hero_ki FROM public.magazin_beitraege WHERE id = b1),
                                'Fallback-Hero setzt hero_ki = true');
    log := log || pg_temp.zeile((SELECT status FROM public.magazin_beitraege WHERE id = b1) = 'entwurf',
                                'Neuer Beitrag startet als entwurf');

    -- Hero-Pfade: erlaubt
    FOREACH x IN ARRAY ARRAY['/fallback/theater-1.webp', '/ort-bilder/weihnachtsmaerkte/maerchen-markt.webp',
                             '/magazin-bilder/test-magazin-eins/hero.webp'] LOOP
        BEGIN
            UPDATE public.magazin_beitraege SET hero_bild = x WHERE id = b1;
            log := log || pg_temp.zeile(true, 'Hero erlaubt: ' || x);
        EXCEPTION WHEN others THEN
            log := log || pg_temp.zeile(false, 'Hero erlaubt: ' || x, SQLERRM);
        END;
    END LOOP;
    -- Hero-Pfade: abgelehnt
    FOREACH x IN ARRAY ARRAY['/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp', '/ort-bilder/events/further-nikolausmarkt.webp',
                             '/../x.webp', '/fallback/../geheim.webp', '/fallback/Theater-1.webp', 'https://fremd.de/x.webp',
                             '/fallback/theater-1.gif'] LOOP
        BEGIN
            UPDATE public.magazin_beitraege SET hero_bild = x WHERE id = b1;
            log := log || pg_temp.zeile(false, 'Hero abgelehnt: ' || x, 'kein Fehler');
        EXCEPTION WHEN check_violation THEN
            log := log || pg_temp.zeile(SQLERRM LIKE '%magazin_hero_pfad%', 'Hero abgelehnt: ' || x, SQLERRM);
        END;
    END LOOP;
    UPDATE public.magazin_beitraege SET hero_bild = '/fallback/theater-1.webp' WHERE id = b1;

    -- Slugs
    FOREACH x IN ARRAY ARRAY['redaktion', 'rubrik', 'Gross-Buchstaben', 'mit--doppelstrich', 'umlaut-ü'] LOOP
        BEGIN
            INSERT INTO public.magazin_beitraege (slug, rubrik, autor_slug, titel) VALUES (x, 'saison', t_autor, 'Slugtest');
            log := log || pg_temp.zeile(false, 'Slug abgelehnt: ' || x, 'kein Fehler');
        EXCEPTION WHEN check_violation THEN
            log := log || pg_temp.zeile(SQLERRM LIKE '%magazin_slug_form%', 'Slug abgelehnt: ' || x, SQLERRM);
        END;
    END LOOP;
    BEGIN
        INSERT INTO public.magazin_beitraege (slug, rubrik, autor_slug, titel) VALUES ('test-rubrik', 'monats_tipps', t_autor, 'Rubriktest');
        log := log || pg_temp.zeile(false, 'Rubrik monats_tipps (Unterstrich) abgelehnt', 'kein Fehler');
    EXCEPTION WHEN check_violation THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%magazin_rubrik_werte%', 'Rubrik monats_tipps (Unterstrich) abgelehnt', SQLERRM);
    END;
    BEGIN
        INSERT INTO public.magazin_beitraege (slug, rubrik, autor_slug, titel, teaser) VALUES ('test-teaser', 'saison', t_autor, 'Teasertest', 'zu kurz');
        log := log || pg_temp.zeile(false, 'Teaser unter 80 Zeichen abgelehnt', 'kein Fehler');
    EXCEPTION WHEN check_violation THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%magazin_laengen%', 'Teaser unter 80 Zeichen abgelehnt', SQLERRM);
    END;
    BEGIN
        INSERT INTO public.magazin_beitraege (slug, rubrik, autor_slug, titel, vorschau_hash) VALUES ('test-hash', 'saison', t_autor, 'Hashtest', 'klartext-schluessel');
        log := log || pg_temp.zeile(false, 'vorschau_hash ohne SHA-256-Form abgelehnt', 'kein Fehler');
    EXCEPTION WHEN check_violation THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%magazin_vorschau_hash_form%', 'vorschau_hash ohne SHA-256-Form abgelehnt', SQLERRM);
    END;
    FOREACH x IN ARRAY ARRAY['a,b', 'Gross', ''] LOOP
        BEGIN
            INSERT INTO public.magazin_beitraege (slug, rubrik, autor_slug, titel, alte_slugs)
            VALUES ('test-alt', 'saison', t_autor, 'Alttest', ARRAY['gueltig-alt', x]);
            log := log || pg_temp.zeile(false, 'alte_slugs mit Eintrag „' || x || '“ abgelehnt', 'kein Fehler');
        EXCEPTION WHEN check_violation THEN
            log := log || pg_temp.zeile(SQLERRM LIKE '%magazin_alte_slugs_form%', 'alte_slugs mit Eintrag „' || x || '“ abgelehnt', SQLERRM);
        END;
    END LOOP;

    -- ── Workflow als Pipeline (service_role) ─────────────────────────────────
    BEGIN
        SET LOCAL ROLE service_role;
        INSERT INTO public.magazin_beitraege (id, slug, rubrik, autor_slug, titel, teaser, vorschau_hash)
        VALUES (b2, 'test-magazin-zwei', 'monats-tipps', t_autor, 'Testbeitrag zwei', t_teaser, repeat('a', 64));
        UPDATE public.magazin_beitraege SET status = 'in_pruefung', pruefung = gruen WHERE id = b1;
        RESET ROLE;
        log := log || pg_temp.zeile(true, 'Pipeline legt Entwurf an und setzt in_pruefung');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'Pipeline legt Entwurf an und setzt in_pruefung', SQLERRM);
    END;
    BEGIN
        SET LOCAL ROLE service_role;
        UPDATE public.magazin_beitraege
           SET status = 'veroeffentlicht', veroeffentlicht_am = now(), freigegeben_von = 'Pipeline',
               hero_alt = 'Alt', hero_nachweis = 'Symbolbild'
         WHERE id = b1;
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'Pipeline veröffentlicht → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'magazin_veroeffentlichen_nur_redaktion', 'Pipeline veröffentlicht → abgelehnt', SQLERRM);
    END;
    BEGIN
        SET LOCAL ROLE service_role;
        INSERT INTO public.magazin_beitraege (slug, rubrik, autor_slug, titel, status) VALUES ('test-direkt', 'saison', t_autor, 'Direkttest', 'veroeffentlicht');
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'Pipeline legt veröffentlichten Beitrag an → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'magazin_veroeffentlichen_nur_redaktion', 'Pipeline legt veröffentlichten Beitrag an → abgelehnt', SQLERRM);
    END;

    -- ── Workflow als Auftraggeber (postgres) ─────────────────────────────────
    BEGIN
        UPDATE public.magazin_beitraege SET status = 'veroeffentlicht', veroeffentlicht_am = now(), freigegeben_von = 'Test',
               hero_alt = 'Alt', hero_nachweis = 'Symbolbild', pruefung = gruen WHERE id = b2;
        log := log || pg_temp.zeile(false, 'Veröffentlichen direkt aus entwurf → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'magazin_veroeffentlichen_nur_aus_pruefung', 'Veröffentlichen direkt aus entwurf → abgelehnt', SQLERRM);
    END;
    BEGIN
        UPDATE public.magazin_beitraege SET status = 'veroeffentlicht' WHERE id = b1;
        log := log || pg_temp.zeile(false, 'Veröffentlichen ohne Pflichtfelder → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'magazin_pflichtfelder_fehlen', 'Veröffentlichen ohne Pflichtfelder → abgelehnt', SQLERRM);
    END;
    BEGIN
        UPDATE public.magazin_beitraege SET status = 'veroeffentlicht', veroeffentlicht_am = now() - interval '1 minute',
               freigegeben_von = 'Test', hero_alt = 'Alt', hero_nachweis = 'Symbolbild', pruefung = '{"ergebnis": "rot"}'
         WHERE id = b1;
        log := log || pg_temp.zeile(false, 'Veröffentlichen mit roter Prüfung → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'magazin_pruefung_nicht_gruen', 'Veröffentlichen mit roter Prüfung → abgelehnt', SQLERRM);
    END;
    BEGIN
        UPDATE public.magazin_beitraege SET vorschau_hash = repeat('b', 64) WHERE id = b1;
        UPDATE public.magazin_beitraege SET status = 'veroeffentlicht', veroeffentlicht_am = now() - interval '1 minute',
               freigegeben_von = 'Test', hero_alt = 'Alt', hero_nachweis = 'Symbolbild', pruefung = gruen
         WHERE id = b1;
        log := log || pg_temp.zeile(true, 'Auftraggeber veröffentlicht aus in_pruefung');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'Auftraggeber veröffentlicht aus in_pruefung', SQLERRM);
    END;
    log := log || pg_temp.zeile((SELECT freigegeben_am IS NOT NULL AND vorschau_hash IS NULL FROM public.magazin_beitraege WHERE id = b1),
                                'Veröffentlichen setzt freigegeben_am und leert vorschau_hash');

    -- Beitrag 3: in_pruefung, veröffentlicht mit Zeitpunkt in der Zukunft
    INSERT INTO public.magazin_beitraege (id, slug, rubrik, autor_slug, titel, teaser, hero_bild, hero_alt, hero_nachweis,
                                          status, pruefung)
    VALUES (b3, 'test-magazin-drei', 'saison', t_autor, 'Testbeitrag drei', t_teaser, '/fallback/theater-3.webp', 'Alt',
            'Symbolbild', 'in_pruefung', gruen);
    UPDATE public.magazin_beitraege SET status = 'veroeffentlicht', veroeffentlicht_am = now() + interval '1 day',
           freigegeben_von = 'Test' WHERE id = b3;

    -- ── Lesen als anon / authenticated ───────────────────────────────────────
    BEGIN
        SET LOCAL ROLE anon;
        SELECT count(*) INTO n FROM public.magazin_oeffentlich WHERE id IN (b1, b2, b3);
        RESET ROLE;
        log := log || pg_temp.zeile(n = 1, 'anon sieht über die View nur den sichtbaren Beitrag (nicht Entwurf, nicht Zukunft)', n::text || ' Zeilen');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'anon liest die View', SQLERRM);
    END;
    BEGIN
        SET LOCAL ROLE authenticated;
        SELECT count(*) INTO n FROM public.magazin_beitraege WHERE id IN (b1, b2, b3);
        RESET ROLE;
        log := log || pg_temp.zeile(n = 1, 'authenticated sieht in der Tabelle nur den sichtbaren Beitrag', n::text || ' Zeilen');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'authenticated liest öffentliche Spalten', SQLERRM);
    END;
    FOREACH x IN ARRAY ARRAY['ki_entwurf', 'pruefung', 'vorschau_hash', 'status', 'alte_slugs', 'freigegeben_von'] LOOP
        BEGIN
            SET LOCAL ROLE anon;
            EXECUTE format('SELECT count(%I) FROM public.magazin_beitraege', x) INTO n;
            RESET ROLE;
            log := log || pg_temp.zeile(false, 'anon liest interne Spalte ' || x || ' → abgelehnt', 'kein Fehler');
        EXCEPTION WHEN insufficient_privilege THEN
            log := log || pg_temp.zeile(true, 'anon liest interne Spalte ' || x || ' → abgelehnt');
        END;
    END LOOP;
    BEGIN
        SET LOCAL ROLE anon;
        SELECT count(*) INTO n FROM public.magazin_ki_kosten;
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'anon liest magazin_ki_kosten → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN insufficient_privilege THEN
        log := log || pg_temp.zeile(true, 'anon liest magazin_ki_kosten → abgelehnt');
    END;
    BEGIN
        SET LOCAL ROLE anon;
        INSERT INTO public.magazin_oeffentlich (slug, rubrik, autor_slug, titel) VALUES ('test-anon', 'saison', t_autor, 'Anon');
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'anon schreibt über die View → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN insufficient_privilege THEN
        log := log || pg_temp.zeile(true, 'anon schreibt über die View → abgelehnt');
    END;
    BEGIN
        SET LOCAL ROLE authenticated;
        UPDATE public.magazin_beitraege SET titel = 'Gekapert' WHERE id = b1;
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'authenticated ändert einen Beitrag → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN insufficient_privilege THEN
        log := log || pg_temp.zeile(true, 'authenticated ändert einen Beitrag → abgelehnt');
    END;
    BEGIN
        SET LOCAL ROLE anon;
        SELECT count(*) INTO n FROM public.magazin_autoren WHERE slug LIKE t_autor || '%';
        RESET ROLE;
        log := log || pg_temp.zeile(n = 1, 'anon sieht nur aktive Autoren', n::text || ' Zeilen');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'anon liest Autoren', SQLERRM);
    END;

    -- ── Veröffentlichte Beiträge sind für die Pipeline gesperrt (bis auf pruefung/gemeldet_am) ──
    BEGIN
        SET LOCAL ROLE service_role;
        UPDATE public.magazin_beitraege SET inhalt_md = 'Überschrieben von der Pipeline' WHERE id = b1;
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'Pipeline ändert Text eines veröffentlichten Beitrags → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'magazin_veroeffentlicht_gesperrt', 'Pipeline ändert Text eines veröffentlichten Beitrags → abgelehnt', SQLERRM);
    END;
    BEGIN
        SET LOCAL ROLE service_role;
        UPDATE public.magazin_beitraege SET pruefung = '{"ergebnis": "gruen", "lauf": "taeglich"}', gemeldet_am = now() WHERE id = b1;
        RESET ROLE;
        log := log || pg_temp.zeile(true, 'Pipeline schreibt pruefung und gemeldet_am eines veröffentlichten Beitrags');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'Pipeline schreibt pruefung und gemeldet_am eines veröffentlichten Beitrags', SQLERRM);
    END;
    BEGIN
        SET LOCAL ROLE service_role;
        UPDATE public.magazin_beitraege SET status = 'zurueckgezogen' WHERE id = b1;
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'Pipeline zieht veröffentlichten Beitrag zurück → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'magazin_veroeffentlicht_gesperrt', 'Pipeline zieht veröffentlichten Beitrag zurück → abgelehnt', SQLERRM);
    END;

    -- ── Slug-Historie (als postgres) ─────────────────────────────────────────
    UPDATE public.magazin_beitraege SET slug = 'test-magazin-eins-neu' WHERE id = b1;
    log := log || pg_temp.zeile((SELECT 'test-magazin-eins' = ANY (alte_slugs) FROM public.magazin_beitraege WHERE id = b1),
                                'Slug-Änderung schreibt alten Slug nach alte_slugs');
    BEGIN
        UPDATE public.magazin_beitraege SET slug = 'test-magazin-eins' WHERE id = b2;
        log := log || pg_temp.zeile(false, 'Anderer Beitrag übernimmt alten Slug → abgelehnt', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'magazin_slug_belegt', 'Anderer Beitrag übernimmt alten Slug → abgelehnt', SQLERRM);
    END;
    UPDATE public.magazin_beitraege SET slug = 'test-magazin-eins' WHERE id = b1;
    log := log || pg_temp.zeile((SELECT slug = 'test-magazin-eins' AND 'test-magazin-eins-neu' = ANY (alte_slugs)
                                        AND NOT ('test-magazin-eins' = ANY (alte_slugs))
                                 FROM public.magazin_beitraege WHERE id = b1),
                                'Zurück auf alten Slug: aus alte_slugs entfernt, neuer Slug in der Historie');
    BEGIN
        UPDATE public.magazin_beitraege SET status = 'zurueckgezogen' WHERE id = b1;
        log := log || pg_temp.zeile(true, 'Auftraggeber zieht Beitrag zurück');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'Auftraggeber zieht Beitrag zurück', SQLERRM);
    END;

    -- ── Kostenprotokoll (service_role) ───────────────────────────────────────
    BEGIN
        SET LOCAL ROLE service_role;
        INSERT INTO public.magazin_ki_kosten (art, kosten_usd, beitrag_id, modell) VALUES ('reserviert', 0.22, b2, 'claude-opus-5-5');
        SELECT count(*) INTO n FROM public.magazin_ki_kosten WHERE beitrag_id = b2;
        RESET ROLE;
        log := log || pg_temp.zeile(n = 1, 'Pipeline schreibt und liest magazin_ki_kosten');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'Pipeline schreibt und liest magazin_ki_kosten', SQLERRM);
    END;

    -- ── Ende: absichtlicher Abbruch, alles wird zurückgerollt ────────────────
    RAISE EXCEPTION 'TESTLAUF (alles zurückgerollt) – % ok, % FEHLER%',
        (length(log) - length(replace(log, E'\nok     |', ''))) / length(E'\nok     |'),
        (length(log) - length(replace(log, E'\nFEHLER |', ''))) / length(E'\nFEHLER |'),
        log;
END $$;
