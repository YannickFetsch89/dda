"""
Tests zu Stufe 5b des Admin-Dashboards (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.10): Quellen an/aus und die
gemeinsame Slug-Prüfliste mit web/tests/admin-meldungen.test.ts.
"""
import json
import unittest
from pathlib import Path

from pipeline.quellen import abgeschaltet_aus_zeilen, meldung
from pipeline.slug_generator import slug_erzeugen, slug_mit_suffix
from pipeline.stadtteil_mapper import PLZ_STADTTEIL

WURZEL = Path(__file__).resolve().parents[1]


class Quellen(unittest.TestCase):
    def test_nur_abgeschaltete(self):
        zeilen = [{"quelle": "zakk", "aktiv": False, "grund": " Wartung "}, {"quelle": "Tonhalle", "aktiv": True}, {"quelle": "", "aktiv": False}]
        self.assertEqual(abgeschaltet_aus_zeilen(zeilen), {"zakk": "Wartung"})

    def test_meldung(self):
        self.assertEqual(meldung("Wartung"), "Im Admin-Bereich abgeschaltet: Wartung")
        self.assertEqual(meldung(""), "Im Admin-Bereich abgeschaltet")

    def test_namen_passen_in_die_tabelle(self):
        import main
        self.assertTrue(all(1 <= len(name) <= 120 for name, _, _ in main.QUELLEN))


class SlugsWieWebsite(unittest.TestCase):
    def test_gemeinsame_pruefliste(self):
        f = json.loads((WURZEL / "tests" / "fixtures" / "slugs.json").read_text(encoding="utf-8"))
        for s in f["slugs"]:
            self.assertEqual(slug_erzeugen(s["titel"], s["ort"], s["datum"]), s["slug"])
        for s in f["suffix"]:
            self.assertEqual(slug_mit_suffix(s["basis"], set(s["vergeben"])), s["slug"])

    def test_plz_tabelle_der_website_aktuell(self):
        web = json.loads((WURZEL / "web" / "lib" / "plz-stadtteil.json").read_text(encoding="utf-8"))
        self.assertEqual(web, PLZ_STADTTEIL, "web/lib/plz-stadtteil.json neu aus PLZ_STADTTEIL erzeugen")


if __name__ == "__main__":
    unittest.main()
