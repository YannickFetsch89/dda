-- Oper und Schauspielhaus dauerhaft in Stadtmitte (Entscheidung des Auftraggebers vom 20.11.2026).
-- Bisher: Events als Pempelfort, die Orte-Tabelle hatte Schauspielhaus = Pempelfort und Opernhaus = Altstadt.
-- Code: pipeline/stadtteil_mapper.py (QUELLE_STADTTEIL, VENUE_STADTTEIL). Junges Schauspiel und Balletthaus
-- (eigene Adressen) sind nicht betroffen. Erzeugt am 20.11.2026, führt der Auftraggeber aus.
BEGIN;

-- 1) Events: Opernhaus und Schauspielhaus (alle Säle, alle Quellen), nicht Junges Schauspiel/Balletthaus
UPDATE events SET stadtteil = 'Stadtmitte'
WHERE stadtteil IS DISTINCT FROM 'Stadtmitte'
  AND (
        ort ILIKE 'Opernhaus Düsseldorf%'
     OR ort ILIKE 'Deutsche Oper am Rhein%'
     OR ort ILIKE 'Düsseldorfer Schauspielhaus%'
     OR ort ILIKE 'Schauspielhaus –%'
     OR ort ILIKE 'Schauspielhaus -%'
     OR (quelle_name = 'Deutsche Oper am Rhein' AND ort NOT ILIKE '%Balletthaus%')
     OR (quelle_name = 'Düsseldorfer Schauspielhaus' AND ort NOT ILIKE '%Junges%')
      )
  AND ort NOT ILIKE '%Duisburg%';

-- 2) Orte-Tabelle (Ortsseiten): Opernhaus, Schauspielhaus und ihre Säle, Schillings im Schauspielhaus
UPDATE orte SET stadtteil = 'Stadtmitte'
WHERE stadtteil IS DISTINCT FROM 'Stadtmitte'
  AND (name ILIKE 'Opernhaus Düsseldorf%' OR name ILIKE 'Düsseldorfer Schauspielhaus%'
       OR name = 'Schillings im Schauspielhaus');

-- Kontrolle
SELECT 'events' AS tabelle, ort, stadtteil, count(*) FROM events
WHERE ort ILIKE 'Opernhaus Düsseldorf%' OR ort ILIKE 'Düsseldorfer Schauspielhaus%' OR ort ILIKE 'Deutsche Oper am Rhein%'
GROUP BY 2, 3
UNION ALL
SELECT 'orte', name, stadtteil, 1 FROM orte
WHERE name ILIKE 'Opernhaus Düsseldorf%' OR name ILIKE 'Düsseldorfer Schauspielhaus%' OR name = 'Schillings im Schauspielhaus'
ORDER BY 1, 4 DESC;

COMMIT;
