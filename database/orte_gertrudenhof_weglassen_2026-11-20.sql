-- Ortsseite „Erlebnisbauernhof Gertrudenhof“ entfernen: liegt in Hürth bei Köln, außerhalb von Düsseldorf, Neuss,
-- Ratingen (E3; Auftraggeber 20.11.2026). Plan docs/plan-locations-2026-11-18.md, 3.4.
-- Stand: 2026-11-20 · Im Supabase SQL-Editor ausführen. Wiederholbar.
-- Die Seite war nie öffentlich (Schritt 3 ist nicht live); der Schutz-Trigger verlangt trotzdem eine Weiterleitung.
-- Ziel leer → der Proxy leitet später auf /orte. Die Events löscht database/gebiet_bereinigung_2026-11-20.sql.

BEGIN;

INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'erlebnisbauernhof-gertrudenhof', NULL, 'Außerhalb des Gebiets (Hürth), Auftraggeber 20.11.2026'
WHERE EXISTS (SELECT 1 FROM public.orte WHERE slug = 'erlebnisbauernhof-gertrudenhof')
ON CONFLICT (alter_slug) DO NOTHING;

UPDATE public.events SET ort_id = NULL
WHERE ort_id = (SELECT id FROM public.orte WHERE slug = 'erlebnisbauernhof-gertrudenhof');

DELETE FROM public.orte WHERE slug = 'erlebnisbauernhof-gertrudenhof';

COMMIT;

-- Kontrolle: Zeile weg (0), Weiterleitung da (1)
SELECT
  (SELECT count(*) FROM public.orte WHERE slug = 'erlebnisbauernhof-gertrudenhof')                    AS zeile,
  (SELECT count(*) FROM public.ort_weiterleitungen WHERE alter_slug = 'erlebnisbauernhof-gertrudenhof') AS weiterleitung;
