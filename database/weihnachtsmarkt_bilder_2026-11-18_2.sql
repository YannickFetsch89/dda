-- Eigene Weihnachtsmarkt-Bilder (2026-11-18) – erst NACH dem Deploy der Bilddateien im Supabase SQL-Editor ausführen.
-- Erlaubnis je Bild steht im Kommentar (Quelle: data/weihnachtsmaerkte/bilder.csv).

-- koe-on-ice: Foto: DEG Winterwelt – Erlaubnis: Genehmigung DEG Winterwelt laut Auftraggeber (18.11.2026)
UPDATE public.orte SET bild_url = '/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp', bild_attribution = 'DEG Winterwelt', extras = (extras - 'bild_link' - 'bild_fokus') || jsonb_build_object('foto_manuell', '2026-11-18', 'foto_version', COALESCE((extras->>'foto_version')::int + 1, 1)) WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'koe-on-ice' RETURNING slug, bild_url, bild_attribution;
-- bilk-arcaden: Foto: (eigenes, ohne Nachweis) – Erlaubnis: eigenes Foto des Auftraggebers (18.11.2026)
UPDATE public.orte SET bild_url = '/ort-bilder/weihnachtsmaerkte/bilk-arcaden.webp', bild_attribution = NULL, extras = (extras - 'bild_link' - 'bild_fokus') || jsonb_build_object('foto_manuell', '2026-11-18', 'foto_version', COALESCE((extras->>'foto_version')::int + 1, 1)) WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'bilk-arcaden' RETURNING slug, bild_url, bild_attribution;
