"""
test_nachtresidenz.py – Tests für scraper/tier2/nachtresidenz.py ohne Netz
(Fixture: Auszug aus https://www.nachtresidenz.de/events/ vom 24.11.2026).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import nachtresidenz as modul

FIXTURE = Path(__file__).parent / "fixtures" / "nachtresidenz_events.html"
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class TestNachtresidenz(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = FIXTURE.read_text(encoding="utf-8")
        cls.events = modul._termine_aus_html(cls.html, date(2026, 11, 24), date(2027, 3, 24))

    def test_anzahl_und_sortierung(self):
        self.assertEqual(len(self.events), 11)
        self.assertEqual(self.events[0]["datum"], "2026-11-25")   # steht auf der Seite weiter unten
        self.assertEqual([e["datum"] for e in self.events], sorted(e["datum"] for e in self.events))

    def test_pflichtfelder(self):
        for e in self.events:
            for feld in PFLICHT:
                self.assertTrue(e[feld], feld)
            self.assertEqual(e["ort"], "Nachtresidenz")
            self.assertEqual(e["adresse"], "Bahnstraße 13, 40212 Düsseldorf")
            self.assertEqual(e["quelle_url"], "https://www.nachtresidenz.de/events/")   # „Mehr“ führt zu Ticket-Shops
            self.assertTrue(e["bild_url"].startswith("https://www.nachtresidenz.de/wp-content/uploads/"))
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])

    def test_einzelner_termin(self):
        e = next(x for x in self.events if x["titel"] == "PEACHES")
        self.assertEqual(e["datum"], "2026-12-12")
        self.assertEqual(e["uhrzeit"], "23:00")
        self.assertEqual(e["kategorie"], "nightlife")

    def test_tour_ist_musik(self):
        e = next(x for x in self.events if x["titel"] == "MAMMA MIA ABBA TOUR")
        self.assertEqual(e["kategorie"], "musik")
        self.assertEqual(e["uhrzeit"], "19:30")

    def test_zeitfenster(self):
        events = modul._termine_aus_html(self.html, date(2026, 12, 31), date(2026, 12, 31))
        self.assertEqual(len(events), 2)

    def test_leere_seite(self):
        self.assertEqual(modul._termine_aus_html("<html></html>", date(2026, 11, 24), date(2027, 1, 1)), [])


if __name__ == "__main__":
    unittest.main()
