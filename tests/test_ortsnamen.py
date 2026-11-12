"""Tests: eine Schreibweise pro Spielstätte (python -m unittest tests.test_ortsnamen)."""
import unittest

from pipeline.deduplication import deduplizieren
from pipeline.ortsnamen import SPIELSTAETTEN, einheitlicher_name, schluessel


class OrtsnamenTest(unittest.TestCase):
    def test_varianten(self):
        for alt, neu in [
            ("Mitsubishi Electric HALLE", "Mitsubishi Electric Halle"),
            ("Mitsubishi Electric  Halle Düsseldorf", "Mitsubishi Electric Halle"),
            ("Mitsubishi Electric HALLE, Dusseldorf, North Rhine-Westphalia, Germany", "Mitsubishi Electric Halle"),
            ("PSD BANK DOME Düsseldorf", "PSD Bank Dome"),
            ("Pitcher", "Pitcher Rock HQ"),
            ("Pitcher - Rock'n'Roll Headquarter Düsseldorf", "Pitcher Rock HQ"),
            ("tanzhaus nrw", "Tanzhaus NRW"),
            ("zakk - Zentrum für Aktion, Kultur und Kommunikation", "zakk"),
            ("Dusseldorf, Germany", "Düsseldorf"),
        ]:
            self.assertEqual(einheitlicher_name(alt), neu, alt)

    def test_raeume_und_allgemeines_bleiben(self):
        for ort in ["zakk – Studio", "zakk – Halle", "Düsseldorfer Schauspielhaus – Großes Haus", "Düsseldorfer Schauspielhaus – Kleines Haus",
                    "Tonhalle Mendelssohn-Saal", "Capitol Theater - Club Saal", "Stone im Ratinger Hof", "Altstadt Düsseldorf",
                    "Bunker", "Kunstsammlung NRW", "Tiefgarage PSD BANK DOME"]:
            self.assertEqual(einheitlicher_name(ort), ort, ort)

    def test_allgemeine_bereinigung(self):
        self.assertEqual(einheitlicher_name("Fichtenstr. 40, 40233 Düsseldorf, Germany"), "Fichtenstr. 40, 40233 Düsseldorf")
        self.assertEqual(einheitlicher_name("Irgendwo  mit   Leerzeichen"), "Irgendwo mit Leerzeichen")
        self.assertIsNone(einheitlicher_name(None))

    def test_liste_eindeutig(self):
        # Kein Schlüssel zeigt auf zwei Namen (sonst wirft schon der Import), jeder Name ist stabil
        for name in SPIELSTAETTEN:
            self.assertEqual(einheitlicher_name(name), name)
        self.assertEqual(schluessel("Merkur Spiel-Arena Düsseldorf"), schluessel("merkur spiel arena"))

    def test_pipeline_fuehrt_zusammen(self):
        # Zwei Quellen, zwei Schreibweisen, gleicher Termin → ein Event mit dem einheitlichen Namen
        e1 = {"titel": "Shinedown", "ort": "Mitsubishi Electric HALLE", "datum": "2026-11-12", "uhrzeit": "19:30", "quelle_name": "d-live"}
        e2 = {"titel": "SHINEDOWN", "ort": "Mitsubishi Electric Halle", "datum": "2026-11-12", "uhrzeit": "19:30", "quelle_name": "Rausgegangen"}
        ergebnis = deduplizieren([e1, e2])
        self.assertEqual(len(ergebnis), 1)
        self.assertEqual(ergebnis[0]["ort"], "Mitsubishi Electric Halle")


if __name__ == "__main__":
    unittest.main()
