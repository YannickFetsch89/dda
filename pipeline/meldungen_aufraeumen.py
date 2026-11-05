"""
meldungen_aufraeumen.py – DiesDasDüsseldorf
Löschfrist für „Event melden“ (Datenschutzerklärung Abschnitt 12): Meldungen samt Kontaktdaten und
privatem Bild werden spätestens sechs Monate nach dem Event-Datum gelöscht – egal ob freigegeben,
abgelehnt oder unbearbeitet. Ein freigegebenes Event selbst (Tabelle events, öffentliches Bild) bleibt.

Läuft als Schritt der Pipeline (main.py) mit dem Service-Key.
"""
import logging
from datetime import date, timedelta

from database.client import get_supabase_client

logger = logging.getLogger(__name__)

AUFBEWAHRUNG_TAGE = 183  # ≈ sechs Monate nach dem Event-Datum


def meldungen_aufraeumen() -> int:
    """Löscht abgelaufene Meldungen. Gibt die Anzahl gelöschter Meldungen zurück."""
    db = get_supabase_client()
    grenze = (date.today() - timedelta(days=AUFBEWAHRUNG_TAGE)).isoformat()
    try:
        alt = (db.table("event_meldungen").select("id, bild_pfad, datum, datum_bis")
               .lt("datum", grenze).limit(500).execute().data or [])
    except Exception as e:
        logger.error("Meldungen-Aufräumen: Laden fehlgeschlagen: %s", e)
        return 0
    # Mehrtägige Events zählen ab ihrem letzten Tag
    alt = [m for m in alt if (m.get("datum_bis") or m["datum"]) < grenze]
    if not alt:
        return 0

    bilder = [m["bild_pfad"] for m in alt if m.get("bild_pfad")]
    if bilder:
        try:
            db.storage.from_("event-meldungen").remove(bilder)
        except Exception as e:
            logger.warning("Meldungen-Aufräumen: Bilder nicht gelöscht: %s", e)
    geloescht = 0
    for m in alt:
        try:
            db.table("event_meldungen").delete().eq("id", m["id"]).execute()
            geloescht += 1
        except Exception as e:
            logger.error("Meldungen-Aufräumen: Meldung %s nicht gelöscht: %s", m["id"], e)
    logger.info("Meldungen-Aufräumen: %d Meldung(en) nach Ablauf der Frist gelöscht", geloescht)
    return geloescht
