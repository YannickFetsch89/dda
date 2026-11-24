"""
test_insel_hombroich.py – Tests für scraper/tier2/insel_hombroich.py ohne Netz.
Fixture: tests/fixtures/insel_hombroich_events.json (Auszug aus der Tribe-API vom 24.11.2026, gekürzt).
"""
import json
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import insel_hombroich as modul

FIXTURE = Path(__file__).parent / "fixtures" / "insel_hombroich_events.json"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


def _roh() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["events"]


class TestInselHombroich(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = modul._termine_aus_api(_roh(), date(2025, 1, 1), date(2027, 12, 31))
        cls.nach_titel = {e["titel"]: e for e in cls.events}

    def test_anzahl_und_pflichtfelder(self):
        self.assertEqual(len(self.events), 9)
        for e in self.events:
            for feld in ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertTrue(e["quelle_url"].startswith("https://www.inselhombroich.de/"))
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])
            self.assertEqual(e["quelle_name"], "Insel Hombroich")

    def test_konzert_raketenstation(self):
        e = self.nach_titel["Konzert: Leonkoro Quartett"]
        self.assertEqual(e["datum"], "2025-09-28")
        self.assertEqual(e["uhrzeit"], "11:00")
        self.assertEqual(e["ort"], "Raketenstation Hombroich")
        self.assertEqual(e["adresse"], "Raketenstation Hombroich 4, 41472 Neuss")
        self.assertEqual(e["kategorie"], "musik")

    def test_doppelter_eintrag_nur_einmal(self):
        self.assertEqual(sum(1 for e in self.events if e["titel"] == "Konzert: Leonkoro Quartett"), 1)

    def test_museum_und_familie(self):
        e = next(e for e in self.events if e["titel"].startswith("Das Dschungelfest"))
        self.assertEqual(e["ort"], "Museum Insel Hombroich")
        self.assertEqual(e["adresse"], "Minkel 2, 41472 Neuss")
        self.assertEqual(e["kategorie"], "family")

    def test_fuehrung_kultur(self):
        e = self.nach_titel["Führungen im Thomas Kling Archiv"]
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2026-12-04", "15:00", "kultur"))
        self.assertEqual(e["ort"], "Raketenstation Hombroich")

    def test_mehrtaegig_ganztags(self):
        e = self.nach_titel["20. Inselfestival"]
        self.assertIsNone(e["uhrzeit"])
        self.assertEqual(e["datum_bis"], "2025-06-09")

    def test_englisch_und_ausstellungen_ausgelassen(self):
        titel = " ".join(self.nach_titel)
        self.assertNotIn("Guided tours", titel)
        self.assertNotIn("Wachhaus", titel)
        self.assertNotIn("Was Jetzt Ist", titel)
        self.assertNotIn("Skulpturenhalle", titel)

    def test_zeitfenster(self):
        events = modul._termine_aus_api(_roh(), date(2026, 11, 24), date(2027, 3, 24))
        self.assertEqual([e["titel"] for e in events], ["Führungen im Thomas Kling Archiv"])

    def test_ort_regel(self):
        self.assertEqual(modul._ort_und_adresse({"venue": [{"venue": "Siza-Pavillon, Raketenstation"}]})[0],
                         "Raketenstation Hombroich")
        self.assertEqual(modul._ort_und_adresse({"venue": []})[0], "Museum Insel Hombroich")
        self.assertIsNone(modul._ort_und_adresse({"venue": {"venue": "Langen Foundation"}}))


if __name__ == "__main__":
    unittest.main()
