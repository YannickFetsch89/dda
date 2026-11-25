"""
test_rsh_hochschule.py – Tests für scraper/tier2/rsh_hochschule.py ohne Netz.
Fixtures: tests/fixtures/rsh_hochschule_liste.html (Auszug der Veranstaltungsliste vom 25.11.2026, gekürzt auf
November + Anfang Dezember, Beschreibungstexte entfernt) und rsh_hochschule_detail.html (eine Detailseite).
"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import rsh_hochschule as modul

FIXTURES = Path(__file__).parent / "fixtures"
KATEGORIEN = {"musik", "kultur", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife", "family",
              "dating", "sonstiges"}


class TestRshHochschule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = (FIXTURES / "rsh_hochschule_liste.html").read_text(encoding="utf-8")
        cls.events = modul._termine_aus_html(html, date(2026, 11, 25), date(2027, 3, 25))

    def _finde(self, titel, datum):
        return next(e for e in self.events if e["titel"] == titel and e["datum"] == datum)

    def test_anzahl_und_pflichtfelder(self):
        self.assertEqual(len(self.events), 14)
        for e in self.events:
            for feld in ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status"):
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertIn(e["kategorie"], KATEGORIEN)
            self.assertTrue(e["quelle_url"].startswith("https://www.rsh-duesseldorf.de/veranstaltungen/details/"))
            self.assertIsNone(e["beschreibung"])
            self.assertFalse(e["bild_generiert"])
            self.assertEqual(e["quelle_name"], "Robert Schumann Hochschule")
            if e["bild_url"]:
                self.assertTrue(e["bild_url"].startswith("https://www.rsh-duesseldorf.de/"))

    def test_saal_der_hochschule(self):
        e = self._finde("Musik für Oboe", "2026-11-27")
        self.assertEqual(e["uhrzeit"], "19:30")
        self.assertEqual(e["ort"], "Robert Schumann Hochschule Düsseldorf")
        self.assertEqual(e["adresse"], "Fischerstraße 110, 40476 Düsseldorf")
        self.assertEqual(e["kategorie"], "musik")

    def test_gleicher_tag_ohne_datum_in_der_zeile(self):
        # „Musik für Fagott“ steht als zweite Zeile am 26.11. (nur Uhrzeit in der Zeile)
        e = self._finde("Musik für Fagott", "2026-11-26")
        self.assertEqual(e["ort"], "Robert Schumann Hochschule Düsseldorf")

    def test_fremder_ort_in_duesseldorf(self):
        e = self._finde("schumann@heine: Zwiegespräche", "2026-11-26")
        self.assertEqual((e["ort"], e["adresse"]), ("Haus der Universität", "Schadowpl. 14, 40212 Düsseldorf"))
        e = self._finde("Sinfoniekonzert: Schostakowitsch 11", "2026-11-29")
        self.assertEqual(e["ort"], "Tonhalle Düsseldorf")
        self.assertEqual(e["uhrzeit"], "18:00")   # „18 Uhr“ ohne Minuten
        e = self._finde('Musik im Advent - "Ave maris stella"', "2026-12-04")
        self.assertEqual(e["ort"], "Neanderkirche")

    def test_ausserhalb_duesseldorf_weggelassen(self):
        # Am 25.11. spielt das Sinfonieorchester in der Historischen Stadthalle Wuppertal
        self.assertFalse(any(e["datum"] == "2026-11-25" for e in self.events))

    def test_zeitfenster(self):
        events = modul._termine_aus_html((FIXTURES / "rsh_hochschule_liste.html").read_text(encoding="utf-8"),
                                         date(2026, 12, 1), date(2026, 12, 2))
        self.assertTrue(events)
        self.assertTrue(all("2026-12-01" <= e["datum"] <= "2026-12-02" for e in events))

    def test_detailseite_preis(self):
        e = dict(self._finde("schumann@heine: Zwiegespräche", "2026-11-26"))
        modul._details_ergaenzen(e, (FIXTURES / "rsh_hochschule_detail.html").read_text(encoding="utf-8"))
        self.assertEqual(e["preis"], "kostenlos")
        self.assertIsNone(e["ticket_url"])

    def test_ortszuordnung(self):
        self.assertIsNone(modul._ort_und_adresse("Historische Stadthalle Wuppertal"))
        self.assertIsNone(modul._ort_und_adresse("WDR 3"))
        self.assertEqual(modul._ort_und_adresse("Partika Saal")[0], "Robert Schumann Hochschule Düsseldorf")
        self.assertEqual(modul._ort_und_adresse("")[0], "Robert Schumann Hochschule Düsseldorf")
        self.assertEqual(modul._ort_und_adresse("Orangerie von Schloss Benrath")[0], "Schloss Benrath")

    def test_uhrzeit(self):
        self.assertEqual(modul._uhrzeit("19:30 Uhr"), "19:30")
        self.assertEqual(modul._uhrzeit("10-17 Uhr"), "10:00")
        self.assertIsNone(modul._uhrzeit("ganztägig"))


if __name__ == "__main__":
    unittest.main()
