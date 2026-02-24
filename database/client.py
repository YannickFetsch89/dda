"""
client.py – DiesDasDüsseldorf
Supabase-Datenbankverbindung
Erstellt: 2026-02-24
"""
import logging
import os

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None

# Felder die beim Upsert ignoriert werden (server-seitig gesetzt)
_IGNORE_FELDER = {"id", "erstellt_am", "gepostet_am"}


def get_supabase_client() -> Client:
    """
    Gibt eine Supabase-Client-Instanz zurück (Singleton).
    Wirft einen Fehler wenn die Umgebungsvariablen fehlen.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL und SUPABASE_KEY müssen in der .env Datei gesetzt sein."
        )

    try:
        _supabase_client = create_client(url, key)
        logger.info("Supabase-Verbindung erfolgreich hergestellt.")
    except Exception as e:
        logger.error("Supabase-Verbindung fehlgeschlagen: %s", str(e))
        raise

    return _supabase_client


def events_speichern(events: list[dict]) -> dict:
    """
    Speichert eine Liste von Events in Supabase.
    Duplikate (gleicher Titel + Datum + Ort) werden übersprungen (upsert).

    Args:
        events: Liste von Event-Dicts im DiesDasDüsseldorf-Format

    Returns:
        Dict mit Statistiken: {"gespeichert": int, "duplikate": int, "fehler": int}
    """
    if not events:
        logger.info("Keine Events zum Speichern übergeben.")
        return {"gespeichert": 0, "duplikate": 0, "fehler": 0}

    db = get_supabase_client()
    gespeichert = 0
    duplikate = 0
    fehler = 0

    for event in events:
        # Server-seitige Felder entfernen (werden von Supabase gesetzt)
        datensatz = {k: v for k, v in event.items() if k not in _IGNORE_FELDER}

        try:
            result = (
                db.table("events")
                .upsert(datensatz, on_conflict="titel,datum,ort", ignore_duplicates=True)
                .execute()
            )
            # Wenn upsert nichts zurückgibt, war es ein Duplikat
            if result.data:
                gespeichert += 1
            else:
                duplikate += 1

        except Exception as e:
            fehler += 1
            logger.error(
                "Fehler beim Speichern von '%s' (%s): %s",
                event.get("titel", "?"), event.get("datum", "?"), str(e)
            )

    logger.info(
        "Speicherung abgeschlossen – Neu: %d | Duplikate: %d | Fehler: %d",
        gespeichert, duplikate, fehler
    )
    return {"gespeichert": gespeichert, "duplikate": duplikate, "fehler": fehler}
