"""
eventbrite.py – DiesDasDüsseldorf
Scraper für die Eventbrite API v3: Events in Düsseldorf
Erstellt: 2026-02-24
"""
import logging
import os
import time
from datetime import date, datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

API_URL = "https://www.eventbriteapi.com/v3/events/search/"
QUELLE_NAME = "Eventbrite"

# Mapping Eventbrite category_id → DiesDasDüsseldorf-Kategorien
KATEGORIE_MAPPING = {
    "103": "musik",       # Music
    "101": "community",   # Business & Professional
    "110": "food",        # Food & Drink
    "104": "kultur",      # Film & Media
    "105": "kultur",      # Performing & Visual Arts
    "108": "sport",       # Sports & Fitness
    "107": "outdoor",     # Science & Technology
    "106": "community",   # Health & Wellness
    "113": "community",   # Community & Culture
    "115": "family",      # Family & Education
    "116": "nightlife",   # Holiday & Seasonal
    "117": "outdoor",     # Travel & Outdoor
    "118": "community",   # Charity & Causes
    "199": "sonstiges",   # Other
}


def _kategorie_mappen(category_id: Optional[str]) -> str:
    """
    Mappt eine numerische Eventbrite category_id auf eine
    DiesDasDüsseldorf-Kategorie.

    Args:
        category_id: Numerische Kategorie-ID als String oder None

    Returns:
        Gültige DiesDasDüsseldorf-Kategorie
    """
    if not category_id:
        return "sonstiges"
    return KATEGORIE_MAPPING.get(str(category_id), "sonstiges")


def _preis_ermitteln(event: dict) -> Optional[str]:
    """
    Ermittelt den Preis eines Events aus den Eventbrite API-Daten.

    Logik:
    - is_free == True → "kostenlos"
    - min == max → "ab {min}€"
    - min != max → "{min}€ – {max}€"
    - Keine Preis-Info vorhanden → None

    Args:
        event: Rohes Event-Dict aus der Eventbrite API

    Returns:
        Preisstring oder None
    """
    if event.get("is_free"):
        return "kostenlos"

    verfuegbarkeit = event.get("ticket_availability") or {}
    min_preis_obj = verfuegbarkeit.get("minimum_ticket_price") or {}
    max_preis_obj = verfuegbarkeit.get("maximum_ticket_price") or {}

    min_preis = min_preis_obj.get("major_value")
    max_preis = max_preis_obj.get("major_value")

    if min_preis is None and max_preis is None:
        return None

    try:
        min_val = float(min_preis) if min_preis is not None else None
        max_val = float(max_preis) if max_preis is not None else None

        if min_val is not None and max_val is not None:
            if min_val == max_val:
                return f"ab {min_val:.0f}€"
            return f"{min_val:.0f}€ – {max_val:.0f}€"

        if min_val is not None:
            return f"ab {min_val:.0f}€"

        if max_val is not None:
            return f"bis {max_val:.0f}€"

    except (ValueError, TypeError) as e:
        logger.warning("Preisangabe konnte nicht verarbeitet werden: %s", e)

    return None


def _event_mappen(event: dict, heute: date) -> Optional[dict]:
    """
    Mappt ein rohes Eventbrite API-Event-Objekt auf das
    DiesDasDüsseldorf Standard Event-Dict.

    Args:
        event: Rohes Event-Objekt aus der Eventbrite API-Antwort
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict im DiesDasDüsseldorf-Format oder None bei Fehler
        bzw. wenn das Event in der Vergangenheit liegt
    """
    try:
        # Titel
        name_obj = event.get("name") or {}
        titel = name_obj.get("text", "").strip()
        if not titel:
            logger.warning("Event ohne Titel übersprungen (ID: %s)", event.get("id"))
            return None

        # Datum und Uhrzeit aus "start.local" (Format: "2026-02-24T18:00:00")
        start_obj = event.get("start") or {}
        start_lokal = start_obj.get("local", "")
        if not start_lokal:
            logger.warning("Event ohne Startdatum übersprungen: %s", titel)
            return None

        try:
            start_dt = datetime.fromisoformat(start_lokal)
            datum = start_dt.date().isoformat()
            uhrzeit = start_dt.strftime("%H:%M")
        except ValueError as e:
            logger.warning(
                "Datum konnte nicht geparst werden für '%s': %s", titel, e
            )
            return None

        # Vergangene Events überspringen
        if date.fromisoformat(datum) < heute:
            return None

        # Venue / Ort
        venue = event.get("venue") or {}
        ort = venue.get("name", "").strip() or "Düsseldorf"

        # Adresse
        adresse_obj = venue.get("address") or {}
        adresse = adresse_obj.get("localized_address_display", "").strip() or None

        # Kategorie
        category_id = event.get("category_id")
        kategorie = _kategorie_mappen(category_id)

        # Bild
        logo_obj = event.get("logo") or {}
        bild_url = logo_obj.get("url") or None

        # Preis
        preis = _preis_ermitteln(event)

        # Quell-URL
        quelle_url = event.get("url", "").strip()
        if not quelle_url:
            logger.warning("Event ohne URL übersprungen: %s", titel)
            return None

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": adresse,
            "kategorie": kategorie,
            "beschreibung": None,
            "preis": preis,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "status": "neu",
        }

    except Exception as e:
        logger.error(
            "Fehler beim Mappen eines Eventbrite-Events: %s", str(e)
        )
        return None


def _api_request_mit_backoff(
    client: httpx.Client, params: dict, max_versuche: int = 3
) -> Optional[httpx.Response]:
    """
    Führt einen API-Request mit exponentiellem Backoff bei HTTP 429 durch.

    Args:
        client: Aktiver httpx-Client mit gesetzten Headern
        params: Query-Parameter für den API-Call
        max_versuche: Maximale Anzahl Versuche bei Rate-Limiting (Standard: 3)

    Returns:
        httpx.Response bei Erfolg, None bei dauerhaftem Fehler
    """
    wartezeit = 2  # Startwartezeit in Sekunden

    for versuch in range(1, max_versuche + 1):
        try:
            response = client.get(API_URL, params=params)

            if response.status_code == 429:
                if versuch < max_versuche:
                    logger.warning(
                        "Rate Limit erreicht (HTTP 429). "
                        "Warte %ds vor Versuch %d/%d ...",
                        wartezeit, versuch + 1, max_versuche
                    )
                    time.sleep(wartezeit)
                    wartezeit *= 2  # Exponentielles Backoff
                    continue
                else:
                    logger.error(
                        "Rate Limit nach %d Versuchen nicht überwunden. "
                        "Abbruch.",
                        max_versuche
                    )
                    return None

            response.raise_for_status()
            return response

        except httpx.TimeoutException:
            logger.error(
                "Timeout beim Eventbrite API-Call (Versuch %d/%d)",
                versuch, max_versuche
            )
            if versuch < max_versuche:
                time.sleep(wartezeit)
                wartezeit *= 2
            else:
                return None

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP Fehler %s bei Eventbrite API: %s",
                e.response.status_code, str(e)
            )
            return None

    return None


def scrape() -> list[dict]:
    """
    Ruft Events von der Eventbrite API v3 für Düsseldorf ab und
    gibt sie als Liste von DiesDasDüsseldorf Event-Dicts zurück.

    Benötigt die Umgebungsvariable EVENTBRITE_TOKEN. Ist diese nicht
    gesetzt oder leer, wird sofort eine leere Liste zurückgegeben.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events: list[dict] = []
    heute = date.today()

    # Token prüfen – Graceful Skip wenn nicht gesetzt
    token = os.getenv("EVENTBRITE_TOKEN", "").strip()
    if not token:
        logger.info(
            "EVENTBRITE_TOKEN nicht gesetzt – Eventbrite Scraper wird übersprungen."
        )
        return []

    logger.info("Starte Scraper: %s", QUELLE_NAME)

    params = {
        "location.address": "Düsseldorf,Germany",
        "location.within": "15km",
        "expand": "venue,ticket_availability",
        "sort_by": "date",
        "page_size": 50,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    try:
        time.sleep(2)  # Rate Limiting

        with httpx.Client(headers=headers, timeout=30, follow_redirects=True) as client:
            response = _api_request_mit_backoff(client, params)

            if response is None:
                logger.error(
                    "Eventbrite API nicht erreichbar. Scraper abgebrochen."
                )
                return []

            try:
                daten = response.json()
            except Exception as e:
                logger.error(
                    "Eventbrite API-Antwort konnte nicht als JSON gelesen werden: %s",
                    str(e)
                )
                return []

            roh_events = daten.get("events", [])
            logger.info("%d rohe Events von Eventbrite API empfangen", len(roh_events))

            # Duplikate innerhalb eines Scraper-Laufs verhindern
            gesehene_urls: set[str] = set()

            for roh_event in roh_events:
                url = roh_event.get("url", "")
                if url in gesehene_urls:
                    continue
                gesehene_urls.add(url)

                event = _event_mappen(roh_event, heute)
                if event:
                    events.append(event)

    except Exception as e:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(e))
        return []

    logger.info(
        "Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events)
    )
    return events


if __name__ == "__main__":
    # Direkter Testlauf
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    import json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
