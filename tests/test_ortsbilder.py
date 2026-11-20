"""Tests: Bilder der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.13, Schritt 4)."""
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scraper.orte import ortsbilder

GUT = {"slug": "tonhalle", "bild_url": "https://www.tonhalle.test/bild.jpg", "seite_url": "https://www.tonhalle.test/",
       "nachweis": "Tonhalle Düsseldorf", "lizenz": "", "link": "https://www.tonhalle.test/", "version": "", "fokus": ""}


class PruefenTest(unittest.TestCase):
    def test_gueltig(self):
        self.assertEqual(ortsbilder.pruefen(GUT), [])

    def test_portal_google_und_wikimedia_ohne_lizenz(self):
        self.assertIn("Portal- oder Google-Bild", ortsbilder.pruefen({**GUT, "bild_url": "https://lh3.googleusercontent.com/x"}))
        self.assertIn("Portal- oder Google-Bild", ortsbilder.pruefen({**GUT, "seite_url": "https://www.eventim.de/x"}))
        self.assertIn("Wikimedia ohne Lizenz", ortsbilder.pruefen({**GUT, "bild_url": "https://upload.wikimedia.org/a.jpg"}))
        self.assertIn("Nachweis fehlt", ortsbilder.pruefen({**GUT, "nachweis": ""}))


class UmwandelnTest(unittest.TestCase):
    def test_webp_ohne_exif_und_verkleinert(self):
        from PIL import Image
        roh = Image.new("RGB", (2400, 1200), "red")
        exif = Image.Exif()
        exif[0x010F] = "Kamera"  # Hersteller
        puffer = io.BytesIO()
        roh.save(puffer, "JPEG", exif=exif)
        with tempfile.TemporaryDirectory() as d:
            ziel = Path(d) / "x.webp"
            breite, _ = ortsbilder.umwandeln(puffer.getvalue(), ziel)
            self.assertEqual(breite, ortsbilder.MAX_BREITE)
            with Image.open(ziel) as fertig:
                self.assertEqual(fertig.format, "WEBP")
                self.assertFalse(fertig.getexif())


class SqlTest(unittest.TestCase):
    def test_nur_mit_datei_und_nachweis_mit_lizenz(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(ortsbilder, "ZIEL", Path(d)):
            (Path(d) / "tonhalle.webp").write_bytes(b"x")
            wiki = {**GUT, "slug": "k20", "bild_url": "https://upload.wikimedia.org/k20.jpg", "nachweis": "Foto A",
                    "lizenz": "CC BY-SA 4.0"}
            (Path(d) / "k20.webp").write_bytes(b"x")
            ohne = {**GUT, "slug": "ohne-datei"}
            sql, n = ortsbilder.sql_bauen([GUT, wiki, ohne], "2026-11-20")
        self.assertEqual(n, 2)
        self.assertIn("bild_url = '/ort-bilder/orte/tonhalle.webp'", sql)
        self.assertIn("bild_attribution = 'Foto A (CC BY-SA 4.0)'", sql)
        self.assertIn('"erlaubnis": "nachtraeglich"', sql)
        self.assertNotIn("ohne-datei", sql)


if __name__ == "__main__":
    unittest.main()
