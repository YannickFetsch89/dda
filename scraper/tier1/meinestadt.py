"""
meinestadt.py – DiesDasDüsseldorf
Scraper für meinestadt.de: Veranstaltungen in Düsseldorf
Erstellt: 2026-02-24
"""
import logging
import re
import time
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://veranstaltungen.meinestadt.de"
LISTE_URL = "https://veranstaltungen.meinestadt.de/duesseldorf"
QUELLE_NAME = "meinestadt.de"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

# Vollständige Monatsnamen auf Deutsch
MONAT_MAP = {
    "januar": 1,
    "februar": 2,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "dezember": 12,
    # Kurzformen als Fallback
    "jan": 1,
    "feb": 2,
    "mär": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "okt": 10,
    "nov": 11,
    "dez": 12,
}

# Regex-Muster für Datum-Erkennung
_RE_DATUM_PUNKT = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
_RE_DATUM_KURZ = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.")
_RE_DATUM_TEXT = re.compile(
    r"(\d{1,2})\.\s*(" + "|".join(MONAT_MAP.keys()) + r")\s+(\d{4})",
    re.IGNORECASE,
)
_RE_UHRZEIT = re.compile(r"\b(\d{2}:\d{2})\b")


def _datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt verschiedene Datumsformate in ISO 8601 (YYYY-MM-DD) um.

    Unterstützte Formate:
        - "24.02.2026"
        - "24. Februar 2026"
        - "heute"
        - "morgen"
        - "Di, 24.02." (Jahr wird ergänzt)
        - Regex-Fallback für weitere Varianten

    Args:
        text: Roher Datumstext von der Webseite

    Returns:
        Datum als ISO-String (YYYY-MM-DD) oder None bei Fehler
    """
    if not text:
        return None

    heute = date.today()
    bereinigt = text.strip().lower()

    # "heute" und "morgen" direkt auflösen
    if bereinigt.startswith("heute"):
        return heute.isoformat()
    if bereinigt.startswith("morgen"):
        return (heute + timedelta(days=1)).isoformat()

    try:
        # Muster 1: "24.02.2026" – vollständiges Datum mit Jahr
        treffer = _RE_DATUM_PUNKT.search(bereinigt)
        if treffer:
            tag = int(treffer.group(1))
            monat = int(treffer.group(2))
            jahr = int(treffer.group(3))
            return date(jahr, monat, tag).isoformat()

        # Muster 2: "24. Februar 2026" – ausgeschriebener Monatsname
        treffer = _RE_DATUM_TEXT.search(bereinigt)
        if treffer:
            tag = int(treffer.group(1))
            monat_name = treffer.group(2).lower()
            jahr = int(treffer.group(3))
            monat = MONAT_MAP.get(monat_name)
            if monat:
                return date(jahr, monat, tag).isoformat()

        # Muster 3: "Di, 24.02." – kurzes Datum ohne Jahr
        treffer = _RE_DATUM_KURZ.search(bereinigt)
        if treffer:
            tag = int(treffer.group(1))
            monat = int(treffer.group(2))
            # Jahr bestimmen: aktuelles oder nächstes Jahr
            for delta_jahre in [0, 1]:
                try:
                    kandidat = date(heute.year + delta_jahre, monat, tag)
                    if kandidat >= heute - timedelta(days=1):
                        return kandidat.isoformat()
                except ValueError:
                    continue

    except (ValueError, AttributeError) as e:
        logger.warning("Datum konnte nicht geparst werden: '%s' – %s", text, e)

    return None


def _uhrzeit_extrahieren(text: str) -> Optional[str]:
    """
    Extrahiert eine Uhrzeit im Format HH:MM aus einem Text.

    Args:
        text: Beliebiger Text der eine Uhrzeit enthalten kann

    Returns:
        Uhrzeit als HH:MM String oder None
    """
    if not text:
        return None
    treffer = _RE_UHRZEIT.search(text)
    return treffer.group(1) if treffer else None


def _hat_datum_muster(text: str) -> bool:
    """
    Prüft ob ein Text ein erkennbares Datumsmuster enthält.

    Args:
        text: Zu prüfender Text

    Returns:
        True wenn ein Datum-Pattern gefunden wurde
    """
    bereinigt = text.strip().lower()
    if bereinigt.startswith(("heute", "morgen")):
        return True
    if _RE_DATUM_PUNKT.search(bereinigt):
        return True
    if _RE_DATUM_TEXT.search(bereinigt):
        return True
    if _RE_DATUM_KURZ.search(bereinigt):
        return True
    return False


def _preis_extrahieren(container) -> Optional[str]:
    """
    Sucht in einem HTML-Container nach Preisinformationen.

    Args:
        container: BeautifulSoup-Element

    Returns:
        Preistext oder None wenn kein Preis gefunden
    """
    preis_schluessel = ["€", "frei", "kostenlos", "eintritt", "eur"]
    for el in container.find_all(string=True):
        text = el.strip()
        if any(s in text.lower() for s in preis_schluessel) and len(text) < 80:
            return text
    return None


def _ort_extrahieren(container, alle_texte: list[str]) -> str:
    """
    Versucht den Veranstaltungsort aus dem Container zu extrahieren.
    Sucht bevorzugt nach Elementen die Ortsangaben signalisieren,
    fällt auf "Düsseldorf" zurück wenn nichts Besseres gefunden wird.

    Args:
        container: BeautifulSoup-Element des Events
        alle_texte: Liste aller Texte aus dem Container

    Returns:
        Ortsname als String (nie None – Fallback "Düsseldorf")
    """
    # Bevorzuge Elemente mit Orts-Klassen oder -Attributen
    ort_klassen = ["location", "venue", "ort", "place", "adress"]
    for klasse in ort_klassen:
        el = container.find(class_=re.compile(klasse, re.IGNORECASE))
        if el:
            text = el.get_text(strip=True)
            if text and 2 < len(text) < 100:
                return text

    # Fallback: Text der "Düsseldorf" enthält oder nach Datum kommt
    datum_gefunden = False
    for text in alle_texte:
        if _hat_datum_muster(text):
            datum_gefunden = True
            continue
        if datum_gefunden:
            # Nächster sinnvoller Text nach dem Datum ist häufig der Ort
            if 2 < len(text) < 100 and not text.isdigit():
                return text

    # Letzter Fallback
    for text in alle_texte:
        if "düsseldorf" in text.lower() and len(text) < 100:
            return text

    return "Düsseldorf"


def _container_finden(soup: BeautifulSoup) -> list:
    """
    Sucht Event-Container in der geparsten Seite mit mehreren Fallback-Strategien.

    Strategie 1: <article>-Elemente
    Strategie 2: div/section mit event-/veranstaltungs-/card-Klassen
    Strategie 3: <li>-Elemente mit event-/item-Klassen

    Args:
        soup: BeautifulSoup-Objekt der geparsten Seite

    Returns:
        Liste von BeautifulSoup-Elementen (kann leer sein)
    """
    # Strategie 1: article-Elemente (semantisch am wahrscheinlichsten)
    container = soup.find_all("article")
    if container:
        logger.info("Container-Strategie: <article> – %d Elemente", len(container))
        return container

    # Strategie 2: div/section mit Event-bezogenen Klassen
    def _event_klasse(css_klasse):
        if not css_klasse:
            return False
        klasse_str = " ".join(css_klasse) if isinstance(css_klasse, list) else css_klasse
        schluessel = ["event", "veranstaltung", "card", "listing", "item"]
        return any(k in klasse_str.lower() for k in schluessel)

    container = soup.find_all(["div", "section"], class_=_event_klasse)
    if container:
        logger.info(
            "Container-Strategie: div/section mit Event-Klassen – %d Elemente",
            len(container),
        )
        return container

    # Strategie 3: li-Elemente mit Event-bezogenen Klassen
    def _event_li_klasse(css_klasse):
        if not css_klasse:
            return False
        klasse_str = " ".join(css_klasse) if isinstance(css_klasse, list) else css_klasse
        return any(k in klasse_str.lower() for k in ["event", "item"])

    container = soup.find_all("li", class_=_event_li_klasse)
    if container:
        logger.info(
            "Container-Strategie: <li> mit Event-Klassen – %d Elemente",
            len(container),
        )
        return container

    return []


def _event_aus_container(element, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem HTML-Container-Element.

    Args:
        element: BeautifulSoup-Element eines einzelnen Events
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict im DiesDasDüsseldorf-Format oder None bei Pflichtfeld-Fehler
    """
    try:
        # --- Titel ---
        titel_el = (
            element.find("h1")
            or element.find("h2")
            or element.find("h3")
            or element.find("h4")
        )
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel:
            return None

        # --- Alle Texte im Container sammeln ---
        alle_texte = []
        for el in element.find_all(string=True):
            text = el.strip()
            if text and len(text) > 1:
                alle_texte.append(text)

        # --- Datum und Uhrzeit ---
        datum_raw = None
        uhrzeit = None
        for text in alle_texte:
            if _hat_datum_muster(text):
                datum_raw = text
                uhrzeit = _uhrzeit_extrahieren(text)
                break

        # Falls kein Datum direkt gefunden: alle Texte per Regex durchsuchen
        if not datum_raw:
            gesamttext = " ".join(alle_texte)
            if _hat_datum_muster(gesamttext):
                datum_raw = gesamttext
                uhrzeit = _uhrzeit_extrahieren(gesamttext)

        datum = _datum_parsen(datum_raw) if datum_raw else None
        if not datum:
            logger.debug("Kein Datum gefunden für Event: %s", titel)
            return None

        # Vergangene Events überspringen
        if date.fromisoformat(datum) < heute:
            return None

        # --- Ort ---
        ort = _ort_extrahieren(element, alle_texte)

        # --- URL ---
        link_el = element.find("a", href=True)
        if link_el:
            quelle_url = urljoin(BASE_URL, link_el["href"])
        else:
            quelle_url = LISTE_URL

        # --- Bild ---
        bild_el = element.find("img")
        bild_url = None
        if bild_el:
            bild_url = (
                bild_el.get("src")
                or bild_el.get("data-src")
                or bild_el.get("data-lazy-src")
            )

        # --- Preis ---
        preis = _preis_extrahieren(element)

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": None,
            "kategorie": "sonstiges",
            "beschreibung": None,
            "preis": preis,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "status": "neu",
        }

    except Exception as e:
        logger.error("Fehler beim Parsen eines Event-Containers: %s", str(e))
        return None


def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen von meinestadt.de für Düsseldorf.

    Abruft die Übersichtsseite, parst alle Event-Container mit mehreren
    Fallback-Strategien und gibt eine Liste normierter Event-Dicts zurück.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
        Leere Liste bei Fehler oder wenn keine Events gefunden wurden.
    """
    events: list[dict] = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        time.sleep(2)  # Rate Limiting

        with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            try:
                response = client.get(LISTE_URL)
                response.raise_for_status()
            except httpx.TimeoutException:
                logger.error("Timeout beim Abrufen von %s", LISTE_URL)
                return []
            except httpx.HTTPStatusError as e:
                logger.error(
                    "HTTP Fehler %s beim Abrufen von %s",
                    e.response.status_code,
                    LISTE_URL,
                )
                return []

        soup = BeautifulSoup(response.text, "html.parser")
        container_liste = _container_finden(soup)

        if not container_liste:
            logger.warning(
                "Keine Events gefunden – Seitenstruktur möglicherweise geändert"
            )
            return []

        logger.info("%d potenzielle Event-Container gefunden", len(container_liste))

        # Duplikate innerhalb eines Laufs per URL verhindern
        gesehene_urls: set[str] = set()

        for element in container_liste:
            event = _event_aus_container(element, heute)
            if not event:
                continue

            url = event["quelle_url"]
            if url in gesehene_urls:
                continue
            gesehene_urls.add(url)

            events.append(event)

        if not events:
            logger.warning(
                "Keine Events gefunden – Seitenstruktur möglicherweise geändert"
            )

    except Exception as e:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(e))
        return []

    logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    # Direkter Testlauf – gibt die ersten 3 gefundenen Events aus
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
