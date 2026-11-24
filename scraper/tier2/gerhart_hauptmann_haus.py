"""
gerhart_hauptmann_haus.py – DiesDasDüsseldorf
Scraper für das Gerhart-Hauptmann-Haus (Stiftung GHH, Deutsch-osteuropäisches Forum): Veranstaltungen.

Quelle: Monatsseiten https://www.g-h-h.de/veranstaltung/2026/november, …/2026/dezember/1m, …/2027/januar/2m
(TYPO3 mit news-Erweiterung). Die Seite bietet nur den laufenden und die zwei folgenden Monate an; spätere
Monatsadressen (…/3m) liefern 404. Der Scraper liest den laufenden Monat und folgt den Monatslinks in der
Brotkrumen-Navigation (höchstens MAX_SEITEN Seiten).

robots.txt (geprüft 24.11.2026): „User-agent: * / Allow: /“ – alles erlaubt.

Aufbau je Termin (main .news-list-item):
  <time itemprop="dateStart" datetime="2026-12-02T18:30:00+00:00">2. Dez 18.30 Uhr</time>
  [<time itemprop="dateEnd" …>] <a href="/veranstaltung/<slug>/2026/dezember/1m"><h2>Titel</h2><h3>– Untertitel</h3></a>
Die Uhrzeit im datetime-Attribut ist Ortszeit (trotz „+00:00“); der Scraper liest sie aus dem sichtbaren Text
(„18.30 Uhr“). Zeiträume (Ausstellungen, Bücherbasar, Schließzeiten) werden übersprungen, ebenso Termine außerhalb
des Hauses (z. B. „conference in Cologne“).

Kategorie: kultur; Konzerte (Konzert, Liederabend, Chor, Klavierabend) musik.

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

BASE_URL = "https://www.g-h-h.de"
START_URL = "https://www.g-h-h.de/"
QUELLE_NAME = "Gerhart Hauptmann Haus"
ORT_STANDARD = "Gerhart Hauptmann Haus"
ADRESSE_STANDARD = "Bismarckstraße 90, 40210 Düsseldorf"
KATEGORIE_STANDARD = "kultur"

MAX_SEITEN = 15
PAUSE_S = 2.0   # Projektregel: mindestens 2 Sekunden zwischen Anfragen

MONATE = ["januar", "februar", "maerz", "april", "mai", "juni", "juli", "august", "september", "oktober",
          "november", "dezember"]

_MONATSLINK = re.compile(r"^/veranstaltung/\d{4}/[a-zäöü]+(?:/\d+m)?/?$")
_MONATSSUFFIX = re.compile(r"/\d{4}/[a-zäöü]+(?:/\d+m)?/?$")
_MUSIK = re.compile(r"konzert|liederabend|\bchor\b|klavierabend|kammermusik", re.I)
_NICHT_TERMIN = re.compile(r"ausstellung|schließzeit|schliesszeit|geschlossen|bücherbasar", re.I)
_AUSWAERTS = re.compile(r"\bin (?:Köln|Cologne|Bonn|Essen|Duisburg|Berlin|Brüssel|Brussels)\b|\bonline\b|\bZoom\b",
                        re.I)
_ABGESAGT = re.compile(r"\babgesagt\b|\bentfällt\b|\bverschoben\b", re.I)
_UHRZEIT = re.compile(r"\b(\d{1,2})[.:](\d{2})\s*Uhr", re.I)


def _monats_url(heute: date) -> str:
    """Adresse der Monatsseite des laufenden Monats (z. B. …/veranstaltung/2026/november)."""
    return f"{BASE_URL}/veranstaltung/{heute.year}/{MONATE[heute.month - 1]}"


def _monatslinks(html: str) -> list[str]:
    """Absolute Adressen aller Monatsseiten aus der Brotkrumen-Navigation, in Seitenreihenfolge."""
    soup = BeautifulSoup(html or "", "html.parser")
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if _MONATSLINK.match(href):
            url = urljoin(BASE_URL, href)
            if url not in links:
                links.append(url)
    return links


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el else ""


def _termin_aus_eintrag(eintrag) -> Optional[dict]:
    """Ein Event-Dict aus einem .news-list-item (ohne Zeitfenster-Prüfung) oder None."""
    start_el = eintrag.find("time", attrs={"itemprop": "dateStart"})
    if not start_el:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", start_el.get("datetime", ""))
    if not m:
        return None
    datum = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    ende_el = eintrag.find("time", attrs={"itemprop": "dateEnd"})
    if ende_el and not ende_el.get("datetime", "").startswith(datum):
        return None   # Zeitraum: Ausstellung, Basar, Schließzeit

    link = eintrag.find("a", href=True)
    if not link:
        return None
    titel = _text(link.find("h2")) or (link.get("title") or "").strip()
    titel = re.sub(r"\s*[–-]\s*$", "", titel).strip()
    untertitel = re.sub(r"^[–-]\s*", "", _text(link.find("h3")))
    if not titel:
        return None
    gesamt = f"{titel} {untertitel}"
    if _NICHT_TERMIN.search(titel) or _AUSWAERTS.search(gesamt) or _ABGESAGT.search(gesamt):
        return None

    uhrzeit = None
    z = _UHRZEIT.search(_text(start_el))
    if z and int(z.group(1)) <= 23 and int(z.group(2)) <= 59:
        uhrzeit = f"{int(z.group(1)):02d}:{int(z.group(2)):02d}"

    quelle_url = urljoin(BASE_URL, _MONATSSUFFIX.sub("", link["href"].strip()))

    bild_url = None
    img = eintrag.find("img")
    if img and (img.get("src") or img.get("data-src")):
        src = urljoin(BASE_URL, (img.get("src") or img.get("data-src")).strip())
        bild_url = src if src.startswith(BASE_URL) else None

    return {
        "titel": titel,
        "datum": datum,
        "uhrzeit": uhrzeit,
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": "musik" if _MUSIK.search(gesamt) else KATEGORIE_STANDARD,
        "beschreibung": None,
        "preis": None,
        "quelle_name": QUELLE_NAME,
        "quelle_url": quelle_url,
        "bild_url": bild_url,
        "bild_generiert": False,
        "status": "neu",
    }


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Alle Termine einer Monatsseite im Zeitfenster heute … enddatum (rein, testbar)."""
    soup = BeautifulSoup(html or "", "html.parser")
    bereich = soup.find("main") or soup
    events, gesehen = [], set()
    for eintrag in bereich.select(".news-list-item"):
        event = _termin_aus_eintrag(eintrag)
        if not event or not (heute <= date.fromisoformat(event["datum"]) <= enddatum):
            continue
        schluessel = (event["titel"], event["datum"], event["uhrzeit"])
        if schluessel not in gesehen:
            gesehen.add(schluessel)
            events.append(event)
    return events


def scrape() -> list[dict]:
    """
    Scrapt die Veranstaltungen des Gerhart-Hauptmann-Hauses (laufender Monat + verlinkte Folgemonate).
    Wirft nie; bei Fehlern leere Liste.
    """
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    events: list[dict] = []
    try:
        erste_url = _monats_url(heute)
        html = seite_abrufen(erste_url, logger, wartezeit=PAUSE_S)
        if html is None:
            # Rückfall: Monatslink von der Startseite (falls sich die Monatsadresse ändert)
            start = seite_abrufen(START_URL, logger, wartezeit=PAUSE_S)
            links = _monatslinks(start or "")
            if not links:
                logger.error("%s: keine Monatsseite erreichbar", QUELLE_NAME)
                return []
            erste_url = links[0]
            html = seite_abrufen(erste_url, logger, wartezeit=PAUSE_S)
            if html is None:
                logger.error("%s: Monatsseite %s nicht erreichbar", QUELLE_NAME, erste_url)
                return []

        seiten = {erste_url: html}
        for url in _monatslinks(html):
            if len(seiten) >= MAX_SEITEN:
                break
            if url in seiten or url.rstrip("/") == erste_url.rstrip("/"):
                continue
            weitere = seite_abrufen(url, logger, wartezeit=PAUSE_S)
            if weitere is not None:
                seiten[url] = weitere

        gesehen: set[tuple] = set()
        for s in seiten.values():
            for event in _termine_aus_html(s, heute, enddatum):
                schluessel = (event["titel"], event["datum"], event["uhrzeit"])
                if schluessel not in gesehen:
                    gesehen.add(schluessel)
                    events.append(event)
        events.sort(key=lambda e: (e["datum"], e["uhrzeit"] or ""))
        logger.info("%s: %d Monatsseite(n) gelesen", QUELLE_NAME, len(seiten))
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
