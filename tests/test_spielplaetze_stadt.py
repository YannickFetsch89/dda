"""Tests für den Spielplatz-Stadt-Import (python -m unittest tests.test_spielplaetze_stadt)."""
import re
import tempfile
import unittest
from pathlib import Path

from scraper.spielplaetze import stadt_import as si

# Ein Grad Breite ≈ 111.195 m; Abstände der Testpunkte in Metern nach Norden
M = 1 / 111195.0
BASIS = (51.22, 6.78)


def feature(schluessel, name, art="336 Kinderspielplatz", groesse="100,0", nummer=9000, nord_m=0.0,
            bezirk=1, strasse="", lon=None):
    lat = BASIS[0] + nord_m * M
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon or BASIS[1], lat]},
            "properties": {"objektschluessel": schluessel, "objektbezeichnung": name, "objektart": art,
                           "groesse": groesse, "4stellige_nr": nummer, "stadtbezirk": bezirk,
                           "strasse_hausnr": strasse}}


def quadrat(lon0, lat0, lon1, lat1):
    return [[lon0, lat0], [lon1, lat0], [lon1, lat1], [lon0, lat1], [lon0, lat0]]


# Zwei Test-Stadtteile: „Pempelfort“ (Bezirk 01) links, „Hafen“ (Bezirk 03) rechts, mit Loch in Pempelfort
STADTTEILE = si.stadtteile_lesen({"features": [
    {"properties": {"Name": "Pempelfort", "Nummer": "011"},
     "geometry": {"type": "MultiPolygon", "coordinates": [[quadrat(6.70, 51.20, 6.79, 51.25),
                                                           quadrat(6.71, 51.21, 6.72, 51.22)]]}},
    {"properties": {"Name": "Hafen", "Nummer": "033"},
     "geometry": {"type": "MultiPolygon", "coordinates": [[quadrat(6.79, 51.20, 6.85, 51.25)]]}},
]})


def planen(features, korrekturen=None, bestehend=(), andere=()):
    plaetze = si.plaetze_bilden(si.teile_lesen({"features": features}))
    return si.planen(plaetze, STADTTEILE, korrekturen, list(bestehend), set(andere), "2026-11-13", "2020-09-25")


def korrektur(**werte):
    basis = {"anzeigename": "", "ausschliessen": False, "grund": "", "stadtteil": "", "bestaetigt": []}
    return {**basis, **werte}


def zeile_aus(datensatz, zid="z1", freigeschaltet_am=None, slug=None, **sp_extra):
    """Macht aus einem geplanten neuen Datensatz eine „bestehende“ Datenbankzeile."""
    sp = {**datensatz["stadtfelder"], "freigeschaltet_am": freigeschaltet_am, **sp_extra}
    return {"id": zid, "name": datensatz["spalten"]["name"], "slug": slug or datensatz["spalten"]["slug"],
            "stadtteil": datensatz["spalten"]["stadtteil"], "extras": {"spielplatz": sp}}


class DateiTest(unittest.TestCase):
    def test_rechteck_abbruch(self):
        with self.assertRaises(ValueError):
            si.teile_lesen({"features": [feature("1/1", "X, Ksp", lon=3456.7)]})

    def test_objektart_text_und_leerzeilen(self):
        teile = si.teile_lesen({"features": [
            feature("1/1", "A, Ksp"), feature("1/2", "B, Wsp", art="337 Wasserspielplatz"),
            feature("1/3", "C, KSP", art="536 Waldkinderspielplatz"), feature("1/4", "D", art="338 Bolzplatz"),
            {"type": "Feature", "geometry": None, "properties": None},
        ]})
        self.assertEqual([t["typ"] for t in teile], ["kinder", "wasser", "wald"])

    def test_groesse_mit_komma(self):
        self.assertEqual(si.groesse_lesen("664,1"), 664.1)
        self.assertEqual(si.groesse_lesen("11.472,3"), 11472.3)
        self.assertIsNone(si.groesse_lesen(""))


class ZusammenfuehrungTest(unittest.TestCase):
    def test_gleicher_punkt_wird_ein_platz(self):
        p = si.plaetze_bilden(si.teile_lesen({"features": [
            feature("1/1", "GRAFENTAL, Naturpark Flingern, Ksp A", groesse="100,0", nummer=9777),
            feature("1/2", "GRAFENTAL, Naturpark Flingern, Ksp B", groesse="300,0", nummer=9777),
            feature("1/3", "GRAFENTAL, Naturpark Flingern, Ksp C", groesse="200,0", nummer=9777),
        ]}))
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0]["groesse_m2"], 600.0)
        self.assertEqual(p[0]["notfallnummer"], "9777")

    def test_40_m_zwei_plaetze_nummer_bleibt(self):
        p = si.plaetze_bilden(si.teile_lesen({"features": [
            feature("1/1", "A, Ksp", nummer=1), feature("1/2", "A, Ksp x", nummer=1, nord_m=40)]}))
        self.assertEqual([x["notfallnummer"] for x in p], ["1", "1"])

    def test_hanielpark_127_m_nummer_bleibt(self):
        p = si.plaetze_bilden(si.teile_lesen({"features": [
            feature("1/1", "HANIELPARK, Ksp a.d.Rollerbahn", nummer=9754),
            feature("1/2", "HANIELPARK, Ksp ggü. Sohnstr.", nummer=9754, nord_m=127)]}))
        self.assertEqual(len(p), 2)
        self.assertTrue(all(x["notfallnummer"] == "9754" for x in p))

    def test_ueber_150_m_nummer_unterdrueckt(self):
        p = si.plaetze_bilden(si.teile_lesen({"features": [
            feature("1/1", "A, Ksp", nummer=2), feature("1/2", "B, Ksp", nummer=2, nord_m=160)]}))
        self.assertEqual(len(p), 2)
        self.assertTrue(all(x["notfallnummer"] is None for x in p))
        self.assertIn("unterdrückt", p[0]["hinweise"][0])

    def test_bolzplatz_zaehlt_nicht(self):
        p = si.plaetze_bilden(si.teile_lesen({"features": [
            feature("1/1", "A, Ksp", nummer=3), feature("1/2", "A, Bolzplatz", art="338 Bolzplatz", nummer=3, nord_m=500)]}))
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0]["notfallnummer"], "3")

    def test_gleiche_groesse_kleinerer_schluessel(self):
        p = si.plaetze_bilden(si.teile_lesen({"features": [
            feature("01001/12", "A, Ksp", nummer=4, nord_m=10), feature("01001/9", "A, Ksp", nummer=4)]}))
        self.assertEqual(p[0]["schluessel"], ["01001/9", "01001/12"])
        self.assertAlmostEqual(p[0]["latitude"], round(BASIS[0], 7))

    def test_gemischte_gruppe(self):
        p = si.plaetze_bilden(si.teile_lesen({"features": [
            feature("1/1", "A, Ksp", nummer=5), feature("1/2", "A, Ksp", nummer=5, nord_m=10),
            feature("1/3", "A, Ksp z", nummer=5, nord_m=100)]}))
        self.assertEqual(len(p), 2)
        self.assertTrue(all("gruppe_gemischt" in x["codes"] for x in p))

    def test_typ_wasser_vor_kinder(self):
        p = si.plaetze_bilden(si.teile_lesen({"features": [
            feature("1/1", "AUF' M ROTT, KSP", nummer=6, groesse="11472,0"),
            feature("1/2", "AUF' M ROTT, WSP", art="337 Wasserspielplatz", nummer=6, groesse="707,0")]}))
        self.assertEqual(p[0]["typ"], "wasser")
        self.assertEqual(si.platz_name(p[0])[0], "Wasserspielplatz Auf’m Rott")


class NameTest(unittest.TestCase):
    def name(self, roh, typ="kinder"):
        segmente, _ = si.name_segmente(roh)
        return si.name_aus_segmenten(segmente, typ), si.ist_unklar(segmente)

    def test_beispiele(self):
        self.assertEqual(self.name("HOFGARTEN, Ksp Oederallee"), ("Spielplatz Hofgarten (Oederallee)", False))
        self.assertEqual(self.name("HANIELPARK, Ksp a.d.Rollerbahn"), ("Spielplatz Hanielpark (an der Rollerbahn)", False))
        self.assertEqual(self.name("HANIELPARK, Ksp ggü. Sohnstr."), ("Spielplatz Hanielpark (gegenüber Sohnstraße)", False))
        self.assertEqual(self.name("VOLKSGARTEN, WSP", "wasser"), ("Wasserspielplatz Volksgarten", False))
        self.assertEqual(self.name("Eller Forst, KSP", "wald"), ("Waldspielplatz Eller Forst", False))

    def test_gw_und_komma(self):
        segmente, hinweise = si.name_segmente("GW SCHORLEMERSTR., KSP Lütticher Str.")
        self.assertEqual(si.name_aus_segmenten(segmente, "kinder"), "Spielplatz Schorlemerstraße (Lütticher Straße)")
        self.assertIn("GW entfernt", hinweise)

    def test_apostroph_und_schreibweise(self):
        self.assertEqual(self.name("SPEE`SCHER GRABEN, KSP")[0], "Spielplatz Spee’scher Graben")
        self.assertEqual(self.name("AN DER LEIMKUHLE, Ksp")[0], "Spielplatz An der Leimkuhle")
        self.assertEqual(self.name("GRAF-VON-STAUFFENBERG-STR., KSP")[0], "Spielplatz Graf-von-Stauffenberg-Straße")
        self.assertEqual(self.name("STAENDEHAUSANLAGEN, Ksp")[0], "Spielplatz Ständehausanlagen")
        self.assertEqual(self.name("MICHAELPLATZ, Ksp")[0], "Spielplatz Michaelplatz")  # kein ae → ä
        self.assertEqual(self.name("AM QUELLENBUSCH, Hallesche Str., KSP")[0],
                         "Spielplatz Am Quellenbusch (Hallesche Straße)")

    def test_strasse_nur_am_wortende(self):
        self.assertEqual(self.name("STERNSTR.33, Ksp")[0], "Spielplatz Sternstraße 33")
        self.assertEqual(self.name("KÖLNER STR. 44/Innenhof, Ksp")[0], "Spielplatz Kölner Straße 44/Innenhof")
        self.assertEqual(self.name("FRITZ-STRASSMANN-STR., KSP")[0], "Spielplatz Fritz-Strassmann-Straße")
        self.assertEqual(self.name("CHRISTOPHSTRASSE   KSP")[0], "Spielplatz Christophstraße")

    def test_ergaenzungsstrich_und_zitat(self):
        self.assertEqual(self.name("LANGER-,BINNENSTR., Ksp")[0], "Spielplatz Langer- und Binnenstraße")
        self.assertEqual(self.name("VOR DEM DEICH, Ksp 'Wind,Wasser,Sonne'", "wasser")[0],
                         "Wasserspielplatz Vor dem Deich („Wind, Wasser, Sonne“)")
        self.assertEqual(self.name("VOLKSGARTEN, Klein-KSP westlich vom WSP")[0],
                         "Spielplatz Volksgarten (Klein-Spielplatz westlich vom Wasserspielplatz)")

    def test_unklar(self):
        self.assertTrue(self.name("GW RATH/ELLER, Ksp Fritz./Mörsenb.")[1])
        self.assertTrue(self.name("RHEINPARK, Ksp gg. Klever Str.")[1])
        self.assertTrue(self.name("VENNHAUSER ALLEE, Ksp DA Distelfink")[1])
        self.assertFalse(self.name("GW GARATH NW, KSP PETER-BEHRENS-STR.91")[1])

    def test_zusammengefuehrt_gemeinsamer_stamm(self):
        p = si.plaetze_bilden(si.teile_lesen({"features": [
            feature("1/1", "ALTER GERRESHEIMER FRIEDHOF, Wsp", art="337 Wasserspielplatz", nummer=7),
            feature("1/2", "ALTER GERRESHEIMER FRIEDHOF, Ksp gg. Wsp", nummer=7, nord_m=5)]}))
        name, unklar, _ = si.platz_name(p[0])
        self.assertEqual(name, "Wasserspielplatz Alter Gerresheimer Friedhof")
        self.assertFalse(unklar)  # unklarer Zusatz eines Teils blockiert den Stamm nicht


class StadtteilTest(unittest.TestCase):
    def test_ray_casting(self):
        self.assertEqual(si.polygon_treffer(51.23, 6.75, STADTTEILE)["name"], "Pempelfort")
        self.assertIsNone(si.polygon_treffer(51.215, 6.715, STADTTEILE))  # im Loch
        self.assertEqual(si.polygon_treffer(51.23, 6.80, STADTTEILE)["name"], "Hafen")
        self.assertIsNone(si.polygon_treffer(51.30, 6.80, STADTTEILE))

    def test_flingern_mapping_und_katalog(self):
        st = si.stadtteile_lesen({"features": [{"properties": {"Name": "Flingern Süd", "Nummer": "021"},
                                                "geometry": {"type": "Polygon", "coordinates": [quadrat(0, 0, 1, 1)]}}]})
        self.assertEqual(st[0]["name"], "Flingern-Süd")
        with self.assertRaises(ValueError):
            si.stadtteile_lesen({"features": [{"properties": {"Name": "Atlantis", "Nummer": "999"},
                                               "geometry": {"type": "Polygon", "coordinates": [quadrat(0, 0, 1, 1)]}}]})

    def test_katalog_wie_web(self):
        ts = (Path(__file__).resolve().parents[1] / "web" / "lib" / "stadtteile.ts").read_text(encoding="utf-8")
        web = set()
        for liste in re.findall(r"stadtteile: \[([^\]]*)\]", ts):
            web |= set(re.findall(r'"([^"]+)"', liste))
        self.assertEqual(web, set(si.KATALOG))

    def test_reihenfolge(self):
        hafen = {"name": "Hafen", "nummer": "033"}
        self.assertEqual(si.stadtteil_bestimmen(hafen, "Bilk", None, False)[0], "Bilk")  # Katalogwert vor Polygon
        wert, codes, _, fehler = si.stadtteil_bestimmen(hafen, "Medienhafen", "Unterbilk", True)
        self.assertEqual((wert, codes), ("Unterbilk", {"kein_stadtteil"}))  # Polygon gilt nicht
        self.assertTrue(fehler)
        self.assertEqual(si.stadtteil_bestimmen(hafen, "Medienhafen", None, False)[:2], (None, {"kein_stadtteil"}))
        self.assertEqual(si.stadtteil_bestimmen(None, "", "Bilk", True)[:2], ("Bilk", {"kein_stadtteil"}))
        self.assertEqual(si.stadtteil_bestimmen(None, "", "Bilk", False)[:2], (None, {"kein_stadtteil"}))

    def test_bezirk(self):
        t = {"name": "Hafen", "nummer": "033"}
        self.assertTrue(si.bezirk_abweichend(t, 1))
        self.assertFalse(si.bezirk_abweichend(t, 3))
        self.assertFalse(si.bezirk_abweichend(t, None))  # leer ist kein Widerspruch
        self.assertFalse(si.bezirk_abweichend(None, 1))


class KorrekturDateiTest(unittest.TestCase):
    def lesen(self, inhalt):
        with tempfile.TemporaryDirectory() as d:
            pfad = Path(d) / "korrekturen.csv"
            pfad.write_text(inhalt, encoding="utf-8")
            return si.korrekturen_lesen(pfad)

    def test_fehlende_datei(self):
        self.assertEqual(si.korrekturen_lesen(Path("gibt/es/nicht.csv")), (None, []))

    def test_lesen_und_fehler(self):
        daten, fehler = self.lesen(
            "schluessel;anzeigename;ausschliessen;grund;stadtteil;bestaetigt\n"
            "1/1;Spielplatz X;;;Bilk;access_private, name_unklar\n"
            "1/2;;ja;;;\n"
            "abenteuer:x;;;;;\n")
        self.assertEqual(daten["1/1"]["bestaetigt"], ["access_private"])
        self.assertTrue(daten["1/2"]["ausschliessen"])
        self.assertNotIn("abenteuer:x", daten)
        self.assertEqual(len(fehler), 3)  # name_unklar bestätigt, ja ohne Grund, abenteuer-Zeile

    def test_ausgeschlossen(self):
        self.assertEqual(si.ausgeschlossen_neu(None, None, "alt"), "alt")  # Datei fehlt
        self.assertIsNone(si.ausgeschlossen_neu({}, None, "alt"))  # Schlüssel fehlt
        self.assertEqual(si.ausgeschlossen_neu({"x": 1}, korrektur(ausschliessen=True, grund="Dublette"), None), "Dublette")
        self.assertEqual(si.ausgeschlossen_neu({"x": 1}, korrektur(ausschliessen=True), "alt"), "alt")  # leerer Grund
        self.assertIsNone(si.ausgeschlossen_neu({"x": 1}, korrektur(), "alt"))


class PlanTest(unittest.TestCase):
    F = [feature("1/1", "HOFGARTEN, Ksp Oederallee", nummer=1, strasse="Oederallee 1"),
         feature("2/1", "GW RATH/ELLER, Ksp Fritz./Mörsenb.", nummer=2, nord_m=500)]

    def test_neuer_platz(self):
        plan = planen(self.F)
        d = plan["neu"][0]
        self.assertEqual(d["spalten"]["name"], "Spielplatz Hofgarten (Oederallee)")
        self.assertEqual(d["spalten"]["slug"], "spielplatz-hofgarten-oederallee-pempelfort")
        self.assertEqual(d["spalten"]["adresse"], "Oederallee 1, Düsseldorf")
        self.assertEqual(d["stadtfelder"]["pruefung"], [])
        self.assertEqual(d["stadtfelder"]["bestaetigt"], [])
        self.assertIn("name_unklar", plan["neu"][1]["stadtfelder"]["pruefung"])

    def test_adresse_leer(self):
        self.assertIsNone(planen(self.F)["neu"][1]["spalten"]["adresse"])

    def test_anzeigename_ersetzt_normalisierung(self):
        plan = planen(self.F, {"2/1": korrektur(anzeigename="Spielplatz Fritz-Wüst-Straße")})
        d = plan["neu"][1]
        self.assertEqual(d["spalten"]["name"], "Spielplatz Fritz-Wüst-Straße")
        self.assertEqual(d["stadtfelder"]["name_quelle"], "korrektur")
        self.assertNotIn("name_unklar", d["stadtfelder"]["pruefung"])
        self.assertTrue(d["spalten"]["slug"].startswith("spielplatz-fritz-wuest-strasse"))

    def test_korrektur_nicht_am_kleinsten_schluessel(self):
        f = [feature("1/1", "A, Ksp", nummer=9), feature("1/2", "A, Ksp", nummer=9, nord_m=5)]
        plan = planen(f, {"1/2": korrektur(anzeigename="X")})
        self.assertNotEqual(plan["neu"][0]["spalten"]["name"], "X")
        self.assertTrue(any("nicht der kleinste" in x for x in plan["fehler"]))

    def test_stadtteil_aus_korrektur_und_ungueltig(self):
        plan = planen(self.F, {"1/1": korrektur(stadtteil="Hafen"), "2/1": korrektur(stadtteil="Medienhafen")})
        self.assertEqual(plan["neu"][0]["spalten"]["stadtteil"], "Hafen")
        self.assertIsNone(plan["neu"][1]["spalten"]["stadtteil"])
        self.assertIn("kein_stadtteil", plan["neu"][1]["stadtfelder"]["pruefung"])
        self.assertTrue(plan["fehler"])

    def test_wiederholung_nie_freigeschaltet_neuer_name_neuer_slug(self):
        erst = planen(self.F)
        alt = [zeile_aus(erst["neu"][1], "z2")]
        plan = planen(self.F, {"2/1": korrektur(anzeigename="Spielplatz Fritz-Wüst-Straße")}, alt)
        a = [x for x in plan["aenderungen"] if x["art"] == "aktualisiert"][0]
        self.assertEqual(a["spalten"]["name"], "Spielplatz Fritz-Wüst-Straße")
        self.assertNotEqual(a["spalten"]["slug"], alt[0]["slug"])
        self.assertNotIn("aktiv", a["spalten"])

    def test_wiederholung_freigeschaltet_slug_und_name_fest(self):
        erst = planen(self.F)
        alt = [zeile_aus(erst["neu"][0], "z1", freigeschaltet_am="2026-12-01")]
        g = [feature("1/1", "HOFGARTEN, Ksp gg. Oederallee", nummer=1)]
        plan = planen(g, None, alt)
        a = plan["aenderungen"][0]
        self.assertEqual(a["spalten"]["slug"], alt[0]["slug"])
        self.assertEqual(a["spalten"]["name"], alt[0]["name"])
        self.assertNotIn("name_unklar", a["stadtfelder"]["pruefung"])  # nur an nie freigeschalteten Zeilen
        self.assertIn("Stadtname neu", a["hinweise"])
        # abgeschaltet (aktiv=false, freigeschaltet_am gesetzt) + Anzeigename: Name neu, Slug bleibt
        plan = planen(g, {"1/1": korrektur(anzeigename="Spielplatz Neu")}, alt)
        self.assertEqual(plan["aenderungen"][0]["spalten"]["name"], "Spielplatz Neu")
        self.assertEqual(plan["aenderungen"][0]["spalten"]["slug"], alt[0]["slug"])

    def test_freigeschaltet_polygon_fehltreffer_behaelt_stadtteil(self):
        erst = planen(self.F)
        alt = [zeile_aus(erst["neu"][0], "z1", freigeschaltet_am="2026-12-01")]
        weg = [feature("1/1", "HOFGARTEN, Ksp Oederallee", nummer=1, nord_m=20000)]  # außerhalb der Test-Polygone
        a = planen(weg, None, alt)["aenderungen"][0]
        self.assertEqual(a["spalten"]["stadtteil"], "Pempelfort")
        self.assertIn("kein_stadtteil", a["stadtfelder"]["pruefung"])

    def test_osm_codes_und_eintritt_bleiben(self):
        erst = planen(self.F)
        alt = [zeile_aus(erst["neu"][0], "z1", pruefung=["access_private"], eintritt="ja")]
        a = planen(self.F[:1], None, alt)["aenderungen"][0]
        self.assertIn("access_private", a["stadtfelder"]["pruefung"])
        self.assertNotIn("eintritt", a["stadtfelder"])

    def test_ausschluss_und_fehlende_datei(self):
        erst = planen(self.F)
        alt = [zeile_aus(erst["neu"][0], "z1", ausgeschlossen="Dublette", bestaetigt=["access_private"])]
        a = planen(self.F[:1], None, alt)["aenderungen"][0]  # Datei fehlt → bleibt
        self.assertEqual(a["stadtfelder"]["ausgeschlossen"], "Dublette")
        self.assertEqual(a["stadtfelder"]["bestaetigt"], ["access_private"])
        a = planen(self.F[:1], {}, alt)["aenderungen"][0]  # Datei da, Schlüssel fehlt → null
        self.assertIsNone(a["stadtfelder"]["ausgeschlossen"])
        self.assertEqual(a["stadtfelder"]["bestaetigt"], [])

    def test_fehlender_schluessel_und_verschwundene_zeile(self):
        f = [feature("1/1", "A, Ksp", nummer=9), feature("1/2", "A, Ksp", nummer=9, nord_m=5)]
        erst = planen(f)
        alt = [zeile_aus(erst["neu"][0], "z1", freigeschaltet_am="2026-12-01")]
        a = planen(f[:1], None, alt)["aenderungen"][0]
        self.assertEqual(a["stadtfelder"]["fehlende_teile"], [{"objektschluessel": "1/2", "seit": "2026-11-13"}])
        self.assertEqual(a["spalten"]["slug"], alt[0]["slug"])
        plan = planen([feature("5/5", "B, Ksp", nummer=8)], None, alt)
        fehlt = [x for x in plan["aenderungen"] if x["art"] == "fehlt"]
        self.assertEqual(fehlt[0]["stadtfelder"], {"stadt_fehlt_seit": "2026-11-13"})
        self.assertTrue(any(z["status"] == "fehlt in Stadtdatei" for z in plan["pruefung"]))

    def test_schluessel_wechseln_gruppe_konflikt(self):
        erst = planen(self.F)
        alt = [zeile_aus(erst["neu"][0], "z1"), zeile_aus(erst["neu"][1], "z2")]
        # beide alten Schlüssel liegen jetzt in einer Gruppe → trifft zwei Zeilen
        f = [feature("1/1", "A, Ksp", nummer=1), feature("2/1", "A, Ksp", nummer=1, nord_m=5)]
        plan = planen(f, None, alt)
        self.assertEqual(plan["neu"], [])
        self.assertEqual([z["status"] for z in plan["pruefung"]], ["konflikt"])

    def test_slug_reihenfolge_und_kollision(self):
        f = [feature("2/1", "A, Ksp", nummer=1), feature("1/1", "A, Ksp", nummer=2, nord_m=500)]
        plan = planen(f, andere={"spielplatz-a-pempelfort"})
        slugs = {d["platz"]["schluessel"][0]: d["spalten"]["slug"] for d in plan["neu"]}
        self.assertEqual(slugs, {"1/1": "spielplatz-a-pempelfort-b", "2/1": "spielplatz-a-pempelfort-c"})
        # Wiederholung ohne Namensänderung → gleiche Slugs
        alt = [zeile_aus(d, f"z{i}") for i, d in enumerate(plan["neu"])]
        wieder = planen(f, None, alt, andere={"spielplatz-a-pempelfort"})
        self.assertEqual(sorted(a["spalten"]["slug"] for a in wieder["aenderungen"]), sorted(slugs.values()))

    def test_freigeschalteter_slug_ist_reserviert(self):
        f = [feature("1/1", "A, Ksp", nummer=1), feature("0/1", "A, Ksp", nummer=2, nord_m=500)]
        erst = planen(f[:1])
        alt = [zeile_aus(erst["neu"][0], "z1", freigeschaltet_am="2026-12-01")]
        plan = planen(f, None, alt)
        self.assertEqual(plan["neu"][0]["spalten"]["slug"], "spielplatz-a-pempelfort-b")


if __name__ == "__main__":
    unittest.main()
