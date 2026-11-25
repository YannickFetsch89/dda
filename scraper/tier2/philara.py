"""
philara.py – DiesDasDüsseldorf
Scraper für die Sammlung Philara (Kunstsammlung in Flingern): Führungen, Familienführungen, Workshops,
Konzerte, Performances.
Quelle: Programmseite https://philara.de/de/programm (Drupal, eine Seite mit allen Programmeinträgen seit 2016,
neueste zuerst – rund 100 Einträge, davon nur wenige in der Zukunft).
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V2, Welle B)

robots.txt (geprüft am 25.11.2026): Drupal-Standard – gesperrt sind /core/, /profiles/, /admin/, /search/, /user/…,
/node/add/; /de/programm und die Eintragsseiten (/de/<name>) sind erlaubt, kein Crawl-delay. Eine Anfrage je Lauf.

Besonderheiten:
- Je Eintrag: linke Spalte mit Datum (h2) und Zeit (h3), mittlere Spalte mit Titel (h2), Untertitel (h3) und Text.
  Das Datum ist Freitext: „12.12.2026“, „6.12 und 13.12.2026“, „6. & 8.7, 22. & 24.9.2026“ (mehrere Einzeltermine,
  das Jahr steht nur am Ende) oder „05.-08.12. 2024“ (Zeitraum → ein Termin mit datum_bis). Fehlt das Jahr, nehmen
  wir das nächste passende Datum ab heute.
- Uhrzeit = Beginn („16:00-17:00“ → 16:00, „14 - 18 Uhr“ → 14:00, „ab 17:30“ → 17:30); „10:41“ ist ein
  Platzhalter der Website bei Einträgen ohne Uhrzeit (Messen, Online) → None.
- Preis aus dem Text („Teilnahmegebühr: kostenlos“, „Eintritt frei“ → „kostenlos“, sonst Betrag mit €).
- Tickets laufen über Reservix: Links auf bekannte Ticketanbieter im Eintrag → ticket_url (calendly-Anmeldungen
  zählen nicht als Ticketverkauf).
- Reine Ausstellungseröffnungen ohne Uhrzeit-Angabe gibt es selten; Eröffnungen mit Uhrzeit sind echte Termine.

Erstellt: 2026-11-25
"""
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ticket_link import ticket_link_aus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Sammlung Philara"
BASIS_URL = "https://philara.de"
PROGRAMM_URL = "https://philara.de/de/programm"

ORT = "Sammlung Philara"
ADRESSE = "Birkenstraße 47a, 40233 Düsseldorf"

WARTEZEIT = 2.0
PLATZHALTER_ZEIT = "10:41"

_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus|verschoben|cancelled)\b", re.I)
_ZEITRAUM = re.compile(r"\d\.?\s*[-–]\s*\d")
_TERMIN = re.compile(r"(\d{1,2})\.(?:\s*(\d{1,2})(?!\d)\.?(?:\s*(\d{4}|\d{2}(?!\d)))?)?")


def _jahr_ergaenzen(tag: int, monat: int, jahr: Optional[int], heute: date) -> Optional[date]:
    try:
        if jahr:
            return date(jahr if jahr > 100 else 2000 + jahr, monat, tag)
        kandidat = date(heute.year, monat, tag)
        if kandidat < heute - timedelta(days=1):
            kandidat = date(heute.year + 1, monat, tag)
        return kandidat
    except ValueError:
        return None


def _daten(text: str, heute: date) -> tuple[list[date], Optional[date]]:
    """
    Freitext-Datum → (Liste der Einzeltermine, Enddatum bei Zeitraum).
    Tage ohne Monat/Jahr übernehmen Monat und Jahr vom nächsten vollständigen Datum dahinter.
    """
    roh: list[list[Optional[int]]] = []
    for m in _TERMIN.finditer(text or ""):
        tag = int(m.group(1))
        monat = int(m.group(2)) if m.group(2) else None
        jahr = int(m.group(3)) if m.group(3) else None
        if not 1 <= tag <= 31 or (monat is not None and not 1 <= monat <= 12):
            continue
        roh.append([tag, monat, jahr])
    # Monat und Jahr von hinten nach vorn auffüllen
    monat_folgt: Optional[int] = None
    jahr_folgt: Optional[int] = None
    for eintrag in reversed(roh):
        if eintrag[1] is None:
            eintrag[1] = monat_folgt
        else:
            monat_folgt = eintrag[1]
        if eintrag[2] is None:
            eintrag[2] = jahr_folgt
        else:
            jahr_folgt = eintrag[2]
    daten = [d for d in (_jahr_ergaenzen(t, mo, j, heute) for t, mo, j in roh if mo) if d]
    if not daten:
        return [], None
    if _ZEITRAUM.search(text) and len(daten) >= 2:
        return [daten[0]], daten[-1] if daten[-1] > daten[0] else None
    return daten, None


def _beginn(text: str) -> Optional[str]:
    """Beginn aus dem Zeittext („16:00-17:00“, „14 - 18 Uhr“, „ab 17:30“, „13:00 Uhr“)."""
    m = re.match(r"\s*(?:ab\s*|jeweils\s*)?(\d{1,2})(?:[:.](\d{2}))?\s*(?:Uhr|-|–|&|\||$)", text or "", re.I)
    if not m or int(m.group(1)) > 23:
        return None
    zeit = f"{int(m.group(1)):02d}:{m.group(2) or '00'}"
    return None if zeit == PLATZHALTER_ZEIT else zeit


def _kategorie(titel: str, untertitel: str) -> str:
    t = f"{titel} {untertitel}".lower()
    if re.search(r"kinder|famili|bastel|weltkindertag", t):
        return "family"
    if re.search(r"party|disco|rave", t):
        return "nightlife"
    if re.search(r"konzert|concert|sound|orgel|requiem|musik", t):
        return "musik"
    if re.search(r"workshop|flohmarkt|trödel|diskussionsgruppe|summer school", t):
        return "community"
    return "kultur"


def _preis(text: str) -> Optional[str]:
    if re.search(r"(teilnahmegebühr|eintritt|teilnahme)\s*:?\s*(frei|kostenlos)|kostenlos|freier eintritt", text, re.I):
        return "kostenlos"
    m = re.search(r"((?:Eintritt|Teilnahmegebühr|Tickets?|Karten)\s*:?[^.\n€]{0,40}€[^.\n]{0,20})", text)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()[:120]
    return None


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Programmseite → Event-Dicts (ein Dict je Einzeltermin im Zeitfenster)."""
    soup = BeautifulSoup(html, "html.parser")
    ergebnis: list[dict] = []
    gesehen: set[tuple] = set()
    for el in soup.select("div.node--type-program-entry"):
        try:
            spalten = el.select(".programm__text")
            if len(spalten) < 2:
                continue
            datum_el = spalten[0].find("h2")
            zeit_el = spalten[0].find("h3")
            titel_el = spalten[1].find("h2")
            unter_el = spalten[1].find("h3")
            titel = titel_el.get_text(" ", strip=True) if titel_el else ""
            untertitel = unter_el.get_text(" ", strip=True) if unter_el else ""
            if not titel or not datum_el:
                continue
            if _ABGESAGT.search(f"{titel} {untertitel}"):
                logger.debug("Philara: abgesagt, ausgelassen: %s", titel)
                continue
            daten, datum_bis = _daten(datum_el.get_text(" ", strip=True), heute)
            if not daten:
                continue
            zeit_text = zeit_el.get_text(" ", strip=True) if zeit_el else ""
            zeiten = [z.strip() for z in zeit_text.split("|")]
            text = spalten[1].get_text("\n", strip=True)
            pfad = el.get("about") or ""
            quelle_url = urljoin(BASIS_URL, pfad) if pfad else PROGRAMM_URL
            bild = el.select_one(".programm__image img[src]")
            bild_url = urljoin(BASIS_URL, bild["src"]) if bild else None
            if bild_url and not bild_url.startswith(BASIS_URL):
                bild_url = None
            ticket = ticket_link_aus(el, BASIS_URL)
            for i, tag in enumerate(daten):
                if tag < heute or tag > enddatum:
                    continue
                # Bei „20.08.: 11:00 | 20.09.: 18:00“ gehört je Datum eine eigene Zeit dazu
                zeit_roh = zeiten[i] if len(zeiten) == len(daten) else zeiten[0]
                zeit_roh = re.sub(r"^\s*\d{1,2}\.\d{1,2}\.(?:\d{2,4})?\s*:\s*", "", zeit_roh)
                uhrzeit = _beginn(zeit_roh)
                schluessel = (titel.lower(), tag.isoformat(), uhrzeit)
                if schluessel in gesehen:
                    continue
                gesehen.add(schluessel)
                event = {
                    "titel": titel,
                    "datum": tag.isoformat(),
                    "uhrzeit": uhrzeit,
                    "ort": ORT,
                    "adresse": ADRESSE,
                    "kategorie": _kategorie(titel, untertitel),
                    "beschreibung": None,
                    "preis": _preis(f"{untertitel}\n{text}"),
                    "quelle_name": QUELLE_NAME,
                    "quelle_url": quelle_url,
                    "bild_url": bild_url,
                    "bild_generiert": False,
                    "status": "neu",
                    "ticket_url": ticket if ticket and ticket != quelle_url else None,
                }
                if datum_bis:
                    event["datum_bis"] = datum_bis.isoformat()
                ergebnis.append(event)
        except Exception as fehler:
            logger.warning("Philara: Eintrag übersprungen (%s)", fehler)
    return ergebnis


def scrape() -> list[dict]:
    """Scrapt das Programm der Sammlung Philara."""
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
            logger.warning("Scraper %s: 0 Termine bei erreichbarer Seite (%d Programmeinträge insgesamt) – "
                           "Seitenstruktur geändert oder nur vergangene Termine?",
                           QUELLE_NAME, html.count("node--type-program-entry"))
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
