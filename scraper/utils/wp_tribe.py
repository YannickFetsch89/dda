"""
wp_tribe.py – DiesDasDüsseldorf
Baustein: WordPress-Plugin „The Events Calendar“ (Tribe) über seine REST-API lesen (Plan docs/plan-quellen-ausbau-
2026-11-23.md, 3.3, Schritt V1). Beispiel: Insel Hombroich (/wp-json/tribe/events/v1/events).

events_holen(basis_url, von, bis, logger) liefert Rohtermine wie scraper/utils/jsonld_events.py:
    {"titel", "start", "uhrzeit", "ende", "ort", "adresse", "bild_url", "preis", "url", "beschreibung", "abgesagt"}
Seitenweise (per_page 50, höchstens MAX_SEITEN), mindestens 2 s zwischen den Anfragen (seite_abrufen), Abbruch der
Schleife bei einem Fehler mit den bis dahin gelesenen Terminen.
"""
import html as html_lib
import json
import logging
import re
from datetime import date
from typing import Optional

from scraper.utils.http_client import seite_abrufen

PFAD = "/wp-json/tribe/events/v1/events"
PRO_SEITE = 50
MAX_SEITEN = 20


def _text(wert: Optional[str]) -> Optional[str]:
    if not wert:
        return None
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_lib.unescape(wert))).strip() or None


def termin_aus_tribe(e: dict) -> Optional[dict]:
    """Ein Eintrag der Tribe-API → Rohtermin (None ohne Titel oder Datum)."""
    start = str(e.get("start_date") or "")
    if not re.match(r"\d{4}-\d{2}-\d{2}", start) or not _text(e.get("title")):
        return None
    venue = e.get("venue") if isinstance(e.get("venue"), dict) else {}
    adresse = ", ".join(x for x in (
        (venue.get("address") or "").strip(),
        " ".join(y for y in ((venue.get("zip") or "").strip(), (venue.get("city") or "").strip()) if y),
    ) if x) or None
    bild = e.get("image") if isinstance(e.get("image"), dict) else {}
    kosten = _text(e.get("cost"))
    return {
        "titel": _text(e.get("title")),
        "start": start[:10],
        "uhrzeit": None if e.get("all_day") else (start[11:16] or None),
        "ende": str(e.get("end_date") or "")[:10] or None,
        "ort": _text(venue.get("venue")),
        "adresse": adresse,
        "bild_url": bild.get("url"),
        "preis": "kostenlos" if kosten and re.fullmatch(r"(?i)(0|frei|kostenlos|free|eintritt frei)( ?€)?", kosten) else kosten,
        "url": e.get("url"),
        "beschreibung": _text(e.get("excerpt")) or _text(e.get("description")),
        "abgesagt": False,
    }


def events_holen(basis_url: str, von: date, bis: date, logger: Optional[logging.Logger] = None,
                 wartezeit: float = 2.0) -> list[dict]:
    """Alle Termine zwischen von und bis über die Tribe-API von basis_url (z. B. "https://www.inselhombroich.de")."""
    log = logger or logging.getLogger(__name__)
    termine: list[dict] = []
    for seite in range(1, MAX_SEITEN + 1):
        url = (f"{basis_url.rstrip('/')}{PFAD}?start_date={von.isoformat()}&end_date={bis.isoformat()}"
               f"&per_page={PRO_SEITE}&page={seite}")
        text = seite_abrufen(url, log, wartezeit=wartezeit)
        if text is None:
            break
        try:
            daten = json.loads(text)
        except json.JSONDecodeError:
            log.warning("Tribe-API: keine JSON-Antwort von %s", url)
            break
        termine.extend(t for e in daten.get("events") or [] if (t := termin_aus_tribe(e)))
        if seite >= int(daten.get("total_pages") or 1):
            break
    return termine
