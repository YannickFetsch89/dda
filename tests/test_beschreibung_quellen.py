"""Tests für die Prüfungen der umgeschriebenen Event-Beschreibungen (python -m unittest tests.test_beschreibung_quellen)."""
import unittest

from pipeline.beschreibung_quellen import (
    MAX_UEBERNAHME,
    _gesperrt,
    laengste_uebernahme,
    titel_treffer,
    titel_woerter,
    zu_lange_uebernahmen,
)

QUELLE = "Erlebe einen Abend mit Jazz und Wein im Hof der alten Villa am Rhein. Einlass ab 18 Uhr."


class UebernahmeTest(unittest.TestCase):
    def test_lange_wortfolge_wird_erkannt(self):
        text = "Hallo. Ein toller Abend mit Jazz und Wein im Hof der alten Villa am Rhein heute."
        self.assertGreater(laengste_uebernahme(text, QUELLE), MAX_UEBERNAHME)
        self.assertEqual(zu_lange_uebernahmen(text, QUELLE), ["abend mit jazz und wein im hof der alten villa am rhein"])

    def test_eigener_wortlaut_ist_ok(self):
        text = "Jazz, Wein und ein schöner Innenhof an einer Villa direkt am Rhein – los geht's um 18 Uhr."
        self.assertLessEqual(laengste_uebernahme(text, QUELLE), MAX_UEBERNAHME)
        self.assertEqual(zu_lange_uebernahmen(text, QUELLE), [])


class TitelTest(unittest.TestCase):
    def test_rausgegangen_zusatz_wird_ignoriert(self):
        self.assertEqual(titel_woerter("S.O.S. EISBERG | Filmreihe - Black Box im Filmmuseum"), {"eisberg"})

    def test_treffer(self):
        self.assertEqual(titel_treffer("Heute im Kino: SOS Eisberg", {"eisberg"}), 1.0)
        self.assertEqual(titel_treffer("Nichts davon", {"eisberg", "hans"}), 0.0)


class GesperrtTest(unittest.TestCase):
    def test_gesperrte_seiten(self):
        self.assertTrue(_gesperrt("https://rausgegangen.de/events/x"))
        self.assertTrue(_gesperrt("https://www.duesseldorf.de/stadtbuechereien"))
        self.assertTrue(_gesperrt("https://m.facebook.com/events/1"))
        self.assertFalse(_gesperrt("https://www.zakk.de/programm"))


if __name__ == "__main__":
    unittest.main()
