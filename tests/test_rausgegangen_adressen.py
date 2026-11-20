"""Tests für Rausgegangen-Adressen: Kachel in Ort/Adresse trennen und Adressen aus eigenen Daten ergänzen
(python -m unittest tests.test_rausgegangen_adressen). Ohne Netz und ohne Datenbank – die Startseite ist eine Fixture."""
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from pipeline import adressen_ergaenzen as ae
from scraper.tier1 import rausgegangen
from scraper.tier1.rausgegangen import _ort_adresse_trennen

FIXTURE = (Path(__file__).parent / "fixtures" / "rausgegangen_startseite.html").read_text(encoding="utf-8")
MORGEN = (date.today() + timedelta(days=1)).isoformat()


class KachelTrennenTest(unittest.TestCase):
    def test_name_strasse_plz(self):
        self.assertEqual(_ort_adresse_trennen("Flow, Mertensgasse 2, 40213 Düsseldorf"),
                         ("Flow", "Mertensgasse 2, 40213 Düsseldorf"))
        self.assertEqual(_ort_adresse_trennen("Hotel Motel One, Immermannstraße 54, 40210 Düsseldorf"),
                         ("Hotel Motel One", "Immermannstraße 54, 40210 Düsseldorf"))

    def test_stadtbezirk_und_land_fallen_weg(self):
        self.assertEqual(
            _ort_adresse_trennen("Cafe Bar La Paillette, Schirmerstraße 2, 40211 Düsseldorf-Stadtbezirk 1"),
            ("Cafe Bar La Paillette", "Schirmerstraße 2, 40211 Düsseldorf"),
        )
        self.assertEqual(_ort_adresse_trennen("Franklinstraße 41, Düsseldorf-Stadtbezirk 1, Deutschland"),
                         ("Franklinstraße 41", "Franklinstraße 41, Düsseldorf"))

    def test_nur_strasse_mit_nummer(self):
        self.assertEqual(_ort_adresse_trennen("Burgplatz 5-6, Düsseldorf"), ("Burgplatz 5-6", "Burgplatz 5-6, Düsseldorf"))

    def test_stadt_vorne_strasse(self):
        self.assertEqual(_ort_adresse_trennen("Düsseldorf, Schadowstraße"), ("Schadowstraße", "Schadowstraße, Düsseldorf"))
        self.assertEqual(_ort_adresse_trennen("Düsseldorf, Königsallee"), ("Königsallee", "Königsallee, Düsseldorf"))
        self.assertEqual(_ort_adresse_trennen("Düsseldorf, Corneliusplatz"), ("Corneliusplatz", "Corneliusplatz, Düsseldorf"))

    def test_stadt_vorne_ohne_strasse_bleibt(self):
        # pipeline/ortsnamen.py kennt „Düsseldorf, Hauptbahnhof“ als Schreibweise
        self.assertEqual(_ort_adresse_trennen("Düsseldorf, Hauptbahnhof"), ("Düsseldorf, Hauptbahnhof", None))

    def test_name_und_stadt_ohne_adresse(self):
        self.assertEqual(_ort_adresse_trennen("Radisson Blu Media Harbour Hotel, Düsseldorf"),
                         ("Radisson Blu Media Harbour Hotel", None))

    def test_namen_mit_komma_bleiben(self):
        for text in [
            "zakk - Zentrum für Aktion, Kultur und Kommunikation",
            "Nilsson, Initiativen Haus",
            "Heinrich-Heine-Universität Düsseldorf, Hörsaal 3A",
            "FUTURO SI, Initiative für Kinder in Lateinamerika e.V.",
            "Stiftsplatz an der Lambertuskirche (Haupteingang, gegenüber vom Pfarrbüro)",
            "Vor dem Cigköfte Stand, Düsseldorf Hbf",
            "Jugendkirche Düsseldorf",
        ]:
            with self.subTest(text=text):
                self.assertEqual(_ort_adresse_trennen(text), (text, None))

    def test_leer(self):
        self.assertEqual(_ort_adresse_trennen(None), (None, None))
        self.assertEqual(_ort_adresse_trennen(""), ("", None))


class ScrapeFixtureTest(unittest.TestCase):
    def setUp(self):
        # Kein Abruf: scheitert der Test hier, hätte der Scraper trotz übergebenem HTML geladen
        patcher = mock.patch.object(rausgegangen, "_seite_laden", side_effect=AssertionError("kein Abruf erlaubt"))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.events = rausgegangen.scrape(html=FIXTURE)
        self.nach_titel = {e["titel"]: e for e in self.events}

    def test_doppelte_kachel_zaehlt_einmal(self):
        self.assertEqual(len(self.events), 5)

    def test_kachel_mit_adresse(self):
        flow = self.nach_titel["Afterwork im Flow"]
        self.assertEqual(flow["ort"], "Flow")
        self.assertEqual(flow["adresse"], "Mertensgasse 2, 40213 Düsseldorf")
        self.assertEqual(flow["datum"], date.today().isoformat())
        self.assertEqual(flow["uhrzeit"], "19:00")

    def test_strassenmarkt(self):
        markt = self.nach_titel["Weihnachtsmarkt an der Schadowstraße"]
        self.assertEqual((markt["ort"], markt["adresse"]), ("Schadowstraße", "Schadowstraße, Düsseldorf"))

    def test_veganer_markt_ohne_adresse_in_der_kachel(self):
        markt = self.nach_titel["Veihnachtsmarkt Düsseldorf: der vegane Weihnachtsmarkt in der Jugendkirche"]
        self.assertEqual(markt["ort"], "Jugendkirche Düsseldorf")
        self.assertIsNone(markt["adresse"])
        self.assertEqual(markt["datum"], MORGEN)
        self.assertTrue(markt["quelle_url"].endswith("-in-der-0/"))

    def test_ohne_kachel_adresse_bleibt_ort(self):
        zakk = self.nach_titel["Sibel Schick im Gespräch"]
        self.assertEqual(zakk["ort"], "zakk - Zentrum für Aktion, Kultur und Kommunikation")
        self.assertIsNone(zakk["adresse"])


def rg(titel="Lesung", ort="Jugendkirche Düsseldorf", datum="2026-11-28", adresse=None):
    return {"titel": titel, "ort": ort, "datum": datum, "adresse": adresse, "quelle_name": "Rausgegangen",
            "quelle_url": "https://rausgegangen.de/events/x-0/"}


def anderes(titel, ort, adresse, datum="2026-11-28", quelle="zakk"):
    return {"titel": titel, "ort": ort, "datum": datum, "adresse": adresse, "quelle_name": quelle,
            "quelle_url": f"https://{quelle}.example/x"}


class AdresseHilfsfunktionenTest(unittest.TestCase):
    def test_ist_adresse(self):
        self.assertTrue(ae.ist_adresse("Fichtenstraße 40, 40233 Düsseldorf"))
        self.assertTrue(ae.ist_adresse("Konrad-Adenauer-Platz 1 Düsseldorf"))
        self.assertTrue(ae.ist_adresse("Volksgarten, 40219 Düsseldorf"))
        self.assertFalse(ae.ist_adresse("Savoy Theater, Düsseldorf", "Savoy Theater"))
        self.assertFalse(ae.ist_adresse("S- und U-Bahnhof Flingern, Düsseldorf"))
        self.assertFalse(ae.ist_adresse(None))
        self.assertFalse(ae.ist_adresse("  "))

    def test_bereinigen(self):
        self.assertEqual(ae.adresse_bereinigen("Ehrenhof 1, 40479 Düsseldorf-Stadtbezirk 1, Germany"),
                         "Ehrenhof 1, 40479 Düsseldorf")
        self.assertEqual(
            ae.adresse_bereinigen("Konrad-Adenauer-Platz 14, 40210 Düsseldorf, Germany 40210 Düsseldorf"),
            "Konrad-Adenauer-Platz 14, 40210 Düsseldorf",
        )
        self.assertEqual(ae.adresse_bereinigen("Konrad-Adenauer-Platz 1, 40210 Düsseldorf-KAP1"),
                         "Konrad-Adenauer-Platz 1, 40210 Düsseldorf")

    def test_beste_adresse_bevorzugt_plz(self):
        from collections import Counter
        kandidaten = Counter({"Ronsdorfer Str. 134 Düsseldorf": 3, "Ronsdorfer Straße 134, 40233 Düsseldorf": 1})
        self.assertEqual(ae._beste_adresse(kandidaten), "Ronsdorfer Straße 134, 40233 Düsseldorf")

    def test_beste_adresse_mehrdeutig(self):
        from collections import Counter
        kandidaten = Counter({"Marktpl. 10, 40878 Ratingen": 1, "Markt 11-15, 41460 Neuss": 1})
        self.assertIsNone(ae._beste_adresse(kandidaten))


class AdressbuchTest(unittest.TestCase):
    def setUp(self):
        self.orte = [
            {"name": "Weihnachtszauber Areal Böhler", "adresse": "Hansaallee 321, 40549 Düsseldorf"},
            {"name": "Cafe Extrablatt Ratingen", "adresse": "Marktpl. 10, 40878 Ratingen"},
            {"name": "Cafe Extrablatt Neuss", "adresse": "Markt 11-15, 41460 Neuss"},
        ]
        self.events = [
            anderes("Konzert", "zakk", "Fichtenstraße 40, 40233 Düsseldorf"),
            anderes("Konzert", "Zentrum für Aktion, Kultur und Kommunikation", "Fichtenstraße 40, 40233 Düsseldorf"),
            # Allgemeine Ortsangaben bekommen nie eine Adresse, auch wenn eine Quelle eine nennt
            anderes("Stadtführung", "Altstadt Düsseldorf", "Burgplatz 1, 40213 Düsseldorf"),
            anderes("Flohmarkt", "Düsseldorf", "Burgplatz 1, 40213 Düsseldorf"),
            anderes("Party", "Flingern", "Ackerstraße 1, 40233 Düsseldorf"),
            # Zwei Quellen, zwei Straßen: mehrdeutig
            anderes("A", "Kulturhaus Süd", "Hauptstraße 1, 40597 Düsseldorf"),
            anderes("B", "Kulturhaus Süd", "Nebenstraße 9, 40597 Düsseldorf"),
        ]
        self.buch = ae.adressbuch_bauen(self.orte, self.events)

    def test_einheitlicher_ortsname(self):
        adresse, herkunft = ae.adresse_finden(rg(ort="zakk - Zentrum für Aktion, Kultur und Kommunikation"), self.buch, {})
        self.assertEqual((adresse, herkunft), ("Fichtenstraße 40, 40233 Düsseldorf", "ort"))

    def test_allgemeine_orte_ohne_adresse(self):
        for ort in ["Altstadt Düsseldorf", "Düsseldorf", "Flingern"]:
            with self.subTest(ort=ort):
                self.assertEqual(ae.adresse_finden(rg(ort=ort), self.buch, {}), (None, None))

    def test_mehrdeutiger_ort_ohne_adresse(self):
        self.assertEqual(ae.adresse_finden(rg(ort="Kulturhaus Süd"), self.buch, {}), (None, None))

    def test_ortsname_in_laengerem_namen(self):
        self.assertEqual(ae.adresse_finden(rg(ort="Areal Böhler"), self.buch, {}),
                         ("Hansaallee 321, 40549 Düsseldorf", "ort"))

    def test_laengerer_name_mehrdeutig(self):
        self.assertEqual(ae.adresse_finden(rg(ort="Cafe Extrablatt Düsseldorf"), self.buch, {}), (None, None))

    def test_einzelwort_nicht_unscharf(self):
        # Ein einzelnes Wort reicht nicht für den Teilabgleich (zu unscharf)
        self.assertEqual(ae.adresse_finden(rg(ort="Böhler"), self.buch, {}), (None, None))


class TitelDatumTest(unittest.TestCase):
    def setUp(self):
        self.index = ae.titel_index_bauen([
            anderes("Fanny und Alexander", "Düsseldorfer Schauspielhaus", "Gustaf-Gründgens-Platz 1, 40211 Düsseldorf",
                    quelle="Düsseldorfer Schauspielhaus"),
            anderes("Weihnachtsmarkt", "Marktplatz Neuss", "Markt 1, 41460 Neuss"),
            # Rausgegangen selbst zählt hier nicht als andere Quelle
            rg(titel="Klima Café", adresse="Irgendwo 1, 40210 Düsseldorf"),
        ])

    def test_gleiches_event_andere_quelle(self):
        e = rg(titel="Fanny und Alexander", ort="Düsseldorfer Schauspielhaus - D’haus")
        self.assertEqual(ae.adresse_finden(e, {}, self.index), ("Gustaf-Gründgens-Platz 1, 40211 Düsseldorf", "titel"))

    def test_anderes_datum_kein_treffer(self):
        e = rg(titel="Fanny und Alexander", ort="D’haus", datum="2026-11-29")
        self.assertEqual(ae.adresse_finden(e, {}, self.index), (None, None))

    def test_einwort_titel_kein_treffer(self):
        self.assertEqual(ae.adresse_finden(rg(titel="Weihnachtsmarkt", ort="Irgendwo"), {}, self.index), (None, None))

    def test_rausgegangen_nicht_im_index(self):
        self.assertEqual(ae.adresse_finden(rg(titel="Klima Café", ort="Irgendwo"), {}, self.index), (None, None))


class ErgaenzenTest(unittest.TestCase):
    def test_nur_rausgegangen_und_nie_ueberschreiben(self):
        buch = {"zakk": "Fichtenstraße 40, 40233 Düsseldorf"}
        events = [
            rg(ort="zakk"),
            rg(ort="zakk", adresse="Eigene Adresse 1, 40233 Düsseldorf"),
            anderes("Konzert", "zakk", None),
            rg(ort="Unbekannter Ort"),
        ]
        zaehler = ae.adressen_ergaenzen(events, buch, {})
        self.assertEqual(events[0]["adresse"], "Fichtenstraße 40, 40233 Düsseldorf")
        self.assertEqual(events[1]["adresse"], "Eigene Adresse 1, 40233 Düsseldorf")
        self.assertIsNone(events[2]["adresse"])
        self.assertIsNone(events[3]["adresse"])
        self.assertEqual((zaehler["ort"], zaehler["ohne"]), (1, 1))

    def test_schritt_ohne_datenbank_bricht_nicht_ab(self):
        events = [rg(ort="zakk")]
        with mock.patch("database.client.get_supabase_client", side_effect=RuntimeError("keine DB")):
            self.assertIs(ae.adressen_schritt(events), events)
        self.assertIsNone(events[0]["adresse"])

    def test_schritt_nutzt_kachel_adressen_desselben_laufs(self):
        events = [
            rg(titel="A", ort="Flow", adresse="Mertensgasse 2, 40213 Düsseldorf"),
            rg(titel="B", ort="Flow"),
        ]
        with mock.patch.object(ae, "daten_laden", return_value=([], [])), \
                mock.patch("database.client.get_supabase_client"):
            ae.adressen_schritt(events)
        self.assertEqual(events[1]["adresse"], "Mertensgasse 2, 40213 Düsseldorf")


if __name__ == "__main__":
    unittest.main()


class OrtIdTest(unittest.TestCase):
    """Schritt 1e2 nutzt zuerst die ort_id aus der Ortszuordnung (Schritt 1d), Ketten ausgenommen."""

    def _index(self):
        from pipeline.ort_zuordnung import OrteIndex
        return OrteIndex.aus_zeilen([
            {"id": "o1", "name": "Filmmuseum Düsseldorf", "aktiv": True, "adresse": "Schulstraße 4, 40213 Düsseldorf"},
            {"id": "o2", "name": "Rewe Filiale", "aktiv": True, "adresse": "Königsallee 1, 40212 Düsseldorf"},
            {"id": "o3", "name": "Ohne Adresse", "aktiv": True, "adresse": None},
        ])

    def test_ort_id_liefert_adresse(self):
        idx = self._index()
        ort_adressen = ae.ort_adressen_bauen(idx)
        self.assertEqual(ort_adressen.get("o1"), "Schulstraße 4, 40213 Düsseldorf")
        self.assertNotIn("o3", ort_adressen)
        e = {"titel": "Kino", "datum": MORGEN, "ort": "Black Box", "ort_id": "o1",
             "quelle_name": "Rausgegangen", "quelle_url": "https://rausgegangen.de/events/x"}
        zaehler = ae.adressen_ergaenzen([e], {}, {}, ort_adressen)
        self.assertEqual(e["adresse"], "Schulstraße 4, 40213 Düsseldorf")
        self.assertEqual(zaehler["ort_id"], 1)

    def test_ohne_index_und_ketten_keine_adresse_ueber_ort_id(self):
        self.assertEqual(ae.ort_adressen_bauen(None), {})
        idx = self._index()
        idx.kette.add("o2")
        self.assertNotIn("o2", ae.ort_adressen_bauen(idx))


class FftTest(unittest.TestCase):
    """FFT sitzt im KAP1 (Konrad-Adenauer-Platz 1, 40210) – Stadtmitte, nicht Pempelfort (Befund 18.11.2026)."""

    def test_adresse_und_stadtteil(self):
        from pipeline.stadtteil_mapper import stadtteil_ermitteln
        from scraper.tier2.fft_duesseldorf import ADRESSE_KAP1, adresse_fuer
        self.assertEqual(adresse_fuer("FFT Düsseldorf – Bühne II"), ADRESSE_KAP1)
        self.assertIsNone(adresse_fuer("FFT JUTA, Düsseldorf"))
        self.assertEqual(stadtteil_ermitteln("FFT Düsseldorf – Bühne II", ADRESSE_KAP1, "FFT Düsseldorf"), "Stadtmitte")
        self.assertEqual(stadtteil_ermitteln("FFT Düsseldorf", None, "Rausgegangen"), "Stadtmitte")
