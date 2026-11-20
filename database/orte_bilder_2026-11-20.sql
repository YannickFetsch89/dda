-- Bilder der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.13, Schritt 4)
-- Erzeugt am 2026-11-20 von `python -m scraper.orte.ortsbilder --sql` aus data/spielstaetten/bilder.csv.
-- ERST nach dem Deploy der Bilddateien ausführen. Nur Zeilen mit vorhandener WebP-Datei. Wiederholbar.
-- erlaubnis = nachtraeglich: Die Freigabe der Rechteinhaber holt der Auftraggeber (Plan E4).

BEGIN;

UPDATE public.orte SET bild_url = '/ort-bilder/orte/capitol-theater.webp', bild_attribution = 'Joerg Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Capitol_Theater_in_Duesseldorf-Flingern-Sued,_von_Suedwesten.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Capitol_Theater_in_Duesseldorf-Flingern-Sued,_von_Suedwesten.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'capitol-theater' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/duesseldorfer-schauspielhaus.webp', bild_attribution = 'Daniel.widawski / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Schauspielhaus_D%C3%BCsseldorf.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Schauspielhaus_D%C3%BCsseldorf.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'duesseldorfer-schauspielhaus' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/filmmuseum-duesseldorf.webp', bild_attribution = 'Frank Vincentz / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Düsseldorf_-_Schulstraße_-_Filmmuseum_01_ies.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Düsseldorf_-_Schulstraße_-_Filmmuseum_01_ies.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'filmmuseum-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/kom-m-oedchen-duesseldorf.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Kom%C3%B6dchen,_Mutter-Ey-Stra%C3%9Fe,_D%C3%BCsseldorf,_August_2026.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Kom%C3%B6dchen,_Mutter-Ey-Stra%C3%9Fe,_D%C3%BCsseldorf,_August_2026.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'kom-m-oedchen-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/kunstpalast-duesseldorf.webp', bild_attribution = 'Raimond Spekking / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Museum_Kunstpalast_-_Ehrenhof_und_n%C3%B6rdlicher_%C3%9Cbergang_(8241-49).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Museum_Kunstpalast_-_Ehrenhof_und_n%C3%B6rdlicher_%C3%9Cbergang_(8241-49).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'kunstpalast-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/mitsubishi-electric-halle.webp', bild_attribution = 'Plumpaquatsch / Wikimedia Commons (Gemeinfrei (Public Domain))',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:MitsubishiElectricHalle.JPG", "bild_quelle": "https://commons.wikimedia.org/wiki/File:MitsubishiElectricHalle.JPG", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'mitsubishi-electric-halle' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/opernhaus-duesseldorf.webp', bild_attribution = 'Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Opernhaus_in_Duesseldorf-Stadtmitte,_von_Suedwesten.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Opernhaus_in_Duesseldorf-Stadtmitte,_von_Suedwesten.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'opernhaus-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/tanzhaus-nrw.webp', bild_attribution = 'Foto: Katja Illner / tanzhaus nrw, via Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Tanzhaus_nrw_2_klein_Foto_Katja_Illner.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Tanzhaus_nrw_2_klein_Foto_Katja_Illner.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'tanzhaus-nrw' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/tonhalle-duesseldorf.webp', bild_attribution = 'Christian A. Schröder (ChristianSchd) / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Tonhalle_Duesseldorf_Oederallee_Pempelfort_Duesseldorf_Germany_02.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Tonhalle_Duesseldorf_Oederallee_Pempelfort_Duesseldorf_Germany_02.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'tonhalle-duesseldorf' AND typ = 'spielstaette';

COMMIT;

-- Kontrolle: Ortsseiten mit eigenem Bild
SELECT count(*) FILTER (WHERE bild_url LIKE '/ort-bilder/orte/%') AS mit_bild FROM public.orte WHERE typ = 'spielstaette';
