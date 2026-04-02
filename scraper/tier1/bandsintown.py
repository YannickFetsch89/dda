"""
bandsintown.py – DiesDasDüsseldorf
Integration der Bandsintown API für Konzert-Events in Düsseldorf.
API-Dokumentation: https://artists.bandsintown.com/support/public-api

Bandsintown bietet strukturierte Konzertdaten über eine öffentliche API.
Der Endpoint gibt Events für eine Stadt zurück.

Authentifizierung: App-ID via Umgebungsvariable BANDSINTOWN_APP_ID
(Kostenlos verfügbar – eigener App-Name als Identifier ausreichend)

Hinweis: Die Bandsintown API ist künstler-zentriert, nicht standort-zentriert.
Für stadtbasiertes Scraping wird die Event-Discovery Seite genutzt.

Erstellt: 2026-04-02
"""
import logging
import os
import time
from datetime import date, timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen, uhrzeit_parsen
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

QUELLE_NAME = "Bandsintown"
DISCOVER_URL = "https://www.bandsintown.com/c/dusseldorf-germany"
BASE_URL = "https://www.bandsintown.com"

KATEGORIE_STANDARD = "musik"

KATEGORIE_MAPPING = {
    "concert": "musik",
    "festival": "musik",
    "club": "nightlife",
    "dj": "nightlife",
    "electronic": "nightlife",
}


def _kategorie_erkennen(text: str) -> str:
    """
    Mappt Bandsintown-Genretext auf DiesDasDüsseldorf-Kategorien.

    Args:
        text: Genre- oder Typentext

    Returns:
        Gültige DiesDasDüsseldorf-Kategorie
    """
    if not text:
        return KATEGORIE_STANDARD

    schluessel = text.strip().lower()
    for keyword, kategorie in KATEGORIE_MAPPING.items():
        if keyword in schluessel:
            return kategorie

    return KATEGORIE_STANDARD


def _event_aus_element(el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem Bandsintown Discover-Seiten-Element.

    Args:
        el: BeautifulSoup-Element
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None
    """
    try:
        # Titel (Künstlername)
        titel_el = (
            el.find("h2")
            or el.find("h3")
            or el.find(class_=lambda c: c and "artist" in str(c).lower())
        )
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel:
            return None

        # URL
        link_el = el.find("a", href=True)
        if not link_el:
            return None
        href = link_el["href"]
        quelle_url = href if href.startswith("http") else BASE_URL + href

        # Datum
        datum = None
        uhrzeit = None
        datum_el = el.find("time") or el.find(class_=lambda c: c and "date" in str(c).lower())
        if datum_el:
            datum_text = datum_el.get("datetime") or datum_el.get_text(strip=True)
            datum = datum_parsen(datum_text)
            uhrzeit = uhrzeit_parsen(datum_text)

        if not datum:
            # Fallback: alle Texte durchsuchen
            for text_el in el.find_all(True):
                text = text_el.get_text(strip=True)
                datum_kandidat = datum_parsen(text)
                if datum_kandidat:
                    datum = datum_kandidat
                    uhrzeit = uhrzeit_parsen(text)
                    break

        if not datum:
            return None

        if date.fromisoformat(datum) < heute:
            return None

        # Venue / Ort
        ort = None
        ort_el = el.find(class_=lambda c: c and any(w in str(c).lower() for w in ["venue", "location"]))
        if ort_el:
            ort = ort_el.get_text(strip=True)

        if not ort:
            ort = "Düsseldorf"

        # Bild
        bild_el = el.find("img")
        bild_url = None
        if bild_el:
            bild_url = (
                bild_el.get("src")
                or bild_el.get("data-src")
            )
            if bild_url and ("placeholder" in bild_url.lower() or not bild_url.startswith("http")):
                bild_url = None

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": None,
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
        }

    except Exception as fehler:
        logger.error("Fehler beim Parsen eines Bandsintown-Events: %s", str(fehler))
        return None


def scrape() -> list[dict]:
    """
    Scrapt Konzert-Events von der Bandsintown Discover-Seite für Düsseldorf.

    Bandsintown ist ein führender Konzert-Aggregator und ergänzt Songkick
    mit teils anderen Künstlern und Events.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = seite_abrufen(DISCOVER_URL, logger)
        if html is None:
            logger.warning("Bandsintown Discover-Seite nicht erreichbar.")
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Event-Elemente suchen
        event_elemente = (
            soup.find_all("article")
            or soup.find_all("li", class_=lambda c: c and "event" in " ".join(c).lower() if c else False)
            or soup.find_all("div", class_=lambda c: c and "event" in " ".join(c).lower() if c else False)
        )

        logger.info("Bandsintown: %d Einträge gefunden", len(event_elemente))

        gesehene_urls: set[str] = set()

        for el in event_elemente:
            event = _event_aus_element(el, heute)
            if event:
                url = event.get("quelle_url", "")
                if url not in gesehene_urls:
                    gesehene_urls.add(url)
                    events.append(event)

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(fehler))
        return []

    # 14-Tage-Fenster
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]

    logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
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
