-- Cafés aufräumen (Auftraggeber, 27.11.2026) – nach der Durchsicht aller Cafés in der Bild-Auswahlseite
-- 1) 12 Orte aus dem Guide nehmen: aktiv = false + Vermerk extras.ausgeblendet (Zeilen bleiben im Datenbestand;
--    Eisdielen kommen im Frühjahr/Sommer in einen eigenen Guide). Kein Import schaltet bestehende Orte wieder ein.
-- 2) 12 Texte neu bzw. überarbeitet (Stichpunkte des Auftraggebers), alter Text in Sicherungstabelle.

begin;

-- 1) Ausblenden
update orte o
set aktiv = false,
    extras = coalesce(o.extras, '{}'::jsonb) || jsonb_build_object('ausgeblendet', jsonb_build_object('grund', v.grund, 'datum', '2026-11-27'))
from (values
  ('2b3cc32d-8817-4505-9092-f229bafcee46'::uuid, 'Eisdiele – eigener Eis-Guide später'),  -- Café Eisgold (Ratingen)
  ('4dcf108a-cd46-41ed-bb23-2998f3866c40'::uuid, 'Eisdiele – eigener Eis-Guide später'),  -- Eis Café Roma (Altstadt)
  ('8f894f40-8aac-458b-a496-c391d0587769'::uuid, 'Eisdiele – eigener Eis-Guide später'),  -- Eiscafe Claudio Eisdiele Ratingen
  ('b8587b33-cb7f-4cf8-b85e-98ab5feb2d14'::uuid, 'Eisdiele – eigener Eis-Guide später'),  -- Eiscafé Antifora (Derendorf)
  ('9cf9de14-6af3-44f2-a99c-2457e23c5f33'::uuid, 'Eisdiele – eigener Eis-Guide später'),  -- Eiscafé Stefan da Roberto (Stadtmitte)
  ('da056454-bf36-4c56-83f9-c4125839a61c'::uuid, 'Eisdiele – eigener Eis-Guide später'),  -- Eiskult Pempelfort
  ('53d581e9-2848-4b40-9ee3-311fce74e291'::uuid, 'Eisdiele – eigener Eis-Guide später'),  -- Eiscafé Tiramisu (Neuss)
  ('9d3b2dd1-cb2b-4a69-9af9-e5652e078d87'::uuid, 'Eisdiele – eigener Eis-Guide später'),  -- kem ice cream (Stadtmitte)
  ('534e4576-ebdc-40df-9fb9-b9dd742d42e0'::uuid, 'kein Café (Chocolaterie)'),  -- Chocolaterie bittersüß & edelweiß (Unterbilk)
  ('d1518843-148a-44a8-83a2-32667eb4f2e5'::uuid, 'kein Café (Torten/Catering)'),  -- Konditorei Sugarbar (Derendorf)
  ('477ff80a-3dc8-4251-ba8e-07bcee62393c'::uuid, 'kein Café (Torten/Kuchen)'),  -- SugArt Factory Konditorei (Pempelfort)
  ('e568ff9e-44e6-4013-bed7-d8c5c9ca48ff'::uuid, 'kein Café (Bubble-Tea-Laden)')   -- Moon Glow (Stadtmitte)
) as v(id, grund)
where o.id = v.id;

-- 2) Texte – Sicherung
create table if not exists public.orte_texte_sicherung_2026_11_27 as
select id, name, beschreibung, now() as gesichert_am from orte where false;
alter table public.orte_texte_sicherung_2026_11_27 enable row level security;
insert into public.orte_texte_sicherung_2026_11_27 (id, name, beschreibung, gesichert_am)
select id, name, beschreibung, now() from orte where id in (
  '7f72412f-56dc-4362-a953-ae94bf0c80a2',
  'fd7e705e-2b9e-407a-8d13-4f1841ccc66e',
  '888432d6-2129-455e-b1d4-219df31aae45',
  '8cd7d90c-158c-4afb-a4b3-e80a8cffadd4',
  '9725ab6e-2c0a-4c93-9f3b-7ab994a2a3d1',
  '9ebd2777-490b-4d2a-8072-8fc1c4720fcf',
  '62429aa4-2e18-4429-a405-11ca3971cf38',
  '9092b8ed-f2ca-44fc-b290-5e4409cbf749',
  '0556de22-e697-49ba-937f-163a96c83793',
  'c61bf387-caf5-4ccf-a183-2859fe627823',
  '07a4759f-6f10-4c45-92ab-e104fffbbe07',
  '0f560fde-c06e-4da5-94cc-33f9126fea63'
);

-- égoïste Matcha & Café (Altstadt)
update orte set beschreibung = replace($t$Das égoïste in der Altstadt ist ein kleiner, **liebevoll gestalteter Spot** für alle, die Matcha lieben. Die **Matcha-Getränke** sind hier richtig stark, ob klassisch oder in einer der fruchtigen Varianten, und auch der **Kaffee** überzeugt. Pflanzliche Milchalternativen gibt es ohne Aufpreis.

Speisen stehen nicht auf der Karte, und Sitzplätze gibt es nur wenige. Das égoïste ist eher ein Laden für **unterwegs**: kurz reinschauen, das Lieblingsgetränk mitnehmen und weiter durch die Altstadt bummeln. Wer einen besonders guten Matcha sucht, macht hier aber garantiert keinen Umweg umsonst.$t$, chr(13), '') where id = '7f72412f-56dc-4362-a953-ae94bf0c80a2';

-- Café Nikan (Düsseltal)
update orte set beschreibung = replace($t$Wer Kaffee liebt, sollte im Café Nikan in Düsseltal vorbeischauen. Die **private Kaffeerösterei** setzt auf Manufaktur-Röstung und Bohnen aus fairem Direkthandel, und man merkt schnell, dass hier mit Leidenschaft gearbeitet wird. Von Espresso über Filterkaffee bis Cappuccino ist alles dabei, und die **selbst gerösteten Bohnen** gibt es direkt im Laden zu kaufen.

Zum Kaffee stehen auch **Kuchen und Croissants** bereit, der Fokus liegt aber klar auf dem, was aus der Röstmaschine kommt. Wer einen richtig guten Flat White oder Filterkaffee sucht, ist hier bestens aufgehoben. Für ein ausgiebiges Frühstück geht man besser woanders hin.

Das Team nimmt sich Zeit für eine **persönliche Beratung** und hilft dabei, die passende Sorte für zu Hause zu finden. Vor dem Haus lädt eine **große Sitzterrasse** zum Verweilen ein, und der Weg von der Haltestelle Zoo ist kurz.$t$, chr(13), '') where id = 'fd7e705e-2b9e-407a-8d13-4f1841ccc66e';

-- Kaffee Privatrösterei Olga Sabristova (Pempelfort)
update orte set beschreibung = replace($t$Wer in Pempelfort einen ruhigen Ort für richtig guten Kaffee sucht, ist hier an der richtigen Adresse. Die Kaffee Privatrösterei Olga Sabristova ist ein gemütliches Café mit **eigener Rösterei**, und genau darum dreht sich hier alles: Die Bohnen werden im Haus geröstet und lassen sich gleich für zu Hause mitnehmen, im Laden oder über den **Onlineshop**.

Neben Espresso und Co. kommen auch der Iced Latte und die **hausgemachte Limonade** gut an. Dazu gibt es eine kleine, feine Kuchenauswahl, etwa Apfelkuchen mit Zimt und Mandeln oder einen **cremigen Käsekuchen**. Ein Frühstückscafé ist die Rösterei nicht, wer aber einfach einen hervorragenden Kaffee trinken möchte, wird hier glücklich.

Im Sommer lädt der **Außenbereich** zum Verweilen ein, und das Team um Olga Sabristova sorgt für eine herzliche Atmosphäre, in der man sich schnell zu Hause fühlt.$t$, chr(13), '') where id = '888432d6-2129-455e-b1d4-219df31aae45';

-- Kaffeerösterei Lamëng (Derendorf)
update orte set beschreibung = replace($t$Diese **kleine Rösterei in Derendorf** ist ein echter Treffpunkt für Kaffeeliebhaber. Die Inhaber sind herzlich und nehmen sich viel Zeit für ihre Gäste, und jede Sorte wird mit viel Leidenschaft und Fachwissen erklärt. Man lernt dabei eine Menge über die Bohnen und ihre Anbaugebiete.

Die Hauptrolle spielt ganz klar der **selbst geröstete Kaffee**, und wer Specialty Coffee probieren möchte, ist hier genau richtig. Zwar gibt es auch richtig leckeren **Kuchen**, zum ausgiebigen Frühstücken kommt man aber nicht hierher, sondern für eine wirklich gute Tasse.

Die Bohnen kann man natürlich auch **für zu Hause** mitnehmen. Und wer nett fragt, bekommt mit etwas Glück sogar ein **kleines Konzert** vom Besitzer.$t$, chr(13), '') where id = '8cd7d90c-158c-4afb-a4b3-e80a8cffadd4';

-- Kaffeeschmiede (Oberkassel)
update orte set beschreibung = replace($t$In der Kaffeeschmiede in Oberkassel dreht sich alles um guten Kaffee, und das merkt man schon beim Hereinkommen: Waagen und **Röstmaschinen** dienen als Dekor und machen den Raum gemütlich und handwerklich. Geröstet wird im eigenen Haus, die Sorten sind originell, und die Bohnen gibt es direkt **zum Mitnehmen**. Wer tiefer einsteigen möchte, besucht ein **Kaffeeseminar in der Rösthalle**.

Zum Kaffee gibt es Kuchen wie **frischen Apfelkuchen**, Waffeln und leckere Limonade. Ein Ort für ein großes Frühstück ist die Kaffeeschmiede allerdings nicht, hier steht die Tasse im Mittelpunkt, und die ist richtig gut.

Viele Plätze und eine große, **schattige Terrasse** machen das Café auch für einen entspannten Sonntagnachmittag angenehm. Der Inhaber ist mit Begeisterung bei der Sache, was man dem kleinen Kleinod in Oberkassel deutlich anmerkt.$t$, chr(13), '') where id = '9725ab6e-2c0a-4c93-9f3b-7ab994a2a3d1';

-- RVTC Rösterei VIER Wallstreet (Altstadt)
update orte set beschreibung = replace($t$Wer im Zentrum unterwegs ist und Lust auf wirklich guten **Specialty Coffee** hat, sollte bei der Rösterei VIER in der Wallstraße vorbeischauen. Die Bohnen werden selbst geröstet und sind wunderbar aromatisch, ob als Batch Brew, Espresso oder, wenn es mal süßer sein darf, als **Karamell Macchiato**.

Die Räume sind zweigeteilt: Im kleineren wird Kaffee getrunken, im größeren wird **geröstet**, probiert und eingekauft, denn alle Sorten gibt es auch zum Mitnehmen. Dazu gibt es **süßes Gebäck** von Bulle und Pure Pastry. Wer ein ausgiebiges Frühstück sucht, ist hier falsch, wer einen richtig guten Kaffee sucht, dagegen genau richtig.

Im Sommer sitzt man draußen in der engen Altstadtgasse, umgeben von italienischen Restaurants und schönen Boutiquen, mit einem jungen Publikum und etwas südländischem Charme. Kleine Gäste bekommen übrigens einen **Babyccino**.$t$, chr(13), '') where id = '9ebd2777-490b-4d2a-8072-8fc1c4720fcf';

-- No Worries (Flingern)
update orte set beschreibung = replace($t$Das No Worries in Flingern ist eines der beliebtesten Cafés im Viertel, und das liegt vor allem am Kaffee: Viele halten ihn für **einen der besten der Stadt**. Ob Espresso, Iced Latte oder ein Filter mit wechselnden **Gastbohnen**, hier stimmt jede Tasse. Dazu gibt es Matcha und Tee.

Zu essen gibt es kaum etwas, höchstens ein Croissant oder eine Zimtschnecke von der Theke. Auch drinnen ist der Platz knapp, Sitzplätze sind rar. Bei schönem Wetter spielt sich das Leben ohnehin **direkt vor der Tür** ab: Junge, hippe Leute treffen sich hier auf einen Kaffee oder einen Drink, und der Gehweg wird zum kleinen Treffpunkt des Viertels.

Die Besitzer und das Team sind **besonders herzlich**, man fühlt sich schon beim ersten Besuch willkommen. Wer mag, nimmt sich noch **Bohnen für zu Hause** mit.$t$, chr(13), '') where id = '62429aa4-2e18-4429-a405-11ca3971cf38';

-- Fjaka Café & Clubhouse (Flingern)
update orte set beschreibung = replace($t$Das Fjaka in Flingern ist ein Café, das schnell zum Stammlokal werden kann. Drinnen wirkt es freundlich und hell eingerichtet, und trotz gutem Besuch bleibt die Stimmung ruhig und angenehm.

Im Mittelpunkt steht der Kaffee aus der **eigenen Rösterei**, bei dem Espresso und Milch genau stimmen, dazu gibt es Matcha-Spezialitäten, einige alkoholische Getränke und Frühstückssnacks wie Bagels. Unbedingt probieren sollte man den **New York Cheesecake**: herrlich cremig und einer der besten der Stadt.

Im Sommer lockt der **Außenbereich** mit Sonnenplätzen und Sonnenschirmen. Das Team ist freundlich und aufmerksam, und für Hunde steht ein **Wassernapf** bereit. Wer einen entspannten Ort zum Verweilen sucht, ist hier richtig.$t$, chr(13), '') where id = '9092b8ed-f2ca-44fc-b290-5e4409cbf749';

-- Isabella Glutenfreie Pâtisserie (Oberkassel)
update orte set beschreibung = replace($t$Wer **glutenfrei genießen** möchte, ohne auf Geschmack zu verzichten, ist in dieser Pâtisserie in Oberkassel richtig. Die Theke lockt mit Rüblitorte, Noisette-Törtchen und **veganen Zimtschnecken**, die man gerne direkt probiert oder für unterwegs mitnimmt. Das Angebot reicht von Backwaren über **laktosefreie und vegane Produkte** bis zu kleinen Gerichten.

Das Frühstück ist abwechslungsreich, und Brot und Gebäck schmecken so natürlich, dass man kaum merkt, dass sie glutenfrei sind. Hier wird mit **sehr hoher Qualität** und viel Sorgfalt gearbeitet, und das hat seinen Preis: Günstig ist die Pâtisserie nicht, dafür bekommt man etwas wirklich Besonderes auf den Teller.

Der **Service ist freundlich** und aufmerksam. Ein schöner Ort für ein entspanntes Frühstück, für den Kaffee am Nachmittag oder für alle, die **Rücksicht auf Unverträglichkeiten** nehmen müssen und sich trotzdem etwas gönnen wollen.$t$, chr(13), '') where id = '0556de22-e697-49ba-937f-163a96c83793';

-- Hala Empanada Café (Pempelfort)
update orte set beschreibung = replace($t$Im Hala Empanada Café an der Münsterstraße dreht sich alles um **handgemachte Empanadas**, und die sind schlicht fantastisch: saftig, gut gewürzt und spürbar **mit viel Liebe gemacht**. Die Auswahl ist groß genug, um sich Stück für Stück durchzuprobieren, von der Variante mit Rindfleisch bis zu Mozzarella und Tomate. Dazu gibt es Süßes und einen **ausgezeichneten Kaffee**.

Einen Haken hat das Ganze: Sitzplätze gibt es nur sehr wenige, drinnen wie auf der kleinen Terrasse vor dem Laden. Wer sicher gehen will, plant die Empanadas am besten **to go** ein. Das freundliche Team und ein Hauch von Südamerika machen jeden Besuch trotzdem zu einem kleinen Highlight.$t$, chr(13), '') where id = 'c61bf387-caf5-4ccf-a183-2859fe627823';

-- KUMO (Oststraße, Stadtmitte)
update orte set beschreibung = replace($t$Das KUMO an der Oststraße ist kein klassisches Café, sondern ein **fancy Dessertcafé** für alle, die es richtig süß mögen. Auf der Karte stehen **asiatische Nachspeisen**, vor allem aus Japan, und im Mittelpunkt die **Dorayaki**: kleine, fluffige Pfannkuchen mit üppiger, luftig-sahniger Füllung, etwa mit Roten Bohnen, Matcha oder Ube.

Dazu gibt es japanisches **Softeis**, und wer es ausgefallener mag, probiert das Mont-Blanc-Eis mit feinen Eisfäden obendrauf. Die Zubereitung braucht etwas Zeit, was für Frische und Sorgfalt spricht, und alles ist hübsch angerichtet.

Der Laden ist sauber und gepflegt, das Team freundlich. Ein schöner Ort für eine **süße Pause** zwischendurch, für Kinder genauso wie für Erwachsene.$t$, chr(13), '') where id = '07a4759f-6f10-4c45-92ab-e104fffbbe07';

-- Soul's (Rath)
update orte set beschreibung = replace($t$Das Soul's in Rath ist ein **rein veganes Café** mit viel Herz und **rustikalem Charme**. Viel natürliches Licht fällt durch die Fenster, die Einrichtung ist liebevoll, und die Inhaberin ist sehr darum bemüht, dass alles perfekt ist. Freundlicher kann man kaum empfangen werden.

Auf der Karte stehen guter Kaffee, Matcha und hausgemachte Getränke, dazu **vegane und glutenfreie Kuchen** ohne Industriezucker. Wer herzhaft mag, findet täglich wechselnde Suppen, französische Quiche und Frühstücksschnitten.

Familien kommen hier ebenfalls auf ihre Kosten: Für die Kleinen gibt es eine **zuckersüße Spielecke mit Kaufladen**. Außerdem finden regelmäßig **Events** statt, vor allem für Frauen. Und wer danach noch Bewegung möchte, startet direkt gegenüber zu einem Spaziergang im Aaper Wald.$t$, chr(13), '') where id = '0f560fde-c06e-4da5-94cc-33f9126fea63';

commit;

-- Prüfung: 12 ausgeblendet, 12 Texte gesetzt
select count(*) as ausgeblendet from orte where extras->'ausgeblendet'->>'datum' = '2026-11-27' and aktiv = false;
select count(*) as neue_texte from orte o join public.orte_texte_sicherung_2026_11_27 s using (id)
where o.beschreibung is distinct from s.beschreibung;
