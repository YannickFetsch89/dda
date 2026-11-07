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
    def test_live_brauhaus_bleibt_restaurant(self):
        typ, extras = aenderung(restaurant(qualitaets_score=8), BRAUHAUS_PLACE)
        self.assertEqual(typ, "restaurant")
        self.assertTrue(extras["auch_kneipe"])
        self.assertTrue(extras["war_live"])

    def test_nie_live_wird_kneipe(self):
        typ, extras = aenderung(restaurant(), BRAUHAUS_PLACE)
        self.assertEqual(typ, "kneipe")
        self.assertTrue(extras["auch_restaurant"])
        self.assertEqual(extras["unterart"], "brauhaus")

    def test_zweiter_lauf_aendert_nichts(self):
        typ, extras = aenderung(restaurant(), BRAUHAUS_PLACE)
        typ2, extras2 = aenderung(restaurant(typ=typ, extras=extras), BRAUHAUS_PLACE)
        self.assertEqual((typ2, extras2), (typ, extras))
        live_typ, live_extras = aenderung(restaurant(qualitaets_score=8), BRAUHAUS_PLACE)
        self.assertEqual(aenderung(restaurant(qualitaets_score=8, extras=live_extras), BRAUHAUS_PLACE),
                         (live_typ, live_extras))

    def test_frueher_live_wird_nicht_umgetypt(self):
        # War live (war_live gemerkt), ist jetzt deaktiviert → Restaurant-URL bleibt
        typ, _ = aenderung(restaurant(aktiv=False, extras={"war_live": True, "auch_kneipe": True}), BRAUHAUS_PLACE)
        self.assertEqual(typ, "restaurant")
        # Auch ohne war_live: schon als auch_kneipe verarbeitet → nicht nachträglich umtypen
        typ, _ = aenderung(restaurant(aktiv=False, extras={"auch_kneipe": True}), BRAUHAUS_PLACE)
        self.assertEqual(typ, "restaurant")

    def test_neuer_gastropub_auch_im_restaurant_hub(self):
        kneipe = {"id": "o2", "name": "The Pub", "typ": "kneipe", "aktiv": True, "qualitaets_score": 8,
                  "google_place_id": "p2", "extras": {"google_primaertyp": "gastropub"}}
        _, extras = aenderung(kneipe, {"id": "p2", "primaryType": "gastropub", "types": ["gastropub", "bar"]})
        self.assertTrue(extras["auch_restaurant"])
        self.assertNotEqual(extras.get("unterart"), "brauhaus")


if __name__ == "__main__":
    unittest.main()
