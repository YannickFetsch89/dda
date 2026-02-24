"""
tonhalle.py – DiesDasDüsseldorf
Scraper für die Tonhalle Düsseldorf: Konzerte und Veranstaltungen.

Primärquelle: Webshop der Tonhalle (webshop.tonhalle.de/list/events)
  → Server-seitig gerendertes HTML mit vollständigen Event-Daten.
  → CSS-Struktur: .main_content > .content_element > .content > .group

Fallbackquelle: Hauptseite (tonhalle.de/das-programm)
  → Next.js-App mit __NEXT_DATA__ JSON im Script-Tag.

Erstellt: 2026-02-24
"""
import json
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

# --- Konstanten -----------------------------------------------------------

WEBSHOP_URL = "https://webshop.tonhalle.de/list/events"
HAUPTSEITE_URL = "https://www.tonhalle.de/das-programm"
KALENDER_URL = "https://www.tonhalle.de/veranstaltungen/kalender"
WEBSHOP_BASE = "https://webshop.tonhalle.de"
HAUPTSEITE_BASE = "https://www.tonhalle.de"

QUELLE_NAME = "Tonhalle Düsseldorf"
ORT_STANDARD = "Tonhalle Düsseldorf"
ADRESSE_STANDARD = "Ehrenhof 1, 40479 Düsseldorf"
KATEGORIE_STANDARD = "musik"

# Monatsnamen auf Deutsch und Englisch (Webshop kann beide liefern)
MONAT_MAP: dict[str, int] = {
    # Deutsch
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
    # Englisch (Webshop liefert manchmal englische Monatsnamen)
    "january": 1, "february": 2, "march": 3,
    "june": 6, "july": 7, "october": 10,
}

MONAT_KURZ_MAP: dict[str, int] = {
    "jan": 1, "feb": 2, "mär": 3, "mar": 3, "apr": 4,
    "mai": 5, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}


# --- Hilfsfunktionen: Datum und Uhrzeit -----------------------------------

def _datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt verschiedene Datumsformate in ISO 8601 (YYYY-MM-DD) um.

    Unterstützte Formate:
        - "2026-02-24"               → "2026-02-24"   (ISO bereits vorhanden)
        - "24.02.2026"               → "2026-02-24"   (deutsches Format)
        - "24. Februar 2026"         → "2026-02-24"   (ausgeschrieben)
        - "Sonntag 8. März 2026"     → "2026-03-08"   (Webshop-Format)
        - "Sunday 8 March 2026"      → "2026-03-08"   (englisches Webshop-Format)
        - "24. Feb" / "24. Feb."     → nächstes passendes Datum

    Args:
        text: Roher Datumstext von der Webseite

    Returns:
        Datum als ISO-String (YYYY-MM-DD) oder None bei Fehler
    """
    if not text:
        return None

    heute = date.today()
    bereinigt = text.strip()
    bereinigt_klein = bereinigt.lower()

    try:
        # Format: "2026-02-24" (ISO bereits vorhanden)
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(1)),
                int(treffer.group(2)),
                int(treffer.group(3)),
            ).isoformat()

        # Format: "24.02.2026"
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(3)),
                int(treffer.group(2)),
                int(treffer.group(1)),
            ).isoformat()

        # Format: "Sonntag 8. März 2026" oder "Sunday 8 March 2026"
        # oder "24. März 2026" oder "24. february 2026"
        treffer = re.search(
            r"(\d{1,2})\.?\s+([a-zäöüß]+)\s+(\d{4})",
            bereinigt_klein,
        )
        if treffer:
            tag = int(treffer.group(1))
            monat_name = treffer.group(2).lower()
            jahr = int(treffer.group(3))
            monat = MONAT_MAP.get(monat_name)
            if monat:
                try:
                    return date(jahr, monat, tag).isoformat()
                except ValueError:
                    pass

        # Format ohne Jahr: "24.02." – nächstes passendes Datum ermitteln
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.", bereinigt)
        if treffer:
            tag = int(treffer.group(1))
            monat = int(treffer.group(2))
            jahr = heute.year
            try:
                kandidat = date(jahr, monat, tag)
            except ValueError:
                return None
            if kandidat < heute - timedelta(days=1):
                kandidat = date(jahr + 1, monat, tag)
            return kandidat.isoformat()

        # Format ohne Jahr: "24. Feb" oder "24. Feb." (Kurzform)
        treffer = re.search(r"(\d{1,2})\.\s*([a-zäöü]{3})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat_kurz = treffer.group(2)[:3].lower()
            monat = MONAT_KURZ_MAP.get(monat_kurz)
            if monat:
                jahr = heute.year
                try:
                    kandidat = date(jahr, monat, tag)
                except ValueError:
                    return None
                if kandidat < heute - timedelta(days=1):
                    kandidat = date(jahr + 1, monat, tag)
                return kandidat.isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning(
            "Datum konnte nicht geparst werden: '%s' – %s", text, fehler
        )
        return None

    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """
    Extrahiert eine Uhrzeit (HH:MM) aus einem beliebigen Text.

    Unterstützte Formate: "19:30", "20.00", "20:00 Uhr"

    Args:
        text: Roher Text mit möglicher Zeitangabe

    Returns:
        Uhrzeit als HH:MM-String oder None
    """
    if not text:
        return None

    treffer = re.search(
        r"\b(\d{1,2})[:\.](\d{2})\s*(?:Uhr)?", text, re.IGNORECASE
    )
    if treffer:
        stunde = int(treffer.group(1))
        minute = int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"
    return None


def _ort_aus_saalname(saalname: str) -> str:
    """
    Mappt einen Saalname der Tonhalle auf den vollständigen Ortsstring.

    Args:
        saalname: Rohtext, z.B. "Mendelssohn-Saal" oder "Rotunde"

    Returns:
        Vollständiger Ort, z.B. "Tonhalle Düsseldorf – Mendelssohn-Saal"
    """
    if not saalname:
        return ORT_STANDARD

    bekannte_saele = [
        "mendelssohn", "rotunde", "saal", "foyer", "terrasse",
    ]
    saalname_klein = saalname.lower()

    for saal in bekannte_saele:
        if saal in saalname_klein:
            # Saalname bereinigen und mit Venue kombinieren
            bereinigt = saalname.strip()
            # Bereits vollständig, wenn "Tonhalle" drin steht
            if "tonhalle" in saalname_klein:
                return bereinigt
            return f"Tonhalle Düsseldorf – {bereinigt}"

    return ORT_STANDARD


# --- Primärstrategie: Webshop (webshop.tonhalle.de) -----------------------

def _event_aus_webshop_gruppe(gruppe_el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einer Gruppe (.group) des Webshops.

    Der Webshop (SecuTix) rendert Events in diesem DOM-Muster:
        <div class="group">
          <h4><a href="/selection/event/date?productId=NNNN">Titel</a></h4>
          <div>Untertitel / Beschreibung</div>
          <div>Datum-Uhrzeit-String (z.B. "Sonntag 8. März 2026 16:30")</div>
          <div>Saalname (z.B. "Tonhalle Mendelssohn-Saal")</div>
          <a href="/selection/event/date?productId=NNNN">Auswählen</a>
        </div>

    Args:
        gruppe_el: BeautifulSoup-Element mit class="group"
        heute:     Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None wenn Pflichtfelder fehlen / Event vergangen
    """
    try:
        # --- Titel und URL aus dem h4-Link ---
        titel_link = gruppe_el.select_one("h4 a[href]")
        if not titel_link:
            # Fallback: erster Link in der Gruppe
            titel_link = gruppe_el.select_one("a[href]")
        if not titel_link:
            return None

        titel = titel_link.get_text(strip=True)
        if not titel:
            return None

        href = titel_link.get("href", "")
        if href.startswith("/"):
            quelle_url = WEBSHOP_BASE + href
        elif href.startswith("http"):
            quelle_url = href
        else:
            quelle_url = WEBSHOP_URL

        # --- Alle Textinhalte der Kind-Divs sammeln ---
        kind_divs = gruppe_el.find_all("div", recursive=False)
        texte = [d.get_text(strip=True) for d in kind_divs if d.get_text(strip=True)]

        # --- Datum und Uhrzeit ---
        # Der Datum-String enthält Monatsnamen und Jahreszahl, z.B.:
        # "Sonntag 8. März 2026 16:30" oder "Sunday 8 March 2026 20:00"
        datum = None
        uhrzeit = None

        for text in texte:
            # Datum suchen: Muss Jahreszahl enthalten oder deutsches Format
            hat_jahreszahl = bool(re.search(r"\b20\d{2}\b", text))
            hat_punkt_datum = bool(re.search(r"\d{1,2}\.\d{2}\.", text))
            monat_in_text = any(
                m in text.lower()
                for m in list(MONAT_MAP.keys()) + list(MONAT_KURZ_MAP.keys())
            )

            if hat_jahreszahl or hat_punkt_datum or monat_in_text:
                kandidat = _datum_parsen(text)
                if kandidat and not datum:
                    datum = kandidat
                    # Uhrzeit aus demselben String extrahieren
                    uhrzeit = _uhrzeit_parsen(text)
                    break

        if not datum:
            logger.debug("Kein Datum für Event '%s' gefunden", titel)
            return None

        # Vergangene Events überspringen
        if date.fromisoformat(datum) < heute:
            return None

        # --- Saalname / Ort ---
        ort = ORT_STANDARD
        for text in texte:
            text_klein = text.lower()
            if any(
                kw in text_klein
                for kw in ["saal", "tonhalle", "rotunde", "foyer"]
            ):
                ort = _ort_aus_saalname(text)
                break

        # --- Beschreibung: zweiter Textinhalt (Untertitel), falls vorhanden ---
        beschreibung = None
        nicht_datum_nicht_ort = [
            t for t in texte
            if t != titel
            and not re.search(r"\b20\d{2}\b", t)
            and not any(
                kw in t.lower()
                for kw in ["saal", "tonhalle", "rotunde", "auswählen"]
            )
        ]
        if nicht_datum_nicht_ort:
            beschreibung = nicht_datum_nicht_ort[0][:300] or None

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": ADRESSE_STANDARD,
            "kategorie": KATEGORIE_STANDARD,
            "beschreibung": beschreibung,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": None,
            "instagram_caption": None,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error(
            "Fehler beim Parsen einer Webshop-Gruppe: %s", str(fehler)
        )
        return None


def _scrape_webshop(heute: date) -> list[dict]:
    """
    Scrapt Events vom Tonhalle-Webshop (primäre Strategie).

    Der Webshop unter webshop.tonhalle.de/list/events ist server-seitig
    gerendert (SecuTix-System) und enthält strukturierte Event-Einträge.

    Args:
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Liste von Event-Dicts oder leere Liste bei Fehler
    """
    logger.info("Primärstrategie: Webshop-Scraping von %s", WEBSHOP_URL)

    try:
        html = seite_abrufen(WEBSHOP_URL, logger)
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Primärsuche: .group-Elemente innerhalb von .content_element
        gruppen = soup.select(".main_content .group")

        # Fallback 1: alle .group-Elemente auf der Seite
        if not gruppen:
            gruppen = soup.select(".group")

        # Fallback 2: div-Elemente die einen h4 mit Link enthalten
        if not gruppen:
            gruppen = [
                el.parent
                for el in soup.select("h4 a[href*='productId']")
                if el.parent
            ]

        if not gruppen:
            logger.warning(
                "Webshop: Keine Event-Gruppen gefunden – "
                "Seitenstruktur möglicherweise geändert."
            )
            return []

        logger.info(
            "Webshop: %d potenzielle Event-Gruppen gefunden", len(gruppen)
        )

        events: list[dict] = []
        gesehene_urls: set[str] = set()

        for gruppe in gruppen:
            event = _event_aus_webshop_gruppe(gruppe, heute)
            if event is None:
                continue

            url = event["quelle_url"]
            if url in gesehene_urls:
                continue
            gesehene_urls.add(url)
            events.append(event)

        logger.info("Webshop-Scraping: %d Events gefunden", len(events))
        return events

    except Exception as fehler:
        logger.error(
            "Webshop-Scraping fehlgeschlagen: %s", str(fehler)
        )
        return []


# --- Fallbackstrategie: __NEXT_DATA__ der Hauptseite ----------------------

def _event_aus_next_data(eintrag: dict, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem Next.js pageProps-Eintrag.

    Die Tonhalle-Hauptseite (Next.js) kann Event-Daten als JSON in einem
    <script id="__NEXT_DATA__">-Tag einbetten.

    Args:
        eintrag: Einzelner Event-Eintrag aus dem Next.js JSON
        heute:   Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None
    """
    try:
        # Titel aus verschiedenen möglichen Schlüsseln
        titel = (
            eintrag.get("title")
            or eintrag.get("titel")
            or eintrag.get("name")
            or eintrag.get("headline")
        )
        if not titel or not isinstance(titel, str):
            return None
        titel = titel.strip()
        if not titel:
            return None

        # Datum
        datum_roh = (
            eintrag.get("startDate")
            or eintrag.get("date")
            or eintrag.get("datum")
            or eintrag.get("startDateTime")
            or eintrag.get("start")
        )
        datum = _datum_parsen(str(datum_roh)) if datum_roh else None
        if not datum:
            return None

        if date.fromisoformat(datum) < heute:
            return None

        # Uhrzeit
        uhrzeit_roh = (
            eintrag.get("startTime")
            or eintrag.get("time")
            or eintrag.get("uhrzeit")
            or datum_roh
        )
        uhrzeit = _uhrzeit_parsen(str(uhrzeit_roh)) if uhrzeit_roh else None

        # URL
        slug = eintrag.get("slug") or eintrag.get("uuid") or eintrag.get("id")
        if slug:
            quelle_url = f"{HAUPTSEITE_BASE}/veranstaltungen/{slug}"
        else:
            quelle_url = HAUPTSEITE_URL

        # Ort
        ort_roh = eintrag.get("location") or eintrag.get("ort") or eintrag.get("venue")
        if ort_roh and isinstance(ort_roh, dict):
            ort_roh = ort_roh.get("name") or ort_roh.get("title") or ""
        ort = _ort_aus_saalname(str(ort_roh)) if ort_roh else ORT_STANDARD

        # Beschreibung
        beschreibung_roh = (
            eintrag.get("description")
            or eintrag.get("beschreibung")
            or eintrag.get("teaser")
            or eintrag.get("subtitle")
        )
        beschreibung = str(beschreibung_roh).strip()[:300] if beschreibung_roh else None

        # Bild
        bild_url = None
        bild_roh = eintrag.get("image") or eintrag.get("bild") or eintrag.get("thumbnail")
        if isinstance(bild_roh, dict):
            bild_url = bild_roh.get("url") or bild_roh.get("src")
        elif isinstance(bild_roh, str) and bild_roh.startswith("http"):
            bild_url = bild_roh

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": ADRESSE_STANDARD,
            "kategorie": KATEGORIE_STANDARD,
            "beschreibung": beschreibung,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error(
            "Fehler beim Parsen eines Next.js-Eintrags: %s", str(fehler)
        )
        return None


def _next_data_durchsuchen(data: dict | list, pfad: str = "") -> list[dict]:
    """
    Durchsucht ein Next.js __NEXT_DATA__ JSON-Objekt rekursiv nach
    Event-artigen Einträgen (Listen von Dicts mit Titel und Datum).

    Args:
        data: JSON-Datenstruktur (Dict oder Liste)
        pfad: Aktueller JSON-Pfad für Logging

    Returns:
        Liste von Event-Dict-Kandidaten
    """
    kandidaten: list[dict] = []

    if isinstance(data, list):
        for i, eintrag in enumerate(data):
            if isinstance(eintrag, dict):
                # Prüfen ob es ein Event-artiger Eintrag ist
                hat_titel = any(k in eintrag for k in ["title", "titel", "name", "headline"])
                hat_datum = any(
                    k in eintrag
                    for k in ["startDate", "date", "datum", "startDateTime", "start"]
                )
                if hat_titel and hat_datum:
                    kandidaten.append(eintrag)
                else:
                    # Rekursiv in verschachtelten Strukturen suchen
                    kandidaten.extend(
                        _next_data_durchsuchen(eintrag, f"{pfad}[{i}]")
                    )
    elif isinstance(data, dict):
        for schluessel, wert in data.items():
            if isinstance(wert, (dict, list)):
                kandidaten.extend(
                    _next_data_durchsuchen(wert, f"{pfad}.{schluessel}")
                )

    return kandidaten


def _scrape_hauptseite(heute: date) -> list[dict]:
    """
    Fallbackstrategie: Scrapt Events von der Tonhalle-Hauptseite.

    Versucht __NEXT_DATA__ JSON aus dem Script-Tag zu extrahieren und
    Event-Einträge darin zu finden. Die Hauptseite ist eine Next.js-App
    (tonhalle.de) die Event-Daten clientseitig lädt – dieser Fallback
    greift nur wenn die Daten im initialen pageProps-Objekt vorhanden sind.

    Args:
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Liste von Event-Dicts oder leere Liste
    """
    logger.info("Fallback: Hauptseiten-Scraping von %s", HAUPTSEITE_URL)

    try:
        html = seite_abrufen(HAUPTSEITE_URL, logger)
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # __NEXT_DATA__ JSON-Script-Tag suchen
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        if next_data_script:
            try:
                next_data = json.loads(next_data_script.string or "{}")
                kandidaten = _next_data_durchsuchen(
                    next_data.get("props", {})
                )
                if kandidaten:
                    logger.info(
                        "Fallback: %d Event-Kandidaten in __NEXT_DATA__ "
                        "gefunden",
                        len(kandidaten),
                    )
                    events: list[dict] = []
                    gesehene_urls: set[str] = set()
                    for eintrag in kandidaten:
                        event = _event_aus_next_data(eintrag, heute)
                        if event is None:
                            continue
                        url = event["quelle_url"]
                        if url not in gesehene_urls:
                            gesehene_urls.add(url)
                            events.append(event)
                    logger.info(
                        "Fallback Hauptseite: %d Events gefunden", len(events)
                    )
                    return events
            except json.JSONDecodeError as fehler:
                logger.warning(
                    "Fallback: __NEXT_DATA__ konnte nicht geparst werden: %s",
                    str(fehler),
                )

        # Letzter Versuch: strukturierte Datums-Texte im HTML suchen
        logger.info(
            "Fallback: Suche nach Datums-Texten im rohen HTML von %s",
            HAUPTSEITE_URL,
        )
        events_aus_html = _scrape_html_fallback(soup, heute)
        if events_aus_html:
            return events_aus_html

        logger.warning(
            "Fallback Hauptseite: Keine Events gefunden – "
            "Seite vermutlich vollständig clientseitig gerendert."
        )
        return []

    except Exception as fehler:
        logger.error(
            "Fallback Hauptseiten-Scraping fehlgeschlagen: %s", str(fehler)
        )
        return []


def _scrape_html_fallback(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    Letzter Fallback: Sucht direkt nach Datum-Mustern im HTML.

    Versucht Event-Einträge anhand von typischen DOM-Mustern zu finden:
    - Artikel- oder Listenelemente mit Datumsangaben
    - Elemente mit itemprop="startDate"
    - Divs/Articles mit Datum-Klassen

    Args:
        soup:  BeautifulSoup-Objekt der bereits geladenen Seite
        heute: Heutiges Datum

    Returns:
        Liste von Event-Dicts (kann leer sein)
    """
    events: list[dict] = []
    gesehene_schluessel: set[str] = set()

    # Strategie 1: itemprop="startDate"
    datum_els = soup.select("[itemprop='startDate']")
    for datum_el in datum_els:
        try:
            datum_text = (
                datum_el.get("content", "")
                or datum_el.get("datetime", "")
                or datum_el.get_text(strip=True)
            )
            datum = _datum_parsen(datum_text)
            if not datum or date.fromisoformat(datum) < heute:
                continue

            # Titel aus itemprop="name" suchen
            container = datum_el.find_parent(
                ["article", "li", "div", "section"]
            )
            if not container:
                continue
            titel_el = container.select_one("[itemprop='name'], h1, h2, h3, h4")
            if not titel_el:
                continue
            titel = titel_el.get_text(strip=True)
            if not titel:
                continue

            schluessel = f"{titel}_{datum}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            # URL
            link = container.find("a", href=True)
            quelle_url = (
                urljoin(HAUPTSEITE_BASE, link["href"])
                if link
                else HAUPTSEITE_URL
            )

            uhrzeit_el = container.select_one("[itemprop='startDate']")
            uhrzeit = (
                _uhrzeit_parsen(uhrzeit_el.get("content", ""))
                if uhrzeit_el
                else None
            )

            bild_el = container.select_one("img")
            bild_url = None
            if bild_el:
                bild_url = (
                    bild_el.get("data-src")
                    or bild_el.get("src")
                    or bild_el.get("data-lazy-src")
                )
                if bild_url and not bild_url.startswith("http"):
                    bild_url = urljoin(HAUPTSEITE_BASE, bild_url)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ORT_STANDARD,
                "adresse": ADRESSE_STANDARD,
                "kategorie": KATEGORIE_STANDARD,
                "beschreibung": None,
                "preis": None,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "instagram_caption": None,
                "status": "neu",
            })
        except Exception as fehler:
            logger.debug("HTML-Fallback Parsing-Fehler: %s", str(fehler))
            continue

    return events


# --- Hauptfunktion --------------------------------------------------------

def scrape() -> list[dict]:
    """
    Scrapt Events von der Tonhalle Düsseldorf.

    Strategie:
    1. Primär: Webshop (webshop.tonhalle.de/list/events) – server-seitig
       gerendertes HTML mit vollständiger Event-Liste.
    2. Fallback: Hauptseite (tonhalle.de/das-programm) – Next.js-App mit
       __NEXT_DATA__ JSON und HTML-Fallback.

    Filtert vergangene Events heraus und verhindert Duplikate.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events: list[dict] = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    # --- Primärstrategie: Webshop ---
    try:
        events = _scrape_webshop(heute)
    except Exception as fehler:
        logger.error("Webshop-Strategie unerwartet fehlgeschlagen: %s", str(fehler))
        events = []

    # --- Fallback: Hauptseite ---
    if not events:
        logger.warning(
            "Webshop-Scraping lieferte keine Events – "
            "starte Fallback auf Hauptseite."
        )
        try:
            events = _scrape_hauptseite(heute)
        except Exception as fehler:
            logger.error(
                "Hauptseiten-Fallback unerwartet fehlgeschlagen: %s", str(fehler)
            )
            events = []

    # --- Abschluss-Log ---
    if not events:
        logger.warning(
            "Scraper %s: 0 Events gefunden – "
            "alle Strategien ohne Ergebnis.",
            QUELLE_NAME,
        )
    else:
        logger.info(
            "Scraper %s fertig: %d Events gefunden",
            QUELLE_NAME,
            len(events),
        )

    return events


# --- Testblock ------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json as _json

    ergebnisse = scrape()

    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")

    if ergebnisse:
        print("Beispiel-Event (erstes gefundenes):")
        print(_json.dumps(ergebnisse[0], ensure_ascii=False, indent=2))
    else:
        print("Keine Events gefunden.")
