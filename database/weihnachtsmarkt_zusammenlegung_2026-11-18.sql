-- Schadow-Markt und Märchen-Markt sind derselbe Markt (Auftraggeber 18.11.2026):
-- Märchen-Markt bleibt (Slug maerchen-markt-stadtmitte, URL unverändert) und heißt jetzt „Märchen-Markt am Schadowplatz“,
-- der Schadow-Markt wird gelöscht. Seine alte URL leitet die Website dauerhaft auf den Märchen-Markt um
-- (web/lib/pfad-pruefung.ts WM_ZUSAMMENGELEGT) – deshalb erst NACH dem Deploy ausführen.
-- Stammdaten: data/weihnachtsmaerkte/maerkte.csv (dort schon zusammengelegt).

BEGIN;

UPDATE public.orte
SET name = 'Märchen-Markt am Schadowplatz',
    beschreibung = 'Auf dem Schadowplatz vor dem Kö-Bogen und entlang der Schadowstraße erzählen Schattenrisse auf den Hütten bekannte Märchen, teils mit bewegten Figuren. Rund 15.000 LEDs beleuchten den Platz, dazwischen gibt es Geschenkideen und Essensstände.',
    extras = jsonb_set(extras, '{weihnachtsmarkt,event_muster}', '["märchen-markt", "schadow-markt"]'::jsonb)
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'maerchen-markt'
RETURNING slug, name, extras->'weihnachtsmarkt'->'event_muster' AS event_muster;

DELETE FROM public.orte
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'schadow-markt'
RETURNING slug, name;

COMMIT;
