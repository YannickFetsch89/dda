-- Club-Foto Kulturschlachthof R25 (Wunsch des Auftraggebers 12.11.2026): DJ am Pult statt Bühne mit Band.
-- Im Supabase SQL-Editor ausführen, dann deployen.
UPDATE public.orte SET bild_attribution = 'Chili Palmer', extras = extras || jsonb_build_object('google_foto', '{"name": "places/ChIJ5U_l65bJuEcRdzcBDa75aNI/photos/AV-0GLeENXDS5aI9xYLUGwJo6shpsNaBUUNAFfqYEXK10E86DzbS-YzLgF2JWr6q-tf3wChTsUUFqk6MGpjXEW_GSfvmafSEvuyFs2LjMMVQkmqhjhpRF08tnGdnHEIZfvHTwnMN9Z67WVqNuuIyfZ_ZDiAPpoC_jgxyDYpOj3e2CvX5qKxlUag983BpvXPcGGSTxZxdgSTqj4v74c5DTXxXn3UjTPF_7bQnKFkuuiqBXqaHsSK70WUOVzX_C4Oo2pa8eNeODifmrfK19DrGu5b-DYcbn5SHECTeJSBWe1WQEJGjtE8FeGrYFT_IABy5Ki6CNHGyZImbDUfRE4TDC9EIPW4nGPJcAhV-WjEYUJOqxMWV3hOFiY2mT1CFOW1ezztOJiAry60tWSxllJeoz81w6lMBZX1wPw7-OfCpkPVSzd9snw", "breite": 4000, "hoehe": 3000, "autor": "Chili Palmer", "autor_url": "https://maps.google.com/maps/contrib/109999148916709207463"}'::jsonb,
  'foto_manuell', '12.11.2026', 'foto_version', COALESCE((extras->>'foto_version')::int, 1) + 1) WHERE id = '728ca26a-3cf3-4a31-bba3-6c0558c248a1';

-- Kontrolle: erwartet 1 Zeile, Autor Chili Palmer, Version 2
SELECT name, bild_attribution, extras->'google_foto'->>'autor' AS foto_autor, extras->>'foto_version' AS version
FROM public.orte WHERE id = '728ca26a-3cf3-4a31-bba3-6c0558c248a1';
