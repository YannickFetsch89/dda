"""
ra_venue.py – DiesDasDüsseldorf
Gemeinsame Scraper-Logik für Resident-Advisor-Venue-Scraper.

kulturschlachthof_r25.py und salon_des_amateurs.py nutzen dieselbe
RA-GraphQL-API mit venue-spezifischem Client-seitigem Filter. Diese
Hilfsfunktionen eliminieren den duplizierten Code zwischen beiden Modulen.

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
AREA_ID = 145  # Düsseldorf, Deutschland

# GraphQL Query – identisch für alle RA-Venue-Scraper
EVENTS_QUERY = """
query GET_VENUE_EVENTS($filters: FilterInputDtoInput, $pageSize: Int, $page: Int) {
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

# Standard-HTTP-Header für RA-API-Anfragen
RA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def bild_url_bauen(image_obj: Optional[dict]) -> Optional[str]:
    """
    Baut vollständige Bild-URL aus einem RA-Image-Objekt.

    RA speichert Bilder entweder als relative Pfade oder direkte CDN-URLs.

    Args:
        image_obj: RA-Image-Dict mit 'filename'-Schlüssel

    Returns:
        Vollständige Bild-URL oder None
    """
    if not image_obj:
        return None
    filename = image_obj.get("filename")
    if not filename:
        return None
    if filename.startswith("http"):
        return filename
    return f"https://www.residentadvisor.net/images/{filename}"


def ra_venue_scrapen(
    quelle_name: str,
    ort_standard: str,
    adresse_standard: str,
    ra_venue_id: int,
    kategorie: str = "nightlife",
) -> list[dict]:
    """
    Scrapt Events eines bestimmten RA-Venues via GraphQL API.

    Die RA-API liefert Events nach Area (Düsseldorf = 145).
    Client-seitig werden nur Events des angegebenen Venues gefiltert.

    Args:
        quelle_name:      Name der Datenquelle (z.B. "Kulturschlachthof R25")
        ort_standard:     Standard-Ortsangabe für alle Events
        adresse_standard: Standard-Adresse für alle Events
        ra_venue_id:      Numerische RA-Venue-ID (z.B. 133380)
        kategorie:        DDA-Kategorie aller Events dieses Venues

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
        Leere Liste bei Fehler oder keine Events.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s (via RA Venue %d)", quelle_name, ra_venue_id)

    alle_events: list[dict] = []
    gesehene_schluessel: set[str] = set()
    seite = 1

    try:
        with httpx.Client(headers=RA_HEADERS, follow_redirects=True, timeout=30) as client:
            while seite <= 5:
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
                if "errors" in daten:
                    logger.error("RA GraphQL-Fehler: %s", daten["errors"][:2])
                    break

                listings = (
                    daten.get("data", {})
                    .get("eventListings", {})
                    .get("data", [])
                )

                if not listings:
                    break

                # Nur Events des gewünschten Venues filtern (client-seitig)
                venue_listings = [
                    l for l in listings
                    if str((l.get("event") or {}).get("venue", {}).get("id", "")) == str(ra_venue_id)
                ]
                logger.debug(
                    "Seite %d: %d Gesamt-Listings, %d Venue-Events für ID %d",
                    seite, len(listings), len(venue_listings), ra_venue_id,
                )

                for listing in venue_listings:
                    try:
                        ev = listing.get("event") or {}
                        titel = (ev.get("title") or "").strip()
                        if not titel:
                            continue

                        datum_str = (listing.get("listingDate") or "")[:10]
                        if not datum_str:
                            continue
                        datum_obj = date.fromisoformat(datum_str)
                        if datum_obj < heute or datum_obj > enddatum:
                            continue

                        # Uhrzeit aus startTime (ISO 8601 mit T-Trennzeichen)
                        start_time = ev.get("startTime", "")
                        uhrzeit: Optional[str] = None
                        if start_time and "T" in start_time:
                            zeit = start_time.split("T")[1][:5]
                            uhrzeit = zeit if len(zeit) == 5 else None

                        # Bild-URL
                        images = ev.get("images") or []
                        bild_url = bild_url_bauen(images[0]) if images else None

                        # Artists → Beschreibung
                        artists = ev.get("artists") or []
                        kuenstler = [a["name"] for a in artists if a.get("name")]
                        beschreibung: Optional[str] = None
                        if kuenstler:
                            beschreibung = ("Mit: " + ", ".join(kuenstler[:8]))[:300]

                        # Quelle-URL
                        content_url = ev.get("contentUrl") or ""
                        quelle_url = urljoin(RA_BASE_URL, content_url) if content_url else RA_BASE_URL

                        # Interne Deduplizierung
                        schluessel = f"{titel}_{datum_str}"
                        if schluessel in gesehene_schluessel:
                            continue
                        gesehene_schluessel.add(schluessel)

                        alle_events.append({
                            "titel": titel,
                            "datum": datum_str,
                            "uhrzeit": uhrzeit,
                            "ort": ort_standard,
                            "adresse": adresse_standard,
                            "kategorie": kategorie,
                            "beschreibung": beschreibung,
                            "preis": None,
                            "quelle_name": quelle_name,
                            "quelle_url": quelle_url,
                            "bild_url": bild_url,
                            "instagram_caption": None,
                            "datum_bis": None,
                            "ist_wiederkehrend": False,
                            "status": "neu",
                        })

                    except Exception as err:
                        logger.error(
                            "Fehler bei Event-Verarbeitung (%s, Venue %d): %s",
                            quelle_name, ra_venue_id, err,
                        )
                        continue

                # Weniger als pageSize Ergebnisse → letzte Seite erreicht
                if len(listings) < 100:
                    break

                seite += 1
                time.sleep(2)  # Rate-Limiting

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", quelle_name, fehler)
        return []

    logger.info("Scraper %s fertig: %d Events", quelle_name, len(alle_events))
    return alle_events
