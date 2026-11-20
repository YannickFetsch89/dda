"""Tests für den PRINZ.de-Scraper (python -m unittest tests.test_prinz). Ohne Netz: nachgebaute Teaser der Seite
„7 Tage“ (Aufbau wie am 20.11.2026)."""
import unittest
from datetime import date
from unittest import mock

from scraper.tier1 import prinz


def teaser(nr, slug, datum, kategorie, stadt, ort, titel, zeit="20:00"):
    return f"""
<article id="event-teaser-{nr}" class="card h-100 event-teaser post-{nr} event type-event event_category-{kategorie} portal-duesseldorf">
  <a href="https://prinz.de/events/{slug}/{datum}/"><img src="https://prinz.de/bild-{nr}.jpg"></a>
  <div class="event-teaser-category">Kategorie</div>
  <h3>{titel}</h3>
  <div class="event-teaser-meta" title="{stadt}, {ort}">
    <div><span class="fw-bold">{zeit}</span> - <span class="text-primary">{stadt}</span></div>
    <div>{ort}</div>
  </div>
</article>"""


SEITE = "<html><body>" + "".join([
    teaser(1, "ballbreakers-ac-dc-tribute", "2026-11-20", "konzerte-livemusik", "Neuss", "Hamtorkrug",
           "Ballbreakers – AC/DC Tribute"),
    teaser(2, "miku-expo", "2026-11-21", "konzerte-livemusik", "Düsseldorf", "PSD BANK DOME", "Miku Expo 2026"),
    teaser(3, "whisky-around-the-world", "2026-11-21", "sonstiges", "Dortmund", "Vienna House", "Whisky"),
    teaser(4, "party-ue40", "2026-11-22", "party-nachtleben", "Düsseldorf", "Stahlwerk", "Ü40-Party"),
    teaser(5, "buchpraesentation", "2026-11-21", "literatur-lesung-diskurs", "Landshut", "Hugendubel", "Buch"),
    # Titel mit Zahl, die früher als Jahr gelesen wurde (26.19 → 2619); das Datum kommt jetzt aus der URL
    teaser(6, "26-19-uhr-show", "2026-11-23", "buehne-theater-show", "Ratingen", "Stadthalle", "Show 26.19"),
    teaser(7, "vergangen", "2026-11-19", "konzerte-livemusik", "Düsseldorf", "zakk", "Gestern"),
]) + "</body></html>"


class PrinzTest(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(prinz, "seite_abrufen", return_value=SEITE):
            self.events = prinz._events_von_seite("https://prinz.de/duesseldorf/events/7-tage/", date(2026, 11, 20))
        self.nach_titel = {e["titel"]: e for e in self.events}

    def test_nur_gebiet_und_keine_vergangenen(self):
        self.assertEqual(sorted(self.nach_titel),
                         sorted(["Ballbreakers – AC/DC Tribute", "Miku Expo 2026", "Ü40-Party", "Show 26.19"]))

    def test_datum_aus_url_und_uhrzeit(self):
        e = self.nach_titel["Show 26.19"]
        self.assertEqual((e["datum"], e["uhrzeit"]), ("2026-11-23", "20:00"))

    def test_kategorie_aus_klasse(self):
        self.assertEqual(self.nach_titel["Ballbreakers – AC/DC Tribute"]["kategorie"], "musik")
        self.assertEqual(self.nach_titel["Ü40-Party"]["kategorie"], "nightlife")
        self.assertEqual(self.nach_titel["Show 26.19"]["kategorie"], "kultur")

    def test_ort_und_adresse(self):
        e = self.nach_titel["Ballbreakers – AC/DC Tribute"]
        self.assertEqual((e["ort"], e["adresse"]), ("Hamtorkrug", "Hamtorkrug, Neuss"))

    def test_seiten(self):
        # Die alten Kategorieseiten sind weg (410 bzw. Weiterleitung); abgerufen wird die Wochenseite
        self.assertEqual(prinz.KATEGORIE_URLS, ["/duesseldorf/events/7-tage/"])

    def test_im_gebiet(self):
        for stadt in ["Düsseldorf", "Neuss", "Ratingen", "Düsseldorf-Benrath", None, ""]:
            self.assertTrue(prinz._im_gebiet(stadt), stadt)
        for stadt in ["Dortmund", "Monheim am Rhein", "Kaarst", "München"]:
            self.assertFalse(prinz._im_gebiet(stadt), stadt)


if __name__ == "__main__":
    unittest.main()
