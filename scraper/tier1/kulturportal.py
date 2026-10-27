"""
kulturportal.py – DiesDasDüsseldorf
Scraper für Kulturportal Düsseldorf: Events und Veranstaltungen
Verwendet Playwright wegen JS-gerenderten Toubiz-CMS.
Erstellt: 2026-02-24
"""
import logging
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen as _datum_parsen, uhrzeit_parsen as _uhrzeit_parsen

logger = logging.getLogger(__name__)

BASE_URL = "https://kulturportal-duesseldorf.de"
LISTE_URL = "https://kulturportal-duesseldorf.de/veranstaltungen/"
QUELLE_NAME = "Kulturportal Düsseldorf"

# Bekannte Düsseldorfer Venues für Ort-Erkennung
BEKANNTE_VENUES = [
    "tonhalle", "schauspielhaus", "oper am rhein", "kunstpalast",
    "kunstsammlung", "k20", "k21", "nrw-forum", "kunsthalle",
    "filmmuseum", "zakk", "stahlwerk", "rudas", "d.live",
    "mitsubishi electric halle", "ffT düsseldorf", "stadtbücherei",
]


def _ort_aus_text(texte: list[str]) -> Optional[str]:
    """
    Sucht in einer Textliste nach einem Ort in Düsseldorf.

    Prüft zuerst bekannte Venue-Namen, dann ob "Düsseldorf" enthalten ist.

    Args:
        texte: Liste von Texten aus dem Event-Container

    Returns:
        Erkannter Ort oder None
    """
    for text in texte:
        text_lower = text.lower()
        for venue in BEKANNTE_VENUES:
            if venue in text_lower:
                return text.strip()

    for text in texte:
        if "düsseldorf" in text.lower() and len(text.strip()) < 120:
            return text.strip()

    return None


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


def _kategorie_aus_text(text: str) -> str:
    """Ermittelt eine DDA-Kategorie aus einem Kategorie-Text der Seite."""
    if not text:
        return "sonstiges"
    text_lower = text.lower()
    for schluessel, kategorie in KATEGORIE_MAP.items():
        if schluessel in text_lower:
            return kategorie
    return "sonstiges"


def _event_aus_teaser(teaser_el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem .tb-teaser <a>-Element des Kulturportals.

    Die Seite verwendet das Toubiz-CMS mit folgendem DOM-Aufbau:
      <a class="tb-teaser" href="/veranstaltungskalender/...">
        <div itemprop="startDate" content="YYYY-MM-DD">...</div>
        <h3 class="tb-teaser__title">Titel</h3>
        <span class="tb-teaser__topline-category">Kategorie</span>
        <span class="tb-teaser__location">Stadt</span>
        <span class="tb-teaser__location">Venue</span>
        <img data-src="...">

    Args:
        teaser_el: BeautifulSoup <a class="tb-teaser"> Element
        heute:     Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None wenn Pflichtfelder fehlen / Event vergangen
    """
    try:
        # --- URL ---
        href = teaser_el.get("href", "")
        quelle_url = urljoin(BASE_URL, href) if href else LISTE_URL

        # --- Titel ---
        titel_el = teaser_el.select_one(".tb-teaser__title")
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel:
            return None

        # --- Datum: itemprop="startDate" oder aus Text wie "Dienstag | 27.10. | 2026" ---
        datum_el = teaser_el.select_one("[itemprop='startDate']")
        datum = None
        if datum_el:
            datum = _datum_parsen(datum_el.get("content", ""))
            if not datum:
                datum = _datum_parsen(datum_el.get_text(strip=True))

        if not datum:
            import re as _re
            teaser_text = teaser_el.get_text(" ", strip=True)
            treffer = _re.search(r"(\d{1,2})\.(\d{1,2})\.\s*\|\s*(\d{4})", teaser_text)
            if treffer:
                tag, monat, jahr = int(treffer.group(1)), int(treffer.group(2)), int(treffer.group(3))
                try:
                    from datetime import date as _date_cls
                    datum = _date_cls(jahr, monat, tag).isoformat()
                except ValueError:
                    pass
            if not datum:
                treffer = _re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", teaser_text)
                if treffer:
                    datum = _datum_parsen(treffer.group(0))
            if not datum:
                treffer = _re.search(r"(\d{1,2})\.(\d{1,2})\.", teaser_text)
                if treffer:
                    tag, monat = int(treffer.group(1)), int(treffer.group(2))
                    try:
                        from datetime import date as _date_cls2
                        kandidat = _date_cls2(date.today().year, monat, tag)
                        if kandidat < date.today() - timedelta(days=30):
                            kandidat = _date_cls2(date.today().year + 1, monat, tag)
                        datum = kandidat.isoformat()
                    except ValueError:
                        pass

        if not datum:
            logger.debug("Kein Datum gefunden für Event: %s", titel)
            return None

        if date.fromisoformat(datum) < heute:
            return None

        # --- Uhrzeit: aus .tb-teaser-date__time oder allgemeinem Text ---
        uhrzeit = None
        zeit_el = teaser_el.select_one(".tb-teaser-date__time, .tb-teaser__time")
        if zeit_el:
            uhrzeit = _uhrzeit_parsen(zeit_el.get_text(strip=True))

        # --- Ort: zwei <span class="tb-teaser__location"> ---
        ort_els = teaser_el.select(".tb-teaser__location")
        if len(ort_els) >= 2:
            # Erstes = Stadt, zweites = Venue-Name
            ort = ort_els[1].get_text(strip=True)
        elif len(ort_els) == 1:
            ort = ort_els[0].get_text(strip=True)
        else:
            ort = "Düsseldorf"

        if not ort:
            ort = "Düsseldorf"

        # --- Kategorie ---
        kat_el = teaser_el.select_one(".tb-teaser__topline-category")
        kategorie_text = ""
        if kat_el:
            kategorie_text = kat_el.get_text(strip=True)
        if not kategorie_text:
            import re as _re2
            teaser_text_all = teaser_el.get_text(" | ", strip=True)
            for kat_key in KATEGORIE_MAP:
                if kat_key in teaser_text_all.lower():
                    kategorie_text = kat_key
                    break
        kategorie = _kategorie_aus_text(kategorie_text)

        # --- Beschreibung: Topline-Kategorie als Kurztext ---
        beschreibung = None
        topline_el = teaser_el.select_one(".tb-teaser__topline")
        if topline_el:
            beschreibung = topline_el.get_text(strip=True)[:300] or None

        # --- Enddatum: itemprop="endDate" content="YYYY-MM-DD" (für laufende Ausstellungen) ---
        datum_bis = None
        enddatum_el = teaser_el.select_one("[itemprop='endDate']")
        if enddatum_el:
            datum_bis = _datum_parsen(enddatum_el.get("content", "") or enddatum_el.get_text(strip=True))

        # --- Bild ---
        bild_url = None
        bild_el = teaser_el.select_one("img")
        if bild_el:
            bild_url = (
                bild_el.get("data-src") or
                bild_el.get("src") or
                bild_el.get("data-lazy-src")
            )
            if bild_url and not bild_url.startswith("http"):
                bild_url = urljoin(BASE_URL, bild_url)

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": None,
            "kategorie": kategorie,
            "beschreibung": beschreibung,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": datum_bis,
            "ist_wiederkehrend": datum_bis is not None,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error("Fehler beim Parsen eines Teaser-Elements: %s", str(fehler))
        return None


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def scrape() -> list[dict]:
    """
    Scrapt Events vom Kulturportal Düsseldorf.

    Verwendet Playwright, da das Toubiz-CMS die Events per JavaScript rendert
    und httpx nur eine leere Seite zurückgibt.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    import time as _time

    events: list[dict] = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    html = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
            try:
                page.goto(LISTE_URL, wait_until="networkidle", timeout=30000)
                _time.sleep(3)
                html = page.content()
            except Exception as fehler:
                logger.error("Playwright Fehler beim Laden von %s: %s", LISTE_URL, str(fehler))
            finally:
                browser.close()
    except Exception as fehler:
        logger.error("Scraper %s: Playwright konnte nicht gestartet werden: %s", QUELLE_NAME, str(fehler))

    if not html:
        logger.warning("Scraper %s: Kein HTML geladen", QUELLE_NAME)
        return []

    soup = BeautifulSoup(html, "html.parser")

    teaser_els = soup.select("a.tb-teaser")

    if not teaser_els:
        teaser_els = [
            fig.find("a", href=True)
            for fig in soup.select("figure.o-grid__item")
            if fig.find("a", href=True)
        ]

    if not teaser_els:
        logger.warning(
            "Keine Event-Teaser gefunden auf %s – "
            "Seitenstruktur hat sich möglicherweise geändert.",
            LISTE_URL,
        )
        return []

    logger.info("%d potenzielle Event-Teaser gefunden", len(teaser_els))

    gesehene_urls: set[str] = set()

    for teaser_el in teaser_els:
        event = _event_aus_teaser(teaser_el, heute)
        if event is None:
            continue

        url = event["quelle_url"]
        if url in gesehene_urls:
            continue
        gesehene_urls.add(url)

        events.append(event)

    if len(events) == 0:
        logger.warning(
            "Scraper %s: 0 Events gefunden – "
            "Seitenstruktur hat sich möglicherweise geändert.",
            QUELLE_NAME,
        )

    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]

    logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    # Direkter Testlauf
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
