-- Restaurants nach dies.das-Wertung (Auftraggeber, 28.11.2026, nach Abschluss der Restaurant-Durchsicht)
-- Regel wie bei den Cafés (27.11.): Restaurants mit dies.das-Wertung unter 7,0 erscheinen NICHT im Guide
-- (aktiv = false + Vermerk extras.ausgeblendet.regel = 'wertung'), Kindercafés ausgenommen. Stand heute 157 Restaurants
-- (110 mit eigenem Wert, 47 mit gerechnetem Wert aus „Auswahl passt“).
-- Ausgenommen bis zur Rückfrage: Café de Bretagne (eigener Wert 2,0 – vermutlich Tippfehler).
-- Die Bild-Auswahlseite hält die Regel beim Speichern ein (Wert ≥ 7 → wieder sichtbar).

begin;

update orte
set aktiv = false,
    extras = coalesce(extras, '{}'::jsonb)
             || jsonb_build_object('ausgeblendet', jsonb_build_object('grund', 'dies.das-Wertung unter 7,0', 'regel', 'wertung',
                                                                      'datum', '2026-11-28'))
where typ = 'restaurant'
  and aktiv = true
  and (extras->>'ddd_wertung')::numeric < 7
  and coalesce(extras->>'kindercafe', '') <> 'true'
  and id <> '49ad5469-9c6b-48af-9646-75ee603c92bb';  -- Café de Bretagne (Rückfrage)

commit;

-- Prüfung 1: heute wegen Wertung ausgeblendete Restaurants (erwartet 157)
select count(*) as ausgeblendet from orte
where typ = 'restaurant' and extras->'ausgeblendet'->>'regel' = 'wertung' and extras->'ausgeblendet'->>'datum' = '2026-11-28';

-- Prüfung 2: Restaurants im Guide (aktiv, Score ≥ 7) – erwartet 273, darunter keins unter 7,0 außer Café de Bretagne
select count(*) as im_guide, count(*) filter (where (extras->>'ddd_wertung')::numeric < 7) as unter_7
from orte where typ = 'restaurant' and aktiv and qualitaets_score >= 7;
