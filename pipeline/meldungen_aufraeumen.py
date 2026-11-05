"""
meldungen_aufraeumen.py – DiesDasDüsseldorf
Löschfrist für „Event melden“ (Datenschutzerklärung Abschnitt 12): Meldungen samt Kontaktdaten und
privatem Bild werden sechs Monate nach dem (letzten) Event-Tag gelöscht – egal ob freigegeben,
abgelehnt oder unbearbeitet. Ein freigegebenes Event selbst (Tabelle events, öffentliches Bild) bleibt.

Läuft als Schritt der Pipeline (main.py, alle drei Tage) mit dem Service-Key.
"""
import logging
from datetime import date, timedelta

from database.client import get_supabase_client

logger = logging.getLogger(__name__)

AUFBEWAHRUNG_TAGE = 183  # ≈ sechs Monate nach dem letzten Event-Tag
SEITE = 200
BUCKET = "event-meldungen"


def _bild_existiert(db, pfad: str) -> bool:
    """True, wenn das Objekt noch im Bucket liegt (im Zweifel True – dann bleibt die Zeile stehen)."""
    ordner, _, datei = pfad.rpartition("/")
    try:
        treffer = db.storage.from_(BUCKET).list(ordner, {"search": datei}) or []
        return any(o.get("name") == datei for o in treffer)
    except Exception:
        return True


def _bilder_loeschen(db, pfade: list[str]) -> set[str]:
    """Löscht Bilder. Gibt die Pfade zurück, die nachweislich weg sind (gelöscht oder nie/nicht mehr da)."""
    try:
        antwort = db.storage.from_(BUCKET).remove(pfade) or []
        weg = {o.get("name") for o in antwort if isinstance(o, dict)}
    except Exception as e:
        logger.warning("Meldungen-Aufräumen: Bilder nicht gelöscht: %s", e)
        return set()
    # Nicht zurückgemeldet = fehlte schon oder Löschen scheiterte → nachsehen
    for pfad in pfade:
        if pfad not in weg and not _bild_existiert(db, pfad):
            weg.add(pfad)
    return weg


def meldungen_aufraeumen() -> int:
    """Löscht alle abgelaufenen Meldungen. Gibt die Anzahl gelöschter Meldungen zurück."""
    db = get_supabase_client()
    grenze = (date.today() - timedelta(days=AUFBEWAHRUNG_TAGE)).isoformat()
    # Abgelaufen = letzter Event-Tag (datum_bis, sonst datum) vor der Grenze – direkt in der DB gefiltert
    abgelaufen = f"datum_bis.lt.{grenze},and(datum_bis.is.null,datum.lt.{grenze})"
    geloescht = 0
    # Zeilen, deren Bild sich nicht löschen ließ, bleiben stehen. Sie liegen in der festen Sortierung
    # (datum, id) immer VOR allen noch nicht gelesenen Zeilen → per Offset überspringen.
    uebersprungen = 0

    while True:
        try:
            seite = (db.table("event_meldungen").select("id, bild_pfad")
                     .or_(abgelaufen).order("datum").order("id")
                     .range(uebersprungen, uebersprungen + SEITE - 1)
                     .execute().data or [])
        except Exception as e:
            logger.error("Meldungen-Aufräumen: Laden fehlgeschlagen: %s", e)
            break
        if not seite:
            break

        pfade = [m["bild_pfad"] for m in seite if m.get("bild_pfad")]
        weg = _bilder_loeschen(db, pfade) if pfade else set()
        # Zeile nur löschen, wenn sie kein Bild hat oder ihr Bild nachweislich weg ist
        loeschbar = [m["id"] for m in seite if not m.get("bild_pfad") or m["bild_pfad"] in weg]
        uebersprungen += len(seite) - len(loeschbar)

        if loeschbar:
            try:
                db.table("event_meldungen").delete().in_("id", loeschbar).execute()
                geloescht += len(loeschbar)
            except Exception as e:
                logger.error("Meldungen-Aufräumen: Löschen fehlgeschlagen: %s", e)
                break
        if len(seite) < SEITE:
            break

    if geloescht or uebersprungen:
        logger.info("Meldungen-Aufräumen: %d Meldung(en) gelöscht, %d wegen Bildfehler vertagt",
                    geloescht, uebersprungen)
    if uebersprungen:
        logger.warning("Meldungen-Aufräumen: %d Bild(er) im Bucket %s ließen sich nicht löschen – bitte prüfen",
                       uebersprungen, BUCKET)
    return geloescht
