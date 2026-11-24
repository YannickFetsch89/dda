"""Tests für den Scraper Roncalli's Apollo Varieté (ohne Netz).
python -m unittest tests.test_apollo_variete"""
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import apollo_variete as modul

ORDNER = Path(__file__).parent / "fixtures"
HEUTE, ENDE = date(2026, 11, 24), date(2027, 11, 24)
URL = "https://www.apollo-variete.com/apollo-shows/camden-chaos/"
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


def _lesen(name: str) -> str:
    return (ORDNER / name).read_text(encoding="utf-8")


class AngabeTest(unittest.TestCase):
    def test_zeitraum(self):
        self.assertEqual(modul.termine_aus_angabe("15. Januar – 11. April 2027"),
                         ([], (date(2027, 1, 15), date(2027, 4, 11))))
        self.assertEqual(modul.termine_aus_angabe("23 . Oktober 2026 – 10. Januar 2027"),
                         ([], (date(2026, 10, 23), date(2027, 1, 10))))
        self.assertEqual(modul.termine_aus_angabe("15. Dezember – 10. Januar 2027"),
                         ([], (date(2026, 12, 15), date(2027, 1, 10))))

    def test_einzeltage(self):
        self.assertEqual(modul.termine_aus_angabe("15. & 16. März 2027")[0], [date(2027, 3, 15), date(2027, 3, 16)])
        self.assertEqual(modul.termine_aus_angabe("31. Mai und 1. Juni 2027")[0], [date(2027, 5, 31), date(2027, 6, 1)])
        self.assertEqual(modul.termine_aus_angabe("12. Juli 2027"), ([date(2027, 7, 12)], None))
        self.assertEqual(modul.termine_aus_angabe("demnächst"), ([], None))


class SeitenTest(unittest.TestCase):
    def test_zeitraum_ein_eintrag_mit_datum_bis(self):
        events = modul._termine_aus_html(_lesen("apollo_variete_camden.html"), URL, HEUTE, ENDE)
        self.assertEqual(len(events), 1)
        e = events[0]
        self.assertEqual((e["titel"], e["datum"], e["datum_bis"]), ("Camden Chaos", "2027-01-15", "2027-04-11"))
        self.assertIsNone(e["uhrzeit"])
        self.assertEqual(e["ort"], "Roncalli's Apollo Varieté")
        self.assertEqual(e["adresse"], "Apollo-Platz 1, 40213 Düsseldorf")
        self.assertEqual(e["kategorie"], "kultur")
        self.assertEqual(e["quelle_url"], URL)
        self.assertTrue(e["bild_url"].startswith("https://www.apollo-variete.com/"))
        self.assertIsNone(e["beschreibung"])
        for feld in PFLICHT:
            self.assertTrue(e[feld], f"{feld} leer")

    def test_laufende_show_beginnt_heute(self):
        events = modul._termine_aus_html(_lesen("apollo_variete_winter.html"), URL, HEUTE, ENDE)
        self.assertEqual([(e["datum"], e["datum_bis"]) for e in events], [("2026-11-24", "2027-01-10")])
        self.assertEqual(modul._termine_aus_html(_lesen("apollo_variete_winter.html"), URL, date(2027, 1, 11), ENDE), [])

    def test_einzeltage_je_ein_termin(self):
        events = modul._termine_aus_html(_lesen("apollo_variete_hokus.html"), URL, HEUTE, ENDE)
        self.assertEqual([e["datum"] for e in events], ["2027-04-04", "2027-06-06", "2027-09-19", "2027-10-28"])
        self.assertEqual(events[0]["titel"], "Hokus Pokus! Die Familienzaubershow")   # ohne weiche Trennstriche
        self.assertTrue(all("datum_bis" not in e for e in events))

    def test_ersatz_aus_uebersicht(self):
        kreis = _lesen("apollo_variete_kreis.html")   # Show-Seite nennt „6. Oktober 2026“ (vergangen)
        url = "https://www.apollo-variete.com/apollo-shows/robert-kreis/"
        self.assertEqual(modul._termine_aus_html(kreis, url, HEUTE, ENDE), [])
        karten = modul._karten_angaben(_lesen("apollo_variete_shows.html"))
        self.assertEqual(karten[url], "6. Oktober 2027")
        events = modul._termine_aus_html(kreis, url, HEUTE, ENDE, karten[url])
        self.assertEqual([(e["titel"], e["datum"]) for e in events], [("Ein Abend Robert Kreis", "2027-10-06")])
        # unscharfe Übersichtsangaben werden nicht übernommen
        self.assertEqual(modul._termine_aus_html(kreis, url, HEUTE, ENDE, "Bis 10. Januar 2027"), [])
        self.assertEqual(modul._termine_aus_html(kreis, url, HEUTE, ENDE, "4. April, 6. Juni und weitere Termine 2027"), [])

    def test_show_links(self):
        links = modul._show_links(_lesen("apollo_variete_shows.html"))
        self.assertIn("https://www.apollo-variete.com/apollo-shows/camden-chaos/", links)
        self.assertNotIn("https://www.apollo-variete.com/apollo-shows/", links)
        self.assertTrue(all("tickets." not in link for link in links))
        self.assertEqual(len(links), len(set(links)))

    def test_scrape_wirft_nie_und_begrenzt(self):
        aufrufe = []

        def abruf(url, logger=None, wartezeit=2.0):
            aufrufe.append(url)
            return _lesen("apollo_variete_shows.html") if url == modul.SHOWS_URL else _lesen("apollo_variete_camden.html")

        with mock.patch.object(modul, "seite_abrufen", side_effect=abruf):
            events = modul.scrape()
        self.assertIsInstance(events, list)
        self.assertLessEqual(len(aufrufe), modul.MAX_SHOWSEITEN + 1)
        self.assertLessEqual(len(events), 1)   # gleiche Show mehrfach → nur einmal
        with mock.patch.object(modul, "seite_abrufen", return_value=None):
            self.assertEqual(modul.scrape(), [])
        with mock.patch.object(modul, "seite_abrufen", side_effect=RuntimeError("kaputt")):
            self.assertEqual(modul.scrape(), [])


if __name__ == "__main__":
    unittest.main()
