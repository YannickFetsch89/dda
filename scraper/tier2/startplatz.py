"""
startplatz.py – DiesDasDüsseldorf
Scraper für den STARTPLATZ Düsseldorf.
URL: https://www.startplatz.de/coworking-duesseldorf

STARTPLATZ ist der größte Startup-Inkubator NRW mit 300+ Events pro Jahr:
Workshops, Pitches, Meetups, Konferenzen. Viele Events sind öffentlich zugänglich.

Erstellt: 2026-04-02
"""
import logging
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen, uhrzeit_parsen
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://www.startplatz.de"
EVENTS_URL = "https://www.startplatz.de/events"
QUELLE_NAME = "STARTPLATZ Düsseldorf"
ORT_STANDARD = "STARTPLATZ Düsseldorf"
ADRESSE_STANDARD = "Speditionstr. 1, 40221 Düsseldorf"
KATEGORIE_STANDARD = "community"

# Fallback-URLs
FALLBACK_URLS = [
    "https://www.startplatz.de/coworking-duesseldorf",
    BASE_URL,
]


def _event_aus_element(el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem STARTPLATZ Event-Element.

    Args:
        el: BeautifulSoup-Element
        heute: Heutiges Datum für Filterung

    Returns:
        Event-Dict oder None
    """
    try:
        # Titel
        titel_el = (
            el.find("h2")
            or el.find("h3")
            or el.find("h4")
            or el.find(class_=lambda c: c and "title" in str(c).lower())
        )
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel:
            return None

        # URL
        link_el = el.find("a", href=True)
        if link_el:
            href = link_el["href"]
            quelle_url = urljoin(BASE_URL, href) if not href.startswith("http") else href
        else:
            quelle_url = EVENTS_URL

        # Datum und Uhrzeit
        datum = None
        uhrzeit = None

        zeit_el = el.find("time")
        if zeit_el:
            datetime_attr = zeit_el.get("datetime", "")
            datum = datum_parsen(datetime_attr) or datum_parsen(zeit_el.get_text(strip=True))
            uhrzeit = uhrzeit_parsen(datetime_attr) or uhrzeit_parsen(zeit_el.get_text(strip=True))

        if not datum:
            for text_el in el.find_all(True):
                text = text_el.get_text(strip=True)
                datum_kandidat = datum_parsen(text)
                if datum_kandidat:
                    datum = datum_kandidat
                    if not uhrzeit:
                        uhrzeit = uhrzeit_parsen(text)
                    break

        if not datum:
            return None

        if date.fromisoformat(datum) < heute:
            return None

        # Preis
        preis = None
        alle_texte_el = el.find_all(True)
        for text_el in alle_texte_el:
            text = text_el.get_text(strip=True)
            if any(p in text.lower() for p in ["kostenlos", "frei", "gratis", "€", "kostenfrei"]):
                if len(text) < 60:
                    preis = text
                    break

        # Kategorie verfeinern
        kategorie = KATEGORIE_STANDARD
        alle_texte = el.get_text(" ", strip=True).lower()
        if "pitch" in alle_texte or "startup" in alle_texte or "gründer" in alle_texte:
            kategorie = "community"
        elif "workshop" in alle_texte:
            kategorie = "community"

        # Beschreibung
        beschreibung = None
        beschr_el = el.find("p")
        if beschr_el:
            beschreibung = beschr_el.get_text(strip=True)[:300] or None

        # Bild
        bild_url = None
        bild_el = el.find("img")
        if bild_el:
            bild_url = (
                bild_el.get("data-src")
                or bild_el.get("data-original")
                or bild_el.get("src")
            )
            if bild_url and not bild_url.startswith("http"):
                bild_url = urljoin(BASE_URL, bild_url)

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT_STANDARD,
            "adresse": ADRESSE_STANDARD,
            "kategorie": kategorie,
            "beschreibung": beschreibung,
            "preis": preis,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error("Fehler beim Parsen eines STARTPLATZ-Events: %s", str(fehler))
        return None


def scrape() -> list[dict]:
    """
    Scrapt Events vom STARTPLATZ Düsseldorf.

    Größter Startup-Inkubator NRW, 300+ Events/Jahr.
    Öffentlich zugängliche Workshops, Pitches, Meetups, Konferenzen.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    alle_urls = [EVENTS_URL] + FALLBACK_URLS

    for url in alle_urls:
        try:
            html = seite_abrufen(url, logger)
            if html is None:
                logger.warning("STARTPLATZ URL nicht erreichbar: %s", url)
                continue

            soup = BeautifulSoup(html, "html.parser")

            # Event-Elemente suchen
            event_elemente = (
                soup.find_all("article")
                or soup.find_all(class_=lambda c: c and "event" in " ".join(c).lower() if c else False)
                or soup.find_all("div", class_=lambda c: c and ("card" in " ".join(c).lower() or "item" in " ".join(c).lower()) if c else False)
            )

            logger.info("STARTPLATZ (%s): %d Einträge gefunden", url, len(event_elemente))

            if event_elemente:
                gesehene_schluessel: set[str] = set()
                for el in event_elemente:
                    event = _event_aus_element(el, heute)
                    if event:
                        schluessel = f"{event['titel']}_{event['datum']}"
                        if schluessel not in gesehene_schluessel:
                            gesehene_schluessel.add(schluessel)
                            events.append(event)
                if events:
                    break

        except Exception as fehler:
            logger.error("Fehler beim Scrapen von %s: %s", url, str(fehler))

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
