"""
tonhalle.py – DiesDasDüsseldorf
Scraper für die Tonhalle Düsseldorf: Konzerte und Veranstaltungen.

Primärquelle: Webshop der Tonhalle (webshop.tonhalle.de/list/events)
  → Server-seitig gerendertes HTML via SecuTix-Buchungssystem.
  → DOM-Struktur:
      <section class="product product_EVENT" id="prod_NNNN">
        <a class="title" href="/selection/event/date?productId=NNNN">Titel</a>
        <p class="date">
          <span class="unique">              ← Einzeltermin
            <span class="day">Do 1. März 2026</span>
            <span class="time">19:30</span>
          </span>
          |
          <span class="range">              ← Zeitraum (von...bis)
            <span class="from"><span class="day">...</span></span>
            <span class="to"><span class="day">...</span></span>
          </span>
        </p>
        <p class="location"><span class="space">Saalname</span></p>
        <span class="inline_name_addon">Untertitel</span>
        <img class="product_image" data-original="...">
      </section>

Fallbackquelle: Hauptseite (tonhalle.de/das-programm)
  → Next.js-App; greift auf __NEXT_DATA__ JSON zurück und durchsucht
    das initiale pageProps-Objekt nach Event-artigen Einträgen.

Erstellt: 2026-02-24
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

# --- Konstanten -----------------------------------------------------------

WEBSHOP_URL = "https://webshop.tonhalle.de/list/events"
HAUPTSEITE_URL = "https://www.tonhalle.de/das-programm"
WEBSHOP_BASE = "https://webshop.tonhalle.de"
HAUPTSEITE_BASE = "https://www.tonhalle.de"

QUELLE_NAME = "Tonhalle Düsseldorf"
ORT_STANDARD = "Tonhalle Düsseldorf"
ADRESSE_STANDARD = "Ehrenhof 1, 40479 Düsseldorf"
KATEGORIE_STANDARD = "musik"

# Monatsnamen Deutsch und Englisch (Webshop kann beides liefern)
MONAT_MAP: dict[str, int] = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
    "january": 1, "february": 2, "march": 3, "june": 6,
    "july": 7, "october": 10,
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
        - "Sunday 8 March 2026"      → "2026-03-08"   (englisches Format)
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

        # Format: "Sonntag 8. März 2026" / "Sunday 8 March 2026" / "24. März 2026"
        # Erkennt: optional Wochentag + Tag + Punkt(optional) + Monatsname + Jahr
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

    saalname_bereinigt = saalname.strip()
    saalname_klein = saalname_bereinigt.lower()

    # Bereits vollständig mit "Tonhalle"
    if "tonhalle" in saalname_klein:
        return saalname_bereinigt

    bekannte_saele = [
        "mendelssohn", "rotunde", "saal", "foyer", "terrasse",
        "trautvetter", "brückner",
    ]
    for saal in bekannte_saele:
        if saal in saalname_klein:
            return f"Tonhalle Düsseldorf – {saalname_bereinigt}"

    return ORT_STANDARD


# --- Primärstrategie: Webshop (webshop.tonhalle.de) -----------------------

def _event_aus_produkt_section(section_el, heute: date) -> list[dict]:
    """
    Extrahiert ein oder mehrere Event-Dicts aus einem Webshop-Produktelement.

    Die SecuTix-Oberfläche rendert jedes Event als
    <section class="product product_EVENT" id="prod_NNNN"> mit diesen Feldern:

      Titel:       <a class="title" href="/selection/event/date?productId=NNNN">
      Datum:       <p class="date">
                     <span class="unique">   → Einzeltermin
                       <span class="day">Wochentag TT. Monat YYYY</span>
                       <span class="time">HH:MM</span>
                     </span>
                     ODER
                     <span class="range">   → Zeitraum
                       <span class="from"><span class="day">...</span></span>
                       <span class="to"><span class="day">...</span></span>
                     </span>
      Ort:         <p class="location"><span class="space">Saalname</span>
      Beschreibung:<span class="inline_name_addon">Untertitel</span>
      Bild:        <img class="product_image" data-original="URL">

    Bei Zeitraum-Events (range) wird für jeden .day-Eintrag ein separates
    Event erzeugt, sofern er nicht in der Vergangenheit liegt.

    Args:
        section_el: BeautifulSoup <section class="product_EVENT"> Element
        heute:      Heutiges Datum für Filterung vergangener Events

    Returns:
        Liste von Event-Dicts (leer wenn Pflichtfelder fehlen oder alles vergangen)
    """
    try:
        # --- Titel und URL ---
        titel_link = section_el.select_one("a.title[href]")
        if not titel_link:
            # Kein klickbarer Titel → Produkt nicht buchbar / kein Event
            return []

        titel = titel_link.get_text(strip=True)
        if not titel:
            return []

        href = titel_link.get("href", "")
        if href.startswith("/"):
            quelle_url = WEBSHOP_BASE + href
        elif href.startswith("http"):
            quelle_url = href
        else:
            quelle_url = WEBSHOP_URL

        # --- Alle relevanten Datum-Strings sammeln ---
        datum_el = section_el.select_one("p.date")
        datums_texte: list[str] = []
        ist_range = False  # Ob die Datumsangabe ein Zeitraum (von...bis) ist

        if datum_el:
            # Einzeltermin: <span class="unique">
            einzel_span = datum_el.select_one("span.unique")
            if einzel_span:
                tag_span = einzel_span.select_one("span.day")
                if tag_span:
                    datums_texte.append(tag_span.get_text(strip=True))

            # Zeitraum: <span class="range"> – beide Endpunkte als separate Events
            # Markierung als Konzertreihe/wiederkehrendes Event
            bereich_span = datum_el.select_one("span.range")
            if bereich_span:
                ist_range = True
                for day_span in bereich_span.select("span.day"):
                    tag_text = day_span.get_text(strip=True)
                    if tag_text:
                        datums_texte.append(tag_text)

            # Fallback: alle .day-Spans direkt
            if not datums_texte:
                for day_span in datum_el.select("span.day"):
                    tag_text = day_span.get_text(strip=True)
                    if tag_text:
                        datums_texte.append(tag_text)

        if not datums_texte:
            logger.debug("Kein Datum für Event '%s' gefunden", titel)
            return []

        # Bei Range-Events: letztes Datum als datum_bis ermitteln
        datum_bis = None
        if ist_range and len(datums_texte) >= 2:
            datum_bis = _datum_parsen(datums_texte[-1])

        # --- Uhrzeit (aus erstem Einzel-Termin-Element) ---
        uhrzeit = None
        if datum_el:
            zeit_span = datum_el.select_one("span.time")
            if zeit_span:
                uhrzeit = _uhrzeit_parsen(zeit_span.get_text(strip=True))

        # --- Ort / Saalname ---
        ort = ORT_STANDARD
        ort_el = section_el.select_one("p.location span.space, .location_container span.space")
        if ort_el:
            ort = _ort_aus_saalname(ort_el.get_text(strip=True))

        # --- Beschreibung aus .inline_name_addon ---
        beschreibung = None
        addon_el = section_el.select_one("span.inline_name_addon")
        if addon_el:
            addon_text = addon_el.get_text(strip=True)
            # Punkte und bedeutungslose Platzhalter ignorieren
            if addon_text and addon_text not in [".", "–", "-", ""]:
                beschreibung = addon_text[:300]

        # --- Bild: data-original (lazy loading) oder src ---
        bild_url = None
        bild_el = section_el.select_one("img.product_image, img.lazy")
        if bild_el:
            bild_url = (
                bild_el.get("data-original")
                or bild_el.get("data-src")
                or bild_el.get("src")
            )
            if bild_url and not bild_url.startswith("http"):
                bild_url = urljoin(WEBSHOP_BASE, bild_url)

        # --- Für jeden Datums-Eintrag ein Event erstellen ---
        events: list[dict] = []
        for datum_text in datums_texte:
            datum = _datum_parsen(datum_text)
            if not datum:
                logger.debug(
                    "Datumsstring '%s' konnte nicht geparst werden "
                    "(Event: '%s')",
                    datum_text, titel,
                )
                continue

            # Vergangene Events überspringen
            if date.fromisoformat(datum) < heute:
                continue

            events.append({
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
                "datum_bis": datum_bis,
                "ist_wiederkehrend": ist_range,
                "status": "neu",
            })

        return events

    except Exception as fehler:
        logger.error(
            "Fehler beim Parsen einer Produkt-Section: %s", str(fehler)
        )
        return []


def _scrape_webshop(heute: date) -> list[dict]:
    """
    Scrapt Events vom Tonhalle-Webshop (primäre Strategie).

    Der Webshop (webshop.tonhalle.de/list/events) ist server-seitig
    gerendert via SecuTix und enthält alle buchbaren Events der Tonhalle.

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

        # Primärsuche: <section class="product product_EVENT">
        produkt_sections = soup.select("section.product_EVENT")

        # Fallback 1: sections mit data-product-type="EVENT"
        if not produkt_sections:
            produkt_sections = soup.select("section[data-product-type='EVENT']")

        # Fallback 2: alle sections mit id="prod_..."
        if not produkt_sections:
            produkt_sections = [
                s for s in soup.select("section[id^='prod_']")
            ]

        if not produkt_sections:
            logger.warning(
                "Webshop: Keine Event-Sections gefunden auf %s – "
                "Seitenstruktur möglicherweise geändert.",
                WEBSHOP_URL,
            )
            return []

        logger.info(
            "Webshop: %d Produkt-Sections gefunden", len(produkt_sections)
        )

        events: list[dict] = []
        # Deduplizierung anhand Titel+Datum-Kombination
        gesehene_schluessel: set[str] = set()

        for section in produkt_sections:
            event_liste = _event_aus_produkt_section(section, heute)
            for event in event_liste:
                schluessel = f"{event['titel']}_{event['datum']}"
                if schluessel in gesehene_schluessel:
                    continue
                gesehene_schluessel.add(schluessel)
                events.append(event)

        logger.info("Webshop-Scraping abgeschlossen: %d Events gefunden", len(events))
        return events

    except Exception as fehler:
        logger.error("Webshop-Scraping fehlgeschlagen: %s", str(fehler))
        return []


# --- Fallbackstrategie: __NEXT_DATA__ der Hauptseite ----------------------

def _event_aus_next_data_eintrag(eintrag: dict, heute: date) -> Optional[dict]:
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

        uhrzeit_roh = (
            eintrag.get("startTime")
            or eintrag.get("time")
            or eintrag.get("uhrzeit")
            or datum_roh
        )
        uhrzeit = _uhrzeit_parsen(str(uhrzeit_roh)) if uhrzeit_roh else None

        slug = eintrag.get("slug") or eintrag.get("uuid") or eintrag.get("id")
        quelle_url = (
            f"{HAUPTSEITE_BASE}/veranstaltungen/{slug}"
            if slug
            else HAUPTSEITE_URL
        )

        ort_roh = (
            eintrag.get("location")
            or eintrag.get("ort")
            or eintrag.get("venue")
        )
        if isinstance(ort_roh, dict):
            ort_roh = ort_roh.get("name") or ort_roh.get("title") or ""
        ort = _ort_aus_saalname(str(ort_roh)) if ort_roh else ORT_STANDARD

        beschreibung_roh = (
            eintrag.get("description")
            or eintrag.get("beschreibung")
            or eintrag.get("teaser")
            or eintrag.get("subtitle")
        )
        beschreibung = (
            str(beschreibung_roh).strip()[:300]
            if beschreibung_roh
            else None
        )

        bild_url = None
        bild_roh = (
            eintrag.get("image")
            or eintrag.get("bild")
            or eintrag.get("thumbnail")
        )
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
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error(
            "Fehler beim Parsen eines Next.js-Eintrags: %s", str(fehler)
        )
        return None


def _next_data_durchsuchen(data: dict | list) -> list[dict]:
    """
    Durchsucht ein Next.js __NEXT_DATA__ JSON-Objekt rekursiv nach
    Event-artigen Einträgen (Dicts mit Titel und Datum).

    Args:
        data: JSON-Datenstruktur (Dict oder Liste)

    Returns:
        Liste von Event-Dict-Kandidaten
    """
    kandidaten: list[dict] = []

    if isinstance(data, list):
        for eintrag in data:
            if isinstance(eintrag, dict):
                hat_titel = any(
                    k in eintrag
                    for k in ["title", "titel", "name", "headline"]
                )
                hat_datum = any(
                    k in eintrag
                    for k in ["startDate", "date", "datum", "startDateTime", "start"]
                )
                if hat_titel and hat_datum:
                    kandidaten.append(eintrag)
                else:
                    kandidaten.extend(_next_data_durchsuchen(eintrag))
    elif isinstance(data, dict):
        for wert in data.values():
            if isinstance(wert, (dict, list)):
                kandidaten.extend(_next_data_durchsuchen(wert))

    return kandidaten


def _scrape_hauptseite_fallback(heute: date) -> list[dict]:
    """
    Fallbackstrategie: Scrapt Events von der Tonhalle-Hauptseite.

    Versucht __NEXT_DATA__ JSON aus dem Script-Tag zu extrahieren und
    Event-Einträge darin zu finden. Die Hauptseite ist eine Next.js-App
    die Event-Daten clientseitig lädt – dieser Fallback greift nur wenn
    die Daten im initialen pageProps-Objekt vorhanden sind.

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
                        "Fallback: %d Event-Kandidaten in __NEXT_DATA__ gefunden",
                        len(kandidaten),
                    )
                    events: list[dict] = []
                    gesehene_schluessel: set[str] = set()
                    for eintrag in kandidaten:
                        event = _event_aus_next_data_eintrag(eintrag, heute)
                        if event is None:
                            continue
                        schluessel = f"{event['titel']}_{event['datum']}"
                        if schluessel not in gesehene_schluessel:
                            gesehene_schluessel.add(schluessel)
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


# --- Hauptfunktion --------------------------------------------------------

def scrape() -> list[dict]:
    """
    Scrapt Events von der Tonhalle Düsseldorf.

    Strategie:
    1. Primär: Webshop (webshop.tonhalle.de/list/events)
       → Server-seitig gerendertes SecuTix-HTML mit vollständiger Event-Liste.
       → Alle aktuellen und kommenden buchbaren Events.
    2. Fallback: Hauptseite (tonhalle.de/das-programm)
       → Next.js-App; greift auf __NEXT_DATA__ JSON zurück.
       → Nur wirksam wenn Event-Daten im initialen Payload vorhanden sind.

    Events werden gefiltert: vergangene Events werden übersprungen.
    Duplikate (gleicher Titel + Datum) werden innerhalb eines Laufs entfernt.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    # --- Primärstrategie: Webshop ---
    try:
        events = _scrape_webshop(heute)
    except Exception as fehler:
        logger.error(
            "Webshop-Strategie unerwartet fehlgeschlagen: %s", str(fehler)
        )
        events = []

    # --- Fallback: Hauptseite ---
    if not events:
        logger.warning(
            "Webshop-Scraping lieferte keine Events – "
            "starte Fallback auf Hauptseite."
        )
        try:
            events = _scrape_hauptseite_fallback(heute)
        except Exception as fehler:
            logger.error(
                "Hauptseiten-Fallback unerwartet fehlgeschlagen: %s", str(fehler)
            )
            events = []

    # --- Abschluss-Log ---
    if not events:
        logger.warning(
            "Scraper %s: 0 Events gefunden – alle Strategien ohne Ergebnis.",
            QUELLE_NAME,
        )
    else:
        # 14-Tage-Fenster: Events weiter als SCRAPER_VORSCHAU_TAGE in der Zukunft ausfiltern
        heute = date.today()
        enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
        events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]
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
