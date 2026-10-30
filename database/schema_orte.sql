-- schema_orte.sql – DiesDasDüsseldorf
-- Tabelle für statische Orte (Restaurants, Cafés, Kneipen, Clubs, Spielplätze etc.)
-- Erstellt: 2026-10-30

-- Typ-Enum als CHECK-Constraint
CREATE TABLE IF NOT EXISTS orte (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                      TEXT NOT NULL,
    slug                      TEXT UNIQUE NOT NULL,
    typ                       TEXT NOT NULL CHECK (typ IN (
                                  'restaurant', 'cafe', 'kneipe', 'club',
                                  'spielplatz', 'ausflug', 'wochenendtipp'
                              )),
    untertitel                TEXT,
    beschreibung              TEXT,
    highlight                 TEXT,
    adresse                   TEXT,
    stadtteil                 TEXT,
    latitude                  DOUBLE PRECISION,
    longitude                 DOUBLE PRECISION,
    bild_url                  TEXT,
    bild_attribution          TEXT,
    tags                      TEXT[] DEFAULT '{}',
    preis_niveau              TEXT CHECK (preis_niveau IS NULL OR preis_niveau IN ('€', '€€', '€€€')),
    oeffnungszeiten           TEXT,
    webseite                  TEXT,
    telefon                   TEXT,
    instagram                 TEXT,
    google_place_id           TEXT,
    google_rating             NUMERIC(2,1),
    google_bewertungen_anzahl INTEGER,
    qualitaets_score          INTEGER CHECK (qualitaets_score IS NULL OR qualitaets_score BETWEEN 1 AND 10),
    extras                    JSONB DEFAULT '{}',
    sortierung                INTEGER DEFAULT 0,
    aktiv                     BOOLEAN DEFAULT false,
    erstellt_am               TIMESTAMPTZ DEFAULT now(),
    aktualisiert_am           TIMESTAMPTZ DEFAULT now()
);

-- Indizes für häufige Abfragen
CREATE INDEX IF NOT EXISTS idx_orte_typ       ON orte (typ);
CREATE INDEX IF NOT EXISTS idx_orte_stadtteil ON orte (stadtteil);
CREATE INDEX IF NOT EXISTS idx_orte_aktiv     ON orte (aktiv) WHERE aktiv = true;
CREATE INDEX IF NOT EXISTS idx_orte_slug      ON orte (slug);
CREATE INDEX IF NOT EXISTS idx_orte_google_id ON orte (google_place_id);

-- Trigger: aktualisiert_am automatisch setzen
CREATE OR REPLACE FUNCTION orte_aktualisiert_am()
RETURNS TRIGGER AS $$
BEGIN
    NEW.aktualisiert_am = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_orte_aktualisiert ON orte;
CREATE TRIGGER trg_orte_aktualisiert
    BEFORE UPDATE ON orte
    FOR EACH ROW
    EXECUTE FUNCTION orte_aktualisiert_am();

-- Row Level Security: Lesen für alle, Schreiben nur für authentifizierte Admins
ALTER TABLE orte ENABLE ROW LEVEL SECURITY;

CREATE POLICY orte_lesen ON orte
    FOR SELECT
    USING (aktiv = true);

CREATE POLICY orte_admin_alles ON orte
    FOR ALL
    USING (auth.role() = 'service_role');
