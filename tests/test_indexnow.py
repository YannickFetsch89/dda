"""Tests für die IndexNow-Meldung (python -m unittest tests.test_indexnow)."""
import unittest
from datetime import date

from pipeline.indexnow import SITE_URL, urls_bauen


class UrlsTest(unittest.TestCase):
    HEUTE = date(2026, 11, 11)

    def test_nur_kommende_mit_slug_und_tagesseiten(self):
        urls = urls_bauen([
            {"kategorie": "musik", "slug": "konzert-2026-11-12", "datum": "2026-11-12", "datum_bis": None},
            {"kategorie": "kultur", "slug": "ausstellung", "datum": "2026-11-01", "datum_bis": "2026-11-13"},
            {"kategorie": "musik", "slug": "vorbei", "datum": "2026-11-01", "datum_bis": None},
            {"kategorie": "musik", "slug": None, "datum": "2026-11-12", "datum_bis": None},
            {"kategorie": "musik", "slug": "weit-weg", "datum": "2026-12-31", "datum_bis": None},
        ], self.HEUTE)
        self.assertEqual(urls[:2], [f"{SITE_URL}/heute", f"{SITE_URL}/"])
        self.assertIn(f"{SITE_URL}/event/musik/konzert-2026-11-12", urls)
        self.assertIn(f"{SITE_URL}/event/kultur/ausstellung", urls)
        self.assertNotIn(f"{SITE_URL}/event/musik/vorbei", urls)
        # Laufende Ausstellung: heute bis Ende – nicht die vergangenen Tage
        for tag in ("2026-11-11", "2026-11-12", "2026-11-13"):
            self.assertIn(f"{SITE_URL}/tag/{tag}", urls)
        self.assertNotIn(f"{SITE_URL}/tag/2026-11-01", urls)
        # Tagesseiten nur im Sitemap-Fenster (14 Tage)
        self.assertNotIn(f"{SITE_URL}/tag/2026-12-31", urls)
        self.assertIn(f"{SITE_URL}/event/musik/weit-weg", urls)
        self.assertEqual(len(urls), len(set(urls)))


if __name__ == "__main__":
    unittest.main()
