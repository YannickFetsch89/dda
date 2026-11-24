"""Tests für den Ticket-Link aus der d.live-Kalender-API (Plan Quellen-Ausbau 5.5.2, Schritt P1).
python -m unittest tests.test_dlive_ticket – Eintrag nach dem Muster der API-Antwort vom 24.11.2026."""
import unittest
from datetime import date

from scraper.tier2 import dlive

EINTRAG = {
    "id": "date_1963", "title": "The Script", "type": "Konzerte", "status": "regular", "status_label": "regular",
    "available": 1, "venue": "venue_3",
    "image": "https://www.d-live.de/fileadmin/_processed_/0/3/csm_eventkalender-thescript.jpg",
    "url_detail": "https://www.mitsubishi-electric-halle.de/event/the-script-24-11-2026",
    "links": [
        {"title": "Parking", "url": "https://www.d-live.de/parken", "icon": "parking", "class": "parking-conversion"},
        {"title": "VIP Logen-Tickets", "url": "https://tickets.psd-bank-dome.de/vip", "icon": "loge",
         "class": "vip-logen-tickets-conversion"},
        {"title": "Tickets", "url": "https://www.eventim.de/event/the-script-12345/", "icon": "ticket",
         "class": "tickets-conversion"},
    ],
    "date": {"formatted": "2099-11-24T19:30:00.000Z", "starting_time": "2099-11-24T19:30:00.000Z"},
}


class TicketUrlTest(unittest.TestCase):
    def test_tickets_button_wird_ticket_url(self):
        event = dlive._event_aus_api_dict(EINTRAG, date(2026, 11, 24))
        self.assertEqual(event["ticket_url"], "https://www.eventim.de/event/the-script-12345/")
        self.assertEqual(event["quelle_url"], EINTRAG["url_detail"])

    def test_nur_vip_oder_parken_kein_ticket_url(self):
        eintrag = dict(EINTRAG, links=EINTRAG["links"][:2])
        self.assertIsNone(dlive._event_aus_api_dict(eintrag, date(2026, 11, 24))["ticket_url"])

    def test_kaputte_links_verhindern_das_event_nicht(self):
        for links in (None, "kaputt", [None, {"class": "tickets-conversion", "url": "/relativ"}]):
            event = dlive._event_aus_api_dict(dict(EINTRAG, links=links), date(2026, 11, 24))
            self.assertIsNotNone(event)
            self.assertIsNone(event["ticket_url"])


if __name__ == "__main__":
    unittest.main()
