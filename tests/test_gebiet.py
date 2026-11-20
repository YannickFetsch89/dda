"""Tests für den Gebietsfilter (python -m unittest tests.test_gebiet). Plan Locations E3, 18.11.2026."""
import unittest

from pipeline.gebiet import gebiet_filtern, grund_ausserhalb
from scraper.tier1.meetup import adresse_bauen


def ev(ort, adresse=None, quelle="Test"):
    return {"titel": "x", "ort": ort, "adresse": adresse, "quelle_name": quelle}


class GebietTest(unittest.TestCase):
    def test_draussen(self):
        for e in [
            ev("Galerie für Zeitgenössische Kunst", "Galerie für Zeitgenössische Kunst, Leipzig"),
            ev("Theater Duisburg", "Heinrich-Heine-Allee 16a, 40213 Düsseldorf"),  # Ort nennt Duisburg
            ev("Opernplatz, Duisburg"),
            ev("Szene 10", "Szene 10, Essen"),
            ev("Herbrand's", "Herbrand's, Köln"),
            ev("Kölner Straße 11", "Kölner Str. 11, 47805 Krefeld, Germany"),
            ev("Waldmeister", "Holbeinstr.6, 42719 Solingen"),
            ev("Planetarium Erkrath"),
            ev("Neanderthal Museum"),
            ev("Café Aroma", "Dorfstraße 34, Meerbusch"),
            # Nachtrag 18.11.2026 (Kandidatenliste)
            ev("Grugahalle Essen"),
            ev("Theater Essen-Süd"),
            ev("LUTZ, theaterhagen"),
            ev("Wuppertaler Miniaturland"),
            ev("Stadthalle Kleve"),
            ev("Theater Gütersloh - Haupteingang"),
        ]:
            with self.subTest(ort=e["ort"]):
                self.assertIsNotNone(grund_ausserhalb(e))

    def test_drin(self):
        for e in [
            ev("Kunstpalast Düsseldorf", "Ehrenhof 4-5, 40479 Düsseldorf"),
            ev("Zeughaus Neuss", "Markt 42, 41460 Neuss"),
            ev("Stadthalle Ratingen", "Schützenstraße 1, 40878 Ratingen"),
            ev("Bar an der Kölner Straße", "Kölner Str. 200, 40227 Düsseldorf"),
            ev("Duisburger Straße 10", "Duisburger Str. 10, 40477 Düsseldorf"),
            ev("KD Köln-Düsseldorfer Anleger Burgplatz", "Rheinwerft, 40213 Düsseldorf"),
            ev("Gemeinsam Essen im Viertel"),
            ev("zakk – Halle", "Fichtenstraße 40, 40233 Düsseldorf"),
            ev("Mitsubishi Electric Halle", "Siegburger Straße 15, 40591 Düsseldorf"),
            ev("Neusser Tor"),
            ev("Meetup Düsseldorf (Online)"),
            ev("Düsseldorf"),
            ev("Theater an der Luegallee"),
            ev("Gare Du Neuss"),
            ev("Das Rheinische Landestheater"),
        ]:
            with self.subTest(ort=e["ort"]):
                self.assertIsNone(grund_ausserhalb(e))

    def test_filtern(self):
        bleiben = gebiet_filtern([ev("Kunsthalle Düsseldorf"), ev("FZW", "FZW, Dortmund")])
        self.assertEqual([e["ort"] for e in bleiben], ["Kunsthalle Düsseldorf"])


class GebietNachtragTest(unittest.TestCase):
    """Nachtrag 19.11.2026, Plan docs/plan-locations-2026-11-18.md, 3.16."""

    def test_draussen(self):
        for ort, adresse in [("Stadthalle Mülheim", ""), ("Theater Mülheim", ""), ("Kirche", "Hochdahl"),
                             ("Kirche", "Büderich"), ("Bar", "Osterath"), ("Mayersche Essen", "Mayersche Essen"),
                             ("Lufre Event & Gastronomie", "Lufre Event & Gastronomie, Kamp-Lintfort"),
                             ("Bürgerhaus Telgte", "Bürgerhaus Telgte"),
                             ("Grefrather EisSport & EventPark", "Grefrather EisSport & EventPark"),
                             ("Erlebnisbauernhof Gertrudenhof", "")]:
            with self.subTest(ort=ort, adresse=adresse):
                self.assertIsNotNone(grund_ausserhalb({"ort": ort, "adresse": adresse}))

    def test_drin(self):
        for ort, adresse in [("Bar", "Mülheimer Straße 5, 40221 Düsseldorf"), ("Unterbacher See", "Unterbach"),
                             ("Kirche", "Hamm"), ("Bar", "Berliner Allee 52, 40212 Düsseldorf"),
                             ("Bar", "Erkrather Straße 1, 40233 Düsseldorf"), ("Bar", "Kölner Straße 1, 40227 Düsseldorf"),
                             ("Bar", "Duisburger Straße 1, 40477 Düsseldorf"), ("Bar", "Neusser Straße 1, 40219 Düsseldorf")]:
            with self.subTest(ort=ort, adresse=adresse):
                self.assertIsNone(grund_ausserhalb({"ort": ort, "adresse": adresse}))


class GebietTitelTest(unittest.TestCase):
    """Nachtrag 20.11.2026: Stadt im Titel und „… Köln“ am Ende des Orts (Befund Rausgegangen/PRINZ.de/AllEvents)."""

    def t(self, titel, ort, adresse=None):
        return grund_ausserhalb({"titel": titel, "ort": ort, "adresse": adresse})

    def test_draussen(self):
        for titel, ort, adresse in [
            ("Westlife European tour at 25", "Lanxess Arena Köln", None),
            ("Leipziger Weihnachtsmarkt 2026", "Leipziger Marktplatz", "Leipziger Marktplatz"),
            ("House of Banksy Hanau | Zeitfensterticket", "Stadthof Hanau", "Stadthof Hanau"),
            ("Duisburg im Winterzauber – Deine Weihnachtsschatzsuche", "Königstraße", None),
            ("AI Coding Hackathon November 2026 Köln", "STARTPLATZ", None),
            ("Lesung in Wuppertal", "Buchhandlung", None),
        ]:
            with self.subTest(titel=titel):
                self.assertIsNotNone(self.t(titel, ort, adresse))

    def test_drin(self):
        for titel, ort, adresse in [
            ("Fortuna Düsseldorf – 1. FC Köln", "Merkur Spiel-Arena", None),
            ("Fortuna Düsseldorf – Eintracht Frankfurt", "Merkur Spiel-Arena", None),
            ("DEG – Kölner Haie", "PSD Bank Dome", "Theodorstraße 281, 40472 Düsseldorf"),
            ("Düsseldorf im Winterzauber – Deine Weihnachtsschatzsuche", "Altstadt Düsseldorf", None),
            ("Gemeinsam Essen", "Café", None),
            ("Kölsch-Tasting", "Brauerei", None),
            ("Berliner Abend mit Currywurst", "Bar", "Berliner Allee 52, 40212 Düsseldorf"),
            ("Konzert: Berlin Calling", "zakk", "Fichtenstraße 40, 40233 Düsseldorf"),
            ("Tour 2026 – Köln", "Mitsubishi Electric Halle", "Siegburger Straße 15, 40591 Düsseldorf"),
            ("Rundfahrt", "KD Köln-Düsseldorfer", None),
        ]:
            with self.subTest(titel=titel):
                self.assertIsNone(self.t(titel, ort, adresse))


class MeetupAdresseTest(unittest.TestCase):
    def test_platzhalter_plz(self):
        self.assertEqual(adresse_bauen("Franklinstraße 5, 40479", "meetup9", "Düsseldorf"), "Franklinstraße 5, 40479 Düsseldorf")
        self.assertEqual(adresse_bauen("Steinstr. 1", "meetup9", "Düsseldorf"), "Steinstr. 1, Düsseldorf")
        self.assertEqual(adresse_bauen("Hansaallee 190", "40547", "Düsseldorf"), "Hansaallee 190, 40547 Düsseldorf")
        self.assertNotIn("meetup", adresse_bauen("düsseldorferstr.81-85", "meetup162", "meerbusch"))
        self.assertIsNone(adresse_bauen(None, None, None))


if __name__ == "__main__":
    unittest.main()
