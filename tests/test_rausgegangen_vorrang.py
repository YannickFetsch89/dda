"""Tests für die Vorrang-Regel: andere Quellen vor Rausgegangen, Auffüllen in jede Richtung
(python -m unittest tests.test_rausgegangen_vorrang)."""
import unittest

from database.client import _anreicherungs_update_bauen
from pipeline.deduplication import aehnliches_event, deduplizieren, ist_rausgegangen

RG_BILD = "https://imageflow.rausgegangen.de/url/abc.jpg"


def rg(**mehr):
    """Rausgegangen-Eintrag mit Preis, langer Beschreibung und Rausgegangen-Bild."""
    return {
        "titel": "Sibel Schick im Gespräch", "ort": "zakk", "datum": "2026-11-20", "uhrzeit": "20:00",
        "quelle_name": "Rausgegangen", "quelle_url": "https://rausgegangen.de/events/sibel-schick-0/",
        "bild_url": RG_BILD, "beschreibung": "Lange Rausgegangen-Beschreibung", "preis": "12 €",
        "adresse": "Fichtenstraße 40, 40233 Düsseldorf", **mehr,
    }


def zakk(**mehr):
    """zakk-Eintrag ohne Preis und ohne Adresse."""
    return {
        "titel": "Sibel Schick im Gespräch", "ort": "zakk", "datum": "2026-11-20", "uhrzeit": "20:00",
        "quelle_name": "zakk", "quelle_url": "https://www.zakk.de/programm/sibel-schick",
        "bild_url": "https://www.zakk.de/bild.jpg", "beschreibung": "zakk-Text", "preis": None,
        "adresse": None, **mehr,
    }


class ErkennungTest(unittest.TestCase):
    def test_ist_rausgegangen(self):
        self.assertTrue(ist_rausgegangen(rg()))
        self.assertTrue(ist_rausgegangen({"quelle_name": None, "quelle_url": "https://rausgegangen.de/x"}))
        self.assertFalse(ist_rausgegangen(zakk()))
        self.assertFalse(ist_rausgegangen({}))


def film(titel, uhrzeit="20:00", ort="Black Box Kino im Filmmuseum Düsseldorf"):
    return {"titel": titel, "ort": ort, "datum": "2026-11-22", "uhrzeit": uhrzeit}


class TitelteileTest(unittest.TestCase):
    """Rausgegangen hängt Reihe und Spielort an, das Filmmuseum nennt Original- und deutschen Titel."""

    def test_gleiche_vorstellung_trotz_zusatz(self):
        rg_ort = "Filmmuseum Düsseldorf"
        paare = [
            ("S.O.S. EISBERG | Filmreihe - Hans Ertl: Virtuose an der Kamera - Black Box im Filmmuseum Düsseldorf",
             "S.O.S. EISBERG"),
            ("BACKROOMS (Extended Cut) | Filmreihe 'Liminal Spaces' - Black Box im Filmmuseum Düsseldorf", "BACKROOMS"),
            ("I WALKED WITH A ZOMBIE | Stationen der Filmgeschichte - Black Box im Filmmuseum Düsseldorf",
             "I WALKED WITH A ZOMBIE · ICH FOLGTE EINEM ZOMBIE"),
            ("RONJA RÄUBERTOCHTER | Familienkino am Sonntag - Black Box im Filmmuseum Düsseldorf",
             "RONJA RÖVARDOTTER · RONJA RÄUBERTOCHTER"),
        ]
        for rg_titel, titel in paare:
            with self.subTest(titel=titel):
                self.assertTrue(aehnliches_event(film(rg_titel, ort=rg_ort), film(titel)))

    def test_keine_falschen_treffer(self):
        # Andere Uhrzeit bleibt weitere Vorstellung
        self.assertFalse(aehnliches_event(film("BACKROOMS | Filmreihe"), film("BACKROOMS", "16:30")))
        # Gleiche Reihe, anderer Film zur selben Zeit an einem anderen Ort
        self.assertFalse(aehnliches_event(film("ALPHA | Französischer Filmclub"), film("ANORA | Französischer Filmclub",
                                                                                        ort="Metropol Kino")))
        # Kurzes Einzelwort reicht nicht
        self.assertFalse(aehnliches_event(film("Jazz | Abend im Foyer"), film("Jazz Brunch mit Trio")))


class LaufTest(unittest.TestCase):
    """In-Memory-Zusammenführung innerhalb eines Laufs."""

    def _pruefen(self, ergebnis):
        self.assertEqual(len(ergebnis), 1)
        e = ergebnis[0]
        # Andere Quelle ist Hauptquelle …
        self.assertEqual(e["quelle_name"], "zakk")
        self.assertEqual(e["quelle_url"], "https://www.zakk.de/programm/sibel-schick")
        self.assertEqual(e["bild_url"], "https://www.zakk.de/bild.jpg")
        self.assertEqual(e["beschreibung"], "zakk-Text")
        # … Rausgegangen füllt die Lücken trotzdem
        self.assertEqual(e["preis"], "12 €")
        self.assertEqual(e["adresse"], "Fichtenstraße 40, 40233 Düsseldorf")

    def test_rausgegangen_zuerst(self):
        self._pruefen(deduplizieren([rg(), zakk()]))

    def test_rausgegangen_zuletzt(self):
        self._pruefen(deduplizieren([zakk(), rg()]))

    def test_nur_rausgegangen_bleibt(self):
        ergebnis = deduplizieren([rg()])
        self.assertEqual(ergebnis[0]["quelle_name"], "Rausgegangen")

    def test_zwei_andere_quellen_nur_auffuellen(self):
        # Zwischen zwei Nicht-Rausgegangen-Quellen bleibt die erste Basis, die zweite füllt nur auf
        visit = zakk(quelle_name="VisitDüsseldorf", quelle_url="https://visit/x", preis="10 €", beschreibung="Visit")
        e = deduplizieren([zakk(), visit])[0]
        self.assertEqual(e["quelle_name"], "zakk")
        self.assertEqual(e["beschreibung"], "zakk-Text")
        self.assertEqual(e["preis"], "10 €")


class SpeichernTest(unittest.TestCase):
    """Abgleich mit bereits gespeicherten Events."""

    def test_rausgegangen_in_db_wechselt_zur_anderen_quelle(self):
        update = _anreicherungs_update_bauen(rg(), zakk())
        self.assertEqual(update["quelle_name"], "zakk")
        self.assertEqual(update["quelle_url"], "https://www.zakk.de/programm/sibel-schick")
        self.assertEqual(update["bild_url"], "https://www.zakk.de/bild.jpg")
        self.assertEqual(update["beschreibung"], "zakk-Text")
        # zakk hat keinen Preis/keine Adresse → Rausgegangen-Werte bleiben stehen
        self.assertNotIn("preis", update)
        self.assertNotIn("adresse", update)
        self.assertNotIn("slug", update)

    def test_andere_quelle_in_db_wird_von_rausgegangen_aufgefuellt(self):
        # Das Beispiel: zakk ohne Preis gespeichert, Rausgegangen kennt den Preis → Preis nachziehen, Quelle bleibt zakk
        update = _anreicherungs_update_bauen(zakk(), rg())
        self.assertEqual(update.get("preis"), "12 €")
        self.assertEqual(update.get("adresse"), "Fichtenstraße 40, 40233 Düsseldorf")
        self.assertNotIn("quelle_name", update)
        self.assertNotIn("quelle_url", update)
        self.assertNotIn("bild_url", update)
        self.assertNotIn("beschreibung", update)

    def test_ohne_link_kein_quellwechsel(self):
        update = _anreicherungs_update_bauen(rg(preis=None), zakk(quelle_url=None, preis="8 €"))
        self.assertNotIn("quelle_name", update)
        self.assertEqual(update.get("preis"), "8 €")  # Auffüllen gilt trotzdem

    def test_rausgegangen_auf_rausgegangen_nur_auffuellen(self):
        update = _anreicherungs_update_bauen(rg(preis=None), rg(beschreibung="Anders", preis="5 €"))
        self.assertEqual(update, {"preis": "5 €"})


if __name__ == "__main__":
    unittest.main()
