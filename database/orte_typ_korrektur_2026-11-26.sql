-- Restaurant-Guide: Art von Hand korrigiert (Auftraggeber, 26.11.2026)
-- typ_fest = true: scraper/orte/imbiss_einteilen.py fasst diese Orte nicht mehr an.
-- Die URLs bleiben gleich (alle drei Arten liegen unter /guides/restaurants-cafes/…).

begin;

-- ARTA - Brunch & Café Düsseldorf: Restaurant → Café
update orte
set typ = 'cafe',
    extras = coalesce(extras, '{}'::jsonb) || jsonb_build_object('typ_fest', true) - 'imbiss_grund'
where id = '93c21dd2-32ef-4bc8-a39a-c44d7f5de492' and typ = 'restaurant';

-- Barbado Sushi and Bowls: Restaurant → Schnellimbiss
update orte
set typ = 'imbiss',
    extras = coalesce(extras, '{}'::jsonb) || jsonb_build_object('typ_fest', true, 'imbiss_grund', 'von Hand (26.11.2026)')
where id = '27d67718-049f-42b0-a3d5-ec87b2753033' and typ = 'restaurant';

commit;

-- Prüfung: erwartet ARTA = cafe, Barbado = imbiss, beide typ_fest = true
select name, typ, extras->'typ_fest' as typ_fest
from orte
where id in ('93c21dd2-32ef-4bc8-a39a-c44d7f5de492', '27d67718-049f-42b0-a3d5-ec87b2753033');
