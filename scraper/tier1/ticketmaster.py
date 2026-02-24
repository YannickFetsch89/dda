"""
ticketmaster.py – DiesDasDüsseldorf
Scraper für die Ticketmaster Discovery API: Events in Düsseldorf
Erstellt: 2026-02-24
"""
import logging
import os
import time
from datetime import date
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

QUELLE_NAME = "Ticketmaster"
API_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

# Mapping Ticketmaster-Segmente → DiesDasDüsseldorf-Kategorien
KATEGORIE_MAPPING = {
    "music": "musik",
    "sports": "sport",
    "arts & theatre": "kultur",
    "film": "kultur",
    "miscellaneous": "sonstiges",
    "family": "family",
}


def _bild_url_ermitteln(images: list[dict]) -> Optional[str]:
    """
    Wählt die beste Bild-URL aus der Ticketmaster-Bilderliste aus.
    Bevorzugt wird ein 16:9-Bild mit mindestens 640px Breite.
    Fallback: erstes verfügbares Bild.

    Args:
        images: Liste von Bild-Dicts aus der Ticketmaster-Antwort

    Returns:
        Bild-URL als String oder None wenn keine Bilder vorhanden
    """
    if not images:
        return None

    # Bevorzugtes Bild: Verhältnis 16_9, mindestens 640px Breite
    for bild in images:
        ratio = bild.get("ratio", "")
        breite = bild.get("width", 0)
        url = bild.get("url")
        if ratio == "16_9" and breite >= 640 and url:
            return url

    # Fallback: erstes verfügbares Bild
    return images[0].get("url") if images[0].get("url") else None


def _preis_formatieren(preis_bereiche: list[dict]) -> Optional[str]:
    """
    Formatiert Preisangaben aus der Ticketmaster-Antwort.
    Beispiele: "ab 25€" (wenn min==max), "25€ – 80€" (bei Preisspanne).

    Args:
        preis_bereiche: Liste von Preisbereich-Dicts aus der Ticketmaster-Antwort

    Returns:
        Formatierter Preisstring oder None wenn keine Preisinfo vorhanden
    """
    if not preis_bereiche:
        return None

    try:
        eintrag = preis_bereiche[0]
        min_preis = eintrag.get("min")
        max_preis = eintrag.get("max")

        if min_preis is None:
            return None

        # Preiswerte als ganze Zahlen formatieren wenn keine Nachkommastellen
        def preis_str(wert: float) -> str:
            if wert == int(wert):
                return f"{int(wert)}€"
            return f"{wert:.2f}€"

        if max_preis is None or min_preis == max_preis:
            return f"ab {preis_str(min_preis)}"

        return f"{preis_str(min_preis)} – {preis_str(max_preis)}"

    except (KeyError, TypeError, ValueError) as e:
        logger.warning("Preis konnte nicht formatiert werden: %s", e)
        return None


def _kategorie_erkennen(klassifizierungen: list[dict]) -> str:
    """
    Mappt Ticketmaster-Klassifizierungen auf DiesDasDüsseldorf-Kategorien.

    Args:
        klassifizierungen: Liste von Klassifizierungs-Dicts aus der API-Antwort

    Returns:
        Gültige DiesDasDüsseldorf-Kategorie
    """
    if not klassifizierungen:
        return "sonstiges"

    try:
        segment = klassifizierungen[0].get("segment", {})
        segment_name = segment.get("name", "").lower()
        return KATEGORIE_MAPPING.get(segment_name, "sonstiges")
    except (IndexError, AttributeError, KeyError):
        return "sonstiges"


def _event_parsen(event: dict, heute: date) -> Optional[dict]:
    """
    Wandelt ein Ticketmaster-API-Event in ein DiesDasDüsseldorf Event-Dict um.

    Args:
        event: Rohes Event-Dict aus der Ticketmaster Discovery API
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict im DiesDasDüsseldorf-Format oder None bei fehlenden Pflichtfeldern
        bzw. wenn das Event in der Vergangenheit liegt
    """
    try:
        # Titel (Pflichtfeld)
        titel = event.get("name", "").strip()
        if not titel:
            logger.warning("Event ohne Titel übersprungen.")
            return None

        # Datum (Pflichtfeld)
        datum_info = event.get("dates", {}).get("start", {})
        datum = datum_info.get("localDate")
        if not datum:
            logger.warning("Kein Datum für Event '%s' – wird übersprungen.", titel)
            return None

        # Vergangene Events herausfiltern
        try:
            event_datum = date.fromisoformat(datum)
        except ValueError:
            logger.warning("Ungültiges Datumsformat '%s' für Event '%s'.", datum, titel)
            return None

        if event_datum < heute:
            return None

        # Uhrzeit (optional, ohne Sekunden)
        uhrzeit_roh = datum_info.get("localTime")
        uhrzeit = uhrzeit_roh[:5] if uhrzeit_roh else None

        # Venue-Informationen
        venues = event.get("_embedded", {}).get("venues", [])
        venue = venues[0] if venues else {}

        # Ort (Pflichtfeld)
        ort = venue.get("name", "").strip()
        if not ort:
            logger.warning("Kein Ort für Event '%s' – wird übersprungen.", titel)
            return None

        # Adresse (optional)
        adresse = venue.get("address", {}).get("line1")
        if adresse:
            adresse = adresse.strip() or None

        # Kategorie
        klassifizierungen = event.get("classifications", [])
        kategorie = _kategorie_erkennen(klassifizierungen)

        # Preis (optional)
        preis_bereiche = event.get("priceRanges", [])
        preis = _preis_formatieren(preis_bereiche)

        # Quell-URL (Pflichtfeld)
        quelle_url = event.get("url", "").strip()
        if not quelle_url:
            logger.warning("Keine URL für Event '%s' – wird übersprungen.", titel)
            return None

        # Bild-URL (optional)
        bilder = event.get("images", [])
        bild_url = _bild_url_ermitteln(bilder)

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
        logger.error("Fehler beim Parsen eines Ticketmaster-Events: %s", str(e))
        return None


def _api_anfrage_mit_backoff(client: httpx.Client, params: dict) -> Optional[httpx.Response]:
    """
    Führt eine API-Anfrage mit exponentiellem Backoff bei HTTP 429 durch.
    Maximal 3 Versuche mit Wartezeiten von 2s, 4s und 8s.

    Args:
        client: httpx.Client-Instanz
        params: Query-Parameter für die API-Anfrage

    Returns:
        httpx.Response bei Erfolg, None bei endgültigem Fehler
    """
    wartezeiten = [2, 4, 8]

    for versuch, wartezeit in enumerate(wartezeiten, start=1):
        try:
            response = client.get(API_URL, params=params, timeout=30)

            if response.status_code == 429:
                if versuch < len(wartezeiten):
                    logger.warning(
                        "HTTP 429 – zu viele Anfragen. Warte %ds vor Versuch %d/%d.",
                        wartezeit, versuch + 1, len(wartezeiten)
                    )
                    time.sleep(wartezeit)
                    continue
                else:
                    logger.error(
                        "HTTP 429 nach %d Versuchen – Ticketmaster-API nicht erreichbar.",
                        len(wartezeiten)
                    )
                    return None

            response.raise_for_status()
            return response

        except httpx.TimeoutException:
            logger.error("Timeout beim Abrufen der Ticketmaster API (Versuch %d/%d).",
                         versuch, len(wartezeiten))
            if versuch < len(wartezeiten):
                time.sleep(wartezeit)
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP Fehler %s bei der Ticketmaster API: %s",
                e.response.status_code, str(e)
            )
            return None

    return None


def scrape() -> list[dict]:
    """
    Ruft Events aus der Ticketmaster Discovery API für Düsseldorf ab.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
        Gibt eine leere Liste zurück wenn kein API-Key gesetzt ist oder
        ein Fehler aufgetreten ist.
    """
    api_key = os.getenv("TICKETMASTER_API_KEY", "")

    # Graceful Skip wenn kein API-Key konfiguriert
    if not api_key:
        logger.info(
            "TICKETMASTER_API_KEY ist nicht gesetzt – Ticketmaster-Scraper wird übersprungen."
        )
        return []

    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    params = {
        "apikey": api_key,
        "city": "Düsseldorf",
        "countryCode": "DE",
        "size": 50,
        "locale": "*",
        "sort": "date,asc",
    }

    try:
        time.sleep(2)  # Rate Limiting

        with httpx.Client(timeout=30) as client:
            response = _api_anfrage_mit_backoff(client, params)

            if response is None:
                logger.error("Ticketmaster API-Anfrage endgültig fehlgeschlagen.")
                return []

            try:
                daten = response.json()
            except Exception as e:
                logger.error("Ticketmaster API-Antwort konnte nicht als JSON gelesen werden: %s", e)
                return []

        # Eingebettete Events extrahieren
        eingebettet = daten.get("_embedded", {})
        rohe_events = eingebettet.get("events", [])

        if not rohe_events:
            logger.info("Keine Events von der Ticketmaster API erhalten.")
            return []

        logger.info("%d Events von der Ticketmaster API empfangen.", len(rohe_events))

        # Duplikate innerhalb eines Scraper-Laufs verhindern
        gesehene_urls: set[str] = set()

        for roher_event in rohe_events:
            url = roher_event.get("url", "")
            if url and url in gesehene_urls:
                continue
            if url:
                gesehene_urls.add(url)

            event = _event_parsen(roher_event, heute)
            if event:
                events.append(event)

    except Exception as e:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(e))
        return []

    logger.info("Scraper %s fertig: %d Events gefunden.", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    # Direkter Testlauf
    from dotenv import load_dotenv
    load_dotenv()
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
