"""Tests zur Cursor-Prüfung der Scraper-Neubauten (24.11.2026): Schlüssel nie im Log, Zeitbudget, Sperrliste für
Ticket-Links der Häuser, Gebiet bei Stagedates und Ticketmaster ohne Stadt.
python -m unittest tests.test_cursor_scraper_2026_11_24"""
import logging
import unittest
from datetime import date, timedelta
from unittest import mock

import httpx

from pipeline.gebiet import adresse_im_gebiet, plz_im_gebiet, stadt_im_gebiet
from scraper.tier1 import stagedates, ticketmaster as tm
from scraper.utils.ticket_link import ticket_link_haus


class SchluesselTest(unittest.TestCase):
    def test_ohne_schluessel(self):
        text = "Client error '400 Bad Request' for url 'https://app.ticketmaster.com/x.json?apikey=GEHEIM123&size=200'"
        self.assertNotIn("GEHEIM123", tm.ohne_schluessel(text))
        self.assertIn("apikey=***", tm.ohne_schluessel(text))

    def test_http_fehler_loggt_keinen_schluessel(self):
        anfrage = httpx.Request("GET", "https://app.ticketmaster.com/discovery/v2/events.json?apikey=GEHEIM123")
        antwort = httpx.Response(400, request=anfrage)

        class Client:
            def get(self, *a, **k):
                return antwort

        with self.assertLogs("scraper.tier1.ticketmaster", level="ERROR") as protokoll:
            self.assertIsNone(tm._api_anfrage_mit_backoff(Client(), {"apikey": "GEHEIM123"}))
        self.assertNotIn("GEHEIM123", "\n".join(protokoll.output))

    def test_httpx_zeilen_ohne_schluessel(self):
        logger = logging.getLogger("httpx")
        with self.assertLogs("httpx", level="INFO") as protokoll:
            logger.info('HTTP Request: %s %s "%s"', "GET", "https://app.ticketmaster.com/e.json?apikey=GEHEIM123&page=0", "HTTP/1.1 200 OK")
        self.assertNotIn("GEHEIM123", "\n".join(protokoll.output))


class ZeitbudgetTest(unittest.TestCase):
    def test_rausgegangen_beschreibungen_halten_budget(self):
        from pipeline import beschreibung_quellen as bq
        events = [{"id": str(i), "titel": f"E{i}", "ort": "X"} for i in range(5)]
        zeiten = iter([0, 0, 10, 99999, 99999, 99999, 99999])
        bearbeitet = []
        with mock.patch.object(bq, "offene_rausgegangen_events", return_value=events), \
                mock.patch("database.client.get_supabase_client", return_value=mock.MagicMock()), \
                mock.patch.object(bq, "orte_webseiten", return_value={}), mock.patch.object(bq, "_cache_laden", return_value={}), \
                mock.patch.object(bq, "event_bearbeiten", side_effect=lambda c, e, w, ca: bearbeitet.append(e["id"]) or {}), \
                mock.patch.object(bq.time, "monotonic", side_effect=lambda: next(zeiten)), \
                mock.patch("anthropic.Anthropic"):
            bq.beschreibungen_nachziehen(limit=5, max_sekunden=60)
        self.assertEqual(bearbeitet, ["0", "1"])


class TicketLinkHausTest(unittest.TestCase):
    def test_sperrliste(self):
        self.assertEqual(ticket_link_haus("https://www.livenation.de/event/x"), "https://www.livenation.de/event/x")
        self.assertEqual(ticket_link_haus("/tickets/1", "https://www.deg-eishockey.de/"), "https://www.deg-eishockey.de/tickets/1")
        for url in ("https://www.paypal.com/ncp/payment/X", "https://rausgegangen.de/events/x", "https://t.rausgegangen.de/x",
                    "https://www.facebook.com/events/1", "mailto:karten@haus.de", "javascript:void(0)", "#", None, "ftp://x"):
            self.assertIsNone(ticket_link_haus(url), url)

    def test_dlive_und_deg_nutzen_sperrliste(self):
        from scraper.tier2 import dlive
        from scraper.tier3 import deg
        api = {"links": [{"class": "tickets-conversion", "url": "https://www.paypal.com/x"}]}
        self.assertIsNone(dlive._ticket_url(api))
        html = '<div class="gc-actions"><a class="gc-button" href="https://www.paypal.me/deg">Tickets</a></div>'
        self.assertIsNone(deg._game_center_auswerten(html)["ticket_url"])


class GebietTest(unittest.TestCase):
    def test_bausteine(self):
        self.assertTrue(plz_im_gebiet("40474"))
        self.assertTrue(plz_im_gebiet("41460"))
        self.assertFalse(plz_im_gebiet("47051"))
        self.assertFalse(plz_im_gebiet(""))
        self.assertTrue(stadt_im_gebiet("Neuss"))
        self.assertTrue(stadt_im_gebiet("Dusseldorf"))
        self.assertFalse(stadt_im_gebiet("Neusser Straße 5"))
        self.assertFalse(adresse_im_gebiet("Neusser Straße 5", "Club X"))
        self.assertFalse(adresse_im_gebiet("Neusser Straße 5, 50670 Köln"))
        self.assertTrue(adresse_im_gebiet("Kölner Str. 1, 40211 Düsseldorf"))
        self.assertTrue(adresse_im_gebiet("Am Hafen 1, Neuss"))

    def test_bindestrich_und_plz_als_adressteil(self):
        for stadt in ("Düsseldorf-Benrath", "Neuss-Holzheim", "Ratingen-Lintorf"):
            self.assertTrue(stadt_im_gebiet(stadt), stadt)
        self.assertFalse(stadt_im_gebiet("Neusser Straße"))
        self.assertFalse(stadt_im_gebiet("Grevenbroich-Neusser Land"))
        self.assertFalse(adresse_im_gebiet("Neusser Str. 40210, Köln"))       # Zahl in der Straße ist keine PLZ
        self.assertTrue(adresse_im_gebiet("Maxstraße 12345, Düsseldorf"))
        self.assertTrue(adresse_im_gebiet("Urdenbacher Allee 6, 40593 Düsseldorf-Benrath"))
        self.assertFalse(adresse_im_gebiet("Plessingstraße 20, 47051 Duisburg"))

    def test_ticketmaster_bindestrich_mit_plz(self):
        e = {"name": "Konzert", "url": "https://www.ticketmaster.de/event/2",
             "dates": {"start": {"localDate": (date.today() + timedelta(days=5)).isoformat(), "localTime": "20:00:00"}},
             "_embedded": {"venues": [{"name": "Schloss", "city": {"name": "Düsseldorf-Benrath"}, "postalCode": "40597"}]},
             "classifications": [], "images": []}
        self.assertIsNotNone(tm._event_parsen(e, date.today()))
        e["_embedded"]["venues"][0] = {"name": "Halle", "city": {"name": "Duisburg"}, "postalCode": "47051"}
        self.assertIsNone(tm._event_parsen(e, date.today()))

    def test_stagedates(self):
        self.assertFalse(stagedates.ist_im_gebiet({"adresse": "Neusser Straße 5", "ort": "Bar"}))
        self.assertTrue(stagedates.ist_im_gebiet({"adresse": "Ronsdorfer Str. 143, 40233 Düsseldorf", "ort": "Rudas"}))

    def test_ticketmaster_ohne_stadt_nur_mit_plz_im_gebiet(self):
        def ereignis(venue):
            return {"name": "Konzert", "url": "https://www.ticketmaster.de/event/1",
                    "dates": {"start": {"localDate": (date.today() + timedelta(days=5)).isoformat(), "localTime": "20:00:00"}},
                    "_embedded": {"venues": [venue]}, "classifications": [], "images": []}
        heute = date.today()
        self.assertIsNone(tm._event_parsen(ereignis({"name": "Halle X"}), heute))
        self.assertIsNone(tm._event_parsen(ereignis({"name": "Halle X", "postalCode": "47051"}), heute))
        self.assertIsNotNone(tm._event_parsen(ereignis({"name": "Halle X", "postalCode": "40474"}), heute))
        self.assertIsNone(tm._event_parsen(ereignis({"name": "Halle X", "city": {"name": "Neusser Land"}}), heute))


if __name__ == "__main__":
    unittest.main()
