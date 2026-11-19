-- D'haus Central: richtige Adresse für die Events im Central (Plan docs/plan-locations-2026-11-18.md, Schritt 2)
-- Stand: 2026-11-19 · Im Supabase SQL-Editor ausführen. Wiederholbar.
--
-- Das Central ist eine eigene Spielstätte des Schauspielhauses am Hauptbahnhof (Worringer Straße 140, 40210,
-- visitduesseldorf.de „D'haus Central“). Der Schauspielhaus-Scraper hat bisher für alle Säle die Adresse am
-- Gustaf-Gründgens-Platz vergeben; ab dem nächsten Deploy setzt er die Central-Adresse selbst (adresse_fuer).
-- Stadtteil zur PLZ 40210 laut pipeline/stadtteil_mapper.py: Stadtmitte.

UPDATE public.events
SET adresse = 'Worringer Straße 140, 40210 Düsseldorf', stadtteil = 'Stadtmitte'
WHERE (ort ~* '^central( [12]| brücke)?$' OR ort ~* '\mim central\M')
  AND (adresse IS NULL OR adresse ILIKE 'Gustaf-Gründgens-Platz%' OR adresse ~* '^central [12],');

-- Kontrolle: erwartet nur noch die Central-Adresse (oder leer bei fremden Quellen)
SELECT ort, adresse, stadtteil, count(*) FROM public.events
WHERE ort ~* '^central( [12]| brücke)?$' OR ort ~* '\mim central\M'
GROUP BY 1, 2, 3 ORDER BY 4 DESC;
