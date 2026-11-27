-- Kindercafés (Auftraggeber, 27.11.2026): eigenes Merkmal extras.kindercafe = true.
-- Gemeint sind Eltern-Kind-/Kindercafés mit Spielbereich – NICHT Googles Ausstattung „Kinderfreundlich“
-- (goodForChildren), die auch normale Restaurants mit Hochstuhl tragen. Die Art bleibt „cafe“; ein Filter auf
-- der Website folgt später. Die Orte-Importe mischen extras nur dazu, das Merkmal bleibt also stehen.
-- Keine Tabellenänderung nötig.

begin;

update orte
set extras = coalesce(extras, '{}'::jsonb) || jsonb_build_object('kindercafe', true)
where id in (
  -- im Guide sichtbar (aktiv, Score ≥ 7)
  'a8305223-75e2-4a93-87ad-7676a976fd2f',  -- Bude eins (Pempelfort)
  '194d3ef5-deaa-4bea-9428-354f70998992',  -- Chiquito (Benrath)
  '9b09fad0-0a3b-4b44-871a-345ed4a2e314',  -- HAPPY KIDS (Düsseltal)
  '39e3f9c7-91ff-421f-87c3-efb1dedd71db',  -- Little Ma‘Vi (Neuss)
  -- im Bestand, aber nicht im Guide (Score unter 7) – Merkmal schon setzen, Sichtbarkeit entscheidet der Auftraggeber
  '56cc48b7-db23-49d0-b602-9915ad350d88',  -- Les Petits – Eltern Kind Café (Friedrichstadt), Score 6
  '078672bf-8a3b-4067-9217-c2c5a403ed2b',  -- Little Bunny (Derendorf), Score 5
  '2852623a-d03d-459d-9aed-eafd3cb24f33',  -- Kindercafé Wunderhaus (Wersten), Score 5
  '09fb2bc8-9610-44ec-8a94-14ff65250369',  -- Kindercafe Zauberwald (Ratingen), Score 4
  '25ed690b-0353-4f2b-8040-5f55e136929f'   -- BUDIGO Kindercafé (Neuss), Score 4
);

commit;

-- Prüfung: 9 Zeilen, 4 davon aktiv mit Score ≥ 7
select name, stadtteil, aktiv, qualitaets_score
from orte
where extras->>'kindercafe' = 'true'
order by aktiv desc, qualitaets_score desc, name;
