"""
test_ampere.py – Tests für scraper/tier2/ampere.py ohne Netz
(Fixtures: Programmseite und eine Detailseite von ampere-club.de vom 24.11.2026, gekürzt).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import ampere as modul

FIXTURES = Path(__file__).parent / "fixtures"
DETAIL_URL = "https://ampere-club.de/veranstaltungen/filmfest-duesseldorf/"
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class TestAmpere(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.liste = (FIXTURES / "ampere_programm.html").read_text(encoding="utf-8")
        cls.detail = (FIXTURES / "ampere_detail.html").read_text(encoding="utf-8")
        cls.details = {DETAIL_URL: modul._details_aus_html(cls.detail, DETAIL_URL)}
        cls.events = modul._termine_aus_html(cls.liste, date(2026, 11, 24), date(2027, 3, 24), cls.details)

    def test_liste_vollstaendig(self):
        self.assertEqual(len(modul._liste_aus_html(self.liste)), 18)

    def test_zeitfenster(self):
        self.assertEqual(len(self.events), 12)
        self.assertEqual(self.events[0]["datum"], "2026-11-27")
        self.assertEqual(self.events[-1]["datum"], "2027-03-18")

    def test_pflichtfelder(self):
        for e in self.events:
            for feld in PFLICHT:
                self.assertTrue(e[feld], feld)
            self.assertEqual(e["ort"], "Ampere")
            self.assertEqual(e["adresse"], "Ronsdorfer Str. 134, 40233 Düsseldorf")
            self.assertTrue(e["quelle_url"].startswith("https://ampere-club.de/veranstaltungen/"))
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])

    def test_detailseite_beginn_statt_jsonld(self):
        self.assertEqual(self.details[DETAIL_URL]["uhrzeit"], "18:00")   # Beginn 18:00, Einlass 17:30
        self.assertEqual(self.details[DETAIL_URL]["preis"], "kostenlos")
        e = self.events[0]
        self.assertEqual(e["titel"], "24. Filmfest Düsseldorf")
        self.assertEqual(e["uhrzeit"], "18:00")
        self.assertEqual(e["kategorie"], "kultur")   # Sparte Film
        self.assertTrue(e["bild_url"].startswith("https://ampere-club.de/wp-content/uploads/"))

    def test_kategorien(self):
        nach_titel = {e["titel"]: e["kategorie"] for e in self.events}
        self.assertEqual(nach_titel["HART AN DER GRENZE"], "nightlife")   # DJ
        self.assertEqual(nach_titel["Rantanplan"], "musik")               # Konzert
        self.assertEqual(nach_titel["Sascha Lange"], "kultur")            # Lesung

    def test_ohne_detailseite_uhrzeit_leer(self):
        e = next(x for x in self.events if x["titel"] == "Rantanplan")
        self.assertIsNone(e["uhrzeit"])
        self.assertEqual(e["datum"], "2027-03-04")

    def test_preisfelder(self):
        html = ('<div class="w-post-elm event_price_presale"><span class="w-post-elm-before">Vorverkauf: </span>'
                '<span class="w-post-elm-value">18</span></div>'
                '<div class="w-post-elm event_price_box_office"><span class="w-post-elm-before">Abendkasse: </span>'
                '<span class="w-post-elm-value">22</span></div>')
        self.assertEqual(modul._details_aus_html(html)["preis"], "Vorverkauf 18 € / Abendkasse 22 €")


if __name__ == "__main__":
    unittest.main()
