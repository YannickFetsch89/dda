"""Tests für den Ticket-Link des Pitcher (Plan Quellen-Ausbau 5.5.2, Schritt P1).
python -m unittest tests.test_pitcher – Einträge nach dem Muster der EventFlow-API vom 24.11.2026."""
import unittest
from datetime import date

from scraper.tier2 import pitcher

EINTRAG = {
    "title": "Konzert", "status": "published", "is_private_event": False, "last_cancellation": None,
    "start_date": "2026-12-05T20:00:00+01:00", "price_from": 0,
    "detail_url": "https://pitcher29.com/veranstaltungen-pitcher-duesseldorf/konzert/",
    "external_ticket_sales_enabled": True, "external_ticket_button_text": "Tickets",
    "external_ticket_url": "https://pitcher.reservix.de/tickets-konzert/e123",
}


class TicketUrlTest(unittest.TestCase):
    def umwandeln(self, **aenderung):
        return pitcher._event_umwandeln(dict(EINTRAG, **aenderung), date(2026, 11, 24), date(2027, 11, 24))

    def test_externer_ticketlink(self):
        event = self.umwandeln()
        self.assertEqual(event["ticket_url"], "https://pitcher.reservix.de/tickets-konzert/e123")
        self.assertEqual(event["quelle_url"], EINTRAG["detail_url"])

    def test_ohne_oder_abgeschaltet_kein_ticket_url(self):
        self.assertIsNone(self.umwandeln(external_ticket_url=None)["ticket_url"])
        self.assertIsNone(self.umwandeln(external_ticket_sales_enabled=False)["ticket_url"])
        self.assertIsNone(self.umwandeln(external_ticket_url="/relativ")["ticket_url"])


if __name__ == "__main__":
    unittest.main()
