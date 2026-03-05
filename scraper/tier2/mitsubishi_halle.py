"""
mitsubishi_halle.py – DiesDasDüsseldorf
Scraper für die Mitsubishi Electric HALLE Düsseldorf.

Strategie:
Die Website nutzt ein TYPO3-CMS mit einem JavaScript-basierten Event-Kalender.
Die Event-Daten werden via jQuery AJAX vom internen JSON-Endpoint
/events-tickets/eventkalender/dates geladen.

Der Endpoint liefert ein JSON-Objekt mit einem "dates"-Array,
das alle kommenden Events enthält.

URL: https://www.mitsubishi-electric-halle.de
API: https://www.mitsubishi-electric-halle.de/events-tickets/eventkalender/dates
Adresse: Siegburger Str. 15, 40591 Düsseldorf
Erstellt: 2026-03-05
"""
import logging
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

import httpx

from config import SCRAPER_VORSCHAU_TAGE

logger = logging.getLogger(__name__)

BASE_URL = "https://www.mitsubishi-electric-halle.de"
API_URL = "https://www.mitsubishi-electric-halle.de/events-tickets/eventkalender/dates"
QUELLE_NAME = "Mitsubishi Electric HALLE"
ORT_STANDARD = "Mitsubishi Electric HALLE"
ADRESSE_STANDARD = "Siegburger Str. 15, 40591 Düsseldorf"

# Event-Typ zu Kategorie Mapping
TYPEN_MAPPING: dict[str, str] = {
    "konzerte": "musik",
    "shows": "kultur",
    "festivals": "musik",
    "ausstellungen": "kultur",
    "workshops": "community",
    "dj sessions": "nightlife",
    "sport": "sport",
    "special events": "sonstiges",
    "familienveranstaltungen": "family",
    "comedy": "kultur",
    "musicals": "kultur",
    "theater": "kultur",
    "dance": "musik",
    "pop": "musik",
    "rock": "musik",
    "metal": "musik",
    "hip hop": "musik",
    "electronic": "nightlife",
}

TITEL_KATEGORIE_MAPPING: dict[str, str] = {
    "konzert": "musik",
    "live": "musik",
    "festival": "musik",
    "tour": "musik",
    "comedy": "kultur",
    "show": "kultur",
    "musical": "kultur",
    "theater": "kultur",
    "boxing": "sport",
    "wrestl": "sport",
    "mma": "sport",
    "ufc": "sport",
    "basketball": "sport",
    "hockey": "sport",
    "party": "nightlife",
    "kids": "family",
    "kinder": "family",
}


def _kategorie_erkennen(typ_text: str, titel: str) -> str:
    """
    Erkennt Kategorie aus Event-Typ und Titel.

    Args:
        typ_text: Event-Typ-Text aus der API
        titel: Event-Titel

    Returns:
        Gültige Kategorie
    """
    if typ_text:
        typ_lower = typ_text.lower()
        for schluessel, kategorie in TYPEN_MAPPING.items():
            if schluessel in typ_lower:
                return kategorie

    if titel:
        titel_lower = titel.lower()
        for schluessel, kategorie in TITEL_KATEGORIE_MAPPING.items():
            if schluessel in titel_lower:
                return kategorie

    return "musik"  # Standard für Konzerthalle


def _datum_und_uhrzeit_aus_iso(iso_string: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Extrahiert Datum (YYYY-MM-DD) und Uhrzeit (HH:MM) aus ISO-8601-String.

    Args:
        iso_string: ISO-8601-Datumsstring aus der API

    Returns:
        Tupel (datum_iso, uhrzeit_hhmm) – beide können None sein
    """
    if not iso_string:
        return None, None
    try:
        # Format: "2026-03-06T19:05:00.000Z"
        teile = iso_string.replace("Z", "").split("T")
        datum = teile[0] if len(teile) >= 1 else None
        uhrzeit = teile[1][:5] if len(teile) >= 2 else None
        # Datum validieren
        if datum:
            date.fromisoformat(datum)
        return datum, uhrzeit
    except (ValueError, IndexError):
        return None, None


def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen der Mitsubishi Electric HALLE.

    Ruft den internen JSON-Endpoint ab, der alle kommenden Events liefert.
    Abgesagte Events (status="canceled") werden übersprungen.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.mitsubishi-electric-halle.de/events-tickets/eventkalender",
    }

    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=30) as client:
            try:
                antwort = client.get(API_URL, params={"total": "9999"})
                antwort.raise_for_status()
            except httpx.HTTPStatusError as err:
                logger.error("MEH API HTTP-Fehler: %s", err)
                return []
            except httpx.RequestError as err:
                logger.error("MEH API Verbindungsfehler: %s", err)
                return []

            # JSON parsen
            try:
                daten = antwort.json()
            except Exception as err:
                logger.error("MEH API: Ungültiges JSON – %s", err)
                return []

            rohe_events = daten.get("dates", [])
            if not rohe_events:
                logger.warning("MEH API lieferte keine Events (leeres dates-Array)")
                return []

            logger.info("MEH API: %d Roh-Events erhalten", len(rohe_events))

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []

    events: list[dict] = []
    gesehene_schluessel: set[str] = set()

    for eintrag in rohe_events:
        try:
            # Abgesagte Events überspringen
            if eintrag.get("status") == "canceled":
                continue

            titel = (eintrag.get("title") or "").strip()
            if not titel:
                continue

            # Datum aus date.formatted
            datum_info = eintrag.get("date") or {}
            datum_str, uhrzeit = _datum_und_uhrzeit_aus_iso(
                datum_info.get("starting_time") or datum_info.get("formatted")
            )

            if not datum_str:
                continue

            try:
                datum_obj = date.fromisoformat(datum_str)
            except ValueError:
                continue

            if datum_obj < heute or datum_obj > enddatum:
                continue

            # Bild-URL
            bild_url: Optional[str] = eintrag.get("image") or None

            # Quelle-URL
            detail_url = eintrag.get("url_detail") or ""
            quelle_url = urljoin(BASE_URL, detail_url) if detail_url else BASE_URL

            # Beschreibung
            beschreibung_roh = (eintrag.get("description") or "").strip()
            beschreibung: Optional[str] = beschreibung_roh[:300] if beschreibung_roh else None

            # Kategorie aus Event-Typ
            typ_text = eintrag.get("type") or ""
            kategorie = _kategorie_erkennen(typ_text, titel)

            # Eintrittsstatus (nicht verfügbar = ausverkauft, aber nicht abgesagt)
            verfuegbar = eintrag.get("available", 1)
            preis: Optional[str] = None
            if verfuegbar == 0:
                preis = "ausverkauft"

            schluessel = f"{titel}_{datum_str}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum_str,
                "uhrzeit": uhrzeit,
                "ort": ORT_STANDARD,
                "adresse": ADRESSE_STANDARD,
                "kategorie": kategorie,
                "beschreibung": beschreibung,
                "preis": preis,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "instagram_caption": None,
                "datum_bis": None,
                "ist_wiederkehrend": False,
                "status": "neu",
            })

        except Exception as fehler:
            logger.error("Fehler beim Verarbeiten eines MEH-Events: %s", fehler)
            continue

    logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json as _json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:5]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
