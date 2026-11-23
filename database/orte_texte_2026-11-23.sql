-- Texte der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.14, Schritt 4) – die 26 Orte ohne Text,
-- nach Vorschlägen des Auftraggebers (Excel 23.11.2026) überarbeitet und von ihm freigegeben
-- Erzeugt am 2026-11-23 von `python -m scraper.orte.spielstaetten_texte --sql` aus data/spielstaetten/texte.csv
-- (nur Zeilen mit freigabe = ja und ohne Prüffehler). Jeder Satz hat eine Quelle (extras.spielstaette.
-- text_freigegeben.quellen). Absätze per Leerzeile, **fett** zeigt die Ortsseite. Wiederholbar.

BEGIN;

UPDATE public.orte SET beschreibung = $txt$Das **Atelier Modeerscheinung** ist ein Ort für alle, die gern mit Stoff und Garn arbeiten. Hier finden unter anderem **Nähworkshops für Einsteiger** statt, bei denen kleine Projekte wie Geschenkbeutel entstehen.

Auch Strickfans kommen auf ihre Kosten: Beim **„Knit & Sip“** wird in geselliger Runde gestrickt.$txt$,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://diesdas.events/event/cda61cb4-e5e3-4ea5-8ce6-460fb71a778f", "https://diesdas.events/event/cda61cb4-e5e3-4ea5-8ce6-460fb71a778f", "https://diesdas.events/event/community/knit-sip-stricktreff-duesseldorf-atelier-modeerscheinung-2026-11-18"]}}'::jsonb)
WHERE slug = 'atelier-modeerscheinung' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$**BREW** steht in Düsseldorf für **Spezialitätenkaffee** aus eigener Röstung. Gäste trinken hier Kaffee und nehmen Bohnen für zu Hause mit.

Regelmäßig finden **Barista-Workshops** und **Cuppings** statt – angeleitete Verkostungen, bei denen verschiedene Kaffees verglichen werden. Wer mag, füllt seinen Kaffee über ein **Zero-Waste-Nachfüllsystem** ab.$txt$, webseite = COALESCE(webseite, 'https://brewroast.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://brewroast.de/", "https://brewroast.de/pages/cafe-store", "https://rausgegangen.de/events/barista-basic-workshop-13/", "https://brewroast.de/pages/cafe-store"]}}'::jsonb)
WHERE slug = 'brew-speciality-coffee-roastery' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Der **Carlstadt – Mat Room** ist ein kleiner Raum für **Yoga** und Entspannung in der **Carlstadt**. Hier finden unter anderem Abende wie **„Red Light Yin & Sound“** statt, die **Yin-Yoga** mit einem Klangerlebnis unter rotem Licht verbinden.$txt$,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://diesdas.events/event/community/red-light-yin-sound-carlstadt-mat-room-2026-11-20", "https://diesdas.events/event/community/red-light-yin-sound-carlstadt-mat-room-2026-11-20"]}}'::jsonb)
WHERE slug = 'carlstadt-mat-room' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$**Das Dazwischen** ist ein Seminar- und Workshopraum in **Unterbilk**, den man für eigene Veranstaltungen mieten kann. Genutzt wird er für **Yoga**, **Meditation**, Workshops, Vorträge, Lesungen und kleine Tagungen.

Für Bewegung und Achtsamkeit liegen Matten, Kissen und Decken bereit, für Seminare lassen sich Tische und Stühle flexibel stellen. Dazu kommen eine **Teeküche** mit Pausenbereich und eine Sitzecke für Gespräche im kleinen Kreis. Je nach Aufbau finden bis zu **50 Personen** Platz.$txt$, webseite = COALESCE(webseite, 'https://www.dasdazwischen.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://www.dasdazwischen.de/", "https://www.dasdazwischen.de/", "https://www.dasdazwischen.de/", "https://www.dasdazwischen.de/", "https://www.dasdazwischen.de/"]}}'::jsonb)
WHERE slug = 'das-dazwischen' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Das **ES365 Art Center** ist ein Kunst- und Atelierort in **Lierenfeld**. Entstanden ist er 2021 als Zwischennutzung in den Gebäuden des ehemaligen **Fiat-Motorvillage**.

Auf dem weitläufigen Gelände gibt es rund **50 Ateliers** und drei große Ausstellungsräume. Die früheren Gewerberäume bieten heute viel Platz für **freie Kunst**. Neben Ausstellungen finden hier auch kreative Formate wie **Aktzeichenkurse** statt.$txt$, webseite = COALESCE(webseite, 'https://es365.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://es365.de/kontakt/", "https://www.viernull.de/stadt-mit-ue/der-sommer-ihres-lebens/", "https://es365.de/about/", "https://www.kulturgehtweiter.de/venues/es365", "https://rausgegangen.de/events/gemutlicher-aktzeichenkurs-in-dusseldorf-41/"]}}'::jsonb)
WHERE slug = 'es365-art-center' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Das **Flow** ist ein Club an der **Mertensgasse** mitten in der Düsseldorfer **Altstadt**. Er trat die Nachfolge des Szeneclubs **Silq** an.

Heute steht der Name vor allem für **Afterhour-Partys**, die bis in den Morgen gehen.$txt$,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://www.fazemag.de/silq-duesseldorf-nachfolger-fuer-szeneclub-gefunden/", "https://www.fazemag.de/silq-duesseldorf-nachfolger-fuer-szeneclub-gefunden/", "https://rausgegangen.de/events/afterhour-nr4-47/"]}}'::jsonb)
WHERE slug = 'flow' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$**FLURSTÜCK** ist ein **Secondhandladen** an der Flurstraße in **Flingern**. Der Laden gehört zum **SKFM Düsseldorf** und läuft auch unter dem Namen „Flurstück by Wertschöpfung“.

Im Sortiment ist gebrauchte **Kleidung für Frauen, Männer und Kinder**. Die Stadt Düsseldorf zählt das Geschäft zu den Adressen für **nachhaltiges und günstiges Einkaufen**.$txt$, webseite = COALESCE(webseite, 'https://www.skfm-duesseldorf.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://www.duesseldorf.de/familie/elternbesuchsdienst/nachhaltig-einkaufen", "https://www.skfm-duesseldorf.de/de/aktuelles/1/2024/154/", "https://www.duesseldorf.de/familie/elternbesuchsdienst/nachhaltig-einkaufen", "https://www.duesseldorf.de/familie/elternbesuchsdienst/nachhaltig-einkaufen"]}}'::jsonb)
WHERE slug = 'flurstueck' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Die **Geissel** ist ein Café und Restaurant in **Bilk**. Auf der Karte stehen deutsche und internationale Gerichte, je nach Saison etwa **Grünkohl**, Sauerbraten oder Kürbisgerichte, dazu vegetarische Burger.

Getrunken wird **Bier vom Fass** und Wein von der eigenen Karte. Eine Besonderheit ist die hauseigene **Kegelbahn**. Im Herbst gibt es außerdem eine eigene **Gänsekarte**.$txt$, webseite = COALESCE(webseite, 'https://geissel-in-bilk.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://geissel-in-bilk.de/", "https://geissel-in-bilk.de/", "https://geissel-in-bilk.de/", "https://geissel-in-bilk.de/", "https://geissel-in-bilk.de/"]}}'::jsonb)
WHERE slug = 'geissel-cafe-restaurant' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$**glazed.** ist ein **Keramik-Malstudio**, in dem man vorgefertigte Stücke selbst gestaltet. Das Studio gibt es seit 2024. Zur Auswahl stehen etwa **Tassen**, Teller und Schalen, die mit Farben und verschiedenen Techniken bemalt werden.

Eine **Malsession** dauert rund zweieinhalb Stunden, Pinsel, Farben und Betreuung sind dabei. Danach wird das Stück **glasiert und gebrannt** und kann nach etwa drei Wochen abgeholt werden. Neben den offenen Sessions gibt es Angebote für **Geburtstage**, private Feiern und andere Gruppen.$txt$, webseite = COALESCE(webseite, 'https://www.glazeddus.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://www.glazeddus.de/", "https://www.potteryhontas.com/toepferkurse/keramik-bemalen/", "https://www.glazeddus.de/", "https://www.glazeddus.de/", "https://www.glazeddus.de/", "https://www.glazeddus.de/"]}}'::jsonb)
WHERE slug = 'glazed-dein-keramik-mal-studio' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Die **Hockerstube** verbindet ein **Brettspielgeschäft** mit einem **Spielecafé**. Im Laden gibt es Brett- und Kartenspiele, Sammelkarten und Zubehör – vom Familienspiel bis zum Expertenspiel.

Im Café wählt man aus einer **Bibliothek mit über 800 Spielen**, lässt sich beraten und spielt gemeinsam am Tisch. Auf rund 240 Quadratmetern ist Platz für mehr als 70 Gäste, dazu gibt es Getränke und kleine Snacks. Regelmäßig stehen auch **Spieleturniere** und Workshops auf dem Programm.$txt$, webseite = COALESCE(webseite, 'https://hockerstube.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://hockerstube.de/", "https://hockerstube.de/", "https://hockerstube.de/", "https://www.kreativquartier-wp.de/de/community/hockerstube", "https://hockerstube.de/"]}}'::jsonb)
WHERE slug = 'hockerstube' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Das **HofArt Studio** ist ein kleines Kreativstudio in einem **Innenhof** in **Unterbilk**. Die Kurse leitet die Künstlerin **Franziska Müller**.

Auf dem Programm stehen **Malkurse** und verschiedene Kreativworkshops, etwa mit **Jesmonite**. Dazu kommen Angebote für Kinder sowie buchbare Formate wie **Kindergeburtstage** und Junggesellenabschiede. Im Mittelpunkt steht das gemeinsame Gestalten ohne Leistungsdruck.$txt$, webseite = COALESCE(webseite, 'https://hofartkurse.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://hofartkurse.wordpress.com/", "https://hofartkurse.wordpress.com/", "https://t.rausgegangen.de/tickets/jesmonite-deine-kreative-dekoration-1", "https://hofartkurse.wordpress.com/", "https://hofartkurse.wordpress.com/"]}}'::jsonb)
WHERE slug = 'hofart-studio' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Das **Interim Museum of Contemporary Art** an der Hansaallee ist ein Ausstellungsort in ehemaligen **Industrie- und Gewerbehallen**. Seit 2023 wird das Areal für **Kunst- und Kulturprojekte** zwischengenutzt.

Gezeigt werden wechselnde **Ausstellungen** mit Malerei, Mixed Media, Skulptur und Fotografie, oft als Gruppenschau vieler Kunstschaffender.$txt$,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://artartist.co/ort/", "https://artartist.co/ort/", "https://www.kulturportal-duesseldorf.de/veranstaltungskalender/unlimited-fantasie-ohne-grenzen-1919760444"]}}'::jsonb)
WHERE slug = 'interimmuseum-hansaallee-190' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Die **Kugel Eismanufaktur** ist ein Eiscafé an der **Nordstraße** in **Pempelfort**. Das Eis entsteht direkt vor Ort – **hausgemacht**, aus natürlichen Zutaten und in wechselnden Sorten.

Neben Eis gibt es Getränke, und ab und zu wird der Laden zur Bühne für kleine Veranstaltungen und **Live-Musik**.$txt$,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://nordstrasse-duesseldorf.org/geschaefte/kugel-eismanufaktur/", "https://nordstrasse-duesseldorf.org/geschaefte/kugel-eismanufaktur/", "https://nordstrasse-duesseldorf.org/geschaefte/kugel-eismanufaktur/"]}}'::jsonb)
WHERE slug = 'kugel-eismanufaktur' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$**La bottega del gusto** ist ein **italienisches Feinkostgeschäft** in **Flingern**. Im Regal stehen Pasta, **Olivenöle** und ausgewählte italienische Weine. Drei Frauen führen den Laden weiter, nachdem sich der frühere Inhaber zurückgezogen hat.

Dazu gehören Veranstaltungen rund um die italienische Küche: **Weinverkostungen**, **Aperitivo-Abende** mit kleinen Speisen und **Pastakurse**, nach denen gemeinsam gegessen wird.$txt$, webseite = COALESCE(webseite, 'https://labottegadelgusto.shop/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://labottegadelgusto.shop/pages/uber-uns", "https://labottegadelgusto.shop/pages/uber-uns", "https://labottegadelgusto.shop/pages/uber-uns", "https://labottegadelgusto.shop/pages/events"]}}'::jsonb)
WHERE slug = 'la-bottega-del-gusto' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$**La Paillette** ist eine **Café-Bar** in **Pempelfort**. Neben Getränken und kleinen Speisen gibt es eine **beheizte Terrasse**. Regelmäßig spielt hier **Live-Musik**.

Auch **Comedy** hat ihren Platz: Bei der Reihe **„Zeitgeist & Wunderlich“** stehen wechselnde Comedians beim Open Mic auf der Bühne. Für private Feiern lassen sich die Räume außerdem mieten.$txt$, webseite = COALESCE(webseite, 'https://lapaillette.metro.bar/?lang=de'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://lapaillette.metro.bar/?lang=de", "https://lapaillette.metro.bar/?lang=de", "https://lapaillette.metro.bar/?lang=de", "https://www.openmics.de/duesseldorf/open-mics/zeitgeist-wunderlich-comedy-open-mic/", "https://lapaillette.metro.bar/?lang=de"]}}'::jsonb)
WHERE slug = 'la-paillette' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Die **Lakritz-Boutique** ist ein Fachgeschäft in **Flingern**. Hier dreht sich alles um **Lakritz** – in vielen Geschmacksrichtungen, Konsistenzen und Stärken. Im Sortiment sind mehrere Hundert Sorten, von klassisch über **salzig** bis mit Schokolade.

Neben dem Laden gibt es einen Onlineshop. Regelmäßig finden außerdem **Lakritz-Tastings** statt, bei denen ausgewählte Sorten probiert werden und es Wissenswertes rund um Lakritz gibt.$txt$, webseite = COALESCE(webseite, 'https://lakritz-boutique.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://lakritz-boutique.de/pages/kontakt-service", "https://lakritz-boutique.de/", "https://lakritz-boutique.de/", "https://lakritz-boutique.de/", "https://rausgegangen.de/events/lakritz-tasting-86/"]}}'::jsonb)
WHERE slug = 'lakritz-boutique' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Das **Lot jonn** ist eine **Kneipe** in **Bilk**, die auch bei Studierenden bekannt ist. Neben dem Kneipenbetrieb gibt es Speisen zum Mitnehmen und sonntags **Frühstück**.

Die Räume lassen sich für **private Feiern** mieten, bis hin zu Hochzeiten. Auch Vereine und Initiativen nutzen das Lokal für eigene Veranstaltungen.$txt$, webseite = COALESCE(webseite, 'https://lot-jonn.eatbu.com/?lang=de'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://rausgegangen.de/blog/studibars-dus/", "https://lot-jonn.eatbu.com/?lang=de", "https://lot-jonn.eatbu.com/?lang=de", "https://jugendring-duesseldorf.de/termin/danke-party/"]}}'::jsonb)
WHERE slug = 'lot-jonn' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$**LULLABY** ist ein Raum für **achtsame, körperorientierte Angebote** in der **Friedrichstadt**. Im Mittelpunkt stehen Körperwahrnehmung, Entspannung und ein bewusster Umgang mit Stress.

Angeboten werden **Massagen**, **Meditationen** und Körperreisen, dazu traumasensible Konzepte und sanfte Bewegung. Leistungsdruck und Vergleiche haben hier keinen Platz.$txt$,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://www.eversports.de/s/lullaby", "https://www.eversports.de/s/lullaby", "https://www.eversports.de/s/lullaby", "https://www.eversports.de/s/lullaby"]}}'::jsonb)
WHERE slug = 'lullaby-praxisorientiere-kurse-und-achtsame-beruehrung' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Das **Mangold** in **Derendorf** ist Restaurant, Bar und Lounge in einem. Gäste sitzen an der Bar, am Restauranttisch oder in der **Lounge-Ecke**.

Die Küche reicht vom **Frühstück** über Mittagessen bis zum Abendessen, etwa mit hausgemachter **Pasta**, Steaks oder Pinsa. Dazu gibt es Weine, Longdrinks und **Cocktails**. Am Wochenende lohnt sich eine Reservierung.$txt$, webseite = COALESCE(webseite, 'https://mangold.tv/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://mangold.tv/", "https://mangold.tv/", "https://mangold.tv/", "https://mangold.tv/", "https://mangold.tv/"]}}'::jsonb)
WHERE slug = 'mangold-restaurant' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Die **MindBar** in **Unterbilk** ist keine klassische Bar, sondern ein Ort für **Achtsamkeit und Coaching**. Es geht um persönliche und berufliche Entwicklung, Selbstreflexion und den Umgang mit Stress.

In **Coachings** werden Ziele, Gewohnheiten und innere Hürden in den Blick genommen. Gespräche finden vor Ort, am Telefon oder digital statt, dazu kommen **Kurse und Workshops**.$txt$, webseite = COALESCE(webseite, 'https://mind-bar.de/de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://mind-bar.de/de/", "https://mind-bar.de/de/", "https://mind-bar.de/de/", "https://bettina-deuster.de/"]}}'::jsonb)
WHERE slug = 'mindbar' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Das **MuSaMe** am **Fürstenplatz** ist **Bar und Café** in einem. Es ist ein Anlaufpunkt für den Abend in der **Friedrichstadt**.

Unter dem Titel **„MuSaMe on Stage“** wird das Lokal regelmäßig zur kleinen Bühne für **Konzerte** verschiedener Stilrichtungen. Auch **Lyrikabende** stehen auf dem Programm.$txt$,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://rausgegangen.de/locations/musame-1/", "https://www.visitduesseldorf.de/storys/2023/01/16/wo-ein-rekord-den-naechsten-jagt-ein-nachmittag-in-der-friedrichstadt/", "https://www.eventbrite.com/e/musame-on-stage-frau-bolke-und-das-groe-ganze-tickets-1999292227873", "https://rausgegangen.de/locations/musame-1/"]}}'::jsonb)
WHERE slug = 'musame' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Das **Nilsson** ist ein ehrenamtlich getragener **Kultur- und Begegnungsraum** im Initiativenhaus an der Martinstraße. Es versteht sich als **offene Bühne** und öffentliches Wohnzimmer für Menschen jeden Alters.

Auf dem Programm stehen **Lesungen**, Vorträge, Ausstellungen, Musik, Comedy und Workshops, dazu regelmäßige **Jazz-Sessions**. Viele Veranstaltungen bringen Initiativen von außen mit, etwa **Tanzabende** wie die „Hustle“-Sessions.$txt$, webseite = COALESCE(webseite, 'https://www.martinstrasse58.de/nilsson/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://www.martinstrasse58.de/nilsson/", "https://www.martinstrasse58.de/nilsson/", "https://www.martinstrasse58.de/nilsson/", "https://rausgegangen.de/events/the-hustle-tanz-session-27/"]}}'::jsonb)
WHERE slug = 'nilsson-initiativen-haus' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Das **Pfarrzentrum Heerdt** ist ein Treffpunkt der katholischen Gemeinde im Stadtteil **Heerdt**. Fester Bestandteil des Programms sind die Aufführungen der **KAB-Bühnen Heerdt**, deren Theatergeschichte bis 1980 zurückreicht.

Neben der **Komödienbühne** gibt es auch eine **Jugendbühne**. Außerdem finden hier Gemeindefeste und Treffen wie das **„CafeBene“** für Seniorinnen und Senioren statt.$txt$, webseite = COALESCE(webseite, 'https://www.santobene.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://www.santobene.de/Veranstaltungen/Pfarrfest-2026.06.21/", "https://www.buehneheerdt.de/", "https://www.buehneheerdt.de/", "https://www.santobene.de/Veranstaltungen/CafeBene-Anmeldung-bis-28.11.-2026.12.02/?instancedate=1796220000000"]}}'::jsonb)
WHERE slug = 'pfarrzentrum-heerdt' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$**QuARTier 8** ist ein **Atelier- und Kreativhof** in **Flingern**. Seit 2017 kommen hier Kunst, Kultur und Nachbarschaft zusammen.

Auf dem Programm stehen **Ausstellungen**, kreative Workshops, Theater, Musik und ein **Literaturclub**. Dazu kommen Spiele- und Nachbarschaftsabende. Außerdem treffen sich hier Gruppen für englischsprachiges **Improtheater**. Getragen wird das Ganze von einem gemeinnützigen Verein.$txt$, webseite = COALESCE(webseite, 'https://www.quartier8flingern.de/'),
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://www.duesseldorfer-anzeiger.de/duesseldorf/der-atelier-und-kreativhof-quartier-8-laedt-zu-ausstellungen-und-anderen-veranstaltungen_aid-44666939", "https://www.duesseldorfer-anzeiger.de/duesseldorf/der-atelier-und-kreativhof-quartier-8-laedt-zu-ausstellungen-und-anderen-veranstaltungen_aid-44666939", "https://www.quartier8flingern.de/", "https://www.quartier8flingern.de/", "https://www.meetup.com/de-de/staged/events/317048536/", "https://www.quartier8flingern.de/"]}}'::jsonb)
WHERE slug = 'quartier-8' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Der **Rote Teppich** in **Oberbilk** ist ein Lokal, das vor allem als **Veranstaltungsort** genutzt wird. Hier treffen sich Vereine und Parteien zu Versammlungen und Sitzungen.

Außerdem ist der Rote Teppich Spielort eines **Nachbarschaftskinos** mit Dokumentarfilmen.$txt$,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://die-partei-duesseldorf.de/kreisparteitag-2025/", "https://www.spd-duesseldorf.de/wp-content/uploads/sites/198/2024/05/2024-04-25_Protokoll_OV_SPD_Oberbilk.pdf", "https://diesdas.events/event/kultur/nachbarschaftskino-auf-panzern-in-die-klimakrise-roter-teppich-2026-11-26"]}}'::jsonb)
WHERE slug = 'roter-teppich' AND typ = 'spielstaette';
UPDATE public.orte SET beschreibung = $txt$Das **Sol y Luna** ist ein **Tanz- und Nachtclub** an der Mertensgasse in der **Altstadt**. Der Club erstreckt sich über **zwei Etagen**.

Musikalisch dreht sich vieles um **Latino**, House und RnB. Unter der Woche gibt es außerdem Tanzabende für Paartänzer, etwa ein **Urban Kiz Social**.$txt$,
  extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || '{"text_freigegeben": {"datum": "2026-11-23", "quellen": ["https://www.mrduesseldorf.de/die-besten-clubs-in-duesseldorf/", "https://www.mrduesseldorf.de/die-besten-clubs-in-duesseldorf/", "https://kizombaduesseldorf.de/orte/sol-y-luna/", "https://kizombaduesseldorf.de/orte/sol-y-luna/"]}}'::jsonb)
WHERE slug = 'sol-y-luna' AND typ = 'spielstaette';

-- Art passend zur Recherche (Secondhand- bzw. Feinkostladen, Coaching-Raum, Spielecafé, Veranstaltungslokal)
UPDATE public.orte SET extras = jsonb_set(extras, '{spielstaette,art}', to_jsonb('Laden'::text)) WHERE slug = 'flurstueck' AND typ = 'spielstaette';
UPDATE public.orte SET extras = jsonb_set(extras, '{spielstaette,art}', to_jsonb('Laden'::text)) WHERE slug = 'la-bottega-del-gusto' AND typ = 'spielstaette';
UPDATE public.orte SET extras = jsonb_set(extras, '{spielstaette,art}', to_jsonb('Kurs/Studio/Sport'::text)) WHERE slug = 'mindbar' AND typ = 'spielstaette';
UPDATE public.orte SET extras = jsonb_set(extras, '{spielstaette,art}', to_jsonb('Café/Restaurant'::text)) WHERE slug = 'hockerstube' AND typ = 'spielstaette';
UPDATE public.orte SET extras = jsonb_set(extras, '{spielstaette,art}', to_jsonb('Gastronomie/Eventlocation'::text)) WHERE slug = 'roter-teppich' AND typ = 'spielstaette';

COMMIT;

-- Kontrolle: Ortsseiten mit freigegebenem Text
SELECT count(*) FILTER (WHERE extras->'spielstaette' ? 'text_freigegeben') AS mit_text,
       count(*) AS spielstaetten FROM public.orte WHERE typ = 'spielstaette';
