"""
stadtstrand.py – DiesDasDüsseldorf
Scraper für die Events des StadtStrand Düsseldorf.

Der StadtStrand bespielt im Sommer die Strände am Rheinufer (z.B. Tonhallenufer)
und im Winter die Indoor-Location "KLONKK" auf dem Factory Campus. Die Website
(Webflow) listet alle geplanten Events als Karten (Klasse "event19_item") mit
Kategorie-Tag, Standort, Datum/Uhrzeit ("13.11.2026 19:00") und Titel.

Saisonaler Hinweis: Liegen im Vorschauzeitraum keine Events, wird eine leere
Liste zurückgegeben und per INFO-Log als Saisonpause gekennzeichnet.

Strategie:
1. Event-Übersicht laden (httpx, statisches HTML, Rate Limiting über http_client)
2. Event-Karten parsen, abgesagte Events überspringen
3. Für Events im Vorschauzeitraum die Detailseite laden (Kurzbeschreibung)

URL: https://www.stadtstrand-duesseldorf.de/events
Erstellt: 2026-03-06
Überarbeitet: 2026-11-04 – Parser an Webflow-Struktur (event19_item) angepasst,
                            Standorte/Adressen, Absagen, Detail-Beschreibung
"""
import asyncio
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

LISTE_URL = "https://www.stadtstrand-duesseldorf.de/events"
BASE_URL = "https://www.stadtstrand-duesseldorf.de"
QUELLE_NAME = "Stadtstrand Düsseldorf"
ORT_STANDARD = "Stadtstrand Düsseldorf"
ADRESSE_STANDARD = "Am Rheinufer, 40213 Düsseldorf"
KATEGORIE = "outdoor"

# Maximale Anzahl Detailseiten pro Lauf (je Request min. 2 s Wartezeit)
MAX_DETAILSEITEN = 15

# Bekannte Standorte (Schlüssel: Standort-Text der Website in Kleinbuchstaben)
# Adresse KLONKK laut https://www.stadtstrand-duesseldorf.de/standorte/klonkk
STANDORTE = {
    "klonkk": ("KLONKK – StadtStrand Indoor-Location", "Factory Campus, Erkrather Straße 401, 40231 Düsseldorf"),
    "kl0nkk": ("KLONKK – StadtStrand Indoor-Location", "Factory Campus, Erkrather Straße 401, 40231 Düsseldorf"),
    "tonhallenufer": ("StadtStrand Tonhallenufer", "Tonhallenufer, Düsseldorf"),
    "mannesmannufer": ("StadtStrand Mannesmannufer", "Mannesmannufer, Düsseldorf"),
    "robert-lehr-ufer": ("StadtStrand Robert-Lehr-Ufer", "Robert-Lehr-Ufer, Düsseldorf"),
}

# Kategorie-Tags der Website → DiesDasDüsseldorf-Kategorien
TAG_MAPPING = {
    "musik": "musik", "konzert": "musik",
    "comedy": "kultur", "kunst": "kultur", "kultur": "kultur", "theater": "kultur", "lesung": "kultur",
    "tanz": "nightlife", "party": "nightlife", "drinks": "nightlife",
    "food": "food",
    "sport": "sport",
    "family": "family", "kinder": "family",
    "workshop": "community",
}

# Fallback: Schlüsselwörter im Titel
KATEGORIE_MAPPING = {
    "quiz": "community", "bingo": "community",
    "konzert": "musik", "musik": "musik", "live": "musik", "dj": "musik",
    "party": "nightlife", "club": "nightlife", "nacht": "nightlife", "fiesta": "nightlife",
    "festival": "musik", "comedy": "kultur",
    "sport": "sport", "volleyball": "sport", "fitness": "sport",
    "workshop": "community", "meetup": "community",
    "kinder": "family", "familie": "family",
    "essen": "food", "food": "food", "bbq": "food", "grill": "food",
    "strand": "outdoor", "rhein": "outdoor",
}

# "13.11.2026 19:00" bzw. "5.12.2026 18:00"
DATUM_REGEX = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+(\d{1,2}):(\d{2}))?")


def _text(element) -> str:
    """
    Liefert den bereinigten Text eines Elements.

    Args:
        element: BeautifulSoup-Element oder None

    Returns:
        Text mit normalisiertem Whitespace (leer bei None)
    """
    if element is None:
        return ""
    return " ".join(element.get_text(" ", strip=True).split())


def _beschreibung_kuerzen(text: str) -> str:
    """
    Kürzt eine Beschreibung auf maximal 300 Zeichen.

    Args:
        text: Roher Beschreibungstext

    Returns:
        Beschreibung mit maximal 300 Zeichen
    """
    if not text:
        return ""
    bereinigt = " ".join(text.split())
    return bereinigt[:300]


def _kategorie_erkennen(tag: str, titel: str) -> str:
    """
    Erkennt die Kategorie anhand des Website-Tags, ersatzweise anhand des Titels.

    "Family" wird nur übernommen, wenn der Titel nicht auf ein Erwachsenen-Format
    wie Bingo oder Pubquiz hinweist (die Website taggt diese ebenfalls als "Family").

    Args:
        tag:   Kategorie-Tag der Website (z.B. "Musik")
        titel: Event-Titel

    Returns:
        Gültige Kategorie als String
    """
    tag_klein = (tag or "").lower().strip()
    titel_klein = (titel or "").lower()

    kategorie = TAG_MAPPING.get(tag_klein)
    if kategorie and not (kategorie == "family" and ("bingo" in titel_klein or "quiz" in titel_klein)):
        return kategorie

    for schluessel, kat in KATEGORIE_MAPPING.items():
        if schluessel in titel_klein:
            return kat
    return KATEGORIE


def _standort_aufloesen(standort: str) -> tuple[str, str]:
    """
    Ordnet den Standort-Text der Website einem Venue-Namen und einer Adresse zu.

    Args:
        standort: Standort-Text der Karte (z.B. "klOnkk", "Tonhallenufer")

    Returns:
        Tupel (ort, adresse)
    """
    schluessel = (standort or "").lower().strip()
    if schluessel in STANDORTE:
        return STANDORTE[schluessel]
    if schluessel:
        return f"StadtStrand {standort.strip()}", ADRESSE_STANDARD
    return ORT_STANDARD, ADRESSE_STANDARD


def _ist_abgesagt(karte) -> bool:
    """
    Prüft, ob eine Event-Karte als abgesagt markiert ist.

    Webflow blendet leere Hinweise per Klasse "w-condition-invisible" aus; ein
    sichtbarer Hinweis mit "abgesagt" bedeutet eine Absage.

    Args:
        karte: BeautifulSoup-Element der Event-Karte

    Returns:
        True, wenn abgesagt
    """
    for hinweis in karte.select(".event19_notice-wrapper"):
        if "w-condition-invisible" in (hinweis.get("class") or []):
            continue
        text = _text(hinweis).lower()
        if "abgesagt" in text or "season closed" in text or "fällt aus" in text:
            return True
    return False


def _karte_parsen(karte) -> Optional[dict]:
    """
    Parst eine Event-Karte der Übersicht.

    Args:
        karte: BeautifulSoup-Element mit Klasse "event19_item"

    Returns:
        Dict mit titel, datum (date), uhrzeit, standort, tag, url, bild_url, abgesagt
        oder None, wenn Pflichtangaben fehlen
    """
    titel_el = karte.find(["h2", "h3", "h4"])
    titel = _text(titel_el)
    if len(titel) < 3:
        return None

    datum_obj = None
    uhrzeit = None
    standort = ""
    for meta in karte.select(".event19_meta-tag"):
        meta_text = _text(meta)
        treffer = DATUM_REGEX.search(meta_text)
        if treffer and datum_obj is None:
            try:
                datum_obj = date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1)))
            except ValueError:
                continue
            if treffer.group(4):
                uhrzeit = f"{int(treffer.group(4)):02d}:{treffer.group(5)}"
        elif meta_text and not standort:
            standort = meta_text
    if datum_obj is None:
        return None

    tag = _text(karte.select_one(".event19_category-wrapper"))

    link_el = karte.find("a", href=True)
    url = urljoin(BASE_URL, link_el["href"]) if link_el else LISTE_URL

    bild_url = None
    for bild_el in karte.select("img.event19_image"):
        if "w-condition-invisible" in (bild_el.get("class") or []):
            continue
        src = bild_el.get("src") or ""
        if src.startswith("http") and "placeholder" not in src.lower():
            bild_url = src
            break

    return {
        "titel": titel,
        "datum": datum_obj,
        "uhrzeit": uhrzeit,
        "standort": standort,
        "tag": tag,
        "url": url,
        "bild_url": bild_url,
        "abgesagt": _ist_abgesagt(karte),
    }


def _beschreibung_von_detailseite(url: str) -> Optional[str]:
    """
    Lädt die Detailseite eines Events und liest die Kurzbeschreibung.

    Args:
        url: URL der Detailseite

    Returns:
        Beschreibung (max. 300 Zeichen) oder None
    """
    html = seite_abrufen(url, logger)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")

    meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
    kurz = (meta.get("content") or "").strip() if meta else ""

    rich = soup.select_one(".w-richtext")
    lang = _text(rich) if rich else ""

    if kurz and lang:
        return _beschreibung_kuerzen(f"{kurz}. {lang}" if not kurz.endswith((".", "!", "?")) else f"{kurz} {lang}")
    return _beschreibung_kuerzen(kurz or lang) or None


async def scrape() -> list[dict]:
    """
    Scrapt die Events des StadtStrand Düsseldorf (Strand im Sommer, KLONKK im Winter).

    Liegen im Vorschauzeitraum keine Termine, wird eine leere Liste
    zurückgegeben (Saisonpause, kein Fehler).

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = await asyncio.to_thread(seite_abrufen, LISTE_URL, logger)
    except Exception as fehler:
        logger.error("Scraper %s: Abruf von %s fehlgeschlagen: %s", QUELLE_NAME, LISTE_URL, str(fehler))
        return []

    if not html:
        logger.warning("Scraper %s: Kein HTML geladen – leere Liste wird zurückgegeben", QUELLE_NAME)
        return []

    soup = BeautifulSoup(html, "html.parser")
    karten = soup.select(".event19_item")
    if not karten:
        logger.warning(
            "Scraper %s: Keine Event-Karten (.event19_item) gefunden – Seitenstruktur prüfen (%s)",
            QUELLE_NAME, LISTE_URL,
        )
        return []

    kandidaten = []
    gesehene_schluessel: set[str] = set()
    anzahl_geparst = 0
    anzahl_abgesagt = 0
    for karte in karten:
        try:
            daten = _karte_parsen(karte)
        except Exception as fehler:
            logger.error("Fehler beim Parsen einer Event-Karte: %s", str(fehler))
            continue
        if not daten:
            continue
        anzahl_geparst += 1

        if daten["datum"] < heute or daten["datum"] > enddatum:
            continue
        if daten["abgesagt"]:
            anzahl_abgesagt += 1
            logger.info("Überspringe abgesagtes Event: %s (%s)", daten["titel"], daten["datum"].isoformat())
            continue

        schluessel = f"{daten['titel']}_{daten['datum'].isoformat()}"
        if schluessel in gesehene_schluessel:
            continue
        gesehene_schluessel.add(schluessel)
        kandidaten.append(daten)

    if anzahl_geparst == 0:
        logger.warning(
            "Scraper %s: %d Karten gefunden, aber keine mit Titel und Datum – Seitenstruktur prüfen",
            QUELLE_NAME, len(karten),
        )
        return []

    events = []
    for index, daten in enumerate(kandidaten):
        beschreibung = None
        if index < MAX_DETAILSEITEN and daten["url"] != LISTE_URL:
            try:
                beschreibung = await asyncio.to_thread(_beschreibung_von_detailseite, daten["url"])
            except Exception as fehler:
                logger.warning("Detailseite %s nicht lesbar: %s", daten["url"], str(fehler))

        ort, adresse = _standort_aufloesen(daten["standort"])
        events.append({
            "titel": daten["titel"],
            "datum": daten["datum"].isoformat(),
            "uhrzeit": daten["uhrzeit"],
            "ort": ort,
            "adresse": adresse,
            "kategorie": _kategorie_erkennen(daten["tag"], daten["titel"]),
            "beschreibung": beschreibung,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": daten["url"],
            "bild_url": daten["bild_url"],
            "bild_generiert": False,
            "post_typ": "feed",
            "instagram_caption": None,
            "instagram_location_id": None,
            "status": "neu",
        })

    if not events:
        logger.info(
            "Scraper %s: Außerhalb der Saison – keine Termine im Vorschauzeitraum "
            "(%d Events auf der Seite, %d davon abgesagt im Zeitraum)",
            QUELLE_NAME, anzahl_geparst, anzahl_abgesagt,
        )
    else:
        logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))

    return events


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json as _json
    ergebnisse = asyncio.run(scrape())
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
