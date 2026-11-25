"""Tests für den Scraper Bürgerhäuser Düsseldorf (Programmseiten von duesseldorf.de, ohne Netz).
python -m unittest tests.test_buergerhaeuser"""
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from scraper.tier2 import buergerhaeuser as modul

FIXTURES = Path(__file__).parent / "fixtures"
HEUTE, ENDE = date(2026, 11, 25), date(2027, 3, 25)
PFLICHT = ("titel", "datum", "ort", "adresse", "kategorie", "quelle_name", "quelle_url", "status")
HAUS = {h["ort"]: h for h in modul.HAEUSER}
URL = "https://www.duesseldorf.de/buergerhaeuser/test"


def _lesen(name: str, ort: str, kategorie=None) -> list[dict]:
    html = (FIXTURES / f"buergerhaeuser_{name}.html").read_text(encoding="utf-8")
    return modul._termine_aus_html(html, HAUS[ort], URL, HEUTE, ENDE, kategorie)


def _nach_titel(events: list[dict]) -> dict:
    return {e["titel"]: e for e in events}


class GemeinsamTest(unittest.TestCase):
    def test_pflichtfelder_alle_seiten(self):
        for name, ort, kat in (
            ("reisholz", "Bürgerhaus Reisholz", None),
            ("bilk", "Bürgerhaus Bilk", None),
            ("salzmannbau", "Bürgerhaus Salzmannbau", None),
            ("kulturhaus_programm", "Kulturhaus Süd / Freizeitstätte Garath", None),
            ("kulturhaus_kindertheater", "Kulturhaus Süd / Freizeitstätte Garath", "family"),
        ):
            events = _lesen(name, ort, kat)
            self.assertGreaterEqual(len(events), 1, name)
            for e in events:
                for feld in PFLICHT:
                    self.assertTrue(e[feld], f"{name}: {feld} leer")
                self.assertEqual(e["ort"], ort)
                self.assertEqual(e["quelle_name"], "Bürgerhäuser Düsseldorf")
                self.assertTrue(e["quelle_url"].startswith("https://"))
                self.assertIsNone(e["beschreibung"])
                self.assertFalse(e["bild_generiert"])
                self.assertIn(e["kategorie"], ("musik", "kultur", "family", "community"))
                self.assertTrue(HEUTE.isoformat() <= e["datum"] <= ENDE.isoformat())

    def test_ortsnamen_wie_ortstabelle(self):
        self.assertEqual(
            [h["ort"] for h in modul.HAEUSER],
            ["Bürgerhaus Reisholz", "Bürgerhaus Bilk", "Bürgerhaus Salzmannbau",
             "Kulturhaus Süd / Freizeitstätte Garath"],
        )
        self.assertEqual(HAUS["Bürgerhaus Reisholz"]["adresse"], "Kappeler Str. 231, 40599 Düsseldorf")


class ReisholzTest(unittest.TestCase):
    """Vorlage A: Monatsprogramm, h3 = „Wochentag, Datum | Uhrzeit | Eintritt“."""

    def setUp(self):
        self.events = _lesen("reisholz", "Bürgerhaus Reisholz")
        self.titel = _nach_titel(self.events)

    def test_anzahl_ohne_kurse_und_doppelte(self):
        # 10 Einzeltermine + Vorschau 28.1.2027; Hip-Hop-Kurs/Kinderwerkstatt („Montags“, „Donnerstags“) und
        # „noch bis 18.12.“ (Ausstellung) fehlen, die JazzBar-/Kinder-Reiter wiederholen nur
        self.assertEqual(len(self.events), 11)
        alles = " ".join(self.titel)
        self.assertNotIn("Hip-Hop", alles)
        self.assertNotIn("Kinderwerkstatt", alles)

    def test_felder(self):
        e = self.titel["SPOTLIGHT: Frair, sidneyy, Horseshoe Woman"]
        self.assertEqual((e["datum"], e["uhrzeit"]), ("2026-11-26", "20:00"))  # Beginn, nicht Einlass 19.30
        self.assertEqual(e["preis"], "kostenlos")
        self.assertEqual(e["kategorie"], "musik")
        self.assertEqual(e["adresse"], "Kappeler Str. 231, 40599 Düsseldorf")
        revue = self.titel["22. Advents-Revue"]
        self.assertEqual((revue["uhrzeit"], revue["preis"]), ("15:30", "18 €"))
        self.assertEqual(self.titel["Café KULT: Bastian Semm – A Country Christmas"]["preis"], "10 € (ermäßigt 8 €)")
        self.assertIsNone(self.titel["SPOTLIGHT"]["uhrzeit"])  # Vorschau ohne Uhrzeit

    def test_kategorien(self):
        self.assertEqual(self.titel["Trödel- und Kindersachenmarkt: Die Schnäppchenjagd im Düsseldorfer Süden"]
                         ["kategorie"], "community")
        self.assertEqual(self.titel["Kindertheater: Theater con Cuore – Das Märchen vom Pfefferkuchenherz"]
                         ["kategorie"], "family")
        self.assertEqual(self.titel["JazzBar: Sabine Kühlich & Laia Genc Quintett"]["kategorie"], "musik")
        self.assertEqual(self.titel["Ausstellungseröffnung: Hans Binn – GR 34"]["kategorie"], "kultur")

    def test_fenster(self):
        spaet = modul._termine_aus_html((FIXTURES / "buergerhaeuser_reisholz.html").read_text(encoding="utf-8"),
                                        HAUS["Bürgerhaus Reisholz"], URL, date(2026, 12, 15), date(2026, 12, 18))
        self.assertEqual([e["datum"] for e in spaet], ["2026-12-16", "2026-12-17"])


class BilkSalzmannbauTest(unittest.TestCase):
    """Vorlage B: ein Akkordeon-Reiter je Veranstaltung, Termine als Textzeilen/Datumslisten."""

    def test_bilk(self):
        titel = _nach_titel(_lesen("bilk", "Bürgerhaus Bilk"))
        self.assertEqual(set(titel), {"Ü60-Party", "Bilker Buchstabensüppchen", "Psst! Die kurze Hörspielnacht"})
        party = titel["Ü60-Party"]
        self.assertEqual((party["datum"], party["uhrzeit"], party["preis"]), ("2026-11-29", "15:00", "5 €"))
        self.assertEqual(party["kategorie"], "community")
        self.assertEqual(titel["Bilker Buchstabensüppchen"]["preis"], "kostenlos")
        self.assertEqual(titel["Psst! Die kurze Hörspielnacht"]["kategorie"], "kultur")

    def test_salzmannbau_datumslisten(self):
        events = _lesen("salzmannbau", "Bürgerhaus Salzmannbau")
        daten = sorted(e["datum"] for e in events if e["titel"] == "Kleidertauschparty")
        self.assertEqual(daten, ["2026-11-27", "2027-03-05"])  # „5.3., 11.6. und 26.11.2027“ → nur 5.3. im Fenster
        zeiten = {e["datum"]: e["uhrzeit"] for e in events if e["titel"] == "Kleidertauschparty"}
        self.assertEqual(zeiten, {"2026-11-27": "16:30", "2027-03-05": "14:00"})
        labor = [e for e in events if e["titel"] == "Stadtteil-Labor"]
        self.assertEqual(len(labor), 4)
        self.assertTrue(all(e["uhrzeit"] == "17:30" for e in labor))  # Zeit aus dem Reihentext

    def test_salzmannbau_titel_preis_kategorie(self):
        titel = _nach_titel(_lesen("salzmannbau", "Bürgerhaus Salzmannbau"))
        soul = titel["Aktiv 60 plus: American Classic Soul Show – Rodney RCM Moore"]
        self.assertEqual((soul["datum"], soul["uhrzeit"], soul["kategorie"]), ("2026-12-02", "15:00", "musik"))
        self.assertEqual(titel["Aktiv 60 plus"]["kategorie"], "community")
        self.assertEqual(titel["Young Stage"]["preis"], "kostenlos")
        self.assertEqual(titel["Young Stage"]["uhrzeit"], "19:30")
        frueh = titel["Familienfrühstück: Michael Carleton & Melanie"]
        self.assertEqual((frueh["uhrzeit"], frueh["kategorie"]), ("10:30", "family"))
        self.assertTrue(frueh["preis"].startswith("Erwachsene: 10 €"))
        film = titel["Film zum internationalen Tag Gegen Gewalt an Frauen"]
        self.assertEqual((film["datum"], film["uhrzeit"], film["preis"], film["kategorie"]),
                         ("2026-12-09", "17:45", "kostenlos", "kultur"))


class KulturhausSuedTest(unittest.TestCase):
    """Vorlage C: h3 = Titel, <li> = „Wochentag, Datum | Uhrzeit | Preis“."""

    def setUp(self):
        self.events = _lesen("kulturhaus_programm", "Kulturhaus Süd / Freizeitstätte Garath")
        self.titel = _nach_titel(self.events)

    def test_ohne_wochentermine_sitzungen_kurse(self):
        alles = " ".join(self.titel)
        for weg in ("Kinderchor", "Südsinger", "Sprechstunde", "Sitzung", "Töpfern", "Trommelkurse", "just B Fit"):
            self.assertNotIn(weg, alles)
        self.assertEqual(len(self.events), 12)

    def test_felder_und_ticket(self):
        e = self.titel["Robert Griess: Natürliche Intelligenz – letzter Versuch!"]
        self.assertEqual((e["datum"], e["uhrzeit"], e["preis"], e["kategorie"]), ("2026-11-25", "20:00", "19 €", "kultur"))
        self.assertTrue(e["ticket_url"].startswith("https://www.reservix.de/"))
        self.assertNotEqual(e["ticket_url"], e["quelle_url"])
        self.assertIsNone(self.titel["Markus Barth: Pures Gold"]["ticket_url"])
        moussa = self.titel["Moussa Diallo & Sapali: Winterzauber trifft Trommelzauber"]
        self.assertEqual(moussa["uhrzeit"], "20:00")  # nicht Einlass 18 Uhr
        self.assertEqual(self.titel["Sonnenrad Sessions: Radio Garath"]["preis"], "kostenlos")
        self.assertEqual(self.titel["One Of These: A Tribute to Pink Floyd"]["kategorie"], "musik")
        self.assertEqual(self.titel["Wildes Holz: Alle Jahre wilder"]["preis"], "26 € (AUSVERKAUFT)")  # bleibt

    def test_kindertheater_unterzeilen(self):
        kinder = _lesen("kulturhaus_kindertheater", "Kulturhaus Süd / Freizeitstätte Garath", "family")
        titel = _nach_titel(kinder)
        self.assertIn("Das Bremer Figurentheater: Hase und Igel", titel)
        self.assertEqual(titel["Das Bremer Figurentheater: Hase und Igel"]["uhrzeit"], "11:00")
        self.assertEqual(titel["Das Bremer Figurentheater: Die Bremer Stadtmusikanten"]["uhrzeit"], "15:00")
        self.assertTrue(all(e["kategorie"] == "family" for e in kinder))

    def test_doppelte_ueber_seiten(self):
        kinder = _lesen("kulturhaus_kindertheater", "Kulturhaus Süd / Freizeitstätte Garath", "family")
        gesamt = modul._ohne_doppelte(self.events + kinder)
        am_15 = [e for e in gesamt if e["datum"] == "2026-12-15"]
        self.assertEqual(len(am_15), 1)  # „Kindertheater | Theater con Cuore: …“ = „Theater con Cuore: …“
        self.assertEqual(len(gesamt), len(self.events) + len(kinder) - 1)


class HelferTest(unittest.TestCase):
    def test_uhrzeit(self):
        self.assertEqual(modul._uhrzeit("20 bis 22 Uhr"), "20:00")
        self.assertEqual(modul._uhrzeit("Einlass: 19.30 Uhr | 20 Uhr"), "20:00")
        self.assertEqual(modul._uhrzeit("15.30 Uhr (Einlass 15.15 Uhr)"), "15:30")
        self.assertEqual(modul._uhrzeit("17 und 20 Uhr"), "17:00")
        self.assertIsNone(modul._uhrzeit("ab 4 Jahren"))

    def test_preis(self):
        self.assertEqual(modul._preis("Eintritt frei"), "kostenlos")
        self.assertEqual(modul._preis("Eintritt: 3,50/3 Euro"), "3,50/3 €")
        self.assertIsNone(modul._preis("ab 4 Jahren"))

    def test_datumsliste(self):
        daten, _ = modul._daten_aus_zeile("5.3., 11.6. und 26.11.2027, 14 bis 18 Uhr")
        self.assertEqual([d.isoformat() for d in daten], ["2027-03-05", "2027-06-11", "2027-11-26"])


class ScrapeTest(unittest.TestCase):
    def test_scrape_ohne_netz(self):
        seiten = {
            "reisholz/veranstaltungen": "reisholz",
            "bilk-stadtteilzentrum/veranstaltungen": "bilk",
            "salzmannbau/veranstaltungen": "salzmannbau",
            "kulturhaus-sued/programm": "kulturhaus_programm",
            "kulturhaus-sued/kindertheater": "kulturhaus_kindertheater",
        }
        abgerufen = []

        def falsch_abrufen(url, logger=None, wartezeit=2.0):
            abgerufen.append((url, wartezeit))
            pfad = url.replace(modul.BASIS, "")
            return (FIXTURES / f"buergerhaeuser_{seiten[pfad]}.html").read_text(encoding="utf-8")

        class Heute(date):
            @classmethod
            def today(cls):
                return HEUTE

        with mock.patch.object(modul, "seite_abrufen", falsch_abrufen), \
                mock.patch.object(modul, "vorschau_ende", lambda q, h: ENDE), \
                mock.patch.object(modul, "date", Heute):
            events = modul.scrape()
        self.assertEqual(len(abgerufen), 5)
        self.assertTrue(all(w >= 2 for _, w in abgerufen))
        self.assertTrue(all("?" not in u for u, _ in abgerufen))  # robots sperrt ?tx_* / ?cHash*
        self.assertEqual(len(events), 11 + 3 + 16 + 12 + 5 - 1)

    def test_scrape_wirft_nie(self):
        with mock.patch.object(modul, "seite_abrufen", side_effect=RuntimeError("kaputt")):
            self.assertEqual(modul.scrape(), [])


if __name__ == "__main__":
    unittest.main()
