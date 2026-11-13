-- Zeitpunkte für Highlight- und Top-Flaggen – DiesDasDüsseldorf, 13.11.2026
-- Plan docs/plan-empfehlungen-2026-11-13.md, Abschnitt 8:
--   Highlight der Woche gilt sieben Tage ab highlight_gesetzt_am, Top-Event des Monats bis zum Ende des Monats,
--   in dem top_gesetzt_am liegt (beides in Europe/Berlin). Danach ignoriert die Website die Flagge; der
--   Wahrheitswert bleibt (pipeline/publisher.py sortiert Instagram-Posts nach denselben Spalten).
--   Das Dashboard schreibt den Zeitpunkt beim Einschalten und leert ihn beim Ausschalten.
--
-- REIHENFOLGE: Kann vor oder nach dem Deploy laufen. Bis es ausgeführt ist, lädt die Website ohne die neuen
-- Spalten (web/lib/daten.ts, SPALTEN_VARIANTEN), und Highlight- und Top-Flaggen ohne Zeitpunkt gelten nicht.
-- Wird im Supabase-SQL-Editor ausgeführt.

ALTER TABLE public.events ADD COLUMN IF NOT EXISTS highlight_gesetzt_am TIMESTAMPTZ;
ALTER TABLE public.events ADD COLUMN IF NOT EXISTS top_gesetzt_am TIMESTAMPTZ;

-- Nachtrag: schon gesetzte Flaggen bekommen jetzt einen Zeitpunkt, sonst verschwänden sie beim Deploy
UPDATE public.events SET highlight_gesetzt_am = now()
 WHERE highlight_der_woche = TRUE AND highlight_gesetzt_am IS NULL;
UPDATE public.events SET top_gesetzt_am = now()
 WHERE top_event_des_monats = TRUE AND top_gesetzt_am IS NULL;

-- Kontrolle: Flaggen ohne Zeitpunkt (erwartet 0 und 0)
SELECT
    count(*) FILTER (WHERE highlight_der_woche AND highlight_gesetzt_am IS NULL) AS highlight_ohne_zeitpunkt,
    count(*) FILTER (WHERE top_event_des_monats AND top_gesetzt_am IS NULL)      AS top_ohne_zeitpunkt
FROM public.events;
