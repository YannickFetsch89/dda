"""
street_food_thursday.py – DiesDasDüsseldorf
Statischer Scraper für den Street Food Thursday im Stahlwerk Düsseldorf.

Der Street Food Thursday ist ein monatliches Gratis-Streetfood-Event im
Stahlwerk Düsseldorf (Ronsdorfer Str. 134). Ca. 2.000 Besucher pro Abend,
kostenloser Eintritt. Termine von März bis mindestens Juli, jeden 2. Donnerstag
im Monat (typischerweise).

Da keine offizielle Event-API existiert, werden die Termine semi-statisch
aus bekannten Mustern berechnet und ggf. durch Website-Scraping ergänzt.

Quellen:
  - Stahlwerk-Website: https://stahlwerk-duesseldorf.de
  - Event-Seite: https://food-festivals.com (Aggregator)

Erstellt: 2026-04-02
"""
import logging
from datetime import date, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen, uhrzeit_parsen
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

QUELLE_NAME = "Street Food Thursday Düsseldorf"
ORT_STANDARD = "Stahlwerk Düsseldorf"
ADRESSE_STANDARD = "Ronsdorfer Str. 134, 40233 Düsseldorf"
KATEGORIE_STANDARD = "food"
QUELLE_URL = "https://stahlwerk-duesseldorf.de"

# Monate in denen das Event typischerweise stattfindet (März bis Oktober)
EVENT_MONATE = [3, 4, 5, 6, 7, 8, 9, 10]

# Typischer Wochentag: Donnerstag (3 = Donnerstag in Python weekday())
EVENT_WOCHENTAG = 3  # Donnerstag

# Typisch: erster oder zweiter Donnerstag im Monat
# Wird als Fallback genutzt wenn keine Website-Daten verfügbar
EVENT_WOCHE_IM_MONAT = 2  # Zweiter Donnerstag

# Uhrzeit (typisch 17:00 Uhr)
EVENT_UHRZEIT = "17:00"

# Scraping-URLs als primäre Datenquelle
SCRAPE_URLS = [
    "https://stahlwerk-duesseldorf.de",
]


def _naechste_donnerstage(heute: date, anzahl: int = 5) -> list[date]:
    """
    Berechnet die nächsten N Donnerstage im Vorschauzeitraum,
    die in den Event-Monaten liegen.

    Args:
        heute: Heutiges Datum
        anzahl: Maximale Anzahl zurückzugebender Termine

    Returns:
        Liste von Datumsobjekten (nur Donnerstage in EVENT_MONATE)
    """
    termine = []
    kandidat = heute

    # Zum nächsten Donnerstag vorspulen
    tage_bis_donnerstag = (EVENT_WOCHENTAG - heute.weekday()) % 7
    if tage_bis_donnerstag == 0:
        tage_bis_donnerstag = 7  # Nächste Woche wenn heute Donnerstag
    kandidat = heute + timedelta(days=tage_bis_donnerstag)

    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)

    while kandidat <= enddatum and len(termine) < anzahl:
        if kandidat.month in EVENT_MONATE:
            # Prüfen ob es der "richtige" Donnerstag im Monat ist
            # (zweiter Donnerstag des Monats)
            erster_tag_monat = kandidat.replace(day=1)
            erster_donnerstag_offset = (EVENT_WOCHENTAG - erster_tag_monat.weekday()) % 7
            erster_donnerstag = erster_tag_monat + timedelta(days=erster_donnerstag_offset)
            zweiter_donnerstag = erster_donnerstag + timedelta(weeks=EVENT_WOCHE_IM_MONAT - 1)

            if kandidat == zweiter_donnerstag:
                termine.append(kandidat)

        kandidat += timedelta(weeks=1)

    return termine


def _events_von_website(heute: date) -> list[dict]:
    """
    Versucht Street-Food-Thursday-Termine von der Stahlwerk-Website zu scrapen.

    Args:
        heute: Heutiges Datum für Filterung

    Returns:
        Liste von Event-Dicts oder leere Liste wenn keine gefunden
    """
    events = []

    for url in SCRAPE_URLS:
        try:
            html = seite_abrufen(url, logger)
            if html is None:
                continue

            soup = BeautifulSoup(html, "html.parser")
            alle_texte = soup.get_text(" ", strip=True)

            # Suche nach "Street Food" Erwähnung mit Datum
            for el in soup.find_all(True):
                text = el.get_text(strip=True)
                if "street food" in text.lower() and len(text) < 200:
                    datum = datum_parsen(text)
                    if datum and date.fromisoformat(datum) >= heute:
                        uhrzeit = uhrzeit_parsen(text) or EVENT_UHRZEIT

                        # URL aus dem Element extrahieren
                        link_el = el.find("a", href=True)
                        event_url = link_el["href"] if link_el else url

                        events.append({
                            "titel": "Street Food Thursday",
                            "datum": datum,
                            "uhrzeit": uhrzeit,
                            "ort": ORT_STANDARD,
                            "adresse": ADRESSE_STANDARD,
                            "kategorie": KATEGORIE_STANDARD,
                            "beschreibung": (
                                "Monatliches Streetfood-Event im Stahlwerk Düsseldorf. "
                                "Kostenloser Eintritt, ca. 2.000 Besucher. "
                                "Streetfood, Getränke, gute Stimmung."
                            ),
                            "preis": "Kostenlos",
                            "quelle_name": QUELLE_NAME,
                            "quelle_url": event_url if event_url.startswith("http") else url,
                            "bild_url": None,
                            "instagram_caption": None,
                            "datum_bis": None,
                            "ist_wiederkehrend": True,
                            "status": "neu",
                        })

        except Exception as fehler:
            logger.error("Fehler beim Scrapen von %s: %s", url, str(fehler))

    return events


def scrape() -> list[dict]:
    """
    Gibt Street-Food-Thursday-Events für den Vorschauzeitraum zurück.

    Strategie:
    1. Website-Scraping für konkrete Termine
    2. Fallback: Berechnung der zweiten Donnerstage im Monat (März–Oktober)

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    # Strategie 1: Website-Scraping
    try:
        website_events = _events_von_website(heute)
        if website_events:
            logger.info("Street Food Thursday: %d Termine von Website gefunden.", len(website_events))
            return website_events
    except Exception as fehler:
        logger.error("Website-Scraping fehlgeschlagen: %s", str(fehler))

    # Strategie 2: Berechnung der Termine
    logger.info("Fallback: Berechne Street-Food-Thursday-Termine aus Muster.")
    termine = _naechste_donnerstage(heute)

    for termin in termine:
        events.append({
            "titel": "Street Food Thursday",
            "datum": termin.isoformat(),
            "uhrzeit": EVENT_UHRZEIT,
            "ort": ORT_STANDARD,
            "adresse": ADRESSE_STANDARD,
            "kategorie": KATEGORIE_STANDARD,
            "beschreibung": (
                "Monatliches Streetfood-Event im Stahlwerk Düsseldorf. "
                "Kostenloser Eintritt, ca. 2.000 Besucher. "
                "Streetfood-Stände, Getränke, entspannte Atmosphäre."
            ),
            "preis": "Kostenlos",
            "quelle_name": QUELLE_NAME,
            "quelle_url": QUELLE_URL,
            "bild_url": None,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": True,
            "status": "neu",
        })

    logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
