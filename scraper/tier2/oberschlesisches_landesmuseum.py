"""
oberschlesisches_landesmuseum.py – DiesDasDüsseldorf
Scraper für das Oberschlesische Landesmuseum in Ratingen (Hösel).
Quelle: iCal-Export des WordPress-Plugins „Modern Events Calendar“ (MEC): https://oberschlesisches-landesmuseum.de/?mec-ical-feed=1
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V2, Welle B).

robots.txt (geprüft am 25.11.2026): „User-agent: * / Disallow: /wp-admin/, /wp-content/uploads/wc-logs/ …,
/*?add-to-cart=“ – der iCal-Export ist erlaubt, kein Crawl-delay. Eine Anfrage je Lauf (der Export enthält alle
Termine, auch vergangene; rund 600 KB).

Warum iCal: Die Website nutzt nicht „The Events Calendar“ (kein Baustein wp_tribe), sondern MEC. Die Liste
„Alle Veranstaltungen“ zeigt nur 8 Termine und lädt den Rest per „Weitere laden“ nach; der RSS-Feed nur 10. Der
iCal-Export enthält alle Termine mit Uhrzeit, Kategorie (CATEGORIES), Detailseite (URL) und Bild (ATTACH). Vor dem
Kalender stehen PHP-Warnungen des Plugins im Text – der Baustein scraper/utils/ical.py überliest sie.

- Termine außer Haus („#oslmontour …“, z. B. Keynote in der Galerie Wedding in Berlin) werden ausgelassen.
- Reine Ausstellungs-Einträge (nur Kategorie Ausstellung/Wanderausstellung) sind keine Einzeltermine und entfallen.
- Kategorie: Familie/Kinder → family, Führung → kultur, Werkstatt/Workshop → community, Konzert → musik,
  Frühstück/Brunch → food, sonst (Lesungen, Gesprächskreise, Eröffnungen) kultur.
- Preis steht nicht im iCal-Export (nur in der Liste/im RSS) → None. Ticket-Link nennt das Haus nicht → keiner.

Erstellt: 2026-11-25
"""
import json
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urlparse

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ical import termine_aus_ics

logger = logging.getLogger(__name__)

QUELLE_NAME = "Oberschlesisches Landesmuseum"
BASIS_URL = "https://oberschlesisches-landesmuseum.de"
ICAL_URL = "https://oberschlesisches-landesmuseum.de/?mec-ical-feed=1"
PROGRAMM_URL = "https://oberschlesisches-landesmuseum.de/startseite-oslm/alle-veranstaltungen/"
ORT = "Oberschlesisches Landesmuseum"
ADRESSE = "Bahnhofstraße 62, 40883 Ratingen"
WARTEZEIT = 2.0

_AUSWAERTS = re.compile(r"#?oslm\s*on\s*tour|\bon tour\b", re.I)
_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus|verschoben)\b", re.I)
_NUR_AUSSTELLUNG = {"ausstellung", "wanderausstellung"}


def _entfalten(text: str) -> list[str]:
    zeilen: list[str] = []
    for zeile in (text or "").replace("\r\n", "\n").split("\n"):
        if zeile.startswith((" ", "\t")) and zeilen:
            zeilen[-1] += zeile[1:]
        else:
            zeilen.append(zeile)
    return zeilen


def _zusatz_je_url(text: str) -> dict[str, tuple[list[str], Optional[str]]]:
    """URL der Detailseite → (Kategorien, Bild-URL) aus den VEVENT-Blöcken (der Baustein liefert beides nicht)."""
    ergebnis: dict[str, tuple[list[str], Optional[str]]] = {}
    aktuell: Optional[dict] = None
    for zeile in _entfalten(text):
        if zeile == "BEGIN:VEVENT":
            aktuell = {}
        elif zeile == "END:VEVENT" and aktuell is not None:
            if aktuell.get("URL"):
                kategorien = [k.strip() for k in (aktuell.get("CATEGORIES") or "").split(",") if k.strip()]
                ergebnis[aktuell["URL"]] = (kategorien, aktuell.get("ATTACH"))
            aktuell = None
        elif aktuell is not None and ":" in zeile:
            kopf, wert = zeile.split(":", 1)
            name = kopf.split(";", 1)[0].upper()
            if name in ("URL", "CATEGORIES", "ATTACH") and name not in aktuell:
                aktuell[name] = wert.replace("\\,", ",").strip()
    return ergebnis


def _kategorie(titel: str) -> str:
    t = titel.lower()
    if re.search(r"famili|für kinder|kinderführung|kinderworkshop", t):
        return "family"
    if "führung" in t:  # „Führung … mit Weihnachtspost-Workshop“ bleibt eine Führung
        return "kultur"
    if re.search(r"werkstatt|workshop", t):
        return "community"
    if "konzert" in t:
        return "musik"
    if re.search(r"frühstück|brunch", t):
        return "food"
    return "kultur"


def _eigenes_bild(url: Optional[str]) -> Optional[str]:
    """Nur Bilder von der Website des Museums übernehmen."""
    if not url or not url.startswith(("http://", "https://")):
        return None
    host = urlparse(url).netloc.lower()
    return url if host == "oberschlesisches-landesmuseum.de" or host.endswith(".oberschlesisches-landesmuseum.de") \
        else None


def _termine_aus_ics(text: str, heute: date, enddatum: date) -> list[dict]:
    """iCal-Export → Event-Dicts im Projektformat (nur Termine im Haus zwischen heute und enddatum)."""
    zusatz = _zusatz_je_url(text)
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for roh in termine_aus_ics(text, heute, enddatum):
        titel = re.sub(r"\s+", " ", roh.get("titel") or "").strip()
        if not titel:
            continue
        if _AUSWAERTS.search(titel):
            logger.debug("OSLM: Termin außer Haus ausgelassen: %s", titel)
            continue
        if _ABGESAGT.search(titel):
            logger.debug("OSLM: abgesagt, ausgelassen: %s", titel)
            continue
        url = roh.get("url") or ""
        kategorien, bild = zusatz.get(url, ([], None))
        if kategorien and {k.lower() for k in kategorien} <= _NUR_AUSSTELLUNG:
            logger.debug("OSLM: Ausstellungseintrag ausgelassen: %s", titel)
            continue
        uhrzeit = roh.get("uhrzeit")
        if uhrzeit == "00:00":
            uhrzeit = None
        schluessel = (titel.lower(), roh["start"], uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        event = {
            "titel": titel,
            "datum": roh["start"],
            "uhrzeit": uhrzeit,
            "ort": ORT,
            "adresse": ADRESSE,
            "kategorie": _kategorie(titel),
            "beschreibung": None,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": url if url.startswith(BASIS_URL) else PROGRAMM_URL,
            "bild_url": _eigenes_bild(bild),
            "bild_generiert": False,
            "status": "neu",
        }
        if roh.get("ende") and roh["ende"] > roh["start"]:
            event["datum_bis"] = roh["ende"]
        events.append(event)
    return events


def scrape() -> list[dict]:
    """Scrapt die Veranstaltungen des Oberschlesischen Landesmuseums (iCal-Export)."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        text = seite_abrufen(ICAL_URL, logger, wartezeit=WARTEZEIT)
        if text is None:
            logger.error("Scraper %s: iCal-Export nicht erreichbar", QUELLE_NAME)
            return []
        if "BEGIN:VCALENDAR" not in text:
            logger.warning("Scraper %s: Antwort ist kein iCal-Kalender – Seitenstruktur geändert?", QUELLE_NAME)
            return []
        events = _termine_aus_ics(text, heute, enddatum)
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
