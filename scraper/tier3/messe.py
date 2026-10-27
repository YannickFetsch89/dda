"""
messe.py – DiesDasDüsseldorf
Playwright-Scraper für Messe Düsseldorf Veranstaltungen.

Scrapt Leitmessen und Events vom offiziellen Veranstaltungsportal der Messe Düsseldorf.

Strategie:
1. Primär: JSON-LD structured data (schema.org/Event)
2. Fallback: HTML-Parsing der Veranstaltungsliste

URL: https://www.messe-duesseldorf.de/de/messen_und_events/messen_national_und_international
Adresse: Stockumer Kirchstraße 61, 40474 Düsseldorf
Erstellt: 2026-03-06
"""
import asyncio
import json
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from playwright.async_api import async_playwright

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen, uhrzeit_parsen

logger = logging.getLogger(__name__)

LISTE_URL = "https://www.messe-duesseldorf.de/de/messen_und_events/messen_national_und_international"
BASE_URL = "https://www.messe-duesseldorf.de"
QUELLE_NAME = "Messe Düsseldorf"
ORT_STANDARD = "Messe Düsseldorf"
ADRESSE_STANDARD = "Stockumer Kirchstraße 61, 40474 Düsseldorf"
KATEGORIE = "community"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _beschreibung_kuerzen(text: str) -> str:
    """
    Kürzt eine Beschreibung auf maximal 300 Zeichen.

    Args:
        text: Roher Beschreibungstext

    Returns:
        Beschreibung mit maximal 300 Zeichen
    """
    if not text:
        return ""
    bereinigt = " ".join(text.split())
    return bereinigt[:300]


def _events_aus_json_ld(html: str, heute: date, enddatum: date) -> list[dict]:
    """
    Extrahiert Messe-Events aus JSON-LD structured data.

    Args:
        html: HTML-Quelltext der Seite
        heute: Aktuelles Datum
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Event-Dicts
    """
    from bs4 import BeautifulSoup

    events = []
    gesehene_schluessel: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            daten = json.loads(script.string or "{}")
        except (json.JSONDecodeError, AttributeError):
            continue

        eintraege = daten if isinstance(daten, list) else [daten]
        for eintrag in eintraege:
            if not isinstance(eintrag, dict):
                continue
            if eintrag.get("@type") not in ("Event", "ExhibitionEvent", "BusinessEvent", "TradeShow"):
                continue

            titel = eintrag.get("name", "").strip()
            if not titel:
                continue

            datum_roh = eintrag.get("startDate") or eintrag.get("startDateTime")
            datum = datum_parsen(str(datum_roh)) if datum_roh else None
            if not datum:
                continue
            datum_obj = date.fromisoformat(datum)
            if datum_obj < heute or datum_obj > enddatum:
                continue

            uhrzeit = uhrzeit_parsen(str(datum_roh))
            url_roh = eintrag.get("url")
            quelle_url = urljoin(BASE_URL, str(url_roh)) if url_roh else LISTE_URL

            beschreibung_roh = eintrag.get("description")
            beschreibung = _beschreibung_kuerzen(str(beschreibung_roh)) if beschreibung_roh else None

            bild_roh = eintrag.get("image")
            if isinstance(bild_roh, list) and bild_roh:
                bild_roh = bild_roh[0]
            if isinstance(bild_roh, dict):
                bild_url = bild_roh.get("url") or bild_roh.get("contentUrl")
            elif isinstance(bild_roh, str) and bild_roh.startswith("http"):
                bild_url = bild_roh
            else:
                bild_url = None

            # Enddatum aus JSON-LD extrahieren (Messen laufen oft mehrere Tage)
            ende_roh = eintrag.get("endDate")
            datum_bis = datum_parsen(str(ende_roh)) if ende_roh else None

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
                "kategorie": KATEGORIE,
                "beschreibung": beschreibung,
                "preis": None,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "bild_generiert": False,
                "post_typ": "feed",
                "instagram_caption": None,
                "status": "neu",
            })

    return events


def _events_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """
    HTML-Parsing der Messe-Veranstaltungsliste.

    Struktur (Stand 2026-10): div.dim-list-item_head mit Kind-Divs
    .title (span.overflow--ellipsis), .date, .city
    """
    from bs4 import BeautifulSoup

    events = []
    gesehene_schluessel: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")

    datum_bereich = re.compile(
        r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s*-\s*(\d{1,2})\.(\d{1,2})\.(\d{4})"
    )

    koepfe = soup.find_all("div", class_="dim-list-item_head")
    logger.debug("Messe HTML: %d dim-list-item_head Einträge", len(koepfe))

    for kopf in koepfe:
        titel_div = kopf.select_one("div.title")
        datum_div = kopf.select_one("div.date")
        stadt_div = kopf.select_one("div.city")

        if not titel_div or not datum_div:
            continue

        span = titel_div.find("span", class_="overflow--ellipsis")
        titel = (span.get_text(strip=True) if span else titel_div.get_text(strip=True))
        if not titel or len(titel) < 2:
            continue

        datum_text = datum_div.get_text(strip=True)
        treffer = datum_bereich.search(datum_text)
        if not treffer:
            continue

        try:
            start_datum = date(
                int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1))
            )
            ende_datum = date(
                int(treffer.group(6)), int(treffer.group(5)), int(treffer.group(4))
            )
        except ValueError:
            continue

        if ende_datum < heute or start_datum > enddatum:
            continue

        stadt = stadt_div.get_text(strip=True) if stadt_div else "Düsseldorf"
        if "düsseldorf" not in stadt.lower():
            continue

        bild_el = titel_div.find("img")
        bild_url = None
        if bild_el:
            bild_src = bild_el.get("src")
            if bild_src:
                bild_url = bild_src if bild_src.startswith("http") else urljoin(BASE_URL, bild_src)

        schluessel = f"{titel}_{start_datum.isoformat()}"
        if schluessel in gesehene_schluessel:
            continue
        gesehene_schluessel.add(schluessel)

        events.append({
            "titel": titel,
            "datum": start_datum.isoformat(),
            "uhrzeit": None,
            "ort": ORT_STANDARD,
            "adresse": ADRESSE_STANDARD,
            "kategorie": KATEGORIE,
            "beschreibung": f"{titel}, {datum_text}, Messe Düsseldorf"[:300],
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": LISTE_URL,
            "bild_url": bild_url,
            "bild_generiert": False,
            "post_typ": "feed",
            "instagram_caption": None,
            "status": "neu",
        })

    return events


async def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen der Messe Düsseldorf.

    Strategie:
    1. JSON-LD structured data
    2. HTML-Fallback

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    html = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers({"User-Agent": USER_AGENT})
            try:
                await page.goto(LISTE_URL, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                html = await page.content()
            except Exception as fehler:
                logger.error("Playwright Fehler beim Laden von %s: %s", LISTE_URL, str(fehler))
            finally:
                await browser.close()
    except Exception as fehler:
        logger.error("Scraper %s: Playwright konnte nicht gestartet werden: %s", QUELLE_NAME, str(fehler))

    if not html:
        logger.warning("Scraper %s: Kein HTML geladen – leere Liste wird zurückgegeben", QUELLE_NAME)
        return []

    events = _events_aus_json_ld(html, heute, enddatum)
    logger.info("JSON-LD: %d Events gefunden", len(events))

    if not events:
        logger.warning("JSON-LD leer – versuche HTML-Fallback")
        events = _events_aus_html(html, heute, enddatum)
        logger.info("HTML-Fallback: %d Events gefunden", len(events))

    logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json as _json
    ergebnisse = asyncio.run(scrape())
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
