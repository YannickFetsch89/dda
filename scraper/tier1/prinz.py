"""
prinz.py – DiesDasDüsseldorf
Scraper für PRINZ.de: Veranstaltungsmagazin Düsseldorf
URL: https://prinz.de/duesseldorf/events

PRINZ.de bietet kategorisierte Event-Listings für Düsseldorf.
Die Seite ist server-seitig gerendert, Events werden als Listeneinträge
mit strukturiertem HTML ausgegeben.

DOM-Struktur (erwartet):
  <article class="event-..."> oder ähnliche Container
  Enthält: Titel, Datum, Ort, Kategorie

Erstellt: 2026-04-02
"""
import logging
import time
from datetime import date, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen, uhrzeit_parsen
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://prinz.de"
LISTE_URL = "https://prinz.de/duesseldorf/events"
QUELLE_NAME = "PRINZ.de Düsseldorf"

# Kategorie-Mapping PRINZ.de-Kategorien → DiesDasDüsseldorf
KATEGORIE_MAPPING = {
    "konzert": "musik",
    "konzerte": "musik",
    "livemusik": "musik",
    "live-musik": "musik",
    "club": "nightlife",
    "party": "nightlife",
    "nightlife": "nightlife",
    "theater": "kultur",
    "bühne": "kultur",
    "buehne": "kultur",
    "ausstellung": "kultur",
    "kunst": "kultur",
    "kino": "kultur",
    "film": "kultur",
    "comedy": "kultur",
    "kabarett": "kultur",
    "musical": "kultur",
    "oper": "kultur",
    "food": "food",
    "kulinarik": "food",
    "markt": "food",
    "sport": "sport",
    "outdoor": "outdoor",
    "natur": "outdoor",
    "workshop": "community",
    "meetup": "community",
    "networking": "community",
    "kinder": "family",
    "familie": "family",
    "family": "family",
    "dating": "dating",
    "singles": "dating",
}

# URL-Pfade für Kategorieseiten (werden zusätzlich zur Hauptseite abgerufen)
KATEGORIE_URLS = [
    "/duesseldorf/events/konzerte-livemusik/",
    "/duesseldorf/events/party/",
    "/duesseldorf/events/buehne/",
]


def _kategorie_aus_text(text: str) -> str:
    """
    Mappt PRINZ.de-Kategorietext auf DiesDasDüsseldorf-Kategorien.

    Args:
        text: Kategorietext von der Webseite

    Returns:
        Gültige DiesDasDüsseldorf-Kategorie
    """
    if not text:
        return "sonstiges"

    schluessel = text.strip().lower()
    for keyword, kategorie in KATEGORIE_MAPPING.items():
        if keyword in schluessel:
            return kategorie

    return "sonstiges"


def _event_aus_artikel(artikel, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem PRINZ.de Artikel-Element.

    Args:
        artikel: BeautifulSoup-Element des Event-Eintrags
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None wenn Pflichtfelder fehlen / Event vergangen
    """
    try:
        # Titel
        titel_el = (
            artikel.find("h2")
            or artikel.find("h3")
            or artikel.find(class_=lambda c: c and "title" in c.lower() if c else False)
            or artikel.find(class_=lambda c: c and "headline" in c.lower() if c else False)
        )
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel:
            return None

        # URL
        link_el = artikel.find("a", href=True)
        quelle_url = BASE_URL + link_el["href"] if link_el and link_el["href"].startswith("/") else (
            link_el["href"] if link_el else LISTE_URL
        )

        # Datum aus allen Texten extrahieren
        alle_texte = [el.get_text(strip=True) for el in artikel.find_all(True) if el.get_text(strip=True)]

        datum = None
        uhrzeit = None
        for text in alle_texte:
            datum_kandidat = datum_parsen(text)
            if datum_kandidat:
                datum = datum_kandidat
                uhrzeit = uhrzeit_parsen(text)
                break

        if not datum:
            return None

        # Vergangene Events überspringen
        if date.fromisoformat(datum) < heute:
            return None

        # Ort
        ort = None
        ort_indikatoren = ["location", "venue", "ort", "place"]
        for el in artikel.find_all(True):
            klassen = el.get("class", [])
            klassen_str = " ".join(klassen).lower() if isinstance(klassen, list) else str(klassen).lower()
            if any(ind in klassen_str for ind in ort_indikatoren):
                text = el.get_text(strip=True)
                if text and len(text) > 2:
                    ort = text
                    break

        if not ort:
            # Fallback: zweiter signifikanter Text nach dem Datum
            for text in alle_texte:
                if text == titel:
                    continue
                if datum_parsen(text):
                    continue
                if len(text) > 3 and not text.isdigit():
                    ort = text
                    break

        if not ort:
            ort = "Düsseldorf"

        # Kategorie
        kategorie_el = artikel.find(class_=lambda c: c and "kategorie" in c.lower() if c else False)
        kategorie_text = kategorie_el.get_text(strip=True) if kategorie_el else ""
        kategorie = _kategorie_aus_text(kategorie_text)

        # Bild
        bild_el = artikel.find("img")
        bild_url = None
        if bild_el:
            bild_url = (
                bild_el.get("data-src")
                or bild_el.get("data-original")
                or bild_el.get("src")
            )

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": None,
            "kategorie": kategorie,
            "beschreibung": None,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error("Fehler beim Parsen eines PRINZ.de-Events: %s", str(fehler))
        return None


def _events_von_seite(url: str, heute: date) -> list[dict]:
    """
    Scrapt Events von einer einzelnen PRINZ.de-Seite.

    Args:
        url: URL der zu scrapenden Seite
        heute: Heutiges Datum für Filterung

    Returns:
        Liste von Event-Dicts
    """
    events = []

    try:
        html = seite_abrufen(url, logger)
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Verschiedene mögliche Container-Selektoren probieren
        artikel_liste = (
            soup.find_all("article")
            or soup.find_all(class_=lambda c: c and "event" in " ".join(c).lower() if c else False)
            or soup.find_all(class_=lambda c: c and "item" in " ".join(c).lower() if c else False)
        )

        logger.info("PRINZ.de %s: %d Einträge gefunden", url, len(artikel_liste))

        for artikel in artikel_liste:
            event = _event_aus_artikel(artikel, heute)
            if event:
                events.append(event)

    except Exception as fehler:
        logger.error("Fehler beim Scrapen von %s: %s", url, str(fehler))

    return events


def scrape() -> list[dict]:
    """
    Scrapt Events von PRINZ.de Düsseldorf.

    Ruft die Hauptseite und ausgewählte Kategorieseiten ab.
    PRINZ.de ist einer der größten lokalen Event-Aggregatoren für Düsseldorf
    und deckt Konzerte, Partys, Theater, Sport und mehr ab.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    gesehene_urls: set[str] = set()

    # Hauptseite scrapen
    haupt_events = _events_von_seite(LISTE_URL, heute)
    for event in haupt_events:
        url = event.get("quelle_url", "")
        if url not in gesehene_urls:
            gesehene_urls.add(url)
            events.append(event)

    # Kategorieseiten scrapen (mit Rate Limiting)
    for pfad in KATEGORIE_URLS:
        url = BASE_URL + pfad
        time.sleep(2)
        kategorie_events = _events_von_seite(url, heute)
        for event in kategorie_events:
            event_url = event.get("quelle_url", "")
            if event_url not in gesehene_urls:
                gesehene_urls.add(event_url)
                events.append(event)

    # 14-Tage-Fenster
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]

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
    for e in ergebnisse[:3]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
