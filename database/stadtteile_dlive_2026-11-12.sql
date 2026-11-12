-- Stadtteile der d.live-Hallen korrigieren – DiesDasDüsseldorf, 12.11.2026
-- Die Pipeline hat alle d.live-Spielstätten pauschal „Stockum“ zugeordnet. Richtig sind:
--   Mitsubishi Electric Halle (Siegburger Straße 15) → Oberbilk
--   PSD Bank Dome (früher ISS Dome)                   → Rath
--   Castello                                          → Reisholz
--   Merkur Spiel-Arena und Messe bleiben Stockum.
-- Andere d.live-Orte ohne eigene Regel (z. B. Rheinterrasse) verlieren den falschen Wert (NULL = ohne Zuordnung).
-- Die Pipeline (pipeline/stadtteil_mapper.py) ist korrigiert; dieses SQL bringt den Bestand nach.
-- Im Supabase-SQL-Editor als Ganzes ausführen.

BEGIN;

UPDATE public.events SET stadtteil = 'Oberbilk'
WHERE stadtteil = 'Stockum' AND ort ILIKE '%mitsubishi electric halle%';

UPDATE public.events SET stadtteil = 'Rath'
WHERE stadtteil = 'Stockum' AND (ort ILIKE '%psd bank dome%' OR ort ILIKE '%iss dome%');

UPDATE public.events SET stadtteil = 'Reisholz'
WHERE stadtteil = 'Stockum' AND ort ILIKE '%castello%';

UPDATE public.events SET stadtteil = NULL
WHERE stadtteil = 'Stockum' AND quelle_name = 'd-live'
  AND ort NOT ILIKE '%merkur spiel-arena%' AND ort NOT ILIKE '%messe%';

COMMIT;

-- Kontrolle: Was steht jetzt noch unter Stockum, und wo liegen die Hallen?
SELECT stadtteil, ort, COUNT(*) AS anzahl
FROM public.events
WHERE ort ILIKE '%mitsubishi%' OR ort ILIKE '%psd bank dome%' OR ort ILIKE '%castello%' OR stadtteil = 'Stockum'
GROUP BY stadtteil, ort
ORDER BY stadtteil, anzahl DESC;
