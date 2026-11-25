"""
filmwerkstatt.py – DiesDasDüsseldorf
Scraper für die Filmwerkstatt Düsseldorf (Kino-Reihen, Filmgespräche, Konzerte im Hof der Birkenstraße 47).
Quelle: Programm auf der Startseite https://www.filmwerkstatt-duesseldorf.de/ (WordPress, eigenes Theme, Einträge
„startItem“ mit Wochentag, „26. Nov“, Uhrzeit, Schlagworten und Titel) und je Termin die Beitragsseite (Jahr,
Uhrzeit, Eintritt, Ticket-Link).
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V2, Welle B)

robots.txt (geprüft am 25.11.2026): Yoast-Standard „User-agent: * / Disallow:“ – alles erlaubt, kein Crawl-delay.
Wir halten mindestens 2 s zwischen den Anfragen ein (Startseite + je Termin eine Beitragsseite, meist unter 10).

Besonderheiten:
- Die Startseite nennt kein Jahr; die Beitragsseite schon („Do 26. Nov 2026 20:00“). Ohne Beitragsseite nehmen wir
  das nächste passende Datum ab heute.
- Manche Termine haben (noch) keine Uhrzeit – dann None.
- Eintritt steht im Text („Eintritt 6/8€“, „Eintritt auf Spendenbasis“); „Eintritt frei“ → „kostenlos“.
- Tickets laufen teils über xceed: Ticket-Links im Beitrag (bekannte Anbieter oder Links mit „Ticket“ im Text)
  → ticket_url. Bisher (25.11.2026) stand kein solcher Link im HTML.
- Kategorie nach Schlagwort: Konzert → musik, Seminar/Workshop → community, Kinder/Junge Filmwerkstatt → family,
  sonst (Film, Filmgespräch, Ausstellung) kultur.

Erstellt: 2026-11-25
"""
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.datum import MONAT_KURZ_MAP
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ticket_link import ticket_link_aus, ticket_link_haus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Filmwerkstatt Düsseldorf"
BASIS_URL = "https://www.filmwerkstatt-duesseldorf.de"
PROGRAMM_URL = "https://www.filmwerkstatt-duesseldorf.de/"

ORT = "Filmwerkstatt Düsseldorf"
ADRESSE = "Birkenstraße 47, 40233 Düsseldorf"

WARTEZEIT = 2.0
MAX_DETAILS = 40

_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus|verschoben)\b", re.I)
_DATUM = re.compile(r"(\d{1,2})\.\s*([A-Za-zÄäöü]{3})[A-Za-zäöü]*\.?(?:\s+(\d{4}))?")
_ZEIT = re.compile(r"\b(\d{1,2})[:.](\d{2})\b")


def _datum(text: str, heute: date) -> Optional[date]:
    """„26. Nov“ / „10. Dez 2026“ → date; ohne Jahr das nächste passende Datum ab heute."""
    m = _DATUM.search(text or "")
    if not m:
        return None
    monat = MONAT_KURZ_MAP.get(m.group(2).lower()[:3])
    if not monat:
        return None
    tag = int(m.group(1))
    try:
        if m.group(3):
            return date(int(m.group(3)), monat, tag)
        kandidat = date(heute.year, monat, tag)
        if kandidat < heute - timedelta(days=1):
            kandidat = date(heute.year + 1, monat, tag)
        return kandidat
    except ValueError:
        return None


def _uhrzeit(text: str) -> Optional[str]:
    m = _ZEIT.search(text or "")
    if m and int(m.group(1)) < 24 and int(m.group(2)) < 60:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    return None


def _kategorie(schlagworte: list[str], titel: str) -> str:
    t = " ".join(schlagworte + [titel]).lower()
    if re.search(r"konzert|live-musik|musik", t):
        return "musik"
    if re.search(r"kinder|junge filmwerkstatt|famili", t):
        return "family"
    if re.search(r"seminar|workshop|kurs", t):
        return "community"
    if re.search(r"party", t):
        return "nightlife"
    return "kultur"


def _preis(text: str) -> Optional[str]:
    if re.search(r"eintritt\s*(ist\s*)?frei|freier eintritt|kostenlos", text or "", re.I):
        return "kostenlos"
    for zeile in (text or "").splitlines():
        zeile = zeile.strip()
        if re.search(r"eintritt|€", zeile, re.I) and len(zeile) <= 80:
            return zeile
    return None


def _eigenes_bild(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    absolut = urljoin(BASIS_URL, url)
    return absolut if (urlparse(absolut).hostname or "").endswith("filmwerkstatt-duesseldorf.de") else None


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Startseite → Event-Dicts (Jahr, Preis und Ticket ergänzt danach die Beitragsseite)."""
    soup = BeautifulSoup(html, "html.parser")
    ergebnis: list[dict] = []
    gesehen: set[tuple] = set()
    for el in soup.select("div.startItem"):
        try:
            datum_el = el.select_one(".startItemDatum")
            unten = el.select_one(".startItemInfoUnten")
            if not datum_el or not unten:
                continue
            grau = unten.select_one(".startItemInfoGrau")
            untertitel = grau.get_text(" ", strip=True) if grau else ""
            if grau:
                grau.extract()
            titel = re.sub(r"\s+", " ", unten.get_text(" ", strip=True)).strip()
            if not titel or _ABGESAGT.search(titel):
                continue
            tag = _datum(datum_el.get_text(" ", strip=True), heute)
            if not tag or tag < heute or tag > enddatum:
                continue
            zeit_el = datum_el.select_one(".grau")
            uhrzeit = _uhrzeit(zeit_el.get_text(" ", strip=True)) if zeit_el else None
            link = datum_el.find("a", href=True) or el.find("a", href=True)
            quelle_url = urljoin(BASIS_URL, link["href"]) if link else PROGRAMM_URL
            schlagworte = [a.get_text(" ", strip=True) for a in el.select(".startItemInfoOben a")]
            schluessel = (titel.lower(), tag.isoformat(), uhrzeit)
            if schluessel in gesehen:
                continue
            gesehen.add(schluessel)
            bild = el.select_one(".startItemPic img[src]")
            ergebnis.append({
                "titel": titel,
                "datum": tag.isoformat(),
                "uhrzeit": uhrzeit,
                "ort": ORT,
                "adresse": ADRESSE,
                "kategorie": _kategorie(schlagworte, titel),
                "beschreibung": None,
                "preis": _preis(untertitel.replace("|", "\n")),
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": _eigenes_bild(bild["src"] if bild else None),
                "bild_generiert": False,
                "status": "neu",
                "ticket_url": None,
            })
        except Exception as fehler:
            logger.warning("Filmwerkstatt: Eintrag übersprungen (%s)", fehler)
    return ergebnis


def _details_ergaenzen(event: dict, html: str, heute: date) -> None:
    """Datum mit Jahr, Uhrzeit, Eintritt und Ticket-Link aus der Beitragsseite."""
    soup = BeautifulSoup(html, "html.parser")
    datum_el = soup.select_one(".contentItemDatum")
    if datum_el:
        text = datum_el.get_text(" ", strip=True)
        tag = _datum(text, heute)
        if tag:
            event["datum"] = tag.isoformat()
        zeit_el = datum_el.select_one(".grau")
        uhrzeit = _uhrzeit(zeit_el.get_text(" ", strip=True)) if zeit_el else None
        if uhrzeit:
            event["uhrzeit"] = uhrzeit
    inhalt = soup.select_one("#contentItemContent")
    if inhalt is None:
        return
    preis = _preis(inhalt.get_text("\n", strip=True))
    if preis:
        event["preis"] = preis
    ticket = ticket_link_aus(inhalt, event["quelle_url"])
    if not ticket:
        for a in inhalt.find_all("a", href=True):
            if re.search(r"ticket|karten", a.get_text(" ", strip=True), re.I):
                ticket = ticket_link_haus(a["href"], event["quelle_url"])
                if ticket:
                    break
    if ticket and ticket != event["quelle_url"]:
        event["ticket_url"] = ticket


def scrape() -> list[dict]:
    """Scrapt das Programm der Filmwerkstatt Düsseldorf (Startseite + Beitragsseiten)."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        html = seite_abrufen(PROGRAMM_URL, logger, wartezeit=WARTEZEIT)
        if html is None:
            logger.error("Scraper %s: Programmseite nicht erreichbar", QUELLE_NAME)
            return []
        events = _termine_aus_html(html, heute, enddatum)
        if not events:
            logger.warning("Scraper %s: 0 Termine bei erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
            return []
        for event in events[:MAX_DETAILS]:
            if event["quelle_url"] == PROGRAMM_URL:
                continue
            detail = seite_abrufen(event["quelle_url"], logger, wartezeit=WARTEZEIT)
            if detail:
                try:
                    _details_ergaenzen(event, detail, heute)
                except Exception as fehler:
                    logger.warning("Filmwerkstatt: Beitragsseite nicht lesbar (%s): %s", event["quelle_url"], fehler)
        # Nach der Jahreskorrektur erneut gegen das Zeitfenster prüfen
        events = [e for e in events if heute.isoformat() <= e["datum"] <= enddatum.isoformat()]
        logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
        return events
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for ev in ergebnisse[:3]:
        print(json.dumps(ev, ensure_ascii=False, indent=2))
