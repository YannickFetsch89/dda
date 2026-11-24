"""Tests für den Ticket-Link der Fortuna-Heimspiele (Plan Quellen-Ausbau 5.5.2, Schritt P1).
python -m unittest tests.test_fortuna – Fixture: drei Spielkarten aus www.f95.de/spielplan (gerendert, 24.11.2026)
plus der allgemeine Navigations-Link „TICKETS“."""
import re
import unittest
from datetime import date
from pathlib import Path

from scraper.tier3 import fortuna

HTML = (Path(__file__).parent / "fixtures" / "fortuna_spielplan.html").read_text(encoding="utf-8")
SHOP = "https://tickets.f95.de/f95/venue/Veranstaltungen/8e0f9d20-8f17-4517-9370-b1dfb316c72a"


class TicketUrlTest(unittest.TestCase):
    def test_button_der_spielkarte_wird_ticket_url(self):
        events = fortuna._events_aus_html(HTML, date(2026, 11, 24), date(2027, 11, 24))
        heimspiel = next(e for e in events if e["datum"] == "2026-12-05")
        self.assertEqual(heimspiel["ticket_url"], SHOP)
        self.assertEqual(heimspiel["quelle_url"], fortuna.LISTE_URL)

    def test_navigationslink_wird_nicht_zugeordnet(self):
        ohne_button = re.sub(r'<a [^>]*href="https://tickets\.f95\.de/f95/venue/[^"]*"[^>]*>.*?</a>', "", HTML)
        events = fortuna._events_aus_html(ohne_button, date(2026, 11, 24), date(2027, 11, 24))
        self.assertTrue(events)
        self.assertTrue(all(e["ticket_url"] is None for e in events))


if __name__ == "__main__":
    unittest.main()
