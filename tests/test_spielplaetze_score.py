"""Tests für Schritt 6 der Spielplätze: Alter, Score, Top, Freischaltung (python -m unittest tests.test_spielplaetze_score)."""
import json
import unittest
from pathlib import Path

from scraper.spielplaetze import score as sc

WURZEL = Path(__file__).resolve().parents[1]


def ja(quelle="osm"):
    return {"wert": "ja", "quelle": quelle, "beleg": "Beleg"}


def zeile(zid="z", aktiv=False, **sp):
    basis = {"quelle": "stadt-duesseldorf", "typ": "kinder", "groesse_m2": 1000.0, "pruefung": [], "bestaetigt": []}
    return {"id": zid, "name": zid, "slug": zid, "aktiv": aktiv, "extras": {"spielplatz": {**basis, **sp}}}


class FreischaltTest(unittest.TestCase):
    def test_freischaltbar(self):
        self.assertTrue(sc.freischaltbar(zeile()))
        self.assertFalse(sc.freischaltbar(zeile(ausgeschlossen="Dublette")))
        self.assertFalse(sc.freischaltbar(zeile(pruefung=["name_unklar"], bestaetigt=["name_unklar"])))
        self.assertFalse(sc.freischaltbar(zeile(pruefung=["kein_stadtteil"])))
        self.assertFalse(sc.freischaltbar(zeile(pruefung=["access_private"])))
        self.assertTrue(sc.freischaltbar(zeile(pruefung=["access_private"], bestaetigt=["access_private"])))
        self.assertFalse(sc.freischaltbar(zeile(pruefung=["gruppe_gemischt"])))
        self.assertTrue(sc.freischaltbar(zeile(pruefung=["bezirk_abweichend", "zuordnung_mehrdeutig"])))
        self.assertFalse(sc.freischaltbar(zeile(aktiv=True)))

    def test_fehlende_arrays_wie_leer(self):
        z = zeile()
        del z["extras"]["spielplatz"]["pruefung"], z["extras"]["spielplatz"]["bestaetigt"]
        self.assertTrue(sc.freischaltbar(z))

    def test_abgeschaltet_wieder_an_nur_ohne_sperrcode(self):
        self.assertTrue(sc.freischaltbar(zeile(freigeschaltet_am="2026-12-01")))
        self.assertFalse(sc.freischaltbar(zeile(freigeschaltet_am="2026-12-01", pruefung=["kein_stadtteil"])))

    def test_abschalten_und_aktiv_mit_neuem_sperrcode(self):
        self.assertTrue(sc.abzuschalten(zeile(aktiv=True, ausgeschlossen="abgebaut")))
        self.assertFalse(sc.abzuschalten(zeile(aktiv=True, pruefung=["access_private"])))  # bleibt aktiv
        self.assertTrue(sc.danach_aktiv(zeile(aktiv=True, pruefung=["access_private"])))

    def test_sql_datei(self):
        sql = (WURZEL / "database" / "spielplaetze_freischalten.sql").read_text(encoding="utf-8")
        for teil in ("COALESCE(extras->'spielplatz'->'pruefung', '[]'::jsonb)", "RETURNING slug, aktiv", "AND aktiv = false",
                     "AND aktiv = true", "array['name_unklar', 'kein_stadtteil']", "? 'access_private'", "? 'gruppe_gemischt'",
                     "extras->'spielplatz'->>'ausgeschlossen' IS NULL", "extras->'spielplatz'->>'ausgeschlossen' IS NOT NULL",
                     "->>'freigeschaltet_am' IS NULL"):
            self.assertIn(teil, sql)
        self.assertNotIn("DELETE", sql.upper())


class IndexierbarTest(unittest.TestCase):
    def test_gemeinsame_fixture(self):
        faelle = json.loads((WURZEL / "tests" / "fixtures" / "spielplatz_indexierbar.json").read_text(encoding="utf-8"))
        for f in faelle:
            self.assertEqual(sc.ist_indexierbar(f["spielplatz"]), f["erwartet"], f["fall"])


class AlterTest(unittest.TestCase):
    def sp(self, *geraete, **mehr):
        return {"ausstattung": {g: ja() for g in geraete}, **mehr}

    def test_vermutet(self):
        self.assertIsNone(sc.alter_bestimmen(self.sp("rutsche")))                                  # 1. weniger als zwei
        self.assertEqual(sc.alter_bestimmen(self.sp("sandkasten", "klettern"))["wert"], "alle")    # 2.
        self.assertEqual(sc.alter_bestimmen(self.sp("sandkasten", "federwippe"))["wert"], "0-3")   # 3.
        self.assertEqual(sc.alter_bestimmen(self.sp("klettern", "rutsche"))["wert"], "6-12")       # 4.
        self.assertEqual(sc.alter_bestimmen(self.sp("rutsche", "schaukel"))["wert"], "3-6")        # 5.
        self.assertIsNone(sc.alter_bestimmen(self.sp("wasserspiel", "wippe")))                     # 6.
        self.assertEqual(sc.alter_bestimmen(self.sp("rutsche", "schaukel"))["art"], "vermutlich")

    def test_sport_zaehlt_nicht(self):
        self.assertIsNone(sc.alter_bestimmen(self.sp("tischtennis", "fussball")))

    def test_belegt_vor_vermutet(self):
        osm = self.sp("sandkasten", "klettern", osm={"min_age": "6", "max_age": "14", "tags_stand": "2024-01-01T00:00:00Z"})
        self.assertEqual(sc.alter_bestimmen(osm)["wert"], "6-12")
        self.assertEqual(sc.alter_bestimmen(osm)["art"], "belegt")
        stadt = self.sp("rutsche", "schaukel", teile=[{"stadt_name": "AM ANGERBACH, KSP (Kleinkind)"},
                                                      {"stadt_name": "AM ANGERBACH, KSP (Schulkind)"}])
        self.assertEqual(sc.alter_bestimmen(stadt)["wert"], "alle")
        self.assertEqual(sc._band_aus_spanne(0, 3), "0-3")
        self.assertEqual(sc._band_aus_spanne(3, 6), "3-6")
        self.assertEqual(sc._band_aus_spanne(2, 10), "alle")

    def test_juengere_quelle_gewinnt(self):
        sp = {"alter": {"wert": "3-6", "art": "belegt", "quelle": "zitat", "beleg": "für Kinder von 3 bis 6 Jahren"},
              "profil_stand": "2025-05", "osm": {"min_age": "6", "tags_stand": "2021-01-01T00:00:00Z"},
              "teile": [{"stadt_name": "X, KSP (Schulkind)"}]}
        self.assertEqual(sc.alter_bestimmen(sp)["quelle"], "zitat")  # Zitat 2025 jünger als OSM 2021 und Stadt 2020
        sp["osm"]["tags_stand"] = "2026-01-01T00:00:00Z"
        self.assertEqual(sc.alter_bestimmen(sp)["quelle"], "osm")


class ScoreTest(unittest.TestCase):
    def test_teilwerte_und_grenzen(self):
        voll = zeile("a", typ="wasser", ausstattung={g: ja() for g in sc.FILTER_GERAETE},
                     extras={k: {"wert": "ja"} for k in sc.EXTRAS_SCORE} | {"rollstuhl": {"wert": "ja"}},
                     google={"rating": 5.0, "anzahl": 10000}, groesse_m2=5000.0)
        leer = zeile("b", groesse_m2=100.0)
        menge = sc.perzentil_menge([voll, leer])
        self.assertEqual(sc.score(voll, menge), 1.0)
        self.assertAlmostEqual(sc.score(leer, menge), 0.15 * 0.5, places=4)  # Größe 0 (kleinster), Google neutral

    def test_perzentil_menge(self):
        z = [zeile("a", groesse_m2=100.0), zeile("b", groesse_m2=200.0, ausgeschlossen="x"),
             zeile("c", groesse_m2=300.0, pruefung=["name_unklar"]), zeile("d", aktiv=True, groesse_m2=400.0, pruefung=["access_private"]),
             zeile("e", quelle="abenteuer", groesse_m2=None)]
        self.assertEqual(sc.perzentil_menge(z), [100.0, 400.0])
        self.assertEqual(sc.score(z[1], sc.perzentil_menge(z)), sc.score(zeile("x", groesse_m2=1.0, ausgeschlossen="x"), [100.0, 400.0]))

    def test_abenteuer_groesse_neutral(self):
        a = zeile("a", quelle="abenteuer", typ="abenteuer", groesse_m2=None)
        self.assertAlmostEqual(sc.score(a, [1.0, 2.0]), 0.2 * 0.5 + 0.2 * 1 + 0.15 * 0.5, places=4)

    def test_top_20_prozent(self):
        b = "Beschreibung mit Inhalt."
        z = [zeile(f"p{i}", beschreibung=b, ausstattung={"rutsche": ja(), "schaukel": ja()}, groesse_m2=float(i * 100))
             for i in range(1, 11)]
        z.append(zeile("ausgeschl", beschreibung=b, ausstattung={"rutsche": ja(), "schaukel": ja()}, ausgeschlossen="x", groesse_m2=5000.0))
        z.append(zeile("duenn", groesse_m2=6000.0))  # nicht indexierbar
        ergebnis = sc.berechnen(z)
        top = {k for k, v in ergebnis.items() if v["top"]}
        self.assertEqual(top, {"p10", "p9"})  # 20 % von 10 = 2


if __name__ == "__main__":
    unittest.main()
