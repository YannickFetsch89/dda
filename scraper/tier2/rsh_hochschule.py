"""
rsh_hochschule.py – DiesDasDüsseldorf
Scraper für die Robert Schumann Hochschule Düsseldorf (Konzerte, Klassenabende, Gesprächskonzerte).
Quelle: Veranstaltungsliste https://www.rsh-duesseldorf.de/veranstaltungen (TYPO3, eine Seite mit allen kommenden
Terminen, nach Monaten gegliedert) und je Termin die Detailseite (Preis, Ticket-Link).
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V2, Welle B)

robots.txt (geprüft am 25.11.2026): „User-agent: *“ sperrt nur /*?id=*, /*&id=*, ?type=98, /typo3temp/, *.sql,
/modulplan/ und eine Schriftenreihe – /veranstaltungen und /veranstaltungen/details/… (mit ?cHash=…) sind erlaubt,
kein Crawl-delay. Wir halten mindestens 2 s zwischen den Anfragen ein.

Besonderheiten:
- Die Liste zeigt je Zeile Wochentag + „TT.MM“ (ohne Jahr) und die Uhrzeit; weitere Termine am selben Tag haben nur
  die Uhrzeit (Klasse „same-day“). Das Datum steht verlässlich im Pfad der Detailseite
  (/veranstaltungen/details/2026-11-25-…); als Ersatz dienen Monatsüberschrift + Tag.
- Spielort steht als Text unter dem Datum. Säle der Hochschule (Partika-Saal, Kammermusiksaal, Ensembleraum …) →
  „Robert Schumann Hochschule Düsseldorf“, Fischerstraße 110. Bekannte Orte in Düsseldorf (Tonhalle, Haus der
  Universität, Maxhaus, Schloss Benrath …) mit ihrem Namen aus der Ortstabelle. Orte außerhalb Düsseldorfs
  (z. B. Historische Stadthalle Wuppertal), Radiosendungen (WDR 3) und unbekannte Orte werden ausgelassen.
- Preis: Die Liste nennt keinen Preis. Die Detailseite sagt oft „Eintritt frei“ → „kostenlos“; Ticket-Links bekannter
  Anbieter auf der Detailseite → ticket_url. Detailseiten werden nur für Termine im Zeitfenster geladen
  (höchstens MAX_DETAILS); ohne Detailseite bleibt preis None.

Erstellt: 2026-11-25
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

QUELLE_NAME = "Robert Schumann Hochschule"
BASIS_URL = "https://www.rsh-duesseldorf.de"
PROGRAMM_URL = "https://www.rsh-duesseldorf.de/veranstaltungen"

ORT_HAUS = "Robert Schumann Hochschule Düsseldorf"
ADRESSE_HAUS = "Fischerstraße 110, 40476 Düsseldorf"

WARTEZEIT = 2.0
MAX_DETAILS = 100

# Säle und Räume der Hochschule selbst (leerer Ort = Hochschule)
_HAUS_RAEUME = re.compile(
    r"partika|kammermusiksaal|ensembleraum|campus der hochschule|studio transmediale|schumann[- ]hochschule|"
    r"fischerstra|tonstudio|orgelsaal|raum [a-z]?_?\d", re.I)  # nicht das bloße Wort „Hochschule“ (Köln …), Cursor V2

# Bekannte Orte in Düsseldorf: Suchmuster → (Ort in der Schreibweise der Ortstabelle, Adresse).
# Reihenfolge zählt (erster Treffer gewinnt).
_ORTE_EXTERN: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"haus der universit", re.I), "Haus der Universität", "Schadowpl. 14, 40212 Düsseldorf"),
    (re.compile(r"robert[- ]schumann[- ]saal", re.I), "Robert-Schumann-Saal", "Ehrenhof 4-5, 40479 Düsseldorf"),
    (re.compile(r"tonhalle", re.I), "Tonhalle Düsseldorf", "Ehrenhof 1, 40479 Düsseldorf"),
    (re.compile(r"schloss benrath", re.I), "Schloss Benrath", "Benrather Schloßallee 100-108, 40597 Düsseldorf"),
    (re.compile(r"maxhaus", re.I), "Maxhaus", "Schulstraße 11, 40213 Düsseldorf"),
    (re.compile(r"filmwerkstatt", re.I), "Filmwerkstatt Düsseldorf", "Birkenstraße 47, 40233 Düsseldorf"),
    (re.compile(r"neanderkirche", re.I), "Neanderkirche", "Bolkerstraße 36, 40213 Düsseldorf"),
    (re.compile(r"friedenskirche d(ü|ue)sseldorf", re.I), "Friedenskirche Düsseldorf",
     "Florastraße 55, 40217 Düsseldorf"),
    (re.compile(r"basilika st\.? margareta", re.I), "Basilika St. Margareta", "Gerricusplatz, 40625 Düsseldorf"),
]

_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus|verschoben)\b", re.I)
_DATUM_URL = re.compile(r"/details/(\d{4})-(\d{2})-(\d{2})-")
_MONATE = {"januar": 1, "februar": 2, "märz": 3, "april": 4, "mai": 5, "juni": 6, "juli": 7, "august": 8,
           "september": 9, "oktober": 10, "november": 11, "dezember": 12}


def _ort_und_adresse(ortstext: str) -> Optional[tuple[str, str]]:
    """(ort, adresse) für den Ortstext der Liste – None für Orte außerhalb Düsseldorfs, Radio und Unbekanntes."""
    text = (ortstext or "").strip()
    for muster, ort, adresse in _ORTE_EXTERN:
        if muster.search(text):
            return ort, adresse
    if not text or _HAUS_RAEUME.search(text):
        return ORT_HAUS, ADRESSE_HAUS
    return None


def _kategorie(titel: str) -> str:
    """Vorträge/Symposien → kultur, Kinder/Familien → family, sonst musik."""
    t = titel.lower()
    if re.search(r"kinder|famili", t):
        return "family"
    if re.search(r"vortrag|symposium|tagung|kolloquium|ringvorlesung|lesung|podium", t):
        return "kultur"
    return "musik"


def _uhrzeit(text: str) -> Optional[str]:
    """Beginn aus dem Zeittext der Liste („19:30 Uhr“, „18 Uhr“, „10-17 Uhr“); „ganztägig“ → None."""
    m = re.match(r"\s*(?:ab\s*)?(\d{1,2})(?:[:.](\d{2}))?\s*(?:Uhr|-|–|$)", text or "", re.I)
    if m and int(m.group(1)) < 24 and int(m.group(2) or 0) < 60:
        return f"{int(m.group(1)):02d}:{m.group(2) or '00'}"
    return None


def _datum(href: str, tag_text: str, monat: Optional[tuple[int, int]], letztes: Optional[str]) -> Optional[str]:
    """Datum aus dem Detail-Pfad, sonst aus „TT.MM“ + Monatsüberschrift, sonst das Datum der Zeile davor."""
    m = _DATUM_URL.search(href or "")
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})\.(\d{1,2})(?!\d)", tag_text or "")
    if m and monat:
        jahr, _ = monat
        try:
            return date(jahr, int(m.group(2)), int(m.group(1))).isoformat()
        except ValueError:
            return None
    return letztes


def _bild(zeile) -> Optional[str]:
    img = zeile.select_one(".event-content img")
    if not img:
        return None
    pfad = img.get("data-src") or img.get("src")
    if not pfad or pfad.startswith("data:"):
        return None
    url = urljoin(BASIS_URL, pfad)
    return url if url.startswith(BASIS_URL) else None


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Veranstaltungsliste → Event-Dicts (ohne Preis/Ticket – die kommen aus der Detailseite)."""
    soup = BeautifulSoup(html, "html.parser")
    ergebnis: list[dict] = []
    gesehen: set[tuple] = set()
    for monat_el in soup.select("div.month"):
        monat = None
        kopf = monat_el.select_one(".month-headline")
        if kopf:
            m = re.match(r"\s*([A-Za-zäÄ]+)\s+(\d{4})", kopf.get_text(" ", strip=True))
            if m and m.group(1).lower() in _MONATE:
                monat = (int(m.group(2)), _MONATE[m.group(1).lower()])
        letztes_datum: Optional[str] = None
        for zeile in monat_el.select("div.event-row"):
            try:
                titel_el = zeile.select_one(".event-title h4") or zeile.select_one(".event-title")
                titel = titel_el.get_text(" ", strip=True) if titel_el else ""
                spalte = zeile.select_one(".first-column-content")
                tag_el = spalte.select_one(".day-title") if spalte else None
                tag_text = tag_el.get_text(" ", strip=True) if tag_el else ""
                zeit_el = tag_el.find("span") if tag_el else None
                zeit_text = zeit_el.get_text(" ", strip=True) if zeit_el else ""
                ortstext = ""
                if spalte:
                    ortstext = " ".join(
                        t.strip() for t in spalte.find_all(string=True, recursive=False) if t.strip())
                link = zeile.select_one(".event-content a[href*='/details/']") or zeile.select_one(
                    "a[href*='/veranstaltungen/details/']")
                href = link["href"] if link else ""
                datum = _datum(href, tag_text, monat, letztes_datum)
                if datum:
                    letztes_datum = datum
                if not titel or not datum:
                    continue
                if _ABGESAGT.search(titel):
                    logger.debug("RSH: abgesagt, ausgelassen: %s", titel)
                    continue
                tag = date.fromisoformat(datum)
                if tag < heute or tag > enddatum:
                    continue
                ort_adresse = _ort_und_adresse(ortstext)
                if not ort_adresse:
                    logger.info("RSH: Ort außerhalb/unbekannt, ausgelassen: %s (%s, %s)", titel, ortstext, datum)
                    continue
                ort, adresse = ort_adresse
                uhrzeit = _uhrzeit(zeit_text)
                schluessel = (titel.lower(), datum, uhrzeit)
                if schluessel in gesehen:
                    continue
                gesehen.add(schluessel)
                ergebnis.append({
                    "titel": titel,
                    "datum": datum,
                    "uhrzeit": uhrzeit,
                    "ort": ort,
                    "adresse": adresse,
                    "kategorie": _kategorie(titel),
                    "beschreibung": None,
                    "preis": None,
                    "quelle_name": QUELLE_NAME,
                    "quelle_url": urljoin(BASIS_URL, href) if href else PROGRAMM_URL,
                    "bild_url": _bild(zeile),
                    "bild_generiert": False,
                    "status": "neu",
                    "ticket_url": None,
                })
            except Exception as fehler:
                logger.warning("RSH: Zeile übersprungen (%s)", fehler)
    return ergebnis


def _details_ergaenzen(event: dict, html: str) -> None:
    """Preis („Eintritt frei“ → kostenlos, sonst kurzer Preistext) und Ticket-Link aus der Detailseite."""
    soup = BeautifulSoup(html, "html.parser")
    inhalt = soup.select_one(".content-default") or soup.body
    if inhalt is None:
        return
    text = inhalt.get_text(" ", strip=True)
    if re.search(r"eintritt\s*(ist\s*)?frei|freier eintritt|eintritt:\s*frei|kostenlos", text, re.I):
        event["preis"] = "kostenlos"
    else:
        m = re.search(r"((?:Eintritt|Karten|Tickets)[^.€]{0,60}€[^.]{0,30})", text)
        if m:
            event["preis"] = re.sub(r"\s+", " ", m.group(1)).strip()[:120]
    ticket = ticket_link_aus(inhalt, event["quelle_url"])
    if ticket and ticket != event["quelle_url"]:
        event["ticket_url"] = ticket


def scrape() -> list[dict]:
    """Scrapt die Veranstaltungen der Robert Schumann Hochschule (Liste + Detailseiten)."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        html = seite_abrufen(PROGRAMM_URL, logger, wartezeit=WARTEZEIT)
        if html is None:
            logger.error("Scraper %s: Veranstaltungsliste nicht erreichbar", QUELLE_NAME)
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
                    _details_ergaenzen(event, detail)
                except Exception as fehler:
                    logger.warning("RSH: Detailseite nicht lesbar (%s): %s", event["quelle_url"], fehler)
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
