-- Restaurant-Guide: Texte mit Absätzen und Fett (Wortlaut unverändert), erzeugt 2026-11-27
-- Erst NACH dem Deploy der Detailseite ausführen (sonst stehen live Sternchen im Text).
-- Aktualisiert nur Zeilen, deren Text noch genau dem alten entspricht. Zurück: siehe Ende der Datei.
begin;
create table if not exists orte_texte_format_sicherung_2026_11_27 as
  select id, beschreibung, now() as gesichert_am from orte where id in (
    '2852623a-d03d-459d-9aed-eafd3cb24f33',
    '09fb2bc8-9610-44ec-8a94-14ff65250369',
    '078672bf-8a3b-4067-9217-c2c5a403ed2b',
    '25ed690b-0353-4f2b-8040-5f55e136929f',
    '56cc48b7-db23-49d0-b602-9915ad350d88');
alter table orte_texte_format_sicherung_2026_11_27 enable row level security;
update orte set beschreibung = replace('Das Kindercafé Wunderhaus in Wersten ist ein **Ort für Familien**, an dem es leichte Gerichte, Kaffee und Süßwaren gibt. Die Desserts sind frisch und lecker, und während die Kleinen in den **Spielbereichen** toben, können die Eltern in Ruhe ihren Kaffee genießen.

Das Personal ist freundlich, aufmerksam und geht **liebevoll auf die Kinder** ein, sodass man schnell merkt, dass Familien hier willkommen sind. Das Café wirkt sauber und gemütlich, und auf der **Straßenterrasse** lässt sich der Nachmittag bei gutem Wetter besonders entspannt verbringen. Wer einen schönen Nachmittag mit der Familie plant, ist hier gut aufgehoben.', chr(13), '') where id = '2852623a-d03d-459d-9aed-eafd3cb24f33' and md5(beschreibung) = 'c63d912e285846b6b85d078c9a7b7b28';
update orte set beschreibung = replace('Das Kindercafé Zauberwald in Ratingen ist ein schöner Ort für einen entspannten **Familienvormittag**. Die **Spielbereiche** sind liebevoll gestaltet, sauber gepflegt und bieten viel Abwechslung, sodass die Kleinen gut beschäftigt sind. Der Essensbereich ist vom Spielbereich getrennt, was gerade mit Kindern sehr angenehm ist.

Auf der Karte stehen **Waffeln, Pancakes und Milchreis**, die bei großen Gruppen gut ankommen. Die Betreiber sind **herzlich und freundlich**, und man fühlt sich sofort willkommen.

Eltern können bei einem Kaffee entspannt sitzen und ihre Kleinen dabei gut im Blick behalten. Für die **ganz Kleinen** ist das Angebot besonders passend.', chr(13), '') where id = '09fb2bc8-9610-44ec-8a94-14ff65250369' and md5(beschreibung) = '91ab324bc4a7bd8afd6a371a59008b2a';
update orte set beschreibung = replace('Wer mit **Kleinkindern** unterwegs ist, findet im Little Bunny in Derendorf eine echte Oase. Der große, schön gestaltete **Indoor-Spielplatz** ist ein Traum für die Kleinen, und weil es meist ruhig und überschaubar bleibt, können die Jüngsten entspannt spielen, ohne von größeren Kindern überrannt zu werden. Eltern behalten dabei alles im Blick, auch wenn es ums Essen und Trinken geht.

Der **Kaffee** kommt gut an, dazu gibt es leckere Snacks, die man gerne mit am Tisch genießt. Das Team begegnet Familien ausgesprochen freundlich und entgegenkommend.

Besonders schön ist der **Geburtstag**: Vom unkomplizierten Buchen über die liebevoll dekorierten Tische und Cupcakes bis zum Singen mit dem Kuchen wird an alles gedacht, sodass Gastgeber entspannt feiern können. Gemütliche Atmosphäre und **Sauberkeit** runden den Besuch ab.', chr(13), '') where id = '078672bf-8a3b-4067-9217-c2c5a403ed2b' and md5(beschreibung) = '485e3d688d9a14ca63064279010b3761';
update orte set beschreibung = replace('Wer mit Kindern eine entspannte Pause im Rheinpark Center in Neuss sucht, ist hier richtig. Der **Babybereich** mit weicher Polsterung und Spiegel ist liebevoll gestaltet, und der Spielbereich bietet altersgerechte Herausforderungen, die die Kleinen lange beschäftigen. Die **Waffeln** kommen frisch auf den Tisch und gelten als wirklich lecker, dazu gibt es Kaffee, und auch der Matcha Latte kommt gut an.

Alles ist sauber und freundlich gestaltet, sodass Erwachsene entspannt sitzen können, während die Kinder spielen. Das **Personal empfängt Familien herzlich** und zuvorkommend, man fühlt sich schnell willkommen. Auch die Spielzeuge sind mit Bedacht ausgewählt, sodass nicht zu viel auf einmal da ist. Ein schöner Abschluss für einen Einkaufsbummel oder ein eigenes Ausflugsziel für die **ganze Familie**.', chr(13), '') where id = '25ed690b-0353-4f2b-8040-5f55e136929f' and md5(beschreibung) = '2d06e3e6e339646dee8ae43b62595228';
update orte set beschreibung = replace('Wer **mit Kindern** einen gemütlichen Ort sucht, an dem man auch mal die Füße hochlegen kann, ist im Les Petits in Friedrichstadt richtig. Der Laden ist liebevoll eingerichtet, sehr sauber und an vielen Details merkt man, dass hier mitgedacht wurde. Im Spielbereich gibt es viele **Montessori-Spielzeuge**, größtenteils aus hochwertigem Holz, und die Kleinen können sich dort gut selbst beschäftigen. Die Spielfläche ist übersichtlich, sodass man die Kinder immer im Blick hat und selbst ein bisschen entspannen kann. Das **Schuhe-aus-Konzept** sorgt dafür, dass alles in Augenhöhe der Kinder steht.

Auf dem Teller landen Flammkuchen, Frühstück und **hausgemachter Kuchen**, dazu gibt es Kaffee, der die Runde gut abrundet. Das Team ist aufmerksam und herzlich, und die Gastgeberin sorgt dafür, dass man sich direkt willkommen fühlt. Auch größere Gruppen werden gut umsorgt. Für **Babys und Kleinkinder** ist der Ort besonders passend.', chr(13), '') where id = '56cc48b7-db23-49d0-b602-9915ad350d88' and md5(beschreibung) = '355fc38cf01c40177d59944f2e2587dd';

-- Windows-Zeilenumbrüche (\r) aus früheren Text-SQLs entfernen – Absätze bleiben, nur das unsichtbare \r fällt weg
update orte set beschreibung = replace(beschreibung, chr(13), '')
where typ in ('restaurant', 'cafe', 'imbiss') and position(chr(13) in beschreibung) > 0;
commit;

-- Prüfung: so viele Texte haben jetzt Fett
select count(*) as mit_fett from orte where id in (select id from orte_texte_format_sicherung_2026_11_27) and beschreibung like '%**%';

-- Zurück (nur bei Bedarf):
-- update orte o set beschreibung = s.beschreibung from orte_texte_format_sicherung_2026_11_27 s where o.id = s.id;
