"""
allevents.py – DiesDasDüsseldorf
Scraper für AllEvents.in: Internationaler Event-Aggregator für Düsseldorf.
URL: https://allevents.in/dusseldorf

AllEvents.in listet Events aller Kategorien für Düsseldorf.
Die Seite erfordert JavaScript-Rendering (Playwright).

Erstellt: 2026-04-02
"""
import logging
import re
import time
from datetime import date, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE

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
    "comedy": "kultur",
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

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

MONAT_MAP_EN = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _kategorie_erkennen(text: str) -> str:
    """
    Mappt AllEvents.in-Kategorietexte auf DiesDasDüsseldorf-Kategorien.
    """
    if not text:
        return "sonstiges"
    schluessel = text.strip().lower()
    for keyword, kategorie in KATEGORIE_MAPPING.items():
        if keyword in schluessel:
            return kategorie
    return "sonstiges"


def _datum_parsen(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parst AllEvents.in-Datumsformat wie 'Sat, 05 Dec • 10:00 AM'
    oder 'Tue, 27 Oct • 8:00 PM' in ISO-Datum und Uhrzeit.

    Returns:
        Tuple (datum_iso, uhrzeit) oder (None, None)
    """
    if not text:
        return None, None

    heute = date.today()

    treffer = re.search(
        r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"(?:\s+(\d{4}))?"
        r"(?:\s*[•·]\s*(\d{1,2}):(\d{2})\s*(AM|PM))?",
        text, re.IGNORECASE
    )
    if not treffer:
        return None, None

    tag = int(treffer.group(1))
    monat = MONAT_MAP_EN.get(treffer.group(2)[:3].lower())
    if not monat:
        return None, None

    jahr = int(treffer.group(3)) if treffer.group(3) else None
    if jahr is None:
        kandidat = date(heute.year, monat, tag)
        if kandidat < heute - timedelta(days=7):
            kandidat = date(heute.year + 1, monat, tag)
        jahr = kandidat.year

    try:
        datum = date(jahr, monat, tag)
    except ValueError:
        return None, None

    uhrzeit = None
    if treffer.group(4) and treffer.group(5):
        stunde = int(treffer.group(4))
        minute = int(treffer.group(5))
        am_pm = (treffer.group(6) or "").upper()
        if am_pm == "PM" and stunde != 12:
            stunde += 12
        elif am_pm == "AM" and stunde == 12:
            stunde = 0
        uhrzeit = f"{stunde:02d}:{minute:02d}"

    return datum.isoformat(), uhrzeit


def scrape() -> list[dict]:
    """
    Scrapt Events von AllEvents.in Düsseldorf via Playwright.
    """
    from playwright.sync_api import sync_playwright

    events = []
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    html = ""
    try:
        time.sleep(2)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            seite = browser.new_page(user_agent=USER_AGENT)
            try:
                seite.goto(LISTE_URL, timeout=30000, wait_until="networkidle")
                seite.wait_for_timeout(3000)
                html = seite.content()
            except Exception as fehler:
                logger.error("Playwright Fehler: %s", fehler)
            finally:
                browser.close()
    except Exception as fehler:
        logger.error("Playwright konnte nicht gestartet werden: %s", fehler)
        return []

    if not html:
        logger.warning("Kein HTML geladen von %s", LISTE_URL)
        return []

    soup = BeautifulSoup(html, "html.parser")
    karten = soup.select("li.event-card")
    logger.info("AllEvents.in: %d Event-Cards gefunden", len(karten))

    gesehene_urls: set[str] = set()

    for karte in karten:
        try:
            titel_el = karte.select_one("h3")
            if not titel_el:
                continue
            titel = titel_el.get_text(strip=True)
            if not titel:
                continue

            quelle_url = karte.get("data-link", "")
            if not quelle_url:
                link_el = karte.select_one("a[href]")
                if link_el:
                    quelle_url = link_el["href"]
            if not quelle_url.startswith("http"):
                quelle_url = BASE_URL + quelle_url

            if quelle_url in gesehene_urls:
                continue
            gesehene_urls.add(quelle_url)

            datum_el = karte.select_one(".date")
            datum_text = datum_el.get_text(strip=True) if datum_el else ""
            datum, uhrzeit = _datum_parsen(datum_text)
            if not datum:
                continue

            datum_obj = date.fromisoformat(datum)
            if datum_obj < heute or datum_obj > enddatum:
                continue

            ort_el = karte.select_one(".location")
            ort = ort_el.get_text(strip=True) if ort_el else "Düsseldorf"
            if not ort:
                ort = "Düsseldorf"

            bild_el = karte.select_one("img.banner-img")
            bild_url = None
            if bild_el:
                bild_url = bild_el.get("data-src") or bild_el.get("src")
                if bild_url and ("placeholder" in bild_url.lower() or bild_url.startswith("data:")):
                    bild_url = None

            preis_el = karte.select_one(".price")
            preis = None
            if preis_el:
                preis_text = preis_el.get_text(strip=True)
                if preis_text.lower() in ("free", "kostenlos"):
                    preis = "kostenlos"
                elif preis_text:
                    preis = preis_text

            kategorie = _kategorie_erkennen(titel)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ort,
                "adresse": None,
                "kategorie": kategorie,
                "beschreibung": None,
                "preis": preis,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "instagram_caption": None,
                "datum_bis": None,
                "ist_wiederkehrend": False,
                "status": "neu",
            })

        except Exception as fehler:
            logger.error("Fehler beim Parsen eines AllEvents.in-Events: %s", str(fehler))
            continue

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
