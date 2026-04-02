"""
allevents.py – DiesDasDüsseldorf
Scraper für AllEvents.in: Internationaler Event-Aggregator für Düsseldorf.
URL: https://allevents.in/dusseldorf

AllEvents.in listet Events aller Kategorien für Düsseldorf.
Die Seite bietet strukturierte HTML-Listings.

Erstellt: 2026-04-02
"""
import logging
from datetime import date, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen, uhrzeit_parsen
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://allevents.in"
LISTE_URL = "https://allevents.in/dusseldorf"
QUELLE_NAME = "AllEvents.in Düsseldorf"

KATEGORIE_MAPPING = {
    "music": "musik",
    "musik": "musik",
    "concert": "musik",
    "konzert": "musik",
    "festival": "musik",
    "party": "nightlife",
    "club": "nightlife",
    "nightlife": "nightlife",
    "theater": "kultur",
    "theatre": "kultur",
    "art": "kultur",
    "kunst": "kultur",
    "exhibition": "kultur",
    "ausstellung": "kultur",
    "film": "kultur",
    "cinema": "kultur",
    "food": "food",
    "culinary": "food",
    "sports": "sport",
    "sport": "sport",
    "fitness": "sport",
    "outdoor": "outdoor",
    "community": "community",
    "networking": "community",
    "workshop": "community",
    "business": "community",
    "family": "family",
    "kids": "family",
    "dating": "dating",
}


def _kategorie_erkennen(text: str) -> str:
    """
    Mappt AllEvents.in-Kategorietexte auf DiesDasDüsseldorf-Kategorien.

    Args:
        text: Kategorietext von der Webseite

    Returns:
        Gültige DiesDasDüsseldorf-Kategorie
    """
    if not text:
        return "sonstiges"

    schluessel = text.strip().lower()
    for keyword, kategorie in KATEGORIE_MAPPING.items():
        if keyword in schluessel:
            return kategorie

    return "sonstiges"


def _event_aus_element(el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem AllEvents.in Listen-Element.

    Args:
        el: BeautifulSoup-Element des Event-Eintrags
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None wenn Pflichtfelder fehlen / Event vergangen
    """
    try:
        # Titel
        titel_el = el.find("h3") or el.find("h2") or el.find(class_=lambda c: c and "title" in str(c).lower())
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

        # Datum aus allen Texten
        datum = None
        uhrzeit = None
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

        # Ort
        ort = None
        ort_el = el.find(class_=lambda c: c and any(w in str(c).lower() for w in ["venue", "location", "place", "ort"]))
        if ort_el:
            ort = ort_el.get_text(strip=True)

        if not ort:
            ort = "Düsseldorf"

        # Kategorie
        kategorie_el = el.find(class_=lambda c: c and "categor" in str(c).lower())
        kategorie_text = kategorie_el.get_text(strip=True) if kategorie_el else ""
        kategorie = _kategorie_erkennen(kategorie_text)

        # Bild
        bild_el = el.find("img")
        bild_url = None
        if bild_el:
            bild_url = (
                bild_el.get("data-src")
                or bild_el.get("data-lazy")
                or bild_el.get("src")
            )
            # Keine Platzhalter-Bilder
            if bild_url and ("placeholder" in bild_url.lower() or "default" in bild_url.lower()):
                bild_url = None

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
        logger.error("Fehler beim Parsen eines AllEvents.in-Events: %s", str(fehler))
        return None


def scrape() -> list[dict]:
    """
    Scrapt Events von AllEvents.in Düsseldorf.

    AllEvents.in ist ein internationaler Aggregator mit breiter Abdeckung
    aller Eventtypen in Düsseldorf.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = seite_abrufen(LISTE_URL, logger)
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Event-Elemente suchen (verschiedene mögliche Strukturen)
        event_elemente = (
            soup.find_all("li", class_=lambda c: c and "event" in " ".join(c).lower() if c else False)
            or soup.find_all("div", class_=lambda c: c and "event" in " ".join(c).lower() if c else False)
            or soup.find_all("article")
        )

        logger.info("AllEvents.in: %d Einträge gefunden", len(event_elemente))

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
