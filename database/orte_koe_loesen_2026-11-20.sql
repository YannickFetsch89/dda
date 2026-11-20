-- Fremde Orte an der Kö vom Kö-Club lösen (Plan docs/plan-locations-2026-11-18.md, 3.4 „Eine Zuordnung lösen“)
-- Fund 20.11.2026: Das Club-Profil hatte „KÖ Galerie Düsseldorf“, „Kö on Ice“, „Winterwelt Kö-on-Ice“ und
-- „Poccino am Kö-Bogen“ als Schreibweisen des Kö-Clubs gespeichert (Treffer über „Kö“ am Namensanfang).
-- Erst ausführen, NACHDEM der Pipeline-Code mit den neuen Einträgen in EVENT_ORTE_AUSSCHLUSS deployt ist – sonst
-- trägt scores_neu die Schreibweisen wieder ein. Wiederholbar.

BEGIN;

-- 1) Schreibweisen aus dem gespeicherten event_orte des Kö-Clubs nehmen
UPDATE public.orte
SET extras = jsonb_set(
  extras, '{club,event_orte}',
  COALESCE((SELECT jsonb_agg(s) FROM jsonb_array_elements_text(extras->'club'->'event_orte') s
            WHERE s NOT IN ('KÖ Galerie Düsseldorf', 'Kö on Ice', 'Winterwelt Kö-on-Ice', 'Poccino am Kö-Bogen')),
           '[]'::jsonb))
WHERE slug = 'koe-club-duesseldorf-friedrichstadt'
  AND extras->'club'->'event_orte' ?| ARRAY['KÖ Galerie Düsseldorf', 'Kö on Ice', 'Winterwelt Kö-on-Ice', 'Poccino am Kö-Bogen'];

-- 2) Zuordnung der Events mit diesen Schreibweisen und dieser Zeile ausdrücklich lösen (automatische Läufe
--    schreiben nie NULL – Plan 3.4)
UPDATE public.events
SET ort_id = NULL
WHERE ort IN ('KÖ Galerie Düsseldorf', 'Kö on Ice', 'Winterwelt Kö-on-Ice', 'Poccino am Kö-Bogen')
  AND ort_id = (SELECT id FROM public.orte WHERE slug = 'koe-club-duesseldorf-friedrichstadt');

COMMIT;

-- Kontrolle: beide Zahlen 0
SELECT
  (SELECT count(*) FROM public.orte WHERE slug = 'koe-club-duesseldorf-friedrichstadt'
     AND extras->'club'->'event_orte' ?| ARRAY['KÖ Galerie Düsseldorf', 'Kö on Ice', 'Winterwelt Kö-on-Ice', 'Poccino am Kö-Bogen']) AS noch_in_event_orte,
  (SELECT count(*) FROM public.events e JOIN public.orte o ON o.id = e.ort_id
     WHERE e.ort IN ('KÖ Galerie Düsseldorf', 'Kö on Ice', 'Winterwelt Kö-on-Ice', 'Poccino am Kö-Bogen')
       AND o.slug = 'koe-club-duesseldorf-friedrichstadt')                                                       AS noch_zugeordnet;
