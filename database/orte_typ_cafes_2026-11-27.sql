-- Restaurant-Guide: Brunch- und Frühstückslokale von „Restaurant“ zu „Café“ (Auftraggeber, 27.11.2026)
-- Google führt sie als brunch_restaurant/breakfast_restaurant, deshalb standen sie als Restaurant im Guide und
-- fehlten im Filter „Cafés“ (Beispiel Boho Brunch Café). typ_fest = true: imbiss_einteilen.py fasst sie nicht mehr an.
-- Die URLs bleiben gleich (alle Arten liegen unter /guides/restaurants-cafes/…).

begin;

update orte
set typ = 'cafe',
    extras = coalesce(extras, '{}'::jsonb) || jsonb_build_object('typ_fest', true) - 'imbiss_grund'
where typ = 'restaurant'
  and id in (
    'a9d5d70f-dc25-4a0d-bf1f-bad14e7abf4d',  -- Boho Brunch Café (Düsseltal)
    '6320546e-1399-4755-8d48-c2d54e2c558d',  -- BIRDIE & CO. Deli · Café (Altstadt)
    'a6ce2079-3ec6-4f13-8765-3b06afe30a7c',  -- BIRDIE & CO. Deli · Café (Pempelfort)
    '7dac6c60-82b2-493d-a4f2-adddac61ee49',  -- Cloud Kitchen (Karl-Geusen-Straße)
    '9c7b2abd-c42e-487f-871b-5ce72b251e9c',  -- Cloud Kitchen (Münsterstraße)
    '44b1d555-7da8-4076-8ae4-60073d730ce8',  -- Cafe Nane Kahvalti Diyari
    '18fd8c35-b5ea-4cf6-9b49-4a32504bca46',  -- Café BARISTAPAS Brunch & Lunch
    'b72d94bb-b83e-4b74-9edf-07fdd4208f14',  -- David's Café Düsseldorf
    'aa65f0fb-e628-41f2-8d83-85ad2ed10bee',  -- Hyde Brunch Düsseldorf
    'ce9be2e4-3b82-4a45-b3ba-8c4a8f20bf13',  -- Seven Sundays
    '7220bcec-262b-4c11-a7e1-6b48ab6f1933'   -- Meeple und Macchiato (Brettspielcafé)
  );

commit;

-- Prüfung: erwartet 11 Zeilen mit typ = cafe und typ_fest = true
select name, stadtteil, typ, extras->'typ_fest' as typ_fest
from orte
where id in (
  'a9d5d70f-dc25-4a0d-bf1f-bad14e7abf4d', '6320546e-1399-4755-8d48-c2d54e2c558d', 'a6ce2079-3ec6-4f13-8765-3b06afe30a7c',
  '7dac6c60-82b2-493d-a4f2-adddac61ee49', '9c7b2abd-c42e-487f-871b-5ce72b251e9c', '44b1d555-7da8-4076-8ae4-60073d730ce8',
  '18fd8c35-b5ea-4cf6-9b49-4a32504bca46', 'b72d94bb-b83e-4b74-9edf-07fdd4208f14', 'aa65f0fb-e628-41f2-8d83-85ad2ed10bee',
  'ce9be2e4-3b82-4a45-b3ba-8c4a8f20bf13', '7220bcec-262b-4c11-a7e1-6b48ab6f1933'
)
order by name;
