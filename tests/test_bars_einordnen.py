"""Tests für die Einordnung von Kneipen & Bars (python -m unittest tests.test_bars_einordnen)."""
import unittest

from scraper.orte.bars_einordnen import belegt, happy_hour_belegt, raucher_belegt, regeln, stichwort_passt, zusammenfuehren

ORT = {
    "name": "Zum Test",
    "stadtteil": "Altstadt",
    "extras": {
        "google_primaertyp": "pub",
        "google_zusammenfassung": "Urige Kneipe mit Biergarten am Rhein.",
        "google_ausstattung": {"outdoorSeating": True},
        "google_bar": {"goodForWatchingSports": True},
        "google_bewertungen": [
            {"text": "Jeden Freitag Happy Hour von 17 bis 19 Uhr, Cocktails zum halben Preis!"},
            {"text": "Sehr gemütlich, tolle Whisky-Auswahl hinter der Theke."},
        ],
    },
}


class BelegTest(unittest.TestCase):
    def test_wortlich_vorhanden(self):
        self.assertTrue(belegt("Sehr gemütlich, tolle Whisky-Auswahl", "x Sehr  gemütlich,  tolle Whisky–Auswahl y"))

    def test_umformuliert_oder_zu_kurz(self):
        self.assertFalse(belegt("tolle Auswahl an Whisky", "Sehr gemütlich, tolle Whisky-Auswahl"))
        self.assertFalse(belegt("Whisky", "Whisky"))
        self.assertFalse(belegt("", "Text"))


class RegelnTest(unittest.TestCase):
    def test_google_signale(self):
        spez, vibes = regeln(ORT)
        self.assertEqual(spez, set())
        self.assertEqual(vibes, {"Draußen sitzen", "Sportsbar"})

    def test_terrasse_ist_kein_raucherbereich(self):
        extras, _, _ = zusammenfuehren(ORT, None)
        self.assertNotIn("raucher", extras)

    def test_brauhaus_regel_vor_ki(self):
        extras, _, _ = zusammenfuehren({**ORT, "name": "Uerige Obergärige Hausbrauerei"}, {
            "unterart": "bar", "merkmale": [], "happy_hour_zeit": "", "happy_hour_zitat": "", "raucher": "unbekannt",
            "raucher_zitat": "", "beschreibung": "", "highlight": ""})
        self.assertEqual(extras["unterart"], "brauhaus")

    def test_hausbrauerei_altbier(self):
        spez, _ = regeln({**ORT, "name": "Brauerei Schumacher"})
        self.assertIn("Altbier", spez)
        self.assertIn("Altbier", regeln({**ORT, "name": "Uerige"})[0])

    def test_andere_brauerei_ist_kein_altbier(self):
        self.assertNotIn("Altbier", regeln({**ORT, "name": "Kölner Brauerei"})[0])
        self.assertNotIn("Altbier", regeln({**ORT, "name": "Café Schlüssel"})[0])
        self.assertNotIn("Altbier", regeln({**ORT, "name": "Hotel Schumacher"})[0])
        self.assertIn("Altbier", regeln({**ORT, "name": "Schumacher Gerresheim"})[0])  # Filiale zählt
        for fremd in ("Pizzeria Schumacher", "Restaurant zum Schlüssel", "Kaffee Schlüssel", "Hostel Uerige"):
            self.assertNotIn("Altbier", regeln({**ORT, "name": fremd})[0], fremd)

    def test_brauerei_als_nebentyp_ist_kein_brauhaus(self):
        # Google hängt „brewery“ auch an Fischrestaurants (Juttas Forelle) – nur Primärtyp/Name zählen
        ort = {**ORT, "name": "Juttas Forelle",
               "extras": {**ORT["extras"], "google_primaertyp": "restaurant", "google_typen": ["restaurant", "brewery"]}}
        extras, _, _ = zusammenfuehren(ort, None)
        self.assertNotEqual(extras.get("unterart"), "brauhaus")


class ZusammenfuehrenTest(unittest.TestCase):
    def ki(self, **teile):
        basis = {"unterart": "kneipe", "merkmale": [], "happy_hour_zeit": "", "happy_hour_zitat": "",
                 "raucher": "unbekannt", "raucher_zitat": "", "beschreibung": "", "highlight": ""}
        return {**basis, **teile}

    def test_belegte_angaben_werden_uebernommen(self):
        extras, _, verworfen = zusammenfuehren(ORT, self.ki(
            merkmale=[{"wert": "Whisky", "zitat": "tolle Whisky-Auswahl hinter der Theke"}],
            happy_hour_zeit="17–19 Uhr", happy_hour_zitat="Happy Hour von 17 bis 19 Uhr",
        ))
        self.assertIn("Whisky", extras["spezialitaeten"])
        self.assertEqual(extras["happy_hour"]["text"], "17–19 Uhr")
        self.assertEqual(verworfen, [])

    def test_erfundene_angaben_werden_verworfen(self):
        extras, _, verworfen = zusammenfuehren(ORT, self.ki(
            merkmale=[{"wert": "Craft Beer", "zitat": "riesige Auswahl an Craft Beer"}],
            happy_hour_zeit="18–20 Uhr", happy_hour_zitat="Happy Hour von 17 bis 19 Uhr",  # Zeit passt nicht
            raucher="innen", raucher_zitat="hier darf drinnen geraucht werden",
        ))
        self.assertNotIn("Craft Beer", extras["spezialitaeten"])
        self.assertNotIn("happy_hour", extras)
        self.assertNotIn("raucher", extras)
        self.assertEqual(len(verworfen), 3)

    def test_unbekannte_werte_ignoriert_und_texte_begrenzt(self):
        extras, spalten, _ = zusammenfuehren(ORT, self.ki(
            merkmale=[{"wert": "Karaoke", "zitat": "Sehr gemütlich, tolle Whisky-Auswahl"}],
            beschreibung="kurz", highlight="x" * 300,
        ))
        self.assertNotIn("Karaoke", extras["spezialitaeten"] + extras["vibes"])
        self.assertEqual(spalten, {})

    def test_beschreibung_auch_ohne_brauhaus(self):
        text = "Urige Kneipe in der Altstadt mit Biergarten, in der man bei einem Bier schnell ins Gespräch kommt."
        _, spalten, _ = zusammenfuehren(ORT, self.ki(beschreibung=text, highlight="Biergarten mitten in der Altstadt"))
        self.assertEqual(spalten["beschreibung"], text)
        self.assertEqual(spalten["highlight"], "Biergarten mitten in der Altstadt")

    def test_brauhaus_ohne_ki(self):
        extras, spalten, _ = zusammenfuehren({**ORT, "name": "Brauhaus Test"}, None)
        self.assertEqual(extras["unterart"], "brauhaus")
        self.assertEqual(spalten, {})

    def test_raucher_und_happy_hour_brauchen_stichwort(self):
        ort = {**ORT, "extras": {**ORT["extras"], "google_bewertungen": [
            {"text": "Ich bin seit 17 Jahren Stammgast hier."},
            {"text": "Wunderbare Kneipe mit toller Terrasse am Rhein."},
        ]}}
        extras, _, verworfen = zusammenfuehren(ort, self.ki(
            happy_hour_zeit="17 Uhr", happy_hour_zitat="seit 17 Jahren Stammgast",
            raucher="aussen", raucher_zitat="mit toller Terrasse am Rhein",
        ))
        self.assertNotIn("happy_hour", extras)
        self.assertNotIn("raucher", extras)
        self.assertEqual(len(verworfen), 2)

    def test_raucherbereich_mit_stichwort(self):
        ort = {**ORT, "extras": {**ORT["extras"], "google_bewertungen": [{"text": "Toiletten sauber, Raucherbereich draußen."}]}}
        extras, _, _ = zusammenfuehren(ort, self.ki(raucher="aussen", raucher_zitat="Raucherbereich draußen"))
        self.assertEqual(extras["raucher"]["wert"], "aussen")

    def test_restaurant_behaelt_eigenen_text(self):
        text = "Urige Kneipe in der Altstadt mit Biergarten, in der man bei einem Bier schnell ins Gespräch kommt."
        restaurant = {**ORT, "typ": "restaurant", "beschreibung": "Bayerische Küche mit Biergarten.", "highlight": None}
        _, spalten, _ = zusammenfuehren(restaurant, self.ki(beschreibung=text, highlight="Biergarten mitten in der Altstadt"))
        self.assertNotIn("beschreibung", spalten)                       # vorhandener Text bleibt
        self.assertEqual(spalten["highlight"], "Biergarten mitten in der Altstadt")  # leeres Feld darf gefüllt werden

    def test_stichworte_ohne_fehltreffer(self):
        nein = {
            "Altbier": "Die Kneipe ist schon sehr alt",
            "Wein": "Die Schweinshaxe war super",
            "Draußen sitzen": "Der Wirt ist sehr besonnen",
            "Sportsbar": "Das Personal ist sportlich gekleidet",
            "Craft Beer": "The principal reason we came",
            "Gemütlich": "Leider war ich etwas traurig",
        }
        for wert, zitat in nein.items():
            self.assertFalse(stichwort_passt(wert, zitat), (wert, zitat))
        ja = {
            "Altbier": "Ein Alt vom Fass für 2,50", "Wein": "Guter Rotwein und Weinschorle",
            "Draußen sitzen": "Schöner Biergarten in der Sonne", "Sportsbar": "Sportübertragung auf großer Leinwand",
            "Craft Beer": "Leckeres IPA vom Hahn",
        }
        for zitat in ("lecker Schumacher Alt getrunken", "Das Alt war lecker", "Anstelle von 0,2 Alt",
                      "zum selbst gebrauten Alt", "Leckeres Schlüssel-Alt vom Fass"):
            self.assertTrue(stichwort_passt("Altbier", zitat), zitat)
        for wert, zitat in ja.items():
            self.assertTrue(stichwort_passt(wert, zitat), (wert, zitat))

    def test_stichworte_dritte_runde(self):
        nein = [
            ("Altbier", "Das Haus ist seit 1890 alt"), ("Altbier", "Das Gebäude ist 100 alt"),
            ("Altbier", "Die Kneipe am Dom alt und gemütlich"), ("Altbier", "Im Herbst alt geworden"),
            ("Wein", "Frohe Weinachten an alle"), ("Wein", "Es war zum Weinen schön"),
            ("Sportsbar", "Mit dem Sportwagen vorgefahren"),
        ]
        for wert, zitat in nein:
            self.assertFalse(stichwort_passt(wert, zitat), (wert, zitat))
        ja = [
            ("Altbier", "Eine Stange Alt bitte"), ("Altbier", "Ein Glas Alt"), ("Altbier", "Düsseldorfer Alt vom Fass"),
            ("Altbier", "Ein kleines Alt zum Abschluss"), ("Altbier", "0,2l Alt für 2,50"), ("Altbier", "0,2 l Alt"),
            ("Altbier", "ein herbes Alt"), ("Wein", "Weinprobe mit drei Weinen"), ("Wein", "Glühwein am Stand"),
            ("Wein", "Tolle Auswahl an Weinen"), ("Wein", "Brot zum Wein"),
            ("Draußen sitzen", "Ein schönes Gartenlokal"), ("Craft Beer", "Große Auswahl an IPAs"),
        ]
        for wert, zitat in ja:
            self.assertTrue(stichwort_passt(wert, zitat), (wert, zitat))

    def test_raucher_klauselweise_und_smoking(self):
        q = "Rauchverbot drinnen, Raucherbereich draußen. Der Wirt kam im Smoking."
        self.assertTrue(raucher_belegt("Rauchverbot drinnen, Raucherbereich draußen.", q))
        self.assertFalse(raucher_belegt("Der Wirt kam im Smoking.", q))

    def test_happy_hour_bindestrich_und_jahre(self):
        q = "Jeden Montag 2-für-1 ab 18 Uhr. Happy Hour seit 17 Jahren. Happy Hour von 17 bis 19 Uhr."
        self.assertTrue(happy_hour_belegt("ab 18 Uhr", "Jeden Montag 2-für-1 ab 18 Uhr.", q))
        self.assertFalse(happy_hour_belegt("17 Uhr", "Happy Hour seit 17 Jahren.", q))
        self.assertTrue(happy_hour_belegt("17–19 Uhr", "Happy Hour von 17 bis 19 Uhr.", q))

    def test_raucher_gegenteil_und_rauchbier(self):
        q = "Hier gibt es Rauchbier. Reine Nichtraucherkneipe. Absolute Nicht-Raucher Bar. Seit Jahren rauchfrei. Raucherbereich im Hof."
        self.assertFalse(raucher_belegt("Hier gibt es Rauchbier.", q))
        self.assertFalse(raucher_belegt("Reine Nichtraucherkneipe.", q))
        self.assertFalse(raucher_belegt("Absolute Nicht-Raucher Bar.", q))
        self.assertFalse(raucher_belegt("Seit Jahren rauchfrei.", q))
        self.assertTrue(raucher_belegt("Raucherbereich im Hof.", q))

    def test_happy_hour_nicht_ueber_halben_preis(self):
        q = "Um 17 Uhr gibt es Bier zum halben Liter. Happy Hour 17-19 Uhr."
        self.assertFalse(happy_hour_belegt("17 Uhr", "Um 17 Uhr gibt es Bier zum halben Liter.", q))
        self.assertTrue(happy_hour_belegt("17–19 Uhr", "Happy Hour 17-19 Uhr.", q))

    def test_allgemeines_lob_belegt_kein_merkmal(self):
        # Zitat steht wörtlich im Text, sagt aber nichts über „gesellig“ – verwerfen
        extras, _, verworfen = zusammenfuehren(ORT, self.ki(
            merkmale=[{"wert": "Gesellig", "zitat": "Sehr gemütlich, tolle Whisky-Auswahl"},
                      {"wert": "Gemütlich", "zitat": "Sehr gemütlich, tolle Whisky-Auswahl"}],
        ))
        self.assertNotIn("Gesellig", extras["vibes"])
        self.assertIn("Gemütlich", extras["vibes"])
        self.assertEqual(extras["merkmal_belege"], {"Gemütlich": "Sehr gemütlich, tolle Whisky-Auswahl"})
        self.assertEqual(verworfen, ["Gesellig (Zitat passt nicht zum Merkmal)"])


if __name__ == "__main__":
    unittest.main()
