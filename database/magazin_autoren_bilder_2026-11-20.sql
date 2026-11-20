-- Magazin: Profilbilder und überarbeitete Kurzbeschreibungen der fünf redaktionellen Pseudonyme
-- (Plan docs/plan-redaktion-2026-11-19.md, Schritt 4; Überarbeitung 20.11.2026 nach rechtlicher Prüfung:
-- Texte machen deutlich, dass unter dem Namen die Redaktion schreibt – keine eigenständige reale Person).
-- Bilder liegen in web/public/magazin-autoren/<slug>.webp (800 × 800, illustriert, KI-generiert).
-- Erst ausführen, wenn der Deploy mit den Bildern live ist – sonst zeigt die Autorenseite kurz ein leeres Bild.
-- bild_ki bleibt TRUE: die Seite zeigt dann „KI-generierte Illustration“ am Bild.
-- Dieselben Texte stehen in database/magazin_rubriken_autoren_2026-11-19.sql (Wiederholung setzt nichts zurück).

BEGIN;

UPDATE public.magazin_autoren AS a
SET kurzbeschreibung = t.text, bild = '/magazin-autoren/' || a.slug || '.webp', bild_ki = TRUE
FROM (VALUES
  ('lisa-hartwig',
   'Unter dem Namen Lisa Hartwig sortiert unsere Redaktion, was in Düsseldorf ansteht: jeden Sonntag die kommende Woche im Überblick, zum Monatsende die stärksten Termine des nächsten Monats. Kurz, verlässlich und mit Blick fürs Wesentliche.'),
  ('dan-suttner',
   'Unter dem Namen Dan Suttner veröffentlicht unsere Redaktion Beiträge über Konzerte, Clubnächte und alles, was nach Sonnenuntergang in Düsseldorf passiert – von der kleinen Bühne bis zur großen Halle. Im Mittelpunkt: Welcher Abend passt zu wem?'),
  ('nathalie-kirchner',
   'Unter dem Namen Nathalie Kirchner erzählt unsere Redaktion vom Leben in Düsseldorf: Stadtteile, Saisonthemen wie Weihnachtsmärkte oder Karneval und alles, was in kein anderes Ressort passt. Neugierig, ruhig im Ton, nah an dem, was die Stadt gerade bewegt.'),
  ('laurenz-weigelt',
   'Unter dem Namen Laurenz Weigelt schreibt unsere Redaktion übers Essen und Trinken: Restaurants, Cafés, Foodmärkte, Tastings und Brauhauskultur in Düsseldorf. Im Mittelpunkt steht, was einen Ort ausmacht – ohne Sterne und ohne Werbesprache.'),
  ('amelie-glasner',
   'Unter dem Namen Amelie Glasner sammelt unsere Redaktion, was Familien in Düsseldorf unternehmen können: Kinderprogramm, Spielplätze, Ausflüge und Ideen für Regentage. Praktisch gedacht – mit Blick auf Alter, Wetter und Wege.')
) AS t (slug, text)
WHERE a.slug = t.slug;

COMMIT;

-- Kontrollabfrage – erwartet fünf Zeilen mit „ok“
SELECT slug, bild,
       CASE WHEN bild = '/magazin-autoren/' || slug || '.webp' AND bild_ki
                 AND kurzbeschreibung LIKE 'Unter dem Namen ' || name || ' %' THEN 'ok' ELSE 'FEHLER' END AS pruefung
FROM public.magazin_autoren
WHERE slug IN ('lisa-hartwig', 'dan-suttner', 'nathalie-kirchner', 'laurenz-weigelt', 'amelie-glasner')
ORDER BY slug;
