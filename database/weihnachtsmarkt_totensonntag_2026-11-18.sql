-- Totensonntag (22.11.2026) geschlossen: Riesenrad „Wheel of Vision“ und Weihnachtszeit Nordstraße
-- (Auftraggeber 18.11.2026). Nach dem Deploy im Supabase SQL-Editor ausführen.
-- Stammdaten: data/weihnachtsmaerkte/saison-2026.csv (dort schon eingetragen). Setzt den Tag nur, wenn er noch fehlt.

BEGIN;

UPDATE public.orte
SET extras = jsonb_set(
  extras,
  '{weihnachtsmarkt,saisons,2026,sonder}',
  '[{"datum": "2026-11-22", "geschlossen": true}]'::jsonb
    || COALESCE(extras->'weihnachtsmarkt'->'saisons'->'2026'->'sonder', '[]'::jsonb)
)
WHERE typ = 'weihnachtsmarkt'
  AND extras->'weihnachtsmarkt'->>'schluessel' IN ('riesenrad', 'nordstrasse')
  AND extras->'weihnachtsmarkt'->'saisons' ? '2026'
  AND NOT COALESCE(extras->'weihnachtsmarkt'->'saisons'->'2026'->'sonder', '[]'::jsonb) @> '[{"datum": "2026-11-22"}]'::jsonb
RETURNING slug, extras->'weihnachtsmarkt'->'saisons'->'2026'->'sonder' AS sonder;

COMMIT;
