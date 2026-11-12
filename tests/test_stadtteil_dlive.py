"""Tests: Stadtteile der d.live-Hallen (python -m unittest tests.test_stadtteil_dlive)."""
import unittest

from pipeline.stadtteil_mapper import stadtteil_ermitteln


class DliveTest(unittest.TestCase):
    def test_hallen(self):
        self.assertEqual(stadtteil_ermitteln("Mitsubishi Electric HALLE", None, "d-live"), "Oberbilk")
        self.assertEqual(stadtteil_ermitteln("Mitsubishi Electric Halle", None, "Rausgegangen"), "Oberbilk")
        self.assertEqual(stadtteil_ermitteln("PSD BANK DOME Düsseldorf", None, "DEG Eishockey Düsseldorf"), "Rath")
        self.assertEqual(stadtteil_ermitteln("CASTELLO Düsseldorf", None, "d-live"), "Reisholz")
        self.assertEqual(stadtteil_ermitteln("Merkur Spiel-Arena", None, "d-live"), "Stockum")
        self.assertEqual(stadtteil_ermitteln("Messe Düsseldorf", None, "Messe Düsseldorf"), "Stockum")

    def test_mehrfache_leerzeichen(self):
        self.assertEqual(stadtteil_ermitteln("Mitsubishi Electric  Halle Düsseldorf", None, "AllEvents.in Düsseldorf"), "Oberbilk")

    def test_scraper_adressen(self):
        from scraper.tier2.dlive import VENUE_MAP
        adressen = {name: adresse for name, adresse in VENUE_MAP.values()}
        self.assertEqual(adressen["PSD BANK DOME"], "Theodorstraße 281, 40472 Düsseldorf")
        self.assertEqual(adressen["CASTELLO Düsseldorf"], "Karl-Hohmann-Straße 1, 40599 Düsseldorf")
        self.assertNotEqual(adressen["PSD BANK DOME"], adressen["Mitsubishi Electric HALLE"])
        from scraper.tier3 import deg
        self.assertEqual(deg.ADRESSE_STANDARD, adressen["PSD BANK DOME"])

    def test_quelle_mit_stadt_anhang(self):
        # Fallback über die Quelle greift auch, wenn der Scraper „ Düsseldorf“ anhängt
        self.assertEqual(stadtteil_ermitteln("Heimspiel", None, "DEG Eishockey Düsseldorf"), "Rath")
        self.assertEqual(stadtteil_ermitteln("Sonderausstellung", None, "Kunstpalast Düsseldorf"), "Pempelfort")
        self.assertIsNone(stadtteil_ermitteln("Irgendwo", None, "Unbekannte Quelle"))

    def test_kein_pauschalwert_fuer_dlive(self):
        # Unbekannte d.live-Spielstätte: nicht mehr pauschal Stockum
        self.assertIsNone(stadtteil_ermitteln("Rheinterrasse", None, "d-live"))


if __name__ == "__main__":
    unittest.main()
