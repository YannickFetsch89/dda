"""
test_comedy_club.py – Tests für scraper/tier2/comedy_club.py ohne Netz (Fixture: Auszug der Programmseite vom 24.11.2026).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import comedy_club as modul

FIXTURE = Path(__file__).parent / "fixtures" / "comedy_club_shows.html"
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")
FELDER = {"titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "beschreibung", "preis", "quelle_name", "ticket_url",
          "quelle_url", "bild_url", "bild_generiert", "status"}


class TestComedyClub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = FIXTURE.read_text(encoding="utf-8")
        cls.events = modul._termine_aus_html(cls.html, date(2026, 11, 24), date(2027, 3, 24))

    def test_anzahl_und_felder(self):
        # 8 Einträge im Auszug: einer an anderer Adresse, einer doppelt → 6 Events
        self.assertEqual(len(self.events), 6)
        for e in self.events:
            self.assertEqual(set(e), FELDER)
            for feld in PFLICHT:
                self.assertTrue(e[feld], feld)
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])

    def test_erster_termin(self):
        e = self.events[0]
        self.assertEqual(e["titel"], "Comedy Open Mic Düsseldorf")
        self.assertEqual(e["datum"], "2026-11-25")
        self.assertEqual(e["uhrzeit"], "20:00")
        self.assertEqual(e["ort"], "Comedy Club Düsseldorf")
        self.assertEqual(e["adresse"], "Oststraße 147, 40210 Düsseldorf")
        self.assertEqual(e["kategorie"], "kultur")
        self.assertEqual(e["preis"], "ab 14,90 €")
        self.assertEqual(e["quelle_url"], "https://comedyclubduesseldorf.de/shows/10433")
        self.assertTrue(e["bild_url"].startswith("https://comedyclubduesseldorf.de/_next/image?url=https%3A%2F%2F"))

    def test_andere_adresse_weggelassen(self):
        self.assertNotIn("7STAGES COMEDY NIGHT", [e["titel"] for e in self.events])

    def test_ausverkauft_bleibt_doppelte_einmal(self):
        bom = [e for e in self.events if e["titel"].startswith("BOM")]
        self.assertEqual(len(bom), 1)

    def test_zeitfenster(self):
        events = modul._termine_aus_html(self.html, date(2026, 11, 26), date(2026, 11, 27))
        self.assertEqual([e["datum"] for e in events], ["2026-11-26", "2026-11-27"])

    def test_kaputte_seite(self):
        self.assertEqual(modul._termine_aus_html("<html></html>", date(2026, 11, 24), date(2027, 1, 1)), [])


if __name__ == "__main__":
    unittest.main()
