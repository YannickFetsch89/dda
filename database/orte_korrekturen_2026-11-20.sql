-- Ortsseiten: Korrekturen aus der Recherche der Ortstexte (Plan docs/plan-locations-2026-11-18.md, 3.4, 3.12)
-- Stand: 2026-11-20 · vom Auftraggeber freigegeben. Im Supabase SQL-Editor ausführen. Wiederholbar.
-- 1) Art korrigieren  2) Orte ohne Seite entfernen (Weiterleitung auf /orte)  3) Adressen (Website des Hauses,
--    Koordinaten OpenStreetMap, Stadtteil nur aus der PLZ). Zusammenlegungen stehen in eigenen Dateien
--    (orte_balletthaus_zusammen_…, orte_bunker_zusammen_…).

BEGIN;

-- ── 1) Art ──
UPDATE public.orte SET extras = jsonb_set(extras, '{spielstaette,art}', to_jsonb('Kurs/Studio/Sport'::text)) WHERE slug = 'boston-club' AND typ = 'spielstaette';
UPDATE public.orte SET extras = jsonb_set(extras, '{spielstaette,art}', to_jsonb('Laden'::text)) WHERE slug = 'the-vinyl-room' AND typ = 'spielstaette';
UPDATE public.orte SET extras = jsonb_set(extras, '{spielstaette,art}', to_jsonb('Museum/Ausstellung'::text)) WHERE slug = 'reinraum-e-v' AND typ = 'spielstaette';

-- ── 2) Keine Seite: Denkmal, Showroom, geschlossen, nicht mehr dort ──
INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'bergischer-loewe-duesseldorf', NULL, 'Bronzedenkmal, nur Treffpunkt – Auftraggeber 20.11.2026'
WHERE EXISTS (SELECT 1 FROM public.orte WHERE slug = 'bergischer-loewe-duesseldorf') ON CONFLICT (alter_slug) DO NOTHING;
UPDATE public.events SET ort_id = NULL WHERE ort_id = (SELECT id FROM public.orte WHERE slug = 'bergischer-loewe-duesseldorf');
DELETE FROM public.orte WHERE slug = 'bergischer-loewe-duesseldorf';

INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'design-center-kronospan', NULL, 'Showroom für Fachleute, kein Veranstaltungsort – Auftraggeber 20.11.2026'
WHERE EXISTS (SELECT 1 FROM public.orte WHERE slug = 'design-center-kronospan') ON CONFLICT (alter_slug) DO NOTHING;
UPDATE public.events SET ort_id = NULL WHERE ort_id = (SELECT id FROM public.orte WHERE slug = 'design-center-kronospan');
DELETE FROM public.orte WHERE slug = 'design-center-kronospan';

INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'lu-fung-chinesisches-restaurant', NULL, 'laut eigener Website zum 31.10.2026 geschlossen – Auftraggeber 20.11.2026'
WHERE EXISTS (SELECT 1 FROM public.orte WHERE slug = 'lu-fung-chinesisches-restaurant') ON CONFLICT (alter_slug) DO NOTHING;
UPDATE public.events SET ort_id = NULL WHERE ort_id = (SELECT id FROM public.orte WHERE slug = 'lu-fung-chinesisches-restaurant');
DELETE FROM public.orte WHERE slug = 'lu-fung-chinesisches-restaurant';

INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'ufo-am-rather-carre-quartiersplatz-duesseldorf-rath', NULL, 'mobile Spielstätte der Oper, dort nur Februar bis Juli 2026 – Auftraggeber 20.11.2026'
WHERE EXISTS (SELECT 1 FROM public.orte WHERE slug = 'ufo-am-rather-carre-quartiersplatz-duesseldorf-rath') ON CONFLICT (alter_slug) DO NOTHING;
UPDATE public.events SET ort_id = NULL WHERE ort_id = (SELECT id FROM public.orte WHERE slug = 'ufo-am-rather-carre-quartiersplatz-duesseldorf-rath');
DELETE FROM public.orte WHERE slug = 'ufo-am-rather-carre-quartiersplatz-duesseldorf-rath';

-- ── 3) Adressen ──
UPDATE public.orte SET adresse = 'Henkelstraße 15, 40589 Düsseldorf', stadtteil = 'Holthausen', latitude = 51.1756343, longitude = 6.8352529,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"adresse_bestaetigt": {"datum": "2026-11-20", "quelle": "Website des Hauses"}, "geo_quelle": "osm", "stadt": "Düsseldorf"}'::jsonb)
WHERE slug = 'zentrum-plus-holthausen' AND typ = 'spielstaette';
UPDATE public.orte SET adresse = 'Schinkelstraße 65, 40211 Düsseldorf', stadtteil = 'Pempelfort', latitude = 51.2352863, longitude = 6.7940827,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"adresse_bestaetigt": {"datum": "2026-11-20", "quelle": "Website des Hauses"}, "geo_quelle": "osm", "stadt": "Düsseldorf"}'::jsonb)
WHERE slug = 'glazed-dein-keramik-mal-studio' AND typ = 'spielstaette';
UPDATE public.orte SET adresse = 'Wiesenstraße 21A, 40549 Düsseldorf', stadtteil = 'Heerdt', latitude = 51.2291484, longitude = 6.7097333,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"adresse_bestaetigt": {"datum": "2026-11-20", "quelle": "Website des Hauses"}, "geo_quelle": "osm", "stadt": "Düsseldorf"}'::jsonb)
WHERE slug = 'glow-patterns-art-studio' AND typ = 'spielstaette';
UPDATE public.orte SET adresse = 'Stresemannplatz 4, 40210 Düsseldorf', stadtteil = 'Stadtmitte', latitude = 51.2189453, longitude = 6.7885814,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"adresse_bestaetigt": {"datum": "2026-11-20", "quelle": "Website des Hauses"}, "geo_quelle": "osm", "stadt": "Düsseldorf"}'::jsonb)
WHERE slug = 'coffee-brew-duesseldorf-cafe-bar' AND typ = 'spielstaette';

COMMIT;

-- Kontrolle: entfernte Orte 0, Weiterleitungen 4, neue Adressen 4
SELECT
  (SELECT count(*) FROM public.orte WHERE slug IN ('bergischer-loewe-duesseldorf', 'design-center-kronospan', 'lu-fung-chinesisches-restaurant', 'ufo-am-rather-carre-quartiersplatz-duesseldorf-rath')) AS entfernt_noch_da,
  (SELECT count(*) FROM public.ort_weiterleitungen WHERE alter_slug IN ('bergischer-loewe-duesseldorf', 'design-center-kronospan', 'lu-fung-chinesisches-restaurant', 'ufo-am-rather-carre-quartiersplatz-duesseldorf-rath')) AS weiterleitungen,
  (SELECT count(*) FROM public.orte WHERE adresse IN ('Henkelstraße 15, 40589 Düsseldorf', 'Schinkelstraße 65, 40211 Düsseldorf', 'Wiesenstraße 21A, 40549 Düsseldorf', 'Stresemannplatz 4, 40210 Düsseldorf')) AS neue_adressen;
