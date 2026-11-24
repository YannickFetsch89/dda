"""Tests für den Scraper Theater an der Luegallee (ohne Netz).
python -m unittest tests.test_theater_luegallee"""
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import theater_luegallee as modul

FIXTURE = Path(__file__).parent / "fixtures" / "theater_luegallee_kalender.html"
HEUTE, ENDE = date(2026, 11, 24), date(2027, 11, 24)
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class KalenderTest(unittest.TestCase):
    def setUp(self):
        self.html = FIXTURE.read_text(encoding="utf-8")
        self.events = modul._termine_aus_html(self.html, HEUTE, ENDE)

    def test_felder(self):
        self.assertEqual(len(self.events), 8)
        e = self.events[0]
        self.assertEqual((e["titel"], e["datum"], e["uhrzeit"]), ("Das Gasthaus an der Düssel", "2026-12-03", "20:00"))
        self.assertEqual(e["ort"], "Theater an der Luegallee")
        self.assertEqual(e["adresse"], "Burggrafenstraße 4, 40545 Düsseldorf")
        self.assertEqual(e["kategorie"], "kultur")
        self.assertEqual(e["quelle_url"], "https://theaterluegallee.de/veranstaltungen/das-gasthaus-an-der-duessel.html")
        self.assertTrue(e["bild_url"].startswith("https://theaterluegallee.de/"))
        self.assertIsNone(e["beschreibung"])
        for ev in self.events:
            for feld in PFLICHT:
                self.assertTrue(ev[feld], f"{feld} leer")

    def test_zwei_vorstellungen_am_tag_und_ausverkauft(self):
        zeiten = {(e["datum"], e["uhrzeit"]) for e in self.events if e["titel"] == "Das Gasthaus an der Düssel"}
        self.assertIn(("2026-12-05", "15:00"), zeiten)
        self.assertIn(("2026-12-05", "20:00"), zeiten)
        # ausverkaufte Vorstellungen bleiben drin
        self.assertIn(("Stollen und Plätzchen", "2026-12-06", "11:30"),
                      {(e["titel"], e["datum"], e["uhrzeit"]) for e in self.events})

    def test_abgesagt_weg(self):
        html = self.html.replace('<span class="event-status">', '<span class="event-status">abgesagt', 1)
        self.assertEqual(len(modul._termine_aus_html(html, HEUTE, ENDE)), 7)

    def test_monate_aus_menue(self):
        self.assertEqual(modul._monate_aus_html(self.html), [(2026, 11), (2026, 12), (2027, 1), (2027, 2)])

    def test_scrape_folgt_monaten(self):
        aufrufe = []

        def abruf(url, logger=None, wartezeit=2.0):
            aufrufe.append(url)
            return self.html

        with mock.patch.object(modul, "seite_abrufen", side_effect=abruf):
            events = modul.scrape()
        self.assertIsInstance(events, list)
        self.assertLessEqual(len(aufrufe), modul.MAX_SEITEN)
        # gleiche Seite mehrfach → doppelte Termine nur einmal
        schluessel = [(e["titel"], e["datum"], e["uhrzeit"]) for e in events]
        self.assertEqual(len(schluessel), len(set(schluessel)))

    def test_scrape_wirft_nie(self):
        with mock.patch.object(modul, "seite_abrufen", return_value=None):
            self.assertEqual(modul.scrape(), [])
        with mock.patch.object(modul, "seite_abrufen", side_effect=RuntimeError("kaputt")):
            self.assertEqual(modul.scrape(), [])


if __name__ == "__main__":
    unittest.main()
