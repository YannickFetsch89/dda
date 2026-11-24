"""
theater_an_der_koe.py – DiesDasDüsseldorf
Scraper für das Theater an der Kö (Boulevardtheater in den Schadow Arkaden).
URL: https://theateranderkoe.de/spielplan

Der Spielplan steht vollständig als HTML auf einer Seite (alle Monate der Saison, je Vorstellung ein Block
„ts_play“ mit Datum/Uhrzeit, Titel, Bild und Link auf die Termin-Detailseite). Kein JSON-LD.

robots.txt geprüft am 2026-11-24: „User-agent: * / Allow: /“ – Spielplan erlaubt.

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1)
"""
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://theateranderkoe.de"
SPIELPLAN_URL = "https://theateranderkoe.de/spielplan"
QUELLE_NAME = "Theater an der Kö"
ORT_STANDARD = "Theater an der Kö"
ADRESSE_STANDARD = "Schadowstraße 11, 40212 Düsseldorf"
KATEGORIE_STANDARD = "kultur"

# „Freitag 27.11.2026 um 20:00 Uhr“
_DATUM_ZEIT = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\D+?(\d{1,2})[:.](\d{2}))?")
_ABGESAGT = re.compile(r"abgesagt|entf(ä|ae)llt|f(ä|ae)llt aus", re.I)


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def _event_aus_block(block, heute: date, enddatum: date) -> Optional[dict]:
    """Wandelt einen Spielplan-Block (div.ts_play) in ein Event-Dict um."""
    treffer = _DATUM_ZEIT.search(_text(block.find(class_="ts_play_info_dt")))
    if not treffer:
        return None
    try:
        tag = date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1)))
    except ValueError:
        return None
    if tag < heute or tag > enddatum:
        return None
    uhrzeit = None
    if treffer.group(4):
        stunde, minute = int(treffer.group(4)), int(treffer.group(5))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            uhrzeit = f"{stunde:02d}:{minute:02d}"

    titel_el = block.find(class_="ts_play_info_tit")
    titel = _text(titel_el)
    if not titel:
        return None

    # Abgesagte Vorstellungen weglassen (Hinweis steht ggf. im Info-Feld oder im Statusfeld)
    if _ABGESAGT.search(_text(block.find(class_="ts_play_info_info")) + " " + _text(block.find(class_="ts_play_num"))):
        return None

    link = block.find("a", class_="ts_play_info_link", href=True) or block.find("a", href=True)
    quelle_url = urljoin(BASE_URL, link["href"]) if link else SPIELPLAN_URL

    bild_url = None
    bild = block.find("img", src=True)
    if bild:
        bild_url = urljoin(BASE_URL, bild["src"])
        if "theateranderkoe.de" not in bild_url:
            bild_url = None   # nur Bilder von der Website des Hauses

    return {
        "titel": titel,
        "datum": tag.isoformat(),
        "uhrzeit": uhrzeit,
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": KATEGORIE_STANDARD,
        "beschreibung": None,
        "preis": None,
        "quelle_name": QUELLE_NAME,
        "quelle_url": quelle_url,
        "bild_url": bild_url,
        "bild_generiert": False,
        "status": "neu",
    }


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Liest alle Vorstellungen aus dem Spielplan-HTML (ohne Netz testbar)."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for block in soup.find_all("div", class_="ts_play"):
        try:
            event = _event_aus_block(block, heute, enddatum)
        except Exception as fehler:
            logger.error("%s: Fehler beim Lesen eines Spielplan-Eintrags: %s", QUELLE_NAME, fehler)
            continue
        if not event:
            continue
        schluessel = (event["titel"].lower(), event["datum"], event["uhrzeit"])
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        events.append(event)
    return events


def scrape() -> list[dict]:
    """Scrapt den Spielplan des Theaters an der Kö. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        html = seite_abrufen(SPIELPLAN_URL, logger, wartezeit=2.0)
        if html is None:
            logger.error("%s: Spielplan nicht erreichbar", QUELLE_NAME)
            return []
        events = _termine_aus_html(html, heute, enddatum)
        if not events:
            logger.warning("%s: 0 Termine auf erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []
    logger.info("Scraper %s fertig: %d Termine", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Termine ===")
    for e in ergebnisse[:5]:
        print(e)
