"""
fortuna.py – DiesDasDüsseldorf
Playwright-Scraper für Fortuna Düsseldorf Heimspiele.

Scrapt nur Heimspiele aus dem offiziellen Spielplan.

Strategie:
1. Primär: JSON-LD structured data (schema.org/SportsEvent)
2. Fallback: HTML-Parsing der Spielplan-Tabelle

URL: https://www.fortuna-duesseldorf.de/spielplan
Adresse: Arena-Straße 1, 40474 Düsseldorf
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

LISTE_URL = "https://www.fortuna-duesseldorf.de/spielplan"
BASE_URL = "https://www.fortuna-duesseldorf.de"
QUELLE_NAME = "Fortuna Düsseldorf"
ORT_STANDARD = "Merkur Spiel-Arena Düsseldorf"
ADRESSE_STANDARD = "Arena-Straße 1, 40474 Düsseldorf"
KATEGORIE = "sport"
PREIS_FALLBACK = "ab 15€"

# Heimspiel-Identifier – Fortuna spielt immer im eigenen Stadion
HEIMSPIEL_BEGRIFFE = [
    "merkur", "arena", "fortuna", "heimspiel", "home",
    "düsseldorf", "duesseldorf", "f95",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _ist_heimspiel(ort_text: str) -> bool:
    """
    Prüft ob ein Spiel ein Heimspiel ist anhand des Ort-Texts.

    Args:
        ort_text: Ortsbezeichnung aus der Webseite

    Returns:
        True wenn Heimspiel, False wenn Auswärtsspiel
    """
    if not ort_text:
        return True  # Im Zweifel annehmen (wird auf Fortuna-Seite gelistet)
    ort_klein = ort_text.lower()
    return any(begriff in ort_klein for begriff in HEIMSPIEL_BEGRIFFE)


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
    Extrahiert Heimspiele aus JSON-LD structured data.

    Args:
        html: HTML-Quelltext der Seite
        heute: Aktuelles Datum
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Event-Dicts (nur Heimspiele)
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
            if eintrag.get("@type") not in ("Event", "SportsEvent", "SoccerGame"):
                continue

            titel = eintrag.get("name", "").strip()
            if not titel:
                continue

            # Heimspiel-Prüfung über Ortsangabe
            ort_roh = eintrag.get("location")
            ort_name = ""
            adresse = ADRESSE_STANDARD
            if isinstance(ort_roh, dict):
                ort_name = ort_roh.get("name", "")
                adresse_roh = ort_roh.get("address")
                if isinstance(adresse_roh, dict):
                    strasse = adresse_roh.get("streetAddress", "")
                    plz = adresse_roh.get("postalCode", "")
                    stadt = adresse_roh.get("addressLocality", "Düsseldorf")
                    adresse = f"{strasse}, {plz} {stadt}".strip(", ") or ADRESSE_STANDARD
                elif isinstance(adresse_roh, str):
                    adresse = adresse_roh
            elif isinstance(ort_roh, str):
                ort_name = ort_roh

            if ort_name and not _ist_heimspiel(ort_name):
                logger.debug("Auswärtsspiel übersprungen: %s (Ort: %s)", titel, ort_name)
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

            # Preis aus Angeboten
            preis = PREIS_FALLBACK
            angebote = eintrag.get("offers", [])
            if isinstance(angebote, dict):
                angebote = [angebote]
            if angebote:
                preise = [str(a.get("price", "")) for a in angebote if a.get("price")]
                if preise:
                    preis = f"ab {preise[0]}€"

            bild_roh = eintrag.get("image")
            if isinstance(bild_roh, list) and bild_roh:
                bild_roh = bild_roh[0]
            if isinstance(bild_roh, dict):
                bild_url = bild_roh.get("url") or bild_roh.get("contentUrl")
            elif isinstance(bild_roh, str) and bild_roh.startswith("http"):
                bild_url = bild_roh
            else:
                bild_url = None

            schluessel = f"{titel}_{datum}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ORT_STANDARD,
                "adresse": adresse,
                "kategorie": KATEGORIE,
                "beschreibung": beschreibung,
                "preis": preis,
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
    Fallback: HTML-Parsing des Spielplans.

    Args:
        html: HTML-Quelltext der Seite
        heute: Aktuelles Datum
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Event-Dicts (nur Heimspiele)
    """
    from bs4 import BeautifulSoup

    events = []
    gesehene_schluessel: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")

    # Typische Selektoren für Spielplan-Seiten
    selektoren = [
        ".match", ".spiel", ".game", ".fixture",
        "article[class*='match']", "div[class*='match']",
        "li[class*='match']", "tr[class*='match']",
        ".schedule-item", ".spielplan-item",
    ]

    karten = []
    for selektor in selektoren:
        karten = soup.select(selektor)
        if len(karten) > 1:
            logger.debug("HTML-Fallback: %d Karten mit Selektor '%s'", len(karten), selektor)
            break

    for karte in karten:
        try:
            # Heimspiel-Prüfung: Suche nach "Heim" oder "Home" im Karten-Text
            karte_text = karte.get_text(separator=" ", strip=True).lower()
            if "auswärts" in karte_text or "away" in karte_text:
                continue

            titel_el = karte.find(["h2", "h3", "h4", "strong", ".match-title", ".spiel-title"])
            if not titel_el:
                continue
            titel = titel_el.get_text(strip=True)
            if not titel or len(titel) < 3:
                continue

            datum_el = karte.find("time") or karte.find(class_=re.compile(r"date|datum|zeit|uhrzeit", re.I))
            if not datum_el:
                continue
            datum_text = datum_el.get("datetime") or datum_el.get_text(strip=True)
            datum = datum_parsen(datum_text)
            if not datum:
                continue
            datum_obj = date.fromisoformat(datum)
            if datum_obj < heute or datum_obj > enddatum:
                continue

            uhrzeit = uhrzeit_parsen(datum_text)

            link_el = karte.find("a", href=True)
            quelle_url = urljoin(BASE_URL, link_el["href"]) if link_el else LISTE_URL

            bild_el = karte.find("img")
            bild_url = None
            if bild_el:
                bild_url = bild_el.get("data-src") or bild_el.get("src")
                if bild_url and bild_url.startswith("/"):
                    bild_url = urljoin(BASE_URL, bild_url)
                if bild_url and not bild_url.startswith("http"):
                    bild_url = None

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
                "beschreibung": None,
                "preis": PREIS_FALLBACK,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "bild_generiert": False,
                "post_typ": "feed",
                "instagram_caption": None,
                "status": "neu",
            })

        except Exception as fehler:
            logger.error("Fehler beim Parsen einer Spielkarte: %s", str(fehler))
            continue

    return events


async def scrape() -> list[dict]:
    """
    Scrapt Fortuna Düsseldorf Heimspiele vom offiziellen Spielplan.

    Strategie:
    1. JSON-LD structured data
    2. HTML-Fallback

    Returns:
        Liste von Event-Dicts (nur Heimspiele) im DiesDasDüsseldorf Standard-Format.
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
    logger.info("JSON-LD: %d Heimspiele gefunden", len(events))

    if not events:
        logger.warning("JSON-LD leer – versuche HTML-Fallback")
        events = _events_aus_html(html, heute, enddatum)
        logger.info("HTML-Fallback: %d Heimspiele gefunden", len(events))

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
