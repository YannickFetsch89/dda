"""Tests für den Scraper Schloss Benrath (Quellen-Ausbau V1, ohne Netz).
python -m unittest tests.test_schloss_benrath"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import schloss_benrath as b

FIXTURES = Path(__file__).parent / "fixtures"
HTML = (FIXTURES / "schloss_benrath_liste.html").read_text(encoding="utf-8")
DETAIL = (FIXTURES / "schloss_benrath_detail.html").read_text(encoding="utf-8")
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")
FELDER = {"titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "beschreibung", "preis", "quelle_name",
          "quelle_url", "bild_url", "bild_generiert", "status"}


class SchlossBenrathTest(unittest.TestCase):
    def setUp(self):
        self.events = b._termine_aus_html(HTML, date(2026, 11, 24), date(2027, 11, 24))

    def _event(self, anfang: str) -> dict:
        return next(e for e in self.events if e["titel"].startswith(anfang))

    def test_termine_aus_dem_auszug(self):
        self.assertGreaterEqual(len(self.events), 12)
        erstes = self.events[0]
        self.assertEqual(erstes["titel"], "Die Leuchtenden Gärten")
        self.assertEqual((erstes["datum"], erstes["uhrzeit"]), ("2026-11-26", "17:00"))
        self.assertEqual(erstes["ort"], "Schloss Benrath")
        self.assertEqual(erstes["adresse"], "Benrather Schloßallee 100-108, 40597 Düsseldorf")
        self.assertTrue(erstes["quelle_url"].startswith("https://www.schloss-benrath.de/veranstaltungs-detail/v/"))
        self.assertTrue(erstes["bild_url"].startswith("https://www.schloss-benrath.de/fileadmin/"))

    def test_pflichtfelder(self):
        for e in self.events:
            self.assertEqual(set(e), FELDER)
            for feld in PFLICHT:
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertRegex(e["uhrzeit"], r"^\d{2}:\d{2}$")
            self.assertIsNone(e["beschreibung"])

    def test_einlass_zeitfenster_weggelassen(self):
        self.assertFalse(any(e["titel"].startswith("Einlass") for e in self.events))

    def test_titel_kategorie_preis(self):
        lesung = self._event("Lesung")
        self.assertEqual(lesung["titel"], "Lesung – Bärbel van Alen: Schneiden. Färben. Sterben")
        self.assertEqual((lesung["kategorie"], lesung["preis"]), ("kultur", "kostenlos"))
        self.assertEqual(self._event("Wandelkonzert")["kategorie"], "musik")
        self.assertEqual(self._event("Lisi Lädt Ein: Weihnachtskonzert")["kategorie"], "musik")
        self.assertEqual(self._event("Führung Schloss Klassik")["kategorie"], "kultur")
        self.assertEqual(self._event("Familienführung")["kategorie"], "family")
        self.assertEqual(self._event("Workshop: Adventskranz-Werkstatt")["kategorie"], "family")
        self.assertEqual(self._event("Lichterfest")["datum"], "2027-07-17")
        self.assertEqual(b.titel_bereinigen("FAMILIENFÜHRUNG | Super-Tiere"), "Familienführung: Super-Tiere")

    def test_fenster_und_detail(self):
        kurz = b._termine_aus_html(HTML, date(2026, 11, 24), date(2026, 12, 31))
        self.assertFalse(any(e["datum"] > "2026-12-31" for e in kurz))
        self.assertEqual(b.zeit_aus_detail(DETAIL), ("2026-11-29", "15:00"))


if __name__ == "__main__":
    unittest.main()
