"""
rausgegangen.py – DiesDasDüsseldorf
Scraper für Rausgegangen.de: Events in Düsseldorf
Verwendet Playwright wegen Cloudflare-Schutz.
"""
import logging
import time
from datetime import date, datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from config import SCRAPER_VORSCHAU_TAGE

logger = logging.getLogger(__name__)

BASE_URL = "https://rausgegangen.de"
LISTE_URL = "https://rausgegangen.de/duesseldorf/"
QUELLE_NAME = "Rausgegangen"

KATEGORIE_MAPPING = {
    "party": "nightlife",
    "club": "nightlife",
    "konzert": "musik",
    "musik": "musik",
    "live": "musik",
    "shows": "kultur",
    "theater": "kultur",
    "ausstellung": "kultur",
    "kunst": "kultur",
    "kino": "kultur",
    "film": "kultur",
    "oper": "kultur",
    "comedy": "kultur",
    "performance": "kultur",
    "sport": "sport",
    "outdoor": "outdoor",
    "natur": "outdoor",
    "food": "food",
    "markt": "food",
    "essen": "food",
    "aktiv": "community",
    "kreativ": "community",
    "workshop": "community",
    "meetup": "community",
    "networking": "community",
    "kinder": "family",
    "familie": "family",
    "dating": "dating",
    "singles": "dating",
}


def _datum_parsen(datum_text: str) -> Optional[str]:
    heute = date.today()
    if not datum_text:
        return None

    datum_text = datum_text.strip().lower()
    # Pipe-Teil (Uhrzeit) abschneiden
    datum_teil = datum_text.split("|")[0].strip()

    try:
        if datum_teil.startswith("heute"):
            return heute.isoformat()
        if datum_teil.startswith("morgen"):
            return (heute + timedelta(days=1)).isoformat()

        monat_map = {
            "jan": 1, "feb": 2, "mär": 3, "apr": 4,
            "mai": 5, "jun": 6, "jul": 7, "aug": 8,
            "sep": 9, "okt": 10, "nov": 11, "dez": 12,
        }

        teile = datum_teil.split(",")
        rest = teile[-1].strip() if len(teile) > 1 else datum_teil
        woerter = rest.split()
        if len(woerter) >= 2:
            tag = int(woerter[0].replace(".", ""))
            monat = monat_map.get(woerter[1][:3].lower())
            if monat is None:
                return None
            jahr = heute.year
            kandidat = date(jahr, monat, tag)
            if kandidat < heute - timedelta(days=1):
                kandidat = date(jahr + 1, monat, tag)
            return kandidat.isoformat()
    except (ValueError, IndexError):
        return None
    return None


def _uhrzeit_parsen(datum_text: str) -> Optional[str]:
    if "|" not in datum_text:
        return None
    try:
        uhrzeit_teil = datum_text.split("|")[1].strip()
        uhrzeit = uhrzeit_teil.replace("Uhr", "").strip()
        datetime.strptime(uhrzeit, "%H:%M")
        return uhrzeit
    except (ValueError, IndexError):
        return None


def _kategorie_erkennen(kategorie_text: str) -> str:
    if not kategorie_text:
        return "sonstiges"
    schluessel = kategorie_text.strip().lower()
    for keyword, kategorie in KATEGORIE_MAPPING.items():
        if keyword in schluessel:
            return kategorie
    return "sonstiges"


def _seite_laden() -> Optional[str]:
    """Lädt die Rausgegangen-Seite mit Playwright (Cloudflare-Bypass)."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="de-DE",
            )
            page = context.new_page()
            page.goto(LISTE_URL, timeout=60000)
            time.sleep(8)
            page.wait_for_selector("[data-testid='event-tile-link']", timeout=15000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        logger.error("Playwright-Fehler beim Laden von %s: %s", LISTE_URL, e)
        return None


def _event_aus_karte(karte, heute: date) -> Optional[dict]:
    try:
        pfad = karte.get("href", "")
        if not pfad:
            return None
        quelle_url = BASE_URL + pfad if pfad.startswith("/") else pfad

        titel_el = karte.select_one("[data-testid='event-tile-name']")
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel:
            return None

        datum_el = karte.select_one("[data-testid='event-tile-datetime']")
        datum_text = datum_el.get_text(strip=True) if datum_el else None
        datum = _datum_parsen(datum_text) if datum_text else None
        if not datum:
            return None

        if date.fromisoformat(datum) < heute:
            return None

        uhrzeit = _uhrzeit_parsen(datum_text) if datum_text else None

        ort_el = karte.select_one("p.text-bw-medium")
        ort = ort_el.get_text(strip=True) if ort_el else None
        if not ort:
            return None

        preis_el = karte.select_one("p.text-primary")
        preis = preis_el.get_text(strip=True) if preis_el else None

        kat_el = karte.select_one("[data-testid='badge-category']")
        kategorie_text = kat_el.get_text(strip=True) if kat_el else ""
        kategorie = _kategorie_erkennen(kategorie_text)

        bild_url = None
        img_el = karte.select_one("picture source")
        if img_el:
            srcset = img_el.get("srcset", "")
            if srcset:
                bild_url = srcset.split(",")[0].split(" ")[0]
        if not bild_url:
            img_tag = karte.select_one("img")
            if img_tag:
                bild_url = img_tag.get("src")

        return {
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
        }
    except Exception as e:
        logger.error("Fehler beim Parsen einer Event-Karte: %s", str(e))
        return None


def scrape(ziel_datum: Optional[date] = None) -> list[dict]:
    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    html = _seite_laden()
    if html is None:
        return []

    soup = BeautifulSoup(html, "html.parser")
    karten = soup.select("a.event-tile")
    logger.info("%d Event-Karten gefunden", len(karten))

    gesehene_urls: set[str] = set()
    for karte in karten:
        url = karte.get("href", "")
        if url in gesehene_urls:
            continue
        gesehene_urls.add(url)
        event = _event_aus_karte(karte, heute)
        if event:
            events.append(event)

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
    for e in ergebnisse[:5]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
