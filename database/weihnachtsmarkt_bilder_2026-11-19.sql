-- Eigene Weihnachtsmarkt-Bilder (2026-11-19) – erst NACH dem Deploy der Bilddateien im Supabase SQL-Editor ausführen.
-- Erlaubnis je Bild steht im Kommentar (Quelle: data/weihnachtsmaerkte/bilder.csv).

-- kiez-advent: Foto: (eigenes, ohne Nachweis) – Erlaubnis: eigenes Foto des Auftraggebers (19.11.2026)
UPDATE public.orte SET bild_url = '/ort-bilder/weihnachtsmaerkte/kiez-advent.webp', bild_attribution = NULL, extras = (extras - 'bild_link' - 'bild_fokus') || jsonb_build_object('foto_manuell', '2026-11-19', 'foto_version', COALESCE((extras->>'foto_version')::int + 1, 1)) WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'kiez-advent' RETURNING slug, bild_url, bild_attribution;
