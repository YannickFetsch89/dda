"""Tests: Lauf-Report speichert Status und Ergebnisse auch, wenn eine Kennzahl keine Spalte hat (20.11.2026)."""
import unittest
from unittest import mock

from pipeline.lauf_report import LaufReport


class _Tabelle:
    def __init__(self, db, name):
        self.db, self.name, self.daten = db, name, None

    def update(self, daten):
        self.daten = ("update", daten)
        return self

    def insert(self, daten):
        self.daten = ("insert", daten)
        return self

    def eq(self, *_):
        return self

    def execute(self):
        art, daten = self.daten
        if art == "update" and "ort_id_mehrdeutig" in daten:
            raise RuntimeError("PGRST204 Could not find the 'ort_id_mehrdeutig' column")
        self.db.geschrieben.append((self.name, art, daten))
        return mock.Mock()


class _Db:
    def __init__(self):
        self.geschrieben = []

    def table(self, name):
        return _Tabelle(self, name)


class KennzahlOhneSpalteTest(unittest.TestCase):
    def test_status_und_ergebnisse_trotzdem(self):
        r = LaufReport()
        r.lauf_id, r._db = "lauf-1", _Db()
        r.ergebnisse = [{"quelle": "x", "status": "ok"}]
        r.kennzahl(neu_gespeichert=5, ort_id_mehrdeutig=0)
        r.abschliessen()
        laeufe = [d for t, a, d in r._db.geschrieben if t == "scraper_laeufe"]
        self.assertEqual(len(laeufe), 1)
        self.assertEqual(laeufe[0]["status"], "erfolgreich")
        self.assertNotIn("ort_id_mehrdeutig", laeufe[0])
        self.assertTrue(any(t == "scraper_ergebnisse" for t, a, d in r._db.geschrieben))


if __name__ == "__main__":
    unittest.main()
