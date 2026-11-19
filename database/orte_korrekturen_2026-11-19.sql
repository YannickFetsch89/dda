-- Korrekturen nach der Cursor-Prüfung der Umsetzung (Plan docs/plan-locations-2026-11-18.md, 3.4 Zusammenlegen/Umbenennen)
-- Stand: 2026-11-19 · Im Supabase SQL-Editor ausführen. Wiederholbar (jeder Teil prüft, ob noch etwas zu tun ist).
--
-- 1) Bambi: „Bambi“ und „Bambi Filmstudio“ sind dasselbe Kino (Klosterstraße 78, gleiche place_id). Es bleibt slug
--    „bambi“ mit dem Namen „Bambi Filmstudio“; „bambi-filmstudio“ wird zusammengelegt.
-- 2) Holocafé: Die Schreibweise „Holocafé Düsseldorf“ (Am Wehrhahn 41) stammt nur aus Meetups im April 2026, seit
--    Oktober 2026 trifft sich dieselbe Gruppe an der Immermannstraße 7 – das Café ist umgezogen. „holocafe-am-wehrhahn“
--    wird mit „holocafe“ zusammengelegt. Damit gibt es auch keinen doppelten Zuordnungsschlüssel mehr.
-- 3) Flow: Name und Slug waren die Adresse. Neuer Name „Flow“, neuer Slug „flow“, alter Slug leitet weiter.
-- Reihenfolge je Zusammenlegung (Plan 3.4): Weiterleitung, ältere Weiterleitungen umhängen, Events verschieben,
-- Schreibweisen zusammenführen, alte Zeile löschen. Der Schutz-Trigger bricht ab, wenn die Reihenfolge nicht stimmt.

BEGIN;

-- ── 1) Bambi ────────────────────────────────────────────────────────────────────────────────────────────────────
INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'bambi-filmstudio', (SELECT id FROM public.orte WHERE slug = 'bambi'), 'Zusammengelegt mit Bambi (19.11.2026)'
WHERE EXISTS (SELECT 1 FROM public.orte WHERE slug = 'bambi-filmstudio')
ON CONFLICT (alter_slug) DO NOTHING;

UPDATE public.ort_weiterleitungen SET ziel_ort_id = (SELECT id FROM public.orte WHERE slug = 'bambi')
WHERE ziel_ort_id = (SELECT id FROM public.orte WHERE slug = 'bambi-filmstudio');

UPDATE public.events SET ort_id = (SELECT id FROM public.orte WHERE slug = 'bambi')
WHERE ort_id = (SELECT id FROM public.orte WHERE slug = 'bambi-filmstudio');

UPDATE public.orte
SET name = 'Bambi Filmstudio',
    extras = jsonb_set(extras, '{spielstaette,event_orte}',
      (SELECT jsonb_agg(DISTINCT s ORDER BY s) FROM (
         SELECT jsonb_array_elements_text(extras->'spielstaette'->'event_orte') AS s
         UNION SELECT 'Bambi Filmstudio') x))
WHERE slug = 'bambi';

DELETE FROM public.orte WHERE slug = 'bambi-filmstudio';

-- ── 2) Holocafé ─────────────────────────────────────────────────────────────────────────────────────────────────
INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'holocafe-am-wehrhahn', (SELECT id FROM public.orte WHERE slug = 'holocafe'),
       'Umgezogen: Am Wehrhahn 41 → Immermannstraße 7, zusammengelegt (19.11.2026)'
WHERE EXISTS (SELECT 1 FROM public.orte WHERE slug = 'holocafe-am-wehrhahn')
ON CONFLICT (alter_slug) DO NOTHING;

UPDATE public.ort_weiterleitungen SET ziel_ort_id = (SELECT id FROM public.orte WHERE slug = 'holocafe')
WHERE ziel_ort_id = (SELECT id FROM public.orte WHERE slug = 'holocafe-am-wehrhahn');

UPDATE public.events SET ort_id = (SELECT id FROM public.orte WHERE slug = 'holocafe')
WHERE ort_id = (SELECT id FROM public.orte WHERE slug = 'holocafe-am-wehrhahn');

UPDATE public.orte
SET extras = jsonb_set(extras, '{spielstaette,event_orte}',
      (SELECT jsonb_agg(DISTINCT s ORDER BY s) FROM (
         SELECT jsonb_array_elements_text(extras->'spielstaette'->'event_orte') AS s
         UNION SELECT 'Holocafé Düsseldorf') x))
WHERE slug = 'holocafe';

DELETE FROM public.orte WHERE slug = 'holocafe-am-wehrhahn';

-- ── 3) Flow ─────────────────────────────────────────────────────────────────────────────────────────────────────
-- Erst die Weiterleitung vom alten Slug auf dieselbe Zeile (die UUID bleibt), dann Name und Slug ändern.
INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'flow-mertensgasse-2-40213-duesseldorf', id, 'Umbenannt in „Flow“ (19.11.2026)'
FROM public.orte WHERE slug = 'flow-mertensgasse-2-40213-duesseldorf'
ON CONFLICT (alter_slug) DO NOTHING;

UPDATE public.orte SET name = 'Flow', slug = 'flow'
WHERE slug = 'flow-mertensgasse-2-40213-duesseldorf'
  AND NOT EXISTS (SELECT 1 FROM public.orte WHERE slug = 'flow');

COMMIT;

-- Kontrolle: alte Zeilen weg (0), Bambi und Holocafe mit beiden Schreibweisen, Flow umbenannt, drei Weiterleitungen
SELECT
  (SELECT count(*) FROM public.orte WHERE slug IN ('bambi-filmstudio', 'holocafe-am-wehrhahn',
                                                   'flow-mertensgasse-2-40213-duesseldorf'))     AS alte_zeilen,
  (SELECT extras->'spielstaette'->'event_orte' FROM public.orte WHERE slug = 'bambi')            AS bambi_schreibweisen,
  (SELECT extras->'spielstaette'->'event_orte' FROM public.orte WHERE slug = 'holocafe')         AS holocafe_schreibweisen,
  (SELECT name FROM public.orte WHERE slug = 'flow')                                             AS flow_name,
  (SELECT count(*) FROM public.ort_weiterleitungen WHERE alter_slug IN ('bambi-filmstudio', 'holocafe-am-wehrhahn',
                                                   'flow-mertensgasse-2-40213-duesseldorf'))     AS weiterleitungen;
