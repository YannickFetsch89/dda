"""
Tests für scraper/orte/spielstaetten_import.py (Plan docs/plan-locations-2026-11-18.md, Schritt 2, Pflicht-Tests
„Import“ in Abschnitt 4).
"""
import unittest
from collections import Counter

from scraper.orte.spielstaetten_import import event_orte_zuordnen, seitenname, sql_text, zeilen_pruefen


def _z(haus, typ="haus", gehoert_zu="", entscheidung="ja", art="Kino", slug=None, name=""):
    return {"haus": haus, "zeile_typ": typ, "gehoert_zu": gehoert_zu, "entscheidung": entscheidung,
            "art_korrigiert": art, "slug_vorschlag": slug if slug is not None else haus.lower().replace(" ", "-"),
            "name_korrigiert": name, "bemerkung_auftraggeber": ""}


def _n(alle=3):
    return {"alle": alle, "kommend": 0, "roh": Counter(), "adresse": Counter(), "stadtteil": Counter(),
            "quelle": Counter()}


class TestImport(unittest.TestCase):
    def test_ablehnungen(self):
        zeilen = [_z("Bambi"), _z("Leer", entscheidung=""), _z("Ohne Art", art=""), _z("Sonst", art="Sonstiges"),
                  _z("Doppelt", slug="vergeben"), _z("Weiter", slug="alt-slug"),
                  _z("Halle", "saal", "Unbekanntes Haus", art="")]
        ok, abgelehnt = zeilen_pruefen(zeilen, {"vergeben"}, {"alt-slug"}, {})
        self.assertEqual([z["haus"] for z in ok], ["Bambi"])
        self.assertEqual(len(abgelehnt), 5)  # leere Entscheidung wird nicht importiert und nicht gemeldet
        self.assertTrue(any("ort_weiterleitungen" in a for a in abgelehnt))
        self.assertTrue(any("parent_id" in a for a in abgelehnt))

    def test_zweiter_lauf_ueberspringt_importierte(self):
        # Schon importierte Spielstätten (Slug vorhanden) werden still übersprungen, nicht als Kollision abgelehnt
        zeilen = [_z("Bambi", slug="bambi"), _z("Neu", slug="neu"), _z("Saal", "saal", "Bambi", art="", slug="bambi-saal")]
        ok, abgelehnt = zeilen_pruefen(zeilen, {"bambi"}, set(), {}, frozenset({"bambi"}))
        self.assertEqual([z["haus"] for z in ok], ["Neu", "Saal"])
        self.assertEqual(abgelehnt, [])
        self.assertEqual(ok[1]["_eltern_slug"], "bambi")

    def test_saal_eines_guide_hauses_und_art_erben(self):
        ok, abgelehnt = zeilen_pruefen([_z("Halle", "saal", "zakk", art="", slug="zakk-flingern-halle")],
                                       set(), set(), {"zakk": "zakk-flingern"})
        self.assertEqual(abgelehnt, [])
        self.assertEqual(ok[0]["_eltern_slug"], "zakk-flingern")
        self.assertEqual(ok[0]["_name"], "zakk – Halle")

    def test_seitenname(self):
        self.assertEqual(seitenname(_z("Central 1", "saal", "D’haus Central")), "D’haus Central 1")
        self.assertEqual(seitenname(_z("Bambi", name="Bambi Filmtheater")), "Bambi Filmtheater")

    def test_event_orte_ohne_saele_und_nicht_im(self):
        namen = {"Tonhalle Düsseldorf": _n(), "Tonhalle Mendelssohn-Saal": _n(), "Tonhalle Düsseldorf – Rotunde": _n(),
                 "zakk – Halle": _n(), "zakk": _n(), "zakk – nicht im zakk": _n()}
        freigegeben = [_z("Tonhalle Düsseldorf", slug="tonhalle"),
                       _z("Mendelssohn-Saal", "saal", "Tonhalle Düsseldorf", slug="tonhalle-mendelssohn-saal"),
                       _z("Halle", "saal", "zakk", slug="zakk-flingern-halle")]
        eo = event_orte_zuordnen(namen, freigegeben)
        self.assertEqual(eo["tonhalle-mendelssohn-saal"], ["Tonhalle Mendelssohn-Saal"])
        self.assertIn("Tonhalle Düsseldorf – Rotunde", eo["tonhalle"])  # Saal ohne eigene Zeile → Haus
        self.assertEqual(eo["zakk-flingern-halle"], ["zakk – Halle"])
        self.assertFalse(any("nicht im" in n for liste in eo.values() for n in liste))

    def test_sql_aktiv_und_parent(self):
        ok, _ = zeilen_pruefen([_z("Haus", slug="haus"), _z("Saal", "saal", "Haus", art="", slug="haus-saal")],
                               set(), set(), {})
        text = sql_text(ok, {"haus": ["Haus"]}, [])
        self.assertIn("'spielstaette', true, NULL", text)
        self.assertIn("(SELECT id FROM public.orte WHERE slug = 'haus')", text)
        self.assertLess(text.index("'haus', 'spielstaette'"), text.index("'haus-saal'"))  # Haus vor Saal


if __name__ == "__main__":
    unittest.main()
