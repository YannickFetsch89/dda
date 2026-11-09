"""Tanzhaus NRW: Screenreader-Datum darf nicht im Titel landen (python -m unittest tests.test_tanzhaus_titel)."""
import unittest

from bs4 import BeautifulSoup

from scraper.tier2.tanzhaus_nrw import _titel_text


def ueberschrift(html: str):
    return BeautifulSoup(html, "html.parser").find("h3")


class TanzhausTitelTest(unittest.TestCase):
    def test_datum_faellt_weg_zusatz_bleibt(self):
        h = ueberschrift('<h3><a><span class="visually-hidden">Mittwoch, 11. November 2026, ab, 20:15: </span>'
                         ' Noche de la Salsa <span class="visually-hidden">, DJ Vilson </span></a></h3>')
        self.assertEqual(_titel_text(h), "Noche de la Salsa – DJ Vilson")

    def test_ohne_zusatz(self):
        h = ueberschrift('<h3><a><span class="visually-hidden">Freitag, 13. November 2026, 18:00: </span> Tracks </a></h3>')
        self.assertEqual(_titel_text(h), "Tracks")

    def test_normale_ueberschrift(self):
        self.assertEqual(_titel_text(ueberschrift("<h3>\n  take-off Festival\n</h3>")), "take-off Festival")


if __name__ == "__main__":
    unittest.main()
