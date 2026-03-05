"""
kulturschlachthof_r25.py – DiesDasDüsseldorf
Scraper für den Kulturschlachthof R25 Düsseldorf.

Strategie:
Die eigene Website (kulturschlachthof.de) ist eine reine Platzhalterseite
ohne Programm-Informationen. Events werden über Resident Advisor
(ra.co GraphQL API, Venue-ID 133380) abgerufen.

Der Kulturschlachthof R25 ist ein Club für elektronische Musik,
Techno, House und experimentelle Sounds in Düsseldorf.

URL: https://kulturschlachthof.de
RA-Venue: https://ra.co/clubs/133380
Adresse: Reisholzer Str. 25, 40721 Hilden (Nähe Düsseldorf)
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
QUELLE_NAME = "Kulturschlachthof R25"
ORT_STANDARD = "Kulturschlachthof R25"
ADRESSE_STANDARD = "Ronsdorfer Str. 134, 40233 Düsseldorf"
RA_VENUE_ID = 133380
AREA_ID = 145  # Düsseldorf

# GraphQL Query mit Venue-Filter (client-seitig gefiltert)
EVENTS_QUERY = """
query GET_R25_EVENTS($filters: FilterInputDtoInput, $pageSize: Int, $page: Int) {
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
    return f"https://www.residentadvisor.net/images/{filename}"


def scrape() -> list[dict]:
    """
    Scrapt Events des Kulturschlachthof R25 via Resident Advisor API.

    Da kulturschlachthof.de keine Programm-Informationen enthält,
    werden Events über die RA GraphQL API (Venue 133380) abgerufen.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s (via RA Venue %d)", QUELLE_NAME, RA_VENUE_ID)

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
    gesehene_schluessel: set[str] = set()
    seite = 1

    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=30) as client:
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

                # Nur R25-Events filtern (Venue-ID 133380)
                r25_listings = [
                    l for l in listings
                    if str((l.get("event") or {}).get("venue", {}).get("id", "")) == str(RA_VENUE_ID)
                ]
                logger.debug("Seite %d: %d Gesamt-Listings, %d R25-Events", seite, len(listings), len(r25_listings))

                for listing in r25_listings:
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

                        # Uhrzeit
                        start_time = ev.get("startTime", "")
                        uhrzeit: Optional[str] = None
                        if start_time and "T" in start_time:
                            zeit = start_time.split("T")[1][:5]
                            uhrzeit = zeit if len(zeit) == 5 else None

                        # Bild
                        images = ev.get("images") or []
                        bild_url = _bild_url_bauen(images[0]) if images else None

                        # Artists
                        artists = ev.get("artists") or []
                        kuenstler = [a["name"] for a in artists if a.get("name")]
                        beschreibung: Optional[str] = None
                        if kuenstler:
                            beschreibung = ("Mit: " + ", ".join(kuenstler[:8]))[:300]

                        # URL
                        content_url = ev.get("contentUrl") or ""
                        quelle_url = urljoin(RA_BASE_URL, content_url) if content_url else RA_BASE_URL

                        schluessel = f"{titel}_{datum_str}"
                        if schluessel in gesehene_schluessel:
                            continue
                        gesehene_schluessel.add(schluessel)

                        alle_events.append({
                            "titel": titel,
                            "datum": datum_str,
                            "uhrzeit": uhrzeit,
                            "ort": ORT_STANDARD,
                            "adresse": ADRESSE_STANDARD,
                            "kategorie": "nightlife",
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

                    except Exception as err:
                        logger.error("Fehler bei R25-Event-Verarbeitung: %s", err)
                        continue

                # Wenn weniger als pageSize Ergebnisse: Ende
                if len(listings) < 100:
                    break

                seite += 1
                time.sleep(2)  # Rate-Limiting

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
