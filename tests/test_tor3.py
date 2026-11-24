"""
test_tor3.py – Tests für scraper/tier2/tor3.py ohne Netz
(Fixture: Wix-warmup-JSON aus https://www.tor3-club.com/home-2 vom 24.11.2026, 7 von 23 Datensätzen, Texte gekürzt).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import tor3 as modul

FIXTURE = Path(__file__).parent / "fixtures" / "tor3_home2.html"
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class TestTor3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = FIXTURE.read_text(encoding="utf-8")
        cls.events = modul._termine_aus_html(cls.html, date(2026, 11, 24), date(2027, 3, 24))

    def test_nur_kommende_termine(self):
        self.assertEqual([e["datum"] for e in self.events], ["2026-11-27", "2026-11-28", "2026-12-12"])

    def test_pflichtfelder(self):
        for e in self.events:
            for feld in PFLICHT:
                self.assertTrue(e[feld], feld)
            self.assertEqual(e["ort"], "Tor 3")
            self.assertEqual(e["adresse"], "Langenberger Str. 9, 40233 Düsseldorf")
            self.assertTrue(e["quelle_url"].startswith("https://www.tor3-club.com/events-1/"))
            self.assertTrue(e["bild_url"].startswith("https://static.wixstatic.com/media/"))
            self.assertIsNone(e["beschreibung"])

    def test_party_mit_startzeit(self):
        e = self.events[-1]
        self.assertEqual(e["titel"], "SNOWFALL SEASON 1")
        self.assertEqual(e["uhrzeit"], "23:00")
        self.assertEqual(e["kategorie"], "nightlife")
        self.assertEqual(e["quelle_url"], "https://www.tor3-club.com/events-1/snowfall-season-1")

    def test_zeitspanne_und_dating(self):
        hardcore = next(e for e in self.events if e["titel"] == "HARDCORE NATION")
        self.assertEqual(hardcore["uhrzeit"], "20:00")
        matching = next(e for e in self.events if e["titel"] == "Matching Night")
        self.assertEqual(matching["kategorie"], "dating")
        self.assertIsNone(matching["uhrzeit"])

    def test_konzert_beginn_vor_einlass(self):
        events = modul._termine_aus_html(self.html, date(2026, 10, 1), date(2026, 10, 31))
        stephane = next(e for e in events if e["titel"] == "STEPHANE LIVE")
        self.assertEqual(stephane["uhrzeit"], "20:00")   # Einlass 18:30, Konzertbeginn 20:00
        self.assertEqual(stephane["kategorie"], "musik")

    def test_uhrzeit_hilfsfunktion(self):
        self.assertEqual(modul._uhrzeit("Party ab 22.00 Uhr"), "22:00")
        self.assertIsNone(modul._uhrzeit("Eintritt ab 18 Jahren"))
        self.assertEqual(modul._uhrzeit("Einlass: 21:00 / Beginn: 22:30"), "22:30")

    def test_ohne_daten(self):
        self.assertEqual(modul._termine_aus_html("<html></html>", date(2026, 11, 24), date(2027, 1, 1)), [])


if __name__ == "__main__":
    unittest.main()
