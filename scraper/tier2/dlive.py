"""
dlive.py – DiesDasDüsseldorf
Scraper für d.live Düsseldorf: Veranstaltungen in der Merkur Spiel-Arena
und dem PSD BANK DOME.

Die Eventseite (d-live.de/events/) ist vollständig JavaScript-gerendert
(clientseitiges EJS/Underscore.js-Templating). Daher wird Playwright
eingesetzt, um den JavaScript-Code auszuführen und die befüllten
Event-Karten im DOM zu lesen.

DOM-Struktur nach dem Rendering:
  <div class="calendar-entry col-...">
    <div class="card calendar-event state-[regular|sold-out|...]">
      <div class="event-date">
        <div class="date-fields ...">
          <p class="day">24</p>
          <p class="month">Feb</p>
          <p class="year">2026</p>
          <p class="day-name">Di</p>
        </div>
        <p class="time">20:00</p>
      </div>
      <a class="image-link stretched-link" href="/events/detail/...">
        <figure ...><img src="https://..." /></figure>
      </a>
      <div class="card-body">
        <p class="card-title fs-6 fw-bold"><a href="...">Titel</a></p>
        <figure class="figure mb-0 location-img">
          <img alt="Merkur Spiel-Arena" src="..." />
        </figure>
      </div>
    </div>
  </div>

Venue-Erkennung: Das alt-Attribut des Venue-Bilds enthält den Venue-Namen
(z.B. "Merkur Spiel-Arena", "PSD BANK DOME"). Als Fallback wird der
Venue-Name aus der Event-URL extrahiert.

Erstellt: 2026-02-24
"""
import logging
import re
import time
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# --- Konstanten -----------------------------------------------------------

BASE_URL = "https://www.d-live.de"
EVENTS_URL = "https://www.d-live.de/events/"
QUELLE_NAME = "d-live"
ORT_FALLBACK = "d-live Düsseldorf"

# Bekannte d.live-Venues mit ihren Adressen
VENUE_ADRESSEN: dict[str, str] = {
    "Merkur Spiel-Arena": "Arena-Straße 1, 40474 Düsseldorf",
    "PSD BANK DOME": "Siegburger Straße 15, 40591 Düsseldorf",
    "Mitsubishi Electric HALLE": "Siegburger Straße 15, 40591 Düsseldorf",
    "Rheinterrasse": "Joseph-Beuys-Ufer 33, 40479 Düsseldorf",
    "CASTELLO Düsseldorf": "Auf'm Hennekamp 71, 40225 Düsseldorf",
    "alltours Kino": "Arena-Straße 1, 40474 Düsseldorf",
}

# Venue-Namensfragmente für die Erkennung aus Alt-Text oder URL
VENUE_FRAGMENTE: dict[str, str] = {
    "merkur": "Merkur Spiel-Arena",
    "spiel-arena": "Merkur Spiel-Arena",
    "spiel arena": "Merkur Spiel-Arena",
    "psd bank dome": "PSD BANK DOME",
    "psd": "PSD BANK DOME",
    "dome": "PSD BANK DOME",
    "mitsubishi": "Mitsubishi Electric HALLE",
    "electric halle": "Mitsubishi Electric HALLE",
    "rheinterrasse": "Rheinterrasse",
    "castello": "CASTELLO Düsseldorf",
    "kino": "alltours Kino",
}

# Monatsabkürzungen und -namen (Deutsch + Englisch) für Datum-Parsing
MONAT_MAP: dict[str, int] = {
    # Deutsch lang
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
    # Englisch lang
    "january": 1, "february": 2, "march": 3,
    "june": 6, "july": 7, "october": 10, "december": 12,
}

MONAT_KURZ_MAP: dict[str, int] = {
    # Deutsch kurz
    "jan": 1, "feb": 2, "mär": 3, "mar": 3, "apr": 4,
    "mai": 5, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}

# Kategorie-Mapping: Schlüsselwort im Titel → DDA-Kategorie
KATEGORIE_MAP: dict[str, str] = {
    "konzert": "musik",
    "concert": "musik",
    "musik": "musik",
    "musik": "musik",
    "festival": "musik",
    "live": "musik",
    "tour": "musik",
    "dj": "musik",
    "club": "nightlife",
    "party": "nightlife",
    "nacht": "nightlife",
    "fußball": "sport",
    "fussball": "sport",
    "fortuna": "sport",
    "bundesliga": "sport",
    "champions league": "sport",
    "cup": "sport",
    "sport": "sport",
    "basketball": "sport",
    "eishockey": "sport",
    "hockey": "sport",
    "boxen": "sport",
    "kampf": "sport",
    "fight": "sport",
    "wrestling": "sport",
    "comedy": "kultur",
    "show": "sonstiges",
    "zirkus": "kultur",
    "circus": "kultur",
    "theater": "kultur",
    "oper": "kultur",
    "ballet": "kultur",
    "ballett": "kultur",
    "kino": "kultur",
    "film": "kultur",
    "family": "family",
    "familie": "family",
    "kinder": "family",
    "weihnacht": "family",
    "messe": "community",
    "expo": "community",
    "congress": "community",
    "konferenz": "community",
}


# --- Hilfsfunktionen: Parsing ---------------------------------------------

def _datum_parsen(tag_str: str, monat_str: str, jahr_str: str) -> Optional[str]:
    """
    Baut ein ISO-8601-Datum aus den drei separaten DOM-Feldern zusammen.

    Die d.live-Seite zeigt Tag, Monat und Jahr in getrennten <p>-Elementen.
    Monat kann als Zahl ("02"), Kurzname ("Feb") oder Langname ("Februar")
    vorliegen.

    Args:
        tag_str:   Text des <p class="day">-Elements (z.B. "24")
        monat_str: Text des <p class="month">-Elements (z.B. "Feb", "2")
        jahr_str:  Text des <p class="year">-Elements (z.B. "2026")

    Returns:
        Datum als ISO-String (YYYY-MM-DD) oder None bei Fehler
    """
    if not tag_str or not monat_str or not jahr_str:
        return None

    try:
        tag = int(re.sub(r"\D", "", tag_str))
        jahr_match = re.search(r"\d{4}", jahr_str)
        if not jahr_match:
            return None
        jahr = int(jahr_match.group())

        # Monat als Zahl?
        monat_roh = monat_str.strip().lower()
        if monat_roh.isdigit():
            monat = int(monat_roh)
        else:
            # Monat als Langname oder Kurzname
            monat = MONAT_MAP.get(monat_roh)
            if not monat:
                monat = MONAT_KURZ_MAP.get(monat_roh[:3])
            if not monat:
                logger.debug(
                    "Unbekannter Monatsname: '%s'", monat_str
                )
                return None

        return date(jahr, monat, tag).isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning(
            "Datum konnte nicht geparst werden: tag='%s' monat='%s' "
            "jahr='%s' – %s",
            tag_str, monat_str, jahr_str, fehler,
        )
        return None


def _datum_aus_volltext(text: str) -> Optional[str]:
    """
    Fallback-Datumsparsing aus beliebigem Text.

    Wird verwendet wenn die strukturierten Tag/Monat/Jahr-Felder fehlen.

    Unterstützte Formate:
        - "24.02.2026"          → "2026-02-24"
        - "2026-02-24"          → "2026-02-24"
        - "24. Februar 2026"    → "2026-02-24"

    Args:
        text: Beliebiger Text mit Datumsangabe

    Returns:
        Datum als ISO-String oder None
    """
    if not text:
        return None

    heute = date.today()
    bereinigt = text.strip()

    try:
        # ISO-Format: 2026-02-24
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(1)),
                int(treffer.group(2)),
                int(treffer.group(3)),
            ).isoformat()

        # Deutsches Format: 24.02.2026
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(3)),
                int(treffer.group(2)),
                int(treffer.group(1)),
            ).isoformat()

        # Ausgeschrieben: "24. Februar 2026"
        treffer = re.search(
            r"(\d{1,2})\.?\s+([a-zäöüß]+)\s+(\d{4})",
            bereinigt.lower(),
        )
        if treffer:
            tag = int(treffer.group(1))
            monat_name = treffer.group(2).lower()
            jahr = int(treffer.group(3))
            monat = MONAT_MAP.get(monat_name) or MONAT_KURZ_MAP.get(monat_name[:3])
            if monat:
                return date(jahr, monat, tag).isoformat()

        # Ohne Jahr: "24.02."
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.", bereinigt)
        if treffer:
            tag = int(treffer.group(1))
            monat = int(treffer.group(2))
            try:
                kandidat = date(heute.year, monat, tag)
            except ValueError:
                return None
            if kandidat < heute - timedelta(days=1):
                kandidat = date(heute.year + 1, monat, tag)
            return kandidat.isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning(
            "Fallback-Datum konnte nicht geparst werden: '%s' – %s",
            text, fehler,
        )
    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """
    Extrahiert eine Uhrzeit (HH:MM) aus einem beliebigen Text.

    Unterstützte Formate: "20:00", "20.00", "20:00 Uhr"

    Args:
        text: Text mit möglicher Zeitangabe

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


def _venue_aus_text(text: str) -> Optional[str]:
    """
    Erkennt einen bekannten d.live-Venue-Namen aus einem beliebigen Text.

    Prüft die konfigurierten VENUE_FRAGMENTE-Schlüssel gegen den
    Eingabe-Text (case-insensitiv).

    Args:
        text: Alt-Text eines Venue-Bilds oder sonstiger Text

    Returns:
        Vollständiger Venue-Name (z.B. "Merkur Spiel-Arena") oder None
    """
    if not text:
        return None

    text_lower = text.lower().strip()

    # Direkte Treffer zuerst (längste Fragmente bevorzugen)
    for fragment, venue in sorted(
        VENUE_FRAGMENTE.items(), key=lambda x: len(x[0]), reverse=True
    ):
        if fragment in text_lower:
            return venue

    return None


def _kategorie_aus_titel(titel: str) -> str:
    """
    Leitet die DDA-Kategorie aus dem Event-Titel ab.

    Durchsucht den Titel nach bekannten Schlüsselwörtern. Bei keinem
    Treffer wird "sonstiges" zurückgegeben.

    Args:
        titel: Event-Titel

    Returns:
        DDA-Kategorie als String
    """
    if not titel:
        return "sonstiges"

    titel_lower = titel.lower()
    for schluessel, kategorie in KATEGORIE_MAP.items():
        if schluessel in titel_lower:
            return kategorie

    return "sonstiges"


# --- Event-Parsing aus gerenderten Karten ---------------------------------

def _event_aus_karte(karte_el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einer gerenderten .card.calendar-event-Karte.

    Erwartet folgende DOM-Struktur (nach JavaScript-Rendering):
      <div class="card calendar-event state-regular">
        <div class="event-date">
          <div class="date-fields ...">
            <p class="day">24</p>
            <p class="month">Feb</p>
            <p class="year">2026</p>
          </div>
          <p class="time">20:00</p>
        </div>
        <a class="image-link stretched-link" href="/events/detail/...">
          <img src="https://..." />
        </a>
        <div class="card-body">
          <p class="card-title ..."><a href="...">Titel</a></p>
          <figure class="location-img"><img alt="Merkur Spiel-Arena" /></figure>
        </div>
      </div>

    Abgesagte Events (state-canceled) werden übersprungen.

    Args:
        karte_el: BeautifulSoup-Element der Event-Karte
        heute:    Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None wenn Pflichtfelder fehlen / Event vergangen /
        Event abgesagt
    """
    try:
        # --- Abgesagte Events überspringen ---
        karten_klassen = " ".join(karte_el.get("class", []))
        if "state-canceled" in karten_klassen:
            logger.debug("Abgesagtes Event übersprungen")
            return None

        # --- Datum aus separaten Tag/Monat/Jahr-Feldern ---
        datum = None
        tag_el = karte_el.select_one("p.day")
        monat_el = karte_el.select_one("p.month")
        jahr_el = karte_el.select_one("p.year")

        if tag_el and monat_el and jahr_el:
            datum = _datum_parsen(
                tag_el.get_text(strip=True),
                monat_el.get_text(strip=True),
                jahr_el.get_text(strip=True),
            )

        # Fallback: Volltext-Suche im Datums-Container
        if not datum:
            datum_container = karte_el.select_one(".event-date, .date-fields")
            if datum_container:
                datum = _datum_aus_volltext(datum_container.get_text(separator=" ", strip=True))

        if not datum:
            logger.debug(
                "Kein Datum gefunden in Event-Karte: %s",
                karte_el.get_text(strip=True)[:80],
            )
            return None

        # Vergangene Events überspringen
        if date.fromisoformat(datum) < heute:
            return None

        # --- Uhrzeit ---
        uhrzeit = None
        zeit_el = karte_el.select_one("p.time, .time")
        if zeit_el:
            uhrzeit = _uhrzeit_parsen(zeit_el.get_text(strip=True))

        # --- Titel und Event-URL ---
        titel = None
        quelle_url = EVENTS_URL

        # Primär: Link in der card-title
        titel_el = karte_el.select_one(".card-title a, p.card-title a")
        if titel_el:
            titel = titel_el.get_text(strip=True)
            href = titel_el.get("href", "")
            if href:
                quelle_url = urljoin(BASE_URL, href)

        # Fallback 1: stretched-link (Bild-Link)
        if not titel or not quelle_url or quelle_url == EVENTS_URL:
            link_el = karte_el.select_one("a.stretched-link, a.image-link")
            if link_el:
                href = link_el.get("href", "")
                if href:
                    quelle_url = urljoin(BASE_URL, href)

        # Fallback 2: erster Link mit /events/ in der URL
        if not titel:
            for anker in karte_el.find_all("a", href=True):
                href = anker.get("href", "")
                anker_text = anker.get_text(strip=True)
                if anker_text and len(anker_text) > 3:
                    titel = anker_text
                    if "/events/" in href:
                        quelle_url = urljoin(BASE_URL, href)
                    break

        # Fallback 3: Überschriften-Tags
        if not titel:
            for tag_name in ["h1", "h2", "h3", "h4", "h5"]:
                heading = karte_el.select_one(tag_name)
                if heading:
                    titel = heading.get_text(strip=True)
                    if titel:
                        break

        if not titel:
            logger.debug("Kein Titel in Event-Karte gefunden")
            return None

        # --- Venue-Name aus Venue-Bild-Alt-Text ---
        ort = None
        venue_bild_el = karte_el.select_one("figure.location-img img, .location-img img")
        if venue_bild_el:
            alt_text = venue_bild_el.get("alt", "")
            ort = _venue_aus_text(alt_text) or (alt_text.strip() if alt_text.strip() else None)

        # Fallback: Venue aus Event-URL extrahieren
        if not ort and "/events/" in quelle_url:
            ort = _venue_aus_text(quelle_url)

        # Letzter Fallback: generischer d.live-Name
        if not ort:
            ort = ORT_FALLBACK

        # --- Adresse des erkannten Venue ---
        adresse = VENUE_ADRESSEN.get(ort)

        # --- Kategorie aus Titel ---
        kategorie = _kategorie_aus_titel(titel)

        # --- Event-Bild (aus Hauptbild-Link) ---
        bild_url = None
        bild_el = karte_el.select_one("a.image-link img, a.stretched-link img, .card-img-top, img")
        if bild_el:
            bild_url = (
                bild_el.get("data-src")
                or bild_el.get("src")
                or bild_el.get("data-lazy-src")
            )
            # Nur absolute URLs behalten; relative zu BASE_URL machen
            if bild_url:
                if bild_url.startswith("//"):
                    bild_url = "https:" + bild_url
                elif bild_url.startswith("/"):
                    bild_url = urljoin(BASE_URL, bild_url)
                elif not bild_url.startswith("http"):
                    bild_url = None  # Datei-Pfad oder Platzhalter → verwerfen

        # --- Status-Label für Beschreibung (z.B. "Ausverkauft") ---
        beschreibung = None
        status_el = karte_el.select_one(".status span, .status")
        if status_el:
            status_text = status_el.get_text(strip=True)
            if status_text and status_text.lower() not in ("regular", ""):
                beschreibung = status_text[:300]

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": adresse,
            "kategorie": kategorie,
            "beschreibung": beschreibung,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error("Fehler beim Parsen einer Event-Karte: %s", str(fehler))
        return None


# --- Playwright-Scraping --------------------------------------------------

def _html_via_playwright() -> Optional[str]:
    """
    Lädt die d.live-Eventseite mit Playwright und gibt das gerenderte HTML zurück.

    Die Seite rendert alle Events clientseitig via JavaScript (EJS-Templates).
    Playwright wartet, bis mindestens eine Event-Karte im DOM erscheint oder
    ein Timeout erreicht wird.

    Returns:
        Gerendertes HTML als String oder None bei Fehler
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    try:
        time.sleep(2)  # Rate Limiting

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            seite = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )

            try:
                logger.info("Lade d.live-Eventseite: %s", EVENTS_URL)
                seite.goto(EVENTS_URL, timeout=30000, wait_until="domcontentloaded")

                # Warten bis Event-Karten gerendert sind
                try:
                    seite.wait_for_selector(
                        ".calendar-event, .card.calendar-event, .calendar-entry",
                        timeout=15000,
                    )
                    logger.info("Event-Karten im DOM erkannt, lese HTML")
                except PlaywrightTimeout:
                    logger.warning(
                        "Timeout beim Warten auf .calendar-event – "
                        "lese verfügbares HTML trotzdem aus"
                    )

                html = seite.content()

            except PlaywrightTimeout:
                logger.error("Timeout beim Laden der d.live-Seite: %s", EVENTS_URL)
                browser.close()
                return None
            except Exception as fehler:
                logger.error(
                    "Playwright-Fehler beim Laden von %s: %s",
                    EVENTS_URL, str(fehler),
                )
                browser.close()
                return None

            browser.close()
            return html

    except ImportError:
        logger.error(
            "Playwright ist nicht installiert. "
            "Bitte 'playwright install chromium' ausführen."
        )
        return None
    except Exception as fehler:
        logger.error("Playwright-Initialisierung fehlgeschlagen: %s", str(fehler))
        return None


# --- Hauptfunktion --------------------------------------------------------

def scrape() -> list[dict]:
    """
    Scrapt Events von d.live Düsseldorf (Merkur Spiel-Arena + PSD BANK DOME).

    Da die Seite vollständig JavaScript-gerendert ist, wird Playwright
    eingesetzt. Nach dem Rendering werden die Event-Karten mit BeautifulSoup
    geparst.

    Strategie:
    1. Playwright lädt d-live.de/events/ und wartet auf .calendar-event-Elemente
    2. BeautifulSoup parst die gerenderten Karten
    3. Mehrere CSS-Selektoren als Fallback falls sich die DOM-Struktur ändert
    4. Vergangene und abgesagte Events werden gefiltert
    5. Duplikate (gleiche URL) werden dedupliziert

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    events: list[dict] = []
    heute = date.today()
    logger.info("Starte Scraper: %s (Playwright)", QUELLE_NAME)

    # --- HTML via Playwright laden ---
    html = _html_via_playwright()

    if html is None:
        logger.error("Scraper %s: Konnte kein HTML laden", QUELLE_NAME)
        return []

    soup = BeautifulSoup(html, "html.parser")

    # --- Event-Karten finden: mehrere Selektoren als Fallback ---
    # Primär: .card.calendar-event (die eigentliche Karte)
    karten = soup.select(".card.calendar-event")

    # Fallback 1: .calendar-event (ohne explizites .card)
    if not karten:
        karten = soup.select(".calendar-event")

    # Fallback 2: .calendar-entry > .card (Container → Karte)
    if not karten:
        karten = [
            eintrag.find("div", class_="card")
            for eintrag in soup.select(".calendar-entry")
            if eintrag.find("div", class_="card")
        ]

    # Fallback 3: Alle divs die Datum-Felder enthalten
    if not karten:
        karten = [
            el.find_parent("div")
            for el in soup.select("p.day")
            if el.find_parent("div")
        ]

    if not karten:
        logger.warning(
            "Scraper %s: Keine Event-Karten im DOM gefunden – "
            "Seitenstruktur hat sich möglicherweise geändert.",
            QUELLE_NAME,
        )
        return []

    logger.info("%d potenzielle Event-Karten gefunden", len(karten))

    # --- Events parsen und Duplikate vermeiden ---
    gesehene_urls: set[str] = set()

    for karte_el in karten:
        if karte_el is None:
            continue

        event = _event_aus_karte(karte_el, heute)
        if event is None:
            continue

        url = event["quelle_url"]
        if url in gesehene_urls:
            continue
        gesehene_urls.add(url)
        events.append(event)

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
    import json as _json

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    ergebnisse = scrape()

    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")

    if ergebnisse:
        print("Beispiel-Event (erstes gefundenes):")
        print(_json.dumps(ergebnisse[0], ensure_ascii=False, indent=2))
        print()
        if len(ergebnisse) > 1:
            print(f"Weitere Events: {len(ergebnisse) - 1} zusätzliche Events gefunden.")
    else:
        print("Keine Events gefunden.")
        print("Mögliche Ursachen:")
        print("  1. Playwright ist nicht installiert (playwright install chromium)")
        print("  2. Die DOM-Struktur der d.live-Seite hat sich geändert")
        print("  3. Netzwerkverbindung nicht verfügbar")
