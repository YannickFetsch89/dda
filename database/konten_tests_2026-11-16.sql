-- konten_tests_2026-11-16.sql – DiesDasDüsseldorf
-- SQL-Tests zu database/konten_2026-11-16.sql (Plan Abschnitt 16.2, Ergebnis von Schritt 3).
--
-- WAS PASSIERT: Der Block legt Testkonten (A, B, C, D), Test-Einwilligungstexte, Test-Merkungen,
-- Test-Events und Test-Protokollzeilen an, prüft Rechte, Trigger und Funktionen als die jeweilige Rolle
-- (anon, authenticated als A/B/C/Admin, service_role) und bricht am Ende ABSICHTLICH mit einer
-- Fehlermeldung ab. Durch den Abbruch wird ALLES zurückgerollt: Es bleibt nichts in der Datenbank.
-- Echte Konten und echte Events werden nicht verändert (bestehende Events werden nur gelesen bzw.
-- innerhalb des Tests kurz gekennzeichnet; auch das wird zurückgerollt).
--
-- ERWARTET: Eine rote Fehlermeldung, die mit „TESTLAUF (alles zurückgerollt)“ beginnt, dann eine Zeile
-- je Test: „ok“ oder „FEHLER“ mit Grund. Bitte die Meldung vollständig an Claude geben.
--
-- Voraussetzung: konten_2026-11-16.sql und konten_stammdaten_2026-11-17.sql sind gelaufen (Stand E16:
-- Vorname, Nachname, Geburtsdatum Pflicht; Abschnitt „Stammdaten und Geburtsdatum“ unten).
-- Ausführen im Supabase-SQL-Editor als postgres.
-- Nicht während eines Pipeline-Laufs (kurze Sperren auf einzelnen Events).

CREATE OR REPLACE FUNCTION pg_temp.zeile(ok BOOLEAN, name TEXT, detail TEXT DEFAULT '')
RETURNS TEXT LANGUAGE sql AS $$
    SELECT E'\n' || CASE WHEN ok THEN 'ok     | ' ELSE 'FEHLER | ' END || name
           || CASE WHEN ok OR coalesce(detail, '') = '' THEN '' ELSE ' | ' || detail END
$$;

DO $$
DECLARE
    a UUID := gen_random_uuid();   -- Mindestalter, ohne (b)
    b UUID := gen_random_uuid();   -- Mindestalter, ohne (b), analyse_erlaubt
    c UUID := gen_random_uuid();   -- Mindestalter, mit (b)
    d UUID := gen_random_uuid();   -- ohne Mindestalter
    admin_id UUID;
    ev   UUID[];                   -- bestehende, nicht sensible Events
    s    UUID;                     -- bestehendes Event, im Test sensibel gekennzeichnet
    t    UUID;                     -- bestehendes Event, später gekennzeichnet
    neu1 UUID := gen_random_uuid();
    neu2 UUID := gen_random_uuid();
    log  TEXT := '';
    n    INTEGER;
    x    TEXT;
    ids  UUID[];
    mail_a TEXT := 'ddd-test-a-' || substr(md5(random()::text), 1, 8) || '@example.invalid';
    gross TEXT;
BEGIN
    -- ── Aufbau (als postgres) ────────────────────────────────────────────────
    INSERT INTO auth.users (id, instance_id, aud, role, email, created_at, updated_at, raw_app_meta_data, raw_user_meta_data)
    VALUES (a, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', mail_a, now(), now(), '{}', '{}'),
           (b, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'ddd-test-b-' || b || '@example.invalid', now(), now(), '{}', '{}'),
           (c, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'ddd-test-c-' || c || '@example.invalid', now(), now(), '{}', '{}'),
           (d, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'ddd-test-d-' || d || '@example.invalid', now(), now(), '{"x":1}', '{"mindestalter":"2026-11","nutzungsbedingungen":"2026-11"}');

    log := log || pg_temp.zeile((SELECT count(*) FROM public.profiles WHERE id IN (a, b, c, d)) = 4,
                                'Profile per profil_anlegen angelegt');
    log := log || pg_temp.zeile((SELECT mindestalter_bestaetigt_am IS NULL AND nutzungsbedingungen_version IS NULL
                                   FROM public.profiles WHERE id = d)
                                AND NOT EXISTS (SELECT 1 FROM public.einwilligungen WHERE nutzer_id = d),
                                'Metadaten aus signUp setzen keinen Nachweis (Konto D)');

    SELECT id INTO admin_id FROM public.profiles WHERE rolle = 'admin' ORDER BY erstellt_am LIMIT 1;

    INSERT INTO public.einwilligungstexte (version, art, zweck, text)
    SELECT 'test-' || art, art, 'Test', 'Testtext ' || art
    FROM unnest(ARRAY['mindestalter', 'nutzungsbedingungen', 'personalisierung',
                      'sensible_events', 'analyse', 'geburtstagsmail']) art;

    PERFORM public.einwilligung_setzen(a, 'mindestalter', true, 'test-mindestalter', 'registrierung');
    PERFORM public.einwilligung_setzen(b, 'mindestalter', true, 'test-mindestalter', 'registrierung');
    PERFORM public.einwilligung_setzen(c, 'mindestalter', true, 'test-mindestalter', 'registrierung');
    PERFORM public.einwilligung_setzen(b, 'analyse', true, 'test-analyse', 'abschlussseite');
    PERFORM public.einwilligung_setzen(c, 'sensible_events', true, 'test-sensible_events', 'abschlussseite');

    SELECT array_agg(id) INTO ev FROM (
        SELECT e.id FROM public.events e
        WHERE NOT EXISTS (SELECT 1 FROM public.event_sensibel x WHERE x.event_id = e.id)
        ORDER BY e.erstellt_am DESC LIMIT 505) z;
    s := ev[array_length(ev, 1)];
    t := ev[array_length(ev, 1) - 1];
    INSERT INTO public.event_sensibel (event_id, grund, quelle) VALUES (s, 'religion', 'hand');

    -- ── Merkliste als Nutzer A ───────────────────────────────────────────────
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        INSERT INTO public.merkliste (nutzer_id, event_id) VALUES (a, ev[1]);
        RESET ROLE;
        log := log || pg_temp.zeile(true, 'A merkt eigenes Event');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'A merkt eigenes Event', SQLERRM);
    END;
    log := log || pg_temp.zeile((SELECT merkliste_begonnen_am IS NOT NULL FROM public.profiles WHERE id = a),
                                'Erster Eintrag setzt merkliste_begonnen_am');

    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        INSERT INTO public.merkliste (nutzer_id, event_id) VALUES (b, ev[2]);
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'A fügt Zeile für B ein', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%row-level security%', 'A fügt Zeile für B ein → abgelehnt', SQLERRM);
    END;

    INSERT INTO public.merkliste (nutzer_id, event_id) VALUES (b, ev[2]);   -- als postgres, für Lesetest
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        SELECT count(*) INTO n FROM public.merkliste WHERE nutzer_id = b;
        RESET ROLE;
        log := log || pg_temp.zeile(n = 0, 'A sieht B''s Merkliste nicht', 'Zeilen: ' || n);
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'A sieht B''s Merkliste nicht', SQLERRM);
    END;

    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        DELETE FROM public.merkliste WHERE nutzer_id = b;
        GET DIAGNOSTICS n = ROW_COUNT;
        DELETE FROM public.merkliste WHERE nutzer_id = a;
        RESET ROLE;
        log := log || pg_temp.zeile(n = 0, 'A löscht B''s Zeilen nicht', 'gelöscht: ' || n);
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'A löscht eigene Zeilen', SQLERRM);
    END;
    log := log || pg_temp.zeile((SELECT merkliste_begonnen_am IS NOT NULL FROM public.profiles WHERE id = a)
                                AND NOT EXISTS (SELECT 1 FROM public.merkliste WHERE nutzer_id = a),
                                'Nach Löschen aller Einträge bleibt merkliste_begonnen_am');

    -- Ohne Mindestalter (D)
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', d, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        INSERT INTO public.merkliste (nutzer_id, event_id) VALUES (d, ev[3]);
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'D ohne Mindestalter merkt', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'mindestalter_fehlt', 'D ohne Mindestalter → mindestalter_fehlt', SQLERRM);
    END;
    log := log || pg_temp.zeile((SELECT merkliste_begonnen_am IS NULL FROM public.profiles WHERE id = d),
                                'Abgewiesener INSERT lässt merkliste_begonnen_am leer');

    -- ── Sensible Events ──────────────────────────────────────────────────────
    -- B ohne (b), erster eigener INSERT ist sensibel (B hat bisher nur die postgres-Zeile, die A nicht löschen durfte)
    DELETE FROM public.merkliste WHERE nutzer_id = b;
    UPDATE public.profiles SET merkliste_begonnen_am = NULL WHERE id = b;
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', b, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        INSERT INTO public.merkliste (nutzer_id, event_id) VALUES (b, s);
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'B ohne (b) merkt sensibles Event', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'nur_geraet', 'B ohne (b) merkt sensibles Event → nur_geraet', SQLERRM);
    END;
    log := log || pg_temp.zeile((SELECT merkliste_begonnen_am IS NULL FROM public.profiles WHERE id = b),
                                'nur_geraet lässt merkliste_begonnen_am leer');

    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', c, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        INSERT INTO public.merkliste (nutzer_id, event_id) VALUES (c, s), (c, t), (c, ev[4]);
        RESET ROLE;
        log := log || pg_temp.zeile(true, 'C mit (b) merkt sensibles Event');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'C mit (b) merkt sensibles Event', SQLERRM);
    END;

    -- Spätere Kennzeichnung von T: bei B (ohne b) weg, bei C (mit b) bleibt
    INSERT INTO public.merkliste (nutzer_id, event_id) VALUES (b, t), (b, ev[4]);
    INSERT INTO public.event_sensibel (event_id, grund, quelle) VALUES (t, 'politik', 'hand');
    log := log || pg_temp.zeile(NOT EXISTS (SELECT 1 FROM public.merkliste WHERE nutzer_id = b AND event_id = t)
                                AND EXISTS (SELECT 1 FROM public.merkliste WHERE nutzer_id = c AND event_id = t),
                                'Spätere Kennzeichnung: bei B entfernt, bei C (mit b) behalten');

    -- Statistik
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        PERFORM * FROM public.merk_statistik(NULL, NULL);
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'merk_statistik als A', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'nur_admins', 'merk_statistik als A → nur_admins', SQLERRM);
    END;
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('role', 'anon')::text, true);
        SET LOCAL ROLE anon;
        PERFORM * FROM public.merk_statistik(NULL, NULL);
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'merk_statistik als anon', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%permission denied%', 'merk_statistik als anon → permission denied', SQLERRM);
    END;
    IF admin_id IS NULL THEN
        log := log || pg_temp.zeile(false, 'merk_statistik als Admin', 'übersprungen: kein Admin-Konto gefunden');
    ELSE
        BEGIN
            PERFORM set_config('request.jwt.claims', json_build_object('sub', admin_id, 'role', 'authenticated')::text, true);
            SET LOCAL ROLE authenticated;
            SELECT count(*) FILTER (WHERE event_id IN (s, t)),
                   coalesce(sum(anzahl) FILTER (WHERE event_id = ev[4]), 0)
              INTO n, x
              FROM public.merk_statistik(NULL, NULL);
            RESET ROLE;
            -- ev[4]: B (analyse) und C (ohne analyse) → genau 1
            log := log || pg_temp.zeile(n = 0 AND x = '1',
                                        'merk_statistik als Admin: keine sensiblen Events, nur Konten mit analyse_erlaubt',
                                        'sensible Zeilen: ' || n || ', Anzahl ev4: ' || x);
        EXCEPTION WHEN others THEN
            log := log || pg_temp.zeile(false, 'merk_statistik als Admin', SQLERRM);
        END;
    END IF;

    -- Widerruf (b) bei C: sensible Zeilen raus, IDs zurück
    ids := public.einwilligung_setzen(c, 'sensible_events', false, 'test-sensible_events', 'konto_schalter');
    log := log || pg_temp.zeile(ids @> ARRAY[s, t] AND array_length(ids, 1) = 2
                                AND NOT EXISTS (SELECT 1 FROM public.merkliste WHERE nutzer_id = c AND event_id IN (s, t))
                                AND EXISTS (SELECT 1 FROM public.merkliste WHERE nutzer_id = c AND event_id = ev[4]),
                                'Widerruf (b): sensible Zeilen entfernt und zurückgegeben, andere bleiben',
                                'Rückgabe: ' || coalesce(array_length(ids, 1), 0));

    -- ── Grenze 500 ───────────────────────────────────────────────────────────
    IF array_length(ev, 1) < 503 THEN
        log := log || pg_temp.zeile(false, 'Grenze 500', 'übersprungen: weniger als 503 Events in der Datenbank');
    ELSE
        INSERT INTO public.merkliste (nutzer_id, event_id) SELECT a, unnest(ev[1:500]);
        BEGIN
            PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
            SET LOCAL ROLE authenticated;
            INSERT INTO public.merkliste (nutzer_id, event_id) VALUES (a, ev[501]);
            RESET ROLE;
            log := log || pg_temp.zeile(false, '501. Eintrag', 'kein Fehler');
        EXCEPTION WHEN others THEN
            log := log || pg_temp.zeile(SQLERRM = 'merkliste_voll', '501. Eintrag → merkliste_voll', SQLERRM);
        END;
        BEGIN
            PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
            SET LOCAL ROLE authenticated;
            INSERT INTO public.merkliste (nutzer_id, event_id) VALUES (a, ev[1]) ON CONFLICT DO NOTHING;
            RESET ROLE;
            log := log || pg_temp.zeile(true, 'Volles Konto: erneutes Merken mit ON CONFLICT DO NOTHING ohne Fehler');
        EXCEPTION WHEN others THEN
            log := log || pg_temp.zeile(false, 'Volles Konto: erneutes Merken mit ON CONFLICT DO NOTHING', SQLERRM);
        END;
        DELETE FROM public.merkliste WHERE nutzer_id = a;
    END IF;

    -- ── Profile: Spaltenrechte und Prüfbedingungen (als A) ───────────────────
    FOREACH x IN ARRAY ARRAY['rolle = ''admin''', 'personalisierung = true', 'sensible_events_erlaubt = true',
                             'analyse_erlaubt = true', 'mindestalter_bestaetigt_am = now()',
                             'nutzungsbedingungen_version = ''x''', 'merkliste_begonnen_am = now()',
                             'geburtsdatum = ''2000-01-01''', 'geburtstagsmail = true',
                             'vorname = ''Test''', 'nachname = ''Test''',
                             'geburtstagsmail_zuletzt = current_date', 'unter16_gesperrt_am = NULL',
                             'erstellt_am = now()']
    LOOP
        BEGIN
            PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
            SET LOCAL ROLE authenticated;
            EXECUTE format('UPDATE public.profiles SET %s WHERE id = %L', x, a);
            RESET ROLE;
            log := log || pg_temp.zeile(false, 'A setzt ' || x, 'kein Fehler');
        EXCEPTION WHEN others THEN
            log := log || pg_temp.zeile(SQLERRM LIKE '%permission denied%', 'A setzt ' || x || ' → permission denied', SQLERRM);
        END;
    END LOOP;

    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        UPDATE public.profiles SET praeferenzen = '{"version":1,"kategorien":["musik"]}' WHERE id = a;
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'A setzt praeferenzen ohne Personalisierung', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%praeferenzen_nur_mit_einwilligung%',
                                    'A setzt praeferenzen ohne Personalisierung → Prüfbedingung', SQLERRM);
    END;

    PERFORM public.einwilligung_setzen(a, 'personalisierung', true, 'test-personalisierung', 'abschlussseite');
    SELECT string_agg(md5(i::text), '') INTO gross FROM generate_series(1, 300) i;   -- rund 9,6 KB
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        UPDATE public.profiles SET praeferenzen = jsonb_build_object('version', 1, 'x', gross) WHERE id = a;
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'A speichert 9 KB praeferenzen', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%praeferenzen_form%', 'A speichert 9 KB praeferenzen → Prüfbedingung', SQLERRM);
    END;
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        UPDATE public.profiles SET praeferenzen = '{"version":1,"kategorien":["musik"]}' WHERE id = a;
        RESET ROLE;
        log := log || pg_temp.zeile(true, 'A speichert praeferenzen mit Personalisierung');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'A speichert praeferenzen mit Personalisierung', SQLERRM);
    END;
    PERFORM public.einwilligung_setzen(a, 'personalisierung', false, 'test-personalisierung', 'konto_schalter');
    log := log || pg_temp.zeile((SELECT praeferenzen = '{}'::jsonb AND NOT personalisierung FROM public.profiles WHERE id = a)
                                AND (SELECT count(*) FROM public.einwilligungen WHERE nutzer_id = a AND art = 'personalisierung') = 2,
                                'Widerruf (a): praeferenzen leer, Nachweiszeile');

    BEGIN
        UPDATE public.profiles SET geburtstagsmail = true WHERE id = a;
        log := log || pg_temp.zeile(false, 'geburtstagsmail ohne geburtsdatum', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%geburtstagsmail_nur_mit_datum%', 'geburtstagsmail ohne geburtsdatum → Prüfbedingung', SQLERRM);
    END;
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        UPDATE public.profiles SET onboarding_fertig_am = now() WHERE id = a;
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'A markiert Profil fertig ohne Stammdaten', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%onboarding_nur_mit_stammdaten%', 'A markiert Profil fertig ohne Stammdaten → Prüfbedingung', SQLERRM);
    END;

    -- ── Rechte auf Tabellen und Funktionen ──────────────────────────────────
    FOREACH x IN ARRAY ARRAY['public.event_sensibel', 'public.sensibel_regeln', 'public.event_sensibel_ausnahmen',
                             'public.merkliste', 'public.einwilligungen', 'public.profiles']
    LOOP
        BEGIN
            PERFORM set_config('request.jwt.claims', json_build_object('role', 'anon')::text, true);
            SET LOCAL ROLE anon;
            EXECUTE 'SELECT count(*) FROM ' || x INTO n;
            RESET ROLE;
            log := log || pg_temp.zeile(false, 'anon liest ' || x, 'kein Fehler, Zeilen: ' || n);
        EXCEPTION WHEN others THEN
            log := log || pg_temp.zeile(SQLERRM LIKE '%permission denied%', 'anon liest ' || x || ' → permission denied', SQLERRM);
        END;
    END LOOP;
    FOREACH x IN ARRAY ARRAY['public.event_sensibel', 'public.sensibel_regeln', 'public.event_sensibel_ausnahmen']
    LOOP
        BEGIN
            PERFORM set_config('request.jwt.claims', json_build_object('sub', c, 'role', 'authenticated')::text, true);
            SET LOCAL ROLE authenticated;
            EXECUTE 'SELECT count(*) FROM ' || x INTO n;
            RESET ROLE;
            log := log || pg_temp.zeile(false, 'authenticated liest ' || x, 'kein Fehler, Zeilen: ' || n);
        EXCEPTION WHEN others THEN
            log := log || pg_temp.zeile(SQLERRM LIKE '%permission denied%', 'authenticated liest ' || x || ' → permission denied', SQLERRM);
        END;
    END LOOP;
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', c, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        SELECT count(*) INTO n FROM public.events e JOIN public.event_sensibel s2 ON s2.event_id = e.id;
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'authenticated: Join events × event_sensibel', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%permission denied%', 'authenticated: Join events × event_sensibel → permission denied', SQLERRM);
    END;
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        INSERT INTO public.einwilligungen (nutzer_id, art, erteilt, textversion, handlung)
        VALUES (a, 'analyse', true, 'test-analyse', 'konto_schalter');
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'A schreibt in einwilligungen', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%permission denied%', 'A schreibt in einwilligungen → permission denied', SQLERRM);
    END;
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        PERFORM public.einwilligung_setzen(a, 'analyse', true, 'test-analyse', 'konto_schalter');
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'A ruft einwilligung_setzen auf', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%permission denied%', 'A ruft einwilligung_setzen auf → permission denied', SQLERRM);
    END;
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        PERFORM public.sensibel_grund('CSD', NULL, NULL);
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'A ruft sensibel_grund auf', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%permission denied%', 'A ruft sensibel_grund auf → permission denied', SQLERRM);
    END;

    -- einwilligungstexte unveränderlich, auch für service_role
    BEGIN
        SET LOCAL ROLE service_role;
        UPDATE public.einwilligungstexte SET text = 'geändert' WHERE version = 'test-analyse';
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'service_role ändert einwilligungstexte', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'einwilligungstexte_unveraenderlich', 'service_role ändert einwilligungstexte → abgelehnt', SQLERRM);
    END;
    BEGIN
        SET LOCAL ROLE service_role;
        DELETE FROM public.einwilligungstexte WHERE version = 'test-analyse';
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'service_role löscht einwilligungstexte', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'einwilligungstexte_unveraenderlich', 'service_role löscht einwilligungstexte → abgelehnt', SQLERRM);
    END;
    BEGIN
        PERFORM public.einwilligung_setzen(a, 'analyse', true, 'gibt-es-nicht', 'konto_schalter');
        log := log || pg_temp.zeile(false, 'Unbekannte textversion', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLSTATE = '23503', 'Unbekannte textversion → Fremdschlüssel-Fehler', SQLERRM);
    END;

    -- ── Sensibel-Trigger auf events (Kopien eines bestehenden Events) ────────
    BEGIN
        INSERT INTO public.events
        SELECT (jsonb_populate_record(NULL::public.events,
                    to_jsonb(e) || jsonb_build_object('id', neu1, 'titel', 'CSD Testlauf ' || neu1,
                                                      'slug', NULL, 'beschreibung', NULL))).*
        FROM public.events e WHERE e.id = ev[5];
        INSERT INTO public.events
        SELECT (jsonb_populate_record(NULL::public.events,
                    to_jsonb(e) || jsonb_build_object('id', neu2, 'titel', 'Messe Düsseldorf Testlauf ' || neu2,
                                                      'slug', NULL, 'beschreibung', NULL))).*
        FROM public.events e WHERE e.id = ev[5];
        log := log || pg_temp.zeile((SELECT grund FROM public.event_sensibel WHERE event_id = neu1) = 'sexualitaet'
                                    AND NOT EXISTS (SELECT 1 FROM public.event_sensibel WHERE event_id = neu2),
                                    'Trigger beim Insert: „CSD …“ gekennzeichnet, „Messe Düsseldorf …“ nicht');

        UPDATE public.events SET beschreibung = 'Mit anschließendem Gottesdienst' WHERE id = neu2;
        log := log || pg_temp.zeile((SELECT grund FROM public.event_sensibel WHERE event_id = neu2) = 'religion',
                                    'Trigger beim Update der Beschreibung: nachgetragen');

        DELETE FROM public.event_sensibel WHERE event_id = neu1;
        INSERT INTO public.event_sensibel_ausnahmen (event_id, notiz) VALUES (neu1, 'Test');
        UPDATE public.events SET beschreibung = 'Queer Party' WHERE id = neu1;
        log := log || pg_temp.zeile(NOT EXISTS (SELECT 1 FROM public.event_sensibel WHERE event_id = neu1),
                                    'Ausnahme: nach Textänderung nicht wieder gekennzeichnet');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'Sensibel-Trigger auf events', SQLERRM);
    END;

    -- ── Anmeldeprotokoll löschen ────────────────────────────────────────────
    INSERT INTO auth.audit_log_entries (id, payload, created_at) VALUES
        (gen_random_uuid(), json_build_object('actor_id', a, 'action', 'login'), now()),
        (gen_random_uuid(), json_build_object('actor_username', mail_a, 'action', 'user_recovery_requested'), now()),
        (gen_random_uuid(), json_build_object('traits', json_build_object('user_id', a, 'user_email', mail_a)), now()),
        (gen_random_uuid(), json_build_object('actor_id', b, 'action', 'login'), now());
    n := public.konto_protokoll_loeschen(a);
    log := log || pg_temp.zeile(n = 3
                                AND NOT EXISTS (SELECT 1 FROM auth.audit_log_entries
                                                WHERE payload::jsonb ->> 'actor_id' = a::text
                                                   OR payload::jsonb ->> 'actor_username' = mail_a
                                                   OR payload::jsonb -> 'traits' ->> 'user_id' = a::text)
                                AND EXISTS (SELECT 1 FROM auth.audit_log_entries WHERE payload::jsonb ->> 'actor_id' = b::text),
                                'konto_protokoll_loeschen: Zeilen von A per ID und Mail weg, B bleibt',
                                'gelöscht: ' || n);
    IF admin_id IS NOT NULL THEN
        BEGIN
            PERFORM public.konto_protokoll_loeschen(admin_id);
            log := log || pg_temp.zeile(false, 'konto_protokoll_loeschen für Admin', 'kein Fehler');
        EXCEPTION WHEN others THEN
            log := log || pg_temp.zeile(SQLERRM = 'admin_konto', 'konto_protokoll_loeschen für Admin → admin_konto', SQLERRM);
        END;
    END IF;

    -- ── Stammdaten und Geburtsdatum (E16, vorher E15) ────────────────────────
    BEGIN
        PERFORM public.einwilligung_setzen(b, 'geburtstagsmail', true, 'test-geburtstagsmail', 'konto_schalter');
        log := log || pg_temp.zeile(false, 'Geburtstagsmail ohne gespeichertes Datum', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'geburtsdatum_fehlt', 'Geburtstagsmail ohne gespeichertes Datum → geburtsdatum_fehlt', SQLERRM);
    END;
    x := public.stammdaten_setzen(b, 'Erika', 'Muster-Frau', ((timezone('Europe/Berlin', now()))::date - INTERVAL '16 years')::date);
    log := log || pg_temp.zeile(x = 'ok' AND (SELECT vorname = 'Erika' AND nachname = 'Muster-Frau' AND geburtsdatum IS NOT NULL
                                                AND NOT geburtstagsmail FROM public.profiles WHERE id = b),
                                'Genau heute vor 16 Jahren → gilt als 16, Stammdaten gespeichert', x);
    log := log || pg_temp.zeile(NOT EXISTS (SELECT 1 FROM public.einwilligungen WHERE nutzer_id = b AND art = 'geburtstagsmail'),
                                'Stammdaten schreiben keine Einwilligungszeile');
    PERFORM public.einwilligung_setzen(b, 'geburtstagsmail', true, 'test-geburtstagsmail', 'abschlussseite');
    log := log || pg_temp.zeile((SELECT geburtstagsmail FROM public.profiles WHERE id = b), 'Geburtstagsmail mit Datum erteilt');
    PERFORM public.einwilligung_setzen(b, 'geburtstagsmail', false, 'test-geburtstagsmail', 'abmeldelink');
    log := log || pg_temp.zeile((SELECT geburtsdatum IS NOT NULL AND NOT geburtstagsmail FROM public.profiles WHERE id = b),
                                'Widerruf (d): Mail aus, Datum bleibt (Pflichtangabe)');
    BEGIN
        PERFORM public.stammdaten_setzen(b, ' Erika', 'Muster', '2000-01-01');
        log := log || pg_temp.zeile(false, 'Vorname mit Leerzeichen am Rand', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM LIKE '%name_plausibel%', 'Vorname mit Leerzeichen am Rand → Prüfbedingung', SQLERRM);
    END;
    BEGIN
        PERFORM public.stammdaten_setzen(b, '', 'Muster', '2000-01-01');
        log := log || pg_temp.zeile(false, 'Leerer Vorname', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'parameter_fehlt', 'Leerer Vorname → parameter_fehlt', SQLERRM);
    END;
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', b, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        UPDATE public.profiles SET onboarding_fertig_am = now() WHERE id = b;
        RESET ROLE;
        log := log || pg_temp.zeile(true, 'B markiert Profil fertig mit Stammdaten');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(false, 'B markiert Profil fertig mit Stammdaten', SQLERRM);
    END;

    x := public.stammdaten_setzen(c, 'Max', 'Muster', ((timezone('Europe/Berlin', now()))::date - INTERVAL '16 years' + INTERVAL '1 day')::date);
    log := log || pg_temp.zeile(x = 'unter_16', 'Morgen vor 16 Jahren → unter_16', x);

    x := public.stammdaten_setzen(a, 'Max', 'Muster', ((timezone('Europe/Berlin', now()))::date - INTERVAL '15 years')::date);
    log := log || pg_temp.zeile(x = 'unter_16'
                                AND (SELECT geburtsdatum IS NULL AND vorname IS NULL AND nachname IS NULL
                                            AND mindestalter_bestaetigt_am IS NULL AND unter16_gesperrt_am IS NOT NULL
                                       FROM public.profiles WHERE id = a)
                                AND EXISTS (SELECT 1 FROM public.einwilligungen
                                            WHERE nutzer_id = a AND art = 'mindestalter' AND NOT erteilt AND handlung = 'altersgrenze'),
                                'Unter 16: Datum nicht gespeichert, Mindestalter entzogen, gesperrt, Nachweis', x);
    BEGIN
        PERFORM public.einwilligung_setzen(a, 'mindestalter', true, 'test-mindestalter', 'abschlussseite');
        log := log || pg_temp.zeile(false, 'Gesperrtes Konto bestätigt Mindestalter erneut', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'unter16_gesperrt', 'Gesperrtes Konto bestätigt Mindestalter erneut → abgelehnt', SQLERRM);
    END;
    BEGIN
        PERFORM set_config('request.jwt.claims', json_build_object('sub', a, 'role', 'authenticated')::text, true);
        SET LOCAL ROLE authenticated;
        INSERT INTO public.merkliste (nutzer_id, event_id) VALUES (a, ev[6]);
        RESET ROLE;
        log := log || pg_temp.zeile(false, 'Gesperrtes Konto merkt', 'kein Fehler');
    EXCEPTION WHEN others THEN
        log := log || pg_temp.zeile(SQLERRM = 'mindestalter_fehlt', 'Gesperrtes Konto merkt → mindestalter_fehlt', SQLERRM);
    END;

    -- ── Ende: absichtlicher Abbruch, alles wird zurückgerollt ────────────────
    RAISE EXCEPTION 'TESTLAUF (alles zurückgerollt) – % ok, % FEHLER%',
        (length(log) - length(replace(log, E'\nok     |', ''))) / length(E'\nok     |'),
        (length(log) - length(replace(log, E'\nFEHLER |', ''))) / length(E'\nFEHLER |'),
        log;
END $$;
