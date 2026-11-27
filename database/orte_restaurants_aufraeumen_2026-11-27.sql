-- Restaurants aufräumen (Auftraggeber, 27.11.2026, Durchsicht der Restaurants)
-- 1) Gelato49 und Ghirloni ausblenden (Eisdielen → eigener Eis-Guide im Frühjahr/Sommer), Zeilen bleiben im Bestand
-- 2) Hamtorkrug (Neuss) wird Kneipe (Unterart „kneipe“ ist schon gesetzt); typ_fest schützt vor imbiss_einteilen.py.
--    Neue Adresse /guides/kneipen-bars/hamtorkrug-neuss, die alte Restaurant-Adresse antwortet danach mit 404
--    (eine Adresse je Ort, lib/pfad-pruefung.ts).
-- 3) 3 Texte angepasst (Grafengrün, Gut Knittkuhle, Taj Palace), alter Text in Sicherungstabelle

begin;

-- 1) Eisdielen ausblenden
update orte o
set aktiv = false,
    extras = coalesce(o.extras, '{}'::jsonb) || jsonb_build_object('ausgeblendet', jsonb_build_object('grund', 'Eisdiele – eigener Eis-Guide später', 'datum', '2026-11-27'))
where o.id in (
  '3d077203-2940-4e7e-b97d-f5056a81a695',  -- Gelato49 (Altstadt)
  'c36d4fd0-c1e3-4bf5-8d77-ae757703b58c'   -- Ghirloni Eismanufaktur (Golzheim)
);

-- 2) Hamtorkrug → Kneipe
update orte
set typ = 'kneipe',
    extras = coalesce(extras, '{}'::jsonb) || jsonb_build_object('typ_fest', true, 'unterart', 'kneipe', 'vorher_typ', 'restaurant') - 'imbiss_grund'
where id = 'af4572ff-be12-42be-b971-b548e85c2ea1' and typ = 'restaurant';

-- 3) Texte
create table if not exists public.orte_texte_sicherung_rest_c_2026_11_27 as
select id, name, beschreibung, now() as gesichert_am from orte where false;
alter table public.orte_texte_sicherung_rest_c_2026_11_27 enable row level security;
insert into public.orte_texte_sicherung_rest_c_2026_11_27 (id, name, beschreibung, gesichert_am)
select id, name, beschreibung, now() from orte where id in (
  'a9a5a30d-c3be-4e47-8caa-722c3cd8d4f9',
  '68f0bca8-1aac-49bc-816c-757e1fa0c931',
  '3d593afa-25c4-474a-9f70-cd2a6a17f721'
);

-- grafengrün. restaurant (Grafenberg)
update orte set beschreibung = replace($t$Das Grafengrün liegt direkt auf dem Gelände der **Pferderennbahn in Grafenberg**, und genau dieser Blick macht den Besuch aus. Die **große Terrasse** bietet eine weite Sicht über die Rennbahn, und wer hier sitzt, lässt die Gedanken gerne schweifen. Drinnen und draußen gibt es Plätze, und die Räume wirken angenehm, ohne Hektik.

Das Essen wird frisch zubereitet und ist schmackhaft, ohne kompliziert sein zu wollen; die Auswahl reicht vom **Frühstück über Lunch** und Nachmittagskaffee bis zum Dinner. **Flammkuchen** wie „Süße Ziege“ oder „Italien“ sind ein schöner Tipp, dazu passt ein Glas Wein auf der Terrasse.

Der Service ist aufmerksam und herzlich, auch auf Englisch, und auf besondere Wünsche wird gerne eingegangen. Das Grafengrün ist zudem eine beliebte **Eventlocation**, etwa für Hochzeiten und Familienfeiern, mit ansprechenden Räumen und gediegener Tischdekoration. Deshalb können die Öffnungszeiten abweichen, am besten ruft man vorher kurz **an**. An **Renntagen** kann man hier meist nicht reservieren.$t$, chr(13), '') where id = 'a9a5a30d-c3be-4e47-8caa-722c3cd8d4f9';

-- Gut Knittkuhle (Grafenberg)
update orte set beschreibung = replace($t$Mitten in der Landschaft in Grafenberg liegt Gut Knittkuhle, ein **rustikaler Landgasthof**, der besonders mit seinem Außenbereich punktet. Der **Biergarten** ist ruhig gelegen und bietet einen schönen Blick über die Felder, im Sommer sitzt man dort richtig gut. Auch für **Kinder** ist der Außenbereich toll, denn sie haben hier einen kleinen **eigenen Spielplatz**.

Die Küche serviert herzhafte Gerichte und **mediterrane Schmankerl**, das Essen kommt ansprechend angerichtet auf den Tisch und schmeckt vielen Gästen richtig gut. Der Service ist sehr aufmerksam und freundlich, sodass man sich schnell willkommen fühlt. Innen ist es gemütlich und ebenfalls rustikal, dazu kommt eine schöne Weinauswahl, bei der besonders die **Weißweine** überzeugen. Ideal für ein entspanntes Mittagessen mit der Familie oder für Feiern.$t$, chr(13), '') where id = '68f0bca8-1aac-49bc-816c-757e1fa0c931';

-- Indian Restaurant Taj Palace (Golzheim)
update orte set beschreibung = replace($t$Wer **authentisch indisch essen** möchte und dabei nicht allzu viel Wert auf die Inneneinrichtung legt, ist im Taj Palace in Golzheim genau richtig. Hier überzeugt nicht das Ambiente, sondern die **Küche**: Das Essen kommt frisch auf den Tisch und duftet schon beim Eintreten herrlich nach Gewürzen. Besonders die **Tandoori-Hühnchen** sind zart und haben eine würzige Marinade, die begeistert.

Die Speisekarte bietet eine gute Auswahl, sodass für jeden Geschmack etwas dabei ist, und die Preise sind fair. Das Personal ist **freundlich, aufmerksam und professionell**, ohne aufdringlich zu wirken. Auch **ohne Reservierung** bekommt man am Abend oft einen Tisch, was den Besuch spontan macht.$t$, chr(13), '') where id = '3d593afa-25c4-474a-9f70-cd2a6a17f721';

commit;

-- Prüfung
select name, typ, aktiv, extras->'ausgeblendet'->>'grund' as ausgeblendet from orte
where id in ('3d077203-2940-4e7e-b97d-f5056a81a695', 'c36d4fd0-c1e3-4bf5-8d77-ae757703b58c', 'af4572ff-be12-42be-b971-b548e85c2ea1');
select count(*) filter (where beschreibung like '%**%') as texte_mit_fett from orte
where id in (select id from public.orte_texte_sicherung_rest_c_2026_11_27);
