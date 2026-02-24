"""
visitduesseldorf.py – DiesDasDüsseldorf
Scraper für VisitDüsseldorf: Veranstaltungskalender der Tourismusbehörde
Nutzt Playwright, da die Seite JavaScript-gerendert ist (Angular SPA).
Erstellt: 2026-02-24
"""
import logging
import re
import time
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from config import SCRAPER_VORSCHAU_TAGE

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.visitduesseldorf.de"
LISTE_URL = "https://www.visitduesseldorf.de/erleben/veranstaltungen"
QUELLE_NAME = "VisitDüsseldorf"

MONAT_MAP = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}

MONAT_KURZ_MAP = {
    "jan": 1, "feb": 2, "mär": 3, "apr": 4,
    "mai": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "nov": 11, "dez": 12,
}

KATEGORIE_MAP = {
    "ausstellung": "kultur",
    "theater": "kultur",
    "oper": "kultur",
    "konzert": "musik",
    "musik": "musik",
    "festival": "musik",
    "party": "nightlife",
    "club": "nightlife",
    "sport": "sport",
    "lesung": "kultur",
    "film": "kultur",
    "kino": "kultur",
    "führung": "kultur",
    "stadtführung": "kultur",
    "workshop": "community",
    "messe": "community",
    "markt": "food",
    "food": "food",
    "family": "family",
    "kinder": "family",
    "outdoor": "outdoor",
}


def _datum_parsen(text: str) -> Optional[str]:
    """Wandelt verschiedene Datumsformate in ISO 8601 um."""
    if not text:
        return None
    heute = date.today()
    bereinigt = text.strip().lower()
    try:
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(int(treffer.group(1)), int(treffer.group(2)), int(treffer.group(3))).isoformat()

        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1))).isoformat()

        treffer = re.search(r"(\d{1,2})\.\s*([a-zäöü]+)\s+(\d{4})", bereinigt)
        if treffer:
            tag, monat_name, jahr = int(treffer.group(1)), treffer.group(2).lower(), int(treffer.group(3))
            monat = MONAT_MAP.get(monat_name)
            if monat:
                return date(jahr, monat, tag).isoformat()

        treffer = re.search(r"(\d{1,2})\.(\d{2})\.", bereinigt)
        if treffer:
            tag, monat = int(treffer.group(1)), int(treffer.group(2))
            try:
                kandidat = date(heute.year, monat, tag)
            except ValueError:
                return None
            if kandidat < heute - timedelta(days=1):
                kandidat = date(heute.year + 1, monat, tag)
            return kandidat.isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning("Datum konnte nicht geparst werden: '%s' – %s", text, fehler)
    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """Extrahiert eine Uhrzeit (HH:MM) aus einem beliebigen Text."""
    if not text:
        return None
    treffer = re.search(r"\b(\d{1,2})[:\.](\d{2})\s*(?:Uhr)?", text, re.IGNORECASE)
    if treffer:
        stunde, minute = int(treffer.group(1)), int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"
    return None


def _kategorie_aus_text(text: str) -> str:
    """Ermittelt eine DDA-Kategorie aus einem Kategorie-Text."""
    if not text:
        return "sonstiges"
    text_lower = text.lower()
    for schluessel, kategorie in KATEGORIE_MAP.items():
        if schluessel in text_lower:
            return kategorie
    return "sonstiges"


def _event_aus_teaser(teaser_el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem Teaser-Element der VisitDüsseldorf-Seite.

    Erwartet Elemente mit Datum, Titel, Ort und Link.

    Args:
        teaser_el: BeautifulSoup-Element des Event-Teasers
        heute:     Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None wenn Pflichtfelder fehlen / Event vergangen
    """
    try:
        # --- Link ---
        anker = teaser_el if teaser_el.name == "a" else teaser_el.find("a", href=True)
        href = anker.get("href", "") if anker else ""
        quelle_url = urljoin(BASE_URL, href) if href else LISTE_URL

        # --- Titel ---
        for sel in [".tb-teaser__title", "h2", "h3", "h4", ".card__title", ".event-title"]:
            el = teaser_el.select_one(sel)
            if el:
                titel = el.get_text(strip=True)
                if titel:
                    break
        else:
            return None

        # --- Datum: itemprop="startDate" oder text ---
        datum = None
        datum_el = teaser_el.select_one("[itemprop='startDate']")
        if datum_el:
            datum = _datum_parsen(datum_el.get("content", "")) or _datum_parsen(datum_el.get_text(strip=True))

        if not datum:
            volltext = teaser_el.get_text(separator=" ", strip=True)
            datum = _datum_parsen(volltext)

        if not datum:
            return None
        if date.fromisoformat(datum) < heute:
            return None

        # --- Uhrzeit ---
        uhrzeit = _uhrzeit_parsen(teaser_el.get_text(separator=" ", strip=True))

        # --- Ort ---
        ort_els = teaser_el.select(".tb-teaser__location, .card__location, .event-location")
        if len(ort_els) >= 2:
            ort = ort_els[1].get_text(strip=True)
        elif len(ort_els) == 1:
            ort = ort_els[0].get_text(strip=True)
        else:
            ort = "Düsseldorf"
        if not ort:
            ort = "Düsseldorf"

        # --- Kategorie ---
        kat_el = teaser_el.select_one(".tb-teaser__topline-category, .card__category, .event-category")
        kategorie = _kategorie_aus_text(kat_el.get_text(strip=True) if kat_el else "")

        # --- Bild ---
        bild_el = teaser_el.select_one("img")
        bild_url = None
        if bild_el:
            bild_url = bild_el.get("data-src") or bild_el.get("src") or bild_el.get("data-lazy-src")
            if bild_url and not bild_url.startswith("http"):
                bild_url = urljoin(BASE_URL, bild_url)

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
        logger.error("Fehler beim Parsen eines VisitDüsseldorf-Teasers: %s", str(fehler))
        return None


def scrape() -> list[dict]:
    """
    Scrapt Events von VisitDüsseldorf mittels Playwright (JavaScript-Rendering).

    Die Seite ist eine Angular-SPA und liefert Events erst nach dem JS-Rendering.
    Playwright wartet bis die Event-Liste sichtbar ist.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    events: list[dict] = []
    heute = date.today()
    logger.info("Starte Scraper: %s (Playwright)", QUELLE_NAME)

    try:
        time.sleep(2)  # Rate Limiting

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            seite = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )

            try:
                seite.goto(LISTE_URL, timeout=30000, wait_until="domcontentloaded")

                # Warten bis Event-Container geladen ist
                try:
                    seite.wait_for_selector(
                        "a.tb-teaser, article, .event-card, .veranstaltung",
                        timeout=15000,
                    )
                except PlaywrightTimeout:
                    logger.warning(
                        "Timeout beim Warten auf Event-Container auf %s – "
                        "Seitenstruktur möglicherweise geändert.",
                        LISTE_URL,
                    )

                html = seite.content()

            except PlaywrightTimeout:
                logger.error("Timeout beim Laden von %s", LISTE_URL)
                browser.close()
                return []
            except Exception as fehler:
                logger.error("Playwright-Fehler beim Laden von %s: %s", LISTE_URL, str(fehler))
                browser.close()
                return []

            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        # Event-Teaser finden
        teaser_els = (
            soup.select("a.tb-teaser") or
            soup.select("article.event-card") or
            soup.select("[class*='event'][class*='card']") or
            soup.select("[class*='veranstaltung']")
        )

        if not teaser_els:
            logger.warning(
                "Keine Event-Teaser auf %s gefunden – "
                "Seitenstruktur hat sich möglicherweise geändert.",
                LISTE_URL,
            )
            return []

        logger.info("%d potenzielle Event-Teaser gefunden", len(teaser_els))

        gesehene_urls: set[str] = set()
        for el in teaser_els:
            event = _event_aus_teaser(el, heute)
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

    if not events:
        logger.warning(
            "Scraper %s: 0 Events gefunden – "
            "Seitenstruktur hat sich möglicherweise geändert.",
            QUELLE_NAME,
        )

    # 14-Tage-Fenster: Events weiter als SCRAPER_VORSCHAU_TAGE in der Zukunft ausfiltern
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
