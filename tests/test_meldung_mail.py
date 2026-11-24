"""
Tests zur Bestätigungsmail an Melder (pipeline/meldung_mail.py, database/meldung_mail_2026-11-24.sql).
Event-URLs über die gemeinsame Fixture tests/fixtures/event_pfade.json (auch web/tests/event-pfade.test.ts).
"""
import json
import os
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from pipeline import meldung_mail as mm

FALL = {
    "id": "99999999-9999-4999-8999-999999999999",
    "kontakt_email": "person@example.org",
    "kontakt_name": "Karin Beispiel",
    "kontakt_rolle": "veranstalter",
    "titel": "Japanese Christmas Market in Düsseldorf",
    "datum": "2026-12-05",
    "datum_bis": None,
    "uhrzeit": "11:30:00",
    "ort": "NEBN Gallery & Rooms",
    "kategorie": "kultur",
    "slug": "japanese-christmas-market-2026-12-05",
    "event_id": "11111111-1111-4111-8111-111111111111",
}


def teile(m):
    return m.get_body(preferencelist=("plain",)).get_content(), m.get_body(preferencelist=("html",)).get_content()


class Pfade(unittest.TestCase):
    def test_gleich_wie_website(self):
        daten = json.loads((Path(__file__).parent / "fixtures" / "event_pfade.json").read_text(encoding="utf-8"))
        for f in daten["faelle"]:
            with self.subTest(f=f):
                self.assertEqual(mm.event_pfad(f["kategorie"], f["slug"], f["id"]), f["pfad"])


class Termin(unittest.TestCase):
    def test_ein_tag_mit_uhrzeit(self):
        self.assertEqual(mm.termin_text("2026-12-05", None, "11:30:00"), "Sa., 5. Dezember 2026, 11:30 Uhr")

    def test_ein_tag_ohne_uhrzeit(self):
        self.assertEqual(mm.termin_text("2026-12-05"), "Sa., 5. Dezember 2026")

    def test_mehrere_tage(self):
        self.assertEqual(mm.termin_text("2026-12-04", "2026-12-06", "18:00"),
                         "Fr., 4. Dezember bis So., 6. Dezember 2026, ab 18:00 Uhr")

    def test_ueber_jahreswechsel(self):
        self.assertEqual(mm.termin_text("2026-12-28", "2027-01-03"), "Mo., 28. Dezember 2026 bis So., 3. Januar 2027")

    def test_gleiches_enddatum_wie_ein_tag(self):
        self.assertEqual(mm.termin_text("2026-12-05", "2026-12-05"), "Sa., 5. Dezember 2026")


class Mail(unittest.TestCase):
    def test_veranstalter(self):
        m = mm.mail_bauen("person@example.org", FALL)
        self.assertEqual(m["Subject"], "Dein Event ist online: Japanese Christmas Market in Düsseldorf")
        self.assertEqual(m["To"], "person@example.org")
        self.assertEqual(m["Reply-To"], "hallo@diesdas.events")
        self.assertIsNone(m["List-Unsubscribe"])
        text, html = teile(m)
        self.assertTrue(text.startswith("Hallo Karin Beispiel,\n"))
        self.assertIn("https://diesdas.events/event/kultur/japanese-christmas-market-2026-12-05", text)
        self.assertIn("Sa., 5. Dezember 2026, 11:30 Uhr · NEBN Gallery & Rooms", text)
        self.assertIn("https://diesdas.events/event-melden", text)
        self.assertIn("https://diesdas.events/konto/anmelden?neu=1", text)
        self.assertIn("Danke, dass du dies.das nutzt", text)
        self.assertIn("einmalig", text)
        self.assertIn("dein nächstes Event", text)
        # HTML: Sonderzeichen maskiert, Button zum Event
        self.assertIn("NEBN Gallery &amp; Rooms", html)
        self.assertIn('href="https://diesdas.events/event/kultur/japanese-christmas-market-2026-12-05"', html)
        self.assertIn("Kostenloses Konto anlegen", html)
        self.assertIn("/datenschutz#event-melden", html)

    def test_besucher_und_ohne_name(self):
        m = mm.mail_bauen("x@example.org", {**FALL, "kontakt_rolle": "besucher", "kontakt_name": None})
        self.assertTrue(m["Subject"].startswith("Das von dir gemeldete Event ist online: "))
        text, _ = teile(m)
        self.assertTrue(text.startswith("Hallo,\n"))
        self.assertIn("dieses Event", text)
        self.assertNotIn("dein nächstes Event", text)

    def test_html_wird_maskiert(self):
        _, html = teile(mm.mail_bauen("x@example.org", {**FALL, "titel": "<b>Party</b>", "kontakt_name": "<script>"}))
        self.assertNotIn("<b>Party</b>", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;b&gt;Party&lt;/b&gt;", html)

    def test_langer_titel_wird_gekuerzt(self):
        m = mm.mail_bauen("x@example.org", {**FALL, "titel": "A" * 200})
        self.assertLessEqual(len(m["Subject"]), 140)

    def test_testmail_link(self):
        text, _ = teile(mm.mail_bauen("x@example.org", mm.BEISPIEL, url="https://diesdas.events/entdecken"))
        self.assertIn("https://diesdas.events/entdecken\n", text)


class FakeAntwort:
    def __init__(self, data):
        self.data = data


class FakeDb:
    def __init__(self, zeilen):
        self.zeilen, self.aufrufe = zeilen, []

    def rpc(self, name, args):
        db = self

        class Aufruf:
            def execute(self_):
                db.aufrufe.append((name, args))
                return FakeAntwort(db.zeilen if name == "meldung_mail_beanspruchen" else None)
        return Aufruf()


class FakeVersender:
    def __init__(self, scheitern_bei=()):
        self.gesendet, self.scheitern_bei = [], set(scheitern_bei)

    def senden(self, m):
        if m["To"] in self.scheitern_bei:
            raise OSError("abgelehnt")
        self.gesendet.append(m["To"])


class Versand(unittest.TestCase):
    def test_nichts_offen_oeffnet_keine_verbindung(self):
        geoeffnet = []

        @contextmanager
        def fabrik():
            geoeffnet.append(1)
            yield FakeVersender()

        zahlen = mm.versenden(FakeDb([]), fabrik)
        self.assertEqual(zahlen, {"beansprucht": 0, "gesendet": 0, "fehlgeschlagen": 0})
        self.assertEqual(geoeffnet, [])

    def test_erfolg_und_fehler_einzeln(self):
        a = {**FALL, "id": "a", "kontakt_email": "a@example.org"}
        b = {**FALL, "id": "b", "kontakt_email": "b@example.org"}
        db, v = FakeDb([a, b]), FakeVersender(scheitern_bei={"b@example.org"})

        @contextmanager
        def fabrik():
            yield v

        zahlen = mm.versenden(db, fabrik)
        self.assertEqual(zahlen, {"beansprucht": 2, "gesendet": 1, "fehlgeschlagen": 1})
        self.assertIn(("meldung_mail_versandt", {"p_id": "a"}), db.aufrufe)
        self.assertIn(("meldung_mail_freigeben", {"p_id": "b"}), db.aufrufe)

    def test_smtp_nicht_erreichbar_gibt_alle_frei(self):
        db = FakeDb([{**FALL, "id": "a"}, {**FALL, "id": "b"}])

        @contextmanager
        def fabrik():
            raise OSError("keine Verbindung")
            yield  # noqa: unreachable – macht die Funktion zum Generator

        zahlen = mm.versenden(db, fabrik)
        self.assertEqual(zahlen["fehlgeschlagen"], 2)
        self.assertEqual([x for x in db.aufrufe if x[0] == "meldung_mail_freigeben"],
                         [("meldung_mail_freigeben", {"p_id": "a"}), ("meldung_mail_freigeben", {"p_id": "b"})])


class Verbuchen(unittest.TestCase):
    """Cursor-Prüfung 24.11.2026, gering 1: Scheitert das Verbuchen nach erfolgreichem Versand, wird nur der RPC
    wiederholt – die Mail geht kein zweites Mal raus."""

    def _db(self, fehler_bis: int):
        db = FakeDb([{**FALL, "id": "a"}])
        zaehler = {"versandt": 0}
        rpc_alt = db.rpc

        def rpc(name, args):
            if name == "meldung_mail_versandt":
                zaehler["versandt"] += 1
                if zaehler["versandt"] <= fehler_bis:
                    class Kaputt:
                        def execute(self_):
                            raise OSError("Datenbank kurz weg")
                    return Kaputt()
            return rpc_alt(name, args)

        db.rpc = rpc
        return db, zaehler

    def test_wiederholt_nur_das_verbuchen(self):
        db, zaehler = self._db(fehler_bis=2)
        v = FakeVersender()

        @contextmanager
        def fabrik():
            yield v

        with mock.patch.object(mm.uhr, "sleep") as schlafen:
            zahlen = mm.versenden(db, fabrik)
        self.assertEqual(zahlen, {"beansprucht": 1, "gesendet": 1, "fehlgeschlagen": 0})
        self.assertEqual(len(v.gesendet), 1)
        self.assertEqual(zaehler["versandt"], 3)
        self.assertEqual(schlafen.call_count, 2)
        self.assertNotIn("meldung_mail_freigeben", [a[0] for a in db.aufrufe])

    def test_gibt_nach_allen_versuchen_auf_ohne_freigeben(self):
        db, zaehler = self._db(fehler_bis=99)
        v = FakeVersender()

        @contextmanager
        def fabrik():
            yield v

        with mock.patch.object(mm.uhr, "sleep"):
            zahlen = mm.versenden(db, fabrik)
        self.assertEqual(zahlen["gesendet"], 1)
        self.assertEqual(zaehler["versandt"], mm.VERBUCHEN_VERSUCHE)
        self.assertEqual(len(v.gesendet), 1)
        self.assertNotIn("meldung_mail_freigeben", [a[0] for a in db.aufrufe])


class Schalter(unittest.TestCase):
    def test_ohne_schalter_kein_versand(self):
        with mock.patch.dict(os.environ, {"MELDUNG_MAIL_AKTIV": "0"}), \
                mock.patch("database.client.get_supabase_client", return_value=FakeDb([FALL])), \
                mock.patch.object(mm, "versenden") as versenden:
            self.assertEqual(mm.main(["senden"]), 0)
            versenden.assert_not_called()


if __name__ == "__main__":
    unittest.main()
