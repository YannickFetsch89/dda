"""
meetup.py – DiesDasDüsseldorf
Scraper für Meetup.com: Community-Events und Meetups in Düsseldorf.

Strategie:
1. Primär: Interne GraphQL API (meetup.com/gql2) – strukturierte Daten
2. Fallback: HTML-Scraping der Suchseite mit BeautifulSoup

Koordinaten Düsseldorf: lat=51.2217, lon=6.7762, Radius 20 km

Erstellt: 2026-03-05
"""
import logging
import re
import time
from datetime import date, timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import STANDARD_HEADERS

logger = logging.getLogger(__name__)

# --- Konstanten ----------------------------------------------------------

BASE_URL = "https://www.meetup.com"
SUCHE_URL = "https://www.meetup.com/de-DE/find/?location=de--D%C3%BCsseldorf&source=EVENTS&distance=twentyMiles"
GQL_URL = "https://www.meetup.com/gql2"
QUELLE_NAME = "Meetup.com"
KATEGORIE_STANDARD = "community"

# Düsseldorf Koordinaten
DUS_LAT = 51.2217
DUS_LON = 6.7762
SUCHRADIUS_KM = 20

KATEGORIE_MAPPING = {
    "tech": "community", "startup": "community", "coding": "community",
    "developer": "community", "software": "community", "networking": "community",
    "business": "community", "entrepreneur": "community", "workshop": "community",
    "sprachkurs": "community", "language": "community", "sprache": "community",
    "meetup": "community", "treffen": "community",
    "sport": "sport", "yoga": "sport", "laufen": "sport", "running": "sport",
    "fitness": "sport", "klettern": "sport", "fahrrad": "sport",
    "hiking": "outdoor", "wandern": "outdoor", "natur": "outdoor",
    "outdoor": "outdoor", "walk": "outdoor",
    "konzert": "musik", "musik": "musik", "music": "musik",
    "kunst": "kultur", "kultur": "kultur", "theater": "kultur",
    "movie": "kultur", "kino": "kultur", "film": "kultur",
    "food": "food", "kochen": "food", "cooking": "food", "essen": "food",
    "dating": "dating", "singles": "dating", "speed dating": "dating",
    "kinder": "family", "familie": "family", "family": "family",
    "party": "nightlife", "club": "nightlife",
}

# GraphQL-Query für die eventSearch API (gql2 Endpoint)
GQL_QUERY = """
query EventSearch($first: Int, $after: String, $filter: EventSearchFilter!) {
  eventSearch(first: $first, after: $after, filter: $filter) {
    totalCount
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        title
        dateTime
        endTime
        venue {
          name
          address
          city
          postalCode
        }
        group {
          name
          urlname
          city
        }
        eventUrl
        description
        isOnline
      }
    }
  }
}
"""


# --- Hilfsfunktionen -----------------------------------------------------

def _datum_parsen(text: str) -> Optional[str]:
    """Extrahiert ISO-Datum (YYYY-MM-DD) aus ISO-Timestamp oder Datumstext."""
    if not text:
        return None
    try:
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if treffer:
            return date(
                int(treffer.group(1)),
                int(treffer.group(2)),
                int(treffer.group(3)),
            ).isoformat()
    except (ValueError, AttributeError) as fehler:
        logger.warning("Datum konnte nicht geparst werden: '%s' – %s", text, fehler)
    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """Extrahiert Uhrzeit (HH:MM) aus ISO-Timestamp."""
    if not text:
        return None
    treffer = re.search(r"T(\d{2}):(\d{2})", text)
    if treffer:
        stunde, minute = int(treffer.group(1)), int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"
    return None


def _kategorie_erkennen(text: str) -> str:
    """Mappt Titel/Beschreibungstext auf DiesDasDüsseldorf-Kategorien."""
    if not text:
        return KATEGORIE_STANDARD
    text_klein = text.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if schluessel in text_klein:
            return kategorie
    return KATEGORIE_STANDARD


def _beschreibung_bereinigen(text: str) -> Optional[str]:
    """Entfernt HTML-Tags und kürzt auf 300 Zeichen."""
    if not text:
        return None
    try:
        # Meetup liefert manchmal HTML, manchmal Plaintext
        if "<" in text and ">" in text:
            soup = BeautifulSoup(text, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
        return text[:300] if text else None
    except Exception:
        return str(text)[:300]


# --- Primärstrategie: GraphQL API (gql2) ---------------------------------

def _event_aus_gql_eintrag(eintrag: dict, heute: date) -> Optional[dict]:
    """Wandelt einen GraphQL Event-Eintrag in ein DiesDasDüsseldorf Event-Dict um."""
    try:
        titel = eintrag.get("title", "").strip()
        if not titel:
            return None

        datum_roh = eintrag.get("dateTime")
        datum = _datum_parsen(str(datum_roh)) if datum_roh else None
        if not datum:
            return None
        if date.fromisoformat(datum) < heute:
            return None

        uhrzeit = _uhrzeit_parsen(str(datum_roh)) if datum_roh else None

        # Ort aus venue-Objekt oder Gruppe
        venue = eintrag.get("venue") or {}
        gruppe = eintrag.get("group") or {}

        if eintrag.get("isOnline"):
            ort = f"{gruppe.get('name', 'Meetup')} (Online)"
        elif isinstance(venue, dict) and venue.get("name"):
            ort = venue["name"]
        else:
            ort = gruppe.get("name") or "Düsseldorf"

        # Adresse zusammenbauen
        adresse = None
        if isinstance(venue, dict) and not eintrag.get("isOnline"):
            teile = [
                venue.get("address"),
                venue.get("postalCode"),
                venue.get("city"),
            ]
            adresse = " ".join(t for t in teile if t) or None

        quelle_url = eintrag.get("eventUrl") or BASE_URL

        # Beschreibung – Meetup liefert Plaintext oder HTML
        beschreibung = _beschreibung_bereinigen(eintrag.get("description"))

        kategorie = _kategorie_erkennen(titel + " " + (beschreibung or ""))

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
        logger.error("Fehler beim Verarbeiten eines GraphQL-Eintrags: %s", str(fehler))
        return None


def _scrape_graphql(heute: date) -> list[dict]:
    """
    Primärstrategie: Meetup-Events via interner GraphQL API (gql2) holen.

    Die API benötigt Session-Cookies und einen query-Parameter im Filter.
    """
    logger.info("Primärstrategie: Meetup GraphQL API (%s)", GQL_URL)

    headers = {
        **STANDARD_HEADERS,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": BASE_URL,
        "Referer": SUCHE_URL,
    }

    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)

    gql_payload = {
        "query": GQL_QUERY,
        "variables": {
            "first": 100,
            "filter": {
                "query": "Düsseldorf",
                "lat": DUS_LAT,
                "lon": DUS_LON,
                "radius": float(SUCHRADIUS_KM),
                "startDateRange": heute.isoformat() + "T00:00:00+01:00",
                "endDateRange": enddatum.isoformat() + "T23:59:59+01:00",
            },
        },
    }

    try:
        with httpx.Client(
            headers=headers,
            timeout=30,
            follow_redirects=True,
        ) as client:
            # Schritt 1: Session-Cookies holen
            time.sleep(2)
            try:
                client.get(SUCHE_URL, timeout=30)
                logger.debug(
                    "Session-Cookies geholt: %d Cookies erhalten",
                    len(client.cookies),
                )
            except Exception as fehler:
                logger.warning("Session-Cookies konnten nicht geholt werden: %s", fehler)

            # CSRF-Token aus Cookies extrahieren
            cookies = dict(client.cookies)
            csrf_token = cookies.get("meetup_csrf") or cookies.get("_csrf_token") or ""
            if csrf_token:
                client.headers.update({"X-Csrf-Token": csrf_token})

            # Schritt 2: GraphQL-Request
            time.sleep(2)
            antwort = client.post(GQL_URL, json=gql_payload)
            antwort.raise_for_status()

            daten = antwort.json()

            # GraphQL-Fehler abfangen
            if "errors" in daten:
                fehler_texte = [e.get("message", "") for e in daten["errors"]]
                logger.warning("GraphQL Fehler: %s", " | ".join(fehler_texte))
                return []

            # Ergebnis-Edges extrahieren
            results = daten.get("data", {}).get("eventSearch", {})
            edges = results.get("edges", [])
            gesamt = results.get("totalCount", 0)

            logger.info("GraphQL: %d Events gefunden (von %d gesamt)", len(edges), gesamt)

            events = []
            gesehene_urls: set[str] = set()

            for edge in edges:
                eintrag = edge.get("node", {})
                if not eintrag:
                    continue

                event = _event_aus_gql_eintrag(eintrag, heute)
                if event is None:
                    continue

                url = event["quelle_url"]
                if url in gesehene_urls:
                    continue
                gesehene_urls.add(url)
                events.append(event)

            return events

    except httpx.HTTPStatusError as fehler:
        logger.error(
            "GraphQL HTTP-Fehler %d: %s",
            fehler.response.status_code, str(fehler),
        )
        return []
    except Exception as fehler:
        logger.error("GraphQL-Anfrage fehlgeschlagen: %s", str(fehler))
        return []


# --- Hauptfunktion -------------------------------------------------------

def scrape() -> list[dict]:
    """
    Scrapt Community-Events von Meetup.com für Düsseldorf.

    Nutzt die interne GraphQL API (gql2 Endpoint) mit eventSearch.
    Kein API-Key erforderlich, Session-Cookies werden automatisch geholt.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    events = _scrape_graphql(heute)
    logger.info("GraphQL: %d Events gefunden", len(events))

    if not events:
        logger.warning("Meetup GraphQL lieferte keine Events")

    # 14-Tage-Fenster anwenden
    events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]
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
