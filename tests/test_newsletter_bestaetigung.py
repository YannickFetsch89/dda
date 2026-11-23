"""
Tests zu Stufe 4 des Admin-Dashboards (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.9): Bestätigungsmail
(Double-Opt-in). Tokens gleich wie web/tests/newsletter.test.ts.
"""
import unittest
from contextlib import contextmanager

from pipeline import newsletter_bestaetigung as nb

ID = "11111111-1111-4111-8111-111111111111"
S = "testschluessel"


class Tokens(unittest.TestCase):
    def test_gleich_wie_website(self):
        self.assertEqual(nb.token(ID, nb.ZWECK_BESTAETIGEN, S), f"{ID}.fsGeRv_rV1jKlVNHfzGT4pIANAPYL-BZMiTKbOt0FL0")
        self.assertEqual(nb.token(ID, nb.ZWECK_ABMELDEN, S), f"{ID}.FRdGhX1Ca8LeXmS471jk01xpskKmgV_dcIU8J4lzkNs")

    def test_links_mit_fragment_und_one_click(self):
        l = nb.links(ID, S)
        self.assertIn("/newsletter/bestaetigen#t=", l["bestaetigen"])
        self.assertIn("/newsletter/abmelden#t=", l["abmelden"])
        self.assertIn("/api/newsletter/abmelden/", l["one_click"])


class Mail(unittest.TestCase):
    def test_kopfzeilen_und_inhalt(self):
        m = nb.mail_bauen("person@example.org", nb.links(ID, S))
        self.assertEqual(m["To"], "person@example.org")
        self.assertEqual(m["List-Unsubscribe-Post"], "List-Unsubscribe=One-Click")
        self.assertIn("/api/newsletter/abmelden/", m["List-Unsubscribe"])
        text = m.get_body(preferencelist=("plain",)).get_content()
        html = m.get_body(preferencelist=("html",)).get_content()
        self.assertIn("Anmeldung bestätigen", html)
        self.assertIn("/newsletter/bestaetigen#t=", text)
        self.assertIn("30 Tagen", text)


class FakeAntwort:
    def __init__(self, data):
        self.data = data


class FakeDb:
    def __init__(self, zeilen):
        self.zeilen, self.freigegeben = zeilen, []

    def rpc(self, name, args):
        db = self

        class Aufruf:
            def execute(self_):
                if name == "newsletter_bestaetigung_beanspruchen":
                    return FakeAntwort(db.zeilen)
                if name == "newsletter_bestaetigung_freigeben":
                    db.freigegeben.append(args["p_id"])
                return FakeAntwort(None)
        return Aufruf()


class Versand(unittest.TestCase):
    def fabrik(self, fehler_bei=(), verbindung_scheitert=False):
        gesendet = []

        @contextmanager
        def f():
            if verbindung_scheitert:
                raise OSError("keine Verbindung")

            class V:
                def senden(self, m):
                    if m["To"] in fehler_bei:
                        raise OSError("abgelehnt")
                    gesendet.append(m["To"])
            yield V()
        f.gesendet = gesendet
        return f

    def test_ohne_offene_keine_verbindung(self):
        f = self.fabrik(verbindung_scheitert=True)
        self.assertEqual(nb.versenden(FakeDb([]), f, S), {"beansprucht": 0, "gesendet": 0, "fehlgeschlagen": 0})

    def test_einzelner_fehler_wird_freigegeben(self):
        db = FakeDb([{"id": "a", "email": "a@x.de"}, {"id": "b", "email": "b@x.de"}])
        f = self.fabrik(fehler_bei=("b@x.de",))
        self.assertEqual(nb.versenden(db, f, S), {"beansprucht": 2, "gesendet": 1, "fehlgeschlagen": 1})
        self.assertEqual(db.freigegeben, ["b"])
        self.assertEqual(f.gesendet, ["a@x.de"])

    def test_verbindung_scheitert_alle_frei(self):
        db = FakeDb([{"id": "a", "email": "a@x.de"}, {"id": "b", "email": "b@x.de"}])
        self.assertEqual(nb.versenden(db, self.fabrik(verbindung_scheitert=True), S)["fehlgeschlagen"], 2)
        self.assertEqual(db.freigegeben, ["a", "b"])


if __name__ == "__main__":
    unittest.main()
