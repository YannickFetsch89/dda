"""
konten_aufraeumen.py – DiesDasDüsseldorf
Aufräumjob für Nutzerkonten (Plan docs/plan-nutzerkonten-2026-11-16.md, Abschnitte 4.6 und 9.3, Schritt 7).

Löscht automatisch:
  1. unbestätigte Konten (Mailadresse nicht bestätigt) nach 48 Stunden
  2. bestätigte Konten ohne Alters-Bestätigung nach 7 Tagen
  3. wegen Alter unter 16 gesperrte Konten beim nächsten Lauf
  4. Einträge im Anmeldeprotokoll von Nutzer-IDs, die es nicht mehr gibt (heute leer, siehe Plan 4.6)
Admin-Konten (profiles.rolle = 'admin') werden NIE gelöscht.

Läuft als Schritt der Pipeline (main.py, alle drei Tage) mit dem Service-Key. Daher die Formulierung in der
Datenschutzerklärung: „nach 48 Stunden, spätestens nach fünf Tagen“ bzw. „nach 7, spätestens nach 10 Tagen“.

Probelauf ohne Löschen (zeigt nur die Kandidaten):
    python -m pipeline.konten_aufraeumen --dry-run

Ins Log kommen nur Anzahlen und gekürzte Nutzer-IDs, nie Mailadressen.
"""
import argparse
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

from database.client import get_supabase_client

logger = logging.getLogger(__name__)

UNBESTAETIGT_STUNDEN = 48
OHNE_ALTER_TAGE = 7
SEITE = 200
# Sicherung gegen Fehler: Mehr Löschungen in einem Lauf sind unplausibel und brauchen --erzwingen
MAX_LOESCHUNGEN_JE_LAUF = 200


@dataclass
class Kandidat:
    nutzer_id: str
    grund: str  # "unbestaetigt" | "ohne_alter" | "unter16"


def _zeit(wert: Any) -> Optional[datetime]:
    """Zeitpunkt aus Supabase (datetime oder ISO-Text) als zeitzonenbewusstes datetime."""
    if wert is None or wert == "":
        return None
    if isinstance(wert, datetime):
        return wert if wert.tzinfo else wert.replace(tzinfo=timezone.utc)
    try:
        d = datetime.fromisoformat(str(wert).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def kandidaten_bestimmen(nutzer: Iterable[Any], profile: dict[str, dict], jetzt: datetime) -> list[Kandidat]:
    """
    Reine Regel ohne Netz (getestet in tests/test_konten_aufraeumen.py).
    nutzer: Objekte mit id, created_at, email_confirmed_at (wie supabase-py User).
    profile: id → {rolle, mindestalter_bestaetigt_am, unter16_gesperrt_am}.
    """
    kandidaten: list[Kandidat] = []
    for u in nutzer:
        nutzer_id = str(u.id)
        profil = profile.get(nutzer_id)
        if profil and profil.get("rolle") == "admin":
            continue
        angelegt = _zeit(getattr(u, "created_at", None))
        bestaetigt = _zeit(getattr(u, "email_confirmed_at", None))
        if angelegt is None:
            continue
        if bestaetigt is None:
            if angelegt < jetzt - timedelta(hours=UNBESTAETIGT_STUNDEN):
                kandidaten.append(Kandidat(nutzer_id, "unbestaetigt"))
            continue
        if profil is None:
            # Bestätigt, aber ohne Profil: unerwartet – lieber stehen lassen und melden
            logger.warning("Konten-Aufräumen: bestätigtes Konto %s… ohne Profil, übersprungen", nutzer_id[:8])
            continue
        if profil.get("unter16_gesperrt_am"):
            kandidaten.append(Kandidat(nutzer_id, "unter16"))
        elif not profil.get("mindestalter_bestaetigt_am") and angelegt < jetzt - timedelta(days=OHNE_ALTER_TAGE):
            kandidaten.append(Kandidat(nutzer_id, "ohne_alter"))
    return kandidaten


def _alle_nutzer(db) -> list[Any]:
    nutzer: list[Any] = []
    seite = 1
    while True:
        teil = db.auth.admin.list_users(page=seite, per_page=SEITE) or []
        nutzer.extend(teil)
        if len(teil) < SEITE:
            return nutzer
        seite += 1


def _profile(db, ids: list[str]) -> dict[str, dict]:
    profile: dict[str, dict] = {}
    for i in range(0, len(ids), SEITE):
        teil = ids[i:i + SEITE]
        antwort = (db.table("profiles")
                   .select("id, rolle, mindestalter_bestaetigt_am, unter16_gesperrt_am")
                   .in_("id", teil).execute())
        for p in antwort.data or []:
            profile[str(p["id"])] = p
    return profile


def _loeschen(db, nutzer_id: str) -> bool:
    """Erst das Anmeldeprotokoll, dann das Konto (Fremdschlüssel räumen Profil, Merkliste, Nachweise ab)."""
    try:
        db.rpc("konto_protokoll_loeschen", {"nutzer": nutzer_id}).execute()
        db.auth.admin.delete_user(nutzer_id)
        return True
    except Exception as e:  # noqa: BLE001 – ein Fehler soll die übrigen Löschungen nicht verhindern
        logger.error("Konten-Aufräumen: %s… nicht gelöscht: %s", nutzer_id[:8], type(e).__name__)
        return False


class _OhneAnfrageLog:
    """
    httpx/httpcore loggen jede Anfrage mit voller URL auf INFO – bei diesem Job stünden dort vollständige Nutzer-IDs
    (z. B. profiles?id=in.(…)), und das Pipeline-Log landet als Artefakt in GitHub Actions. Während des Laufs daher
    nur Warnungen dieser Bibliotheken zulassen (Probelauf 17.11.2026).
    """

    NAMEN = ("httpx", "httpcore", "hpack")

    def __enter__(self):
        self._vorher = {n: logging.getLogger(n).level for n in self.NAMEN}
        for n in self.NAMEN:
            logging.getLogger(n).setLevel(logging.WARNING)

    def __exit__(self, *_):
        for n, stufe in self._vorher.items():
            logging.getLogger(n).setLevel(stufe)


def konten_aufraeumen(dry_run: bool = False, erzwingen: bool = False) -> dict[str, int]:
    """Führt den Aufräumlauf aus. Gibt die Anzahl je Grund zurück (im Probelauf: Kandidaten)."""
    with _OhneAnfrageLog():
        return _konten_aufraeumen(dry_run, erzwingen)


def _konten_aufraeumen(dry_run: bool, erzwingen: bool) -> dict[str, int]:
    db = get_supabase_client()
    jetzt = datetime.now(timezone.utc)
    ergebnis = {"unbestaetigt": 0, "ohne_alter": 0, "unter16": 0, "protokoll_waisen": 0, "fehler": 0}

    try:
        nutzer = _alle_nutzer(db)
        profile = _profile(db, [str(u.id) for u in nutzer])
    except Exception as e:  # noqa: BLE001
        # z. B. Migration noch nicht gelaufen (Spalten fehlen) – dann nichts tun
        logger.error("Konten-Aufräumen abgebrochen, Konten nicht lesbar: %s", e)
        return ergebnis

    kandidaten = kandidaten_bestimmen(nutzer, profile, jetzt)
    if len(kandidaten) > MAX_LOESCHUNGEN_JE_LAUF and not dry_run and not erzwingen:
        logger.error("Konten-Aufräumen: %d Kandidaten sind unplausibel viele – abgebrochen. "
                     "Probelauf prüfen und ggf. mit --erzwingen starten.", len(kandidaten))
        return ergebnis

    for k in kandidaten:
        if dry_run:
            logger.info("Probelauf: würde löschen %s… (%s)", k.nutzer_id[:8], k.grund)
            ergebnis[k.grund] += 1
        elif _loeschen(db, k.nutzer_id):
            ergebnis[k.grund] += 1
        else:
            ergebnis["fehler"] += 1

    # Anmeldeprotokoll von Nutzer-IDs ohne Konto (heute leer, Plan 4.6)
    try:
        waisen = db.rpc("konto_protokoll_waisen", {}).execute().data or []
    except Exception as e:  # noqa: BLE001
        logger.warning("Konten-Aufräumen: Protokoll-Waisen nicht abfragbar (%s) – konten_aufraeumen_2026-11-17.sql gelaufen?", e)
        waisen = []
    for zeile in waisen:
        nutzer_id = str(zeile.get("nutzer") if isinstance(zeile, dict) else zeile)
        if dry_run:
            ergebnis["protokoll_waisen"] += 1
            continue
        try:
            db.rpc("konto_protokoll_loeschen", {"nutzer": nutzer_id}).execute()
            ergebnis["protokoll_waisen"] += 1
        except Exception as e:  # noqa: BLE001
            logger.error("Konten-Aufräumen: Protokoll von %s… nicht gelöscht: %s", nutzer_id[:8], type(e).__name__)
            ergebnis["fehler"] += 1

    art = "Probelauf (nichts gelöscht)" if dry_run else "gelöscht"
    logger.info("Konten-Aufräumen %s: unbestätigt %d, ohne Alter %d, unter 16 %d, Protokoll-Waisen %d, Fehler %d",
                art, ergebnis["unbestaetigt"], ergebnis["ohne_alter"], ergebnis["unter16"],
                ergebnis["protokoll_waisen"], ergebnis["fehler"])
    return ergebnis


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aufräumjob für Nutzerkonten")
    parser.add_argument("--dry-run", action="store_true", help="nur Kandidaten zeigen, nichts löschen")
    parser.add_argument("--erzwingen", action="store_true", help=f"auch mehr als {MAX_LOESCHUNGEN_JE_LAUF} Löschungen zulassen")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    konten_aufraeumen(dry_run=args.dry_run, erzwingen=args.erzwingen)
