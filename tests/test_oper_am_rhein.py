"""Tests für den Ticket-Link der Deutschen Oper am Rhein (Plan Quellen-Ausbau 5.5.2, Schritt P1).
python -m unittest tests.test_oper_am_rhein – Fixture: Auszug aus /spielplan/ vom 24.11.2026 (eine Vorstellung mit,
eine ohne Karten-Button)."""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import oper_am_rhein as oper

HTML = (Path(__file__).parent / "fixtures" / "oper_am_rhein_spielplan.html").read_text(encoding="utf-8")


class TicketUrlTest(unittest.TestCase):
    def setUp(self):
        self.events = oper._events_aus_html(HTML, date(2026, 11, 24), set())

    def test_karten_button_wird_ticket_url(self):
        self.assertEqual(len(self.events), 2)
        mit = self.events[0]
        self.assertTrue(mit["ticket_url"].startswith("https://webshop.operamrhein.de/eventim.webshop/"))
        self.assertTrue(mit["quelle_url"].startswith("https://www.operamrhein.de/spielplan/"))

    def test_ohne_button_kein_ticket_url(self):
        self.assertIsNone(self.events[1]["ticket_url"])


if __name__ == "__main__":
    unittest.main()
