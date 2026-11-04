"""
classic_remise.py – DiesDasDüsseldorf
Scraper für die Classic Remise Düsseldorf.

Scrapt Oldtimer- und Kulturveranstaltungen der Classic Remise Düsseldorf,
einem einzigartigen Automobil-Kulturzentrum im historischen Lokschuppen.

Hintergrund (Stand 2026-11):
  Die alte Domain classic-remise.de leitet per HTTP 301 auf remise.de um;
  per HTTPS scheitert dort bereits der TLS-Handshake (deshalb lieferte der alte
  Playwright-Scraper nichts). /veranstaltungen/ existiert nicht mehr (404).
  Termine stehen jetzt als statische Tabelle auf
  https://remise.de/duesseldorf/news-und-termine („Classic Remise Highlights <Jahr>“),
  gemeinsam für Berlin und Düsseldorf. Kein JSON-LD für Events, kein iCal.

Tabellenstruktur:
  <div class="table-row">
    <div class="cell" data-title="Datum">09.12.</div>            (auch "07.01. - 09.12.")
    <div class="cell" data-title="Ort">Düsseldorf</div>
    <div class="cell" data-title="Beschreibung">Titel (19:00 Uhr)</div>
    <div class="cell" data-title="Info"><a href="...">Details</a></div>
  </div>

Datumsangaben haben kein Jahr: Das Jahr kommt aus der Überschrift, ein
Jahreswechsel wird an fallenden Monaten in der (chronologischen) Liste erkannt.
Wiederkehrende Termine („JEDEN zweiten Mittwoch im Monat: …“) werden in
Einzeltermine aufgelöst.

URL: https://remise.de/duesseldorf/news-und-termine
Adresse: Harffstraße 110, 40591 Düsseldorf
Erstellt: 2026-03-06 · Überarbeitet: 2026-11-04 (Domainwechsel, neues HTML)
"""
import asyncio
import logging
import re
from datetime import date, timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import uhrzeit_parsen

logger = logging.getLogger(__name__)

LISTE_URL = "https://remise.de/duesseldorf/news-und-termine"
BASE_URL = "https://remise.de"
QUELLE_NAME = "Classic Remise"
ORT_STANDARD = "Classic Remise Düsseldorf"
ADRESSE_STANDARD = "Harffstraße 110, 40591 Düsseldorf"
KATEGORIE = "kultur"

# Wartezeit vor dem Request (Rate Limiting, Sekunden)
WARTEZEIT = 2.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

# Kategorie-Mapping für Classic Remise Events
KATEGORIE_MAPPING = {
    "konzert": "musik", "musik": "musik", "live": "musik",
    "party": "nightlife", "club": "nightlife",
    "ausstellung": "kultur", "kunst": "kultur", "galerie": "kultur",
    "ballett": "kultur", "theater": "kultur",
    "oldtimer": "kultur", "automobil": "kultur", "auto": "kultur",
    "film": "kultur", "kino": "kultur",
    "workshop": "community", "vortrag": "community", "meetup": "community",
    "treff": "community",
    "kinder": "family", "familie": "family",
    "whisky": "food", "brunch": "food",
    "essen": "food", "food": "food", "markt": "food",
    "sport": "sport", "rennen": "sport",
    "outdoor": "outdoor", "park": "outdoor",
}

WOCHENTAGE = {
    "montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3,
    "freitag": 4, "samstag": 5, "sonntag": 6,
}
ORDINALE = {
    "ersten": 1, "erster": 1, "1.": 1,
    "zweiten": 2, "zweiter": 2, "2.": 2,
    "dritten": 3, "dritter": 3, "3.": 3,
    "vierten": 4, "vierter": 4, "4.": 4,
    "letzten": -1, "letzter": -1,
}


def _kategorie_erkennen(text: str) -> str:
    """
    Erkennt die passende Kategorie anhand von Titel oder Beschreibung.

    Args:
        text: Titel oder Beschreibungstext des Events

    Returns:
        Gültige Kategorie als String
    """
    if not text:
        return KATEGORIE
    text_klein = text.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if schluessel in text_klein:
            return kategorie
    return KATEGORIE


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


def _tag_monat_liste(text: str) -> list[tuple[int, int]]:
    """
    Liest alle "TT.MM." Angaben aus einer Datumszelle.

    Args:
        text: Inhalt der Datumszelle, z.B. "07.01. - 09.12."

    Returns:
        Liste von (tag, monat)-Tupeln
    """
    return [(int(t), int(m)) for t, m in re.findall(r"(\d{1,2})\.(\d{1,2})\.", text)]


def _wiederholung_erkennen(titel: str) -> Optional[tuple[int, int]]:
    """
    Erkennt Muster wie "JEDEN zweiten Mittwoch im Monat" oder "JEDEN SONNTAG".

    Args:
        titel: Beschreibungstext der Tabellenzeile

    Returns:
        (ordinal, wochentag) – ordinal 0 = jede Woche, -1 = letzter im Monat –
        oder None, wenn keine Wiederholung erkannt wurde
    """
    klein = titel.lower()
    treffer = re.search(r"jede[nr]?\s+(?:(\S+)\s+)?(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)", klein)
    if not treffer:
        return None
    ordinal_wort = treffer.group(1)
    wochentag = WOCHENTAGE[treffer.group(2)]
    if ordinal_wort:
        ordinal = ORDINALE.get(ordinal_wort)
        if ordinal is None:
            return None
        return ordinal, wochentag
    return 0, wochentag


def _termine_expandieren(
    start: date, ende: date, ordinal: int, wochentag: int
) -> list[date]:
    """
    Löst eine Wiederholungsregel in konkrete Termine zwischen start und ende auf.

    Args:
        start:     Erster möglicher Tag
        ende:      Letzter möglicher Tag
        ordinal:   0 = jede Woche, 1–4 = n-ter Wochentag im Monat, -1 = letzter
        wochentag: 0 = Montag … 6 = Sonntag

    Returns:
        Liste der Termine (sortiert)
    """
    termine = []
    tag = start
    while tag <= ende:
        if tag.weekday() == wochentag:
            if ordinal == 0:
                termine.append(tag)
            elif ordinal > 0 and (tag.day - 1) // 7 + 1 == ordinal:
                termine.append(tag)
            elif ordinal == -1 and (tag + timedelta(days=7)).month != tag.month:
                termine.append(tag)
        tag += timedelta(days=1)
    return termine


def _titel_bereinigen(titel: str) -> str:
    """
    Entfernt Wiederholungs-Präfix und Uhrzeit-Klammer aus dem Titel.

    Args:
        titel: Roher Beschreibungstext

    Returns:
        Bereinigter Titel
    """
    bereinigt = re.sub(r"^\s*jede[nr]?\s+[^:]{0,40}:\s*", "", titel, flags=re.IGNORECASE)
    bereinigt = re.sub(r"\s*\(\s*\d{1,2}(?:[:.]\d{2})?\s*Uhr\s*\)", "", bereinigt, flags=re.IGNORECASE)
    return " ".join(bereinigt.split()).strip(" -–:")


def _events_aus_tabelle(html: str, heute: date, enddatum: date) -> list[dict]:
    """
    Extrahiert Düsseldorfer Termine aus der Tabelle „Classic Remise Highlights“.

    Args:
        html:     HTML-Quelltext der Seite
        heute:    Aktuelles Datum
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Event-Dicts
    """
    soup = BeautifulSoup(html, "html.parser")

    # Basisjahr aus der Überschrift "Classic Remise Highlights 2026"
    basisjahr = heute.year
    for kopf in soup.select(".news-headline"):
        treffer = re.search(r"Highlights\s+(\d{4})", kopf.get_text(" ", strip=True))
        if treffer:
            basisjahr = int(treffer.group(1))
            break

    zeilen = soup.select("div.table-row")
    logger.debug("Tabelle: %d Zeilen gefunden", len(zeilen))

    events = []
    gesehene_schluessel: set[str] = set()
    jahr = basisjahr
    letzter_monat = 0

    for zeile in zeilen:
        try:
            zellen = {
                (z.get("data-title") or "").strip().lower(): z
                for z in zeile.select("div.cell")
            }
            datum_zelle = zellen.get("datum")
            ort_zelle = zellen.get("ort")
            text_zelle = zellen.get("beschreibung")
            if not datum_zelle or not text_zelle:
                continue

            tage = _tag_monat_liste(datum_zelle.get_text(" ", strip=True))
            if not tage:
                continue

            # Jahreswechsel erkennen (Liste ist chronologisch nach Startdatum sortiert)
            start_tag, start_monat = tage[0]
            if start_monat < letzter_monat:
                jahr += 1
            letzter_monat = start_monat

            # Nur Düsseldorf (Liste enthält auch Berlin)
            ort_text = ort_zelle.get_text(" ", strip=True).lower() if ort_zelle else ""
            if "düsseldorf" not in ort_text and "duesseldorf" not in ort_text:
                continue

            roh_titel = " ".join(text_zelle.get_text(" ", strip=True).replace("\xa0", " ").split())
            titel = _titel_bereinigen(roh_titel)
            if not titel or len(titel) < 3:
                continue

            try:
                start = date(jahr, start_monat, start_tag)
            except ValueError:
                continue
            ende = start
            if len(tage) > 1:
                end_tag, end_monat = tage[1]
                end_jahr = jahr if end_monat >= start_monat else jahr + 1
                try:
                    ende = date(end_jahr, end_monat, end_tag)
                except ValueError:
                    ende = start

            wiederholung = _wiederholung_erkennen(roh_titel)
            if wiederholung and ende > start:
                ordinal, wochentag = wiederholung
                termine = _termine_expandieren(max(start, heute), min(ende, enddatum), ordinal, wochentag)
            elif ende > start:
                # Mehrtägiges Event ohne Regel: nur aufnehmen, wenn es im Fenster beginnt
                termine = [start] if heute <= start <= enddatum else []
            else:
                termine = [start] if heute <= start <= enddatum else []

            if not termine:
                continue

            uhrzeit = uhrzeit_parsen(roh_titel) if re.search(r"uhr", roh_titel, re.IGNORECASE) else None

            link_el = zellen.get("info").find("a", href=True) if zellen.get("info") else None
            quelle_url = link_el["href"] if link_el and link_el["href"].startswith("http") else LISTE_URL

            beschreibung = roh_titel if roh_titel != titel else None
            kategorie = _kategorie_erkennen(roh_titel)

            for termin in termine:
                datum = termin.isoformat()
                schluessel = f"{titel}_{datum}"
                if schluessel in gesehene_schluessel:
                    continue
                gesehene_schluessel.add(schluessel)

                events.append({
                    "titel": titel,
                    "datum": datum,
                    "uhrzeit": uhrzeit,
                    "ort": ORT_STANDARD,
                    "adresse": ADRESSE_STANDARD,
                    "kategorie": kategorie,
                    "beschreibung": _beschreibung_kuerzen(beschreibung) if beschreibung else None,
                    "preis": None,
                    "quelle_name": QUELLE_NAME,
                    "quelle_url": quelle_url,
                    "bild_url": None,
                    "bild_generiert": False,
                    "post_typ": "feed",
                    "instagram_caption": None,
                    "instagram_location_id": None,
                    "status": "neu",
                })

        except Exception as fehler:
            logger.error("Fehler beim Parsen einer Tabellenzeile: %s", str(fehler))
            continue

    return events


async def scrape() -> list[dict]:
    """
    Scrapt Oldtimer- und Kulturveranstaltungen der Classic Remise Düsseldorf.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    html = None
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            wartezeit = WARTEZEIT
            for versuch in range(3):
                await asyncio.sleep(wartezeit)
                antwort = await client.get(LISTE_URL)
                if antwort.status_code == 429:
                    wartezeit *= 2
                    logger.warning("HTTP 429 – warte %.0f s (Versuch %d)", wartezeit, versuch + 1)
                    continue
                antwort.raise_for_status()
                html = antwort.text
                break
    except httpx.HTTPStatusError as fehler:
        logger.error("HTTP Fehler %s beim Abrufen von %s", fehler.response.status_code, LISTE_URL)
    except Exception as fehler:
        logger.error("Scraper %s: Fehler beim Laden von %s: %s", QUELLE_NAME, LISTE_URL, str(fehler))

    if not html:
        logger.warning("Scraper %s: Kein HTML geladen – leere Liste wird zurückgegeben", QUELLE_NAME)
        return []

    events = _events_aus_tabelle(html, heute, enddatum)
    if not events:
        logger.warning("Scraper %s: Keine Düsseldorfer Termine im Zeitfenster gefunden", QUELLE_NAME)

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
