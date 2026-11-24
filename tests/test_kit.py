"""Tests für den Scraper KIT – Kunst im Tunnel (Quellen-Ausbau V1, ohne Netz).
python -m unittest tests.test_kit"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier2 import kit as k

JSON = (Path(__file__).parent / "fixtures" / "kit_posts.json").read_text(encoding="utf-8")
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")
FELDER = {"titel", "datum", "uhrzeit", "ort", "adresse", "kategorie", "beschreibung", "preis", "quelle_name",
          "quelle_url", "bild_url", "bild_generiert", "status"}


class KitTest(unittest.TestCase):
    def setUp(self):
        self.events = k._termine_aus_json(JSON, date(2026, 11, 24), date(2027, 3, 24))

    def _event(self, anfang: str) -> dict:
        return next(e for e in self.events if e["titel"].startswith(anfang))

    def test_termine_aus_dem_auszug(self):
        self.assertEqual(len(self.events), 9)   # 10 Beiträge, der Schließtag „closed“ fehlt
        erstes = self.events[0]
        self.assertEqual(erstes["titel"], "Eröffnung: In jeder Sprache sitzen andere Augen")
        self.assertEqual((erstes["datum"], erstes["uhrzeit"]), ("2026-11-27", "18:00"))
        self.assertEqual(erstes["ort"], "KIT - Kunst im Tunnel")
        self.assertEqual(erstes["adresse"], "Mannesmannufer 1, 40213 Düsseldorf")
        self.assertEqual(erstes["kategorie"], "kultur")
        self.assertEqual(erstes["preis"], "kostenlos")
        self.assertEqual(erstes["quelle_url"], "https://www.kunst-im-tunnel.de/programm/kalender/"
                                               "eroeffnung-in-jeder-sprache-sitzen-andere-augen/")

    def test_pflichtfelder(self):
        for e in self.events:
            self.assertEqual(set(e), FELDER)
            for feld in PFLICHT:
                self.assertTrue(e[feld], f"{feld} leer in {e}")
            self.assertEqual(e["quelle_name"], "KIT – Kunst im Tunnel")
            self.assertRegex(e["uhrzeit"], r"^\d{2}:\d{2}$")
            self.assertIsNone(e["beschreibung"])

    def test_weggelassen_und_sonderfaelle(self):
        titel = [e["titel"] for e in self.events]
        self.assertNotIn("closed", titel)
        # „<s>in der Kunsthalle</s> ACHTUNG ORTSWECHSEL: Der Kurs findet im KIT statt!“ → bleibt drin
        pottery = self._event("Pottery Lab (Kurs 3 / Tag 2)")
        self.assertEqual((pottery["datum"], pottery["uhrzeit"]), ("2026-11-29", "12:15"))
        auswaerts = {"title": {"rendered": "Kurs"}, "acf": {"date": 1795954500}, "link": "",
                     "content": {"rendered": "<p>Sonntag, 29. November 2026<br />12 Uhr</p><p>in der Kunsthalle</p>"}}
        self.assertIsNone(k._termin_aus_beitrag(auswaerts))
        architektur = self._event("Architekturführungen")
        self.assertEqual(architektur["datum"], "2026-12-19")   # Text „Samstag, 19. Dezember 2026“ statt ACF 12.12.
        self.assertEqual(architektur["preis"], "im Eintritt inbegriffen")
        self.assertEqual(self._event("Familientag")["kategorie"], "family")
        self.assertEqual(self._event("Schreibwerkstatt")["preis"], "12 €")
        self.assertEqual(self._event("Schreibwerkstatt")["datum"], "2027-02-23")

    def test_hilfsfunktionen(self):
        self.assertEqual(k._acf_zeit(1795802400), ("2026-11-27", "18:00"))
        self.assertEqual(k._acf_zeit(1798070400), ("2026-12-24", None))   # 00:00 → keine Uhrzeit
        self.assertEqual(k._uhrzeit_aus_text("Sonntag, 29. November 2026 12.15–14.15 Uhr"), "12:15")
        self.assertEqual(k._uhrzeit_aus_text("Sonntag, 13. Dezember 2026 11–18 Uhr"), "11:00")
        self.assertIsNone(k._datum_aus_text("Freitag, 28. November 2026"))   # Wochentag passt nicht
        self.assertEqual(k._termine_aus_json(JSON, date(2027, 3, 1), date(2027, 3, 24)), [])


if __name__ == "__main__":
    unittest.main()
