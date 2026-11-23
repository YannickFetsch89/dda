"""
Tests zum Schutz von Redaktionsänderungen vor der Pipeline (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.4, E7).
Aufruf: python -m unittest tests.test_redaktion_feldschutz
"""
import unittest
from unittest.mock import MagicMock, patch

from database.client import _abgleich_redaktion, _anreicherungs_update_bauen


def _db_mit(zeilen):
    """Supabase-Attrappe: jede Abfrage auf events liefert `zeilen`."""
    db = MagicMock()
    kette = db.table.return_value.select.return_value
    kette.eq.return_value = kette
    kette.execute.return_value = MagicMock(data=zeilen)
    return db


class TestFeldschutz(unittest.TestCase):
    """Teil A: alle vier Schreibstellen in _anreicherungs_update_bauen beachten redaktion_felder."""

    def test_ohne_schutz_wie_bisher(self):
        alt = {"quelle_name": "Rausgegangen", "quelle_url": "https://rausgegangen.de/x", "bild_url": None, "preis": None}
        neu = {"quelle_name": "zakk", "quelle_url": "https://zakk.de/x", "bild_url": "https://zakk.de/b.jpg", "preis": "12 €"}
        update = _anreicherungs_update_bauen(alt, neu)
        self.assertEqual(update["bild_url"], "https://zakk.de/b.jpg")
        self.assertEqual(update["quelle_name"], "zakk")

    def test_schleife_bild_kategorie_abgesagt(self):
        alt = {
            "quelle_name": "zakk", "quelle_url": "https://zakk.de/x",
            "bild_url": None, "kategorie": "kultur", "abgesagt": False, "adresse": None,
            "redaktion_felder": ["bild_url", "kategorie", "abgesagt"],
        }
        neu = {"quelle_name": "zakk", "quelle_url": "https://zakk.de/x", "bild_url": "https://zakk.de/b.jpg",
               "kategorie": "stadtfuehrung", "abgesagt": True, "adresse": "Fichtenstr. 40"}
        update = _anreicherungs_update_bauen(alt, neu, kategorie_fest=True)
        self.assertNotIn("bild_url", update)
        self.assertNotIn("kategorie", update)
        self.assertNotIn("abgesagt", update)  # false gilt in der Schleife als leer – geschützt bleibt es false
        self.assertEqual(update["adresse"], "Fichtenstr. 40")  # nicht geschützt → wie bisher

    def test_uhrzeit_block(self):
        alt = {"quelle_name": "Rausgegangen", "quelle_url": "https://rausgegangen.de/x", "uhrzeit": "19:00",
               "redaktion_felder": ["uhrzeit"]}
        neu = {"quelle_name": "zakk", "quelle_url": "https://zakk.de/x", "uhrzeit": "20:00"}
        self.assertNotIn("uhrzeit", _anreicherungs_update_bauen(alt, neu))

    def test_quellenwechsel(self):
        alt = {"quelle_name": "Rausgegangen", "quelle_url": "https://rausgegangen.de/x", "beschreibung": "Redaktionstext",
               "preis": "frei", "redaktion_felder": ["beschreibung", "preis", "quelle_url"]}
        neu = {"quelle_name": "zakk", "quelle_url": "https://zakk.de/x", "beschreibung": "Text der Quelle", "preis": "12 €"}
        update = _anreicherungs_update_bauen(alt, neu)
        self.assertNotIn("beschreibung", update)
        self.assertNotIn("preis", update)
        self.assertNotIn("quelle_url", update)
        self.assertEqual(update.get("quelle_name"), "zakk")

    def test_ort_id_nachtrag(self):
        alt = {"quelle_name": "zakk", "quelle_url": "https://zakk.de/x", "ort_id": None, "redaktion_felder": ["ort_id"]}
        neu = {"quelle_name": "zakk", "quelle_url": "https://zakk.de/x", "ort_id": "11111111-1111-1111-1111-111111111111"}
        self.assertNotIn("ort_id", _anreicherungs_update_bauen(alt, neu))


class TestSchrittNull(unittest.TestCase):
    """Teil B: Schritt 0 findet umbenannte/verschobene Events über abgleich_* wieder."""

    def test_trifft_eindeutige_zeile(self):
        db = _db_mit([{"id": "a", "abgleich_uhrzeit": "20:00:00"}])
        self.assertEqual(_abgleich_redaktion(db, "Konzert", "2026-11-28", "zakk", "20:00")["id"], "a")
        db.table.return_value.select.return_value.eq.assert_any_call("abgleich_titel", "Konzert")

    def test_andere_uhrzeit_trifft_nicht(self):
        db = _db_mit([{"id": "a", "abgleich_uhrzeit": "20:00:00"}])
        self.assertIsNone(_abgleich_redaktion(db, "Konzert", "2026-11-28", "zakk", "15:00"))

    def test_ohne_uhrzeit_nur_bei_genau_einer_zeile(self):
        zwei = [{"id": "a", "abgleich_uhrzeit": "15:00:00"}, {"id": "b", "abgleich_uhrzeit": "20:00:00"}]
        self.assertIsNone(_abgleich_redaktion(_db_mit(zwei), "Konzert", "2026-11-28", "zakk", None))
        self.assertEqual(_abgleich_redaktion(_db_mit(zwei[:1]), "Konzert", "2026-11-28", "zakk", None)["id"], "a")

    def test_ohne_abgleich_keine_zeile(self):
        self.assertIsNone(_abgleich_redaktion(_db_mit([]), "Konzert", "2026-11-28", "zakk", "20:00"))


class TestWeitereSchreiber(unittest.TestCase):
    """vereinheitlichen(): geschützte Zeile zählt bei der Mehrheit mit, wird aber nicht geändert."""

    def test_vereinheitlichen_laesst_geschuetzte_zeile(self):
        from pipeline import unterkategorien

        zeilen = [
            {"id": "1", "titel": "Der Hobbit", "ort": "Capitol", "kategorie": "kultur", "unterkategorie": "theater", "redaktion_felder": []},
            {"id": "2", "titel": "Der Hobbit", "ort": "Capitol", "kategorie": "kultur", "unterkategorie": "theater", "redaktion_felder": []},
            {"id": "3", "titel": "Der Hobbit", "ort": "Capitol", "kategorie": "kultur", "unterkategorie": "comedy", "redaktion_felder": ["unterkategorie"]},
            {"id": "4", "titel": "Der Hobbit", "ort": "Capitol", "kategorie": "kultur", "unterkategorie": "comedy", "redaktion_felder": []},
            {"id": "5", "titel": "Der Hobbit", "ort": "Capitol", "kategorie": "kultur", "unterkategorie": "theater", "redaktion_felder": []},
        ]
        db = MagicMock()
        kette = db.table.return_value.select.return_value
        for m in ("eq", "gte", "range"):
            getattr(kette, m).return_value = kette
        kette.not_.is_.return_value = kette
        kette.execute.return_value = MagicMock(data=zeilen)
        with patch("database.client.get_supabase_client", return_value=db):
            unterkategorien.vereinheitlichen()
        geaendert = [c.args[0] for c in db.table.return_value.update.call_args_list]
        self.assertEqual(geaendert, [{"unterkategorie": "theater"}])  # nur Zeile 4, Zeile 3 bleibt
        db.table.return_value.update.return_value.eq.assert_called_once_with("id", "4")


class TestVorschlaege(unittest.TestCase):
    def test_gebiet_vorschlag(self):
        from pipeline.vorschlaege import gebiet_vorschlaege

        events = [
            {"id": "x", "titel": "Weihnachtsmarkt", "datum": "2026-11-28", "ort": "Lanxess Arena Köln", "adresse": None, "quelle_name": "PRINZ"},
            {"id": "y", "titel": "Konzert", "datum": "2026-11-28", "ort": "zakk", "adresse": "Fichtenstr. 40, 40233 Düsseldorf", "quelle_name": "zakk"},
        ]
        zeilen = gebiet_vorschlaege(events, "lauf-1")
        self.assertEqual([z["schluessel"] for z in zeilen], ["x"])
        self.assertEqual(zeilen[0]["art"], "gebiet")
        self.assertEqual(zeilen[0]["vorschlag"]["event"], "x")
        self.assertEqual(zeilen[0]["quelle_lauf"], "lauf-1")

    def test_dubletten_vorschlag(self):
        from pipeline.vorschlaege import dubletten_vorschlaege

        basis = {"datum": "2026-11-28", "ort": "zakk", "kategorie": "musik", "abgesagt": False}
        behalten = {**basis, "id": "b", "slug": "konzert-zakk-2026-11-28", "titel": "Konzert XY", "uhrzeit": "20:00:00",
                    "quelle_name": "zakk", "quelle_url": "https://zakk.de/x", "erstellt_am": "2026-11-01"}
        dublette = {**basis, "id": "d", "slug": "konzert-xy-zakk-2026-11-28", "titel": "Konzert XY", "uhrzeit": "20:00:00",
                    "quelle_name": "Rausgegangen", "quelle_url": "https://rausgegangen.de/x", "erstellt_am": "2026-11-02"}
        events = [behalten, dublette]
        zeilen = dubletten_vorschlaege(events, {e["id"]: dict(e) for e in events})
        self.assertEqual(len(zeilen), 1)
        z = zeilen[0]
        self.assertEqual(z["art"], "dublette")
        self.assertEqual(z["schluessel"], f"{z['vorschlag']['behalten']}:{z['vorschlag']['dublette']}")
        self.assertTrue(z["vorschlag"]["ziel"].startswith("/event/musik/"))
        self.assertFalse(z["vorschlag"]["uhrzeit_uebernehmen"])

    def test_schreiben_ohne_doppelte(self):
        from pipeline.vorschlaege import vorschlaege_schreiben

        db = MagicMock()
        vorschlaege_schreiben(db, [{"art": "gebiet", "schluessel": "x"}])
        db.table.return_value.upsert.assert_called_once_with([{"art": "gebiet", "schluessel": "x"}], on_conflict="art,schluessel", ignore_duplicates=True)


if __name__ == "__main__":
    unittest.main()
