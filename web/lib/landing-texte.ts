// Feste Texte der Kategorie- und Stadtteilseiten (SEO-/GEO-Plan Nov. 2026, Maßnahme 5).
// Von Hand gepflegt, nicht pro Request generiert. Vor dem Deploy gegenlesen und freigeben.
// Regel: Der erste Satz nennt etwas, das sich unterscheidet – keine Schablone mit ausgetauschtem Namen.
// Zahlen (Events, Orte) kommen live aus dem Pool und stehen NICHT hier.

/** Kategorieseiten /kategorie/{slug}: zwei bis drei Sätze */
export const KATEGORIE_TEXTE: Record<string, string[]> = {
  kultur: [
    "Theater, Oper, Ausstellungen, Film und Lesungen: Der Kulturkalender reicht vom Schauspielhaus und der Deutschen Oper am Rhein über Kunstpalast, K20 und K21 bis zu kleinen Bühnen und dem Filmmuseum.",
    "Wir sammeln die Termine täglich aus den Spielplänen der Häuser und aus Veranstaltungsportalen.",
  ],
  musik: [
    "Konzerte vom Clubgig bis zur Arena – in der Tonhalle, im zakk, im Pitcher, in der Jazz-Schmiede, in der Mitsubishi Electric Halle und im PSD Bank Dome.",
    "Klassik, Jazz, Rock, Hip-Hop oder elektronisch: Über die Musikrichtung lässt sich die Liste eingrenzen.",
  ],
  food: [
    "Märkte, Tastings, Themen-Dinner und Kochkurse in Düsseldorf.",
    "Restaurants und Cafés zum Hingehen ohne festen Termin stehen im Guide „Restaurants & Cafés“.",
  ],
  sport: [
    "Fortuna in der Merkur Spiel-Arena, die DEG im PSD Bank Dome, Läufe am Rhein und Sport zum Mitmachen.",
    "Heimspiele, Lauftreffs und Fitness-Angebote stehen hier mit Datum und Uhrzeit.",
  ],
  outdoor: [
    "Draußen in Düsseldorf: Parks, Natur, Touren und Veranstaltungen unter freiem Himmel.",
    "Im Winter ist das Angebot klein, ab dem Frühjahr wächst es deutlich.",
  ],
  stadtfuehrung: [
    "Stadt-, Viertel- und Themenführungen, kulinarische Touren und Kneipentouren durch die Altstadt.",
    "Viele Touren haben feste Treffpunkte und brauchen eine Anmeldung beim Anbieter.",
  ],
  community: [
    "Meetups, Sprachcafés, Workshops und Vorträge – viele davon in den Stadtbüchereien und bei Meetup-Gruppen.",
    "Gut, um Leute kennenzulernen oder etwas Neues auszuprobieren; vieles ist kostenlos.",
  ],
  nightlife: [
    "Partys, Clubnächte, Barabende und Karneval in Düsseldorf.",
    "Die Clubs selbst – mit Musikrichtung und Programm – stellt der Club-Guide vor.",
  ],
  familie: [
    "Kindertheater, Kinderkino, Basteln, Vorlesen und Familienfeste in Düsseldorf.",
    "Viele Angebote der Stadtbüchereien sind kostenlos, manche brauchen eine Anmeldung.",
  ],
  dating: [
    "Speed Dating und Singles-Events in Düsseldorf.",
    "Das Angebot ist klein – hier steht alles, was wir finden.",
  ],
};

/**
 * Stadtteilseiten /stadtteil/{slug} und Guide-Stadtteilseiten: ein bis zwei Sätze, was den Stadtteil ausmacht.
 * Schlüssel = Stadtteil wie in der DB („Hafen“, nicht „Medienhafen“). Ohne Eintrag gibt es nur den Bezirks-Satz.
 */
export const STADTTEIL_TEXTE: Record<string, string> = {
  Altstadt: "Die Altstadt zwischen Rheinufer und Heinrich-Heine-Allee ist Düsseldorfs Ausgehviertel mit Brauhäusern, Kneipen und Clubs – und mit Museen wie dem K20 und der Kunsthalle am Grabbeplatz.",
  Carlstadt: "Die Carlstadt südlich der Altstadt: Carlsplatz mit dem Markt, Galerien, das Filmmuseum und ruhigere Straßen am Rand des Zentrums.",
  Stadtmitte: "Stadtmitte rund um Königsallee, Kö-Bogen und Schauspielhaus – mit Einkaufsstraßen, Bühnen und dem japanischen Viertel an der Immermannstraße.",
  Pempelfort: "Pempelfort nördlich der Innenstadt: Am Ehrenhof liegen Tonhalle, Kunstpalast und NRW-Forum, dazu kommen die Nordstraße und viele Restaurants.",
  Derendorf: "Derendorf im Norden der Innenstadt mit dem Campus der Hochschule Düsseldorf, Neubauquartieren und einer wachsenden Gastroszene.",
  Golzheim: "Golzheim am Rhein mit dem Rheinpark, Bürohäusern am Kennedydamm und ruhigen Wohnstraßen.",
  Flingern: "Flingern östlich der Innenstadt: Die Ackerstraße steht für kleine Läden und Cafés, im Süden des Viertels liegt das zakk.",
  "Flingern-Nord": "Flingern-Nord rund um die Ackerstraße mit kleinen Läden, Cafés und Bars.",
  "Flingern-Süd": "Flingern-Süd mit dem zakk als Konzert- und Kulturzentrum und Gewerbehöfen, in denen Ateliers und Clubs Platz finden.",
  Düsseltal: "Düsseltal rund um den Zoopark und den Brehmplatz – ein Wohnviertel mit Cafés und Restaurants zwischen Flingern und Grafenberg.",
  Bilk: "Bilk im Süden der Innenstadt mit der Heinrich-Heine-Universität, den Bilker Arcaden und Kulturorten wie der Jazz-Schmiede.",
  Unterbilk: "Unterbilk zwischen Medienhafen und Bilk: Rund um Lorettostraße und Bilker Allee reihen sich Restaurants, Cafés und kleine Läden.",
  Hafen: "Der Medienhafen am Rhein mit den Gehry-Bauten, Büros, Restaurants und Bars am Wasser, gleich neben dem Rheinturm.",
  Friedrichstadt: "Die Friedrichstadt südlich der Königsallee rund um Graf-Adolf-Straße und Kirchplatz – zentral, dicht bebaut, mit vielen Restaurants.",
  Oberbilk: "Oberbilk östlich des Hauptbahnhofs mit der Mitsubishi Electric Halle und internationaler Küche entlang der Ellerstraße.",
  Oberkassel: "Oberkassel auf der linken Rheinseite mit der Luegallee, den Rheinwiesen und Blick auf die Altstadt.",
  Niederkassel: "Niederkassel links des Rheins mit dem EKŌ-Haus der Japanischen Kultur und viel Grün an den Rheinwiesen.",
  Heerdt: "Heerdt im linksrheinischen Westen der Stadt, zwischen Wohnvierteln und Gewerbe an der Grenze zu Neuss.",
  Lörick: "Lörick links des Rheins mit dem Löricker See und viel Grün im Norden von Oberkassel.",
  Stockum: "Stockum im Norden mit der Messe, der Merkur Spiel-Arena und dem Nordpark samt Aquazoo.",
  Kaiserswerth: "Kaiserswerth im Norden am Rhein mit den Resten der Kaiserpfalz und einem historischen Ortskern.",
  Rath: "Rath im Nordosten mit dem PSD Bank Dome, in dem die DEG spielt und große Konzerte stattfinden.",
  Gerresheim: "Gerresheim im Osten mit der Basilika St. Margareta und einem eigenen, kleinstädtischen Zentrum.",
  Lierenfeld: "Lierenfeld im Osten der Stadt zwischen Oberbilk und Eller, geprägt von Gewerbe und Veranstaltungsorten in alten Hallen.",
  Eller: "Eller im Südosten mit dem Schloss Eller und dem Schlosspark.",
  Benrath: "Benrath im Süden mit dem Schloss Benrath, seinem Park und einem eigenen Ortszentrum.",
  Wersten: "Wersten im Süden der Stadt, ein Wohnviertel am Rand des Südparks.",
  Neuss: "Neuss, die Nachbarstadt auf der linken Rheinseite, mit Innenstadt rund um das Quirinus-Münster.",
  Ratingen: "Ratingen, die Nachbarstadt im Nordosten, mit Altstadt rund um den Marktplatz und dem Blauen See.",
};
