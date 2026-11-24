"""Tests für den Scraper Goethe-Museum (Quellen-Ausbau V1, ohne Netz).
python -m unittest tests.test_goethe_museum"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import goethe_museum as g

HTML = (Path(__file__).parent / "fixtures" / "goethe_museum_kalender.html").read_text(encoding="utf-8")
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")
FELDER = {"titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "beschreibung", "preis", "quelle_name",
          "quelle_url", "bild_url", "bild_generiert", "status"}


class GoetheMuseumTest(unittest.TestCase):
    def setUp(self):
        self.events = g._termine_aus_html(HTML, date(2026, 11, 24), date(2027, 3, 24))

    def test_termine_aus_dem_auszug(self):
        self.assertEqual(len(self.events), 4)   # zwei Sonderausstellungen (Zeiträume) fehlen
        konzert = self.events[0]
        self.assertTrue(konzert["titel"].startswith("Wahlverwandtschaften"))
        self.assertEqual(konzert["datum"], "2026-11-27")
        self.assertEqual(konzert["uhrzeit"], "19:30")
        self.assertEqual(konzert["kategorie"], "musik")   # Untertitel „Ein Konzert der Lehrenden …“
        self.assertEqual(konzert["ort"], "Goethe-Museum")
        self.assertEqual(konzert["adresse"], "Jacobistraße 2, 40211 Düsseldorf")
        slam = self.events[1]
        self.assertEqual(slam["titel"], 'Schnickschnack Poetry Slam "Dead or Alive"')
        self.assertEqual((slam["datum"], slam["uhrzeit"], slam["kategorie"]), ("2026-12-04", "20:00", "kultur"))

    def test_pflichtfelder(self):
        for e in self.events:
            self.assertEqual(set(e), FELDER)
            for feld in PFLICHT:
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertTrue(e["quelle_url"].startswith("https://www.goethe-museum.de/de/veranstaltung/"))
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(any("Sonderausstellung" in e["titel"] for e in self.events))

    def test_fenster_und_pager(self):
        self.assertEqual(g._termine_aus_html(HTML, date(2026, 12, 14), date(2027, 3, 24)), [])
        self.assertEqual(g._weitere_seiten(HTML), [])
        self.assertEqual(g._weitere_seiten('<a href="/de/veranstaltung/veranstaltungskalender?page=1">2</a>'),
                         [g.LISTE_URL + "?page=1"])


if __name__ == "__main__":
    unittest.main()
