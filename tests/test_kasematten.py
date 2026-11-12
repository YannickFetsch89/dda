"""Tests für den Kasematten-Scraper (python -m unittest tests.test_kasematten)."""
import unittest
from datetime import date

from scraper.tier3.kasematten import (
    WOECHENTLICH,
    karten_parsen,
    kategorie_erkennen,
    titel_parsen,
    uhrzeit_finden,
    wochen_termine,
)


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

    def test_jahreswechsel(self):
        d = titel_parsen("31.12.26 – 01.01.26 – Silvester")
        self.assertEqual((d["datum"], d["datum_bis"]), (date(2026, 12, 31), date(2027, 1, 1)))
        d = titel_parsen("31.12.26 – 01.01.27 – Silvester")
        self.assertEqual(d["datum_bis"], date(2027, 1, 1))
        # gleicher Monat, Ende vor Start: kein stilles Jahr+1
        self.assertIsNone(titel_parsen("31.-01.10.26 – Rückwärts"))
        # Tippfehler über Monate (nicht Dezember → Januar): verworfen, nicht ins nächste Jahr verlegt
        self.assertIsNone(titel_parsen("01.06.26 – 01.05.26 – Tippfehler"))

    def test_woechentlich_und_ohne_datum(self):
        self.assertEqual(titel_parsen("Jeden Freitag – Freak Friday"), {"woechentlich": "freitag", "titel": "Freak Friday"})
        self.assertIsNone(titel_parsen("Unsere Events"))
        self.assertIsNone(titel_parsen("31.02.26 – Kein Tag"))  # ungültiges Datum
        self.assertFalse(WOECHENTLICH)
        # 13.11.2026 und 20.11.2026 sind Freitage
        self.assertEqual(
            wochen_termine("freitag", date(2026, 11, 12), date(2026, 11, 20)),
            [date(2026, 11, 13), date(2026, 11, 20)],
        )

    def test_uhrzeit_und_kategorie(self):
        self.assertEqual(uhrzeit_finden("verwandeln sich die Kasematten von 17 bis 24 Uhr in den Treffpunkt"), "17:00")
        self.assertEqual(uhrzeit_finden("Einlass ab 19 Uhr"), "19:00")
        self.assertEqual(uhrzeit_finden("Start 18:30 Uhr"), "18:30")
        self.assertIsNone(uhrzeit_finden("Fünf Locations. Eine Nacht."))
        self.assertEqual(
            uhrzeit_finden("Öffnungszeiten von 11 bis 23 Uhr. Am Freitag ab 19 Uhr"),
            "19:00",
        )
        self.assertEqual(uhrzeit_finden("von 24 bis 2 Uhr und von 19 bis 23 Uhr"), "19:00")
        self.assertIsNone(uhrzeit_finden("Einlass 24 Uhr"))
        self.assertEqual(kategorie_erkennen("Chefs in Town – Samoa Seepferdchen"), "food")
        self.assertEqual(kategorie_erkennen("Silvester 2026"), "nightlife")

    def test_karten_parsen(self):
        html = """
        <article class="qodef-blog-item">
          <a class="qodef-e-title-link" href="https://kasematten-duesseldorf.de/oktoberfest/">
            19.09.26 – 18.10.26 – Oktoberfest 2026
          </a>
          <div class="qodef-e-media-image"><img src="https://example.test/oktoberfest.jpg" /></div>
          <p class="qodef-e-excerpt">Zwei Wochen Festzelt.</p>
        </article>
        <article class="qodef-blog-item">
          <div class="qodef-e-title">ohne Link</div>
        </article>
        """
        karten = karten_parsen(html)
        self.assertEqual(len(karten), 1)
        self.assertEqual(karten[0]["titel_roh"], "19.09.26 – 18.10.26 – Oktoberfest 2026")
        self.assertEqual(karten[0]["url"], "https://kasematten-duesseldorf.de/oktoberfest/")
        self.assertEqual(karten[0]["bild_url"], "https://example.test/oktoberfest.jpg")
        self.assertEqual(karten[0]["auszug"], "Zwei Wochen Festzelt.")


if __name__ == "__main__":
    unittest.main()
