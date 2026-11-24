"""
theatermuseum.py – DiesDasDüsseldorf
Scraper für das Theatermuseum Düsseldorf (TMD, Hofgartenhaus): Programmkalender.

Quelle: https://theater-museum.de/kalender (Seiten ?page=2, ?page=3 …)
Die städtische Seite https://www.duesseldorf.de/theatermuseum verweist nur noch auf www.theater-museum.de; ihr
„Programmkalender“ (/theatermuseum/programmkalender) ist leer („Keine Nachrichten verfügbar“, Stand 24.11.2026).
Die eigene Website nutzt dieselbe CMS-Familie wie das Filmmuseum (Kacheln „b-teaser-slider“), JSON-LD nur als WebPage.

robots.txt (geprüft 24.11.2026):
  www.duesseldorf.de: sperrt nur „/*?tx_*“, „/*?cHash*“ und /typo3/ – solche URLs ruft der Scraper nicht ab.
  theater-museum.de: „User-agent: * / Disallow:“ – alles erlaubt.

Aufbau je Termin (div.event-item):
  <h4><strong>24.11.2026</strong></h4> <p>18:00–20:00 Uhr</p> <p class="address"> Zürndorfer-Forum</p>
  <p class="eventtype"> Workshop</p> … <a class="mb-2 d-block" href="…/kalender/veranstaltungen-startseite/…"
  title="Titel"> … <img src="https://theater-museum.de/media/…">

Ort: immer das Theatermuseum (Räume wie Lore-Lorentz-Saal, Studiobühne, Foyer liegen im Hofgartenhaus); nur Termine
mit Raum „Goethe-Museum“ (Kooperation, z. B. Poetry Slam) bekommen Ort und Adresse des Goethe-Museums.
Kategorie: kultur; Kinder-/Familienangebote (Typ oder Titel mit Kinder, Familie, Nachwuchs, Baby) family.

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

BASE_URL = "https://theater-museum.de"
LISTE_URL = "https://theater-museum.de/kalender"
QUELLE_NAME = "Theatermuseum Düsseldorf"
ORT_STANDARD = "Theatermuseum Düsseldorf"
ADRESSE_STANDARD = "Jägerhofstraße 1, 40479 Düsseldorf"
ORT_GOETHE = "Goethe-Museum"
ADRESSE_GOETHE = "Jacobistraße 2, 40211 Düsseldorf"
KATEGORIE_STANDARD = "kultur"

MAX_SEITEN = 15          # höchstens so viele Kalenderseiten je Lauf
PAUSE_S = 2.0            # Projektregel: mindestens 2 Sekunden zwischen Anfragen

_FAMILIE = re.compile(r"kinder|familie|nachwuchs|baby|eltern|kita", re.I)
_DATUM = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
_UHRZEIT = re.compile(r"\b(\d{1,2})[:.](\d{2})\b")


def _uhrzeit_aus(text: str) -> Optional[str]:
    """Beginn aus „18:00–20:00 Uhr“ oder „18:00–20:00, stille Lesezeit ab 18:30 Uhr“ (erste Uhrzeit)."""
    m = _UHRZEIT.search(text or "")
    if not m:
        return None
    stunde, minute = int(m.group(1)), int(m.group(2))
    return f"{stunde:02d}:{minute:02d}" if stunde <= 23 and minute <= 59 else None


def _kategorie(titel: str, typ: str) -> str:
    """family bei Kinder-/Familienangeboten, sonst kultur."""
    return "family" if _FAMILIE.search(f"{typ} {titel}") else KATEGORIE_STANDARD


def _ort(raum: str) -> tuple[str, str]:
    """Ort und Adresse: Theatermuseum, außer der Termin findet im Goethe-Museum statt."""
    if "goethe" in (raum or "").lower():
        return ORT_GOETHE, ADRESSE_GOETHE
    return ORT_STANDARD, ADRESSE_STANDARD


def _termin_aus_kachel(kachel) -> Optional[dict]:
    """Ein Event-Dict aus einem div.event-item (ohne Zeitfenster-Prüfung) oder None."""
    datum_el = kachel.find("h4")
    m = _DATUM.search(datum_el.get_text(" ", strip=True)) if datum_el else None
    if not m:
        return None
    try:
        datum = date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return None

    zeit_el = datum_el.find_next("p")
    uhrzeit = _uhrzeit_aus(zeit_el.get_text(" ", strip=True)) if zeit_el else None

    raum_el = kachel.find("p", class_="address")
    typ_el = kachel.find("p", class_="eventtype")
    raum = raum_el.get_text(" ", strip=True) if raum_el else ""
    typ = typ_el.get_text(" ", strip=True) if typ_el else ""

    link = kachel.find("a", class_="mb-2", href=True) or kachel.find("a", href=re.compile(r"/kalender/"))
    if not link:
        return None
    titel_el = link.find(["h4", "h3", "h2"])
    titel = (titel_el.get_text(" ", strip=True) if titel_el else "") or (link.get("title") or "").strip()
    titel = re.sub(r"\s+", " ", titel).strip()
    if not titel:
        return None
    quelle_url = urljoin(BASE_URL + "/", link["href"].strip())

    bild_url = None
    img = kachel.find("img")
    if img:
        src = img.get("src") or img.get("data-src")
        if src:
            src = urljoin(BASE_URL + "/", src.strip())
            bild_url = src if "theater-museum.de" in src else None

    if re.search(r"\babgesagt\b|\bentfällt\b", f"{titel} {typ}", re.I):
        return None

    ort, adresse = _ort(raum)
    return {
        "titel": titel,
        "datum": datum,
        "uhrzeit": uhrzeit,
        "ort": ort,
        "adresse": adresse,
        "kategorie": _kategorie(titel, typ),
        "beschreibung": None,
        "preis": None,
        "quelle_name": QUELLE_NAME,
        "quelle_url": quelle_url,
        "bild_url": bild_url,
        "bild_generiert": False,
        "status": "neu",
    }


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Alle Termine einer Kalenderseite im Zeitfenster heute … enddatum (rein, testbar)."""
    soup = BeautifulSoup(html or "", "html.parser")
    events = []
    gesehen: set[tuple] = set()
    for kachel in soup.select("div.event-item"):
        event = _termin_aus_kachel(kachel)
        if not event:
            continue
        if not (heute <= date.fromisoformat(event["datum"]) <= enddatum):
            continue
        schluessel = (event["titel"], event["datum"], event["uhrzeit"])
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        events.append(event)
    return events


def _letztes_datum(html: str) -> Optional[date]:
    """Spätestes Datum einer Kalenderseite (für den Abbruch, sobald das Fenster überschritten ist)."""
    daten = []
    for kachel in BeautifulSoup(html or "", "html.parser").select("div.event-item"):
        event = _termin_aus_kachel(kachel)
        if event:
            daten.append(date.fromisoformat(event["datum"]))
    return max(daten) if daten else None


def _seitenzahl(html: str) -> int:
    """Höchste Seitennummer aus den Blätter-Links (kalender?page=N), mindestens 1."""
    nummern = [int(n) for n in re.findall(r"kalender\?page=(\d+)", html or "")]
    return max(nummern + [1])


def scrape() -> list[dict]:
    """
    Scrapt den Programmkalender des Theatermuseums Düsseldorf (theater-museum.de/kalender, alle Seiten bis zum
    Ende des Vorschau-Fensters, höchstens MAX_SEITEN). Wirft nie; bei Fehlern leere Liste.
    """
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    events: list[dict] = []
    try:
        html = seite_abrufen(LISTE_URL, logger, wartezeit=PAUSE_S)
        if html is None:
            logger.error("%s: Kalenderseite nicht erreichbar", QUELLE_NAME)
            return []
        seiten = [html]
        letzte = min(_seitenzahl(html), MAX_SEITEN)
        seite = 2
        while seite <= letzte:
            spaetestes = _letztes_datum(seiten[-1])
            if spaetestes and spaetestes > enddatum:
                break   # Fenster überschritten, weitere Seiten unnötig
            weitere = seite_abrufen(f"{LISTE_URL}?page={seite}", logger, wartezeit=PAUSE_S)
            if weitere is None:
                break
            seiten.append(weitere)
            letzte = min(max(letzte, _seitenzahl(weitere)), MAX_SEITEN)
            seite += 1

        gesehen: set[tuple] = set()
        for s in seiten:
            for event in _termine_aus_html(s, heute, enddatum):
                schluessel = (event["titel"], event["datum"], event["uhrzeit"])
                if schluessel not in gesehen:
                    gesehen.add(schluessel)
                    events.append(event)
        logger.info("%s: %d Kalenderseite(n) gelesen", QUELLE_NAME, len(seiten))
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
