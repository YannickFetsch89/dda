"""Tests für den Ticket-Link des Düsseldorfer Schauspielhauses (Plan Quellen-Ausbau 5.5.2, Schritt P1).
python -m unittest tests.test_schauspielhaus – Fixture: ein Spielplan-Tag (4 Vorstellungen, 2 mit Karten-Button)
aus /programm/spielplan/ vom 24.11.2026."""
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import schauspielhaus as sh

HTML = (Path(__file__).parent / "fixtures" / "schauspielhaus_spielplan.html").read_text(encoding="utf-8")
SHOP = "https://ticket.dhaus.de/eventim.webshop/webticket/shop?&event={}&language=de"


class TicketUrlTest(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(sh, "seite_abrufen", return_value=HTML):
            events = sh._monatlichen_spielplan_scrapen(2026, 11, date(2026, 11, 24))
        self.je_url = {e["quelle_url"].replace(sh.BASE_URL, ""): e for e in events}

    def test_jede_vorstellung_bekommt_ihren_eigenen_button(self):
        self.assertEqual(self.je_url["/programm/spielplan/das-gruene-koenigreich/2985/"]["ticket_url"],
                         SHOP.format(26008))
        self.assertEqual(self.je_url["/programm/spielplan/verbrennungen/3102/"]["ticket_url"], SHOP.format(26126))

    def test_ohne_button_kein_ticket_url(self):
        self.assertIsNone(self.je_url["/programm/spielplan/move-it/3103/"]["ticket_url"])
        self.assertIsNone(
            self.je_url["/programm/spielplan/internationaler-tag-gegen-gewalt-an-frauen/3101/"]["ticket_url"])


if __name__ == "__main__":
    unittest.main()
