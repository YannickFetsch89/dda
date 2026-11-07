"""Tests für die Einordnung von Kneipen & Bars (python -m unittest tests.test_bars_einordnen)."""
import unittest

from scraper.orte.bars_einordnen import belegt, regeln, zusammenfuehren

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


if __name__ == "__main__":
    unittest.main()
