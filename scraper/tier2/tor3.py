"""
tor3.py – DiesDasDüsseldorf
Scraper für den Club Tor 3 (Langenberger Str. 9).
URL: https://www.tor3-club.com/home-2 (http://tor3-club.com/home-2 leitet dorthin weiter)

robots.txt geprüft am 2026-11-24: „User-agent: * Allow: /“, gesperrt nur „*?lightbox=“ → /home-2 erlaubt.
Crawl-delay nur für dotbot/AhrefsBot (10 s), nicht für uns.

Methode: Wix-Website. Die Termine stehen als CMS-Sammlung „Events“ im JSON-Block <script id="wix-warmup-data">
(appsWarmupData → dataBinding → dataStore → recordsByCollectionId → Events; Felder title_fld, datum, description_fld,
image_fld, link-events-1-title_fld, ticketlink). Sortierung der Sammlung: datum absteigend – die neuesten
(kommenden) Termine sind also immer dabei. Die Uhrzeit steht nur im Beschreibungstext („Start: 23:00 Uhr“).
Ein Abruf je Lauf.

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1, Welle A)
"""
import html as html_lib
import json
import logging
import re
from datetime import date
from typing import Any, Optional
from urllib.parse import urljoin

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASIS_URL = "https://www.tor3-club.com"
PROGRAMM_URL = "https://www.tor3-club.com/home-2"
QUELLE_NAME = "Tor 3"
ORT = "Tor 3"
ADRESSE = "Langenberger Str. 9, 40233 Düsseldorf"

_WARMUP = re.compile(r'<script[^>]*id="wix-warmup-data"[^>]*>(.*?)</script>', re.S)
_WIX_BILD = re.compile(r"^wix:image://v1/([^/#]+)")
_ABGESAGT = re.compile(r"(?i)\b(abgesagt|entfällt|cancelled|canceled|verschoben)\b")
_MUSIK = re.compile(r"(?i)\blive\b|konzert|\btour\b|on stage")
_DATING = re.compile(r"(?i)speed ?dating|matching night|singles?[- ]party|single-?abend")
# Reihenfolge = Vorrang: Beginn (auch „Konzertbeginn“) vor Start vor „ab“ vor Einlass
_ZEIT_SCHLUESSEL = (r"beginn", r"\bstart", r"\bab", r"einlass", r"\bdoors?")
_ZEITSPANNE = re.compile(r"(?<![\d.])(\d{1,2})[:.](\d{2})\s*[–-]\s*\d{1,2}[:.]\d{2}\s*uhr", re.I)


def _sammlung(html: str) -> list[dict]:
    """Datensätze der Wix-Sammlung „Events“ aus dem warmup-JSON; leere Liste, wenn nicht vorhanden."""
    treffer = _WARMUP.search(html or "")
    if not treffer:
        return []
    try:
        daten = json.loads(treffer.group(1))
    except json.JSONDecodeError:
        return []

    def suchen(obj: Any) -> Optional[Any]:
        if isinstance(obj, dict):
            if isinstance(obj.get("recordsByCollectionId"), dict) and "Events" in obj["recordsByCollectionId"]:
                return obj["recordsByCollectionId"]["Events"]
            for wert in obj.values():
                gefunden = suchen(wert)
                if gefunden is not None:
                    return gefunden
        return None

    events = suchen(daten)
    if isinstance(events, dict):
        events = list(events.values())
    return [e for e in events or [] if isinstance(e, dict)]


def _klartext(roh: str) -> str:
    text = re.sub(r"<br\s*/?>|</(p|h\d|div|li)>", "\n", roh or "", flags=re.I)
    return html_lib.unescape(re.sub(r"<[^>]+>", " ", text))


def _uhrzeit(beschreibung: str) -> Optional[str]:
    """Beginn aus dem Beschreibungstext („Start: 23:00 Uhr“, „ab 22.00“, „Einlass 21:00“, „20:00–06:00 Uhr“)."""
    text = _klartext(beschreibung)
    for schluessel in _ZEIT_SCHLUESSEL:
        muster = re.compile(rf"(?i){schluessel}\b\W{{0,8}}(\d{{1,2}})(?:[:.](\d{{2}}))?(\s*uhr)?")
        for treffer in muster.finditer(text):
            stunde, minute, uhr = treffer.group(1), treffer.group(2), treffer.group(3)
            if (minute or uhr) and 0 <= int(stunde) <= 23:
                return f"{int(stunde):02d}:{minute or '00'}"
    spanne = _ZEITSPANNE.search(text)   # „| 20:00–06:00 Uhr“
    if spanne and 0 <= int(spanne.group(1)) <= 23:
        return f"{int(spanne.group(1)):02d}:{spanne.group(2)}"
    return None


def _bild(feld: Any) -> Optional[str]:
    """wix:image://v1/<id>/… → Bild-URL der Website (static.wixstatic.com)."""
    treffer = _WIX_BILD.match(str(feld or ""))
    return f"https://static.wixstatic.com/media/{treffer.group(1)}" if treffer else None


def _kategorie(titel: str, ticketlink: str) -> str:
    if _DATING.search(f"{titel} {ticketlink}"):
        return "dating"
    if _MUSIK.search(titel):
        return "musik"
    return "nightlife"


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Wandelt die Wix-Sammlung in Events um (heute bis enddatum, ohne Doppelte)."""
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for satz in _sammlung(html):
        if str(satz.get("_publishStatus") or "PUBLISHED").upper() != "PUBLISHED":
            continue
        titel = re.sub(r"\s+", " ", html_lib.unescape(str(satz.get("title_fld") or ""))).strip()
        treffer = re.match(r"(\d{4}-\d{2}-\d{2})", str(satz.get("datum") or ""))
        if not titel or not treffer:
            continue
        datum = treffer.group(1)
        if not (heute <= date.fromisoformat(datum) <= enddatum) or _ABGESAGT.search(titel):
            continue
        uhrzeit = _uhrzeit(str(satz.get("description_fld") or ""))
        schluessel = (titel.lower(), datum, uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        pfad = str(satz.get("link-events-1-title_fld") or "")
        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT,
            "adresse": ADRESSE,
            "kategorie": _kategorie(titel, str(satz.get("ticketlink") or "")),
            "beschreibung": None,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": urljoin(BASIS_URL, pfad) if pfad.startswith("/") else PROGRAMM_URL,
            "bild_url": _bild(satz.get("image_fld")),
            "bild_generiert": False,
            "status": "neu",
        })
    return sorted(events, key=lambda e: (e["datum"], e["uhrzeit"] or ""))


def scrape() -> list[dict]:
    """Scrapt die Events des Tor 3. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    try:
        html = seite_abrufen(PROGRAMM_URL, logger, wartezeit=2.0)
        if html is None:
            logger.error("%s: Programmseite nicht erreichbar", QUELLE_NAME)
            return []
        if not _sammlung(html):
            logger.warning("%s: keine Event-Sammlung im Wix-JSON – Seitenstruktur geändert?", QUELLE_NAME)
            return []
        events = _termine_aus_html(html, heute, enddatum)
        if not events:
            # Die Sammlung ist da, nur ohne kommende Termine – beim Club nicht ungewöhnlich
            logger.warning("%s: 0 kommende Termine gefunden – Seitenstruktur geändert?", QUELLE_NAME)
        logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
        return events
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
