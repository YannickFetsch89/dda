-- „Theater an der Kö“ vom Kö-Club lösen (Plan docs/plan-locations-2026-11-18.md, 3.2 und 3.4, Deploy-Punkt 2b)
-- Stand: 2026-11-19 · Erst ausführen, NACHDEM der Pipeline-Code mit EVENT_ORTE_AUSSCHLUSS deployt ist – sonst trägt
-- der alte scores_neu die Schreibweise beim nächsten Lauf wieder ein. Wiederholbar.

BEGIN;

-- 1) Schreibweise aus dem gespeicherten event_orte des Kö-Clubs nehmen
UPDATE public.orte
SET extras = jsonb_set(
  extras, '{club,event_orte}',
  COALESCE((SELECT jsonb_agg(s) FROM jsonb_array_elements_text(extras->'club'->'event_orte') s
            WHERE s <> 'Theater an der Kö'), '[]'::jsonb))
WHERE slug = 'koe-club-duesseldorf-friedrichstadt'
  AND extras->'club'->'event_orte' ? 'Theater an der Kö';

-- 2) Zuordnung der Events mit dieser Schreibweise und dieser Zeile ausdrücklich lösen (automatische Läufe
--    schreiben nie NULL – Plan 3.4)
UPDATE public.events
SET ort_id = NULL
WHERE ort = 'Theater an der Kö'
  AND ort_id = (SELECT id FROM public.orte WHERE slug = 'koe-club-duesseldorf-friedrichstadt');

COMMIT;

-- Kontrolle: beide Zahlen 0
SELECT
  (SELECT count(*) FROM public.orte WHERE slug = 'koe-club-duesseldorf-friedrichstadt'
     AND extras->'club'->'event_orte' ? 'Theater an der Kö')                                   AS noch_in_event_orte,
  (SELECT count(*) FROM public.events e JOIN public.orte o ON o.id = e.ort_id
     WHERE e.ort = 'Theater an der Kö' AND o.slug = 'koe-club-duesseldorf-friedrichstadt')      AS noch_zugeordnet;
