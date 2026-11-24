"""Tests für den Scraper Theatermuseum Düsseldorf (Quellen-Ausbau V1, ohne Netz).
python -m unittest tests.test_theatermuseum"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import theatermuseum as t

HTML = (Path(__file__).parent / "fixtures" / "theatermuseum_kalender.html").read_text(encoding="utf-8")
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")
FELDER = {"titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "beschreibung", "preis", "quelle_name",
          "quelle_url", "bild_url", "bild_generiert", "status"}


class TheatermuseumTest(unittest.TestCase):
    def setUp(self):
        self.events = t._termine_aus_html(HTML, date(2026, 11, 24), date(2027, 3, 24))

    def test_termine_aus_dem_auszug(self):
        self.assertGreaterEqual(len(self.events), 8)
        erstes = self.events[0]
        self.assertEqual(erstes["titel"], "Lasst uns zurückblicken: Fotoalbum-Abend Teil I")
        self.assertEqual(erstes["datum"], "2026-11-24")
        self.assertEqual(erstes["uhrzeit"], "18:00")
        self.assertEqual(erstes["ort"], "Theatermuseum Düsseldorf")
        self.assertEqual(erstes["adresse"], "Jägerhofstraße 1, 40479 Düsseldorf")
        self.assertEqual(erstes["kategorie"], "kultur")
        self.assertTrue(erstes["quelle_url"].startswith("https://theater-museum.de/kalender/"))
        self.assertTrue(erstes["bild_url"].startswith("https://theater-museum.de/media/"))

    def test_pflichtfelder(self):
        for e in self.events:
            self.assertEqual(set(e), FELDER)
            for feld in PFLICHT:
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])
            self.assertEqual(e["quelle_name"], "Theatermuseum Düsseldorf")
            self.assertRegex(e["uhrzeit"], r"^\d{2}:\d{2}$")

    def test_familie_und_goethe_museum(self):
        nachwuchs = next(e for e in self.events if e["titel"] == "TMD mit Nachwuchs")
        self.assertEqual(nachwuchs["kategorie"], "family")
        slam = next(e for e in self.events if "Poetry Slam" in e["titel"])
        self.assertEqual(slam["ort"], "Goethe-Museum")
        self.assertEqual(slam["adresse"], "Jacobistraße 2, 40211 Düsseldorf")
        self.assertEqual(slam["uhrzeit"], "19:30")

    def test_zeitfenster_und_seiten(self):
        self.assertEqual(t._termine_aus_html(HTML, date(2026, 11, 25), date(2026, 11, 25)), [])
        self.assertEqual(t._seitenzahl(HTML), 3)
        self.assertEqual(t._uhrzeit_aus("18:00–20:00, stille Lesezeit ab 18:30 Uhr"), "18:00")


if __name__ == "__main__":
    unittest.main()
