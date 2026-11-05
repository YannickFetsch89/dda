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


def meldungen_aufraeumen() -> int:
    """Löscht alle abgelaufenen Meldungen. Gibt die Anzahl gelöschter Meldungen zurück."""
    db = get_supabase_client()
    grenze = (date.today() - timedelta(days=AUFBEWAHRUNG_TAGE)).isoformat()
    # Abgelaufen = letzter Event-Tag (datum_bis, sonst datum) vor der Grenze – direkt in der DB gefiltert
    abgelaufen = f"datum_bis.lt.{grenze},and(datum_bis.is.null,datum.lt.{grenze})"
    geloescht = 0
    uebersprungen: set[str] = set()  # Bild ließ sich nicht löschen → Zeile bleibt für den nächsten Lauf

    while True:
        try:
            abfrage = (db.table("event_meldungen").select("id, bild_pfad")
                       .or_(abgelaufen).order("datum").order("id").limit(SEITE))
            if uebersprungen:
                abfrage = abfrage.not_.in_("id", sorted(uebersprungen))
            seite = abfrage.execute().data or []
        except Exception as e:
            logger.error("Meldungen-Aufräumen: Laden fehlgeschlagen: %s", e)
            break
        if not seite:
            break

        loeschbar = [m["id"] for m in seite if not m.get("bild_pfad")]
        mit_bild = [m for m in seite if m.get("bild_pfad")]
        if mit_bild:
            try:
                db.storage.from_("event-meldungen").remove([m["bild_pfad"] for m in mit_bild])
                loeschbar += [m["id"] for m in mit_bild]
            except Exception as e:
                # Ohne gelöschtes Bild bleibt die Zeile stehen – sonst wüsste niemand mehr vom Bild
                logger.warning("Meldungen-Aufräumen: %d Bild(er) nicht gelöscht, Meldungen bleiben vorerst: %s",
                               len(mit_bild), e)
                uebersprungen.update(m["id"] for m in mit_bild)

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
                    geloescht, len(uebersprungen))
    return geloescht
