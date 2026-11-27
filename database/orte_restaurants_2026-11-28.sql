-- Restaurants (Auftraggeber, 28.11.2026, Abschluss der Restaurant-Durchsicht)
-- 1) Stadtstrand Düsseldorf ausblenden (cooler Ort, aber Strandbar statt Restaurant), Zeile bleibt im Bestand
-- 2) 3 Takumi-Texte: klein und schlicht eingerichtet, aber mit das beste und authentischste japanische Essen der Stadt

begin;

update orte
set aktiv = false,
    extras = coalesce(extras, '{}'::jsonb) || jsonb_build_object('ausgeblendet', jsonb_build_object('grund', 'kein Restaurant (Strandbar)', 'datum', '2026-11-28'))
where id = '78f73229-42ec-4abb-bb48-f3b3fe880f8f';  -- Stadtstrand-Düsseldorf am Tonhallenufer

create table if not exists public.orte_texte_sicherung_rest_2026_11_28 as
select id, name, beschreibung, now() as gesichert_am from orte where false;
alter table public.orte_texte_sicherung_rest_2026_11_28 enable row level security;
insert into public.orte_texte_sicherung_rest_2026_11_28 (id, name, beschreibung, gesichert_am)
select id, name, beschreibung, now() from orte where id in (
  '94f363db-6e02-4089-9d0b-291955d105b6',
  '13218082-4340-4f4f-bbef-d0329b5b188c',
  'c0efc332-f443-4449-b756-ee4e45d7c1c9'
);

-- Takumi (Immermannstraße, Stadtmitte)
update orte set beschreibung = replace($t$Wer in Stadtmitte Lust auf **warme Ramen** hat, ist bei Takumi richtig. Die Karte lebt von Variationen wie **Tonkotsu und Tantanmen**, dazu gibt es Teriyaki-Hähnchen. Das Ramen-Baukastensystem ist übersichtlich aufgebaut, sodass auch Einsteiger in die asiatische Küche schnell ihre Lieblingskombination finden. Die Brühe ist kräftig, das Verhältnis von Nudeln und Einlage stimmt, und die Hähnchen-Variante ist außen knusprig und innen zart. Auch die veganen Gyoza kommen angenehm knusprig auf den Tisch, und die Yuzu-Limonade ist eine erfrischende Ergänzung.

Groß ist das Takumi nicht, und mit seiner Einrichtung will es auch niemanden beeindrucken. Dafür bekommt man hier eines der besten und **authentischsten japanischen Essen** der Stadt. Das Lokal ist lebhaft, mit einer **Terrasse** für lauwarme Tage und Sitznischen, die ein wenig Privatsphäre bieten. Das Personal ist freundlich und das Essen kommt schnell an den Tisch. Ideal für einen entspannten Abend mit Freunden oder einen **schnellen, guten Lunch**.$t$, chr(13), '') where id = '94f363db-6e02-4089-9d0b-291955d105b6';

-- Takumi 2nd Tonkotsu (Oststraße, Pempelfort)
update orte set beschreibung = replace($t$Wer in Pempelfort Lust auf richtig gute **Nudelsuppe** hat, ist im Takumi 2nd Tonkotsu gut aufgehoben. Die Küche ist **japanisch**, und neben den Ramen gibt es Teigtaschen und Teriyaki-Gerichte. Die Brühe ist extrem schmackhaft, und wer die Ramen probiert, versteht schnell, warum Gäste immer wieder zurückkommen. Auch die Gyoza sind einen Versuch wert, denn sie kommen **knusprig und lecker** auf den Tisch. Die Karte ist groß und bietet auch einige vegetarische und **vegane Optionen**.

Der Laden selbst ist recht klein und schlicht, wer ein schickes Interieur sucht, ist hier falsch. Wer dagegen **authentische japanische Küche** auf richtig hohem Niveau erleben möchte, ist genau richtig. An warmen Tagen lohnt sich ein Platz im **Hinterhof**. Der Service ist freundlich, hilfsbereit und oft erstaunlich schnell, auch wenn man vor vollen Abenden etwas Geduld mitbringen sollte.$t$, chr(13), '') where id = '13218082-4340-4f4f-bbef-d0329b5b188c';

-- Takumi Chicken & Veggie (Klosterstraße, Pempelfort)
update orte set beschreibung = replace($t$Wer Ramen mag, sollte bei Takumi Chicken & Veggie in Pempelfort vorbeischauen. Die klassischen Gerichte werden hier kreativ interpretiert, und das Angebot reicht von Hühnerbrühe bis zu **Gemüsebrühe mit Vollkornnudeln**. Das **Miso Ramen** gehört zu den Lieblingen: Die Brühe ist kräftig und aromatisch, das Fleisch zergeht auf der Zunge und das Gemüse wirkt frisch. Auch die Gyoza, die es ebenfalls in veganer Variante gibt, begeistern. Wer es vegan mag, findet mit dem Special vegan Ramen und dem **veganen Tan Tan Men** gleich mehrere passende Optionen. Das Chicken Ramen mit **knusprigem Hähnchen Schnitzel** ist saftig und zart und passt perfekt zur würzigen Brühe.

Viel Platz gibt es nicht, und auch die Einrichtung ist eher zweckmäßig als besonders. Das spielt aber kaum eine Rolle, denn auf den Teller kommt japanisches Essen, wie man es **besser und authentischer** in Düsseldorf kaum findet. Drinnen herrscht oft viel Betrieb, doch das Team bleibt aufmerksam und freundlich und nimmt sich Zeit, Brühen und Beilagen zu erklären. Japanische Musik und japanisch gesprochene Gespräche sorgen für eine **angenehm authentische Stimmung**.$t$, chr(13), '') where id = 'c0efc332-f443-4449-b756-ee4e45d7c1c9';

commit;

-- Prüfung
select name, aktiv, extras->'ausgeblendet'->>'grund' as ausgeblendet from orte where id = '78f73229-42ec-4abb-bb48-f3b3fe880f8f';
select count(*) filter (where beschreibung like '%**%') as texte_mit_fett from orte
where id in (select id from public.orte_texte_sicherung_rest_2026_11_28);
