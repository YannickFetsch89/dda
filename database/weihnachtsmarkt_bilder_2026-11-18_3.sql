-- Eigene Weihnachtsmarkt-Bilder (2026-11-18) – erst NACH dem Deploy der Bilddateien im Supabase SQL-Editor ausführen.
-- Erlaubnis je Bild steht im Kommentar (Quelle: data/weihnachtsmaerkte/bilder.csv).

-- winter-village: Foto: (eigenes, ohne Nachweis) – Erlaubnis: eigenes Foto des Auftraggebers (18.11.2026)
UPDATE public.orte SET bild_url = '/ort-bilder/weihnachtsmaerkte/winter-village.webp', bild_attribution = NULL, extras = (extras - 'bild_link' - 'bild_fokus') || jsonb_build_object('foto_manuell', '2026-11-18', 'foto_version', COALESCE((extras->>'foto_version')::int + 1, 1)) WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'winter-village' RETURNING slug, bild_url, bild_attribution;
-- riesenrad: Foto: (eigenes, ohne Nachweis) – Erlaubnis: eigenes Foto des Auftraggebers (18.11.2026)
UPDATE public.orte SET bild_url = '/ort-bilder/weihnachtsmaerkte/riesenrad.webp', bild_attribution = NULL, extras = (extras - 'bild_link' - 'bild_fokus') || jsonb_build_object('foto_manuell', '2026-11-18', 'foto_version', COALESCE((extras->>'foto_version')::int + 1, 1)) WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'riesenrad' RETURNING slug, bild_url, bild_attribution;
