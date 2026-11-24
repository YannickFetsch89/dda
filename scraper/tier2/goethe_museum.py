"""
goethe_museum.py – DiesDasDüsseldorf
Scraper für das Goethe-Museum Düsseldorf (Anton-und-Katharina-Kippenberg-Stiftung, Schloss Jägerhof).

Quelle: https://www.goethe-museum.de/de/veranstaltung/veranstaltungskalender (Drupal-View, Auswahl „Aktuell“).
Weitere Seiten (Drupal-Pager „?page=N“) werden gelesen, falls vorhanden (Stand 24.11.2026: eine Seite, 6 Einträge).

robots.txt (geprüft 24.11.2026): „Crawl-delay: 10“, gesperrt sind nur Systempfade (/admin/, /search/, /user/…,
/modules/ usw.) – /de/veranstaltung/ ist erlaubt. Der Scraper wartet vor jeder Anfrage 10 Sekunden.

Aufbau je Termin (.views-row):
  <span class="date-display-single">27.11.2026 <br> Freitag <br> 19:30 Uhr</span>   (oder date-display-range)
  <h3>Untertitel</h3> <h2>Titel</h2> <p>Teaser</p> <a href="/de/veranstaltung/<slug>">mehr</a>
Zeiträume über mehrere Tage (Sonderausstellungen) werden übersprungen. Bilder hat die Liste nicht (bild_url None).

Kategorie: kultur; Konzerte (Konzert im Titel/Untertitel, Liederabend, Chor) musik.

Erstellt: 2026-11-24
"""
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://www.goethe-museum.de"
LISTE_URL = "https://www.goethe-museum.de/de/veranstaltung/veranstaltungskalender"
QUELLE_NAME = "Goethe-Museum"
ORT_STANDARD = "Goethe-Museum"
ADRESSE_STANDARD = "Jacobistraße 2, 40211 Düsseldorf"
KATEGORIE_STANDARD = "kultur"

CRAWL_DELAY_S = 10.0   # robots.txt: Crawl-delay 10
MAX_SEITEN = 15

_DATUM = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
_UHRZEIT = re.compile(r"\b(\d{1,2})[:.](\d{2})\s*Uhr", re.I)
_MUSIK = re.compile(r"konzert|liederabend|\bchor\b|klavierabend|kammermusik", re.I)
_ABGESAGT = re.compile(r"\babgesagt\b|\bentfällt\b|\bfällt aus\b", re.I)


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el else ""


def _datum(text: str) -> Optional[str]:
    m = _DATUM.search(text or "")
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return None


def _uhrzeit(text: str) -> Optional[str]:
    m = _UHRZEIT.search(text or "")
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        return None
    return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"


def _termin_aus_zeile(zeile) -> Optional[dict]:
    """Ein Event-Dict aus einer .views-row (ohne Zeitfenster-Prüfung) oder None."""
    termin = zeile.select_one(".views-field-field-termin")
    if not termin:
        return None
    start_el = termin.select_one(".date-display-start") or termin.select_one(".date-display-single") or termin
    ende_el = termin.select_one(".date-display-end")
    datum = _datum(_text(start_el))
    if not datum:
        return None
    if ende_el and _datum(_text(ende_el)) not in (None, datum):
        return None   # mehrtägiger Zeitraum = Ausstellung

    titel = _text(zeile.select_one(".views-field-title"))
    untertitel = _text(zeile.select_one(".views-field-field-veranstaltungsub"))
    if not titel:
        return None
    if _ABGESAGT.search(f"{titel} {untertitel}"):
        return None

    link = zeile.select_one(".views-field-view-node a[href]") or zeile.find("a", href=re.compile(r"/veranstaltung/"))
    quelle_url = urljoin(BASE_URL, link["href"].strip()) if link else LISTE_URL

    return {
        "titel": titel,
        "datum": datum,
        "uhrzeit": _uhrzeit(_text(start_el)),
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": "musik" if _MUSIK.search(f"{titel} {untertitel}") else KATEGORIE_STANDARD,
        "beschreibung": None,
        "preis": None,
        "quelle_name": QUELLE_NAME,
        "quelle_url": quelle_url,
        "bild_url": None,
        "bild_generiert": False,
        "status": "neu",
    }


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Alle Termine der Kalenderseite im Zeitfenster heute … enddatum (rein, testbar)."""
    soup = BeautifulSoup(html or "", "html.parser")
    events, gesehen = [], set()
    for zeile in soup.select(".views-row"):
        event = _termin_aus_zeile(zeile)
        if not event or not (heute <= date.fromisoformat(event["datum"]) <= enddatum):
            continue
        schluessel = (event["titel"], event["datum"], event["uhrzeit"])
        if schluessel not in gesehen:
            gesehen.add(schluessel)
            events.append(event)
    return events


def _weitere_seiten(html: str) -> list[str]:
    """Adressen weiterer Seiten aus dem Drupal-Pager (…veranstaltungskalender?page=N), aufsteigend."""
    nummern = sorted({int(n) for n in re.findall(r"veranstaltungskalender\?(?:[^\"'#]*&(?:amp;)?)?page=(\d+)",
                                                  html or "") if int(n) > 0})
    return [f"{LISTE_URL}?page={n}" for n in nummern]


def scrape() -> list[dict]:
    """
    Scrapt den Veranstaltungskalender des Goethe-Museums (Crawl-delay 10 s). Wirft nie; bei Fehlern leere Liste.
    """
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    events: list[dict] = []
    try:
        html = seite_abrufen(LISTE_URL, logger, wartezeit=CRAWL_DELAY_S)
        if html is None:
            logger.error("%s: Veranstaltungskalender nicht erreichbar", QUELLE_NAME)
            return []
        seiten = [html]
        for url in _weitere_seiten(html)[: MAX_SEITEN - 1]:
            weitere = seite_abrufen(url, logger, wartezeit=CRAWL_DELAY_S)
            if weitere is None:
                break
            seiten.append(weitere)

        gesehen: set[tuple] = set()
        for s in seiten:
            for event in _termine_aus_html(s, heute, enddatum):
                schluessel = (event["titel"], event["datum"], event["uhrzeit"])
                if schluessel not in gesehen:
                    gesehen.add(schluessel)
                    events.append(event)
        logger.info("%s: %d Seite(n) gelesen", QUELLE_NAME, len(seiten))
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []

    if not events:
        logger.warning("%s: 0 Termine bei erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
    logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    import json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
