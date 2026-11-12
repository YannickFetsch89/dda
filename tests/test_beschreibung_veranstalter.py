"""Tests: Beschreibungen aus der Veranstalter-Seite (python -m unittest tests.test_beschreibung_veranstalter)."""
import unittest

from pipeline.beschreibung_quellen import _seiten_pfad, ersetzen_erlaubt, stuecke_bilden


def ev(i, titel, ort, url, datum="2026-11-20"):
    return {"id": f"e{i}", "titel": titel, "ort": ort, "quelle_url": url, "datum": datum}


class StueckeTest(unittest.TestCase):
    def test_gleiches_stueck_ueber_monate(self):
        a = ev(1, "BLUTBUCH", "Kleines Haus", "https://www.dhaus.de/programm/spielplan/2026-11/blutbuch/3072/", "2026-11-12")
        b = ev(2, "Blutbuch", "Kleines Haus", "https://www.dhaus.de/programm/spielplan/2026-12/blutbuch/3072/", "2026-12-05")
        self.assertEqual(_seiten_pfad(a["quelle_url"]), _seiten_pfad(b["quelle_url"]))
        self.assertEqual([[e["id"] for e in g] for g in stuecke_bilden([b, a])], [["e1", "e2"]])

    def test_allgemeiner_titel_verschiedene_seiten_getrennt(self):
        a = ev(1, "Öffentliche Führung", "Kunstpalast", "https://www.kunstpalast.de/de/event/oeffentliche-fuehrung-niki/?date=12.11.2026")
        b = ev(2, "Öffentliche Führung", "Kunstpalast", "https://www.kunstpalast.de/de/event/oeffentliche-fuehrung-niki/?date=19.11.2026")
        c = ev(3, "Öffentliche Führung", "Kunstpalast", "https://www.kunstpalast.de/de/event/oeffentliche-fuehrung-sammlung/?date=13.11.2026")
        gruppen = sorted(sorted(e["id"] for e in g) for g in stuecke_bilden([a, b, c]))
        self.assertEqual(gruppen, [["e1", "e2"], ["e3"]])

    def test_ohne_url_kein_stueck(self):
        self.assertEqual(stuecke_bilden([ev(1, "X", "Ort", None)]), [])


class ErsetzenTest(unittest.TestCase):
    def test_regeln(self):
        lang = "Neuer Text aus der Quelle. " * 20
        self.assertTrue(ersetzen_erlaubt(None, lang))
        self.assertTrue(ersetzen_erlaubt("", lang))
        self.assertTrue(ersetzen_erlaubt("Ein intensives Theatererlebnis.", "Kurzer echter Text."))  # alter Text kurz
        self.assertFalse(ersetzen_erlaubt("A" * 400, "B" * 300))  # langer Originaltext bleibt, wenn der neue kürzer ist
        self.assertTrue(ersetzen_erlaubt("A" * 400, "B" * 600))
        self.assertFalse(ersetzen_erlaubt(None, "   "))


if __name__ == "__main__":
    unittest.main()
