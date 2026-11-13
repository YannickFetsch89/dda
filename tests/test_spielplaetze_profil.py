"""Tests für die Spielplatz-Profile (python -m unittest tests.test_spielplaetze_profil)."""
import unittest

from scraper.spielplaetze import profil as pr

QUELLEN = [("https://a.test", "Der Spielplatz im Volksgarten hat eine große Rutsche und eine Nestschaukel. "
                              "Die Wasserpumpe läuft von Mai bis September. Für Kinder von 3 bis 12 Jahren geeignet. "
                              "Eine Toilette gibt es leider nicht auf dem Gelände. Der alte Kletterturm wurde abgebaut.")]


def ki(**werte):
    basis = {"passt": True, "passt_grund": "Volksgarten", "geraete": [], "extras": [],
             "alter": {"wert": "", "zitat": "", "quelle": 1}, "saison": {"text": "", "zitat": "", "quelle": 1},
             "beschreibung": "", "highlight": "", "quellen_datum": []}
    return {**basis, **werte}


def zeile(typ, groesse=None, ausgeschlossen=None, name="X"):
    return {"name": name, "extras": {"spielplatz": {"typ": typ, "groesse_m2": groesse, "ausgeschlossen": ausgeschlossen}}}


class RundeTest(unittest.TestCase):
    def test_runde(self):
        self.assertEqual(pr.runde(zeile("wasser", 100)), 1)
        self.assertEqual(pr.runde(zeile("kinder", 3000)), 1)
        self.assertEqual(pr.runde(zeile("kinder", 1500)), 2)
        self.assertIsNone(pr.runde(zeile("kinder", 1499)))
        self.assertIsNone(pr.runde(zeile("wald", ausgeschlossen="x")))

    def test_probe(self):
        z = [zeile("wasser", name=f"W{i}") for i in range(5)] + [zeile("wald", name=f"F{i}") for i in range(5)] \
            + [zeile("abenteuer", name=f"A{i}") for i in range(4)] + [zeile("kinder", 3000 + i, name=f"K{i}") for i in range(5)]
        auswahl = pr.probe_auswahl(z)
        self.assertEqual(len(auswahl), 10)
        self.assertEqual([x["name"] for x in auswahl[-3:]], ["K4", "K3", "K2"])  # größte Kinderspielplätze


class PruefTest(unittest.TestCase):
    def test_belegte_geraete(self):
        p, verworfen = pr.pruefen(ki(geraete=[
            {"geraet": "rutsche", "wert": "ja", "zitat": "hat eine große Rutsche und eine Nestschaukel", "quelle": 1},
            {"geraet": "schaukel", "wert": "ja", "zitat": "hat eine große Rutsche und eine Nestschaukel", "quelle": 1},
            {"geraet": "klettern", "wert": "nein", "zitat": "Der alte Kletterturm wurde abgebaut", "quelle": 1},
        ]), QUELLEN)
        self.assertEqual(set(p["ausstattung"]), {"rutsche", "schaukel", "klettern"})
        self.assertEqual(p["ausstattung"]["rutsche"]["quelle"], "zitat")
        self.assertEqual(verworfen, [])

    def test_verworfen(self):
        p, verworfen = pr.pruefen(ki(geraete=[
            {"geraet": "seilbahn", "wert": "ja", "zitat": "hat eine große Rutsche und eine Nestschaukel", "quelle": 1},  # Stichwort fehlt
            {"geraet": "sandkasten", "wert": "ja", "zitat": "ein riesiger Sandkasten mit Bagger", "quelle": 1},  # nicht wörtlich
            {"geraet": "rutsche", "wert": "nein", "zitat": "hat eine große Rutsche und eine Nestschaukel", "quelle": 1},  # keine Verneinung
        ]), QUELLEN)
        self.assertEqual(p["ausstattung"], {})
        self.assertEqual(len(verworfen), 3)

    def test_skaten_nur_als_anlage(self):
        q = [("https://b.test", "Außerdem gibt's jede Menge Bälle, Skateboards oder Jongliermaterial. Neben dem Platz liegt eine Skateanlage mit Halfpipe.")]
        p, v = pr.pruefen(ki(geraete=[{"geraet": "skaten", "wert": "ja", "zitat": "jede Menge Bälle, Skateboards oder Jongliermaterial", "quelle": 1}]), q)
        self.assertEqual((p["ausstattung"], len(v)), ({}, 1))
        p, _ = pr.pruefen(ki(geraete=[{"geraet": "skaten", "wert": "ja", "zitat": "Neben dem Platz liegt eine Skateanlage mit Halfpipe", "quelle": 1}]), q)
        self.assertIn("skaten", p["ausstattung"])

    def test_alle_altersgruppen(self):
        q = [("https://c.test", "Sehr vielseitig, da für alle Altersgruppen geeignet.")]
        p, _ = pr.pruefen(ki(alter={"wert": "alle", "zitat": "da für alle Altersgruppen geeignet", "quelle": 1}), q)
        self.assertEqual(p["alter"]["wert"], "alle")

    def test_extras_alter_saison(self):
        p, _ = pr.pruefen(ki(
            extras=[{"merkmal": "wc", "wert": "nein", "notiz": "", "zitat": "Eine Toilette gibt es leider nicht", "quelle": 1}],
            alter={"wert": "alle", "zitat": "Für Kinder von 3 bis 12 Jahren geeignet", "quelle": 1},
            saison={"text": "Wasser Mai bis September", "zitat": "Die Wasserpumpe läuft von Mai bis September", "quelle": 1}),
            QUELLEN)
        self.assertEqual(p["extras"]["wc"]["wert"], "nein")
        self.assertEqual(p["alter"], {"wert": "alle", "art": "belegt", "beleg": "Für Kinder von 3 bis 12 Jahren geeignet"})
        self.assertEqual(p["saison"]["text"], "Wasser Mai bis September")

    def test_nicht_passend_und_beschreibung(self):
        p, verworfen = pr.pruefen(ki(passt=False, passt_grund="anderer Platz"), QUELLEN)
        self.assertEqual(p["ausstattung"], {})
        self.assertIn("anderer Platz", verworfen[0])
        p, verworfen = pr.pruefen(ki(beschreibung="Ein Geheimtipp mit 5 Sternen. " * 6), QUELLEN)
        self.assertIsNone(p["beschreibung"])
        p, _ = pr.pruefen(ki(beschreibung="Viel Platz zum Spielen und Toben im Park. " * 3
                             + "Ein Leser-Kommentar bemängelt allerdings Zustand und Sauberkeit."), QUELLEN)
        self.assertIsNone(p["beschreibung"])  # Kritik aus Kommentaren gehört nicht in die Beschreibung
        p, _ = pr.pruefen(ki(beschreibung="Kurz."), QUELLEN)
        self.assertIsNone(p["beschreibung"])
        text = "Im Volksgarten findet ihr eine große Rutsche und eine Nestschaukel. Im Sommer läuft die Wasserpumpe, " \
               "dann wird gematscht."
        p, _ = pr.pruefen(ki(beschreibung=text, highlight="Wasserpumpe im Sommer"), QUELLEN)
        self.assertEqual((p["beschreibung"], p["highlight"]), (text, "Wasserpumpe im Sommer"))


class ZusammenTest(unittest.TestCase):
    def test_vorrang(self):
        alt = {"rutsche": {"wert": "ja", "quelle": "osm"}, "tischtennis": {"wert": "ja", "quelle": "sichtung"},
               "schaukel": {"wert": "ja", "quelle": "zitat"}, "klettern": {"wert": "ja", "quelle": "osm"}}
        neu = {"tischtennis": {"wert": "nein", "quelle": "zitat"}, "klettern": {"wert": "nein", "quelle": "zitat"},
               "sandkasten": {"wert": "ja", "quelle": "zitat"}}
        erg, konflikte = pr.zusammenfuehren(alt, neu, "2026-05", "2025-01-01")
        self.assertEqual(erg["tischtennis"]["quelle"], "sichtung")      # Sichtung bleibt immer
        self.assertEqual(erg["klettern"]["quelle"], "zitat")            # Zitat jünger als OSM
        self.assertNotIn("schaukel", erg)                               # altes Profil-Zitat ersetzt
        self.assertEqual(erg["rutsche"]["quelle"], "osm")
        self.assertEqual(len(konflikte), 2)
        erg, _ = pr.zusammenfuehren(alt, neu, None, "2025-01-01")
        self.assertEqual(erg["klettern"]["quelle"], "osm")              # Datum unbekannt → OSM bleibt

    def test_profil_stand(self):
        self.assertEqual(pr.profil_stand({"quellen_datum": [{"quelle": 1, "datum": "2024-05"}, {"quelle": 2, "datum": "2025-03-01"},
                                                            {"quelle": 3, "datum": "letztes Jahr"}]}), "2025-03-01")
        self.assertIsNone(pr.profil_stand({"quellen_datum": []}))


if __name__ == "__main__":
    unittest.main()
