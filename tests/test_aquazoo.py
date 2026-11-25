"""
test_aquazoo.py – Tests für scraper/tier2/aquazoo.py ohne Netz.
Fixture: tests/fixtures/aquazoo_events.json (Antwort von /api/events/list?type=upcoming&all_websites=1 vom
25.11.2026, gekürzt auf 14 Einträge, ohne das Feld „debug“).
"""
import json
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import aquazoo as modul

FIXTURE = Path(__file__).parent / "fixtures" / "aquazoo_events.json"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


class TestAquazoo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daten = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.events = modul._termine_aus_api(cls.daten, date(2026, 11, 25), date(2027, 3, 25))

    def test_anzahl_und_pflichtfelder(self):
        self.assertEqual(len(self.events), 11)
        for e in self.events:
            for feld in ("titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "quelle_name", "quelle_url",
                         "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertTrue(e["quelle_url"].startswith("https://aquazoo-duesseldorf.de/veranstaltungen/"))
            self.assertEqual((e["ort"], e["adresse"]),
                             ("Aquazoo Löbbecke Museum", "Kaiserswerther Str. 380, 40474 Düsseldorf"))
            self.assertEqual(e["quelle_name"], "Aquazoo Löbbecke Museum")
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])
            self.assertTrue(e["bild_url"].startswith("https://aquazoo-duesseldorf.de/media/"))

    def test_abendfuehrung(self):
        e = self.events[0]
        self.assertEqual(e["titel"], "Tierisch anders - Geschlechterrollen im Tierreich")
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"], e["preis"]),
                         ("2026-11-25", "18:30", "kultur", None))

    def test_infotisch_familie(self):
        e = next(e for e in self.events if e["titel"] == "Zeigt her eure Zähne!")
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2026-12-05", "11:00", "family"))

    def test_kostenfreie_fuehrung(self):
        e = next(e for e in self.events if e["titel"] == "Führung am Evolutionsweg")
        self.assertEqual((e["datum"], e["uhrzeit"], e["preis"]), ("2026-12-06", "13:00", "kostenlos"))

    def test_tagung_ausgelassen(self):
        self.assertFalse(any("Regionaltreffen" in e["titel"] for e in self.events))

    def test_doppelter_termin_nur_einmal(self):
        alle = modul._termine_aus_api(self.daten, date(2026, 11, 25), date(2027, 12, 31))
        juli = [e for e in alle if e["datum"] == "2027-07-04" and e["titel"] == "Das Tier in Dir!"]
        self.assertEqual(len(juli), 1)

    def test_beginn(self):
        self.assertEqual(modul._beginn("11 – 13.30 Uhr", "11:00:00"), "11:00")
        self.assertEqual(modul._beginn("", "15:00:00"), "15:00")
        self.assertIsNone(modul._beginn(None, None))


if __name__ == "__main__":
    unittest.main()
