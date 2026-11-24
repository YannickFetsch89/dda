"""
tas_neuss.py – DiesDasDüsseldorf
Scraper für das Theater am Schlachthof (TaS) in Neuss.
URL: https://tas-neuss.de/spielplan/ (WordPress, eigener Block „wp-block-tas-spielplan“)
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V1, Welle A).

robots.txt (geprüft am 24.11.2026): „User-agent: * / Disallow: /wp-admin/ / Allow: /wp-admin/admin-ajax.php“ –
der Spielplan ist erlaubt, kein Crawl-delay. Eine Anfrage je Lauf (der Spielplan zeigt die ganze Spielzeit).

Aufbau: Je Vorstellung eine Karte (div.grid) mit Schlagwörtern (Schauspiel, Kabarett, Kindertheater, Konzert …),
Titel mit Link zur Stückseite, Datum „Fr., 27.11.26“, Uhrzeit „19:30 Uhr“ bzw. „15 Uhr“, Kartenlink oder
„Ausverkauft“. Kein JSON-LD für Veranstaltungen.
- Kategorie: Kindertheater → family, Schlagwort Konzert → musik, sonst kultur.
- Vorstellungen mit dem Schlagwort „Wetthalle“ finden nicht im Theater am Schlachthof statt (Gastspielort in Neuss)
  und werden ausgelassen, weil der Ort fest „Theater am Schlachthof“ ist.
- „– Premiere“ wird vom Titel entfernt, damit Premiere und Folgevorstellungen denselben Titel tragen.
- Ausverkaufte Vorstellungen bleiben, abgesagte entfallen.

Erstellt: 2026-11-24
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
from scraper.utils.ticket_link import ticket_link_aus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Theater am Schlachthof Neuss"
BASIS_URL = "https://tas-neuss.de"
SPIELPLAN_URL = "https://tas-neuss.de/spielplan/"
ORT = "Theater am Schlachthof"
# Adresse aus dem Fuß der Website (24.11.2026)
ADRESSE = "Blücherstraße 31-33, 41460 Neuss"
WARTEZEIT = 2.0

_DATUM = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})")
_UHRZEIT = re.compile(r"(\d{1,2})(?:[:.](\d{2}))?\s*Uhr", re.I)
_PREMIERE = re.compile(r"\s*[–—-]\s*(Uraufführung|Premiere|Wiederaufnahme)\s*$", re.I)
_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus)\b", re.I)


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el else ""


def _datum(text: str) -> Optional[str]:
    m = _DATUM.search(text)
    if not m:
        return None
    tag, monat, jahr = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if jahr < 100:
        jahr += 2000
    try:
        return date(jahr, monat, tag).isoformat()
    except ValueError:
        return None


def _uhrzeit(text: str) -> Optional[str]:
    m = _UHRZEIT.search(text)
    if not m:
        return None
    stunde, minute = int(m.group(1)), int(m.group(2) or 0)
    return f"{stunde:02d}:{minute:02d}" if 0 <= stunde <= 23 and 0 <= minute <= 59 else None


def _kategorie(schlagwoerter: list[str]) -> str:
    klein = {s.lower() for s in schlagwoerter}
    if "kindertheater" in klein or any(s.startswith("ab ") for s in klein):
        return "family"
    if "konzert" in klein:
        return "musik"
    return "kultur"


def _bild(karte) -> Optional[str]:
    """Bild der Karte – nur von tas-neuss.de (lazyload: data-src, sonst <noscript>-Bild)."""
    for img in karte.select("img"):
        src = img.get("data-src") or img.get("src") or ""
        if not src or src.startswith("data:"):
            continue
        url = urljoin(BASIS_URL, src)
        host = urlparse(url).netloc.lower()
        if host == "tas-neuss.de" or host.endswith(".tas-neuss.de"):
            return url
    return None


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Spielplan-HTML → Event-Dicts im Projektformat (nur Vorstellungen zwischen heute und enddatum)."""
    soup = BeautifulSoup(html, "html.parser")
    block = soup.select_one(".wp-block-tas-spielplan") or soup
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for karte in block.select("div.grid"):
        titel_el = karte.select_one("h3.wp-block-post-title") or karte.select_one("h3")
        titel = _PREMIERE.sub("", _text(titel_el)).strip()
        if not titel:
            continue
        schlagwoerter = [_text(a) for a in karte.select('a[rel="tag"]')]
        if any(s.lower() == "wetthalle" for s in schlagwoerter):
            logger.debug("TaS: Vorstellung in der Wetthalle ausgelassen: %s", titel)
            continue
        karten_text = _text(karte)
        if _ABGESAGT.search(karten_text):
            logger.debug("TaS: abgesagt, ausgelassen: %s", titel)
            continue
        datum, uhrzeit = None, None
        for p in karte.select("div.flex.gap-2"):
            art = _text(p.find("title")).lower()
            wert = _text(p.find("p"))
            if art == "datum":
                datum = _datum(wert)
            elif art == "uhrzeit":
                uhrzeit = _uhrzeit(wert)
        if not datum:
            datum = _datum(karten_text)
        if not datum:
            continue
        if not heute.isoformat() <= datum <= enddatum.isoformat():
            continue
        schluessel = (titel.lower(), datum, uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        link = titel_el.find("a", href=True) if titel_el else None
        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT,
            "adresse": ADRESSE,
            "kategorie": _kategorie(schlagwoerter),
            "beschreibung": None,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": urljoin(BASIS_URL, link["href"]) if link else SPIELPLAN_URL,
            "ticket_url": ticket_link_aus(karte, BASIS_URL),  # Kartenkauf karten.tas-neuss.de (Plan 5.5.2, P1)
            "bild_url": _bild(karte),
            "bild_generiert": False,
            "status": "neu",
        })
    return events


def scrape() -> list[dict]:
    """Scrapt den Spielplan des Theaters am Schlachthof Neuss."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        html = seite_abrufen(SPIELPLAN_URL, logger, wartezeit=WARTEZEIT)
        if html is None:
            logger.error("Scraper %s: Spielplan nicht erreichbar", QUELLE_NAME)
            return []
        events = _termine_aus_html(html, heute, enddatum)
        if not events:
            logger.warning("Scraper %s: 0 Termine bei erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
        logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
        return events
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for ev in ergebnisse[:3]:
        print(json.dumps(ev, ensure_ascii=False, indent=2))
