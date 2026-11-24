"""
test_bilker_bunker.py – Tests für scraper/tier2/bilker_bunker.py ohne Netz
(Fixture: Auszug aus https://bilkerbunker.de/schleuse-zwei vom 24.11.2026).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import bilker_bunker as modul

FIXTURE = Path(__file__).parent / "fixtures" / "bilker_bunker_schleuse_zwei.html"
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")


class TestBilkerBunker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = FIXTURE.read_text(encoding="utf-8")
        cls.events = modul._ohne_doppelte(modul._termine_aus_html(cls.html, date(2026, 11, 24), date(2027, 3, 24)))

    def test_anzahl_ohne_doppelte_und_geschlossene_gesellschaft(self):
        # 3 Listeneinträge + 1 „Geschlossene Gesellschaft“ + 6 im Konzert-Block (2 davon doppelt) → 7
        self.assertEqual(len(self.events), 7)
        self.assertNotIn("Geschlossene Gesellschaft", [e["titel"] for e in self.events])

    def test_pflichtfelder(self):
        for e in self.events:
            for feld in PFLICHT:
                self.assertTrue(e[feld], feld)
            self.assertIn(e["ort"], ("Bilker Bunker", "Schleuse Zwei"))
            self.assertEqual(e["adresse"], "Aachener Str. 39, 40223 Düsseldorf")
            self.assertTrue(e["quelle_url"].startswith("https://bilkerbunker.de/"))
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])

    def test_konzert(self):
        e = self.events[0]
        self.assertEqual(e["titel"], "Davina Soleil & Ilyas Samy – live")
        self.assertEqual(e["datum"], "2026-11-25")
        self.assertEqual(e["uhrzeit"], "20:00")   # Beginn, nicht Einlass 19 Uhr
        self.assertEqual(e["ort"], "Schleuse Zwei")
        self.assertEqual(e["kategorie"], "musik")
        self.assertEqual(e["preis"], "VVK 10 € (zzgl. Geb.) / AK 15 €")

    def test_barabend(self):
        e = next(x for x in self.events if x["titel"].startswith("Barabend"))
        self.assertEqual(e["kategorie"], "nightlife")
        self.assertEqual(e["uhrzeit"], "20:00")
        self.assertEqual(e["preis"], "kostenlos")

    def test_einlass_und_beginn_gleich(self):
        e = next(x for x in self.events if x["titel"] == "RAR Vol. X")
        self.assertEqual(e["uhrzeit"], "19:00")

    def test_hilfsfunktionen(self):
        self.assertEqual(modul._uhrzeit("/ Einlass 18:30 / Beginn ca. 20 Uhr"), "20:00")
        self.assertEqual(modul._uhrzeit("/ Einlass 21 Uhr"), "21:00")
        self.assertIsNone(modul._uhrzeit(""))
        self.assertEqual(modul._ort("Lesung im Ausstellungsraum"), "Bilker Bunker")
        self.assertEqual(modul._ort("Konzert in der Schleuse Zwei"), "Schleuse Zwei")
        self.assertEqual(modul._kategorie("Vernissage: Max Frintrop", ""), "kultur")
        self.assertEqual(modul._naechste_seite(self.html), "https://bilkerbunker.de/schleuse-zwei?page=1")

    def test_zeitfenster(self):
        events = modul._termine_aus_html(self.html, date(2026, 12, 5), date(2026, 12, 10))
        self.assertEqual({e["datum"] for e in events}, {"2026-12-09"})


if __name__ == "__main__":
    unittest.main()
