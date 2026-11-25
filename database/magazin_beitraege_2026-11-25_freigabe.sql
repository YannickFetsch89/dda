-- Magazin: magazin_beitraege_2026-11-25 veröffentlichen – ERST nach der Durchsicht der Vorschau. Nur im SQL-/Table-Editor (postgres),
-- nur aus „in_pruefung“, mit grüner Prüfung und allen Pflichtfeldern (Trigger magazin_status_pruefen).

BEGIN;

UPDATE public.magazin_beitraege
SET status = 'veroeffentlicht', veroeffentlicht_am = now(), freigegeben_von = 'Yannick Fetsch'
WHERE slug IN ('top-5-cafes-in-flingern', '10-empfehlungen-fuer-familien-im-dezember') AND status = 'in_pruefung';

COMMIT;

-- Kontrollabfrage – erwartet je Beitrag eine Zeile mit „ok“
SELECT slug, status, veroeffentlicht_am,
       CASE WHEN status = 'veroeffentlicht' AND vorschau_hash IS NULL THEN 'ok' ELSE 'FEHLER' END AS kontrolle
FROM public.magazin_beitraege WHERE slug IN ('top-5-cafes-in-flingern', '10-empfehlungen-fuer-familien-im-dezember') ORDER BY slug;
