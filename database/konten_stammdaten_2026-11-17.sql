-- konten_stammdaten_2026-11-17.sql – DiesDasDüsseldorf
-- Nutzerkonten: Vorname, Nachname und Geburtsdatum als Pflichtangaben (Entscheidung des Auftraggebers vom
-- 17.11.2026, Plan Nutzerkonten Abschnitt 20, E16). Ersetzt E15 „Geburtsdatum freiwillig, nur mit Geburtstagsmail“.
--
-- WAS SICH ÄNDERT:
--   1. profiles bekommt vorname und nachname (Pflicht für ein fertiges Profil, Prüfbedingung onboarding_nur_mit_stammdaten).
--   2. Das Geburtsdatum hängt nicht mehr an der Geburtstagsmail: Es ist Pflicht (Altersprüfung ab 16) und bleibt
--      beim Widerruf der Geburtstagsmail stehen. Die Geburtstagsmail bleibt eine freiwillige Einwilligung (d)
--      (§ 7 Abs. 2 UWG) und setzt ein gespeichertes Datum voraus.
--   3. Neue Funktion stammdaten_setzen (nur service_role) mit derselben Altersprüfung wie bisher geburtstag_setzen.
--      geburtstag_setzen entfällt.
--   4. einwilligung_setzen: Zweig „geburtstagsmail“ setzt nur noch den Schalter.
--   5. Profile, die schon als fertig markiert sind, aber keine Stammdaten haben (nur Testkonten), gelten wieder als
--      unfertig. Sie sehen beim nächsten Besuch /konto/willkommen.
--
-- VORAUSSETZUNG: konten_2026-11-16.sql ist gelaufen. Wiederholbar. Ausführen als postgres im Supabase-SQL-Editor,
-- und zwar VOR dem Deploy der Website mit diesem Stand (die Website ruft stammdaten_setzen auf).
-- ERWARTET: am Ende eine Kontrolltabelle, jede Zeile „ok“. Steht dort „FEHLER“, bitte an Claude geben.

BEGIN;

-- ════════════════════════════════════════════════════════════════════════════
-- 1  Spalten und Prüfbedingungen
-- ════════════════════════════════════════════════════════════════════════════
ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS vorname  TEXT,   -- E16: Pflicht, nur über stammdaten_setzen
    ADD COLUMN IF NOT EXISTS nachname TEXT;   -- E16: Pflicht, nur über stammdaten_setzen

-- Namen: 1–60 Zeichen, ohne Leerraum am Rand, ohne Steuerzeichen und spitze Klammern (die Website prüft genauer)
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS name_plausibel;
ALTER TABLE public.profiles ADD CONSTRAINT name_plausibel CHECK (
    (vorname IS NULL OR (char_length(vorname) BETWEEN 1 AND 60 AND vorname = btrim(vorname) AND vorname !~ '[[:cntrl:]<>]'))
    AND
    (nachname IS NULL OR (char_length(nachname) BETWEEN 1 AND 60 AND nachname = btrim(nachname) AND nachname !~ '[[:cntrl:]<>]'))
);

-- Geburtsdatum unabhängig von der Geburtstagsmail; die Mail braucht aber ein Datum
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS geburtsdatum_nur_mit_einwilligung;
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS geburtstagsmail_nur_mit_datum;
ALTER TABLE public.profiles ADD CONSTRAINT geburtstagsmail_nur_mit_datum
    CHECK (NOT geburtstagsmail OR geburtsdatum IS NOT NULL);

-- Fertig ist ein Profil erst mit allen drei Pflichtangaben. authenticated darf onboarding_fertig_am selbst setzen,
-- daher wacht die Datenbank. Bestehende Testkonten ohne Stammdaten gelten vorher wieder als unfertig.
UPDATE public.profiles
   SET onboarding_fertig_am = NULL
 WHERE onboarding_fertig_am IS NOT NULL
   AND (vorname IS NULL OR nachname IS NULL OR geburtsdatum IS NULL);
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS onboarding_nur_mit_stammdaten;
ALTER TABLE public.profiles ADD CONSTRAINT onboarding_nur_mit_stammdaten
    CHECK (onboarding_fertig_am IS NULL OR (vorname IS NOT NULL AND nachname IS NOT NULL AND geburtsdatum IS NOT NULL));

-- Rechte: vorname/nachname bekommen bewusst KEIN Spaltenrecht für authenticated (geschrieben wird nur über
-- stammdaten_setzen mit Altersprüfung). Lesen des eigenen Profils gilt über die bestehende Policy.


-- ════════════════════════════════════════════════════════════════════════════
-- 2  einwilligung_setzen: Geburtstagsmail setzt nur noch den Schalter
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
            IF einwilligung_setzen.erteilt AND gesperrt IS NOT NULL THEN
                RAISE EXCEPTION 'unter16_gesperrt';
            END IF;
            IF einwilligung_setzen.erteilt AND datum IS NULL THEN
                RAISE EXCEPTION 'geburtsdatum_fehlt';
            END IF;
            UPDATE public.profiles p
               SET geburtstagsmail = einwilligung_setzen.erteilt
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


-- ════════════════════════════════════════════════════════════════════════════
-- 3  stammdaten_setzen (ersetzt geburtstag_setzen)
-- ════════════════════════════════════════════════════════════════════════════
-- Vorname, Nachname und Geburtsdatum setzen oder ändern. Nur service_role. Antwort 'ok' oder 'unter_16'.
-- Rechtsgrundlage ist der Nutzungsvertrag (Art. 6 Abs. 1 lit. b DSGVO), daher keine Einwilligungszeile.
-- Unter 16 (Stichtag in Europe/Berlin, der 16. Geburtstag zählt als 16, Zukunft = unter 16): Es wird NICHTS
-- gespeichert, das Mindestalter entzogen und das Konto gesperrt (Löschung beim nächsten Job-Lauf).
CREATE OR REPLACE FUNCTION public.stammdaten_setzen(
    nutzer   UUID,
    vorname  TEXT,
    nachname TEXT,
    datum    DATE
)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
#variable_conflict use_column
DECLARE
    gesperrt      TIMESTAMPTZ;
    stichtag      DATE;
    version_alter TEXT;
BEGIN
    IF stammdaten_setzen.nutzer IS NULL OR stammdaten_setzen.datum IS NULL
       OR coalesce(stammdaten_setzen.vorname, '') = '' OR coalesce(stammdaten_setzen.nachname, '') = '' THEN
        RAISE EXCEPTION 'parameter_fehlt';
    END IF;

    SELECT p.unter16_gesperrt_am INTO gesperrt
      FROM public.profiles p
     WHERE p.id = stammdaten_setzen.nutzer
       FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'konto_fehlt';
    END IF;
    IF gesperrt IS NOT NULL THEN
        RAISE EXCEPTION 'unter16_gesperrt';
    END IF;

    stichtag := ((timezone('Europe/Berlin', now()))::date - INTERVAL '16 years')::date;

    IF stammdaten_setzen.datum > stichtag THEN
        -- Nachweis der Sperre mit der aktuell gültigen Fassung des Mindestalter-Textes
        SELECT t.version INTO version_alter
          FROM public.einwilligungstexte t
         WHERE t.art = 'mindestalter'
         ORDER BY t.gueltig_ab DESC, t.version DESC
         LIMIT 1;
        IF version_alter IS NULL THEN
            RAISE EXCEPTION 'textversion_fehlt';
        END IF;

        UPDATE public.profiles p
           SET mindestalter_bestaetigt_am = NULL,
               geburtstagsmail            = FALSE,
               unter16_gesperrt_am        = now()
         WHERE p.id = stammdaten_setzen.nutzer;

        INSERT INTO public.einwilligungen (nutzer_id, art, erteilt, textversion, handlung)
        VALUES (stammdaten_setzen.nutzer, 'mindestalter', FALSE, version_alter, 'altersgrenze');

        RETURN 'unter_16';
    END IF;

    UPDATE public.profiles p
       SET vorname      = stammdaten_setzen.vorname,
           nachname     = stammdaten_setzen.nachname,
           geburtsdatum = stammdaten_setzen.datum
     WHERE p.id = stammdaten_setzen.nutzer;

    RETURN 'ok';
END;
$$;

REVOKE ALL ON FUNCTION public.stammdaten_setzen(UUID, TEXT, TEXT, DATE) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.stammdaten_setzen(UUID, TEXT, TEXT, DATE) TO service_role;

-- einwilligung_setzen behält seine Rechte (CREATE OR REPLACE mit gleicher Signatur); zur Sicherheit erneut:
REVOKE ALL ON FUNCTION public.einwilligung_setzen(UUID, TEXT, BOOLEAN, TEXT, TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.einwilligung_setzen(UUID, TEXT, BOOLEAN, TEXT, TEXT) TO service_role;

DROP FUNCTION IF EXISTS public.geburtstag_setzen(UUID, DATE, TEXT, TEXT);

COMMIT;


-- ════════════════════════════════════════════════════════════════════════════
-- Kontrolle
-- ════════════════════════════════════════════════════════════════════════════
SELECT pruefung, soll, ist, CASE WHEN soll = ist THEN 'ok' ELSE 'FEHLER' END AS ergebnis
FROM (VALUES
    ('Spalte profiles.vorname',  'true', EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'vorname')::text),
    ('Spalte profiles.nachname', 'true', EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'nachname')::text),
    ('Prüfbedingung name_plausibel',                 'true',  EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'name_plausibel')::text),
    ('Prüfbedingung geburtstagsmail_nur_mit_datum',  'true',  EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'geburtstagsmail_nur_mit_datum')::text),
    ('Prüfbedingung onboarding_nur_mit_stammdaten',  'true',  EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'onboarding_nur_mit_stammdaten')::text),
    ('Alte Prüfbedingung geburtsdatum_nur_mit_einwilligung entfernt', 'false', EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'geburtsdatum_nur_mit_einwilligung')::text),
    ('Spaltenrecht UPDATE authenticated profiles.vorname',  'false', has_column_privilege('authenticated', 'public.profiles', 'vorname', 'UPDATE')::text),
    ('Spaltenrecht UPDATE authenticated profiles.nachname', 'false', has_column_privilege('authenticated', 'public.profiles', 'nachname', 'UPDATE')::text),
    ('Spaltenrecht UPDATE authenticated profiles.geburtsdatum', 'false', has_column_privilege('authenticated', 'public.profiles', 'geburtsdatum', 'UPDATE')::text),
    ('anon: stammdaten_setzen',          'false', has_function_privilege('anon', 'public.stammdaten_setzen(uuid,text,text,date)', 'EXECUTE')::text),
    ('authenticated: stammdaten_setzen', 'false', has_function_privilege('authenticated', 'public.stammdaten_setzen(uuid,text,text,date)', 'EXECUTE')::text),
    ('service_role: stammdaten_setzen',  'true',  has_function_privilege('service_role', 'public.stammdaten_setzen(uuid,text,text,date)', 'EXECUTE')::text),
    ('authenticated: einwilligung_setzen', 'false', has_function_privilege('authenticated', 'public.einwilligung_setzen(uuid,text,boolean,text,text)', 'EXECUTE')::text),
    ('geburtstag_setzen entfernt', 'false', EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'geburtstag_setzen' AND pronamespace = 'public'::regnamespace)::text),
    ('Fertige Profile ohne Stammdaten', '0', (SELECT count(*) FROM public.profiles WHERE onboarding_fertig_am IS NOT NULL AND (vorname IS NULL OR nachname IS NULL OR geburtsdatum IS NULL))::text)
) AS k (pruefung, soll, ist);
