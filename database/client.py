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
