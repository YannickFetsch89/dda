"""
eventbrite.py – DiesDasDüsseldorf
Scraper für die Eventbrite API v3: Events in Düsseldorf
Erstellt: 2026-02-24
"""
import json
import logging
import re
from datetime import date, datetime
from typing import Optional

from bs4 import BeautifulSoup

from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

# Hinweis: Die Eventbrite API v3 /events/search/ wurde abgeschaltet (2024).
# Stattdessen wird die öffentliche Website mit JSON-LD Markup gescrapt.
WEBSITE_URL = "https://www.eventbrite.de/d/germany--d%C3%BCsseldorf/events/"
QUELLE_NAME = "Eventbrite"

# Mapping Eventbrite category_id → DiesDasDüsseldorf-Kategorien
KATEGORIE_MAPPING = {
    "103": "musik",       # Music
    "101": "community",   # Business & Professional
    "110": "food",        # Food & Drink
    "104": "kultur",      # Film & Media
    "105": "kultur",      # Performing & Visual Arts
    "108": "sport",       # Sports & Fitness
    "107": "outdoor",     # Science & Technology
    "106": "community",   # Health & Wellness
    "113": "community",   # Community & Culture
    "115": "family",      # Family & Education
    "116": "nightlife",   # Holiday & Seasonal
    "117": "outdoor",     # Travel & Outdoor
    "118": "community",   # Charity & Causes
    "199": "sonstiges",   # Other
}


def _kategorie_mappen(category_id: Optional[str]) -> str:
    """
    Mappt eine numerische Eventbrite category_id auf eine
    DiesDasDüsseldorf-Kategorie.

    Args:
        category_id: Numerische Kategorie-ID als String oder None

    Returns:
        Gültige DiesDasDüsseldorf-Kategorie
    """
    if not category_id:
        return "sonstiges"
    return KATEGORIE_MAPPING.get(str(category_id), "sonstiges")


def _preis_ermitteln(event: dict) -> Optional[str]:
    """
    Ermittelt den Preis eines Events aus den Eventbrite API-Daten.

    Logik:
    - is_free == True → "kostenlos"
    - min == max → "ab {min}€"
    - min != max → "{min}€ – {max}€"
    - Keine Preis-Info vorhanden → None

    Args:
        event: Rohes Event-Dict aus der Eventbrite API

    Returns:
        Preisstring oder None
    """
    if event.get("is_free"):
        return "kostenlos"

    verfuegbarkeit = event.get("ticket_availability") or {}
    min_preis_obj = verfuegbarkeit.get("minimum_ticket_price") or {}
    max_preis_obj = verfuegbarkeit.get("maximum_ticket_price") or {}

    min_preis = min_preis_obj.get("major_value")
    max_preis = max_preis_obj.get("major_value")

    if min_preis is None and max_preis is None:
        return None

    try:
        min_val = float(min_preis) if min_preis is not None else None
        max_val = float(max_preis) if max_preis is not None else None

        if min_val is not None and max_val is not None:
            if min_val == max_val:
                return f"ab {min_val:.0f}€"
            return f"{min_val:.0f}€ – {max_val:.0f}€"

        if min_val is not None:
            return f"ab {min_val:.0f}€"

        if max_val is not None:
            return f"bis {max_val:.0f}€"

    except (ValueError, TypeError) as e:
        logger.warning("Preisangabe konnte nicht verarbeitet werden: %s", e)

    return None


def _event_aus_jsonld(item: dict, heute: date) -> Optional[dict]:
    """
    Mappt ein JSON-LD ListItem-Event auf das DiesDasDüsseldorf Standard Event-Dict.

    Die Eventbrite-Website liefert Events als JSON-LD itemListElement mit
    startDate, description, url und image.

    Args:
        item: JSON-LD ListItem-Dict (enthält "item"-Unterebene mit Event-Daten)
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict im DiesDasDüsseldorf-Format oder None bei Fehler
    """
    try:
        event = item.get("item", item)

        # --- URL ---
        quelle_url = event.get("url", "").strip()
        if not quelle_url:
            return None

        # --- Titel: aus URL ableiten wenn kein name-Feld ---
        titel = event.get("name", "").strip()
        if not titel:
            # Aus URL-Slug extrahieren: /e/titel-tickets-123 → "Titel"
            slug = quelle_url.rstrip("/").split("/")[-1]
            slug = re.sub(r"-tickets-\d+$", "", slug)
            titel = slug.replace("-", " ").title()
        if not titel:
            return None

        # --- Datum ---
        start_date = event.get("startDate", "")
        if not start_date:
            return None
        try:
            if "T" in start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                datum = start_dt.date().isoformat()
                uhrzeit = start_dt.strftime("%H:%M")
            else:
                datum = start_date[:10]
                uhrzeit = None
        except (ValueError, TypeError):
            return None

        if date.fromisoformat(datum) < heute:
            return None

        # --- Ort ---
        location = event.get("location", {})
        ort = location.get("name", "").strip() or "Düsseldorf"
        adresse = location.get("address", {}).get("streetAddress", "").strip() or None

        # --- Kategorie aus Titel ableiten ---
        titel_lower = titel.lower()
        kategorie = "sonstiges"
        for schluessel, kat in {
            "konzert": "musik", "musik": "musik", "festival": "musik",
            "ausstellung": "kultur", "theater": "kultur", "oper": "kultur",
            "party": "nightlife", "club": "nightlife",
            "sport": "sport", "fitness": "sport",
            "workshop": "community", "meetup": "community",
            "food": "food", "markt": "food",
            "kinder": "family", "family": "family",
        }.items():
            if schluessel in titel_lower:
                kategorie = kat
                break

        # --- Bild ---
        bild_url = event.get("image", None)

        # --- Beschreibung ---
        beschreibung = event.get("description", "").strip()[:300] or None

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": adresse,
            "kategorie": kategorie,
            "beschreibung": beschreibung,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "status": "neu",
        }

    except Exception as e:
        logger.error("Fehler beim Mappen eines Eventbrite-Events: %s", str(e))
        return None


def scrape() -> list[dict]:
    """
    Scrapt Events von der Eventbrite-Website für Düsseldorf via JSON-LD Markup.

    Hinweis: Die Eventbrite API v3 /events/search/ wurde 2024 abgeschaltet.
    Stattdessen wird die öffentliche Eventbrite-Website gescrapt, die Events
    als strukturierte JSON-LD Daten (schema.org) ausliefert.

    Bei Bot-Schutz (AWS WAF / 405) wird die Liste leer zurückgegeben.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events: list[dict] = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = seite_abrufen(WEBSITE_URL, logger)
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # JSON-LD Markup parsen
        jsonld_scripts = soup.find_all("script", type="application/ld+json")
        if not jsonld_scripts:
            logger.warning(
                "Kein JSON-LD Markup auf Eventbrite-Seite gefunden – "
                "Seitenstruktur möglicherweise geändert."
            )
            return []

        roh_events: list[dict] = []
        for script in jsonld_scripts:
            try:
                daten = json.loads(script.string or "")
                items = daten.get("itemListElement", [])
                roh_events.extend(items)
            except (json.JSONDecodeError, AttributeError):
                continue

        logger.info("%d rohe Events aus Eventbrite JSON-LD extrahiert", len(roh_events))

        gesehene_urls: set[str] = set()
        for item in roh_events:
            event = _event_aus_jsonld(item, heute)
            if event is None:
                continue
            url = event["quelle_url"]
            if url in gesehene_urls:
                continue
            gesehene_urls.add(url)
            events.append(event)

    except Exception as e:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(e))
        return []

    if not events:
        logger.warning(
            "Scraper %s: 0 Events gefunden. "
            "Eventbrite-Website möglicherweise durch Bot-Schutz blockiert.",
            QUELLE_NAME,
        )

    logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    # Direkter Testlauf
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    import json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
