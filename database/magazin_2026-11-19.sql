-- magazin_2026-11-19.sql – DiesDasDüsseldorf
-- Magazin (redaktionelle Beiträge): Datenmodell, Rechte, Workflow-Trigger.
-- Plan docs/plan-redaktion-2026-11-19.md (siebte Fassung, freigegeben 19.11.2026), Abschnitt 3.1, Schritt 1 in Abschnitt 8.
--
-- WAS PASSIERT
--   1 magazin_autoren       – redaktionelle Pseudonyme (Plan 2.3); bleibt leer bis Schritt 4 (E15)
--   2 magazin_beitraege     – Beiträge mit Workflow entwurf → in_pruefung → veroeffentlicht (+ zurueckgezogen)
--   3 magazin_ki_kosten     – Kostenprotokoll und Reservierungen der Pipeline (Plan 4.4), nur service_role
--   4 Trigger magazin_status_pruefen – nur der Auftraggeber (Table Editor / SQL-Editor) kann veröffentlichen;
--     Pflichtfelder, grüne Prüfung, Slug-Historie, Kennzeichen „KI-Symbolbild“
--   5 Rechte: RLS an, anon/authenticated lesen nur öffentliche Spalten veröffentlichter Beiträge;
--     View magazin_oeffentlich mit security_invoker
--   6 Indizes
--   7 Kontrollabfrage (letzte Anweisung, eine Tabelle): erwartet überall „ok“
--
-- DANACH
--   - database/magazin_tests_2026-11-19.sql ausführen (Testlauf, wird komplett zurückgerollt).
--   - database/konten_rechte_pruefung_2026-11-16.sql erneut ausführen: bei den magazin_-Objekten keine „LÜCKE“.
--
-- Unkritisch für die Pipeline und die Website: Es entstehen nur neue Objekte, bestehende Tabellen werden
-- nicht verändert. Wiederholbar. Gespeichert in UTF-8. Ausführen im Supabase-SQL-Editor als postgres.
--
-- Auslegung über den Plantext hinaus (im Sinne von Plan T5 „kein KI-Artikel ohne Freigabe“): Ein bereits
-- veröffentlichter Beitrag darf über service_role/anon/authenticated nur noch in den Spalten pruefung und
-- gemeldet_am geändert werden (täglicher Prüflauf, IndexNow-Meldung). Text, Bild, Status usw. ändert nur
-- der Auftraggeber. Sonst könnte die Pipeline einen freigegebenen Text nachträglich überschreiben.

BEGIN;

-- ════════════════════════════════════════════════════════════════════════════
-- 1  Autoren (redaktionelle Pseudonyme, Plan 2.3)
-- ════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.magazin_autoren (
    slug             TEXT PRIMARY KEY CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
    name             TEXT NOT NULL CHECK (length(name) BETWEEN 2 AND 60),
    kurzbeschreibung TEXT NOT NULL CHECK (length(kurzbeschreibung) <= 300),   -- ohne Qualifikationen/Lebenslauf
    schwerpunkt      TEXT NOT NULL,
    rubriken         TEXT[] NOT NULL DEFAULT '{}'
                     CHECK (rubriken <@ ARRAY['wochenvorschau', 'monats-tipps', 'saison', 'stadtleben']),
    bild             TEXT CHECK (bild ~ '^/magazin-autoren/[a-z0-9-]+\.webp$'),
    bild_ki          BOOLEAN NOT NULL DEFAULT TRUE,                           -- „KI-generiertes Profilbild“
    aktiv            BOOLEAN NOT NULL DEFAULT TRUE
);


-- ════════════════════════════════════════════════════════════════════════════
-- 2  Beiträge (Plan 3.1)
-- ════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.magazin_beitraege (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug               TEXT NOT NULL UNIQUE,
    alte_slugs         TEXT[] NOT NULL DEFAULT '{}',
    rubrik             TEXT NOT NULL,
    autor_slug         TEXT NOT NULL REFERENCES public.magazin_autoren(slug),
    titel              TEXT NOT NULL,
    seo_titel          TEXT,
    teaser             TEXT,
    inhalt_md          TEXT NOT NULL DEFAULT '',
    kurzfassung        TEXT[],
    faq                JSONB,
    hero_bild          TEXT,
    hero_alt           TEXT,
    hero_nachweis      TEXT,
    hero_ki            BOOLEAN NOT NULL DEFAULT FALSE,
    status             TEXT NOT NULL DEFAULT 'entwurf',
    veroeffentlicht_am TIMESTAMPTZ,
    aktualisiert_am    TIMESTAMPTZ,
    korrektur_hinweis  TEXT,
    gueltig_von        DATE,
    gueltig_bis        DATE,
    naechste_pruefung  DATE,
    event_ids          UUID[] NOT NULL DEFAULT '{}',
    ort_slugs          TEXT[] NOT NULL DEFAULT '{}',
    quellen            JSONB NOT NULL DEFAULT '[]'::jsonb,
    ki_entwurf         JSONB NOT NULL DEFAULT '{}'::jsonb,
    pruefung           JSONB NOT NULL DEFAULT '{}'::jsonb,
    vorschau_hash      TEXT,
    freigegeben_von    TEXT,
    freigegeben_am     TIMESTAMPTZ,
    gemeldet_am        TIMESTAMPTZ,
    erstellt_am        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Prüfbedingungen einzeln (wiederholbar: erst entfernen, dann anlegen)
ALTER TABLE public.magazin_beitraege DROP CONSTRAINT IF EXISTS magazin_slug_form;
ALTER TABLE public.magazin_beitraege ADD CONSTRAINT magazin_slug_form
    CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'
           AND slug NOT IN ('rubrik', 'autor', 'vorschau', 'seite', 'redaktion'));

ALTER TABLE public.magazin_beitraege DROP CONSTRAINT IF EXISTS magazin_alte_slugs_form;
ALTER TABLE public.magazin_beitraege ADD CONSTRAINT magazin_alte_slugs_form
    CHECK (array_position(alte_slugs, NULL) IS NULL
           AND array_to_string(alte_slugs, ',') ~ '^([a-z0-9]+(-[a-z0-9]+)*(,[a-z0-9]+(-[a-z0-9]+)*)*)?$'
           -- genau ein Komma weniger als Einträge: kein Eintrag enthält selbst ein Komma
           AND length(array_to_string(alte_slugs, ',')) - length(replace(array_to_string(alte_slugs, ','), ',', ''))
               = greatest(cardinality(alte_slugs) - 1, 0)
           AND NOT (slug = ANY (alte_slugs)));

-- Rubrik = URL-Segment (Plan 3.1, Cursor-Prüfung 2 Befund 9)
-- ACHTUNG: Seit Schritt 4 gilt die Rubrikliste aus database/magazin_rubriken_autoren_2026-11-19.sql (sieben Rubriken).
-- Wer diese Datei erneut ausführt, setzt den CHECK hier auf vier Rubriken zurück – danach die Schritt-4-Datei ebenfalls
-- erneut ausführen (Cursor-Gesamtprüfung 19.11.2026).
ALTER TABLE public.magazin_beitraege DROP CONSTRAINT IF EXISTS magazin_rubrik_werte;
ALTER TABLE public.magazin_beitraege ADD CONSTRAINT magazin_rubrik_werte
    CHECK (rubrik IN ('wochenvorschau', 'monats-tipps', 'saison', 'stadtleben'));

ALTER TABLE public.magazin_beitraege DROP CONSTRAINT IF EXISTS magazin_status_werte;
ALTER TABLE public.magazin_beitraege ADD CONSTRAINT magazin_status_werte
    CHECK (status IN ('entwurf', 'in_pruefung', 'veroeffentlicht', 'zurueckgezogen'));

ALTER TABLE public.magazin_beitraege DROP CONSTRAINT IF EXISTS magazin_laengen;
ALTER TABLE public.magazin_beitraege ADD CONSTRAINT magazin_laengen
    CHECK (length(titel) BETWEEN 1 AND 90
           AND (seo_titel IS NULL OR length(seo_titel) <= 60)
           AND (teaser IS NULL OR length(teaser) BETWEEN 80 AND 160)
           AND (kurzfassung IS NULL OR array_length(kurzfassung, 1) BETWEEN 3 AND 5));

ALTER TABLE public.magazin_beitraege DROP CONSTRAINT IF EXISTS magazin_json_form;
ALTER TABLE public.magazin_beitraege ADD CONSTRAINT magazin_json_form
    CHECK ((faq IS NULL OR jsonb_typeof(faq) = 'array')
           AND jsonb_typeof(quellen) = 'array'
           AND jsonb_typeof(ki_entwurf) = 'object'
           AND jsonb_typeof(pruefung) = 'object');

ALTER TABLE public.magazin_beitraege DROP CONSTRAINT IF EXISTS magazin_zeitraum;
ALTER TABLE public.magazin_beitraege ADD CONSTRAINT magazin_zeitraum
    CHECK (gueltig_von IS NULL OR gueltig_bis IS NULL OR gueltig_von <= gueltig_bis);

-- SHA-256 als Hex (Plan 5.3); nie der Schlüssel selbst
ALTER TABLE public.magazin_beitraege DROP CONSTRAINT IF EXISTS magazin_vorschau_hash_form;
ALTER TABLE public.magazin_beitraege ADD CONSTRAINT magazin_vorschau_hash_form
    CHECK (vorschau_hash IS NULL OR vorschau_hash ~ '^[0-9a-f]{64}$');

-- Hero-Pfad (Plan 3.1, Cursor-Prüfung 2 Befund 1): ungeschützte | als Oder; das Fremdfoto als eigenes Verbot.
-- Die Mindesthöhe (≥ 675 px) prüfen Pipeline und Website (ERLAUBTE_FALLBACK_HEROS), nicht dieses Muster.
ALTER TABLE public.magazin_beitraege DROP CONSTRAINT IF EXISTS magazin_hero_pfad;
ALTER TABLE public.magazin_beitraege ADD CONSTRAINT magazin_hero_pfad
    CHECK (hero_bild IS NULL OR (
        hero_bild ~ '^/(magazin-bilder/[a-z0-9-]+|fallback|ort-bilder/weihnachtsmaerkte)/[a-z0-9-]+\.(webp|jpg|png)$'
        AND hero_bild <> '/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp'
    ));


-- ════════════════════════════════════════════════════════════════════════════
-- 3  KI-Kosten (Plan 4.4) – nur die Pipeline (service_role)
-- ════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public.magazin_ki_kosten (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zeitpunkt  TIMESTAMPTZ NOT NULL DEFAULT now(),
    art        TEXT NOT NULL CHECK (art IN ('reserviert', 'gemessen')),
    kosten_usd NUMERIC(8, 4) NOT NULL CHECK (kosten_usd >= 0),
    beitrag_id UUID REFERENCES public.magazin_beitraege(id) ON DELETE SET NULL,
    modell     TEXT,
    tokens_ein INTEGER CHECK (tokens_ein IS NULL OR tokens_ein >= 0),
    tokens_aus INTEGER CHECK (tokens_aus IS NULL OR tokens_aus >= 0)
);


-- ════════════════════════════════════════════════════════════════════════════
-- 4  Workflow-Trigger (Plan 3.1 „Trigger magazin_status_pruefen“, T5)
-- ════════════════════════════════════════════════════════════════════════════
-- SECURITY INVOKER (Standard): current_user ist die schreibende Rolle. Die Pipeline schreibt über PostgREST als
-- service_role, die Website als anon/authenticated, der Auftraggeber im Table Editor / SQL-Editor als postgres.
CREATE OR REPLACE FUNCTION public.magazin_status_pruefen()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = ''
AS $$
DECLARE
    maschine BOOLEAN := current_user IN ('service_role', 'anon', 'authenticated');
BEGIN
    -- Kennzeichen „Symbolbild (KI-generiert)“: alle Bilder aus /fallback/ sind KI-generiert (Plan 1.2, E7)
    IF NEW.hero_bild LIKE '/fallback/%' THEN
        NEW.hero_ki := TRUE;
    END IF;

    -- Veröffentlichen nur durch den Auftraggeber, nur aus in_pruefung, nur mit Pflichtfeldern und grüner Prüfung
    IF NEW.status = 'veroeffentlicht' AND (TG_OP = 'INSERT' OR OLD.status IS DISTINCT FROM 'veroeffentlicht') THEN
        IF maschine THEN
            RAISE EXCEPTION 'magazin_veroeffentlichen_nur_redaktion'
                USING HINT = 'Veröffentlichen kann nur der Auftraggeber im Supabase-Table-Editor (Plan T5).';
        END IF;
        IF TG_OP = 'INSERT' OR OLD.status <> 'in_pruefung' THEN
            RAISE EXCEPTION 'magazin_veroeffentlichen_nur_aus_pruefung'
                USING HINT = 'Ein Beitrag wird nur aus dem Status in_pruefung veröffentlicht.';
        END IF;
        IF NEW.veroeffentlicht_am IS NULL OR coalesce(NEW.freigegeben_von, '') = ''
           OR NEW.hero_bild IS NULL OR coalesce(NEW.hero_alt, '') = '' OR coalesce(NEW.hero_nachweis, '') = ''
           OR NEW.teaser IS NULL THEN
            RAISE EXCEPTION 'magazin_pflichtfelder_fehlen'
                USING HINT = 'Vor dem Veröffentlichen setzen: veroeffentlicht_am, freigegeben_von, hero_bild, hero_alt, hero_nachweis, teaser.';
        END IF;
        IF coalesce(NEW.pruefung ->> 'ergebnis', '') <> 'gruen' THEN
            RAISE EXCEPTION 'magazin_pruefung_nicht_gruen'
                USING HINT = 'Die automatische Prüfung (Spalte pruefung) muss ergebnis = gruen haben.';
        END IF;
        NEW.freigegeben_am := now();
        NEW.vorschau_hash := NULL;
    END IF;

    -- Veröffentlichte Beiträge: Pipeline und Website dürfen nur pruefung und gemeldet_am ändern (siehe Kopf)
    IF TG_OP = 'UPDATE' AND OLD.status = 'veroeffentlicht' AND maschine
       AND (to_jsonb(NEW) - 'pruefung' - 'gemeldet_am') IS DISTINCT FROM (to_jsonb(OLD) - 'pruefung' - 'gemeldet_am') THEN
        RAISE EXCEPTION 'magazin_veroeffentlicht_gesperrt'
            USING HINT = 'Veröffentlichte Beiträge ändert nur der Auftraggeber; die Pipeline darf nur pruefung und gemeldet_am schreiben.';
    END IF;

    -- Slug-Historie: geänderter Slug eines veröffentlichten Beitrags → alter Slug in alte_slugs (308 im Proxy)
    IF TG_OP = 'UPDATE' AND OLD.status = 'veroeffentlicht' AND NEW.slug <> OLD.slug THEN
        IF NOT (OLD.slug = ANY (NEW.alte_slugs)) THEN
            NEW.alte_slugs := array_append(NEW.alte_slugs, OLD.slug);
        END IF;
    END IF;
    -- Zurück auf einen früheren Slug: aus der Historie nehmen
    NEW.alte_slugs := array_remove(NEW.alte_slugs, NEW.slug);

    -- Eindeutigkeit über Slugs und alte Slugs hinweg (sonst wäre die 308 im Proxy mehrdeutig)
    IF EXISTS (SELECT 1 FROM public.magazin_beitraege b
               WHERE b.id <> NEW.id AND (NEW.slug = ANY (b.alte_slugs) OR b.slug = ANY (NEW.alte_slugs)
                                         OR b.alte_slugs && NEW.alte_slugs)) THEN
        RAISE EXCEPTION 'magazin_slug_belegt'
            USING HINT = 'Slug oder alter Slug ist bei einem anderen Beitrag schon vergeben.';
    END IF;

    RETURN NEW;
END;
$$;

REVOKE ALL ON FUNCTION public.magazin_status_pruefen() FROM PUBLIC, anon, authenticated;

DROP TRIGGER IF EXISTS magazin_status_pruefen ON public.magazin_beitraege;
CREATE TRIGGER magazin_status_pruefen
    BEFORE INSERT OR UPDATE ON public.magazin_beitraege
    FOR EACH ROW EXECUTE FUNCTION public.magazin_status_pruefen();


-- ════════════════════════════════════════════════════════════════════════════
-- 5  Rechte (Plan 3.1 „Rechte“, Cursor-Prüfungen 1–3)
-- ════════════════════════════════════════════════════════════════════════════
ALTER TABLE public.magazin_beitraege ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.magazin_autoren   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.magazin_ki_kosten ENABLE ROW LEVEL SECURITY;   -- keine Policy: nur service_role

-- Ein REVOKE auf Tabellenebene entfernt auch Spaltenrechte; deshalb erst entziehen, dann gezielt geben.
REVOKE ALL ON public.magazin_beitraege, public.magazin_autoren, public.magazin_ki_kosten FROM PUBLIC, anon, authenticated;
GRANT ALL ON public.magazin_beitraege, public.magazin_autoren, public.magazin_ki_kosten TO service_role;

-- Lesen: nur öffentliche Spalten, nur veröffentlichte Beiträge
GRANT SELECT (id, slug, rubrik, autor_slug, titel, seo_titel, teaser, inhalt_md, kurzfassung, faq, hero_bild, hero_alt,
              hero_nachweis, hero_ki, veroeffentlicht_am, aktualisiert_am, korrektur_hinweis, gueltig_von, gueltig_bis,
              event_ids, ort_slugs, quellen)
    ON public.magazin_beitraege TO anon, authenticated;

DROP POLICY IF EXISTS magazin_lesen ON public.magazin_beitraege;
CREATE POLICY magazin_lesen ON public.magazin_beitraege FOR SELECT TO anon, authenticated
    USING (status = 'veroeffentlicht' AND veroeffentlicht_am <= now());

GRANT SELECT (slug, name, kurzbeschreibung, schwerpunkt, rubriken, bild, bild_ki)
    ON public.magazin_autoren TO anon, authenticated;

DROP POLICY IF EXISTS autoren_lesen ON public.magazin_autoren;
CREATE POLICY autoren_lesen ON public.magazin_autoren FOR SELECT TO anon, authenticated
    USING (aktiv);

-- View mit den Rechten der aufrufenden Rolle (greift Policy und Spaltenrechte; Rechte-Prüfung p4)
CREATE OR REPLACE VIEW public.magazin_oeffentlich WITH (security_invoker = true) AS
    SELECT id, slug, rubrik, autor_slug, titel, seo_titel, teaser, inhalt_md, kurzfassung, faq, hero_bild, hero_alt,
           hero_nachweis, hero_ki, veroeffentlicht_am, aktualisiert_am, korrektur_hinweis, gueltig_von, gueltig_bis,
           event_ids, ort_slugs, quellen
    FROM public.magazin_beitraege;

REVOKE ALL ON public.magazin_oeffentlich FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.magazin_oeffentlich TO anon, authenticated;
GRANT ALL ON public.magazin_oeffentlich TO service_role;


-- ════════════════════════════════════════════════════════════════════════════
-- 6  Indizes (Plan 3.1)
-- ════════════════════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS magazin_beitraege_status_idx ON public.magazin_beitraege (status, veroeffentlicht_am DESC);
CREATE INDEX IF NOT EXISTS magazin_beitraege_rubrik_idx ON public.magazin_beitraege (rubrik, veroeffentlicht_am DESC);
CREATE INDEX IF NOT EXISTS magazin_beitraege_alte_slugs_idx ON public.magazin_beitraege USING GIN (alte_slugs);
CREATE INDEX IF NOT EXISTS magazin_beitraege_event_ids_idx ON public.magazin_beitraege USING GIN (event_ids);
CREATE INDEX IF NOT EXISTS magazin_ki_kosten_zeit_idx ON public.magazin_ki_kosten (zeitpunkt);

COMMIT;


-- ════════════════════════════════════════════════════════════════════════════
-- 7  Kontrollabfrage – erwartet in jeder Zeile „ok“
-- ════════════════════════════════════════════════════════════════════════════
WITH
tabellen (nr, objekt) AS (VALUES (1, 'magazin_autoren'), (1, 'magazin_beitraege'), (1, 'magazin_ki_kosten')),
k_tabellen AS (
    SELECT t.nr, 'Tabelle mit RLS'::text AS pruefung, t.objekt, 'RLS an'::text AS erwartet,
           coalesce((SELECT CASE WHEN c.relrowsecurity THEN 'RLS an' ELSE 'RLS AUS' END
                     FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                     WHERE n.nspname = 'public' AND c.relname = t.objekt), 'fehlt') AS ist
    FROM tabellen t
),
k_view AS (
    SELECT 2 AS nr, 'View security_invoker'::text AS pruefung, 'magazin_oeffentlich'::text AS objekt,
           'true'::text AS erwartet,
           coalesce((SELECT o.option_value FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace,
                            pg_options_to_table(c.reloptions) o
                     WHERE n.nspname = 'public' AND c.relname = 'magazin_oeffentlich'
                       AND o.option_name = 'security_invoker'), 'fehlt') AS ist
),
policies (objekt) AS (VALUES ('magazin_lesen'), ('autoren_lesen')),
k_policies AS (
    SELECT 3 AS nr, 'Policy vorhanden'::text AS pruefung, p.objekt, 'vorhanden'::text AS erwartet,
           CASE WHEN EXISTS (SELECT 1 FROM pg_policies x WHERE x.schemaname = 'public' AND x.policyname = p.objekt)
                THEN 'vorhanden' ELSE 'fehlt' END AS ist
    FROM policies p
),
k_trigger AS (
    SELECT 4 AS nr, 'Trigger aktiv'::text AS pruefung, 'magazin_status_pruefen'::text AS objekt,
           'vorhanden, an'::text AS erwartet,
           coalesce((SELECT CASE WHEN tg.tgenabled = 'D' THEN 'vorhanden, AUS' ELSE 'vorhanden, an' END
                     FROM pg_trigger tg WHERE tg.tgname = 'magazin_status_pruefen' AND NOT tg.tgisinternal
                     LIMIT 1), 'fehlt') AS ist
),
-- Rechte je Rolle: (Rolle, Objekt, Spalte oder NULL, Recht, erwartet)
rechte_soll (rolle, objekt, spalte, recht, soll) AS (
    VALUES
    ('anon',          'magazin_beitraege',   'titel',           'SELECT', true),
    ('anon',          'magazin_beitraege',   'inhalt_md',       'SELECT', true),
    ('anon',          'magazin_beitraege',   'status',          'SELECT', false),
    ('anon',          'magazin_beitraege',   'ki_entwurf',      'SELECT', false),
    ('anon',          'magazin_beitraege',   'pruefung',        'SELECT', false),
    ('anon',          'magazin_beitraege',   'vorschau_hash',   'SELECT', false),
    ('anon',          'magazin_beitraege',   'alte_slugs',      'SELECT', false),
    ('anon',          'magazin_beitraege',   'freigegeben_von', 'SELECT', false),
    ('authenticated', 'magazin_beitraege',   'ki_entwurf',      'SELECT', false),
    ('authenticated', 'magazin_beitraege',   'vorschau_hash',   'SELECT', false),
    ('anon',          'magazin_beitraege',   NULL,              'INSERT', false),
    ('anon',          'magazin_beitraege',   NULL,              'UPDATE', false),
    ('authenticated', 'magazin_beitraege',   NULL,              'INSERT', false),
    ('authenticated', 'magazin_beitraege',   NULL,              'UPDATE', false),
    ('authenticated', 'magazin_beitraege',   NULL,              'DELETE', false),
    ('anon',          'magazin_oeffentlich', NULL,              'SELECT', true),
    ('anon',          'magazin_oeffentlich', NULL,              'INSERT', false),
    ('authenticated', 'magazin_oeffentlich', NULL,              'UPDATE', false),
    ('anon',          'magazin_autoren',     'name',            'SELECT', true),
    ('anon',          'magazin_autoren',     'aktiv',           'SELECT', false),
    ('anon',          'magazin_autoren',     NULL,              'INSERT', false),
    ('anon',          'magazin_ki_kosten',   NULL,              'SELECT', false),
    ('authenticated', 'magazin_ki_kosten',   NULL,              'SELECT', false),
    ('service_role',  'magazin_beitraege',   NULL,              'UPDATE', true),
    ('service_role',  'magazin_ki_kosten',   NULL,              'INSERT', true)
),
k_rechte AS (
    SELECT 5 AS nr, 'Recht ' || r.recht AS pruefung,
           r.rolle || ' → ' || r.objekt || coalesce('.' || r.spalte, '') AS objekt,
           CASE WHEN r.soll THEN 'ja' ELSE 'nein' END AS erwartet,
           CASE WHEN (CASE WHEN r.spalte IS NULL
                           THEN has_table_privilege(r.rolle, 'public.' || r.objekt, r.recht)
                           ELSE has_column_privilege(r.rolle, 'public.' || r.objekt, r.spalte, r.recht) END)
                THEN 'ja' ELSE 'nein' END AS ist
    FROM rechte_soll r
),
alles AS (
    SELECT nr, pruefung, objekt, erwartet, ist FROM k_tabellen
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM k_view
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM k_policies
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM k_trigger
    UNION ALL SELECT nr, pruefung, objekt, erwartet, ist FROM k_rechte
)
SELECT nr, pruefung, objekt, erwartet, ist,
       CASE WHEN erwartet = ist THEN 'ok' ELSE 'FEHLER' END AS ergebnis
FROM alles
ORDER BY CASE WHEN erwartet = ist THEN 1 ELSE 0 END, nr, objekt;
