"""Tests für die Magazin-Pipeline (Plan docs/plan-redaktion-2026-11-19.md, 7.2) – ohne Netz und ohne Modellaufruf.
python -m unittest tests.test_magazin
"""
import unittest
from datetime import date, datetime, timezone

from pipeline import magazin as m

E1 = "11111111-1111-4111-8111-111111111111"
E2 = "22222222-2222-4222-8222-222222222222"
E3 = "33333333-3333-4333-8333-333333333333"
VON, BIS = date(2026, 11, 30), date(2026, 12, 6)


class FakeDb:
    """Speicher-Ersatz für SupabaseDatenbank; merkt sich alle Schreibvorgänge."""

    def __init__(self, autor=True, vorhanden=False, kosten=0.0):
        self.autor = {"slug": "lena-test", "name": "Lena Rheinblick"} if autor else None
        self.vorhanden = vorhanden
        self.kosten = [{"id": "k0", "art": "gemessen", "kosten_usd": kosten}] if kosten else []
        self.beitraege: list[dict] = []
        self.gemeldet: dict[str, str | None] = {}
        self.pruefungen: dict[str, dict] = {}
        self.melde_zeilen: list[dict] = []
        self.veroeffentlicht: list[dict] = []
        self.events: dict[str, dict] = {}

    def autor_fuer(self, rubrik):
        return self.autor

    def ausgabe_vorhanden(self, rubrik, von):
        return self.vorhanden or any(b["rubrik"] == rubrik and b["gueltig_von"] == von for b in self.beitraege)

    def monatskosten(self, seit_iso):
        return sum(k["kosten_usd"] for k in self.kosten)

    def kosten_eintragen(self, eintrag):
        self.kosten.append({"id": f"k{len(self.kosten) + 1}", **eintrag})
        return self.kosten[-1]["id"]

    def kosten_aktualisieren(self, kosten_id, werte):
        next(k for k in self.kosten if k["id"] == kosten_id).update(werte)

    def beitrag_anlegen(self, zeile):
        self.beitraege.append({"id": f"b{len(self.beitraege) + 1}", **zeile})
        return self.beitraege[-1]["id"]

    def zu_melden(self):
        return self.melde_zeilen

    def gemeldet_setzen(self, beitrag_id, wert):
        self.gemeldet[beitrag_id] = wert

    def veroeffentlichte(self):
        return self.veroeffentlicht

    def events_status(self, ids):
        return {i: self.events[i] for i in ids if i in self.events}

    def pruefung_setzen(self, beitrag_id, pruefung):
        self.pruefungen[beitrag_id] = pruefung


class Antwort:
    def __init__(self, status=200, daten=None, json_fehler=False):
        self.status_code, self._daten, self._fehler = status, daten, json_fehler

    def json(self):
        if self._fehler:
            raise ValueError("kein JSON")
        return self._daten


def auswahl(kandidaten=None):
    return {"rubrik": "wochenvorschau", "von": VON.isoformat(), "bis": BIS.isoformat(), "highlight": E1, "top": None,
            "kandidaten": kandidaten if kandidaten is not None else [
                {"id": E1, "titel": "Konzert", "pfad": "/event/musik/konzert-2026-12-01"},
                {"id": E2, "titel": "Theater", "pfad": "/event/kultur/theater-2026-12-03"},
            ]}


def fliesstext(woerter=700):
    return " ".join(["Ein guter Abend in der Stadt"] * (woerter // 6 + 1))


def guter_entwurf(**aenderung):
    daten = {
        "titel_vorschlaege": ["Was ist los in Düsseldorf? 30. November bis 6. Dezember 2026", "B", "C"],
        "teaser": "Die Woche in Düsseldorf: Konzerte, Bühne und ein paar ruhige Abende – unsere Auswahl für euch.",
        "kurzfassung": ["Highlight am Dienstag", "Theater am Donnerstag", "Wochenende am Rhein"],
        "abschnitte": [
            {"ueberschrift": "Montag, 30. November", "text_md": fliesstext(), "event_ids": [E1]},
            {"ueberschrift": "Donnerstag, 3. Dezember", "text_md": "Mehr auf [dem Wochenende](/wochenende).", "event_ids": [E2]},
        ],
        "faq": [],
    }
    daten.update(aenderung)
    return daten


def ki_mit(daten, aufrufe):
    def ki(system, eingabe):
        aufrufe.append((system, eingabe))
        return m.KiAntwort(daten, 15000, 8000, m.MODELL)
    return ki


class AuswahlRouteTest(unittest.TestCase):
    """Fehler der Auswahl-Route: kein Entwurf, kein Modellaufruf, keine Kostenreservierung (Cursor-Prüfung 4, Befund 2)."""

    def lauf(self, post):
        db, aufrufe = FakeDb(), []
        with self.assertLogs("pipeline.magazin", level="INFO"):
            try:
                m.entwurf_erstellen(db, "wochenvorschau", VON, schluessel="geheim", post=post, ki=ki_mit(guter_entwurf(), aufrufe))
            except m.AuswahlFehler:
                pass
        return db, aufrufe

    def pruefe_nichts_passiert(self, post):
        db, aufrufe = self.lauf(post)
        self.assertEqual(db.beitraege, [])
        self.assertEqual(aufrufe, [])
        self.assertEqual(db.kosten, [])

    def test_fehlerfaelle(self):
        def zeitueberschreitung(*a, **k):
            raise TimeoutError("30 s")
        for post in (
            lambda *a, **k: Antwort(404), lambda *a, **k: Antwort(500), zeitueberschreitung,
            lambda *a, **k: Antwort(200, json_fehler=True), lambda *a, **k: Antwort(200, {"rubrik": "wochenvorschau"}),
            lambda *a, **k: Antwort(200, auswahl([{"id": "keine-uuid"}])),
        ):
            self.pruefe_nichts_passiert(post)

    def test_ohne_schluessel_kein_aufruf(self):
        with self.assertRaises(m.AuswahlFehler):
            m.auswahl_holen("wochenvorschau", VON, BIS, None, post=lambda *a, **k: Antwort(200, auswahl()))

    def test_leere_auswahl_ist_gueltig(self):
        db, aufrufe = FakeDb(), []
        url = m.entwurf_erstellen(db, "wochenvorschau", VON, schluessel="g", post=lambda *a, **k: Antwort(200, auswahl([])),
                                  ki=ki_mit(guter_entwurf(), aufrufe))
        self.assertIsNone(url)
        self.assertEqual((db.beitraege, aufrufe, db.kosten), ([], [], []))


class EntwurfTest(unittest.TestCase):
    def test_entwurf_mit_gruener_pruefung(self):
        db, aufrufe = FakeDb(), []
        url = m.entwurf_erstellen(db, "wochenvorschau", VON, schluessel="g", post=lambda *a, **k: Antwort(200, auswahl()),
                                  ki=ki_mit(guter_entwurf(), aufrufe))
        self.assertEqual(len(aufrufe), 1)
        b = db.beitraege[0]
        self.assertEqual(b["status"], "in_pruefung", b["pruefung"]["punkte"])
        self.assertNotEqual(b["status"], "veroeffentlicht")
        self.assertEqual(b["slug"], "events-duesseldorf-30-november-bis-6-dezember-2026")
        self.assertEqual(b["event_ids"], [E1, E2])
        self.assertIn(f"{{{{event:{E1}}}}}", b["inhalt_md"])
        self.assertEqual(len(b["vorschau_hash"]), 64)
        self.assertIn(f"/magazin/vorschau/{b['id']}?s=", url)
        # Reservierung durch gemessene Kosten ersetzt: 15 000 × 4 $ + 8 000 × 20 $ je Mio. = 0,22 $
        self.assertEqual(db.kosten[0]["art"], "gemessen")
        self.assertAlmostEqual(db.kosten[0]["kosten_usd"], 0.22, places=4)
        self.assertEqual(db.kosten[0]["beitrag_id"], b["id"])

    def test_pipeline_setzt_nie_veroeffentlicht(self):
        db = FakeDb()
        m.entwurf_erstellen(db, "wochenvorschau", VON, schluessel="g", post=lambda *a, **k: Antwort(200, auswahl()),
                            ki=ki_mit(guter_entwurf(titel_vorschlaege=["Unglaublich!"]), []))
        self.assertEqual(db.beitraege[0]["status"], "entwurf")

    def test_doppelter_lauf_kein_zweiter_entwurf(self):
        db, aufrufe = FakeDb(), []
        post = lambda *a, **k: Antwort(200, auswahl())  # noqa: E731
        m.entwurf_erstellen(db, "wochenvorschau", VON, schluessel="g", post=post, ki=ki_mit(guter_entwurf(), aufrufe))
        m.entwurf_erstellen(db, "wochenvorschau", VON, schluessel="g", post=post, ki=ki_mit(guter_entwurf(), aufrufe))
        self.assertEqual(len(db.beitraege), 1)
        self.assertEqual(len(aufrufe), 1)

    def test_ohne_autor_kein_lauf(self):
        db, aufrufe = FakeDb(autor=False), []
        self.assertIsNone(m.entwurf_erstellen(db, "wochenvorschau", VON, schluessel="g", post=lambda *a, **k: Antwort(200, auswahl()),
                                              ki=ki_mit(guter_entwurf(), aufrufe)))
        self.assertEqual(aufrufe, [])

    def test_dry_run_ruft_kein_modell(self):
        db, aufrufe = FakeDb(), []
        m.entwurf_erstellen(db, "wochenvorschau", VON, dry_run=True, schluessel="g",
                            post=lambda *a, **k: Antwort(200, auswahl()), ki=ki_mit(guter_entwurf(), aufrufe))
        self.assertEqual((db.beitraege, aufrufe, db.kosten), ([], [], []))


class KostendeckelTest(unittest.TestCase):
    def test_monatssumme_erreicht_kein_aufruf(self):
        db, aufrufe = FakeDb(kosten=10.0), []
        m.entwurf_erstellen(db, "wochenvorschau", VON, schluessel="g", post=lambda *a, **k: Antwort(200, auswahl()),
                            ki=ki_mit(guter_entwurf(), aufrufe))
        self.assertEqual(aufrufe, [])

    def test_reservierung_zaehlt_fuer_den_naechsten_lauf(self):
        db = FakeDb(kosten=9.70)
        db.kosten_eintragen({"art": "reserviert", "kosten_usd": 0.22})  # gleichzeitiger Lauf hat reserviert
        aufrufe = []
        m.entwurf_erstellen(db, "wochenvorschau", VON, schluessel="g", post=lambda *a, **k: Antwort(200, auswahl()),
                            ki=ki_mit(guter_entwurf(), aufrufe))
        self.assertEqual(aufrufe, [])  # 9,70 + 0,22 + 0,22 > 10

    def test_zwei_laeufe_nacheinander_addieren_sich(self):
        db = FakeDb(kosten=9.5)
        post = lambda *a, **k: Antwort(200, auswahl())  # noqa: E731
        m.entwurf_erstellen(db, "wochenvorschau", VON, schluessel="g", post=post, ki=ki_mit(guter_entwurf(), []))
        self.assertAlmostEqual(db.monatskosten(""), 9.72, places=4)
        aufrufe = []
        m.entwurf_erstellen(db, "wochenvorschau", date(2026, 12, 7), schluessel="g",
                            post=lambda *a, **k: Antwort(200, {**auswahl(), "von": "2026-12-07", "bis": "2026-12-13"}),
                            ki=ki_mit(guter_entwurf(), aufrufe))
        self.assertEqual(len(aufrufe), 1)  # 9,72 + 0,22 ≤ 10
        self.assertEqual(len(db.beitraege), 2)


class PruefungenTest(unittest.TestCase):
    def entwurf(self, **daten):
        d = guter_entwurf(**daten)
        return m.Entwurf(titel=d["titel_vorschlaege"][0], teaser=d["teaser"], kurzfassung=d["kurzfassung"],
                         abschnitte=d["abschnitte"], faq=d["faq"])

    def punkte(self, e, hero="/fallback/theater-1.webp"):
        return m.pruefen(e, "wochenvorschau", VON, BIS, auswahl()["kandidaten"], hero)["punkte"]

    def test_guter_entwurf_ist_gruen(self):
        self.assertEqual(self.punkte(self.entwurf()), [])

    def test_b_uhrzeit_preis_ausverkauft(self):
        for text in ("Einlass 19:30 am Rhein.", "Beginn um 20 Uhr.", "Karten ab 12 €.", "Für 5 Euro dabei.",
                     "Der Eintritt ist kostenlos.", "Leider ausverkauft."):
            abschnitte = [{"ueberschrift": "Montag, 30. November", "text_md": fliesstext() + " " + text, "event_ids": [E1]}]
            self.assertTrue(any(p.startswith("(b)") for p in self.punkte(self.entwurf(abschnitte=abschnitte))), text)

    def test_b_europa_und_uhrwerk_schlagen_nicht_an(self):
        abschnitte = [{"ueberschrift": "Montag, 30. November", "text_md": fliesstext() + " Europa tanzt, das Uhrwerk tickt.", "event_ids": [E1]}]
        self.assertEqual(self.punkte(self.entwurf(abschnitte=abschnitte)), [])

    def test_b_daten(self):
        # Tagesüberschrift im Zeitraum: grün; Datum außerhalb in der Überschrift: rot; Datum im Fließtext: rot
        ausserhalb = [{"ueberschrift": "Montag, 7. Dezember", "text_md": fliesstext(), "event_ids": [E1]}]
        self.assertTrue(any("außerhalb" in p for p in self.punkte(self.entwurf(abschnitte=ausserhalb))))
        im_text = [{"ueberschrift": "Montag", "text_md": fliesstext() + " Am 2. Dezember lohnt es sich.", "event_ids": [E1]}]
        self.assertTrue(any("Fließtext" in p for p in self.punkte(self.entwurf(abschnitte=im_text))))
        saison = self.entwurf(kurzfassung=["Vom 30. November bis 6. Dezember", "zwei", "drei"])
        self.assertEqual(self.punkte(saison), [])

    def test_b_jahreswechsel(self):
        e = self.entwurf(abschnitte=[{"ueberschrift": "Samstag, 2. Januar", "text_md": fliesstext(), "event_ids": [E1]}],
                         titel_vorschlaege=["Was ist los in Düsseldorf? 28. Dezember bis 3. Januar"])
        punkte = m.pruefen(e, "wochenvorschau", date(2026, 12, 28), date(2027, 1, 3), auswahl()["kandidaten"], "/fallback/theater-1.webp")["punkte"]
        self.assertFalse(any("außerhalb" in p for p in punkte), punkte)

    def test_a_c_e_f_h_i(self):
        fremd = [{"ueberschrift": "Montag", "text_md": fliesstext(), "event_ids": [E3]}]
        self.assertTrue(any(p.startswith("(a)") for p in self.punkte(self.entwurf(abschnitte=fremd))))
        for link in ("//fremd.de", "/../x", "http://unsicher.de", "javascript:alert(1)"):
            abschnitte = [{"ueberschrift": "Montag", "text_md": fliesstext() + f" [x]({link})", "event_ids": [E1]}]
            self.assertTrue(any(p.startswith("(c)") for p in self.punkte(self.entwurf(abschnitte=abschnitte))), link)
        for text, kennung in (("Das ist unglaublich gut.", "(e)"), ("Ich war selbst dort.", "(e)"), ("Bei Google 4,8 Sterne.", "(f)")):
            abschnitte = [{"ueberschrift": "Montag", "text_md": fliesstext() + " " + text, "event_ids": [E1]}]
            self.assertTrue(any(p.startswith(kennung) for p in self.punkte(self.entwurf(abschnitte=abschnitte))), text)
        hub = self.entwurf(titel_vorschlaege=["Clubs in Düsseldorf: die Woche"])
        self.assertTrue(any(p.startswith("(h)") for p in self.punkte(hub)))
        self.assertTrue(any(p.startswith("(i)") for p in self.punkte(self.entwurf(), hero="/fallback/sprachcafe-2.webp")))

    def test_faq_wird_mitgeprueft(self):
        """FAQ steht sichtbar und im JSON-LD – dieselben Regeln wie der Fließtext (Cursor-Gesamtprüfung)."""
        faelle = (
            ({"frage": "Wann geht es los?", "antwort": "Um 19:30 am Rhein."}, "(b)"),
            ({"frage": "Was kostet es?", "antwort": "Karten ab 12 €."}, "(b)"),
            ({"frage": "Gibt es noch Karten?", "antwort": "Leider ausverkauft."}, "(b)"),
            ({"frage": "Wann genau?", "antwort": "Am 2. Dezember."}, "(b)"),
            ({"frage": "Mehr?", "antwort": "Siehe [hier](//fremd.de)."}, "(c)"),
            ({"frage": "Lohnt es sich?", "antwort": "Ich war selbst dort."}, "(e)"),
            ({"frage": "Wie gut?", "antwort": "Bei Google 4,8 Sterne."}, "(f)"),
        )
        for faq, kennung in faelle:
            self.assertTrue(any(p.startswith(kennung) for p in self.punkte(self.entwurf(faq=[faq]))), faq)
        harmlos = {"frage": "Wo finde ich alle Termine?", "antwort": "Im [Kalender](/entdecken) und am [Wochenende](/wochenende)."}
        self.assertEqual(self.punkte(self.entwurf(faq=[harmlos])), [])

    def test_i_fremdfoto_und_fremde_ordner(self):
        for hero in ("/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp", "/ort-bilder/events/further-nikolausmarkt.webp", "https://x.de/a.webp"):
            self.assertTrue(any(p.startswith("(i)") for p in self.punkte(self.entwurf(), hero=hero)), hero)
        self.assertEqual(self.punkte(self.entwurf(), hero="/ort-bilder/weihnachtsmaerkte/maerchen-markt.webp"), [])

    def test_d_laengen(self):
        kurz = self.entwurf(teaser="zu kurz", kurzfassung=["eins"],
                            abschnitte=[{"ueberschrift": "Montag", "text_md": "Wenig Text.", "event_ids": [E1]}])
        punkte = self.punkte(kurz)
        self.assertTrue(any("Teaser" in p for p in punkte))
        self.assertTrue(any("Kurzfassung" in p for p in punkte))
        self.assertTrue(any("Wörter" in p for p in punkte))


class ZeitraumTest(unittest.TestCase):
    def test_naechste_ausgaben(self):
        freitag = date(2026, 11, 27)
        self.assertEqual(m.zeitraum("wochenvorschau", heute=freitag), (date(2026, 11, 30), date(2026, 12, 6)))
        self.assertEqual(m.zeitraum("monats-tipps", heute=date(2026, 11, 28)), (date(2026, 12, 1), date(2026, 12, 31)))
        self.assertEqual(m.zeitraum("monats-tipps", heute=date(2027, 1, 28)), (date(2027, 2, 1), date(2027, 2, 28)))
        with self.assertRaises(ValueError):
            m.zeitraum("wochenvorschau", von=freitag)

    def test_slugs(self):
        self.assertEqual(m.slug_fuer("monats-tipps", date(2027, 3, 1), date(2027, 3, 31)), "top-events-duesseldorf-maerz-2027")


class MeldenTest(unittest.TestCase):
    def test_feed_404_keine_meldung(self):
        db = FakeDb()
        db.melde_zeilen = [{"id": "b1", "slug": "a", "rubrik": "saison", "status": "veroeffentlicht",
                            "veroeffentlicht_am": "2026-11-29T07:00:00+00:00", "aktualisiert_am": None, "gemeldet_am": None}]
        gesendet = []
        n = m.melden_lauf(db, get=lambda *a, **k: Antwort(404), melden=lambda urls: gesendet.append(urls) or len(urls))
        self.assertEqual((n, gesendet), (0, []))

    def test_neu_geaendert_zurueckgezogen(self):
        db = FakeDb()
        jetzt = datetime(2026, 11, 29, 9, 0, tzinfo=timezone.utc)
        db.melde_zeilen = [
            {"id": "neu", "slug": "neu", "rubrik": "saison", "status": "veroeffentlicht", "veroeffentlicht_am": "2026-11-29T07:00:00+00:00", "aktualisiert_am": None, "gemeldet_am": None},
            {"id": "zukunft", "slug": "zukunft", "rubrik": "saison", "status": "veroeffentlicht", "veroeffentlicht_am": "2026-11-30T07:00:00+00:00", "aktualisiert_am": None, "gemeldet_am": None},
            {"id": "alt", "slug": "alt", "rubrik": "saison", "status": "veroeffentlicht", "veroeffentlicht_am": "2026-11-20T07:00:00+00:00", "aktualisiert_am": None, "gemeldet_am": "2026-11-20T08:00:00+00:00"},
            {"id": "weg", "slug": "weg", "rubrik": "stadtleben", "status": "zurueckgezogen", "veroeffentlicht_am": "2026-11-20T07:00:00+00:00", "aktualisiert_am": None, "gemeldet_am": "2026-11-20T08:00:00+00:00"},
        ]
        gesendet = []
        m.melden_lauf(db, get=lambda *a, **k: Antwort(200), melden=lambda urls: gesendet.extend(urls) or len(urls), jetzt=jetzt)
        self.assertIn(f"{m.SITE_URL}/magazin/neu", gesendet)
        self.assertIn(f"{m.SITE_URL}/magazin/weg", gesendet)
        self.assertNotIn(f"{m.SITE_URL}/magazin/zukunft", gesendet)
        self.assertNotIn(f"{m.SITE_URL}/magazin/alt", gesendet)
        self.assertEqual(db.gemeldet, {"neu": jetzt.isoformat(), "weg": None})


class PrueflaufTest(unittest.TestCase):
    def test_abgesagt_geloescht_faellig(self):
        db = FakeDb()
        db.veroeffentlicht = [{"id": "b1", "slug": "a", "rubrik": "wochenvorschau", "inhalt_md": "[x](//fremd.de)",
                               "event_ids": [E1, E2], "gueltig_bis": "2026-12-06", "naechste_pruefung": "2026-12-01"}]
        db.events = {E1: {"id": E1, "abgesagt": True, "abgelehnt": False}}
        self.assertEqual(m.pruef_lauf(db, heute=date(2026, 12, 2)), 1)
        punkte = " | ".join(db.pruefungen["b1"]["punkte"])
        for erwartet in ("abgesagt", "existiert nicht mehr", "Link prüfen", "Überarbeitung fällig"):
            self.assertIn(erwartet, punkte)


if __name__ == "__main__":
    unittest.main()
