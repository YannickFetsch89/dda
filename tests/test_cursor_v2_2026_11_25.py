"""Tests zur Cursor-Prüfung V2 (Welle B, 25.11.2026): HdU nur mit gelesener Detailseite, LVR ohne Shop-Startseite,
RSH nur eigene Säle als Haus. python -m unittest tests.test_cursor_v2_2026_11_25"""
import unittest
from datetime import date, timedelta
from unittest import mock

from scraper.tier2 import haus_der_universitaet as hdu
from scraper.tier2 import rsh_hochschule as rsh


class HduTest(unittest.TestCase):
    def test_ohne_detailseite_kein_termin(self):
        tag = (date.today() + timedelta(days=5)).isoformat()
        roh = [{"titel": "Vortrag A", "datum": tag, "uhrzeit": "18:00", "quelle_url": "https://www.hdu.hhu.de/a"},
               {"titel": "Vortrag B", "datum": tag, "uhrzeit": "19:00", "quelle_url": "https://www.hdu.hhu.de/b"}]
        antworten = {hdu.KALENDER_URL: "<html>Liste</html>", "https://www.hdu.hhu.de/a": None, "https://www.hdu.hhu.de/b": "<html>B</html>"}
        with mock.patch.object(hdu, "seite_abrufen", side_effect=lambda url, *a, **k: antworten.get(url)), \
                mock.patch.object(hdu, "_termine_aus_liste", side_effect=[roh, []]), \
                mock.patch.object(hdu, "_naechste_seite", return_value=None), \
                mock.patch.object(hdu, "_details_ergaenzen", return_value=True):
            events = hdu.scrape()
        self.assertEqual([e["titel"] for e in events], ["Vortrag B"])


class RshOrtTest(unittest.TestCase):
    def test_nur_eigene_saele(self):
        self.assertEqual(rsh._ort_und_adresse("Partika-Saal")[0], rsh.ORT_HAUS)
        self.assertEqual(rsh._ort_und_adresse("")[0], rsh.ORT_HAUS)
        self.assertEqual(rsh._ort_und_adresse("Robert Schumann Hochschule, Raum 1.25")[0], rsh.ORT_HAUS)
        self.assertIsNone(rsh._ort_und_adresse("Hochschule für Musik und Tanz Köln"))
        self.assertEqual(rsh._ort_und_adresse("Robert-Schumann-Saal")[0], "Robert-Schumann-Saal")


if __name__ == "__main__":
    unittest.main()
