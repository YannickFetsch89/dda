"""Tests für den Ticket-Link der Tonhalle (Plan Quellen-Ausbau 5.5.2, Schritt P1).
python -m unittest tests.test_tonhalle – Fixture: ein Produkt aus webshop.tonhalle.de/list/events vom 24.11.2026."""
import unittest
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

from scraper.tier2 import tonhalle

HTML = (Path(__file__).parent / "fixtures" / "tonhalle_webshop.html").read_text(encoding="utf-8")


class TicketUrlTest(unittest.TestCase):
    def test_auswaehlen_button_wird_ticket_url(self):
        section = BeautifulSoup(HTML, "html.parser").select_one("section.product")
        events = tonhalle._event_aus_produkt_section(section, date(2026, 11, 24))
        self.assertTrue(events)
        for event in events:
            self.assertTrue(event["ticket_url"].startswith("https://webshop.tonhalle.de/selection/event/date?productId="))

    def test_ohne_shop_link_kein_ticket_url(self):
        section = BeautifulSoup('<section class="product"><a class="title" href="#">X</a></section>', "html.parser")
        self.assertIsNone(tonhalle._ticket_url(section.section, tonhalle.WEBSHOP_URL.replace("webshop.", "www.")))


if __name__ == "__main__":
    unittest.main()
