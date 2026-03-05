"""
stahlwerk.py – DiesDasDüsseldorf
Scraper für das Stahlwerk Düsseldorf: Konzerte, Club-Events und Partys.

Strategie:
1. Primär: JSON-LD structured data (schema.org/Event)
2. Fallback: HTML-Parsing der Event-Liste

Das Stahlwerk ist eine der größten Veranstaltungshallen Düsseldorfs mit
Fokus auf Rock, Metal, Electronic und Großveranstaltungen.

URL: https://www.stahlwerk-duesseldorf.de
Adresse: Ronsdorfer Str. 134, 40233 Düsseldorf
Erstellt: 2026-03-05
"""
import json
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen as _datum_parsen, uhrzeit_parsen as _uhrzeit_parsen
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://www.stahlwerk-duesseldorf.de"
LISTE_URL = "https://www.stahlwerk-duesseldorf.de"
QUELLE_NAME = "Stahlwerk Düsseldorf"
ORT_STANDARD = "Stahlwerk Düsseldorf"
ADRESSE_STANDARD = "Ronsdorfer Str. 134, 40233 Düsseldorf"

KATEGORIE_MAPPING = {
    "party": "nightlife", "club": "nightlife", "dj": "nightlife",
    "electronic": "nightlife", "techno": "nightlife", "house": "nightlife",
    "konzert": "musik", "rock": "musik", "metal": "musik", "pop": "musik",
    "live": "musik", "band": "musik", "hip hop": "musik", "rap": "musik",
    "comedy": "kultur", "show": "kultur",
}


def _kategorie_erkennen(text: str) -> str:
    """
    Mappt Titel/Kategorietexte auf DiesDasDüsseldorf-Kategorien.
    Nightlife und Musik dominieren beim Stahlwerk.

    Args:
        text: Titel oder Kategorietext

    Returns:
        Gültige Kategorie
    """
    if not text:
        return "musik"
    text_klein = text.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if schluessel in text_klein:
            return kategorie
    return "musik"  # Standard beim Stahlwerk: Musik


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
            if eintrag.get("@type") not in ("Event", "MusicEvent", "DanceEvent", "SocialEvent"):
                continue

            titel = eintrag.get("name", "").strip()
            if not titel:
                continue

            datum_roh = eintrag.get("startDate") or eintrag.get("startDateTime")
            datum = _datum_parsen(str(datum_roh)) if datum_roh else None
            if not datum or date.fromisoformat(datum) < heute:
                continue

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

            # Preis aus Angeboten
            preis = None
            angebote = eintrag.get("offers", [])
            if isinstance(angebote, dict):
                angebote = [angebote]
            if angebote:
                preise = [str(a.get("price", "")) for a in angebote if a.get("price")]
                if preise:
                    preis = f"ab {preise[0]}€"

            kategorie = _kategorie_erkennen(titel + " " + (beschreibung or ""))

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
                "preis": preis,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "instagram_caption": None,
                "datum_bis": None,
                "ist_wiederkehrend": False,
                "status": "neu",
            })

    return events


def _events_aus_html(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    Fallback: HTML-Parsing der Event-Übersicht.

    Args:
        soup: Geparste HTML-Seite
        heute: Heute-Datum für Filterung

    Returns:
        Liste von Event-Dicts
    """
    events = []
    gesehene_schluessel: set[str] = set()

    selektoren = [
        "article.event", "div.event", "li.event", ".event-item",
        "article[class*='event']", "div[class*='event']",
        ".show-item", ".concert-item", ".veranstaltung",
    ]

    karten = []
    for selektor in selektoren:
        karten = soup.select(selektor)
        if len(karten) > 1:
            logger.debug("HTML-Fallback: %d Karten mit Selektor '%s'", len(karten), selektor)
            break

    for karte in karten:
        try:
            titel_el = karte.find(["h2", "h3", "h4", "strong"])
            if not titel_el:
                continue
            titel = titel_el.get_text(strip=True)
            if not titel or len(titel) < 3:
                continue

            link_el = karte.find("a", href=True)
            quelle_url = urljoin(BASE_URL, link_el["href"]) if link_el else LISTE_URL

            datum_el = karte.find("time") or karte.find(class_=re.compile(r"date|datum|zeit", re.I))
            if not datum_el:
                continue
            datum_text = datum_el.get("datetime") or datum_el.get_text(strip=True)
            datum = _datum_parsen(datum_text)
            if not datum or date.fromisoformat(datum) < heute:
                continue

            uhrzeit = _uhrzeit_parsen(datum_text)

            bild_el = karte.find("img")
            bild_url = None
            if bild_el:
                bild_url = bild_el.get("data-src") or bild_el.get("src")
                if bild_url and bild_url.startswith("/"):
                    bild_url = urljoin(BASE_URL, bild_url)

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

        except Exception as fehler:
            logger.error("Fehler beim Parsen einer Event-Karte: %s", str(fehler))
            continue

    return events


def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen des Stahlwerks Düsseldorf.

    Strategie:
    1. JSON-LD structured data
    2. HTML-Parsing

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = seite_abrufen(LISTE_URL, logger)
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")

        events = _events_aus_json_ld(soup, heute)
        logger.info("JSON-LD: %d Events gefunden", len(events))

        if not events:
            logger.warning("JSON-LD leer – versuche HTML-Fallback")
            events = _events_aus_html(soup, heute)
            logger.info("HTML-Fallback: %d Events gefunden", len(events))

        events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]
        logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
        return events

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(fehler))
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
