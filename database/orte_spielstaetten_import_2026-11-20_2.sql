-- Import der freigegebenen Ortsseiten (Plan docs/plan-locations-2026-11-18.md, Schritt 2, Deploy-Punkt 3)
-- Erzeugt am 2026-11-20 von `python -m scraper.orte.spielstaetten_import` aus
-- data/spielstaetten/kandidaten.csv (nur Zeilen mit entscheidung = ja). Wiederholbar (ON CONFLICT DO NOTHING).
-- Voraussetzung: database/orte_spielstaetten_2026-11-19.sql ist ausgeführt.
-- Importiert: 7 Zeilen. Abgelehnt: 0.

BEGIN;

INSERT INTO public.orte (name, slug, typ, aktiv, parent_id, extras) VALUES ('Cuvée', 'cuvee', 'spielstaette', true, NULL, jsonb_build_object('spielstaette', '{"art": "Club/Bar/Kneipe", "zeile_typ": "haus", "event_orte": ["Cuvée"], "freigabe": "freigegeben 20.11.2026", "import": "2026-11-20"}'::jsonb)) ON CONFLICT (slug) DO NOTHING;
INSERT INTO public.orte (name, slug, typ, aktiv, parent_id, extras) VALUES ('Hamtorkrug', 'hamtorkrug', 'spielstaette', true, NULL, jsonb_build_object('spielstaette', '{"art": "Club/Bar/Kneipe", "zeile_typ": "haus", "event_orte": ["Hamtorkrug"], "freigabe": "freigegeben 20.11.2026", "import": "2026-11-20"}'::jsonb)) ON CONFLICT (slug) DO NOTHING;
INSERT INTO public.orte (name, slug, typ, aktiv, parent_id, extras) VALUES ('Jugendkirche', 'jugendkirche', 'spielstaette', true, NULL, jsonb_build_object('spielstaette', '{"art": "Kirche/Gemeinde", "zeile_typ": "haus", "event_orte": ["Jugendkirche", "Jugendkirche Düsseldorf"], "freigabe": "freigegeben 20.11.2026", "import": "2026-11-20"}'::jsonb)) ON CONFLICT (slug) DO NOTHING;
INSERT INTO public.orte (name, slug, typ, aktiv, parent_id, extras) VALUES ('Raketenstation Hombroich', 'raketenstation-hombroich', 'spielstaette', true, NULL, jsonb_build_object('spielstaette', '{"art": "Ausflugsziel/Sehenswürdigkeit", "zeile_typ": "haus", "event_orte": ["Raketenstation Hombroich"], "freigabe": "freigegeben 20.11.2026", "import": "2026-11-20"}'::jsonb)) ON CONFLICT (slug) DO NOTHING;
INSERT INTO public.orte (name, slug, typ, aktiv, parent_id, extras) VALUES ('SCHVARZ KAFFEE HQ', 'schvarz-kaffee-hq', 'spielstaette', true, NULL, jsonb_build_object('spielstaette', '{"art": "Café/Restaurant", "zeile_typ": "haus", "event_orte": ["SCHVARZ KAFFEE HQ"], "freigabe": "freigegeben 20.11.2026", "import": "2026-11-20"}'::jsonb)) ON CONFLICT (slug) DO NOTHING;
INSERT INTO public.orte (name, slug, typ, aktiv, parent_id, extras) VALUES ('Theaterfabrik', 'theaterfabrik', 'spielstaette', true, NULL, jsonb_build_object('spielstaette', '{"art": "Oper/Theater/Bühne", "zeile_typ": "haus", "event_orte": ["Theaterfabrik"], "freigabe": "freigegeben 20.11.2026", "import": "2026-11-20"}'::jsonb)) ON CONFLICT (slug) DO NOTHING;
INSERT INTO public.orte (name, slug, typ, aktiv, parent_id, extras) VALUES ('Vino Tinto', 'vino-tinto', 'spielstaette', true, NULL, jsonb_build_object('spielstaette', '{"art": "Gastronomie/Eventlocation", "zeile_typ": "haus", "event_orte": ["Vino Tinto"], "freigabe": "freigegeben 20.11.2026", "import": "2026-11-20"}'::jsonb)) ON CONFLICT (slug) DO NOTHING;

COMMIT;

-- Kontrolle: Spielstätten, davon Säle/Standorte mit Haus, ohne Schreibweisen
SELECT count(*) AS spielstaetten, count(parent_id) AS mit_haus,
       count(*) FILTER (WHERE jsonb_array_length(extras->'spielstaette'->'event_orte') = 0) AS ohne_schreibweisen
FROM public.orte WHERE typ = 'spielstaette';
