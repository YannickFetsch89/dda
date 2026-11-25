"""
test_philara.py – Tests für scraper/tier2/philara.py ohne Netz.
Fixture: tests/fixtures/philara_programm.html (8 Einträge der Programmseite vom 25.11.2026: drei kommende Termine,
dazu ältere Einträge mit schwierigen Datumsangaben und einem Reservix-Link).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import philara as modul

FIXTURE = Path(__file__).parent / "fixtures" / "philara_programm.html"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


class TestPhilara(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = FIXTURE.read_text(encoding="utf-8")
        cls.events = modul._termine_aus_html(cls.html, date(2026, 11, 25), date(2027, 3, 25))
        cls.alle = modul._termine_aus_html(cls.html, date(2022, 1, 1), date(2027, 12, 31))

    def test_kommende_termine_und_pflichtfelder(self):
        self.assertEqual(len(self.events), 4)
        for e in self.events:
            for feld in ("titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "quelle_name", "quelle_url",
                         "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertTrue(e["quelle_url"].startswith("https://philara.de/de/"))
            self.assertEqual((e["ort"], e["adresse"]), ("Sammlung Philara", "Birkenstraße 47a, 40233 Düsseldorf"))
            self.assertEqual(e["quelle_name"], "Sammlung Philara")
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])
            self.assertTrue(e["bild_url"].startswith("https://philara.de/sites/default/files/"))

    def test_fuehrung(self):
        e = next(e for e in self.events if e["datum"] == "2026-12-12")
        self.assertEqual((e["uhrzeit"], e["kategorie"], e["preis"]), ("16:00", "kultur", "kostenlos"))
        self.assertEqual(e["quelle_url"], "https://philara.de/de/ekskursiya-ukrainskoyu-movoyu-0")

    def test_zwei_termine_in_einem_eintrag(self):
        # „6.12 und 13.12.2026“, 15:00-17:00
        basteln = [e for e in self.events if e["titel"] == "Offene Basteltische im Dezember"]
        self.assertEqual([e["datum"] for e in basteln], ["2026-12-06", "2026-12-13"])
        self.assertTrue(all(e["uhrzeit"] == "15:00" and e["kategorie"] == "family" for e in basteln))

    def test_familienfuehrung_zeit_mit_leerzeichen(self):
        e = next(e for e in self.events if e["titel"] == "HOUSE OF BALAGAN")
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2026-12-05", "14:00", "family"))

    def test_mehrere_tage_ohne_monat(self):
        # „6. & 8.7, 22. & 24.9.2026“
        kunst = sorted(e["datum"] for e in self.alle if e["titel"].startswith('"Kunst"'))
        self.assertEqual(kunst, ["2026-07-06", "2026-07-08", "2026-09-22", "2026-09-24"])

    def test_zeitraum(self):
        e = next(e for e in self.alle if e["titel"] == "WINTERMARKT")
        self.assertEqual((e["datum"], e["datum_bis"], e["uhrzeit"]), ("2024-12-05", "2024-12-08", "16:00"))

    def test_eigene_zeit_je_datum(self):
        social = sorted((e["datum"], e["uhrzeit"]) for e in self.alle if e["titel"] == "Social Fiction")
        self.assertEqual(social, [("2023-08-20", "11:00"), ("2023-09-20", "18:00")])

    def test_reservix_ticket(self):
        e = next(e for e in self.alle if e["titel"] == "Windrosen & Gläserspiel")
        self.assertTrue(e["ticket_url"].startswith("https://ido-festival.reservix.de/"))
        self.assertEqual(e["kategorie"], "musik")
        self.assertIn("€", e["preis"])

    def test_beginn(self):
        self.assertEqual(modul._beginn("14 - 18 Uhr"), "14:00")
        self.assertEqual(modul._beginn("ab 17:30"), "17:30")
        self.assertIsNone(modul._beginn("10:41"))


if __name__ == "__main__":
    unittest.main()
