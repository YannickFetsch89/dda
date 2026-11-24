"""Tests für den Ticket-Link des Tanzhaus NRW (Plan Quellen-Ausbau 5.5.2, Schritt P1).
python -m unittest tests.test_tanzhaus_nrw_ticket – Fixture: zwei Kalendereinträge aus /de/kalender vom 24.11.2026."""
import unittest
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

from scraper.tier2 import tanzhaus_nrw as tanzhaus

HTML = (Path(__file__).parent / "fixtures" / "tanzhaus_nrw_kalender.html").read_text(encoding="utf-8")


class TicketUrlTest(unittest.TestCase):
    def setUp(self):
        artikel = BeautifulSoup(HTML, "html.parser").find_all("article")
        self.ohne, self.mit = (tanzhaus._event_aus_element(a, date(2026, 11, 24)) for a in artikel)

    def test_tickets_button_wird_ticket_url(self):
        self.assertTrue(self.mit["ticket_url"].startswith("https://tanzhaus-nrw.reservix.de/"))
        self.assertTrue(self.mit["quelle_url"].startswith("https://tanzhaus-nrw.de/"))

    def test_ohne_button_kein_ticket_url(self):
        self.assertIsNone(self.ohne["ticket_url"])


if __name__ == "__main__":
    unittest.main()
