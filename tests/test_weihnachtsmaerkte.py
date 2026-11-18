"""Tests für den Weihnachtsmarkt-Guide (python -m unittest tests.test_weihnachtsmaerkte). Plan 7.1."""
import json
import unittest
from datetime import date
from pathlib import Path

from scraper.weihnachtsmaerkte import import_maerkte as im
from scraper.weihnachtsmaerkte import toubiz_lesen as tl
from scraper.weihnachtsmaerkte import zeiten as z

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "weihnachtsmaerkte_oeffnung.json").read_text(encoding="utf-8"))
SQL = (Path(__file__).resolve().parents[1] / "database" / "weihnachtsmaerkte_freischalten.sql").read_text(encoding="utf-8")


class ParserTest(unittest.TestCase):
    def test_kurzschrift_hin_und_zurueck(self):
        text = "Mo-Do,So 11:00-20:00; Fr-Sa 11:00-21:00"
        gelesen = z.zeiten_lesen(text)
        self.assertEqual(gelesen[0]["tage"], ["mo", "di", "mi", "do", "so"])
        self.assertEqual(z.kurzschrift(gelesen), text)

    def test_einzeltage_und_leer(self):
        self.assertEqual(z.zeiten_lesen(""), [])
        self.assertEqual(z.zeiten_lesen("Fr 14:00-21:00; Sa 11:00-21:00")[1]["tage"], ["sa"])

    def test_fehler(self):
        for falsch in ("Mo-Do 11-20", "Xy 11:00-20:00", "Mo 20:00-11:00", "Mo 22:00-01:00", "Mo 11:00-20:00; Mo 12:00-13:00", "Do-Mo 11:00-20:00"):
            with self.assertRaises(z.ZeitFehler, msg=falsch):
                z.zeiten_lesen(falsch)

    def test_sonder(self):
        s = z.sonder_lesen("2026-12-24 11:00-15:00; 2026-11-22 zu", "2026-11-19", "2026-12-30")
        self.assertEqual(s[0], {"datum": "2026-11-22", "geschlossen": True})
        with self.assertRaises(z.ZeitFehler):
            z.sonder_lesen("2027-01-02 zu", "2026-11-19", "2026-12-30")  # außerhalb
        with self.assertRaises(z.ZeitFehler):
            z.sonder_lesen("2026-02-30 zu")
        with self.assertRaises(z.ZeitFehler):
            z.sonder_lesen("2026-12-24 zu; 2026-12-24 11:00-15:00")

    def test_zeitraum(self):
        with self.assertRaises(z.ZeitFehler):
            z.zeitraum_pruefen("2026-12-30", "2026-11-19")


class ToubizTest(unittest.TestCase):
    def termine(self):
        # 19.11.–10.12.2026, So–Do 11–20, Fr/Sa 11–21; 22.11. fehlt (Totensonntag), 24.11. mit Sonderzeit
        t = []
        tag = date(2026, 11, 19)
        while tag <= date(2026, 12, 10):
            iso = tag.isoformat()
            if iso != "2026-11-22":
                bis = "21:00" if tag.weekday() in (4, 5) else "20:00"
                t.append({"datum": iso, "von": "11:00", "bis": "16:00" if iso == "2026-11-24" else bis})
            tag = date.fromordinal(tag.toordinal() + 1)
        return t

    def test_ableitung(self):
        a = z.aus_terminen(self.termine())
        self.assertEqual((a["von"], a["bis"]), ("2026-11-19", "2026-12-10"))
        self.assertEqual(z.kurzschrift(a["zeiten"]), "Mo-Do,So 11:00-20:00; Fr-Sa 11:00-21:00")
        self.assertEqual(a["sonder"], [{"datum": "2026-11-24", "von": "11:00", "bis": "16:00"}])

    def test_luecke_ist_nur_hinweis(self):
        a = z.aus_terminen(self.termine())
        self.assertEqual(a["luecken"], ["2026-11-22"])
        self.assertFalse(any(s.get("geschlossen") for s in a["sonder"]))  # nie „zu“

    def test_closed_ist_beleg_fuer_zu(self):
        # Toubiz meldet den 22.11. ausdrücklich als geschlossen → Sonderzeile „zu“, keine Lücke (Plan 3.2, Cursor-Check Stufe 1a)
        a = z.aus_terminen(self.termine() + [{"datum": "2026-11-22", "geschlossen": True}])
        self.assertIn({"datum": "2026-11-22", "geschlossen": True}, a["sonder"])
        self.assertEqual(a["luecken"], [])
        self.assertEqual(z.oeffnung_am({"2026": {**a, "zeiten": a["zeiten"]}}, "2026-11-22")["zustand"], "zu")

    def test_roh_auszug_behaelt_closed(self):
        roh = tl.roh_auszug({"dates": [
            {"date": "2026-11-21", "startAt": "11:00:00", "endAt": "21:00:00", "active": True},
            {"date": "2026-11-22", "closed": True, "active": True},
            {"date": "2026-11-23", "isCancelled": True, "startAt": "11:00:00", "endAt": "20:00:00"},
        ]})
        self.assertEqual(roh["termine"][1], {"datum": "2026-11-22", "geschlossen": True})
        self.assertEqual(len(roh["termine"]), 2)  # abgesagter Termin fällt weg

    def test_nur_wochenende(self):
        a = z.aus_terminen([{"datum": "2026-11-20", "von": "14:00", "bis": "21:00"},
                            {"datum": "2026-11-21", "von": "11:00", "bis": "21:00"},
                            {"datum": "2026-11-28", "von": "11:00", "bis": "21:00"}])
        self.assertEqual(z.kurzschrift(a["zeiten"]), "Fr 14:00-21:00; Sa 11:00-21:00")
        self.assertEqual(a["luecken"], ["2026-11-27"])  # Mo–Do haben keine Zeit → keine Lücke

    def test_json_aus_seite(self):
        seite = """<div data-tb-detail-event='{"name":"Markt &amp; Mehr","dates":[]}'></div>"""
        self.assertEqual(tl.json_aus_seite(seite)["name"], "Markt & Mehr")
        self.assertIsNone(tl.json_aus_seite("<html></html>"))


class OeffnungTest(unittest.TestCase):
    def test_fixture(self):
        for fall in FIXTURE["faelle"]:
            o = z.oeffnung_am(FIXTURE["eintraege"][fall["eintrag"]], fall["datum"])
            with self.subTest(**{k: fall[k] for k in ("eintrag", "datum")}):
                self.assertEqual(o["zustand"], fall["zustand"])
                for k in ("von", "bis", "grund"):
                    if k in fall:
                        self.assertEqual(o.get(k), fall[k])

    def test_totensonntag(self):
        for jahr, erwartet in FIXTURE["totensonntag"].items():
            self.assertEqual(z.totensonntag(int(jahr)).isoformat(), erwartet)


def csv_markt(**kw):
    basis = {"schluessel": "test", "name": "Testmarkt", "stadtteil": "Altstadt", "lat": "51.2261", "lng": "6.7721"}
    return {**basis, **kw}


SAISON_GRUPPE = {"schluessel": "innenstadt", "von": "2026-11-19", "bis": "2026-12-30", "zeiten": "Mo-Do,So 11:00-20:00; Fr-Sa 11:00-21:00",
                 "sonder": "2026-11-22 zu; 2026-12-24 11:00-15:00", "quelle": "toubiz", "beleg": "Zitat", "url": "https://x.test", "stand": "2026-11-17"}


class ImportTest(unittest.TestCase):
    def bilden(self, maerkte, saisons, merkmale=()):
        return im.eintraege_bilden(maerkte, saisons, list(merkmale))

    def test_feldweise_erbung(self):
        maerkte = [csv_markt(schluessel="innenstadt", ist_gruppe="ja"), csv_markt(schluessel="winter-village", gruppe="innenstadt"),
                   csv_markt(schluessel="altstadt-markt", gruppe="innenstadt")]
        saisons = [SAISON_GRUPPE, {"schluessel": "winter-village", "von": "2026-11-20", "quelle": "toubiz", "beleg": "Termine",
                                   "url": "https://y.test", "stand": "2026-11-17"}]
        e, fehler = self.bilden(maerkte, saisons)
        self.assertEqual(fehler, [])
        wv = e["winter-village"]["saison"]
        self.assertEqual(wv["von"], "2026-11-20")  # eigene Zelle gewinnt
        self.assertEqual(wv["bis"], "2026-12-30")
        self.assertEqual(wv["geerbt"], ["bis", "zeiten", "sonder"])
        self.assertEqual(wv["geerbt_von"], "innenstadt")
        self.assertEqual(z.oeffnung_am({"2026": wv}, "2026-11-19")["zustand"], "vor_saison")
        self.assertEqual(z.oeffnung_am({"2026": wv}, "2026-11-22")["zustand"], "zu")
        alt = e["altstadt-markt"]["saison"]  # Zeile fehlt ganz → alles geerbt
        self.assertEqual(alt["geerbt"], ["von", "bis", "zeiten", "sonder"])

    def test_attraktion_erbt_nie(self):
        maerkte = [csv_markt(schluessel="innenstadt", ist_gruppe="ja"), csv_markt(schluessel="rad", gruppe="innenstadt", attraktion="ja")]
        e, _ = self.bilden(maerkte, [SAISON_GRUPPE])
        self.assertIsNone(e["rad"]["saison"])

    def test_ungueltige_zeiten_schreiben_keine_saison(self):
        e, fehler = self.bilden([csv_markt()], [{**SAISON_GRUPPE, "schluessel": "test", "zeiten": "Mo 22:00-01:00"}])
        self.assertIsNone(e["test"]["saison"])
        self.assertTrue(any("nicht geschrieben" in f for f in fehler))

    def test_pflichtfelder(self):
        for falsch in (csv_markt(stadtteil="Kö"), csv_markt(lat="50.9"), csv_markt(art="disco"), csv_markt(ausschliessen="ja"),
                       csv_markt(eintritt="frei"), csv_markt(top5_rang="6"), csv_markt(score_manuell="11")):
            e, fehler = im.markt_pruefen(falsch)
            self.assertIsNone(e)
            self.assertTrue(fehler)
        self.assertIsNotNone(im.markt_pruefen(csv_markt(stadtteil="Neuss", lat="51.198", lng="6.692"))[0])

    def test_merkmale(self):
        zeilen = [{"schluessel": "test", "merkmal": "eisbahn", "wert": "ja", "quelle": "zitat", "beleg": "Eisbahn", "stand": "2026-11-17"},
                  {"schluessel": "test", "merkmal": "glühwein", "wert": "ja", "quelle": "zitat", "beleg": "x", "stand": "2026-11-17"},
                  {"schluessel": "test", "merkmal": "wc", "wert": "ja", "quelle": "zitat", "beleg": "", "stand": "2026-11-17"}]
        mm, fehler = im.merkmale_pruefen(zeilen, {"test"})
        self.assertEqual(list(mm["test"]), ["eisbahn"])
        self.assertEqual(len(fehler), 2)

    def plan(self, bestehend=(), andere=frozenset()):
        e, _ = self.bilden([csv_markt(), csv_markt(schluessel="zwei", name="Testmarkt")], [{**SAISON_GRUPPE, "schluessel": "test"}])
        return im.planen(e, list(bestehend), set(andere))

    def test_slug_kollision_und_neu_inaktiv(self):
        p = self.plan(andere={"testmarkt-altstadt"})
        slugs = sorted(d["spalten"]["slug"] for d in p["neu"])
        self.assertEqual(len(set(slugs)), 2)
        self.assertNotIn("testmarkt-altstadt", slugs)

    def test_slug_fest_ab_freischaltung(self):
        p = self.plan()
        d = next(x for x in p["neu"] if x["schluessel"] == "test")
        zeile = {"id": "1", "slug": "alter-slug", "extras": {"weihnachtsmarkt": {**d["wm"], "freigeschaltet_am": "2026-11-18"}}}
        p2 = self.plan(bestehend=[zeile])
        a = next(x for x in p2["aenderungen"] if x["schluessel"] == "test")
        self.assertEqual(a["spalten"]["slug"], "alter-slug")
        self.assertEqual(a["wm"]["freigeschaltet_am"], "2026-11-18")
        self.assertNotIn("aktiv", a["spalten"])

    def test_keine_google_rohwerte(self):
        p = self.plan()
        text = json.dumps([d["wm"] for d in p["neu"]])
        self.assertNotIn("rating", text.replace("Ratingen", ""))
        self.assertNotIn("userRatingCount", text)

    def test_score_manuell_bleibt_nur_wenn_gesetzt(self):
        e, _ = self.bilden([csv_markt(score_manuell="0")], [])
        self.assertEqual(im.extras_bauen(e["test"], None)["score"], {"manuell": 0.0})
        e2, _ = self.bilden([csv_markt()], [])
        self.assertNotIn("score", im.extras_bauen(e2["test"], {"score": {"manuell": 5}}))


class SqlTest(unittest.TestCase):
    def test_freischalt_sql(self):
        self.assertIn("RETURNING o.slug, o.aktiv", SQL)
        self.assertIn("o.aktiv = false", SQL)
        self.assertIn("o.aktiv = true", SQL)
        self.assertIn("COALESCE", SQL)
        self.assertIn("jsonb_array_length(s.value->'zeiten') > 0", SQL)
        self.assertIn("ausgeschlossen", SQL)
        self.assertNotIn("WHERE false", SQL)

    def test_typ_sql_vollstaendig(self):
        typ_sql = (Path(__file__).resolve().parents[1] / "database" / "orte_typ_weihnachtsmarkt_2026-11-17.sql").read_text(encoding="utf-8")
        for typ in ("restaurant", "imbiss", "cafe", "kneipe", "club", "spielplatz", "ausflug", "wochenendtipp", "weihnachtsmarkt"):
            self.assertIn(f"'{typ}'", typ_sql)
        self.assertIn("RAISE EXCEPTION", typ_sql)


if __name__ == "__main__":
    unittest.main()


class EventMusterTest(unittest.TestCase):
    def test_trenner_doppelstrich_laesst_regex_oder_stehen(self):
        e, fehler = im.markt_pruefen(csv_markt(event_muster=r"k(ö|oe)\s*on\s*ice||deg[- ]winterwelt"))
        self.assertEqual(fehler, [])
        self.assertEqual(e["event_muster"], [r"k(ö|oe)\s*on\s*ice", "deg[- ]winterwelt"])

    def test_ungueltiges_muster_ist_fehler(self):
        e, fehler = im.markt_pruefen(csv_markt(event_muster="(("))
        self.assertIsNone(e)
        self.assertTrue(fehler)


class GoogleLaufTest(unittest.TestCase):
    from scraper.weihnachtsmaerkte import google_lauf as gl  # noqa: E402

    def eintrag(self, s, **kw):
        saison = {"von": "2026-11-19", "bis": "2026-12-30", "zeiten": [{"tage": ["mo", "di", "mi", "do", "fr", "sa", "so"], "von": "11:00", "bis": "20:00"}],
                  "sonder": [{"datum": "2026-11-22", "geschlossen": True}]}
        return {"schluessel": s, "attraktion": False, "merkmale": {}, "art": [], "saison": saison, "eintritt": None, "anfahrt": None, **kw}

    def test_score_skala_und_randfaelle(self):
        gl = self.gl
        e = [self.eintrag("a", eintritt={"wert": "frei"}, anfahrt={"haltestellen": [{"name": "X"}]},
                          merkmale={"eisbahn": {"wert": "ja"}, "kunsthandwerk": {"wert": "teilweise"}}),
             self.eintrag("b"), self.eintrag("rad", attraktion=True)]
        ohne_google = gl.score_berechnen(e, {})
        self.assertNotIn("rad", ohne_google)                       # Attraktion ohne Score
        self.assertTrue(0 <= ohne_google["a"]["wert"] <= 10)
        self.assertGreater(ohne_google["a"]["wert"], ohne_google["b"]["wert"])
        self.assertEqual(ohne_google["b"]["teile"]["beliebtheit"], 0.5)  # kein Markt-Treffer → neutral
        mit = gl.score_berechnen(e, {"a": {"bezug": "markt", "rating": 4.6, "anzahl": 900}, "b": {"bezug": "ort", "rating": 4.9, "anzahl": 5000}})
        self.assertEqual(mit["b"]["teile"]["beliebtheit"], 0.5)          # Ort-Bewertungen zählen nicht
        self.assertEqual(mit["b"]["google_bezug"], "ort")
        null = gl.score_berechnen(e, {"a": {"bezug": "markt", "rating": 4.0, "anzahl": 0}})
        self.assertTrue(0 <= null["a"]["wert"] <= 10)                    # n_max = 0 wirft nicht
        self.assertNotIn("rating", json.dumps(mit))                      # keine Rohwerte im Ergebnis

    def test_oeffnungstage_ohne_geschlossene(self):
        self.assertEqual(self.gl.oeffnungstage(self.eintrag("a")["saison"]), 41)  # 42 Tage − Totensonntag

    def test_bezug_und_treffer(self):
        gl = self.gl
        nah = {"id": "p1", "displayName": {"text": "Weihnachtsmarkt Schloss Benrath"}, "location": {"latitude": 51.1612, "longitude": 6.8704}}
        fern = {"id": "p2", "displayName": {"text": "Weihnachtsmarkt Schloss Benrath"}, "location": {"latitude": 51.2, "longitude": 6.8}}
        t, art = gl.treffer_waehlen("Weihnachtsmarkt Schloss Benrath", 51.161181, 6.870436, [fern, nah])
        self.assertEqual((t["id"], art), ("p1", "name"))
        self.assertEqual(gl.google_bezug(t), "markt")
        self.assertEqual(gl.google_bezug({"displayName": {"text": "Schloss Benrath"}}), "ort")
        self.assertEqual(gl.treffer_waehlen("X", 51.0, 6.0, [nah])[1], "kein_treffer")

    def test_foto_sql(self):
        sql = self.gl.sql_aus_sichtung({"bilk-arcaden": {"foto": 0, "grund": "ohne Gesichter", "fokus": "40%"}, "x": {"foto": None, "grund": "nur Gesichter"}},
                                       {"bilk-arcaden": [{"name": "places/a/photos/b", "breite": 800, "hoehe": 600, "autor": "Max O'Neil", "autor_url": "https://u"}]},
                                       "2026-11-17")
        self.assertIn("extras->'weihnachtsmarkt'->>'schluessel' = 'bilk-arcaden'", sql)
        self.assertIn("Max O''Neil", sql)
        self.assertIn("'bild_fokus', '40%'", sql)
        self.assertIn("-- x: kein Foto", sql)


class ScoreRandfaelleTest(unittest.TestCase):
    """Cursor-Check Stufe 1b: n = 0 und „teilweise“ exakt prüfen."""
    from scraper.weihnachtsmaerkte import google_lauf as gl  # noqa: E402

    def eintrag(self, s, **kw):
        return {"schluessel": s, "attraktion": False, "merkmale": {}, "art": [], "saison": None, "eintritt": None, "anfahrt": None, **kw}

    def test_markt_treffer_alle_ohne_bewertung(self):
        r = self.gl.score_berechnen([self.eintrag("a"), self.eintrag("b")],
                                    {"a": {"bezug": "markt", "rating": None, "anzahl": 0}, "b": {"bezug": "markt", "rating": 4.0, "anzahl": 0}})
        self.assertAlmostEqual(r["a"]["teile"]["beliebtheit"], round(0.5 * 0.30 / 0.45, 3))
        self.assertAlmostEqual(r["b"]["teile"]["beliebtheit"], round(0.5 * 0.30 / 0.45, 3))

    def test_kein_markt_treffer(self):
        r = self.gl.score_berechnen([self.eintrag("a")], {"a": {"bezug": "ort", "rating": 4.9, "anzahl": 999}})
        self.assertEqual(r["a"]["teile"]["beliebtheit"], 0.5)

    def test_teilweise_ist_halbes_merkmal(self):
        r = self.gl.score_berechnen([self.eintrag("a", merkmale={"eisbahn": {"wert": "ja"}, "wc": {"wert": "ja"},
                                                                  "kunsthandwerk": {"wert": "teilweise"}})], {})
        self.assertAlmostEqual(r["a"]["teile"]["angebot"], 1.5 / 4)   # wc zählt nicht zum Angebot

    def test_markt_mit_null_bewertungen_neben_bewerteten(self):
        r = self.gl.score_berechnen([self.eintrag("a"), self.eintrag("b")],
                                    {"a": {"bezug": "markt", "rating": 4.5, "anzahl": 400}, "b": {"bezug": "markt", "rating": None, "anzahl": 0}})
        self.assertEqual(r["b"]["teile"]["beliebtheit"], round(((4.5 - 3.5) / 1.5 * 0.30 + 0.0) / 0.45, 3))


class BilderTest(unittest.TestCase):
    """Eigene Bilder (Veranstalter) – scraper/weihnachtsmaerkte/bilder.py."""

    def setUp(self):
        import tempfile
        from scraper.weihnachtsmaerkte import bilder as b
        self.b = b
        self.tmp = tempfile.TemporaryDirectory()
        self.roh = Path(self.tmp.name)
        (self.roh / "nord.jpg").write_bytes(b"x")

    def tearDown(self):
        self.tmp.cleanup()

    def zeile(self, **k):
        z = {"schluessel": "nordstrasse", "datei": "nord.jpg", "nachweis": "Foto: IG Nordstraße", "link": "",
             "erlaubnis": "E-Mail 18.11.2026", "fokus": ""}
        z.update(k)
        return z

    def test_gueltige_zeile_und_nachweis_ohne_foto_praefix(self):
        gut, fehler = self.b.zeilen_pruefen([self.zeile()], {"nordstrasse"}, self.roh)
        self.assertEqual(fehler, [])
        self.assertEqual(gut[0]["nachweis"], "IG Nordstraße")

    def test_ohne_erlaubnis_kein_bild(self):
        gut, fehler = self.b.zeilen_pruefen([self.zeile(erlaubnis="")], {"nordstrasse"}, self.roh)
        self.assertEqual(gut, [])
        self.assertIn("Erlaubnis", fehler[0])

    def test_unbekannter_schluessel_fehlende_datei_pfad_und_link(self):
        faelle = [self.zeile(schluessel="gibtsnicht"), self.zeile(datei="fehlt.jpg"), self.zeile(datei="../nord.jpg"),
                  self.zeile(link="http://x.de"), self.zeile(fokus="mitte"), self.zeile(nachweis="", link="https://x.de")]
        for z in faelle:
            gut, fehler = self.b.zeilen_pruefen([z], {"nordstrasse"}, self.roh)
            self.assertEqual(gut, [], z)
            self.assertEqual(len(fehler), 1, z)

    def test_doppelter_schluessel(self):
        gut, fehler = self.b.zeilen_pruefen([self.zeile(), self.zeile()], {"nordstrasse"}, self.roh)
        self.assertEqual(len(gut), 1)
        self.assertIn("doppelt", fehler[0])

    def test_sql_setzt_bild_nachweis_und_verwirft_alten_fokus(self):
        gut, _ = self.b.zeilen_pruefen([self.zeile(nachweis="Schausteller O'Brien", link="https://nordstrasse.de", fokus="35%")],
                                       {"nordstrasse"}, self.roh)
        sql = self.b.sql_bauen(gut, "2026-11-18")
        self.assertIn("bild_url = '/guides/weihnachtsmaerkte/nordstrasse.webp'", sql)
        self.assertIn("bild_attribution = 'Schausteller O''Brien'", sql)
        self.assertIn("(extras - 'bild_link' - 'bild_fokus') || jsonb_build_object(", sql)
        self.assertIn("'bild_link', 'https://nordstrasse.de'", sql)
        self.assertIn("'bild_fokus', '35%'", sql)
        self.assertIn("->>'schluessel' = 'nordstrasse'", sql)
        ohne, _ = self.b.zeilen_pruefen([self.zeile()], {"nordstrasse"}, self.roh)
        self.assertNotIn("'bild_link',", self.b.sql_bauen(ohne, "2026-11-18"))

    def test_umwandeln_verkleinert_und_speichert_webp(self):
        from PIL import Image
        Image.new("RGB", (3200, 1600), "red").save(self.roh / "gross.png")
        breite, hoehe = self.b.bild_umwandeln(self.roh / "gross.png", self.roh / "aus" / "x.webp")
        self.assertEqual((breite, hoehe), (1600, 800))
        with Image.open(self.roh / "aus" / "x.webp") as i:
            self.assertEqual(i.format, "WEBP")

    def test_eigenes_foto_ohne_nachweis(self):
        gut, fehler = self.b.zeilen_pruefen([self.zeile(nachweis="")], {"nordstrasse"}, self.roh)
        self.assertEqual(fehler, [])
        sql = self.b.sql_bauen(gut, "2026-11-18")
        self.assertIn("bild_attribution = NULL", sql)
        self.assertIn("(eigenes, ohne Nachweis)", sql)
