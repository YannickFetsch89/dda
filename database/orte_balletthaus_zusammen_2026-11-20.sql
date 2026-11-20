-- „Ballettprobenhaus“ mit „Balletthaus“ zusammenlegen (Plan docs/plan-locations-2026-11-18.md, 3.4 Zusammenlegen)
-- Stand: 2026-11-20 · Fund bei den Ortstexten: beide Zeilen sind dasselbe Haus (Merowingerstraße 88, Probenhaus des
-- Ballett am Rhein). Es bleibt slug „balletthaus“; „ballettprobenhaus“ leitet dorthin weiter. Wiederholbar.
-- Reihenfolge (Schutz-Trigger): Weiterleitung, ältere Weiterleitungen umhängen, Events verschieben, Schreibweisen
-- zusammenführen, alte Zeile löschen.

BEGIN;

INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'ballettprobenhaus', (SELECT id FROM public.orte WHERE slug = 'balletthaus'),
       'Zusammengelegt mit Balletthaus, gleiche Adresse (20.11.2026)'
WHERE EXISTS (SELECT 1 FROM public.orte WHERE slug = 'ballettprobenhaus')
ON CONFLICT (alter_slug) DO NOTHING;

UPDATE public.ort_weiterleitungen SET ziel_ort_id = (SELECT id FROM public.orte WHERE slug = 'balletthaus')
WHERE ziel_ort_id = (SELECT id FROM public.orte WHERE slug = 'ballettprobenhaus');

UPDATE public.events SET ort_id = (SELECT id FROM public.orte WHERE slug = 'balletthaus')
WHERE ort_id = (SELECT id FROM public.orte WHERE slug = 'ballettprobenhaus');

UPDATE public.orte
SET extras = jsonb_set(extras, '{spielstaette,event_orte}',
      (SELECT jsonb_agg(DISTINCT s ORDER BY s) FROM (
         SELECT jsonb_array_elements_text(extras->'spielstaette'->'event_orte') AS s
         UNION SELECT 'Ballettprobenhaus') x))
WHERE slug = 'balletthaus';

DELETE FROM public.orte WHERE slug = 'ballettprobenhaus';

COMMIT;

-- Kontrolle: 0 | 1 | 1
SELECT
  (SELECT count(*) FROM public.orte WHERE slug = 'ballettprobenhaus')                                   AS alte_zeile,
  (SELECT count(*) FROM public.ort_weiterleitungen WHERE alter_slug = 'ballettprobenhaus')              AS weiterleitung,
  (SELECT count(*) FROM public.orte WHERE slug = 'balletthaus'
     AND extras->'spielstaette'->'event_orte' ? 'Ballettprobenhaus')                                    AS schreibweise_da;
