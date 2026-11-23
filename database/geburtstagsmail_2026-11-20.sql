-- geburtstagsmail_2026-11-20.sql – DiesDasDüsseldorf
-- Geburtstagsmail, Kontenplan Schritt 9a (Plan docs/plan-geburtstagsmail-2026-11-20.md, freigegeben 20.11.2026).
--
-- WAS SICH ÄNDERT:
--   1. einwilligung_setzen: Beim Widerruf der Geburtstagsmail wird auch geburtstagsmail_zuletzt geleert (G5). So stimmt
--      die Datenschutzerklärung („das Datum der letzten Mail wird dann gelöscht“). Beim Erteilen bleibt der Wert.
--      Alles andere ist wörtlich wie in konten_stammdaten_2026-11-17.sql.
--   2. Neu, nur service_role (der Versandjob pipeline/geburtstag_mails.py):
--      - geburtstag_heute(geburtsdatum, tag): Hat jemand an diesem Tag Geburtstag? 29.2. → 28.2. in Nicht-Schaltjahren (G6).
--      - geburtstag_empfaenger(tag): IDs aller Empfänger dieses Tages (Einwilligung, nicht gesperrt, Mindestalter
--        bestätigt, in diesem Jahr noch keine Mail).
--      - geburtstag_beanspruchen(nutzer, tag): setzt geburtstagsmail_zuletzt = tag, nur wenn noch nicht in diesem Jahr
--        und die Einwilligung noch gilt; gibt zurück, ob es geklappt hat, und den alten Wert (G7, gegen Doppelversand).
--      - geburtstag_freigeben(nutzer, tag, vorher): setzt den alten Wert zurück, wenn der Versand scheiterte.
--
-- VORAUSSETZUNG: konten_2026-11-16.sql und konten_stammdaten_2026-11-17.sql sind gelaufen. Wiederholbar.
-- Ausführen als postgres im Supabase-SQL-Editor, VOR dem Deploy der Website und vor dem ersten Lauf des Jobs.
-- ERWARTET: am Ende eine Kontrolltabelle, jede Zeile „ok“. Steht dort „FEHLER“, bitte an Claude geben.

BEGIN;


-- ════════════════════════════════════════════════════════════════════════════
-- 1  einwilligung_setzen: Widerruf der Geburtstagsmail leert geburtstagsmail_zuletzt
-- ════════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.einwilligung_setzen(
    nutzer      UUID,
    art         TEXT,
    erteilt     BOOLEAN,
    textversion TEXT,
    handlung    TEXT
)
RETURNS UUID[]
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
#variable_conflict use_column
DECLARE
    gesperrt TIMESTAMPTZ;
    datum    DATE;
    zurueck  UUID[] := '{}';
BEGIN
    IF einwilligung_setzen.nutzer IS NULL OR einwilligung_setzen.erteilt IS NULL THEN
        RAISE EXCEPTION 'parameter_fehlt';
    END IF;

    SELECT p.unter16_gesperrt_am, p.geburtsdatum INTO gesperrt, datum
      FROM public.profiles p
     WHERE p.id = einwilligung_setzen.nutzer
       FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'konto_fehlt';
    END IF;

    CASE einwilligung_setzen.art
        WHEN 'mindestalter' THEN
            IF einwilligung_setzen.erteilt AND gesperrt IS NOT NULL THEN
                RAISE EXCEPTION 'unter16_gesperrt';
            END IF;
            UPDATE public.profiles p
               SET mindestalter_bestaetigt_am = CASE WHEN einwilligung_setzen.erteilt THEN now() END
             WHERE p.id = einwilligung_setzen.nutzer;

        WHEN 'nutzungsbedingungen' THEN
            UPDATE public.profiles p
               SET nutzungsbedingungen_version = CASE WHEN einwilligung_setzen.erteilt
                                                      THEN einwilligung_setzen.textversion END
             WHERE p.id = einwilligung_setzen.nutzer;

        WHEN 'personalisierung' THEN
            -- Eine Anweisung: Die Prüfbedingung praeferenzen_nur_mit_einwilligung gilt sofort.
            UPDATE public.profiles p
               SET personalisierung = einwilligung_setzen.erteilt,
                   praeferenzen     = CASE WHEN einwilligung_setzen.erteilt THEN p.praeferenzen ELSE '{}'::jsonb END
             WHERE p.id = einwilligung_setzen.nutzer;

        WHEN 'sensible_events' THEN
            UPDATE public.profiles p
               SET sensible_events_erlaubt = einwilligung_setzen.erteilt
             WHERE p.id = einwilligung_setzen.nutzer;
            IF NOT einwilligung_setzen.erteilt THEN
                WITH weg AS (
                    DELETE FROM public.merkliste m
                     USING public.event_sensibel s
                     WHERE m.nutzer_id = einwilligung_setzen.nutzer
                       AND s.event_id = m.event_id
                    RETURNING m.event_id
                )
                SELECT coalesce(array_agg(weg.event_id), '{}') INTO zurueck FROM weg;
            END IF;

        WHEN 'analyse' THEN
            UPDATE public.profiles p
               SET analyse_erlaubt = einwilligung_setzen.erteilt
             WHERE p.id = einwilligung_setzen.nutzer;

        WHEN 'geburtstagsmail' THEN
            -- E16: Das Datum ist Pflichtangabe und bleibt beim Widerruf stehen. Erteilen nur mit Datum.
            -- 20.11.2026 (G5): Beim Widerruf wird auch das Datum der letzten Mail gelöscht (Datenschutzerklärung).
            IF einwilligung_setzen.erteilt AND gesperrt IS NOT NULL THEN
                RAISE EXCEPTION 'unter16_gesperrt';
            END IF;
            IF einwilligung_setzen.erteilt AND datum IS NULL THEN
                RAISE EXCEPTION 'geburtsdatum_fehlt';
            END IF;
            UPDATE public.profiles p
               SET geburtstagsmail         = einwilligung_setzen.erteilt,
                   geburtstagsmail_zuletzt = CASE WHEN einwilligung_setzen.erteilt THEN p.geburtstagsmail_zuletzt END
             WHERE p.id = einwilligung_setzen.nutzer;

        ELSE
            RAISE EXCEPTION 'art_unbekannt';
    END CASE;

    INSERT INTO public.einwilligungen (nutzer_id, art, erteilt, textversion, handlung)
    VALUES (einwilligung_setzen.nutzer, einwilligung_setzen.art, einwilligung_setzen.erteilt,
            einwilligung_setzen.textversion, einwilligung_setzen.handlung);

    RETURN zurueck;
END;
$$;

REVOKE ALL ON FUNCTION public.einwilligung_setzen(UUID, TEXT, BOOLEAN, TEXT, TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.einwilligung_setzen(UUID, TEXT, BOOLEAN, TEXT, TEXT) TO service_role;


-- ════════════════════════════════════════════════════════════════════════════
-- 2  Versandjob: Empfänger, Beanspruchen, Freigeben (nur service_role)
-- ════════════════════════════════════════════════════════════════════════════

-- Hat jemand mit diesem Geburtsdatum am Tag `tag` Geburtstag? 29.2. in Nicht-Schaltjahren am 28.2. (G6).
CREATE OR REPLACE FUNCTION public.geburtstag_heute(geburtsdatum DATE, tag DATE)
RETURNS BOOLEAN
LANGUAGE sql
IMMUTABLE
SET search_path = ''
AS $$
    SELECT CASE
        WHEN geburtsdatum IS NULL OR tag IS NULL THEN FALSE
        WHEN extract(month FROM geburtsdatum) = extract(month FROM tag)
         AND extract(day FROM geburtsdatum) = extract(day FROM tag) THEN TRUE
        -- 29.2.: in Jahren ohne 29.2. am 28.2.
        WHEN extract(month FROM geburtsdatum) = 2 AND extract(day FROM geburtsdatum) = 29
         AND extract(month FROM tag) = 2 AND extract(day FROM tag) = 28
         AND extract(month FROM (date_trunc('year', tag) + interval '1 month 28 days')) = 3 THEN TRUE
        ELSE FALSE
    END
$$;

-- Empfänger dieses Tages (Kontenplan 13a): Einwilligung (d), nicht gesperrt, Mindestalter bestätigt, Geburtstag heute,
-- in diesem Jahr noch keine Mail. Höchstens 1000 je Lauf (Sicherung).
CREATE OR REPLACE FUNCTION public.geburtstag_empfaenger(tag DATE)
RETURNS SETOF UUID
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT p.id
      FROM public.profiles p
     WHERE p.geburtstagsmail
       AND p.geburtsdatum IS NOT NULL
       AND p.unter16_gesperrt_am IS NULL
       AND p.mindestalter_bestaetigt_am IS NOT NULL
       AND (p.geburtstagsmail_zuletzt IS NULL OR p.geburtstagsmail_zuletzt < date_trunc('year', geburtstag_empfaenger.tag)::date)
       AND public.geburtstag_heute(p.geburtsdatum, geburtstag_empfaenger.tag)
     ORDER BY p.id
     LIMIT 1000
$$;

-- Vor dem Versand beanspruchen (G7): nur ein Lauf bekommt TRUE. `vorher` ist der alte Wert für geburtstag_freigeben.
CREATE OR REPLACE FUNCTION public.geburtstag_beanspruchen(nutzer UUID, tag DATE)
RETURNS TABLE (beansprucht BOOLEAN, vorher DATE)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    alt DATE;
BEGIN
    SELECT p.geburtstagsmail_zuletzt INTO alt
      FROM public.profiles p
     WHERE p.id = geburtstag_beanspruchen.nutzer
       AND p.geburtstagsmail
       AND p.unter16_gesperrt_am IS NULL
       AND p.mindestalter_bestaetigt_am IS NOT NULL
       AND (p.geburtstagsmail_zuletzt IS NULL OR p.geburtstagsmail_zuletzt < date_trunc('year', geburtstag_beanspruchen.tag)::date)
       FOR UPDATE;
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, NULL::date;
        RETURN;
    END IF;
    UPDATE public.profiles p
       SET geburtstagsmail_zuletzt = geburtstag_beanspruchen.tag
     WHERE p.id = geburtstag_beanspruchen.nutzer;
    RETURN QUERY SELECT TRUE, alt;
END;
$$;

-- Versand gescheitert: alten Wert zurück, aber nur, wenn noch der beanspruchte Tag drinsteht.
CREATE OR REPLACE FUNCTION public.geburtstag_freigeben(nutzer UUID, tag DATE, vorher DATE)
RETURNS VOID
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$
    UPDATE public.profiles p
       SET geburtstagsmail_zuletzt = geburtstag_freigeben.vorher
     WHERE p.id = geburtstag_freigeben.nutzer
       AND p.geburtstagsmail_zuletzt = geburtstag_freigeben.tag
$$;

REVOKE ALL ON FUNCTION public.geburtstag_heute(DATE, DATE) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.geburtstag_heute(DATE, DATE) TO service_role;
REVOKE ALL ON FUNCTION public.geburtstag_empfaenger(DATE) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.geburtstag_empfaenger(DATE) TO service_role;
REVOKE ALL ON FUNCTION public.geburtstag_beanspruchen(UUID, DATE) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.geburtstag_beanspruchen(UUID, DATE) TO service_role;
REVOKE ALL ON FUNCTION public.geburtstag_freigeben(UUID, DATE, DATE) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.geburtstag_freigeben(UUID, DATE, DATE) TO service_role;

COMMIT;


-- ════════════════════════════════════════════════════════════════════════════
-- Kontrolle
-- ════════════════════════════════════════════════════════════════════════════
SELECT pruefung, soll, ist, CASE WHEN soll = ist THEN 'ok' ELSE 'FEHLER' END AS ergebnis
FROM (VALUES
    ('Widerruf leert geburtstagsmail_zuletzt', 'true',
        (pg_get_functiondef('public.einwilligung_setzen(uuid,text,boolean,text,text)'::regprocedure) LIKE '%geburtstagsmail_zuletzt = CASE WHEN einwilligung_setzen.erteilt%')::text),
    ('Geburtstag gleicher Tag',                 'true',  public.geburtstag_heute('1990-11-20', '2026-11-20')::text),
    ('Geburtstag anderer Tag',                  'false', public.geburtstag_heute('1990-11-21', '2026-11-20')::text),
    ('29.2. im Nicht-Schaltjahr am 28.2.',      'true',  public.geburtstag_heute('2000-02-29', '2027-02-28')::text),
    ('29.2. im Schaltjahr nicht am 28.2.',      'false', public.geburtstag_heute('2000-02-29', '2028-02-28')::text),
    ('29.2. im Schaltjahr am 29.2.',            'true',  public.geburtstag_heute('2000-02-29', '2028-02-29')::text),
    ('28.2. bleibt 28.2.',                      'true',  public.geburtstag_heute('1999-02-28', '2028-02-28')::text),
    ('2100 ist kein Schaltjahr',                'true',  public.geburtstag_heute('2000-02-29', '2100-02-28')::text),
    ('anon: geburtstag_empfaenger',             'false', has_function_privilege('anon', 'public.geburtstag_empfaenger(date)', 'EXECUTE')::text),
    ('authenticated: geburtstag_empfaenger',    'false', has_function_privilege('authenticated', 'public.geburtstag_empfaenger(date)', 'EXECUTE')::text),
    ('authenticated: geburtstag_beanspruchen',  'false', has_function_privilege('authenticated', 'public.geburtstag_beanspruchen(uuid,date)', 'EXECUTE')::text),
    ('authenticated: geburtstag_freigeben',     'false', has_function_privilege('authenticated', 'public.geburtstag_freigeben(uuid,date,date)', 'EXECUTE')::text),
    ('service_role: geburtstag_empfaenger',     'true',  has_function_privilege('service_role', 'public.geburtstag_empfaenger(date)', 'EXECUTE')::text),
    ('service_role: geburtstag_beanspruchen',   'true',  has_function_privilege('service_role', 'public.geburtstag_beanspruchen(uuid,date)', 'EXECUTE')::text),
    ('authenticated: einwilligung_setzen',      'false', has_function_privilege('authenticated', 'public.einwilligung_setzen(uuid,text,boolean,text,text)', 'EXECUTE')::text)
) AS k (pruefung, soll, ist);
