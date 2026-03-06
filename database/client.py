"""
client.py – DiesDasDüsseldorf
Supabase-Datenbankverbindung
Erstellt: 2026-02-24
"""
import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None

# Felder die beim Upsert ignoriert werden (server-seitig gesetzt)
_IGNORE_FELDER = {"id", "erstellt_am", "gepostet_am"}

# Felder die bei bereits gespeicherten Events ergänzt werden dürfen
_ANREICHERBARE_FELDER: list[str] = [
    "adresse",
    "uhrzeit",
    "beschreibung",
    "preis",
    "bild_url",
    "kategorie",
]

# Spalten die noch nicht in der DB existieren – werden aus Inserts/Selects herausgefiltert
# Nachtragen via Supabase Dashboard: ALTER TABLE events ADD COLUMN instagram_location_id TEXT;
_NICHT_IN_DB: set[str] = {"instagram_location_id"}

# Erkennung von Rausgegangen-Bildern (imageflow.rausgegangen.de / s3/.../rausgegangen)
_RAUSGEGANGEN_MUSTER = re.compile(r"rausgegangen", re.IGNORECASE)


def _ist_rausgegangen_bild(bild_url: Optional[str]) -> bool:
    """Erkennt ob eine Bild-URL von Rausgegangen stammt."""
    return bool(bild_url and _RAUSGEGANGEN_MUSTER.search(bild_url))


def _anreicherungs_update_bauen(bestehendes: dict, neu: dict) -> dict:
    """
    Berechnet welche Felder eines bestehenden DB-Eintrags angereichert werden sollen.

    Regeln:
    - Feld wird ergänzt wenn im bestehenden Eintrag None/leer und im neuen Eintrag belegt
    - bild_url: Rausgegangen-Bild wird durch nicht-Rausgegangen-Bild ersetzt,
      auch wenn bereits vorhanden

    Args:
        bestehendes: Aktueller DB-Eintrag
        neu: Neu eingehender Event

    Returns:
        Dict mit Feldern die aktualisiert werden sollen (leer = kein Update nötig)
    """
    update: dict = {}

    for feld in _ANREICHERBARE_FELDER:
        db_wert = bestehendes.get(feld)
        neu_wert = neu.get(feld)

        if feld == "bild_url":
            # Rausgegangen-Bild durch bessere Quelle ersetzen
            if _ist_rausgegangen_bild(db_wert) and neu_wert and not _ist_rausgegangen_bild(neu_wert):
                update[feld] = neu_wert
            elif not db_wert and neu_wert:
                update[feld] = neu_wert
        else:
            if not db_wert and neu_wert:
                update[feld] = neu_wert

    return update


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

    Für neue Events: INSERT.
    Für bereits vorhandene Events (Duplikat nach Titel + Datum + Ort):
      - Fehlende Felder werden aus dem neuen Eintrag ergänzt.
      - Ein Rausgegangen-Bild wird durch ein Bild einer anderen Quelle ersetzt,
        sofern der neue Eintrag ein besseres Bild mitbringt.

    Args:
        events: Liste von Event-Dicts im DiesDasDüsseldorf-Format

    Returns:
        Dict mit Statistiken: {"gespeichert": int, "duplikate": int,
                                "angereichert": int, "fehler": int}
    """
    if not events:
        logger.info("Keine Events zum Speichern übergeben.")
        return {"gespeichert": 0, "duplikate": 0, "angereichert": 0, "fehler": 0}

    db = get_supabase_client()
    gespeichert = 0
    duplikate = 0
    angereichert = 0
    fehler = 0

    for event in events:
        # Server-seitige Felder und noch nicht existierende DB-Spalten entfernen
        datensatz = {k: v for k, v in event.items() if k not in _IGNORE_FELDER and k not in _NICHT_IN_DB}

        titel = event.get("titel", "?")
        datum = event.get("datum", "?")
        ort = event.get("ort", "?")

        try:
            # Schritt 1: Prüfen ob Event bereits in DB vorhanden
            treffer = (
                db.table("events")
                .select("id," + ",".join(_ANREICHERBARE_FELDER))
                .eq("titel", titel)
                .eq("datum", datum)
                .eq("ort", ort)
                .limit(1)
                .execute()
            )

            if not treffer.data:
                # Neues Event: direkt einfügen
                db.table("events").insert(datensatz).execute()
                gespeichert += 1

            else:
                # Duplikat: Anreicherung prüfen
                duplikate += 1
                bestehendes = treffer.data[0]
                update = _anreicherungs_update_bauen(bestehendes, datensatz)

                if update:
                    db.table("events").update(update).eq("id", bestehendes["id"]).execute()
                    angereichert += 1
                    logger.info(
                        "Duplikat angereichert in DB: '%s' (%s) – Felder: %s",
                        titel[:40], datum, ", ".join(update.keys()),
                    )
                else:
                    logger.debug(
                        "Duplikat ohne neue Daten übersprungen: '%s' (%s)",
                        titel[:40], datum,
                    )

        except Exception as e:
            fehler += 1
            logger.error(
                "Fehler beim Speichern von '%s' (%s): %s",
                titel, datum, str(e),
            )

    logger.info(
        "Speicherung abgeschlossen – Neu: %d | Duplikate: %d | Angereichert: %d | Fehler: %d",
        gespeichert, duplikate, angereichert, fehler,
    )
    return {"gespeichert": gespeichert, "duplikate": duplikate, "angereichert": angereichert, "fehler": fehler}
