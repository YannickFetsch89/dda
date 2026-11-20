"""Tests für pipeline/geburtstag_mails.py (Plan docs/plan-geburtstagsmail-2026-11-20.md, Abschnitt 5). Ohne Netz."""
import logging
from datetime import date, datetime, timezone

from pipeline import geburtstag_mails as g

ID = "11111111-1111-4111-8111-111111111111"
# Derselbe Vektor steht in web/tests/geburtstag.test.ts: Python und TypeScript rechnen gleich
VEKTOR = "11111111-1111-4111-8111-111111111111.BRfJlKb2M3AvQu-zT11zVD367NArUYwl-_3hz0aCAEc"
VORLAGE = "<html><body><p>{{ANREDE}}</p>{{TIPPS}}<a href=\"{{ABMELDEN_URL}}\">ab</a></body></html>"


def test_token_gleich_typescript():
    assert g.abmelde_token(ID, "testschluessel") == VEKTOR


def test_token_haengt_an_schluessel_und_id():
    assert g.abmelde_token(ID, "anderer") != VEKTOR
    assert g.abmelde_token("22222222-2222-4222-8222-222222222222", "testschluessel").split(".")[1] != VEKTOR.split(".")[1]


def test_mail_kopfzeilen_und_teile():
    m = g.mail_bauen("a@example.org", [], VEKTOR, vorlage=VORLAGE)
    assert m["Subject"] == "Alles Gute zum Geburtstag!"
    assert m["List-Unsubscribe"] == f"<https://diesdas.events/api/konto/geburtstag-abmelden/{VEKTOR}>"
    assert m["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert m["Reply-To"] == "hallo@diesdas.events"
    assert "hallo@diesdas.events" in m["From"]
    assert m["Auto-Submitted"] == "auto-generated"
    assert m["Message-ID"].endswith("@diesdas.events>")
    assert m["Date"]
    typen = [t.get_content_type() for t in m.iter_parts()]
    assert typen == ["text/plain", "text/html"]
    html_teil = m.get_body(("html",)).get_content()
    assert f"https://diesdas.events/konto/geburtstag-abmelden#t={VEKTOR}" in html_teil
    text_teil = m.get_body(("plain",)).get_content()
    assert "Keine Geburtstagsmails mehr:" in text_teil


def test_ohne_tipps_kein_tippblock():
    m = g.mail_bauen("a@example.org", [], VEKTOR, vorlage=VORLAGE)
    assert "ausgewählte Tipps" not in m.get_body(("html",)).get_content()
    assert "ausgewählte Tipps" not in m.get_body(("plain",)).get_content()


def test_anrede_mit_vornamen_und_tippsatz():
    tipps = [{"titel": "Jazz", "ort": "zakk", "uhrzeit": "20:00", "pfad": "/e"}]
    m = g.mail_bauen("a@example.org", tipps, VEKTOR, vorlage=VORLAGE, vorname="Erika")
    h, t = m.get_body(("html",)).get_content(), m.get_body(("plain",)).get_content()
    assert "<p>Hallo Erika,</p>" in h
    assert "Hallo Erika,\n\nheute ist dein Tag" in t
    assert g.TIPPS_SATZ in t and g.TIPPS_SATZ == "Hier haben wir ein paar ausgewählte Tipps, falls du heute noch was unternehmen willst:"
    assert "ausgewählte Tipps, falls du heute noch was unternehmen willst:" in h


def test_anrede_maskiert_und_ohne_namen():
    m = g.mail_bauen("a@example.org", [], VEKTOR, vorlage=VORLAGE, vorname="<b>Ed</b>")
    assert "Hallo &lt;b&gt;Ed&lt;/b&gt;," in m.get_body(("html",)).get_content()
    assert g.anrede(None) == "Hallo,"
    assert g.anrede("  Anna   Lena ") == "Hallo Anna Lena,"


def test_tipps_hoechstens_drei_und_maskiert():
    tipps = [{"titel": f"<b>Event {i}</b>", "ort": "zakk", "uhrzeit": "20:00", "pfad": f"/event/musik/e{i}"} for i in range(5)]
    m = g.mail_bauen("a@example.org", tipps, VEKTOR, vorlage=VORLAGE)
    h = m.get_body(("html",)).get_content()
    assert h.count('class="tipp"') == 3
    assert "<b>Event" not in h and "&lt;b&gt;Event 0" in h
    assert "20:00 Uhr · zakk" in h
    assert "https://diesdas.events/event/musik/e0" in h


def test_tipp_ohne_uhrzeit_nur_ort():
    m = g.mail_bauen("a@example.org", [{"titel": "Markt", "ort": "Burgplatz", "uhrzeit": None, "pfad": "/event/x"}], VEKTOR, vorlage=VORLAGE)
    assert "Markt (Burgplatz)" in m.get_body(("plain",)).get_content()


def test_empfaenger_ids_beide_formen():
    assert g.empfaenger_ids([ID, {"geburtstag_empfaenger": ID}, "kaputt", None]) == [ID, ID]
    assert g.empfaenger_ids(None) == []


def test_heute_berlin_um_mitternacht():
    # 23:30 UTC am 19.11. ist in Berlin schon der 20.11.
    assert g.heute_berlin(datetime(2026, 11, 19, 23, 30, tzinfo=timezone.utc)) == date(2026, 11, 20)


# ── Lauf mit Attrappen ────────────────────────────────────────────────────────────────────────────

class _Antwort:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return self


class _Nutzer:
    def __init__(self, email, bestaetigt=True):
        self.user = type("U", (), {"email": email, "email_confirmed_at": "2026-01-01" if bestaetigt else None})()


class FakeDb:
    def __init__(self, ids, beanspruchbar, adressen):
        self.ids, self.beanspruchbar, self.adressen = ids, set(beanspruchbar), adressen
        self.aufrufe = []
        admin = type("A", (), {"get_user_by_id": lambda _s, nid: _Nutzer(self.adressen[nid]) if nid in self.adressen else None})()
        self.auth = type("Auth", (), {"admin": admin})()

    def table(self, name):
        """profiles.select("vorname").eq("id", …).limit(1).execute() → Vorname „Erika“ für ID, sonst keiner."""
        db = self

        class Abfrage:
            def select(self, *_):
                return self

            def eq(self, _spalte, wert):
                self.wert = wert
                return self

            def limit(self, _n):
                return self

            def execute(self):
                return _Antwort([{"vorname": "Erika"}] if name == "profiles" and self.wert == ID else [])
        db.aufrufe.append(("table", name))
        return Abfrage()

    def rpc(self, name, args):
        self.aufrufe.append((name, args))
        if name == "geburtstag_empfaenger":
            return _Antwort(list(self.ids))
        if name == "geburtstag_beanspruchen":
            ok = args["nutzer"] in self.beanspruchbar
            self.beanspruchbar.discard(args["nutzer"])
            return _Antwort([{"beansprucht": ok, "vorher": "2025-11-20" if ok else None}])
        return _Antwort(None)


class FakeVersender:
    def __init__(self, scheitert=False):
        self.mails, self.scheitert = [], scheitert

    def senden(self, m):
        if self.scheitert:
            raise OSError("smtp weg")
        self.mails.append(m)


TAG = date(2026, 11, 20)
B = "22222222-2222-4222-8222-222222222222"


def _tipps(datum="2026-11-20"):
    return lambda ids: g.TippAntwort(datum=datum, allgemein=[], tipps={i: [{"titel": "Jazz", "ort": "zakk", "uhrzeit": "20:00", "pfad": "/e"}] for i in ids})


def test_lauf_sendet_und_ueberspringt_beanspruchte():
    db = FakeDb([ID, B], beanspruchbar=[ID], adressen={ID: "a@example.org", B: "b@example.org"})
    v = FakeVersender()
    z = g.versenden(db, TAG, v, _tipps(), "testschluessel")
    assert z == {"gefunden": 2, "gesendet": 1, "uebersprungen": 1, "fehlgeschlagen": 0}
    assert len(v.mails) == 1 and v.mails[0]["To"] == "a@example.org"
    assert "Jazz" in v.mails[0].get_body(("html",)).get_content()
    # Vorname aus dem Profil in der Anrede
    assert "Hallo Erika," in v.mails[0].get_body(("plain",)).get_content()


def test_sendefehler_gibt_frei():
    db = FakeDb([ID], beanspruchbar=[ID], adressen={ID: "a@example.org"})
    z = g.versenden(db, TAG, FakeVersender(scheitert=True), _tipps(), "testschluessel")
    assert z["fehlgeschlagen"] == 1
    frei = [a for n, a in db.aufrufe if n == "geburtstag_freigeben"]
    assert frei == [{"nutzer": ID, "tag": "2026-11-20", "vorher": "2025-11-20"}]


def test_ohne_adresse_gibt_frei():
    db = FakeDb([ID], beanspruchbar=[ID], adressen={})
    z = g.versenden(db, TAG, FakeVersender(), _tipps(), "testschluessel")
    assert z["fehlgeschlagen"] == 1
    assert any(n == "geburtstag_freigeben" for n, _ in db.aufrufe)


def test_tipps_anderer_tag_werden_verworfen():
    db = FakeDb([ID], beanspruchbar=[ID], adressen={ID: "a@example.org"})
    v = FakeVersender()
    g.versenden(db, TAG, v, _tipps(datum="2026-11-21"), "testschluessel")
    assert "Jazz" not in v.mails[0].get_body(("html",)).get_content()


def test_tipps_ausfall_mail_ohne_tipps():
    db = FakeDb([ID], beanspruchbar=[ID], adressen={ID: "a@example.org"})
    v = FakeVersender()
    z = g.versenden(db, TAG, v, lambda ids: None, "testschluessel")
    assert z["gesendet"] == 1
    assert "ausgewählte Tipps" not in v.mails[0].get_body(("html",)).get_content()


def test_keine_empfaenger_keine_tipps_abfrage():
    db = FakeDb([], beanspruchbar=[], adressen={})
    gefragt = []
    z = g.versenden(db, TAG, FakeVersender(), lambda ids: gefragt.append(ids), "testschluessel")
    assert z["gefunden"] == 0 and gefragt == []


def test_log_ohne_adressen_und_ids(caplog):
    db = FakeDb([ID], beanspruchbar=[ID], adressen={ID: "a@example.org"})
    with caplog.at_level(logging.INFO):
        g.versenden(db, TAG, FakeVersender(scheitert=True), _tipps(), "testschluessel")
    assert "a@example.org" not in caplog.text and ID not in caplog.text


def test_tipps_holen_fehler_ergibt_none():
    class R:
        status_code = 503

        def json(self):
            return {}
    assert g.tipps_holen([ID], "s", post=lambda *a, **k: R()) is None
    assert g.tipps_holen([ID], None) is None

    def kaputt(*a, **k):
        raise TimeoutError()
    assert g.tipps_holen([ID], "s", post=kaputt) is None


def test_tipps_holen_schickt_schluessel():
    gesendet = {}

    class R:
        status_code = 200

        def json(self):
            return {"datum": "2026-11-20", "allgemein": [], "tipps": {ID: []}}

    def post(url, json, headers, timeout):
        gesendet.update(url=url, json=json, headers=headers)
        return R()
    a = g.tipps_holen([ID], "geheim", post=post)
    assert a is not None and a.datum == "2026-11-20"
    assert gesendet["url"].endswith("/api/intern/geburtstag-tipps")
    assert gesendet["headers"] == {"x-geburtstag-schluessel": "geheim"}
    assert gesendet["json"] == {"nutzer": [ID]}


def test_senden_ohne_schalter_verschickt_nichts(monkeypatch):
    monkeypatch.delenv("GEBURTSTAG_AKTIV", raising=False)
    monkeypatch.setenv("GEBURTSTAG_TOKEN_SCHLUESSEL", "x")
    import database.client as client
    # Der Client wird geholt, aber ohne Schalter nie benutzt
    monkeypatch.setattr(client, "get_supabase_client", lambda: object())
    monkeypatch.setattr(g, "_versender", lambda: (_ for _ in ()).throw(AssertionError("kein Versand erwartet")))
    assert g.main(["senden"]) == 0


def test_vorlage_hat_platzhalter():
    roh = g.VORLAGE.read_text(encoding="utf-8")
    assert "{{TIPPS}}" in roh and "{{ABMELDEN_URL}}" in roh and "{{ANREDE}}" in roh
    assert "BEISPIEL" not in roh
