"""Tests für die Rangfolge der Quellen (Plan docs/plan-quellen-ausbau-2026-11-23.md, 4.1/4.2, Schritt R1).
python -m unittest tests.test_quellen_rang"""
import json
import re
import unittest
from pathlib import Path

from database.client import _anreicherungs_update_bauen
from pipeline.deduplication import deduplizieren, ist_aggregator
from pipeline.dubletten_sql import paare_finden
from pipeline.quellen_rang import (
    RANG_ANZEIGE,
    RANG_GESPEICHERT,
    UNBEKANNT_GESPEICHERT,
    quellen_rang,
    rang_anzeige,
    rang_gespeichert,
)

WURZEL = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((WURZEL / "tests" / "fixtures" / "quellen_rang.json").read_text(encoding="utf-8"))


def quellen_zeilen() -> list[tuple[str, int, str]]:
    """(Anzeigename, Tier, Modul) aus main.py QUELLEN – per Text, ohne main.py zu importieren."""
    text = (WURZEL / "main.py").read_text(encoding="utf-8")
    return [(n, int(t), m) for n, t, m in re.findall(r'\("([^"]+)", (\d), (\w+)\.scrape\)', text)]


def modul_namen(modul: str) -> set[str]:
    """QUELLE_NAME-Konstanten bzw. feste quelle_name-Werte eines Scraper-Moduls."""
    for ordner in ("tier1", "tier2", "tier3"):
        pfad = WURZEL / "scraper" / ordner / f"{modul}.py"
        if pfad.exists():
            text = pfad.read_text(encoding="utf-8")
            return set(re.findall(r'QUELLE_NAME\s*=\s*"([^"]+)"', text)) | set(re.findall(r'"quelle_name":\s*"([^"]+)"', text))
    return set()


class TabelleTest(unittest.TestCase):
    def test_jede_quelle_hat_einen_rang(self):
        zeilen = quellen_zeilen()
        self.assertGreater(len(zeilen), 40)
        for name, _, _ in zeilen:
            self.assertIn(name, RANG_ANZEIGE, f"{name} fehlt in pipeline/quellen_rang.py RANG_ANZEIGE")

    def test_gespeicherte_namen_mit_gleichem_rang(self):
        for name, _, modul in quellen_zeilen():
            for gespeichert in modul_namen(modul):
                with self.subTest(modul=modul, name=gespeichert):
                    self.assertIn(gespeichert, RANG_GESPEICHERT)
                    self.assertEqual(RANG_GESPEICHERT[gespeichert], RANG_ANZEIGE[name])

    def test_tiers(self):
        for name, tier, _ in quellen_zeilen():
            if tier in (2, 3):
                self.assertEqual(RANG_ANZEIGE[name], 1, name)
        self.assertEqual(RANG_ANZEIGE["Ticketmaster"], 2)
        self.assertEqual(RANG_ANZEIGE["Rausgegangen"], 5)

    def test_unbekannte_namen(self):
        self.assertEqual(rang_anzeige("Neues Haus", 2), 1)
        self.assertEqual(rang_anzeige("Neues Haus", 3), 1)
        self.assertEqual(rang_anzeige("Neuer Kalender", 1), 4)
        self.assertEqual(rang_gespeichert("Stadt Neuss"), UNBEKANNT_GESPEICHERT)
        # im Lauf zählt der Anzeigename samt Tier, nicht der gespeicherte Name
        self.assertEqual(quellen_rang({"quelle_name": "Stadt Neuss", "_scraper": "Kleine Weihnachtsmärkte", "_tier": 3}), 1)
        self.assertEqual(quellen_rang({"quelle_name": "Stadt Neuss"}), 3)

    def test_gemeinsame_pruefdaten(self):
        """Dieselbe Tabelle wie web/lib/quellen-rang.ts (tests/fixtures/quellen_rang.json)."""
        self.assertEqual(FIXTURE["gespeichert"], RANG_GESPEICHERT)
        self.assertEqual(FIXTURE["unbekannt_gespeichert"], UNBEKANNT_GESPEICHERT)
        for fall in FIXTURE["faelle"]:
            with self.subTest(fall=fall):
                self.assertEqual(rang_gespeichert(fall["quelle_name"], fall["quelle_url"]), fall["rang"])

    def test_ticket_domain_macht_kein_haus_zum_ticketverkauf(self):
        self.assertEqual(rang_gespeichert("d-live", "https://www.eventim.de/event/x"), 1)
        self.assertFalse(ist_aggregator({"quelle_name": "d-live", "quelle_url": "https://www.ticketmaster.de/x"}))


def ev(quelle, **mehr):
    """Ein Event derselben Vorstellung aus verschiedenen Quellen."""
    basis = {
        "titel": "Shinedown", "ort": "Mitsubishi Electric HALLE", "datum": "2026-12-01", "uhrzeit": "19:30",
        "quelle_name": quelle, "quelle_url": f"https://{quelle.lower().replace(' ', '-')}.example/shinedown",
        "_scraper": quelle,
    }
    basis.update(mehr)
    return basis


class MergeTest(unittest.TestCase):
    """In-Memory-Deduplizierung: der strikt bessere Rang wird Hauptquelle (4.2 Punkt 1)."""

    def basis_von(self, *events):
        ergebnis = deduplizieren([dict(e) for e in events])
        self.assertEqual(len(ergebnis), 1)
        return ergebnis[0]["quelle_name"]

    def test_paare_in_beiden_reihenfolgen(self):
        paare = [
            ("Mitsubishi Electric HALLE", "Ticketmaster"),
            ("Ticketmaster", "PRINZ.de Düsseldorf"),
            ("PRINZ.de Düsseldorf", "Rausgegangen"),
            ("Mitsubishi Electric HALLE", "Rausgegangen"),
            ("VisitDüsseldorf", "AllEvents.in Düsseldorf"),
        ]
        for besser, schlechter in paare:
            with self.subTest(besser=besser, schlechter=schlechter):
                self.assertEqual(self.basis_von(ev(besser), ev(schlechter)), besser)
                self.assertEqual(self.basis_von(ev(schlechter), ev(besser)), besser)

    def test_gleicher_rang_erste_bleibt(self):
        self.assertEqual(self.basis_von(ev("PRINZ.de Düsseldorf"), ev("AllEvents.in Düsseldorf")), "PRINZ.de Düsseldorf")
        self.assertEqual(self.basis_von(ev("AllEvents.in Düsseldorf"), ev("PRINZ.de Düsseldorf")), "AllEvents.in Düsseldorf")

    def test_bessere_quelle_ohne_link_wird_nicht_basis(self):
        ergebnis = deduplizieren([ev("PRINZ.de Düsseldorf"), ev("Mitsubishi Electric HALLE", quelle_url=None)])
        self.assertEqual(ergebnis[0]["quelle_name"], "PRINZ.de Düsseldorf")

    def test_uhrzeit_des_hauses(self):
        # Haus kommt als Basis: seine Zeit bleibt; Haus ohne Link: seine Zeit wird trotzdem übernommen
        ergebnis = deduplizieren([ev("Rausgegangen", uhrzeit="18:30"), ev("Mitsubishi Electric HALLE", uhrzeit="19:30")])
        self.assertEqual(ergebnis[0]["uhrzeit"], "19:30")
        ergebnis = deduplizieren([ev("Rausgegangen", uhrzeit="18:30"),
                                  ev("Mitsubishi Electric HALLE", uhrzeit="19:30", quelle_url=None)])
        self.assertEqual(ergebnis[0]["uhrzeit"], "19:30")
        # gleicher Rang ändert die Uhrzeit nicht
        ergebnis = deduplizieren([ev("PRINZ.de Düsseldorf", uhrzeit="18:30"), ev("AllEvents.in Düsseldorf", uhrzeit="19:30")])
        self.assertEqual(ergebnis[0]["uhrzeit"], "18:30")

    def test_bild_der_ticketquelle_bleibt_wenn_haus_keines_hat(self):
        ergebnis = deduplizieren([ev("Ticketmaster", bild_url="https://tm.example/bild.jpg"),
                                  ev("Mitsubishi Electric HALLE", bild_url=None)])
        self.assertEqual(ergebnis[0]["quelle_name"], "Mitsubishi Electric HALLE")
        self.assertEqual(ergebnis[0]["bild_url"], "https://tm.example/bild.jpg")


def gespeichert(quelle, **mehr):
    """Gespeicherte Zeile (ohne „_“-Felder)."""
    e = ev(quelle, **mehr)
    e.pop("_scraper")
    return {"id": "x", **e}


class SpeichernTest(unittest.TestCase):
    """Speichern: Quellenwechsel nur zu strikt besserem Rang und nur mit Link (4.2 Punkt 2)."""

    def test_haus_loest_aggregator_ab(self):
        alt = gespeichert("PRINZ.de Düsseldorf", preis="ab 30 €", adresse="Alt")
        neu = gespeichert("Mitsubishi Electric HALLE", preis="ab 35 €", adresse="Siegburger Str. 15")
        update = _anreicherungs_update_bauen(alt, neu, rang_neu=1)
        self.assertEqual(update["quelle_name"], "Mitsubishi Electric HALLE")
        self.assertEqual(update["quelle_url"], neu["quelle_url"])
        self.assertEqual(update["preis"], "ab 35 €")
        self.assertEqual(update["adresse"], "Siegburger Str. 15")

    def test_kein_wechsel_zurueck_und_nicht_bei_gleichem_rang(self):
        haus = gespeichert("Mitsubishi Electric HALLE")
        self.assertNotIn("quelle_name", _anreicherungs_update_bauen(haus, gespeichert("PRINZ.de Düsseldorf"), rang_neu=4))
        prinz = gespeichert("PRINZ.de Düsseldorf")
        self.assertNotIn("quelle_name", _anreicherungs_update_bauen(prinz, gespeichert("AllEvents.in Düsseldorf"), rang_neu=4))

    def test_rang_ohne_angabe_aus_dem_gespeicherten_namen(self):
        alt = gespeichert("Rausgegangen", quelle_url="https://rausgegangen.de/events/x")
        self.assertEqual(_anreicherungs_update_bauen(alt, gespeichert("Ticketmaster"))["quelle_name"], "Ticketmaster")

    def test_ohne_link_kein_wechsel(self):
        alt = gespeichert("PRINZ.de Düsseldorf")
        neu = gespeichert("Mitsubishi Electric HALLE", quelle_url=None)
        self.assertNotIn("quelle_name", _anreicherungs_update_bauen(alt, neu, rang_neu=1))

    def test_bild_nur_von_rang_vier_und_schlechter_ersetzt(self):
        tm = gespeichert("Ticketmaster", bild_url="https://tm.example/a.jpg")
        haus = gespeichert("Mitsubishi Electric HALLE", bild_url="https://halle.example/b.jpg")
        update = _anreicherungs_update_bauen(tm, haus, rang_neu=1)
        self.assertEqual(update["quelle_name"], "Mitsubishi Electric HALLE")
        self.assertNotIn("bild_url", update)
        prinz = gespeichert("PRINZ.de Düsseldorf", bild_url="https://prinz.example/a.jpg")
        self.assertEqual(_anreicherungs_update_bauen(prinz, haus, rang_neu=1)["bild_url"], "https://halle.example/b.jpg")

    def test_schutz_bleibt(self):
        alt = gespeichert("PRINZ.de Düsseldorf", beschreibung="Recherchiert", beschreibung_quelle="https://x",
                          ort_id="o1", redaktion_felder=["preis"], preis="frei gesetzt")
        neu = gespeichert("Mitsubishi Electric HALLE", beschreibung="Haus-Text", ort_id="o2", preis="ab 35 €")
        update = _anreicherungs_update_bauen(alt, neu, rang_neu=1)
        self.assertEqual(update["quelle_name"], "Mitsubishi Electric HALLE")
        self.assertNotIn("beschreibung", update)
        self.assertNotIn("ort_id", update)
        self.assertNotIn("preis", update)

    def test_uhrzeit_nur_vom_haus(self):
        alt = gespeichert("Ticketmaster", uhrzeit="18:30")
        self.assertEqual(_anreicherungs_update_bauen(alt, gespeichert("Mitsubishi Electric HALLE"), rang_neu=1)["uhrzeit"], "19:30")
        alt = gespeichert("PRINZ.de Düsseldorf", uhrzeit="18:30")
        self.assertNotIn("uhrzeit", _anreicherungs_update_bauen(alt, gespeichert("Ticketmaster"), rang_neu=2))


class DublettenTest(unittest.TestCase):
    def test_besserer_rang_wird_behalten(self):
        aelter = {**gespeichert("Ticketmaster"), "id": "a", "erstellt_am": "2026-11-01"}
        neuer = {**gespeichert("Mitsubishi Electric HALLE"), "id": "b", "erstellt_am": "2026-11-20"}
        paare, _ = paare_finden([aelter, neuer])
        self.assertEqual(len(paare), 1)
        behalten, dublette = paare[0]
        self.assertEqual(behalten["id"], "b")
        self.assertEqual(dublette["id"], "a")

    def test_gleicher_rang_der_aeltere(self):
        a = {**gespeichert("PRINZ.de Düsseldorf"), "id": "a", "erstellt_am": "2026-11-01"}
        b = {**gespeichert("AllEvents.in Düsseldorf"), "id": "b", "erstellt_am": "2026-11-20"}
        paare, _ = paare_finden([b, a])
        self.assertEqual(paare[0][0]["id"], "a")


if __name__ == "__main__":
    unittest.main()
