-- „Bunker“ mit „Bilker Bunker“ zusammenlegen (Plan docs/plan-locations-2026-11-18.md, 3.4 Zusammenlegen)
-- Stand: 2026-11-20 · Fund bei den Ortstexten: beide Zeilen sind dasselbe Haus (Aachener Straße 39; die Schleuse Zwei bleibt
-- nach Entscheidung vom 19.11. ein eigener Ort). Es bleibt slug „bilker-bunker“; „bunker“ leitet dorthin weiter. Wiederholbar.
-- Reihenfolge (Schutz-Trigger): Weiterleitung, ältere Weiterleitungen umhängen, Events verschieben, Schreibweisen
-- zusammenführen, alte Zeile löschen.

BEGIN;

INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'bunker', (SELECT id FROM public.orte WHERE slug = 'bilker-bunker'),
       'Zusammengelegt mit Bilker Bunker, gleiche Adresse (20.11.2026)'
WHERE EXISTS (SELECT 1 FROM public.orte WHERE slug = 'bunker')
ON CONFLICT (alter_slug) DO NOTHING;

UPDATE public.ort_weiterleitungen SET ziel_ort_id = (SELECT id FROM public.orte WHERE slug = 'bilker-bunker')
WHERE ziel_ort_id = (SELECT id FROM public.orte WHERE slug = 'bunker');

UPDATE public.events SET ort_id = (SELECT id FROM public.orte WHERE slug = 'bilker-bunker')
WHERE ort_id = (SELECT id FROM public.orte WHERE slug = 'bunker');

UPDATE public.orte
SET extras = jsonb_set(extras, '{spielstaette,event_orte}',
      (SELECT jsonb_agg(DISTINCT s ORDER BY s) FROM (
         SELECT jsonb_array_elements_text(extras->'spielstaette'->'event_orte') AS s
         UNION SELECT 'Bunker') x))
WHERE slug = 'bilker-bunker';

DELETE FROM public.orte WHERE slug = 'bunker';

COMMIT;

-- Kontrolle: 0 | 1 | 1
SELECT
  (SELECT count(*) FROM public.orte WHERE slug = 'bunker')                                   AS alte_zeile,
  (SELECT count(*) FROM public.ort_weiterleitungen WHERE alter_slug = 'bunker')              AS weiterleitung,
  (SELECT count(*) FROM public.orte WHERE slug = 'bilker-bunker'
     AND extras->'spielstaette'->'event_orte' ? 'Bunker')                                    AS schreibweise_da;
