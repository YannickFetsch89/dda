"""
caption_generator.py – DiesDasDüsseldorf
Generiert Instagram-Captions für Events mit Claude Sonnet.
Verarbeitet Events mit status='neu' und vorhandener Beschreibung.
Erstellt: 2026-02-24
"""
import logging
import os
import time
from datetime import date

import anthropic
from dotenv import load_dotenv

from database.client import get_supabase_client

load_dotenv()

logger = logging.getLogger(__name__)

# Maximale Caption-Länge laut Instagram-Richtlinien
MAX_CAPTION_LAENGE = 2200

# Wartezeit zwischen Claude API Aufrufen (Rate Limiting)
API_WARTEZEIT_SEKUNDEN = 1

# Deutsche Wochentage
WOCHENTAGE_DE = {
    0: "Montag",
    1: "Dienstag",
    2: "Mittwoch",
    3: "Donnerstag",
    4: "Freitag",
    5: "Samstag",
    6: "Sonntag",
}

# Deutsche Monatsnamen
MONATE_DE = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April",
    5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
    9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
}


def _datum_formatieren(datum_iso: str) -> str:
    """
    Wandelt ein ISO-Datum in eine deutsche Datumsangabe um.
    Beispiel: '2026-02-24' → 'Dienstag, 24. Februar 2026'

    Args:
        datum_iso: Datum im ISO-Format (YYYY-MM-DD)

    Returns:
        Ausgeschriebenes deutsches Datum
    """
    try:
        datum = date.fromisoformat(datum_iso)
        wochentag = WOCHENTAGE_DE[datum.weekday()]
        monat = MONATE_DE[datum.month]
        return f"{wochentag}, {datum.day}. {monat} {datum.year}"
    except (ValueError, KeyError) as e:
        logger.warning("Datum konnte nicht formatiert werden: '%s' – %s", datum_iso, e)
        return datum_iso


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


def _caption_generieren(
    client: anthropic.Anthropic,
    event: dict
) -> str | None:
    """
    Generiert eine Instagram-Caption für ein Event mit Claude Sonnet.

    Args:
        client: Anthropic API Client
        event: Event-Dict mit allen relevanten Feldern

    Returns:
        Fertige Instagram-Caption oder None bei Fehler
    """
    titel = event.get("titel", "")
    ort = event.get("ort", "")
    datum_iso = event.get("datum", "")
    uhrzeit = event.get("uhrzeit")
    kategorie = event.get("kategorie", "sonstiges")
    beschreibung = event.get("beschreibung", "")
    preis = event.get("preis")
    quelle_url = event.get("quelle_url", "")

    # Datum ausschreiben
    datum_ausgeschrieben = _datum_formatieren(datum_iso)

    # Zeitangabe vorbereiten
    zeitangabe = f"{uhrzeit} Uhr" if uhrzeit else "Uhrzeit nach Ankündigung"

    # Preisangabe vorbereiten
    preisangabe = preis if preis else "Eintritt nicht angegeben"

    prompt = f"""Du schreibst Instagram-Captions für einen Düsseldorf Stadtguide namens DiesDasDüsseldorf.

Event-Informationen:
- Titel: {titel}
- Datum: {datum_ausgeschrieben}
- Uhrzeit: {zeitangabe}
- Ort: {ort}
- Kategorie: {kategorie}
- Beschreibung: {beschreibung}
- Preis: {preisangabe}
- Link: {quelle_url}

Schreibe eine Instagram-Caption auf Deutsch mit diesen Regeln:
1. Beginne DIREKT mit Datum, Uhrzeit und Ort (z.B. "Dienstag, 24. Februar | 20:00 Uhr | Tonhalle Düsseldorf")
2. Locker und einladend – als würdest du einem Freund empfehlen
3. Kein Clickbait, keine übertriebene Werbesprache
4. Maximal 2200 Zeichen gesamt
5. Am Ende mindestens 5 passende Hashtags (immer #düsseldorf und #dusevents dabei)
6. Keine Emojis außer 1-2 passende am Anfang oder Ende

Antworte NUR mit dem Caption-Text, ohne Erklärungen davor oder danach."""

    try:
        antwort = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        caption = antwort.content[0].text.strip()

        # Länge prüfen und ggf. kürzen
        if len(caption) > MAX_CAPTION_LAENGE:
            logger.warning(
                "Caption für '%s' zu lang (%d Zeichen) – wird gekürzt",
                titel, len(caption)
            )
            # Beim letzten vollständigen Satz abschneiden
            caption = caption[:MAX_CAPTION_LAENGE - 3] + "..."

        return caption

    except anthropic.RateLimitError:
        logger.error(
            "Claude API Rate Limit erreicht bei Event '%s' – warte 30 Sekunden", titel
        )
        time.sleep(30)
        return None
    except anthropic.APIStatusError as e:
        logger.error(
            "Claude API Fehler (Status %s) bei Event '%s': %s",
            e.status_code, titel, str(e)
        )
        return None
    except Exception as e:
        logger.error(
            "Unerwarteter Fehler bei Caption-Generierung für '%s': %s", titel, str(e)
        )
        return None


def captions_generieren(limit: int = 10) -> int:
    """
    Lädt Events mit status='neu' und vorhandener Beschreibung aus Supabase
    und generiert Instagram-Captions mit Claude Sonnet.
    Setzt Status auf 'aufbereitet' nach erfolgreicher Generierung.

    Args:
        limit: Maximale Anzahl zu verarbeitender Events

    Returns:
        Anzahl erfolgreich verarbeiteter Events
    """
    logger.info("--- Caption-Generierung gestartet (max. %d Events) ---", limit)

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

    # Events mit status='neu' und vorhandener Beschreibung laden
    try:
        ergebnis = (
            db.table("events")
            .select("id, titel, ort, datum, uhrzeit, kategorie, beschreibung, preis, quelle_url")
            .eq("status", "neu")
            .not_.is_("beschreibung", "null")
            .limit(limit)
            .execute()
        )
        events = ergebnis.data
    except Exception as e:
        logger.error("Fehler beim Laden der Events aus Supabase: %s", str(e))
        return 0

    if not events:
        logger.info(
            "Keine Events mit status='neu' und vorhandener Beschreibung gefunden."
        )
        return 0

    logger.info("%d Events zur Caption-Generierung geladen", len(events))

    verarbeitet = 0

    for event in events:
        event_id = event.get("id")
        titel = event.get("titel", "?")

        logger.info("Generiere Caption für Event: '%s'", titel)

        # Rate Limiting zwischen API Aufrufen
        if verarbeitet > 0:
            time.sleep(API_WARTEZEIT_SEKUNDEN)

        caption = _caption_generieren(client, event)

        if caption is None:
            # Fehler bei diesem Event – Status auf 'fehler' setzen und weitermachen
            try:
                db.table("events").update({"status": "fehler"}).eq("id", event_id).execute()
                logger.warning(
                    "Event '%s' (ID: %s) auf Status 'fehler' gesetzt", titel, event_id
                )
            except Exception as update_fehler:
                logger.error(
                    "Konnte Status nicht aktualisieren für '%s': %s",
                    titel, str(update_fehler)
                )
            continue

        # Supabase aktualisieren: Caption speichern und Status auf 'aufbereitet' setzen
        try:
            db.table("events").update({
                "instagram_caption": caption,
                "status": "aufbereitet",
            }).eq("id", event_id).execute()

            verarbeitet += 1
            logger.info(
                "Caption generiert für '%s' – Status: aufbereitet (%d Zeichen)",
                titel, len(caption)
            )

        except Exception as e:
            logger.error(
                "Fehler beim Speichern der Caption für '%s' (ID: %s): %s",
                titel, event_id, str(e)
            )
            # Status auf 'fehler' setzen
            try:
                db.table("events").update({"status": "fehler"}).eq("id", event_id).execute()
            except Exception:
                pass

    logger.info(
        "Caption-Generierung abgeschlossen – %d von %d Events erfolgreich verarbeitet",
        verarbeitet, len(events)
    )
    return verarbeitet
