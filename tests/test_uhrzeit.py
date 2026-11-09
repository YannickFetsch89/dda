"""Tests für uhrzeit_parsen – Datum darf nicht als Uhrzeit erkannt werden (python -m unittest tests.test_uhrzeit)."""
import unittest

from scraper.utils.datum import uhrzeit_parsen


class UhrzeitTest(unittest.TestCase):
    def test_datum_ist_keine_uhrzeit(self):
        # Fehler bis 2026-11-09: „09.11.2026“ wurde zu 09:11
        self.assertIsNone(uhrzeit_parsen("Mo., 09.11.2026"))
        self.assertIsNone(uhrzeit_parsen("Mo., 09.11."))
        self.assertIsNone(uhrzeit_parsen("12.12.26"))
        self.assertIsNone(uhrzeit_parsen("Mittwoch, 2.12.2026"))

    def test_datum_und_uhrzeit(self):
        self.assertEqual(uhrzeit_parsen("Mo., 09.11.2026, 20:00 Uhr"), "20:00")
        self.assertEqual(uhrzeit_parsen("09.11.2026 20.00 Uhr"), "20:00")
        self.assertEqual(uhrzeit_parsen("Sa 14.11.2026 | 14:30"), "14:30")

    def test_uhrzeiten_bleiben(self):
        self.assertEqual(uhrzeit_parsen("20:00"), "20:00")
        self.assertEqual(uhrzeit_parsen("Beginn 20.00 Uhr"), "20:00")
        self.assertEqual(uhrzeit_parsen("Einlass ab 19.30."), "19:30")
        self.assertEqual(uhrzeit_parsen("20 Uhr"), "20:00")
        self.assertEqual(uhrzeit_parsen("2026-11-09T20:00:00"), "20:00")


if __name__ == "__main__":
    unittest.main()
