"""Tests für den OSM-Abgleich der Spielplätze (python -m unittest tests.test_spielplaetze_osm)."""
import unittest

from scraper.spielplaetze import osm_abgleich as oa

M = 1 / 111195.0  # Grad Breite je Meter
LAT, LON = 51.22, 6.78


def ost(m):  # Grad Länge je Meter in dieser Breite
    return m / (111320.0 * 0.6266)


def quadrat(nord_m, ost_m, groesse_m):
    a = (LAT + nord_m * M, LON + ost(ost_m))
    b = (a[0] + groesse_m * M, a[1] + ost(groesse_m))
    return [{"lat": a[0], "lon": a[1]}, {"lat": a[0], "lon": b[1]}, {"lat": b[0], "lon": b[1]},
            {"lat": b[0], "lon": a[1]}, {"lat": a[0], "lon": a[1]}]


def flaeche(i, tags, nord_m, ost_m, groesse_m):
    return {"type": "way", "id": i, "tags": tags, "geometry": quadrat(nord_m, ost_m, groesse_m), "timestamp": "2025-01-01T00:00:00Z"}


def punkt(i, tags, nord_m=0.0, ost_m=0.0):
    return {"type": "node", "id": i, "tags": tags, "lat": LAT + nord_m * M, "lon": LON + ost(ost_m), "timestamp": "2025-01-01T00:00:00Z"}


def zeile(ausstattung=None, extras=None, pruefung=None, quelle="stadt-duesseldorf", eintritt=None):
    sp = {"quelle": quelle, "ausstattung": ausstattung or {}, "extras": extras or {}, "pruefung": pruefung or [],
          "teile": [{"objektschluessel": "1/1"}]}
    if eintritt:
        sp["eintritt"] = eintritt
    return {"id": "z1", "name": "Test", "slug": "test", "latitude": LAT, "longitude": LON, "extras": {"spielplatz": sp}}


def auswerten(elemente, **z):
    return oa.zeile_auswerten(zeile(**z), oa.osm_aufbereiten({"elements": elemente}))


class ZuordnungTest(unittest.TestCase):
    def test_punkt_in_einer_flaeche(self):
        e = auswerten([flaeche(1, {"leisure": "playground"}, -20, -20, 40), punkt(2, {"leisure": "playground"}, 30)])
        self.assertEqual((e["art"], e["neu"]["osm"]["id"]), ("in_flaeche", "way/1"))

    def test_zwei_flaechen_mehrdeutig(self):
        e = auswerten([flaeche(1, {"leisure": "playground"}, -20, -20, 40),
                       flaeche(2, {"leisure": "playground", "playground": "slide"}, -10, -10, 20)])
        self.assertEqual(e["art"], "mehrdeutig")
        self.assertIn("zuordnung_mehrdeutig", e["neu"]["pruefung"])
        self.assertEqual(e["neu"]["ausstattung"], {})

    def test_ohne_flaeche_ein_kandidat_bis_60_m(self):
        self.assertEqual(auswerten([punkt(1, {"leisure": "playground"}, 50)])["art"], "nah")
        self.assertEqual(auswerten([punkt(1, {"leisure": "playground"}, 70)])["art"], "kein_treffer")
        self.assertEqual(auswerten([punkt(1, {"leisure": "playground"}, 20),
                                    punkt(2, {"leisure": "playground"}, -20)])["art"], "mehrdeutig")


class GeraeteTest(unittest.TestCase):
    def test_geraete_in_der_flaeche(self):
        e = auswerten([flaeche(1, {"leisure": "playground"}, -20, -20, 40),
                       punkt(2, {"playground": "slide;swing"}, 5), punkt(3, {"playground": "sandpit"}, 50),
                       punkt(4, {"playground": "springy"}, -5)])
        self.assertEqual(e["neu"]["osm"]["geraete_roh"], ["slide", "springy", "swing"])
        self.assertEqual(set(e["neu"]["ausstattung"]), {"rutsche", "schaukel", "federwippe"})
        self.assertEqual(e["neu"]["ausstattung"]["rutsche"], {"wert": "ja", "quelle": "osm", "beleg": "way/1 playground=slide"})

    def test_geraete_um_osm_punkt(self):
        e = auswerten([punkt(1, {"leisure": "playground"}, 10), punkt(2, {"playground": "zipwire"}, 35),
                       punkt(3, {"playground": "slide"}, 45)])
        self.assertEqual(e["neu"]["osm"]["geraete_roh"], ["zipwire"])

    def test_sichtung_und_zitat_bleiben(self):
        e = auswerten([flaeche(1, {"leisure": "playground"}, -20, -20, 40), punkt(2, {"playground": "slide"})],
                      ausstattung={"rutsche": {"wert": "nein", "quelle": "sichtung"},
                                   "schaukel": {"wert": "ja", "quelle": "osm"}})
        self.assertEqual(e["neu"]["ausstattung"], {"rutsche": {"wert": "nein", "quelle": "sichtung"}})  # alte OSM-Schaukel weg
        self.assertTrue(e["konflikte"])

    def test_alter_rollstuhl_eintritt_access(self):
        e = auswerten([flaeche(1, {"leisure": "playground", "min_age": "3", "max_age": "12", "wheelchair": "limited",
                                   "fee": "yes", "access": "private"}, -20, -20, 40)])
        self.assertEqual((e["neu"]["osm"]["min_age"], e["neu"]["osm"]["max_age"]), ("3", "12"))
        self.assertEqual(e["neu"]["extras"]["rollstuhl"]["wert"], "teilweise")
        self.assertEqual(e["neu"]["eintritt"], "ja")
        self.assertIn("access_private", e["neu"]["pruefung"])

    def test_osm_codes_neu_gesetzt(self):
        e = auswerten([flaeche(1, {"leisure": "playground"}, -20, -20, 40)],
                      pruefung=["access_private", "zuordnung_mehrdeutig", "bezirk_abweichend"])
        self.assertEqual(e["neu"]["pruefung"], ["bezirk_abweichend"])
        self.assertIsNone(e["neu"]["eintritt"])

    def test_abenteuer_eintritt_bleibt(self):
        e = auswerten([flaeche(1, {"leisure": "playground", "fee": "yes", "access": "customers"}, -20, -20, 40)],
                      quelle="abenteuer", eintritt="nein")
        self.assertNotIn("eintritt", e["neu"])
        self.assertTrue(e["fee_hinweis"])
        self.assertIn("access_private", e["neu"]["pruefung"])


class SportTest(unittest.TestCase):
    def test_sport_bis_40_m_vom_punkt(self):
        e = auswerten([punkt(1, {"leisure": "pitch", "sport": "table_tennis"}, 20),
                       flaeche(2, {"leisure": "pitch", "sport": "soccer"}, 30, -10, 20),
                       flaeche(3, {"leisure": "pitch", "sport": "basketball"}, 60, -10, 20)])
        self.assertEqual(set(e["neu"]["ausstattung"]), {"tischtennis", "fussball"})

    def test_sport_bis_40_m_von_der_flaeche(self):
        e = auswerten([flaeche(1, {"leisure": "playground"}, -20, -20, 80),
                       flaeche(2, {"leisure": "pitch", "sport": "basketball"}, 90, 0, 20)])
        self.assertIn("basketball", e["neu"]["ausstattung"])

    def test_nicht_oeffentlich_und_multi(self):
        e = auswerten([flaeche(1, {"leisure": "pitch", "sport": "soccer", "access": "private"}, 0, 0, 20),
                       flaeche(2, {"leisure": "pitch", "sport": "multi"}, 0, 0, 20)])
        self.assertEqual(e["neu"]["ausstattung"], {})
        self.assertEqual(e["neu"]["osm"]["sport_roh"], ["multi"])

    def test_volleyball_und_skaten_nebengeraet(self):
        e = auswerten([punkt(1, {"leisure": "pitch", "sport": "beachvolleyball;skateboard"}, 10)])
        self.assertEqual(set(e["neu"]["ausstattung"]), {"volleyball", "skaten"})


if __name__ == "__main__":
    unittest.main()
