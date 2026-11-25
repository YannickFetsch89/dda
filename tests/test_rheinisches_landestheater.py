"""
test_rheinisches_landestheater.py – Tests für scraper/tier2/rheinisches_landestheater.py ohne Netz.
Fixture: tests/fixtures/rheinisches_landestheater.html (9 Vorstellungen aus den AJAX-Abschnitten November/Dezember
2026 des Spielplans vom 25.11.2026, gekürzt).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import rheinisches_landestheater as modul

FIXTURE = Path(__file__).parent / "fixtures" / "rheinisches_landestheater.html"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


class TestRheinischesLandestheater(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = FIXTURE.read_text(encoding="utf-8")
        cls.events = modul._termine_aus_html(cls.html, date(2026, 11, 25), date(2027, 11, 25))
        cls.nach_titel = {(e["titel"], e["datum"]): e for e in cls.events}

    def test_anzahl_und_pflichtfelder(self):
        # 9 Karten: geschlossene Vorstellung und Gruppenbuchung fallen weg → 7
        self.assertEqual(len(self.events), 7)
        for e in self.events:
            for feld in ("titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "quelle_name", "quelle_url",
                         "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertEqual(e["ort"], "Das Rheinische Landestheater")
            self.assertEqual(e["adresse"], "Oberstraße 95, 41460 Neuss")
            self.assertTrue(e["quelle_url"].startswith("https://www.rheinisches-landestheater.de/produktionen/"))
            self.assertNotEqual(e["quelle_url"], e.get("ticket_url"))
            self.assertIsNone(e["beschreibung"])
            self.assertNotIn("\xad", e["titel"])

    def test_schauspiel_mit_ticket_und_bild(self):
        e = self.nach_titel[("Die Wut, die bleibt", "2026-11-25")]
        self.assertEqual((e["uhrzeit"], e["kategorie"]), ("19:30", "kultur"))
        self.assertTrue(e["ticket_url"].startswith("https://dtsinhousesales2.derticketservice.de/rlt.webshop/"))
        self.assertTrue(e["bild_url"].startswith("https://www.rheinisches-landestheater.de/uploads/"))
        self.assertIn("ID_Vorstellung=1539", e["quelle_url"])

    def test_eintritt_frei_community(self):
        e = self.nach_titel[("Orange Days 2026", "2026-11-25")]
        self.assertEqual((e["uhrzeit"], e["preis"], e["kategorie"]), ("17:00", "kostenlos", "community"))
        self.assertIsNone(e["ticket_url"])

    def test_ausverkauft_bleibt_und_kinder_family(self):
        e = next(e for e in self.events if e["titel"].startswith("Ginpuin"))
        self.assertEqual(e["kategorie"], "family")

    def test_ohne_raum_kulturamt(self):
        e = self.nach_titel[("Der satanarchäolügenialkohöllische Wunschpunsch", "2026-12-20")]
        self.assertEqual((e["uhrzeit"], e["kategorie"]), ("14:00", "family"))
        self.assertTrue(e["ticket_url"].startswith("https://kulturamt-neuss.de/"))

    def test_geschlossen_und_gruppe_fehlen(self):
        self.assertFalse(any(e["datum"] in ("2026-11-27", "2026-11-30") and "Wunschpunsch" in e["titel"]
                             for e in self.events))

    def test_gastspiel_anderswo_fehlt(self):
        html = self.html.replace('spielplan-ort d-block">Neuss', 'spielplan-ort d-block">Gütersloh', 1)
        events = modul._termine_aus_html(html, date(2026, 11, 25), date(2027, 11, 25))
        self.assertEqual(len(events), 6)
        self.assertNotIn("Orange Days 2026", {e["titel"] for e in events})

    def test_letzter_termin(self):
        self.assertEqual(modul._letzter_termin(self.html), "1798736400")


if __name__ == "__main__":
    unittest.main()
