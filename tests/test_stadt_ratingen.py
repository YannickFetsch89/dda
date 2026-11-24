"""
test_stadt_ratingen.py – Tests für scraper/tier2/stadt_ratingen.py ohne Netz.
Fixtures: tests/fixtures/stadt_ratingen_liste.html (erste Listenseite, auf 6 Reihen gekürzt) und
tests/fixtures/stadt_ratingen_detail.html (Detailseite „Arsène Lupin“), beide vom 24.11.2026.
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import stadt_ratingen as modul

FIXTURES = Path(__file__).parent / "fixtures"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}
HEUTE, ENDE = date(2026, 11, 24), date(2027, 3, 24)


class TestStadtRatingen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.liste = (FIXTURES / "stadt_ratingen_liste.html").read_text(encoding="utf-8")
        cls.detail = modul._details_aus_html((FIXTURES / "stadt_ratingen_detail.html").read_text(encoding="utf-8"))
        cls.reihen, cls.naechste = modul._reihen_aus_liste(cls.liste)
        arsene = next(r for r in cls.reihen if r["titel"].startswith("Arsène Lupin"))
        cls.detail["url"] = arsene["url"]
        cls.events = modul._termine_aus_html(cls.liste, HEUTE, ENDE, {cls.detail["ort"]: cls.detail})

    def test_pflichtfelder(self):
        self.assertGreaterEqual(len(self.events), 1)
        for e in self.events:
            for feld in ("titel", "datum", "ort", "kategorie", "quelle_name", "quelle_url", "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertTrue(e["quelle_url"].startswith("https://www.stadt-ratingen.de/veranstaltungskalender"))
            self.assertIsNone(e["beschreibung"])
            self.assertEqual(e["quelle_name"], "Stadt Ratingen Veranstaltungskalender")
            self.assertTrue(HEUTE.isoformat() <= e["datum"] <= ENDE.isoformat())

    def test_naechste_seite(self):
        self.assertIsNotNone(self.naechste)
        self.assertIn("%5Bpage%5D=1", self.naechste)

    def test_wochenmarkt_ausgelassen(self):
        self.assertFalse(any("Wochenmarkt" in e["titel"] for e in self.events))

    def test_theater_mit_adresse_und_mehreren_terminen(self):
        termine = [(e["datum"], e["uhrzeit"]) for e in self.events if e["titel"].startswith("Arsène Lupin")]
        self.assertEqual(termine, [("2026-11-28", "15:00"), ("2026-11-28", "19:00"), ("2026-11-29", "15:00")])
        e = next(e for e in self.events if e["titel"].startswith("Arsène Lupin"))
        self.assertEqual(e["ort"], "Aula im Schulzentrum Lintorf (Kopernikus-Gymnasium)")
        self.assertEqual(e["adresse"], "Duisburger Straße 112, 40885 Ratingen")
        self.assertEqual(e["kategorie"], "kultur")
        self.assertIn("10,00 €", e["preis"])

    def test_uhrzeit_beginn_nicht_ende(self):
        e = next(e for e in self.events if e["titel"] == "3D-Drucker für Kids")
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2026-11-24", "16:00", "family"))
        self.assertEqual(e["ort"], "Medienzentrum")

    def test_kategorien(self):
        kat = {e["titel"]: e["kategorie"] for e in self.events}
        self.assertEqual(kat["Mittagsführung"], "kultur")
        self.assertEqual(kat["Schnupperworkshop: Spinnen am Spinnrad"], "community")

    def test_fenster_wiederholung(self):
        # donnerstags vom 26.11.2026 bis 18.03.2027
        self.assertEqual(sum(1 for e in self.events if e["titel"] == "Mittagsführung"), 17)

    def test_ort_platzhalter_ausgelassen(self):
        reihe = dict(self.reihen[1], ort="Veranstaltungsort folgt")
        self.assertEqual(modul._termine_aus_reihen([reihe], HEUTE, ENDE), [])

    def test_stichwort_kategorien(self):
        def kat(titel):
            return modul._kategorie({"titel": titel, "untertitel": "", "ort": ""})
        self.assertEqual(kat("47. Ratinger Neujahrslauf"), "sport")
        self.assertEqual(kat("Duo StringBreeze"), "musik")
        self.assertEqual(kat("Kasperl, Nikolaus und die kleine Zaubermaus"), "family")
        self.assertEqual(kat("Vitamine, Mineralien & Co."), "sonstiges")

    def test_nur_ratingen(self):
        reihe = dict(self.reihen[1], stadt="Düsseldorf")
        self.assertEqual(modul._termine_aus_reihen([reihe], HEUTE, ENDE), [])


if __name__ == "__main__":
    unittest.main()
