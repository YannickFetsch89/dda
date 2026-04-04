"""
publisher.py – DiesDasDüsseldorf
Veröffentlicht aufbereitete Events als Instagram-Posts via Instagram Graph API.
Zwei-Schritt-Prozess: Media-Container erstellen, dann veröffentlichen.
Erstellt: 2026-02-24
"""
import logging
import os
import time
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

from database.client import get_supabase_client

load_dotenv()

logger = logging.getLogger(__name__)

# Instagram Graph API Basis-URL
INSTAGRAM_API_URL = "https://graph.facebook.com/v21.0"

# Wartezeit zwischen Posts in Sekunden (Instagram Rate Limit)
POST_WARTEZEIT_SEKUNDEN = 30

# Exponentielles Backoff bei HTTP 429 (in Sekunden)
BACKOFF_ZEITEN = [60, 120, 240]

# Maximale Anzahl Versuche bei HTTP 429
MAX_VERSUCHE = 3


def _credentials_pruefen() -> tuple[str, str] | tuple[None, None]:
    """
    Liest Instagram-Credentials aus Umgebungsvariablen.

    Returns:
        Tuple (access_token, account_id) oder (None, None) wenn nicht konfiguriert
    """
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    account_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "")

    if not access_token or not account_id:
        return None, None

    return access_token, account_id


def _media_container_erstellen(
    client: httpx.Client,
    account_id: str,
    access_token: str,
    bild_url: str,
    caption: str,
) -> str | None:
    """
    Schritt A: Erstellt einen Instagram Media-Container.

    Args:
        client: httpx-Client
        account_id: Instagram-Account-ID
        access_token: Instagram Access Token
        bild_url: Öffentliche URL des Bildes
        caption: Instagram-Caption-Text

    Returns:
        creation_id bei Erfolg, None bei Fehler
    """
    url = f"{INSTAGRAM_API_URL}/{account_id}/media"
    params = {
        "image_url": bild_url,
        "caption": caption,
        "access_token": access_token,
    }

    for versuch in range(1, MAX_VERSUCHE + 1):
        try:
            antwort = client.post(url, params=params)

            if antwort.status_code == 200:
                daten = antwort.json()
                creation_id = daten.get("id")
                if creation_id:
                    logger.debug("Media-Container erstellt (ID: %s)", creation_id)
                    return creation_id
                else:
                    logger.error(
                        "Unerwartete API-Antwort beim Erstellen des Containers: %s",
                        daten
                    )
                    return None

            elif antwort.status_code == 429:
                if versuch < MAX_VERSUCHE:
                    wartezeit = BACKOFF_ZEITEN[versuch - 1]
                    logger.warning(
                        "HTTP 429 (zu viele Anfragen) beim Erstellen des Containers – "
                        "warte %d Sekunden (Versuch %d/%d)",
                        wartezeit, versuch, MAX_VERSUCHE
                    )
                    time.sleep(wartezeit)
                else:
                    logger.error(
                        "HTTP 429 nach %d Versuchen – Media-Container konnte nicht erstellt werden",
                        MAX_VERSUCHE
                    )
                    return None

            else:
                logger.error(
                    "HTTP %d beim Erstellen des Media-Containers: %s",
                    antwort.status_code, antwort.text
                )
                return None

        except httpx.RequestError as e:
            logger.error(
                "Netzwerkfehler beim Erstellen des Media-Containers (Versuch %d/%d): %s",
                versuch, MAX_VERSUCHE, str(e)
            )
            if versuch == MAX_VERSUCHE:
                return None

    return None


def _container_veroeffentlichen(
    client: httpx.Client,
    account_id: str,
    access_token: str,
    creation_id: str,
) -> str | None:
    """
    Schritt B: Veröffentlicht einen erstellten Media-Container.

    Args:
        client: httpx-Client
        account_id: Instagram-Account-ID
        access_token: Instagram Access Token
        creation_id: ID des erstellten Media-Containers

    Returns:
        post_id bei Erfolg, None bei Fehler
    """
    url = f"{INSTAGRAM_API_URL}/{account_id}/media_publish"
    params = {
        "creation_id": creation_id,
        "access_token": access_token,
    }

    for versuch in range(1, MAX_VERSUCHE + 1):
        try:
            antwort = client.post(url, params=params)

            if antwort.status_code == 200:
                daten = antwort.json()
                post_id = daten.get("id")
                if post_id:
                    logger.debug("Container veröffentlicht (Post-ID: %s)", post_id)
                    return post_id
                else:
                    logger.error(
                        "Unerwartete API-Antwort beim Veröffentlichen: %s", daten
                    )
                    return None

            elif antwort.status_code == 429:
                if versuch < MAX_VERSUCHE:
                    wartezeit = BACKOFF_ZEITEN[versuch - 1]
                    logger.warning(
                        "HTTP 429 beim Veröffentlichen des Containers – "
                        "warte %d Sekunden (Versuch %d/%d)",
                        wartezeit, versuch, MAX_VERSUCHE
                    )
                    time.sleep(wartezeit)
                else:
                    logger.error(
                        "HTTP 429 nach %d Versuchen – Container konnte nicht veröffentlicht werden",
                        MAX_VERSUCHE
                    )
                    return None

            else:
                logger.error(
                    "HTTP %d beim Veröffentlichen des Containers: %s",
                    antwort.status_code, antwort.text
                )
                return None

        except httpx.RequestError as e:
            logger.error(
                "Netzwerkfehler beim Veröffentlichen des Containers (Versuch %d/%d): %s",
                versuch, MAX_VERSUCHE, str(e)
            )
            if versuch == MAX_VERSUCHE:
                return None

    return None


def _event_als_gepostet_markieren(db, event_id: str) -> bool:
    """
    Setzt den Status eines Events auf 'gepostet' und trägt den aktuellen UTC-Timestamp ein.

    Args:
        db: Supabase-Client
        event_id: UUID des Events

    Returns:
        True bei Erfolg, False bei Fehler
    """
    try:
        db.table("events").update({
            "status": "gepostet",
            "gepostet_am": datetime.now(timezone.utc).isoformat(),
        }).eq("id", event_id).execute()
        return True
    except Exception as e:
        logger.error(
            "Fehler beim Markieren von Event %s als 'gepostet': %s",
            event_id, str(e)
        )
        return False


def _event_als_fehler_markieren(db, event_id: str) -> None:
    """
    Setzt den Status eines Events auf 'fehler'.

    Args:
        db: Supabase-Client
        event_id: UUID des Events
    """
    try:
        db.table("events").update({"status": "fehler"}).eq("id", event_id).execute()
    except Exception as e:
        logger.error(
            "Fehler beim Markieren von Event %s als 'fehler': %s",
            event_id, str(e)
        )


def posten(limit: int = 5) -> int:
    """
    Lädt aufbereitete Events aus Supabase und postet sie auf Instagram.

    Ablauf für jedes Event:
    1. Bild-URL und Caption prüfen
    2. Media-Container erstellen (Schritt A)
    3. Container veröffentlichen (Schritt B)
    4. Status in Supabase aktualisieren

    Args:
        limit: Maximale Anzahl zu postender Events (Standard: 5)

    Returns:
        Anzahl erfolgreich geposteter Events
    """
    logger.info("--- Instagram-Publisher gestartet (max. %d Posts) ---", limit)

    # Credentials prüfen
    access_token, account_id = _credentials_pruefen()
    if access_token is None:
        logger.error(
            "INSTAGRAM_ACCESS_TOKEN und/oder INSTAGRAM_ACCOUNT_ID fehlen in der .env Datei – "
            "Instagram-Posting wird übersprungen"
        )
        return 0

    # Datenbankverbindung herstellen
    try:
        db = get_supabase_client()
    except Exception as e:
        logger.error("Datenbankverbindung fehlgeschlagen: %s", str(e))
        return 0

    # Aufbereitete Events laden – abgelehnte Events werden ausgeschlossen.
    # Reihenfolge: top_event_des_monats → highlight_der_woche → tipp_des_tages → älteste zuerst
    try:
        ergebnis = (
            db.table("events")
            .select("*")
            .eq("status", "aufbereitet")
            .eq("abgelehnt", False)
            .order("top_event_des_monats", desc=True)
            .order("highlight_der_woche", desc=True)
            .order("tipp_des_tages", desc=True)
            .order("datum", desc=False)
            .limit(limit)
            .execute()
        )
        events = ergebnis.data
    except Exception as e:
        logger.error("Fehler beim Laden der aufbereiteten Events: %s", str(e))
        return 0

    if not events:
        logger.info("Keine Events mit status='aufbereitet' gefunden.")
        return 0

    logger.info("%d aufbereitete Event(s) zum Posten gefunden", len(events))

    gepostet = 0

    with httpx.Client(timeout=30.0) as http_client:
        for index, event in enumerate(events):
            event_id = event.get("id")
            titel = event.get("titel", "?")
            bild_url = event.get("bild_url")
            caption = event.get("instagram_caption")

            logger.info("Verarbeite Event %d/%d: '%s'", index + 1, len(events), titel)

            # Bild-URL prüfen – ohne Bild kein Instagram-Post möglich
            if not bild_url:
                logger.warning(
                    "Event '%s' (ID: %s): Kein Bild vorhanden – übersprungen",
                    titel, event_id
                )
                continue

            # Caption prüfen
            if not caption:
                logger.warning(
                    "Event '%s' (ID: %s): Keine Instagram-Caption vorhanden – übersprungen",
                    titel, event_id
                )
                continue

            # Rate Limiting zwischen Posts (nicht vor dem ersten Post)
            if index > 0:
                logger.info(
                    "Warte %d Sekunden vor dem nächsten Post (Instagram Rate Limit) ...",
                    POST_WARTEZEIT_SEKUNDEN
                )
                time.sleep(POST_WARTEZEIT_SEKUNDEN)

            # Schritt A: Media-Container erstellen
            logger.info("Schritt A: Erstelle Media-Container für '%s' ...", titel)
            creation_id = _media_container_erstellen(
                http_client, account_id, access_token, bild_url, caption
            )

            if creation_id is None:
                logger.error(
                    "Media-Container für '%s' konnte nicht erstellt werden – "
                    "Status wird auf 'fehler' gesetzt",
                    titel
                )
                _event_als_fehler_markieren(db, event_id)
                continue

            # Schritt B: Container veröffentlichen
            logger.info("Schritt B: Veröffentliche Container für '%s' ...", titel)
            post_id = _container_veroeffentlichen(
                http_client, account_id, access_token, creation_id
            )

            if post_id is None:
                logger.error(
                    "Container für '%s' konnte nicht veröffentlicht werden – "
                    "Status wird auf 'fehler' gesetzt",
                    titel
                )
                _event_als_fehler_markieren(db, event_id)
                continue

            # Erfolg: Status aktualisieren
            if _event_als_gepostet_markieren(db, event_id):
                gepostet += 1
                logger.info(
                    "Event '%s' erfolgreich gepostet (Instagram Post-ID: %s)",
                    titel, post_id
                )
            else:
                logger.warning(
                    "Event '%s' gepostet, aber Datenbankaktualisierung fehlgeschlagen "
                    "(Post-ID: %s)",
                    titel, post_id
                )
                # Zählen wir dennoch als erfolgreich gepostet, da der Post live ist
                gepostet += 1

    logger.info(
        "Instagram-Publisher abgeschlossen – %d von %d Events erfolgreich gepostet",
        gepostet, len(events)
    )
    return gepostet
