"""Tests für die Reihen-Erkennung (python -m unittest tests.test_reihen)."""
import unittest

from pipeline.reihen_zuordnen import basis_titel, reihe_slug, reihen_bilden, reihen_schluessel


def ev(id_, titel, ort, datum):
    return {"id": id_, "titel": titel, "ort": ort, "datum": datum, "kategorie": "kultur", "reihe_id": None}


class ReihenTest(unittest.TestCase):
    def test_basis_titel_entfernt_uhrzeit(self):
        self.assertEqual(basis_titel("Japanviertel (14:00 Uhr)"), "Japanviertel")
        self.assertEqual(basis_titel("Konzert"), "Konzert")

    def test_schluessel_vereinheitlicht(self):
        self.assertEqual(reihen_schluessel("Öffentliche Führung!", "Kunstpalast"),
                         reihen_schluessel("öffentliche führung", "KUNSTPALAST"))

    def test_schluessel_ohne_allgemeinen_ort(self):
        self.assertIsNone(reihen_schluessel("Stadtführung", "Düsseldorf"))
        self.assertIsNone(reihen_schluessel("Webinar", "Online"))

    def test_reihe_braucht_zwei_verschiedene_tage(self):
        events = [
            ev("1", "Führung", "Kunstpalast", "2026-11-01"),
            ev("2", "Führung (14:00 Uhr)", "Kunstpalast", "2026-11-01"),  # gleicher Tag, andere Uhrzeit
            ev("3", "Comedy", "zakk", "2026-11-01"),
            ev("4", "Comedy", "zakk", "2026-12-01"),
        ]
        gruppen = reihen_bilden(events)
        self.assertEqual(list(gruppen), [reihen_schluessel("Comedy", "zakk")])
        self.assertEqual({e["id"] for e in gruppen[reihen_schluessel("Comedy", "zakk")]}, {"3", "4"})

    def test_slug_lesbar_und_eindeutig(self):
        slug = reihe_slug("Öffentliche Führung (11:00 Uhr)", "Kunstpalast", set())
        self.assertEqual(slug, "oeffentliche-fuehrung-kunstpalast")
        self.assertEqual(reihe_slug("Öffentliche Führung", "Kunstpalast", {slug}), f"{slug}-b")


if __name__ == "__main__":
    unittest.main()
