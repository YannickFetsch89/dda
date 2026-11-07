"""Tests für E1 – Brauhäuser/Gastropubs in beiden Guides mit EINER URL (python -m unittest tests.test_bars_e1)."""
import unittest

from scraper.orte.bars_e1 import aenderung

BRAUHAUS_PLACE = {"id": "p1", "primaryType": "brewery", "types": ["brewery", "restaurant"],
                  "displayName": {"text": "Brauhaus Test"}}


def restaurant(**teile) -> dict:
    basis = {"id": "o1", "name": "Brauhaus Test", "typ": "restaurant", "aktiv": True, "qualitaets_score": 5,
             "google_place_id": "p1", "extras": {}}
    return {**basis, **teile}


class E1Test(unittest.TestCase):
    def test_restaurant_brauhaus_wird_nur_markiert(self):
        # Ob live, nie live oder früher live ohne Merker: die Restaurant-URL bleibt immer
        for o in (restaurant(qualitaets_score=8), restaurant(), restaurant(aktiv=False, qualitaets_score=8)):
            extras = aenderung(o, BRAUHAUS_PLACE)
            self.assertTrue(extras["auch_kneipe"])
            self.assertEqual(extras["unterart"], "brauhaus")
            self.assertNotIn("auch_restaurant", extras)

    def test_zweiter_lauf_aendert_nichts(self):
        extras = aenderung(restaurant(), BRAUHAUS_PLACE)
        self.assertEqual(aenderung(restaurant(extras=extras), BRAUHAUS_PLACE), extras)

    def test_ki_unterart_bleibt(self):
        gastropub = {"id": "p3", "primaryType": "gastropub", "types": ["gastropub", "bar"]}
        o = restaurant(name="Zum Anker", google_place_id="p3", extras={"unterart": "bar"})
        self.assertEqual(aenderung(o, gastropub)["unterart"], "bar")
        # ohne vorhandene Unterart setzt die Regel eine
        self.assertEqual(aenderung(restaurant(name="Zum Anker", google_place_id="p3"), gastropub)["unterart"], "kneipe")

    def test_neuer_gastropub_auch_im_restaurant_hub(self):
        kneipe = {"id": "o2", "name": "The Pub", "typ": "kneipe", "aktiv": True, "qualitaets_score": 8,
                  "google_place_id": "p2", "extras": {"google_primaertyp": "gastropub"}}
        extras = aenderung(kneipe, {"id": "p2", "primaryType": "gastropub", "types": ["gastropub", "bar"]})
        self.assertTrue(extras["auch_restaurant"])
        self.assertNotEqual(extras.get("unterart"), "brauhaus")

    def test_kneipen_brauhaus(self):
        kneipe = {"id": "o4", "name": "Brauerei im Füchschen", "typ": "kneipe", "aktiv": True, "qualitaets_score": 5,
                  "google_place_id": "p4", "extras": {"google_primaertyp": "brewery"}}
        extras = aenderung(kneipe, {"id": "p4", "primaryType": "brewery", "types": ["brewery"]})
        self.assertTrue(extras["auch_restaurant"])
        self.assertEqual(extras["unterart"], "brauhaus")


if __name__ == "__main__":
    unittest.main()
