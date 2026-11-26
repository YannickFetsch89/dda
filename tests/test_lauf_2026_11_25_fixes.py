"""
Fixes nach dem Volllauf 45611523099 (25.11.2026, Plan Quellen-Ausbau Anhang C):
Ticketmaster-Parkangebote am Ort, VisitDüsseldorf-Einzelpreis (VIP-Paket), Abgleich über die Quell-Adresse,
Kategorisierung seitenweise mit Zeitbudget.
python -m unittest tests.test_lauf_2026_11_25_fixes
"""
import unittest
from datetime import date
from unittest import mock

from pipeline.deduplication import bester_treffer, url_ist_eigen
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
    """Gleiche eigene Quell-Adresse zur selben Uhrzeit = dasselbe Event (bester_treffer, 25./26.11.2026)."""
    URL = "https://www.mitsubishi-electric-halle.de/event/lichterkinder-28-11-2026"
    BRYSON = "https://www.mitsubishi-electric-halle.de/event/bryson-tiller-presents-the-neo-trapsoul-tour"

    def ev(self, titel, uhrzeit, url, quellen=(), ort="Mitsubishi Electric Halle", quelle="d-live"):
        return {"titel": titel, "datum": "2026-11-28", "uhrzeit": uhrzeit, "ort": ort, "quelle_name": quelle,
                "quelle_url": url, "quellen": [{"url": u, "name": "d-live", "rang": 1} for u in quellen]}

    def test_lichterkinder_anderer_titel_gleiche_seite(self):
        alt = self.ev("Lichterkinder // Live - Millionen Sterne Tour 2026", "15:30:00",
                      "https://rausgegangen.de/events/lichterkinder", quellen=[self.URL + "/"])
        anderes = self.ev("Paul Panzer", "15:30:00", "https://www.mitsubishi-electric-halle.de/event/paul-panzer")
        self.assertIs(bester_treffer([alt, anderes], self.ev("Lichterkinder", "15:30", self.URL)), alt)

    def test_bryson_tiller_dreimal(self):
        gut = self.ev("Bryson Tiller – Bryson Tiller Presents: The Neo Trapsoul Tour", "20:00:00", self.BRYSON)
        neu = self.ev("Bryson Tiller, Majid Jordan in Düsseldorf", "20:00:00", self.BRYSON, quelle="AllEvents.in Düsseldorf")
        self.assertIs(bester_treffer([gut], neu), gut)

    def test_andere_uhrzeit_ist_weiterer_termin(self):
        alt = self.ev("Lichterkinder", "15:30", self.URL)
        self.assertIsNone(bester_treffer([alt], self.ev("Lichterkinder Abendshow", "19:00", self.URL)))

    def test_ohne_uhrzeit_kein_treffer_ueber_die_adresse(self):
        alt = self.ev("Messe A", None, "https://x.de/event/messe-a-12345")
        self.assertIsNone(bester_treffer([alt], self.ev("Ganz anderer Titel", None, "https://x.de/event/messe-a-12345")))

    def test_savoy_startseite_ist_sammeladresse(self):
        a = self.ev("Nikita Miller – Natural Born Miller", "20:00", "https://savoy-theater.de", ort="Savoy Theater")
        b = self.ev("Peter Illmann – Eine Zeitreise in das Kult-Jahrzehnt", "20:00", "https://savoy-theater.de", ort="Savoy Theater")
        self.assertIsNone(bester_treffer([a], b))

    def test_verschiedene_hauptadressen_beim_selben_haus(self):
        wort = self.ev("Workshop des Moduls „Wort“", "18:00", "https://zakk.de/event-detail?event=16323", ort="zakk",
                       quellen=["https://zakk.de/event-detail?event=16334"])
        koerper = self.ev("Workshop des Moduls „Körper“", "18:00", "https://zakk.de/event-detail?event=16334", ort="zakk")
        self.assertIsNone(bester_treffer([wort], koerper))

    def test_messe_uebersicht_ist_sammeladresse(self):
        url = "https://www.messe-duesseldorf.de/de/messen_und_events/messen_national_und_international"
        self.assertFalse(url_ist_eigen(url, "MEDICA"))
        self.assertFalse(url_ist_eigen(url, "COMPAMED"))

    def test_eigene_adressen(self):
        self.assertTrue(url_ist_eigen(self.BRYSON, "Bryson Tiller at Mitsubishi Electric Halle"))
        self.assertTrue(url_ist_eigen("https://zakk.de/event-detail?event=15539", "Selig"))
        self.assertTrue(url_ist_eigen("https://www.dhaus.de/programm/spielplan/2026-12/impro/3167", "Offenes Training"))
        self.assertTrue(url_ist_eigen("https://kasematten-duesseldorf.de/31-12-26-silvester-2026", "Silvester an den Kasematten"))
        # nur Jahreszahl oder nur Füllwörter → keine eigene Seite
        self.assertFalse(url_ist_eigen("https://haus.de/programm/2027", "Konzert"))
        self.assertFalse(url_ist_eigen("https://haus.de/events/duesseldorf-live", "Live in Düsseldorf"))


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
