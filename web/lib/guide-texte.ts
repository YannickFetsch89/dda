// Redaktionelle Texte der Guide-Seiten (12.11.2026): kurze Einleitung unter der Überschrift, längerer Text und
// fünf häufige Fragen am Seitenende (FAQPage-JSON-LD). Jede Seite hat einen eigenen Text – keine Bausteine.
//
// Platzhalter in geschweiften Klammern ({anzahl}, {restaurants} …) setzt die Seite mit echten Zahlen ein.
// Links als [Text](/pfad) – nur interne Pfade; das JSON-LD bekommt den reinen Text.
// Fakten nur aus unseren Daten (Küchen, Stadtteile, Genres, Brauhäuser) und allgemein bekanntem Stadtwissen.

export type GuideSeite = "uebersicht" | "restaurants-cafes" | "kneipen-bars" | "clubs";

export interface GuideFrage { frage: string; antwort: string }
export interface GuideAbschnitt { titel: string; absaetze: string[] }
export interface GuideText {
  einleitung: string;
  titel: string; // Überschrift über dem längeren Text
  abschnitte: GuideAbschnitt[];
  faq: GuideFrage[];
}

export const GUIDE_TEXTE: Record<GuideSeite, GuideText> = {
  uebersicht: {
    einleitung:
      "Wo isst man gut, wo trinkt man das beste Alt, wo wird bis zum Morgen getanzt? In unserem Guide stehen " +
      "{restaurants} Restaurants und Cafés, {kneipen} Kneipen und Bars und {clubs} Clubs in Düsseldorf und Umgebung – " +
      "jede Empfehlung mit eigener Seite, Adresse und Karte.",
    titel: "Düsseldorf von morgens bis spät in die Nacht",
    abschnitte: [
      {
        titel: "Essen gehen: von Little Tokyo bis Brauhaus",
        absaetze: [
          "Düsseldorf ist eine Stadt zum Essengehen. Rund um die Immermannstraße liegt eines der größten japanischen " +
            "Viertel Europas, mit Ramen-Bars, Sushi und koreanischen Grills. In Pempelfort, Unterbilk und Flingern reihen " +
            "sich kleine Restaurants und Cafés aneinander, in der Altstadt gibt es rheinische Küche im Brauhaus. Mit den " +
            "Filtern für Küche und Preis kommt ihr schnell vom Mittagssnack zum Abendessen für besondere Anlässe. Alle " +
            "Adressen findet ihr unter [Restaurants & Cafés](/guides/restaurants-cafes).",
        ],
      },
      {
        titel: "Abends: Altbier, Cocktails und Wein",
        absaetze: [
          "Kein Abend in Düsseldorf ohne Alt: In den Hausbrauereien der Altstadt wird es frisch gezapft, der Köbes " +
            "bringt nach, bis ein Deckel auf dem Glas liegt. Wer es ruhiger mag, findet in Pempelfort, Friedrichstadt und " +
            "Derendorf Cocktailbars mit eigener Karte, in der Altstadt auch kleine Weinbars. Unsere Auswahl steht unter " +
            "[Kneipen & Bars](/guides/kneipen-bars).",
        ],
      },
      {
        titel: "Nachts: Clubs von Techno bis Schlager",
        absaetze: [
          "Das Nachtleben reicht vom elektronischen Programm im Salon des Amateurs über Partys in Kulturhäusern wie dem " +
            "zakk bis zu den Clubs der Altstadt, in denen Charts, House und Latin laufen. Unter [Clubs](/guides/clubs) " +
            "seht ihr zu jedem Club Musikrichtung, Partyreihen und das nächste Event aus unserem Kalender.",
        ],
      },
      {
        titel: "Nach Stadtteil stöbern",
        absaetze: [
          "Jeder Guide lässt sich nach Stadtteil filtern; für Viertel mit vielen Empfehlungen gibt es eigene Seiten, " +
            "etwa [Restaurants in Pempelfort](/guides/restaurants-cafes/stadtteil/pempelfort) oder " +
            "[Kneipen und Bars in der Altstadt](/guides/kneipen-bars/stadtteil/altstadt). Was in eurem Viertel gerade " +
            "passiert, zeigen die [Stadtteilseiten](/stadtteile) unseres Eventkalenders.",
        ],
      },
    ],
    faq: [
      {
        frage: "Was finde ich unter „Düsseldorf entdecken“?",
        antwort:
          "Ausgewählte Restaurants, Cafés, Kneipen, Bars und Clubs in Düsseldorf, Neuss und Ratingen. Jeder Ort hat eine " +
          "eigene Seite mit Beschreibung, Adresse, Karte und – wo bekannt – Öffnungszeiten; bei Clubs außerdem Musikrichtung und Partyreihen.",
      },
      {
        frage: "Kann ich die Tipps nach Stadtteil durchsuchen?",
        antwort:
          "Ja. In jedem Guide gibt es einen Stadtteil-Filter, und für Viertel mit vielen Empfehlungen eigene Seiten – zum " +
          "Beispiel [Restaurants in Unterbilk](/guides/restaurants-cafes/stadtteil/unterbilk), " +
          "[Kneipen und Bars in Flingern](/guides/kneipen-bars/stadtteil/flingern) oder " +
          "[Clubs in der Altstadt](/guides/clubs/stadtteil/altstadt).",
      },
      {
        frage: "Sind auch Neuss und Ratingen dabei?",
        antwort:
          "Ja, vor allem bei Restaurants und Cafés. Dazu kommen einige Bars und Clubs in Neuss. Im Stadtteil-Filter " +
          "stehen Neuss und Ratingen neben den Düsseldorfer Vierteln.",
      },
      {
        frage: "Wo finde ich Events zu den Orten?",
        antwort:
          "Club-Seiten zeigen die nächsten Events direkt aus unserem Kalender. Alles, was in der Stadt los ist, steht im " +
          "Eventkalender – zum Beispiel für [heute](/heute) oder [das Wochenende](/wochenende).",
      },
      {
        frage: "Welche Guides kommen noch dazu?",
        antwort:
          "In Arbeit sind Guides für Spielplätze, Ausflüge in der Umgebung und Wochenend-Trips. Bis dahin findet ihr " +
          "Ideen für Familien und Ausflüge in unserem [Eventkalender](/entdecken).",
      },
    ],
  },

  "restaurants-cafes": {
    einleitung:
      "Von Ramen in Little Tokyo bis zum Sauerbraten im Brauhaus: Hier stehen {anzahl} Restaurants, Cafés und Imbisse " +
      "in Düsseldorf, Neuss und Ratingen, die uns überzeugt haben. Filtert nach Küche, Stadtteil und Preis – oder lasst " +
      "euch über „dies.das empfiehlt dir was“ einen Tipp geben.",
    titel: "Essen gehen in Düsseldorf",
    abschnitte: [
      {
        titel: "Little Tokyo und die Küchen der Welt",
        absaetze: [
          "Düsseldorf hat eine der größten japanischen Gemeinden Europas, und das schmeckt man: Rund um die " +
            "Immermannstraße in [Stadtmitte](/guides/restaurants-cafes/stadtteil/stadtmitte) liegen Ramen-Bars, " +
            "Sushi-Restaurants, japanische Cafés und koreanische Grills dicht beieinander. Vor den bekanntesten " +
            "Nudelküchen bilden sich zur Essenszeit oft Schlangen – wer früh kommt, wartet kürzer.",
          "Am häufigsten in unserem Guide ist trotzdem die italienische Küche, gefolgt von deutschen, türkischen und " +
            "griechischen Restaurants. Dazu kommen vietnamesische, indische, persische und chinesische Adressen bis hin " +
            "zum Hotpot – mit dem Küchen-Filter findet ihr schnell die passende Richtung.",
        ],
      },
      {
        titel: "Rheinisch essen: Halve Hahn, Sauerbraten, Senf",
        absaetze: [
          "Wer Düsseldorf schmecken will, geht ins Brauhaus. Dort gibt es zum Alt die Klassiker der rheinischen Küche: " +
            "den Halve Hahn – ein Roggenbrötchen mit mittelaltem Gouda, Zwiebeln und Senf –, Rheinischen Sauerbraten, " +
            "Himmel un Ääd mit Blutwurst und im Winter Reibekuchen. Der scharfe Düsseldorfer Senf gehört fast immer dazu.",
          "Die Brauhäuser aus unserem [Kneipen-Guide](/guides/kneipen-bars) stehen deshalb auch hier – etwa die " +
            "[Brauerei Schumacher](/guides/kneipen-bars/brauerei-schumacher-stadtmitte) an der Oststraße oder das " +
            "[Füchschen](/guides/kneipen-bars/brauerei-im-fuechschen-altstadt) in der Altstadt.",
        ],
      },
      {
        titel: "Die besten Viertel zum Essengehen",
        absaetze: [
          "Besonders viele Empfehlungen liegen in [Pempelfort](/guides/restaurants-cafes/stadtteil/pempelfort) rund " +
            "um die Nordstraße, in [Unterbilk](/guides/restaurants-cafes/stadtteil/unterbilk) zwischen Lorettostraße und " +
            "Medienhafen und in [Flingern](/guides/restaurants-cafes/stadtteil/flingern), wo sich an der Ackerstraße " +
            "kleine Restaurants und Cafés aneinanderreihen. Linksrheinisch lohnt sich " +
            "[Oberkassel](/guides/restaurants-cafes/stadtteil/oberkassel), in der " +
            "[Altstadt](/guides/restaurants-cafes/stadtteil/altstadt) mischen sich Brauhäuser mit internationaler Küche.",
        ],
      },
      {
        titel: "Cafés, Frühstück und Kuchen",
        absaetze: [
          "Über hundert Cafés gehören zum Guide – vom Spezialitäten-Kaffee über Brunch-Lokale bis zur Konditorei. Wählt " +
            "oben den Reiter „Cafés“, um nur sie zu sehen, und kombiniert das mit eurem Stadtteil. Die Karte zeigt auf " +
            "einen Blick, was in der Nähe liegt.",
        ],
      },
    ],
    faq: [
      {
        frage: "Wo isst man in Düsseldorf am besten japanisch?",
        antwort:
          "Rund um die Immermannstraße in Stadtmitte, Düsseldorfs japanischem Viertel. Dort liegen Ramen-Bars, Sushi und " +
          "japanische Cafés nah beieinander. Unsere Auswahl für das Viertel steht unter " +
          "[Restaurants in Stadtmitte](/guides/restaurants-cafes/stadtteil/stadtmitte).",
      },
      {
        frage: "Welche Stadtteile eignen sich besonders zum Essengehen?",
        antwort:
          "Pempelfort, Unterbilk, Stadtmitte, Flingern und die Altstadt haben die meisten Empfehlungen. Für jeden dieser " +
          "Stadtteile gibt es eine eigene Seite, zum Beispiel " +
          "[Restaurants in Flingern](/guides/restaurants-cafes/stadtteil/flingern).",
      },
      {
        frage: "Was ist typisch Düsseldorfer Essen?",
        antwort:
          "Rheinische Brauhausküche: Halve Hahn, Rheinischer Sauerbraten, Himmel un Ääd und Reibekuchen, dazu " +
          "Düsseldorfer Senf und ein frisch gezapftes Alt. Am besten in einer Hausbrauerei wie dem " +
          "[Uerige](/guides/kneipen-bars/uerige-obergaerige-hausbrauerei-altstadt) in der Altstadt.",
      },
      {
        frage: "Wo kann man in Düsseldorf gut frühstücken oder brunchen?",
        antwort:
          "In vielen der Cafés aus diesem Guide – besonders in Pempelfort, Unterbilk und Flingern. Wählt den Reiter „Cafés“ und " +
          "euren Stadtteil; auf jeder Detailseite stehen die Öffnungszeiten.",
      },
      {
        frage: "Gibt es auch günstige Restaurants?",
        antwort:
          "Ja. Viele Empfehlungen liegen bei 10 bis 20 Euro pro Person, Imbisse und Cafés oft darunter. Mit dem " +
          "Preisfilter zeigt die Liste nur Orte in eurer Preisklasse.",
      },
    ],
  },

  "kneipen-bars": {
    einleitung:
      "Altbier frisch vom Fass, Cocktails in versteckten Bars und Eckkneipen mit Stammtisch-Charme: {anzahl} Kneipen, " +
      "Bars und Brauhäuser in Düsseldorf, die einen Abend lohnen. Die meisten liegen in der Altstadt – aber auch " +
      "Flingern, Pempelfort und Friedrichstadt haben starke Adressen.",
    titel: "Ausgehen in Düsseldorf",
    abschnitte: [
      {
        titel: "Altbier und Hausbrauereien",
        absaetze: [
          "Alt ist ein dunkles, obergäriges Bier und Düsseldorfs Stolz. In den Hausbrauereien wird es noch vor Ort gebraut " +
            "und frisch gezapft: im [Uerige](/guides/kneipen-bars/uerige-obergaerige-hausbrauerei-altstadt) " +
            "an der Berger Straße, im [Füchschen](/guides/kneipen-bars/brauerei-im-fuechschen-altstadt) an der Ratinger " +
            "Straße, im [Schlüssel](/guides/kneipen-bars/hausbrauerei-zum-schluessel-altstadt) an der Bolkerstraße und bei " +
            "[Kürzer](/guides/kneipen-bars/brauerei-kuerzer-altstadt) in der Kurzen Straße. Außerhalb der Altstadt zapft die " +
            "[Brauerei Schumacher](/guides/kneipen-bars/brauerei-schumacher-stadtmitte) an der Oststraße.",
          "Serviert wird vom Köbes, dem Brauhaus-Kellner. Er bringt ungefragt ein neues Glas, sobald das alte leer " +
            "ist, und macht einen Strich auf den Bierdeckel. Wer genug hat, legt den Deckel aufs Glas.",
        ],
      },
      {
        titel: "Die Altstadt – die „längste Theke der Welt“",
        absaetze: [
          "Auf engem Raum zwischen Rhein und Heinrich-Heine-Allee liegen so viele Kneipen, Bars und " +
            "Brauhäuser, dass die Altstadt ihren Spitznamen zu Recht trägt. Neben den Brauhäusern gibt es Craft Beer in der " +
            "[Holy Craft Beer Bar](/guides/kneipen-bars/holy-craft-beer-bar-altstadt), Wein in der " +
            "[Galerie am Karlplatz](/guides/kneipen-bars/weinlokal-galerie-am-karlplatz-altstadt) und den Düsseldorfer " +
            "Kräuterlikör Killepitsch im [Kabüffke](/guides/kneipen-bars/et-kabueffke-killepitschstube-altstadt). Alle " +
            "Adressen im Viertel stehen unter [Kneipen und Bars in der Altstadt](/guides/kneipen-bars/stadtteil/altstadt).",
        ],
      },
      {
        titel: "Cocktailbars abseits der Altstadt",
        absaetze: [
          "Cocktails sind die häufigste Spezialität in unserem Guide – und die besten Bars liegen oft ein Stück weg vom " +
            "Trubel: die [squarebar](/guides/kneipen-bars/squarebar-derendorf) in Derendorf, " +
            "[Petit Punch](/guides/kneipen-bars/petit-punch-pempelfort) in Pempelfort oder " +
            "[Boothby's Bar](/guides/kneipen-bars/boothby-s-bar-friedrichstadt) und die " +
            "[Hideaway Bar](/guides/kneipen-bars/cocktail-bar-hideaway-friedrichstadt) in Friedrichstadt. In " +
            "[Flingern](/guides/kneipen-bars/stadtteil/flingern) mischen sich kleine Bars mit Kneipen – und die Brauerei " +
            "Kürzer hat dort einen zweiten Ausschank.",
        ],
      },
    ],
    faq: [
      {
        frage: "Was ist Altbier und wo trinkt man es am besten?",
        antwort:
          "Alt ist ein dunkles, obergäriges Bier aus Düsseldorf. Am besten schmeckt es frisch in einer Hausbrauerei – etwa " +
          "im [Uerige](/guides/kneipen-bars/uerige-obergaerige-hausbrauerei-altstadt), im " +
          "[Füchschen](/guides/kneipen-bars/brauerei-im-fuechschen-altstadt) oder bei " +
          "[Schumacher](/guides/kneipen-bars/brauerei-schumacher-stadtmitte).",
      },
      {
        frage: "Wie funktioniert das Bestellen im Brauhaus?",
        antwort:
          "Gar nicht – der Köbes bringt von selbst ein neues Alt, sobald euer Glas leer ist, und notiert es mit einem " +
          "Strich auf dem Bierdeckel. Wer nichts mehr möchte, legt den Deckel auf das Glas.",
      },
      {
        frage: "Warum heißt die Düsseldorfer Altstadt „längste Theke der Welt“?",
        antwort:
          "Weil sich auf wenigen Straßen zwischen Rhein und Heinrich-Heine-Allee Kneipe an Kneipe reiht – so dicht, dass " +
          "die Theken wie eine einzige wirken. Unsere Auswahl steht unter " +
          "[Kneipen und Bars in der Altstadt](/guides/kneipen-bars/stadtteil/altstadt).",
      },
      {
        frage: "Wo gibt es gute Cocktailbars in Düsseldorf?",
        antwort:
          "Viele der besten liegen außerhalb der Altstadt, zum Beispiel die " +
          "[squarebar](/guides/kneipen-bars/squarebar-derendorf) in Derendorf, " +
          "[Petit Punch](/guides/kneipen-bars/petit-punch-pempelfort) in Pempelfort und " +
          "[Boothby's Bar](/guides/kneipen-bars/boothby-s-bar-friedrichstadt) in Friedrichstadt. Im Filter „Spezialität“ " +
          "zeigt „Cocktails“ alle Bars mit Cocktailkarte.",
      },
      {
        frage: "Wo kann man in Düsseldorf draußen sitzen?",
        antwort:
          "Viele Kneipen und Bars haben Plätze im Freien – der Filter „Draußen sitzen“ zeigt sie. Ein Klassiker im Grünen " +
          "ist der [Biergarten Stoffeln](/guides/kneipen-bars/biergarten-stoffeln-duesseldorf-bilk) in Bilk.",
      },
    ],
  },

  clubs: {
    einleitung:
      "Elektronische Nächte im Salon des Amateurs, Punk-Geschichte im Ratinger Hof, große Partys im Stahlwerk: Hier " +
      "stehen {anzahl} Clubs, Kulturhäuser und Partylocations in Düsseldorf und Neuss – mit Musikrichtung, Partyreihen " +
      "und dem nächsten Event aus unserem Kalender. Filtert nach Musikrichtung, Stadtteil oder Empfehlung – als Liste " +
      "oder auf der Karte.",
    titel: "Feiern in Düsseldorf",
    abschnitte: [
      {
        titel: "Altstadt: viele Clubs auf kurzen Wegen",
        absaetze: [
          "Fast die Hälfte der Clubs liegt in der Altstadt, oft nur ein paar Schritte voneinander entfernt. Die meisten " +
            "spielen Charts, House und Hip-Hop. Latin, Salsa und Reggaeton sind das Programm im " +
            "[Rio Arriba](/guides/clubs/rio-arriba-altstadt), das auch Tanzkurse anbietet; am Rheinufer lädt das " +
            "[The Eight](/guides/clubs/the-eight) zu elektronischen Sunset-Abenden. Ganz anders der [Salon des Amateurs](/guides/clubs/salon-des-amateurs-altstadt) am Grabbeplatz: ein kleiner " +
            "Club im Gebäude der Kunsthalle mit elektronischer und experimenteller Musik. Alle Clubs des Viertels stehen unter " +
            "[Clubs in der Altstadt](/guides/clubs/stadtteil/altstadt).",
        ],
      },
      {
        titel: "Techno und elektronische Musik",
        absaetze: [
          "Wer Techno sucht, wird im [Kulturschlachthof R25](/guides/clubs/kulturschlachthof-r25) an der Rather Straße " +
            "fündig, in der [Giselle Bar](/guides/clubs/giselle-bar-stadtmitte) mit Techno und House und im " +
            "[Ampere](/guides/clubs/ampere-flingern), wo auch Drum & Bass läuft. Die " +
            "[Schleuse Zwei](/guides/clubs/schleuse-zwei-s2-hafen) an der Aachener Straße setzt auf elektronische und " +
            "experimentelle Abende, mal mit House, mal mit Hip-Hop. Mit der Musikrichtung „Techno“ oder " +
            "„Elektro/Experimental“ im Filter seht ihr alle Adressen auf einen Blick.",
        ],
      },
      {
        titel: "Kulturhäuser, Rock und große Hallen",
        absaetze: [
          "Ein Teil des Düsseldorfer Nachtlebens spielt in Kulturhäusern: Das [zakk](/guides/clubs/zakk-flingern) an der " +
            "Fichtenstraße mischt Konzerte, Lesungen und Partys, der [Ratinger Hof](/guides/clubs/ratinger-hof-duesseldorf-altstadt) " +
            "war Ende der 1970er-Jahre Treffpunkt der Punk- und New-Wave-Szene und steht bis heute für Rock und Indie. " +
            "Härter wird es im [Pitcher](/guides/kneipen-bars/pitcher-flingern) mit Rock und Metal. Große Partynächte gibt " +
            "es im [Stahlwerk](/guides/clubs/stahlwerk-duesseldorf-lierenfeld) an der Ronsdorfer Straße – mit Hits der " +
            "80er, 90er und 2000er und einer eigenen Ü30-Hip-Hop-Party – und im [Tor 3](/guides/clubs/tor-3-flingern) " +
            "mit elektronischen und gemischten Abenden.",
        ],
      },
      {
        titel: "Auf der anderen Rheinseite: Neuss",
        absaetze: [
          "Auch in Neuss wird gefeiert, und die Nachbarstadt ist mit S-Bahn und Straßenbahn schnell erreicht. Der " +
            "[Revolution Nachtpalast](/guides/clubs/revolution-nachtpalast-neuss) mischt R&B und Latin mit Mottopartys wie " +
            "einer Abba-Nacht; " +
            "dazu kommen weitere Clubs, die ihr über den Stadtteil-Filter „Neuss“ findet.",
        ],
      },
    ],
    faq: [
      {
        frage: "Wo kann man in Düsseldorf am besten feiern gehen?",
        antwort:
          "Die meisten Clubs liegen in der Altstadt, wo man zu Fuß von einem zum nächsten kommt. Größere Partys gibt es " +
          "im [Stahlwerk](/guides/clubs/stahlwerk-duesseldorf-lierenfeld) und im [Tor 3](/guides/clubs/tor-3-flingern), " +
          "alternative Abende im [zakk](/guides/clubs/zakk-flingern) und im " +
          "[Salon des Amateurs](/guides/clubs/salon-des-amateurs-altstadt).",
      },
      {
        frage: "Welche Clubs in Düsseldorf spielen Techno?",
        antwort:
          "Techno ist das Hauptprogramm im [Kulturschlachthof R25](/guides/clubs/kulturschlachthof-r25), im " +
          "[Salon des Amateurs](/guides/clubs/salon-des-amateurs-altstadt), in der " +
          "[Giselle Bar](/guides/clubs/giselle-bar-stadtmitte) und im [Ampere](/guides/clubs/ampere-flingern). Die " +
          "Musikrichtung „Techno“ im Filter zeigt alle Clubs, in denen er regelmäßig läuft.",
      },
      {
        frage: "Wo gibt es Hip-Hop und R&B?",
        antwort:
          "R&B und House sind das Hauptprogramm der [Nachtresidenz](/guides/clubs/nachtresidenz-duesseldorf-pempelfort). " +
          "Hip-Hop läuft oft als Teil gemischter Abende, etwa im [Tor 3](/guides/clubs/tor-3-flingern) oder im " +
          "[Ampere](/guides/clubs/ampere-flingern); das [Stahlwerk](/guides/clubs/stahlwerk-duesseldorf-lierenfeld) hat " +
          "eine eigene Ü30-Hip-Hop-Party. Die Musikrichtungen „Hip-Hop“ und „R&B“ im Filter zeigen alle Clubs.",
      },
      {
        frage: "Wo tanzt man in Düsseldorf Latin und Reggaeton?",
        antwort:
          "Vor allem im [Rio Arriba](/guides/clubs/rio-arriba-altstadt) in der Altstadt – dort gibt es auch Tanzkurse für " +
          "Salsa und Bachata. Latin-Nächte stehen außerdem in der " +
          "[Nachtresidenz](/guides/clubs/nachtresidenz-duesseldorf-pempelfort) und im " +
          "[Revolution Nachtpalast](/guides/clubs/revolution-nachtpalast-neuss) in Neuss auf dem Programm.",
      },
      {
        frage: "Wie finde ich heute Abend eine Party?",
        antwort:
          "Auf jeder Club-Karte steht das nächste Event aus unserem Kalender. Alle Partys und Konzerte der nächsten Tage " +
          "findet ihr unter [Nightlife](/kategorie/nightlife) und für den Abend unter [heute](/heute).",
      },
    ],
  },
};

/** Platzhalter {name} durch Zahlen ersetzen (unbekannte bleiben stehen – fällt im Test auf). */
export function textFuellen(text: string, werte: Record<string, string>): string {
  return text.replace(/\{(\w+)\}/g, (ganz, name: string) => werte[name] ?? ganz);
}

/** Link-Muster [Text](/pfad) – nur interne Pfade. */
export const LINK_MUSTER = /\[([^\]]+)\]\((\/[^)\s]*)\)/g;

/** Reiner Text ohne Link-Markup (für JSON-LD und Meta). */
export const ohneLinks = (text: string) => text.replace(LINK_MUSTER, "$1");

/** Alle Link-Ziele einer Seite (für Tests). */
export function linkZiele(t: GuideText): string[] {
  const texte = [t.einleitung, ...t.abschnitte.flatMap((a) => a.absaetze), ...t.faq.map((f) => f.antwort)];
  return texte.flatMap((x) => [...x.matchAll(LINK_MUSTER)].map((m) => m[2]));
}

/** FAQPage-JSON-LD (schema.org) aus den Fragen einer Seite. */
export function faqJsonLd(faq: GuideFrage[]): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faq.map((f) => ({
      "@type": "Question",
      name: f.frage,
      acceptedAnswer: { "@type": "Answer", text: ohneLinks(f.antwort) },
    })),
  };
}
