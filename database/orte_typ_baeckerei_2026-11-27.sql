-- Neue Art „baeckerei“ (Auftraggeber, 27.11.2026): Bäckereien bleiben im Datenbestand, erscheinen aber nirgends auf der
-- Website (Guide, Karte, Suche, Sitemap und Detailseiten fragen nur ausdrücklich genannte Arten ab – eine Bäckerei-Seite
-- unter /guides/restaurants-cafes/… antwortet danach mit 404).
-- typ_fest = true: imbiss_einteilen.py fasst umgestellte Orte nicht mehr an.

begin;

-- 1) Art erlauben (bisherige Liste aus orte_spielstaetten_2026-11-19.sql + 'baeckerei')
ALTER TABLE public.orte DROP CONSTRAINT IF EXISTS orte_typ_check;
ALTER TABLE public.orte
  ADD CONSTRAINT orte_typ_check CHECK (typ IN (
    'restaurant', 'imbiss', 'cafe', 'kneipe', 'club',
    'spielplatz', 'ausflug', 'wochenendtipp', 'weihnachtsmarkt', 'spielstaette', 'baeckerei'
  ));

-- 2) Backbrüder - Glutenfreie Bio-Bäckerei (Pempelfort): Café → Bäckerei
update orte
set typ = 'baeckerei',
    extras = coalesce(extras, '{}'::jsonb) || jsonb_build_object('typ_fest', true) - 'imbiss_grund'
where id = '839477cd-6066-46a5-89b1-83e0e125a742' and typ = 'cafe';

commit;

-- Prüfung: Regel enthält 'baeckerei'; Backbrüder hat typ = baeckerei
SELECT pg_get_constraintdef(oid) AS regel FROM pg_constraint
WHERE conrelid = 'public.orte'::regclass AND contype = 'c' AND conname = 'orte_typ_check';
select name, typ, extras->'typ_fest' as typ_fest from orte where id = '839477cd-6066-46a5-89b1-83e0e125a742';
