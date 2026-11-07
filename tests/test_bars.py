"""Tests für den Hub „Kneipen & Bars“ in der Flächensuche (python -m unittest tests.test_bars)."""
import unittest

from scraper.orte import bars
from scraper.orte import flaechensuche as fs


def place(primaer, typen=(), rating=4.5, anzahl=200, adresse="Bolkerstraße 1, 40213 Düsseldorf"):
    return {"id": f"x-{primaer}-{len(typen)}", "primaryType": primaer, "types": list(typen) or [primaer],
            "rating": rating, "userRatingCount": anzahl, "formattedAddress": adresse,
            "businessStatus": "OPERATIONAL", "displayName": {"text": "Test"}}


class BarRegelnTest(unittest.TestCase):
    def test_suchtypen_gueltig(self):
        # beer_hall ist kein Places-Typ (Table A) und würde die Anfrage mit HTTP 400 abbrechen
        self.assertNotIn("beer_hall", bars.SUCH_TYPEN_BARS)
        self.assertNotIn("hookah_bar", bars.SUCH_TYPEN_BARS)
        self.assertNotIn("night_club", bars.SUCH_TYPEN_BARS)
        self.assertEqual(bars.SUCH_TYPEN_CLUBS, ["night_club"])

    def test_unterart(self):
        self.assertEqual(bars.unterart(place("cocktail_bar")), "bar")
        self.assertEqual(bars.unterart(place("pub")), "kneipe")
        self.assertEqual(bars.unterart(place("german_restaurant", ["german_restaurant", "brewery"])), "kneipe")  # Nebentyp zählt bewusst nicht
        self.assertEqual(bars.unterart(place("brewery")), "brauhaus")
        self.assertEqual(bars.unterart({**place("restaurant"), "displayName": {"text": "Brauhaus zum Weißen Bären"}}), "brauhaus")

    def test_shisha_auch_als_nebentyp(self):
        self.assertTrue(bars.ist_shisha(place("bar", ["bar", "hookah_bar"])))
        self.assertFalse(bars.ist_bar_ort(place("bar", ["bar", "hookah_bar"])))

    def test_gastropub_ist_kneipe(self):
        self.assertTrue(bars.ist_bar_ort(place("gastropub")))
        self.assertEqual(bars.unterart(place("gastropub")), "kneipe")

    def test_brauhaus_als_restaurant(self):
        self.assertTrue(bars.ist_bar_ort(place("german_restaurant", ["german_restaurant", "brewery"])))
        self.assertFalse(bars.ist_bar_ort(place("italian_restaurant")))

    def test_hotelbar(self):
        self.assertFalse(bars.ist_hotel_ohne_bar(place("cocktail_bar", ["cocktail_bar", "bar", "hotel"])))
        self.assertTrue(bars.ist_hotel_ohne_bar(place("hotel", ["hotel", "bar"])))


class HubFilterTest(unittest.TestCase):
    def tearDown(self):
        fs.hub_setzen("restaurants")

    def test_restaurant_hub_unveraendert(self):
        fs.hub_setzen("restaurants")
        self.assertEqual(fs.ort_typ(place("italian_restaurant")), "restaurant")
        self.assertIsNone(fs.ort_typ(place("pub")))
        self.assertEqual(fs.ist_kandidat(place("cocktail_bar", ["cocktail_bar", "hotel"]))[1], "Ausschlusstyp")
        self.assertTrue(str(fs.ZWISCHENSPEICHER).endswith("flaechensuche.json"))
        self.assertEqual([z.get("typen") for z in fs._typ_nachzuege({"stufe": 3, "i": 1, "j": 1})],
                         [["restaurant"], ["cafe", "coffee_shop"]])

    def test_bar_hub(self):
        fs.hub_setzen("bars")
        self.assertTrue(str(fs.ZWISCHENSPEICHER).endswith("flaechensuche_bars.json"))
        self.assertEqual(fs.SUCH_TYPEN, bars.SUCH_TYPEN_BARS)
        self.assertEqual(fs.ist_kandidat(place("pub")), (True, "ok"))
        self.assertEqual(fs.ist_kandidat(place("cocktail_bar", ["cocktail_bar", "hotel"])), (True, "ok"))  # Hotelbar
        self.assertEqual(fs.ist_kandidat(place("hotel", ["hotel", "bar"]))[1], "Ausschlusstyp")
        self.assertEqual(fs.ist_kandidat(place("bar", ["bar", "hookah_bar"]))[1], "Shisha-Bar")
        self.assertEqual(fs.ist_kandidat(place("night_club"))[1], "keine Kneipe/Bar")  # Clubs getrennt
        self.assertEqual(fs.ist_kandidat(place("pub", adresse="Hauptstr. 1, 40699 Erkrath"))[1], "außerhalb")
        self.assertEqual(len(fs._typ_nachzuege({"stufe": 3, "i": 1, "j": 1})), 3)

    def test_club_hub_getrennt(self):
        fs.hub_setzen("clubs")
        self.assertTrue(str(fs.ZWISCHENSPEICHER).endswith("flaechensuche_clubs.json"))
        self.assertEqual(fs.ist_kandidat(place("night_club")), (True, "ok"))
        self.assertEqual(fs.ist_kandidat(place("pub"))[1], "kein Club")
        self.assertFalse(fs.HUBS["clubs"]["import"])
        self.assertEqual(fs.importieren(10, 1, True), {})  # kein Import für Clubs


if __name__ == "__main__":
    unittest.main()
