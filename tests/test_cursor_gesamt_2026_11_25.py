"""Tests zur Cursor-Gesamtprüfung seit V2 (25.11.2026): Ticket-Links ohne Benutzername, Jahreswechsel in den
Datumslisten der Bürgerhäuser. python -m unittest tests.test_cursor_gesamt_2026_11_25"""
import unittest
from datetime import date

from scraper.tier2 import buergerhaeuser as bh
from scraper.utils.ticket_link import ticket_link, ticket_link_haus


class BenutzerInUrlTest(unittest.TestCase):
    def test_nie_mit_benutzername(self):
        for url in ("https://www.eventim.de@evil.com/phish", "https://user:pass@www.reservix.de/e/1"):
            self.assertIsNone(ticket_link(url), url)
            self.assertIsNone(ticket_link_haus(url), url)
        self.assertEqual(ticket_link("https://www.eventim.de/event/x/"), "https://www.eventim.de/event/x/")


class JahreswechselTest(unittest.TestCase):
    def test_liste_ueber_den_jahreswechsel(self):
        daten, _ = bh._daten_aus_zeile("Sonntag, 28.12., 4.1.2027")
        self.assertEqual(daten, [date(2026, 12, 28), date(2027, 1, 4)])

    def test_liste_im_selben_jahr(self):
        daten, _ = bh._daten_aus_zeile("5.3., 11.6. und 26.11.2027")
        self.assertEqual(daten, [date(2027, 3, 5), date(2027, 6, 11), date(2027, 11, 26)])


if __name__ == "__main__":
    unittest.main()
