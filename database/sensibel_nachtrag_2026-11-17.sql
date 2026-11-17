-- sensibel_nachtrag_2026-11-17.sql – DiesDasDüsseldorf
-- Sensibel-Nachtrag, Teil 2: EINTRAGEN (Plan Nutzerkonten 5.8, Schritt 7).
--
-- ERST AUSFÜHREN, WENN die Vorschau (sensibel_nachtrag_vorschau_2026-11-17.sql) durchgesehen ist und die
-- Fehltreffer unten als Ausnahmen eingetragen sind. Läuft VOR dem ersten Einschalten der Konten, damit noch keine
-- Merkliste betroffen ist.
--
-- WAS PASSIERT (in einer Transaktion):
--   1. Ausnahmen: bestätigte Fehltreffer kommen in event_sensibel_ausnahmen (Block unten, von Claude befüllt).
--   2. Nachtrag: alle übrigen Treffer der Regeln ab heute minus 400 Tage kommen in event_sensibel (quelle = 'regel').
--   3. Kontrolle: Anzahl je Grund, dazu wie viele Ausnahmen bestehen.
-- Wiederholbar: schon gekennzeichnete Events und Ausnahmen werden übersprungen.
-- Ausführen außerhalb eines Pipeline-Laufs (nicht zwischen 6 und 9 Uhr). Als postgres im Supabase-SQL-Editor.

BEGIN;

-- 1. Ausnahmen (bestätigte Fehltreffer aus der Sichtprüfung vom 17.11.2026, Vorschlag Claude, vom Auftraggeber
--    zu bestätigen). Grundsatz: Steht das Stichwort nur in der Inhaltsbeschreibung eines Theaterstücks, Films,
--    Konzerts oder einer Ausstellung, verrät das Merken nichts über die Person. Im Zweifel bleibt ein Treffer sensibel.
INSERT INTO public.event_sensibel_ausnahmen (event_id, notiz)
SELECT v.event_id, v.notiz
FROM (VALUES
    ('6871e7e2-06a6-44ae-bb04-206cb5c06977'::uuid, 'Sichtprüfung 2026-11: Die Verwandlung (Theater, Inhaltshinweis Depression)'),
    ('c8e30ae4-2494-48f5-bc83-995881431166'::uuid, 'Sichtprüfung 2026-11: Nektarios Vlachopoulos (Kabarett)'),
    ('f98c12b4-0817-4f22-9f84-16bd64388b17'::uuid, 'Sichtprüfung 2026-11: Tributkonzert Manos Loizos (Konzert im Gemeindesaal)'),
    ('74ed010d-a116-4529-8369-195fc91ad3b0'::uuid, 'Sichtprüfung 2026-11: Gemalte Gebete (Ausstellung Wandmalereien)'),
    ('5b4626a9-d414-43e6-843f-e78693ec5d45'::uuid, 'Sichtprüfung 2026-11: PINK FLAMINGOS (Film)'),
    ('ca10cab5-3344-43a9-be7f-9b38b4b5631b'::uuid, 'Sichtprüfung 2026-11: PINK FLAMINGOS (Film)'),
    ('7391365a-5c9f-4515-b183-c84a64f61ef3'::uuid, 'Sichtprüfung 2026-11: MAIKA Record Release (Konzert)'),
    ('6e1ab93c-f518-499c-8103-3b6cbd3db1d9'::uuid, 'Sichtprüfung 2026-11: Gallery Crush (Hetero-Edition)'),
    ('d9bb6881-5c6f-473b-81b1-bdc69ca63c69'::uuid, 'Sichtprüfung 2026-11: COMEDY GEGEN RECHTS (Comedy)'),
    ('0ec98638-28d0-43fb-b136-01ffa78ddf43'::uuid, 'Sichtprüfung 2026-11: ICH MACH JA DOCH, WAS ICH WILL (Theater)'),
    ('1d816812-09ad-4f2a-b11a-cda888b1c628'::uuid, 'Sichtprüfung 2026-11: ICH MACH JA DOCH, WAS ICH WILL (Theater)'),
    ('7333a2b5-7e29-443d-84e5-15bf5e400906'::uuid, 'Sichtprüfung 2026-11: ICH MACH JA DOCH, WAS ICH WILL (Theater)'),
    ('ae5c6cff-4d1c-4dc1-b38a-ea3a421dd3b2'::uuid, 'Sichtprüfung 2026-11: ICH MACH JA DOCH, WAS ICH WILL (Theater)')
) AS v (event_id, notiz)
WHERE EXISTS (SELECT 1 FROM public.events e WHERE e.id = v.event_id)
ON CONFLICT (event_id) DO NOTHING;

-- 2. Nachtrag
INSERT INTO public.event_sensibel (event_id, grund, quelle)
SELECT k.id, k.grund, 'regel'
FROM (
    SELECT e.id, public.sensibel_grund(e.titel, e.beschreibung, e.ort) AS grund
    FROM public.events e
    WHERE coalesce(e.datum_bis, e.datum) >= current_date - 400
      AND NOT EXISTS (SELECT 1 FROM public.event_sensibel_ausnahmen a WHERE a.event_id = e.id)
) k
WHERE k.grund IS NOT NULL
ON CONFLICT (event_id) DO NOTHING;

COMMIT;

-- 3. Kontrolle
SELECT 'gekennzeichnet' AS art, grund, count(*) AS anzahl
FROM public.event_sensibel
GROUP BY grund
UNION ALL
SELECT 'ausnahmen', '–', count(*)
FROM public.event_sensibel_ausnahmen
ORDER BY art, grund;
