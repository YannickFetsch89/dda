"""
Tests zur Ortszuordnung events.ort_id und zur Dubletten-Regel nach Häusern
(Plan docs/plan-locations-2026-11-18.md, Abschnitt 3.4 und Pflicht-Tests in Abschnitt 4).
"""
import unittest

from database.client import _anreicherungs_update_bauen
from pipeline.deduplication import _events_mergen, _ort_passt
from pipeline.ort_zuordnung import (
    OrteIndex,
    adresse_passt,
    annotieren,
    ausgeschlossen,
    nachtrag_aenderungen,
    nicht_im_ort,
    ort_zuordnen,
)
from scraper.orte.clubs_profil import event_orte, event_orte_vereinigen
from scraper.tier2.schauspielhaus import ADRESSE_CENTRAL, ADRESSE_STANDARD, adresse_fuer

ZAKK, HALLE, STUDIO, PITCHER, STARBUCKS, KOE, ALT = "id-zakk", "id-halle", "id-studio", "id-pitcher", "id-sb", "id-koe", "id-alt"


def _index() -> OrteIndex:
    return OrteIndex.aus_zeilen([
        {"id": ZAKK, "name": "zakk", "slug": "zakk-flingern", "typ": "club", "aktiv": True,
         "extras": {"club": {"event_orte": ["zakk", "zakk – Kneipe", "zakk – nicht im zakk"]}}},
        {"id": HALLE, "name": "Halle", "slug": "zakk-flingern-halle", "typ": "spielstaette", "aktiv": True,
         "parent_id": ZAKK, "extras": {"spielstaette": {"event_orte": ["zakk – Halle"]}}},
        {"id": STUDIO, "name": "Studio", "slug": "zakk-flingern-studio", "typ": "spielstaette", "aktiv": True,
         "parent_id": ZAKK, "extras": {"spielstaette": {"event_orte": ["zakk – Studio"]}}},
        {"id": PITCHER, "name": "Pitcher Rock HQ", "slug": "pitcher", "typ": "club", "aktiv": True,
         "extras": {"club": {"event_orte": ["Pitcher", "Pitcher, nicht im Freien"]}}},
        {"id": STARBUCKS, "name": "Starbucks", "slug": "starbucks", "typ": "cafe", "aktiv": True,
         "adresse": "Steinstr. 1 Düsseldorf", "extras": {}},
        {"id": KOE, "name": "Kö Club", "slug": "koe-club-duesseldorf-friedrichstadt", "typ": "club", "aktiv": True,
         "extras": {"club": {"event_orte": ["Kö Club", "Theater an der Kö"]}}},
        {"id": ALT, "name": "Altes Haus", "slug": "altes-haus", "typ": "spielstaette", "aktiv": False,
         "extras": {"spielstaette": {"event_orte": ["Altes Haus"]}}},
    ])


class TestZuordnung(unittest.TestCase):
    def setUp(self):
        self.idx = _index()

    def test_treffer_ueber_event_orte_und_guide_name(self):
        self.assertEqual(ort_zuordnen({"ort": "zakk – Halle"}, self.idx), (HALLE, "treffer"))
        self.assertEqual(ort_zuordnen({"ort": "zakk"}, self.idx), (ZAKK, "treffer"))
        self.assertEqual(ort_zuordnen({"ort": "Pitcher Rock HQ"}, self.idx), (PITCHER, "treffer"))

    def test_nicht_im_und_ausnahmen(self):
        # „nicht im zakk“ bekommt keine ID, auch wenn es noch in einem gespeicherten event_orte stünde
        self.assertEqual(ort_zuordnen({"ort": "zakk – nicht im zakk"}, self.idx), (None, "kein"))
        self.assertEqual(ort_zuordnen({"ort": "Pitcher, nicht im Freien"}, self.idx), (PITCHER, "treffer"))
        self.assertTrue(nicht_im_ort("zakk – nicht im zakk", ["zakk"]))
        self.assertFalse(nicht_im_ort("Pitcher, nicht im Freien", ["pitcher"]))
        self.assertFalse(nicht_im_ort("nicht im Saal, sondern im Pitcher Club", ["pitcher"]))

    def test_ausschlussliste(self):
        self.assertTrue(ausgeschlossen("koe-club-duesseldorf-friedrichstadt", "Theater an der Kö"))
        self.assertEqual(ort_zuordnen({"ort": "Theater an der Kö"}, self.idx), (None, "kein"))

    def test_kette_nur_mit_passender_adresse(self):
        self.assertEqual(ort_zuordnen({"ort": "Starbucks", "adresse": "Steinstraße 1, 40212 Düsseldorf"}, self.idx),
                         (STARBUCKS, "treffer"))
        self.assertEqual(ort_zuordnen({"ort": "Starbucks", "adresse": "Schadowstraße 84"}, self.idx), (None, "kein"))
        self.assertTrue(adresse_passt("Steinstr. 1 Düsseldorf", "Steinstraße 1, 40212 Düsseldorf"))

    def test_saal_vor_haus(self):
        # „zakk – Halle“ steht auch im event_orte des Clubs: der Saal mit eigener Seite gewinnt
        idx = OrteIndex.aus_zeilen([
            {"id": ZAKK, "name": "zakk", "slug": "zakk-flingern", "typ": "club", "aktiv": True,
             "extras": {"club": {"event_orte": ["zakk", "zakk – Halle"]}}},
            {"id": HALLE, "name": "Halle", "slug": "zakk-flingern-halle", "typ": "spielstaette", "aktiv": True,
             "parent_id": ZAKK, "extras": {"spielstaette": {"event_orte": ["zakk – Halle"]}}},
        ])
        self.assertEqual(ort_zuordnen({"ort": "zakk – Halle"}, idx), (HALLE, "treffer"))

    def test_inaktive_zeile_nie_zugeordnet(self):
        self.assertEqual(ort_zuordnen({"ort": "Altes Haus"}, self.idx), (None, "kein"))

    def test_mehrdeutig(self):
        idx = OrteIndex.aus_zeilen([
            {"id": "a", "name": "Central", "slug": "a", "typ": "kneipe", "aktiv": True, "extras": {}},
            {"id": "b", "name": "Central", "slug": "b", "typ": "club", "aktiv": True, "extras": {}},
        ])
        self.assertEqual(ort_zuordnen({"ort": "Central"}, idx), (None, "mehrdeutig"))

    def test_nachtrag_wiederholbar_und_nie_null(self):
        events = [{"id": "e1", "ort": "zakk – Halle", "ort_id": None},
                  {"id": "e2", "ort": "zakk – Halle", "ort_id": HALLE},          # schon richtig
                  {"id": "e3", "ort": "Unbekannt", "ort_id": ZAKK},              # ohne Treffer: bleibt
                  {"id": "e4", "ort": "zakk – Studio", "ort_id": ZAKK}]          # Saal hat jetzt eine Seite
        aenderungen = nachtrag_aenderungen(events, self.idx)
        self.assertEqual(aenderungen, {HALLE: ["e1"], STUDIO: ["e4"]})
        for e in events:  # nach dem Ausführen: zweiter Lauf ohne Änderung
            for oid, ids in aenderungen.items():
                if e["id"] in ids:
                    e["ort_id"] = oid
        self.assertEqual(nachtrag_aenderungen(events, self.idx), {})


class TestDublettenRegel(unittest.TestCase):
    def setUp(self):
        self.idx = _index()

    def _e(self, ort, ort_id=None, adresse=None):
        return annotieren({"ort": ort, "ort_id": ort_id, "adresse": adresse}, self.idx)

    def test_zakk_saele_desselben_hauses_ueber_namen(self):
        a = self._e("zakk – Studio", STUDIO)
        b = self._e("zakk - Zentrum für Aktion, Kultur und Kommunikation", ZAKK)
        self.assertTrue(_ort_passt(a, b))

    def test_verschiedene_haeuser_nicht(self):
        self.assertFalse(_ort_passt(self._e("zakk", ZAKK), self._e("Pitcher", PITCHER)))

    def test_ohne_haus_zuordnung_namensvergleich(self):
        # z. B. rausgegangen_nachziehen.py: keine geladenen Häuser → Namensvergleich wie bisher
        self.assertTrue(_ort_passt({"ort": "zakk – Studio", "ort_id": STUDIO},
                                   {"ort": "zakk - Zentrum für Aktion, Kultur und Kommunikation", "ort_id": ZAKK}))

    def test_kette_nur_mit_adresse(self):
        mit = self._e("Starbucks", STARBUCKS, "Steinstr. 1")
        self.assertFalse(_ort_passt(mit, self._e("Starbucks", None, "Schadowstraße 84")))
        self.assertTrue(_ort_passt(mit, self._e("Starbucks", None, "Steinstraße 1")))

    def test_mergen_behaelt_ort_id(self):
        rausgegangen = {"titel": "X", "ort": "zakk – Halle", "ort_id": HALLE, "quelle_name": "Rausgegangen",
                        "quelle_url": "https://rausgegangen.de/x"}
        veranstalter = {"titel": "X", "ort": "zakk Halle (Ersatz)", "quelle_name": "zakk", "quelle_url": "https://zakk.de/x"}
        self.assertEqual(_events_mergen(rausgegangen, veranstalter)["ort_id"], HALLE)

    def test_bestand_nur_ergaenzen(self):
        self.assertEqual(_anreicherungs_update_bauen({"ort_id": None}, {"ort_id": HALLE}).get("ort_id"), HALLE)
        self.assertNotIn("ort_id", _anreicherungs_update_bauen({"ort_id": ZAKK}, {"ort_id": HALLE}))
        self.assertNotIn("ort_id", _anreicherungs_update_bauen({"ort_id": ZAKK}, {"ort_id": None}))


class TestClubsProfil(unittest.TestCase):
    def test_event_orte_waechst_nur(self):
        ort = {"name": "zakk", "slug": "zakk-flingern",
               "extras": {"club": {"event_orte": ["zakk", "zakk – Kneipe", "zakk – nicht im zakk"]}}}
        # „zakk – Kneipe“ hatte 180 Tage kein Event, bleibt trotzdem; „nicht im zakk“ fällt heraus
        self.assertEqual(event_orte_vereinigen(ort, ["zakk", "zakk – Halle"]), ["zakk", "zakk – Halle", "zakk – Kneipe"])

    def test_ausschluss_und_nicht_im_in_event_orte(self):
        alle = {"Kö Club", "Theater an der Kö", "zakk – nicht im zakk"}
        self.assertNotIn("Theater an der Kö", event_orte("Kö Club", alle, "koe-club-duesseldorf-friedrichstadt"))
        # Fund 20.11.2026: fremde Orte an der Kö gehören nicht zum Kö-Club
        fremd = {"KÖ Galerie Düsseldorf", "Kö on Ice", "Winterwelt Kö-on-Ice", "Poccino am Kö-Bogen"}
        self.assertFalse(fremd & set(event_orte("Kö Club - Düsseldorf", alle | fremd, "koe-club-duesseldorf-friedrichstadt")))
        ort = {"name": "Kö Club", "slug": "koe-club-duesseldorf-friedrichstadt",
               "extras": {"club": {"event_orte": ["Kö Club", "Theater an der Kö"]}}}
        self.assertNotIn("Theater an der Kö", event_orte_vereinigen(ort, []))


class TestSchauspielhausAdresse(unittest.TestCase):
    def test_central_eigene_adresse(self):
        for ort in ("Central 1", "Central Brücke", "Junges Schauspiel im Central — D’haus"):
            self.assertEqual(adresse_fuer(ort), ADRESSE_CENTRAL)
        self.assertEqual(adresse_fuer("Düsseldorfer Schauspielhaus – Großes Haus"), ADRESSE_STANDARD)


if __name__ == "__main__":
    unittest.main()
