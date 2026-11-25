"""
test_hetjens.py – Tests für scraper/tier2/hetjens.py ohne Netz.
Fixture: tests/fixtures/hetjens_events.json (Antwort von /api/events/list?type=upcoming&all_websites=1 vom
25.11.2026, gekürzt: nur 3 der 86 Sonntags-Suchspiele, ohne das Feld „debug“).
"""
import json
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import hetjens as modul

FIXTURE = Path(__file__).parent / "fixtures" / "hetjens_events.json"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


class TestHetjens(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daten = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.events = modul._termine_aus_api(cls.daten, date(2026, 11, 25), date(2027, 3, 25))

    def test_anzahl_und_pflichtfelder(self):
        self.assertEqual(len(self.events), 13)
        for e in self.events:
            for feld in ("titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "quelle_name", "quelle_url",
                         "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertTrue(e["quelle_url"].startswith("https://hetjensmuseum.de/programm/"))
            self.assertEqual((e["ort"], e["adresse"]),
                             ("Hetjens - Deutsches Keramikmuseum", "Schulstraße 4, 40213 Düsseldorf"))
            self.assertEqual(e["quelle_name"], "Hetjens-Museum")
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])

    def test_suchspiel_ausgelassen(self):
        self.assertFalse(any("Suchspiel" in e["titel"] for e in self.events))

    def test_eroeffnung(self):
        e = next(e for e in self.events if e["titel"].startswith("Eröffnung"))
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"], e["preis"]),
                         ("2026-12-02", "18:30", "kultur", "kostenlos"))

    def test_kurs_ausgebucht_bleibt(self):
        kurs = [e for e in self.events if e["titel"] == "Drehkurs an der Töpferscheibe"]
        self.assertEqual([e["datum"] for e in kurs], ["2026-11-25", "2026-12-02"])
        self.assertEqual(kurs[0]["kategorie"], "community")
        self.assertIn("AUSGEBUCHT", kurs[0]["preis"])

    def test_beginn_aus_zeittext_statt_start_time(self):
        # „15:30-17:30 Uhr“ mit start_time 17:30:00 → Beginn 15:30
        zeiten = sorted(e["uhrzeit"] for e in self.events
                        if e["titel"] == "Malerei-Workshop mit Matthias Dotschko" and e["datum"] == "2027-02-20")
        self.assertEqual(zeiten, ["12:30", "15:30"])

    def test_zeitfenster(self):
        events = modul._termine_aus_api(self.daten, date(2027, 1, 1), date(2027, 1, 31))
        self.assertEqual([e["datum"] for e in events], ["2027-01-27"])


if __name__ == "__main__":
    unittest.main()
