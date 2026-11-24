"""Tests für den Veranstaltungskalender der Kunstsammlung NRW (Plan Quellen-Ausbau, Schritt V0).
python -m unittest tests.test_kunstsammlung_kalender"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import kunstsammlung as k

HTML = (Path(__file__).parent / "fixtures" / "kunstsammlung_kalender.html").read_text(encoding="utf-8")


class KalenderTest(unittest.TestCase):
    def test_termine_aus_dem_auszug(self):
        events = k._kalender_events(HTML, date(2026, 11, 24), date(2027, 11, 24))
        self.assertGreaterEqual(len(events), 10)
        erstes = events[0]
        self.assertEqual(erstes["datum"], "2026-11-25")
        self.assertEqual(erstes["uhrzeit"], "16:00")
        self.assertEqual(erstes["ort"], "K21 Ständehaus")
        self.assertIn("40217", erstes["adresse"])
        self.assertEqual(erstes["preis"], "kostenlos")
        self.assertFalse(erstes["titel"].startswith("K21 "))
        self.assertTrue(erstes["quelle_url"].startswith("https://www.kunstsammlung.de/de/events/"))
        self.assertTrue(all(e["quelle_name"] == "Kunstsammlung NRW (K20/K21)" for e in events))

    def test_ticket_url(self):
        """Plan 5.5.2 P1: Button „Tickets“ des Termins → Webshop-Link, ohne Button kein ticket_url."""
        events = k._kalender_events(HTML, date(2026, 11, 24), date(2027, 11, 24))
        yoga = next(e for e in events if "Yoga" in e["titel"])
        self.assertEqual(yoga["ticket_url"], "https://shop.kunstsammlung.de/de/offers/a954")
        self.assertTrue(any(e["ticket_url"] is None for e in events))
        self.assertTrue(all(e["ticket_url"] is None or e["ticket_url"].startswith("https://") for e in events))

    def test_zeitfenster(self):
        self.assertEqual(k._kalender_events(HTML, date(2026, 11, 24), date(2026, 11, 24)), [])

    def test_uhrzeit(self):
        self.assertEqual(k._uhrzeit_aus("13.30 – 14.30 Uhr"), "13:30")
        self.assertEqual(k._uhrzeit_aus("15 – 18 Uhr"), "15:00")
        self.assertIsNone(k._uhrzeit_aus("ganztägig"))


if __name__ == "__main__":
    unittest.main()
