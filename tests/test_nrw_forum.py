"""Tests für den Ticket-Link des NRW-Forums (Plan Quellen-Ausbau 5.5.2, Schritt P1).
python -m unittest tests.test_nrw_forum – Playwright wird ersetzt; Roheinträge nach dem Muster des Shadow DOM
von <nrwf-dates> (24.11.2026)."""
import unittest
from datetime import date, timedelta
from unittest import mock

from scraper.tier2 import nrw_forum

TAG = date.today() + timedelta(days=5)
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
          "November", "Dezember"]
DATUM = f"{TAG.day}. {MONATE[TAG.month - 1]} {TAG.year}"
SHOP = "https://www.kunstpalast.de/de/shop/ticketauswahl-nrw-forum/?e=274907"

ROHDATEN = [
    {"date": DATUM, "time": "18:00 Uhr", "title": "Reisesprachkurs Japanisch", "subtitle": "", "venue": "",
     "img": None, "href": "/veranstaltungen/reisesprachkurs-japanisch", "ticket": SHOP},
    {"date": DATUM, "time": "20:00 Uhr", "title": "Ohne Tickets", "subtitle": "", "venue": "",
     "img": None, "href": "/veranstaltungen/ohne", "ticket": None},
]


class TicketUrlTest(unittest.TestCase):
    def test_tickets_button_wird_ticket_url(self):
        pw = mock.MagicMock()
        pw.__enter__.return_value.chromium.launch.return_value.new_page.return_value.evaluate.return_value = ROHDATEN
        with mock.patch("playwright.sync_api.sync_playwright", return_value=pw), mock.patch("time.sleep"):
            events = {e["titel"]: e for e in nrw_forum.scrape()}
        self.assertEqual(events["Reisesprachkurs Japanisch"]["ticket_url"], SHOP)
        self.assertEqual(events["Reisesprachkurs Japanisch"]["quelle_url"],
                         "https://www.nrw-forum.de/veranstaltungen/reisesprachkurs-japanisch")
        self.assertIsNone(events["Ohne Tickets"]["ticket_url"])

    def test_ticket_url_regeln(self):
        self.assertEqual(nrw_forum._ticket_url("https://nrw-forum.reservix.de/e1"), "https://nrw-forum.reservix.de/e1")
        self.assertIsNone(nrw_forum._ticket_url("/veranstaltungen/x"))
        self.assertIsNone(nrw_forum._ticket_url("mailto:info@nrw-forum.de"))
        self.assertIsNone(nrw_forum._ticket_url(None))


if __name__ == "__main__":
    unittest.main()
