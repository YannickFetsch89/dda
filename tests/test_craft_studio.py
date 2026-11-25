"""Tests für den Scraper The Craft Studio (mitgelesene Wix-Bookings-Antworten, ohne Netz und ohne Browser).
python -m unittest tests.test_craft_studio"""
import json
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import craft_studio as modul

FIXTURE = Path(__file__).parent / "fixtures" / "craft_studio_kalender.json"
HEUTE, ENDE = date(2026, 11, 25), date(2027, 3, 25)
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class DatenTest(unittest.TestCase):
    def setUp(self):
        self.daten = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.events = modul._termine_aus_daten(self.daten["slots"], self.daten["dienste"], HEUTE, ENDE)

    def test_felder(self):
        # 20 Termine im Auszug: 2 am 24.11. (vor heute), 1 abgesagt → 17
        self.assertEqual(len(self.events), 17)
        e = self.events[0]
        self.assertEqual(e["titel"], "Adventskranz Binden + Dip Dye Kerzen")
        self.assertEqual((e["datum"], e["uhrzeit"]), ("2026-11-26", "10:00"))
        self.assertEqual(e["ort"], "The Craft Studio DÜSSELDORF")
        self.assertEqual(e["adresse"], "Stresemannplatz 4, 40210 Düsseldorf")
        self.assertEqual(e["kategorie"], "community")
        self.assertEqual(e["preis"], "79 €")
        self.assertEqual(e["quelle_url"], "https://www.the-craftstudio.de/service-page/adventskranz-binden-dip-dye-kerzen")
        self.assertEqual(e["ticket_url"], "https://www.the-craftstudio.de/booking-calendar/adventskranz-binden-dip-dye-kerzen")
        self.assertTrue(e["bild_url"].startswith("https://static.wixstatic.com/media/"))
        self.assertIsNone(e["beschreibung"])
        for ev in self.events:
            for feld in PFLICHT:
                self.assertTrue(ev[feld], f"{feld} leer")
            self.assertNotEqual(ev["ticket_url"], ev["quelle_url"])

    def test_titel_ohne_emoji(self):
        titel = {e["titel"] for e in self.events}
        self.assertIn("Cozy Colours - Tassen bemalen", titel)
        self.assertIn("Sip & Style - Weinglas bemalen", titel)
        self.assertEqual(modul._titel("Mending Stitches x Katoy 💛"), "Mending Stitches x Katoy")
        self.assertEqual(modul._titel("⚡Spraylabz - Graffiti & Streetart Kunst"), "Spraylabz - Graffiti & Streetart Kunst")

    def test_abgesagt_weg_ausgebucht_bleibt(self):
        self.assertNotIn(("2026-12-04", "09:00"), [(e["datum"], e["uhrzeit"]) for e in self.events])
        # 26.11. 10:00 ist im Auszug ausgebucht (noRemainingCapacity) und bleibt
        self.assertIn(("2026-11-26", "10:00"), [(e["datum"], e["uhrzeit"]) for e in self.events])

    def test_fenster(self):
        kurz = modul._termine_aus_daten(self.daten["slots"], self.daten["dienste"], HEUTE, date(2026, 11, 30))
        self.assertTrue(kurz and all(e["datum"] <= "2026-11-30" for e in kurz))

    def test_kinderkurs_family(self):
        daten = json.loads(FIXTURE.read_text(encoding="utf-8"))
        slot = daten["slots"][1]["timeSlots"][0]
        slot["eventInfo"]["eventTitle"] = "Mini Me Perlenzauber"
        events = modul._termine_aus_daten(daten["slots"], daten["dienste"], HEUTE, ENDE)
        self.assertEqual({e["kategorie"] for e in events if e["titel"] == "Mini Me Perlenzauber"}, {"family"})

    def test_scrape_wirft_nie(self):
        with mock.patch.object(modul, "_antworten_holen", side_effect=RuntimeError("kein Browser")):
            self.assertEqual(modul.scrape(), [])
        with mock.patch.object(modul, "_antworten_holen", return_value=([], [])):
            self.assertEqual(modul.scrape(), [])


if __name__ == "__main__":
    unittest.main()
