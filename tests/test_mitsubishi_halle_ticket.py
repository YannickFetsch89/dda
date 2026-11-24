"""Tests für den Ticket-Link der Mitsubishi Electric HALLE (Plan Quellen-Ausbau 5.5.2, Schritt P1).
python -m unittest tests.test_mitsubishi_halle_ticket – API-Antwort nach dem Muster vom 24.11.2026, ohne Netz."""
import unittest
from datetime import date, timedelta
from unittest import mock

from scraper.tier2 import mitsubishi_halle as meh

TAG = (date.today() + timedelta(days=5)).isoformat()


def _eintrag(titel, links):
    return {"title": titel, "type": "Konzerte", "status": "regular", "available": 1,
            "url_detail": f"/event/{titel.lower()}", "links": links,
            "date": {"formatted": f"{TAG}T19:30:00.000Z", "starting_time": f"{TAG}T19:30:00.000Z"}}


ANTWORT = {"dates": [
    _eintrag("Mit", [
        {"title": "KITCHEN Ticket", "url": "https://tickets.mitsubishi-electric-halle.de/kitchen", "class": ""},
        {"title": "Tickets", "url": "https://www.livenation.de/the-script-tickets-adp11534",
         "class": "tickets-conversion"},
    ]),
    _eintrag("Ohne", []),
]}


class TicketUrlTest(unittest.TestCase):
    def test_tickets_button_wird_ticket_url(self):
        client = mock.MagicMock()
        client.__enter__.return_value.get.return_value.json.return_value = ANTWORT
        with mock.patch.object(meh.httpx, "Client", return_value=client):
            events = {e["titel"]: e for e in meh.scrape()}
        self.assertEqual(events["Mit"]["ticket_url"], "https://www.livenation.de/the-script-tickets-adp11534")
        self.assertTrue(events["Mit"]["quelle_url"].startswith("https://www.mitsubishi-electric-halle.de/event/"))
        self.assertIsNone(events["Ohne"]["ticket_url"])


if __name__ == "__main__":
    unittest.main()
