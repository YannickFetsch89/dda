"""
test_filmwerkstatt.py – Tests für scraper/tier2/filmwerkstatt.py ohne Netz.
Fixtures: tests/fixtures/filmwerkstatt_programm.html (Programmbereich der Startseite vom 25.11.2026),
filmwerkstatt_detail.html („Five Easy Pieces“) und filmwerkstatt_detail_ohne_zeit.html („The Last Detail“).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import filmwerkstatt as modul

FIXTURES = Path(__file__).parent / "fixtures"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}
HEUTE = date(2026, 11, 25)


class TestFilmwerkstatt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = (FIXTURES / "filmwerkstatt_programm.html").read_text(encoding="utf-8")
        cls.events = modul._termine_aus_html(html, HEUTE, date(2027, 3, 25))
        cls.nach_titel = {e["titel"]: e for e in cls.events}

    def test_anzahl_und_pflichtfelder(self):
        self.assertEqual(len(self.events), 6)
        for e in self.events:
            for feld in ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertTrue(e["quelle_url"].startswith("https://www.filmwerkstatt-duesseldorf.de/"))
            self.assertNotEqual(e["quelle_url"], modul.PROGRAMM_URL)
            self.assertEqual((e["ort"], e["adresse"]),
                             ("Filmwerkstatt Düsseldorf", "Birkenstraße 47, 40233 Düsseldorf"))
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])
            self.assertTrue(e["bild_url"].startswith("https://www.filmwerkstatt-duesseldorf.de/wp-content/"))

    def test_film(self):
        e = self.nach_titel["Five Easy Pieces"]
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2026-11-26", "20:00", "kultur"))
        self.assertEqual(e["quelle_url"], "https://www.filmwerkstatt-duesseldorf.de/five-easy-pieces/")

    def test_konzert(self):
        e = self.nach_titel["Drei Kerzen: Konzertabend"]
        self.assertEqual((e["datum"], e["uhrzeit"], e["kategorie"]), ("2026-12-13", None, "musik"))
        self.assertEqual(e["preis"], "Eintritt auf Spendenbasis")

    def test_jahreswechsel(self):
        # Ohne Jahr: „10. Jan“ liegt nach dem 25.11.2026 im Jahr 2027
        self.assertEqual(modul._datum("Sa 10. Jan", HEUTE), date(2027, 1, 10))
        self.assertEqual(modul._datum("Do 10. Dez 2026", HEUTE), date(2026, 12, 10))

    def test_detailseite(self):
        e = dict(self.nach_titel["Five Easy Pieces"])
        modul._details_ergaenzen(e, (FIXTURES / "filmwerkstatt_detail.html").read_text(encoding="utf-8"), HEUTE)
        self.assertEqual((e["datum"], e["uhrzeit"], e["preis"]), ("2026-11-26", "20:00", "Eintritt 6/8€"))
        self.assertIsNone(e["ticket_url"])

    def test_detailseite_ohne_uhrzeit(self):
        e = dict(self.nach_titel["The Last Detail"])
        modul._details_ergaenzen(e, (FIXTURES / "filmwerkstatt_detail_ohne_zeit.html").read_text(encoding="utf-8"),
                                 HEUTE)
        self.assertEqual((e["datum"], e["uhrzeit"], e["preis"]), ("2026-12-10", None, "Eintritt 6/8€"))

    def test_ticket_link_im_beitrag(self):
        e = dict(self.nach_titel["Five Easy Pieces"])
        html = (FIXTURES / "filmwerkstatt_detail.html").read_text(encoding="utf-8").replace(
            "Eintritt 6/8€", 'Eintritt 6/8€ <a href="https://xceed.me/de/duesseldorf/event/five-easy-pieces">Tickets</a>')
        modul._details_ergaenzen(e, html, HEUTE)
        self.assertEqual(e["ticket_url"], "https://xceed.me/de/duesseldorf/event/five-easy-pieces")


if __name__ == "__main__":
    unittest.main()
