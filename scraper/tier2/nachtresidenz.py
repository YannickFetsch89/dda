"""
nachtresidenz.py – DiesDasDüsseldorf
Scraper für den Club Nachtresidenz (Bahnstraße 13, im ehemaligen Residenz-Theater).
URL: https://www.nachtresidenz.de/events/

robots.txt geprüft am 2026-11-24: gesperrt nur /wp-admin/ → /events/ erlaubt. Kein Crawl-delay.

Methode: WordPress-Theme ohne Tribe/JSON-LD. Die Programmseite listet die Termine als .b-tabs__pane-item mit
<h3 class="c-box__ttl-s3"> (Titel), <time datetime="2026-11-27 19:00:00"> (Beginn) und data-bgimage (Bild).
„Mehr“ führt meist zu fremden Ticket-Shops (ticket.io u. a.) – dann ist quelle_url die Programmseite.
Ein Abruf je Lauf.

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1, Welle A)
"""
import json
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASIS_URL = "https://www.nachtresidenz.de"
PROGRAMM_URL = "https://www.nachtresidenz.de/events/"
QUELLE_NAME = "Nachtresidenz"
ORT = "Nachtresidenz"
ADRESSE = "Bahnstraße 13, 40212 Düsseldorf"

_ABGESAGT = re.compile(r"(?i)\b(abgesagt|entfällt|cancelled|canceled|verschoben)\b")
_MUSIK = re.compile(r"(?i)\blive\b|konzert|\btour\b|tribute")
_ZEITPUNKT = re.compile(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}):(\d{2}))?")


def _eigene_url(url: Optional[str]) -> bool:
    return bool(url) and urlparse(url).netloc.lower().endswith("nachtresidenz.de")


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Wandelt die Programmseite in Events um (heute bis enddatum, ohne Doppelte, nach Datum sortiert)."""
    soup = BeautifulSoup(html or "", "html.parser")
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for item in soup.select(".b-tabs__pane-item"):
        titel_el = item.select_one(".c-box__ttl-s3") or item.find(["h2", "h3"])
        zeit = item.find("time")
        titel = " ".join(titel_el.get_text(" ", strip=True).split()) if titel_el else ""
        treffer = _ZEITPUNKT.search(str(zeit.get("datetime") or "")) if zeit else None
        if not titel or not treffer:
            continue
        datum = treffer.group(1)
        uhrzeit = f"{treffer.group(2)}:{treffer.group(3)}" if treffer.group(2) else None
        if uhrzeit == "00:00":
            uhrzeit = None
        if not (heute <= date.fromisoformat(datum) <= enddatum) or _ABGESAGT.search(titel):
            continue
        schluessel = (titel.lower(), datum, uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)

        link = item.select_one("a.btn-pointer[href]") or item.select_one("a.b-box__link[href]")
        ziel = urljoin(PROGRAMM_URL, link["href"]) if link else None
        bild_el = item.select_one("[data-bgimage]")
        bild = urljoin(BASIS_URL, bild_el["data-bgimage"]) if bild_el and bild_el.get("data-bgimage") else None

        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT,
            "adresse": ADRESSE,
            "kategorie": "musik" if _MUSIK.search(titel) else "nightlife",
            "beschreibung": None,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": ziel if _eigene_url(ziel) else PROGRAMM_URL,
            "bild_url": bild if _eigene_url(bild) else None,
            "bild_generiert": False,
            "status": "neu",
        })
    return sorted(events, key=lambda e: (e["datum"], e["uhrzeit"] or ""))


def scrape() -> list[dict]:
    """Scrapt die Events der Nachtresidenz. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    try:
        html = seite_abrufen(PROGRAMM_URL, logger, wartezeit=2.0)
        if html is None:
            logger.error("%s: Programmseite nicht erreichbar", QUELLE_NAME)
            return []
        events = _termine_aus_html(html, heute, enddatum)
        if not events:
            logger.warning("%s: 0 Termine gefunden – Seitenstruktur geändert?", QUELLE_NAME)
        logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
        return events
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
