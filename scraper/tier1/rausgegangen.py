"""
rausgegangen.py – DiesDasDüsseldorf
Scraper für Rausgegangen.de: Events in Düsseldorf
Erstellt: 2026-02-24
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://rausgegangen.de"
LISTE_URL = "https://rausgegangen.de/duesseldorf/"
QUELLE_NAME = "Rausgegangen"

# Mapping Rausgegangen-Kategorien → DiesDasDüsseldorf-Kategorien
KATEGORIE_MAPPING = {
    "party": "nightlife",
    "club": "nightlife",
    "konzert": "musik",
    "musik": "musik",
    "live": "musik",
    "theater": "kultur",
    "ausstellung": "kultur",
    "kunst": "kultur",
    "kino": "kultur",
    "film": "kultur",
    "oper": "kultur",
    "comedy": "kultur",
    "sport": "sport",
    "outdoor": "outdoor",
    "natur": "outdoor",
    "food": "food",
    "markt": "food",
    "essen": "food",
    "workshop": "community",
    "meetup": "community",
    "networking": "community",
    "kinder": "family",
    "familie": "family",
    "dating": "dating",
    "singles": "dating",
}


def _datum_parsen(datum_text: str) -> Optional[str]:
    """
    Wandelt Rausgegangen-Datumstexte in ISO 8601 Format um.
    Beispiele: 'Heute, 24. Feb', 'Morgen, 25. Feb', 'Mo, 3. Mär'

    Args:
        datum_text: Roher Datumstext von der Webseite

    Returns:
        Datum als ISO-String (YYYY-MM-DD) oder None bei Fehler
    """
    heute = date.today()

    if not datum_text:
        return None

    datum_text = datum_text.strip().lower()

    try:
        if datum_text.startswith("heute"):
            return heute.isoformat()

        if datum_text.startswith("morgen"):
            return (heute + timedelta(days=1)).isoformat()

        # Format: "Mo, 3. Mär" oder "Heute, 24. Feb"
        monat_map = {
            "jan": 1, "feb": 2, "mär": 3, "apr": 4,
            "mai": 5, "jun": 6, "jul": 7, "aug": 8,
            "sep": 9, "okt": 10, "nov": 11, "dez": 12,
        }

        # Datumsanteil nach dem Komma extrahieren
        teile = datum_text.split(",")
        datum_teil = teile[-1].strip() if len(teile) > 1 else datum_text

        # Tag und Monat extrahieren
        woerter = datum_teil.split()
        if len(woerter) >= 2:
            tag_str = woerter[0].replace(".", "").strip()
            monat_str = woerter[1][:3].lower()

            tag = int(tag_str)
            monat = monat_map.get(monat_str)

            if monat is None:
                logger.warning("Unbekannter Monat: %s", monat_str)
                return None

            # Jahr bestimmen (aktuelles oder nächstes Jahr)
            jahr = heute.year
            kandidat = date(jahr, monat, tag)
            if kandidat < heute - timedelta(days=1):
                kandidat = date(jahr + 1, monat, tag)

            return kandidat.isoformat()

    except (ValueError, IndexError) as e:
        logger.warning("Datum konnte nicht geparst werden: '%s' – %s", datum_text, e)
        return None

    return None


def _uhrzeit_parsen(datum_text: str) -> Optional[str]:
    """
    Extrahiert die Uhrzeit aus einem Datumstext.
    Beispiel: 'Heute, 24. Feb | 18:00 Uhr' → '18:00'

    Args:
        datum_text: Roher Text der Datums-/Uhrzeitangabe

    Returns:
        Uhrzeit als HH:MM String oder None
    """
    if "|" not in datum_text:
        return None

    try:
        uhrzeit_teil = datum_text.split("|")[1].strip()
        uhrzeit = uhrzeit_teil.replace("Uhr", "").strip()
        # Validieren
        datetime.strptime(uhrzeit, "%H:%M")
        return uhrzeit
    except (ValueError, IndexError):
        return None


def _kategorie_erkennen(kategorie_text: str) -> str:
    """
    Mappt Rausgegangen-Kategorietext auf DiesDasDüsseldorf-Kategorien.

    Args:
        kategorie_text: Kategorietext von der Webseite (z.B. 'Party')

    Returns:
        Gültige DiesDasDüsseldorf-Kategorie
    """
    if not kategorie_text:
        return "sonstiges"

    schluessel = kategorie_text.strip().lower()

    for keyword, kategorie in KATEGORIE_MAPPING.items():
        if keyword in schluessel:
            return kategorie

    return "sonstiges"


def _event_aus_karte(karte, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einer Rausgegangen Event-Karte.

    Args:
        karte: BeautifulSoup-Element der Event-Karte
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None wenn Pflichtfelder fehlen / Event vergangen
    """
    try:
        # URL
        pfad = karte.get("href", "")
        if not pfad:
            return None
        quelle_url = BASE_URL + pfad

        # Titel
        titel_el = karte.find("h4")
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel:
            return None

        # Alle Texte aus der Karte sammeln
        alle_texte = [
            el.get_text(strip=True)
            for el in karte.find_all(["span", "div", "p"], string=True)
            if el.get_text(strip=True) and len(el.get_text(strip=True)) > 2
        ]

        # Datum und Uhrzeit (erster Text der | enthält oder mit Wochentag beginnt)
        datum_text = None
        for text in alle_texte:
            text_lower = text.lower()
            if any(text_lower.startswith(t) for t in [
                "heute", "morgen", "mo,", "di,", "mi,", "do,", "fr,", "sa,", "so,"
            ]):
                datum_text = text
                break

        datum = _datum_parsen(datum_text) if datum_text else None
        if not datum:
            logger.warning("Kein Datum gefunden für Event: %s", titel)
            return None

        # Vergangene Events überspringen
        if date.fromisoformat(datum) < heute:
            return None

        uhrzeit = _uhrzeit_parsen(datum_text) if datum_text else None

        # Ort (zweiter relevanter Text nach dem Datum)
        ort = None
        datum_gefunden = False
        for text in alle_texte:
            text_lower = text.lower()
            if any(text_lower.startswith(t) for t in [
                "heute", "morgen", "mo,", "di,", "mi,", "do,", "fr,", "sa,", "so,"
            ]):
                datum_gefunden = True
                continue
            if datum_gefunden and text not in ["TAGESTIPP"] and len(text) > 2:
                ort = text
                break

        if not ort:
            logger.warning("Kein Ort gefunden für Event: %s", titel)
            return None

        # Preis
        preis = None
        for text in alle_texte:
            if any(p in text.lower() for p in ["frei", "€", "eintritt", "kostenlos"]):
                preis = text
                break

        # Kategorie (letzter kurzer Text)
        kategorie_text = ""
        for text in reversed(alle_texte):
            if len(text) < 30 and text not in ["TAGESTIPP"]:
                kategorie_text = text
                break
        kategorie = _kategorie_erkennen(kategorie_text)

        # Bild
        bild_el = karte.find("img")
        bild_url = bild_el.get("src") if bild_el else None

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": None,
            "kategorie": kategorie,
            "beschreibung": None,
            "preis": preis,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        }

    except Exception as e:
        logger.error("Fehler beim Parsen einer Event-Karte: %s", str(e))
        return None


def scrape(ziel_datum: Optional[date] = None) -> list[dict]:
    """
    Scrapt Events von Rausgegangen.de für Düsseldorf.

    Args:
        ziel_datum: Optionales Datum – wird aktuell nicht zur Filterung
                    genutzt (Seite zeigt automatisch kommende Events).
                    None = heute und nächste Tage.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = seite_abrufen(LISTE_URL, logger)
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")
        karten = soup.find_all("a", class_="event-tile")
        logger.info("%d Event-Karten gefunden", len(karten))

        # Duplikate innerhalb eines Scraper-Laufs verhindern
        gesehene_urls: set[str] = set()

        for karte in karten:
            url = karte.get("href", "")
            if url in gesehene_urls:
                continue
            gesehene_urls.add(url)

            event = _event_aus_karte(karte, heute)
            if event:
                events.append(event)

    except Exception as e:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(e))
        return []

    # 14-Tage-Fenster: Events weiter als SCRAPER_VORSCHAU_TAGE in der Zukunft ausfiltern
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]

    logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    # Direkter Testlauf
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
