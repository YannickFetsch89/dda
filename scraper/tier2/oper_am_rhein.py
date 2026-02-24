"""
oper_am_rhein.py – DiesDasDüsseldorf
Scraper für die Deutsche Oper am Rhein: Spielplan und Veranstaltungen.

Die Seite nutzt ein spiritec-WebCMS und rendert alle Events serverseitig als HTML.
Jede Performance ist ein <div class="performance js-schedule-element"> mit
Schema.org-Mikrodaten (itemprop="startDate", "name", "location").

Erstellt: 2026-02-24
"""
import logging
import re
import unicodedata
from datetime import date, datetime
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://www.operamrhein.de"
SPIELPLAN_URL = "https://www.operamrhein.de/spielplan/"
QUELLE_NAME = "Deutsche Oper am Rhein"
STANDARD_ADRESSE = "Heinrich-Heine-Allee 16a, 40213 Düsseldorf"

# Anzahl der zukünftigen Monate, die zusätzlich zur Startseite abgerufen werden.
# Die Startseite enthält bereits den laufenden und den Folgemonat.
# Weitere Monate werden über /spielplan/kalender/YYYY-MM/ abgerufen.
MONATE_VORAUS = 2


# ---------------------------------------------------------------------------
# Kategorie-Mapping: colorscheme-Klassen → DDA-Kategorien
# ---------------------------------------------------------------------------
COLORSCHEME_KATEGORIE: dict[str, str] = {
    "oper": "kultur",
    "ballett": "kultur",
    "jungeoper": "kultur",
    "ufo": "kultur",
    "sonderveranstaltungen": "kultur",
    "default": "kultur",
}

# Schlüsselwörter in Kategorie-/Attribut-Texten für feinere Zuordnung
KATEGORIE_SCHLUESSELN: list[tuple[str, str]] = [
    ("konzert", "musik"),
    ("gala", "musik"),
    ("festival", "musik"),
    ("ballett", "kultur"),
    ("tanz", "kultur"),
    ("oper", "kultur"),
    ("theater", "kultur"),
    ("führung", "kultur"),
    ("workshop", "community"),
    ("mitmachen", "community"),
    ("kinder", "family"),
    ("familien", "family"),
    ("jugend", "family"),
]


def _kategorie_ermitteln(colorscheme: str, kategorie_text: str, attrs: list[str]) -> str:
    """
    Ermittelt die DDA-Kategorie aus colorscheme-Klasse, Kategorie-Span und Attributen.

    Die colorscheme-Klasse ist der zuverlässigste Indikator. Zur Verfeinerung
    werden Kategorie-Text und Attribut-Texte durchsucht.

    Args:
        colorscheme:    Wert aus der colorscheme-* CSS-Klasse (z.B. "oper")
        kategorie_text: Text aus .performance__category (z.B. "Ballett")
        attrs:          Texte aus .attribute-Spans (z.B. ["Mitmachen", "Führung"])

    Returns:
        DDA-Kategorie-String
    """
    # Sonderveranstaltungen und Gala prüfen
    alle_texte = " ".join([kategorie_text] + attrs).lower()
    for schluessel, kategorie in KATEGORIE_SCHLUESSELN:
        if schluessel in alle_texte:
            return kategorie

    return COLORSCHEME_KATEGORIE.get(colorscheme, "kultur")


def _text_bereinigen(text: str) -> str:
    """
    Entfernt weiche Trennzeichen (soft hyphens, zero-width spaces) und
    normalisiert Unicode, um Anzeigeprobleme zu vermeiden.

    Args:
        text: Rohtext von der Seite

    Returns:
        Bereinigter Text
    """
    # Weiche Trennzeichen (U+00AD) und ähnliche Steuerzeichen entfernen
    text = text.replace("\u00ad", "")  # soft hyphen
    text = text.replace("\u200b", "")  # zero-width space
    text = text.replace("\u200c", "")  # zero-width non-joiner
    text = text.replace("\u200d", "")  # zero-width joiner
    # NFC-Normalisierung
    text = unicodedata.normalize("NFC", text)
    return text.strip()


def _preis_aus_element(performance_el) -> Optional[str]:
    """
    Extrahiert den Preis aus einem Performance-Element.

    Die Website verwendet eine Anti-Scraping-Technik: Der angezeigte Preis
    wird durch CSS-versteckte Zahlen verfälscht. Deshalb lesen wir den Preis
    nicht über get_text(), sondern suchen nach dem sichtbaren <span>-Element
    mit der Klasse .ticketbutton__price.

    Wenn die Vorstellung ausverkauft ist, wird "Ausverkauft" zurückgegeben.
    Wenn keine Preisinformation vorhanden ist, wird None zurückgegeben.

    Args:
        performance_el: BeautifulSoup-Element einer Performance

    Returns:
        Preis als String (z.B. "ab 12 €", "Ausverkauft") oder None
    """
    # Ausverkauft prüfen
    ausverkauft = performance_el.select_one(
        ".ticketbutton__tickets--style-soldout"
    )
    if ausverkauft:
        return "Ausverkauft"

    # Preis-Span: Wir lesen nur den direkten Text-Inhalt des Spans,
    # da versteckte Spans in CSS andere Zahlen einblenden können.
    preis_el = performance_el.select_one(".ticketbutton__price")
    if preis_el:
        # Nur direkte Text-Nodes auslesen (keine Kinder-Elemente)
        direkte_texte = [
            t.strip()
            for t in preis_el.find_all(string=True, recursive=False)
            if t.strip()
        ]
        if direkte_texte:
            zahl = direkte_texte[0]
            # Plausibilitätsprüfung: Oper-Preise sind typischerweise 1–500 €
            try:
                wert = int(zahl)
                if 0 < wert <= 500:
                    return f"ab {wert} €"
            except ValueError:
                pass

    # Ticket-Button-Text als letzten Hinweis auswerten
    ticket_btn = performance_el.select_one(".ticketbutton__tickets")
    if ticket_btn:
        btn_text = ticket_btn.get_text(strip=True)
        if btn_text in ("Karten", "Restkarten"):
            return None  # Preis unbekannt, aber Karten verfügbar
        if btn_text == "Info":
            return "kostenlos oder auf Anfrage"

    return None


def _event_aus_performance(performance_el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem <div class="performance js-schedule-element">.

    Seitenstruktur (spiritec WebCMS):
        <div class="performance ... js-schedule-element"
             id="YYYY-MM-DD-pNNNN"
             data-day-token="YYYY-MM-DD"
             itemscope itemtype="http://schema.org/Event">
          <div itemprop="location" ...>
            <span itemprop="address">...</span>
          </div>
          <div class="performance__col performance__col--date">
            <meta itemprop="startDate" content="YYYY-MM-DDTHH:MM:SS">...
            <div class="performance__location ...">Venue-Name</div>
          </div>
          <div class="performance__col performance__col--info">
            <div class="performance__maininfo ...">
              <div class="performance__image" data-image-url="/...">
              <a class="performance__link" href="/spielplan/kalender/.../NNN/">
                <div class="performance__attributes">
                  <span class="attribute">Label</span>
                  <span class="performance__category">Typ</span>
                </div>
                <div class="performance__title">
                  <h3><span itemprop="name">Titel</span></h3>
                </div>
              </a>
            </div>
            <div class="performance__productioninfo ...">Beschreibung</div>
          </div>
          <div class="performance__col performance__col--action">
            <div class="ticketbutton ...">
              <span class="ticketbutton__price">Preis</span>
            </div>
          </div>
        </div>

    Args:
        performance_el: BeautifulSoup-Element
        heute:          Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict oder None bei fehlenden Pflichtfeldern / vergangenem Event
    """
    try:
        # --- Datum aus data-day-token (zuverlässigster Wert) ---
        day_token = performance_el.get("data-day-token", "")
        if not day_token:
            # Fallback: ID parsen (Format: "2026-02-24-p3271")
            perf_id = performance_el.get("id", "")
            treffer = re.match(r"(\d{4}-\d{2}-\d{2})", perf_id)
            day_token = treffer.group(1) if treffer else ""

        if not day_token:
            logger.debug("Kein Datum gefunden, Performance wird übersprungen")
            return None

        try:
            datum_obj = date.fromisoformat(day_token)
        except ValueError:
            logger.debug("Ungültiges Datumsformat: %s", day_token)
            return None

        # Vergangene Events überspringen
        if datum_obj < heute:
            return None

        datum = datum_obj.isoformat()

        # --- Uhrzeit aus itemprop="startDate" content ---
        uhrzeit = None
        # Performance-Spalte --date enthält die primäre Zeitangabe
        startdate_el = performance_el.select_one(
            ".performance__col--date [itemprop='startDate'][content]"
        )
        if startdate_el:
            content = startdate_el.get("content", "")
            # Format: "2026-02-24T11:00:00"
            treffer = re.search(r"T(\d{2}):(\d{2})", content)
            if treffer:
                stunde = int(treffer.group(1))
                minute = int(treffer.group(2))
                if 0 <= stunde <= 23 and 0 <= minute <= 59:
                    uhrzeit = f"{stunde:02d}:{minute:02d}"

        # --- Titel: itemprop="name" innerhalb der Hauptüberschrift ---
        # Die itemprop="name"-Location-Spans haben denselben Wert ("Deutsche Oper am Rhein"),
        # daher gezielt den Titel-Span im h3 suchen.
        titel_span = performance_el.select_one(
            "h3.headline__headline [itemprop='name']"
        )
        if not titel_span:
            # Fallback: erster itemprop-name, der nicht der Venue-Name ist
            for span in performance_el.select("[itemprop='name']"):
                text = _text_bereinigen(span.get_text(strip=True))
                if text and text != QUELLE_NAME:
                    titel_span = span
                    break

        if not titel_span:
            logger.debug("Kein Titel gefunden für %s", day_token)
            return None

        titel = _text_bereinigen(titel_span.get_text(strip=True))
        if not titel:
            return None

        # Untertitel (optional) an Titel anhängen
        subtitle_el = performance_el.select_one(".headline__subtitle")
        if subtitle_el:
            subtitle = _text_bereinigen(subtitle_el.get_text(strip=True))
            if subtitle:
                titel = f"{titel} – {subtitle}"

        # --- Event-URL ---
        link_el = performance_el.select_one("a.performance__link")
        if link_el and link_el.get("href"):
            quelle_url = urljoin(BASE_URL, link_el.get("href"))
        else:
            quelle_url = SPIELPLAN_URL

        # --- Ort: .performance__location in der Datumsspalte (für Desktop) ---
        # Es gibt zwei identische Spans (Desktop / Mobile), wir nehmen den ersten.
        ort_el = performance_el.select_one(
            ".performance__col--date .performance__location"
        )
        if ort_el:
            ort = _text_bereinigen(ort_el.get_text(strip=True))
        else:
            # Fallback: beliebiger .performance__location
            ort_els = performance_el.select(".performance__location")
            ort = _text_bereinigen(ort_els[0].get_text(strip=True)) if ort_els else ""

        if not ort:
            ort = QUELLE_NAME

        # --- Adresse: aus itemprop="address" (im versteckten Location-Block) ---
        adresse_el = performance_el.select_one("[itemprop='address']")
        if adresse_el:
            adresse = _text_bereinigen(adresse_el.get_text(strip=True))
            if not adresse:
                adresse = STANDARD_ADRESSE
        else:
            adresse = STANDARD_ADRESSE

        # --- Kategorie ---
        css_klassen = performance_el.get("class", [])
        colorscheme = next(
            (k.replace("colorscheme-", "") for k in css_klassen if k.startswith("colorscheme-")),
            "default",
        )
        kategorie_el = performance_el.select_one(".performance__category")
        kategorie_text = (
            _text_bereinigen(kategorie_el.get_text(strip=True)) if kategorie_el else ""
        )
        attr_els = performance_el.select(".attribute")
        attrs = [_text_bereinigen(a.get_text(strip=True)) for a in attr_els if a.get_text(strip=True)]

        kategorie = _kategorie_ermitteln(colorscheme, kategorie_text, attrs)

        # --- Beschreibung ---
        # Primär: .performance__productioninfo (Unterzeile unter dem Titel)
        # Sekundär: Kategorie-Text und Attribute als Kurzinfo
        beschreibung = None
        desc_els = performance_el.select(".performance__productioninfo")
        if desc_els:
            # Ersten beschreibenden Text nehmen (Desktop-Version), duplizierten ignorieren
            desc_text = _text_bereinigen(desc_els[0].get_text(strip=True))
            if desc_text:
                beschreibung = desc_text[:300]

        if not beschreibung and (kategorie_text or attrs):
            teile = []
            if kategorie_text:
                teile.append(kategorie_text)
            teile.extend(attrs)
            beschreibung = ", ".join(teile)[:300] or None

        # --- Preis ---
        preis = _preis_aus_element(performance_el)

        # --- Bild ---
        bild_url = None
        bild_el = performance_el.select_one(".performance__image[data-image-url]")
        if bild_el:
            bild_pfad = bild_el.get("data-image-url", "")
            if bild_pfad:
                bild_url = urljoin(BASE_URL, bild_pfad)

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": adresse,
            "kategorie": kategorie,
            "beschreibung": beschreibung,
            "preis": preis,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error(
            "Fehler beim Parsen einer Performance: %s", str(fehler), exc_info=True
        )
        return None


def _events_aus_html(html: str, heute: date, gesehene_ids: set[str]) -> list[dict]:
    """
    Parst alle Events aus dem HTML-Inhalt einer Spielplan-Seite.

    Args:
        html:          HTML-String der Spielplan-Seite
        heute:         Heutiges Datum für Filterung
        gesehene_ids:  Set mit bereits verarbeiteten Performance-IDs (Duplikat-Schutz)

    Returns:
        Liste neu gefundener Event-Dicts
    """
    events: list[dict] = []
    soup = BeautifulSoup(html, "html.parser")

    performance_els = soup.select("div.performance.js-schedule-element")

    if not performance_els:
        logger.warning(
            "Keine Performance-Elemente auf der Seite gefunden – "
            "Seitenstruktur hat sich möglicherweise geändert."
        )
        return events

    for perf_el in performance_els:
        # Eindeutige ID zur Duplikatsvermeidung (Format: "2026-02-24-p3271")
        perf_id = perf_el.get("id", "")
        if perf_id in gesehene_ids:
            continue
        gesehene_ids.add(perf_id)

        event = _event_aus_performance(perf_el, heute)
        if event is not None:
            events.append(event)

    return events


def _naechste_monate_ermitteln(html_startseite: str, heute: date) -> list[str]:
    """
    Ermittelt die URLs der nächsten Monate aus den Navigationslinks der Startseite.

    Die Startseite enthält bereits den aktuellen und den nächsten Monat.
    Für weitere Monate werden die Kalender-Navigationslinks ausgelesen.

    Args:
        html_startseite: HTML der Spielplan-Startseite
        heute:           Heutiges Datum

    Returns:
        Liste von Monats-URLs (z.B. ["https://...//spielplan/kalender/2026-04/", ...])
    """
    soup = BeautifulSoup(html_startseite, "html.parser")

    # Alle Monats-URLs aus den Navigationslinks sammeln
    monate_im_html: set[str] = set()
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        treffer = re.match(r"^/spielplan/kalender/(\d{4}-\d{2})/$", href)
        if treffer:
            monate_im_html.add(treffer.group(1))

    if not monate_im_html:
        return []

    # Bereits geladene Monate (der aktuelle und nächste sind in der Startseite)
    aktuelle_monate = soup.select(".schedule__monthinfos[data-month]")
    bereits_geladen: set[str] = {
        el.get("data-month", "") for el in aktuelle_monate
    }

    # Zukünftige Monate nach heute sortieren
    alle_monate_sortiert = sorted(
        m for m in monate_im_html if m >= heute.strftime("%Y-%m")
    )

    # Monate, die noch nicht geladen wurden, bis zum Limit aufnehmen
    neue_monate_urls: list[str] = []
    zaehler = 0
    for monat in alle_monate_sortiert:
        if monat in bereits_geladen:
            continue
        if zaehler >= MONATE_VORAUS:
            break
        neue_monate_urls.append(
            urljoin(BASE_URL, f"/spielplan/kalender/{monat}/")
        )
        zaehler += 1

    return neue_monate_urls


def scrape() -> list[dict]:
    """
    Scrapt den kompletten Spielplan der Deutschen Oper am Rhein.

    Ablauf:
      1. Startseite /spielplan/ abrufen (enthält laufenden + nächsten Monat)
      2. Weitere Monats-URLs aus der Navigation ermitteln
      3. Diese Zusatzmonate ebenfalls abrufen (bis MONATE_VORAUS)
      4. Aus allen Seiten Events extrahieren, Duplikate verhindern

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
        Nur zukünftige Events (heute oder später) werden zurückgegeben.
    """
    events: list[dict] = []
    heute = date.today()
    gesehene_ids: set[str] = set()

    logger.info("Starte Scraper: %s", QUELLE_NAME)

    # --- Schritt 1: Startseite abrufen ---
    try:
        html_startseite = seite_abrufen(SPIELPLAN_URL, logger)
        if html_startseite is None:
            logger.error("Startseite konnte nicht abgerufen werden: %s", SPIELPLAN_URL)
            return []
    except Exception as fehler:
        logger.error("Unerwarteter Fehler beim Abrufen der Startseite: %s", fehler)
        return []

    startseite_events = _events_aus_html(html_startseite, heute, gesehene_ids)
    logger.info("Startseite: %d Events gefunden", len(startseite_events))
    events.extend(startseite_events)

    # --- Schritt 2: Weitere Monate aus Navigation ermitteln ---
    weitere_urls: list[str] = []
    try:
        weitere_urls = _naechste_monate_ermitteln(html_startseite, heute)
        logger.info("Weitere Monats-URLs: %s", weitere_urls)
    except Exception as fehler:
        logger.warning("Monatsnavigation konnte nicht ausgewertet werden: %s", fehler)

    # --- Schritt 3: Zusätzliche Monate abrufen ---
    for url in weitere_urls:
        try:
            html_monat = seite_abrufen(url, logger)
            if html_monat is None:
                logger.warning("Monatsseite konnte nicht abgerufen werden: %s", url)
                continue
            monat_events = _events_aus_html(html_monat, heute, gesehene_ids)
            logger.info("Seite %s: %d neue Events", url, len(monat_events))
            events.extend(monat_events)
        except Exception as fehler:
            logger.error("Fehler beim Abrufen von %s: %s", url, fehler)

    if not events:
        logger.warning(
            "Scraper %s: 0 Events gefunden – "
            "Seitenstruktur oder Verfügbarkeit hat sich möglicherweise geändert.",
            QUELLE_NAME,
        )
    else:
        logger.info(
            "Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events)
        )

    return events


if __name__ == "__main__":
    # Direkter Testlauf: python -m scraper.tier2.oper_am_rhein
    import json

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    ergebnisse = scrape()

    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    if ergebnisse:
        print("--- Beispiel-Event (erstes Ergebnis) ---")
        print(json.dumps(ergebnisse[0], ensure_ascii=False, indent=2))
        print()

        if len(ergebnisse) > 1:
            print("--- Beispiel-Event (letztes Ergebnis) ---")
            print(json.dumps(ergebnisse[-1], ensure_ascii=False, indent=2))
