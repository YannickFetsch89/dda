"""
pitcher.py – DiesDasDüsseldorf
Scraper für den Pitcher Rock HQ Düsseldorf.

Strategie:
1. Primär: Playwright-Scraper für pitcher.de/programm (JavaScript-gerenderte Seite)
2. Fallback: JSON-LD structured data aus dem HTML
3. Fallback: HTML-Parsing der Event-Liste

Hinweis: Die Website (pitcher.de) war zum Entwicklungszeitpunkt
(2026-03-05) nicht erreichbar (503 TLS-Fehler). Der Scraper ist
implementiert und wird aktiv, sobald die Website wieder verfügbar ist.

Der Pitcher Rock HQ ist ein Livemusik-Club in Düsseldorf mit Fokus
auf Rock, Metal, Punk und Alternative sowie DJ-Abende.

URL: https://www.pitcher.de
Adresse: Himmelgeister Str. 130, 40225 Düsseldorf
Erstellt: 2026-03-05
"""
import json
import logging
import re
import time
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://www.pitcher.de"
LISTE_URL = "https://www.pitcher.de/programm"
QUELLE_NAME = "Pitcher Rock HQ"
ORT_STANDARD = "Pitcher Rock HQ"
ADRESSE_STANDARD = "Himmelgeister Str. 130, 40225 Düsseldorf"

MONAT_MAP: dict[str, int] = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}
MONAT_KURZ_MAP: dict[str, int] = {
    "jan": 1, "feb": 2, "mär": 3, "mar": 3, "apr": 4,
    "mai": 5, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}

KATEGORIE_MAPPING: dict[str, str] = {
    "rock": "musik",
    "metal": "musik",
    "punk": "musik",
    "alternative": "musik",
    "indie": "musik",
    "konzert": "musik",
    "live": "musik",
    "band": "musik",
    "acoustic": "musik",
    "open mic": "musik",
    "party": "nightlife",
    "dj": "nightlife",
    "club": "nightlife",
    "80er": "nightlife",
    "90er": "nightlife",
    "karaoke": "nightlife",
    "quiz": "community",
    "comedy": "kultur",
}


def _datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt verschiedene Datumsformate in ISO 8601 (YYYY-MM-DD) um.

    Args:
        text: Roher Datumstext

    Returns:
        ISO-Datum oder None
    """
    if not text:
        return None
    heute = date.today()
    bereinigt = text.strip()
    bereinigt_klein = bereinigt.lower()

    try:
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(int(treffer.group(1)), int(treffer.group(2)), int(treffer.group(3))).isoformat()

        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1))).isoformat()

        treffer = re.search(r"(\d{1,2})\.?\s+([a-zäöüß]+)\s+(\d{4})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat = MONAT_MAP.get(treffer.group(2))
            jahr = int(treffer.group(3))
            if monat:
                return date(jahr, monat, tag).isoformat()

        treffer = re.search(r"(\d{1,2})\.\s*([a-zäöü]{3})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat = MONAT_KURZ_MAP.get(treffer.group(2)[:3])
            if monat:
                kandidat = date(heute.year, monat, tag)
                if kandidat < heute - timedelta(days=1):
                    kandidat = date(heute.year + 1, monat, tag)
                return kandidat.isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning("Datum konnte nicht geparst werden: '%s' – %s", text, fehler)
    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """
    Extrahiert Uhrzeit im Format HH:MM aus Text.

    Args:
        text: Roher Text

    Returns:
        Uhrzeit als HH:MM oder None
    """
    if not text:
        return None
    treffer = re.search(r"\b(\d{1,2})[:\.](\d{2})\s*(?:Uhr)?", text, re.IGNORECASE)
    if treffer:
        stunde, minute = int(treffer.group(1)), int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"
    return None


def _kategorie_erkennen(text: str) -> str:
    """
    Mappt Titel/Kategorietexte auf DiesDasDüsseldorf-Kategorien.

    Args:
        text: Titel oder Kategorietext

    Returns:
        Gültige Kategorie
    """
    if not text:
        return "musik"
    text_klein = text.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if schluessel in text_klein:
            return kategorie
    return "musik"  # Standard beim Pitcher: Live-Musik


def _events_aus_json_ld(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    Primärstrategie: JSON-LD structured data extrahieren.

    Args:
        soup: Geparste HTML-Seite
        heute: Heute-Datum für Filterung

    Returns:
        Liste von Event-Dicts
    """
    events = []
    gesehene_schluessel: set[str] = set()

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            daten = json.loads(script.string or "{}")
        except (json.JSONDecodeError, AttributeError):
            continue

        eintraege = daten if isinstance(daten, list) else [daten]
        for eintrag in eintraege:
            if not isinstance(eintrag, dict):
                continue
            if eintrag.get("@type") not in ("Event", "MusicEvent", "DanceEvent", "SocialEvent"):
                continue

            titel = eintrag.get("name", "").strip()
            if not titel:
                continue

            datum_roh = eintrag.get("startDate") or eintrag.get("startDateTime")
            datum = _datum_parsen(str(datum_roh)) if datum_roh else None
            if not datum or date.fromisoformat(datum) < heute:
                continue

            uhrzeit = _uhrzeit_parsen(str(datum_roh))

            url_roh = eintrag.get("url")
            quelle_url = str(url_roh) if url_roh else LISTE_URL
            if quelle_url.startswith("/"):
                quelle_url = urljoin(BASE_URL, quelle_url)

            beschreibung_roh = eintrag.get("description")
            beschreibung = str(beschreibung_roh).strip()[:300] if beschreibung_roh else None

            bild_roh = eintrag.get("image")
            if isinstance(bild_roh, list) and bild_roh:
                bild_roh = bild_roh[0]
            if isinstance(bild_roh, dict):
                bild_url = bild_roh.get("url") or bild_roh.get("contentUrl")
            elif isinstance(bild_roh, str) and bild_roh.startswith("http"):
                bild_url = bild_roh
            else:
                bild_url = None

            preis = None
            angebote = eintrag.get("offers", [])
            if isinstance(angebote, dict):
                angebote = [angebote]
            if angebote:
                preise = [str(a.get("price", "")) for a in angebote if a.get("price")]
                if preise:
                    preis = f"ab {preise[0]}€"

            kategorie = _kategorie_erkennen(titel + " " + (beschreibung or ""))

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
                "kategorie": kategorie,
                "beschreibung": beschreibung,
                "preis": preis,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "instagram_caption": None,
                "datum_bis": None,
                "ist_wiederkehrend": False,
                "status": "neu",
            })

    return events


def _events_aus_html(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    Fallback: HTML-Parsing der Event-Übersicht.

    Args:
        soup: Geparste HTML-Seite
        heute: Heute-Datum für Filterung

    Returns:
        Liste von Event-Dicts
    """
    events = []
    gesehene_schluessel: set[str] = set()

    selektoren = [
        "article.event", "div.event", "li.event", ".event-item",
        "article[class*='event']", "div[class*='event']",
        ".show-item", ".concert-item", ".programm-item",
        ".veranstaltung", "[class*='programm']",
    ]

    karten = []
    for selektor in selektoren:
        karten = soup.select(selektor)
        if len(karten) > 1:
            logger.debug("HTML-Fallback: %d Karten mit Selektor '%s'", len(karten), selektor)
            break

    for karte in karten:
        try:
            titel_el = karte.find(["h2", "h3", "h4", "strong"])
            if not titel_el:
                continue
            titel = titel_el.get_text(strip=True)
            if not titel or len(titel) < 3:
                continue

            link_el = karte.find("a", href=True)
            quelle_url = urljoin(BASE_URL, link_el["href"]) if link_el else LISTE_URL

            datum_el = karte.find("time") or karte.find(class_=re.compile(r"date|datum|zeit", re.I))
            if not datum_el:
                continue
            datum_text = datum_el.get("datetime") or datum_el.get_text(strip=True)
            datum = _datum_parsen(datum_text)
            if not datum or date.fromisoformat(datum) < heute:
                continue

            uhrzeit = _uhrzeit_parsen(datum_text)

            bild_el = karte.find("img")
            bild_url = None
            if bild_el:
                bild_url = bild_el.get("data-src") or bild_el.get("src")
                if bild_url and bild_url.startswith("/"):
                    bild_url = urljoin(BASE_URL, bild_url)

            kategorie = _kategorie_erkennen(titel)

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
            })

        except Exception as fehler:
            logger.error("Fehler beim Parsen einer Pitcher-Event-Karte: %s", str(fehler))
            continue

    return events


def _playwright_scrape() -> str:
    """
    Ruft die Pitcher-Programm-Seite via Playwright ab.

    Returns:
        HTML-String der gerenderten Seite, oder leer bei Fehler
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    try:
        time.sleep(2)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            seite = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )
            try:
                seite.goto(LISTE_URL, timeout=30000, wait_until="domcontentloaded")
                # Kurz warten bis dynamische Inhalte geladen
                seite.wait_for_timeout(3000)
                html = seite.content()
            except PlaywrightTimeout:
                logger.warning("Pitcher Playwright-Timeout beim Laden von %s", LISTE_URL)
                html = ""
            except Exception as fehler:
                logger.error("Pitcher Playwright-Fehler: %s", fehler)
                html = ""
            finally:
                browser.close()
        return html
    except Exception as fehler:
        logger.error("Pitcher Playwright konnte nicht gestartet werden: %s", fehler)
        return ""


def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen des Pitcher Rock HQ Düsseldorf.

    Strategie:
    1. Playwright (JavaScript-Rendering) für pitcher.de/programm
    2. Fallback: statischer HTTP-Request
    3. JSON-LD structured data parsen
    4. HTML-Parsing als letzter Fallback

    Hinweis: Die Website war zum Entwicklungszeitpunkt (2026-03-05)
    nicht erreichbar (503 TLS-Fehler). Der Scraper läuft sobald
    die Website wieder verfügbar ist.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    import concurrent.futures

    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    html = ""

    # Strategie 1: Playwright
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_playwright_scrape)
            html = future.result(timeout=60)
    except Exception as fehler:
        logger.warning("Pitcher Playwright fehlgeschlagen: %s – versuche HTTP-Fallback", fehler)

    # Strategie 2: Statischer HTTP-Request als Fallback
    if not html:
        logger.info("Pitcher: Wechsle zu HTTP-Fallback")
        html = seite_abrufen(LISTE_URL, logger) or ""

    if not html:
        logger.warning(
            "Scraper %s: Seite %s nicht erreichbar – "
            "Website möglicherweise vorübergehend offline (503 TLS-Fehler bekannt)",
            QUELLE_NAME, LISTE_URL,
        )
        return []

    soup = BeautifulSoup(html, "html.parser")

    # JSON-LD zuerst
    events = _events_aus_json_ld(soup, heute)
    logger.info("Pitcher JSON-LD: %d Events", len(events))

    if not events:
        logger.info("Pitcher JSON-LD leer – versuche HTML-Parsing")
        events = _events_aus_html(soup, heute)
        logger.info("Pitcher HTML-Fallback: %d Events", len(events))

    events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]
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
    for e in ergebnisse[:5]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
