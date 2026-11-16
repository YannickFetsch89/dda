-- Spielplatz-Fotos: Bildausschnitt (extras.bild_fokus) – im Supabase SQL-Editor ausführen.
-- Hochformat-Fotos im Querformat-Rahmen: Prozent = senkrechte Lage (0 % oben, 100 % unten). Wirkt mit dem Website-Stand
-- ab dem Deploy „Bildausschnitt in Prozent“; vorher ignoriert die Seite die Prozentwerte (kein Schaden).

-- Spielplatz Röntgenweg (Cronenberger Weg): Ausschnitt oben, Datumsstempel unten fällt weg
UPDATE public.orte SET extras = extras || jsonb_build_object('bild_fokus', '22%')
WHERE id = 'd3adba6d-f310-48c2-9667-0c6080e2c9ca' AND typ = 'spielplatz';

-- Spielplatz Venn- und Brinellstraße: Ausschnitt oben (Spielgerät statt Sandfläche)
UPDATE public.orte SET extras = extras || jsonb_build_object('bild_fokus', '20%')
WHERE id = '20931679-490e-4b60-99d4-f573efedc53c' AND typ = 'spielplatz';

-- Spielplatz Ziegeleiweg: Foto mit den Federwippen (Foto 0 von Pawel aus Düsseldorf) statt der Schaukel, Ausschnitt 26 %
-- (Wahl des Auftraggebers; oben vor dem Haus steht klein eine Person, kein Gesicht erkennbar)
UPDATE public.orte SET bild_attribution = 'Pawel aus Düsseldorf', bild_url = NULL, extras = extras || jsonb_build_object(
  'google_foto', '{"name": "places/ChIJx8wfRKbLuEcR-dP7gE1CkoM/photos/AV-0GLd_yXcmcjLBqSzsW6hEt_zaFUG6yQe_bOiSicHCH0fcnav_fgfSgxp0jq5N2RQtyT-jnMFFDc5Aciz_IAjhxGAitCTd8wkLFvcFV55kogtOrNf_SQppCOIYVlqM2ojtqyDGW0QJmxYaILNGWltSZvXayJC48CUfAo1pw91_mPrX7DSIRsNVzYrZMU4mhNtp0P9gOtLrA8ctCe55vLi1aJ7V1fUemkQLBVGKLp2qKwy0i7xbStOsIVoPPVmeCkm8SmVba5qHF_b_6iD7WfBd8b2da9VYv4kERyVr7JSKiM2vlMyJG-6bCTqDVlTEsP_0Dv_V7fK_vl94FEne8nc8GTPW2hZexrk73WBllyKQPl4MWLpDcoueW87xnWKkjRa-F4nR_t-Av0-4_Q8WLELOOa_3Mg", "breite": 2464, "hoehe": 3280, "autor": "Pawel aus Düsseldorf", "autor_url": "https://maps.google.com/maps/contrib/106783373554393960186"}'::jsonb, 'foto_manuell', '2026-11-16',
  'foto_version', COALESCE((extras->>'foto_version')::int + 1, 1), 'bild_fokus', '26%')
WHERE id = '16244e93-4313-4b56-a7dc-92f15af885d2' AND typ = 'spielplatz';
