"""
Tests zu Stufe 3c des Admin-Dashboards (Plan docs/plan-admin-dashboard-2026-11-23.md, 3.5 und 4.7):
Vorschläge für Ortsnamen, Ortszuordnung und Adressen statt SQL-Dateien. Felder in redaktion_felder bleiben.
"""
import unittest

from pipeline.ort_zuordnung import OrteIndex
from pipeline.vorschlaege import adresse_vorschlaege, ort_id_vorschlaege, ortsname_vorschlaege


def event(i, ort, **kw):
    return {"id": f"e{i}", "titel": kw.pop("titel", f"Konzert {i}"), "datum": "2026-12-01", "uhrzeit": kw.pop("uhrzeit", None),
            "ort": ort, "reihe_id": None, "abgelehnt": False, "redaktion_felder": [], **kw}


class Ortsnamen(unittest.TestCase):
    def test_ein_vorschlag_je_alter_name(self):
        events = [event(1, "Mitsubishi Electric HALLE"), event(2, "Mitsubishi Electric HALLE"), event(3, "Mitsubishi Electric Halle")]
        zeilen = ortsname_vorschlaege(events, [])
        self.assertEqual(len(zeilen), 1)
        v = zeilen[0]
        self.assertEqual(v["art"], "ortsname")
        self.assertEqual(v["schluessel"], "Mitsubishi Electric HALLE→Mitsubishi Electric Halle")
        self.assertEqual(v["vorschlag"]["events"], ["e1", "e2"])

    def test_redaktion_schuetzt_ort(self):
        events = [event(1, "Mitsubishi Electric HALLE", redaktion_felder=["ort"])]
        self.assertEqual(ortsname_vorschlaege(events, []), [])

    def test_reihen_schluessel_schon_vergeben_kein_vorschlag(self):
        from pipeline.reihen_zuordnen import reihen_schluessel

        e = event(1, "Pitcher", titel="Rock am Montag", reihe_id="r1")
        neu_k = reihen_schluessel("Rock am Montag", "Pitcher Rock HQ")
        alt_k = reihen_schluessel("Rock am Montag", "Pitcher")
        if not neu_k or neu_k == alt_k:
            self.skipTest("Schlüssel unterscheidet Groß-/Kleinschreibung nicht – kein Reihen-Fall")
        self.assertEqual(ortsname_vorschlaege([e], [{"id": "r2", "schluessel": neu_k, "ort": "x"}]), [])


class Ortszuordnung(unittest.TestCase):
    def setUp(self):
        self.index = OrteIndex.aus_zeilen([
            {"id": "o1", "name": "zakk", "slug": "zakk", "typ": "club", "aktiv": True, "extras": {"club": {"event_orte": ["zakk"]}}},
        ])

    def test_vorschlag_nur_bei_abweichung(self):
        events = [event(1, "zakk"), event(2, "zakk", ort_id="o1"), event(3, "Irgendwo")]
        zeilen = ort_id_vorschlaege(events, self.index)
        self.assertEqual([z["schluessel"] for z in zeilen], ["e1:o1"])
        self.assertEqual(zeilen[0]["vorschlag"]["ort_name"], "zakk")

    def test_redaktion_schuetzt_ort_id(self):
        self.assertEqual(ort_id_vorschlaege([event(1, "zakk", redaktion_felder=["ort_id"])], self.index), [])


class Adressen(unittest.TestCase):
    def test_nur_gefundene_und_ungeschuetzte(self):
        events = [
            event(1, "zakk", adresse="Fichtenstraße 40, 40233 Düsseldorf", stadtteil=None, quelle_name="Rausgegangen"),
            event(2, "zakk", adresse=None),
            event(3, "zakk", adresse="Fichtenstraße 40, 40233 Düsseldorf", redaktion_felder=["adresse"]),
        ]
        zeilen = adresse_vorschlaege(events)
        self.assertEqual([z["schluessel"] for z in zeilen], ["e1"])
        self.assertEqual(zeilen[0]["vorschlag"]["adresse"], "Fichtenstraße 40, 40233 Düsseldorf")

    def test_stadtteil_nur_wenn_leer_und_ungeschuetzt(self):
        e = event(1, "zakk", adresse="Fichtenstraße 40, 40233 Düsseldorf", stadtteil="Flingern-Süd")
        self.assertIsNone(adresse_vorschlaege([e])[0]["vorschlag"]["stadtteil"])
        g = event(2, "zakk", adresse="Fichtenstraße 40, 40233 Düsseldorf", stadtteil=None, redaktion_felder=["stadtteil"])
        self.assertIsNone(adresse_vorschlaege([g])[0]["vorschlag"]["stadtteil"])


if __name__ == "__main__":
    unittest.main()
