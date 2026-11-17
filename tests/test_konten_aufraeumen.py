"""Tests für die Löschregeln des Konten-Aufräumjobs (python -m unittest tests.test_konten_aufraeumen).
Plan Nutzerkonten 9.3, 16.2 „Aufräumjob im Probelauf“."""
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from pipeline.konten_aufraeumen import kandidaten_bestimmen

JETZT = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


def nutzer(nid: str, angelegt_vor: timedelta, bestaetigt: bool = True):
    return SimpleNamespace(
        id=nid,
        created_at=JETZT - angelegt_vor,
        email_confirmed_at=(JETZT - angelegt_vor + timedelta(minutes=5)) if bestaetigt else None,
    )


def profil(rolle="user", alter=True, gesperrt=False):
    return {
        "rolle": rolle,
        "mindestalter_bestaetigt_am": "2026-11-01T00:00:00Z" if alter else None,
        "unter16_gesperrt_am": "2026-11-16T00:00:00Z" if gesperrt else None,
    }


def gruende(nutzer_liste, profile):
    return {k.nutzer_id: k.grund for k in kandidaten_bestimmen(nutzer_liste, profile, JETZT)}


class KontenAufraeumenTest(unittest.TestCase):
    def test_unbestaetigt_erst_nach_48_stunden(self):
        n = [nutzer("a", timedelta(hours=49), bestaetigt=False), nutzer("b", timedelta(hours=47), bestaetigt=False)]
        self.assertEqual(gruende(n, {"a": profil(alter=False), "b": profil(alter=False)}), {"a": "unbestaetigt"})

    def test_ohne_alter_erst_nach_7_tagen(self):
        n = [nutzer("a", timedelta(days=8)), nutzer("b", timedelta(days=6))]
        self.assertEqual(gruende(n, {"a": profil(alter=False), "b": profil(alter=False)}), {"a": "ohne_alter"})

    def test_gesperrt_unabhaengig_vom_alter_des_kontos(self):
        n = [nutzer("a", timedelta(hours=1))]
        self.assertEqual(gruende(n, {"a": profil(alter=False, gesperrt=True)}), {"a": "unter16"})

    def test_admins_nie(self):
        n = [
            nutzer("admin1", timedelta(days=30), bestaetigt=False),
            nutzer("admin2", timedelta(days=30)),
            nutzer("admin3", timedelta(days=30)),
        ]
        p = {
            "admin1": profil(rolle="admin", alter=False),
            "admin2": profil(rolle="admin", alter=False),
            "admin3": profil(rolle="admin", gesperrt=True),
        }
        self.assertEqual(gruende(n, p), {})

    def test_normales_konto_bleibt(self):
        self.assertEqual(gruende([nutzer("a", timedelta(days=400))], {"a": profil()}), {})

    def test_bestaetigt_ohne_profil_bleibt_stehen(self):
        self.assertEqual(gruende([nutzer("a", timedelta(days=30))], {}), {})

    def test_unbestaetigt_ohne_profil_wird_geloescht(self):
        self.assertEqual(gruende([nutzer("a", timedelta(days=3), bestaetigt=False)], {}), {"a": "unbestaetigt"})

    def test_iso_zeiten_als_text(self):
        n = [SimpleNamespace(id="a", created_at="2026-11-01T00:00:00Z", email_confirmed_at=None)]
        self.assertEqual(gruende(n, {}), {"a": "unbestaetigt"})


if __name__ == "__main__":
    unittest.main()
