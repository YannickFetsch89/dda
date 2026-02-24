"""
dlive.py – DiesDasDüsseldorf
Scraper für d.live Düsseldorf: Veranstaltungen in der Merkur Spiel-Arena,
PSD BANK DOME, Mitsubishi Electric HALLE, Rheinterrasse und CASTELLO.

Die Seite lädt Events via AJAX-Call an den internen JSON-Endpunkt
/events/eventkalender/dates?total=9999. Dieser gibt alle zukünftigen Events
als strukturiertes JSON zurück – kein JavaScript-Rendering nötig.

API-Response-Struktur:
  {
    "dates": [
      {
        "id": "date_1623",
        "title": "Fortuna Düsseldorf - VfL Bochum",
        "type": "Sport-Events",
        "subtype": "Fussball",
        "status": "regular",
        "venue": "venue_1",
        "venue_image": "https://...logo-merkur.svg",
        "image": "https://...event-bild.jpg",
        "url_detail": "https://www.merkur-spiel-arena.de/event/...",
        "date": {
          "formatted": "2026-02-27T18:30:00.000Z",
          "starting_time": "2026-02-27T18:30:00.000Z"
        }
      },
      ...
    ],
    "months": [...]
  }

Erstellt: 2026-02-24
"""
import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import httpx

from config import SCRAPER_VORSCHAU_TAGE

logger = logging.getLogger(__name__)

# --- Konstanten -----------------------------------------------------------

BASE_URL = "https://www.d-live.de"
API_URL = "https://www.d-live.de/events/eventkalender/dates"
QUELLE_NAME = "d-live"

# Venue-ID → (Venue-Name, Adresse)
VENUE_MAP: dict[str, tuple[str, str]] = {
    "venue_1":  ("Merkur Spiel-Arena", "Arena-Straße 1, 40474 Düsseldorf"),
    "venue_2":  ("PSD BANK DOME", "Siegburger Straße 15, 40591 Düsseldorf"),
    "venue_3":  ("Mitsubishi Electric HALLE", "Siegburger Straße 15, 40591 Düsseldorf"),
    "venue_4":  ("CASTELLO Düsseldorf", "Auf'm Hennekamp 71, 40225 Düsseldorf"),
    "venue_14": ("OPEN AIR PARK Düsseldorf", "Arena-Straße 1, 40474 Düsseldorf"),
    "venue_19": ("Rheinterrasse", "Joseph-Beuys-Ufer 33, 40479 Düsseldorf"),
}

# Event-Typ-Feld der API → DDA-Kategorie
TYP_KATEGORIE_MAP: dict[str, str] = {
    "konzerte": "musik",
    "sport-events": "sport",
    "shows": "sonstiges",
    "messen & kongresse": "community",
    "partys": "nightlife",
    "parties": "nightlife",
    "festival": "musik",
    "ausstellungen": "kultur",
    "workshops": "community",
    "dj sessions": "nightlife",
}


# --- Hilfsfunktionen ------------------------------------------------------

def _datum_uhrzeit_parsen(iso_string: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Zerlegt einen ISO-8601-Zeitstempel aus der API in Datum und Uhrzeit.

    Args:
        iso_string: Zeitstempel wie "2026-02-27T18:30:00.000Z"

    Returns:
        Tupel (datum_iso, uhrzeit_hhmm) oder (None, None) bei Fehler
    """
    if not iso_string:
        return None, None

    try:
        # API liefert UTC-Zeitstempel – für Datum/Uhrzeit-Anzeige als Lokalzeit
        # behandeln (die Uhrzeiten sind in der API bereits in lokaler Zeit
        # gespeichert, nur das Z-Suffix ist nominell)
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        # Datum
        datum = dt.date().isoformat()
        # Uhrzeit (nur wenn nicht Mitternacht – dann kein sinnvoller Wert)
        if dt.hour == 0 and dt.minute == 0:
            uhrzeit = None
        else:
            uhrzeit = f"{dt.hour:02d}:{dt.minute:02d}"
        return datum, uhrzeit

    except (ValueError, AttributeError) as fehler:
        logger.warning(
            "Datum/Uhrzeit konnte nicht geparst werden: '%s' – %s",
            iso_string, fehler,
        )
        return None, None


def _kategorie_aus_typ(typ: str) -> str:
    """
    Mappt den Event-Typ der API auf die DDA-Kategorie.

    Args:
        typ: type-Feld aus der API (z.B. "Sport-Events", "Konzerte")

    Returns:
        DDA-Kategorie-String
    """
    if not typ:
        return "sonstiges"

    typ_lower = typ.lower().strip()
    return TYP_KATEGORIE_MAP.get(typ_lower, "sonstiges")


# --- API-Abruf ------------------------------------------------------------

def _events_von_api() -> list[dict]:
    """
    Ruft alle zukünftigen Events von der d.live JSON-API ab.

    Die API ist ein interner AJAX-Endpunkt der TYPO3-Seite. Der Parameter
    total=9999 lädt alle verfügbaren Events ohne Paginierung.

    Returns:
        Liste der rohen API-Event-Dicts oder [] bei Fehler
    """
    time.sleep(2)  # Rate Limiting

    try:
        logger.info("Rufe d.live API ab: %s", API_URL)
        antwort = httpx.get(
            API_URL,
            params={"total": 9999},
            headers={
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.d-live.de/events/eventkalender",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            },
            timeout=20,
            follow_redirects=True,
        )

        if antwort.status_code == 429:
            logger.warning("Rate Limit (429) bei d.live API – warte 10 Sekunden")
            time.sleep(10)
            antwort = httpx.get(API_URL, params={"total": 9999}, timeout=20)

        antwort.raise_for_status()
        daten = antwort.json()
        return daten.get("dates", [])

    except httpx.HTTPStatusError as fehler:
        logger.error(
            "HTTP-Fehler bei d.live API: %s %s",
            fehler.response.status_code, fehler.response.url,
        )
        return []
    except httpx.RequestError as fehler:
        logger.error("Netzwerkfehler bei d.live API: %s", str(fehler))
        return []
    except (ValueError, KeyError) as fehler:
        logger.error("Fehler beim Parsen der d.live API-Antwort: %s", str(fehler))
        return []


# --- Event-Konvertierung --------------------------------------------------

def _event_aus_api_dict(api_event: dict, heute: date) -> Optional[dict]:
    """
    Konvertiert ein API-Event-Dict in das DDA-Standardformat.

    Abgesagte Events (status="canceled") werden übersprungen.
    Vergangene Events werden gefiltert.

    Args:
        api_event: Rohes Event-Dict aus der d.live API
        heute:     Heutiges Datum für Filterung

    Returns:
        DDA-konformes Event-Dict oder None
    """
    try:
        # --- Abgesagte Events überspringen ---
        if api_event.get("status", "").lower() == "canceled":
            logger.debug("Abgesagtes Event übersprungen: %s", api_event.get("title"))
            return None

        # --- Datum und Uhrzeit ---
        datum_obj = api_event.get("date", {})
        # starting_time bevorzugen, dann formatted
        zeit_str = datum_obj.get("starting_time") or datum_obj.get("formatted")
        datum, uhrzeit = _datum_uhrzeit_parsen(zeit_str)

        if not datum:
            logger.debug(
                "Kein Datum für Event: %s", api_event.get("title", "?")
            )
            return None

        # Vergangene Events überspringen
        if date.fromisoformat(datum) < heute:
            return None

        # --- Titel ---
        titel = (api_event.get("title") or "").strip()
        if not titel:
            logger.debug("Leerer Titel in API-Event: %s", api_event.get("id"))
            return None

        # --- Venue / Ort ---
        venue_id = api_event.get("venue", "")
        venue_name, adresse = VENUE_MAP.get(venue_id, ("d-live Düsseldorf", None))

        # --- Kategorie ---
        kategorie = _kategorie_aus_typ(api_event.get("type", ""))

        # --- Event-URL ---
        quelle_url = (api_event.get("url_detail") or "").strip()
        if not quelle_url:
            quelle_url = f"{BASE_URL}/events/eventkalender"

        # --- Bild ---
        bild_url = (api_event.get("image") or "").strip() or None

        # --- Beschreibung (aus status_label wenn nicht "Terminiert") ---
        beschreibung = None
        status_label = (api_event.get("status_label") or "").strip()
        if status_label and status_label.lower() not in ("terminiert", "regular", ""):
            beschreibung = status_label[:300]

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": venue_name,
            "adresse": adresse,
            "kategorie": kategorie,
            "beschreibung": beschreibung,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error(
            "Fehler beim Konvertieren von API-Event '%s': %s",
            api_event.get("id", "?"), str(fehler),
        )
        return None


# --- Hauptfunktion --------------------------------------------------------

def scrape() -> list[dict]:
    """
    Scrapt Events von d.live Düsseldorf über die interne JSON-API.

    Strategie:
    1. GET /events/eventkalender/dates?total=9999 (AJAX-Endpunkt)
    2. JSON-Response direkt parsen – kein Browser/Playwright nötig
    3. Vergangene und abgesagte Events filtern
    4. Duplikate anhand URL deduplizieren

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    logger.info("Starte Scraper: %s (JSON-API)", QUELLE_NAME)
    heute = date.today()

    api_events = _events_von_api()

    if not api_events:
        logger.warning("Scraper %s: API lieferte keine Events", QUELLE_NAME)
        return []

    logger.info("%d Events von d.live API empfangen", len(api_events))

    events: list[dict] = []
    gesehene_urls: set[str] = set()

    for api_event in api_events:
        event = _event_aus_api_dict(api_event, heute)
        if event is None:
            continue

        url = event["quelle_url"]
        if url in gesehene_urls:
            continue
        gesehene_urls.add(url)
        events.append(event)

    if not events:
        logger.warning("Scraper %s: 0 gültige Events nach Filterung", QUELLE_NAME)
    else:
        # 14-Tage-Fenster: Events weiter als SCRAPER_VORSCHAU_TAGE in der Zukunft ausfiltern
        heute = date.today()
        enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
        events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]
        logger.info(
            "Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events)
        )

    return events


# --- Testblock ------------------------------------------------------------

if __name__ == "__main__":
    import json as _json

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    ergebnisse = scrape()

    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")

    if ergebnisse:
        print("Beispiel-Event (erstes gefundenes):")
        print(_json.dumps(ergebnisse[0], ensure_ascii=False, indent=2))
        print()
        if len(ergebnisse) > 1:
            print(f"Weitere Events: {len(ergebnisse) - 1} zusätzliche Events gefunden.")
        # Venues zusammenfassen
        venues = {}
        for e in ergebnisse:
            venues[e["ort"]] = venues.get(e["ort"], 0) + 1
        print("Events je Venue:")
        for venue, anzahl in sorted(venues.items(), key=lambda x: -x[1]):
            print(f"  {venue}: {anzahl}")
    else:
        print("Keine Events gefunden.")
        print("Mögliche Ursachen:")
        print("  1. d.live API nicht erreichbar")
        print("  2. API-Endpunkt hat sich geändert")
        print("  3. Netzwerkverbindung nicht verfügbar")
