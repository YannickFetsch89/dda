"""Tests: Dubletten über Quellen hinweg (Einlass/Beginn, fehlende Uhrzeit) und Absage-Zusätze im Titel
(python -m unittest tests.test_dedup_toleranz)."""
import unittest

from database.client import _anreicherungs_update_bauen
from pipeline.deduplication import (
    TITEL_STATUS_FELD,
    aehnliches_event,
    bester_treffer,
    deduplizieren,
    ist_aggregator,
    titel_status_bereinigen,
)


def ev(titel, ort, uhrzeit="20:00", quelle="Rausgegangen", datum="2026-11-12", **mehr):
    return {"titel": titel, "ort": ort, "datum": datum, "uhrzeit": uhrzeit, "quelle_name": quelle, **mehr}


class QuellenToleranzTest(unittest.TestCase):
    def test_einlass_und_beginn_aus_zwei_quellen(self):
        # Beispiele aus der Datenbank vom 11.11.2026
        self.assertTrue(aehnliches_event(ev("Shinedown", "Mitsubishi Electric HALLE", "19:30", "d-live"),
                                         ev("SHINEDOWN", "Mitsubishi Electric Halle", "18:30")))
        self.assertTrue(aehnliches_event(ev("KORSAKOW", "Pitcher Rock HQ", "20:00", "Pitcher Rock HQ"),
                                         ev("KORSAKOW", "Pitcher", "18:00")))
        self.assertTrue(aehnliches_event(ev("D.Now: Genevieve O’Driscoll", "Jazz-Schmiede Düsseldorf", "20:30", "Jazz-Schmiede Düsseldorf"),
                                         ev("D.Now: Genevieve O’Driscoll", "Jazz Schmiede", "20:30")))

    def test_bandname_im_langen_titel(self):
        self.assertTrue(aehnliches_event(
            ev("Shinedown", "Mitsubishi Electric HALLE", "19:30", "d-live"),
            ev("SHINEDOWN - Dance Kid Dance Act II - Düsseldorf, Mitsubishi Electric Halle", "Mitsubishi Electric Halle", "18:00", "AllEvents.in Düsseldorf")))
        # Allgemeine Einzelwörter reichen nicht
        self.assertFalse(aehnliches_event(ev("Party", "zakk", "22:00", "zakk"), ev("Halloween Party mit DJ Foo", "zakk", "22:00")))
        # Dieselbe Quelle: nein
        self.assertFalse(aehnliches_event(ev("Shinedown", "Halle", "19:30", "d-live"), ev("Shinedown Aftershow", "Halle", "23:00", "d-live")))

    def test_eine_uhrzeit_fehlt_bei_anderer_quelle(self):
        self.assertTrue(aehnliches_event(ev("Disney Der Glöckner von Notre Dame", "Capitol Theater Düsseldorf", None, "Capitol Theater Düsseldorf"),
                                         ev("Disney`s der Glöckner von Notre Dame das Musical", "Capitol Theater Düsseldorf", "19:30")))

    def test_grenzen(self):
        # Mehr als zwei Stunden auseinander: eigener Termin
        self.assertFalse(aehnliches_event(ev("Monica Muñoz – FLIP", "Tanzhaus NRW", "10:00", "Tanzhaus NRW"),
                                          ev("Monica Muñoz: FLIP", "tanzhaus nrw", "16:00")))
        # Dieselbe Quelle mit anderer Uhrzeit bleibt ein weiterer Termin
        self.assertFalse(aehnliches_event(ev("Der Hobbit", "Schauspielhaus", "09:30", "Düsseldorfer Schauspielhaus"),
                                          ev("Der Hobbit", "Schauspielhaus", "11:45", "Düsseldorfer Schauspielhaus")))
        # Anderer Ort bleibt anders
        self.assertFalse(aehnliches_event(ev("Tatort Live", "Savoy", "20:00", "zakk"), ev("Tatort Live", "Capitol", "19:00")))

    def test_mehrdeutig_bleibt_getrennt(self):
        frueh = ev("Romeo und Julia", "Schauspielhaus", "18:00", "Düsseldorfer Schauspielhaus")
        spaet = ev("Romeo und Julia", "Schauspielhaus", "20:00", "Düsseldorfer Schauspielhaus")
        self.assertIsNone(bester_treffer([frueh, spaet], ev("Romeo und Julia", "Schauspielhaus", "19:00")))
        # Exakte Uhrzeit gewinnt immer
        self.assertIs(bester_treffer([frueh, spaet], ev("Romeo und Julia", "Schauspielhaus", "20:00")), spaet)
        # Nur ein Termin in Reichweite: der nächste
        matinee = ev("Romeo und Julia", "Schauspielhaus", "11:00", "Düsseldorfer Schauspielhaus")
        self.assertIs(bester_treffer([matinee, spaet], ev("Romeo und Julia", "Schauspielhaus", "19:00")), spaet)

    def test_veranstalterzeit_gewinnt(self):
        ergebnis = deduplizieren([ev("SHINEDOWN", "Mitsubishi Electric Halle", "18:30"),
                                  ev("Shinedown", "Mitsubishi Electric HALLE", "19:30", "d-live", quelle_url="https://d-live.de/x")])
        self.assertEqual(len(ergebnis), 1)
        self.assertEqual(ergebnis[0]["uhrzeit"], "19:30")
        # AllEvents (kein Rausgegangen-Tausch) bekommt trotzdem die Zeit des Veranstalters
        ergebnis = deduplizieren([ev("Good Charlotte", "Mitsubishi Electric HALLE", "20:00", "AllEvents.in Düsseldorf"),
                                  ev("Good Charlotte", "Mitsubishi Electric HALLE", "19:30", "d-live")])
        self.assertEqual([e["uhrzeit"] for e in ergebnis], ["19:30"])

    def test_db_anreicherung_uebernimmt_veranstalterzeit(self):
        alt = ev("SHINEDOWN", "Mitsubishi Electric Halle", "18:30:00", quelle_url="https://rausgegangen.de/events/x")
        neu = ev("Shinedown", "Mitsubishi Electric HALLE", "19:30", "d-live", quelle_url="https://d-live.de/x")
        self.assertEqual(_anreicherungs_update_bauen(alt, neu)["uhrzeit"], "19:30")
        # Umgekehrt (Veranstalter gespeichert, Aggregator kommt dazu): Zeit bleibt
        self.assertNotIn("uhrzeit", _anreicherungs_update_bauen(neu, alt))

    def test_aggregatoren(self):
        for q in ["Rausgegangen", "VisitDüsseldorf", "AllEvents.in Düsseldorf", "Resident Advisor", "PRINZ.de Düsseldorf"]:
            self.assertTrue(ist_aggregator({"quelle_name": q}), q)
        for q in ["d-live", "zakk", "Meetup.com", "Stadtbüchereien Düsseldorf", "Jazz-Schmiede Düsseldorf"]:
            self.assertFalse(ist_aggregator({"quelle_name": q}), q)


class TitelStatusTest(unittest.TestCase):
    def pruefe(self, titel, erwartet, abgesagt):
        e = titel_status_bereinigen({"titel": titel})
        self.assertEqual(e["titel"], erwartet)
        self.assertEqual(bool(e.get("abgesagt")), abgesagt, titel)

    def test_beispiele_aus_der_datenbank(self):
        self.pruefe('ENTFÄLLT! 11.11.2026 | "Kinder sicher im Internet" in Bilk', '"Kinder sicher im Internet" in Bilk', True)
        self.pruefe("Entfällt: Zwischenruf - U20 Poetry Slam", "Zwischenruf - U20 Poetry Slam", True)
        self.pruefe('Leider abgesagt: Sarah Kuttner: "Mama & Sam"', 'Sarah Kuttner: "Mama & Sam"', True)
        self.pruefe("! ENTFÄLLT ! Musikstudio - Erste Schritte mit Logic Pro", "Musikstudio - Erste Schritte mit Logic Pro", True)
        self.pruefe("VERLEGT AUF 11.11.2026 Musikstudio - Erste Schritte mit Logic Pro", "Musikstudio - Erste Schritte mit Logic Pro", True)
        self.pruefe("AUSGEBUCHT! 09.12.2026 | 3D-Druckstifte Workshop - makerkids", "3D-Druckstifte Workshop - makerkids", False)
        self.pruefe("Swiss & Die Anderen - Punk Lebt Tour 2026 (AUSVERKAUFT)", "Swiss & Die Anderen - Punk Lebt Tour 2026", False)

    def test_normale_titel_bleiben(self):
        for t in ["Abgesang der Saison", "Ausverkaufte Häuser – ein Theaterabend", "Die Absage", "ENTFÄLLT!"]:
            self.assertEqual(titel_status_bereinigen({"titel": t})["titel"], t)

    def test_absage_trifft_das_original(self):
        original = {"titel": '"Kinder sicher im Internet" in Bilk', "ort": "Stadtbüchereien Düsseldorf", "datum": "2026-11-11",
                    "uhrzeit": None, "quelle_name": "Stadtbüchereien Düsseldorf"}
        absage = {**original, "titel": 'ENTFÄLLT! 11.11.2026 | "Kinder sicher im Internet"'}
        ergebnis = deduplizieren([dict(original), absage])
        self.assertEqual(len(ergebnis), 1)
        self.assertTrue(ergebnis[0]["abgesagt"])
        self.assertTrue(absage.get(TITEL_STATUS_FELD))


if __name__ == "__main__":
    unittest.main()
