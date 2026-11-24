"""Tests für den Scraper Theater an der Kö (ohne Netz).
python -m unittest tests.test_theater_an_der_koe"""
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import theater_an_der_koe as modul

FIXTURE = Path(__file__).parent / "fixtures" / "theater_an_der_koe_spielplan.html"
HEUTE, ENDE = date(2026, 11, 24), date(2027, 11, 24)
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class SpielplanTest(unittest.TestCase):
    def setUp(self):
        self.html = FIXTURE.read_text(encoding="utf-8")
        self.events = modul._termine_aus_html(self.html, HEUTE, ENDE)

    def test_felder(self):
        self.assertEqual(len(self.events), 5)
        e = self.events[0]
        self.assertEqual((e["titel"], e["datum"], e["uhrzeit"]), ("ERBE GUT - ALLES GUT", "2026-11-27", "20:00"))
        self.assertEqual(e["ort"], "Theater an der Kö")
        self.assertEqual(e["adresse"], "Schadowstraße 11, 40212 Düsseldorf")
        self.assertEqual(e["kategorie"], "kultur")
        self.assertTrue(e["quelle_url"].startswith("https://theateranderkoe.de/spielplan/theaterstuecke/erbe-gut"))
        self.assertTrue(e["bild_url"].startswith("https://theateranderkoe.de/fileadmin/"))
        self.assertIsNone(e["beschreibung"])
        self.assertFalse(e["bild_generiert"])
        for ev in self.events:
            for feld in PFLICHT:
                self.assertTrue(ev[feld], f"{feld} leer")
            self.assertTrue(ev["quelle_url"].startswith("https://"))

    def test_gastspiel_und_letzter_termin(self):
        termine = {(e["titel"], e["datum"], e["uhrzeit"]) for e in self.events}
        self.assertIn(("DISTEL - STADT LAND SOCKENSCHUSS", "2026-11-30", "20:00"), termine)
        self.assertIn(("YES, WE CAMP", "2027-06-27", "17:00"), termine)

    def test_zeitfenster(self):
        nur_november = modul._termine_aus_html(self.html, HEUTE, date(2026, 11, 30))
        self.assertEqual({e["datum"] for e in nur_november}, {"2026-11-27", "2026-11-28", "2026-11-29", "2026-11-30"})
        self.assertEqual(modul._termine_aus_html(self.html, date(2027, 7, 1), date(2028, 7, 1)), [])

    def test_doppelte_und_abgesagt(self):
        inhalt = self.html.split("<body>")[1].split("</body>")[0]
        doppelt = self.html.replace("</body>", inhalt + "</body>")
        self.assertEqual(len(modul._termine_aus_html(doppelt, HEUTE, ENDE)), 5)
        abgesagt = self.html.replace('<div class="ts_play_info_info">', '<div class="ts_play_info_info">ABGESAGT', 1)
        self.assertEqual(len(modul._termine_aus_html(abgesagt, HEUTE, ENDE)), 4)

    def test_scrape_wirft_nie(self):
        with mock.patch.object(modul, "seite_abrufen", return_value=None):
            self.assertEqual(modul.scrape(), [])
        with mock.patch.object(modul, "seite_abrufen", side_effect=RuntimeError("kaputt")):
            self.assertEqual(modul.scrape(), [])
        with mock.patch.object(modul, "seite_abrufen", return_value=self.html):
            self.assertIsInstance(modul.scrape(), list)


if __name__ == "__main__":
    unittest.main()
