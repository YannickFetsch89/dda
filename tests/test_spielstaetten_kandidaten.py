"""
Tests für scraper/orte/spielstaetten_kandidaten.py – Schritt 1 des Plans docs/plan-locations-2026-11-18.md
(Abschnitt 7.2, Punkte 1–21, und Pflicht-Test „Kandidatenliste“ in Abschnitt 4).
"""
import csv
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scraper.orte.spielstaetten_kandidaten import (
    art_vorschlag,
    entscheidungen_lesen,
    entscheidungen_uebernehmen,
    haus_und_saal,
    klasse,
    nicht_im,
    zeilen_bauen,
    zeilen_schluessel,
)


def _n(alle: int, kommend: int = 0, adresse: str = "", quelle: str = "Rausgegangen") -> dict:
    return {"alle": alle, "kommend": kommend, "roh": Counter(), "adresse": Counter({adresse: alle} if adresse else {}),
            "stadtteil": Counter(), "quelle": Counter({quelle: alle})}


def _bauen(namen: dict, guide=None, slugs=None, vergeben=frozenset()) -> list[dict]:
    for name, n in namen.items():
        n["roh"][name] += n["alle"]
    return zeilen_bauen(namen, guide or {}, slugs or {}, set(vergeben))


def _zeile(zeilen: list[dict], haus: str, gehoert_zu: str = "") -> dict:
    return next(z for z in zeilen if z["haus"] == haus and z["gehoert_zu"] == gehoert_zu)


class TestKlasse(unittest.TestCase):
    def test_strasse_und_ortswort_nur_am_wortende(self):
        # Punkt 1: „saal“ in „Hansaallee“ ist kein Ortswort; Punkt 17: das Interimmuseum bleibt ein Ort
        self.assertEqual(klasse("Hansaallee 190"), "treffpunkt")
        self.assertEqual(klasse("Interimmuseum Hansaallee 190"), "ort")
        self.assertEqual(klasse("Theater an der Luegallee"), "ort")

    def test_platz_vor_stadtname_und_tourist_information(self):
        self.assertEqual(klasse("Marktplatz Düsseldorf"), "treffpunkt")                     # Punkt 2
        self.assertEqual(klasse("Tourist-Information - Visit Düsseldorf"), "treffpunkt")    # Punkt 3

    def test_turnhalle_und_alter_bahnhof_sind_orte(self):
        self.assertEqual(klasse("Franklinstraße Turnhalle"), "ort")                         # Punkt 5
        self.assertEqual(klasse("Alter Bahnhof Oberkassel"), "ort")                          # Punkt 15

    def test_nicht_im_wie_event_orte(self):
        self.assertTrue(nicht_im("zakk – nicht im zakk"))
        self.assertFalse(nicht_im("Pitcher, nicht im Freien"))
        self.assertFalse(nicht_im("nicht im Saal, sondern im Pitcher Club"))


class TestArt(unittest.TestCase):
    def test_arten_aus_7_2(self):
        erwartet = {
            "S- und U-Bahnhof Flingern": "Sonstiges",                 # Punkt 4: kein „flin“ in „Flingern“
            "Kloster Flingern": "Kirche/Gemeinde",                    # Punkt 16
            "Franklinstraße Turnhalle": "Kurs/Studio/Sport",          # Punkt 5
            "Xafe in KAP 1 Zentralbibliothek": "Café/Restaurant",     # Punkt 12
            "Rathaus Düsseldorf": "Öffentliches Gebäude",             # Punkt 18
            "Pfarrzentrum Heerdt": "Kirche/Gemeinde",
            "Billardzentrum": "Kurs/Studio/Sport",
            "Kulturhaus Süd / Freizeitstätte Garath": "Kultur-/Bürgerzentrum",
            "Klanghaus": "Kultur-/Bürgerzentrum",
            "Gerhart Hauptmann Haus": "Kultur-/Bürgerzentrum",
            "EKŌ-Haus der Japanischen Kultur": "Kultur-/Bürgerzentrum",
            "Heine Haus Literaturhaus Düsseldorf": "Kultur-/Bürgerzentrum",
            "ASG-Bildungsforum Düsseldorf": "Bibliothek/Bildung",
            "Rigpa Zentrum Düsseldorf": "Kirche/Gemeinde",
        }
        for name, art in erwartet.items():
            with self.subTest(name=name):
                self.assertEqual(art_vorschlag(name)[0], art)

    def test_pruefhinweis_bei_unsicherer_art(self):
        self.assertIn("prüfen", art_vorschlag("Haus Spilles")[1])
        self.assertIn("Abschnitt 9", art_vorschlag("Alter Bahnhof Oberkassel")[1])


class TestHaeuser(unittest.TestCase):
    def test_dubletten(self):
        for name in ("Holo Cafe", "Holocafe Düsseldorf", "Holocafe Immermannstraße 7"):
            self.assertEqual(haus_und_saal(name, set())[0], "Holocafe")
        self.assertEqual(haus_und_saal("Holocafé Düsseldorf", set())[0], "Holocafé am Wehrhahn")
        self.assertEqual(haus_und_saal("La Pailette Bar", set())[0], "La Paillette")

    def test_saalliste_und_schein_saele(self):
        zeilen = _bauen({
            "zakk": _n(50), "zakk – Halle": _n(30), "zakk – Tanzraum": _n(5), "zakk – nicht im zakk": _n(43),
            "FFT Düsseldorf – Bühne I": _n(19), "FFT Düsseldorf – Bühne II": _n(22),
            "PubCrawl Düsseldorf": _n(2), "PubCrawl Düsseldorf - das Original! seit 2008!": _n(2),
        }, guide={"zakk": "Guide (club): zakk-flingern"}, slugs={"zakk": "zakk-flingern"})
        halle = _zeile(zeilen, "Halle", "zakk")
        self.assertEqual(halle["zeile_typ"], "saal")
        self.assertEqual(halle["slug_vorschlag"], "zakk-flingern-halle")        # gespeicherter Haus-Slug + Saal
        self.assertIn("eigene Seite empfohlen", halle["hinweis"])
        self.assertNotIn("eigene Seite empfohlen", _zeile(zeilen, "Tanzraum", "zakk")["hinweis"])
        # Punkt 19: Bühne I unter der Hinweisgrenze bekommt trotzdem eine Zeile
        self.assertEqual(_zeile(zeilen, "Bühne I", "FFT Düsseldorf")["events_12m_und_kommend"], 19)
        # „nicht im zakk“: keine Saalzeile, nicht mitgezählt
        zakk = _zeile(zeilen, "zakk")
        self.assertEqual(zakk["events_12m_und_kommend"], 85)
        self.assertIn("nicht mitgezählt", zakk["hinweis"])
        self.assertFalse(any(z["gehoert_zu"] == "zakk" and "nicht im" in z["haus"] for z in zeilen))
        # Punkt 21: PubCrawl-Teil ist kein Saal
        self.assertFalse(any(z["gehoert_zu"] == "PubCrawl Düsseldorf" for z in zeilen))

    def test_standorte_kap1_ketten_guides(self):
        zeilen = _bauen({
            "K20 Grabbeplatz / Kunstsammlung NRW": _n(27), "K21 / Kunstsammlung NRW": _n(33),
            "Stadtbüchereien Düsseldorf": _n(300), "Zentralbibliothek KAP1": _n(29),
            "Starbucks": _n(5), "Starbucks Reserve": _n(5), "Starbucks Schadowstr": _n(2),
            "CADO Kaffeebar": _n(2), "Theater an der Kö": _n(5),
        }, guide={"starbucks": "in orte, unsichtbar (cafe)", "cado kaffeebar": "in orte, unsichtbar (cafe)",
                  "theater an der koe": "Club: koe-club"})
        self.assertEqual(_zeile(zeilen, "K20 Grabbeplatz", "Kunstsammlung NRW")["zeile_typ"], "standort")
        self.assertEqual(_zeile(zeilen, "K21 Ständehaus", "Kunstsammlung NRW")["zeile_typ"], "standort")
        self.assertEqual(_zeile(zeilen, "Stadtbüchereien Düsseldorf")["vorschlag"], "keine Seite (Büchereinetz)")
        self.assertEqual(_zeile(zeilen, "Zentralbibliothek KAP1", "Stadtbüchereien Düsseldorf")["zeile_typ"], "filiale")
        for kette in ("Starbucks", "Starbucks Reserve", "Starbucks Schadowstr"):
            self.assertEqual(_zeile(zeilen, kette)["vorschlag"], "keine Seite (Kette)")
        self.assertEqual(_zeile(zeilen, "CADO Kaffeebar")["vorschlag"], "keine Seite (Guide unsichtbar)")
        self.assertEqual(_zeile(zeilen, "Theater an der Kö")["vorschlag"], "offen: Abschnitt 9")

    def test_dhaus_central_eigenes_haus(self):
        # Entscheidung 19.11.2026: Central (Worringer Straße 140) ist eigenes Haus mit drei Sälen
        zeilen = _bauen({"Central 1": _n(46), "Central 2": _n(41), "Central Brücke": _n(31), "Central": _n(8),
                         "D'haus im Central": _n(5), "Düsseldorfer Schauspielhaus – Großes Haus": _n(85)})
        self.assertEqual(_zeile(zeilen, "D’haus Central")["slug_vorschlag"], "dhaus-central")
        self.assertEqual(_zeile(zeilen, "Central 1", "D’haus Central")["slug_vorschlag"], "dhaus-central-1")
        self.assertEqual(_zeile(zeilen, "Central Brücke", "D’haus Central")["slug_vorschlag"], "dhaus-central-bruecke")
        self.assertFalse(any(z["gehoert_zu"] == "Düsseldorfer Schauspielhaus" and "Central" in z["haus"] for z in zeilen))
        self.assertNotIn("Saal?", _zeile(zeilen, "D’haus Central")["hinweis"])

    def test_entscheidungen_abschnitt_9(self):
        zeilen = _bauen({"Stone im Ratinger Hof": _n(6), "Bilker Bunker": _n(12), "Theater an der Kö": _n(5)})
        self.assertEqual(_zeile(zeilen, "Stone im Ratinger Hof")["vorschlag"], "keine Seite (geschlossen)")
        self.assertEqual(_zeile(zeilen, "Bilker Bunker")["vorschlag"], "neue Ortsseite")
        self.assertEqual(_zeile(zeilen, "Theater an der Kö")["vorschlag"], "offen: Abschnitt 9")

    def test_slug_kollision_ist_hinweis(self):
        # Gleicher Slug heißt nicht gleicher Ort (Plan 3.3 Punkt 7): nur Hinweis, der Auftraggeber entscheidet
        zeilen = _bauen({"Bilker Häzz": _n(3)}, vergeben={"bilker-haezz"})
        self.assertIn("Slug-Kollision", _zeile(zeilen, "Bilker Häzz")["hinweis"])


class TestEntscheidungen(unittest.TestCase):
    def _alt(self, zeilen: list[dict]) -> Path:
        pfad = Path(tempfile.mkdtemp()) / "alt.csv"
        with pfad.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["haus", "entscheidung", "name_korrigiert", "art_korrigiert",
                                              "bemerkung_auftraggeber"], delimiter=";")
            w.writeheader()
            w.writerows(zeilen)
        return pfad

    def test_entscheidung_wandert_auf_zusammengefuehrte_zeile(self):
        alt = entscheidungen_lesen(self._alt([{"haus": "Holo Cafe", "entscheidung": "ja", "art_korrigiert": "Café"}]))
        zeilen = _bauen({"Holo Cafe": _n(4), "Holocafe Düsseldorf": _n(4)})
        self.assertEqual(entscheidungen_uebernehmen(zeilen, alt), 1)
        self.assertEqual(_zeile(zeilen, "Holocafe")["entscheidung"], "ja")

    def test_widerspruch_ergibt_hinweis(self):
        alt = entscheidungen_lesen(self._alt([{"haus": "Holo Cafe", "entscheidung": "ja"},
                                              {"haus": "Holocafe Düsseldorf", "entscheidung": "nein"}]))
        zeilen = _bauen({"Holo Cafe": _n(4), "Holocafe Düsseldorf": _n(4)})
        entscheidungen_uebernehmen(zeilen, alt)
        holo = _zeile(zeilen, "Holocafe")
        self.assertEqual(holo["entscheidung"], "")
        self.assertIn("Entscheidung prüfen", holo["hinweis"])

    def test_schluessel_trennt_saal_und_haus(self):
        self.assertNotEqual(zeilen_schluessel("Halle", "zakk"), zeilen_schluessel("Halle"))


if __name__ == "__main__":
    unittest.main()
