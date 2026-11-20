-- FFT Düsseldorf: Spielstätte ist seit 2021 das KAP1 am Hauptbahnhof (Konrad-Adenauer-Platz 1, 40210 Düsseldorf,
-- Stadtmitte). Bisher standen FFT-Events als Pempelfort und meist ohne Adresse in der Datenbank (Befund 18.11.2026).
-- Betrifft nur FFT-Orte, nicht die alten Häuser JUTA/Kammerspiele. Erzeugt am 20.11.2026, führt der Auftraggeber aus.
BEGIN;

-- 1) Stadtteil: Pempelfort → Stadtmitte
UPDATE events SET stadtteil = 'Stadtmitte'
WHERE stadtteil = 'Pempelfort'
  AND (ort ILIKE 'FFT%' OR ort ILIKE '%Forum Freies Theater%')
  AND ort !~* 'juta|kammerspiele';

-- 2) Adresse nur, wo sie fehlt oder die alte Schreibweise mit „-KAP1“ steht
UPDATE events SET adresse = 'Konrad-Adenauer-Platz 1, 40210 Düsseldorf'
WHERE (ort ILIKE 'FFT%' OR ort ILIKE '%Forum Freies Theater%')
  AND ort !~* 'juta|kammerspiele'
  AND (adresse IS NULL OR adresse = 'Konrad-Adenauer-Platz 1, 40210 Düsseldorf-KAP1');

-- Kontrolle: alle FFT-Events stehen jetzt in Stadtmitte mit KAP1-Adresse
SELECT ort, adresse, stadtteil, count(*) FROM events
WHERE ort ILIKE 'FFT%' OR ort ILIKE '%Forum Freies Theater%'
GROUP BY 1, 2, 3 ORDER BY 4 DESC;

COMMIT;
