"""
rheinisches_landestheater.py – DiesDasDüsseldorf
Scraper für das Rheinische Landestheater Neuss (RLT).
Quelle: Spielplan https://www.rheinisches-landestheater.de/spielplan/index.html – die Vorstellungen lädt die Seite
monatsweise per AJAX nach: spielplan/programm.html?ajax=1&offset=<Monat ab heute, 0 = laufender Monat>&letzterTermin=<Zeitstempel>
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V2, Welle B).

robots.txt (geprüft am 25.11.2026): keine vorhanden (HTTP 404) – alles erlaubt, kein Crawl-delay. Der Browser fragt
die Monate per POST ab; ein GET mit denselben Parametern liefert dasselbe HTML (nur lesend, ohne Filter). Eine Anfrage
je Monat, Abbruch nach dem Fenster-Ende, bei „ende erreicht.“ oder nach MAX_SEITEN; mindestens 2 s Pause.
Hinweis: Der Spielplan-Link der Startseite (./spielplan/index.html relativ zu /start/) führt auf 404 – richtig ist
/spielplan/index.html.

Aufbau je Vorstellung (div.performance): Klassen date-DDMMYY, sparte-N, ort-N; .spielplan-zeit („19:30–21:20 Uhr“),
.spielplan-raum („Kleine Bühne“ + span.spielplan-ort „Neuss“), Titel in .head-bold-l, Link zur Produktionsseite mit
ID_Vorstellung, Button „Tickets“ (a.btn-ticket, Shop dtsinhousesales2.derticketservice.de), „Ausverkauft“,
„Eintritt frei“, „Gruppenbuchung“.
- Gastspiele in anderen Städten (span.spielplan-ort ≠ Neuss) werden ausgelassen: außerhalb des Gebiets
  (pipeline.gebiet.stadt_im_gebiet) sowieso, Gastspiele in Düsseldorf/Ratingen auch, weil der Ort fest
  „Das Rheinische Landestheater“ (Oberstraße 95) ist und der fremde Spielort nicht in der Ortstabelle stünde.
- Vorstellungen ohne Raum/Stadt (z. B. „Kultur für Kinder – Kulturamt Neuss“) finden laut Kulturamt auf der großen
  Bühne des RLT statt und bleiben; der Zusatz „- Rheinisches Landestheater“ im Titel entfällt.
- Geschlossene Veranstaltungen und reine Gruppen-/Schulvorstellungen (nur Button „Gruppenbuchung“) entfallen,
  ausverkaufte bleiben, abgesagte entfallen.
- Kategorie: Kinder-/Jugendtheater, Angebote für Kinder oder Altersempfehlung bis 10 Jahre → family,
  Community-Events → community, Chor → musik, sonst (Schauspiel, Tanz, Lesung, Kabarett) kultur.

Erstellt: 2026-11-25
"""
import json
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import vorschau_ende
from pipeline.gebiet import stadt_im_gebiet
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ticket_link import ticket_link_haus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Rheinisches Landestheater Neuss"
BASIS_URL = "https://www.rheinisches-landestheater.de/"
SPIELPLAN_URL = "https://www.rheinisches-landestheater.de/spielplan/index.html"
AJAX_URL = "https://www.rheinisches-landestheater.de/spielplan/programm.html?ajax=1&offset={offset}&letzterTermin={letzter}"
ORT = "Das Rheinische Landestheater"
ADRESSE = "Oberstraße 95, 41460 Neuss"
STADT = "Neuss"
WARTEZEIT = 2.0
MAX_SEITEN = 14  # Monate; die Spielzeit reicht bis Juli

# Sparten-IDs aus dem Filter der Spielplan-Seite (25.11.2026)
SPARTEN_FAMILIE = {"9", "18", "23"}   # Kinder- und Jugendtheater, Angebote für Kinder und Jugendliche
SPARTE_COMMUNITY = "20"               # Community-Events
SPARTE_CHOR = "21"

_UHRZEIT = re.compile(r"(\d{1,2})(?:[:.](\d{2}))?\s*(?:[–-]\s*\d{1,2}(?:[:.]\d{2})?\s*)?Uhr", re.I)
_LETZTER = re.compile(r'class="d-none letzterTermin">\s*(\d+)\s*<')
_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus)\b", re.I)
_GESCHLOSSEN = re.compile(r"geschlossene veranstaltung|nur gruppenbuchung", re.I)
_KOSTENLOS = re.compile(r"eintritt frei|kostenfrei|kostenlos", re.I)
_ALTER_AB = re.compile(r"\bab (\d{1,2}) jahren", re.I)
_ALTER_SPANNE = re.compile(r"\b(\d{1,2}) bis (\d{1,2}) jahre", re.I)
_TITEL_ZUSATZ = re.compile(r"\s*[-–]\s*(das )?rheinische(s)? landestheater\s*$", re.I)


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True).replace("\xad", "")).strip() if el else ""


def _klassen_werte(div, praefix: str) -> list[str]:
    return [k[len(praefix):] for k in div.get("class", []) if k.startswith(praefix)]


def _datum(div) -> Optional[str]:
    for wert in _klassen_werte(div, "date-"):
        if re.fullmatch(r"\d{6}", wert):
            try:
                return date(2000 + int(wert[4:6]), int(wert[2:4]), int(wert[0:2])).isoformat()
            except ValueError:
                return None
    return None


def _uhrzeit(text: str) -> Optional[str]:
    m = _UHRZEIT.search(text)
    if not m:
        return None
    stunde, minute = int(m.group(1)), int(m.group(2) or 0)
    return f"{stunde:02d}:{minute:02d}" if 0 <= stunde <= 23 and 0 <= minute <= 59 else None


def _kategorie(sparten: set[str], karten_text: str) -> str:
    if sparten & SPARTEN_FAMILIE:
        return "family"
    alter = [int(a) for a in _ALTER_AB.findall(karten_text)] + [int(a) for a, _ in _ALTER_SPANNE.findall(karten_text)]
    if alter and min(alter) <= 10:
        return "family"
    if SPARTE_COMMUNITY in sparten:
        return "community"
    if SPARTE_CHOR in sparten:
        return "musik"
    return "kultur"


def _bild(div) -> Optional[str]:
    """Szenenfoto der Karte (img in div.ratio) – nur von rheinisches-landestheater.de, keine Logos/Sticker."""
    for img in div.select("div.ratio img"):
        src = (img.get("src") or "").strip()
        if not src or src.startswith("data:"):
            continue
        url = urljoin(BASIS_URL, src)
        host = urlparse(url).netloc.lower()
        if host == "rheinisches-landestheater.de" or host.endswith(".rheinisches-landestheater.de"):
            return url
    return None


def _letzter_termin(html: str) -> Optional[str]:
    m = _LETZTER.search(html or "")
    return m.group(1) if m else None


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Ein AJAX-Abschnitt des Spielplans → Event-Dicts im Projektformat (nur Vorstellungen im Haus im Fenster)."""
    soup = BeautifulSoup(html or "", "html.parser")
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for div in soup.select("div.performance"):
        titel_el = div.select_one(".head-bold-l")
        titel = _TITEL_ZUSATZ.sub("", _text(titel_el)).strip()
        datum = _datum(div)
        if not titel or not datum or not heute.isoformat() <= datum <= enddatum.isoformat():
            continue
        karten_text = _text(div)
        stadt = _text(div.select_one(".spielplan-ort"))
        if stadt and stadt.lower() != STADT.lower():
            grund = "außerhalb des Gebiets" if not stadt_im_gebiet(stadt) else "fremder Spielort"
            logger.debug("RLT: Gastspiel in %s ausgelassen (%s): %s", stadt, grund, titel)
            continue
        if _ABGESAGT.search(karten_text):
            logger.debug("RLT: abgesagt, ausgelassen: %s", titel)
            continue
        knoepfe = [_text(b).lower() for b in div.select(".btn")]
        if _GESCHLOSSEN.search(karten_text) or "gruppenbuchung" in knoepfe:
            logger.debug("RLT: geschlossene bzw. Gruppenvorstellung ausgelassen: %s (%s)", titel, datum)
            continue
        uhrzeit = _uhrzeit(_text(div.select_one(".spielplan-zeit")))
        schluessel = (titel.lower(), datum, uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        link = (titel_el.find("a", href=True) if titel_el else None) or div.select_one("a.btn-more[href]")
        ticket = div.select_one("a.btn-ticket[href]")
        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT,
            "adresse": ADRESSE,
            "kategorie": _kategorie(set(_klassen_werte(div, "sparte-")), karten_text),
            "beschreibung": None,
            "preis": "kostenlos" if any(_KOSTENLOS.search(k) for k in knoepfe) else None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": urljoin(BASIS_URL, link["href"]) if link else SPIELPLAN_URL,
            "ticket_url": ticket_link_haus(ticket["href"], BASIS_URL) if ticket else None,
            "bild_url": _bild(div),
            "bild_generiert": False,
            "status": "neu",
        })
    return events


def scrape() -> list[dict]:
    """Scrapt den Spielplan des Rheinischen Landestheaters Neuss (monatsweise)."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        events: list[dict] = []
        gesehen: set[tuple] = set()
        letzter = "0"
        erreicht = False
        for offset in range(MAX_SEITEN):
            # offset = Monat ab dem laufenden Monat; Monate nach dem Fenster-Ende nicht mehr abfragen
            monat = heute.month - 1 + offset
            if date(heute.year + monat // 12, monat % 12 + 1, 1) > enddatum:
                break
            html = seite_abrufen(AJAX_URL.format(offset=offset, letzter=letzter), logger, wartezeit=WARTEZEIT)
            if html is None:
                if offset == 0:
                    logger.error("Scraper %s: Spielplan nicht erreichbar", QUELLE_NAME)
                    return []
                break
            erreicht = True
            if html.strip() == "ende erreicht.":
                break
            for ev in _termine_aus_html(html, heute, enddatum):
                schluessel = (ev["titel"].lower(), ev["datum"], ev["uhrzeit"])
                if schluessel not in gesehen:
                    gesehen.add(schluessel)
                    events.append(ev)
            letzter = _letzter_termin(html) or letzter
        if erreicht and not events:
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
