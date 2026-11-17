-- konten_2026-11-16.sql – DiesDasDüsseldorf
-- Nutzerkonten: Datenmodell, Rechte, Funktionen, Sensibel-Kennzeichnung
-- Plan docs/plan-nutzerkonten-2026-11-16.md, Abschnitte 4.1–4.5 und 4.8, Schritt 3 in Abschnitt 15.
--
-- WAS PASSIERT
--   1 profiles: neue Spalten, Prüfbedingungen, engere Rechte (Nutzer ändern nur noch anzeigename,
--     praeferenzen, onboarding_fertig_am, letzte_aktivitaet_am)
--   2 einwilligungstexte (unveränderliches Archiv) und einwilligungen (Nachweise)
--   3 Sensibel-Kennzeichnung: event_sensibel, event_sensibel_ausnahmen, sensibel_regeln (11 Startregeln aus
--     Plan 5.8), Funktion sensibel_grund, Trigger auf events und auf event_sensibel
--   4 merkliste mit Trigger (Grenze 500, Mindestalter, sensible Events, merkliste_begonnen_am)
--   5 Funktionen einwilligung_setzen, geburtstag_setzen, konto_protokoll_loeschen, merk_statistik
--   6 Kontrollabfrage (letzte Anweisung, eine Tabelle): erwartet überall „ok“
--
-- WICHTIG VOR DEM AUSFÜHREN
--   - NICHT während eines Pipeline-Laufs ausführen (scrape.yml startet 05:00 UTC, also 6 bzw. 7 Uhr
--     deutscher Zeit; am besten nachmittags). Der neue Trigger auf events läuft ab sofort bei jedem neuen
--     oder geänderten Event mit.
--   - Danach einen Testlauf der Pipeline (z. B. ein einzelnes Test-Event bzw. --dry-run) und die SQL-Tests
--     database/konten_tests_2026-11-16.sql laufen lassen.
--   - Stört der Trigger die Pipeline: database/konten_rueckbau_2026-11-16.sql Teil 1 (entfernt nur ihn).
--   - Die Tabelle einwilligungstexte bleibt LEER, bis die Wortlaute freigegeben sind (Schritt 6). Bis dahin
--     scheitern einwilligung_setzen und geburtstag_setzen am Fremdschlüssel. Das ist gewollt: Ohne
--     freigegebenen Text gibt es keinen Nachweis. Die Website ruft sie vor Schritt 8 ohnehin nicht auf.
--
-- Wiederholbar. Gespeichert in UTF-8 (Umlaute in den Mustern). Wird im Supabase-SQL-Editor als postgres
-- ausgeführt. Der SQL-Editor zeigt nur das Ergebnis der letzten Anweisung, das ist die Kontrollabfrage.
--
-- Abweichung vom Plan (in Plan 4.3 nachgetragen): Das Mindestalter beim Merken prüft der Trigger
-- merkliste_vor_insert (Fehler „mindestalter_fehlt“), nicht eine EXISTS-Bedingung in der INSERT-Policy.
-- Wirkung für Nutzer gleich, gilt aber für jeden Schreibweg (auch service_role, spätere App), und die
-- Policy bleibt eine reine Bindung an die Person, die die Rechte-Prüfung eindeutig erkennt.

BEGIN;

-- ════════════════════════════════════════════════════════════════════════════
-- 0  Vorabprüfung: Bestehende Profile dürfen noch keine Interessen haben (Plan 4.1)
-- ════════════════════════════════════════════════════════════════════════════
DO $$
BEGIN
    -- Nur beim ersten Lauf nötig: Danach gibt es personalisierung, und die Prüfbedingung wacht selbst.
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'public' AND table_name = 'profiles' AND column_name = 'personalisierung')
       AND EXISTS (SELECT 1 FROM public.profiles WHERE praeferenzen <> '{}'::jsonb) THEN
        RAISE EXCEPTION 'Abbruch: Es gibt Profile mit gespeicherten Interessen (praeferenzen). Bitte zuerst an Claude melden.';
    END IF;
END $$;


-- ════════════════════════════════════════════════════════════════════════════
-- 1  profiles erweitern (Plan 4.1)
-- ════════════════════════════════════════════════════════════════════════════
ALTER TABLE public.profiles
    ADD COLUMN IF NOT EXISTS onboarding_fertig_am        TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS mindestalter_bestaetigt_am  TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS personalisierung            BOOLEAN NOT NULL DEFAULT FALSE, -- E12a: nur mit Einwilligung (a)
    ADD COLUMN IF NOT EXISTS sensible_events_erlaubt     BOOLEAN NOT NULL DEFAULT FALSE, -- E13: nur mit ausdrücklicher Einwilligung (b)
    ADD COLUMN IF NOT EXISTS analyse_erlaubt             BOOLEAN NOT NULL DEFAULT FALSE, -- E4: true erst nach dem Hinweis auf der Abschlussseite
    ADD COLUMN IF NOT EXISTS nutzungsbedingungen_version TEXT,                           -- E14: akzeptierte Fassung
    ADD COLUMN IF NOT EXISTS geburtstagsmail             BOOLEAN NOT NULL DEFAULT FALSE, -- E15: Einwilligung (d)
    ADD COLUMN IF NOT EXISTS geburtsdatum                DATE,                           -- E15: nur mit (d)
    ADD COLUMN IF NOT EXISTS geburtstagsmail_zuletzt     DATE,                           -- letzter Versand, gegen Doppelversand
    ADD COLUMN IF NOT EXISTS unter16_gesperrt_am         TIMESTAMPTZ,                    -- Geburtsdatum unter 16 angegeben, Löschung beim nächsten Job-Lauf
    ADD COLUMN IF NOT EXISTS letzte_aktivitaet_am        TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS merkliste_begonnen_am       TIMESTAMPTZ;                    -- erster Eintrag je, setzt merkliste_vor_insert

ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS praeferenzen_form;
ALTER TABLE public.profiles ADD CONSTRAINT praeferenzen_form
    CHECK (jsonb_typeof(praeferenzen) = 'object' AND pg_column_size(praeferenzen) <= 8192);

-- Interessen gibt es nur mit Einwilligung (E12); auch ein direkter Schreibversuch ohne sie scheitert
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS praeferenzen_nur_mit_einwilligung;
ALTER TABLE public.profiles ADD CONSTRAINT praeferenzen_nur_mit_einwilligung
    CHECK (personalisierung OR praeferenzen = '{}'::jsonb);

-- Geburtsdatum nur mit Einwilligung (d), plausibel ab 1900 (die Altersgrenze prüft geburtstag_setzen)
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS geburtsdatum_nur_mit_einwilligung;
ALTER TABLE public.profiles ADD CONSTRAINT geburtsdatum_nur_mit_einwilligung
    CHECK ((geburtstagsmail AND geburtsdatum IS NOT NULL) OR (NOT geburtstagsmail AND geburtsdatum IS NULL));
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS geburtsdatum_plausibel;
ALTER TABLE public.profiles ADD CONSTRAINT geburtsdatum_plausibel
    CHECK (geburtsdatum IS NULL OR geburtsdatum >= DATE '1900-01-01');

-- Rechte (Plan 4.1, 4.0): anon gar nichts, authenticated lesen (Policy: eigenes Profil) und nur vier Spalten ändern.
-- Ein REVOKE auf Tabellenebene entfernt auch Spaltenrechte; deshalb erst entziehen, dann gezielt geben.
-- Das Dashboard liest profiles nur (dashboard/auth.py), Rollen setzt der SQL-Editor als postgres.
REVOKE ALL ON public.profiles FROM anon;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON public.profiles FROM authenticated;
GRANT SELECT ON public.profiles TO authenticated;
GRANT UPDATE (anzeigename, praeferenzen, onboarding_fertig_am, letzte_aktivitaet_am) ON public.profiles TO authenticated;
-- Der bestehende Trigger profil_vor_update (auth_rollen.sql) bleibt als zweite Sperre für rolle.


-- ════════════════════════════════════════════════════════════════════════════
-- 2  Einwilligungen (Plan 4.4)
-- ════════════════════════════════════════════════════════════════════════════

-- Archiv der gezeigten Wortlaute. Bleibt bis Schritt 6 leer.
CREATE TABLE IF NOT EXISTS public.einwilligungstexte (
    version    TEXT PRIMARY KEY CHECK (length(version) <= 40),   -- z. B. 'sensible-events-2026-11'
    art        TEXT NOT NULL CHECK (art IN ('mindestalter', 'nutzungsbedingungen', 'personalisierung',
                                            'sensible_events', 'analyse', 'geburtstagsmail')),
    zweck      TEXT NOT NULL,
    sprache    TEXT NOT NULL DEFAULT 'de',
    text       TEXT NOT NULL,                                     -- vollständiger angezeigter Wortlaut
    gueltig_ab TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Unveränderlich: kein UPDATE, DELETE oder TRUNCATE, auch nicht für service_role.
-- Bewusst abschalten kann das nur postgres (ALTER TABLE … DISABLE TRIGGER).
CREATE OR REPLACE FUNCTION public.einwilligungstexte_schuetzen()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
    RAISE EXCEPTION 'einwilligungstexte_unveraenderlich'
        USING HINT = 'Neue Fassungen kommen als neue Zeile (neue version).';
END;
$$;

DROP TRIGGER IF EXISTS einwilligungstexte_schuetzen ON public.einwilligungstexte;
CREATE TRIGGER einwilligungstexte_schuetzen
    BEFORE UPDATE OR DELETE ON public.einwilligungstexte
    FOR EACH ROW EXECUTE FUNCTION public.einwilligungstexte_schuetzen();
DROP TRIGGER IF EXISTS einwilligungstexte_schuetzen_leeren ON public.einwilligungstexte;
CREATE TRIGGER einwilligungstexte_schuetzen_leeren
    BEFORE TRUNCATE ON public.einwilligungstexte
    FOR EACH STATEMENT EXECUTE FUNCTION public.einwilligungstexte_schuetzen();

-- Nachweise. Geschrieben wird nur über einwilligung_setzen / geburtstag_setzen (service_role).
CREATE TABLE IF NOT EXISTS public.einwilligungen (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nutzer_id   UUID NOT NULL REFERENCES public.profiles (id) ON DELETE CASCADE,
    art         TEXT NOT NULL CHECK (art IN ('mindestalter', 'nutzungsbedingungen', 'personalisierung',
                                             'sensible_events', 'analyse', 'geburtstagsmail')),
    erteilt     BOOLEAN NOT NULL,                                 -- bei 'analyse': false = Widerspruch
    textversion TEXT NOT NULL REFERENCES public.einwilligungstexte (version),
    handlung    TEXT NOT NULL CHECK (handlung IN ('registrierung', 'abschlussseite', 'konto_schalter',
                                                  'interessen_aendern', 'abmeldelink', 'altersgrenze')),
    zeitpunkt   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS einwilligungen_nutzer_idx ON public.einwilligungen (nutzer_id, art, zeitpunkt DESC);


-- ════════════════════════════════════════════════════════════════════════════
-- 3  Sensibel-Kennzeichnung (Plan 4.8, 5.8) – nur Backend, für Nutzer nie sichtbar
-- ════════════════════════════════════════════════════════════════════════════

-- Eigene Tabelle statt Spalte in events: events ist für anon lesbar, diese Tabelle nicht.
CREATE TABLE IF NOT EXISTS public.event_sensibel (
    event_id   UUID PRIMARY KEY REFERENCES public.events (id) ON DELETE CASCADE,
    grund      TEXT NOT NULL CHECK (grund IN ('gesundheit', 'religion', 'sexualitaet', 'politik', 'gewerkschaft', 'herkunft')),
    quelle     TEXT NOT NULL CHECK (quelle IN ('regel', 'ki', 'hand')),
    gesetzt_am TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Von Hand bestätigte Fehltreffer: werden nie wieder automatisch gekennzeichnet
CREATE TABLE IF NOT EXISTS public.event_sensibel_ausnahmen (
    event_id   UUID PRIMARY KEY REFERENCES public.events (id) ON DELETE CASCADE,
    notiz      TEXT,
    gesetzt_am TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Regeln. Die CHECK-Bedingungen kompilieren jedes Muster beim Speichern: Ein kaputtes Muster wird schon
-- beim Eintragen abgelehnt und kann später keinen Event-Insert der Pipeline zum Scheitern bringen.
CREATE TABLE IF NOT EXISTS public.sensibel_regeln (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prioritaet      INT  NOT NULL,
    grund           TEXT NOT NULL CHECK (grund IN ('gesundheit', 'religion', 'sexualitaet', 'politik', 'gewerkschaft', 'herkunft')),
    muster          TEXT NOT NULL CHECK (('' ~* muster) IS NOT NULL),
    kontext_muster  TEXT          CHECK (kontext_muster  IS NULL OR ('' ~* kontext_muster)  IS NOT NULL),
    ausnahme_muster TEXT          CHECK (ausnahme_muster IS NULL OR ('' ~* ausnahme_muster) IS NOT NULL),
    aktiv           BOOLEAN NOT NULL DEFAULT TRUE,
    angelegt_am     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Startregeln aus Plan 5.8 (verbindlich). \y = Wortgrenze. Geprüft wird titel + ort + beschreibung.
-- Wiederholbar: Eine Regel wird nur eingetragen, wenn es dieselbe Priorität mit demselben Muster noch nicht gibt.
INSERT INTO public.sensibel_regeln (prioritaet, grund, muster, kontext_muster, ausnahme_muster)
SELECT r.prioritaet, r.grund, r.muster, r.kontext_muster, r.ausnahme_muster
FROM (VALUES
    (10, 'sexualitaet',
     '\y(csd|christopher street day|queer\w*|lgbt\w*|lsbt\w*|schwul\w*|lesbisch\w*|bisexuell\w*|transgender|transident\w*|nonbinär\w*|non-binary|drag ?(queen|king|show)s?)\y',
     NULL, NULL),
    (11, 'sexualitaet', '\ypride\y', NULL, 'pride and prejudice|stolz und vorurteil'),
    (20, 'religion',
     '\y(gottesdienst\w*|andacht\w*|freitagsgebet|gebetsabend|moschee\w*|synagoge\w*|kirchengemeinde\w*|pfarrgemeinde\w*|taufe|firmung|konfirmation|kommunion|ramadan|iftar|chanukka|bibelkreis|bibelabend|koranlesung)\y',
     NULL, NULL),
    (21, 'religion', '\ymesse\y', '\y(kirche\w*|gemeinde\w*|pfarr\w*|gottes\w*|heilige?n?|dom|kapelle)\y', NULL),
    (30, 'gesundheit',
     '\y(selbsthilfe\w*|suchtberatung|suchthilfe|suchtkrank\w*|anonyme alkoholiker|hiv|aids-hilfe|aidshilfe|krebsberatung|krebshilfe|krebserkrank\w*|depression\w*|demenz\w*|trauergruppe\w*|trauercaf[eé]|psychotherap\w*|blutspende\w*)\y',
     NULL, NULL),
    (40, 'politik',
     '\y(cdu|csu|spd|fdp|afd|bsw|linkspartei|bündnis 90|die grünen|freie wähler|piratenpartei|ödp|tierschutzpartei)\y',
     NULL, NULL),
    (41, 'politik', '\y(die linke|die partei)\y',
     '\y(partei\w*|wahl\w*|kandidat\w*|ortsverband|kreisverband|fraktion|bundestag|landtag|stadtrat)\y', NULL),
    (42, 'politik', '\yvolt\y', '\y(partei|europa|wahl\w*|kandidat\w*)\y', NULL),
    (43, 'politik', '\y(parteitag|ortsverband|kreisverband|wahlkampf\w*|kundgebung)\y', NULL, NULL),
    (44, 'politik', '\ydemonstration\y',
     '\y(gegen|für|protest\w*|kundgebung|bündnis|aufruf|solidarität\w*|rathaus|landtag)\y',
     '\y(live|koch|produkt|tanz)[- ]?demonstration\y'),
    (50, 'gewerkschaft', '\y(gewerkschaft\w*|ver\.di|ig metall|ig bce|dgb|betriebsrat|betriebsräte\w*)\y', NULL, NULL)
) AS r (prioritaet, grund, muster, kontext_muster, ausnahme_muster)
WHERE NOT EXISTS (SELECT 1 FROM public.sensibel_regeln s
                  WHERE s.prioritaet = r.prioritaet AND s.muster = r.muster);

-- Grund der ersten treffenden Regel (ORDER BY prioritaet, id) oder NULL. Nur intern (Trigger, Nachtrag).
CREATE OR REPLACE FUNCTION public.sensibel_grund(titel TEXT, beschreibung TEXT, ort TEXT)
RETURNS TEXT
LANGUAGE sql
STABLE
SET search_path = ''
AS $$
    SELECT r.grund
    FROM public.sensibel_regeln r
    CROSS JOIN (SELECT coalesce(sensibel_grund.titel, '') || ' ' || coalesce(sensibel_grund.ort, '') || ' '
                       || coalesce(sensibel_grund.beschreibung, '') AS t) x
    WHERE r.aktiv
      AND x.t ~* r.muster
      AND (r.kontext_muster  IS NULL OR x.t ~*  r.kontext_muster)
      AND (r.ausnahme_muster IS NULL OR x.t !~* r.ausnahme_muster)
    ORDER BY r.prioritaet, r.id
    LIMIT 1;
$$;

-- Trigger auf events: kennzeichnet in derselben Transaktion wie der Insert bzw. die Textänderung.
-- Schlägt er fehl, schlägt auch der Insert des Events fehl (kein sichtbares, ungekennzeichnetes Event).
-- Nimmt nie eine Kennzeichnung zurück. Meldet bei einem Treffer nichts nach außen.
CREATE OR REPLACE FUNCTION public.events_sensibel_pruefen()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    gefunden TEXT;
BEGIN
    IF TG_OP = 'UPDATE'
       AND NEW.titel IS NOT DISTINCT FROM OLD.titel
       AND NEW.beschreibung IS NOT DISTINCT FROM OLD.beschreibung
       AND NEW.ort IS NOT DISTINCT FROM OLD.ort THEN
        RETURN NULL;
    END IF;

    IF EXISTS (SELECT 1 FROM public.event_sensibel_ausnahmen a WHERE a.event_id = NEW.id) THEN
        RETURN NULL;
    END IF;

    gefunden := public.sensibel_grund(NEW.titel, NEW.beschreibung, NEW.ort);
    IF gefunden IS NOT NULL THEN
        INSERT INTO public.event_sensibel (event_id, grund, quelle)
        VALUES (NEW.id, gefunden, 'regel')
        ON CONFLICT (event_id) DO NOTHING;
    END IF;
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS events_sensibel_pruefen ON public.events;
CREATE TRIGGER events_sensibel_pruefen
    AFTER INSERT OR UPDATE OF titel, beschreibung, ort ON public.events
    FOR EACH ROW EXECUTE FUNCTION public.events_sensibel_pruefen();


-- ════════════════════════════════════════════════════════════════════════════
-- 4  merkliste (Plan 4.3)
-- ════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.merkliste (
    nutzer_id  UUID NOT NULL REFERENCES public.profiles (id) ON DELETE CASCADE,
    event_id   UUID NOT NULL REFERENCES public.events (id)   ON DELETE CASCADE,
    gemerkt_am TIMESTAMPTZ NOT NULL DEFAULT now(),
    quelle     TEXT NOT NULL DEFAULT 'konto' CHECK (quelle IN ('konto', 'geraet', 'app')),
    PRIMARY KEY (nutzer_id, event_id)
);
CREATE INDEX IF NOT EXISTS merkliste_event_idx ON public.merkliste (event_id);  -- Statistik, Löschen von Events

-- Vor jedem Einfügen, für jeden Schreibweg (Herz, Übernahme, App, service_role):
--   schon gemerkt → nichts tun (ON CONFLICT DO NOTHING darf bei vollem Konto nicht scheitern)
--   kein Mindestalter → mindestalter_fehlt
--   sensibles Event ohne Einwilligung (b) → nur_geraet
--   500 Einträge erreicht → merkliste_voll
--   sonst merkliste_begonnen_am setzen, falls leer (wird bei Abweisung mit zurückgerollt)
CREATE OR REPLACE FUNCTION public.merkliste_vor_insert()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    alter_bestaetigt TIMESTAMPTZ;
    sensible_ok      BOOLEAN;
    anzahl           INTEGER;
BEGIN
    IF EXISTS (SELECT 1 FROM public.merkliste m
               WHERE m.nutzer_id = NEW.nutzer_id AND m.event_id = NEW.event_id) THEN
        RETURN NEW;
    END IF;

    SELECT p.mindestalter_bestaetigt_am, p.sensible_events_erlaubt
      INTO alter_bestaetigt, sensible_ok
      FROM public.profiles p
     WHERE p.id = NEW.nutzer_id;

    IF alter_bestaetigt IS NULL THEN
        RAISE EXCEPTION 'mindestalter_fehlt';
    END IF;

    IF NOT coalesce(sensible_ok, FALSE)
       AND EXISTS (SELECT 1 FROM public.event_sensibel s WHERE s.event_id = NEW.event_id) THEN
        RAISE EXCEPTION 'nur_geraet';
    END IF;

    SELECT count(*) INTO anzahl FROM public.merkliste m WHERE m.nutzer_id = NEW.nutzer_id;
    IF anzahl >= 500 THEN
        RAISE EXCEPTION 'merkliste_voll';
    END IF;

    UPDATE public.profiles
       SET merkliste_begonnen_am = now()
     WHERE id = NEW.nutzer_id
       AND merkliste_begonnen_am IS NULL;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS merkliste_vor_insert ON public.merkliste;
CREATE TRIGGER merkliste_vor_insert
    BEFORE INSERT ON public.merkliste
    FOR EACH ROW EXECUTE FUNCTION public.merkliste_vor_insert();

-- Spätere Kennzeichnung (Textänderung, neue Regel, von Hand): Merkungen dieses Events bei allen Konten
-- ohne Einwilligung (b) löschen. Bewusst ohne Rückgabe an die Geräte (Plan 4.8).
CREATE OR REPLACE FUNCTION public.event_sensibel_merkliste_raeumen()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    DELETE FROM public.merkliste m
     USING public.profiles p
     WHERE m.event_id = NEW.event_id
       AND p.id = m.nutzer_id
       AND NOT p.sensible_events_erlaubt;
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS event_sensibel_merkliste_raeumen ON public.event_sensibel;
CREATE TRIGGER event_sensibel_merkliste_raeumen
    AFTER INSERT ON public.event_sensibel
    FOR EACH ROW EXECUTE FUNCTION public.event_sensibel_merkliste_raeumen();


-- ════════════════════════════════════════════════════════════════════════════
-- 5  Funktionen (Plan 4.5, 4.6)
-- ════════════════════════════════════════════════════════════════════════════

-- Einwilligung setzen oder widerrufen, Profilspalte und Nachweis in einer Transaktion. Nur service_role.
-- Rückgabe: IDs der Events, die beim Widerruf von (b) aus dem Konto entfernt wurden (sonst leer).
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
    zurueck  UUID[] := '{}';
BEGIN
    IF einwilligung_setzen.nutzer IS NULL OR einwilligung_setzen.erteilt IS NULL THEN
        RAISE EXCEPTION 'parameter_fehlt';
    END IF;

    SELECT p.unter16_gesperrt_am INTO gesperrt
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
            IF einwilligung_setzen.erteilt THEN
                RAISE EXCEPTION 'nur_ueber_geburtstag_setzen';
            END IF;
            -- Eine Anweisung: Die Prüfbedingung geburtsdatum_nur_mit_einwilligung gilt sofort.
            UPDATE public.profiles p
               SET geburtstagsmail = FALSE,
                   geburtsdatum    = NULL
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

-- Geburtsdatum setzen oder ändern (E15). Nur service_role. Antwort 'ok' oder 'unter_16'.
-- Unter 16 (Stichtag in Europe/Berlin, der 16. Geburtstag zählt als 16, Zukunft = unter 16):
-- Datum wird NICHT gespeichert, Mindestalter entzogen, Konto gesperrt (Löschung beim nächsten Job-Lauf).
CREATE OR REPLACE FUNCTION public.geburtstag_setzen(
    nutzer      UUID,
    datum       DATE,
    textversion TEXT,
    handlung    TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
#variable_conflict use_column
DECLARE
    gesperrt        TIMESTAMPTZ;
    stichtag        DATE;
    version_alter   TEXT;
BEGIN
    IF geburtstag_setzen.nutzer IS NULL OR geburtstag_setzen.datum IS NULL THEN
        RAISE EXCEPTION 'parameter_fehlt';
    END IF;

    SELECT p.unter16_gesperrt_am INTO gesperrt
      FROM public.profiles p
     WHERE p.id = geburtstag_setzen.nutzer
       FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'konto_fehlt';
    END IF;
    IF gesperrt IS NOT NULL THEN
        RAISE EXCEPTION 'unter16_gesperrt';
    END IF;

    stichtag := ((timezone('Europe/Berlin', now()))::date - INTERVAL '16 years')::date;

    IF geburtstag_setzen.datum > stichtag THEN
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
               unter16_gesperrt_am        = now()
         WHERE p.id = geburtstag_setzen.nutzer;

        INSERT INTO public.einwilligungen (nutzer_id, art, erteilt, textversion, handlung)
        VALUES (geburtstag_setzen.nutzer, 'mindestalter', FALSE, version_alter, 'altersgrenze');

        RETURN 'unter_16';
    END IF;

    -- Eine Anweisung: Die Prüfbedingung geburtsdatum_nur_mit_einwilligung gilt sofort.
    UPDATE public.profiles p
       SET geburtsdatum    = geburtstag_setzen.datum,
           geburtstagsmail = TRUE
     WHERE p.id = geburtstag_setzen.nutzer;

    INSERT INTO public.einwilligungen (nutzer_id, art, erteilt, textversion, handlung)
    VALUES (geburtstag_setzen.nutzer, 'geburtstagsmail', TRUE,
            geburtstag_setzen.textversion, geburtstag_setzen.handlung);

    RETURN 'ok';
END;
$$;

-- Einträge eines Kontos im Anmeldeprotokoll löschen (Plan 4.6). Nur service_role.
-- Der Aufrufer übergibt nur die ID; die Mailadresse bestimmt die Funktion selbst (auth.users, sonst die
-- Audit-Zeilen derselben ID). Hat sich dieselbe Adresse neu registriert, bleiben deren Zeilen stehen.
-- Laut Schritt 1 ist die Tabelle heute leer; die Funktion greift, falls Supabase künftig Zeilen schreibt.
-- Payload-Felder nach dem Aufbau von Supabase Auth; Bestätigung an echten Zeilen steht aus (Plan 4.6).
CREATE OR REPLACE FUNCTION public.konto_protokoll_loeschen(nutzer UUID)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
#variable_conflict use_column
DECLARE
    adresse       TEXT;
    neueres_konto TIMESTAMPTZ;
    per_id        INTEGER := 0;
    per_adresse   INTEGER := 0;
BEGIN
    IF konto_protokoll_loeschen.nutzer IS NULL THEN
        RAISE EXCEPTION 'parameter_fehlt';
    END IF;
    IF EXISTS (SELECT 1 FROM public.profiles p
               WHERE p.id = konto_protokoll_loeschen.nutzer AND p.rolle = 'admin') THEN
        RAISE EXCEPTION 'admin_konto';
    END IF;

    SELECT u.email INTO adresse FROM auth.users u WHERE u.id = konto_protokoll_loeschen.nutzer;

    IF adresse IS NULL THEN
        SELECT coalesce(nullif(a.payload -> 'traits' ->> 'user_email', ''), a.payload ->> 'actor_username')
          INTO adresse
          FROM auth.audit_log_entries a
         WHERE (a.payload ->> 'actor_id' = konto_protokoll_loeschen.nutzer::text
                OR a.payload -> 'traits' ->> 'user_id' = konto_protokoll_loeschen.nutzer::text)
           AND coalesce(nullif(a.payload -> 'traits' ->> 'user_email', ''), a.payload ->> 'actor_username') LIKE '%@%'
         ORDER BY a.created_at DESC
         LIMIT 1;
    END IF;

    DELETE FROM auth.audit_log_entries a
     WHERE a.payload ->> 'actor_id' = konto_protokoll_loeschen.nutzer::text
        OR a.payload -> 'traits' ->> 'user_id' = konto_protokoll_loeschen.nutzer::text;
    GET DIAGNOSTICS per_id = ROW_COUNT;

    IF adresse IS NOT NULL THEN
        -- Ein anderes, lebendes Konto mit derselben Adresse (spätere Neuregistrierung) behält seine Zeilen
        SELECT min(u.created_at) INTO neueres_konto
          FROM auth.users u
         WHERE lower(u.email) = lower(adresse)
           AND u.id <> konto_protokoll_loeschen.nutzer;

        DELETE FROM auth.audit_log_entries a
         WHERE (lower(a.payload ->> 'actor_username') = lower(adresse)
                OR lower(a.payload -> 'traits' ->> 'user_email') = lower(adresse))
           AND (neueres_konto IS NULL OR a.created_at < neueres_konto);
        GET DIAGNOSTICS per_adresse = ROW_COUNT;
    END IF;

    RETURN per_id + per_adresse;
END;
$$;

-- Summen für die Analyse (Phase 3): nur Admins, nur Konten ohne Widerspruch, nie sensible Events,
-- nie eine Nutzer-ID. von/bis beziehen sich auf gemerkt_am in deutscher Zeit, beide einschließlich, NULL = offen.
CREATE OR REPLACE FUNCTION public.merk_statistik(von DATE, bis DATE)
RETURNS TABLE (event_id UUID, anzahl BIGINT, zuerst_gemerkt TIMESTAMPTZ, zuletzt_gemerkt TIMESTAMPTZ)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
#variable_conflict use_column
BEGIN
    IF NOT coalesce(public.ist_admin(), FALSE) THEN
        RAISE EXCEPTION 'nur_admins';
    END IF;

    RETURN QUERY
        SELECT m.event_id, count(*)::BIGINT, min(m.gemerkt_am), max(m.gemerkt_am)
          FROM public.merkliste m
          JOIN public.profiles p ON p.id = m.nutzer_id
         WHERE p.analyse_erlaubt
           AND NOT EXISTS (SELECT 1 FROM public.event_sensibel s WHERE s.event_id = m.event_id)
           AND (merk_statistik.von IS NULL
                OR m.gemerkt_am >= (merk_statistik.von::timestamp AT TIME ZONE 'Europe/Berlin'))
           AND (merk_statistik.bis IS NULL
                OR m.gemerkt_am <  ((merk_statistik.bis + 1)::timestamp AT TIME ZONE 'Europe/Berlin'))
         GROUP BY m.event_id;
END;
$$;


-- ════════════════════════════════════════════════════════════════════════════
-- 6  Row Level Security, Policies und Rechte (Plan 4.5)
-- ════════════════════════════════════════════════════════════════════════════

-- merkliste: nur die eigenen Zeilen, kein UPDATE
ALTER TABLE public.merkliste ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.merkliste FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, DELETE ON public.merkliste TO authenticated;

DROP POLICY IF EXISTS "Eigene Merkliste lesen" ON public.merkliste;
CREATE POLICY "Eigene Merkliste lesen" ON public.merkliste
    FOR SELECT TO authenticated
    USING (nutzer_id = (SELECT auth.uid()));

DROP POLICY IF EXISTS "Eigene Merkliste ergänzen" ON public.merkliste;
CREATE POLICY "Eigene Merkliste ergänzen" ON public.merkliste
    FOR INSERT TO authenticated
    WITH CHECK (nutzer_id = (SELECT auth.uid()));   -- Mindestalter prüft merkliste_vor_insert

DROP POLICY IF EXISTS "Eigene Merkliste löschen" ON public.merkliste;
CREATE POLICY "Eigene Merkliste löschen" ON public.merkliste
    FOR DELETE TO authenticated
    USING (nutzer_id = (SELECT auth.uid()));

-- einwilligungen: nur eigene lesen, schreiben nur über die Funktionen
ALTER TABLE public.einwilligungen ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.einwilligungen FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.einwilligungen TO authenticated;

DROP POLICY IF EXISTS "Eigene Einwilligungen lesen" ON public.einwilligungen;
CREATE POLICY "Eigene Einwilligungen lesen" ON public.einwilligungen
    FOR SELECT TO authenticated
    USING (nutzer_id = (SELECT auth.uid()));

-- einwilligungstexte: öffentlich lesbar (Whitelist der Rechte-Prüfung), schreiben niemand über die API
ALTER TABLE public.einwilligungstexte ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.einwilligungstexte FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.einwilligungstexte TO anon, authenticated;

DROP POLICY IF EXISTS "Einwilligungstexte lesen" ON public.einwilligungstexte;
CREATE POLICY "Einwilligungstexte lesen" ON public.einwilligungstexte
    FOR SELECT TO anon, authenticated
    USING (true);

-- Sensibel-Tabellen: keine Rechte, keine Policy (nur service_role und SECURITY-DEFINER-Funktionen)
ALTER TABLE public.event_sensibel           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_sensibel_ausnahmen ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sensibel_regeln          ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.event_sensibel           FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.event_sensibel_ausnahmen FROM PUBLIC, anon, authenticated;
REVOKE ALL ON public.sensibel_regeln          FROM PUBLIC, anon, authenticated;

-- Funktionen: zuerst alles entziehen, dann nur das Nötige geben (Plan 4.5)
REVOKE ALL ON FUNCTION public.einwilligungstexte_schuetzen()            FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.sensibel_grund(TEXT, TEXT, TEXT)          FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.events_sensibel_pruefen()                 FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.event_sensibel_merkliste_raeumen()        FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.merkliste_vor_insert()                    FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.einwilligung_setzen(UUID, TEXT, BOOLEAN, TEXT, TEXT) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.geburtstag_setzen(UUID, DATE, TEXT, TEXT) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.konto_protokoll_loeschen(UUID)            FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.merk_statistik(DATE, DATE)                FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION public.merkliste_vor_insert()                    TO authenticated;  -- unschädlich, Trigger-Funktion
GRANT EXECUTE ON FUNCTION public.merk_statistik(DATE, DATE)                TO authenticated;  -- Admin-Prüfung innen
GRANT EXECUTE ON FUNCTION public.einwilligung_setzen(UUID, TEXT, BOOLEAN, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.geburtstag_setzen(UUID, DATE, TEXT, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.konto_protokoll_loeschen(UUID)            TO service_role;

COMMIT;


-- ════════════════════════════════════════════════════════════════════════════
-- 7  Kontrollabfrage: erwartet in jeder Zeile „ok“. Zeilen mit „FEHLER“ bitte an Claude geben.
--    Die Muster-Tests rufen nur sensibel_grund auf und schreiben nichts.
-- ════════════════════════════════════════════════════════════════════════════
WITH
tabellen (nr, objekt) AS (
    VALUES (1, 'public.merkliste'), (1, 'public.einwilligungen'), (1, 'public.einwilligungstexte'),
           (1, 'public.event_sensibel'), (1, 'public.event_sensibel_ausnahmen'), (1, 'public.sensibel_regeln')
),
k_tabellen AS (
    SELECT t.nr, 'Tabelle mit RLS'::text AS pruefung, t.objekt,
           'vorhanden, RLS an'::text AS erwartet,
           CASE WHEN c.oid IS NULL THEN 'fehlt'
                WHEN c.relrowsecurity THEN 'vorhanden, RLS an' ELSE 'vorhanden, RLS AUS' END AS ist
    FROM tabellen t
    LEFT JOIN pg_class c ON c.oid = to_regclass(t.objekt)
),
rechte (nr, pruefung, objekt, erwartet, ist) AS (
    VALUES
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.rolle',                 'false', has_column_privilege('authenticated', 'public.profiles', 'rolle', 'UPDATE')::text),
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.erstellt_am',           'false', has_column_privilege('authenticated', 'public.profiles', 'erstellt_am', 'UPDATE')::text),
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.personalisierung',      'false', has_column_privilege('authenticated', 'public.profiles', 'personalisierung', 'UPDATE')::text),
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.sensible_events_erlaubt','false', has_column_privilege('authenticated', 'public.profiles', 'sensible_events_erlaubt', 'UPDATE')::text),
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.analyse_erlaubt',       'false', has_column_privilege('authenticated', 'public.profiles', 'analyse_erlaubt', 'UPDATE')::text),
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.mindestalter_bestaetigt_am', 'false', has_column_privilege('authenticated', 'public.profiles', 'mindestalter_bestaetigt_am', 'UPDATE')::text),
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.geburtsdatum',          'false', has_column_privilege('authenticated', 'public.profiles', 'geburtsdatum', 'UPDATE')::text),
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.unter16_gesperrt_am',   'false', has_column_privilege('authenticated', 'public.profiles', 'unter16_gesperrt_am', 'UPDATE')::text),
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.merkliste_begonnen_am', 'false', has_column_privilege('authenticated', 'public.profiles', 'merkliste_begonnen_am', 'UPDATE')::text),
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.praeferenzen',          'true',  has_column_privilege('authenticated', 'public.profiles', 'praeferenzen', 'UPDATE')::text),
    (2, 'Spaltenrecht UPDATE authenticated', 'profiles.letzte_aktivitaet_am',  'true',  has_column_privilege('authenticated', 'public.profiles', 'letzte_aktivitaet_am', 'UPDATE')::text),
    (3, 'Tabellenrecht', 'anon liest profiles',                    'false', has_table_privilege('anon', 'public.profiles', 'SELECT')::text),
    (3, 'Tabellenrecht', 'anon liest merkliste',                   'false', has_table_privilege('anon', 'public.merkliste', 'SELECT')::text),
    (3, 'Tabellenrecht', 'authenticated ändert merkliste',         'false', has_table_privilege('authenticated', 'public.merkliste', 'UPDATE')::text),
    (3, 'Tabellenrecht', 'authenticated fügt in merkliste ein',    'true',  has_table_privilege('authenticated', 'public.merkliste', 'INSERT')::text),
    (3, 'Tabellenrecht', 'authenticated fügt in einwilligungen ein','false', has_table_privilege('authenticated', 'public.einwilligungen', 'INSERT')::text),
    (3, 'Tabellenrecht', 'anon liest einwilligungen',              'false', has_table_privilege('anon', 'public.einwilligungen', 'SELECT')::text),
    (3, 'Tabellenrecht', 'anon liest einwilligungstexte',          'true',  has_table_privilege('anon', 'public.einwilligungstexte', 'SELECT')::text),
    (3, 'Tabellenrecht', 'authenticated ändert einwilligungstexte','false', has_table_privilege('authenticated', 'public.einwilligungstexte', 'UPDATE')::text),
    (3, 'Tabellenrecht', 'anon liest event_sensibel',              'false', has_table_privilege('anon', 'public.event_sensibel', 'SELECT')::text),
    (3, 'Tabellenrecht', 'authenticated liest event_sensibel',     'false', has_table_privilege('authenticated', 'public.event_sensibel', 'SELECT')::text),
    (3, 'Tabellenrecht', 'authenticated liest sensibel_regeln',    'false', has_table_privilege('authenticated', 'public.sensibel_regeln', 'SELECT')::text),
    (3, 'Tabellenrecht', 'authenticated liest event_sensibel_ausnahmen', 'false', has_table_privilege('authenticated', 'public.event_sensibel_ausnahmen', 'SELECT')::text),
    (4, 'Funktionsrecht', 'anon: merk_statistik',                  'false', has_function_privilege('anon', 'public.merk_statistik(date,date)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'authenticated: merk_statistik',         'true',  has_function_privilege('authenticated', 'public.merk_statistik(date,date)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'anon: merkliste_vor_insert',            'false', has_function_privilege('anon', 'public.merkliste_vor_insert()', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'authenticated: einwilligung_setzen',    'false', has_function_privilege('authenticated', 'public.einwilligung_setzen(uuid,text,boolean,text,text)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'anon: einwilligung_setzen',             'false', has_function_privilege('anon', 'public.einwilligung_setzen(uuid,text,boolean,text,text)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'service_role: einwilligung_setzen',     'true',  has_function_privilege('service_role', 'public.einwilligung_setzen(uuid,text,boolean,text,text)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'authenticated: geburtstag_setzen',      'false', has_function_privilege('authenticated', 'public.geburtstag_setzen(uuid,date,text,text)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'service_role: geburtstag_setzen',       'true',  has_function_privilege('service_role', 'public.geburtstag_setzen(uuid,date,text,text)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'authenticated: konto_protokoll_loeschen','false', has_function_privilege('authenticated', 'public.konto_protokoll_loeschen(uuid)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'service_role: konto_protokoll_loeschen','true',  has_function_privilege('service_role', 'public.konto_protokoll_loeschen(uuid)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'anon: sensibel_grund',                  'false', has_function_privilege('anon', 'public.sensibel_grund(text,text,text)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'authenticated: sensibel_grund',         'false', has_function_privilege('authenticated', 'public.sensibel_grund(text,text,text)', 'EXECUTE')::text),
    (4, 'Funktionsrecht', 'authenticated: events_sensibel_pruefen','false', has_function_privilege('authenticated', 'public.events_sensibel_pruefen()', 'EXECUTE')::text)
),
trigger_liste (nr, objekt) AS (
    VALUES (5, 'events_sensibel_pruefen'), (5, 'merkliste_vor_insert'), (5, 'event_sensibel_merkliste_raeumen'),
           (5, 'einwilligungstexte_schuetzen'), (5, 'einwilligungstexte_schuetzen_leeren'), (5, 'profil_vor_update')
),
k_trigger AS (
    SELECT l.nr, 'Trigger aktiv'::text AS pruefung, l.objekt, 'vorhanden, an'::text AS erwartet,
           coalesce((SELECT CASE WHEN tg.tgenabled = 'D' THEN 'vorhanden, AUS' ELSE 'vorhanden, an' END
                     FROM pg_trigger tg WHERE tg.tgname = l.objekt AND NOT tg.tgisinternal LIMIT 1), 'fehlt') AS ist
    FROM trigger_liste l
),
k_regeln AS (
    SELECT 6 AS nr, 'Startregeln'::text AS pruefung, 'sensibel_regeln (aktiv)'::text AS objekt,
           '11'::text AS erwartet, count(*)::text AS ist
    FROM public.sensibel_regeln WHERE aktiv
),
-- Muster-Tests aus Plan 16.2 (Treffer und Fehltreffer, Umlaute, Priorität). Erwartet: Grund bzw. „–“.
muster_tests (beispiel, erwartet) AS (
    VALUES
    ('CSD Düsseldorf',                             'sexualitaet'),
    ('Queer Filmnacht im Kino',                    'sexualitaet'),
    ('Treffen für nonbinäre Menschen',             'sexualitaet'),
    ('Pride Parade am Rhein',                      'sexualitaet'),
    ('Pride and Prejudice – Theater',              '–'),
    ('Ökumenischer Gottesdienst im Park',          'religion'),
    ('Heilige Messe St. Lambertus',                'religion'),
    ('Messe Düsseldorf: boot 2027',                '–'),
    ('Selbsthilfegruppe Angst',                    'gesundheit'),
    ('Trauercafé im Stadtteil',                    'gesundheit'),
    ('Infostand der SPD',                          'politik'),
    ('ÖDP-Infostand',                              'politik'),
    ('Bündnis 90 lädt ein',                        'politik'),
    ('Die Linke',                                  '–'),
    ('Die Linke Ortsverband Bilk',                 'politik'),
    ('Volt Europa Wahlkampf',                      'politik'),
    ('Demonstration vor dem Rathaus',              'politik'),
    ('Demonstration gegen Rechts',                 'politik'),
    ('Kurz davor Demonstration für Klimaschutz',   'politik'),
    ('Kochdemonstration',                          '–'),
    ('Live-Demonstration der neuen Technik',       '–'),
    ('Grüne Woche',                                '–'),
    ('ver.di-Versammlung',                         'gewerkschaft'),
    ('La Traviata (Verdi)',                        '–'),
    ('Verdi Requiem',                              '–'),
    ('Er sucht das Glück',                         '–'),
    ('Demo-Tape Release Party',                    '–'),
    ('CSD-Gottesdienst',                           'sexualitaet')   -- zwei Regeln: kleinere Priorität gewinnt
),
k_muster AS (
    SELECT 7 AS nr, 'Muster-Test sensibel_grund'::text AS pruefung, m.beispiel AS objekt, m.erwartet,
           coalesce(public.sensibel_grund(m.beispiel, NULL, NULL), '–') AS ist
    FROM muster_tests m
),
alles AS (
    SELECT nr, pruefung, objekt, erwartet, ist FROM k_tabellen
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM rechte
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM k_trigger
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM k_regeln
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM k_muster
)
SELECT nr, pruefung, objekt, erwartet, ist,
       CASE WHEN erwartet = ist THEN 'ok' ELSE 'FEHLER' END AS ergebnis
FROM alles
ORDER BY CASE WHEN erwartet = ist THEN 1 ELSE 0 END, nr, objekt;
