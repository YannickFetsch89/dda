"""
aquazoo.py – DiesDasDüsseldorf
Scraper für das Aquazoo Löbbecke Museum (Führungen, Infotische für Familien, Abendführungen).
Quelle: Die Seite https://aquazoo-duesseldorf.de/veranstaltungen lädt ihre Termine per JavaScript aus der
JSON-Schnittstelle der Website (frontend/js/event-calendar.js): /api/events/list?type=upcoming&all_websites=1 –
alle kommenden Termine in einer Antwort (Titel, Datum, Zeittext, Typ, Preis, Detail-URL, Vorschaubild).
Dieselbe Schnittstelle nutzt das Hetjens-Museum (gleiches CMS der Stadt), siehe hetjens.py.
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V2, Welle B)

robots.txt (geprüft am 25.11.2026): „User-agent: * / Disallow:“ – alles erlaubt, kein Crawl-delay. Eine Anfrage je
Lauf (mindestens 2 s Wartezeit über seite_abrufen).

Besonderheiten:
- Führungen am Evolutionsweg (Nordpark) haben als Ortsnamen „Nordpark Düsseldorf“, aber dieselbe Adresse
  (Kaiserswerther Straße 380) – sie beginnen am Museum; Ort bleibt „Aquazoo Löbbecke Museum“.
- Typ „Tagung“ (Fachtreffen, z. B. Regionaltreffen des Zoopädagogen-Verbands) ist keine Veranstaltung für Besucher
  und wird ausgelassen.
- Uhrzeit = Beginn aus dem Zeittext („11 – 13.30 Uhr“ → 11:00, „18:30-20:00“ → 18:30), sonst start_time.
- Preis: „kostenfrei“/„kostenlos“ → „kostenlos“, sonst der Preistext; ohne Angabe None (dann gilt der Museumseintritt).

Erstellt: 2026-11-25
"""
import json
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin, urlparse

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

QUELLE_NAME = "Aquazoo Löbbecke Museum"
BASIS_URL = "https://aquazoo-duesseldorf.de"
PROGRAMM_URL = "https://aquazoo-duesseldorf.de/veranstaltungen"
API_URL = "https://aquazoo-duesseldorf.de/api/events/list?type=upcoming&all_websites=1"

ORT = "Aquazoo Löbbecke Museum"
ADRESSE = "Kaiserswerther Str. 380, 40474 Düsseldorf"

WARTEZEIT = 2.0
TYPEN_AUSLASSEN = {"tagung"}

_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus|verschoben)\b", re.I)


def _beginn(zeit_text: Optional[str], start_time: Optional[str]) -> Optional[str]:
    """Beginn aus dem Zeittext („13 Uhr“, „11 – 13.30 Uhr“, „18:30-20:00“), sonst aus start_time („13:00:00“)."""
    m = re.match(r"\s*(?:ab\s*)?(\d{1,2})(?:[:.](\d{2}))?\s*(?:Uhr|-|–|$)", zeit_text or "", re.I)
    if m and int(m.group(1)) < 24:
        return f"{int(m.group(1)):02d}:{m.group(2) or '00'}"
    m = re.match(r"(\d{2}):(\d{2})", start_time or "")
    if m and m.group(0) != "00:00":
        return m.group(0)
    return None


def _preis(preis: Optional[str]) -> Optional[str]:
    if not preis or not str(preis).strip():
        return None
    text = re.sub(r"\s+", " ", str(preis)).strip()
    if re.search(r"kostenfrei|kostenlos|eintritt frei|^frei$", text, re.I):
        return "kostenlos"
    return text[:120]


def _kategorie(titel: str, typ: str) -> str:
    t = f"{titel} {typ}".lower()
    if re.search(r"kinder|famili|infotisch|ferien", t):
        return "family"
    if re.search(r"workshop|mitmach", t):
        return "community"
    return "kultur"


def _bild(e: dict) -> Optional[str]:
    bild = e.get("teaser_image") if isinstance(e.get("teaser_image"), dict) else {}
    pfad = bild.get("path")
    if not pfad:
        return None
    url = urljoin(BASIS_URL, pfad)
    host = (urlparse(url).hostname or "").lower()
    return url if host.endswith("aquazoo-duesseldorf.de") else None


def _termine_aus_api(daten: dict, heute: date, enddatum: date) -> list[dict]:
    """Antwort der Schnittstelle (dict mit „events“) → Event-Dicts im Projektformat."""
    ergebnis: list[dict] = []
    gesehen: set[tuple] = set()
    for e in (daten or {}).get("events") or []:
        try:
            if not isinstance(e, dict) or e.get("is_past"):
                continue
            titel = re.sub(r"\s+", " ", str(e.get("title") or "")).strip()
            typ = str(e.get("type") or "").strip()
            datum = str(e.get("occurrence_date") or e.get("start_date") or "")[:10]
            if not titel or not re.match(r"\d{4}-\d{2}-\d{2}$", datum):
                continue
            if typ.lower() in TYPEN_AUSLASSEN:
                logger.debug("Aquazoo: Fachtermin ausgelassen: %s (%s)", titel, typ)
                continue
            if _ABGESAGT.search(titel):
                continue
            tag = date.fromisoformat(datum)
            if tag < heute or tag > enddatum:
                continue
            uhrzeit = _beginn(e.get("time"), e.get("start_time"))
            schluessel = (titel.lower(), datum, uhrzeit)
            if schluessel in gesehen:
                continue
            gesehen.add(schluessel)
            quelle_url = e.get("url") or PROGRAMM_URL
            event = {
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ORT,
                "adresse": ADRESSE,
                "kategorie": _kategorie(titel, typ),
                "beschreibung": None,
                "preis": _preis(e.get("price")),
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": _bild(e),
                "bild_generiert": False,
                "status": "neu",
                "ticket_url": None,
            }
            ende = str(e.get("occurrence_end_date") or e.get("end_date") or "")[:10]
            if re.match(r"\d{4}-\d{2}-\d{2}$", ende) and ende > datum:
                event["datum_bis"] = ende
            ergebnis.append(event)
        except Exception as fehler:
            logger.warning("Aquazoo: Eintrag übersprungen (%s)", fehler)
    return ergebnis


def scrape() -> list[dict]:
    """Scrapt die kommenden Veranstaltungen des Aquazoo Löbbecke Museum."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        text = seite_abrufen(API_URL, logger, wartezeit=WARTEZEIT)
        if text is None:
            logger.error("Scraper %s: Termin-Schnittstelle nicht erreichbar", QUELLE_NAME)
            return []
        try:
            daten = json.loads(text)
        except json.JSONDecodeError:
            logger.error("Scraper %s: keine JSON-Antwort von %s", QUELLE_NAME, API_URL)
            return []
        events = _termine_aus_api(daten, heute, enddatum)
        if not events:
            logger.warning("Scraper %s: 0 Termine bei erreichbarer Schnittstelle (%d Rohdaten) – "
                           "Seitenstruktur geändert?", QUELLE_NAME, len(daten.get("events") or []))
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
