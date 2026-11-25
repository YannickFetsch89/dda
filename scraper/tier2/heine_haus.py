"""
heine_haus.py – DiesDasDüsseldorf
Scraper für das Heine Haus Literaturhaus Düsseldorf (Bolkerstraße 53).
Programmseite: https://www.heinehaus.de/ (Startseite)

WordPress ohne Kalender-Plugin für die Liste: Die Startseite zeigt die Termine als Beiträge (div.post im
#loop-container, Titel mit Link zur Beitragsseite) und im Slider oben; Datum steht im Text als
„TT.MM.JJJJ, Wd., HH:MM Uhr“. Weiter unten und auf /index.php/page/2/ ff. stehen alte Beiträge – wir nehmen nur
Daten ab heute. Das iCal (/?feed=my-calendar-ics) ist unvollständig und wird nicht genutzt.
Beiträge mit „Außer Haus“ finden an einem anderen Ort statt (z. B. Buchhandlung, Zentralbibliothek) und werden
weggelassen – der Ort wäre sonst falsch.

robots.txt geprüft am 2026-11-25: keine robots.txt vorhanden (404) → keine Sperren. Ein Abruf je Lauf, 2 s Pause.

Kategorie: kultur (Lesungen, Buchvorstellungen, Gespräche).

Erstellt: 2026-11-25 (Quellen-Ausbau, Schritt V2, Welle C)
"""
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ticket_link import ticket_link_aus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Heine Haus Literaturhaus"
START_URL = "https://www.heinehaus.de/"
ORT_STANDARD = "Heine Haus Literaturhaus Düsseldorf"
ADRESSE_STANDARD = "Bolkerstraße 53, 40213 Düsseldorf"
KATEGORIE_STANDARD = "kultur"
WARTEZEIT_S = 2.0

# „08.12.2026, Di., 19:30 Uhr“ / „16.11.2026, Mo, 19:00 Uhr“ / „22.01.2026, Do. 11:00 bis 13:00 Uhr“
_TERMIN = re.compile(
    r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s*,?\s*(?:[A-Za-zÄÖÜäöü]{2,3}\.?\s*,?\s*)?"
    r"(?:(\d{1,2})[:.](\d{2})(?:\s*(?:bis|–|-)\s*\d{1,2}[:.]\d{2})?\s*Uhr)?"
)
_AUSSER_HAUS = re.compile(r"au(?:ß|ss)er\s+haus", re.I)


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el is not None else ""


def _termin(text: str) -> Optional[tuple[date, Optional[str], int]]:
    """Erstes Datum im Text → (Tag, Uhrzeit, Position) oder None."""
    treffer = _TERMIN.search(text)
    if not treffer:
        return None
    try:
        tag = date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1)))
    except ValueError:
        return None
    uhrzeit = None
    if treffer.group(4):
        stunde, minute = int(treffer.group(4)), int(treffer.group(5))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            uhrzeit = f"{stunde:02d}:{minute:02d}"
    return tag, uhrzeit, treffer.start()


def _titel(roh: str) -> str:
    """Schlusspunkt weg („Flurina Badel. Nebelflüchtige.“ → „Flurina Badel. Nebelflüchtige“)."""
    return re.sub(r"\s*\.\s*$", "", roh.strip())


def _event(titel: str, tag: date, uhrzeit: Optional[str], url: str, ticket: Optional[str]) -> dict:
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
        "quelle_url": url,
        "ticket_url": ticket,
        "bild_url": None,
        "bild_generiert": False,
        "status": "neu",
    }


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Liest die Termine der Startseite: erst Beiträge (mit eigener URL), dann Slider (ohne Doppelte)."""
    soup = BeautifulSoup(html or "", "html.parser")
    kandidaten: list[tuple[str, str, str, Optional[str]]] = []  # (Titel, Text, URL, Ticket)

    for beitrag in soup.select("#loop-container div.post, #loop-container article"):
        if beitrag.name == "article" and beitrag.find_parent("div", class_="post"):
            continue  # article steckt im div.post – nur einmal lesen
        titel_el = beitrag.select_one(".post-title a") or beitrag.select_one(".post-title")
        inhalt = beitrag.select_one(".post-content") or beitrag
        if not titel_el:
            continue
        link = titel_el.get("href") if titel_el.name == "a" else None
        url = urljoin(START_URL, link) if link else START_URL
        kandidaten.append((_text(titel_el), _text(inhalt), url, ticket_link_aus(inhalt, START_URL)))

    for folie in soup.select("#bb-slider li.slide"):
        titel_el = folie.select_one(".title")
        if titel_el:
            kandidaten.append((_text(titel_el), _text(folie.select_one("p") or folie), START_URL,
                               ticket_link_aus(folie, START_URL)))

    events: list[dict] = []
    gesehen: set[tuple] = set()
    for titel_roh, text, url, ticket in kandidaten:
        termin = _termin(text)
        if not termin or not titel_roh:
            continue
        tag, uhrzeit, pos = termin
        if _AUSSER_HAUS.search(text[:pos + 1]):
            logger.debug("%s: „%s“ findet außer Haus statt – übersprungen", QUELLE_NAME, titel_roh)
            continue
        if tag < heute or tag > enddatum:
            continue
        titel = _titel(titel_roh)
        schluessel = (tag, uhrzeit)  # Slider wiederholt Beiträge (Titel teils anders geschrieben)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        events.append(_event(titel, tag, uhrzeit, url, ticket))
    events.sort(key=lambda e: (e["datum"], e["uhrzeit"] or ""))
    return events


def scrape() -> list[dict]:
    """Scrapt die Termine des Heine Hauses von der Startseite. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        html = seite_abrufen(START_URL, logger, wartezeit=WARTEZEIT_S)
        if html is None:
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
    for e in scrape():
        print(e)
