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

    def test_kein_pauschalwert_fuer_dlive(self):
        # Unbekannte d.live-Spielstätte: nicht mehr pauschal Stockum
        self.assertIsNone(stadtteil_ermitteln("Rheinterrasse", None, "d-live"))


if __name__ == "__main__":
    unittest.main()
