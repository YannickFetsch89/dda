-- Anpassungen Weihnachtsmarkt-Guide (Auftraggeber 18.11.2026) – nach dem Deploy im Supabase SQL-Editor ausführen.
-- Stammdaten: data/weihnachtsmaerkte/maerkte.csv (dort schon geändert). Slugs/URLs bleiben unverändert.

BEGIN;

-- Gruppe Innenstadt umbenennen
UPDATE public.orte SET name = 'Düsseldorfer Weihnachtsmärkte in der Innenstadt'
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'innenstadt'
RETURNING slug, name;

-- The Winter Village: Badge „Kunsthandwerk“
UPDATE public.orte SET extras = jsonb_set(extras, '{weihnachtsmarkt,art}', '["kunsthandwerk"]'::jsonb)
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'winter-village'
RETURNING slug, extras->'weihnachtsmarkt'->'art' AS art;

-- Top 5 neu: 1 Innenstadt, 2 Schloss Benrath, 3 Areal Böhler, 4 Weihnachtspromenade, 5 Nordstraße
UPDATE public.orte o SET extras = jsonb_set(o.extras, '{weihnachtsmarkt,top5_rang}', to_jsonb(n.rang))
FROM (VALUES ('innenstadt', 1), ('schloss-benrath', 2), ('areal-boehler', 3), ('weihnachtspromenade', 4), ('nordstrasse', 5)) AS n(schluessel, rang)
WHERE o.typ = 'weihnachtsmarkt' AND o.extras->'weihnachtsmarkt'->>'schluessel' = n.schluessel
RETURNING o.slug, o.extras->'weihnachtsmarkt'->'top5_rang' AS top5_rang;

COMMIT;
