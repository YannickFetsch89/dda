"""
test_globe_neuss.py – Tests für scraper/tier2/globe_neuss.py ohne Netz.
Fixtures (Kulturamt Neuss, Stand 25.11.2026, gekürzt):
- tests/fixtures/globe_neuss_programm.html – Programmseite des Shakespeare Festivals 2026 (5 Produktionen, alle vorbei)
- tests/fixtures/globe_neuss_detail.html – Produktionsseite „Romeo und Julia“ mit dem Abschnitt „Termine“
"""
import logging
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import globe_neuss as modul

FIXTURES = Path(__file__).parent / "fixtures"
PROGRAMM = (FIXTURES / "globe_neuss_programm.html").read_text(encoding="utf-8")
DETAIL = (FIXTURES / "globe_neuss_detail.html").read_text(encoding="utf-8")
DETAIL_URL = "https://kulturamt-neuss.de/shakespeare/programm/romeo-und-julia/"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


class TestGlobeNeuss(unittest.TestCase):
    def test_programm_ausserhalb_der_saison_leer(self):
        self.assertEqual(modul._programm_aus_html(PROGRAMM), [])
        alle = modul._programm_aus_html(PROGRAMM, alle=True)
        self.assertEqual(len(alle), 5)
        self.assertIn(DETAIL_URL, alle)
        self.assertTrue(all(u.startswith("https://kulturamt-neuss.de/shakespeare/") for u in alle))

    def test_detail_termin_im_globe(self):
        events = modul._termine_aus_detail(DETAIL, DETAIL_URL, date(2026, 1, 1), date(2026, 12, 31))
        self.assertEqual(len(events), 1)
        e = events[0]
        for feld in ("titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status"):
            self.assertTrue(e[feld], f"{feld} leer in {e}")
        self.assertEqual((e["titel"], e["datum"], e["uhrzeit"]), ("Romeo und Julia", "2026-05-16", "19:30"))
        self.assertEqual((e["ort"], e["adresse"]), ("Globe Neuss", "Hammer Landstraße 2, 41460 Neuss"))
        self.assertIn(e["kategorie"], KATEGORIEN)
        self.assertEqual(e["kategorie"], "kultur")
        self.assertEqual(e["quelle_url"], DETAIL_URL)
        self.assertTrue(e["bild_url"].startswith("https://kulturamt-neuss.de/wp-content/uploads/"))
        self.assertIsNone(e["beschreibung"])

    def test_anderer_spielort_und_zeitfenster(self):
        anderswo = DETAIL.replace(">Globe Neuss<", ">Stadtgarten Neuss<")
        self.assertEqual(modul._termine_aus_detail(anderswo, DETAIL_URL, date(2026, 1, 1), date(2026, 12, 31)), [])
        self.assertEqual(modul._termine_aus_detail(DETAIL, DETAIL_URL, date(2026, 11, 25), date(2027, 11, 25)), [])

    def test_ticket_link(self):
        mit_ticket = DETAIL.replace(
            '<div class="brxe-diovbg brxe-div dates-grid-item__links"></div>',
            '<div class="brxe-diovbg brxe-div dates-grid-item__links"><a class="dates-grid-item__link" '
            'href="https://tickets.kulturamt-neuss.de/webshop/webticket/shop?event=2000">Tickets</a></div>')
        e = modul._termine_aus_detail(mit_ticket, DETAIL_URL, date(2026, 1, 1), date(2026, 12, 31))[0]
        self.assertEqual(e["ticket_url"], "https://tickets.kulturamt-neuss.de/webshop/webticket/shop?event=2000")

    def test_scrape_saisonal_info_statt_warnung(self):
        with mock.patch.object(modul, "seite_abrufen", return_value=PROGRAMM), \
                self.assertLogs(modul.logger, level=logging.INFO) as log:
            self.assertEqual(modul.scrape(), [])
        self.assertTrue(any("saison" in z.lower() for z in log.output))
        self.assertFalse(any(z.startswith(("WARNING", "ERROR")) for z in log.output))


if __name__ == "__main__":
    unittest.main()
