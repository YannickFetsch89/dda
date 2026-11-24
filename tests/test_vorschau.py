"""Tests für den Zeitraum je Quelle und die 60-Tage-Grenzen der KI-/Instagram-Schritte (Plan Quellen-Ausbau 5.2/5.3, Z1).
python -m unittest tests.test_vorschau"""
import os
import re
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import config
from config import VORSCHAU_TAGE, vorschau_ende, vorschau_tage

WURZEL = Path(__file__).resolve().parents[1]


def quellen_zeilen() -> list[tuple[str, int, str]]:
    text = (WURZEL / "main.py").read_text(encoding="utf-8")
    return [(n, int(t), m) for n, t, m in re.findall(r'\("([^"]+)", (\d), (\w+)\.scrape\)', text)]


def modul_pfad(modul: str) -> Path:
    for ordner in ("tier1", "tier2", "tier3"):
        p = WURZEL / "scraper" / ordner / f"{modul}.py"
        if p.exists():
            return p
    raise FileNotFoundError(modul)


LANG = {
    "Ticketmaster", "d-live", "Mitsubishi Electric HALLE", "Capitol Theater Düsseldorf", "Tonhalle Düsseldorf",
    "Deutsche Oper am Rhein", "Düsseldorfer Schauspielhaus", "Kom(m)ödchen Düsseldorf", "Messe Düsseldorf",
    "Fortuna Düsseldorf", "DEG Eishockey Düsseldorf", "Kunstsammlung NRW (K20/K21)",
}


class TabelleTest(unittest.TestCase):
    def setUp(self):
        os.environ.pop("VORSCHAU_NOTAUS", None)

    def test_jede_quelle_und_jeder_gespeicherte_name_hat_ein_fenster(self):
        for name, _, modul in quellen_zeilen():
            self.assertIn(name, VORSCHAU_TAGE, name)
            text = modul_pfad(modul).read_text(encoding="utf-8")
            for konstante in re.findall(r'^QUELLE_NAME\s*=\s*"([^"]+)"', text, flags=re.M):
                with self.subTest(modul=modul):
                    self.assertIn(konstante, VORSCHAU_TAGE)
                    self.assertEqual(VORSCHAU_TAGE[konstante], VORSCHAU_TAGE[name])

    def test_gruppen_nach_q7(self):
        for name, tier, _ in quellen_zeilen():
            with self.subTest(name=name):
                if name in LANG:
                    self.assertEqual(vorschau_tage(name), 365)
                elif tier in (2, 3) or name.startswith("VisitDüsseldorf"):
                    self.assertEqual(vorschau_tage(name), 120)
                else:
                    self.assertEqual(vorschau_tage(name), 60)

    def test_unbekannte_namen(self):
        self.assertEqual(vorschau_tage("Neues Haus", 2), 120)
        self.assertEqual(vorschau_tage("Neuer Kalender", 1), 60)
        self.assertEqual(vorschau_tage("Neuer Kalender"), 60)

    def test_ende_und_notaus(self):
        heute = date(2026, 11, 24)
        self.assertEqual(vorschau_ende("d-live", heute), heute + timedelta(days=365))
        with mock.patch.dict(os.environ, {"VORSCHAU_NOTAUS": "1"}):
            self.assertEqual(vorschau_ende("d-live", heute), heute + timedelta(days=60))
            self.assertEqual(vorschau_tage("zakk"), 60)
        with mock.patch.dict(os.environ, {"VORSCHAU_NOTAUS": "0"}):
            self.assertEqual(vorschau_tage("d-live"), 365)


class StrukturTest(unittest.TestCase):
    def test_kein_scraper_rechnet_das_fenster_selbst(self):
        for p in (WURZEL / "scraper").rglob("*.py"):
            self.assertNotIn("SCRAPER_VORSCHAU_TAGE", p.read_text(encoding="utf-8"), str(p))

    def test_notaus_im_workflow(self):
        text = (WURZEL / ".github" / "workflows" / "scrape.yml").read_text(encoding="utf-8")
        self.assertIn("VORSCHAU_NOTAUS: ${{ vars.VORSCHAU_NOTAUS }}", text)

    def test_monatsgrenzen_der_grossen_haeuser(self):
        from scraper.tier2 import oper_am_rhein, schauspielhaus
        self.assertGreaterEqual(oper_am_rhein.MONATE_VORAUS + 2, 13)   # Startseite liefert schon zwei Monate
        self.assertGreaterEqual(schauspielhaus.MONATE_VORAUS, 13)

    def test_captions_und_publisher_bleiben_nah(self):
        for datei in ("pipeline/caption_generator.py", "pipeline/publisher.py"):
            text = (WURZEL / datei).read_text(encoding="utf-8")
            self.assertIn('.lte("datum", (date.today() + timedelta(days=INSTAGRAM_TAGE)).isoformat())', text, datei)
        from pipeline import caption_generator, publisher
        self.assertEqual(caption_generator.INSTAGRAM_TAGE, 60)
        self.assertEqual(publisher.INSTAGRAM_TAGE, 60)

    def test_kategorien_rueckstand_ist_befristet(self):
        text = (WURZEL / "main.py").read_text(encoding="utf-8")
        self.assertIn("KATEGORIEN_RUECKSTAND_BIS = date(2026, 12, 9)", text)


class OperMonateTest(unittest.TestCase):
    def test_monate_ohne_navigationslinks(self):
        from scraper.tier2 import oper_am_rhein as oper
        start = '<div class="schedule__monthinfos" data-month="2026-11"></div><div class="schedule__monthinfos" data-month="2026-12"></div>'
        urls = oper._naechste_monate_ermitteln(start, date(2026, 11, 24))
        self.assertEqual(len(urls), oper.MONATE_VORAUS)
        self.assertTrue(urls[0].endswith("/spielplan/kalender/2027-01/"))

    def test_stopp_nach_leeren_monaten(self):
        from scraper.tier2 import oper_am_rhein as oper
        seiten = {oper.SPIELPLAN_URL: "<html></html>"}
        abrufe = []

        def abrufen(url, _logger=None):
            abrufe.append(url)
            return seiten.get(url, "<html></html>")

        with mock.patch.object(oper, "seite_abrufen", abrufen),                 mock.patch.object(oper, "_events_aus_html", lambda html, heute, ids: []):
            self.assertEqual(oper.scrape(), [])
        # Startseite + LEERE_MONATE_STOPP leere Monate, danach keine Anfragen mehr
        self.assertEqual(len(abrufe), 1 + oper.LEERE_MONATE_STOPP)

    def test_notaus_senkt_die_monate_beim_import(self):
        import importlib
        from scraper.tier2 import oper_am_rhein, schauspielhaus
        try:
            with mock.patch.dict(os.environ, {"VORSCHAU_NOTAUS": "1"}):
                self.assertEqual(importlib.reload(schauspielhaus).MONATE_VORAUS, 3)
                self.assertEqual(importlib.reload(oper_am_rhein).MONATE_VORAUS, 2)
        finally:
            os.environ.pop("VORSCHAU_NOTAUS", None)
            importlib.reload(schauspielhaus)
            importlib.reload(oper_am_rhein)


class ClubPromptTest(unittest.TestCase):
    def test_nur_naechste_60_tage(self):
        from scraper.orte.clubs_profil import kalender_quelle
        heute = date.today()
        events = [{"datum": (heute + timedelta(days=t)).isoformat(), "titel": f"T{t}", "kategorie": "nightlife"}
                  for t in (1, 30, 59, 61, 200, 300)]
        text = kalender_quelle(events)
        self.assertIn("T59", text)
        self.assertNotIn("T61", text)
        self.assertNotIn("T300", text)


class FakeAbfrage:
    """Supabase-Abfrage, die die Filter mitschreibt und feste Zeilen liefert."""

    def __init__(self, zeilen):
        self.zeilen, self.filter, self.start, self.ende = zeilen, [], 0, 0

    def table(self, _):
        self.filter = []
        return self

    def __getattr__(self, name):
        def methode(*args):
            self.filter.append((name, args))
            if name == "range":
                self.start, self.ende = args
            return self
        return methode

    @property
    def not_(self):
        return self

    def execute(self):
        return type("A", (), {"data": self.zeilen[self.start:self.ende + 1]})()


class BeschreibungFensterTest(unittest.TestCase):
    def test_nah_mit_obergrenze(self):
        from pipeline.beschreibung_quellen import offene_veranstalter_events
        db = FakeAbfrage([{"id": "1", "quelle_name": "zakk", "quelle_url": "u"}])
        self.assertEqual(len(offene_veranstalter_events(db)), 1)
        grenze = (date.today() + timedelta(days=60)).isoformat()
        self.assertIn(("lte", ("datum", grenze)), db.filter)

    def test_fern_nur_rang_eins_und_zwei_hoechstens_100(self):
        from pipeline.beschreibung_quellen import FERN_BESCHREIBUNGEN, offene_veranstalter_events
        zeilen = [{"id": str(i), "quelle_name": "PRINZ.de Düsseldorf" if i % 2 else "Tonhalle Düsseldorf", "quelle_url": "u"}
                  for i in range(400)]
        db = FakeAbfrage(zeilen)
        ergebnis = offene_veranstalter_events(db, fern=True)
        self.assertEqual(len(ergebnis), FERN_BESCHREIBUNGEN)
        self.assertTrue(all(e["quelle_name"] == "Tonhalle Düsseldorf" for e in ergebnis))
        ab = (date.today() + timedelta(days=61)).isoformat()
        self.assertIn(("gte", ("datum", ab)), db.filter)
        self.assertNotIn("lte", [f[0] for f in db.filter])


if __name__ == "__main__":
    unittest.main()
