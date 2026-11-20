-- Lauf-Bericht: Spalten für die Kennzahlen der Ortszuordnung (Plan docs/plan-locations-2026-11-18.md, 3.4).
-- Seit Schritt 2 (f33890f, live 19.11.2026) meldet main.py diese vier Kennzahlen, die Spalten fehlten aber –
-- deshalb scheiterte das Speichern des Lauf-Berichts (PGRST204 „ort_id_mehrdeutig“). Wiederholbar.
--   ort_treffer          – Events dieses Laufs, denen ein Ort zugeordnet wurde
--   ort_mehrdeutig_neu   – Events dieses Laufs mit mehreren passenden Orten (keine ort_id gesetzt)
--   ort_id_ohne_treffer  – gespeicherte ort_id im ganzen Bestand, deren Ortsname keine Zeile mehr trifft (Hinweis)
--   ort_id_mehrdeutig    – gespeicherte ort_id im ganzen Bestand, deren Ortsname mehrere Zeilen trifft (Hinweis)

ALTER TABLE public.scraper_laeufe
    ADD COLUMN IF NOT EXISTS ort_treffer         INTEGER,
    ADD COLUMN IF NOT EXISTS ort_mehrdeutig_neu  INTEGER,
    ADD COLUMN IF NOT EXISTS ort_id_ohne_treffer INTEGER,
    ADD COLUMN IF NOT EXISTS ort_id_mehrdeutig   INTEGER;

-- PostgREST den neuen Aufbau sofort mitteilen (sonst kennt der Schema-Cache die Spalten erst später)
NOTIFY pgrst, 'reload schema';

-- Kontrolle: die vier Spalten
SELECT column_name, data_type FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'scraper_laeufe' AND column_name LIKE 'ort%'
ORDER BY column_name;
