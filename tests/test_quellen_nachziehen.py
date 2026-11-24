"""Tests für das Umhängen des Bestands auf die Rangfolge (Plan Quellen-Ausbau 4.2 Punkt 4, Schritt N1) – ohne Netz.
python -m unittest tests.test_quellen_nachziehen"""
import unittest

from pipeline import quellen_nachziehen as n
from pipeline.quellen_rang import QUELLEN_FELD

TAG = "2026-12-05"


def gescrapt(quelle: str, tier: int, **felder) -> dict:
    """Gescraptes Event wie aus dem Lauf-Report (mit `_scraper`, `_tier` und Quellenliste)."""
    e = {"titel": "Hamlet", "datum": TAG, "uhrzeit": "19:30", "ort": "Düsseldorfer Schauspielhaus",
         "quelle_name": quelle, "quelle_url": f"https://{quelle.lower().replace(' ', '')}.example/hamlet",
         "_scraper": quelle, "_tier": tier}
    e.update(felder)
    e[QUELLEN_FELD] = [{"name": quelle, "url": e["quelle_url"], "rang": 0, "zuletzt": "2026-11-24T00:00:00+00:00"}]
    return e


def zeile(quelle: str, url: str, **felder) -> dict:
    """Gespeicherte Zeile wie aus bestand_laden."""
    z = {"id": "1", "titel": "Hamlet", "datum": TAG, "uhrzeit": "19:30:00", "ort": "Düsseldorfer Schauspielhaus",
         "slug": "hamlet-2026-12-05-duesseldorfer-schauspielhaus", "quelle_name": quelle, "quelle_url": url,
         "beschreibung": None, "bild_url": None, "preis": None, "adresse": None, "redaktion_felder": None,
         "beschreibung_quelle": None, "ort_id": None, "quellen": None, "ticket_url": None}
    z.update(felder)
    return z


class PlanTest(unittest.TestCase):
    def test_rausgegangen_wird_haus(self):
        bestand = [zeile("Rausgegangen", "https://rausgegangen.de/events/hamlet",
                         bild_url="https://imageflow.rausgegangen.de/x.jpg", ort_id="o1")]
        haus = gescrapt("Düsseldorfer Schauspielhaus", 2, ticket_url="https://ticket.dhaus.de/e/1",
                        bild_url="https://www.dhaus.de/b.jpg")
        plan = n.plan_erstellen(bestand, [haus])
        self.assertEqual(len(plan), 1)
        u = plan[0]["update"]
        self.assertEqual(u["quelle_name"], "Düsseldorfer Schauspielhaus")
        self.assertEqual(u["ticket_url"], "https://ticket.dhaus.de/e/1")
        self.assertEqual(u["bild_url"], "https://www.dhaus.de/b.jpg")  # Rausgegangen-Bild (Rang 5) wird ersetzt
        self.assertNotIn("ort_id", u)  # vorhandene Zuordnung bleibt
        self.assertNotIn("slug", u)
        self.assertEqual({q["name"] for q in u["quellen"]}, {"Düsseldorfer Schauspielhaus", "Rausgegangen"})  # beide bleiben gelistet
        self.assertEqual((plan[0]["rang_alt"], plan[0]["rang_treffer"]), (5, 1))
        self.assertEqual(plan[0]["vorher"]["quelle_name"], "Rausgegangen")

    def test_bester_treffer_gewinnt(self):
        bestand = [zeile("Rausgegangen", "https://rausgegangen.de/events/hamlet")]
        kandidaten = [gescrapt("Kulturportal Düsseldorf", 1), gescrapt("Düsseldorfer Schauspielhaus", 2)]
        plan = n.plan_erstellen(bestand, kandidaten)
        self.assertEqual(plan[0]["update"]["quelle_name"], "Düsseldorfer Schauspielhaus")

    def test_gleicher_oder_schlechterer_rang_wechselt_nicht(self):
        bestand = [zeile("Kulturportal Düsseldorf", "https://kulturportal.example/hamlet", preis="ab 20 €")]
        plan = n.plan_erstellen(bestand, [gescrapt("PRINZ.de Düsseldorf", 1, preis="ab 18 €")])
        self.assertFalse([p for p in plan if "quelle_name" in p["update"]])

    def test_ohne_link_kein_wechsel_nur_luecken(self):
        bestand = [zeile("Rausgegangen", "https://rausgegangen.de/events/hamlet")]
        haus = gescrapt("Düsseldorfer Schauspielhaus", 2, quelle_url=None, preis="ab 15 €")
        plan = n.plan_erstellen(bestand, [haus])
        self.assertNotIn("quelle_name", plan[0]["update"])
        self.assertEqual(plan[0]["update"]["preis"], "ab 15 €")

    def test_redaktion_und_recherchierte_beschreibung_bleiben(self):
        bestand = [zeile("Rausgegangen", "https://rausgegangen.de/events/hamlet", beschreibung="eigener Text",
                         beschreibung_quelle="https://www.dhaus.de/hamlet", redaktion_felder=["preis"], preis="frei")]
        haus = gescrapt("Düsseldorfer Schauspielhaus", 2, beschreibung="Haus-Text", preis="ab 15 €")
        u = n.plan_erstellen(bestand, [haus])[0]["update"]
        self.assertNotIn("beschreibung", u)
        self.assertNotIn("preis", u)
        self.assertEqual(u["quelle_name"], "Düsseldorfer Schauspielhaus")

    def test_vorhandener_ticket_link_bleibt(self):
        bestand = [zeile("Rausgegangen", "https://rausgegangen.de/events/hamlet", ticket_url="https://www.eventim.de/e/1")]
        u = n.plan_erstellen(bestand, [gescrapt("Düsseldorfer Schauspielhaus", 2)])[0]["update"]
        self.assertNotIn("ticket_url", u)

    def test_ohne_ticket_spalte_kein_ticket_link(self):
        bestand = [zeile("Rausgegangen", "https://rausgegangen.de/events/hamlet")]
        haus = gescrapt("Düsseldorfer Schauspielhaus", 2, ticket_url="https://ticket.dhaus.de/e/1")
        self.assertNotIn("ticket_url", n.plan_erstellen(bestand, [haus], mit_ticket=False)[0]["update"])

    def test_andere_uhrzeit_ist_anderer_termin(self):
        bestand = [zeile("Rausgegangen", "https://rausgegangen.de/events/hamlet")]
        self.assertEqual(n.plan_erstellen(bestand, [gescrapt("Düsseldorfer Schauspielhaus", 2, uhrzeit="15:00")]), [])

    def test_bericht(self):
        bestand = [zeile("Rausgegangen", "https://rausgegangen.de/events/hamlet")]
        plan = n.plan_erstellen(bestand, [gescrapt("Düsseldorfer Schauspielhaus", 2)])
        text = n.bericht(bestand, plan)
        self.assertIn("Quellenwechsel: 1", text)
        self.assertIn("5→1: 1", text)


class SchreibenTest(unittest.TestCase):
    def test_sichern_schreiben_zuruecksetzen(self):
        import json
        import tempfile
        from pathlib import Path

        class Db:
            def __init__(self):
                self.updates = []

            def table(self, _):
                return self

            def update(self, werte):
                self.updates.append(werte)
                return self

            def eq(self, *_):
                return self

            def execute(self):
                return None

        plan = [{"id": "1", "vorher": {"quelle_name": "Rausgegangen"}, "update": {"quelle_name": "zakk"}}]
        alt = n.ORDNER
        with tempfile.TemporaryDirectory() as ordner:
            try:
                n.ORDNER = Path(ordner)
                db = Db()
                sicherung = n.schreiben(db, plan)
                self.assertEqual(json.loads(sicherung.read_text(encoding="utf-8")), [{"id": "1", "vorher": {"quelle_name": "Rausgegangen"}}])
                n.zuruecksetzen(db, sicherung)
                self.assertEqual(db.updates, [{"quelle_name": "zakk"}, {"quelle_name": "Rausgegangen"}])
            finally:
                n.ORDNER = alt


if __name__ == "__main__":
    unittest.main()
