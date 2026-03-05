"""
resident_advisor.py – DiesDasDüsseldorf
Scraper für Resident Advisor (RA) Düsseldorf via GraphQL API.

Strategie:
Resident Advisor stellt eine öffentliche GraphQL API bereit, die ohne
Authentifizierung Events nach Area (Düsseldorf = ID 145) liefert.

Die API liefert Events aus Clubs und Venues der elektronischen Musik
und Clubbing-Szene in Düsseldorf (Nightlife, Techno, House, Disco etc.)

URL: https://ra.co/events/de/dusseldorf
API: https://ra.co/graphql
Area-ID: 145 (Düsseldorf, Deutschland)
Erstellt: 2026-03-05
"""
import logging
import time
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

import httpx

from config import SCRAPER_VORSCHAU_TAGE

logger = logging.getLogger(__name__)

RA_GRAPHQL_URL = "https://ra.co/graphql"
RA_BASE_URL = "https://ra.co"
QUELLE_NAME = "Resident Advisor"
AREA_ID = 145  # Düsseldorf, Deutschland

# GraphQL Query für Event-Listings
EVENTS_QUERY = """
query GET_DUSSELDORF_EVENTS($filters: FilterInputDtoInput, $pageSize: Int, $page: Int) {
  eventListings(filters: $filters, pageSize: $pageSize, page: $page) {
    data {
      id
      listingDate
      event {
        id
        title
        startTime
        endTime
        images { filename }
        venue {
          id
          name
          address
          contentUrl
        }
        artists { name }
        contentUrl
      }
    }
  }
}
"""

KATEGORIE_MAPPING: dict[str, str] = {
    "techno": "nightlife",
    "house": "nightlife",
    "disco": "nightlife",
    "dnb": "nightlife",
    "drum": "nightlife",
    "trance": "nightlife",
    "club": "nightlife",
    "party": "nightlife",
    "dj": "nightlife",
    "rave": "nightlife",
    "electronic": "nightlife",
    "ambient": "musik",
    "jazz": "musik",
    "live": "musik",
    "band": "musik",
    "konzert": "musik",
    "concert": "musik",
    "pop": "musik",
    "rock": "musik",
    "hip hop": "musik",
    "hip-hop": "musik",
    "soul": "musik",
    "funk": "musik",
    "opening": "kultur",
    "exhibition": "kultur",
    "ausstellung": "kultur",
    "film": "kultur",
    "theater": "kultur",
}


def _kategorie_erkennen(titel: str) -> str:
    """
    Erkennt Kategorie anhand des Titels.

    Args:
        titel: Event-Titel

    Returns:
        Gültige Kategorie
    """
    if not titel:
        return "nightlife"
    text = titel.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if schluessel in text:
            return kategorie
    return "nightlife"  # Standard bei RA: Nightlife/Clubbing


def _bild_url_bauen(image_obj: Optional[dict]) -> Optional[str]:
    """
    Baut vollständige Bild-URL aus RA Image-Objekt.

    Args:
        image_obj: RA Image-Dict mit 'filename'

    Returns:
        Vollständige URL oder None
    """
    if not image_obj:
        return None
    filename = image_obj.get("filename")
    if not filename:
        return None
    if filename.startswith("http"):
        return filename
    # RA speichert Bilder als relative Pfade oder CDN-URLs
    return f"https://www.residentadvisor.net/images/{filename}"


def _events_aus_antwort(antwort: dict, heute: date, enddatum: date) -> list[dict]:
    """
    Verarbeitet GraphQL-Antwort zu DiesDasDüsseldorf Event-Dicts.

    Args:
        antwort: Geparstes JSON der API-Antwort
        heute: Heute-Datum für Filterung
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Event-Dicts
    """
    events: list[dict] = []
    gesehene_schluessel: set[str] = set()

    listings = (
        antwort
        .get("data", {})
        .get("eventListings", {})
        .get("data", [])
    )
    if not listings:
        return []

    for listing in listings:
        try:
            ev = listing.get("event")
            if not ev:
                continue

            titel = (ev.get("title") or "").strip()
            if not titel:
                continue

            # Datum aus listingDate
            listing_date_str = listing.get("listingDate", "")
            if not listing_date_str:
                continue
            try:
                datum_obj = date.fromisoformat(listing_date_str[:10])
            except ValueError:
                continue

            if datum_obj < heute or datum_obj > enddatum:
                continue

            # Uhrzeit aus startTime (ISO 8601 mit Zeit)
            start_time = ev.get("startTime", "")
            uhrzeit: Optional[str] = None
            if start_time and "T" in start_time:
                zeit_teil = start_time.split("T")[1][:5]
                uhrzeit = zeit_teil if len(zeit_teil) == 5 else None

            # Venue-Daten
            venue = ev.get("venue") or {}
            ort = (venue.get("name") or "Düsseldorf").strip()
            adresse = (venue.get("address") or "").strip() or None

            # Bild-URL
            images = ev.get("images") or []
            bild_url: Optional[str] = None
            if images:
                bild_url = _bild_url_bauen(images[0])

            # Artists zu Beschreibung zusammenführen
            artists = ev.get("artists") or []
            kuenstler_namen = [a.get("name", "") for a in artists if a.get("name")]
            beschreibung: Optional[str] = None
            if kuenstler_namen:
                beschreibung = "Mit: " + ", ".join(kuenstler_namen[:8])
                beschreibung = beschreibung[:300]

            # Quelle-URL
            content_url = ev.get("contentUrl") or ""
            quelle_url = urljoin(RA_BASE_URL, content_url) if content_url else RA_BASE_URL

            kategorie = _kategorie_erkennen(titel)

            schluessel = f"{titel}_{datum_obj.isoformat()}_{ort}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum_obj.isoformat(),
                "uhrzeit": uhrzeit,
                "ort": ort,
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
            })

        except Exception as fehler:
            logger.error("Fehler beim Verarbeiten eines RA-Events: %s", fehler)
            continue

    return events


def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen von Resident Advisor für Düsseldorf (Area 145).

    Nutzt die öffentliche GraphQL API von ra.co.
    Liefert hauptsächlich Nightlife- und Clubbing-Events.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s (Düsseldorf, Area %d)", QUELLE_NAME, AREA_ID)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    alle_events: list[dict] = []
    seite = 1
    seiten_max = 10  # Schutz vor Endlosschleife

    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=30) as client:
            while seite <= seiten_max:
                variablen = {
                    "filters": {
                        "areas": {"eq": AREA_ID},
                        "listingDate": {
                            "gte": heute.isoformat(),
                            "lte": enddatum.isoformat(),
                        },
                    },
                    "pageSize": 100,
                    "page": seite,
                }

                try:
                    antwort = client.post(
                        RA_GRAPHQL_URL,
                        json={"query": EVENTS_QUERY, "variables": variablen},
                    )
                    antwort.raise_for_status()
                except httpx.HTTPStatusError as err:
                    logger.error("RA API HTTP-Fehler (Seite %d): %s", seite, err)
                    break
                except httpx.RequestError as err:
                    logger.error("RA API Verbindungsfehler (Seite %d): %s", seite, err)
                    break

                daten = antwort.json()

                # GraphQL-Fehler prüfen
                if "errors" in daten:
                    fehler_texte = [e.get("message", "?") for e in daten["errors"][:3]]
                    logger.error("RA GraphQL-Fehler: %s", fehler_texte)
                    break

                events_seite = _events_aus_antwort(daten, heute, enddatum)
                logger.debug("RA Seite %d: %d Events", seite, len(events_seite))

                if not events_seite:
                    # Keine weiteren Ergebnisse
                    break

                alle_events.extend(events_seite)
                seite += 1
                time.sleep(2)  # Rate-Limiting: 2 Sekunden zwischen Requests

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []

    logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(alle_events))
    return alle_events


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
