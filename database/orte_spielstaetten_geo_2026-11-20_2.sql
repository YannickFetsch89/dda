-- Adressen, Stadtteile, Koordinaten der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.12)
-- Erzeugt am 2026-11-20 von `python -m scraper.orte.spielstaetten_geo --sql` aus der lokalen
-- Prüfdatei (nur Zeilen mit bestaetigung = ja). Koordinaten von OpenStreetMap (© OpenStreetMap-Mitwirkende),
-- von Google nur die place_id. Stadtteil nur aus der PLZ. Wiederholbar.

BEGIN;

UPDATE public.orte SET adresse = 'Friedrichstraße 102, 40217 Düsseldorf', stadtteil = 'Unterbilk', latitude = 51.2117628, longitude = 6.7769265, google_place_id = COALESCE(NULL, google_place_id), extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"adresse_bestaetigt": {"datum": "2026-11-20", "quelle": "Website des Hauses"}, "geo_quelle": "osm", "stadt": "Düsseldorf"}'::jsonb) WHERE slug = 'ausarten' AND typ = 'spielstaette';
UPDATE public.orte SET adresse = 'Brehmstraße 41, 40239 Düsseldorf', stadtteil = 'Düsseltal', latitude = 51.2443412, longitude = 6.8020764, google_place_id = COALESCE(NULL, google_place_id), extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"adresse_bestaetigt": {"datum": "2026-11-20", "quelle": "Website des Hauses"}, "geo_quelle": "osm", "stadt": "Düsseldorf"}'::jsonb) WHERE slug = 'b41' AND typ = 'spielstaette';
UPDATE public.orte SET adresse = 'Cecilienallee 25, 40474 Düsseldorf', stadtteil = 'Golzheim', latitude = 51.2439555, longitude = 6.7693897, google_place_id = COALESCE(NULL, google_place_id), extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"adresse_bestaetigt": {"datum": "2026-11-20", "quelle": "Website des Hauses"}, "geo_quelle": "osm", "stadt": "Düsseldorf"}'::jsonb) WHERE slug = 'pialana-manufaktur' AND typ = 'spielstaette';
UPDATE public.orte SET adresse = 'Robert-Lehr-Ufer, 40474 Düsseldorf', stadtteil = 'Golzheim', latitude = 51.2419429, longitude = 6.7675486, google_place_id = COALESCE('ChIJyalmmie4uEcRV4UZA2mBtVU', google_place_id), extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"adresse_bestaetigt": {"datum": "2026-11-20", "quelle": "Website des Hauses"}, "geo_quelle": "osm", "stadt": "Düsseldorf"}'::jsonb) WHERE slug = 'ms-rheinfantasie' AND typ = 'spielstaette';

COMMIT;

-- Kontrolle: Spielstätten mit bestätigter Adresse, mit Koordinaten
SELECT count(*) FILTER (WHERE extras->'spielstaette' ? 'adresse_bestaetigt') AS bestaetigt,
       count(latitude) AS mit_koordinaten FROM public.orte WHERE typ = 'spielstaette';
