-- Dubletten aufräumen – DiesDasDüsseldorf, erzeugt am 2026-11-27 von pipeline/dubletten_sql.py
-- Im Supabase-SQL-Editor als Ganzes ausführen (eine Transaktion). Betrifft nur Events ab heute.
-- Dubletten werden ausgeblendet (abgelehnt = true) und per 301 auf das behaltene Event umgeleitet.

BEGIN;

-- 2. Dubletten: behaltenes Event ergänzen, Dublette ausblenden und umleiten
-- 2026-11-27: „Max Dax & Max Frintrop – Artist Talk & Musik“ [Rausgegangen, 19:00]  ←  „Max Dax & Max Frintrop – Artist Talk & Musik“ [Rausgegangen, 19:00]
UPDATE public.events k SET bild_url = COALESCE(NULLIF(k.bild_url, ''), d.bild_url), beschreibung = COALESCE(NULLIF(k.beschreibung, ''), d.beschreibung), preis = COALESCE(NULLIF(k.preis, ''), d.preis), adresse = COALESCE(NULLIF(k.adresse, ''), d.adresse) FROM public.events d WHERE k.id = '649eddb3-b021-4315-b321-a6e571236514' AND d.id = '231e8584-c98c-4cda-9522-58e22994db89';
UPDATE public.events SET abgelehnt = true WHERE id = '231e8584-c98c-4cda-9522-58e22994db89';
INSERT INTO public.event_seo_entscheidungen (event_id, slug, aktion, ziel) VALUES ('231e8584-c98c-4cda-9522-58e22994db89', 'max-dax-max-frintrop-artist-talk-musik-schleuse-zwei-2026-11-27', 'weiterleiten', '/event/musik/max-dax-max-frintrop-artist-talk-musik-bilker-bunker-2026-11-27') ON CONFLICT (event_id) DO UPDATE SET aktion = 'weiterleiten', ziel = EXCLUDED.ziel, entschieden_am = now();
-- 2026-12-09: „Rudelsingen“ [Kunstpalast Düsseldorf, 20:00]  ←  „Das Düsseldorfer Rudelsingen“ [VisitDüsseldorf, 20:00]
UPDATE public.events k SET bild_url = COALESCE(NULLIF(k.bild_url, ''), d.bild_url), beschreibung = COALESCE(NULLIF(k.beschreibung, ''), d.beschreibung), preis = COALESCE(NULLIF(k.preis, ''), d.preis), adresse = COALESCE(NULLIF(k.adresse, ''), d.adresse) FROM public.events d WHERE k.id = '64459cb4-2ff2-45d7-9fd5-13533bc6ae08' AND d.id = 'ee18d64f-345c-46fd-af50-0d837cab2a5e';
UPDATE public.events SET abgelehnt = true WHERE id = 'ee18d64f-345c-46fd-af50-0d837cab2a5e';
INSERT INTO public.event_seo_entscheidungen (event_id, slug, aktion, ziel) VALUES ('ee18d64f-345c-46fd-af50-0d837cab2a5e', 'das-duesseldorfer-rudelsingen-robert-schumann-saal-2026-12-09', 'weiterleiten', '/event/kultur/rudelsingen-kunstpalast-duesseldorf-2026-12-09') ON CONFLICT (event_id) DO UPDATE SET aktion = 'weiterleiten', ziel = EXCLUDED.ziel, entschieden_am = now();


COMMIT;

-- Kontrolle: neue Weiterleitungen von heute
SELECT slug, ziel FROM public.event_seo_entscheidungen WHERE aktion = 'weiterleiten' AND entschieden_am::date = CURRENT_DATE ORDER BY slug;
