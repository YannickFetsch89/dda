"""
ihk.py – DiesDasDüsseldorf
Playwright-Scraper für IHK Düsseldorf Veranstaltungen.

Scrapt Business-Events, Seminare und Netzwerkveranstaltungen der
IHK Düsseldorf (Industrie- und Handelskammer).

Strategie:
1. Playwright rendert die Veranstaltungssuche
2. HTML-Parsing der .result .event-teaser Elemente

URL: https://www.ihk.de/duesseldorf/system/veranstaltungssuche/suche-tibros/6138840
Adresse: Ernst-Schneider-Platz 1, 40212 Düsseldorf
Erstellt: 2026-03-06
"""
import asyncio
import logging
import re
from datetime import date, timedelta
from urllib.parse import urljoin

from playwright.async_api import async_playwright

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen, uhrzeit_parsen

logger = logging.getLogger(__name__)

LISTE_URL = "https://www.ihk.de/duesseldorf/system/veranstaltungssuche/suche-tibros/6138840"
BASE_URL = "https://www.ihk.de"
QUELLE_NAME = "IHK Düsseldorf"
ORT_STANDARD = "IHK Düsseldorf"
ADRESSE_STANDARD = "Ernst-Schneider-Platz 1, 40212 Düsseldorf"
KATEGORIE = "community"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _beschreibung_kuerzen(text: str) -> str:
    """
    Kürzt eine Beschreibung auf maximal 300 Zeichen.
    """
    if not text:
        return ""
    bereinigt = " ".join(text.split())
    return bereinigt[:300]


def _events_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """
    Parst IHK-Veranstaltungsergebnisse aus gerendertem HTML.

    Struktur: .result > .event-teaser mit .ev-title, .date, .time, .location, .price
    """
    from bs4 import BeautifulSoup

    events = []
    gesehene_schluessel: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")

    karten = soup.select(".result .event-teaser")
    if not karten:
        karten = soup.select(".event-teaser")
    logger.info("IHK: %d Event-Teaser gefunden", len(karten))

    for karte in karten:
        try:
            titel_el = karte.select_one("p.ev-title")
            if not titel_el:
                continue
            titel = titel_el.get_text(strip=True)
            if not titel or len(titel) < 3:
                continue

            datum_el = karte.select_one("div.date")
            if not datum_el:
                continue
            datum_text = datum_el.get_text(strip=True)
            datum = datum_parsen(datum_text)
            if not datum:
                continue

            datum_obj = date.fromisoformat(datum)
            if datum_obj < heute or datum_obj > enddatum:
                continue

            zeit_el = karte.select_one("div.time")
            uhrzeit = None
            if zeit_el:
                uhrzeit = uhrzeit_parsen(zeit_el.get_text(strip=True))

            ort = ORT_STANDARD
            adresse = ADRESSE_STANDARD
            ort_el = karte.select_one("div.location")
            if ort_el:
                ort_text = ort_el.get_text(strip=True)
                if ort_text:
                    if "online" in ort_text.lower():
                        ort = "Online (IHK Düsseldorf)"
                        adresse = None
                    elif ort_text:
                        adresse = ort_text + " Düsseldorf" if "düsseldorf" not in ort_text.lower() else ort_text

            preis = None
            preis_el = karte.select_one("div.price")
            if preis_el:
                preis_text = preis_el.get_text(strip=True)
                if preis_text:
                    if preis_text.lower() in ("kostenfrei", "kostenlos", "0", "0,00"):
                        preis = "kostenlos"
                    else:
                        preis_text = preis_text.replace(".", "").replace(",", ".")
                        try:
                            betrag = float(preis_text)
                            preis = f"{betrag:.0f}€"
                        except ValueError:
                            preis = preis_text

            link_el = karte.select_one("a.teaser--link")
            quelle_url = LISTE_URL
            if link_el:
                href = link_el.get("href", "")
                if href:
                    quelle_url = urljoin(BASE_URL, href)

            schluessel = f"{titel}_{datum}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ort,
                "adresse": adresse,
                "kategorie": KATEGORIE,
                "beschreibung": None,
                "preis": preis,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": None,
                "bild_generiert": False,
                "post_typ": "feed",
                "instagram_caption": None,
                "instagram_location_id": None,
                "status": "neu",
            })

        except Exception as fehler:
            logger.error("Fehler beim Parsen einer IHK-Veranstaltung: %s", str(fehler))
            continue

    return events


async def scrape() -> list[dict]:
    """
    Scrapt Business-Events und Veranstaltungen der IHK Düsseldorf.
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
                await asyncio.sleep(3)
                html = await page.content()
            except Exception as fehler:
                logger.error("Playwright Fehler beim Laden von %s: %s", LISTE_URL, str(fehler))
            finally:
                await browser.close()
    except Exception as fehler:
        logger.error("Scraper %s: Playwright konnte nicht gestartet werden: %s", QUELLE_NAME, str(fehler))

    if not html:
        logger.warning("Scraper %s: Kein HTML geladen", QUELLE_NAME)
        return []

    events = _events_aus_html(html, heute, enddatum)
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
