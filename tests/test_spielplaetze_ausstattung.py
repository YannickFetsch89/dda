"""Tests für die Ausstattung von Hand (python -m unittest tests.test_spielplaetze_ausstattung)."""
import tempfile
import unittest
from pathlib import Path

from scraper.spielplaetze import ausstattung_import as ai

KOPF = "schluessel;merkmal;wert;beleg;stand\n"


def lesen(inhalt):
    with tempfile.TemporaryDirectory() as d:
        pfad = Path(d) / "ausstattung.csv"
        pfad.write_text(KOPF + inhalt, encoding="utf-8")
        return ai.ausstattung_lesen(pfad)


def zeile(zid, schluessel, ausstattung=None, extras=None, abenteuer=False):
    sp = {"ausstattung": ausstattung or {}, "extras": extras or {}}
    if abenteuer:
        sp.update(quelle="abenteuer", schluessel=schluessel[0])
    else:
        sp.update(quelle="stadt-duesseldorf", teile=[{"objektschluessel": s} for s in schluessel])
    return {"id": zid, "name": zid, "slug": zid, "extras": {"spielplatz": sp}}


def eintrag(schluessel="1/1", merkmal="tischtennis", wert="ja"):
    return {"schluessel": schluessel, "merkmal": merkmal, "wert": wert, "beleg": "vor Ort gesehen", "stand": "2026-11-13"}


class LesenTest(unittest.TestCase):
    def test_fehlende_datei(self):
        self.assertEqual(ai.ausstattung_lesen(Path("gibt/es/nicht.csv")), (None, []))

    def test_gueltig(self):
        z, f = lesen("1/1;Tischtennis;ja;vor Ort gesehen;2026-11-13\n1/1;rollstuhl;teilweise;vor Ort;2026-11-13\n")
        self.assertEqual(f, [])
        self.assertEqual([x["merkmal"] for x in z], ["tischtennis", "rollstuhl"])

    def test_ungueltig(self):
        z, f = lesen("1/1;trampolin;ja;x;2026-11-13\n"      # unbekanntes Merkmal
                     "1/1;rutsche;teilweise;x;2026-11-13\n"  # teilweise nur bei rollstuhl
                     "1/1;rutsche;ja;;2026-11-13\n"          # Beleg fehlt
                     "1/1;rutsche;ja;x;13.11.2026\n"         # Datum
                     "1/1;wc;nein;x;2026-11-13\n"
                     "1/1;wc;ja;x;2026-11-13\n")             # doppelt
        self.assertEqual([x["merkmal"] for x in z], ["wc"])
        self.assertEqual(len(f), 5)


class PlanTest(unittest.TestCase):
    def test_setzen_mit_quelle_sichtung(self):
        a, f = ai.planen([eintrag()], [zeile("z1", ["1/1", "1/2"])])
        self.assertEqual(f, [])
        self.assertEqual(a[0]["ausstattung"]["tischtennis"],
                         {"wert": "ja", "quelle": "sichtung", "beleg": "vor Ort gesehen", "stand": "2026-11-13"})

    def test_extra_landet_in_extras(self):
        a, _ = ai.planen([eintrag(merkmal="wc", wert="nein")], [zeile("z1", ["1/1"])])
        self.assertEqual(a[0]["extras"]["wc"]["wert"], "nein")
        self.assertEqual(a[0]["ausstattung"], {})

    def test_sichtung_ersetzt_osm(self):
        alt = {"tischtennis": {"wert": "nein", "quelle": "osm"}, "rutsche": {"wert": "ja", "quelle": "osm"}}
        a, _ = ai.planen([eintrag()], [zeile("z1", ["1/1"], ausstattung=alt)])
        self.assertEqual(a[0]["ausstattung"]["tischtennis"]["quelle"], "sichtung")
        self.assertEqual(a[0]["ausstattung"]["rutsche"]["quelle"], "osm")

    def test_entfernte_zeile_entfernt_nur_sichtung(self):
        alt = {"tischtennis": {"wert": "ja", "quelle": "sichtung"}, "rutsche": {"wert": "ja", "quelle": "osm"}}
        a, _ = ai.planen([], [zeile("z1", ["1/1"], ausstattung=alt)])
        self.assertEqual(a[0]["ausstattung"], {"rutsche": {"wert": "ja", "quelle": "osm"}})
        self.assertEqual(a[0]["entfernt"], ["tischtennis"])

    def test_keine_aenderung_ohne_unterschied(self):
        alt = {"tischtennis": {"wert": "ja", "quelle": "sichtung", "beleg": "vor Ort gesehen", "stand": "2026-11-13"}}
        a, _ = ai.planen([eintrag()], [zeile("z1", ["1/1"], ausstattung=alt)])
        self.assertEqual(a, [])

    def test_schluessel_fehler(self):
        a, f = ai.planen([eintrag("1/2"), eintrag("9/9")], [zeile("z1", ["1/1", "1/2"])])
        self.assertEqual(a, [])
        self.assertIn("nicht der kleinste", f[0])
        self.assertIn("gibt es nicht", f[1])

    def test_abenteuer_schluessel(self):
        a, f = ai.planen([eintrag("abenteuer:x")], [zeile("z1", ["abenteuer:x"], abenteuer=True)])
        self.assertEqual((f, a[0]["gesetzt"]), ([], ["tischtennis"]))


if __name__ == "__main__":
    unittest.main()
