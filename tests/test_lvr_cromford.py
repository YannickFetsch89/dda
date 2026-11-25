"""
test_lvr_cromford.py – Tests für scraper/tier2/lvr_cromford.py ohne Netz.
Fixture: tests/fixtures/lvr_cromford.json (Antwort der Suchschnittstelle www.lvr.de/industriemuseum/.elasticsearch,
Filter Textilfabrik Cromford, vom 25.11.2026 – 6 Termine).
"""
import json
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import lvr_cromford as modul

FIXTURE = Path(__file__).parent / "fixtures" / "lvr_cromford.json"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


class TestLvrCromford(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.daten = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.events = modul._termine_aus_json(cls.daten, date(2026, 11, 25), date(2027, 3, 31))
        cls.nach_titel = {(e["titel"], e["datum"]): e for e in cls.events}

    def test_anzahl_und_pflichtfelder(self):
        self.assertEqual(len(self.events), 6)
        for e in self.events:
            for feld in ("titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "quelle_name", "quelle_url",
                         "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertEqual(e["ort"], "LVR-Industriemuseum Textilfabrik Cromford")
            self.assertEqual(e["adresse"], "Cromforder Allee 24, 40878 Ratingen")
            self.assertTrue(e["quelle_url"].startswith("https://www.lvr.de/industriemuseum/textilfabrik-cromford/"))
            self.assertEqual(e["ticket_url"], "https://www.shop.industriemuseum.lvr.de")
            self.assertTrue(e["bild_url"].startswith("https://lvr.gomus.de/"))
            self.assertIsNone(e["beschreibung"])
            self.assertEqual(e["quelle_name"], "LVR-Industriemuseum Cromford")

    def test_ortszeit_und_familie(self):
        e = self.nach_titel[("Familienworkshop: Weihnachtskarten mit eigenen Stempeln gestalten", "2026-11-29")]
        self.assertEqual((e["uhrzeit"], e["kategorie"]), ("14:00", "family"))

    def test_konzert_und_praefix(self):
        e = self.nach_titel[("Konzert im Kartensaal: Duo Dafne", "2026-12-06")]
        self.assertEqual((e["uhrzeit"], e["kategorie"]), ("18:30", "musik"))
        self.assertIn(('Eröffnungswochenende "Entgrenzungen"', "2026-12-05"), self.nach_titel)
        self.assertIn(('Eröffnungswochenende "Entgrenzungen"', "2026-12-06"), self.nach_titel)

    def test_fuehrung_kultur(self):
        e = self.nach_titel[("Führung: Baumwollspinnerei Cromford – Lebens- und Arbeitswelten um 1800", "2026-12-13")]
        self.assertEqual((e["uhrzeit"], e["kategorie"]), ("14:00", "kultur"))

    def test_zeitfenster(self):
        self.assertEqual(len(modul._termine_aus_json(self.daten, date(2026, 12, 7), date(2026, 12, 31))), 2)

    def test_api_url_filter(self):
        url = modul.api_url()
        self.assertTrue(url.startswith("https://www.lvr.de/industriemuseum/.elasticsearch?"))
        self.assertIn("museum.id.terms", url.replace("%22", "").replace("%3A", ":"))


if __name__ == "__main__":
    unittest.main()
