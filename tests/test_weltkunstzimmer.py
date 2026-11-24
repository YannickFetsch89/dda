"""
test_weltkunstzimmer.py – Tests für scraper/tier2/weltkunstzimmer.py ohne Netz
(Fixtures: 10 Beiträge der Programmseite und eine gekürzte Detailseite von weltkunstzimmer.de vom 24.11.2026).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import weltkunstzimmer as modul

FIXTURES = Path(__file__).parent / "fixtures"
BEGEMANN = "https://weltkunstzimmer.de/bernd-begemann-die-befreiung/"
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class TestWeltkunstzimmer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.liste = (FIXTURES / "weltkunstzimmer_programm.html").read_text(encoding="utf-8")
        cls.detail = modul._details_aus_html((FIXTURES / "weltkunstzimmer_detail.html").read_text(encoding="utf-8"))
        cls.events = modul._termine_aus_html(cls.liste, date(2026, 11, 24), date(2027, 3, 24), {BEGEMANN: cls.detail})

    def test_zeitfenster(self):
        self.assertEqual([e["datum"] for e in self.events], ["2026-12-11", "2027-01-29", "2027-03-05", "2027-03-06"])

    def test_pflichtfelder(self):
        for e in self.events:
            for feld in PFLICHT:
                self.assertTrue(e[feld], feld)
            self.assertEqual(e["ort"], "Weltkunstzimmer")
            self.assertEqual(e["adresse"], "Ronsdorfer Str. 77a, 40233 Düsseldorf")
            self.assertTrue(e["quelle_url"].startswith("https://weltkunstzimmer.de/"))
            self.assertTrue(e["bild_url"].startswith("https://weltkunstzimmer.de/wp-content/uploads/"))
            self.assertIsNone(e["beschreibung"])

    def test_konzert_mit_detailseite(self):
        e = next(x for x in self.events if x["quelle_url"] == BEGEMANN)
        self.assertEqual(e["titel"], "BERND BEGEMANN & DIE BEFREIUNG")
        self.assertEqual(e["uhrzeit"], "20:00")   # Beginn, nicht Einlass 19 Uhr
        self.assertEqual(e["kategorie"], "musik")
        self.assertIn("25 Euro", e["preis"])
        self.assertNotIn("datum_bis", e)

    def test_mehrtaegig(self):
        e = self.events[0]
        self.assertEqual(e["titel"], "Electric Assembly – Workshop & Performance")
        self.assertEqual(e["datum_bis"], "2026-12-13")
        self.assertEqual(e["kategorie"], "kultur")
        pupapo = self.events[1]
        self.assertEqual((pupapo["datum"], pupapo["datum_bis"]), ("2027-01-29", "2027-01-31"))

    def test_zerlegen(self):
        self.assertEqual(modul._zerlegen("Sonic Fusion #4, Die Frage, Louretta &amp; Dr. Schmitt, Samstag 21. Februar 2026, 20 Uhr"),
                         ("Sonic Fusion #4, Die Frage, Louretta & Dr. Schmitt", [("2026-02-21", None)], "20:00"))
        self.assertEqual(modul._zerlegen("Intersection / EINE MENGE, 25. – 26. April und 1. – 2. Mai 2026")[1],
                         [("2026-04-25", "2026-04-26"), ("2026-05-01", "2026-05-02")])
        self.assertEqual(modul._zerlegen("UNHEARD, Samstag 13. Juni 2026, 16 – 18 Uhr")[2], "16:00")
        self.assertEqual(modul._zerlegen("9. Urban Space Video Walk – 11. September 2026, 19 Uhr")[0],
                         "9. Urban Space Video Walk")
        self.assertIsNone(modul._zerlegen("space_relations Lab 2"))

    def test_vergangene_termine_im_auszug(self):
        alle = modul._termine_aus_html(self.liste, date(2026, 1, 1), date(2027, 12, 31))
        self.assertGreater(len(alle), len(self.events))
        jules = next(e for e in alle if e["titel"].startswith("Jules Ahoi"))
        self.assertEqual((jules["datum"], jules["uhrzeit"]), ("2026-10-15", "20:00"))


if __name__ == "__main__":
    unittest.main()
