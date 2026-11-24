"""
theater_luegallee.py – DiesDasDüsseldorf
Scraper für das Theater an der Luegallee (Zimmertheater in Oberkassel).
URL: https://theaterluegallee.de/kalender/?year=JJJJ&month=M

Offizielle Domain: www.theater-an-der-luegallee.de leitet per HTTP 301 auf https://theaterluegallee.de weiter
(das Zertifikat für die alte Domain passt nicht, deshalb direkt die neue Domain). Der Kalender zeigt je Monat
alle Vorstellungen als HTML (div.calendar-item mit Datum in der id, darin div.calendar-event mit Uhrzeit, Titel,
Status und Link). Welche Monate es gibt, steht im Menü „Spielplan“ (Links kalender/?year=…&month=…).
JSON-LD gibt es nur für die nächsten ~7 Vorstellungen auf der Startseite – deshalb der Monatskalender.

robots.txt geprüft am 2026-11-24 (theaterluegallee.de): nur „User-agent: 008 / Disallow: /“ – für alle anderen
erlaubt.

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1)
"""
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.datum import uhrzeit_parsen
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://theaterluegallee.de/"
KALENDER_URL = "https://theaterluegallee.de/kalender/?year={jahr}&month={monat}"
QUELLE_NAME = "Theater an der Luegallee"
ORT_STANDARD = "Theater an der Luegallee"
ADRESSE_STANDARD = "Burggrafenstraße 4, 40545 Düsseldorf"
KATEGORIE_STANDARD = "kultur"
MAX_SEITEN = 13   # höchstens 13 Monatsseiten je Lauf (365-Tage-Fenster)

_TAG_ID = re.compile(r"calendar-item-(\d{4})-(\d{2})-(\d{2})")
_MONATS_LINK = re.compile(r"kalender/\?year=(\d{4})&(?:amp;)?month=(\d{1,2})")
_ABGESAGT = re.compile(r"abgesagt|entf(ä|ae)llt|f(ä|ae)llt aus", re.I)


def _monate_aus_html(html: str) -> list[tuple[int, int]]:
    """Monate (Jahr, Monat), die das Menü „Spielplan“ bzw. die Monatsnavigation verlinkt – sortiert, ohne Doppel."""
    return sorted({(int(j), int(m)) for j, m in _MONATS_LINK.findall(html) if 1 <= int(m) <= 12})


def _event_aus_eintrag(eintrag, tag: date) -> Optional[dict]:
    """Wandelt einen Kalendereintrag (div.calendar-event) in ein Event-Dict um."""
    titel_el = eintrag.find("a", class_="event_name")
    titel = titel_el.get_text(" ", strip=True) if titel_el else ""
    if not titel:
        return None

    status_el = eintrag.find(class_="event-status")
    if status_el and _ABGESAGT.search(status_el.get_text(" ", strip=True)):
        return None

    zeit_el = eintrag.find(class_="event-time")
    uhrzeit = uhrzeit_parsen(zeit_el.get_text(" ", strip=True)) if zeit_el else None

    href = titel_el.get("href") if titel_el else None
    quelle_url = urljoin(BASE_URL, href) if href else BASE_URL + "kalender/"

    bild_url = None
    bild = eintrag.find("img", src=True)
    if bild:
        bild_url = urljoin(BASE_URL, bild["src"])
        if "theaterluegallee.de" not in bild_url:
            bild_url = None

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
    """Liest alle Vorstellungen einer Monatsseite des Kalenders (ohne Netz testbar)."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []
    for tag_el in soup.find_all("div", class_="calendar-item", id=_TAG_ID):
        treffer = _TAG_ID.search(tag_el["id"])
        try:
            tag = date(int(treffer.group(1)), int(treffer.group(2)), int(treffer.group(3)))
        except ValueError:
            continue
        if tag < heute or tag > enddatum:
            continue
        for eintrag in tag_el.find_all("div", class_="calendar-event"):
            try:
                event = _event_aus_eintrag(eintrag, tag)
            except Exception as fehler:
                logger.error("%s: Fehler beim Lesen eines Kalendereintrags: %s", QUELLE_NAME, fehler)
                continue
            if event:
                events.append(event)
    return events


def _ohne_doppelte(events: list[dict]) -> list[dict]:
    """Gleicher Titel, Tag und Uhrzeit nur einmal."""
    gesehen: set[tuple] = set()
    ergebnis = []
    for e in events:
        schluessel = (e["titel"].lower(), e["datum"], e["uhrzeit"])
        if schluessel not in gesehen:
            gesehen.add(schluessel)
            ergebnis.append(e)
    return ergebnis


def scrape() -> list[dict]:
    """Scrapt die Monatskalender des Theaters an der Luegallee. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    events: list[dict] = []
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        erste_url = KALENDER_URL.format(jahr=heute.year, monat=heute.month)
        html = seite_abrufen(erste_url, logger, wartezeit=2.0)
        if html is None:
            logger.error("%s: Kalender nicht erreichbar", QUELLE_NAME)
            return []
        events.extend(_termine_aus_html(html, heute, enddatum))

        # Weitere Monate laut Menü (nur künftige, nur bis zum Fensterende)
        weitere = [
            (j, m) for j, m in _monate_aus_html(html)
            if (j, m) > (heute.year, heute.month) and date(j, m, 1) <= enddatum
        ][: MAX_SEITEN - 1]
        for jahr, monat in weitere:
            seite = seite_abrufen(KALENDER_URL.format(jahr=jahr, monat=monat), logger, wartezeit=2.0)
            if seite is None:
                logger.warning("%s: Monat %02d/%d nicht erreichbar – übersprungen", QUELLE_NAME, monat, jahr)
                continue
            events.extend(_termine_aus_html(seite, heute, enddatum))

        events = _ohne_doppelte(events)
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
