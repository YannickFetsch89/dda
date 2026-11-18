-- Längere Beschreibungen Weihnachtsmarkt-Guide (Auftraggeber 18.11.2026) – nach dem Deploy im Supabase SQL-Editor ausführen.
-- Nur belegte Angaben (Visit Düsseldorf/Toubiz, Veranstalterseiten); Absätze per Leerzeile, **fett** zeigt nur der Weihnachtsmarkt-Guide.
-- Stammdaten: data/weihnachtsmaerkte/maerkte.csv (dort schon geändert).

BEGIN;

UPDATE public.orte SET beschreibung = $txt$Der **Düsseldorfer Weihnachtsmarkt** ist kein einzelner Platz, sondern eine Reihe von **Themenmärkten**, die nah beieinanderliegen: der Altstadt-Markt zwischen Flinger Straße und Marktstraße, der Märchen-Markt am Schadowplatz, The Winter Village auf der Königsallee und die Weihnachtspromenade am Rhein. Dazu kommen die Eisbahn Kö on Ice und das Riesenrad auf dem Burgplatz, die eigene Öffnungszeiten haben und länger laufen. Alles ist zu Fuß erreichbar – zwischen Shoppingmeilen, Altstadt und Museen.

2026 sind die Märkte vom **19. November bis 30. Dezember** geöffnet, der **Eintritt ist frei**. Am Totensonntag und am 1. Weihnachtstag bleiben sie geschlossen, an Heiligabend und am 2. Weihnachtstag gelten kürzere Zeiten; einzelne Händler dürfen täglich bis 22 Uhr verlängern. Zum Programm gehören eine festliche Eröffnung, das traditionelle Adventssingen zum Mitsingen und Kasperletheater. Am besten kommt man mit Bus und Bahn – die zentrale Haltestelle ist **Heinrich-Heine-Allee**. Zusätzliche Geldautomaten werden auf den Märkten nicht aufgestellt.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'innenstadt'
RETURNING slug, length(beschreibung) AS zeichen;

UPDATE public.orte SET beschreibung = $txt$Der **Altstadt-Markt** verbindet die Marktstraße mit der **Flinger Straße** und ist damit eine weihnachtliche Flaniermeile mitten in der Altstadt. Die Hütten sind **alten Düsseldorfer Bürgerhäusern** nachempfunden und passen sich so in die Häuserzeilen ringsum ein. Über der Straße hängt die Weihnachtsdekoration, unten duftet es nach gebrannten Mandeln und Glühwein.

Angeboten werden **Kunsthandwerk**, Geschenkideen und weihnachtliche Spezialitäten – das klassische Weihnachtsmarkt-Erlebnis. Der Markt gehört zum Düsseldorfer Weihnachtsmarkt in der Innenstadt und hat dieselben Öffnungszeiten, der Eintritt ist frei. Vom Marktplatz aus sind es nur wenige Schritte zum Riesenrad auf dem Burgplatz und zur Weihnachtspromenade am Rhein.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'altstadt-markt'
RETURNING slug, length(beschreibung) AS zeichen;

UPDATE public.orte SET beschreibung = $txt$Auf dem **Schadowplatz** zwischen Schadowstraße und Königsallee liegt der Märchen-Markt, umgeben von der modernen Architektur des **Kö-Bogens**. Eine Künstlerin hat die **Schattenrisse** auf den Hütten gestaltet: Sie erzählen bekannte deutsche Märchen auf neue Art, manche Figuren bewegen sich sogar im Lichtspiel. Rund **15.000 LEDs** lassen den Platz am Abend leuchten.

Der Markt zieht sich weiter in die **Schadowstraße** bis in die Nähe des Schauspielhauses. Dort reiht sich Hütte an Hütte zwischen den Geschäften, mit Geschenkideen, Essensständen und viel Platz zum Bummeln. Der Märchen-Markt gehört zum Düsseldorfer Weihnachtsmarkt in der Innenstadt, hat dieselben Öffnungszeiten und freien Eintritt.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'maerchen-markt'
RETURNING slug, length(beschreibung) AS zeichen;

UPDATE public.orte SET beschreibung = $txt$**The Winter Village** ist der Weihnachtsmarkt der **Interessengemeinschaft Königsallee (IG Kö)**. Auf der Kö zwischen **Corneliusplatz und Girardetbrücke** entsteht ein Winterdorf aus weißen **Glascontainern**, Hütten und stimmungsvoller Beleuchtung. Das Konzept verbindet Weihnachtstradition mit zeitgenössischem Design.

In den Containern zeigen Marken, **Manufakturen** und Kreative ihre Produkte in **Pop-up-Läden**. Dazu gibt es ein gehobenes gastronomisches Angebot, das regionale Spezialitäten neu interpretiert. Der Eintritt ist frei, und gleich am Corneliusplatz beginnt die Eisbahn Kö on Ice.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'winter-village'
RETURNING slug, length(beschreibung) AS zeichen;

UPDATE public.orte SET beschreibung = $txt$Die **Weihnachtspromenade** gibt es seit **2024**: Gemeinsam mit dem **Circus-Theater Roncalli** wird die Rheinuferpromenade zwischen Burgplatz und Altem Hafen zum Weihnachtsmarkt. Das Konzept ist in Düsseldorf und Umgebung einzigartig. **Nostalgische Verkaufswagen** und **gläserne Pavillons** erinnern an Orangerien aus der Jugendstilzeit.

In **Pop-up-Restaurants** kann man essen und dabei auf den Rhein schauen. Am nördlichen Ende dreht sich das Riesenrad auf dem Burgplatz, die Altstadt mit den übrigen Märkten liegt direkt dahinter. Der Eintritt ist frei. Wer mit dem Rad unterwegs ist: Der Radweg wird während des Marktes über das Rathausufer umgeleitet.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'weihnachtspromenade'
RETURNING slug, length(beschreibung) AS zeichen;

UPDATE public.orte SET beschreibung = $txt$**Kö on Ice** ist die Eisbahn der **DEG Winterwelt** an der Königsallee und läuft länger als die Weihnachtsmärkte: vom 6. November 2026 bis zum **10. Januar 2027**. Gelaufen wird auf **echtem Eis** – die Fläche wurde aus Umwelt- und Energiegründen verkleinert. Der Eintritt kostet 9 Euro, für Kinder unter 11 Jahren 6 Euro; Schlittschuhe kann man für 6 Euro leihen, Helme gibt es auf Nachfrage kostenlos.

Fürs **Eisstockschießen** stehen sechs Bahnen aus Kunststoff an der Theodor-Körner-Straße bereit, für bis zu acht Personen je Bahn; gebucht wird vorab im Ticketshop. Die **Füchschen-Alm** hat zwei Etagen: oben ein Speiserestaurant, unten Würstchen vom Grill und Suppe, dazu Füchschen Alt. An Werktagen gibt es tagsüber Zeitfenster fürs **Schuleislaufen**, Düsseldorfer Schulklassen zahlen dabei keinen Eintritt. Am Totensonntag und an Heiligabend bleibt die Eisbahn geschlossen.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'koe-on-ice'
RETURNING slug, length(beschreibung) AS zeichen;

UPDATE public.orte SET beschreibung = $txt$Das **Wheel of Vision** wird jedes Jahr zur Vorweihnachtszeit auf dem **Burgplatz** am Rhein aufgebaut und dreht sich 2026 schon ab dem 23. Oktober bis zum 3. Januar 2027. Mit **55 Metern** Höhe bietet es einen weiten Blick über Altstadt, Rhein und die beleuchteten Märkte. Die **42 Gondeln** fassen bis zu acht Personen, sind rundum geschlossen und beheizbar – auch bei Wind und Kälte fährt man also geschützt.

Tickets gibt es an der Tageskasse oder online. Wer es besonders mag, bucht eine **Exklusivfahrt**, etwa ein Frühstück in der Gondel. Betrieben wird das Riesenrad von Oscar Bruch jr. aus Düsseldorf. Bei starkem Wind können sich die Öffnungszeiten kurzfristig ändern.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'riesenrad'
RETURNING slug, length(beschreibung) AS zeichen;

UPDATE public.orte SET beschreibung = $txt$Vor der Kulisse von **Schloss Benrath** steht an den **Adventswochenenden** ein Weihnachtsmarkt auf dem Schlossvorplatz. Geöffnet ist er jeweils **freitags bis sonntags**, dazu am Wochenende vor dem ersten Advent; am Totensonntag bleibt er zu. In gemütlichen Holzhütten gibt es ausgefallenes **Kunsthandwerk** als Geschenkidee, dazu warme Getränke und Essen.

Für Kinder fährt wieder die traditionelle **Eisenbahn**. Im Schloss selbst laden **Sonderführungen und Konzerte** dazu ein, das Gebäude von innen zu sehen und das Treiben draußen von drinnen zu beobachten. Der Besuch des Marktes ist **kostenlos**. Am besten fährt man mit der U72 bis „Schloss Benrath“ – an Markttagen fährt sie öfter –, die S-Bahn-Station Benrath liegt etwa zehn Minuten zu Fuß entfernt.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'schloss-benrath'
RETURNING slug, length(beschreibung) AS zeichen;

UPDATE public.orte SET beschreibung = $txt$Beim **Weihnachtszauber** im Böhler Park stehen die Hütten zwischen den **historischen Industriehallen** des Areal Böhler – Industriecharme trifft Weihnachtsstimmung. Der Markt läuft vom **24. November bis 20. Dezember**, dienstags bis sonntags; unter der Woche öffnet er erst am Nachmittag. Die Marktfläche ist größer geworden und hat mehr Plätze zum Verweilen.

Auf der Bühne gibt es täglich **Live-Musik**, unter anderem mit dem New Life Gospelchor und der Böhler Werkskapelle, dazu Mitsingkonzerte und Open-Mic-Abende. Für Kinder gibt es Kinderschminken, Mitmachaktionen und die **Puppenbühne Maatz**, und auch der Weihnachtsmann schaut vorbei. An den Hütten warten Glühwein, winterliche Spezialitäten und herzhafte Klassiker. Das aktuelle Programm steht auf der Website des Areal Böhler.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'areal-boehler'
RETURNING slug, length(beschreibung) AS zeichen;

UPDATE public.orte SET beschreibung = $txt$Vor den **Düsseldorf Arcaden** in Bilk stehen in der Adventszeit mehrere Weihnachtsstände – ein Ort für eine Pause beim Einkaufen an der **Friedrichstraße**. Auch die Arcaden selbst sind mit neuer Weihnachtsdekoration und festlicher Beleuchtung geschmückt. Für Familien lohnt sich besonders der **5. Dezember**: Dann kommen **Mickey und Minnie Maus** vorbei, für Fotos mit den Kindern.

Der Markt hat auch **sonntags** geöffnet, wenn das Einkaufszentrum geschlossen ist. An Heiligabend schließen die Stände am Nachmittag; am Totensonntag und an beiden Weihnachtstagen bleibt der Markt zu.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'bilk-arcaden'
RETURNING slug, length(beschreibung) AS zeichen;

UPDATE public.orte SET beschreibung = $txt$Die **Weihnachtszeit Nordstraße** beginnt am **19. November** auf der Einkaufsstraße in Pempelfort und läuft bis kurz vor Weihnachten. Veranstalter ist die Werbegemeinschaft nördliche Innenstadt (NORD). An den Buden gibt es Punsch, Glühwein, gebrannte Mandeln und handgemachte **Mutzen**; Studierende bekommen mit Studentenausweis 50 Cent Rabatt auf den Glühwein.

Jeder Montag ist **Kids-Day** mit Kasperletheater und günstigerem Kinderkarussell. Auch die Adventssonntage haben eigene Themen: Am 1. Advent dürfen Kinder kostenlos am Glücksrad drehen, am 2. Advent haben die Geschäfte von 13 bis 18 Uhr geöffnet (**verkaufsoffener Sonntag**), der 3. Advent ist Familientag und der 4. Advent steht unter dem Motto „vegan – bio – regional“. Die U-Bahn-Haltestelle Nordstraße ist wegen Renovierung bis 2028 geschlossen – man kommt mit den Straßenbahnlinien 701, 705 und 707 hin.$txt$
WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = 'nordstrasse'
RETURNING slug, length(beschreibung) AS zeichen;

COMMIT;
