"""Tests für den Google-Abgleich der Spielplätze (python -m unittest tests.test_spielplaetze_google)."""
import unittest

from scraper.spielplaetze import google_abgleich as ga


def zeile(typ="kinder", groesse=None, ausgeschlossen=None, quelle="stadt-duesseldorf"):
    return {"extras": {"spielplatz": {"typ": typ, "groesse_m2": groesse, "ausgeschlossen": ausgeschlossen, "quelle": quelle}}}


def ort(name, **extra):
    return {"id": name, "displayName": {"text": name}, **extra}


class RundeTest(unittest.TestCase):
    def test_runde_1(self):
        self.assertTrue(ga.ist_runde_1(zeile("wasser", 100)))
        self.assertTrue(ga.ist_runde_1(zeile("wald")))
        self.assertTrue(ga.ist_runde_1(zeile("abenteuer", quelle="abenteuer")))
        self.assertTrue(ga.ist_runde_1(zeile("kinder", 3000)))
        self.assertFalse(ga.ist_runde_1(zeile("kinder", 2999.9)))
        self.assertFalse(ga.ist_runde_1(zeile("wasser", ausgeschlossen="Dublette")))


class TrefferTest(unittest.TestCase):
    def test_woerter(self):
        self.assertEqual(ga.woerter("Spielplatz Hofgartenstraße (Oederallee)"), {"hofgarten", "oederallee"})

    def test_name_aehnlich(self):
        t, art = ga.treffer_waehlen("Spielplatz Hofgarten (Oederallee)", [ort("Kita Sonnenschein"), ort("Spielplatz Hofgarten")])
        self.assertEqual((t["id"], art), ("Spielplatz Hofgarten", "name"))

    def test_einziger_treffer(self):
        t, art = ga.treffer_waehlen("Spielplatz Am Klosterhof", [ort("Spielplatz")])
        self.assertEqual(art, "einziger")

    def test_gleichstand_typwort_und_doppelt(self):
        orte = [ort("Wasserspielplatz Frankenplatz"), ort("Spielplatz Frankenplatz II")]
        self.assertEqual(ga.treffer_waehlen("Spielplatz Frankenplatz", orte)[0]["id"], "Spielplatz Frankenplatz II")
        self.assertEqual(ga.treffer_waehlen("Wasserspielplatz Frankenplatz", orte)[0]["id"], "Wasserspielplatz Frankenplatz")
        doppelt = [{"id": "a", "displayName": {"text": "Waldspielplatz Plagbergwiese"}, "userRatingCount": 3},
                   {"id": "b", "displayName": {"text": "Waldspielplatz Plagbergwiese"}, "userRatingCount": 40}]
        self.assertEqual(ga.treffer_waehlen("Waldspielplatz Plagbergwiese", doppelt), (doppelt[1], "name_doppelt"))

    def test_mehrdeutig_und_leer(self):
        self.assertEqual(ga.treffer_waehlen("Spielplatz X", [ort("Spielplatz"), ort("Kinderspielplatz")])[1], "mehrdeutig")
        self.assertEqual(ga.treffer_waehlen("Spielplatz Volksgarten", [ort("Volksgarten Nord"), ort("Volksgarten Süd")])[1],
                         "mehrdeutig")  # gleich ähnlich → nicht raten
        self.assertEqual(ga.treffer_waehlen("Spielplatz X", []), (None, "kein_treffer"))


class FotoTest(unittest.TestCase):
    def test_kandidaten(self):
        o = ort("A", photos=[{"name": f"places/a/photos/{i}", "widthPx": 800, "heightPx": 600,
                              "authorAttributions": [{"displayName": "Anna", "uri": "https://x"}]} for i in range(12)])
        k = ga.foto_kandidaten(o)
        self.assertEqual(len(k), 10)
        self.assertEqual(k[0], {"name": "places/a/photos/0", "breite": 800, "hoehe": 600, "autor": "Anna", "autor_url": "https://x"})

    def test_sql(self):
        kand = {"z1": [{"name": "places/a/photos/0", "breite": 800, "hoehe": 600, "autor": "Anna O'Neil", "autor_url": "https://x"}]}
        sql = ga.sql_aus_sichtung({"z1": {"foto": 0, "grund": "Klettergerüst"}, "z2": {"foto": None, "grund": "nur Personen"}},
                                  kand, {"z1": "Spielplatz A", "z2": "Spielplatz B"}, "2026-11-13")
        self.assertIn("bild_attribution = 'Anna O''Neil'", sql)
        self.assertIn("'foto_manuell', '2026-11-13'", sql)
        self.assertIn("COALESCE((extras->>'foto_version')::int + 1, 1)", sql)
        self.assertIn("bild_url = NULL", sql)
        self.assertIn("WHERE id = 'z1' AND typ = 'spielplatz'", sql)
        self.assertIn("-- Spielplatz B: kein Foto – nur Personen", sql)
        self.assertNotIn("'z2'", sql)


if __name__ == "__main__":
    unittest.main()
