"""Tests für den Kasematten-Scraper (python -m unittest tests.test_kasematten)."""
import unittest
from datetime import date

from scraper.tier3.kasematten import kategorie_erkennen, titel_parsen, uhrzeit_finden


class TitelTest(unittest.TestCase):
    def test_einzeltag(self):
        self.assertEqual(titel_parsen("31.12.26 – Silvester 2026"),
                         {"datum": date(2026, 12, 31), "datum_bis": None, "titel": "Silvester 2026"})
        self.assertEqual(titel_parsen("11.10.2026 – AFTER FISCHMARKT")["datum"], date(2026, 10, 11))

    def test_bereich(self):
        d = titel_parsen("19.09.26 – 18.10.26 – Oktoberfest 2026")
        self.assertEqual((d["datum"], d["datum_bis"], d["titel"]), (date(2026, 9, 19), date(2026, 10, 18), "Oktoberfest 2026"))
        # Bindestrich ohne Leerzeichen vor dem Titel
        d = titel_parsen("25.09.26 – 07.10.26 -BACK TO THE 90’s")
        self.assertEqual((d["datum_bis"], d["titel"]), (date(2026, 10, 7), "BACK TO THE 90’s"))
        d = titel_parsen("26.-31.10.26 – Halloween Week")
        self.assertEqual((d["datum"], d["datum_bis"]), (date(2026, 10, 26), date(2026, 10, 31)))

    def test_woechentlich_und_ohne_datum(self):
        self.assertEqual(titel_parsen("Jeden Freitag – Freak Friday"), {"woechentlich": "freitag", "titel": "Freak Friday"})
        self.assertIsNone(titel_parsen("Unsere Events"))
        self.assertIsNone(titel_parsen("31.02.26 – Kein Tag"))  # ungültiges Datum

    def test_uhrzeit_und_kategorie(self):
        self.assertEqual(uhrzeit_finden("verwandeln sich die Kasematten von 17 bis 24 Uhr in den Treffpunkt"), "17:00")
        self.assertEqual(uhrzeit_finden("Einlass ab 19 Uhr"), "19:00")
        self.assertEqual(uhrzeit_finden("Start 18:30 Uhr"), "18:30")
        self.assertIsNone(uhrzeit_finden("Fünf Locations. Eine Nacht."))
        self.assertEqual(kategorie_erkennen("Chefs in Town – Samoa Seepferdchen"), "food")
        self.assertEqual(kategorie_erkennen("Silvester 2026"), "nightlife")


if __name__ == "__main__":
    unittest.main()
