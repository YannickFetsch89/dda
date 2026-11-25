"""
globe_neuss.py – DiesDasDüsseldorf
Scraper für das Globe Neuss (Shakespeare Festival des Kulturamts Neuss).
Quelle: Programmseite https://kulturamt-neuss.de/shakespeare/programm/ (www.shakespeare-festival.de leitet dorthin
weiter) und die Seiten der einzelnen Produktionen (Abschnitt „Termine“ mit Datum, Uhrzeit, Spielort, Ticket-Link)
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V2, Welle B).

robots.txt (kulturamt-neuss.de, geprüft am 25.11.2026): „User-agent: * / Disallow: /wp-admin/ / Allow:
/wp-admin/admin-ajax.php“ – Programm- und Produktionsseiten sind erlaubt, kein Crawl-delay. shakespeare-festival.de
hat keine robots.txt (404). Mindestens 2 s zwischen den Anfragen.

Ablauf: Die Programmseite listet die Produktionen des laufenden Festivaljahrs (div.program-grid-item, Attribut
data-past="true", wenn alle Termine vorbei sind). Nur für Produktionen mit kommenden Terminen wird die Detailseite
geladen (während des Festivals rund 20 Anfragen, sonst keine). Auf der Detailseite steht je Termin ein
div.dates-grid-item („Sa., 16. Mai 2026 | 19:30 Uhr“, Spielort „Globe Neuss“, Link „Tickets“ zum Webshop
tickets.kulturamt-neuss.de).
- Das Festival läuft nur im Mai/Juni. Außerhalb der Festivalzeit gibt es 0 Termine – dann logger.info mit dem Wort
  „Festivalsaison“, damit pipeline/lauf_report.py die Quelle als saisonal erkennt (Muster „saison“), keine Warnung.
- Nur Termine im Globe (Spielort enthält „Globe“). 2025 spielte das Festival z. B. gar nicht im Globe; Termine an
  anderen Orten (Landesgartenschau, Stadtgarten …) werden ausgelassen.
- Kategorie: Workshop → community, sonst kultur (Theater, Lesungen, Musiktheater).
- Adresse: „Globe Theater Neuss, Hammer Landstraße 2, 41460 Neuss“ (Pressedienst der Stadt Neuss zum Festival
  2022/2023) – die Website des Kulturamts nennt keine Anschrift.

Erstellt: 2026-11-25
"""
import json
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.datum import MONAT_MAP
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ticket_link import ticket_link_aus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Globe Neuss"
BASIS_URL = "https://kulturamt-neuss.de"
PROGRAMM_URL = "https://kulturamt-neuss.de/shakespeare/programm/"
ORT = "Globe Neuss"
ADRESSE = "Hammer Landstraße 2, 41460 Neuss"
WARTEZEIT = 2.0
MAX_DETAILSEITEN = 40

_DATUM = re.compile(r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)\.?\s+(\d{4})")
_UHRZEIT = re.compile(r"(\d{1,2})(?:[:.](\d{2}))?\s*Uhr", re.I)
_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus)\b", re.I)


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True).replace("\xad", "")).strip() if el else ""


def _datum(text: str) -> Optional[str]:
    m = _DATUM.search(text or "")
    if not m:
        return None
    monat = MONAT_MAP.get(m.group(2).lower())
    if not monat:
        return None
    try:
        return date(int(m.group(3)), monat, int(m.group(1))).isoformat()
    except ValueError:
        return None


def _uhrzeit(text: str) -> Optional[str]:
    m = _UHRZEIT.search(text or "")
    if not m:
        return None
    stunde, minute = int(m.group(1)), int(m.group(2) or 0)
    return f"{stunde:02d}:{minute:02d}" if 0 <= stunde <= 23 and 0 <= minute <= 59 else None


def _eigenes_bild(url: Optional[str]) -> Optional[str]:
    """Nur Bilder von kulturamt-neuss.de übernehmen."""
    if not url or url.startswith("data:"):
        return None
    absolut = urljoin(BASIS_URL, url)
    host = urlparse(absolut).netloc.lower()
    return absolut if host == "kulturamt-neuss.de" or host.endswith(".kulturamt-neuss.de") else None


def _programm_aus_html(html: str, alle: bool = False) -> list[str]:
    """Programmseite → URLs der Produktionsseiten (ohne alle=True nur Produktionen mit kommenden Terminen)."""
    soup = BeautifulSoup(html or "", "html.parser")
    urls: list[str] = []
    for item in soup.select("div.program-grid-item"):
        if not alle and (item.get("data-past") or "").lower() == "true":
            continue
        a = item.select_one("h3 a[href]") or item.select_one("a[href]")
        if not a:
            continue
        url = urljoin(BASIS_URL, a["href"])
        if url not in urls:
            urls.append(url)
    return urls


def _termine_aus_detail(html: str, seiten_url: str, heute: date, enddatum: date) -> list[dict]:
    """Produktionsseite → Event-Dicts im Projektformat (nur Termine im Globe zwischen heute und enddatum)."""
    soup = BeautifulSoup(html or "", "html.parser")
    titel = _text(soup.select_one("h1.hero-section__title") or soup.select_one("h1"))
    if not titel:
        return []
    bild_el = soup.select_one("section.hero-section img") or soup.select_one("img.size-full")
    bild = _eigenes_bild(bild_el.get("src") if bild_el else None)
    kategorie = "community" if re.search(r"workshop", titel, re.I) else "kultur"
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for termin in soup.select("div.dates-grid-item"):
        datum_text = _text(termin.select_one(".dates-grid-item__date"))
        spielort = _text(termin.select_one(".dates-grid-item__venue"))
        datum = _datum(datum_text)
        if not datum or not heute.isoformat() <= datum <= enddatum.isoformat():
            continue
        if "globe" not in spielort.lower():
            logger.debug("Globe Neuss: Termin an anderem Ort ausgelassen: %s (%s, %s)", titel, datum, spielort)
            continue
        if _ABGESAGT.search(_text(termin)):
            continue
        uhrzeit = _uhrzeit(datum_text)
        schluessel = (titel.lower(), datum, uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT,
            "adresse": ADRESSE,
            "kategorie": kategorie,
            "beschreibung": None,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": seiten_url,
            "ticket_url": ticket_link_aus(termin.select_one(".dates-grid-item__links"), BASIS_URL),
            "bild_url": bild,
            "bild_generiert": False,
            "status": "neu",
        })
    return events


def scrape() -> list[dict]:
    """Scrapt die Vorstellungen des Shakespeare Festivals im Globe Neuss (nur zur Festivalzeit)."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        html = seite_abrufen(PROGRAMM_URL, logger, wartezeit=WARTEZEIT)
        if html is None:
            logger.error("Scraper %s: Programmseite nicht erreichbar", QUELLE_NAME)
            return []
        if not _programm_aus_html(html, alle=True):
            logger.warning("Scraper %s: keine Produktionen auf der Programmseite – Seitenstruktur geändert?",
                           QUELLE_NAME)
            return []
        urls = _programm_aus_html(html)
        if not urls:
            logger.info("Scraper %s: keine kommenden Vorstellungen – außerhalb der Festivalsaison (Mai/Juni)",
                        QUELLE_NAME)
            return []
        events: list[dict] = []
        gesehen: set[tuple] = set()
        termine_gelesen = 0
        for url in urls[:MAX_DETAILSEITEN]:
            detail = seite_abrufen(url, logger, wartezeit=WARTEZEIT)
            if detail is None:
                continue
            termine_gelesen += detail.count("dates-grid-item__date")
            for ev in _termine_aus_detail(detail, url, heute, enddatum):
                schluessel = (ev["titel"].lower(), ev["datum"], ev["uhrzeit"])
                if schluessel not in gesehen:
                    gesehen.add(schluessel)
                    events.append(ev)
        if not events and termine_gelesen:
            logger.info("Scraper %s: keine Termine im Globe in dieser Festivalsaison (andere Spielorte)", QUELLE_NAME)
        elif not events:
            logger.warning("Scraper %s: 0 Termine bei erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
        logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
        return events
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for ev in ergebnisse[:3]:
        print(json.dumps(ev, ensure_ascii=False, indent=2))
