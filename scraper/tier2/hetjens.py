"""
hetjens.py – DiesDasDüsseldorf
Scraper für das HETJENS – Deutsches Keramikmuseum (Kuratorenführungen, Eröffnungen, Workshops, Kurse der
Töpferwerkstatt).
Quelle: Die Programmseite https://www.hetjensmuseum.de/programm lädt ihre Termine per JavaScript aus der
JSON-Schnittstelle der Website (gleiches CMS wie das Aquazoo, frontend/js/event-calendar.js):
/api/events/list?type=upcoming&all_websites=1 – alle kommenden Termine, Serien schon in Einzeltermine aufgelöst
(occurrence_date).
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V2, Welle B)

robots.txt (geprüft am 25.11.2026): „User-agent: * / Disallow:“ – alles erlaubt, kein Crawl-delay. Eine Anfrage je
Lauf (mindestens 2 s Wartezeit über seite_abrufen).

Besonderheiten:
- Das „Suchspiel für Familien“ („Mit der Maus durchs Haus“, jeden Sonntag ab 12 Uhr, zwei Jahre im Voraus) ist ein
  Dauerangebot während der Öffnungszeit, kein Termin – Typ „Suchspiel …“ wird ausgelassen.
- Kurse der Töpferwerkstatt (Ortsname „Töpferwerkstatt“, Citadellstraße/Schulstraße) gehören zum Museum; Ort bleibt
  „Hetjens - Deutsches Keramikmuseum“ (Schreibweise der Ortstabelle), Adresse Schulstraße 4.
- Uhrzeit = Beginn aus dem Zeittext („18:30 - 20:30 Uhr“, „Ab 12:00 Uhr“) – start_time ist bei manchen Einträgen
  das Ende („15:30-17:30 Uhr“ mit start_time 17:30) und dient nur als Ersatz.
- Preis: „kostenlos …“ → „kostenlos“, sonst der Preistext („160 Euro, 5 Termine (AUSGEBUCHT)“ bleibt stehen –
  ausgebuchte Termine behalten wir).

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

QUELLE_NAME = "Hetjens-Museum"
BASIS_URL = "https://www.hetjensmuseum.de"
PROGRAMM_URL = "https://www.hetjensmuseum.de/programm"
API_URL = "https://www.hetjensmuseum.de/api/events/list?type=upcoming&all_websites=1"

ORT = "Hetjens - Deutsches Keramikmuseum"
ADRESSE = "Schulstraße 4, 40213 Düsseldorf"

WARTEZEIT = 2.0
# Typen ohne echten Termin (Dauerangebot während der Öffnungszeit)
_TYP_AUSLASSEN = re.compile(r"suchspiel", re.I)
_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus|verschoben)\b", re.I)


def _beginn(zeit_text: Optional[str], start_time: Optional[str]) -> Optional[str]:
    """Beginn aus dem Zeittext („18:30 Uhr“, „Ab 12:00 Uhr“, „18:30 - 20:30 Uhr“), sonst aus start_time."""
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
    if re.match(r"(kostenlos|kostenfrei|eintritt frei|frei\b)", text, re.I):
        return "kostenlos"
    return text[:120]


def _kategorie(titel: str, typ: str) -> str:
    """Kinder/Familien → family, Workshops/Kurse → community, sonst (Führung, Eröffnung, Vortrag) kultur."""
    t = f"{titel} {typ}".lower()
    if re.search(r"kinder|famili", t):
        return "family"
    if re.search(r"workshop|kurs|zeichnen|werkstatt", t):
        return "community"
    return "kultur"


def _bild(e: dict) -> Optional[str]:
    bild = e.get("teaser_image") if isinstance(e.get("teaser_image"), dict) else {}
    pfad = bild.get("path")
    if not pfad:
        return None
    url = urljoin(BASIS_URL, pfad)
    host = (urlparse(url).hostname or "").lower()
    return url if host.endswith("hetjensmuseum.de") else None


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
            if _TYP_AUSLASSEN.search(typ):
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
                "quelle_url": e.get("url") or PROGRAMM_URL,
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
            logger.warning("Hetjens: Eintrag übersprungen (%s)", fehler)
    return ergebnis


def scrape() -> list[dict]:
    """Scrapt die kommenden Veranstaltungen des Hetjens – Deutsches Keramikmuseum."""
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
