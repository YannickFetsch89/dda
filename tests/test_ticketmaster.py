"""Tests für den Ticketmaster-Abruf je Monat (Plan Quellen-Ausbau 5.1, Schritt T1). python -m unittest tests.test_ticketmaster"""
import os
import re
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from scraper.tier1 import ticketmaster as tm

WURZEL = Path(__file__).resolve().parents[1]


def roh(nr: int, tage: int = 10, bilder: bool = True) -> dict:
    tag = (date.today() + timedelta(days=tage)).isoformat()
    return {
        "name": f"Konzert {nr}", "url": f"https://www.ticketmaster.de/event/{nr}",
        "dates": {"start": {"localDate": tag, "localTime": "20:00:00"}},
        "_embedded": {"venues": [{"name": "Mitsubishi Electric HALLE", "address": {"line1": "Siegburger Str. 15"},
                                  "city": {"name": "Düsseldorf"}, "postalCode": "40591"}]},
        "classifications": [{"segment": {"name": "Music"}}],
        "images": [{"ratio": "16_9", "width": 1024, "url": f"https://s1.ticketm.net/{nr}.jpg"}] if bilder else [],
    }


class Antwort:
    def __init__(self, daten):
        self.status_code, self._daten = 200, daten

    def json(self):
        return self._daten

    def raise_for_status(self):
        return None


class FakeClient:
    """Liefert im ersten Monatsfenster zwei Seiten mit je zwei Events, sonst nichts; merkt sich die Parameter.
    kaputt_ab: ab dem n-ten Fenster (0 = erstes) antwortet die API mit HTTP 500."""

    def __init__(self, kaputt_ab=None):
        self.aufrufe = []
        self.kaputt_ab = kaputt_ab
        self.fenster = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None, timeout=None):
        self.aufrufe.append(dict(params))
        if params["startDateTime"] not in self.fenster:
            self.fenster.append(params["startDateTime"])
        if self.kaputt_ab is not None and self.fenster.index(params["startDateTime"]) >= self.kaputt_ab:
            raise tm.httpx.TimeoutException("Zeitüberschreitung")
        seite = params["page"]
        if self.fenster.index(params["startDateTime"]) == 0:
            events = [roh(1000 * seite + i) for i in range(2)]
            return Antwort({"_embedded": {"events": events}, "page": {"totalPages": 2}})
        return Antwort({"page": {"totalPages": 0}})


class MonatsfensterTest(unittest.TestCase):
    def test_monate_bis_zum_ende(self):
        f = tm.monatsfenster(date(2026, 11, 24), date(2027, 11, 24))
        self.assertEqual(len(f), 13)
        # erstes Fenster zwei Stunden vor Mitternacht UTC (Event um 00:30 Ortszeit)
        self.assertEqual(f[0], ("2026-11-23T22:00:00Z", "2026-11-30T23:59:59Z"))
        self.assertEqual(f[1], ("2026-12-01T00:00:00Z", "2026-12-31T23:59:59Z"))
        self.assertEqual(f[-1], ("2027-11-01T00:00:00Z", "2027-11-24T23:59:59Z"))

    def test_grenze_der_api(self):
        self.assertLessEqual(tm.SEITENGROESSE * 5, tm.MAX_TREFFER_JE_ABFRAGE)


class ScrapeTest(unittest.TestCase):
    def lauf(self, umgebung, kaputt_ab=None):
        client = FakeClient(kaputt_ab)
        with mock.patch.dict(os.environ, umgebung, clear=False), \
                mock.patch.object(tm.httpx, "Client", lambda **kw: client), mock.patch.object(tm.time, "sleep"):
            os.environ.pop("VORSCHAU_NOTAUS", None)
            return tm.scrape(), client

    def test_ohne_schluessel_uebersprungen(self):
        with mock.patch.dict(os.environ, {"TICKETMASTER_API_KEY": ""}):
            self.assertEqual(tm.scrape(), [])

    def test_monate_seiten_und_ohne_bilder(self):
        os.environ.pop("TICKETMASTER_BILDER_OK", None)
        events, client = self.lauf({"TICKETMASTER_API_KEY": "x"})
        self.assertEqual(len(events), 4)  # zwei Seiten à zwei Events im ersten Fenster
        self.assertTrue(all(e["bild_url"] is None for e in events))
        erste = client.aufrufe[0]
        self.assertEqual((erste["geoPoint"], erste["radius"], erste["unit"]), (tm.GEOPUNKT, tm.RADIUS_KM, "km"))
        fenster = {a["startDateTime"] for a in client.aufrufe}
        self.assertGreaterEqual(len(fenster), 12)  # ein Fenster je Monat bis 365 Tage

    def test_fehler_in_einem_fenster_behaelt_die_anderen(self):
        events, client = self.lauf({"TICKETMASTER_API_KEY": "x"}, kaputt_ab=1)
        self.assertEqual(len(events), 4)  # erstes Fenster gelesen, die gestörten übersprungen
        # nach ABBRUCH_NACH_FEHLERN gestörten Fenstern in Folge wird nicht weiter gefragt
        self.assertEqual(len(client.fenster), 1 + tm.ABBRUCH_NACH_FEHLERN)

    def test_bilder_nur_mit_freigabe(self):
        events, _ = self.lauf({"TICKETMASTER_API_KEY": "x", "TICKETMASTER_BILDER_OK": "1"})
        self.assertTrue(events[0]["bild_url"].startswith("https://s1.ticketm.net/"))
        os.environ.pop("TICKETMASTER_BILDER_OK", None)


class QuellenTest(unittest.TestCase):
    def test_nur_duesseldorf_neuss_ratingen(self):
        """Der 25-km-Umkreis reicht bis Duisburg (Test 24.11.2026: Theater am Marientor) – solche Orte fallen weg."""
        def mit_ort(name, stadt, plz, strasse):
            e = roh(1)
            e["_embedded"]["venues"] = [{"name": name, "city": {"name": stadt}, "postalCode": plz, "address": {"line1": strasse}}]
            return tm._event_parsen(e, date.today())

        self.assertIsNone(mit_ort("Theater am Marientor", "Duisburg", "47051", "Plessingstraße 20"))
        self.assertIsNone(mit_ort("Scala", "Haan", "42781", "Hauptstr. 1"))
        dome = mit_ort("PSD BANK DOME", "Düsseldorf", "40474", "Theodorstr. 281")
        self.assertEqual(dome["adresse"], "Theodorstr. 281, 40474 Düsseldorf")
        self.assertIsNotNone(mit_ort("Swiss Life Hall", "Neuss", "41460", "Am Hafen 1"))
        self.assertIsNotNone(mit_ort("Stadthalle", "Ratingen", "40878", "Schützenstr. 1"))

    def test_zusatzangebote_sind_keine_events(self):
        for titel in ("THE KEHLANI WORLD TOUR: EU & UK | VIP Upgrades (no ticket included)", "Parkplatz – Rea Garvey",
                      "Konzert X - VIP Package"):
            e = roh(1)
            e["name"] = titel
            self.assertIsNone(tm._event_parsen(e, date.today()), titel)
        e = roh(1)
        e["name"] = "Parkway Drive"
        self.assertIsNotNone(tm._event_parsen(e, date.today()))

    def test_songkick_nicht_mehr_in_quellen(self):
        text = (WURZEL / "main.py").read_text(encoding="utf-8")
        self.assertNotIn("songkick.scrape", text)
        self.assertIn('("Ticketmaster", 1, ticketmaster.scrape)', text)

    def test_workflow_gibt_schluessel_weiter(self):
        text = (WURZEL / ".github" / "workflows" / "scrape.yml").read_text(encoding="utf-8")
        self.assertIn("TICKETMASTER_API_KEY: ${{ secrets.TICKETMASTER_API_KEY }}", text)
        self.assertIn("TICKETMASTER_BILDER_OK: ${{ vars.TICKETMASTER_BILDER_OK }}", text)
        self.assertTrue(re.search(r"VORSCHAU_NOTAUS: \$\{\{ vars\.VORSCHAU_NOTAUS \}\}", text))


if __name__ == "__main__":
    unittest.main()
