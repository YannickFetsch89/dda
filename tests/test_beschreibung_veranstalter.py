"""Tests: Beschreibungen aus der Veranstalter-Seite (python -m unittest tests.test_beschreibung_veranstalter)."""
import unittest

from pipeline.beschreibung_quellen import _seiten_pfad, ersetzen_erlaubt, sammel_pfade, stuecke_bilden


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

    def test_sammelseiten(self):
        kalender = "https://www.d-live.de/events/eventkalender"
        events = [ev(1, "Shinedown", "Halle", kalender), ev(2, "Good Charlotte", "Halle", kalender),
                  ev(3, "BLUTBUCH", "Kleines Haus", "https://www.dhaus.de/programm/spielplan/2026-11/blutbuch/3072/"),
                  ev(4, "Blutbuch", "Kleines Haus", "https://www.dhaus.de/programm/spielplan/2026-12/blutbuch/3072/"),
                  ev(5, "Startseite", "Ort", "https://example.org/")]
        sammel = sammel_pfade(events)
        self.assertIn(_seiten_pfad(kalender), sammel)  # verschiedene Titel → Sammel-Seite
        self.assertNotIn(_seiten_pfad(events[2]["quelle_url"]), sammel)  # ein Stück, zwei Monate → Event-Seite
        self.assertIn(_seiten_pfad("https://example.org/"), sammel)  # Startseite einer Domain ist nie eine Event-Seite

    def test_kennung_in_der_abfrage(self):
        # zakk/Tonhalle: Event-Kennung in der Abfrage → verschiedene Seiten, keine Sammel-Seite
        a = ev(1, "Tango im zakk", "zakk", "https://zakk.de/event-detail?event=16368")
        b = ev(2, "Poesieschlacht", "zakk", "https://zakk.de/event-detail?event=15566")
        self.assertNotEqual(_seiten_pfad(a["quelle_url"]), _seiten_pfad(b["quelle_url"]))
        self.assertEqual(sammel_pfade([a, b]), set())
        # Kunstpalast/Kunsthalle: nur Datum/Zeitstempel in der Abfrage → dieselbe Seite
        self.assertEqual(_seiten_pfad("https://www.kunstpalast.de/de/event/open-studio/?date=20.12.2026&time=12:00"),
                         _seiten_pfad("https://www.kunstpalast.de/de/event/open-studio/?date=12.12.2026&time=12:00"))
        self.assertEqual(_seiten_pfad("https://www.kunsthalle-duesseldorf.de/kalender/x/?stamp=1"),
                         _seiten_pfad("https://www.kunsthalle-duesseldorf.de/kalender/x/?stamp=2"))


class StueckBearbeitenTest(unittest.TestCase):
    def test_fehlgeschlagene_umschrift_bleibt_offen(self):
        from unittest import mock
        import pipeline.beschreibung_quellen as bq
        stueck = [ev(1, "BLUTBUCH", "Kleines Haus", "https://www.dhaus.de/programm/spielplan/2026-11/blutbuch/3072/")]
        seite = "<main>" + "BLUTBUCH von Kim de l'Horizon. " * 20 + "</main>"
        with mock.patch.object(bq, "_gesperrt", return_value=False), mock.patch.object(bq, "robots_erlaubt", return_value=True),                 mock.patch.object(bq, "seite_laden", return_value=seite),                 mock.patch.object(bq, "umschreiben", side_effect=RuntimeError("API nicht erreichbar")):
            eintrag = bq.stueck_bearbeiten(None, stueck)
        self.assertEqual(eintrag["abruf"], "fehler")  # nicht als gesucht markieren
        self.assertIn("API", eintrag["fehler"])


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
