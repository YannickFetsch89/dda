"""
fft_duesseldorf.py – DiesDasDüsseldorf
Scraper für das FFT Düsseldorf (Forum Freies Theater): Theatervorstellungen und Events.

Strategie:
1. Primär: JSON-LD structured data (schema.org/Event)
2. Fallback: __NEXT_DATA__ JSON (Next.js App)
3. Fallback: HTML-Parsing der Programm-Liste

URL: https://www.fft-duesseldorf.de/programm
Adresse: Jahnstr. 3 / Kasernenstr. 6, 40215 Düsseldorf
Erstellt: 2026-03-05
"""
import json
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://www.fft-duesseldorf.de"
PROGRAMM_URL = "https://www.fft-duesseldorf.de/programm"
QUELLE_NAME = "FFT Düsseldorf"
ORT_STANDARD = "FFT Düsseldorf"
KATEGORIE_STANDARD = "kultur"

# FFT hat zwei Spielstätten
ORT_MAP = {
    "juta": "FFT JUTA, Düsseldorf",
    "jahnstr": "FFT JUTA, Düsseldorf",
    "kammerspiele": "FFT Kammerspiele, Düsseldorf",
    "kasernenstr": "FFT Kammerspiele, Düsseldorf",
}

MONAT_MAP: dict[str, int] = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}
MONAT_KURZ_MAP: dict[str, int] = {
    "jan": 1, "feb": 2, "mär": 3, "mar": 3, "apr": 4,
    "mai": 5, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}


def _datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt verschiedene Datumsformate in ISO 8601 (YYYY-MM-DD) um.

    Args:
        text: Roher Datumstext

    Returns:
        ISO-Datum oder None
    """
    if not text:
        return None

    heute = date.today()
    bereinigt = text.strip()
    bereinigt_klein = bereinigt.lower()

    try:
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(int(treffer.group(1)), int(treffer.group(2)), int(treffer.group(3))).isoformat()

        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1))).isoformat()

        treffer = re.search(r"(\d{1,2})\.?\s+([a-zäöüß]+)\s+(\d{4})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat = MONAT_MAP.get(treffer.group(2).lower())
            jahr = int(treffer.group(3))
            if monat:
                return date(jahr, monat, tag).isoformat()

        treffer = re.search(r"(\d{1,2})\.\s*([a-zäöü]{3})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat = MONAT_KURZ_MAP.get(treffer.group(2)[:3])
            if monat:
                kandidat = date(heute.year, monat, tag)
                if kandidat < heute - timedelta(days=1):
                    kandidat = date(heute.year + 1, monat, tag)
                return kandidat.isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning("Datum konnte nicht geparst werden: '%s' – %s", text, fehler)
        return None

    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """
    Extrahiert Uhrzeit im Format HH:MM aus Text.

    Args:
        text: Roher Text

    Returns:
        Uhrzeit als HH:MM oder None
    """
    if not text:
        return None
    treffer = re.search(r"\b(\d{1,2})[:\.](\d{2})\s*(?:Uhr)?", text, re.IGNORECASE)
    if treffer:
        stunde, minute = int(treffer.group(1)), int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"
    return None


def _ort_erkennen(text: str) -> str:
    """
    Ordnet Ortsangaben der richtigen FFT-Spielstätte zu.

    Args:
        text: Roher Ortstext

    Returns:
        Bereinigter Ortsname
    """
    if not text:
        return ORT_STANDARD
    text_klein = text.lower()
    for schluessel, ort in ORT_MAP.items():
        if schluessel in text_klein:
            return ort
    return text.strip() or ORT_STANDARD


def _events_aus_json_ld(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    Primärstrategie: JSON-LD structured data extrahieren.

    Args:
        soup: Geparste HTML-Seite
        heute: Heute-Datum für Filterung

    Returns:
        Liste von Event-Dicts
    """
    events = []
    gesehene_schluessel: set[str] = set()

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            daten = json.loads(script.string or "{}")
        except (json.JSONDecodeError, AttributeError):
            continue

        eintraege = daten if isinstance(daten, list) else [daten]
        for eintrag in eintraege:
            if not isinstance(eintrag, dict):
                continue
            if eintrag.get("@type") not in ("Event", "TheaterEvent", "DanceEvent", "PerformingArtsEvent"):
                continue

            titel = eintrag.get("name", "").strip()
            if not titel:
                continue

            datum_roh = eintrag.get("startDate") or eintrag.get("startDateTime")
            datum = _datum_parsen(str(datum_roh)) if datum_roh else None
            if not datum or date.fromisoformat(datum) < heute:
                continue

            uhrzeit = _uhrzeit_parsen(str(datum_roh))

            ort_roh = eintrag.get("location", {})
            if isinstance(ort_roh, dict):
                ort = _ort_erkennen(ort_roh.get("name", ""))
            else:
                ort = _ort_erkennen(str(ort_roh)) if ort_roh else ORT_STANDARD

            url_roh = eintrag.get("url")
            quelle_url = str(url_roh) if url_roh else PROGRAMM_URL
            if quelle_url.startswith("/"):
                quelle_url = urljoin(BASE_URL, quelle_url)

            beschreibung_roh = eintrag.get("description")
            beschreibung = str(beschreibung_roh).strip()[:300] if beschreibung_roh else None

            bild_roh = eintrag.get("image")
            if isinstance(bild_roh, list) and bild_roh:
                bild_roh = bild_roh[0]
            if isinstance(bild_roh, dict):
                bild_url = bild_roh.get("url") or bild_roh.get("contentUrl")
            elif isinstance(bild_roh, str) and bild_roh.startswith("http"):
                bild_url = bild_roh
            else:
                bild_url = None

            # Preis aus Angebotsdaten
            preis = None
            angebote = eintrag.get("offers", [])
            if isinstance(angebote, dict):
                angebote = [angebote]
            if angebote:
                preise = [str(a.get("price", "")) for a in angebote if a.get("price")]
                if preise:
                    preis = f"ab {preise[0]}€" if len(preise) == 1 else f"{min(preise)}–{max(preise)}€"

            schluessel = f"{titel}_{datum}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ort,
                "adresse": None,
                "kategorie": KATEGORIE_STANDARD,
                "beschreibung": beschreibung,
                "preis": preis,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "instagram_caption": None,
                "datum_bis": None,
                "ist_wiederkehrend": False,
                "status": "neu",
            })

    return events


def _kandidaten_rekursiv_suchen(data: dict | list) -> list[dict]:
    """
    Durchsucht Next.js __NEXT_DATA__ rekursiv nach Event-Einträgen.

    Args:
        data: JSON-Datenstruktur

    Returns:
        Liste von Event-Kandidaten
    """
    kandidaten: list[dict] = []
    if isinstance(data, list):
        for eintrag in data:
            if isinstance(eintrag, dict):
                hat_titel = any(k in eintrag for k in ["title", "titel", "name", "headline"])
                hat_datum = any(k in eintrag for k in ["startDate", "date", "datum", "start"])
                if hat_titel and hat_datum:
                    kandidaten.append(eintrag)
                else:
                    kandidaten.extend(_kandidaten_rekursiv_suchen(eintrag))
    elif isinstance(data, dict):
        for wert in data.values():
            if isinstance(wert, (dict, list)):
                kandidaten.extend(_kandidaten_rekursiv_suchen(wert))
    return kandidaten


def _events_aus_next_data(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    Fallback: __NEXT_DATA__ aus Next.js-App extrahieren.

    Args:
        soup: Geparste HTML-Seite
        heute: Heute-Datum für Filterung

    Returns:
        Liste von Event-Dicts
    """
    next_script = soup.find("script", id="__NEXT_DATA__")
    if not next_script:
        return []

    try:
        next_data = json.loads(next_script.string or "{}")
    except json.JSONDecodeError:
        return []

    kandidaten = _kandidaten_rekursiv_suchen(next_data.get("props", {}))
    if not kandidaten:
        return []

    events = []
    gesehene_schluessel: set[str] = set()

    for eintrag in kandidaten:
        titel = (
            eintrag.get("title") or eintrag.get("titel")
            or eintrag.get("name") or eintrag.get("headline", "")
        )
        if not isinstance(titel, str) or not titel.strip():
            continue
        titel = titel.strip()

        datum_roh = eintrag.get("startDate") or eintrag.get("date") or eintrag.get("datum")
        datum = _datum_parsen(str(datum_roh)) if datum_roh else None
        if not datum or date.fromisoformat(datum) < heute:
            continue

        uhrzeit = _uhrzeit_parsen(str(datum_roh))

        ort_roh = eintrag.get("location") or eintrag.get("venue") or ""
        if isinstance(ort_roh, dict):
            ort_roh = ort_roh.get("name", "")
        ort = _ort_erkennen(str(ort_roh)) if ort_roh else ORT_STANDARD

        slug = eintrag.get("slug") or eintrag.get("id")
        quelle_url = f"{BASE_URL}/programm/{slug}" if slug else PROGRAMM_URL

        beschreibung_roh = eintrag.get("description") or eintrag.get("teaser")
        beschreibung = str(beschreibung_roh).strip()[:300] if beschreibung_roh else None

        bild_url = None
        bild_roh = eintrag.get("image") or eintrag.get("thumbnail")
        if isinstance(bild_roh, dict):
            bild_url = bild_roh.get("url") or bild_roh.get("src")
        elif isinstance(bild_roh, str) and bild_roh.startswith("http"):
            bild_url = bild_roh

        schluessel = f"{titel}_{datum}"
        if schluessel in gesehene_schluessel:
            continue
        gesehene_schluessel.add(schluessel)

        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": None,
            "kategorie": KATEGORIE_STANDARD,
            "beschreibung": beschreibung,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        })

    return events


def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen des FFT Düsseldorf.

    Strategie:
    1. JSON-LD structured data
    2. __NEXT_DATA__ (Next.js)

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = seite_abrufen(PROGRAMM_URL, logger)
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")

        events = _events_aus_json_ld(soup, heute)
        logger.info("JSON-LD: %d Events gefunden", len(events))

        if not events:
            logger.warning("JSON-LD leer – versuche __NEXT_DATA__")
            events = _events_aus_next_data(soup, heute)
            logger.info("Next.js: %d Events gefunden", len(events))

        events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]
        logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
        return events

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(fehler))
        return []


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json as _json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
