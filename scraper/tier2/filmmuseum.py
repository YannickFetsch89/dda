"""
filmmuseum.py – DiesDasDüsseldorf
Scraper für das Filmmuseum Düsseldorf / Black Box Kino: Kinoprogramm und Events.

Strategie:
1. Primär: JSON-LD structured data (schema.org/Event, ScreeningEvent)
2. Fallback: HTML-Parsing der städtischen Website – .event-list, .veranstaltung,
   .program, table-Tags mit Kinoprogramm

URL: https://filmmuseum-duesseldorf.de/
Adresse: Schulstraße 4, 40213 Düsseldorf
Erstellt: 2026-03-06
"""
import json
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://filmmuseum-duesseldorf.de"
LISTE_URL = "https://filmmuseum-duesseldorf.de/black-box-kino/kinoprogramm"
FALLBACK_URL = "https://filmmuseum-duesseldorf.de/"
QUELLE_NAME = "Filmmuseum Düsseldorf"
ORT_STANDARD = "Black Box Kino im Filmmuseum Düsseldorf"
ADRESSE_STANDARD = "Schulstraße 4, 40213 Düsseldorf"
KATEGORIE_STANDARD = "kultur"

MONAT_MAP: dict[str, int] = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}
MONAT_KURZ_MAP: dict[str, int] = {
    "jan": 1, "feb": 2, "mär": 3, "mar": 3, "apr": 4,
    "mai": 5, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}

KATEGORIE_MAPPING = {
    "konzert": "musik", "musik": "musik", "live": "musik",
    "party": "nightlife", "club": "nightlife",
    "theater": "kultur", "ausstellung": "kultur", "kunst": "kultur",
    "kino": "kultur", "film": "kultur", "screening": "kultur",
    "workshop": "community", "vortrag": "community", "talk": "community",
    "festival": "musik",
}


def _datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt verschiedene Datumsformate in ISO 8601 (YYYY-MM-DD) um.

    Args:
        text: Roher Datumstext

    Returns:
        ISO-Datum oder None
    """
    if not text:
        return None

    heute = date.today()
    bereinigt = text.strip()
    bereinigt_klein = bereinigt.lower()

    try:
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(int(treffer.group(1)), int(treffer.group(2)), int(treffer.group(3))).isoformat()

        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1))).isoformat()

        treffer = re.search(r"(\d{1,2})\.?\s+([a-zäöüß]+)\s+(\d{4})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat = MONAT_MAP.get(treffer.group(2).lower())
            jahr = int(treffer.group(3))
            if monat:
                return date(jahr, monat, tag).isoformat()

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
    Extrahiert Uhrzeit im Format HH:MM aus Text.

    Args:
        text: Roher Text

    Returns:
        Uhrzeit als HH:MM oder None
    """
    if not text:
        return None
    treffer = re.search(r"\b(\d{1,2})[:\.](\d{2})\s*(?:Uhr)?", text, re.IGNORECASE)
    if treffer:
        stunde, minute = int(treffer.group(1)), int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"
    return None


def _kategorie_erkennen(text: str) -> str:
    """
    Mappt Texte auf DiesDasDüsseldorf-Kategorien.

    Args:
        text: Kategorie- oder Titeltext

    Returns:
        Gültige Kategorie
    """
    if not text:
        return KATEGORIE_STANDARD
    text_klein = text.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if schluessel in text_klein:
            return kategorie
    return KATEGORIE_STANDARD


def _events_aus_json_ld(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    Primärstrategie: JSON-LD structured data extrahieren.

    Args:
        soup: Geparste HTML-Seite
        heute: Heute-Datum für Filterung

    Returns:
        Liste von Event-Dicts
    """
    events = []
    gesehene_schluessel: set[str] = set()

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            daten = json.loads(script.string or "{}")
        except (json.JSONDecodeError, AttributeError):
            continue

        eintraege = daten if isinstance(daten, list) else [daten]
        for eintrag in eintraege:
            if not isinstance(eintrag, dict):
                continue
            if eintrag.get("@type") not in (
                "Event", "ExhibitionEvent", "VisualArtsEvent", "ScreeningEvent", "MusicEvent"
            ):
                continue

            titel = eintrag.get("name", "").strip()
            if not titel:
                continue

            datum_roh = eintrag.get("startDate") or eintrag.get("startDateTime")
            datum = _datum_parsen(str(datum_roh)) if datum_roh else None
            if not datum or date.fromisoformat(datum) < heute:
                continue

            ende_roh = eintrag.get("endDate")
            datum_bis = _datum_parsen(str(ende_roh)) if ende_roh else None

            uhrzeit = _uhrzeit_parsen(str(datum_roh))

            url_roh = eintrag.get("url")
            quelle_url = str(url_roh) if url_roh else LISTE_URL
            if quelle_url.startswith("/"):
                quelle_url = urljoin(BASE_URL, quelle_url)

            beschreibung_roh = eintrag.get("description")
            beschreibung = str(beschreibung_roh).strip()[:300] if beschreibung_roh else None

            bild_roh = eintrag.get("image")
            if isinstance(bild_roh, list) and bild_roh:
                bild_roh = bild_roh[0]
            if isinstance(bild_roh, dict):
                bild_url = bild_roh.get("url") or bild_roh.get("contentUrl")
            elif isinstance(bild_roh, str) and bild_roh.startswith("http"):
                bild_url = bild_roh
            else:
                bild_url = None

            kategorie = _kategorie_erkennen(titel)

            schluessel = f"{titel}_{datum}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ORT_STANDARD,
                "adresse": ADRESSE_STANDARD,
                "kategorie": kategorie,
                "beschreibung": beschreibung,
                "preis": None,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "instagram_caption": None,
                "datum_bis": datum_bis,
                "ist_wiederkehrend": False,
                "status": "neu",
            })

    return events


def _events_aus_html(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    HTML-Parsing der filmmuseum-duesseldorf.de Kinoprogramm-Seite.

    Struktur: div.b-teaser-slider__content Karten mit
    - Datum: <strong>Di 27.10.</strong>
    - Uhrzeit: <p>20:00 Uhr</p>
    - Titel: <a title="..."><strong>Titel</strong></a>
    - Info: <p>Regisseur · Land Jahr</p>
    """
    events = []
    gesehene_schluessel: set[str] = set()

    karten = soup.find_all("div", class_="b-teaser-slider__content")
    if not karten:
        karten = soup.select("article") or soup.select(".program-item") or soup.select(".veranstaltung")

    if not karten:
        logger.warning("HTML-Fallback: Keine Programm-Einträge gefunden")
        return []

    for karte in karten:
        datum_el = karte.find("strong")
        if not datum_el:
            continue
        datum_text = datum_el.get_text(strip=True)

        treffer = re.search(r"(\d{1,2})\.(\d{1,2})\.", datum_text)
        if not treffer:
            continue
        tag, monat = int(treffer.group(1)), int(treffer.group(2))
        jahr = heute.year
        try:
            datum_obj = date(jahr, monat, tag)
        except ValueError:
            continue
        if datum_obj < heute:
            datum_obj = date(jahr + 1, monat, tag)
        datum = datum_obj.isoformat()

        uhrzeit = None
        for p in karte.find_all("p"):
            uhrzeit_kandidat = _uhrzeit_parsen(p.get_text(strip=True))
            if uhrzeit_kandidat:
                uhrzeit = uhrzeit_kandidat
                break

        link_el = karte.find("a", href=lambda h: h and "/kinoprogramm/" in h)
        if not link_el:
            continue
        titel = link_el.get("title") or link_el.get_text(strip=True)
        if not titel:
            continue

        quelle_url = link_el["href"]
        if not quelle_url.startswith("http"):
            quelle_url = urljoin(BASE_URL, quelle_url)

        bild_el = karte.find("img")
        bild_url = None
        if bild_el:
            bild_src = bild_el.get("src") or bild_el.get("data-src")
            if bild_src:
                bild_url = bild_src if bild_src.startswith("http") else urljoin(BASE_URL, bild_src)

        schluessel = f"{titel}_{datum}"
        if schluessel in gesehene_schluessel:
            continue
        gesehene_schluessel.add(schluessel)

        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT_STANDARD,
            "adresse": ADRESSE_STANDARD,
            "kategorie": KATEGORIE_STANDARD,
            "beschreibung": None,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        })

    return events


def scrape() -> list[dict]:
    """
    Scrapt das Kinoprogramm und Events des Filmmuseums Düsseldorf / Black Box Kino.

    Strategie:
    1. JSON-LD structured data
    2. HTML-Parsing als Fallback (table-Tags, Event-Listen)

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    for url in [LISTE_URL, FALLBACK_URL]:
        try:
            html = seite_abrufen(url, logger)
            if html is None:
                logger.warning("Filmmuseum URL nicht erreichbar: %s", url)
                continue

            soup = BeautifulSoup(html, "html.parser")

            events = _events_aus_json_ld(soup, heute)
            logger.info("JSON-LD (%s): %d Events gefunden", url, len(events))

            if not events:
                logger.warning("JSON-LD leer – versuche HTML-Parsing")
                events = _events_aus_html(soup, heute)
                logger.info("HTML-Fallback (%s): %d Events gefunden", url, len(events))

            if events:
                events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]
                logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
                return events

        except Exception as fehler:
            logger.error("Scraper %s fehlgeschlagen bei %s: %s", QUELLE_NAME, url, str(fehler))

    logger.warning("Scraper %s: Keine Events von keiner URL gefunden", QUELLE_NAME)
    return []


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json as _json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
