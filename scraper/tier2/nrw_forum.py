"""
nrw_forum.py – DiesDasDüsseldorf
Scraper für das NRW-Forum Düsseldorf: Ausstellungen und Veranstaltungen.

Die Website nutzt Lit Web Components mit Shadow DOM, daher werden
Events direkt über Playwright's JavaScript-Evaluation extrahiert.

URL: https://www.nrw-forum.de/veranstaltungen
Adresse: Ehrenhof 2, 40479 Düsseldorf
Erstellt: 2026-03-05
"""
import logging
import re
from datetime import date, timedelta
from typing import Optional

from config import SCRAPER_VORSCHAU_TAGE

logger = logging.getLogger(__name__)

BASE_URL = "https://www.nrw-forum.de"
LISTE_URL = "https://www.nrw-forum.de/veranstaltungen"
QUELLE_NAME = "NRW-Forum Düsseldorf"
ORT_STANDARD = "NRW-Forum Düsseldorf"
ADRESSE_STANDARD = "Ehrenhof 2, 40479 Düsseldorf"
KATEGORIE_STANDARD = "kultur"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

MONAT_MAP: dict[str, int] = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}

KATEGORIE_MAPPING = {
    "konzert": "musik", "musik": "musik", "live": "musik",
    "party": "nightlife", "club": "nightlife",
    "theater": "kultur", "ausstellung": "kultur", "kunst": "kultur",
    "kino": "kultur", "film": "kultur", "digital": "kultur",
    "workshop": "community", "vortrag": "community", "talk": "community",
    "festival": "musik",
    "kinder": "family", "familie": "family", "jugendliche": "family",
    "führung": "kultur",
}


def _datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt NRW-Forum-Datumsformat '27. Oktober 2026' in ISO 8601 um.
    """
    if not text:
        return None
    bereinigt = text.strip().lower()
    treffer = re.search(r"(\d{1,2})\.\s*([a-zäöüß]+)\s*(\d{4})", bereinigt)
    if treffer:
        tag = int(treffer.group(1))
        monat = MONAT_MAP.get(treffer.group(2))
        jahr = int(treffer.group(3))
        if monat:
            try:
                return date(jahr, monat, tag).isoformat()
            except ValueError:
                return None
    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """
    Extrahiert Uhrzeit aus Text wie '10:00 Uhr'.
    """
    if not text:
        return None
    treffer = re.search(r"(\d{1,2}):(\d{2})", text)
    if treffer:
        stunde, minute = int(treffer.group(1)), int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"
    return None


def _kategorie_erkennen(text: str) -> str:
    """
    Mappt Texte auf DiesDasDüsseldorf-Kategorien.
    """
    if not text:
        return KATEGORIE_STANDARD
    text_klein = text.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if schluessel in text_klein:
            return kategorie
    return KATEGORIE_STANDARD


def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen des NRW-Forums Düsseldorf.

    Die Website nutzt Lit Web Components mit Shadow DOM.
    Events werden über JavaScript-Evaluation direkt aus dem Shadow DOM
    des <nrwf-dates>-Elements extrahiert.
    """
    import time
    from playwright.sync_api import sync_playwright

    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    rohdaten = []
    try:
        time.sleep(2)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            seite = browser.new_page(user_agent=USER_AGENT)
            try:
                seite.goto(LISTE_URL, timeout=30000, wait_until="networkidle")
                seite.wait_for_timeout(3000)

                rohdaten = seite.evaluate("""() => {
                    let host = document.querySelector('nrwf-dates');
                    if (!host || !host.shadowRoot) return [];

                    let items = host.shadowRoot.querySelectorAll('.list-item');
                    return Array.from(items).map(el => {
                        let btn = el.querySelector('sl-button[href]');
                        return {
                            date: el.querySelector('.when div')?.textContent?.trim() || '',
                            time: el.querySelector('.when small:last-child')?.textContent?.trim() || '',
                            title: el.querySelector('.title-block h2')?.textContent?.trim() || '',
                            subtitle: el.querySelector('.title-block small')?.textContent?.trim() || '',
                            venue: el.querySelector('.venue-block small')?.textContent?.trim() || '',
                            img: el.querySelector('.thumb img')?.src || null,
                            href: btn ? btn.getAttribute('href') : null,
                        };
                    });
                }""")

            except Exception as fehler:
                logger.error("Playwright Fehler: %s", fehler)
            finally:
                browser.close()
    except Exception as fehler:
        logger.error("Playwright konnte nicht gestartet werden: %s", fehler)
        return []

    if not rohdaten:
        logger.warning("Keine Events im Shadow DOM gefunden")
        return []

    logger.info("NRW-Forum: %d Roheinträge aus Shadow DOM", len(rohdaten))

    events = []
    gesehene_schluessel: set[str] = set()

    for eintrag in rohdaten:
        try:
            titel = eintrag.get("title", "").strip()
            if not titel or len(titel) < 3:
                continue

            datum = _datum_parsen(eintrag.get("date", ""))
            if not datum:
                continue

            datum_obj = date.fromisoformat(datum)
            if datum_obj < heute or datum_obj > enddatum:
                continue

            uhrzeit = _uhrzeit_parsen(eintrag.get("time", ""))

            href = eintrag.get("href")
            quelle_url = (BASE_URL + href) if href else LISTE_URL

            subtitle = eintrag.get("subtitle", "").strip()
            beschreibung = subtitle[:300] if subtitle else None

            venue = eintrag.get("venue", "").strip()
            ort = venue if venue else ORT_STANDARD

            bild_url = eintrag.get("img")
            if bild_url and not bild_url.startswith("http"):
                bild_url = None

            kategorie = _kategorie_erkennen(titel + " " + (subtitle or ""))

            schluessel = f"{titel}_{datum}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ort,
                "adresse": ADRESSE_STANDARD,
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
            })

        except Exception as fehler:
            logger.error("Fehler beim Parsen: %s", str(fehler))
            continue

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
    for e in ergebnisse[:3]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
