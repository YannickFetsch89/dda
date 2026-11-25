"""Tests für den Scraper Boston Club (Veranstaltungsseite, ohne Netz).
python -m unittest tests.test_boston_club"""
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import boston_club as modul

FIXTURE = Path(__file__).parent / "fixtures" / "boston_club_veranstaltungen.html"
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class SeiteTest(unittest.TestCase):
    def setUp(self):
        self.html = FIXTURE.read_text(encoding="utf-8")

    def test_partys(self):
        events = modul._termine_aus_html(self.html, date(2026, 11, 25), date(2027, 3, 25))
        # 21.11.2026 liegt zurück, 14.11. (Sport) auch; aus „Termine 2027“ fallen 23.01., 20.02., 06.03. ins Fenster
        self.assertEqual([e["datum"] for e in events], ["2027-01-23", "2027-02-20", "2027-03-06"])
        e = events[0]
        self.assertEqual(e["titel"], "Tanz-Übungsparty")
        self.assertEqual(e["uhrzeit"], "19:30")
        self.assertEqual(e["ort"], "Boston Club")
        self.assertEqual(e["adresse"], "Vennhauser Allee 135, 40627 Düsseldorf")
        self.assertEqual(e["kategorie"], "community")
        self.assertEqual(e["preis"], "kostenlos")
        self.assertEqual(e["quelle_url"], "https://www.boston-club.de/Veranstaltungen.html")
        self.assertEqual(e["bild_url"], "https://www.boston-club.de/images/Beets4feats.jpg")
        self.assertIsNone(e["beschreibung"])
        for ev in events:
            for feld in PFLICHT:
                self.assertTrue(ev[feld], f"{feld} leer")

    def test_sport_und_naechste_party(self):
        events = modul._termine_aus_html(self.html, date(2026, 11, 1), date(2026, 12, 31))
        nach_datum = {e["datum"]: e for e in events}
        self.assertEqual(nach_datum["2026-11-14"]["titel"], "Move&Learn-Seminar")
        self.assertEqual(nach_datum["2026-11-14"]["kategorie"], "sport")
        self.assertEqual(nach_datum["2026-11-14"]["preis"], "16 €")
        self.assertIsNone(nach_datum["2026-11-14"]["uhrzeit"])
        self.assertEqual(nach_datum["2026-11-21"]["uhrzeit"], "19:30")

    def test_jahr_ergaenzen(self):
        # Ein Datum ohne Jahr, das weit zurückliegt, gehört ins nächste Jahr
        html = self.html.replace("<span style=\"font-weight: 700;\">14.11.</span>", "<span>16.01.</span>")
        events = modul._termine_aus_html(html, date(2026, 11, 25), date(2027, 3, 25))
        self.assertIn(("2027-01-16", "sport"), [(e["datum"], e["kategorie"]) for e in events])

    def test_ball_mit_datum(self):
        html = self.html.replace("Ab dem 02.11.2026 beginnt der Vorverkauf.",
                                 "Der Ball findet am 05.12.2026 ab 19:00 Uhr statt. Ab dem 02.11.2026 beginnt der Vorverkauf.")
        events = modul._termine_aus_html(html, date(2026, 11, 25), date(2027, 3, 25))
        ball = [e for e in events if e["titel"] == "Weihnachtsball"]
        self.assertEqual([(e["datum"], e["uhrzeit"]) for e in ball], [("2026-12-05", "19:00")])

    def test_scrape_wirft_nie(self):
        with mock.patch.object(modul, "seite_abrufen", return_value=None):
            self.assertEqual(modul.scrape(), [])
        with mock.patch.object(modul, "seite_abrufen", side_effect=RuntimeError("kaputt")):
            self.assertEqual(modul.scrape(), [])


if __name__ == "__main__":
    unittest.main()
