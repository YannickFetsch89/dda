-- meldungen_newsletter_2026-11-05.sql – DiesDasDüsseldorf
-- Newsletter-Anmeldungen und „Event melden“ (Website-Formulare) + Bild-Speicher
-- Im Supabase SQL-Editor ausführen. Wiederholbar (idempotent). Voraussetzung: auth_rollen.sql (ist_admin()).
--
-- Grundsatz: Die Website (anon-Key, nur serverseitig in den Route-Handlern) darf in diese Tabellen
-- ausschließlich NEUE Einträge schreiben – nichts lesen, ändern oder löschen. Lesen/Bearbeiten nur Admins
-- (Dashboard). Bilder aus Meldungen liegen privat; erst bei Freigabe kopiert das Dashboard sie in den
-- öffentlichen Bucket „event-bilder“.


-- ── 1. Newsletter-Anmeldungen (vorerst ohne Double-Opt-in) ──────────────────

CREATE TABLE IF NOT EXISTS public.newsletter_anmeldungen (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email          TEXT NOT NULL CHECK (char_length(email) <= 254 AND email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    quelle         TEXT NOT NULL DEFAULT 'website' CHECK (char_length(quelle) <= 40),
    erstellt_am    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bestaetigt_am  TIMESTAMPTZ,   -- für ein späteres Double-Opt-in
    abgemeldet_am  TIMESTAMPTZ
);
-- Jede Adresse nur einmal (unabhängig von Groß-/Kleinschreibung)
CREATE UNIQUE INDEX IF NOT EXISTS idx_newsletter_email ON public.newsletter_anmeldungen (lower(email));

ALTER TABLE public.newsletter_anmeldungen ENABLE ROW LEVEL SECURITY;
GRANT INSERT ON public.newsletter_anmeldungen TO anon, authenticated;
GRANT SELECT, UPDATE, DELETE ON public.newsletter_anmeldungen TO authenticated;

DROP POLICY IF EXISTS "Newsletter anmelden" ON public.newsletter_anmeldungen;
CREATE POLICY "Newsletter anmelden" ON public.newsletter_anmeldungen
    FOR INSERT TO anon, authenticated
    WITH CHECK (bestaetigt_am IS NULL AND abgemeldet_am IS NULL);

DROP POLICY IF EXISTS "Admins lesen Newsletter" ON public.newsletter_anmeldungen;
CREATE POLICY "Admins lesen Newsletter" ON public.newsletter_anmeldungen
    FOR SELECT TO authenticated USING (public.ist_admin());

DROP POLICY IF EXISTS "Admins ändern Newsletter" ON public.newsletter_anmeldungen;
CREATE POLICY "Admins ändern Newsletter" ON public.newsletter_anmeldungen
    FOR UPDATE TO authenticated USING (public.ist_admin()) WITH CHECK (public.ist_admin());

DROP POLICY IF EXISTS "Admins löschen Newsletter" ON public.newsletter_anmeldungen;
CREATE POLICY "Admins löschen Newsletter" ON public.newsletter_anmeldungen
    FOR DELETE TO authenticated USING (public.ist_admin());


-- ── 2. Event-Meldungen (müssen von Admins freigegeben werden) ───────────────

CREATE TABLE IF NOT EXISTS public.event_meldungen (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    erstellt_am     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status          TEXT NOT NULL DEFAULT 'neu' CHECK (status IN ('neu', 'freigegeben', 'abgelehnt')),
    titel           TEXT NOT NULL CHECK (char_length(titel) BETWEEN 3 AND 150),
    kategorie       TEXT NOT NULL CHECK (kategorie IN (
                        'kultur', 'musik', 'food', 'sport', 'outdoor', 'stadtfuehrung',
                        'community', 'nightlife', 'family', 'dating', 'sonstiges'
                    )),
    datum           DATE NOT NULL,
    datum_bis       DATE CHECK (datum_bis IS NULL OR datum_bis >= datum),
    uhrzeit         TIME,
    ort             TEXT NOT NULL CHECK (char_length(ort) BETWEEN 2 AND 150),
    adresse         TEXT CHECK (char_length(adresse) <= 200),
    preis           TEXT CHECK (char_length(preis) <= 80),
    beschreibung    TEXT NOT NULL CHECK (char_length(beschreibung) BETWEEN 20 AND 2000),
    link            TEXT CHECK (link IS NULL OR (char_length(link) <= 500 AND link ~* '^https?://')),
    bild_pfad       TEXT CHECK (char_length(bild_pfad) <= 200),   -- Pfad im privaten Bucket event-meldungen
    bild_rechte     BOOLEAN NOT NULL DEFAULT FALSE,               -- Einsender bestätigt die Bildrechte
    kontakt_name    TEXT CHECK (char_length(kontakt_name) <= 100),
    kontakt_email   TEXT NOT NULL CHECK (char_length(kontakt_email) <= 254 AND kontakt_email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$'),
    kontakt_rolle   TEXT NOT NULL DEFAULT 'veranstalter' CHECK (kontakt_rolle IN ('veranstalter', 'besucher')),
    anmerkung       TEXT CHECK (char_length(anmerkung) <= 1000),
    -- Bearbeitung durch Admins
    event_id        UUID REFERENCES public.events (id) ON DELETE SET NULL,
    bearbeitet_am   TIMESTAMPTZ,
    bearbeitet_von  UUID,
    ablehngrund     TEXT
);
CREATE INDEX IF NOT EXISTS idx_event_meldungen_status ON public.event_meldungen (status, erstellt_am);

ALTER TABLE public.event_meldungen ENABLE ROW LEVEL SECURITY;
GRANT INSERT ON public.event_meldungen TO anon, authenticated;
GRANT SELECT, UPDATE, DELETE ON public.event_meldungen TO authenticated;

-- Website: nur neue, unbearbeitete Meldungen anlegen
DROP POLICY IF EXISTS "Event melden" ON public.event_meldungen;
CREATE POLICY "Event melden" ON public.event_meldungen
    FOR INSERT TO anon, authenticated
    WITH CHECK (status = 'neu' AND event_id IS NULL AND bearbeitet_am IS NULL
                AND bearbeitet_von IS NULL AND ablehngrund IS NULL);

DROP POLICY IF EXISTS "Admins lesen Meldungen" ON public.event_meldungen;
CREATE POLICY "Admins lesen Meldungen" ON public.event_meldungen
    FOR SELECT TO authenticated USING (public.ist_admin());

DROP POLICY IF EXISTS "Admins bearbeiten Meldungen" ON public.event_meldungen;
CREATE POLICY "Admins bearbeiten Meldungen" ON public.event_meldungen
    FOR UPDATE TO authenticated USING (public.ist_admin()) WITH CHECK (public.ist_admin());

DROP POLICY IF EXISTS "Admins löschen Meldungen" ON public.event_meldungen;
CREATE POLICY "Admins löschen Meldungen" ON public.event_meldungen
    FOR DELETE TO authenticated USING (public.ist_admin());


-- ── 3. Events: Admins dürfen freigegebene Meldungen als Event anlegen ───────

DROP POLICY IF EXISTS "Admins legen Events an" ON public.events;
CREATE POLICY "Admins legen Events an" ON public.events
    FOR INSERT TO authenticated WITH CHECK (public.ist_admin());


-- ── 4. Bild-Speicher ────────────────────────────────────────────────────────
-- event-meldungen: privat, Website lädt hoch (nur neue Dateien), nur Admins lesen/löschen
-- event-bilder:    öffentlich lesbar (Bilder freigegebener Events), nur Admins schreiben

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('event-meldungen', 'event-meldungen', FALSE, 2097152, ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO UPDATE SET public = EXCLUDED.public, file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('event-bilder', 'event-bilder', TRUE, 5242880, ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO UPDATE SET public = EXCLUDED.public, file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

DROP POLICY IF EXISTS "Meldungsbild hochladen" ON storage.objects;
CREATE POLICY "Meldungsbild hochladen" ON storage.objects
    FOR INSERT TO anon, authenticated
    WITH CHECK (bucket_id = 'event-meldungen' AND name LIKE 'meldungen/%');

DROP POLICY IF EXISTS "Admins lesen Meldungsbilder" ON storage.objects;
CREATE POLICY "Admins lesen Meldungsbilder" ON storage.objects
    FOR SELECT TO authenticated USING (bucket_id = 'event-meldungen' AND public.ist_admin());

DROP POLICY IF EXISTS "Admins löschen Meldungsbilder" ON storage.objects;
CREATE POLICY "Admins löschen Meldungsbilder" ON storage.objects
    FOR DELETE TO authenticated USING (bucket_id = 'event-meldungen' AND public.ist_admin());

DROP POLICY IF EXISTS "Admins schreiben Event-Bilder" ON storage.objects;
CREATE POLICY "Admins schreiben Event-Bilder" ON storage.objects
    FOR INSERT TO authenticated WITH CHECK (bucket_id = 'event-bilder' AND public.ist_admin());

DROP POLICY IF EXISTS "Admins verwalten Event-Bilder" ON storage.objects;
CREATE POLICY "Admins verwalten Event-Bilder" ON storage.objects
    FOR DELETE TO authenticated USING (bucket_id = 'event-bilder' AND public.ist_admin());


-- ── Kontrolle ───────────────────────────────────────────────────────────────
SELECT 'Tabellen' AS was, string_agg(table_name, ', ') AS ergebnis
FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('newsletter_anmeldungen', 'event_meldungen')
UNION ALL
SELECT 'Buckets', string_agg(id || CASE WHEN public THEN ' (öffentlich)' ELSE ' (privat)' END, ', ')
FROM storage.buckets WHERE id IN ('event-meldungen', 'event-bilder')
UNION ALL
SELECT 'Regeln', count(*)::text FROM pg_policies
WHERE policyname IN ('Newsletter anmelden', 'Event melden', 'Admins legen Events an', 'Meldungsbild hochladen');
