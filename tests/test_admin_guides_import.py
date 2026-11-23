"""
Tests zu Stufe 3b des Admin-Dashboards (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.7, Entscheidung Q6):
Die Importe lassen die im Admin-Bereich gepflegten Felder stehen.
"""
import unittest

from scraper.spielplaetze.redaktion import redaktion_behalten
from scraper.weihnachtsmaerkte.import_maerkte import dashboard_felder_behalten


class WeihnachtsmaerkteImport(unittest.TestCase):
    def test_rang_ausschluss_freischaltung_aus_der_datenbank(self):
        csv = {"schluessel": "riesenrad", "top5_rang": 1, "ausgeschlossen": None, "freigeschaltet_am": None, "art": "riesenrad"}
        db = {"top5_rang": 3, "ausgeschlossen": "Auftraggeber: dieses Jahr nicht", "freigeschaltet_am": "2026-11-17"}
        wm, hinweise = dashboard_felder_behalten(csv, db)
        self.assertEqual(wm["top5_rang"], 3)
        self.assertEqual(wm["ausgeschlossen"], "Auftraggeber: dieses Jahr nicht")
        self.assertEqual(wm["freigeschaltet_am"], "2026-11-17")
        self.assertEqual(wm["art"], "riesenrad")  # übrige Felder aus der CSV
        self.assertEqual(len(hinweise), 2)

    def test_gleiche_werte_ohne_hinweis(self):
        wm, hinweise = dashboard_felder_behalten({"top5_rang": None, "ausgeschlossen": ""}, {"top5_rang": None})
        self.assertEqual(hinweise, [])
        self.assertIsNone(wm["top5_rang"])


class SpielplaetzeImport(unittest.TestCase):
    def test_ohne_redaktion_gilt_der_import(self):
        neu = {"pruefung": ["access_private"], "bestaetigt": [], "ausgeschlossen": None}
        self.assertEqual(redaktion_behalten(neu, {"bestaetigt": ["access_private"]}), neu)

    def test_redaktion_schuetzt_bestaetigt_und_ausgeschlossen(self):
        neu = {"pruefung": ["access_private"], "bestaetigt": [], "ausgeschlossen": None, "name_quelle": "stadt"}
        aktuell = {"bestaetigt": ["access_private"], "ausgeschlossen": "Schulhof", "redaktion": ["ausgeschlossen", "bestaetigt"]}
        ergebnis = redaktion_behalten(neu, aktuell)
        self.assertEqual(ergebnis["bestaetigt"], ["access_private"])
        self.assertEqual(ergebnis["ausgeschlossen"], "Schulhof")
        self.assertEqual(ergebnis["pruefung"], ["access_private"])
        self.assertEqual(ergebnis["redaktion"], ["ausgeschlossen", "bestaetigt"])

    def test_nur_erlaubte_felder(self):
        neu = {"pruefung": ["name_unklar"]}
        ergebnis = redaktion_behalten(neu, {"pruefung": [], "redaktion": ["pruefung"]})
        self.assertEqual(ergebnis["pruefung"], ["name_unklar"])


if __name__ == "__main__":
    unittest.main()
