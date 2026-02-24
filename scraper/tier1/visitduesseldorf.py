"""
visitduesseldorf.py – DiesDasDüsseldorf
Scraper für VisitDüsseldorf: Veranstaltungskalender der Tourismusbehörde
Erstellt: 2026-02-24
"""
import logging
import re
import time
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.visitduesseldorf.de"
LISTE_URL = "https://www.visitduesseldorf.de/erleben/veranstaltungen"
QUELLE_NAME = "VisitDüsseldorf"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

MONAT_MAP = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}

# Abkürzungen für den Monatsnamen (z.B. "Jan." → 1)
MONAT_KURZ_MAP = {
    "jan": 1, "feb": 2, "mär": 3, "apr": 4,
    "mai": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "nov": 11, "dez": 12,
}

# Bekannte Düsseldorfer Venues für Ort-Erkennung
BEKANNTE_VENUES = [
    "tonhalle", "schauspielhaus", "oper am rhein", "kunstpalast",
    "kunstsammlung", "k20", "k21", "nrw-forum", "kunsthalle",
    "filmmuseum", "zakk", "stahlwerk", "rudas", "d.live",
    "mitsubishi electric halle", "fft düsseldorf", "stadtbücherei",
    "altstadt", "medienhafen", "rheinufer", "kö", "königsallee",
]


def _datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt verschiedene Datumsformate in ISO 8601 um.

    Unterstützte Formate:
        - "24.02.2026"         → "2026-02-24"
        - "24. Februar 2026"   → "2026-02-24"
        - "2026-02-24"         → "2026-02-24"
        - "Di, 24.02."         → nächstes passendes Jahr wird ermittelt

    Args:
        text: Roher Datumstext von der Webseite

    Returns:
        Datum als ISO-String (YYYY-MM-DD) oder None bei Fehler
    """
    if not text:
        return None

    heute = date.today()
    bereinigt = text.strip().lower()

    try:
        # Format: "2026-02-24" (ISO bereits vorhanden)
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(1)),
                int(treffer.group(2)),
                int(treffer.group(3)),
            ).isoformat()

        # Format: "24.02.2026"
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(3)),
                int(treffer.group(2)),
                int(treffer.group(1)),
            ).isoformat()

        # Format: "24. Februar 2026" oder "24. februar 2026"
        treffer = re.search(
            r"(\d{1,2})\.\s*([a-zäöü]+)\s+(\d{4})", bereinigt
        )
        if treffer:
            tag = int(treffer.group(1))
            monat_name = treffer.group(2).lower()
            jahr = int(treffer.group(3))
            monat = MONAT_MAP.get(monat_name)
            if monat:
                return date(jahr, monat, tag).isoformat()

        # Format: "Di, 24.02." – Jahr fehlt, nächstes passendes ermitteln
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.", bereinigt)
        if treffer:
            tag = int(treffer.group(1))
            monat = int(treffer.group(2))
            jahr = heute.year
            try:
                kandidat = date(jahr, monat, tag)
            except ValueError:
                return None
            # Falls Datum bereits vergangen, nächstes Jahr versuchen
            if kandidat < heute - timedelta(days=1):
                kandidat = date(jahr + 1, monat, tag)
            return kandidat.isoformat()

        # Format: "24. Feb" oder "24. Feb." (ohne Jahr)
        treffer = re.search(r"(\d{1,2})\.\s*([a-zäöü]{3})", bereinigt)
        if treffer:
            tag = int(treffer.group(1))
            monat_kurz = treffer.group(2)[:3].lower()
            monat = MONAT_KURZ_MAP.get(monat_kurz)
            if monat:
                jahr = heute.year
                try:
                    kandidat = date(jahr, monat, tag)
                except ValueError:
                    return None
                if kandidat < heute - timedelta(days=1):
                    kandidat = date(jahr + 1, monat, tag)
                return kandidat.isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning(
            "Datum konnte nicht geparst werden: '%s' – %s", text, fehler
        )
        return None

    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """
    Extrahiert eine Uhrzeit (HH:MM) aus einem beliebigen Text.

    Args:
        text: Roher Text mit möglicher Zeitangabe

    Returns:
        Uhrzeit als HH:MM String oder None
    """
    if not text:
        return None

    treffer = re.search(r"\b(\d{1,2})[:\.](\d{2})\s*(?:Uhr)?", text, re.IGNORECASE)
    if treffer:
        stunde = int(treffer.group(1))
        minute = int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"
    return None


def _ort_aus_text(texte: list[str]) -> Optional[str]:
    """
    Sucht in einer Textliste nach einem Ort in Düsseldorf.

    Prüft zuerst bekannte Venue-Namen, dann ob "Düsseldorf" enthalten ist.

    Args:
        texte: Liste von Texten aus dem Event-Container

    Returns:
        Erkannter Ort oder None
    """
    for text in texte:
        text_lower = text.lower()
        for venue in BEKANNTE_VENUES:
            if venue in text_lower:
                return text.strip()

    for text in texte:
        if "düsseldorf" in text.lower() and len(text.strip()) < 120:
            return text.strip()

    return None


def _event_aus_container(element, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem BeautifulSoup-Container-Element.

    Args:
        element: BeautifulSoup-Element (article, div, li)
        heute:   Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None wenn Pflichtfelder fehlen / Event vergangen
    """
    try:
        # --- Titel ---
        titel_el = (
            element.find("h1") or
            element.find("h2") or
            element.find("h3") or
            element.find("h4")
        )
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel:
            return None

        # --- URL ---
        anker = element.find("a", href=True)
        if anker:
            quelle_url = urljoin(BASE_URL, anker["href"])
        else:
            quelle_url = urljoin(BASE_URL, element.get("href", "")) or LISTE_URL

        # --- Alle Texte aus dem Container sammeln ---
        alle_texte = []
        for el in element.find_all(["span", "div", "p", "time", "li", "strong"]):
            t = el.get_text(separator=" ", strip=True)
            if t and len(t) > 1:
                alle_texte.append(t)

        # Volltext des Containers als Fallback
        volltext = element.get_text(separator=" ", strip=True)

        # --- Datum suchen ---
        datum = None
        datum_text_roh = None

        # Zuerst <time datetime="..."> auslesen
        time_el = element.find("time")
        if time_el:
            dt_attr = time_el.get("datetime", "")
            datum = _datum_parsen(dt_attr) if dt_attr else None
            if not datum:
                datum = _datum_parsen(time_el.get_text(strip=True))
            datum_text_roh = time_el.get_text(strip=True)

        # Falls kein <time> oder kein Ergebnis: alle Texte durchsuchen
        if not datum:
            for text in alle_texte:
                kandidat = _datum_parsen(text)
                if kandidat:
                    datum = kandidat
                    datum_text_roh = text
                    break

        # Letzter Versuch: Volltext des gesamten Containers
        if not datum:
            datum = _datum_parsen(volltext)
            datum_text_roh = volltext if datum else None

        if not datum:
            logger.debug("Kein Datum gefunden für Event: %s", titel)
            return None

        # Vergangene Events überspringen
        if date.fromisoformat(datum) < heute:
            return None

        # --- Uhrzeit ---
        uhrzeit = None
        if datum_text_roh:
            uhrzeit = _uhrzeit_parsen(datum_text_roh)
        if not uhrzeit:
            uhrzeit = _uhrzeit_parsen(volltext)

        # --- Ort ---
        ort = _ort_aus_text(alle_texte)
        if not ort:
            # Fallback: Düsseldorf
            ort = "Düsseldorf"

        # --- Beschreibung ---
        beschreibung = None
        for el in element.find_all(["p"]):
            text = el.get_text(strip=True)
            if text and len(text) > 20 and text != titel:
                beschreibung = text[:300]
                break

        # --- Preis ---
        preis = None
        preis_schluesselbegriffe = ["kostenlos", "frei", "eintritt frei", "€", "eur"]
        for text in alle_texte:
            if any(p in text.lower() for p in preis_schluesselbegriffe):
                preis = text.strip()[:100]
                break

        # --- Bild ---
        bild_el = element.find("img")
        bild_url = None
        if bild_el:
            bild_url = (
                bild_el.get("src") or
                bild_el.get("data-src") or
                bild_el.get("data-lazy-src")
            )
            if bild_url:
                bild_url = urljoin(BASE_URL, bild_url)

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": None,
            "kategorie": "sonstiges",
            "beschreibung": beschreibung,
            "preis": preis,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error("Fehler beim Parsen eines Event-Containers: %s", str(fehler))
        return None


def scrape() -> list[dict]:
    """
    Scrapt Events von VisitDüsseldorf (Veranstaltungskalender).

    Probiert mehrere DOM-Selektoren, da die genaue Seitenstruktur variieren kann.
    Filtert vergangene Events heraus und verhindert Duplikate innerhalb eines Laufs.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
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
            except httpx.HTTPStatusError as fehler:
                logger.error(
                    "HTTP Fehler %s beim Abrufen von %s",
                    fehler.response.status_code, LISTE_URL,
                )
                return []

        soup = BeautifulSoup(response.text, "html.parser")

        # Robuste Selektor-Strategie: mehrere Container-Typen ausprobieren
        container = (
            soup.find_all("article") or
            soup.find_all(
                "div",
                class_=lambda c: c and any(
                    k in c.lower()
                    for k in ["event", "veranstaltung", "card", "item"]
                ),
            ) or
            soup.find_all(
                "li",
                class_=lambda c: c and "event" in c.lower()
            )
        )

        if not container:
            logger.warning(
                "Keine Event-Container gefunden auf %s – "
                "Seitenstruktur hat sich möglicherweise geändert.",
                LISTE_URL,
            )
            return []

        logger.info("%d potenzielle Event-Container gefunden", len(container))

        # Duplikate innerhalb eines Scraper-Laufs verhindern
        gesehene_urls: set[str] = set()

        for element in container:
            event = _event_aus_container(element, heute)
            if event is None:
                continue

            url = event["quelle_url"]
            if url in gesehene_urls:
                continue
            gesehene_urls.add(url)

            events.append(event)

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(fehler))
        return []

    if len(events) == 0:
        logger.warning(
            "Scraper %s: 0 Events gefunden – "
            "Seitenstruktur hat sich möglicherweise geändert.",
            QUELLE_NAME,
        )

    logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    # Direkter Testlauf
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
