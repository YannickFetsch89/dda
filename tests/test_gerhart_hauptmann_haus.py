"""Tests für den Scraper Gerhart-Hauptmann-Haus (Quellen-Ausbau V1, ohne Netz).
python -m unittest tests.test_gerhart_hauptmann_haus"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import gerhart_hauptmann_haus as g

HTML = (Path(__file__).parent / "fixtures" / "gerhart_hauptmann_haus_monat.html").read_text(encoding="utf-8")
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")
FELDER = {"titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "beschreibung", "preis", "quelle_name",
          "quelle_url", "bild_url", "bild_generiert", "status"}


class GerhartHauptmannHausTest(unittest.TestCase):
    def setUp(self):
        self.events = g._termine_aus_html(HTML, date(2026, 11, 24), date(2027, 3, 24))

    def test_termine_aus_dem_auszug(self):
        self.assertGreaterEqual(len(self.events), 5)
        erstes = self.events[0]
        self.assertEqual(erstes["titel"], "Der Hitler-Stalin-Pakt vom August 1939 in der deutschen Erinnerungskultur")
        self.assertEqual(erstes["datum"], "2026-11-27")
        self.assertEqual(erstes["uhrzeit"], "19:00")
        self.assertEqual(erstes["ort"], "Gerhart Hauptmann Haus")
        self.assertEqual(erstes["adresse"], "Bismarckstraße 90, 40210 Düsseldorf")
        self.assertEqual(erstes["kategorie"], "kultur")
        # Monatsanhang („/2026/dezember/1m“) wird von der Detailadresse entfernt
        self.assertEqual(erstes["quelle_url"], "https://www.g-h-h.de/veranstaltung/"
                         "der-hitler-stalin-pakt-vom-august-1939-in-der-deutschen-erinnerungskultur")

    def test_pflichtfelder(self):
        for e in self.events:
            self.assertEqual(set(e), FELDER)
            for feld in PFLICHT:
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIsNone(e["beschreibung"])
            self.assertTrue(e["quelle_url"].startswith("https://www.g-h-h.de/veranstaltung/"))

    def test_zeitraeume_und_auswaerts_weggelassen(self):
        titel = [e["titel"] for e in self.events]
        self.assertFalse(any("Ausstellung" in t or "Bücherbasar" in t for t in titel))
        self.assertNotIn("Civil society resilience against disinformation", titel)   # Konferenz in Köln
        filtsch = next(e for e in self.events if "Carl Filtsch" in e["titel"])
        self.assertEqual((filtsch["datum"], filtsch["uhrzeit"]), ("2026-12-02", "18:30"))
        tieck = next(e for e in self.events if e["titel"].startswith("Ludwig Tieck"))
        self.assertEqual(tieck["titel"], "Ludwig Tieck: Der Weihnachtsabend")   # Strich am Ende entfernt

    def test_monatslinks_und_fenster(self):
        links = g._monatslinks(HTML)
        self.assertIn("https://www.g-h-h.de/veranstaltung/2027/januar/2m", links)
        self.assertEqual(g._monats_url(date(2026, 11, 24)), "https://www.g-h-h.de/veranstaltung/2026/november")
        self.assertEqual(g._termine_aus_html(HTML, date(2026, 11, 28), date(2026, 11, 30)), [])


if __name__ == "__main__":
    unittest.main()
