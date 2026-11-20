"""Die ersten beiden Magazin-Beiträge (Plan docs/plan-redaktion-2026-11-19.md, Schritt 6, 20.11.2026).

Geschrieben in einer Claude-Code-Session mit dem Auftraggeber (Saison/Stadtleben, Plan 4.2), Datenbasis: Stammdaten des
Weihnachtsmarkt-Guides (Tabelle orte, typ weihnachtsmarkt, Stand 17.–19.11.2026). Der Generator
docs/magazin-startbeitraege/sql_erzeugen.py prüft beide Beiträge mit pipeline.magazin.pruefen (a)–(i) und schreibt das SQL.
"""
from datetime import date

WM = "/guides/weihnachtsmaerkte"

# ── Beitrag 1: Launch des Magazins (Stadtleben) ─────────────────────────────────────────────────────
LAUNCH = {
    "id": "0d68a5fe-d20f-4086-a4df-a91971359813",  # fest: so passen neue Vorschau-Links auch nach dem ersten Anlegen
    "slug": "willkommen-im-magazin",
    "rubrik": "stadtleben",
    "autor_slug": "nathalie-kirchner",
    "titel": "Neu bei dies.das.düsseldorf: unser Magazin für die Stadt",
    "seo_titel": "Neu: das Magazin für Düsseldorf",
    "teaser": "Wochenvorschau, Monats-Tipps, Saison, Nachtleben, Genuss und Familie: Was euch im neuen Magazin "
              "von dies.das.düsseldorf erwartet.",
    "kurzfassung": [
        "Das Magazin ordnet ein, was in Düsseldorf ansteht – mit Event-Karten, die immer aktuell sind.",
        "Jede Woche eine Vorschau, zum Monatsende die Tipps für den nächsten Monat, dazu Saison- und Stadtthemen.",
        "Sieben Rubriken von Nachtleben über Genuss bis Familie, jede mit einem festen Themenschwerpunkt.",
        "Jeder Beitrag wird vor der Veröffentlichung von der Redaktion geprüft und freigegeben.",
    ],
    "hero_bild": "/ort-bilder/weihnachtsmaerkte/riesenrad.webp",
    "hero_alt": "Düsseldorfer Altstadt am Abend: Schlossturm, beleuchtetes Riesenrad auf dem Burgplatz und der Turm von "
                "St. Lambertus, davor der Rhein",
    "hero_nachweis": "dies.das.düsseldorf",  # eigenes Foto: Pflichtfeld, wird nicht angezeigt
    "gueltig_von": None,
    "gueltig_bis": None,
    "naechste_pruefung": None,
    "ort_slugs": [],
    "quellen": [],
    "abschnitte": [
        {
            "ueberschrift": "",
            "text_md": (
                "Jeden Tag sammelt dies.das.düsseldorf Veranstaltungen, Orte und Termine aus Düsseldorf, Neuss und "
                "Ratingen: Konzerte und Clubnächte, Ausstellungen, Märkte, Lesungen, Kinderprogramm und vieles mehr. "
                "Das ist eine Menge – und genau deshalb gibt es jetzt das Magazin. Hier suchen wir aus, ordnen ein und "
                "erklären, warum sich etwas lohnt und für wen.\n\n"
                "Das Magazin ersetzt nicht den Kalender, es ergänzt ihn. Wer schnell wissen will, was heute los ist, "
                "findet das wie gewohnt unter [Heute](/heute) oder in der Suche unter [Entdecken](/entdecken). Wer "
                "lieber eine Auswahl mit Begründung liest, ist hier richtig."
            ),
        },
        {
            "ueberschrift": "Was ihr hier findet",
            "text_md": (
                "Das Magazin ist in sieben Rubriken gegliedert. Jede hat einen klaren Auftrag:\n\n"
                "- **[Wochenvorschau](/magazin/rubrik/wochenvorschau):** Jede Woche ein Überblick über die kommenden "
                "Tage – mit einem Highlight der Woche und einer Auswahl, die von Kultur bis Party reicht.\n"
                "- **[Monats-Tipps](/magazin/rubrik/monats-tipps):** Zum Monatsende die stärksten Termine des nächsten "
                "Monats, damit ihr früh planen und Tickets rechtzeitig sichern könnt.\n"
                "- **[Saison](/magazin/rubrik/saison):** Themen, die zur Jahreszeit gehören – jetzt im Advent die "
                "Weihnachtsmärkte, später Karneval, Sommer am Rhein und die großen Feste der Stadt.\n"
                "- **[Nachtleben & Musik](/magazin/rubrik/nachtleben):** Konzerte, Clubnächte und alles, was nach "
                "Sonnenuntergang passiert.\n"
                "- **[Genuss](/magazin/rubrik/genuss):** Restaurants, Cafés, Foodmärkte, Tastings und Brauhauskultur.\n"
                "- **[Familie](/magazin/rubrik/familie):** Kinderprogramm, Ausflüge und Ideen für Tage, an denen das "
                "Wetter nicht mitspielt.\n"
                "- **[Stadtleben](/magazin/rubrik/stadtleben):** Stadtteile, Hintergründe und alles, was in keine "
                "andere Schublade passt – so wie dieser Beitrag."
            ),
        },
        {
            "ueberschrift": "Termine, die nicht veralten",
            "text_md": (
                "Ein Problem vieler Veranstaltungstipps kennt ihr: Der Text ist geschrieben, dann verschiebt sich ein "
                "Termin oder ein Konzert fällt aus, und niemand ändert den Artikel. Bei uns stehen die harten Fakten "
                "deshalb nicht im Fließtext. Datum, Uhrzeit, Ort und Preis zeigen die eingebetteten Event-Karten – und "
                "die kommen direkt aus unserer Veranstaltungsdatenbank, die jeden Tag aktualisiert wird.\n\n"
                "Ändert sich etwas, ändert sich die Karte im Beitrag mit. Wird ein Event abgesagt, seht ihr das "
                "sofort. Der Text kümmert sich um das, was eine Datenbank nicht kann: einordnen, vergleichen, "
                "empfehlen. Welches Konzert passt zu einem ruhigen Abend, welcher Markt zu einem Ausflug mit Kindern, "
                "welches Viertel lohnt sich für einen Spaziergang mit Abstecher ins Café."
            ),
        },
        {
            "ueberschrift": "Wie wir auswählen",
            "text_md": (
                "Die Auswahl für Wochenvorschau und Monats-Tipps folgt festen Regeln, damit sie nicht einseitig wird: "
                "Sie mischt verschiedene Kategorien, nimmt höchstens wenige Termine vom selben Ort auf und zeigt "
                "Veranstaltungen über mehrere Tage nur einmal. So steht das Theaterstück neben dem Clubabend, die "
                "Ausstellung neben dem Familienprogramm – und ihr bekommt einen Eindruck davon, wie vielseitig "
                "Düsseldorf in einer Woche sein kann."
            ),
        },
        {
            "ueberschrift": "Verknüpft mit unseren Guides",
            "text_md": (
                "Neben dem Kalender pflegen wir Guides zu Orten, die man in Düsseldorf kennen sollte: "
                "[Weihnachtsmärkte](/guides/weihnachtsmaerkte), [Restaurants & Cafés](/guides/restaurants-cafes), "
                "[Kneipen & Bars](/guides/kneipen-bars) und [Clubs](/guides/clubs). Das Magazin greift darauf zurück. "
                "Wenn ein Beitrag einen Ort erwähnt, führt euch die Karte direkt auf dessen Seite im Guide – mit "
                "Lage, Öffnungszeiten und allem, was wir dazu gesammelt haben.\n\n"
                "Zum Start passt das besonders gut: Die Weihnachtsmarkt-Saison hat begonnen, und unser erster Saison-Beitrag stellt "
                "[die schönsten Weihnachtsmärkte in Düsseldorf](/magazin/die-schoensten-weihnachtsmaerkte-in-duesseldorf) "
                "vor – von den Themenmärkten in der Innenstadt bis zum Markt vor Schloss Benrath.\n\n"
                "{{guide:weihnachtsmaerkte}}"
            ),
        },
        {
            "ueberschrift": "Wer hier schreibt",
            "text_md": (
                "Die Beiträge erscheinen unter fünf Autorennamen, die jeweils für einen Themenbereich stehen: "
                "[Lisa Hartwig](/magazin/autor/lisa-hartwig) für Events und Wochenplanung, "
                "[Dan Suttner](/magazin/autor/dan-suttner) für Nachtleben und Musik, "
                "[Laurenz Weigelt](/magazin/autor/laurenz-weigelt) für Genuss, "
                "[Amelie Glasner](/magazin/autor/amelie-glasner) für Familie und "
                "[Nathalie Kirchner](/magazin/autor/nathalie-kirchner) für das Stadtleben. Es sind redaktionelle "
                "Pseudonyme – so findet ihr Beiträge zu einem Thema schnell wieder.\n\n"
                "Unsere Beiträge entstehen auf Grundlage eigener Veranstaltungsdaten, redaktioneller Recherche und "
                "teilweise mithilfe KI-gestützter Werkzeuge. Jeder Beitrag wird vor der Veröffentlichung auf Fakten, "
                "Quellen und Relevanz geprüft und redaktionell freigegeben. Wer die Verantwortung trägt, steht in den "
                "Autorenprofilen, die über die Namen oben verlinkt sind."
            ),
        },
        {
            "ueberschrift": "Sagt uns, was fehlt",
            "text_md": (
                "Das Magazin wächst mit euch. Wenn euch ein Fehler auffällt, ein Thema fehlt oder ihr einen Ort kennt, "
                "der unbedingt in einen Guide gehört, schreibt uns an [hallo@diesdas.events](mailto:hallo@diesdas.events). "
                "Sachliche Korrekturen "
                "vermerken wir am Ende des jeweiligen Beitrags.\n\n"
                "Und wenn ihr nichts verpassen wollt: Alle Beiträge findet ihr gesammelt auf der "
                "[Startseite des Magazins](/magazin), sortiert nach Rubriken und Autorennamen."
            ),
        },
    ],
    "faq": [
        {"frage": "Wie oft erscheinen neue Beiträge?",
         "antwort": "Die Wochenvorschau erscheint jede Woche, die Monats-Tipps zum Monatsende. Dazu kommen Beiträge zu "
                    "Saisonthemen, Nachtleben, Genuss, Familie und Stadtleben, wenn es etwas zu erzählen gibt."},
        {"frage": "Woher stammen die Informationen?",
         "antwort": "Aus der Veranstaltungsdatenbank von dies.das.düsseldorf, aus unseren Guides und aus redaktioneller "
                    "Recherche. Die Quellen nennen wir unter dem jeweiligen Beitrag."},
        {"frage": "Wer schreibt die Beiträge?",
         "antwort": "Die Redaktion von dies.das.düsseldorf. Die Autorennamen sind redaktionelle Pseudonyme für "
                    "Themenbereiche. Jeder Beitrag wird vor der Veröffentlichung geprüft und freigegeben."},
    ],
}

# ── Beitrag 2: Die schönsten Weihnachtsmärkte (Saison) ──────────────────────────────────────────────
WEIHNACHTSMAERKTE = {
    "id": "a784bc5b-1146-4fce-986a-4c1b4743da05",  # fest: so passen neue Vorschau-Links auch nach dem ersten Anlegen
    "slug": "die-schoensten-weihnachtsmaerkte-in-duesseldorf",
    "rubrik": "saison",
    "autor_slug": "nathalie-kirchner",
    "titel": "Die schönsten Weihnachtsmärkte in Düsseldorf",
    "seo_titel": "Die schönsten Weihnachtsmärkte in Düsseldorf 2026",
    "teaser": "Themenmärkte in der Innenstadt, Kunsthandwerk vor Schloss Benrath, Live-Musik im Areal Böhler: "
              "unsere Auswahl für den Advent 2026.",
    "kurzfassung": [
        "Die Märkte in der Innenstadt laufen vom 19. November bis 30. Dezember und liegen zu Fuß beieinander.",
        "Schloss Benrath öffnet an den Adventswochenenden, mit Kunsthandwerk und Eisenbahn für Kinder.",
        "Im Areal Böhler gibt es an allen Markttagen Live-Musik zwischen historischen Industriehallen.",
        "Für Familien: Puppenbühnen, Karussells und in Gerresheim sogar eine Rodelbahn.",
        "Welche Märkte heute geöffnet haben, zeigt unser Weihnachtsmarkt-Guide.",
    ],
    "hero_bild": "/ort-bilder/weihnachtsmaerkte/maerchen-markt.webp",
    "hero_alt": "Märchen-Markt am Schadowplatz am Abend: beleuchtete Hütten, ein Karussell und ein Baum voller Lichter",
    "hero_nachweis": "dies.das.düsseldorf",  # eigenes Foto: Pflichtfeld, wird nicht angezeigt
    "gueltig_von": date(2026, 11, 19),
    "gueltig_bis": date(2027, 1, 10),
    "naechste_pruefung": date(2026, 12, 1),
    "ort_slugs": [
        "duesseldorfer-weihnachtsmarkt-in-der-innenstadt-altstadt",
        "maerchen-markt-stadtmitte",
        "weihnachtspromenade-am-rhein-altstadt",
        "weihnachtsmarkt-schloss-benrath",
        "weihnachtszauber-areal-boehler-heerdt",
        "weihnachtszeit-nordstrasse-pempelfort",
        "koe-on-ice-deg-winterwelt-stadtmitte",
        "kiez-advent-markt-der-1000-lichter-derendorf",
        "weihnachtsmarkt-gerresheim",
        "neusser-weihnachtsmarkt-neuss",
        "ratinger-weihnachtsmarkt-ratingen",
    ],
    "quellen": [
        {"titel": "Visit Düsseldorf: Weihnachten in Düsseldorf – häufige Fragen",
         "url": "https://www.visitduesseldorf.de/erleben/veranstaltungen/weihnachten-in-duesseldorf/faq",
         "abgerufen_am": "2026-11-17"},
        {"titel": "Stiftung Schloss und Park Benrath: Weihnachtsmarkt",
         "url": "https://www.schloss-benrath.de/weihnachtsmarkt", "abgerufen_am": "2026-11-17"},
        {"titel": "Areal Böhler: Weihnachtszauber", "url": "https://areal-boehler.de/weihnachtszauber/",
         "abgerufen_am": "2026-11-17"},
        {"titel": "Visit Düsseldorf: Weihnachtszeit Nordstraße",
         "url": "https://www.visitduesseldorf.de/event/weihnachtszeit-nordstrasse-9312526b20",
         "abgerufen_am": "2026-11-17"},
        {"titel": "DEG Winterwelt: Kö on Ice", "url": "https://deg-winterwelt.de/", "abgerufen_am": "2026-11-17"},
        {"titel": "Visit Düsseldorf: Riesenrad „Wheel of Vision“",
         "url": "https://www.visitduesseldorf.de/attraktionen/riesenrad-wheel-of-vision-7176a064d7",
         "abgerufen_am": "2026-11-17"},
        {"titel": "Maus Event: Kiez Advent – Markt der 1000 Lichter",
         "url": "https://mausevent.de/pages/kiez-advent-markt-der-1000-lichter", "abgerufen_am": "2026-11-19"},
        {"titel": "Stadt Neuss: Neusser Weihnachtsmärkte 2026",
         "url": "https://www.neuss.de/news/2026/11/17/neusser-weihnachtsmaerkte-2026", "abgerufen_am": "2026-11-19"},
        {"titel": "Ratinger Weihnachtsmarkt", "url": "https://weihnachtsmarkt-ratingen.de/", "abgerufen_am": "2026-11-19"},
    ],
    "abschnitte": [
        {
            "ueberschrift": "",
            "text_md": (
                "Düsseldorf hat im Advent nicht den einen Weihnachtsmarkt, sondern viele: Themenmärkte in der "
                "Innenstadt, einen Markt vor einem Schloss, einen zwischen alten Industriehallen und kleine Märkte in "
                "den Vierteln, die ihren ganz eigenen Charakter haben. In unserem "
                f"[Weihnachtsmarkt-Guide]({WM}) haben wir alle gesammelt, dazu die Märkte in Neuss und Ratingen.\n\n"
                "„Am schönsten“ ist natürlich Geschmackssache. Unsere Auswahl folgt deshalb nachvollziehbaren Gründen: "
                "Atmosphäre und Kulisse, ein eigenes Konzept statt Hütte an Hütte, ein Programm, das über Glühwein "
                "hinausgeht, und gute Erreichbarkeit. Darunter findet ihr Tipps für Familien, für Schlittschuhfans, "
                "für ruhigere Abende im Viertel und für einen Abstecher in die Nachbarstädte."
            ),
        },
        {
            "ueberschrift": "Die Innenstadt: viele Märkte, kurze Wege",
            "text_md": (
                "Der Klassiker ist eigentlich eine ganze Reihe von Märkten. Zwischen Altstadt, Kö und Rhein liegen "
                "mehrere Themenmärkte so nah beieinander, dass ihr sie an einem Abend zu Fuß verbinden könnt.\n\n"
                "- **Altstadt-Markt:** Die Hütten zwischen Marktstraße und Flinger Straße sind alten Düsseldorfer "
                "Bürgerhäusern nachempfunden und fügen sich in die Häuserzeilen ein. Hier gibt es Kunsthandwerk, "
                "Geschenkideen und weihnachtliche Spezialitäten – das klassische Weihnachtsmarkt-Gefühl.\n"
                "- **Märchen-Markt am Schadowplatz:** Eine Künstlerin hat die Schattenrisse auf den Hütten gestaltet, "
                "sie erzählen bekannte deutsche Märchen neu, manche Figuren bewegen sich im Lichtspiel. Tausende LEDs "
                "lassen den Platz vor dem Kö-Bogen am Abend leuchten, und der Markt zieht sich weiter in die "
                "Schadowstraße.\n"
                "- **The Winter Village:** Auf der Königsallee zwischen Corneliusplatz und Girardetbrücke entsteht ein "
                "Winterdorf aus weißen Glascontainern. Marken, Manufakturen und Kreative zeigen dort ihre Produkte in "
                "Pop-up-Läden, dazu kommt gehobene Gastronomie.\n"
                "- **Weihnachtspromenade am Rhein:** Gemeinsam mit dem Circus-Theater Roncalli wird die "
                "Rheinuferpromenade zwischen Burgplatz und Altem Hafen zum Weihnachtsmarkt – mit nostalgischen "
                "Verkaufswagen, gläsernen Pavillons im Stil alter Orangerien und Pop-up-Restaurants mit Blick aufs "
                "Wasser. In Düsseldorf und Umgebung gibt es kein vergleichbares Konzept.\n\n"
                "Am nördlichen Ende der Promenade dreht sich auf dem Burgplatz das Riesenrad „Wheel of Vision“. Mit "
                "55 Metern Höhe bietet es einen weiten Blick über Altstadt, Rhein und die beleuchteten Märkte; die "
                "geschlossenen Gondeln sind beheizbar. Am bequemsten kommt ihr mit der Bahn zur Haltestelle "
                "Heinrich-Heine-Allee, sie liegt mitten im Geschehen. Am Totensonntag und am ersten Weihnachtstag "
                "bleiben die Innenstadt-Märkte geschlossen.\n\n"
                "{{ort:duesseldorfer-weihnachtsmarkt-in-der-innenstadt-altstadt}}\n\n"
                "{{ort:maerchen-markt-stadtmitte}}\n\n"
                "{{ort:weihnachtspromenade-am-rhein-altstadt}}"
            ),
        },
        {
            "ueberschrift": "Schloss Benrath: Kunsthandwerk vor großer Kulisse",
            "text_md": (
                "Ein Weihnachtsmarkt vor einem Schloss – das gibt es in Düsseldorf nur in Benrath. An den "
                "Adventswochenenden stehen auf dem Schlossvorplatz Holzhütten mit ausgefallenem Kunsthandwerk, das "
                "sich gut als Geschenk eignet, dazu warme Getränke und Essen. Geöffnet ist jeweils von Freitag bis "
                "Sonntag.\n\n"
                "Für Kinder fährt die traditionelle Eisenbahn, und im Schloss selbst gibt es Sonderführungen und "
                "Konzerte – eine gute Gelegenheit, das Gebäude auch von innen zu sehen. Anreise: Die U72 hält direkt "
                "an der Haltestelle Schloss Benrath und fährt an Markttagen öfter, alternativ sind es vom S-Bahnhof "
                "Benrath etwa zehn Minuten zu Fuß.\n\n"
                "{{ort:weihnachtsmarkt-schloss-benrath}}"
            ),
        },
        {
            "ueberschrift": "Areal Böhler: Weihnachten mit Industriecharme",
            "text_md": (
                "Beim Weihnachtszauber im Böhler Park in Heerdt stehen die Hütten zwischen den historischen "
                "Industriehallen des Areal Böhler. Die Marktfläche ist größer geworden und hat mehr Plätze zum "
                "Verweilen. Der Markt hat von Dienstag bis Sonntag geöffnet, unter der Woche erst am Nachmittag.\n\n"
                "Was ihn besonders macht, ist das Programm: An allen Markttagen gibt es Live-Musik auf der Bühne, "
                "unter anderem mit dem New Life Gospelchor und der Böhler Werkskapelle, dazu Mitsingkonzerte und "
                "Open-Mic-Abende. Für Kinder gibt es Kinderschminken, Mitmachaktionen und die Puppenbühne Maatz, und "
                "auch der Weihnachtsmann schaut vorbei.\n\n"
                "{{ort:weihnachtszauber-areal-boehler-heerdt}}"
            ),
        },
        {
            "ueberschrift": "Nordstraße: Advent im Viertel",
            "text_md": (
                "Wer es nachbarschaftlicher mag, ist auf der Nordstraße in Pempelfort richtig. Die Werbegemeinschaft "
                "nördliche Innenstadt stellt Buden mit Punsch, Glühwein, gebrannten Mandeln und handgemachten Mutzen "
                "auf die Einkaufsstraße. Jeder Montag ist Kids-Day mit Kasperletheater und vergünstigtem "
                "Kinderkarussell, und die Adventssonntage haben eigene Themen – vom Glücksrad für Kinder bis zum "
                "Familientag.\n\n"
                "{{ort:weihnachtszeit-nordstrasse-pempelfort}}"
            ),
        },
        {
            "ueberschrift": "Mit Kindern",
            "text_md": (
                "Fast jeder Markt hat etwas für Kinder, manche haben aber deutlich mehr:\n\n"
                "- **Weihnachtsmarkt Gerresheim:** Auf dem Gerricusplatz gibt es an zwei Adventswochenenden eine rund "
                "20 Meter lange Rodelbahn, ein Puppentheater und Eisstockschießen für Groß und Klein.\n"
                "- **Areal Böhler:** Puppenbühne Maatz, Kinderschminken und Mitmachaktionen.\n"
                "- **Schloss Benrath:** die traditionelle Eisenbahn für Kinder.\n"
                "- **Nordstraße:** montags Kasperletheater und Kinderkarussell.\n"
                "- **Ratinger Weihnachtsmarkt:** ein Karussell mit Helikopter, Rennauto und Motorrad und bis zum "
                "vierten Advent der Kasperl auf der Marktbühne.\n\n"
                "Im Guide könnt ihr die Märkte auch nach Merkmalen wie Karussell oder Puppenbühne "
                "filtern.\n\n"
                "{{ort:weihnachtsmarkt-gerresheim}}"
            ),
        },
        {
            "ueberschrift": "Zum Schlittschuhlaufen",
            "text_md": (
                "Kö on Ice, die Eisbahn der DEG Winterwelt an der Königsallee, läuft länger als die Märkte – bis in "
                "den Januar hinein. Gelaufen wird auf echtem Eis, Schlittschuhe könnt ihr vor Ort leihen. Daneben "
                "gibt es Bahnen fürs Eisstockschießen, die ihr vorab bucht, und die Füchschen-Alm mit Essen und Altbier. "
                "Vom Corneliusplatz aus geht es direkt weiter ins Winter Village.\n\n"
                "{{ort:koe-on-ice-deg-winterwelt-stadtmitte}}"
            ),
        },
        {
            "ueberschrift": "Abseits vom Trubel",
            "text_md": (
                "Der Kiez Advent – Markt der 1000 Lichter auf dem Münsterplatz in Derendorf setzt auf stimmungsvolle "
                "Beleuchtung und winterliche Speisen. Neu ist eine beheizte Ski-Gondel, die ihr für kleine Gruppen "
                "reservieren könnt. Das Benrather Weihnachtsdörfchen auf der Hauptstraße begleitet den Markt mit einem "
                "Bühnenprogramm, und vor den Düsseldorf Arcaden in Bilk laden ein paar Weihnachtsstände zur Pause beim "
                "Einkaufen auf der Friedrichstraße ein – auch sonntags.\n\n"
                "{{ort:kiez-advent-markt-der-1000-lichter-derendorf}}"
            ),
        },
        {
            "ueberschrift": "Ein Abstecher nach Neuss und Ratingen",
            "text_md": (
                "In Neuss steht der Weihnachtsmarkt auf dem Münsterplatz direkt am Quirinusmünster. Blickfang ist eine "
                "rund 15 Meter hohe Glühwein-Pyramide, dazu kommt ein Bühnenprogramm. Wer nach Weihnachten noch "
                "Marktstimmung sucht: Der Advent am Konvent in der Neusser Innenstadt hat eine besonders lange Saison "
                "und läuft bis nach Neujahr.\n\n"
                "Der Ratinger Weihnachtsmarkt auf dem Marktplatz punktet mit Familienprogramm und einer neuen "
                "Feuerzangen-Scheune. An den Ständen reicht das Angebot von Reibekuchen und Grünkohl bis zu Crêpes "
                "und Dampfnudeln.\n\n"
                "{{ort:neusser-weihnachtsmarkt-neuss}}\n\n"
                "{{ort:ratinger-weihnachtsmarkt-ratingen}}"
            ),
        },
        {
            "ueberschrift": "So plant ihr euren Besuch",
            "text_md": (
                "Die Öffnungszeiten unterscheiden sich von Markt zu Markt, manche öffnen nur an den Wochenenden, "
                "andere erst am Nachmittag. An Totensonntag, Heiligabend und den Feiertagen gelten oft Sonderzeiten. "
                "Unser Guide zeigt deshalb für jeden Tag, welche Märkte geöffnet haben – mit Karte, Filtern und allen "
                "Sonderzeiten.\n\n"
                "{{guide:weihnachtsmaerkte}}"
            ),
        },
    ],
    "faq": [
        {"frage": "Welche Weihnachtsmärkte in Düsseldorf liegen nah beieinander?",
         "antwort": "Altstadt-Markt, Märchen-Markt am Schadowplatz, The Winter Village auf der Kö und die "
                    "Weihnachtspromenade am Rhein liegen in der Innenstadt und sind zu Fuß verbunden. Dazu kommen das "
                    "Riesenrad auf dem Burgplatz und die Eisbahn Kö on Ice."},
        {"frage": "Welche Weihnachtsmärkte eignen sich für Kinder?",
         "antwort": "Besonders viel Programm haben Gerresheim mit Rodelbahn und Puppentheater, das Areal Böhler mit "
                    "Puppenbühne und Mitmachaktionen, Schloss Benrath mit der Kindereisenbahn und die Nordstraße mit "
                    "ihrem Kids-Day am Montag."},
        {"frage": "Wie komme ich zum Weihnachtsmarkt an Schloss Benrath?",
         "antwort": "Am einfachsten mit der U72 bis zur Haltestelle Schloss Benrath, die an Markttagen öfter fährt. "
                    "Vom S-Bahnhof Benrath sind es etwa zehn Minuten zu Fuß."},
    ],
}

BEITRAEGE = [LAUNCH, WEIHNACHTSMAERKTE]
