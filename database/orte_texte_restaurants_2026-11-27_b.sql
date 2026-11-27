-- Restaurant-Guide: 6 neue Texte (Orte ohne Text) + 5 angepasste Texte nach Stichpunkten (Auftraggeber, 27.11.2026)
-- Alter Text in Sicherungstabelle; replace(…, chr(13), '') hält Windows-Umbrüche aus den Texten heraus.

begin;

create table if not exists public.orte_texte_sicherung_rest_2026_11_27 as
select id, name, beschreibung, now() as gesichert_am from orte where false;
alter table public.orte_texte_sicherung_rest_2026_11_27 enable row level security;
insert into public.orte_texte_sicherung_rest_2026_11_27 (id, name, beschreibung, gesichert_am)
select id, name, beschreibung, now() from orte where id in (
  '8dbf0f8f-459f-47c4-ae49-8d8c8ab8d034',
  '4946b13d-7c81-43c1-bcfd-4ba6c2731610',
  'bf65577b-5c0a-4cbc-80d8-6ff029a98973',
  '2ff1ef5e-fcdb-40be-8e1d-d1fdc4584714',
  'b72d94bb-b83e-4b74-9edf-07fdd4208f14',
  '4a739a47-9430-432a-b738-e2cce3e1a6a5',
  '50589e4b-fc1c-4b94-9019-8636810990ef',
  '49ad5469-9c6b-48af-9646-75ee603c92bb',
  'a9a8cc32-62ef-4607-935b-a75491f48e75',
  '97c14294-3055-4dec-8d89-f29dbd60163e',
  '3a921404-4e4f-43dd-83a0-ee6745b23588'
);

-- Sina Pizzeria (Neuss-Weckhoven) – neu
update orte set beschreibung = replace($t$Die Sina Pizzeria in Neuss-Weckhoven ist ein **unkomplizierter Imbiss** für den Hunger zwischendurch. Neben Pizza gibt es hier vor allem **Döner und Dürüm**, und die kommen schön saftig auf den Teller. Wer lieber mit Messer und Gabel isst, greift zum Dönerteller.

Das Team ist **ausgesprochen freundlich** und nimmt sich Zeit für seine Gäste, sodass man sich schnell willkommen fühlt. Wer nicht bleiben möchte, nimmt sein Essen einfach **zum Mitnehmen** mit. Ein verlässlicher Anlaufpunkt im Viertel, auch für Familien mit Kindern.$t$, chr(13), '') where id = '8dbf0f8f-459f-47c4-ae49-8d8c8ab8d034';

-- Bürgerhaus Ratingen – neu
update orte set beschreibung = replace($t$Das Bürgerhaus am **Ratinger Marktplatz** steht für ehrliche, bodenständige Küche ohne Schnickschnack. Die Karte ist angenehm übersichtlich, und was draufsteht, überzeugt: Ein echtes Highlight ist die **Schweinshaxe**, die so beliebt ist, dass sie manchmal ausverkauft ist. Auch die Schnitzel kommen gut an, und zum Abschluss lohnt sich der **Kaiserschmarrn**, am besten zum Teilen.

Dazu gibt es frisch gezapftes Bier in mehreren Sorten, je nach Saison auch mit besonderen Bieren. Der Service ist **freundlich, flott und aufmerksam**, auch bei größeren Gruppen, und die Stimmung ist entspannt. Weil das Haus oft gut gebucht ist, lohnt sich eine **Reservierung**.$t$, chr(13), '') where id = '4946b13d-7c81-43c1-bcfd-4ba6c2731610';

-- La Cucina (Neuss) – neu
update orte set beschreibung = replace($t$Von außen eher unscheinbar, drinnen herzlich italienisch: Das La Cucina in Neuss ist ein **Italiener**, bei dem man sich ein bisschen wie im Urlaub fühlt. Im Mittelpunkt steht die **Pizza**, die viele Gäste begeistert, dazu gibt es Pasta und Vorspeisen. Und wenn der Pizzabäcker dabei mal ein Lied anstimmt, gehört das hier einfach dazu.

Der **Service ist ausgesprochen freundlich** und zuvorkommend, und auch größere Runden, etwa zum Geburtstag, sind hier gut aufgehoben. Bei gutem Wetter lockt die **Terrasse**, und wer lieber zu Hause isst, nimmt sein Essen mit. Ein sympathischer Italiener für einen entspannten Abend mit Familie oder Freunden.$t$, chr(13), '') where id = 'bf65577b-5c0a-4cbc-80d8-6ff029a98973';

-- Küppers Bierstuben (Heerdt) – neu
update orte set beschreibung = replace($t$Die Küppers Bierstuben in Heerdt sind eine Adresse für **gutbürgerliche Küche** und großzügige Portionen. Bekannt ist das Haus für seine **Schnitzel**, allen voran das Schnitzel „Air France“ mit Camembert, Preiselbeeren und Sauce Hollandaise, dazu goldbraune Bratkartoffeln. Auch die Haxenpfanne und das hausgemachte **Schoko-Soufflé** sind eine Empfehlung.

Von außen wirkt das alte Gebäude eher unscheinbar, drinnen ist es aber **richtig gemütlich**, und das Team empfängt seine Gäste mit viel Herz. Der Service ist schnell und aufmerksam, und auch Familien mit Kindern sind willkommen. Wer lieber draußen sitzt, findet zudem eine **Terrasse**.$t$, chr(13), '') where id = '2ff1ef5e-fcdb-40be-8e1d-d1fdc4584714';

-- David's Café (Gerresheim) – neu
update orte set beschreibung = replace($t$David's Café in Gerresheim ist ein **italienisches Café**, das weit über Pasta und Pizza hinausgeht. Zum Kaffee gibt es **Cannoli, Sfogliatelle**, Cornetti und Kuchen, und wer es herzhaft mag, bestellt Panini, Focaccia oder Piadina. Dazu kommen eine eigene **Frühstückskarte**, auch mit italienischem Frühstück, und hausgemachte Limonaden.

Der Kaffee ist **richtig gut**, die Einrichtung modern und schnörkellos und trotzdem gemütlich, und vor der Tür gibt es ein paar Plätze im Freien. Das Team ist herzlich und mit viel Liebe bei der Sache. Wenn es voll ist, nimmt man sich die Leckereien einfach **zum Mitnehmen** mit. Mit der Bahn ist man hier oft besser dran als mit dem Auto, denn Parkplätze sind knapp.$t$, chr(13), '') where id = 'b72d94bb-b83e-4b74-9edf-07fdd4208f14';

-- Pizzeria Da Christian (Neuss-Grefrath) – neu
update orte set beschreibung = replace($t$Die Pizzeria Da Christian in Neuss-Grefrath ist eine kleine **Stehpizzeria** mit großem Herz. Hier dreht sich alles um **italienische Pizza**, gebacken, wie es sich gehört, dazu gibt es Nudeln, Pizzabrötchen und frischen Salat. Extrawünsche werden gern erfüllt, und die Preise sind **fair und günstig**.

Das Lokal ist klein, Platz gibt es nur für wenige Gäste am Hochtisch, viele nehmen ihre Pizza daher **mit nach Hause** oder lassen sie liefern. Die Familie hinter dem Tresen ist ausgesprochen **freundlich und herzlich**, sodass man gern wiederkommt.$t$, chr(13), '') where id = '4a739a47-9430-432a-b738-e2cce3e1a6a5';

-- Café Bakers (Heerdt) – angepasst
update orte set beschreibung = replace($t$Auch wenn der Name nach Kaffee und Kuchen klingt: Das Café Bakers im Herzen von Heerdt ist vielmehr ein **Restaurant mit vollwertiger Speisekarte**, und deshalb findet man es bei uns auch in dieser Kategorie. Auf der Karte stehen unter anderem **Suppen, Fisch und Salate**, mittags gibt es einen Mittagstisch mit wechselnden Gerichten, und wer früh kommt, wird beim Frühstück mehr als satt. Alles ist **frisch und selbstgemacht**, und die Kuchen sind ein Highlight, das man sich unbedingt für den Nachtisch aufheben sollte.

Drinnen sorgt stilvolle, leise Hintergrundmusik für eine entspannte Stimmung, im **Außenbereich unter Sonnenschirmen** lässt es sich wunderbar draußen sitzen. Der Service ist **aufmerksam und herzlich**, man fühlt sich schnell wohl, fast wie im Urlaub. Ideal für ein entspanntes Essen unter Freunden oder eine kleine Auszeit vom Alltag.$t$, chr(13), '') where id = '50589e4b-fc1c-4b94-9019-8636810990ef';

-- Café de Bretagne (Altstadt) – angepasst
update orte set beschreibung = replace($t$Wer bei dem Namen an Milchkaffee und Croissants denkt, liegt daneben: Das Café de Bretagne in der Altstadt ist ein **Meeresfrüchte-Restaurant**, in dem sich alles um das Meer dreht. **Bretonische Muscheln, Austern** und Hummer stehen im Mittelpunkt, dazu kommen Aufläufe und Fischgerichte. Die Austernauswahl ist groß, und das Brot mit **Algenmayonnaise** ist eine schöne Ergänzung, die man extra bestellt. Wer sich für Fisch entscheidet, bekommt frische Ware, die hübsch angerichtet auf den Tisch kommt.

Die Weinkarte hat hervorragende Tropfen, etwa einen **Sancerre**, der gut zum Seafood passt. Zum Abschluss lohnt sich die **Crème brûlée**. Das Bistro ist hell und charmant, perfekt für einen entspannten **Abend zu zweit** oder ein Essen mit Freunden.$t$, chr(13), '') where id = '49ad5469-9c6b-48af-9646-75ee603c92bb';

-- Cuvée Flingern – angepasst
update orte set beschreibung = replace($t$Das Cuvée in Flingern Nord ist ein schönes Lokal für einen **entspannten Abend mit Freunden**. Besonders gemütlich ist es draußen auf der Terrasse oder im netten Innenhof, doch auch der Innenraum überzeugt mit einer **warmen, lockeren Atmosphäre**. Das Publikum ist eher jung, der Service ebenso, freundlich und unkompliziert.

Das Cuvée ist ein **geselliger Ort**, an dem es durchaus auch mal etwas lauter zugehen kann, wer einen ganz ruhigen Abend sucht, sollte das wissen. Auf der Karte stehen Gerichte, die gut und frisch zubereitet sind, ohne spektakulär daherzukommen. Wer gerne Wein trinkt, findet eine **reichhaltige Weinkarte**, dazu gibt es viele alkoholfreie Biere und Alternativen.$t$, chr(13), '') where id = 'a9a8cc32-62ef-4607-935b-a75491f48e75';

-- Da Giacomo (Gerresheim) – angepasst
update orte set beschreibung = replace($t$Wer in Gerresheim einen Abend mit **italienischer Küche** verbringen möchte, ist bei Da Giacomo gut aufgehoben. Die Speisen sind traditionell gehalten, schön angerichtet und frisch zubereitet, und dazu gibt es eine **große Auswahl an Weinen**, bei der man sich gerne beraten lässt. Die Karte ist überschaubar, doch was draufsteht, überzeugt, und mit der **Tageskarte** kommt noch mehr Abwechslung auf den Tisch.

Innen ist das Lokal eher klassisch und schlicht gehalten, sauber und familiär, aber ohne besondere Highlights. Der eigentliche Trumpf ist die **große Terrasse**: Bei gutem Wetter sitzt man hier draußen besonders schön, ein Platz im Freien ist sehr zu empfehlen. Der Service ist aufmerksam und zuvorkommend, ideal für besondere Anlässe oder einen **Abend zu zweit**.$t$, chr(13), '') where id = '97c14294-3055-4dec-8d89-f29dbd60163e';

-- dreiRaum Bistro (Oberbilk) – angepasst
update orte set beschreibung = replace($t$Das dreiRaum Bistro in Oberbilk ist ein kleines, **urig gemütliches Lokal** mit eigener Bar und gemusterten Tapeten, das man sofort ins Herz schließt. Die Karte bietet für jeden etwas: vom Frühstück bis zu internationaler Küche, und sie wirkt angenehm überschaubar statt überladen. Besonders beliebt sind die **Fettuccine mit Trüffel** und die Rinderfiletstreifen, dazu knusprige Hähnchenschnitzel und zum Start das Brot mit Aioli. Zum Abschluss lohnt das **Spekulatius Tiramisu**, und auch die Kuchen sehen verlockend aus.

Bei gutem Wetter lockt ein **schöner Außenbereich**, in dem man draußen frühstücken oder den Abend ausklingen lassen kann. Der Service ist aufmerksam und freundlich, der Empfang herzlich, und die Gerichte kommen hübsch angerichtet auf den Tisch. Ideal für einen gemütlichen Abend zu zweit oder zu dritt, am besten mit Reservierung, und für ein **entspanntes Frühstück** mit etwas Zeit.$t$, chr(13), '') where id = '3a921404-4e4f-43dd-83a0-ee6745b23588';

commit;

-- Prüfung: 11 Texte, alle mit Fett
select count(*) as gesetzt, count(*) filter (where beschreibung like '%**%') as mit_fett
from orte where id in (select id from public.orte_texte_sicherung_rest_2026_11_27);
