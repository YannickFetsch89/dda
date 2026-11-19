"""Tests für scraper/orte/spielstaetten_geo.py (Plan docs/plan-locations-2026-11-18.md, 3.12, Pflicht-Tests)."""
import unittest

from scraper.orte.spielstaetten_geo import plz_im_gebiet, sql_text, stadt_aus_plz, stadtteil_aus_plz


class TestGeo(unittest.TestCase):
    def test_stadt_und_stadtteil_nur_aus_plz(self):
        self.assertEqual(stadt_aus_plz("Markt 1, 41460 Neuss"), "Neuss")
        self.assertEqual(stadtteil_aus_plz("Markt 1, 41460 Neuss"), "")          # Neuss ohne Stadtteil
        self.assertEqual(stadt_aus_plz("Worringer Straße 140, 40210 Düsseldorf"), "Düsseldorf")
        self.assertEqual(stadtteil_aus_plz("Worringer Straße 140, 40210 Düsseldorf"), "Stadtmitte")
        self.assertFalse(plz_im_gebiet("Steinstr. 1, Düsseldorf"))               # ohne PLZ keine Koordinaten

    def test_sql_ohne_plz_keine_koordinaten_und_nur_bestaetigt(self):
        zeilen = [
            {"slug": "a", "adresse_bestaetigt": "Worringer Straße 140, 40210 Düsseldorf", "bestaetigung": "ja",
             "osm_lat": "51.22", "osm_lon": "6.79", "place_id": "ChIJ1"},
            {"slug": "b", "adresse_bestaetigt": "Steinstr. 1, Düsseldorf", "bestaetigung": "ja",
             "osm_lat": "51.1", "osm_lon": "6.7", "place_id": ""},
            {"slug": "c", "adresse_bestaetigt": "X 1, 40210 Düsseldorf", "bestaetigung": "", "osm_lat": "1"},
        ]
        text = sql_text(zeilen)
        self.assertIn("latitude = 51.22", text)
        zeile_b = next(z for z in text.splitlines() if "slug = 'b'" in z)
        self.assertIn("latitude = NULL", zeile_b)
        self.assertNotIn("slug = 'c'", text)
        self.assertIn("'Stadtmitte'", text)


if __name__ == "__main__":
    unittest.main()
