-- schema.sql – DiesDasDüsseldorf
-- Supabase / PostgreSQL Tabellenstruktur
-- Erstellt: 2026-02-24

-- Erweiterung für UUID-Generierung
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Haupt-Tabelle für alle Events
CREATE TABLE IF NOT EXISTS events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titel           TEXT NOT NULL,
    datum           DATE NOT NULL,
    uhrzeit         TIME,
    ort             TEXT NOT NULL,
    adresse         TEXT,
    kategorie       TEXT NOT NULL CHECK (kategorie IN (
                        'kultur', 'musik', 'food', 'sport',
                        'outdoor', 'community', 'nightlife',
                        'family', 'dating', 'sonstiges'
                    )),
    beschreibung    TEXT CHECK (char_length(beschreibung) <= 300),
    preis           TEXT,
    quelle_name     TEXT NOT NULL,
    quelle_url      TEXT NOT NULL,
    bild_url        TEXT,
    instagram_caption TEXT CHECK (char_length(instagram_caption) <= 2200),
    datum_bis       DATE,                          -- Enddatum für laufende/wiederkehrende Events
    ist_wiederkehrend BOOLEAN NOT NULL DEFAULT FALSE, -- Ausstellung, Konzertreihe, o.ä.
    status          TEXT NOT NULL DEFAULT 'neu' CHECK (status IN (
                        'neu', 'aufbereitet', 'gepostet', 'fehler'
                    )),
    erstellt_am     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    gepostet_am     TIMESTAMPTZ,

    -- Duplikat-Schutz: gleicher Titel + Datum + Ort = Duplikat
    UNIQUE (titel, datum, ort)
);

-- Index für häufige Abfragen
CREATE INDEX IF NOT EXISTS idx_events_datum           ON events (datum);
CREATE INDEX IF NOT EXISTS idx_events_status          ON events (status);
CREATE INDEX IF NOT EXISTS idx_events_kategorie       ON events (kategorie);
CREATE INDEX IF NOT EXISTS idx_events_wiederkehrend   ON events (ist_wiederkehrend);

-- Migration: Neue Spalten zu bestehender Tabelle hinzufügen (falls Tabelle existiert)
ALTER TABLE events ADD COLUMN IF NOT EXISTS datum_bis DATE;
ALTER TABLE events ADD COLUMN IF NOT EXISTS ist_wiederkehrend BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE events ADD COLUMN IF NOT EXISTS instagram_location_id TEXT;

-- Dashboard: Admin-Steuerung (opt-out + Featured-Tiers)
ALTER TABLE events ADD COLUMN IF NOT EXISTS abgelehnt BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE events ADD COLUMN IF NOT EXISTS tipp_des_tages BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE events ADD COLUMN IF NOT EXISTS highlight_der_woche BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE events ADD COLUMN IF NOT EXISTS top_event_des_monats BOOLEAN NOT NULL DEFAULT FALSE;

-- Indizes für Dashboard-Abfragen
CREATE INDEX IF NOT EXISTS idx_events_abgelehnt  ON events (abgelehnt);
CREATE INDEX IF NOT EXISTS idx_events_featured   ON events (tipp_des_tages, highlight_der_woche, top_event_des_monats);
