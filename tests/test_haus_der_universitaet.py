"""
test_haus_der_universitaet.py – Tests für scraper/tier2/haus_der_universitaet.py ohne Netz.
Fixtures: tests/fixtures/haus_der_universitaet_kalender.html (erste Kalenderseite vom 25.11.2026, nur die Liste)
und haus_der_universitaet_detail.html (Detailseite „Düsseldorfer Patiententag“, nur der Inhaltsbereich).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import haus_der_universitaet as modul

FIXTURES = Path(__file__).parent / "fixtures"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


class TestHausDerUniversitaet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (FIXTURES / "haus_der_universitaet_kalender.html").read_text(encoding="utf-8")
        cls.detail = (FIXTURES / "haus_der_universitaet_detail.html").read_text(encoding="utf-8")
        cls.events = modul._termine_aus_liste(cls.html, date(2026, 11, 25), date(2027, 3, 25))

    def test_anzahl_und_pflichtfelder(self):
        self.assertEqual(len(self.events), 10)
        for e in self.events:
            for feld in ("titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "quelle_name", "quelle_url",
                         "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertTrue(e["quelle_url"].startswith("https://www.hdu.hhu.de/programm/einzeltermin/"))
            self.assertEqual(e["ort"], "Haus der Universität")
            self.assertEqual(e["adresse"], "Schadowpl. 14, 40212 Düsseldorf")
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])

    def test_vortrag(self):
        e = self.events[0]
        self.assertEqual(e["titel"], "100 Jahre „Das Totenschiff“ – B. Traven zwischen Düsseldorf und Mexiko")
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2026-11-25", "18:30", "kultur"))

    def test_konzert_und_patiententag(self):
        konzert = next(e for e in self.events if e["titel"].startswith("schumann@heine: Verwandt"))
        self.assertEqual((konzert["datum"], konzert["uhrzeit"], konzert["kategorie"]), ("2026-12-16", "19:30", "musik"))
        tag = next(e for e in self.events if "Patiententag" in e["titel"])
        self.assertEqual((tag["datum"], tag["uhrzeit"], tag["kategorie"]), ("2026-11-28", "10:00", "community"))

    def test_naechste_seite(self):
        self.assertEqual(modul._naechste_seite(self.html),
                         "https://www.hdu.hhu.de/programm/veranstaltungskalender/event-page-2")

    def test_detailseite(self):
        e = dict(next(e for e in self.events if "Patiententag" in e["titel"]))
        self.assertTrue(modul._details_ergaenzen(e, self.detail))
        self.assertEqual(e["preis"], "kostenlos")
        self.assertIsNone(e["ticket_url"])

    def test_anderer_ort_ausgelassen(self):
        e = dict(self.events[0])
        anders = self.detail.replace("Ort: Haus der Universität", "Ort: Hörsaal 3A, Campus der HHU")
        self.assertFalse(modul._details_ergaenzen(e, anders))

    def test_zeitfenster(self):
        events = modul._termine_aus_liste(self.html, date(2026, 12, 1), date(2026, 12, 9))
        self.assertEqual(len(events), 3)


if __name__ == "__main__":
    unittest.main()
