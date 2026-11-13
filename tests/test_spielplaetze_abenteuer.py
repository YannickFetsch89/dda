"""Tests für den Import der Abenteuer-/Bauspielplätze (python -m unittest tests.test_spielplaetze_abenteuer)."""
import tempfile
import unittest
from pathlib import Path

from scraper.spielplaetze import abenteuer_import as ai

KOPF = "schluessel;name;traeger;adresse;latitude;longitude;stadtteil;oeffnungszeiten;eintritt;quelle_url;ausschliessen;grund;bestaetigt\n"
GUT = "abenteuer:eller;Abenteuerspielplatz Eller;Verein X;Weg 1, 40229 Düsseldorf;51.19631;6.84946;Eller;Mo–Fr 14–18 Uhr;nein;https://beispiel.test/asp;;;\n"


def lesen(zeilen):
    with tempfile.TemporaryDirectory() as d:
        pfad = Path(d) / "abenteuer.csv"
        pfad.write_text(KOPF + zeilen, encoding="utf-8")
        return ai.abenteuer_lesen(pfad)


def bestand(d, zid="z1", freigeschaltet_am=None, **sp):
    """Macht aus einem geplanten neuen Datensatz eine bestehende Datenbankzeile."""
    return {"id": zid, "name": d["spalten"]["name"], "slug": d["spalten"]["slug"], "stadtteil": d["spalten"]["stadtteil"],
            "extras": {"spielplatz": {**d["felder"], "freigeschaltet_am": freigeschaltet_am, **sp}}}


class LesenTest(unittest.TestCase):
    def test_fehlende_datei(self):
        self.assertEqual(ai.abenteuer_lesen(Path("gibt/es/nicht.csv")), (None, []))

    def test_gueltige_zeile(self):
        daten, meldungen = lesen(GUT)
        self.assertEqual(meldungen, [])
        z = daten["abenteuer:eller"]
        self.assertEqual((z["eintritt"], z["stadtteil"], z["ausgeschlossen"]), ("nein", "Eller", None))

    def test_pflichtfelder(self):
        faelle = [
            GUT.replace("abenteuer:eller", "Eller"),             # Schlüsselmuster
            GUT.replace(";nein;", ";vielleicht;"),               # Eintritt
            GUT.replace("51.19631", "50.0"),                     # Koordinate außerhalb
            GUT.replace("https://beispiel.test/asp", ""),        # Quelle
            GUT.replace(";;;\n", ";ja;;\n"),                     # ausschliessen ohne Grund
        ]
        for f in faelle:
            daten, meldungen = lesen(f)
            self.assertTrue(next(iter(daten.values())).get("ungueltig"), f)
            self.assertTrue(meldungen)

    def test_stadtteil_und_bestaetigt(self):
        daten, meldungen = lesen(GUT.replace(";Eller;", ";Medienhafen;").replace(";;;\n", ";;;access_private, name_unklar\n"))
        z = daten["abenteuer:eller"]
        self.assertIsNone(z["stadtteil"])
        self.assertTrue(z["stadtteil_ungueltig"])
        self.assertEqual(z["bestaetigt"], ["access_private"])
        self.assertEqual(len(meldungen), 2)


class PlanTest(unittest.TestCase):
    def plan(self, zeilen, bestehend=(), andere=()):
        daten, _ = lesen(zeilen)
        return ai.planen(daten, list(bestehend), set(andere))

    def test_neu_inaktiv_mit_feldern(self):
        d = self.plan(GUT)["neu"][0]
        self.assertEqual(d["spalten"]["slug"], "abenteuerspielplatz-eller")
        self.assertEqual(d["spalten"]["oeffnungszeiten"], "Mo–Fr 14–18 Uhr")
        self.assertEqual((d["felder"]["typ"], d["felder"]["quelle"], d["felder"]["traeger"]), ("abenteuer", "abenteuer", "Verein X"))
        self.assertEqual((d["felder"]["pruefung"], d["felder"]["bestaetigt"]), ([], []))

    def test_ungueltig_neu_nicht_angelegt_bestehend_unveraendert(self):
        alt = bestand(self.plan(GUT)["neu"][0])
        p = self.plan(GUT.replace(";nein;", ";;"), [alt])
        self.assertEqual((p["neu"], p["aenderungen"]), ([], []))
        self.assertTrue(any("unverändert" in m for m in p["log"]))

    def test_nicht_katalog_stadtteil(self):
        p = self.plan(GUT.replace(";Eller;", ";Medienhafen;"))
        self.assertIsNone(p["neu"][0]["spalten"]["stadtteil"])
        self.assertIn("kein_stadtteil", p["neu"][0]["felder"]["pruefung"])
        alt = bestand(self.plan(GUT)["neu"][0])
        a = self.plan(GUT.replace(";Eller;", ";Medienhafen;"), [alt])["aenderungen"][0]
        self.assertEqual(a["spalten"]["stadtteil"], "Eller")  # bestehende Zeile behält den alten Wert
        a = self.plan(GUT, [bestand(self.plan(GUT)["neu"][0], pruefung=["kein_stadtteil", "access_private"])])["aenderungen"][0]
        self.assertEqual(a["felder"]["pruefung"], ["access_private"])  # Katalogwert entfernt den Code, OSM-Code bleibt

    def test_slug_nie_freigeschaltet_neu_freigeschaltet_fest(self):
        alt = bestand(self.plan(GUT)["neu"][0])
        umbenannt = GUT.replace("Abenteuerspielplatz Eller;", "Bauspielplatz Eller;")
        self.assertEqual(self.plan(umbenannt, [alt])["aenderungen"][0]["spalten"]["slug"], "bauspielplatz-eller")
        alt = bestand(self.plan(GUT)["neu"][0], freigeschaltet_am="2026-12-01")
        a = self.plan(umbenannt, [alt])["aenderungen"][0]
        self.assertEqual((a["spalten"]["name"], a["spalten"]["slug"]), ("Bauspielplatz Eller", "abenteuerspielplatz-eller"))

    def test_ausschluss_gesetzt_und_aufgehoben(self):
        alt = bestand(self.plan(GUT)["neu"][0])
        a = self.plan(GUT.replace(";;;\n", ";ja;geschlossen;\n"), [alt])["aenderungen"][0]
        self.assertEqual(a["felder"]["ausgeschlossen"], "geschlossen")
        a = self.plan(GUT, [bestand(self.plan(GUT)["neu"][0], ausgeschlossen="geschlossen")])["aenderungen"][0]
        self.assertIsNone(a["felder"]["ausgeschlossen"])

    def test_geloeschter_schluessel_aendert_nichts(self):
        alt = bestand(self.plan(GUT)["neu"][0])
        p = self.plan("", [alt])
        self.assertEqual((p["neu"], p["aenderungen"]), ([], []))
        self.assertTrue(p["log"])

    def test_nie_aktiv_oder_freigeschaltet_am_im_plan(self):
        alt = bestand(self.plan(GUT)["neu"][0])
        a = self.plan(GUT, [alt])["aenderungen"][0]
        self.assertNotIn("aktiv", a["spalten"])
        self.assertNotIn("freigeschaltet_am", a["felder"])

    def test_slug_kollision(self):
        p = self.plan(GUT, andere={"abenteuerspielplatz-eller"})
        self.assertEqual(p["neu"][0]["spalten"]["slug"], "abenteuerspielplatz-eller-b")


if __name__ == "__main__":
    unittest.main()
