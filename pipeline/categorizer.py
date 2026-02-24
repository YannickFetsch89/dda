"""
categorizer.py – DiesDasDüsseldorf
KI-basierte Kategorisierung und Beschreibungsgenerierung für Events.
Nutzt Claude Haiku um Events mit status='neu' zu kategorisieren.
Erstellt: 2026-02-24
"""
import logging
import os
import time

import anthropic
from dotenv import load_dotenv

from database.client import get_supabase_client

load_dotenv()

logger = logging.getLogger(__name__)

# Gültige Kategorien laut Datenschema
GUELTIGE_KATEGORIEN = {
    "kultur", "musik", "food", "sport", "outdoor",
    "community", "nightlife", "family", "dating", "sonstiges"
}

# Wartezeit zwischen Claude API Aufrufen (Rate Limiting)
API_WARTEZEIT_SEKUNDEN = 1


def _claude_client_erstellen() -> anthropic.Anthropic:
    """
    Erstellt einen Claude API Client.

    Returns:
        Anthropic-Client-Instanz

    Raises:
        EnvironmentError: Wenn der API Key fehlt
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY muss in der .env Datei gesetzt sein."
        )
    return anthropic.Anthropic(api_key=api_key)


def _event_kategorisieren_und_beschreiben(
    client: anthropic.Anthropic,
    event: dict
) -> tuple[str, str] | tuple[None, None]:
    """
    Nutzt Claude Haiku um Kategorie und Beschreibung für ein Event zu generieren.

    Args:
        client: Anthropic API Client
        event: Event-Dict mit Pflichtfeldern

    Returns:
        Tuple (kategorie, beschreibung) oder (None, None) bei Fehler
    """
    titel = event.get("titel", "")
    ort = event.get("ort", "")
    aktuelle_kategorie = event.get("kategorie", "sonstiges")
    preis = event.get("preis", "")
    datum = event.get("datum", "")

    prompt = f"""Du kategorisierst und beschreibst Events für einen Düsseldorf Stadtguide.

Event-Daten:
- Titel: {titel}
- Ort: {ort}
- Datum: {datum}
- Preis: {preis if preis else 'nicht angegeben'}
- Aktuelle Kategorie: {aktuelle_kategorie}

Aufgabe:
1. Bestimme die beste Kategorie aus dieser Liste: kultur, musik, food, sport, outdoor, community, nightlife, family, dating, sonstiges
2. Schreibe eine kurze, einladende Beschreibung auf Deutsch (max. 300 Zeichen)

Antworte NUR in diesem Format (zwei Zeilen):
KATEGORIE: [eine Kategorie aus der Liste]
BESCHREIBUNG: [kurze Beschreibung auf Deutsch, max. 300 Zeichen]"""

    try:
        antwort = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        antwort_text = antwort.content[0].text.strip()
        zeilen = antwort_text.split("\n")

        kategorie = None
        beschreibung = None

        for zeile in zeilen:
            if zeile.startswith("KATEGORIE:"):
                rohe_kategorie = zeile.replace("KATEGORIE:", "").strip().lower()
                if rohe_kategorie in GUELTIGE_KATEGORIEN:
                    kategorie = rohe_kategorie
                else:
                    logger.warning(
                        "Ungültige Kategorie von KI erhalten: '%s' – behalte '%s'",
                        rohe_kategorie, aktuelle_kategorie
                    )
                    kategorie = aktuelle_kategorie
            elif zeile.startswith("BESCHREIBUNG:"):
                beschreibung = zeile.replace("BESCHREIBUNG:", "").strip()
                # Auf max. 300 Zeichen kürzen
                if len(beschreibung) > 300:
                    beschreibung = beschreibung[:297] + "..."

        if not kategorie:
            kategorie = aktuelle_kategorie
        if not beschreibung:
            logger.warning("Keine Beschreibung von KI erhalten für Event: %s", titel)
            return None, None

        return kategorie, beschreibung

    except anthropic.RateLimitError:
        logger.error(
            "Claude API Rate Limit erreicht bei Event '%s' – warte 30 Sekunden", titel
        )
        time.sleep(30)
        return None, None
    except anthropic.APIStatusError as e:
        logger.error(
            "Claude API Fehler (Status %s) bei Event '%s': %s",
            e.status_code, titel, str(e)
        )
        return None, None
    except Exception as e:
        logger.error("Unerwarteter Fehler bei KI-Kategorisierung von '%s': %s", titel, str(e))
        return None, None


def kategorisieren(limit: int = 10) -> int:
    """
    Lädt Events mit status='neu' aus Supabase und kategorisiert sie mit Claude Haiku.
    Aktualisiert Beschreibung und ggf. korrigierte Kategorie in Supabase.
    Status bleibt 'neu' – Kategorisierung ist kein eigener Status-Schritt.

    Args:
        limit: Maximale Anzahl zu verarbeitender Events

    Returns:
        Anzahl erfolgreich verarbeiteter Events
    """
    logger.info("--- Kategorisierung gestartet (max. %d Events) ---", limit)

    try:
        db = get_supabase_client()
    except Exception as e:
        logger.error("Datenbankverbindung fehlgeschlagen: %s", str(e))
        return 0

    try:
        client = _claude_client_erstellen()
    except EnvironmentError as e:
        logger.error("Claude Client konnte nicht erstellt werden: %s", str(e))
        return 0

    # Events mit status='neu' laden
    try:
        ergebnis = (
            db.table("events")
            .select("id, titel, ort, datum, preis, kategorie")
            .eq("status", "neu")
            .is_("beschreibung", "null")
            .limit(limit)
            .execute()
        )
        events = ergebnis.data
    except Exception as e:
        logger.error("Fehler beim Laden der Events aus Supabase: %s", str(e))
        return 0

    if not events:
        logger.info("Keine Events mit status='neu' und fehlender Beschreibung gefunden.")
        return 0

    logger.info("%d Events zur Kategorisierung geladen", len(events))

    verarbeitet = 0

    for event in events:
        event_id = event.get("id")
        titel = event.get("titel", "?")

        logger.info("Kategorisiere Event: '%s'", titel)

        # Rate Limiting zwischen API Aufrufen
        if verarbeitet > 0:
            time.sleep(API_WARTEZEIT_SEKUNDEN)

        kategorie, beschreibung = _event_kategorisieren_und_beschreiben(client, event)

        if beschreibung is None:
            # Fehler bei diesem Event – Status auf 'fehler' setzen und weitermachen
            try:
                db.table("events").update({"status": "fehler"}).eq("id", event_id).execute()
                logger.warning("Event '%s' (ID: %s) auf Status 'fehler' gesetzt", titel, event_id)
            except Exception as update_fehler:
                logger.error(
                    "Konnte Status nicht aktualisieren für '%s': %s", titel, str(update_fehler)
                )
            continue

        # Supabase aktualisieren
        try:
            aktualisierung = {"beschreibung": beschreibung}

            # Kategorie nur aktualisieren wenn KI eine bessere vorschlägt
            if kategorie and kategorie != event.get("kategorie"):
                aktualisierung["kategorie"] = kategorie
                logger.info(
                    "Kategorie korrigiert: '%s' → '%s' für Event '%s'",
                    event.get("kategorie"), kategorie, titel
                )

            db.table("events").update(aktualisierung).eq("id", event_id).execute()
            verarbeitet += 1
            logger.info("Event kategorisiert: '%s' | Kategorie: %s", titel, kategorie)

        except Exception as e:
            logger.error(
                "Fehler beim Aktualisieren von Event '%s' (ID: %s): %s",
                titel, event_id, str(e)
            )
            # Status auf 'fehler' setzen
            try:
                db.table("events").update({"status": "fehler"}).eq("id", event_id).execute()
            except Exception:
                pass

    logger.info(
        "Kategorisierung abgeschlossen – %d von %d Events erfolgreich verarbeitet",
        verarbeitet, len(events)
    )
    return verarbeitet
