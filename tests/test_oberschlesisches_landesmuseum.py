"""
test_oberschlesisches_landesmuseum.py – Tests für scraper/tier2/oberschlesisches_landesmuseum.py ohne Netz.
Fixture: tests/fixtures/oberschlesisches_landesmuseum.ics (Auszug aus dem MEC-iCal-Export vom 25.11.2026, gekürzt,
mit den PHP-Warnungen vor dem Kalender wie im Original).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import oberschlesisches_landesmuseum as modul

FIXTURE = Path(__file__).parent / "fixtures" / "oberschlesisches_landesmuseum.ics"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


class TestOberschlesischesLandesmuseum(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = FIXTURE.read_text(encoding="utf-8")
        cls.events = modul._termine_aus_ics(text, date(2026, 11, 25), date(2027, 11, 25))
        cls.nach_titel = {e["titel"]: e for e in cls.events}

    def test_anzahl_und_pflichtfelder(self):
        # 8 Einträge im Auszug: 1 vergangener, 1 außer Haus (#oslmontour) → 6
        self.assertEqual(len(self.events), 6)
        for e in self.events:
            for feld in ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertEqual(e["ort"], "Oberschlesisches Landesmuseum")
            self.assertEqual(e["adresse"], "Bahnhofstraße 62, 40883 Ratingen")
            self.assertTrue(e["quelle_url"].startswith("https://oberschlesisches-landesmuseum.de/veranstaltungen/"))
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])
            self.assertEqual(e["quelle_name"], "Oberschlesisches Landesmuseum")

    def test_werkstatt(self):
        e = next(e for e in self.events if e["titel"].startswith("Samstags im Museum: Advents-Werkstatt"))
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2026-11-28", "12:00", "community"))
        self.assertTrue(e["bild_url"].startswith("https://oberschlesisches-landesmuseum.de/wp-content/uploads/"))

    def test_fuehrung_kultur(self):
        e = next(e for e in self.events if e["titel"].startswith("Taschenlampenführung"))
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2026-12-04", "17:00", "kultur"))

    def test_fruehstueck_food(self):
        e = self.nach_titel["Osterfrühstück im Oberschlesischen Landesmuseum"]
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2027-03-21", "11:00", "food"))

    def test_fuehrung_mit_workshop_bleibt_kultur(self):
        self.assertEqual(modul._kategorie("Finissage: Öffentliche Führung durch die Sonderausstellung mit "
                                          "Weihnachtspost-Workshop"), "kultur")
        self.assertEqual(modul._kategorie("Zeit für die eigene weibliche Kraft. Lunnica-Schnupperworkshop"),
                         "community")

    def test_ausser_haus_und_vergangen_fehlen(self):
        self.assertFalse(any("oslmontour" in e["titel"] for e in self.events))
        self.assertTrue(all(e["datum"] >= "2026-11-25" for e in self.events))

    def test_zeitfenster(self):
        text = FIXTURE.read_text(encoding="utf-8")
        kurz = modul._termine_aus_ics(text, date(2026, 11, 25), date(2026, 12, 31))
        self.assertEqual(len(kurz), 3)


if __name__ == "__main__":
    unittest.main()
