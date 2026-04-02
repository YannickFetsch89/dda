"""
capitol_theater.py – DiesDasDüsseldorf
Scraper für das Capitol Theater Düsseldorf.
URL: https://www.capitol-theater.de/programm-tickets

Das Capitol Theater ist das größte Theater Düsseldorfs (1.250+ Plätze) in
einem ehemaligen Straßenbahndepot. Musicals, Shows, Comedy-Gastspiele.

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

BASE_URL = "https://www.capitol-theater.de"
PROGRAMM_URL = "https://www.capitol-theater.de/programm-tickets"
QUELLE_NAME = "Capitol Theater Düsseldorf"
ORT_STANDARD = "Capitol Theater Düsseldorf"
ADRESSE_STANDARD = "Erkrather Str. 30, 40233 Düsseldorf"
KATEGORIE_STANDARD = "kultur"


def _event_aus_element(el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem Capitol-Theater Programm-Element.

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
            quelle_url = PROGRAMM_URL

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
        for text_el in el.find_all(True):
            text = text_el.get_text(strip=True)
            if any(p in text.lower() for p in ["€", "ab ", "preis", "ticket"]):
                if len(text) < 60:
                    preis = text
                    break

        # Beschreibung
        beschreibung = None
        beschr_el = el.find("p")
        if beschr_el:
            beschreibung = beschr_el.get_text(strip=True)[:300] or None

        # Kategorie verfeinern (Musical vs. Comedy vs. Show)
        kategorie = KATEGORIE_STANDARD
        alle_texte = el.get_text(" ", strip=True).lower()
        if "musical" in alle_texte:
            kategorie = "musik"
        elif "comedy" in alle_texte or "kabarett" in alle_texte:
            kategorie = "kultur"

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
        logger.error("Fehler beim Parsen eines Capitol-Theater-Events: %s", str(fehler))
        return None


def scrape() -> list[dict]:
    """
    Scrapt Events vom Capitol Theater Düsseldorf.

    Größtes Theater Düsseldorfs (1.250+ Plätze), Musicals, Shows, Comedy.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = seite_abrufen(PROGRAMM_URL, logger)
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Event-Elemente suchen
        event_elemente = (
            soup.find_all("article")
            or soup.find_all(class_=lambda c: c and ("event" in " ".join(c).lower() or "show" in " ".join(c).lower()) if c else False)
            or soup.find_all("li", class_=True)
        )

        logger.info("Capitol Theater: %d Einträge gefunden", len(event_elemente))

        gesehene_schluessel: set[str] = set()

        for el in event_elemente:
            event = _event_aus_element(el, heute)
            if event:
                schluessel = f"{event['titel']}_{event['datum']}"
                if schluessel not in gesehene_schluessel:
                    gesehene_schluessel.add(schluessel)
                    events.append(event)

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(fehler))
        return []

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
