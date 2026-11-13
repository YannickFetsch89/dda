-- Spielplätze freischalten und abschalten (Plan docs/plan-spielplaetze-2026-11-12.md, Schritt 6).
-- Im Supabase SQL-Editor ausführen. Vorher die Vorschau ansehen: python -m scraper.spielplaetze.score vorschau
-- Dieselbe Bedingung steht als freischaltbar() in scraper/spielplaetze/score.py (Tests in tests/test_spielplaetze_score.py).
--
-- Anschalten: inaktive Zeilen ohne Ausschluss und ohne sperrenden Prüf-Code. name_unklar und kein_stadtteil sperren immer,
-- access_private und gruppe_gemischt nur, wenn sie nicht unter bestaetigt stehen. freigeschaltet_am bleibt der erste Tag.
-- Abschalten: aktive Zeilen mit gesetztem ausgeschlossen (die alte URL leitet danach weiter, Plan 5.5).
-- Beide UPDATE filtern auf den alten Wert von aktiv – RETURNING liefert nur Zeilen, deren aktiv sich ändert (Liste für IndexNow).
-- Kann jederzeit erneut laufen; ohne Änderungen kommen keine Zeilen zurück.

WITH anschalten AS (
  UPDATE public.orte
  SET aktiv = true,
      extras = jsonb_set(
        extras, '{spielplatz,freigeschaltet_am}',
        CASE WHEN extras->'spielplatz'->>'freigeschaltet_am' IS NULL
             THEN to_jsonb(to_char(now() AT TIME ZONE 'Europe/Berlin', 'YYYY-MM-DD'))
             ELSE extras->'spielplatz'->'freigeschaltet_am' END)
  WHERE typ = 'spielplatz'
    AND aktiv = false
    AND extras->'spielplatz'->>'ausgeschlossen' IS NULL
    AND NOT (COALESCE(extras->'spielplatz'->'pruefung', '[]'::jsonb) ?| array['name_unklar', 'kein_stadtteil'])
    AND NOT (COALESCE(extras->'spielplatz'->'pruefung', '[]'::jsonb) ? 'access_private'
             AND NOT COALESCE(extras->'spielplatz'->'bestaetigt', '[]'::jsonb) ? 'access_private')
    AND NOT (COALESCE(extras->'spielplatz'->'pruefung', '[]'::jsonb) ? 'gruppe_gemischt'
             AND NOT COALESCE(extras->'spielplatz'->'bestaetigt', '[]'::jsonb) ? 'gruppe_gemischt')
  RETURNING slug, aktiv
),
abschalten AS (
  UPDATE public.orte
  SET aktiv = false
  WHERE typ = 'spielplatz'
    AND aktiv = true
    AND extras->'spielplatz'->>'ausgeschlossen' IS NOT NULL
  RETURNING slug, aktiv
)
SELECT 'angeschaltet' AS aenderung, slug FROM anschalten
UNION ALL
SELECT 'abgeschaltet' AS aenderung, slug FROM abschalten
ORDER BY aenderung, slug;
