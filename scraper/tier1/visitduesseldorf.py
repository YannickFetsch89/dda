"""
visitduesseldorf.py – DiesDasDüsseldorf
Veranstaltungskalender von Visit Düsseldorf – komplett aus den Eventseiten der Sitemap (Toubiz-JSON).

Seit dem Quellen-Ausbau, Schritt V0 (Plan docs/plan-quellen-ausbau-2026-11-23.md, 3.2): Bis dahin las ein
Playwright-Scraper nur die erste Seite des Kalenders (≈ 10 Events je Lauf). Jede /event/-Seite enthält aber das
komplette Event als JSON (Kategorie, Ort mit Adresse, alle Termine). Den Abruf und Zwischenspeicher teilt sich dieses
Modul mit dem Führungs-Scraper (visitduesseldorf_fuehrungen.seiten_laden): geänderte Seiten werden je Lauf höchstens
einmal geladen. Führungen liefert weiter der Führungs-Scraper, hier bleiben sie außen vor.

Rang 3 (offizielles Portal, pipeline/quellen_rang.py): Liefert ein Haus dasselbe Event, wird das Haus Hauptquelle.
Zeitraum 120 Tage (config.VORSCHAU_TAGE). Beschreibung bleibt leer – den Text schreibt Schritt 3b aus der Eventseite
in eigenen Worten (pipeline/beschreibung_quellen.py).

robots.txt: /event/ und /sitemap.xml sind erlaubt (gesperrt sind nur /duesseldorf/offer, Warenkorb, /neos/).
Erstellt: 2026-02-24, neu gebaut 2026-11-24
"""
import logging
from datetime import date

from config import vorschau_ende
from scraper.tier1.visitduesseldorf_fuehrungen import (
    _preis,
    _treffpunkt,
    seiten_laden,
)

logger = logging.getLogger(__name__)

QUELLE_NAME = "VisitDüsseldorf"

# Toubiz-Kategorien (rootlineNames und secondaryCategories) → DDA-Kategorie; erste passende gewinnt
KATEGORIE_MAP = [
    ("kinder", "family"), ("familie", "family"),
    ("party", "nightlife"), ("club", "nightlife"), ("disco", "nightlife"),
    ("konzert", "musik"), ("musik", "musik"), ("jazz", "musik"), ("festival", "musik"),
    ("musical", "kultur"), ("oper", "kultur"), ("ballett", "kultur"), ("tanz", "kultur"), ("theater", "kultur"),
    ("aufführung", "kultur"), ("kabarett", "kultur"), ("comedy", "kultur"), ("lesung", "kultur"),
    ("vortrag", "kultur"), ("ausstellung", "kultur"), ("film", "kultur"), ("kino", "kultur"),
    ("sport", "sport"), ("lauf", "sport"),
    ("markt", "food"), ("kulinar", "food"), ("food", "food"), ("genuss", "food"),
    ("natur", "outdoor"), ("garten", "outdoor"),
    ("workshop", "community"), ("seminar", "community"), ("kurs", "community"), ("messe", "community"),
]
# Diese Kategorien gehören zum Führungs-Scraper bzw. zu den Museen (siehe visitduesseldorf_fuehrungen.py)
FUEHRUNG = ("führung", "stadtrundgang", "stadtrundfahrt", "rundfahrt")
# Buchbare Angebote mit täglichen Terminen (Rhein-Schifffahrt, Hop-on-Hop-off …) sind keine Events – sie würden den
# Kalender mit Dutzenden Terminen je Angebot füllen (Probelauf 24.11.: 82 Termine „Panoramafahrt auf dem Rhein“)
AUSSCHLUSS = ("aktivität", "schifffahrt", "bustour")


def _kategorien(event: dict) -> list[str]:
    namen = [n for n in (event.get("category") or {}).get("rootlineNames") or [] if n and n.lower() != "event"]
    namen += [k.get("name") or "" for k in event.get("secondaryCategories") or []]
    return [n.lower() for n in namen if n]


def kategorie_zuordnen(event: dict) -> str:
    """DDA-Kategorie aus den Toubiz-Kategorien; ohne Treffer „sonstiges“ (die KI-Kategorisierung prüft nach)."""
    text = " ".join(_kategorien(event))
    for wort, kategorie in KATEGORIE_MAP:
        if wort in text:
            return kategorie
    return "sonstiges"


def ist_fuehrung(event: dict) -> bool:
    """Führung, Stadt-/Museumsführung, Rundgang – aber nicht „Aufführung“/„Uraufführung“ (Theater)."""
    return any(w in k and "aufführung" not in k for k in _kategorien(event) for w in FUEHRUNG)


def events_aus_cache(cache: dict, heute: date, enddatum: date) -> list[dict]:
    """Alle Termine der Kalender-Events (ohne Führungen) zwischen heute und enddatum, je Titel/Tag/Uhrzeit einmal."""
    roh: list[tuple[str, dict, dict]] = []
    for url, eintrag in cache.items():
        event = eintrag.get("roh")
        if not event or event.get("canceled") or event.get("trashed") or not (event.get("name") or "").strip():
            continue
        if ist_fuehrung(event) or any(w in k for k in _kategorien(event) for w in AUSSCHLUSS):
            continue
        for d in event.get("datesCache") or []:
            if not d.get("date") or not d.get("active", True) or d.get("isCancelled") or d.get("closed"):
                continue
            try:
                tag = date.fromisoformat(d["date"])
            except (TypeError, ValueError):
                continue
            if heute <= tag <= enddatum:
                roh.append((url, event, d))

    gesehen: set = set()
    events = []
    for url, event, d in sorted(roh, key=lambda r: (r[2]["date"], r[2].get("startAt") or "")):
        titel = event["name"].strip()
        uhrzeit = (d.get("startAt") or "")[:5] or None
        schluessel = (titel.lower(), d["date"], uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        ort, adresse = _treffpunkt(event)
        events.append({
            "titel": titel,
            "datum": d["date"],
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": adresse,
            "kategorie": kategorie_zuordnen(event),
            "beschreibung": None,
            "preis": _preis(event),
            "quelle_name": QUELLE_NAME,
            "quelle_url": url,
            "bild_url": (event.get("mainImage") or {}).get("url"),
            "bild_generiert": False,
            "post_typ": "feed",
            "instagram_caption": None,
            "instagram_location_id": None,
            "status": "neu",
        })
    return events


async def scrape() -> list[dict]:
    """Termine aus dem Visit-Düsseldorf-Kalender bis zum Zeitraum der Quelle (120 Tage)."""
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (Eventseiten der Sitemap, bis %s)", QUELLE_NAME, enddatum.isoformat())
    cache = await seiten_laden()
    events = events_aus_cache(cache, heute, enddatum)
    logger.info("Scraper %s fertig: %d Termine aus %d Eventseiten", QUELLE_NAME, len(events), len(cache))
    return events


if __name__ == "__main__":
    import asyncio
    import json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ergebnis = asyncio.run(scrape())
    print(json.dumps(ergebnis[:4], ensure_ascii=False, indent=2))
    print(f"… insgesamt {len(ergebnis)} Termine")
