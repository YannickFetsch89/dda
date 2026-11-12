-- Ortsnamen vereinheitlichen – DiesDasDüsseldorf, erzeugt am 2026-11-12 von pipeline/ortsnamen.py
-- Eine Schreibweise pro Spielstätte (Liste: SPIELSTAETTEN in pipeline/ortsnamen.py). Räume im selben Haus,
-- Treffpunkte und allgemeine Angaben bleiben, wie sie sind. Event-Slugs (URLs) ändern sich nicht.
-- Reihen behalten ihren Slug; nur ihr interner Schlüssel wird an den neuen Ortsnamen angepasst.
-- Im Supabase-SQL-Editor als Ganzes ausführen.

BEGIN;

UPDATE public.events SET ort = 'Ampere' WHERE ort IN ('AMPERE Düsseldorf');
UPDATE public.reihen SET ort = 'Ampere' WHERE ort IN ('AMPERE Düsseldorf');
UPDATE public.events SET ort = 'Aquazoo Löbbecke Museum' WHERE ort IN ('Aquazoo Löbbecke');
UPDATE public.reihen SET ort = 'Aquazoo Löbbecke Museum' WHERE ort IN ('Aquazoo Löbbecke');
UPDATE public.events SET ort = 'Black Box Kino im Filmmuseum' WHERE ort IN ('Black Box - Kino im Filmmuseum Düsseldorf', 'Black Box Kino im Filmmuseum Düsseldorf', 'Blackbox (Kino im Filmmuseum Düsseldorf)');
UPDATE public.reihen SET ort = 'Black Box Kino im Filmmuseum' WHERE ort IN ('Black Box - Kino im Filmmuseum Düsseldorf', 'Black Box Kino im Filmmuseum Düsseldorf', 'Blackbox (Kino im Filmmuseum Düsseldorf)');
UPDATE public.events SET ort = 'Blumengroßmarkt' WHERE ort IN ('Blumengroßmarkt Düsseldorf');
UPDATE public.reihen SET ort = 'Blumengroßmarkt' WHERE ort IN ('Blumengroßmarkt Düsseldorf');
UPDATE public.events SET ort = 'Boston Club' WHERE ort IN ('Boston Club Düsseldorf e.V.');
UPDATE public.reihen SET ort = 'Boston Club' WHERE ort IN ('Boston Club Düsseldorf e.V.');
UPDATE public.events SET ort = 'BrauArt' WHERE ort IN ('BrauArt Düsseldorf');
UPDATE public.reihen SET ort = 'BrauArt' WHERE ort IN ('BrauArt Düsseldorf');
UPDATE public.events SET ort = 'Brauerei Kürzer' WHERE ort IN ('Brauerei Kürzer (Flingern)');
UPDATE public.reihen SET ort = 'Brauerei Kürzer' WHERE ort IN ('Brauerei Kürzer (Flingern)');
UPDATE public.events SET ort = 'Capitol Theater' WHERE ort IN ('Capitol Theater - Düsseldorf', 'Capitol Theater Düsseldorf', 'Capitol-Theater');
UPDATE public.reihen SET ort = 'Capitol Theater' WHERE ort IN ('Capitol Theater - Düsseldorf', 'Capitol Theater Düsseldorf', 'Capitol-Theater');
UPDATE public.events SET ort = 'Cosmo Sports' WHERE ort IN ('COSMO SPORTS');
UPDATE public.reihen SET ort = 'Cosmo Sports' WHERE ort IN ('COSMO SPORTS');
UPDATE public.events SET ort = 'D''haus im Central' WHERE ort IN ('D''haus — Central');
UPDATE public.reihen SET ort = 'D''haus im Central' WHERE ort IN ('D''haus — Central');
UPDATE public.events SET ort = 'Düsseldorf' WHERE ort IN ('Dusseldorf, Germany', 'Düsseldorf, Germany');
UPDATE public.reihen SET ort = 'Düsseldorf' WHERE ort IN ('Dusseldorf, Germany', 'Düsseldorf, Germany');
UPDATE public.events SET ort = 'Düsseldorf Hauptbahnhof' WHERE ort IN ('Dusseldorf Hauptbahnhof', 'Düsseldorf, Hauptbahnhof');
UPDATE public.reihen SET ort = 'Düsseldorf Hauptbahnhof' WHERE ort IN ('Dusseldorf Hauptbahnhof', 'Düsseldorf, Hauptbahnhof');
UPDATE public.events SET ort = 'Düsseldorf International Football Club (INDOOR & OUTDOOR)' WHERE ort IN ('Düsseldorf International Football Club  (INDOOR & OUTDOOR)');
UPDATE public.reihen SET ort = 'Düsseldorf International Football Club (INDOOR & OUTDOOR)' WHERE ort IN ('Düsseldorf International Football Club  (INDOOR & OUTDOOR)');
UPDATE public.events SET ort = 'Fatty''s Irish Pub' WHERE ort IN ('The Irish Pub Bei Fatty - Fatty''s', 'The Irish Pub bei Fatty - Fatty''s');
UPDATE public.reihen SET ort = 'Fatty''s Irish Pub' WHERE ort IN ('The Irish Pub Bei Fatty - Fatty''s', 'The Irish Pub bei Fatty - Fatty''s');
UPDATE public.events SET ort = 'Fichtenstr. 40, 40233 Düsseldorf' WHERE ort IN ('Fichtenstr. 40, 40233 Düsseldorf, Germany');
UPDATE public.reihen SET ort = 'Fichtenstr. 40, 40233 Düsseldorf' WHERE ort IN ('Fichtenstr. 40, 40233 Düsseldorf, Germany');
UPDATE public.events SET ort = 'Goethe-Museum' WHERE ort IN ('Goethe Museum', 'Goethe-Museum Düsseldorf');
UPDATE public.reihen SET ort = 'Goethe-Museum' WHERE ort IN ('Goethe Museum', 'Goethe-Museum Düsseldorf');
UPDATE public.events SET ort = 'Holy Craft Beer Bar' WHERE ort IN ('HOLY CRAFT Beer Bar');
UPDATE public.reihen SET ort = 'Holy Craft Beer Bar' WHERE ort IN ('HOLY CRAFT Beer Bar');
UPDATE public.events SET ort = 'Jazz-Schmiede' WHERE ort IN ('Jazz Schmiede', 'Jazz-Schmiede Düsseldorf', 'Jazz-Schmiede Düsseldorf | Jazzclub');
UPDATE public.reihen SET ort = 'Jazz-Schmiede' WHERE ort IN ('Jazz Schmiede', 'Jazz-Schmiede Düsseldorf', 'Jazz-Schmiede Düsseldorf | Jazzclub');
UPDATE public.events SET ort = 'KaBARett FLiN' WHERE ort IN ('Kabarett FLiN');
UPDATE public.reihen SET ort = 'KaBARett FLiN' WHERE ort IN ('Kabarett FLiN');
UPDATE public.events SET ort = 'Kasematten' WHERE ort IN ('Kasematten Düsseldorf');
UPDATE public.reihen SET ort = 'Kasematten' WHERE ort IN ('Kasematten Düsseldorf');
UPDATE public.events SET ort = 'Kay-und-Lore-Lorentz-Platz' WHERE ort IN ('Kay-und-Lore-Lorentz-Platz Düsseldorf');
UPDATE public.reihen SET ort = 'Kay-und-Lore-Lorentz-Platz' WHERE ort IN ('Kay-und-Lore-Lorentz-Platz Düsseldorf');
UPDATE public.events SET ort = 'Klub Kulb' WHERE ort IN ('KLUB KULB');
UPDATE public.reihen SET ort = 'Klub Kulb' WHERE ort IN ('KLUB KULB');
UPDATE public.events SET ort = 'Kurzestr.11, 40213 Düsseldorf' WHERE ort IN ('Kurzestr.11, 40213 Düsseldorf, Germany');
UPDATE public.reihen SET ort = 'Kurzestr.11, 40213 Düsseldorf' WHERE ort IN ('Kurzestr.11, 40213 Düsseldorf, Germany');
UPDATE public.events SET ort = 'Maxhaus' WHERE ort IN ('maxhaus');
UPDATE public.reihen SET ort = 'Maxhaus' WHERE ort IN ('maxhaus');
UPDATE public.events SET ort = 'Merkur Spiel-Arena' WHERE ort IN ('Merkur Spiel-Arena Düsseldorf');
UPDATE public.reihen SET ort = 'Merkur Spiel-Arena' WHERE ort IN ('Merkur Spiel-Arena Düsseldorf');
UPDATE public.events SET ort = 'Metropol Kino' WHERE ort IN ('Metropol Kino Düsseldorf');
UPDATE public.reihen SET ort = 'Metropol Kino' WHERE ort IN ('Metropol Kino Düsseldorf');
UPDATE public.events SET ort = 'Mitsubishi Electric Halle' WHERE ort IN ('Mitsubishi Electric  Halle Düsseldorf', 'Mitsubishi Electric HALLE', 'Mitsubishi Electric HALLE, Dusseldorf, North Rhine-Westphalia, Germany');
UPDATE public.reihen SET ort = 'Mitsubishi Electric Halle' WHERE ort IN ('Mitsubishi Electric  Halle Düsseldorf', 'Mitsubishi Electric HALLE', 'Mitsubishi Electric HALLE, Dusseldorf, North Rhine-Westphalia, Germany');
UPDATE public.events SET ort = 'NEU #GoFreizeitGO - Deine Freizeit- und Eventbörse' WHERE ort IN ('NEU #GoFreizeitGO  -  Deine Freizeit- und Eventbörse');
UPDATE public.reihen SET ort = 'NEU #GoFreizeitGO - Deine Freizeit- und Eventbörse' WHERE ort IN ('NEU #GoFreizeitGO  -  Deine Freizeit- und Eventbörse');
UPDATE public.events SET ort = 'NEU #GoFreizeitGO - Deine Freizeit- und Eventbörse (Online)' WHERE ort IN ('NEU #GoFreizeitGO  -  Deine Freizeit- und Eventbörse (Online)');
UPDATE public.reihen SET ort = 'NEU #GoFreizeitGO - Deine Freizeit- und Eventbörse (Online)' WHERE ort IN ('NEU #GoFreizeitGO  -  Deine Freizeit- und Eventbörse (Online)');
UPDATE public.events SET ort = 'NRW-Forum' WHERE ort IN ('NRW-Forum Düsseldorf');
UPDATE public.reihen SET ort = 'NRW-Forum' WHERE ort IN ('NRW-Forum Düsseldorf');
UPDATE public.events SET ort = 'Nachtresidenz' WHERE ort IN ('Nachtresidenz Düsseldorf');
UPDATE public.reihen SET ort = 'Nachtresidenz' WHERE ort IN ('Nachtresidenz Düsseldorf');
UPDATE public.events SET ort = 'PSD Bank Dome' WHERE ort IN ('PSD BANK DOME', 'PSD BANK DOME Düsseldorf');
UPDATE public.reihen SET ort = 'PSD Bank Dome' WHERE ort IN ('PSD BANK DOME', 'PSD BANK DOME Düsseldorf');
UPDATE public.events SET ort = 'Pitcher Rock HQ' WHERE ort IN ('Pitcher', 'Pitcher - Rock''n''Roll Headquarter Düsseldorf');
UPDATE public.reihen SET ort = 'Pitcher Rock HQ' WHERE ort IN ('Pitcher', 'Pitcher - Rock''n''Roll Headquarter Düsseldorf');
UPDATE public.events SET ort = 'R25 Kulturschlachthof' WHERE ort IN ('R25-Kulturschlachthof');
UPDATE public.reihen SET ort = 'R25 Kulturschlachthof' WHERE ort IN ('R25-Kulturschlachthof');
UPDATE public.events SET ort = 'Ratinger Hof' WHERE ort IN ('Ratinger Hof Düsseldorf');
UPDATE public.reihen SET ort = 'Ratinger Hof' WHERE ort IN ('Ratinger Hof Düsseldorf');
UPDATE public.events SET ort = 'Rheintreppe' WHERE ort IN ('Rheintreppe Düsseldorf');
UPDATE public.reihen SET ort = 'Rheintreppe' WHERE ort IN ('Rheintreppe Düsseldorf');
UPDATE public.events SET ort = 'Rheinuferpromenade, 40213 Düsseldorf' WHERE ort IN ('Rheinuferpromenade, 40213 Düsseldorf, Germany');
UPDATE public.reihen SET ort = 'Rheinuferpromenade, 40213 Düsseldorf' WHERE ort IN ('Rheinuferpromenade, 40213 Düsseldorf, Germany');
UPDATE public.events SET ort = 'Robert-Schumann-Saal' WHERE ort IN ('Robert Schumann Saal');
UPDATE public.reihen SET ort = 'Robert-Schumann-Saal' WHERE ort IN ('Robert Schumann Saal');
UPDATE public.events SET ort = 'Rudas Studios' WHERE ort IN ('Rudas Studios Düsseldorf');
UPDATE public.reihen SET ort = 'Rudas Studios' WHERE ort IN ('Rudas Studios Düsseldorf');
UPDATE public.events SET ort = 'Savoy Theater' WHERE ort IN ('Savoy Theater Düsseldorf');
UPDATE public.reihen SET ort = 'Savoy Theater' WHERE ort IN ('Savoy Theater Düsseldorf');
UPDATE public.events SET ort = 'Stahlwerk' WHERE ort IN ('Stahlwerk Düsseldorf');
UPDATE public.reihen SET ort = 'Stahlwerk' WHERE ort IN ('Stahlwerk Düsseldorf');
UPDATE public.events SET ort = 'Superblock Boulderhalle' WHERE ort IN ('Superblock', 'Superblock - Boulderhalle Düsseldorf');
UPDATE public.reihen SET ort = 'Superblock Boulderhalle' WHERE ort IN ('Superblock', 'Superblock - Boulderhalle Düsseldorf');
UPDATE public.events SET ort = 'THE FAWLEY''S CLUB - Dinner Culture Sport Society (Online)' WHERE ort IN ('THE FAWLEY''S CLUB - Dinner  Culture  Sport  Society (Online)');
UPDATE public.reihen SET ort = 'THE FAWLEY''S CLUB - Dinner Culture Sport Society (Online)' WHERE ort IN ('THE FAWLEY''S CLUB - Dinner  Culture  Sport  Society (Online)');
UPDATE public.events SET ort = 'Tanzhaus NRW' WHERE ort IN ('Tanzhaus NRW Düsseldorf', 'tanzhaus nrw');
UPDATE public.reihen SET ort = 'Tanzhaus NRW' WHERE ort IN ('Tanzhaus NRW Düsseldorf', 'tanzhaus nrw');
UPDATE public.events SET ort = 'Theatermuseum Düsseldorf' WHERE ort IN ('TMD Theatermuseum Hofgartenhaus Düsseldorf');
UPDATE public.reihen SET ort = 'Theatermuseum Düsseldorf' WHERE ort IN ('TMD Theatermuseum Hofgartenhaus Düsseldorf');
UPDATE public.events SET ort = 'UFA-Palast' WHERE ort IN ('UFA Palast Düsseldorf', 'UFA-Palast Düsseldorf');
UPDATE public.reihen SET ort = 'UFA-Palast' WHERE ort IN ('UFA Palast Düsseldorf', 'UFA-Palast Düsseldorf');
UPDATE public.events SET ort = 'Velvet' WHERE ort IN ('VELVET');
UPDATE public.reihen SET ort = 'Velvet' WHERE ort IN ('VELVET');
UPDATE public.events SET ort = 'Volksgarten' WHERE ort IN ('Düsseldorf, Volksgarten', 'Volksgarten Düsseldorf');
UPDATE public.reihen SET ort = 'Volksgarten' WHERE ort IN ('Düsseldorf, Volksgarten', 'Volksgarten Düsseldorf');
UPDATE public.events SET ort = 'Winkelsfelder Straße 21, 40476 Düsseldorf' WHERE ort IN ('Winkelsfelder Straße 21, 40476 Düsseldorf, Germany');
UPDATE public.reihen SET ort = 'Winkelsfelder Straße 21, 40476 Düsseldorf' WHERE ort IN ('Winkelsfelder Straße 21, 40476 Düsseldorf, Germany');
UPDATE public.events SET ort = 'Zentralbibliothek KAP1' WHERE ort IN ('Düsseldorfer Zentralbibliothek im KAP1');
UPDATE public.reihen SET ort = 'Zentralbibliothek KAP1' WHERE ort IN ('Düsseldorfer Zentralbibliothek im KAP1');
UPDATE public.events SET ort = 'hirschchen' WHERE ort IN ('*hirschchen');
UPDATE public.reihen SET ort = 'hirschchen' WHERE ort IN ('*hirschchen');
UPDATE public.events SET ort = 'zakk' WHERE ort IN ('Zentrum für Aktion, Kultur und Kommunikation', 'zakk - Zentrum für Aktion, Kultur und Kommunikation', 'zakk Düsseldorf');
UPDATE public.reihen SET ort = 'zakk' WHERE ort IN ('Zentrum für Aktion, Kultur und Kommunikation', 'zakk - Zentrum für Aktion, Kultur und Kommunikation', 'zakk Düsseldorf');
UPDATE public.events SET ort = 'zakk – Halle' WHERE ort IN ('zakk Halle');
UPDATE public.reihen SET ort = 'zakk – Halle' WHERE ort IN ('zakk Halle');

-- Reihen-Schlüssel (titel|ort) an die neuen Ortsnamen anpassen – Slugs bleiben
UPDATE public.reihen SET schluessel = 'aquazoo löbbecke museum düsseldorf|aquazoo löbbecke museum' WHERE id = '0fd6d7ea-36f2-43a4-94b9-3a8f8060070b';
UPDATE public.reihen SET schluessel = 'mädchenklamotte düsseldorf boston club|boston club' WHERE id = '26800a95-f65d-40a0-9bbd-8301d2695fea';
UPDATE public.reihen SET schluessel = 'tmd mit nachwuchs eltern baby tour|theatermuseum' WHERE id = '3acc3c02-541f-44e3-b3c1-576608fdfab4';
UPDATE public.reihen SET schluessel = 'foto trifft kostüm abgewandter lear|theatermuseum' WHERE id = '42b485e5-e6e4-490f-ace8-5cf6d891cbf8';
UPDATE public.reihen SET schluessel = 'dart night 2 vs 2 düsseldorf|fattys irish pub' WHERE id = '5695e0ac-bcf3-4834-bb92-5a49e7b22489';
UPDATE public.reihen SET schluessel = 'punk 50 demand the impossible|theatermuseum' WHERE id = '5b86db0e-01dc-43b2-a05b-4465a76a179d';
UPDATE public.reihen SET schluessel = 'karaoke till death liveband karaoke party|pitcher rock hq' WHERE id = '65071fae-2bc4-4613-9ea6-4651769864b6';
UPDATE public.reihen SET schluessel = 'pitcher poetry slam|pitcher rock hq' WHERE id = '98cedbc2-8d54-4a1a-9d59-a1551cf577b9';
UPDATE public.reihen SET schluessel = 'the düsseldorf expat meetup fattys irish pub|fattys irish pub' WHERE id = 'eea66d15-c12e-41d5-8072-d7dc693fda62';
UPDATE public.reihen SET schluessel = '1904 bis 1947 wandel zwischen aufbruch archiv|theatermuseum' WHERE id = 'efae1ee1-fa5d-4cc4-8af3-8810b1cc8ae3';

COMMIT;

-- Kontrolle 1: alte Schreibweisen – erwartet: KEINE Zeile
SELECT ort, COUNT(*) AS anzahl FROM public.events WHERE ort IN ('*hirschchen', 'AMPERE Düsseldorf', 'Aquazoo Löbbecke', 'Black Box - Kino im Filmmuseum Düsseldorf', 'Black Box Kino im Filmmuseum Düsseldorf', 'Blackbox (Kino im Filmmuseum Düsseldorf)', 'Blumengroßmarkt Düsseldorf', 'Boston Club Düsseldorf e.V.', 'BrauArt Düsseldorf', 'Brauerei Kürzer (Flingern)', 'COSMO SPORTS', 'Capitol Theater - Düsseldorf', 'Capitol Theater Düsseldorf', 'Capitol-Theater', 'D''haus — Central', 'Dusseldorf Hauptbahnhof', 'Düsseldorf, Hauptbahnhof', 'Dusseldorf, Germany', 'Düsseldorf, Germany', 'Düsseldorf International Football Club  (INDOOR & OUTDOOR)', 'Düsseldorf, Volksgarten', 'Volksgarten Düsseldorf', 'Düsseldorfer Zentralbibliothek im KAP1', 'Fichtenstr. 40, 40233 Düsseldorf, Germany', 'Goethe Museum', 'Goethe-Museum Düsseldorf', 'HOLY CRAFT Beer Bar', 'Jazz Schmiede', 'Jazz-Schmiede Düsseldorf', 'Jazz-Schmiede Düsseldorf | Jazzclub', 'KLUB KULB', 'Kabarett FLiN', 'Kasematten Düsseldorf', 'Kay-und-Lore-Lorentz-Platz Düsseldorf', 'Kurzestr.11, 40213 Düsseldorf, Germany', 'Merkur Spiel-Arena Düsseldorf', 'Metropol Kino Düsseldorf', 'Mitsubishi Electric  Halle Düsseldorf', 'Mitsubishi Electric HALLE', 'Mitsubishi Electric HALLE, Dusseldorf, North Rhine-Westphalia, Germany', 'NEU #GoFreizeitGO  -  Deine Freizeit- und Eventbörse', 'NEU #GoFreizeitGO  -  Deine Freizeit- und Eventbörse (Online)', 'NRW-Forum Düsseldorf', 'Nachtresidenz Düsseldorf', 'PSD BANK DOME', 'PSD BANK DOME Düsseldorf', 'Pitcher', 'Pitcher - Rock''n''Roll Headquarter Düsseldorf', 'R25-Kulturschlachthof', 'Ratinger Hof Düsseldorf', 'Rheintreppe Düsseldorf', 'Rheinuferpromenade, 40213 Düsseldorf, Germany', 'Robert Schumann Saal', 'Rudas Studios Düsseldorf', 'Savoy Theater Düsseldorf', 'Stahlwerk Düsseldorf', 'Superblock', 'Superblock - Boulderhalle Düsseldorf', 'THE FAWLEY''S CLUB - Dinner  Culture  Sport  Society (Online)', 'TMD Theatermuseum Hofgartenhaus Düsseldorf', 'Tanzhaus NRW Düsseldorf', 'tanzhaus nrw', 'The Irish Pub Bei Fatty - Fatty''s', 'The Irish Pub bei Fatty - Fatty''s', 'UFA Palast Düsseldorf', 'UFA-Palast Düsseldorf', 'VELVET', 'Winkelsfelder Straße 21, 40476 Düsseldorf, Germany', 'Zentrum für Aktion, Kultur und Kommunikation', 'zakk - Zentrum für Aktion, Kultur und Kommunikation', 'zakk Düsseldorf', 'maxhaus', 'zakk Halle') GROUP BY ort;

-- Kontrolle 2: neue Namen mit Anzahl
SELECT ort, COUNT(*) AS anzahl FROM public.events WHERE ort IN ('Ampere', 'Aquazoo Löbbecke Museum', 'Black Box Kino im Filmmuseum', 'Blumengroßmarkt', 'Boston Club', 'BrauArt', 'Brauerei Kürzer', 'Capitol Theater', 'Cosmo Sports', 'D''haus im Central', 'Düsseldorf', 'Düsseldorf Hauptbahnhof', 'Düsseldorf International Football Club (INDOOR & OUTDOOR)', 'Fatty''s Irish Pub', 'Fichtenstr. 40, 40233 Düsseldorf', 'Goethe-Museum', 'Holy Craft Beer Bar', 'Jazz-Schmiede', 'KaBARett FLiN', 'Kasematten', 'Kay-und-Lore-Lorentz-Platz', 'Klub Kulb', 'Kurzestr.11, 40213 Düsseldorf', 'Maxhaus', 'Merkur Spiel-Arena', 'Metropol Kino', 'Mitsubishi Electric Halle', 'NEU #GoFreizeitGO - Deine Freizeit- und Eventbörse', 'NEU #GoFreizeitGO - Deine Freizeit- und Eventbörse (Online)', 'NRW-Forum', 'Nachtresidenz', 'PSD Bank Dome', 'Pitcher Rock HQ', 'R25 Kulturschlachthof', 'Ratinger Hof', 'Rheintreppe', 'Rheinuferpromenade, 40213 Düsseldorf', 'Robert-Schumann-Saal', 'Rudas Studios', 'Savoy Theater', 'Stahlwerk', 'Superblock Boulderhalle', 'THE FAWLEY''S CLUB - Dinner Culture Sport Society (Online)', 'Tanzhaus NRW', 'Theatermuseum Düsseldorf', 'UFA-Palast', 'Velvet', 'Volksgarten', 'Winkelsfelder Straße 21, 40476 Düsseldorf', 'Zentralbibliothek KAP1', 'hirschchen', 'zakk', 'zakk – Halle') GROUP BY ort ORDER BY anzahl DESC;
