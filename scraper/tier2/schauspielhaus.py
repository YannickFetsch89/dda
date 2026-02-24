"""
schauspielhaus.py – DiesDasDüsseldorf
Scraper für das Düsseldorfer Schauspielhaus: Spielplan und Veranstaltungen.

Primärquelle:  https://www.dhaus.de/programm/spielplan/YYYY-MM/
  → Spiritec CMS, server-seitig gerendert, HTML-Parsing.
  → Monat-für-Monat-Iteration über die nächsten 6 Monate.

Fallback:      https://www.dhaus.de/programm/spielplan/
  → Übersichtsseite ohne Monatsfilter, zeigt aktuelle Events.

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

BASE_URL = "https://www.dhaus.de"
SPIELPLAN_URL = "https://www.dhaus.de/programm/spielplan/"
QUELLE_NAME = "Düsseldorfer Schauspielhaus"
ORT_STANDARD = "Düsseldorfer Schauspielhaus"
ADRESSE_STANDARD = "Gustaf-Gründgens-Platz 1, 40211 Düsseldorf"
KATEGORIE_STANDARD = "kultur"

# Anzahl Monate voraus, die gescrapt werden (aktueller Monat + 5 weitere)
MONATE_VORAUS = 6

# Bekannte Spielstätten des Schauspielhauses für Ort-Normalisierung
SPIELSTAETTEN = {
    "großes haus":    "Düsseldorfer Schauspielhaus – Großes Haus",
    "kleines haus":   "Düsseldorfer Schauspielhaus – Kleines Haus",
    "unterhaus":      "Düsseldorfer Schauspielhaus – Unterhaus",
    "foyer":          "Düsseldorfer Schauspielhaus – Foyer",
    "central 1":      "Central 1",
    "central 2":      "Central 2",
    "central brücke": "Central Brücke",
    "central":        "Central",
    "the box":        "The Box",
    "cave":           "Cave",
}

# Monatsnamen Deutsch (für URL-Generierung und Datum-Parsing)
MONAT_MAP: dict[str, int] = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}

MONAT_KURZ_MAP: dict[str, int] = {
    "jan": 1, "feb": 2, "mär": 3, "apr": 4,
    "mai": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "nov": 11, "dez": 12,
}


# --- Hilfsfunktionen: Datum und Uhrzeit -----------------------------------

def _datum_parsen(text: str, kontext_jahr: int = 0, kontext_monat: int = 0) -> Optional[str]:
    """
    Wandelt verschiedene Datumsformate in ISO 8601 (YYYY-MM-DD) um.

    Das Schauspielhaus nutzt typischerweise:
      - "24.02."         → mit Kontext-Jahr und -Monat
      - "24.02.2026"     → mit vollem Jahr
      - "Dienstag 24.02." → Wochentag + Datum ohne Jahr
      - "2026-02-24"     → ISO bereits vorhanden

    Args:
        text:          Roher Datumstext von der Webseite
        kontext_jahr:  Bekanntes Jahr aus der URL (z.B. 2026), falls vorhanden
        kontext_monat: Bekannter Monat aus der URL (z.B. 2), falls vorhanden

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

        # Format: "24. März 2026" oder "24. märz 2026"
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

        # Format: "24.02." – Datum ohne Jahr
        # Priorität: Kontext-Jahr/-Monat aus der URL
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.", bereinigt)
        if treffer:
            tag = int(treffer.group(1))
            monat = int(treffer.group(2))

            # Kontext-Jahr nutzen wenn vorhanden und passend
            if kontext_jahr and kontext_monat and monat == kontext_monat:
                try:
                    return date(kontext_jahr, monat, tag).isoformat()
                except ValueError:
                    pass

            # Nächstes passendes Datum ermitteln
            jahr = heute.year
            try:
                kandidat = date(jahr, monat, tag)
            except ValueError:
                return None
            if kandidat < heute - timedelta(days=1):
                kandidat = date(jahr + 1, monat, tag)
            return kandidat.isoformat()

        # Format: "24. Feb" oder "24. Feb." (Kurzform)
        treffer = re.search(r"(\d{1,2})\.\s*([a-zäöü]{3})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat_kurz = treffer.group(2)[:3].lower()
            monat = MONAT_KURZ_MAP.get(monat_kurz)
            if monat:
                jahr = kontext_jahr if kontext_jahr else heute.year
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
    Extrahiert die erste Uhrzeit (HH:MM) aus einem beliebigen Text.

    Unterstützte Formate: "19:30", "20.00", "19:30 – 22:00", "20:00 Uhr"

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


def _ort_normalisieren(roh_text: str) -> str:
    """
    Mappt einen Spielstätten-Rohtext auf den standardisierten Ortsnamen.

    Vergleicht mit bekannten Spielstätten des Schauspielhauses (case-insensitiv).

    Args:
        roh_text: Ortstext wie er von der Seite extrahiert wurde,
                  z.B. "Schauspielhaus, Großes Haus"

    Returns:
        Normalisierter Ort, z.B. "Düsseldorfer Schauspielhaus – Großes Haus"
        oder ORT_STANDARD als Fallback
    """
    if not roh_text:
        return ORT_STANDARD

    roh_klein = roh_text.lower().strip()

    for schluessel, ort_name in SPIELSTAETTEN.items():
        if schluessel in roh_klein:
            return ort_name

    # Falls Schauspielhaus im Text aber kein bekannter Saal
    if "schauspielhaus" in roh_klein or "dhaus" in roh_klein:
        return ORT_STANDARD

    # Eigenständige Venue (z.B. "Central") direkt übernehmen
    if roh_text.strip():
        return roh_text.strip()

    return ORT_STANDARD


def _preis_aus_text(text: str) -> Optional[str]:
    """
    Extrahiert Preisinformationen aus einem Text.

    Sucht nach typischen Preisangaben wie "12 €", "ab 8€", "kostenlos".

    Args:
        text: Beliebiger Text der Preisangaben enthalten kann

    Returns:
        Preis-String wie "ab 8 €" oder None wenn kein Preis gefunden
    """
    if not text:
        return None

    text_klein = text.lower()

    if "kostenlos" in text_klein or "eintritt frei" in text_klein or "frei" in text_klein:
        return "kostenlos"

    # Preisbereich: "8 – 25 €" oder "8€ - 25€"
    treffer = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(?:–|-)\s*(\d+(?:[.,]\d+)?)\s*€",
        text,
    )
    if treffer:
        return f"{treffer.group(1)} – {treffer.group(2)} €"

    # Einzelpreis: "12 €" oder "12€" oder "ab 8 €"
    treffer = re.search(r"(?:ab\s+)?(\d+(?:[.,]\d+)?)\s*€", text)
    if treffer:
        prefix = "ab " if "ab" in text_klein else ""
        return f"{prefix}{treffer.group(1)} €"

    return None


# --- Strategie 1: Monatlicher Spielplan -----------------------------------

def _event_aus_container(container, heute: date, kontext_jahr: int, kontext_monat: int) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem Event-Container-Element des Spielplans.

    Das Schauspielhaus (Spiritec CMS) rendert den Spielplan mit typischen
    Event-Card-Mustern. Diese Funktion probiert mehrere DOM-Selektoren.

    Erwartete DOM-Muster (in Priorität):
      Pattern A – Article mit data-Attributen:
        <article class="event-item" data-date="2026-03-01" data-time="16:00">
          <h4 class="event-title"><a href="/programm/spielplan/...">Titel</a></h4>
          <span class="event-location">Schauspielhaus, Großes Haus</span>
          <img src="...">
        </article>

      Pattern B – Listen-/Div-Elemente mit Klassen:
        <div class="event ...">
          <a href="/programm/spielplan/.../2370/">
            <h2/h3/h4>Titel</h2/h3/h4>
          </a>
          <div class="date">Sonntag 01.03.</div>
          <div class="time">16:00</div>
          <div class="location">Schauspielhaus, Großes Haus</div>
        </div>

      Pattern C – Implizite Struktur anhand von Datum-Texten.

    Args:
        container:     BeautifulSoup-Element das ein Event repräsentiert
        heute:         Heutiges Datum für Filterung vergangener Events
        kontext_jahr:  Jahr aus der Spielplan-URL (z.B. 2026)
        kontext_monat: Monat aus der Spielplan-URL (z.B. 3)

    Returns:
        Event-Dict oder None wenn Pflichtfelder fehlen / Event vergangen
    """
    try:
        # --- URL und Titel ---
        # Bevorzugt: Link mit /programm/spielplan/-Pfad
        link_el = container.select_one("a[href*='/programm/spielplan/']")
        if not link_el:
            link_el = container.find("a", href=True)

        href = link_el.get("href", "") if link_el else ""
        quelle_url = urljoin(BASE_URL, href) if href else SPIELPLAN_URL

        # Titel aus verschiedenen Quellen
        titel = None

        # Priorität 1: Überschrift im Link
        for selector in ["h1", "h2", "h3", "h4", "h5", ".event-title", ".title"]:
            titel_el = container.select_one(selector)
            if titel_el:
                titel = titel_el.get_text(strip=True)
                if titel:
                    break

        # Priorität 2: Text des Links selbst
        if not titel and link_el:
            titel = link_el.get_text(strip=True)

        # Priorität 3: data-title Attribut
        if not titel:
            titel = container.get("data-title") or container.get("title")

        if not titel:
            return None

        # Zu kurze Titel (Navigationselemente etc.) überspringen
        if len(titel) < 3:
            return None

        # --- Datum ---
        datum = None

        # Priorität 1: data-date oder datetime-Attribut am Container
        for attr in ["data-date", "datetime", "data-startdate", "data-start"]:
            attr_val = container.get(attr)
            if attr_val:
                datum = _datum_parsen(attr_val, kontext_jahr, kontext_monat)
                if datum:
                    break

        # Priorität 2: <time>-Element mit datetime-Attribut
        if not datum:
            zeit_el = container.select_one("time[datetime]")
            if zeit_el:
                datum = _datum_parsen(
                    zeit_el.get("datetime", ""), kontext_jahr, kontext_monat
                )

        # Priorität 3: Datum-Klassen-Elemente
        if not datum:
            for selector in [
                ".date", ".datum", ".event-date", ".spielplan-date",
                "[class*='date']", "[class*='datum']",
            ]:
                datum_el = container.select_one(selector)
                if datum_el:
                    datum_text = datum_el.get_text(strip=True)
                    datum = _datum_parsen(datum_text, kontext_jahr, kontext_monat)
                    if datum:
                        break

        # Priorität 4: Datum-Regex im gesamten Container-Text
        if not datum:
            gesamt_text = container.get_text(" ", strip=True)
            # Suche nach "DD.MM." oder "DD.MM.YYYY" im Text
            treffer = re.search(r"\b(\d{1,2}\.\d{2}\.(?:\d{4})?)", gesamt_text)
            if treffer:
                datum = _datum_parsen(
                    treffer.group(1), kontext_jahr, kontext_monat
                )

        if not datum:
            logger.debug("Kein Datum gefunden für Event: %s", titel)
            return None

        # Vergangene Events filtern
        if date.fromisoformat(datum) < heute:
            return None

        # --- Uhrzeit ---
        uhrzeit = None

        # Priorität 1: data-time Attribut
        for attr in ["data-time", "data-starttime"]:
            attr_val = container.get(attr)
            if attr_val:
                uhrzeit = _uhrzeit_parsen(attr_val)
                if uhrzeit:
                    break

        # Priorität 2: <time>-Elemente
        if not uhrzeit:
            for zeit_el in container.select("time"):
                uhrzeit = (
                    _uhrzeit_parsen(zeit_el.get("datetime", ""))
                    or _uhrzeit_parsen(zeit_el.get_text(strip=True))
                )
                if uhrzeit:
                    break

        # Priorität 3: Zeit-Klassen
        if not uhrzeit:
            for selector in [
                ".time", ".uhrzeit", ".event-time",
                "[class*='time']", "[class*='uhr']",
            ]:
                time_el = container.select_one(selector)
                if time_el:
                    uhrzeit = _uhrzeit_parsen(time_el.get_text(strip=True))
                    if uhrzeit:
                        break

        # Priorität 4: Uhrzeit-Regex im Text
        if not uhrzeit:
            gesamt_text = container.get_text(" ", strip=True)
            uhrzeit = _uhrzeit_parsen(gesamt_text)

        # --- Spielort ---
        ort = ORT_STANDARD

        for selector in [
            ".location", ".ort", ".venue", ".spielort", ".event-location",
            "[class*='location']", "[class*='venue']", "[class*='ort']",
        ]:
            ort_el = container.select_one(selector)
            if ort_el:
                ort_text = ort_el.get_text(strip=True)
                if ort_text:
                    ort = _ort_normalisieren(ort_text)
                    break

        # --- Beschreibung ---
        beschreibung = None
        for selector in [
            ".description", ".beschreibung", ".teaser", ".summary",
            ".event-description", ".excerpt", "p",
        ]:
            beschr_el = container.select_one(selector)
            if beschr_el:
                beschr_text = beschr_el.get_text(strip=True)
                # Beschreibung darf nicht der Titel selbst sein
                if beschr_text and beschr_text != titel and len(beschr_text) > 20:
                    beschreibung = beschr_text[:300]
                    break

        # --- Preis ---
        preis = None
        gesamt_text = container.get_text(" ", strip=True)
        preis = _preis_aus_text(gesamt_text)

        # --- Bild ---
        bild_url = None
        bild_el = container.select_one("img")
        if bild_el:
            bild_url = (
                bild_el.get("data-src")
                or bild_el.get("data-lazy-src")
                or bild_el.get("src")
            )
            if bild_url and bild_url.startswith("/"):
                bild_url = urljoin(BASE_URL, bild_url)
            # Data-URIs und Platzhalter verwerfen
            if bild_url and (
                bild_url.startswith("data:")
                or "placeholder" in bild_url.lower()
                or len(bild_url) < 10
            ):
                bild_url = None

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": ADRESSE_STANDARD,
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
        }

    except Exception as fehler:
        logger.error("Fehler beim Parsen eines Event-Containers: %s", str(fehler))
        return None


def _container_aus_soup_extrahieren(soup: BeautifulSoup) -> list:
    """
    Sucht im BeautifulSoup-Objekt nach Event-Containern mit mehreren Strategien.

    Versucht die typischen Spiritec-CMS-Klassen sowie generische Muster.

    Strategie 1: Klassen die 'event' enthalten (häufig im Spiritec CMS)
    Strategie 2: <article>-Elemente mit Datum-Inhalten
    Strategie 3: Listenelemente mit Links zu /programm/spielplan/
    Strategie 4: Divs mit Links zu /programm/spielplan/ als Fallback

    Args:
        soup: BeautifulSoup-Objekt der geladenen Seite

    Returns:
        Liste von BeautifulSoup-Elementen die Events repräsentieren könnten
    """
    # Strategie 1: Klassen-basiert (Spiritec CMS Muster)
    for selector in [
        "[class*='event-item']",
        "[class*='event_item']",
        "[class*='spielplan-item']",
        "[class*='spielplan_item']",
        "[class*='performance']",
        "[class*='vorstellung']",
        "article.event",
        "li.event",
        ".events-list li",
        ".event-list li",
        ".spielplan li",
        ".schedule-item",
    ]:
        container = soup.select(selector)
        if container:
            logger.info(
                "Event-Container gefunden via Selektor '%s': %d Elemente",
                selector, len(container),
            )
            return container

    # Strategie 2: <article>-Elemente mit Spielplan-Links
    artikel = [
        el for el in soup.find_all("article")
        if el.find("a", href=re.compile(r"/programm/spielplan/"))
    ]
    if artikel:
        logger.info(
            "Event-Container: %d <article>-Elemente mit Spielplan-Links",
            len(artikel),
        )
        return artikel

    # Strategie 3: <li>-Elemente mit Spielplan-Links
    listen_eintraege = [
        li for li in soup.find_all("li")
        if li.find("a", href=re.compile(r"/programm/spielplan/"))
        and len(li.get_text(strip=True)) > 20
    ]
    if listen_eintraege:
        logger.info(
            "Event-Container: %d <li>-Elemente mit Spielplan-Links",
            len(listen_eintraege),
        )
        return listen_eintraege

    # Strategie 4: Direkte Links zu Einzelevents (/spielplan/YYYY-MM/slug/ID/)
    # Jeder Link wird zum Container für sein Elternelement
    event_links = soup.find_all(
        "a",
        href=re.compile(r"/programm/spielplan/\d{4}-\d{2}/.+/\d+/"),
    )
    if event_links:
        # Elternelement nehmen, aber Duplikate vermeiden
        gesehene_els = set()
        container = []
        for link in event_links:
            el = link.parent
            if id(el) not in gesehene_els:
                gesehene_els.add(id(el))
                container.append(el)
        if container:
            logger.info(
                "Event-Container: %d Eltern-Elemente von Spielplan-Links",
                len(container),
            )
            return container

    return []


def _datum_text_aus_link_url(href: str) -> tuple[int, int]:
    """
    Extrahiert Jahr und Monat aus einer Spielplan-URL.

    Beispiel: "/programm/spielplan/2026-03/..." → (2026, 3)

    Args:
        href: Pfad oder vollständige URL

    Returns:
        Tuple (jahr, monat) oder (0, 0) wenn nicht erkennbar
    """
    treffer = re.search(r"/spielplan/(\d{4})-(\d{2})/", href)
    if treffer:
        return int(treffer.group(1)), int(treffer.group(2))
    return 0, 0


def _monatlichen_spielplan_scrapen(
    jahr: int, monat: int, heute: date
) -> list[dict]:
    """
    Scrapt den Spielplan für einen bestimmten Monat.

    Lädt die URL /programm/spielplan/YYYY-MM/ und extrahiert alle Events.

    Args:
        jahr:  Ziel-Jahr (z.B. 2026)
        monat: Ziel-Monat (1–12)
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Liste von Event-Dicts für diesen Monat
    """
    url = f"{SPIELPLAN_URL}{jahr}-{monat:02d}/"
    logger.info("Lade Spielplan für %d-%02d: %s", jahr, monat, url)

    try:
        html = seite_abrufen(url, logger)
        if html is None:
            logger.warning("Keine Antwort für Monat %d-%02d", jahr, monat)
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Event-Container extrahieren
        container_liste = _container_aus_soup_extrahieren(soup)

        if not container_liste:
            # Letzter Fallback: alle Links zu Einzelevents direkt parsen
            logger.info(
                "Kein Container-Pattern gefunden – "
                "versuche direkte Link-Extraktion für %d-%02d", jahr, monat
            )
            return _events_aus_links_extrahieren(soup, heute, jahr, monat)

        events: list[dict] = []
        gesehene_urls: set[str] = set()

        for container in container_liste:
            event = _event_aus_container(container, heute, jahr, monat)
            if event is None:
                continue

            url_event = event["quelle_url"]
            if url_event in gesehene_urls:
                continue
            gesehene_urls.add(url_event)
            events.append(event)

        logger.info(
            "Monat %d-%02d: %d Events extrahiert", jahr, monat, len(events)
        )
        return events

    except Exception as fehler:
        logger.error(
            "Fehler beim Scrapen des Spielplans %d-%02d: %s",
            jahr, monat, str(fehler),
        )
        return []


def _events_aus_links_extrahieren(
    soup: BeautifulSoup, heute: date, kontext_jahr: int, kontext_monat: int
) -> list[dict]:
    """
    Fallback: Extrahiert Events direkt aus Spielplan-Links im HTML.

    Findet alle <a>-Tags mit dem Muster /programm/spielplan/YYYY-MM/slug/ID/
    und baut minimale Event-Dicts daraus auf. Datum wird aus dem URL-Pfad
    und dem umliegenden Text ermittelt.

    Args:
        soup:           BeautifulSoup-Objekt der Seite
        heute:          Heutiges Datum
        kontext_jahr:   Jahr aus der Monat-URL
        kontext_monat:  Monat aus der Monat-URL

    Returns:
        Liste von Event-Dicts (mit Pflichtfeldern, beschreibung=None)
    """
    # Alle Links mit Muster /programm/spielplan/YYYY-MM/slug/ID/
    event_links = soup.find_all(
        "a",
        href=re.compile(r"/programm/spielplan/\d{4}-\d{2}/.+/\d+/"),
    )

    if not event_links:
        logger.warning(
            "Keine Spielplan-Links im HTML für %d-%02d gefunden",
            kontext_jahr, kontext_monat,
        )
        return []

    events: list[dict] = []
    gesehene_urls: set[str] = set()

    for link in event_links:
        try:
            href = link.get("href", "")
            quelle_url = urljoin(BASE_URL, href)

            if quelle_url in gesehene_urls:
                continue

            # Titel aus Link-Text oder Überschrift
            titel = link.get_text(strip=True)
            if not titel or len(titel) < 3:
                # Geschwisterelement prüfen
                elternelement = link.parent
                if elternelement:
                    for selector in ["h1", "h2", "h3", "h4", "h5"]:
                        ueberschrift = elternelement.select_one(selector)
                        if ueberschrift:
                            titel = ueberschrift.get_text(strip=True)
                            break
            if not titel or len(titel) < 3:
                continue

            # Jahr und Monat aus URL extrahieren
            url_jahr, url_monat = _datum_text_aus_link_url(href)
            if not url_jahr:
                url_jahr = kontext_jahr
                url_monat = kontext_monat

            # Datum aus URL-Kontext und umliegendem Text
            datum = None
            umgebungstext = ""
            elternelement = link.parent
            if elternelement:
                umgebungstext = elternelement.get_text(" ", strip=True)
                datum = _datum_parsen(umgebungstext, url_jahr, url_monat)

            # Fallback: Ersten Tag des URL-Monats als Datum
            if not datum and url_jahr and url_monat:
                try:
                    erster_tag = date(url_jahr, url_monat, 1)
                    if erster_tag >= heute:
                        datum = erster_tag.isoformat()
                except ValueError:
                    pass

            if not datum:
                continue

            if date.fromisoformat(datum) < heute:
                continue

            # Uhrzeit
            uhrzeit = _uhrzeit_parsen(umgebungstext) if umgebungstext else None

            # Ort aus umliegendem Text
            ort = ORT_STANDARD
            for schluessel, ort_name in SPIELSTAETTEN.items():
                if schluessel in umgebungstext.lower():
                    ort = ort_name
                    break

            # Preis
            preis = _preis_aus_text(umgebungstext)

            gesehene_urls.add(quelle_url)
            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ort,
                "adresse": ADRESSE_STANDARD,
                "kategorie": KATEGORIE_STANDARD,
                "beschreibung": None,
                "preis": preis,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": None,
                "instagram_caption": None,
                "datum_bis": None,
                "ist_wiederkehrend": False,
                "status": "neu",
            })

        except Exception as fehler:
            logger.debug(
                "Fehler beim Verarbeiten eines Spielplan-Links: %s", str(fehler)
            )
            continue

    logger.info(
        "Link-Extraktion für %d-%02d: %d Events gefunden",
        kontext_jahr, kontext_monat, len(events),
    )
    return events


# --- Strategie 2: JSON-LD und strukturierte Daten -------------------------

def _events_aus_json_ld(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    Sucht nach JSON-LD <script type="application/ld+json"> Tags auf der Seite
    und extrahiert Event-Daten daraus.

    Schema.org-Event-Format:
        {
          "@type": "Event",
          "name": "Titel",
          "startDate": "2026-03-01T16:00:00",
          "location": {"name": "..."},
          ...
        }

    Args:
        soup:  BeautifulSoup-Objekt der geladenen Seite
        heute: Heutiges Datum

    Returns:
        Liste von Event-Dicts oder leere Liste
    """
    events: list[dict] = []
    gesehene_urls: set[str] = set()

    json_ld_scripts = soup.find_all("script", type="application/ld+json")
    if not json_ld_scripts:
        return []

    for script in json_ld_scripts:
        try:
            daten = json.loads(script.string or "{}")
        except (json.JSONDecodeError, AttributeError):
            continue

        # Kann ein einzelnes Objekt oder eine Liste sein
        eintraege = daten if isinstance(daten, list) else [daten]

        # Auch "@graph"-Container durchsuchen
        for eintrag in list(eintraege):
            if isinstance(eintrag, dict) and "@graph" in eintrag:
                eintraege.extend(
                    e for e in eintrag["@graph"] if isinstance(e, dict)
                )

        for eintrag in eintraege:
            if not isinstance(eintrag, dict):
                continue

            typ = eintrag.get("@type", "")
            if typ not in ("Event", "TheaterEvent", "PerformingArtsEvent",
                           "MusicEvent", "ScreeningEvent"):
                continue

            event = _event_aus_json_ld_eintrag(eintrag, heute)
            if event is None:
                continue

            url = event["quelle_url"]
            if url not in gesehene_urls:
                gesehene_urls.add(url)
                events.append(event)

    if events:
        logger.info("JSON-LD: %d Events gefunden", len(events))
    return events


def _event_aus_json_ld_eintrag(eintrag: dict, heute: date) -> Optional[dict]:
    """
    Wandelt einen einzelnen JSON-LD-Event-Eintrag in ein DDA-Event-Dict um.

    Args:
        eintrag: JSON-LD Event-Objekt (Schema.org)
        heute:   Heutiges Datum

    Returns:
        Event-Dict oder None
    """
    try:
        titel = (
            eintrag.get("name")
            or eintrag.get("headline")
        )
        if not titel or not isinstance(titel, str):
            return None
        titel = titel.strip()
        if not titel:
            return None

        # Datum aus startDate (kann ISO-Datetime sein: "2026-03-01T16:00:00")
        start_date = eintrag.get("startDate") or eintrag.get("startDateTime")
        datum = _datum_parsen(str(start_date)) if start_date else None
        if not datum:
            return None

        if date.fromisoformat(datum) < heute:
            return None

        # Uhrzeit
        uhrzeit = _uhrzeit_parsen(str(start_date)) if start_date else None

        # URL
        url = eintrag.get("url") or eintrag.get("@id")
        if url and isinstance(url, str) and url.startswith("/"):
            quelle_url = urljoin(BASE_URL, url)
        elif url and isinstance(url, str) and url.startswith("http"):
            quelle_url = url
        else:
            quelle_url = SPIELPLAN_URL

        # Ort
        ort_daten = eintrag.get("location") or eintrag.get("Place")
        ort = ORT_STANDARD
        if isinstance(ort_daten, dict):
            ort_name = ort_daten.get("name") or ort_daten.get("title")
            if ort_name:
                ort = _ort_normalisieren(str(ort_name))
        elif isinstance(ort_daten, str):
            ort = _ort_normalisieren(ort_daten)

        # Beschreibung
        beschreibung_roh = (
            eintrag.get("description")
            or eintrag.get("abstract")
        )
        beschreibung = str(beschreibung_roh).strip()[:300] if beschreibung_roh else None

        # Preis
        preis = None
        angebot = eintrag.get("offers")
        if isinstance(angebot, dict):
            preis_val = angebot.get("price") or angebot.get("lowPrice")
            if preis_val is not None:
                preis = f"ab {preis_val} €"
        elif isinstance(angebot, list) and angebot:
            preis_val = angebot[0].get("price") or angebot[0].get("lowPrice")
            if preis_val is not None:
                preis = f"ab {preis_val} €"

        # Bild
        bild_url = None
        bild_roh = eintrag.get("image") or eintrag.get("thumbnail")
        if isinstance(bild_roh, dict):
            bild_url = bild_roh.get("url") or bild_roh.get("contentUrl")
        elif isinstance(bild_roh, str) and len(bild_roh) > 5:
            bild_url = bild_roh
        elif isinstance(bild_roh, list) and bild_roh:
            erstes = bild_roh[0]
            if isinstance(erstes, str):
                bild_url = erstes
            elif isinstance(erstes, dict):
                bild_url = erstes.get("url") or erstes.get("contentUrl")

        if bild_url and bild_url.startswith("/"):
            bild_url = urljoin(BASE_URL, bild_url)

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": ADRESSE_STANDARD,
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
        }

    except Exception as fehler:
        logger.error("Fehler beim Parsen eines JSON-LD-Eintrags: %s", str(fehler))
        return None


# --- Deduplizierung -------------------------------------------------------

def _deduplizieren(events: list[dict]) -> list[dict]:
    """
    Entfernt Duplikate aus der Event-Liste.

    Duplikat-Kriterien (in Priorität):
    1. Identische quelle_url
    2. Gleicher Titel + Datum + Uhrzeit

    Args:
        events: Rohe Event-Liste mit möglichen Duplikaten

    Returns:
        Deduplizierte Event-Liste in Originalreihenfolge
    """
    eindeutig: list[dict] = []
    gesehene_urls: set[str] = set()
    gesehene_schluessel: set[str] = set()

    for event in events:
        url = event.get("quelle_url", "")
        schluessel = f"{event.get('titel', '')}|{event.get('datum', '')}|{event.get('uhrzeit', '')}"

        if url and url != SPIELPLAN_URL and url in gesehene_urls:
            continue
        if schluessel in gesehene_schluessel:
            continue

        if url:
            gesehene_urls.add(url)
        gesehene_schluessel.add(schluessel)
        eindeutig.append(event)

    return eindeutig


# --- Hauptfunktion --------------------------------------------------------

def scrape() -> list[dict]:
    """
    Scrapt den Spielplan des Düsseldorfer Schauspielhauses.

    Strategie:
    1. Primär: Monatliche Spielplan-Seiten (/programm/spielplan/YYYY-MM/)
       für den aktuellen und die nächsten MONATE_VORAUS Monate.
       Jede Seite wird auf Event-Container gescannt (mehrere Selektoren).
       Fallback innerhalb der Monatsstrategie: direkte Link-Extraktion.

    2. Fallback: Übersichtsseite (/programm/spielplan/)
       Wird genutzt wenn die Monatsstrategie gar keine Events liefert.

    Filtert vergangene Events heraus und verhindert Duplikate.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    alle_events: list[dict] = []
    heute = date.today()

    logger.info("Starte Scraper: %s", QUELLE_NAME)

    # --- Primärstrategie: Monat-für-Monat ---
    aktuelles_datum = heute.replace(day=1)  # Erster des aktuellen Monats

    for i in range(MONATE_VORAUS):
        # Datum um i Monate vorrücken
        if i > 0:
            # Nächsten Monatsanfang berechnen
            if aktuelles_datum.month == 12:
                aktuelles_datum = aktuelles_datum.replace(
                    year=aktuelles_datum.year + 1, month=1
                )
            else:
                aktuelles_datum = aktuelles_datum.replace(
                    month=aktuelles_datum.month + 1
                )

        monat_events = _monatlichen_spielplan_scrapen(
            aktuelles_datum.year, aktuelles_datum.month, heute
        )
        alle_events.extend(monat_events)

    # --- Fallback: Übersichtsseite ---
    if not alle_events:
        logger.warning(
            "Monatsstrategie lieferte keine Events – "
            "versuche Übersichtsseite %s",
            SPIELPLAN_URL,
        )
        try:
            html = seite_abrufen(SPIELPLAN_URL, logger)
            if html:
                soup = BeautifulSoup(html, "html.parser")

                # Versuch 1: JSON-LD
                json_ld_events = _events_aus_json_ld(soup, heute)
                alle_events.extend(json_ld_events)

                # Versuch 2: Container-Pattern
                if not alle_events:
                    container_liste = _container_aus_soup_extrahieren(soup)
                    for container in container_liste:
                        event = _event_aus_container(container, heute, 0, 0)
                        if event:
                            alle_events.append(event)

                # Versuch 3: Direkte Link-Extraktion
                if not alle_events:
                    alle_events = _events_aus_links_extrahieren(
                        soup, heute, heute.year, heute.month
                    )

        except Exception as fehler:
            logger.error(
                "Fallback Übersichtsseite fehlgeschlagen: %s", str(fehler)
            )

    # --- Deduplizierung ---
    alle_events = _deduplizieren(alle_events)

    # --- Abschluss-Log ---
    if not alle_events:
        logger.warning(
            "Scraper %s: 0 Events gefunden – "
            "alle Strategien ohne Ergebnis.",
            QUELLE_NAME,
        )
    else:
        # 14-Tage-Fenster: Events weiter als SCRAPER_VORSCHAU_TAGE in der Zukunft ausfiltern
        enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
        alle_events = [e for e in alle_events if date.fromisoformat(e["datum"]) <= enddatum]
        logger.info(
            "Scraper %s fertig: %d Events gefunden",
            QUELLE_NAME,
            len(alle_events),
        )

    return alle_events


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
        print()
        if len(ergebnisse) > 1:
            print(f"Weitere {len(ergebnisse) - 1} Events vorhanden.")
            print(f"Zeitraum: {ergebnisse[0]['datum']} bis {ergebnisse[-1]['datum']}")
    else:
        print("Keine Events gefunden.")
        print("Mögliche Ursachen:")
        print("  - Seitenstruktur hat sich geändert")
        print("  - Netzwerkfehler")
        print("  - Alle gefundenen Events liegen in der Vergangenheit")
