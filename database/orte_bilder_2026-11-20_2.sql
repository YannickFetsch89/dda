-- Bilder der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.13, Schritt 4)
-- Erzeugt am 2026-11-20 von `python -m scraper.orte.ortsbilder --sql` aus data/spielstaetten/bilder.csv.
-- ERST nach dem Deploy der Bilddateien ausführen. Nur Zeilen mit vorhandener WebP-Datei. Wiederholbar.
-- erlaubnis = nachtraeglich: Die Freigabe der Rechteinhaber holt der Auftraggeber (Plan E4).

BEGIN;

UPDATE public.orte SET bild_url = '/ort-bilder/orte/alter-bahnhof-oberkassel.webp', bild_attribution = 'Tischgenosse / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Alter_Bahnhof_Oberkassel_2018.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Alter_Bahnhof_Oberkassel_2018.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'alter-bahnhof-oberkassel' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/aquazoo-loebbecke-museum.webp', bild_attribution = 'Stefan3345 / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Au%C3%9Fenansicht_PS_(82).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Au%C3%9Fenansicht_PS_(82).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'aquazoo-loebbecke-museum' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/areal-boehler.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Areal_B%C3%B6hler,_D%C3%BCsseldorf,_April_2025_(2).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Areal_B%C3%B6hler,_D%C3%BCsseldorf,_April_2025_(2).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'areal-boehler' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/balletthaus.webp', bild_attribution = 'Deutsche Oper am Rhein',
  extras = extras || '{"bild_link": "https://www.operamrhein.de/", "bild_quelle": "https://www.operamrhein.de/en/your-visit/balletthaus/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'balletthaus' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/bambi.webp', bild_attribution = 'Bambi Filmstudio / Düsseldorfer Filmkunstkinos',
  extras = extras || '{"bild_link": "https://filmkunstkinos.de/kinos/bambi/", "bild_quelle": "https://filmkunstkinos.de/kinos/bambi/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'bambi' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/berger-kirche.webp', bild_attribution = 'Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Berger_Kirche_in_Duesseldorf-Altstadt,_von_Westen.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Berger_Kirche_in_Duesseldorf-Altstadt,_von_Westen.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'berger-kirche' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/bilker-bunker.webp', bild_attribution = 'Jula2812 / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Bilker_Bunker,_Aachener_Stra%C3%9Fe_39,_D%C3%BCsseldorf-Bilk.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Bilker_Bunker,_Aachener_Stra%C3%9Fe_39,_D%C3%BCsseldorf-Bilk.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'bilker-bunker' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/buergerhaus-reisholz.webp', bild_attribution = 'Bürgerhaus Reisholz',
  extras = extras || '{"bild_link": "https://www.duesseldorf.de/buergerhaeuser/reisholz", "bild_quelle": "https://www.duesseldorf.de/buergerhaeuser/reisholz", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'buergerhaus-reisholz' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/buergerhaus-salzmannbau.webp', bild_attribution = 'Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Salzmannbau_in_Duesseldorf-Bilk,_von_Sueden.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Salzmannbau_in_Duesseldorf-Bilk,_von_Sueden.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'buergerhaus-salzmannbau' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/cageball-duesseldorf.webp', bild_attribution = 'Cageball Düsseldorf',
  extras = extras || '{"bild_link": "https://www.cageball-duesseldorf.de/", "bild_quelle": "https://www.cageball-duesseldorf.de/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'cageball-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/capitol-theater.webp', bild_attribution = 'Joerg Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Capitol_Theater_in_Duesseldorf-Flingern-Sued,_von_Suedwesten.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Capitol_Theater_in_Duesseldorf-Flingern-Sued,_von_Suedwesten.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'capitol-theater' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/castello-duesseldorf.webp', bild_attribution = 'Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Burg-Waechter_Castello_in_Duesseldorf-Reisholz,_von_Suedwesten.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Burg-Waechter_Castello_in_Duesseldorf-Reisholz,_von_Suedwesten.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'castello-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/cinema.webp', bild_attribution = 'Filmkunstkinos Düsseldorf',
  extras = extras || '{"bild_link": "https://filmkunstkinos.de/kinos/cinema/", "bild_quelle": "https://filmkunstkinos.de/kinos/cinema/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'cinema' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/classic-remise-duesseldorf.webp', bild_attribution = 'Paintdog / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:2025-09-06_09-27-26_Eingang_zur_Classic_Remise_in_D%C3%BCsseldorf.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:2025-09-06_09-27-26_Eingang_zur_Classic_Remise_in_D%C3%BCsseldorf.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'classic-remise-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/cuvee.webp', bild_attribution = 'Cuvée Flingern',
  extras = extras || '{"bild_link": "https://cuvee-flingern.de/", "bild_quelle": "https://cuvee-flingern.de/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'cuvee' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/das-rheinische-landestheater.webp', bild_attribution = 'Michael Reschke / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Neuss,_Rheinisches_Landestheater_2008.JPG", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Neuss,_Rheinisches_Landestheater_2008.JPG", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'das-rheinische-landestheater' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/djk-tusa-06-e-v.webp', bild_attribution = 'DJK TuSA 06 Düsseldorf',
  extras = extras || '{"bild_link": "https://www.tusa06.de", "bild_quelle": "https://www.tusa06.de/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'djk-tusa-06-e-v' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/duesseldorfer-marionetten-theater.webp', bild_attribution = 'Düsseldorfer Marionetten-Theater / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Duesseldorfer_Marionetten-Theater_Toreingang_Palais_Wittgenstein_mit_Theaterschild_(Duesseldorfer_Marionetten-Theater).JPG", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Duesseldorfer_Marionetten-Theater_Toreingang_Palais_Wittgenstein_mit_Theaterschild_(Duesseldorfer_Marionetten-Theater).JPG", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'duesseldorfer-marionetten-theater' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/duesseldorfer-schauspielhaus.webp', bild_attribution = 'Daniel.widawski / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Schauspielhaus_D%C3%BCsseldorf.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Schauspielhaus_D%C3%BCsseldorf.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'duesseldorfer-schauspielhaus' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/eko-haus-der-japanischen-kultur.webp', bild_attribution = 'Frank Vincentz / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_Br%C3%BCggener_Weg_-_EKO-Haus_01_ies.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_Br%C3%BCggener_Weg_-_EKO-Haus_01_ies.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'eko-haus-der-japanischen-kultur' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/em-poeoetzke.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Em_P%C3%B6%C3%B6tzke,_D%C3%BCsseldorf,_Januar_2026.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Em_P%C3%B6%C3%B6tzke,_D%C3%BCsseldorf,_Januar_2026.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'em-poeoetzke' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/fft-duesseldorf.webp', bild_attribution = 'Kürschner / Wikimedia Commons (Public Domain)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Konrad-Adenauer-Platz_1,_D%C3%BCsseldorf_Mai_2023_(1).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Konrad-Adenauer-Platz_1,_D%C3%BCsseldorf_Mai_2023_(1).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'fft-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/filmmuseum-duesseldorf.webp', bild_attribution = 'Frank Vincentz / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Düsseldorf_-_Schulstraße_-_Filmmuseum_01_ies.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Düsseldorf_-_Schulstraße_-_Filmmuseum_01_ies.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'filmmuseum-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/gare-du-neuss.webp', bild_attribution = 'Gare du Neuss',
  extras = extras || '{"bild_link": "https://www.gare-du-neuss.de", "bild_quelle": "https://eventlocation.gareduneuss.de/location/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'gare-du-neuss' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/gerhart-hauptmann-haus.webp', bild_attribution = 'Derbrauni / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Gerhart-Hauptmann-Haus_D%C3%BCDo_total.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Gerhart-Hauptmann-Haus_D%C3%BCDo_total.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'gerhart-hauptmann-haus' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/goethe-museum.webp', bild_attribution = 'Jörg Wiegels / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Schloss_Jaegerhof_in_Duesseldorf-Pempelfort,_von_Westen.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Schloss_Jaegerhof_in_Duesseldorf-Pempelfort,_von_Westen.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'goethe-museum' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/hamtorkrug.webp', bild_attribution = 'Käthe u. Bernd Limburg / Wikimedia Commons (CC BY-SA 3.0 DE)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:(092)_1-197_Wohn-_u._Gesch%C3%A4ftshaus,_B%C3%BCttger_Stra%C3%9Fe_3_(Neuss).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:(092)_1-197_Wohn-_u._Gesch%C3%A4ftshaus,_B%C3%BCttger_Stra%C3%9Fe_3_(Neuss).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'hamtorkrug' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/haus-der-universitaet.webp', bild_attribution = 'Jörg Wiegels / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Gebaeude_Schadowplatz_14_in_Duesseldorf-Stadtmitte,_von_Westen.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Gebaeude_Schadowplatz_14_in_Duesseldorf-Stadtmitte,_von_Westen.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'haus-der-universitaet' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/haus-spilles.webp', bild_attribution = 'noebse / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Haus_Spilles_D%C3%BCsseldorf_Benrath.JPG", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Haus_Spilles_D%C3%BCsseldorf_Benrath.JPG", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'haus-spilles' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/heine-haus-literaturhaus-duesseldorf.webp', bild_attribution = 'Katja Stuke / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Heine_Haus_D%C3%BCsseldorf_2020.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Heine_Haus_D%C3%BCsseldorf_2020.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'heine-haus-literaturhaus-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/hetjens-deutsches-keramikmuseum.webp', bild_attribution = 'Frank Vincentz / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_Schulstra%C3%9Fe_-_Hetjens-Museum_01_ies.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_Schulstra%C3%9Fe_-_Hetjens-Museum_01_ies.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'hetjens-deutsches-keramikmuseum' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/ihk-duesseldorf.webp', bild_attribution = 'Kalligraf / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_Ernst-Schneider-Platz_1.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_Ernst-Schneider-Platz_1.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'ihk-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/jazz-schmiede.webp', bild_attribution = 'Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Jazz-Schmiede_in_Duesseldorf-Bilk,_von_Sueden.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Jazz-Schmiede_in_Duesseldorf-Bilk,_von_Sueden.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'jazz-schmiede' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/jugendkirche.webp', bild_attribution = 'Taurus65 / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Christuskirche_D%C3%BCsseldorf-Oberbilk.JPG", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Christuskirche_D%C3%BCsseldorf-Oberbilk.JPG", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'jugendkirche' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/kit.webp', bild_attribution = 'Frank Vincentz / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_Mannesmannufer_-_KIT_01_ies.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_Mannesmannufer_-_KIT_01_ies.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'kit' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/kom-m-oedchen-duesseldorf.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Kom%C3%B6dchen,_Mutter-Ey-Stra%C3%9Fe,_D%C3%BCsseldorf,_August_2026.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Kom%C3%B6dchen,_Mutter-Ey-Stra%C3%9Fe,_D%C3%BCsseldorf,_August_2026.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'kom-m-oedchen-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/kulturhaus-sued-freizeitstaette-garath.webp', bild_attribution = 'Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Gebaeude_Fritz-Erler-Strasse_21_in_Duesseldorf-Garath,_von_Sueden.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Gebaeude_Fritz-Erler-Strasse_21_in_Duesseldorf-Garath,_von_Sueden.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'kulturhaus-sued-freizeitstaette-garath' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/kunsthalle-duesseldorf.webp', bild_attribution = 'Raimond Spekking / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Au%C3%9Fenansicht_Kunsthalle_D%C3%BCsseldorf_2026-0726.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Au%C3%9Fenansicht_Kunsthalle_D%C3%BCsseldorf_2026-0726.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'kunsthalle-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/kunstpalast-duesseldorf.webp', bild_attribution = 'Raimond Spekking / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Museum_Kunstpalast_-_Ehrenhof_und_n%C3%B6rdlicher_%C3%9Cbergang_(8241-49).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Museum_Kunstpalast_-_Ehrenhof_und_n%C3%B6rdlicher_%C3%9Cbergang_(8241-49).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'kunstpalast-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/kunstsammlung-nrw.webp', bild_attribution = 'Fred Romero / Wikimedia Commons (CC BY 2.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_K21_St%C3%A4ndehaus,_Kunstsammlung_Nordrhein-Westfalen.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_K21_St%C3%A4ndehaus,_Kunstsammlung_Nordrhein-Westfalen.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'kunstsammlung-nrw' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/landtag-nrw.webp', bild_attribution = 'Островский Александр, Киев / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:NRW,_D%C3%BCsseldorf,_Rheinturm_-_view_to_Landtag.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:NRW,_D%C3%BCsseldorf,_Rheinturm_-_view_to_Landtag.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'landtag-nrw' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/maison-zen-studio-fuer-mentale-gesundheit.webp', bild_attribution = 'Maison Zen',
  extras = extras || '{"bild_link": "https://www.maisonzen.de", "bild_quelle": "https://www.maisonzen.de/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'maison-zen-studio-fuer-mentale-gesundheit' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/maxhaus.webp', bild_attribution = 'Frank Vincentz / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_Schulstra%C3%9Fe_-_Maxhaus_01_ies.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_Schulstra%C3%9Fe_-_Maxhaus_01_ies.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'maxhaus' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/merkur-spiel-arena.webp', bild_attribution = 'Peter Weihs / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Merkur-Spiel-Arena_(D%C3%BCsseldorf,_GER)_2021.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Merkur-Spiel-Arena_(D%C3%BCsseldorf,_GER)_2021.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'merkur-spiel-arena' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/messe-duesseldorf.webp', bild_attribution = 'Messe Düsseldorf GmbH / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Messe_D%C3%BCsseldorf_Halle_6.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Messe_D%C3%BCsseldorf_Halle_6.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'messe-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/metropol-kino.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Metropol_Theater,_Brunnenstra%C3%9Fe,_D%C3%BCsseldorf,_August_2026_(01).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Metropol_Theater,_Brunnenstra%C3%9Fe,_D%C3%BCsseldorf,_August_2026_(01).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'metropol-kino' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/mitsubishi-electric-halle.webp', bild_attribution = 'Plumpaquatsch / Wikimedia Commons (Gemeinfrei (Public Domain))',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:MitsubishiElectricHalle.JPG", "bild_quelle": "https://commons.wikimedia.org/wiki/File:MitsubishiElectricHalle.JPG", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'mitsubishi-electric-halle' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/ms-rheinfantasie.webp', bild_attribution = 'Rolf Heinrich, Köln / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:RheinFantasie_(ship,_2011)_102.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:RheinFantasie_(ship,_2011)_102.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'ms-rheinfantasie' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/nrw-akademie-der-wissenschaften-und-der-kuenste.webp', bild_attribution = 'Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Karl-Arnold-Haus_in_Duesseldorf-Unterbilk,_von_Sueden.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Karl-Arnold-Haus_in_Duesseldorf-Unterbilk,_von_Sueden.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'nrw-akademie-der-wissenschaften-und-der-kuenste' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/nrw-forum.webp', bild_attribution = 'Raimond Spekking / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:NRW-Forum,_Ehrenhof,_D%C3%BCsseldorf-0790.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:NRW-Forum,_Ehrenhof,_D%C3%BCsseldorf-0790.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'nrw-forum' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/oberschlesisches-landesmuseum.webp', bild_attribution = 'Lena Ciochon / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Oberschlesisches_Landesmuseum_Front.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Oberschlesisches_Landesmuseum_Front.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'oberschlesisches-landesmuseum' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/opernhaus-duesseldorf.webp', bild_attribution = 'Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Opernhaus_in_Duesseldorf-Stadtmitte,_von_Suedwesten.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Opernhaus_in_Duesseldorf-Stadtmitte,_von_Suedwesten.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'opernhaus-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/palais-wittgenstein.webp', bild_attribution = 'Velopilger / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Palais_Wittgenstein_(D%C3%BCsseldorf)_foto-2.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Palais_Wittgenstein_(D%C3%BCsseldorf)_foto-2.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'palais-wittgenstein' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/psd-bank-dome.webp', bild_attribution = 'M 93 / Wikimedia Commons (CC BY-SA 3.0 DE)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:ISS_DOME_%E2%80%93_Nordansicht,_21._Juli_2012,_D%C3%BCsseldorf.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:ISS_DOME_%E2%80%93_Nordansicht,_21._Juli_2012,_D%C3%BCsseldorf.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'psd-bank-dome' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/raketenstation-hombroich.webp', bild_attribution = 'Anil Öztas / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Neuss_(DE),_Raketenstation_Hombroich,_Turmgeb%C3%A4ude_--_2014_--_7387.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Neuss_(DE),_Raketenstation_Hombroich,_Turmgeb%C3%A4ude_--_2014_--_7387.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'raketenstation-hombroich' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/rathaus-duesseldorf.webp', bild_attribution = 'Frank Vincentz / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_Marktplatz_-_Rathaus_01_ies.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf_-_Marktplatz_-_Rathaus_01_ies.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'rathaus-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/reinraum-e-v.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Reinraum_e._V.,_D%C3%BCsseldorf,_April_2025_(3).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Reinraum_e._V.,_D%C3%BCsseldorf,_April_2025_(3).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'reinraum-e-v' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/rheinturm-duesseldorf.webp', bild_attribution = 'Taxiarchos228 / Wikimedia Commons (FAL (Free Art License))',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Rheinturm_-_Gesamtansicht_vom_Medienhafen.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Rheinturm_-_Gesamtansicht_vom_Medienhafen.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'rheinturm-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/robert-schumann-hochschule-duesseldorf.webp', bild_attribution = 'Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Robert-Schumann-Hochschule_in_Duesseldorf-Golzheim,_von_Osten.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Robert-Schumann-Hochschule_in_Duesseldorf-Golzheim,_von_Osten.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'robert-schumann-hochschule-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/robert-schumann-saal.webp', bild_attribution = 'Andreas Grieger',
  extras = extras || '{"bild_link": "https://www.kunstpalast.de/", "bild_quelle": "https://www.kunstpalast.de/en/corporate-events/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'robert-schumann-saal' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/ruby-leni-hotel-bar.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Ruby,_Jahnstra%C3%9Fe_3,_D%C3%BCsseldorf,_Oktober_2025.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Ruby,_Jahnstra%C3%9Fe_3,_D%C3%BCsseldorf,_Oktober_2025.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'ruby-leni-hotel-bar' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/sammlung-philara.webp', bild_attribution = 'Stefan Müller / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Sammlung_Philara_D%C3%BCsseldorf.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Sammlung_Philara_D%C3%BCsseldorf.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'sammlung-philara' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/savoy-theater.webp', bild_attribution = 'Marek Gehrmann / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Duesseldorf_Savoy_Theater.JPG", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Duesseldorf_Savoy_Theater.JPG", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'savoy-theater' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/schloss-benrath.webp', bild_attribution = 'A.Savin / Wikimedia Commons (CC BY-SA 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Schloss_Benrath_Jan2012.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Schloss_Benrath_Jan2012.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'schloss-benrath' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/sponk-keramik-workshop.webp', bild_attribution = 'Sponk Keramik',
  extras = extras || '{"bild_link": "https://www.sponkkeramik.de", "bild_quelle": "https://www.sponkkeramik.de/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'sponk-keramik-workshop' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/stadtbuecherei-benrath.webp', bild_attribution = 'Hermann Luyken / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:2015.09.28.083352_Orangerie_Schlo%C3%9F_Benrath_D%C3%BCsseldorf.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:2015.09.28.083352_Orangerie_Schlo%C3%9F_Benrath_D%C3%BCsseldorf.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'stadtbuecherei-benrath' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/stadtbuecherei-garath.webp', bild_attribution = 'Wiegels / Wikimedia Commons (CC BY 3.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Gebaeude_Fritz-Erler-Strasse_21_in_Duesseldorf-Garath,_von_Sueden.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Gebaeude_Fritz-Erler-Strasse_21_in_Duesseldorf-Garath,_von_Sueden.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'stadtbuecherei-garath' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/stadtbuecherei-gerresheim.webp', bild_attribution = 'Stadtbüchereien Düsseldorf',
  extras = extras || '{"bild_link": "https://www.duesseldorf.de/stadtbuechereien/standorte/gerresheim", "bild_quelle": "https://www.duesseldorf.de/stadtbuechereien/standorte/gerresheim", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'stadtbuecherei-gerresheim' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/stadtbuecherei-kaiserswerth.webp', bild_attribution = 'Kürschner / Wikimedia Commons (Public Domain)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Kaiserswerther_Markt_22-24,_D%C3%BCsseldorf_2019_(1).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Kaiserswerther_Markt_22-24,_D%C3%BCsseldorf_2019_(1).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'stadtbuecherei-kaiserswerth' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/stadtbuecherei-oberkassel.webp', bild_attribution = 'Stadtbüchereien Düsseldorf',
  extras = extras || '{"bild_link": "https://www.duesseldorf.de/stadtbuechereien/standorte/oberkassel", "bild_quelle": "https://www.duesseldorf.de/stadtbuechereien/standorte/oberkassel", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'stadtbuecherei-oberkassel' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/stadtbuecherei-rath.webp', bild_attribution = 'Stadtbüchereien Düsseldorf',
  extras = extras || '{"bild_link": "https://www.duesseldorf.de/stadtbuechereien/standorte/rath", "bild_quelle": "https://www.duesseldorf.de/stadtbuechereien/standorte/rath", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'stadtbuecherei-rath' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/stadtbuecherei-unterbach.webp', bild_attribution = 'Stadtbüchereien Düsseldorf',
  extras = extras || '{"bild_link": "https://www.duesseldorf.de/stadtbuechereien/standorte/unterbach", "bild_quelle": "https://www.duesseldorf.de/stadtbuechereien/standorte/unterbach", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'stadtbuecherei-unterbach' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/stadtbuecherei-wersten.webp', bild_attribution = 'Stadtbüchereien Düsseldorf',
  extras = extras || '{"bild_link": "https://www.duesseldorf.de/stadtbuechereien/standorte/wersten", "bild_quelle": "https://www.duesseldorf.de/stadtbuechereien/standorte/wersten", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'stadtbuecherei-wersten' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/studio-brick-duesseldorf.webp', bild_attribution = 'StudioBrick',
  extras = extras || '{"bild_link": "https://studio-brick.de/", "bild_quelle": "https://studio-brick.de/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'studio-brick-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/tanzhaus-nrw.webp', bild_attribution = 'Foto: Katja Illner / tanzhaus nrw, via Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Tanzhaus_nrw_2_klein_Foto_Katja_Illner.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Tanzhaus_nrw_2_klein_Foto_Katja_Illner.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'tanzhaus-nrw' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/the-old-irish-pub.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:The_Old_Irish_Pub,_D%C3%BCsseldorf-Altstadt,_Dezember_2024.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:The_Old_Irish_Pub,_D%C3%BCsseldorf-Altstadt,_Dezember_2024.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'the-old-irish-pub' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/the-paris-club-bar.webp', bild_attribution = '25hours Hotel Das Tour',
  extras = extras || '{"bild_link": "https://www.25hours-hotels.com/en/restaurants-bars/duesseldorf/the-paris-club", "bild_quelle": "https://www.25hours-hotels.com/en/restaurants-bars/duesseldorf/the-paris-club", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'the-paris-club-bar' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/theater-an-der-koe.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Theater_an_der_K%C3%B6,_D%C3%BCsseldorf,_Juni_2025.JPG", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Theater_an_der_K%C3%B6,_D%C3%BCsseldorf,_Juni_2025.JPG", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'theater-an-der-koe' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/theater-an-der-luegallee.webp', bild_attribution = 'Christiane Reichert / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:2020_Theater_aussen.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:2020_Theater_aussen.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'theater-an-der-luegallee' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/theatermuseum-duesseldorf.webp', bild_attribution = 'Kürschner / Wikimedia Commons (Public domain)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Theatermuseum_D%C3%BCsseldorf,_Oktober_2016.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Theatermuseum_D%C3%BCsseldorf,_Oktober_2016.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'theatermuseum-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/tonhalle-duesseldorf.webp', bild_attribution = 'Christian A. Schröder (ChristianSchd) / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Tonhalle_Duesseldorf_Oederallee_Pempelfort_Duesseldorf_Germany_02.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Tonhalle_Duesseldorf_Oederallee_Pempelfort_Duesseldorf_Germany_02.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'tonhalle-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/tribe-hotel-duesseldorf.webp', bild_attribution = 'TRIBE Düsseldorf',
  extras = extras || '{"bild_link": "https://all.accor.com/hotel/C1T5/index.de.shtml", "bild_quelle": "https://all.accor.com/hotel/C1T5/index.de.shtml", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'tribe-hotel-duesseldorf' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/ufa-palast.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:UFA-Palast,_D%C3%BCsseldorf,_Dezember_2024_(1).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:UFA-Palast,_D%C3%BCsseldorf,_Dezember_2024_(1).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'ufa-palast' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/xafe-in-kap-1-zentralbibliothek.webp', bild_attribution = 'Raimond Spekking / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Eingang_zur_Zentralbibliothek_D%C3%BCsseldorf_im_KAP1-0978.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Eingang_zur_Zentralbibliothek_D%C3%BCsseldorf_im_KAP1-0978.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'xafe-in-kap-1-zentralbibliothek' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/yoga-kali.webp', bild_attribution = 'Yoga Kali',
  extras = extras || '{"bild_link": "https://yogakali.de/", "bild_quelle": "https://yogakali.de/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'yoga-kali' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/zehn-null-zwo-kreativstudio.webp', bild_attribution = 'zehn null zwo',
  extras = extras || '{"bild_link": "https://zehnnullzwo.de/", "bild_quelle": "https://zehnnullzwo.de/", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'zehn-null-zwo-kreativstudio' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/zentralbibliothek-kap1.webp', bild_attribution = 'Raimond Spekking / Wikimedia Commons (CC BY-SA 4.0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:Konrad-Adenauer-Platz_1,_D%C3%BCsseldorf-0973.jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:Konrad-Adenauer-Platz_1,_D%C3%BCsseldorf-0973.jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'zentralbibliothek-kap1' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/zero-foundation.webp', bild_attribution = 'Kürschner / Wikimedia Commons (CC0)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:H%C3%BCttenstra%C3%9Fe_104,_D%C3%BCsseldorf,_November_2023_(1).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:H%C3%BCttenstra%C3%9Fe_104,_D%C3%BCsseldorf,_November_2023_(1).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'zero-foundation' AND typ = 'spielstaette';
UPDATE public.orte SET bild_url = '/ort-bilder/orte/zurheide-feine-kost.webp', bild_attribution = 'Kürschner / Wikimedia Commons (Public domain)',
  extras = extras || '{"bild_link": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf,_Crown-Hotel,_Edeka_Zurheide,_2018_(1).jpg", "bild_quelle": "https://commons.wikimedia.org/wiki/File:D%C3%BCsseldorf,_Crown-Hotel,_Edeka_Zurheide,_2018_(1).jpg", "bild_abruf": "2026-11-20", "erlaubnis": "nachtraeglich", "foto_version": 1}'::jsonb
WHERE slug = 'zurheide-feine-kost' AND typ = 'spielstaette';

COMMIT;

-- Kontrolle: Ortsseiten mit eigenem Bild
SELECT count(*) FILTER (WHERE bild_url LIKE '/ort-bilder/orte/%') AS mit_bild FROM public.orte WHERE typ = 'spielstaette';
