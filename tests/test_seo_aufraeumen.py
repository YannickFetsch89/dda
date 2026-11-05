"""Tests für den Dashboard-Tab „SEO-Aufräumen“ (python -m unittest tests.test_seo_aufraeumen)."""
import unittest

from dashboard.seo_aufraeumen import entscheidungen_bauen, event_url, web_kategorie, ziel_fuer

EV = {"id": "e1", "slug": "jazz-2025-01-10", "titel": "Jazz", "ort": "Jazz-Schmiede", "kategorie": "family",
      "datum": "2025-01-10", "reihe": {"slug": "jazz-am-abend"}}


class SeoAufraeumenTest(unittest.TestCase):
    def test_kategorie_und_url(self):
        self.assertEqual(web_kategorie("family"), "familie")
        self.assertEqual(event_url(EV), "https://diesdas.events/event/familie/jazz-2025-01-10")

    def test_ziele_sind_intern_und_nie_die_startseite(self):
        for art in ("reihe", "ort", "kategorie"):
            ziel = ziel_fuer(EV, art)
            self.assertTrue(ziel.startswith("/") and not ziel.startswith("//") and ziel != "/", ziel)
        self.assertEqual(ziel_fuer(EV, "reihe"), "/reihe/jazz-am-abend")
        self.assertEqual(ziel_fuer(EV, "kategorie"), "/entdecken?kategorie=familie&datum=alle")
        self.assertEqual(ziel_fuer(EV, "ort"), "/entdecken?q=Jazz-Schmiede&datum=alle")

    def test_ohne_reihe_wird_uebersprungen(self):
        ohne = {**EV, "id": "e2", "slug": "x", "reihe": None}
        zeilen, uebersprungen = entscheidungen_bauen([EV, ohne], "reihe", None)
        self.assertEqual([z["event_id"] for z in zeilen], ["e1"])
        self.assertEqual([e["id"] for e in uebersprungen], ["e2"])

    def test_gone_und_behalten_ohne_ziel(self):
        for art, aktion in (("gone", "gone"), ("behalten", "behalten")):
            zeilen, _ = entscheidungen_bauen([EV], art, "admin")
            self.assertEqual((zeilen[0]["aktion"], zeilen[0]["ziel"], zeilen[0]["entschieden_von"]), (aktion, None, "admin"))


class KandidatenTest(unittest.TestCase):
    def _db(self, ids):
        from unittest import mock
        db = mock.MagicMock()
        kette = db.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.or_.return_value
        def seite(lo, hi):
            return mock.Mock(execute=lambda: mock.Mock(data=[{"id": i} for i in ids[lo:hi + 1]]))
        kette.order.return_value.order.return_value.range.side_effect = seite
        return db

    def test_grenze_gilt_fuer_offene_und_blaettert_weiter(self):
        from unittest import mock
        from datetime import date
        import dashboard.seo_aufraeumen as S
        ids = [f"e{i:05d}" for i in range(2500)]
        entschieden = set(ids[:1200])  # die ältesten sind schon entschieden
        with mock.patch.object(S, "SEITE", 1000):
            events, mehr = S.kandidaten_laden(self._db(ids), date(2027, 6, 1), entschieden, max_anzahl=1000)
        self.assertEqual(len(events), 1000)
        self.assertEqual(events[0]["id"], "e01200")  # erste noch offene
        self.assertTrue(mehr)
        with mock.patch.object(S, "SEITE", 1000):
            events, mehr = S.kandidaten_laden(self._db(ids), date(2027, 6, 1), entschieden, max_anzahl=5000)
        self.assertEqual((len(events), mehr), (1300, False))

    def test_tabellen_schluessel_haengt_an_den_zeilen(self):
        from dashboard.seo_aufraeumen import tabellen_schluessel
        self.assertNotEqual(tabellen_schluessel(["a", "b"], False), tabellen_schluessel(["b", "c"], False))
        self.assertNotEqual(tabellen_schluessel(["a"], False), tabellen_schluessel(["a"], True))


if __name__ == "__main__":
    unittest.main()
