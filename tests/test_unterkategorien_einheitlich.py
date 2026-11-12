"""Tests: Unterkategorien gleicher Titel angleichen (python -m unittest tests.test_unterkategorien_einheitlich)."""
import unittest

from pipeline.unterkategorien import angleichungen


def z(i, titel, ort, unter, kategorie="kultur"):
    return {"id": f"e{i}", "titel": titel, "ort": ort, "kategorie": kategorie, "unterkategorie": unter}


class AngleichenTest(unittest.TestCase):
    def test_gleicher_titel_gleicher_ort_wird_angeglichen(self):
        zeilen = [z(1, "Der Hobbit", "Düsseldorfer Schauspielhaus", "theater"),
                  z(2, "Der Hobbit", "Düsseldorfer Schauspielhaus", "theater"),
                  z(3, "DER HOBBIT", "Düsseldorfer  Schauspielhaus", "comedy")]
        self.assertEqual(angleichungen(zeilen), [("e3", "theater")])

    def test_gleicher_titel_verschiedene_orte_bleibt_getrennt(self):
        zeilen = [z(1, "Öffentliche Führung", "Kunstpalast", "ausstellungen"),
                  z(2, "Öffentliche Führung", "Kunstpalast", "ausstellungen"),
                  z(3, "Öffentliche Führung", "Schauspielhaus", "theater")]
        self.assertEqual(angleichungen(zeilen), [])

    def test_gleichstand_und_andere_kategorie(self):
        self.assertEqual(angleichungen([z(1, "X", "Ort", "theater"), z(2, "X", "Ort", "comedy")]), [])
        # Gleicher Titel und Ort, aber andere Kategorie: eigene Gruppe
        self.assertEqual(angleichungen([z(1, "X", "Ort", "theater"), z(2, "X", "Ort", "klassik", kategorie="musik")]), [])

    def test_ohne_ort_keine_angleichung(self):
        self.assertEqual(angleichungen([z(1, "X", "", "theater"), z(2, "X", "", "theater"), z(3, "X", "", "comedy")]), [])


if __name__ == "__main__":
    unittest.main()
