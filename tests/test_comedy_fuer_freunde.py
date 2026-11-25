"""Tests für den Scraper Comedy für Freunde (JSON-LD + MEC-Liste, ohne Netz).
python -m unittest tests.test_comedy_fuer_freunde"""
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import comedy_fuer_freunde as modul

FIXTURE = Path(__file__).parent / "fixtures" / "comedy_fuer_freunde_duesseldorf.html"
HEUTE, ENDE = date(2026, 11, 25), date(2027, 3, 25)
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class SeiteTest(unittest.TestCase):
    def setUp(self):
        self.html = FIXTURE.read_text(encoding="utf-8")
        self.events = modul._termine_aus_html(self.html, HEUTE, ENDE)

    def test_felder(self):
        self.assertEqual(len(self.events), 1)
        e = self.events[0]
        self.assertEqual(e["titel"], "Profi-Testbühne")
        # JSON-LD sagt 21:00 (MEC-Zeitzonenfehler), sichtbar und laut Beschreibung 20:00
        self.assertEqual((e["datum"], e["uhrzeit"]), ("2026-11-30", "20:00"))
        self.assertEqual(e["ort"], "Comedy für Freunde Club Düsseldorf")
        self.assertEqual(e["adresse"], "Ackerstraße 109, 40233 Düsseldorf")
        self.assertEqual(e["kategorie"], "kultur")
        self.assertEqual(e["preis"], "9,99 €")
        self.assertEqual(e["quelle_url"], "https://comedy-fuer-freunde.com/duesseldorf/")
        self.assertIsNone(e["beschreibung"])
        self.assertTrue(e["bild_url"].startswith("https://comedy-fuer-freunde.com/wp-content/uploads/"))
        for feld in PFLICHT:
            self.assertTrue(e[feld], f"{feld} leer")

    def test_ticket_link_aus_html(self):
        e = self.events[0]
        self.assertTrue(e["ticket_url"].startswith("https://www.weezevent.com/widget_billeterie.php?"))
        self.assertIn("occurrence=2026-11-30", e["ticket_url"])
        self.assertNotIn("&amp;", e["ticket_url"])
        self.assertNotEqual(e["ticket_url"], e["quelle_url"])

    def test_andere_stadt_weg(self):
        html = self.html.replace('"name": "Düsseldorf"', '"name": "Köln"').replace(
            '<div class="mec-event-loc-place">Düsseldorf</div>', '<div class="mec-event-loc-place">Köln</div>')
        self.assertEqual(modul._termine_aus_html(html, HEUTE, ENDE), [])

    def test_fenster(self):
        self.assertEqual(modul._termine_aus_html(self.html, date(2026, 12, 1), ENDE), [])
        self.assertEqual(modul._termine_aus_html(self.html, HEUTE, date(2026, 11, 29)), [])

    def test_ohne_jsonld_ersatz_liste(self):
        ohne = self.html.split("</head>", 1)[1]
        events = modul._termine_aus_html(ohne, HEUTE, ENDE)
        self.assertEqual([(e["datum"], e["uhrzeit"]) for e in events], [("2026-11-30", "20:00")])


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
        self.assertEqual(len(events), 1)
        self.assertEqual(abruf.call_count, 1)
        self.assertNotIn("weezevent", abruf.call_args[0][0])  # Widget wird nie abgerufen

    def test_scrape_wirft_nie(self):
        with mock.patch.object(modul, "seite_abrufen", side_effect=RuntimeError("kaputt")):
            self.assertEqual(modul.scrape(), [])


if __name__ == "__main__":
    unittest.main()
