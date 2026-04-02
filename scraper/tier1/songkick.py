"""
songkick.py – DiesDasDüsseldorf
Integration der Songkick API für Konzert-Events in Düsseldorf.
API-Dokumentation: https://www.songkick.com/developer

Songkick bietet strukturierte Konzertdaten mit offizieller API.
Düsseldorf Metro Area ID: 28470

Authentifizierung: API Key via Umgebungsvariable SONGKICK_API_KEY

Erstellt: 2026-04-02
"""
import logging
import os
import time
from datetime import date, timedelta
from typing import Optional

import httpx

from config import SCRAPER_VORSCHAU_TAGE

logger = logging.getLogger(__name__)

QUELLE_NAME = "Songkick"
API_BASE_URL = "https://api.songkick.com/api/3.0"
# Düsseldorf Metro Area ID auf Songkick
METRO_AREA_ID = 28470

# Kategorie ist immer musik für Songkick (Konzert-Aggregator)
KATEGORIE_STANDARD = "musik"


def _bild_url_ermitteln(event: dict) -> Optional[str]:
    """
    Extrahiert die beste verfügbare Bild-URL aus einem Songkick-Event.

    Args:
        event: Songkick Event-Dict

    Returns:
        Bild-URL als String oder None
    """
    # Songkick liefert keine direkten Bilder in der Metro-Events-API
    # Künstler-Bilder wären über separate Anfragen verfügbar
    return None


def _preis_formatieren(event: dict) -> Optional[str]:
    """
    Extrahiert Preisangaben aus einem Songkick-Event.

    Args:
        event: Songkick Event-Dict

    Returns:
        Formatierter Preisstring oder None
    """
    performance = event.get("performance", [])
    if not performance:
        return None

    # Songkick liefert keine direkten Preise in der freien API
    return None


def _kategorie_aus_typ(event_typ: str) -> str:
    """
    Mappt den Songkick-Event-Typ auf DiesDasDüsseldorf-Kategorien.

    Args:
        event_typ: Songkick Event-Typ (z.B. 'Concert', 'Festival')

    Returns:
        Gültige DiesDasDüsseldorf-Kategorie
    """
    typ_mapping = {
        "Concert": "musik",
        "Festival": "musik",
        "club night": "nightlife",
    }
    return typ_mapping.get(event_typ, "musik")


def _event_parsen(event: dict, heute: date) -> Optional[dict]:
    """
    Wandelt ein Songkick-API-Event in ein DiesDasDüsseldorf Event-Dict um.

    Args:
        event: Rohes Event-Dict aus der Songkick API
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict im DiesDasDüsseldorf-Format oder None
    """
    try:
        # Titel aus Hauptkünstler oder Display-Name
        performances = event.get("performance", [])
        if performances:
            hauptkuenstler = performances[0].get("artist", {}).get("displayName", "")
            if len(performances) > 1:
                weitere = [p.get("artist", {}).get("displayName", "") for p in performances[1:3]]
                titel = f"{hauptkuenstler} + {', '.join(w for w in weitere if w)}"
            else:
                titel = hauptkuenstler
        else:
            titel = event.get("displayName", "").strip()

        if not titel:
            logger.warning("Songkick-Event ohne Titel übersprungen.")
            return None

        # Datum
        start = event.get("start", {})
        datum = start.get("date")
        if not datum:
            logger.warning("Kein Datum für Songkick-Event '%s'.", titel)
            return None

        try:
            event_datum = date.fromisoformat(datum)
        except ValueError:
            logger.warning("Ungültiges Datumsformat '%s' für Event '%s'.", datum, titel)
            return None

        if event_datum < heute:
            return None

        # Uhrzeit
        uhrzeit = start.get("time")
        if uhrzeit:
            uhrzeit = uhrzeit[:5]  # Nur HH:MM

        # Venue / Ort
        venue = event.get("venue", {})
        ort = venue.get("displayName", "").strip()
        if not ort:
            logger.warning("Kein Ort für Songkick-Event '%s'.", titel)
            return None

        # Adresse (aus Location)
        location = venue.get("city", {})
        adresse = None
        if location:
            stadt = location.get("displayName", "")
            if stadt:
                adresse = f"{ort}, {stadt}"

        # Quell-URL
        quelle_url = event.get("uri", "").strip()
        if not quelle_url:
            logger.warning("Keine URL für Songkick-Event '%s'.", titel)
            return None

        # Kategorie
        event_typ = event.get("type", "Concert")
        kategorie = _kategorie_aus_typ(event_typ)

        # Beschreibung aus Display-Name
        beschreibung = event.get("displayName", "")[:300] if event.get("displayName") else None

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": adresse,
            "kategorie": kategorie,
            "beschreibung": beschreibung,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": None,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error("Fehler beim Parsen eines Songkick-Events: %s", str(fehler))
        return None


def _api_anfrage_mit_backoff(client: httpx.Client, url: str, params: dict) -> Optional[httpx.Response]:
    """
    Führt eine Songkick API-Anfrage mit exponentiellem Backoff bei HTTP 429 durch.

    Args:
        client: httpx.Client-Instanz
        url: API-URL
        params: Query-Parameter

    Returns:
        httpx.Response bei Erfolg, None bei endgültigem Fehler
    """
    wartezeiten = [2, 4, 8]

    for versuch, wartezeit in enumerate(wartezeiten, start=1):
        try:
            response = client.get(url, params=params, timeout=30)

            if response.status_code == 429:
                if versuch < len(wartezeiten):
                    logger.warning(
                        "HTTP 429 – zu viele Anfragen. Warte %ds vor Versuch %d/%d.",
                        wartezeit, versuch + 1, len(wartezeiten),
                    )
                    time.sleep(wartezeit)
                    continue
                else:
                    logger.error("HTTP 429 nach %d Versuchen – Songkick API nicht erreichbar.", len(wartezeiten))
                    return None

            response.raise_for_status()
            return response

        except httpx.TimeoutException:
            logger.error("Timeout bei Songkick API (Versuch %d/%d).", versuch, len(wartezeiten))
            if versuch < len(wartezeiten):
                time.sleep(wartezeit)
        except httpx.HTTPStatusError as e:
            logger.error("HTTP Fehler %s bei der Songkick API: %s", e.response.status_code, str(e))
            return None

    return None


def scrape() -> list[dict]:
    """
    Ruft Konzert-Events aus der Songkick API für Düsseldorf ab.

    Nutzt die Metro Area Events Endpoint für die Düsseldorf Metro Area (ID: 28470).
    Gibt eine leere Liste zurück wenn kein API-Key konfiguriert ist.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    api_key = os.getenv("SONGKICK_API_KEY", "")

    if not api_key:
        logger.info("SONGKICK_API_KEY nicht gesetzt – Songkick-Scraper wird übersprungen.")
        return []

    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    url = f"{API_BASE_URL}/metro_areas/{METRO_AREA_ID}/calendar.json"

    params = {
        "apikey": api_key,
        "min_date": heute.isoformat(),
        "max_date": enddatum.isoformat(),
        "per_page": 50,
        "page": 1,
    }

    try:
        time.sleep(2)  # Rate Limiting

        with httpx.Client(timeout=30) as client:
            # Paginierung: bis zu 5 Seiten abrufen
            for seite in range(1, 6):
                params["page"] = seite
                response = _api_anfrage_mit_backoff(client, url, params)

                if response is None:
                    logger.error("Songkick API-Anfrage fehlgeschlagen (Seite %d).", seite)
                    break

                try:
                    daten = response.json()
                except Exception as e:
                    logger.error("Songkick API-Antwort konnte nicht als JSON gelesen werden: %s", e)
                    break

                resultat = daten.get("resultsPage", {})
                ergebnisse = resultat.get("results", {})
                rohe_events = ergebnisse.get("event", [])

                if not rohe_events:
                    logger.info("Keine weiteren Events auf Seite %d.", seite)
                    break

                logger.info("Songkick Seite %d: %d Events empfangen.", seite, len(rohe_events))

                gesehene_urls: set[str] = set()
                for roher_event in rohe_events:
                    event_url = roher_event.get("uri", "")
                    if event_url and event_url in gesehene_urls:
                        continue
                    if event_url:
                        gesehene_urls.add(event_url)

                    event = _event_parsen(roher_event, heute)
                    if event:
                        events.append(event)

                # Prüfen ob weitere Seiten vorhanden sind
                gesamt = resultat.get("totalEntries", 0)
                pro_seite = resultat.get("perPage", 50)
                if seite * pro_seite >= gesamt:
                    break

                time.sleep(2)  # Rate Limiting zwischen Seiten

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(fehler))
        return []

    logger.info("Scraper %s fertig: %d Events gefunden.", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
