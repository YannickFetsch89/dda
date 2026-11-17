-- Weihnachtsmarkt-Guide: Freischalten und Abschalten (Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, Schritt 3)
-- Feste Datei, wiederholbar. Im Supabase SQL-Editor ausführen, NACH scraper/weihnachtsmaerkte/import_maerkte.py.
-- Voraussetzung: database/orte_typ_weihnachtsmarkt_2026-11-17.sql ist ausgeführt.
--
-- Anschalten: typ weihnachtsmarkt, bisher inaktiv, nicht ausgeschlossen, und mindestens eine Saison mit Zeitraum
--             (von, bis) UND Wochenzeiten (zeiten nicht leer). freigeschaltet_am wird nur beim ersten Mal gesetzt.
-- Abschalten: bisher aktiv und ausgeschlossen gesetzt (die URL leitet danach per 308 auf den Hub weiter).
-- Beide UPDATE filtern auf den alten aktiv-Wert, damit RETURNING nur Zeilen liefert, die sich wirklich ändern
-- (Slugs für IndexNow).

-- 1) Anschalten (freigeschaltet_am nur setzen, wenn leer – bei Wiederfreischaltung bleibt der erste Tag)
UPDATE public.orte o
SET aktiv = true,
    extras = CASE
      WHEN COALESCE(o.extras->'weihnachtsmarkt'->>'freigeschaltet_am', '') = ''
        THEN jsonb_set(o.extras, '{weihnachtsmarkt,freigeschaltet_am}',
                       to_jsonb(to_char(now() AT TIME ZONE 'Europe/Berlin', 'YYYY-MM-DD')))
      ELSE o.extras
    END,
    aktualisiert_am = now()
WHERE o.typ = 'weihnachtsmarkt'
  AND o.aktiv = false
  AND COALESCE(o.extras->'weihnachtsmarkt'->>'ausgeschlossen', '') = ''
  AND EXISTS (
    SELECT 1
    FROM jsonb_each(COALESCE(o.extras->'weihnachtsmarkt'->'saisons', '{}'::jsonb)) s
    WHERE COALESCE(s.value->>'von', '') <> ''
      AND COALESCE(s.value->>'bis', '') <> ''
      AND jsonb_typeof(s.value->'zeiten') = 'array'
      AND jsonb_array_length(s.value->'zeiten') > 0
  )
RETURNING o.slug, o.aktiv;

-- 2) Abschalten
UPDATE public.orte o
SET aktiv = false, aktualisiert_am = now()
WHERE o.typ = 'weihnachtsmarkt'
  AND o.aktiv = true
  AND COALESCE(o.extras->'weihnachtsmarkt'->>'ausgeschlossen', '') <> ''
RETURNING o.slug, o.aktiv;

-- 3) Kontrolle
SELECT slug, aktiv, extras->'weihnachtsmarkt'->>'freigeschaltet_am' AS freigeschaltet_am,
       extras->'weihnachtsmarkt'->>'ausgeschlossen' AS ausgeschlossen
FROM public.orte
WHERE typ = 'weihnachtsmarkt'
ORDER BY aktiv DESC, slug;
