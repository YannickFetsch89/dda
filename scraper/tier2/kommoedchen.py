"""
kommoedchen.py – DiesDasDüsseldorf
Scraper für das Kom(m)ödchen Düsseldorf.
URL: https://www.kommoedchen.de

Das Kom(m)ödchen ist eine der renommiertesten Kleinkunstbühnen Deutschlands,
gegründet 1947. Kabarett, politische Satire, Stand-up-Comedy.

Erstellt: 2026-04-02
"""
import logging
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen, uhrzeit_parsen
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://www.kommoedchen.de"
SPIELPLAN_URL = "https://www.kommoedchen.de/spielplan/"
QUELLE_NAME = "Kom(m)ödchen Düsseldorf"
ORT_STANDARD = "Kom(m)ödchen Düsseldorf"
ADRESSE_STANDARD = "Kay- und Lore-Lorentz-Platz 1, 40213 Düsseldorf"
KATEGORIE_STANDARD = "kultur"

# Fallback-URL wenn /spielplan nicht erreichbar
FALLBACK_URL = BASE_URL


def _event_aus_element(el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem Kom(m)ödchen Spielplan-Element.

    Args:
        el: BeautifulSoup-Element
        heute: Heutiges Datum für Filterung

    Returns:
        Event-Dict oder None
    """
    try:
        # Titel
        titel_el = (
            el.find("h2")
            or el.find("h3")
            or el.find("h4")
            or el.find(class_=lambda c: c and "title" in str(c).lower())
            or el.find(class_=lambda c: c and "stueck" in str(c).lower())
        )
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel:
            return None

        # URL
        link_el = el.find("a", href=True)
        if link_el:
            href = link_el["href"]
            quelle_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
        else:
            quelle_url = SPIELPLAN_URL

        # Datum und Uhrzeit
        datum = None
        uhrzeit = None

        zeit_el = el.find("time")
        if zeit_el:
            datetime_attr = zeit_el.get("datetime", "")
            datum = datum_parsen(datetime_attr) or datum_parsen(zeit_el.get_text(strip=True))
            uhrzeit = uhrzeit_parsen(datetime_attr) or uhrzeit_parsen(zeit_el.get_text(strip=True))

        if not datum:
            for text_el in el.find_all(True):
                text = text_el.get_text(strip=True)
                datum_kandidat = datum_parsen(text)
                if datum_kandidat:
                    datum = datum_kandidat
                    if not uhrzeit:
                        uhrzeit = uhrzeit_parsen(text)
                    break

        if not datum:
            return None

        if date.fromisoformat(datum) < heute:
            return None

        # Preis
        preis = None
        for text_el in el.find_all(True):
            text = text_el.get_text(strip=True)
            if any(p in text.lower() for p in ["€", "eintritt", "preis"]):
                if len(text) < 60:
                    preis = text
                    break

        # Beschreibung
        beschreibung = None
        beschr_el = el.find("p") or el.find(class_=lambda c: c and "teaser" in str(c).lower())
        if beschr_el:
            beschreibung = beschr_el.get_text(strip=True)[:300] or None

        # Bild
        bild_url = None
        bild_el = el.find("img")
        if bild_el:
            bild_url = (
                bild_el.get("data-src")
                or bild_el.get("data-original")
                or bild_el.get("src")
            )
            if bild_url and not bild_url.startswith("http"):
                bild_url = urljoin(BASE_URL, bild_url)

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT_STANDARD,
            "adresse": ADRESSE_STANDARD,
            "kategorie": KATEGORIE_STANDARD,
            "beschreibung": beschreibung,
            "preis": preis,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error("Fehler beim Parsen eines Kom(m)ödchen-Events: %s", str(fehler))
        return None


def _seite_mit_playwright(url: str) -> Optional[str]:
    """
    Lädt eine Seite mit Playwright bei Sucuri/WAF Bot-Schutz.
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            seite = browser.new_page()
            seite.goto(url, wait_until="domcontentloaded", timeout=30000)
            seite.wait_for_timeout(3000)
            html = seite.content()
            browser.close()
            return html
    except Exception as fehler:
        logger.warning("Playwright-Fallback fehlgeschlagen: %s", fehler)
        return None


def scrape() -> list[dict]:
    """
    Scrapt Events vom Kom(m)ödchen Düsseldorf.

    Renommierteste Kleinkunstbühne Deutschlands seit 1947.
    Kabarett, politische Satire, Stand-up-Comedy.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = seite_abrufen(SPIELPLAN_URL, logger)
        if html is None:
            logger.warning("httpx fehlgeschlagen – versuche Playwright")
            html = _seite_mit_playwright(SPIELPLAN_URL)
        if html is None:
            logger.warning("Kom(m)ödchen nicht erreichbar")
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Spielplan-Kalender: div.day-event-wrapper mit data-date Attribut
        event_wrapper = soup.find_all("div", class_="day-event-wrapper")
        logger.info("Kom(m)ödchen: %d Kalender-Einträge gefunden", len(event_wrapper))

        gesehene_schluessel: set[str] = set()

        for wrapper in event_wrapper:
            datum_raw = wrapper.get("data-date")
            if not datum_raw:
                continue
            try:
                datum_obj = date.fromisoformat(datum_raw)
            except ValueError:
                continue
            if datum_obj < heute:
                continue

            datum = datum_obj.isoformat()

            item = wrapper.find("div", class_="day-event-item")
            if not item:
                continue

            # Uhrzeit
            uhrzeit = None
            zeit_el = item.find("span", class_="date-time")
            if zeit_el:
                uhrzeit = uhrzeit_parsen(zeit_el.get_text(strip=True))

            # Titel und URL
            titel_div = item.find("div", class_="title")
            if not titel_div:
                continue
            titel = titel_div.get_text(strip=True)
            if not titel:
                continue

            untertitel_div = item.find("div", class_="subtitle")
            if untertitel_div:
                untertitel = untertitel_div.get_text(strip=True)
                if untertitel:
                    titel = f"{untertitel}: {titel}"

            link_el = item.find("a", href=lambda h: h and "/spielplan/" in h)
            quelle_url = link_el["href"] if link_el else SPIELPLAN_URL
            if not quelle_url.startswith("http"):
                quelle_url = urljoin(BASE_URL, quelle_url)

            # Bild
            bild_url = None
            bild_el = item.find("img")
            if bild_el:
                bild_url = bild_el.get("src") or bild_el.get("data-src")
                if bild_url and not bild_url.startswith("http"):
                    bild_url = urljoin(BASE_URL, bild_url)

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

    except Exception as fehler:
        logger.error("Fehler beim Scrapen: %s", str(fehler))

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
