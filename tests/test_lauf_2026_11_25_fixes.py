"""
Fixes nach dem Volllauf 45611523099 (25.11.2026, Plan Quellen-Ausbau Anhang C):
Ticketmaster-Parkangebote am Ort, VisitDüsseldorf-Einzelpreis (VIP-Paket), Abgleich über die Quell-Adresse,
Kategorisierung seitenweise mit Zeitbudget.
python -m unittest tests.test_lauf_2026_11_25_fixes
"""
import unittest
from datetime import date
from unittest import mock

from database.client import gleiche_quell_url
from pipeline import categorizer
from scraper.tier1 import ticketmaster as tm
from scraper.tier1.visitduesseldorf_fuehrungen import _preis
from tests.test_ticketmaster import roh


class TicketmasterParkort(unittest.TestCase):
    def test_tiefgarage_als_ort_ist_kein_event(self):
        e = roh(1)
        e["name"] = "Muse – The Wow! Signal Europa Tour"
        e["_embedded"]["venues"][0]["name"] = "Tiefgarage PSD BANK DOME"
        self.assertIsNone(tm._event_parsen(e, date.today()))

    def test_parkhaus_und_parkplatz(self):
        for ort in ("Parkhaus Merkur Spiel-Arena", "PARKPLATZ P1 Messe"):
            e = roh(2)
            e["_embedded"]["venues"][0]["name"] = ort
            self.assertIsNone(tm._event_parsen(e, date.today()), ort)

    def test_halle_bleibt(self):
        self.assertIsNotNone(tm._event_parsen(roh(3), date.today()))

    def test_ort_mit_park_im_namen_bleibt(self):
        # „Parkbühne“, „Volksgarten-Park …“ sind echte Orte – nur Parkangebote am Anfang des Namens fallen weg
        e = roh(4)
        e["_embedded"]["venues"][0]["name"] = "Parkbühne Düsseldorf"
        self.assertIsNotNone(tm._event_parsen(e, date.today()))


class VisitDuesseldorfPreis(unittest.TestCase):
    def preis(self, werte, praefix=""):
        return _preis({"price": {"marketingPrices": [{"price": w} for w in werte], "marketingPricePrefix": praefix}})

    def test_einzelner_hoher_preis_wird_verworfen(self):
        self.assertIsNone(self.preis([304.9]))

    def test_einzelner_normaler_preis(self):
        self.assertEqual(self.preis([45.9]), "45,90 €")
        self.assertEqual(self.preis([200]), "200 €")

    def test_mehrere_preise_nehmen_den_kleinsten(self):
        self.assertEqual(self.preis([304.9, 59.5]), "ab 59,50 €")

    def test_hoher_preis_mit_praefix_bleibt(self):
        self.assertEqual(self.preis([250], praefix="ab"), "ab 250 €")

    def test_kostenlos(self):
        self.assertEqual(_preis({"price": {"freeEntry": True}}), "kostenlos")


class AbgleichQuellAdresse(unittest.TestCase):
    URL = "https://www.mitsubishi-electric-halle.de/event/lichterkinder-28-11-2026"

    def bestand(self):
        return [
            {"id": "alt", "titel": "Lichterkinder // Live - Millionen Sterne Tour 2026", "uhrzeit": "15:30:00",
             "quelle_url": "https://rausgegangen.de/events/lichterkinder",
             "quellen": [{"url": self.URL + "/", "name": "d-live", "rang": 1}]},
            {"id": "anderes", "titel": "Paul Panzer", "uhrzeit": "18:00:00",
             "quelle_url": "https://www.mitsubishi-electric-halle.de/event/paul-panzer", "quellen": []},
        ]

    def test_gleiche_url_und_uhrzeit_trifft_auch_bei_anderem_titel(self):
        t = gleiche_quell_url(self.bestand(), {"titel": "Lichterkinder", "uhrzeit": "15:30", "quelle_url": self.URL})
        self.assertEqual(t["id"], "alt")

    def test_andere_uhrzeit_ist_weiterer_termin(self):
        self.assertIsNone(gleiche_quell_url(self.bestand(), {"uhrzeit": "19:00", "quelle_url": self.URL}))

    def test_ohne_uhrzeit_kein_treffer(self):
        self.assertIsNone(gleiche_quell_url(self.bestand(), {"uhrzeit": None, "quelle_url": self.URL}))

    def test_sammel_url_mit_mehreren_treffern_bleibt_getrennt(self):
        kalender = "https://www.d-live.de/events/eventkalender"
        bestand = [{"id": "a", "uhrzeit": "20:00", "quelle_url": kalender}, {"id": "b", "uhrzeit": "20:00", "quelle_url": kalender}]
        self.assertIsNone(gleiche_quell_url(bestand, {"uhrzeit": "20:00", "quelle_url": kalender}))


class FakeAbfrage:
    """Supabase-Abfrage-Kette; liefert `gesamt` Zeilen seitenweise und merkt sich die angefragten Bereiche."""

    def __init__(self, gesamt, bereiche):
        self.gesamt, self.bereiche = gesamt, bereiche

    def __getattr__(self, name):
        return lambda *a, **k: self

    def range(self, von, bis):
        self.bereiche.append((von, bis))
        self.von, self.bis = von, bis
        return self

    def execute(self):
        bis = min(self.bis, self.gesamt - 1, self.von + 999)  # PostgREST: höchstens 1.000 Zeilen
        return mock.Mock(data=[{"id": str(i), "titel": f"E{i}"} for i in range(self.von, bis + 1)])


class KategorisierungSeitenweise(unittest.TestCase):
    def laden(self, gesamt, limit, max_sekunden=None, ki=None):
        bereiche = []
        db = mock.Mock()
        db.table.return_value = FakeAbfrage(gesamt, bereiche)
        with mock.patch.object(categorizer, "get_supabase_client", return_value=db), \
                mock.patch.object(categorizer, "_claude_client_erstellen", return_value=object()), \
                mock.patch.object(categorizer, "_event_kategorisieren_und_beschreiben",
                                  side_effect=ki or (lambda c, e: (None, None, None))), \
                mock.patch.object(categorizer.time, "sleep"):
            categorizer.kategorisieren(limit=limit, max_sekunden=max_sekunden)
        return bereiche

    def test_1500_werden_in_zwei_seiten_geladen(self):
        with self.assertLogs("pipeline.categorizer", level="INFO") as log:
            bereiche = self.laden(gesamt=3000, limit=1500)
        self.assertEqual(bereiche, [(0, 999), (1000, 1499)])
        self.assertTrue(any("1500 Events zur Kategorisierung geladen" in z for z in log.output))

    def test_weniger_als_eine_seite(self):
        self.assertEqual(self.laden(gesamt=40, limit=1500), [(0, 999)])

    def test_zeitbudget_bricht_ab(self):
        uhr = iter([0.0, 0.0, 10.0, 99999.0, 99999.0, 99999.0])
        aufrufe = []

        def ki(client, event):
            aufrufe.append(event["id"])
            return None, None, None

        with mock.patch.object(categorizer.time, "monotonic", side_effect=lambda: next(uhr)):
            self.laden(gesamt=5, limit=10, max_sekunden=60, ki=ki)
        self.assertEqual(aufrufe, ["0", "1"])


if __name__ == "__main__":
    unittest.main()
