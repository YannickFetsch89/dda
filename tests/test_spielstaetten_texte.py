"""Tests: Texte der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.14, Schritt 4)."""
import unittest

from scraper.orte.spielstaetten_texte import pruefen, saetze, sql_bauen

TEXT = ("Die **Tonhalle** liegt am **Ehrenhof**. Sie wurde 1926 z. B. als Planetarium gebaut.\n\n"
        "Heute spielen hier u. a. die Symphoniker. Eröffnet wurde sie am 3. Oktober 1926.")
BELEGE = " | ".join(f"https://quelle.test/{i}" for i in range(4))


class SaetzeTest(unittest.TestCase):
    def test_abkuerzungen_und_datum_trennen_nicht(self):
        self.assertEqual(len(saetze(TEXT)), 4)
        self.assertEqual(saetze("Der Saal hat ca. 1.900 Plätze. St. Lambertus liegt nah.")[1], "St. Lambertus liegt nah.")
        # Zahl am Satzende ist kein Datum: „Kleine Saal 89. Als …“ sind zwei Sätze
        self.assertEqual(len(saetze("Der Große Saal hat 318 Plätze, der Kleine Saal 89. Als Produktionshaus arbeitet es.")), 2)
        self.assertEqual(len(saetze("Gebaut im 19. Jahrhundert. Eröffnet am 3. Oktober 1926.")), 2)
        self.assertEqual(len(saetze("Sie zeigt Kunst des 20. und 21. Jahrhunderts an zwei Standorten. Gegründet 1961.")), 2)
        self.assertEqual(len(saetze("Am Schaft hängt der Lichtzeitpegel von Horst H. Baumann. Er zeigt die Uhrzeit.")), 2)


class PruefenTest(unittest.TestCase):
    def test_gueltig(self):
        self.assertEqual(pruefen({"text": TEXT, "belege": BELEGE})[0], [])

    def test_beleg_je_satz_pflicht(self):
        self.assertIn("3 Belege für 4 Sätze", pruefen({"text": TEXT, "belege": " | ".join(BELEGE.split(" | ")[:3])})[0])

    def test_wir_text_und_fett_fehler(self):
        f, _ = pruefen({"text": "Wir zeigen Kunst. Unser Haus ist **alt.", "belege": "https://a.test | https://b.test"})
        self.assertTrue(any("wir" in x for x in f))
        self.assertTrue(any("Fettschrift" in x for x in f))

    def test_hinweis_bei_uhrzeit_und_preis(self):
        _, h = pruefen({"text": "Einlass ist um 19 Uhr. Karten kosten 10 €.", "belege": "https://a.test | https://b.test"})
        self.assertTrue(any("Uhrzeit" in x for x in h) and any("Preis" in x for x in h))


class SqlTest(unittest.TestCase):
    def test_nur_freigegebene_ohne_fehler(self):
        zeilen = [
            {"slug": "tonhalle", "text": TEXT, "belege": BELEGE, "webseite": "https://tonhalle.test", "freigabe": "ja"},
            {"slug": "offen", "text": TEXT, "belege": BELEGE, "webseite": "", "freigabe": ""},
            {"slug": "kaputt", "text": TEXT, "belege": "https://a.test", "webseite": "", "freigabe": "ja"},
        ]
        sql, n, ueber = sql_bauen(zeilen, "2026-11-20")
        self.assertEqual(n, 1)
        self.assertIn("WHERE slug = 'tonhalle' AND typ = 'spielstaette'", sql)
        self.assertIn('"text_freigegeben"', sql)
        self.assertIn("COALESCE(webseite, 'https://tonhalle.test')", sql)
        self.assertNotIn("'offen'", sql)
        self.assertTrue(any(u.startswith("kaputt") for u in ueber))


if __name__ == "__main__":
    unittest.main()
