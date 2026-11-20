-- Magazin: Startbeiträge veröffentlichen (Plan Redaktion, Schritt 6) – ERST nach der Durchsicht der Vorschau.
-- Der Trigger magazin_status_pruefen lässt das nur im SQL-Editor/Table-Editor (Rolle postgres) zu, nur aus
-- „in_pruefung“, nur mit grüner Prüfung und allen Pflichtfeldern. Die Pipeline (service_role) kann es nicht.
-- Der Launch-Beitrag ist auf gestern datiert (Wunsch des Auftraggebers), der Weihnachtsmarkt-Beitrag auf jetzt.
-- Sichtbar wird beides nach ein paar Minuten (Cache); solange MAGAZIN_VERLINKT aus ist, bleiben die Seiten
-- noindex und unverlinkt.

BEGIN;

UPDATE public.magazin_beitraege
SET status = 'veroeffentlicht', veroeffentlicht_am = '2026-11-19 10:00:00+01', freigegeben_von = 'Yannick Fetsch'
WHERE slug = 'willkommen-im-magazin' AND status = 'in_pruefung';

UPDATE public.magazin_beitraege
SET status = 'veroeffentlicht', veroeffentlicht_am = now(), freigegeben_von = 'Yannick Fetsch'
WHERE slug = 'die-schoensten-weihnachtsmaerkte-in-duesseldorf' AND status = 'in_pruefung';

COMMIT;

-- Kontrollabfrage – erwartet zwei Zeilen mit „ok“
SELECT slug, status, veroeffentlicht_am, freigegeben_von, freigegeben_am,
       CASE WHEN status = 'veroeffentlicht' AND vorschau_hash IS NULL AND freigegeben_am IS NOT NULL
            THEN 'ok' ELSE 'FEHLER' END AS kontrolle
FROM public.magazin_beitraege
WHERE slug IN ('willkommen-im-magazin', 'die-schoensten-weihnachtsmaerkte-in-duesseldorf')
ORDER BY slug;
