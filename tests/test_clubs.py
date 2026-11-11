"""Tests für den Club-Hub: Kandidatenfilter, Event-Abgleich, Belegprüfung und Club-Score
(python -m unittest tests.test_clubs)."""
import unittest
from datetime import date

from scraper.orte.clubs import ausgeschlossen, name_passt, unterart_regel
from scraper.orte.clubs_profil import club_score, event_orte, ort_schluessel, pruefen


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


if __name__ == "__main__":
    unittest.main()
