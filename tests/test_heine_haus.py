"""Tests für den Scraper Heine Haus Literaturhaus (Startseite, ohne Netz).
python -m unittest tests.test_heine_haus"""
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import heine_haus as modul

FIXTURE = Path(__file__).parent / "fixtures" / "heine_haus_start.html"
HEUTE, ENDE = date(2026, 11, 25), date(2027, 3, 25)
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class StartseiteTest(unittest.TestCase):
    def setUp(self):
        self.html = FIXTURE.read_text(encoding="utf-8")
        self.events = modul._termine_aus_html(self.html, HEUTE, ENDE)

    def test_nur_kuenftige(self):
        # Seite listet auch alte Beiträge (Januar/Februar 2026) und den 24.11.2026 – nur ab heute
        self.assertEqual([e["datum"] for e in self.events], ["2026-12-02", "2026-12-08"])

    def test_felder(self):
        e = self.events[1]
        self.assertEqual(e["titel"], "Flurina Badel. Nebelflüchtige")
        self.assertEqual((e["datum"], e["uhrzeit"]), ("2026-12-08", "19:30"))
        self.assertEqual(e["ort"], "Heine Haus Literaturhaus Düsseldorf")
        self.assertEqual(e["adresse"], "Bolkerstraße 53, 40213 Düsseldorf")
        self.assertEqual(e["kategorie"], "kultur")
        self.assertTrue(e["quelle_url"].startswith("https://www.heinehaus.de/index.php/2026/"))
        self.assertIsNone(e["beschreibung"])
        self.assertIsNone(e["ticket_url"])
        for ev in self.events:
            for feld in PFLICHT:
                self.assertTrue(ev[feld], f"{feld} leer")
        self.assertEqual(self.events[0]["uhrzeit"], "18:30")

    def test_slider_nicht_doppelt(self):
        # 08.12. steht im Slider und als Beitrag → einmal, mit der Beitrags-URL
        am_8 = [e for e in self.events if e["datum"] == "2026-12-08"]
        self.assertEqual(len(am_8), 1)
        self.assertNotEqual(am_8[0]["quelle_url"], modul.START_URL)

    def test_ausser_haus_weg(self):
        alle = modul._termine_aus_html(self.html, date(2026, 1, 1), ENDE)
        titel = " ".join(e["titel"] for e in alle)
        self.assertNotIn("Christoph Geiser", titel)  # „Außer Haus: 16.11.2026 …“
        self.assertIn("Esther Kinsky", titel)          # nur im Slider → Startseite als quelle_url
        jocks = [e for e in alle if e["titel"] == "Literatur-Lesen mit Heinz-Norbert Jocks"]
        self.assertEqual(jocks[0]["uhrzeit"], "11:00")  # „Do. 11:00 bis 13:00 Uhr“

    def test_termin_helfer(self):
        self.assertEqual(modul._termin("16.11.2026, Mo, 19:00 Uhr")[:2], (date(2026, 11, 16), "19:00"))
        self.assertEqual(modul._termin("02.12.2026, Mi., 18:30 Uhr")[:2], (date(2026, 12, 2), "18:30"))
        self.assertIsNone(modul._termin("ohne Datum"))


class ScrapeTest(unittest.TestCase):
    def test_scrape_ohne_netz(self):
        html = FIXTURE.read_text(encoding="utf-8")

        class Heute(date):
            @classmethod
            def today(cls):
                return HEUTE

        with mock.patch.object(modul, "seite_abrufen", return_value=html) as abruf, \
                mock.patch.object(modul, "vorschau_ende", lambda q, h: ENDE), \
                mock.patch.object(modul, "date", Heute):
            events = modul.scrape()
        self.assertEqual(len(events), 2)
        self.assertEqual(abruf.call_count, 1)
        self.assertNotIn("my-calendar-ics", abruf.call_args[0][0])

    def test_scrape_wirft_nie(self):
        with mock.patch.object(modul, "seite_abrufen", side_effect=RuntimeError("kaputt")):
            self.assertEqual(modul.scrape(), [])


if __name__ == "__main__":
    unittest.main()
