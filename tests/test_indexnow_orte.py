"""IndexNow für Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.11, Pflicht-Tests)."""
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from pipeline.indexnow import ort_indexierbar, ortsseiten_melden_an, ortsseiten_urls


class OrtIndexierbarTest(unittest.TestCase):
    def test_gemeinsame_faelle_wie_typescript(self):
        faelle = json.loads((Path(__file__).parent / "fixtures" / "ort_indexierbar.json").read_text(encoding="utf-8"))
        for f in faelle:
            with self.subTest(f=f):
                self.assertEqual(ort_indexierbar(f["adresseBestaetigt"], f["textFreigegeben"], f["kommende"]), f["erwartet"])

    def test_schalter(self):
        with mock.patch.dict(os.environ, {"ORTSSEITEN_MELDEN": "0"}):
            self.assertFalse(ortsseiten_melden_an())
        with mock.patch.dict(os.environ, {"ORTSSEITEN_MELDEN": "1"}):
            self.assertTrue(ortsseiten_melden_an())


class OrtsseitenUrlsTest(unittest.TestCase):
    ORTE = {
        "haus": {"slug": "tonhalle", "typ": "spielstaette", "aktiv": True, "spielstaette": {"adresse_bestaetigt": {"datum": "x"}}},
        "saal": {"slug": "tonhalle-mendelssohn-saal", "typ": "spielstaette", "aktiv": True, "parent_id": "haus", "spielstaette": {}},
        "zakk": {"slug": "zakk-flingern", "typ": "club", "aktiv": True, "adresse": "Fichtenstraße 40, 40233 Düsseldorf"},
        "halle": {"slug": "zakk-flingern-halle", "typ": "spielstaette", "aktiv": True, "parent_id": "zakk", "spielstaette": {}},
        "ohne": {"slug": "ohne-adresse", "typ": "spielstaette", "aktiv": True, "spielstaette": {}},
    }

    def test_saal_meldet_saal_und_haus(self):
        self.assertEqual(ortsseiten_urls({"saal"}, self.ORTE),
                         ["https://diesdas.events/orte/tonhalle-mendelssohn-saal", "https://diesdas.events/orte/tonhalle"])

    def test_guide_haus_nur_saalseite(self):
        urls = ortsseiten_urls({"halle"}, self.ORTE)
        self.assertEqual(urls, ["https://diesdas.events/orte/zakk-flingern-halle"])
        self.assertFalse(any("/guides/" in u or u.endswith("/orte/zakk-flingern") for u in urls))

    def test_noindex_nicht_melden(self):
        self.assertEqual(ortsseiten_urls({"ohne", "zakk"}, self.ORTE), [])


if __name__ == "__main__":
    unittest.main()
