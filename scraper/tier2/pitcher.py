"""
pitcher.py – DiesDasDüsseldorf
Scraper für das Pitcher – Rock'n'Roll Headquarter Düsseldorf.

Hintergrund (Stand 2026-11-04):
Die alte Domain pitcher.de zeigt nur noch eine IONOS-Parkingseite
(HTTPS: TLS-Fehler, HTTP: 404 + Sedo-Parking). Der Club ist auf
https://pitcher29.com umgezogen (WordPress mit dem Ticket-Plugin
"EventFlow Pro"). Die Veranstaltungsseite rendert ihre Liste per
JavaScript aus einer öffentlichen WP-REST-Route.

Strategie:
1. Öffentliche EventFlow-REST-API:
   https://pitcher29.com/wp-json/eventflow/v1/public/events
   (liefert nur kommende Events, paginiert, sortiert nach Startdatum)
   Kein Playwright nötig. robots.txt sperrt nur /wp-admin/.

URL: https://pitcher29.com
Adresse: Oberbilker Allee 29, 40215 Düsseldorf
Erstellt: 2026-03-05
Überarbeitet: 2026-11-04 (Umzug auf pitcher29.com, REST-API statt HTML)
"""
import json
import logging
import re
from datetime import date, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://pitcher29.com"
LISTE_URL = "https://pitcher29.com/veranstaltungen-2/"
API_URL = "https://pitcher29.com/wp-json/eventflow/v1/public/events"
QUELLE_NAME = "Pitcher Rock HQ"
ORT_STANDARD = "Pitcher Rock HQ"
ADRESSE_STANDARD = "Oberbilker Allee 29, 40215 Düsseldorf"

SEITENGROESSE = 100
MAX_SEITEN = 5

# Reihenfolge ist relevant: spezifische Formate vor allgemeinen Musik-Begriffen,
# damit z.B. "Musikkneipenquiz (mit Liveband)" als community erkannt wird.
KATEGORIE_MAPPING: dict[str, str] = {
    "poetry slam": "kultur",
    "comedy": "kultur",
    "lesung": "kultur",
    "impro": "kultur",
    "quiz": "community",
    "karaoke": "nightlife",
    "party": "nightlife",
    "dj": "nightlife",
    "80er": "nightlife",
    "90er": "nightlife",
}


def _kategorie_erkennen(titel: str) -> str:
    """
    Mappt den Event-Titel auf eine DiesDasDüsseldorf-Kategorie.

    Kurze Schlüssel (≤ 3 Zeichen, z.B. "dj") werden nur als ganzes Wort
    erkannt, um Fehltreffer in längeren Wörtern zu vermeiden.

    Args:
        titel: Event-Titel

    Returns:
        Gültige Kategorie (Standard beim Pitcher: musik)
    """
    if not titel:
        return "musik"
    text_klein = titel.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if len(schluessel) <= 3:
            if re.search(rf"\b{re.escape(schluessel)}\b", text_klein):
                return kategorie
        elif schluessel in text_klein:
            return kategorie
    return "musik"


def _text_bereinigen(roh: Optional[str], max_laenge: int = 300) -> Optional[str]:
    """
    Entfernt HTML-Tags und überflüssige Leerzeichen und kürzt auf max_laenge.

    Args:
        roh:        Roher Beschreibungstext (ggf. mit HTML)
        max_laenge: Maximale Länge des Ergebnisses

    Returns:
        Bereinigter Text oder None
    """
    if not roh:
        return None
    # BeautifulSoup nur bei echtem HTML nutzen (vermeidet Warnungen bei Klartext)
    text = BeautifulSoup(roh, "html.parser").get_text(" ") if "<" in roh else roh
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    if len(text) > max_laenge:
        text = text[: max_laenge - 1].rsplit(" ", 1)[0] + "…"
    return text


def _preis_formatieren(preis_ab) -> Optional[str]:
    """
    Formatiert den Mindestpreis aus der API (z.B. 18.5 → "ab 18,50€").

    Die API liefert 0, wenn der Verkauf nicht über EventFlow läuft
    (z.B. externer Ticketshop) – dann ist kein Preis bekannt.

    Args:
        preis_ab: Zahl oder None

    Returns:
        Preis-String oder None
    """
    try:
        wert = float(preis_ab)
    except (TypeError, ValueError):
        return None
    if wert <= 0:
        return None
    if wert.is_integer():
        return f"ab {int(wert)}€"
    return f"ab {wert:.2f}€".replace(".", ",")


def _event_umwandeln(eintrag: dict, heute: date, enddatum: date) -> Optional[dict]:
    """
    Wandelt einen EventFlow-API-Eintrag in ein DDD-Event-Dict um.

    Args:
        eintrag:  Event-Objekt aus der API
        heute:    Untere Datumsgrenze
        enddatum: Obere Datumsgrenze

    Returns:
        Event-Dict oder None, wenn das Event übersprungen werden soll
    """
    titel = (eintrag.get("title") or "").strip()
    if not titel:
        return None

    # Abgesagte, private oder unveröffentlichte Events überspringen
    if eintrag.get("status") != "published":
        logger.debug("Pitcher: überspringe '%s' (Status %s)", titel, eintrag.get("status"))
        return None
    if eintrag.get("is_private_event") or eintrag.get("last_cancellation"):
        logger.debug("Pitcher: überspringe '%s' (privat/abgesagt)", titel)
        return None

    # start_date ist ISO 8601 mit lokalem Offset, z.B. "2026-11-05T19:00:00+01:00"
    start = eintrag.get("start_date") or ""
    if not re.match(r"\d{4}-\d{2}-\d{2}", start):
        return None
    datum = start[:10]
    datum_obj = date.fromisoformat(datum)
    # Mehrtägige Aktionen mit Start in der Vergangenheit (z.B. Verlosungen) entfallen
    if datum_obj < heute or datum_obj > enddatum:
        return None

    uhrzeit = start[11:16] if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", start) else None

    beschreibung = _text_bereinigen(eintrag.get("short_description")) or _text_bereinigen(
        eintrag.get("description")
    )

    return {
        "titel": titel,
        "datum": datum,
        "uhrzeit": uhrzeit,
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": _kategorie_erkennen(titel),
        "beschreibung": beschreibung,
        "preis": _preis_formatieren(eintrag.get("price_from")),
        "quelle_name": QUELLE_NAME,
        "quelle_url": eintrag.get("detail_url") or LISTE_URL,
        "bild_url": eintrag.get("featured_image_url") or None,
        "instagram_caption": None,
        "datum_bis": None,
        "ist_wiederkehrend": False,
        "status": "neu",
    }


def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen des Pitcher Rock HQ Düsseldorf über die
    öffentliche EventFlow-REST-API von pitcher29.com.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
        Leere Liste bei Fehler.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    events: list[dict] = []
    gesehene_schluessel: set[str] = set()

    try:
        for seite in range(1, MAX_SEITEN + 1):
            url = (
                f"{API_URL}?per_page={SEITENGROESSE}&page={seite}"
                "&sort=start_date_asc"
            )
            # seite_abrufen wartet vor jedem Request 2 s (Rate Limiting)
            antwort = seite_abrufen(url, logger)
            if antwort is None:
                logger.warning("Pitcher: API-Seite %d nicht abrufbar", seite)
                break

            try:
                daten = json.loads(antwort)
            except json.JSONDecodeError:
                logger.error("Pitcher: API-Antwort ist kein gültiges JSON (Seite %d)", seite)
                break

            eintraege = daten.get("items") if isinstance(daten, dict) else None
            if not isinstance(eintraege, list) or not eintraege:
                break

            letztes_datum: Optional[str] = None
            for eintrag in eintraege:
                if not isinstance(eintrag, dict):
                    continue
                try:
                    letztes_datum = (eintrag.get("start_date") or "")[:10] or letztes_datum
                    event = _event_umwandeln(eintrag, heute, enddatum)
                except Exception as fehler:
                    logger.error("Pitcher: Fehler bei Event-Verarbeitung: %s", fehler)
                    continue
                if not event:
                    continue
                schluessel = f"{event['titel']}_{event['datum']}"
                if schluessel in gesehene_schluessel:
                    continue
                gesehene_schluessel.add(schluessel)
                events.append(event)

            # Abbruch: letzte Seite erreicht oder Vorschau-Zeitraum überschritten
            if len(eintraege) < SEITENGROESSE:
                break
            if letztes_datum and letztes_datum > enddatum.isoformat():
                break

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []

    logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:5]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
