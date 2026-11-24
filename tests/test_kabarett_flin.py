"""Tests für den Scraper KaBARett FLiN (Spielplan-Widget, ohne Netz).
python -m unittest tests.test_kabarett_flin"""
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import kabarett_flin as modul

FIXTURE = Path(__file__).parent / "fixtures" / "kabarett_flin_widget.html"
HEUTE, ENDE = date(2026, 11, 24), date(2027, 11, 24)
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class WidgetTest(unittest.TestCase):
    def setUp(self):
        self.html = FIXTURE.read_text(encoding="utf-8")
        self.events = modul._termine_aus_html(self.html, HEUTE, ENDE)

    def test_felder(self):
        # 4 Termine im Auszug: normal, ausverkauft, verlegt (alter Termin), abgesagt → 2 bleiben
        self.assertEqual(len(self.events), 2)
        e = self.events[0]
        self.assertEqual(e["titel"], "Heinz Gröning – Verschollen im Weihnachtsstollen 26.0")
        self.assertEqual((e["datum"], e["uhrzeit"]), ("2026-11-25", "20:00"))
        self.assertEqual(e["ort"], "KaBARett FLiN")
        self.assertEqual(e["adresse"], "Ludenberger Str. 37, 40629 Düsseldorf")
        self.assertEqual(e["kategorie"], "kultur")
        self.assertEqual(e["preis"], "EUR 33,00 / 30,00 (ermäßigt)")
        self.assertEqual(e["quelle_url"], "https://www.kabarett-flin.de/spielplan-und-tickets")
        self.assertIsNone(e["bild_url"])   # Bilder liegen beim Ticketdienstleister
        self.assertIsNone(e["beschreibung"])
        for ev in self.events:
            for feld in PFLICHT:
                self.assertTrue(ev[feld], f"{feld} leer")

    def test_ausverkauft_bleibt_verlegt_und_abgesagt_weg(self):
        daten = {e["datum"] for e in self.events}
        self.assertIn("2026-11-26", daten)        # ausverkauft
        self.assertNotIn("2026-12-09", daten)     # verlegt
        self.assertNotIn("2027-02-20", daten)     # abgesagt

    def test_fremder_ort_weg(self):
        html = self.html.replace('<span class="klive-city">Düsseldorf</span>', '<span class="klive-city">Wuppertal</span>', 1)
        self.assertEqual(len(modul._termine_aus_html(html, HEUTE, ENDE)), 1)

    def test_zeitfenster(self):
        self.assertEqual(len(modul._termine_aus_html(self.html, date(2026, 11, 26), ENDE)), 1)

    def test_scrape_wartet_crawl_delay(self):
        with mock.patch.object(modul, "seite_abrufen", return_value=self.html) as abruf:
            self.assertIsInstance(modul.scrape(), list)
        self.assertEqual(abruf.call_args.kwargs.get("wartezeit"), 10.0)
        with mock.patch.object(modul, "seite_abrufen", return_value=None):
            self.assertEqual(modul.scrape(), [])
        with mock.patch.object(modul, "seite_abrufen", side_effect=RuntimeError("kaputt")):
            self.assertEqual(modul.scrape(), [])


if __name__ == "__main__":
    unittest.main()
