"""Tests für den Ticket-Link des Hauses (Plan Quellen-Ausbau 5.5.2, Schritt P1): Baustein, Speichern, Deduplizierung,
Kennzahl und die Venue-Scraper der Welle A.
python -m unittest tests.test_ticket_link"""
import json
import unittest
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup

from scraper.utils import ticket_link as tl

FIXTURES = Path(__file__).parent / "fixtures"


def _lesen(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class BausteinTest(unittest.TestCase):
    def test_anbieter(self):
        self.assertEqual(tl.anbieter("https://www.eventim.de/event/x-123/"), "Eventim")
        self.assertEqual(tl.anbieter("https://nachtresidenz.ticket.io/abc/"), "ticket.io")
        self.assertEqual(tl.anbieter("https://www.eventim-light.com/de/a/1/e/2"), "Eventim")
        self.assertEqual(tl.anbieter("https://tickets.apollo-variete.com/webshop"), "eigener Shop")
        self.assertEqual(tl.anbieter("https://karten.tas-neuss.de/tickets?eventId=1"), "eigener Shop")
        self.assertIsNone(tl.anbieter("https://www.zakk.de/programm"))
        self.assertIsNone(tl.anbieter("https://rausgegangen.de/events/x"))  # Aggregator, kein Ticketverkauf
        self.assertIsNone(tl.anbieter("https://www.paypal.com/ncp/payment/X"))
        self.assertIsNone(tl.anbieter("https://notticket.io.example.com/"))  # nur echte Subdomains zählen

    def test_ticket_link(self):
        self.assertEqual(tl.ticket_link(" https://www.reservix.de/tickets-x/e1 "), "https://www.reservix.de/tickets-x/e1")
        self.assertIsNone(tl.ticket_link("mailto:tickets@eventim.de"))
        self.assertIsNone(tl.ticket_link("/programm", "https://www.zakk.de/"))
        self.assertIsNone(tl.ticket_link(None))
        self.assertEqual(tl.ticket_link("/shop", "https://tickets.haus.de/"), "https://tickets.haus.de/shop")

    def test_ticket_link_aus(self):
        html = '<div><a href="/info">Info</a><a href="mailto:a@eventim.de">x</a><a href="https://www.adticket.de/e.html">Tickets</a></div>'
        self.assertEqual(tl.ticket_link_aus(BeautifulSoup(html, "html.parser"), "https://h.de/"), "https://www.adticket.de/e.html")
        self.assertIsNone(tl.ticket_link_aus(None))


class SpeichernTest(unittest.TestCase):
    """database/client._anreicherungs_update_bauen: ergänzen, behalten, nur vom Besseren oder Eigenen ersetzen."""

    def setUp(self):
        from database.client import _anreicherungs_update_bauen
        self.bauen = _anreicherungs_update_bauen
        self.haus = {"quelle_name": "zakk", "quelle_url": "https://www.zakk.de/e/1", "ticket_url": "https://www.eventim.de/e/1"}

    def test_ergaenzen(self):
        bestehend = {**self.haus, "ticket_url": None}
        neu = {"quelle_name": "Rausgegangen", "quelle_url": "https://rausgegangen.de/x", "ticket_url": "https://www.eventim.de/e/1"}
        self.assertEqual(self.bauen(bestehend, neu, rang_neu=5)["ticket_url"], "https://www.eventim.de/e/1")

    def test_vorhandener_bleibt_ohne_neuen(self):
        neu = {"quelle_name": "zakk", "quelle_url": "https://www.zakk.de/e/1", "ticket_url": None}
        self.assertNotIn("ticket_url", self.bauen(self.haus, neu, rang_neu=1))

    def test_schlechtere_quelle_ersetzt_nicht(self):
        neu = {"quelle_name": "Ticketmaster", "quelle_url": "https://www.ticketmaster.de/e/9", "ticket_url": "https://www.ticketmaster.de/e/9"}
        self.assertNotIn("ticket_url", self.bauen(self.haus, neu, rang_neu=2))

    def test_haus_aendert_eigenen_link(self):
        neu = {**self.haus, "ticket_url": "https://www.reservix.de/e/2"}
        self.assertEqual(self.bauen(self.haus, neu, rang_neu=1)["ticket_url"], "https://www.reservix.de/e/2")

    def test_besserer_rang_ersetzt(self):
        bestehend = {"quelle_name": "Rausgegangen", "quelle_url": "https://rausgegangen.de/x", "ticket_url": "https://x.ticket.io/a"}
        neu = {**self.haus, "ticket_url": "https://www.eventim.de/e/1"}
        update = self.bauen(bestehend, neu, rang_neu=1)
        self.assertEqual((update["quelle_name"], update["ticket_url"]), ("zakk", "https://www.eventim.de/e/1"))

    def test_redaktion_geschuetzt(self):
        bestehend = {**self.haus, "ticket_url": None, "redaktion_felder": ["ticket_url"]}
        self.assertNotIn("ticket_url", self.bauen(bestehend, {**self.haus}, rang_neu=1))

    def test_ohne_spalte_nicht_im_abgleich(self):
        import database.client as client
        try:
            client._TICKET_SPALTE["da"] = False
            self.assertNotIn("ticket_url", client._abgleich_spalten())
            client._TICKET_SPALTE["da"] = True
            self.assertIn("ticket_url", client._abgleich_spalten())
        finally:
            client._TICKET_SPALTE["da"] = True


class DeduplizierungTest(unittest.TestCase):
    def test_link_aus_schlechterer_quelle_ergaenzt(self):
        from pipeline.deduplication import _events_mergen
        haus = {"titel": "A", "datum": "2026-12-01", "ort": "zakk", "quelle_name": "zakk", "quelle_url": "https://www.zakk.de/a"}
        rg = {**haus, "quelle_name": "Rausgegangen", "quelle_url": "https://rausgegangen.de/a", "ticket_url": "https://x.ticket.io/a"}
        self.assertEqual(_events_mergen(haus, rg)["ticket_url"], "https://x.ticket.io/a")
        eigener = {**haus, "ticket_url": "https://www.eventim.de/a"}
        self.assertEqual(_events_mergen(rg, eigener)["ticket_url"], "https://www.eventim.de/a")


class KennzahlTest(unittest.TestCase):
    def test_zaehlen(self):
        from pipeline.quellen_kennzahlen import ticket_links_zaehlen
        anzahl, je = ticket_links_zaehlen([
            {"ticket_url": "https://www.eventim.de/a"}, {"ticket_url": "https://www.eventim.de/b"},
            {"ticket_url": "https://tickets.haus.de/c"}, {"ticket_url": None}, {},
            {"ticket_url": "https://anderswo.example/x"},
        ])
        self.assertEqual(anzahl, 4)
        self.assertEqual(je, {"Eventim": 2, "eigener Shop": 1, "andere": 1})


class ScraperTest(unittest.TestCase):
    """Die Fixtures der Welle A liefern den Ticket-Link des Hauses."""
    HEUTE, ENDE = date(2026, 11, 24), date(2027, 11, 24)

    def _pruefen(self, events, anbieter_erwartet=None, mindestens=1):
        mit = [e for e in events if e.get("ticket_url")]
        self.assertGreaterEqual(len(mit), mindestens, "kein Ticket-Link")
        for e in mit:
            self.assertTrue(e["ticket_url"].startswith(("https://", "http://")), e["ticket_url"])
            self.assertNotEqual(e["ticket_url"], e["quelle_url"])
            if anbieter_erwartet:
                self.assertEqual(tl.anbieter(e["ticket_url"]), anbieter_erwartet, e["ticket_url"])
        return mit

    def test_savoy(self):
        from scraper.tier2 import savoy_theater as m
        html = json.loads(_lesen("savoy_theater_ajax.json"))["html"]
        mit = self._pruefen(m._termine_aus_html(html, self.HEUTE, self.ENDE), "Eventim", 3)
        self.assertNotIn("&amp;", mit[0]["ticket_url"])

    def test_theater_an_der_koe(self):
        from scraper.tier2 import theater_an_der_koe as m
        self._pruefen(m._termine_aus_html(_lesen("theater_an_der_koe_spielplan.html"), self.HEUTE, self.ENDE), "Rodrigue")

    def test_tor3_ohne_paypal(self):
        from scraper.tier2 import tor3 as m
        events = m._termine_aus_html(_lesen("tor3_home2.html"), self.HEUTE, date(2027, 3, 24))
        self._pruefen(events, "Eventim")
        self.assertFalse([e for e in events if "paypal" in (e.get("ticket_url") or "")])

    def test_nachtresidenz(self):
        from scraper.tier2 import nachtresidenz as m
        self._pruefen(m._termine_aus_html(_lesen("nachtresidenz_events.html"), self.HEUTE, date(2027, 3, 24)), mindestens=3)

    def test_bilker_bunker(self):
        from scraper.tier2 import bilker_bunker as m
        self._pruefen(m._termine_aus_html(_lesen("bilker_bunker_schleuse_zwei.html"), self.HEUTE, date(2027, 3, 24)), "Eventim")

    def test_kabarett_flin_eventseite_bei_neanderticket(self):
        from scraper.tier2 import kabarett_flin as m
        mit = self._pruefen(m._termine_aus_html(_lesen("kabarett_flin_widget.html"), self.HEUTE, self.ENDE), "Neanderticket")
        for e in mit:
            self.assertRegex(e["ticket_url"], r"^https://www\.neanderticket\.de/\??\d+$")

    def test_apollo(self):
        from scraper.tier2 import apollo_variete as m
        url = "https://www.apollo-variete.com/apollo-shows/camden-chaos/"
        self._pruefen(m._termine_aus_html(_lesen("apollo_variete_camden.html"), url, self.HEUTE, self.ENDE), "eigener Shop")

    def test_stadt_ratingen(self):
        from scraper.tier2 import stadt_ratingen as m
        detail = m._details_aus_html(_lesen("stadt_ratingen_detail.html"))
        self.assertEqual(tl.anbieter(detail["ticket_url"]), "YesTicket")
        liste = _lesen("stadt_ratingen_liste.html")
        reihen, _ = m._reihen_aus_liste(liste)
        detail["url"] = next(r for r in reihen if r["titel"].startswith("Arsène Lupin"))["url"]
        events = m._termine_aus_html(liste, self.HEUTE, date(2027, 3, 24), {detail["ort"]: detail})
        mit = self._pruefen(events, "YesTicket")
        self.assertTrue(all(e["titel"].startswith("Arsène Lupin") for e in mit))  # nur die Reihe der Detailseite

    def test_comedy_club_nur_externer_verkauf(self):
        from scraper.tier2 import comedy_club as m
        self.assertEqual(m._ticket_url({"ticket_details": [{"external_url": "https://fienta.com/de/x", "active": True}]}),
                         "https://fienta.com/de/x")
        self.assertIsNone(m._ticket_url({"ticket_details": [{"external_url": None, "active": True}]}))
        self.assertIsNone(m._ticket_url({}))

    def test_tas_neuss(self):
        from scraper.tier2 import tas_neuss as m
        self._pruefen(m._termine_aus_html(_lesen("tas_neuss_spielplan.html"), self.HEUTE, self.ENDE), "eigener Shop")

    def test_deg_game_center(self):
        from scraper.tier3 import deg as m
        html = '<div class="gc-actions"><a class="gc-button" href="https://www.deg-tickets.de/spiel/1">Tickets</a></div>'
        self.assertEqual(m._game_center_auswerten(html)["ticket_url"], "https://www.deg-tickets.de/spiel/1")
        kaputt = '<div class="gc-actions"><a class="gc-button" href="javascript:void(0)">Tickets</a></div>'
        self.assertIsNone(m._game_center_auswerten(kaputt)["ticket_url"])


if __name__ == "__main__":
    unittest.main()
