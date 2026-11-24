"""Tests für den Scraper Savoy Theater (admin-ajax-Antwort, ohne Netz).
python -m unittest tests.test_savoy_theater"""
import json
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import savoy_theater as modul

FIXTURE = Path(__file__).parent / "fixtures" / "savoy_theater_ajax.json"
HEUTE, ENDE = date(2026, 11, 24), date(2027, 11, 24)
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class ListeTest(unittest.TestCase):
    def setUp(self):
        self.antwort = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.events = modul._termine_aus_html(self.antwort["html"], HEUTE, ENDE)

    def test_felder(self):
        # 4 Boxen im Auszug, eine davon in der Mitsubishi Electric Halle → 3
        self.assertEqual(len(self.events), 3)
        e = self.events[1]
        self.assertEqual(e["titel"], "Jan van Weyde – Immer Weyder!")
        self.assertEqual((e["datum"], e["uhrzeit"]), ("2026-11-26", "20:00"))
        self.assertEqual(e["ort"], "Savoy Theater")
        self.assertEqual(e["adresse"], "Graf-Adolf-Straße 47, 40215 Düsseldorf")
        self.assertEqual(e["kategorie"], "kultur")
        self.assertEqual(e["quelle_url"], "https://savoy-theater.de/")
        self.assertTrue(e["bild_url"].startswith("https://savoy-theater.de/wp-content/uploads/"))
        self.assertIsNone(e["beschreibung"])
        for ev in self.events:
            for feld in PFLICHT:
                self.assertTrue(ev[feld], f"{feld} leer")

    def test_fremder_spielort_weg(self):
        self.assertNotIn("Paul Panzer", " ".join(e["titel"] for e in self.events))

    def test_kategorie(self):
        nach_titel = {e["titel"]: e["kategorie"] for e in self.events}
        self.assertEqual(nach_titel["WDR4 sing(t) mit Guildo Horn"], "musik")
        self.assertEqual(modul._kategorie("Tom Gaebel & His Orchestra", "A Swinging Christmas", ""), "musik")
        self.assertEqual(modul._kategorie("Hagen Rether", "Liebe", "Der Kabarettist spricht über Musik"), "kultur")
        self.assertEqual(modul._kategorie("Mirja Boes", "Carpfe Diem", "Comedy pur"), "kultur")
        self.assertEqual(modul._kategorie("Berlin Comedian Harmonists", "Morgen, Kinder", ""), "musik")
        self.assertEqual(modul._kategorie("EOFT", "European Outdoor Film Tour Filmfestival", ""), "kultur")

    def test_titel_mit_doppelpunkt(self):
        html = self.antwort["html"].replace("Jan van Weyde</div>", "GRENZGANG Live-Show:</div>", 1)
        titel = [e["titel"] for e in modul._termine_aus_html(html, HEUTE, ENDE)]
        self.assertIn("GRENZGANG Live-Show: Immer Weyder!", titel)

    def test_abgesagt_weg(self):
        html = self.antwort["html"].replace("ticket-button buchbar", "ticket-button abgesagt", 2)
        self.assertEqual(len(modul._termine_aus_html(html, HEUTE, ENDE)), 2)

    def test_scrape_blaettert_mit_limit(self):
        seiten = []

        def holen(client, seite):
            seiten.append(seite)
            return dict(self.antwort, max_page=40)

        with mock.patch.object(modul, "_seite_holen", side_effect=holen):
            events = modul.scrape()
        self.assertLessEqual(len(seiten), modul.MAX_SEITEN)
        schluessel = [(e["titel"], e["datum"], e["uhrzeit"]) for e in events]
        self.assertEqual(len(schluessel), len(set(schluessel)))

    def test_scrape_wirft_nie(self):
        with mock.patch.object(modul, "_seite_holen", return_value=None):
            self.assertEqual(modul.scrape(), [])
        with mock.patch.object(modul, "_seite_holen", side_effect=RuntimeError("kaputt")):
            self.assertEqual(modul.scrape(), [])


if __name__ == "__main__":
    unittest.main()
