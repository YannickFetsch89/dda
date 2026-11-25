"""Zwei Redaktionsbeiträge vom 25.11.2026 (Auftraggeber: „Top 5 Cafés in Flingern“, „10 Empfehlungen für Familien im
Dezember“). Geschrieben in der Claude-Code-Session; Datenbasis: Guide Restaurants & Cafés (Tabelle orte, Flingern),
Eventkalender (Kategorie family, Dezember 2026) und Weihnachtsmarkt-Guide. SQL: beitraege_sql.py.
"""
from datetime import date

RC = "/guides/restaurants-cafes"
WM = "/guides/weihnachtsmaerkte"

# ── Genuss: Top 5 Cafés in Flingern ─────────────────────────────────────────────────────────────────
CAFES = {
    "id": "9a0d7dfc-a326-4901-ac63-aab64c124e6a",
    "slug": "top-5-cafes-in-flingern",
    "rubrik": "genuss",
    "autor_slug": "laurenz-weigelt",
    "titel": "Top 5 Cafés in Flingern: Wo sich der Weg für Kaffee und Kuchen lohnt",
    "seo_titel": "Top 5 Cafés in Flingern – Kaffee, Kuchen, Frühstück",
    "teaser": "Specialty Coffee, eigene Rösterei, Frühstück mit Ruhe: unsere fünf liebsten Cafés in Flingern – "
              "und warum die Ackerstraße eine Kaffeemeile ist.",
    "kurzfassung": [
        "Jaenner Modern Coffee: Pour Over und frisch geröstete Bohnen zum Mitnehmen.",
        "No Worries: wechselnde Gastbohnen, Zimtschnecken und ein Babyccino für die Kleinen.",
        "Fjaka Café & Clubhouse: Kaffee aus der eigenen Rösterei und cremiger Cheesecake.",
        "MERCY coffee company: Kuchen und Bagels in einem kleinen, gemütlichen Café.",
        "Café Liebe: marokkanisches Frühstück und Bowls ohne Eile.",
    ],
    "hero_bild": "/fallback/sprachcafe-1.webp",
    "hero_alt": "Symbolbild: Gäste an Holztischen in einem Café mit großen Fenstern",
    "hero_nachweis": "Symbolbild",
    "gueltig_von": None,
    "gueltig_bis": None,
    "naechste_pruefung": date(2027, 2, 1),
    "ort_slugs": ["jaenner-modern-coffee-flingern", "no-worries-flingern", "fjaka-cafe-clubhouse-flingern",
                  "mercy-coffee-company-flingern", "cafe-liebe-flingern"],
    "quellen": [{"titel": "dies.das.düsseldorf: Restaurants & Cafés in Flingern",
                 "url": "https://diesdas.events/guides/restaurants-cafes/stadtteil/flingern", "abgerufen_am": "2026-11-25"}],
    "datenbasis": "Guide Restaurants & Cafés (orte, Flingern), Stand 25.11.2026",
    "abschnitte": [
        {"ueberschrift": "", "text_md": (
            "Flingern ist eines der besten Viertel Düsseldorfs, um einfach Kaffee trinken zu gehen. In unserem Guide stehen "
            "allein hier mehr als zehn Cafés – von der kleinen Rösterei bis zum Frühstückscafé. Die Auswahl ist also groß, "
            "und genau deshalb lohnt sich ein genauer Blick.\n\n"
            "Unsere fünf Favoriten haben jeweils ein eigenes Profil: Hier geht es um sorgfältig zubereiteten Kaffee, gutes "
            "Gebäck, eine Atmosphäre zum Bleiben und das gewisse Etwas, das man nicht in jedem Viertel findet. Die "
            "Reihenfolge ist keine strenge Rangliste – jedes Café ist für einen anderen Moment das richtige."
        )},
        {"ueberschrift": "1. Jaenner Modern Coffee: für alle, die Kaffee ernst nehmen", "text_md": (
            "Das kleine Café an der Ackerstraße ist die erste Adresse für Kaffeeliebhaber. Der Kaffee wird hier mit viel "
            "Sorgfalt zubereitet, besonders der Pour Over hat einen sehr guten Ruf, und die Bohnenauswahl ist vielseitig. Wer "
            "auf den Geschmack gekommen ist, nimmt die Bohnen frisch geröstet für zu Hause mit.\n\n"
            "Dazu gibt es Kuchen und süße Teilchen, allen voran ein Pistazien-Croissant und einen Schokokuchen, der angenehm "
            "wenig süß ist. Am Wochenende kommt ein Frühstück dazu – ein guter Grund, den Samstag hier zu beginnen.\n\n"
            "{{ort:jaenner-modern-coffee-flingern}}"
        )},
        {"ueberschrift": "2. No Worries: Kaffee mit Gastbohnen und Herz", "text_md": (
            "An der Lindenstraße wartet ein kleines Café, das mit richtig gutem Kaffee punktet und immer wieder Gastbohnen "
            "zum Probieren anbietet. Neben Espresso-Varianten gibt es Matcha, Tee und einen klassischen Babyccino für die "
            "Kleinen – praktisch, wenn Kinder mit dabei sind. Der Iced Latte ist ein Favorit vieler Gäste.\n\n"
            "Auf der Theke liegen Croissants, Zimtschnecken, Schokomürbchen und eine wechselnde Kuchenauswahl. Die "
            "Atmosphäre ist entspannt, die Inhaber und das Team sind herzlich, und auch hier gibt es Kaffeebohnen zum "
            "Mitnehmen.\n\n"
            "{{ort:no-worries-flingern}}"
        )},
        {"ueberschrift": "3. Fjaka Café & Clubhouse: Kaffee aus der eigenen Rösterei", "text_md": (
            "Im Fjaka an der Ackerstraße steht der Kaffee aus der eigenen Rösterei im Mittelpunkt, Espresso und Milch sind "
            "genau aufeinander abgestimmt. Dazu gibt es Matcha-Spezialitäten, Frühstückssnacks und auch einige alkoholische "
            "Getränke – das Café kann schnell zum Stammlokal werden.\n\n"
            "An der kleinen, feinen Kuchentheke ist der New York Cheesecake besonders cremig, herzhaft geht es mit Bagels. "
            "Drinnen ist es hell und freundlich, die Stimmung bleibt auch bei gutem Besuch ruhig. Im Sommer locken "
            "Sonnenplätze draußen, und für Hunde steht ein Wassernapf bereit.\n\n"
            "{{ort:fjaka-cafe-clubhouse-flingern}}"
        )},
        {"ueberschrift": "4. MERCY coffee company: Kuchen, Bagels und Zeit zum Lesen", "text_md": (
            "Das MERCY an der Birkenstraße ist klein, aber richtig gemütlich und liebevoll eingerichtet – ein Ort, an dem man "
            "gerne hängen bleibt, ein Buch dabei hat oder sich mit Freunden trifft. Neben gutem Kaffee kommen auch heiße "
            "Schokolade und Tee gut an.\n\n"
            "Die Stärke ist der Kuchen: Karottenkuchen und Zitronen-Käsekuchen gehören zu den Empfehlungen. Wer es herzhaft "
            "mag, nimmt einen frisch getoasteten Bagel, etwa mit Tomate und Mozzarella. Verschiedene Milchalternativen sind "
            "selbstverständlich.\n\n"
            "{{ort:mercy-coffee-company-flingern}}"
        )},
        {"ueberschrift": "5. Café Liebe: Frühstück ohne Eile", "text_md": (
            "Wer in Flingern in Ruhe frühstücken möchte, ist im Café Liebe an der Platanenstraße richtig. Das marokkanische "
            "Frühstück ist der Tipp des Hauses: Eier, die genau auf den Punkt kommen, dazu Lachs und frische Beilagen, die gut "
            "zusammenpassen. Die Beeren-Bowl mit frischem Obst, Banane und Nüssen ist liebevoll angerichtet.\n\n"
            "Das Ambiente ist stilvoll und gemütlich, draußen lässt es sich angenehm sitzen. Ideal für ein ausgiebiges "
            "Frühstück zu zweit oder mit Freunden.\n\n"
            "{{ort:cafe-liebe-flingern}}"
        )},
        {"ueberschrift": "Die Ackerstraße: Flingerns Kaffeemeile", "text_md": (
            "Auffällig ist, wie viele gute Cafés an einer einzigen Straße liegen. Neben Jaenner und dem Fjaka findet ihr an der "
            "Ackerstraße das [Café Kleinod](" + RC + "/cafe-kleinod-flingern), in dem ein Paar aus Italien hausgemachte "
            "Kuchen, Tiramisu und Gebäck mit Pistazie serviert – ruhig gelegen und ideal zum Plaudern. Das "
            "[coffiez](" + RC + "/coffiez-flingern) ist modern und gemütlich zugleich, der Chef bedient oft selbst, und der "
            "Matcha mit Erdbeeren ist ein Hingucker. Und im [NOSTIMO](" + RC + "/nostimo-flingerns-finest-flingern) "
            "fühlt sich der Espresso an wie in einer italienischen Bar, dazu gibt es frische Cornetti und Panini mit "
            "Mortadella.\n\n"
            "Wer an einem freien Vormittag Zeit hat, kann die Ackerstraße entlangspazieren und sich von Café zu Café treiben "
            "lassen – Flingern lässt sich so gut kennenlernen."
        )},
        {"ueberschrift": "Noch mehr gute Adressen", "text_md": (
            "Zwei weitere Tipps für den Brunch: Im [Dritan Alsela Coffee](" + RC + "/dritan-alsela-coffee-flingern) an der "
            "Schlüterstraße hat das Frühstück einen festen Platz, mit internationalen Gerichten und frischen Baguettes. Und im "
            "[Espresso Perfetto](" + RC + "/espresso-perfetto-flingern) an der Grafenberger Allee lohnt sich die schöne "
            "Terrasse, dazu gibt es ukrainische Syrnyki, frisch gebratene Käsepfannkuchen.\n\n"
            "Alle Cafés und Restaurants im Viertel findet ihr in unserem Guide unter [Flingern](" + RC + "/stadtteil/flingern).\n\n"
            "{{guide:restaurants-cafes}}"
        )},
    ],
    "faq": [
        {"frage": "Wo gibt es in Flingern besonders guten Kaffee?",
         "antwort": "Für Specialty Coffee sind Jaenner Modern Coffee und No Worries gute Adressen, beide verkaufen auch "
                    "Bohnen zum Mitnehmen. Das Fjaka röstet seinen Kaffee selbst."},
        {"frage": "Wo kann man in Flingern gut frühstücken?",
         "antwort": "Im Café Liebe gibt es ein marokkanisches Frühstück und Bowls, im Dritan Alsela Coffee internationale "
                    "Frühstücksgerichte. Jaenner Modern Coffee bietet am Wochenende Frühstück an."},
        {"frage": "Welches Café in Flingern passt mit Kindern?",
         "antwort": "No Worries hat einen Babyccino für die Kleinen und eine entspannte Atmosphäre."},
    ],
}

# ── Familie: 10 Empfehlungen im Dezember ───────────────────────────────────────────────────────────
FAMILIE = {
    "id": "79b06de0-41f3-4647-bed2-d07956059ebf",
    "slug": "10-empfehlungen-fuer-familien-im-dezember",
    "rubrik": "familie",
    "autor_slug": "amelie-glasner",
    "titel": "10 Empfehlungen für Familien im Dezember: Düsseldorf mit Kindern",
    "seo_titel": "Düsseldorf mit Kindern im Dezember: 10 Tipps",
    "teaser": "Musical, Kinderkino, Becher bemalen und ein Weihnachtsmarkt mit Rodelbahn: zehn Ideen für Familien in "
              "Düsseldorf und Umgebung im Dezember.",
    "kurzfassung": [
        "Musicals für Kinder: „Der Glöckner von Notre Dame“ im Capitol, „Santa Claus“ am 5. Dezember in Ratingen.",
        "Am 6. Dezember läuft „Momo“ im Familienkino des Filmmuseums.",
        "Am 12. Dezember: Familienführung im NRW-Forum, Familienworkshop im K20 und Spieletag in Neuss.",
        "Weihnachtsmarkt Gerresheim mit Rodelbahn und Puppentheater an zwei Adventswochenenden.",
        "Vorlesen und Basteln in den Stadtbüchereien, etwa am 19. Dezember in der Zentralbibliothek.",
    ],
    "hero_bild": "/ort-bilder/weihnachtsmaerkte/gerresheim.webp",
    "hero_alt": "Weihnachtsmarkt in Gerresheim am Abend: Kinderkarussell vor der Basilika, beleuchtete Hütten",
    "hero_nachweis": "dies.das.düsseldorf",  # eigenes Foto: Pflichtfeld, wird nicht angezeigt
    "gueltig_von": date(2026, 12, 1),
    "gueltig_bis": date(2026, 12, 31),
    "naechste_pruefung": date(2026, 12, 8),
    "ort_slugs": ["weihnachtsmarkt-gerresheim", "weihnachtszauber-areal-boehler-heerdt", "maerchen-markt-stadtmitte",
                  "weihnachtszeit-nordstrasse-pempelfort"],
    "quellen": [
        {"titel": "dies.das.düsseldorf: Familienevents", "url": "https://diesdas.events/kategorie/familie", "abgerufen_am": "2026-11-25"},
        {"titel": "dies.das.düsseldorf: Weihnachtsmärkte", "url": "https://diesdas.events/guides/weihnachtsmaerkte", "abgerufen_am": "2026-11-25"},
    ],
    "datenbasis": "Eventkalender (Kategorie family, Dezember 2026) und Weihnachtsmarkt-Guide, Stand 25.11.2026",
    "abschnitte": [
        {"ueberschrift": "", "text_md": (
            "Im Dezember ist in Düsseldorf für Familien besonders viel los: Bühnen spielen Weihnachtsstücke, Museen laden zu "
            "Familienführungen ein, und auf den Weihnachtsmärkten drehen sich die Karussells. Aus unserem Kalender haben wir "
            "zehn Ideen ausgewählt, die gut zu Kindern passen – von der großen Musicalbühne bis zur Vorlesestunde in der "
            "Bücherei um die Ecke.\n\n"
            "Termine, Uhrzeiten und Preise stehen in den Karten unter jedem Tipp. Sie kommen live aus unserem Kalender – "
            "ändert sich etwas, seht ihr es dort sofort."
        )},
        {"ueberschrift": "1. Musical-Klassiker im Capitol: Der Glöckner von Notre Dame", "text_md": (
            "Im Capitol Theater in Flingern steht das Disney-Musical über den Glöckner Quasimodo auf dem Spielplan, der sich "
            "in Notre-Dame versteckt und sich nach dem Leben draußen sehnt – bis die mutige Esmeralda ihm beisteht. Die Songs "
            "stammen von Alan Menken und Stephen Schwartz, das Ensemble des Budapester Operettentheaters spielt mit einem "
            "vierzehnköpfigen Live-Orchester. Gespielt wird an vielen Terminen im Dezember. Die Geschichte hat auch ernste "
            "Momente, für Schulkinder ist sie ein großes Bühnenerlebnis.\n\n"
            "{{event:6d392e7f-f941-4161-a698-a312c088d5b3}}"
        )},
        {"ueberschrift": "2. Geburtstagsparty mit den tonies in der Tonhalle", "text_md": (
            "Wer zu Hause eine Toniebox hat, kennt die kleinen Hörfiguren. Jetzt laden die tonies zur großen "
            "Geburtstagsparty in die Tonhalle ein – ein Termin für alle, bei denen die Box im Kinderzimmer nicht mehr "
            "stillsteht.\n\n"
            "{{event:d9f8745e-3f2d-4507-9045-c7105067d9d9}}"
        )},
        {"ueberschrift": "3. Weihnachtsmarkt mit Rodelbahn: Gerresheim", "text_md": (
            "Unter den Weihnachtsmärkten ist der Markt auf dem Gerricusplatz in Gerresheim für Kinder ein Höhepunkt. An zwei "
            "Adventswochenenden gibt es dort eine rund zwanzig Meter lange Rodelbahn, ein Puppentheater und Eisstockschießen "
            "für Groß und Klein. Wer an anderen Tagen unterwegs ist: Im Areal Böhler in Heerdt spielt die Puppenbühne Maatz, "
            "dazu gibt es Kinderschminken und Mitmachaktionen, und vor Schloss Benrath fährt die traditionelle Eisenbahn für "
            "Kinder. Welche Märkte heute geöffnet haben, zeigt unser [Weihnachtsmarkt-Guide](" + WM + ").\n\n"
            "{{ort:weihnachtsmarkt-gerresheim}}\n\n"
            "{{ort:weihnachtszauber-areal-boehler-heerdt}}"
        )},
        {"ueberschrift": "4. Kinderkino am Sonntag: Momo im Filmmuseum", "text_md": (
            "Das Familienkino in der Black Box im Filmmuseum in der Altstadt zeigt „Momo“ – die Geschichte nach Michael Ende "
            "über das Mädchen, das den grauen Herren die gestohlene Zeit zurückholt. Ein schöner Programmpunkt für einen "
            "Adventssonntag, der draußen vielleicht grau ist.\n\n"
            "{{event:d787de03-bca6-4aea-af7e-7019709cb691}}"
        )},
        {"ueberschrift": "5. Weihnachtsmusical in Ratingen: Santa Claus", "text_md": (
            "Ein Musical ausdrücklich für Kinder und Familien: In der Stadthalle Ratingen kommt „Santa Claus – das Musical“ "
            "auf die Bühne – ein kurzer Ausflug über die Stadtgrenze, der sich zum Start in die Adventszeit anbietet.\n\n"
            "{{event:0496484d-939e-47a4-8322-43de7a900e12}}"
        )},
        {"ueberschrift": "6. Anime, Mangas und Super Mario: Familienführung im NRW-Forum", "text_md": (
            "Ob Sailor Moon, One Piece oder Super Mario: Die Familienführung im NRW-Forum ist eine Entdeckungsreise durch die "
            "ostasiatische Popkultur. Rund tausend Werke zeigen Essen, Mode, Filme und Comics aus China, Hongkong, Japan, "
            "Südkorea und Taiwan. Kleine und große Besucherinnen und Besucher schauen, hören und probieren gemeinsam aus – "
            "ideal für Familien mit Kindern, die selbst gerade Fans sind.\n\n"
            "{{event:47b0356c-ad3a-42dc-a9f0-cddbd6ec9b42}}"
        )},
        {"ueberschrift": "7. Kunst zum Mitmachen: Familienworkshop im K20", "text_md": (
            "Im K20 am Grabbeplatz öffnet der Playground für einen offenen Familienworkshop. Offen heißt: Ihr könnt "
            "dazukommen und gemeinsam mit euren Kindern kreativ werden – ein guter Weg, Kinder ohne Druck an ein Kunstmuseum "
            "heranzuführen.\n\n"
            "{{event:55e7be0d-5bf0-4851-b895-0c2fa34e3f7a}}"
        )},
        {"ueberschrift": "8. Spieletag in Neuss: Rheingespielt XXL", "text_md": (
            "Das Rheinische Landestheater in Neuss wird zum großen Spieletag: Bei „Rheingespielt XXL“ dreht sich alles ums "
            "gemeinsame Spielen. Für Familien, die gerne am Tisch zusammensitzen, ist das ein Ausflug wert.\n\n"
            "{{event:f414c593-afa4-4043-bdba-e6b49c4c51c4}}"
        )},
        {"ueberschrift": "9. Gemeinsam kreativ: Lieblingsbecher bemalen im Craft Studio", "text_md": (
            "Ein Programmpunkt für Groß und Klein zusammen: Beim Workshop „Mini & Me – Lieblingsbecher“ im Craft Studio "
            "gestalten Kinder gemeinsam mit einem Erwachsenen ihren eigenen Becher. Am Ende steht ein Stück, das jeden Morgen "
            "auf dem Frühstückstisch an den Nachmittag erinnert – und vielleicht auch ein schönes Weihnachtsgeschenk für "
            "Oma und Opa. Wer lieber allein gestaltet, findet im Dezember im Craft Studio weitere Workshops, vom Tassenmalen "
            "bis zum Kerzengießen.\n\n"
            "{{event:ed197365-8c99-47c8-bf9a-b59a8766cdeb}}"
        )},
        {"ueberschrift": "10. Vorlesen und Basteln in den Stadtbüchereien", "text_md": (
            "Die Stadtbüchereien sind im Dezember eine kleine Fundgrube für Familien: In vielen Stadtteilen gibt es "
            "Geschichtenzeiten zum Zuhören, weihnachtliche Bastelaktionen und Workshops mit 3D-Stiften. Zwei Beispiele: In der "
            "Zentralbibliothek im KAP1 wartet man gemeinsam aufs Christkind, in der Stadtbücherei Unterrath wird "
            "weihnachtlich vorgelesen. Der Vorteil: Die Büchereien liegen oft direkt im Viertel, der Weg ist kurz.\n\n"
            "{{event:732761d0-8557-46eb-adf8-d1bb6bc89517}}\n\n"
            "{{event:8738c603-107d-4a9e-952f-c348551f619a}}"
        )},
        {"ueberschrift": "Noch mehr Ideen für Familien", "text_md": (
            "Das waren unsere zehn Tipps – im Kalender gibt es noch viel mehr: Kindertheater, Kreativworkshops, "
            "Nikolausaktionen und Familienbrunch. Alle Termine findet ihr gesammelt unter [Familie](/kategorie/familie), "
            "und was am Wochenende los ist, steht in unserem [Wochenend-Programm](/wochenende)."
        )},
        {"ueberschrift": "Zum Schluss: Weihnachtsmärkte mit Kindern", "text_md": (
            "Ein Weihnachtsmarkt gehört für viele Familien einfach zum Dezember – und in Düsseldorf und Umgebung gibt es "
            "einige, die für Kinder besonders viel zu bieten haben. Neben Gerresheim lohnen sich diese Märkte:\n\n"
            "- **Märchen-Markt am Schadowplatz:** Auf den Hütten erzählen Schattenrisse bekannte deutsche Märchen neu, "
            "manche Figuren bewegen sich sogar im Lichtspiel. Wer mit Kindern durch die Innenstadt bummelt, kann hier "
            "Märchen raten.\n"
            "- **Riesenrad auf dem Burgplatz:** Aus den geschlossenen, beheizbaren Gondeln geht der Blick über Altstadt, "
            "Rhein und die beleuchteten Märkte – auch bei Wind und Kälte ein Erlebnis.\n"
            "- **Kö on Ice:** Auf der Eisbahn an der Königsallee wird auf echtem Eis gelaufen, Schlittschuhe können vor Ort "
            "geliehen werden, Helme gibt es auf Nachfrage.\n"
            "- **Weihnachtszeit Nordstraße:** Jeder Montag ist Kids-Day mit Kasperletheater und vergünstigtem Kinderkarussell, "
            "der dritte Advent ist Familientag.\n"
            "- **Benrather Weihnachtsdörfchen:** Am Nikolaustag schaut der Nikolaus vorbei – für Kinder ein Höhepunkt.\n"
            "- **Ratinger Weihnachtsmarkt:** In der Mitte des Marktplatzes dreht sich ein Karussell mit Helikopter, Rennauto "
            "und Motorrad, und bis zum vierten Advent spielt der Kasperl auf der Marktbühne.\n\n"
            "Die Öffnungszeiten unterscheiden sich von Markt zu Markt, manche öffnen nur an den Wochenenden. Unser "
            "Weihnachtsmarkt-Guide zeigt für jeden Tag, welche Märkte geöffnet haben – und mit den Filtern für Karussell und "
            "Puppenbühne findet ihr schnell die Märkte, auf denen Kinder am meisten Spaß haben.\n\n"
            "{{ort:maerchen-markt-stadtmitte}}\n\n"
            "{{ort:weihnachtszeit-nordstrasse-pempelfort}}\n\n"
            "{{guide:weihnachtsmaerkte}}"
        )},
    ],
    "faq": [
        {"frage": "Was kann man im Dezember mit Kindern in Düsseldorf unternehmen?",
         "antwort": "Zum Beispiel ein Musical im Capitol, Kinderkino im Filmmuseum, Kreativworkshops für Eltern und Kinder, "
                    "Familienführungen in Museen wie dem NRW-Forum und dem K20, Weihnachtsmärkte mit Kinderprogramm und "
                    "Vorlesestunden in den Stadtbüchereien."},
        {"frage": "Welcher Weihnachtsmarkt in Düsseldorf hat besonders viel für Kinder?",
         "antwort": "Gerresheim mit Rodelbahn und Puppentheater, das Areal Böhler mit der Puppenbühne Maatz, Schloss Benrath "
                    "mit der Kindereisenbahn und die Nordstraße mit ihrem Kids-Day am Montag."},
        {"frage": "Wo finde ich alle Familienevents in Düsseldorf?",
         "antwort": "Im Kalender von dies.das.düsseldorf unter der Kategorie Familie, mit Datum, Ort und Preis."},
    ],
}

BEITRAEGE = [CAFES, FAMILIE]
