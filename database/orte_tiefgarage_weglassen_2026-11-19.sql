-- Ortsseite „Tiefgarage PSD BANK DOME“ wieder entfernen (Auftraggeber 19.11.2026: weglassen)
-- Plan docs/plan-locations-2026-11-18.md, 3.4 (Abschalten/Löschen nur mit Weiterleitung, Zuordnung ausdrücklich lösen)
-- Stand: 2026-11-19 · Im Supabase SQL-Editor ausführen. Wiederholbar.
-- Die Seite war nie öffentlich (Schritt 3 ist nicht live); der Schutz-Trigger verlangt trotzdem eine Weiterleitung.
-- Ziel: die Spielstätte PSD Bank Dome. Der Slug bleibt damit gesperrt und wird nicht neu vergeben.

BEGIN;

-- 1) Weiterleitung zuerst (sonst bricht der Trigger das Löschen ab)
INSERT INTO public.ort_weiterleitungen (alter_slug, ziel_ort_id, grund)
SELECT 'tiefgarage-psd-bank-dome', (SELECT id FROM public.orte WHERE slug = 'psd-bank-dome'),
       'Ortsseite weggelassen (Auftraggeber 19.11.2026)'
WHERE EXISTS (SELECT 1 FROM public.orte WHERE slug = 'tiefgarage-psd-bank-dome')
ON CONFLICT (alter_slug) DO NOTHING;

-- 2) Zuordnung der Events ausdrücklich lösen (automatische Läufe schreiben nie NULL)
UPDATE public.events SET ort_id = NULL
WHERE ort_id = (SELECT id FROM public.orte WHERE slug = 'tiefgarage-psd-bank-dome');

-- 3) Zeile löschen
DELETE FROM public.orte WHERE slug = 'tiefgarage-psd-bank-dome';

COMMIT;

-- Kontrolle: Zeile weg (0), Weiterleitung da (1)
SELECT
  (SELECT count(*) FROM public.orte WHERE slug = 'tiefgarage-psd-bank-dome')                 AS zeile,
  (SELECT count(*) FROM public.ort_weiterleitungen WHERE alter_slug = 'tiefgarage-psd-bank-dome') AS weiterleitung;
