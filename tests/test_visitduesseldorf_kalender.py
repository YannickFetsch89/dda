"""Tests für den Visit-Düsseldorf-Kalender aus den Eventseiten (Plan Quellen-Ausbau, Schritt V0).
python -m unittest tests.test_visitduesseldorf_kalender"""
import asyncio
import unittest
from datetime import date, timedelta
from unittest import mock

from scraper.tier1 import visitduesseldorf as vd
from scraper.tier1 import visitduesseldorf_fuehrungen as vf

HEUTE = date(2026, 11, 24)


def roh(name, kategorien, termine, ort="Mitsubishi Electric HALLE", **mehr):
    return {
        "name": name, "canceled": False, "trashed": False,
        "category": {"rootlineNames": ["Event", *kategorien]}, "secondaryCategories": [],
        "location": {"name": ort, "address": {"street": "Siegburger Straße", "streetNumber": "15", "zip": "40591", "city": "Düsseldorf"}},
        "locationData": {"address": {}}, "additionalMeetingPointInformation": None,
        "price": {"marketingPrices": [{"price": 49.9}]}, "mainImage": {"url": "https://img.example/x.jpg"},
        "datesCache": [{"date": d, "startAt": z, "active": True} for d, z in termine],
        **mehr,
    }


class KalenderTest(unittest.TestCase):
    def test_termine_kategorie_ort_und_fenster(self):
        cache = {
            "https://www.visitduesseldorf.de/event/aladin": {"roh": roh("Aladin – das Musical", ["Aufführung", "Musical"],
                                                                         [("2026-12-29", "19:30:00"), ("2027-06-01", "19:30:00"), ("2026-11-01", "19:30:00")])},
            "https://www.visitduesseldorf.de/event/jazz": {"roh": roh("Achim Seifert Project", ["Konzert"], [("2026-11-27", "20:00:00")], ort="Jazz-Schmiede Düsseldorf")},
            "https://www.visitduesseldorf.de/event/fuehrung": {"roh": roh("Altstadtführung", ["Führung"], [("2026-12-05", "14:00:00")])},
            "https://www.visitduesseldorf.de/event/schiff": {"roh": roh("Panoramafahrt auf dem Rhein", ["Aktivität", "Schifffahrt"], [("2026-12-01", "12:00:00")], ort=None)},
            "https://www.visitduesseldorf.de/event/abgesagt": {"roh": roh("Abgesagt", ["Konzert"], [("2026-12-05", "20:00:00")], canceled=True)},
        }
        events = vd.events_aus_cache(cache, HEUTE, HEUTE + timedelta(days=120))
        titel = [(e["titel"], e["datum"]) for e in events]
        self.assertEqual(titel, [("Achim Seifert Project", "2026-11-27"), ("Aladin – das Musical", "2026-12-29")])
        aladin = events[1]
        self.assertEqual((aladin["kategorie"], aladin["uhrzeit"], aladin["ort"]), ("kultur", "19:30", "Mitsubishi Electric HALLE"))
        self.assertIn("40591", aladin["adresse"])
        self.assertEqual(aladin["quelle_name"], "VisitDüsseldorf")
        self.assertIsNone(aladin["beschreibung"])
        self.assertEqual(events[0]["kategorie"], "musik")

    def test_kategorien(self):
        self.assertEqual(vd.kategorie_zuordnen(roh("x", ["Party"], [])), "nightlife")
        self.assertEqual(vd.kategorie_zuordnen(roh("x", ["Kinder & Familie", "Theater"], [])), "family")
        self.assertEqual(vd.kategorie_zuordnen(roh("x", ["Sonstiges"], [])), "sonstiges")
        self.assertTrue(vd.ist_fuehrung(roh("x", ["Stadtführung"], [])))
        self.assertTrue(vd.ist_fuehrung(roh("x", ["Museumsführung"], [])))
        self.assertFalse(vd.ist_fuehrung(roh("x", ["Aufführung", "Uraufführung"], [])))
        self.assertFalse(vd.ist_fuehrung(roh("x", ["Filmvorführung", "Vorführung", "Einführung"], [])))
        self.assertTrue(vd.ist_fuehrung(roh("x", ["Kultur", "Führung"], [])))


class SeitenLadenTest(unittest.TestCase):
    def setUp(self):
        vf._GELADEN["cache"] = None

    def tearDown(self):
        vf._GELADEN["cache"] = None

    def test_grenze_je_lauf_und_nur_einmal_je_prozess(self):
        urls = [f"https://www.visitduesseldorf.de/event/e{i}" for i in range(5)]
        sitemap = "<urlset>" + "".join(f"<url><loc>{u}</loc><lastmod>2026-11-2{i}</lastmod></url>" for i, u in enumerate(urls)) + "</urlset>"
        abrufe = []

        async def abrufen(_client, url):
            abrufe.append(url)
            return sitemap if url == vf.SITEMAP_URL else "<div data-tb-detail-event='{\"name\": \"E\"}'></div>"

        with mock.patch.object(vf, "_abrufen", abrufen), mock.patch.object(vf, "_cache_laden", lambda: {}), \
                mock.patch.object(vf, "_cache_speichern", lambda c: None), mock.patch.object(vf, "MAX_NEU_JE_LAUF", 3):
            cache = asyncio.run(vf.seiten_laden())
            asyncio.run(vf.seiten_laden())  # zweiter Aufruf im selben Prozess lädt nichts
        self.assertEqual(len(cache), 3)
        self.assertEqual(len(abrufe), 1 + 3)
        # neueste Seiten zuerst
        self.assertEqual(sorted(cache), sorted(urls[2:]))


if __name__ == "__main__":
    unittest.main()
