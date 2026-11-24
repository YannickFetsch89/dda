"""
test_tas_neuss.py – Tests für scraper/tier2/tas_neuss.py ohne Netz.
Fixture: tests/fixtures/tas_neuss_spielplan.html (Spielplan vom 24.11.2026, auf 9 Karten gekürzt).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import tas_neuss as modul

FIXTURE = Path(__file__).parent / "fixtures" / "tas_neuss_spielplan.html"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


class TestTasNeuss(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = FIXTURE.read_text(encoding="utf-8")
        cls.events = modul._termine_aus_html(cls.html, date(2026, 11, 24), date(2027, 11, 24))

    def test_pflichtfelder(self):
        self.assertEqual(len(self.events), 8)
        for e in self.events:
            for feld in ("titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "quelle_name", "quelle_url"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertEqual(e["ort"], "Theater am Schlachthof")
            self.assertEqual(e["adresse"], "Blücherstraße 31-33, 41460 Neuss")
            self.assertTrue(e["quelle_url"].startswith("https://tas-neuss.de/veranstaltung/"))
            self.assertIsNone(e["beschreibung"])
            self.assertEqual(e["status"], "neu")

    def test_schauspiel(self):
        e = self.events[0]
        self.assertEqual((e["titel"], e["datum"], e["uhrzeit"], e["kategorie"]),
                         ("Ein Mann des Volkes", "2026-11-27", "19:30", "kultur"))
        self.assertTrue(e["bild_url"].startswith("https://tas-neuss.de/wp-content/uploads/"))

    def test_kindertheater_volle_stunde(self):
        e = next(e for e in self.events if e["titel"] == "Ein schrecklich schöner Weihnachtsspuk")
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2026-11-29", "15:00", "family"))

    def test_premiere_aus_titel(self):
        titel = [e["titel"] for e in self.events if e["titel"].startswith("Ab ins Bett")]
        self.assertEqual(titel, ["Ab ins Bett!", "Ab ins Bett!"])

    def test_wetthalle_ausgelassen(self):
        self.assertFalse(any("80er" in e["titel"] for e in self.events))

    def test_titel_ohne_umbruch(self):
        self.assertIn("Das NEINhorn von Marc-Uwe Kling", [e["titel"] for e in self.events])

    def test_zeitfenster(self):
        events = modul._termine_aus_html(self.html, date(2026, 11, 28), date(2026, 12, 31))
        self.assertEqual({e["datum"] for e in events}, {"2026-11-29"})


if __name__ == "__main__":
    unittest.main()
