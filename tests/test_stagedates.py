"""Tests für Stagedates (Plan Quellen-Ausbau 5.1, Schritt V1). python -m unittest tests.test_stagedates"""
import unittest
from datetime import date
from pathlib import Path

from scraper.tier1 import stagedates as sd
from scraper.utils.jsonld_events import events_aus_html

HTML = (Path(__file__).parent / "fixtures" / "stagedates_event.html").read_text(encoding="utf-8")
URL = "https://stagedates.com/events/habibi-night-dusseldorf-the-eight-club-20261225-NIFB8"


class StagedatesTest(unittest.TestCase):
    def test_sitemap_nach_datum_im_slug(self):
        sitemap = ("<urlset><url><loc>https://stagedates.com/events/a-club-20261201-AB12c</loc></url>"
                   "<url><loc>https://stagedates.com/events/b-club-20261101-XY9</loc></url>"
                   "<url><loc>https://stagedates.com/events/c-club-20281201-ZZ1</loc></url>"
                   "<url><loc>https://stagedates.com/ueber-uns</loc></url></urlset>")
        urls = sd.urls_im_fenster(sitemap, date(2026, 11, 24), date(2027, 11, 24))
        self.assertEqual(list(urls), ["https://stagedates.com/events/a-club-20261201-AB12c"])

    def test_event_aus_jsonld(self):
        termine = events_aus_html(HTML, URL)
        self.assertEqual(len(termine), 1)
        t = termine[0]
        self.assertTrue(sd.ist_im_gebiet(t))
        e = sd.event_aus_termin(t)
        self.assertEqual((e["titel"], e["datum"], e["uhrzeit"]), ("Habibi Night Düsseldorf", "2026-12-25", "23:00"))
        self.assertEqual(e["ort"], "The Eight Club")
        self.assertEqual(e["adresse"], "Rathausufer 8, 40213 Düsseldorf")
        self.assertEqual(e["preis"], "10 €")
        self.assertEqual(e["quelle_url"], URL)
        self.assertEqual(e["quelle_name"], "Stagedates")

    def test_leere_seite_wird_nachgeholt(self):
        from unittest import mock
        heute = date.today()
        url = f"https://stagedates.com/events/x-club-{heute.strftime('%Y%m%d')}-AB1"
        sitemap = f"<urlset><url><loc>{url}</loc></url></urlset>"
        abrufe, gespeichert = [], {}

        def abrufen(u, _logger=None, wartezeit=2.0):
            abrufe.append(u)
            return sitemap if u == sd.SITEMAP_URL else "<html>leer</html>"

        with mock.patch.object(sd, "seite_abrufen", abrufen), mock.patch.object(sd, "_cache_laden", lambda: dict(gespeichert)),                 mock.patch.object(sd, "_cache_speichern", lambda c: gespeichert.update(c)):
            for _ in range(3):
                sd.scrape()
        # zwei Versuche für die leere Seite, danach nicht mehr
        self.assertEqual(abrufe.count(url), sd.MAX_FEHLVERSUCHE)
        self.assertEqual(gespeichert[url]["fehlversuche"], sd.MAX_FEHLVERSUCHE)

    def test_ausserhalb_des_gebiets(self):
        self.assertFalse(sd.ist_im_gebiet({"ort": "Weinerei Club", "adresse": "Hauptstr. 1, 97070 Würzburg"}))


if __name__ == "__main__":
    unittest.main()
