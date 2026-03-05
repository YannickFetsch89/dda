"""
meetup.py – DiesDasDüsseldorf
Scraper für Meetup.com: Community-Events und Meetups in Düsseldorf.

Meetup.com stellt keine kostenfreie öffentliche REST API mehr zur Verfügung.
Stattdessen wird die interne GraphQL API genutzt, die das Meetup-Frontend
selbst verwendet. Diese ist ohne API-Key zugänglich, benötigt aber Session-
Cookies (werden automatisch geholt).

Strategie:
1. Primär: Interne GraphQL API (meetup.com/gql) – strukturierte Daten
2. Fallback: HTML-Scraping der Suchseite mit BeautifulSoup

Koordinaten Düsseldorf: lat=51.2217, lon=6.7762, Radius 20 km

Erstellt: 2026-03-05
"""
import json
import logging
import re
import time
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import STANDARD_HEADERS

logger = logging.getLogger(__name__)

# --- Konstanten ----------------------------------------------------------

BASE_URL = "https://www.meetup.com"
SUCHE_URL = "https://www.meetup.com/de-DE/find/?location=de--D%C3%BCsseldorf&source=EVENTS&distance=twentyMiles"
GQL_URL = "https://www.meetup.com/gql"
QUELLE_NAME = "Meetup.com"
KATEGORIE_STANDARD = "community"

# Düsseldorf Koordinaten
DUS_LAT = 51.2217
DUS_LON = 6.7762
SUCHRADIUS_KM = 20

MONAT_MAP: dict[str, int] = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
    "january": 1, "february": 2, "march": 3, "june": 6,
    "july": 7, "october": 10, "december": 12,
}
MONAT_KURZ_MAP: dict[str, int] = {
    "jan": 1, "feb": 2, "mär": 3, "mar": 3, "apr": 4,
    "mai": 5, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}

KATEGORIE_MAPPING = {
    "tech": "community", "startup": "community", "coding": "community",
    "developer": "community", "software": "community", "networking": "community",
    "business": "community", "entrepreneur": "community", "workshop": "community",
    "sprachkurs": "community", "language": "community", "sprache": "community",
    "meetup": "community", "treffen": "community",
    "sport": "sport", "yoga": "sport", "laufen": "sport", "running": "sport",
    "fitness": "sport", "klettern": "sport", "fahrrad": "sport",
    "outdoor": "outdoor", "wandern": "outdoor", "natur": "outdoor",
    "konzert": "musik", "musik": "musik", "music": "musik",
    "kunst": "kultur", "kultur": "kultur", "theater": "kultur",
    "food": "food", "kochen": "food", "cooking": "food", "essen": "food",
    "dating": "dating", "singles": "dating",
    "kinder": "family", "familie": "family", "family": "family",
    "party": "nightlife", "club": "nightlife",
}

# GraphQL-Query: Meetup-interne Event-Suche nach Standort
# Diese Query repliziert exakt den API-Call des Meetup-Frontends
GQL_QUERY = """
query EventSearch($input: ConnectionInput, $filter: SearchConnectionFilter) {
  results: keywordSearch(
    input: $input
    filter: $filter
  ) {
    count
    edges {
      node {
        result {
          ... on Event {
            id
            title
            dateTime
            endTime
            going
            venue {
              name
              address
              city
              postalCode
              country
            }
            group {
              name
              urlname
              city
            }
            eventUrl
            description
            shortDescription
            images {
              baseUrl
            }
            isOnline
            isSaved
          }
        }
      }
    }
  }
}
"""


# --- Hilfsfunktionen: Datum und Uhrzeit ----------------------------------

def _datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt verschiedene Datumsformate in ISO 8601 (YYYY-MM-DD) um.

    Verarbeitet ISO-Timestamps wie "2026-03-15T19:00:00+01:00"
    sowie gängige Datumsformate.

    Args:
        text: Roher Datumstext oder ISO-Timestamp

    Returns:
        ISO-Datum (YYYY-MM-DD) oder None
    """
    if not text:
        return None

    heute = date.today()
    bereinigt = text.strip()
    bereinigt_klein = bereinigt.lower()

    try:
        # ISO-Timestamp: "2026-03-15T19:00:00+01:00" oder "2026-03-15T19:00:00Z"
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(1)),
                int(treffer.group(2)),
                int(treffer.group(3)),
            ).isoformat()

        # Deutsches Format: "15.03.2026"
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(3)),
                int(treffer.group(2)),
                int(treffer.group(1)),
            ).isoformat()

        # "15. März 2026"
        treffer = re.search(r"(\d{1,2})\.?\s+([a-zäöüß]+)\s+(\d{4})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat = MONAT_MAP.get(treffer.group(2).lower())
            jahr = int(treffer.group(3))
            if monat:
                return date(jahr, monat, tag).isoformat()

        # Kurzform ohne Jahr: "15. Mär"
        treffer = re.search(r"(\d{1,2})\.\s*([a-zäöü]{3})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat = MONAT_KURZ_MAP.get(treffer.group(2)[:3])
            if monat:
                kandidat = date(heute.year, monat, tag)
                if kandidat < heute - timedelta(days=1):
                    kandidat = date(heute.year + 1, monat, tag)
                return kandidat.isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning("Datum konnte nicht geparst werden: '%s' – %s", text, fehler)
        return None

    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """
    Extrahiert Uhrzeit (HH:MM) aus ISO-Timestamp oder Zeittext.

    Args:
        text: Roher Text oder ISO-Timestamp

    Returns:
        Uhrzeit als HH:MM oder None
    """
    if not text:
        return None
    treffer = re.search(r"T(\d{2}):(\d{2}):|(\d{1,2})[:\.](\d{2})\s*(?:Uhr)?", text, re.IGNORECASE)
    if treffer:
        if treffer.group(1):
            stunde, minute = int(treffer.group(1)), int(treffer.group(2))
        else:
            stunde, minute = int(treffer.group(3)), int(treffer.group(4))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"
    return None


def _kategorie_erkennen(text: str) -> str:
    """
    Mappt Titel und Beschreibungstext auf DiesDasDüsseldorf-Kategorien.

    Bei Meetup-Events ist community der häufigste Typ, daher als Standard.

    Args:
        text: Titel oder Beschreibungstext

    Returns:
        Gültige DiesDasDüsseldorf-Kategorie
    """
    if not text:
        return KATEGORIE_STANDARD
    text_klein = text.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if schluessel in text_klein:
            return kategorie
    return KATEGORIE_STANDARD


def _beschreibung_bereinigen(html_text: str) -> Optional[str]:
    """
    Entfernt HTML-Tags aus der Meetup-Beschreibung und kürzt auf 300 Zeichen.

    Args:
        html_text: Beschreibung mit HTML-Markup

    Returns:
        Bereinigter Plaintext oder None
    """
    if not html_text:
        return None
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return text[:300] if text else None
    except Exception:
        return str(html_text)[:300]


# --- Primärstrategie: Interne GraphQL API --------------------------------

def _session_cookies_holen(client: httpx.Client) -> dict:
    """
    Ruft die Meetup-Startseite ab um Session-Cookies zu erhalten.

    Die GraphQL API benötigt gültige Session-Cookies (csrf_token etc.)
    die bei einem normalen Seitenaufruf automatisch gesetzt werden.

    Args:
        client: httpx.Client mit Cookie-Jar

    Returns:
        Dict der erhaltenen Cookies (kann leer sein)
    """
    try:
        time.sleep(2)
        antwort = client.get(SUCHE_URL, timeout=30)
        logger.debug(
            "Session-Cookies geholt: %d Cookies erhalten",
            len(client.cookies),
        )
        return dict(client.cookies)
    except Exception as fehler:
        logger.warning("Session-Cookies konnten nicht geholt werden: %s", fehler)
        return {}


def _event_aus_gql_eintrag(eintrag: dict, heute: date) -> Optional[dict]:
    """
    Wandelt einen GraphQL Event-Eintrag in ein DiesDasDüsseldorf Event-Dict um.

    Args:
        eintrag: Event-Dict aus dem GraphQL edges[].node.result
        heute:   Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None wenn Pflichtfelder fehlen
    """
    try:
        titel = eintrag.get("title", "").strip()
        if not titel:
            return None

        datum_roh = eintrag.get("dateTime") or eintrag.get("startTime")
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
            stadt = venue.get("city") or venue.get("addressLocality") or ""
            if stadt and "düsseldorf" not in ort.lower():
                ort = f"{ort}, {stadt}"
        else:
            ort = gruppe.get("name") or "Düsseldorf"

        # Adresse zusammenbauen
        adresse = None
        if isinstance(venue, dict) and not eintrag.get("isOnline"):
            teile = [
                venue.get("address") or venue.get("streetAddress"),
                venue.get("postalCode"),
                venue.get("city") or venue.get("addressLocality"),
            ]
            adresse = " ".join(t for t in teile if t) or None

        quelle_url = eintrag.get("eventUrl") or BASE_URL

        # Beschreibung – Meetup liefert HTML
        beschreibung_roh = eintrag.get("shortDescription") or eintrag.get("description")
        beschreibung = _beschreibung_bereinigen(beschreibung_roh)

        # Bild
        bild_url = None
        bilder = eintrag.get("images")
        if bilder and isinstance(bilder, list) and bilder[0]:
            base = bilder[0].get("baseUrl")
            if base:
                bild_url = base if base.startswith("http") else f"https:{base}"

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
            "bild_url": bild_url,
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
    Primärstrategie: Meetup-Events via interner GraphQL API holen.

    Meetup.com nutzt für seine Suche intern die URL /gql. Diese API
    ist ohne API-Key zugänglich, benötigt aber Session-Cookies, die
    durch einen vorherigen GET-Request automatisch geholt werden.

    Args:
        heute: Heutiges Datum für Filterung

    Returns:
        Liste von Event-Dicts oder leere Liste bei Fehler
    """
    logger.info("Primärstrategie: Meetup GraphQL API (%s)", GQL_URL)

    headers = {
        **STANDARD_HEADERS,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": BASE_URL,
        "Referer": SUCHE_URL,
        "X-Requested-With": "XMLHttpRequest",
    }

    # Vorschau-Endpunkt berechnen
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)

    gql_payload = {
        "operationName": "EventSearch",
        "query": GQL_QUERY,
        "variables": {
            "input": {
                "first": 100,
            },
            "filter": {
                "lat": DUS_LAT,
                "lon": DUS_LON,
                "radius": SUCHRADIUS_KM,
                "startDateRange": heute.isoformat() + "T00:00:00",
                "endDateRange": enddatum.isoformat() + "T23:59:59",
                "upcomingEvents": True,
                "source": "EVENTS",
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
            cookies = _session_cookies_holen(client)
            if not cookies:
                logger.warning("Keine Session-Cookies erhalten – GraphQL könnte scheitern")

            # CSRF-Token aus Cookies extrahieren wenn vorhanden
            csrf_token = cookies.get("meetup_csrf") or cookies.get("_csrf_token") or ""
            if csrf_token:
                client.headers.update({"X-Csrf-Token": csrf_token})
                logger.debug("CSRF-Token gesetzt: %s...", csrf_token[:8])

            # Schritt 2: GraphQL-Request
            time.sleep(2)  # Rate Limiting
            antwort = client.post(GQL_URL, json=gql_payload)
            antwort.raise_for_status()

            daten = antwort.json()

            # GraphQL-Fehler abfangen
            if "errors" in daten:
                fehler_texte = [e.get("message", "") for e in daten["errors"]]
                logger.warning("GraphQL Fehler: %s", " | ".join(fehler_texte))
                return []

            # Ergebnis-Edges extrahieren
            results = daten.get("data", {}).get("results", {})
            edges = results.get("edges", [])
            gesamt = results.get("count", 0)

            logger.info("GraphQL: %d Events gefunden (von %d gesamt)", len(edges), gesamt)

            events = []
            gesehene_urls: set[str] = set()

            for edge in edges:
                eintrag = edge.get("node", {}).get("result", {})
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


# --- Fallbackstrategie: HTML-Scraping ------------------------------------

def _event_aus_html_karte(karte, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event aus einer HTML-Event-Karte der Meetup-Suchseite.

    Args:
        karte: BeautifulSoup-Element einer Event-Karte
        heute: Heutiges Datum für Filterung

    Returns:
        Event-Dict oder None
    """
    try:
        # Titel
        titel_el = karte.find(["h2", "h3", "h4", "strong", "a"])
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel or len(titel) < 3:
            return None

        # URL
        link_el = karte.find("a", href=True)
        quelle_url = None
        if link_el:
            href = link_el.get("href", "")
            quelle_url = href if href.startswith("http") else urljoin(BASE_URL, href)
        if not quelle_url:
            return None

        # Datum
        datum_el = (
            karte.find("time")
            or karte.find(attrs={"datetime": True})
            or karte.find(class_=re.compile(r"date|datum|time|zeit", re.I))
        )
        if not datum_el:
            return None

        datum_text = datum_el.get("datetime") or datum_el.get_text(strip=True)
        datum = _datum_parsen(datum_text)
        if not datum or date.fromisoformat(datum) < heute:
            return None

        uhrzeit = _uhrzeit_parsen(datum_text)

        # Ort
        ort_el = karte.find(class_=re.compile(r"venue|location|ort|place", re.I))
        ort = ort_el.get_text(strip=True) if ort_el else "Düsseldorf"

        # Bild
        bild_el = karte.find("img")
        bild_url = None
        if bild_el:
            bild_url = bild_el.get("data-src") or bild_el.get("src")
            if bild_url and bild_url.startswith("/"):
                bild_url = urljoin(BASE_URL, bild_url)

        kategorie = _kategorie_erkennen(titel)

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": None,
            "kategorie": kategorie,
            "beschreibung": None,
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
        logger.error("Fehler beim Parsen einer HTML-Karte: %s", str(fehler))
        return None


def _scrape_html(heute: date) -> list[dict]:
    """
    Fallbackstrategie: HTML-Scraping der Meetup-Suchseite.

    Meetup ist eine React-App. Diese Strategie liefert nur dann Daten,
    wenn serverseitig gerenderter Inhalt oder __NEXT_DATA__ vorhanden ist.

    Args:
        heute: Heutiges Datum für Filterung

    Returns:
        Liste von Event-Dicts oder leere Liste
    """
    logger.info("Fallback: HTML-Scraping von %s", SUCHE_URL)

    try:
        time.sleep(2)
        with httpx.Client(headers=STANDARD_HEADERS, timeout=30, follow_redirects=True) as client:
            antwort = client.get(SUCHE_URL)
            antwort.raise_for_status()
            html = antwort.text

        soup = BeautifulSoup(html, "html.parser")

        # Versuch: server-seitig eingebettete JSON-Daten ("__NEXT_DATA__" oder "window.__data__")
        events_aus_json: list[dict] = []
        for script in soup.find_all("script"):
            script_text = script.string or ""
            if '"dateTime"' in script_text or '"startDate"' in script_text:
                try:
                    # JSON-Block aus Script extrahieren
                    match = re.search(r'\{.*"dateTime".*\}', script_text, re.DOTALL)
                    if match:
                        daten = json.loads(match.group())
                        if isinstance(daten, dict) and daten.get("dateTime"):
                            event = _event_aus_gql_eintrag(daten, heute)
                            if event:
                                events_aus_json.append(event)
                except (json.JSONDecodeError, Exception):
                    pass

        if events_aus_json:
            logger.info("HTML-Fallback (JSON-Extraktion): %d Events", len(events_aus_json))
            return events_aus_json

        # Versuch: direkte HTML-Karten parsen
        selektoren = [
            "li[data-testid*='event']", "article[data-testid*='event']",
            "div[data-testid*='event']", ".event-card", ".eventCard",
            "li.event", "article.event",
        ]
        karten = []
        for selektor in selektoren:
            karten = soup.select(selektor)
            if karten:
                logger.debug("HTML: %d Karten mit '%s' gefunden", len(karten), selektor)
                break

        if not karten:
            logger.warning(
                "HTML-Fallback: Keine Event-Karten gefunden – "
                "Seite wahrscheinlich vollständig clientseitig gerendert. "
                "Für vollständiges Meetup-Scraping wird Playwright empfohlen."
            )
            return []

        events = []
        gesehene_urls: set[str] = set()
        for karte in karten:
            event = _event_aus_html_karte(karte, heute)
            if event and event["quelle_url"] not in gesehene_urls:
                gesehene_urls.add(event["quelle_url"])
                events.append(event)

        logger.info("HTML-Fallback: %d Events gefunden", len(events))
        return events

    except Exception as fehler:
        logger.error("HTML-Fallback fehlgeschlagen: %s", str(fehler))
        return []


# --- Hauptfunktion -------------------------------------------------------

def scrape() -> list[dict]:
    """
    Scrapt Community-Events von Meetup.com für Düsseldorf.

    Strategie:
    1. Primär: Interne GraphQL API (meetup.com/gql)
       → Keine API-Key erforderlich, nutzt Session-Cookies
       → Liefert strukturierte Daten inkl. Koordinaten, Venue, Gruppe
    2. Fallback: HTML-Scraping der Suchseite
       → Begrenzt durch clientseitiges Rendering
       → Tipp: Playwright für zuverlässigeres HTML-Scraping

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    # Primärstrategie: GraphQL
    events = _scrape_graphql(heute)
    logger.info("GraphQL: %d Events gefunden", len(events))

    # Fallback: HTML
    if not events:
        logger.warning("GraphQL lieferte keine Events – starte HTML-Fallback")
        events = _scrape_html(heute)
        logger.info("HTML-Fallback: %d Events gefunden", len(events))

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
