"""Tests für den Club-Hub: Kandidatenfilter, Event-Abgleich, Belegprüfung und Club-Score
(python -m unittest tests.test_clubs)."""
import unittest
from datetime import date

from scraper.orte.clubs import ausgeschlossen, name_passt, unterart_regel
from scraper.orte.clubs_profil import (anzeige_belegt, club_score, event_orte, link_pruefen, ort_schluessel, pruefen,
                                       umtypen_erlaubt)


def place(name, primaer="night_club", adresse="Ronsdorfer Str. 134, 40233 Düsseldorf, Deutschland", **mehr):
    return {"displayName": {"text": name}, "primaryType": primaer, "types": [primaer], "formattedAddress": adresse,
            "businessStatus": "OPERATIONAL", **mehr}


class KandidatenTest(unittest.TestCase):
    def test_ausschluss(self):
        self.assertIsNone(ausgeschlossen(place("Ampere")))
        self.assertIsNotNone(ausgeschlossen(place("Palmera Düsseldorf: Erotikclub, Bordell, Nightclub")))
        self.assertIsNotNone(ausgeschlossen(place("Farell Lounge Swingerclub")))
        self.assertIsNotNone(ausgeschlossen(place("Atash Shisha Bar & Lounge", "hookah_bar")))
        self.assertIsNotNone(ausgeschlossen(place("Mikroport", adresse="Dießemer Str. 22, 47799 Krefeld")))
        self.assertIsNotNone(ausgeschlossen(place("Cube", businessStatus="CLOSED_PERMANENTLY")))
        # Vereine bleiben (R25 heißt bei Google „Kultur-Schlachthof e.V.“)
        self.assertIsNone(ausgeschlossen(place("Kultur-Schlachthof e.V.", "live_music_venue",
                                               adresse="Rather Str. 25, 40476 Düsseldorf-Stadtbezirk 1")))

    def test_name_passt(self):
        self.assertTrue(name_passt("Salon des Amateurs Düsseldorf", place("Salon des Amateurs")))
        self.assertTrue(name_passt("Kulturschlachthof Düsseldorf", place("Kultur-Schlachthof e.V.")))
        self.assertFalse(name_passt("Kassette Club Düsseldorf", place("Kö Club")))

    def test_unterart_regel(self):
        self.assertEqual(unterart_regel(place("X")), "club")
        self.assertEqual(unterart_regel(place("X", "event_venue")), "kulturhaus")
        self.assertEqual(unterart_regel(place("X", "bar")), "partylocation")


class EventAbgleichTest(unittest.TestCase):
    ORTE = {"Salon des Amateurs", "zakk – Halle", "zakk – Club", "Rudas Studios Düsseldorf", "Kunsthalle Düsseldorf",
            "Tor 3", "Torhaus Kaiserswerth", "Kulturschlachthof R25", "R25 Kulturschlachthof"}

    def test_schluessel(self):
        self.assertEqual(ort_schluessel("Rudas Studios Club"), "rudasstudios")
        self.assertEqual(ort_schluessel("Kö Club - Düsseldorf"), "koeclub")  # zu kurz → ganzer Name

    def test_event_orte(self):
        self.assertEqual(event_orte("Salon des Amateurs", self.ORTE), ["Salon des Amateurs"])
        self.assertEqual(event_orte("Rudas Studios Club", self.ORTE), ["Rudas Studios Düsseldorf"])
        self.assertEqual(event_orte("Zentrum für Aktion, Kultur und Kommunikation", self.ORTE), ["zakk – Club", "zakk – Halle"])
        self.assertEqual(event_orte("Kultur-Schlachthof e.V.", self.ORTE), ["Kulturschlachthof R25", "R25 Kulturschlachthof"])
        self.assertEqual(event_orte("Tor 3", self.ORTE), ["Tor 3"])


QUELLEN = [
    ("https://club.example/", "Jeden Freitag: TECHNO NIGHT mit Residents. Eintritt 12 Euro, Abendkasse. Samstags House & Disco."),
    ("Google", "Super Laune, tolle Musik, die Türsteher waren freundlich."),
]


def ki(**mehr):
    basis = {
        "passt": True, "passt_grund": "Club", "unterart": "club",
        "genres": [{"wert": "Techno", "anteil": "haupt", "zitat": "Jeden Freitag: TECHNO NIGHT mit Residents"}],
        "formate": [], "zusatz_events": [],
        "fakten": {k: {"text": "", "zitat": ""} for k in ("oeffnung", "eintritt", "tuer", "alter", "kapazitaet", "floors")},
        "eintritt_min_euro": "", "eintritt_max_euro": "", "dresscode": "unbekannt", "dresscode_zitat": "",
        "publikum": [], "ausstattung": [], "instagram": "", "resident_advisor": "", "beschreibung": "", "highlight": "",
    }
    basis.update(mehr)
    return basis


class BelegTest(unittest.TestCase):
    def test_genre_mit_beleg(self):
        profil, verworfen = pruefen(ki(), QUELLEN)
        self.assertEqual([g["wert"] for g in profil["genres"]], ["Techno"])
        self.assertEqual(profil["genres"][0]["quelle"], "https://club.example/")
        self.assertEqual(verworfen, [])

    def test_genre_ohne_stichwort_oder_zitat(self):
        profil, verworfen = pruefen(ki(genres=[
            {"wert": "Hip-Hop", "anteil": "haupt", "zitat": "Super Laune, tolle Musik"},       # Stichwort fehlt
            {"wert": "House", "anteil": "neben", "zitat": "Samstags House & Techno-Marathon"},  # nicht im Text
        ]), QUELLEN)
        self.assertEqual(profil["genres"], [])
        self.assertEqual(len(verworfen), 2)

    def test_eintritt_nur_mit_zahl_im_zitat(self):
        fakten = ki()["fakten"]
        fakten["eintritt"] = {"text": "12 €", "zitat": "Eintritt 12 Euro, Abendkasse"}
        profil, _ = pruefen(ki(fakten=fakten, eintritt_min_euro="12", eintritt_max_euro="20"), QUELLEN)
        self.assertEqual(profil["eintritt"], {"min": 12.0})

    def test_dresscode_ohne_beleg_unbekannt(self):
        profil, verworfen = pruefen(ki(dresscode="schick", dresscode_zitat="Hemdpflicht am Einlass"), QUELLEN)
        self.assertEqual(profil["dresscode"], "unbekannt")
        self.assertTrue(any("Dresscode" in v for v in verworfen))

    def test_links_nur_aus_quellen(self):
        profil, _ = pruefen(ki(instagram="https://instagram.com/erfunden", resident_advisor="https://ra.co/clubs/1"), QUELLEN)
        self.assertIsNone(profil["instagram"])
        self.assertIsNone(profil["resident_advisor"])


class ScoreTest(unittest.TestCase):
    HEUTE = date(2026, 11, 11)

    def events(self, n, quelle="zakk"):
        return [{"datum": f"2026-11-{(i % 28) + 1:02d}", "kategorie": "nightlife", "quelle_name": quelle} for i in range(n)]

    def test_aktiver_szeneclub_hoch(self):
        ort = {"google_rating": 4.4, "google_bewertungen_anzahl": 500}
        profil = {"genres": [{"wert": "Techno", "anteil": "haupt"}], "formate": [{}, {}, {}], "zusatz_events": [{}, {}],
                  "fakten": {"oeffnung": {}, "eintritt": {}}, "publikum": ["Underground"], "resident_advisor": None,
                  "unterart": "club"}
        s = club_score(ort, profil, self.events(12, "Resident Advisor"), self.HEUTE)
        self.assertGreaterEqual(s["gesamt"], 8)

    def test_ohne_programm_niedrig(self):
        ort = {"google_rating": 3.1, "google_bewertungen_anzahl": 300}
        profil = {"genres": [], "formate": [], "zusatz_events": [], "fakten": {}, "publikum": [], "unterart": "club"}
        s = club_score(ort, profil, [], self.HEUTE)
        self.assertLessEqual(s["gesamt"], 3)

    def test_google_schwach_gewichtet(self):
        # Gleiches Programm/Profil: 1,8 vs. 4,6 Sterne verschiebt den Score um höchstens 2 Punkte
        profil = {"genres": [{"wert": "Techno", "anteil": "haupt"}], "formate": [{}, {}], "zusatz_events": [],
                  "fakten": {"oeffnung": {}}, "publikum": [], "unterart": "club"}
        schlecht = club_score({"google_rating": 1.8, "google_bewertungen_anzahl": 800}, profil, self.events(8), self.HEUTE)
        gut = club_score({"google_rating": 4.6, "google_bewertungen_anzahl": 800}, profil, self.events(8), self.HEUTE)
        self.assertLessEqual(gut["gesamt"] - schlecht["gesamt"], 2)


class CursorBefundeTest(unittest.TestCase):
    """Fälle aus dem Cursor-Review vom 11.11.2026."""

    def test_anzeige_passt_zum_zitat(self):
        tuer = [("https://club.example/faq", "Die Tür ist streng."),
                ("https://club.example/programm", "Jeden Samstag Ü30-Party ab 22 Uhr.")]
        fakten = ki()["fakten"]
        fakten["eintritt"] = {"text": "meist 5 €", "zitat": "Die Tür ist streng."}
        fakten["tuer"] = {"text": "Strenge Tür", "zitat": "Die Tür ist streng."}
        profil, verworfen = pruefen(ki(genres=[], fakten=fakten, formate=[
            {"name": "Ü30", "rhythmus": "jeden Samstag", "musik": "Charts", "zitat": "Die Tür ist streng."},
            {"name": "Ü30-Party", "rhythmus": "jeden Samstag", "musik": "Techno",
             "zitat": "Jeden Samstag Ü30-Party ab 22 Uhr."},
        ]), tuer)
        self.assertNotIn("eintritt", profil["fakten"])             # „5“ steht nicht im Zitat
        self.assertIn("tuer", profil["fakten"])                    # „streng“ steht im Zitat
        self.assertEqual([f["name"] for f in profil["formate"]], ["Ü30-Party"])
        self.assertEqual(profil["formate"][0]["rhythmus"], "jeden Samstag")
        self.assertEqual(profil["formate"][0]["musik"], "")       # „Techno“ ist nicht belegt → leer
        self.assertTrue(any("Name steht nicht beim Zitat" in v for v in verworfen))

    def test_reihenname_als_ueberschrift_ueber_dem_zitat(self):
        q = [("https://zakk.example/", "Der Rockclub\nFinest Alternative Rock mit DJ MajorTom im zakk Club.")]
        profil, _ = pruefen(ki(genres=[], formate=[
            {"name": "Der Rockclub", "rhythmus": "monatlich", "musik": "Alternative Rock",
             "zitat": "Finest Alternative Rock mit DJ MajorTom im zakk Club."}]), q)
        self.assertEqual([f["name"] for f in profil["formate"]], ["Der Rockclub"])
        self.assertEqual(profil["formate"][0]["musik"], "Alternative Rock")
        self.assertEqual(profil["formate"][0]["rhythmus"], "")   # „monatlich“ steht nirgends

    def test_anzeige_belegt(self):
        self.assertTrue(anzeige_belegt("Fr und Sa ab 22 Uhr", "FREITAG AB 22 UHR SAMSTAG AB 22 UHR"))
        self.assertFalse(anzeige_belegt("meist 5 €", "Die Tür ist streng."))
        self.assertFalse(anzeige_belegt("Kleiner Raum", "The Salon is a small, simple space"))

    def test_event_orte_ganze_woerter(self):
        self.assertEqual(event_orte("Graf Eventlocation", {"Grafenberg"}), [])
        self.assertEqual(event_orte("The Gate", {"Southgate"}), [])
        self.assertEqual(event_orte("Pitcher", {"Pitcher, nicht im Freien"}), ["Pitcher, nicht im Freien"])
        self.assertEqual(event_orte("zakk", {"zakk – nicht im zakk", "zakk – Halle",
                                             "HHU, am Finaltag im zakk"}), ["zakk – Halle"])
        self.assertEqual(event_orte("The Eight", {"The Eight - Eventlocation & Club in Düsseldorf"}),
                         ["The Eight - Eventlocation & Club in Düsseldorf"])

    def test_umtypen_nur_mit_freigabe_und_score(self):
        basis = {"typ": "restaurant", "aktiv": False,
                 "extras": {"club": {"passt": True}, "club_score": {"gesamt": 8}, "club_freigegeben": "2026-11-11"}}
        self.assertTrue(umtypen_erlaubt(basis))
        self.assertFalse(umtypen_erlaubt({**basis, "aktiv": True}))   # aktiv im Haupt-Hub → nie
        ohne = {**basis, "extras": {**basis["extras"], "club_freigegeben": None}}
        self.assertFalse(umtypen_erlaubt(ohne))
        schwach = {**basis, "extras": {**basis["extras"], "club_score": {"gesamt": 5}}}
        self.assertFalse(umtypen_erlaubt(schwach))

    def test_links(self):
        quelle = "Folgt uns!\nLinks: https://www.instagram.com/echterclub/ https://ra.co/clubs/15478"
        # mit oder ohne „www“ ist dasselbe Profil
        self.assertEqual(link_pruefen("https://instagram.com/echterclub", "instagram", quelle), "https://instagram.com/echterclub")
        self.assertEqual(link_pruefen("https://www.instagram.com/echterclub/", "instagram", quelle),
                         "https://www.instagram.com/echterclub/")
        self.assertIsNone(link_pruefen("https://www.instagram.com/echterclub?next=https://example.org/", "instagram", quelle))
        self.assertIsNone(link_pruefen("https://www.instagram.com/echter", "instagram", quelle))  # nur Präfix
        self.assertEqual(link_pruefen("http://ra.co/clubs/15478", "resident_advisor", quelle), "https://ra.co/clubs/15478")

    def test_genre_stichworte_eng(self):
        q = [("https://club.example/", "Warehouse-Party im Keller. Open from 23 bis 5 Uhr. Technology Talk.")]
        profil, _ = pruefen(ki(genres=[
            {"wert": "House", "anteil": "haupt", "zitat": "Warehouse-Party im Keller"},
            {"wert": "Mixed", "anteil": "neben", "zitat": "Open from 23 bis 5 Uhr"},
            {"wert": "Techno", "anteil": "neben", "zitat": "Technology Talk"},
        ]), q)
        self.assertEqual(profil["genres"], [])


class CursorDritteRundeTest(unittest.TestCase):
    """Fälle aus der dritten Cursor-Runde vom 11.11.2026."""

    def _formate(self, text, zitat, name, musik=""):
        profil, _ = pruefen(ki(genres=[], formate=[
            {"name": name, "rhythmus": "jeden Samstag", "musik": musik, "zitat": zitat}]), [("https://x.example/", text)])
        return profil["formate"]

    def test_satz_davor_belegt_keinen_reihennamen(self):
        self.assertEqual(self._formate("Samstags Ü30 Party mit Charts. Die Tür ist streng.", "Die Tür ist streng.", "Ü30"), [])

    def test_programmzeile_darueber_belegt_keinen_reihennamen(self):
        text = "Fr 22 Uhr Techno Bunker\nDie Tür ist streng."
        self.assertEqual(self._formate(text, "Die Tür ist streng.", "Techno Bunker", "Techno"), [])

    def test_ueberschrift_darueber_belegt_den_namen(self):
        text = "Techno Bunker\nJeden Samstag harter Techno bis zum Morgen."
        f = self._formate(text, "Jeden Samstag harter Techno bis zum Morgen.", "Techno Bunker", "Techno")
        self.assertEqual([x["name"] for x in f], ["Techno Bunker"])

    def test_nicht_im_sondern_im_club(self):
        ort = "Konzert – nicht im Saal, sondern im Pitcher Club"
        self.assertEqual(event_orte("Pitcher", {ort}), [ort])
        self.assertEqual(event_orte("Pitcher", {"Lesung – nicht im alten großen Pitcher"}), [])

    def test_stichworte_plural_und_zusammensetzungen(self):
        q = [("https://x.example/", "Flohmärkte und Designmärkte im Hof. Masterclass für DJs. Punkrockabend im Keller.")]
        profil, _ = pruefen(ki(
            genres=[{"wert": "Metal/Punk", "anteil": "neben", "zitat": "Punkrockabend im Keller."}],
            zusatz_events=[{"art": "Flohmarkt/Märkte", "beispiel": "", "zitat": "Flohmärkte und Designmärkte im Hof."},
                           {"art": "Workshops/Kurse", "beispiel": "", "zitat": "Masterclass für DJs."}],
        ), q)
        self.assertEqual([g["wert"] for g in profil["genres"]], ["Metal/Punk"])
        self.assertEqual([z["art"] for z in profil["zusatz_events"]], ["Flohmarkt/Märkte", "Workshops/Kurse"])


class CursorNachreviewTest(unittest.TestCase):
    """Fälle aus dem Cursor-Nachreview vom 11.11.2026."""

    def test_eine_quelle_nachbarsaetze_belegen_nichts(self):
        q = [("https://club.example/", "Freitags Eintritt 5 Euro ab 23 Uhr. Die Tür ist streng. Samstags Ü30 Party mit Charts.")]
        fakten = ki()["fakten"]
        fakten["eintritt"] = {"text": "meist 5 €", "zitat": "Die Tür ist streng."}
        profil, _ = pruefen(ki(genres=[], fakten=fakten, formate=[
            {"name": "Ü30", "rhythmus": "jeden Samstag", "musik": "Charts", "zitat": "Die Tür ist streng."},
            {"name": "Charts Party", "rhythmus": "", "musik": "", "zitat": "Die Tür ist streng."},
        ]), q)
        self.assertNotIn("eintritt", profil["fakten"])
        self.assertEqual(profil["formate"], [])

    def test_stichworte_ohne_nachbarwoerter(self):
        q = [("https://club.example/", "Auf den Punkt gebracht: Discoabend im Kulturzentrum mit Partys. Kein Dresscode, "
                                       "classic hits. Supermarkt um die Ecke.")]
        zitat = "Auf den Punkt gebracht: Discoabend im Kulturzentrum mit Partys."
        rest = "Kein Dresscode, classic hits. Supermarkt um die Ecke."
        profil, _ = pruefen(ki(
            genres=[{"wert": "Metal/Punk", "anteil": "neben", "zitat": zitat},
                    {"wert": "Disco/Funk/Soul", "anteil": "haupt", "zitat": zitat}],
            publikum=[{"wert": "Szene/Kenner", "zitat": zitat}, {"wert": "Schick", "zitat": rest}],
            zusatz_events=[{"art": "Workshops/Kurse", "beispiel": "", "zitat": rest},
                           {"art": "Flohmarkt/Märkte", "beispiel": "", "zitat": rest}],
        ), q)
        self.assertEqual([g["wert"] for g in profil["genres"]], ["Disco/Funk/Soul"])
        self.assertEqual(profil["publikum"], [])
        self.assertEqual(profil["zusatz_events"], [])

    def test_nicht_im_mehrere_woerter(self):
        self.assertEqual(event_orte("Pitcher", {"Lesung – nicht im alten großen Pitcher"}), [])
        self.assertEqual(event_orte("Pitcher", {"Pitcher, nicht im Freien"}), ["Pitcher, nicht im Freien"])

    def test_sonstiges_zaehlt_nicht(self):
        ort = {"google_rating": 4.0, "google_bewertungen_anzahl": 50}
        basis = {"genres": [], "formate": [], "fakten": {}, "publikum": [], "unterart": "club"}
        ohne = club_score(ort, {**basis, "zusatz_events": []}, [], date(2026, 11, 11))
        mit = club_score(ort, {**basis, "zusatz_events": [{"art": "Sonstiges"}]}, [], date(2026, 11, 11))
        self.assertEqual(ohne, mit)


if __name__ == "__main__":
    unittest.main()
