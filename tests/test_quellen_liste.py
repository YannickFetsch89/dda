"""Tests für die Quellenliste events.quellen und die Quellen-Kennzahlen (Plan Quellen-Ausbau 4.3/4.5, Schritt R2).
python -m unittest tests.test_quellen_liste"""
import unittest
from datetime import datetime, timedelta, timezone

from database.client import _anreicherungs_update_bauen
from pipeline.deduplication import deduplizieren
from pipeline.quellen_kennzahlen import bestand_zaehlen, luecken_berechnen
from pipeline.quellen_rang import QUELLEN_FELD, nur_rausgegangen, quellen_der_zeile, quellen_vereinigen


def iso(tage_her: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=tage_her)).isoformat(timespec="seconds")


def ev(quelle, **mehr):
    e = {
        "titel": "Sibel Schick im Gespräch", "ort": "zakk", "datum": "2026-12-01", "uhrzeit": "20:00",
        "quelle_name": quelle, "quelle_url": f"https://{quelle.lower().replace(' ', '-')}.example/x", "_scraper": quelle,
    }
    e.update(mehr)
    return e


class VereinigenTest(unittest.TestCase):
    def test_neue_quelle_wird_angehaengt(self):
        liste, geaendert = quellen_vereinigen([{"name": "zakk", "url": "u", "rang": 1, "zuletzt": iso()}],
                                              [{"name": "Rausgegangen", "url": "r", "rang": 5, "zuletzt": iso()}])
        self.assertTrue(geaendert)
        self.assertEqual([e["name"] for e in liste], ["zakk", "Rausgegangen"])

    def test_gleiche_quelle_hoechstens_einmal(self):
        alt = [{"name": "zakk", "url": "u", "rang": 1, "zuletzt": iso(1)}]
        liste, geaendert = quellen_vereinigen(alt, [{"name": "zakk", "url": "u", "rang": 1, "zuletzt": iso()}])
        self.assertEqual(len(liste), 1)
        self.assertFalse(geaendert, "frisches „zuletzt“ allein ist kein Grund für ein Update")

    def test_veraltetes_zuletzt_und_neuer_link(self):
        alt = [{"name": "zakk", "url": "u", "rang": 1, "zuletzt": iso(10)}]
        liste, geaendert = quellen_vereinigen(alt, [{"name": "zakk", "url": "u", "rang": 1, "zuletzt": iso()}])
        self.assertTrue(geaendert)
        self.assertGreater(liste[0]["zuletzt"], alt[0]["zuletzt"])
        _, geaendert = quellen_vereinigen(alt, [{"name": "zakk", "url": "neu", "rang": 1, "zuletzt": iso(10)}])
        self.assertTrue(geaendert)

    def test_alte_zeile_ohne_liste(self):
        self.assertEqual(quellen_der_zeile({"quelle_name": "Rausgegangen", "quelle_url": None})[0]["rang"], 5)
        self.assertEqual(quellen_der_zeile({"quelle_name": None}), [])
        self.assertTrue(nur_rausgegangen([{"name": "Rausgegangen", "rang": 5}]))
        self.assertFalse(nur_rausgegangen([{"name": "Rausgegangen", "rang": 5}, {"name": "zakk", "rang": 1}]))
        self.assertFalse(nur_rausgegangen([]))


class DeduplizierungTest(unittest.TestCase):
    def test_merge_merkt_beide_quellen(self):
        ergebnis = deduplizieren([ev("Rausgegangen", quelle_url="https://rausgegangen.de/events/x"), ev("zakk")])
        self.assertEqual(len(ergebnis), 1)
        self.assertEqual(ergebnis[0]["quelle_name"], "zakk")
        namen = {e["name"]: e["rang"] for e in ergebnis[0][QUELLEN_FELD]}
        self.assertEqual(namen, {"Rausgegangen": 5, "zakk": 1})

    def test_einzelnes_event_hat_seine_quelle(self):
        ergebnis = deduplizieren([ev("zakk")])
        self.assertEqual([e["name"] for e in ergebnis[0][QUELLEN_FELD]], ["zakk"])


class SpeichernTest(unittest.TestCase):
    def test_duplikat_ergaenzt_die_liste(self):
        bestehend = {"id": "x", **{k: v for k, v in ev("zakk").items() if not k.startswith("_")},
                     "quellen": [{"name": "zakk", "url": "u", "rang": 1, "zuletzt": iso()}]}
        neu = {"quelle_name": "Rausgegangen", "quelle_url": "https://rausgegangen.de/events/x",
               "quellen": [{"name": "Rausgegangen", "url": "https://rausgegangen.de/events/x", "rang": 5, "zuletzt": iso()}]}
        update = _anreicherungs_update_bauen(bestehend, neu, rang_neu=5)
        self.assertEqual([e["name"] for e in update["quellen"]], ["zakk", "Rausgegangen"])
        self.assertNotIn("quelle_name", update)

    def test_bekannte_quelle_schreibt_nicht(self):
        bestehend = {"id": "x", "quelle_name": "zakk", "quelle_url": "u",
                     "quellen": [{"name": "zakk", "url": "u", "rang": 1, "zuletzt": iso(1)}]}
        neu = {"quelle_name": "zakk", "quelle_url": "u", "quellen": [{"name": "zakk", "url": "u", "rang": 1, "zuletzt": iso()}]}
        self.assertEqual(_anreicherungs_update_bauen(bestehend, neu, rang_neu=1), {})

    def test_zeile_ohne_liste_bekommt_eine(self):
        bestehend = {"id": "x", "quelle_name": "zakk", "quelle_url": "u"}
        neu = {"quelle_name": "zakk", "quelle_url": "u", "quellen": [{"name": "zakk", "url": "u", "rang": 1, "zuletzt": iso()}]}
        self.assertEqual(len(_anreicherungs_update_bauen(bestehend, neu, rang_neu=1)["quellen"]), 1)


class LueckenTest(unittest.TestCase):
    def test_luecke_nur_an_direkt_abgefragtem_haus_ohne_treffer_am_tag(self):
        events = deduplizieren([
            ev("zakk", titel="Konzert A", datum="2026-12-01", ort_id="zakk-halle", _haus_id="zakk"),
            ev("Rausgegangen", titel="Lesung B", datum="2026-12-02", ort_id="zakk-studio", _haus_id="zakk",
               quelle_url="https://rausgegangen.de/events/b"),
            ev("Rausgegangen", titel="Party C", datum="2026-12-01", ort_id="zakk-club", _haus_id="zakk",
               quelle_url="https://rausgegangen.de/events/c"),
            ev("Rausgegangen", titel="Yoga D", ort="Bar Lola", datum="2026-12-02", ort_id="lola",
               quelle_url="https://rausgegangen.de/events/d"),
        ])
        # B: Haus zakk direkt abgefragt, an dem Tag kein zakk-Event → Lücke; C: zakk hat am Tag ein Event → keine;
        # D: Bar Lola fragen wir nicht direkt ab → keine
        self.assertEqual(luecken_berechnen(events), {"zakk": 1})

    def test_rausgegangen_mit_direkttreffer_ist_keine_luecke(self):
        events = deduplizieren([
            ev("Rausgegangen", quelle_url="https://rausgegangen.de/events/x", ort_id="zakk", datum="2026-12-03"),
            ev("zakk", ort_id="zakk", datum="2026-12-03"),
        ])
        self.assertEqual(luecken_berechnen(events), {})


class FakeDb:
    """Minimaler Ersatz für den Supabase-Client (select/eq/gte/order/range/execute)."""

    def __init__(self, zeilen, fehler=False):
        self.zeilen, self.fehler, self.start, self.ende = zeilen, fehler, 0, 0

    def table(self, _):
        return self

    def select(self, _):
        return self

    def eq(self, *_):
        return self

    def gte(self, *_):
        return self

    def order(self, *_):
        return self

    def range(self, start, ende):
        self.start, self.ende = start, ende
        return self

    def execute(self):
        if self.fehler:
            raise RuntimeError("Spalte quellen fehlt")
        return type("A", (), {"data": self.zeilen[self.start:self.ende + 1]})()


class BestandTest(unittest.TestCase):
    def test_zaehlt_nur_rausgegangen(self):
        zeilen = [
            {"id": "1", "quelle_name": "Rausgegangen", "quelle_url": None, "quellen": None},
            {"id": "2", "quelle_name": "zakk", "quelle_url": "u", "quellen": [{"name": "zakk", "rang": 1}, {"name": "Rausgegangen", "rang": 5}]},
            {"id": "3", "quelle_name": "Rausgegangen", "quelle_url": "r", "quellen": [{"name": "Rausgegangen", "rang": 5}]},
        ]
        self.assertEqual(bestand_zaehlen(FakeDb(zeilen), "2026-11-24"), (3, 2))

    def test_fehler_liefert_none(self):
        self.assertEqual(bestand_zaehlen(FakeDb([], fehler=True), "2026-11-24"), (None, None))


if __name__ == "__main__":
    unittest.main()


class OhneQuellenSpalteTest(unittest.TestCase):
    """Fehlt events.quellen (SQL nicht ausgeführt), speichert der Lauf trotzdem – ohne Quellenliste (Ausfall 24.11.2026)."""

    class Db:
        def __init__(self):
            self.inserts, self._quellen_gefragt = [], False

        def table(self, _):
            self._quellen_gefragt = False
            return self

        def select(self, spalten, **_):
            self._quellen_gefragt = "quellen" in spalten
            return self

        def insert(self, datensatz):
            self.inserts.append(datensatz)
            self._quellen_gefragt = "quellen" in datensatz
            return self

        def __getattr__(self, _):
            return lambda *a, **k: self

        @property
        def not_(self):
            return self

        def execute(self):
            if self._quellen_gefragt:
                raise RuntimeError("column events.quellen does not exist")
            return type("A", (), {"data": [], "count": 0})()

    def test_speichert_ohne_quellenliste(self):
        from unittest import mock
        import database.client as client
        db = self.Db()
        event = {**ev("zakk"), "kategorie": "musik"}
        try:
            with mock.patch.object(client, "get_supabase_client", lambda: db):
                ergebnis = client.events_speichern(deduplizieren([event]))
            self.assertEqual(ergebnis["fehler"], 0)
            self.assertEqual(ergebnis["gespeichert"], 1)
            self.assertNotIn("quellen", db.inserts[0])
        finally:
            client._QUELLEN_SPALTE["da"] = True

    def test_netzfehler_schaltet_quellenliste_nicht_ab(self):
        import database.client as client

        class Kaputt:
            def table(self, _):
                raise RuntimeError("Server disconnected without sending a response")
        try:
            self.assertTrue(client._quellen_spalte_pruefen(Kaputt()))
        finally:
            client._QUELLEN_SPALTE["da"] = True
