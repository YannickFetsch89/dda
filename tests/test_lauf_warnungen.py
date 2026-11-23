"""Tests für pipeline/lauf_warnungen.py – gleiche Fixture wie web/tests/admin-cockpit.test.ts (Plan Admin-Dashboard 4.3).
Aufruf: python -m unittest tests.test_lauf_warnungen
"""
import json
import os
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline.lauf_warnungen import _mail_bauen, warnmail_nach_lauf, warnungen_berechnen

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "lauf_warnungen.json").read_text(encoding="utf-8"))
SMTP = {"SMTP_HOST": "smtp.test", "SMTP_BENUTZER": "u", "SMTP_PASSWORT": "p"}


def _zeit(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def _db(laeufe, ergebnisse):
    """Supabase-Client-Attrappe: liefert je Tabelle die gegebenen Zeilen."""
    db = MagicMock()

    def tabelle(name):
        t = MagicMock()
        kette = t.select.return_value
        for methode in ("order", "limit", "in_"):
            getattr(kette, methode).return_value = kette
        kette.execute.return_value = MagicMock(data=laeufe if name == "scraper_laeufe" else ergebnisse)
        return t

    db.table.side_effect = tabelle
    return db


class TestWarnregeln(unittest.TestCase):
    def test_fixture_gleich_wie_typescript(self):
        for fall in FIXTURE["faelle"]:
            with self.subTest(fall["name"]):
                ist = sorted(f"{w.regel}|{w.quelle or ''}" for w in warnungen_berechnen(fall["laeufe"], fall["ergebnisse"], _zeit(fall["jetzt"])))
                soll = sorted(f"{w['regel']}|{w['quelle'] or ''}" for w in fall["erwartet"])
                self.assertEqual(ist, soll)


class TestWarnmail(unittest.TestCase):
    @patch.dict(os.environ, SMTP)
    def test_mail_nur_bei_mailregeln(self):
        fall = FIXTURE["faelle"][0]
        with patch("pipeline.geburtstag_mails.Versender") as versender:
            gesendet = warnmail_nach_lauf(_db(fall["laeufe"], fall["ergebnisse"]), "l6", _zeit(fall["jetzt"]))
        self.assertTrue(gesendet)
        mail = versender.return_value.__enter__.return_value.senden.call_args[0][0]
        text = mail.get_content()
        self.assertEqual(mail["To"], "hallo@diesdas.events")
        for teil in ("W1 fehlerhaft", "W2 leer_geworden", "W4 dauerkaputt", "W6 Lauf"):
            self.assertIn(teil, text)
        self.assertNotIn("W3", text)  # nur gelb, nur im Cockpit

    @patch.dict(os.environ, SMTP)
    def test_keine_mail_ohne_warnung(self):
        laeufe = [{"id": "x", "gestartet_am": "2026-11-23T05:00:00Z", "beendet_am": "2026-11-23T06:00:00Z", "status": "erfolgreich", "speicher_fehler": 0}]
        ergebnisse = [{"lauf_id": "x", "quelle": "gesund", "status": "ok", "anzahl": 20}]
        with patch("pipeline.geburtstag_mails.Versender") as versender:
            self.assertFalse(warnmail_nach_lauf(_db(laeufe, ergebnisse), "x", _zeit("2026-11-23T07:00:00Z")))
        versender.assert_not_called()

    def test_abgebrochener_lauf_meldet_auch_ohne_regel(self):
        mail = _mail_bauen([], {"id": "x", "gestartet_am": "2026-11-23T05:00:00Z", "status": "fehler", "fehlermeldung": "Timeout"})
        self.assertIn("abgebrochen", mail["Subject"])
        self.assertIn("Timeout", mail.get_content())

    def test_ohne_smtp_kein_versand_und_kein_fehler(self):
        fall = FIXTURE["faelle"][0]
        ohne = {k: v for k, v in os.environ.items() if k not in SMTP}
        with patch.dict(os.environ, ohne, clear=True):
            self.assertFalse(warnmail_nach_lauf(_db(fall["laeufe"], fall["ergebnisse"]), "l6", _zeit(fall["jetzt"])))

    def test_wirft_nie(self):
        db = MagicMock()
        db.table.side_effect = RuntimeError("Datenbank weg")
        self.assertFalse(warnmail_nach_lauf(db, "x"))


if __name__ == "__main__":
    unittest.main()
