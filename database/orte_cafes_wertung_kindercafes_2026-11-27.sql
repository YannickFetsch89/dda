-- Cafés nach dies.das-Wertung + Kindercafés freischalten (Auftraggeber, 27.11.2026)
--
-- 1) Regel: Cafés mit dies.das-Wertung unter 7,0 erscheinen NICHT im Guide (aktiv = false + Vermerk
--    extras.ausgeblendet.regel = 'wertung'). Gilt vorerst nur für Cafés – Restaurants folgen nach ihrer Durchsicht.
--    Ausnahme: Kindercafés (extras.kindercafe) werden immer gezeigt.
--    Die Bild-Auswahlseite hält die Regel beim Speichern ein (Wert ≥ 7 → wieder sichtbar).
-- 2) Die 5 Kindercafés mit Score unter 7 freischalten: Wertung des Auftraggebers, redaktioneller Score 7
--    (extras.score_manuell – die Score-Neuberechnung in flaechensuche.py lässt ihn stehen).

begin;

-- 1) Kindercafés: Wertungen + Freischaltung
update orte o
set aktiv = true,
    qualitaets_score = greatest(coalesce(o.qualitaets_score, 0), 7),
    extras = coalesce(o.extras, '{}'::jsonb)
             || jsonb_build_object('ddd_wertung', v.wert, 'ddd_wertung_hand', v.wert, 'kindercafe', true,
                                   'score_manuell', 'Kindercafé – immer im Guide (27.11.2026)')
from (values
  ('56cc48b7-db23-49d0-b602-9915ad350d88'::uuid, 7.6),  -- Les Petits – Eltern Kind Café (Friedrichstadt)
  ('078672bf-8a3b-4067-9217-c2c5a403ed2b'::uuid, 8.9),  -- Little Bunny (Derendorf)
  ('25ed690b-0353-4f2b-8040-5f55e136929f'::uuid, 7.2),  -- BUDIGO Kindercafé (Neuss)
  ('09fb2bc8-9610-44ec-8a94-14ff65250369'::uuid, 6.8),  -- Kindercafe Zauberwald (Ratingen)
  ('2852623a-d03d-459d-9aed-eafd3cb24f33'::uuid, 5.5)   -- Kindercafé Wunderhaus (Wersten)
) as v(id, wert)
where o.id = v.id;

-- 2) Cafés unter 7,0 ausblenden (ohne Kindercafés)
update orte
set aktiv = false,
    extras = coalesce(extras, '{}'::jsonb)
             || jsonb_build_object('ausgeblendet', jsonb_build_object('grund', 'dies.das-Wertung unter 7,0', 'regel', 'wertung',
                                                                      'datum', '2026-11-27'))
where typ = 'cafe'
  and aktiv = true
  and (extras->>'ddd_wertung')::numeric < 7
  and coalesce(extras->>'kindercafe', '') <> 'true';

commit;

-- Prüfung 1: die 9 Kindercafés – alle aktiv, Score ≥ 7, mit Wertung
select name, stadtteil, aktiv, qualitaets_score, extras->'ddd_wertung' as wertung
from orte where extras->>'kindercafe' = 'true' order by (extras->>'ddd_wertung')::numeric desc;

-- Prüfung 2: wegen Wertung ausgeblendete Cafés (Stand heute 26)
select name, stadtteil, extras->'ddd_wertung' as wertung
from orte where extras->'ausgeblendet'->>'regel' = 'wertung' order by name;

-- Prüfung 3: Cafés im Guide – keines unter 7,0 außer Kindercafés (erwartet: nur Wunderhaus 5,5 und Zauberwald 6,8)
select name, extras->'ddd_wertung' as wertung from orte
where typ = 'cafe' and aktiv and qualitaets_score >= 7 and (extras->>'ddd_wertung')::numeric < 7;
