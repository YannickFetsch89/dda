"""Tests für den Scraper Ratinger Hof (concertteam-Liste + Detailseite, ohne Netz).
python -m unittest tests.test_ratinger_hof"""
import json
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import ratinger_hof as modul

FIXTURES = Path(__file__).parent / "fixtures"
HEUTE, ENDE = date(2026, 11, 25), date(2027, 3, 25)


class _Heute(date):
    """date mit festem „heute“, damit der Test nicht mit der Zeit veraltet."""
    @classmethod
    def today(cls):
        return cls(2026, 11, 25)


PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class ListeTest(unittest.TestCase):
    def setUp(self):
        self.daten = json.loads((FIXTURES / "ratinger_hof_liste.json").read_text(encoding="utf-8"))
        self.events = modul._termine_aus_liste(self.daten, HEUTE, ENDE)

    def test_felder(self):
        # 8 Einträge: 1 hinter dem Fensterende (Okt. 2027), 1 abgesagt, 1 fremder Ort → 5
        self.assertEqual(len(self.events), 5)
        e = self.events[0]
        self.assertEqual((e["titel"], e["datum"]), ("Ohrenfeindt", "2026-11-27"))
        self.assertEqual(e["ort"], "Ratinger Hof Düsseldorf")
        self.assertEqual(e["adresse"], "Ratinger Str. 10, 40213 Düsseldorf")
        self.assertEqual(e["kategorie"], "musik")
        self.assertEqual(e["quelle_url"], "https://www.concertteam.de/events/ohrenfeindt-2026-11-27")
        self.assertTrue(e["bild_url"].startswith("https://www.concertteam.de/media/"))
        self.assertIsNone(e["beschreibung"])
        self.assertFalse(e["bild_generiert"])
        for ev in self.events:
            for feld in PFLICHT:
                self.assertTrue(ev[feld], f"{feld} leer")
            self.assertTrue(ev["quelle_url"].startswith("https://"))

    def test_abgesagt_und_fremder_ort_weg(self):
        titel = [e["titel"] for e in self.events]
        self.assertNotIn("Ninamarie", titel)          # abgesagt
        self.assertNotIn("Alex Henry Foster", titel)  # Ort „Live Music Hall“
        self.assertNotIn("Drunken Swallows", titel)   # nach dem Fensterende

    def test_kategorie(self):
        nach_titel = {e["titel"]: e["kategorie"] for e in self.events}
        self.assertEqual(nach_titel["Die Toten Hosen Party"], "nightlife")
        self.assertEqual(nach_titel["DJ-Battle"], "nightlife")
        self.assertEqual(nach_titel["GLAM BANG!"], "nightlife")   # Slug „glam-bang-silvester-ball“
        self.assertEqual(nach_titel["The Spitfires"], "musik")


class DetailTest(unittest.TestCase):
    def test_beginn_preis_ticket(self):
        html = (FIXTURES / "ratinger_hof_detail.html").read_text(encoding="utf-8")
        d = modul._details_aus_html(html, "https://www.concertteam.de/events/the-spitfires-2026-12-06")
        self.assertEqual(d["uhrzeit"], "20:00")   # Beginn, nicht Einlass 19:00
        self.assertEqual(d["preis"], "22,88 €")
        self.assertTrue(d["ticket_url"].startswith("https://www.eventim-light.com/"))

    def test_ohne_beginn_einlass(self):
        html = (FIXTURES / "ratinger_hof_detail.html").read_text(encoding="utf-8").replace(">Beginn<", ">Ende<")
        self.assertEqual(modul._details_aus_html(html, "https://www.concertteam.de/")["uhrzeit"], "19:00")


class ScrapeTest(unittest.TestCase):
    def test_scrape_mit_details(self):
        daten = json.loads((FIXTURES / "ratinger_hof_liste.json").read_text(encoding="utf-8"))
        html = (FIXTURES / "ratinger_hof_detail.html").read_text(encoding="utf-8")
        with mock.patch.object(modul, "_liste_holen", return_value=daten), \
                mock.patch.object(modul, "seite_abrufen", return_value=html), \
                mock.patch.object(modul, "date", _Heute):
            events = modul.scrape()
        self.assertTrue(events)
        self.assertTrue(all(e["uhrzeit"] == "20:00" for e in events))
        self.assertTrue(all(e["ticket_url"] != e["quelle_url"] for e in events))

    def test_scrape_wirft_nie(self):
        with mock.patch.object(modul, "_liste_holen", side_effect=RuntimeError("kaputt")):
            self.assertEqual(modul.scrape(), [])
        with mock.patch.object(modul, "_liste_holen", return_value={"items": []}):
            self.assertEqual(modul.scrape(), [])


if __name__ == "__main__":
    unittest.main()
