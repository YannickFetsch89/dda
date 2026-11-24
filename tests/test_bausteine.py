"""Tests für die Bausteine JSON-LD, WP-Tribe und iCal (Plan Quellen-Ausbau 3.3, Schritt V1).
python -m unittest tests.test_bausteine"""
import json
import unittest
from datetime import date
from unittest import mock

from scraper.utils import ical, jsonld_events, wp_tribe


class JsonLdTest(unittest.TestCase):
    def test_graph_subevent_zeitzone_angebot(self):
        daten = {"@context": "https://schema.org", "@graph": [
            {"@type": "Organization", "name": "Haus"},
            {"@type": "TheaterEvent", "name": "Hamlet", "url": "/stueck/hamlet", "image": [{"url": "https://h.example/b.jpg"}],
             "location": {"@type": "Place", "name": "Großes Haus", "address": {"streetAddress": "Gustaf-Gründgens-Platz 1", "postalCode": "40211", "addressLocality": "Düsseldorf"}},
             "offers": [{"price": "19"}, {"price": "45,50"}],
             "subEvent": [{"@type": "Event", "startDate": "2026-12-01T19:30:00+01:00"},
                          {"@type": "Event", "startDate": "2026-12-02T18:30:00Z", "eventStatus": "https://schema.org/EventCancelled"}]},
        ]}
        html = f'<html><script type="application/ld+json">{json.dumps(daten)}</script></html>'
        termine = jsonld_events.events_aus_html(html, "https://h.example/spielplan")
        self.assertEqual(len(termine), 2)
        a, b = termine
        self.assertEqual((a["titel"], a["start"], a["uhrzeit"]), ("Hamlet", "2026-12-01", "19:30"))
        self.assertEqual(b["uhrzeit"], "19:30")  # 18:30 UTC → Ortszeit
        self.assertTrue(b["abgesagt"])
        self.assertEqual(a["ort"], "Großes Haus")
        self.assertEqual(a["adresse"], "Gustaf-Gründgens-Platz 1, 40211 Düsseldorf")
        self.assertEqual(a["preis"], "ab 19 €")
        self.assertEqual(a["url"], "https://h.example/stueck/hamlet")
        self.assertEqual(a["bild_url"], "https://h.example/b.jpg")

    def test_kaputtes_skript_und_kein_event(self):
        html = '<script type="application/ld+json">{kaputt</script><script type="application/ld+json">{"@type": "Organization"}</script>'
        self.assertEqual(jsonld_events.events_aus_html(html, "https://x"), [])


class TribeTest(unittest.TestCase):
    def test_seiten_und_felder(self):
        seiten = {
            1: {"events": [{"title": "Lesung &amp; Gespräch", "start_date": "2026-12-03 19:00:00", "end_date": "2026-12-03 21:00:00",
                            "url": "https://i.example/e/1", "cost": "Eintritt frei", "venue": {"venue": "Raketenstation", "address": "Raketenstation Hombroich 4", "zip": "41472", "city": "Neuss"},
                            "image": {"url": "https://i.example/1.jpg"}, "all_day": False}], "total_pages": 2},
            2: {"events": [{"title": "Ausstellung", "start_date": "2026-12-05 00:00:00", "all_day": True, "url": "https://i.example/e/2"}], "total_pages": 2},
        }
        abrufe = []

        def abrufen(url, logger=None, wartezeit=2.0):
            abrufe.append(url)
            return json.dumps(seiten[int(url.rsplit("page=", 1)[1])])

        with mock.patch.object(wp_tribe, "seite_abrufen", abrufen):
            termine = wp_tribe.events_holen("https://i.example/", date(2026, 11, 24), date(2027, 11, 24))
        self.assertEqual(len(abrufe), 2)
        self.assertEqual([t["titel"] for t in termine], ["Lesung & Gespräch", "Ausstellung"])
        self.assertEqual((termine[0]["uhrzeit"], termine[0]["preis"], termine[0]["adresse"]), ("19:00", "kostenlos", "Raketenstation Hombroich 4, 41472 Neuss"))
        self.assertIsNone(termine[1]["uhrzeit"])


ICS = """BEGIN:VCALENDAR\r
BEGIN:VEVENT\r
SUMMARY:Plattenparty\r
DTSTART:20261204T190000Z\r
RRULE:FREQ=WEEKLY;INTERVAL=2;COUNT=4\r
EXDATE:20261218T190000Z\r
LOCATION:The Vinyl Room\\, Düsseldorf\r
URL:https://v.example/plattenparty\r
END:VEVENT\r
BEGIN:VEVENT\r
SUMMARY:Ganztags-Markt mit sehr langem Titel, der über\r
  zwei Zeilen geht\r
DTSTART;VALUE=DATE:20261212\r
DTEND;VALUE=DATE:20261214\r
END:VEVENT\r
BEGIN:VEVENT\r
SUMMARY:Abgesagt\r
DTSTART:20261205T200000\r
STATUS:CANCELLED\r
END:VEVENT\r
END:VCALENDAR\r
"""


class IcalTest(unittest.TestCase):
    def test_termine(self):
        termine = ical.termine_aus_ics(ICS, date(2026, 11, 24), date(2027, 3, 1))
        party = [t for t in termine if t["titel"] == "Plattenparty"]
        # 4 Termine alle zwei Wochen ab 04.12., der 18.12. fällt aus
        self.assertEqual([t["start"] for t in party], ["2026-12-04", "2027-01-01", "2027-01-15"])
        self.assertEqual(party[0]["uhrzeit"], "20:00")  # 19:00 UTC → MEZ
        self.assertEqual(party[0]["ort"], "The Vinyl Room, Düsseldorf")
        markt = [t for t in termine if t["titel"].startswith("Ganztags-Markt")]
        self.assertEqual(len(markt), 1)
        self.assertIn("zwei Zeilen", markt[0]["titel"])
        self.assertEqual((markt[0]["uhrzeit"], markt[0]["ende"]), (None, "2026-12-14"))
        self.assertFalse([t for t in termine if t["titel"] == "Abgesagt"])

    def test_nicht_unterstuetzte_regel_nur_erster_termin(self):
        text = "BEGIN:VEVENT\nSUMMARY:X\nDTSTART:20261201T100000\nRRULE:FREQ=MONTHLY;BYDAY=1MO\nEND:VEVENT"
        self.assertEqual(len(ical.termine_aus_ics(text, date(2026, 11, 1), date(2027, 11, 1))), 1)


if __name__ == "__main__":
    unittest.main()
