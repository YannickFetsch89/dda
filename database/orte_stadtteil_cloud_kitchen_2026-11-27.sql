-- Cloud Kitchen: beide Filialen standen fälschlich als „Unterbilk“ (Auftraggeber, 27.11.2026).
-- Stadtteil nach Postleitzahl (web/lib/plz-stadtteil.json): 40231 → Lierenfeld, 40470 → Mörsenbroich.
-- Slugs (…-unterbilk, …-unterbilk-b) bleiben, damit die Adressen ohne Weiterleitung gültig bleiben.

begin;

update orte set stadtteil = 'Lierenfeld'
where id = '7dac6c60-82b2-493d-a4f2-adddac61ee49' and adresse like 'Karl-Geusen-Straße 167%';

update orte set stadtteil = 'Mörsenbroich'
where id = '9c7b2abd-c42e-487f-871b-5ce72b251e9c' and adresse like 'Münsterstraße 261%';

commit;

-- Prüfung: erwartet Lierenfeld und Mörsenbroich
select name, adresse, stadtteil from orte
where id in ('7dac6c60-82b2-493d-a4f2-adddac61ee49', '9c7b2abd-c42e-487f-871b-5ce72b251e9c');
