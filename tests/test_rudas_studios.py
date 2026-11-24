"""Tests für den Ticket-Link der Rudas Studios (Plan Quellen-Ausbau 5.5.2, Schritt P1).
python -m unittest tests.test_rudas_studios – stagedates-API-Antwort nach dem Muster vom 24.11.2026, ohne Netz."""
import json
import unittest
from datetime import date
from unittest import mock

from scraper.tier2 import rudas_studios as rudas

ANTWORT = json.dumps({"data": [
    {"title": "Rudas Night", "slug": "rudas-night", "shortCode": "AB12C", "startDate": "2026-12-05T22:00:00Z",
     "timezone": {"name": "Europe/Berlin"}, "cheapestPriceMny": {"amount": "15.00"}},
    {"title": "Ohne Shop", "startDate": "2026-12-06T22:00:00Z", "timezone": {"name": "Europe/Berlin"}},
]})


class TicketUrlTest(unittest.TestCase):
    def test_stagedates_shop_wird_ticket_url(self):
        with mock.patch.object(rudas, "seite_abrufen", return_value=ANTWORT):
            mit, ohne = rudas._events_aus_stagedates(date(2026, 11, 24), date(2027, 11, 24))
        self.assertEqual(mit["ticket_url"], "https://stagedates.com/events/rudas-night-AB12C")
        self.assertEqual(mit["quelle_url"], mit["ticket_url"])
        self.assertIsNone(ohne.get("ticket_url"))


if __name__ == "__main__":
    unittest.main()
