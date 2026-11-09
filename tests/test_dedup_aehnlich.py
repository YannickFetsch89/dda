"""Tests für die strengere Duplikat-Erkennung und die Preis-Schreibweise (python -m unittest tests.test_dedup_aehnlich)."""
import unittest

from pipeline.deduplication import aehnliches_event, deduplizieren, preis_normalisieren


def ev(titel, ort, uhrzeit="20:00", datum="2026-11-09", **mehr):
    return {"titel": titel, "ort": ort, "datum": datum, "uhrzeit": uhrzeit, **mehr}


class AehnlichTest(unittest.TestCase):
    def test_beispiele_aus_der_praxis(self):
        # Gleicher Titel, Ortsname einmal lang, einmal mit Raum
        self.assertTrue(aehnliches_event(ev("Sibel Schick im Gespräch", "zakk - Zentrum für Aktion, Kultur und Kommunikation"),
                                         ev("Sibel Schick im Gespräch", "zakk – Studio")))
        # Gleicher Ort, Titel mit anderer Jahresangabe
        self.assertTrue(aehnliches_event(ev("European Outdoor Film Tour 2026 - EOFT", "Savoy Theater", "19:30"),
                                         ev("European Outdoor Film Tour 26/27 – EOFT", "Savoy Theater", "19:30")))
        # Ein Titel enthält den anderen
        self.assertTrue(aehnliches_event(ev("Sibel Schick", "zakk Halle"), ev("Sibel Schick im Gespräch", "zakk – Studio")))

    def test_keine_falschen_treffer(self):
        # Andere Uhrzeit = weitere Vorstellung
        self.assertFalse(aehnliches_event(ev("Sibel Schick im Gespräch", "zakk"), ev("Sibel Schick im Gespräch", "zakk", "17:00")))
        # Fehlende Uhrzeit reicht nicht für den Ähnlichkeitsabgleich
        self.assertFalse(aehnliches_event(ev("Sibel Schick im Gespräch", "zakk", None), ev("Sibel Schick im Gespräch", "zakk Studio", None)))
        # Anderer Ort
        self.assertFalse(aehnliches_event(ev("Tatort Live", "Savoy Theater"), ev("Tatort Live", "Capitol Theater")))
        # Anderer Tag
        self.assertFalse(aehnliches_event(ev("Tatort Live", "Savoy"), ev("Tatort Live", "Savoy", datum="2026-11-10")))
        # Zwei Filme im selben Kino zur selben Zeit
        self.assertFalse(aehnliches_event(ev("Barrio Triste", "Black Box Kino"), ev("I Walked with a Zombie", "Black Box Kino")))
        # Nur ein gemeinsames Wort reicht nicht
        self.assertFalse(aehnliches_event(ev("Jazz am Montag", "Jazz-Schmiede"), ev("Jazz Session", "Jazz-Schmiede")))

    def test_deduplizieren_fasst_zusammen(self):
        ergebnis = deduplizieren([
            ev("Sibel Schick im Gespräch", "zakk - Zentrum für Aktion, Kultur und Kommunikation", quelle_name="Rausgegangen"),
            ev("Sibel Schick im Gespräch", "zakk – Studio", quelle_name="zakk", preis="kostenlos"),
            ev("Sibel Schick im Gespräch", "zakk – Studio", "17:00", quelle_name="zakk"),
        ])
        self.assertEqual(len(ergebnis), 2)


class PreisTest(unittest.TestCase):
    def test_kostenlos_einheitlich(self):
        for wert in ("Eintritt frei", "eintritt: frei", "Freier Eintritt", "kostenfrei", "gratis", "frei", "0,00 €", "0 €", "Kostenlos"):
            self.assertEqual(preis_normalisieren(wert), "kostenlos", wert)

    def test_andere_preise_bleiben(self):
        for wert in ("kostenlos oder auf Anfrage", "Auf Spendenbasis", "10,00 €", "0,00 bis 4,00 €", "VVK 12,50 € / AK 13,00 €"):
            self.assertEqual(preis_normalisieren(wert), wert)
        self.assertIsNone(preis_normalisieren(None))


if __name__ == "__main__":
    unittest.main()
