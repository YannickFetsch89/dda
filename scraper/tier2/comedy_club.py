"""
comedy_club.py – DiesDasDüsseldorf
Scraper für den Comedy Club Düsseldorf (Oststraße 147).
URL: https://comedyclubduesseldorf.de/shows

robots.txt geprüft am 2026-11-24: keine robots.txt vorhanden (HTTP 404) → Abruf erlaubt.

Methode: Die Seite ist eine Next.js-App. Alle Shows stehen als JSON im Seitenquelltext (self.__next_f.push-Blöcke,
Schlüssel "uniqueShows": je Termin id, title, duration ["Start", "Ende"], location, ticket_details, imageUrl).
Ein Abruf je Lauf reicht. Shows an anderen Adressen (z. B. Plange Mühle, Erkrather Str.) werden übersprungen,
weil der Ort sonst falsch wäre.

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1, Welle A)
"""
import json
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import quote

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASIS_URL = "https://comedyclubduesseldorf.de"
PROGRAMM_URL = "https://comedyclubduesseldorf.de/shows"
QUELLE_NAME = "Comedy Club Düsseldorf"
ORT = "Comedy Club Düsseldorf"
ADRESSE = "Oststraße 147, 40210 Düsseldorf"
KATEGORIE = "kultur"
# Bilder liegen im Supabase-Speicher der Website; ausgeliefert werden sie über den Bild-Dienst der Website selbst.
SUPABASE_STANDARD = "https://yddipficdegaegdtsikf.supabase.co"

_PUSH = re.compile(r"self\.__next_f\.push\(\[1,(\".*?\")\]\)</script>", re.S)
_SUPABASE = re.compile(r"https(?:%3A%2F%2F|://)([a-z0-9]+)\.supabase\.co", re.I)
_ABGESAGT = re.compile(r"(?i)\b(abgesagt|entfällt|cancelled|canceled)\b")


def _next_daten(html: str) -> str:
    """Setzt die Next.js-Datenblöcke (JSON-Strings) zu einem Text zusammen."""
    teile = []
    for roh in _PUSH.findall(html or ""):
        try:
            teile.append(json.loads(roh))
        except json.JSONDecodeError:
            continue
    return "".join(teile)


def _shows(html: str) -> list[dict]:
    """Liest das Array "uniqueShows" aus dem Seitenquelltext; ohne Treffer leere Liste."""
    text = _next_daten(html)
    pos = text.find('"uniqueShows":')
    if pos < 0:
        return []
    try:
        daten, _ = json.JSONDecoder().raw_decode(text, pos + len('"uniqueShows":'))
    except json.JSONDecodeError:
        return []
    return [s for s in daten if isinstance(s, dict)] if isinstance(daten, list) else []


def _start(show: dict) -> tuple[Optional[str], Optional[str]]:
    """("YYYY-MM-DD", "HH:MM" | None) aus duration '["2026-11-25 20:00:00","2026-11-25 22:00:00"]'."""
    dauer = show.get("duration")
    try:
        werte = json.loads(dauer) if isinstance(dauer, str) else dauer
        anfang = str(werte[0])
    except (json.JSONDecodeError, TypeError, IndexError, KeyError):
        anfang = str(dauer or "")
    treffer = re.search(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}):(\d{2}))?", anfang)
    if not treffer:
        return None, None
    uhrzeit = f"{treffer.group(2)}:{treffer.group(3)}" if treffer.group(2) else None
    return treffer.group(1), (uhrzeit if uhrzeit != "00:00" else None)


def _preis(show: dict) -> Optional[str]:
    """Kleinster Preis der aktiven Ticketarten als Text („ab 14,90 €“)."""
    werte = []
    for t in show.get("ticket_details") or []:
        if not isinstance(t, dict) or t.get("active") is False:
            continue
        for feld in ("min_price", "price"):
            try:
                if t.get(feld) is not None:
                    werte.append(float(t[feld]))
            except (TypeError, ValueError):
                pass
    if not werte:
        return None
    kleinster = min(werte)
    if kleinster == 0:
        return "kostenlos"
    betrag = f"{kleinster:.2f}".replace(".", ",").replace(",00", "")
    return f"ab {betrag} €"


def _bild(show: dict, supabase_basis: str) -> Optional[str]:
    """Bild über den Bild-Dienst der Website (gleiche Adresse wie auf der Seite, Breite 1080)."""
    pfad = str(show.get("imageUrl") or "").strip().lstrip("/")
    if not pfad:
        return None
    original = f"{supabase_basis}/storage/v1/object/public/{pfad}"
    return f"{BASIS_URL}/_next/image?url={quote(original, safe='')}&w=1080&q=75"


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Wandelt die Programmseite in Events um (nur Oststraße, heute bis enddatum, ohne Doppelte)."""
    treffer = _SUPABASE.search(html or "")
    supabase_basis = f"https://{treffer.group(1)}.supabase.co" if treffer else SUPABASE_STANDARD

    events: list[dict] = []
    gesehen: set[tuple] = set()
    for show in _shows(html):
        titel = re.sub(r"\s+", " ", str(show.get("title") or "")).strip()
        datum, uhrzeit = _start(show)
        if not titel or not datum:
            continue
        if not (heute <= date.fromisoformat(datum) <= enddatum):
            continue
        if "oststr" not in str(show.get("location") or "oststraße").lower():
            logger.debug("Comedy Club: Show an anderer Adresse übersprungen: %s (%s)", titel, show.get("location"))
            continue
        if _ABGESAGT.search(titel):
            continue
        schluessel = (titel.lower(), datum, uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        show_id = show.get("id") or show.get("eventId")
        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT,
            "adresse": ADRESSE,
            "kategorie": KATEGORIE,
            "beschreibung": None,
            "preis": _preis(show),
            "quelle_name": QUELLE_NAME,
            "quelle_url": f"{PROGRAMM_URL}/{show_id}" if show_id else PROGRAMM_URL,
            "bild_url": _bild(show, supabase_basis),
            "bild_generiert": False,
            "status": "neu",
        })
    return events


def scrape() -> list[dict]:
    """Scrapt die Shows des Comedy Club Düsseldorf. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    try:
        html = seite_abrufen(PROGRAMM_URL, logger, wartezeit=2.0)
        if html is None:
            logger.error("%s: Programmseite nicht erreichbar", QUELLE_NAME)
            return []
        events = _termine_aus_html(html, heute, enddatum)
        if not events:
            logger.warning("%s: 0 Termine gefunden – Seitenstruktur geändert?", QUELLE_NAME)
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
