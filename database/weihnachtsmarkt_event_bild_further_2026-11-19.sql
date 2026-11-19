-- Foto für das Event „Further Nikolausmarkt“ (eigenes Foto des Auftraggebers, ohne Bildnachweis; 19.11.2026).
-- Erst NACH dem Deploy ausführen – die Datei web/public/ort-bilder/events/further-nikolausmarkt.webp muss live sein.
UPDATE public.events
SET bild_url = '/ort-bilder/events/further-nikolausmarkt.webp'
WHERE titel = 'Further Nikolausmarkt'
  AND datum = '2026-12-03'
  AND quelle_url = 'https://www.neuss.de/news/2026/11/17/neusser-weihnachtsmaerkte-2026'
RETURNING id, slug, bild_url;
