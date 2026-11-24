"""
ampere.py – DiesDasDüsseldorf
Scraper für den Club Ampere (Ronsdorfer Str. 134, Gelände Kulturzentrum).
URL: https://ampere-club.de/programm/

robots.txt geprüft am 2026-11-24: Yoast-Standard „User-agent: * / Disallow:“ → alles erlaubt. Kein Crawl-delay.

Methode: WordPress (Theme Impreza, Beitragstyp us_portfolio). Die Programmseite listet alle Termine als
<article class="w-grid-item"> mit Titel (.event_title), Datum (.event_date „Fr. 27.11.2026“), Sparte (term-konzert,
term-dj, …) und Bild – aber ohne Uhrzeit. Für Termine im Zeitfenster wird deshalb die Detailseite gelesen
(höchstens MAX_DETAILSEITEN je Lauf): Beginn steht dort in .event_start_time, Einlass in .event_doors_open, Preise in
.event_price_*; das JSON-LD der Detailseite dient nur als Rückfall (seine Uhrzeit wich im Test vom Beginn ab).

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1, Welle A)
"""
import json
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen
from scraper.utils.jsonld_events import events_aus_html

logger = logging.getLogger(__name__)

BASIS_URL = "https://ampere-club.de"
PROGRAMM_URL = "https://ampere-club.de/programm/"
QUELLE_NAME = "Ampere"
ORT = "Ampere"
ADRESSE = "Ronsdorfer Str. 134, 40233 Düsseldorf"
MAX_DETAILSEITEN = 14   # höchstens ~15 Seiten je Lauf (Auftrag): 1 Programmseite + 14 Detailseiten

# Sparte (CSS-Klasse term-…) → Kategorie; Konzerte musik, DJ/Party nightlife, Bühne/Film/Lesung kultur
SPARTEN = {
    "konzert": "musik",
    "dj": "nightlife",
    "party": "nightlife",
    "lesung": "kultur",
    "comedy": "kultur",
    "film": "kultur",
    "live-podcast": "kultur",
}
_ABGESAGT = re.compile(r"(?i)\b(abgesagt|entfällt|fällt aus|cancelled|canceled)\b")
_DATUM = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
_ZEIT = re.compile(r"(\d{1,2})(?:[:.](\d{2}))?")


def _text(el) -> str:
    return " ".join(el.get_text(" ", strip=True).split()) if el else ""


def _liste_aus_html(html: str) -> list[dict]:
    """Einträge der Programmseite: titel, datum, sparte, url, bild (ohne Zeitfilter)."""
    soup = BeautifulSoup(html or "", "html.parser")
    eintraege = []
    for art in soup.select("article.w-grid-item"):
        titel = _text(art.select_one(".event_title"))
        datum_text = _text(art.select_one(".event_date"))
        treffer = _DATUM.search(datum_text)
        link = art.select_one("a.w-grid-item-anchor[href]") or art.select_one("a[href]")
        if not titel or not treffer or not link:
            continue
        try:
            datum = date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1))).isoformat()
        except ValueError:
            continue
        sparte = None
        term = art.select_one(".post_taxonomy [class*=term-]")
        for klasse in (term.get("class") or []) if term else []:
            if klasse.startswith("term-") and not klasse[5:].isdigit():
                sparte = klasse[5:]
        bild_el = art.select_one("img.wp-post-image")
        bild = bild_el.get("src") if bild_el else None
        eintraege.append({
            "titel": titel,
            "datum": datum,
            "sparte": sparte,
            "url": urljoin(BASIS_URL, link["href"]),
            "bild": urljoin(BASIS_URL, bild) if bild else None,
            "zusatz": _text(art.select_one(".event_subline_1")),
        })
    return eintraege


def _feldwert(soup: BeautifulSoup, klasse: str) -> Optional[str]:
    el = soup.select_one(f".{klasse} .w-post-elm-value")
    return _text(el) or None


def _uhrzeit(wert: Optional[str]) -> Optional[str]:
    treffer = _ZEIT.search(wert or "")
    if not treffer or not 0 <= int(treffer.group(1)) <= 23:
        return None
    return f"{int(treffer.group(1)):02d}:{treffer.group(2) or '00'}"


def _details_aus_html(html: str, seiten_url: str = "") -> dict:
    """Detailseite: {"uhrzeit", "preis", "abgesagt"} – Beginn vor JSON-LD vor Einlass."""
    soup = BeautifulSoup(html or "", "html.parser")
    jsonld = events_aus_html(html or "", seiten_url)
    uhrzeit = (
        _uhrzeit(_feldwert(soup, "event_start_time"))
        or (jsonld[0]["uhrzeit"] if jsonld else None)
        or _uhrzeit(_feldwert(soup, "event_doors_open"))
    )
    preise = []
    for el in soup.select("[class*=event_price]"):
        wert = _text(el.select_one(".w-post-elm-value"))
        if not wert:
            continue
        if re.search(r"(?i)frei|kostenlos", wert):
            preise = ["kostenlos"]
            break
        bezeichnung = _text(el.select_one(".w-post-elm-before")).rstrip(":").strip()
        betrag = wert if "€" in wert or not re.search(r"\d", wert) else f"{wert} €"
        preise.append(f"{bezeichnung} {betrag}".strip())
    preis = " / ".join(dict.fromkeys(preise)) or (jsonld[0]["preis"] if jsonld else None)
    return {"uhrzeit": uhrzeit, "preis": preis, "abgesagt": bool(jsonld and jsonld[0]["abgesagt"])}


def _event(eintrag: dict, details: Optional[dict]) -> dict:
    details = details or {}
    bild = eintrag.get("bild")
    return {
        "titel": eintrag["titel"],
        "datum": eintrag["datum"],
        "uhrzeit": details.get("uhrzeit"),
        "ort": ORT,
        "adresse": ADRESSE,
        "kategorie": SPARTEN.get(eintrag.get("sparte") or "", "nightlife"),
        "beschreibung": None,
        "preis": details.get("preis"),
        "quelle_name": QUELLE_NAME,
        "quelle_url": eintrag["url"],
        "bild_url": bild if bild and urlparse(bild).netloc.endswith("ampere-club.de") else None,
        "bild_generiert": False,
        "status": "neu",
    }


def _termine_aus_html(html: str, heute: date, enddatum: date, details: Optional[dict] = None) -> list[dict]:
    """Programmseite (+ optional bereits gelesene Details je URL) → Events im Zeitfenster, ohne Doppelte."""
    details = details or {}
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for eintrag in _liste_aus_html(html):
        if not (heute <= date.fromisoformat(eintrag["datum"]) <= enddatum):
            continue
        if _ABGESAGT.search(f"{eintrag['titel']} {eintrag['zusatz']}"):
            continue
        d = details.get(eintrag["url"])
        if d and d.get("abgesagt"):
            continue
        event = _event(eintrag, d)
        schluessel = (event["titel"].lower(), event["datum"], event["uhrzeit"])
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        events.append(event)
    return sorted(events, key=lambda e: (e["datum"], e["uhrzeit"] or ""))


def scrape() -> list[dict]:
    """Scrapt das Programm des Ampere (Liste + Detailseiten für die Uhrzeit). Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    try:
        html = seite_abrufen(PROGRAMM_URL, logger, wartezeit=2.0)
        if html is None:
            logger.error("%s: Programmseite nicht erreichbar", QUELLE_NAME)
            return []
        im_fenster = [e for e in _liste_aus_html(html)
                      if heute <= date.fromisoformat(e["datum"]) <= enddatum]
        details: dict[str, dict] = {}
        for eintrag in im_fenster[:MAX_DETAILSEITEN]:
            try:
                seite = seite_abrufen(eintrag["url"], logger, wartezeit=2.0)
                if seite:
                    details[eintrag["url"]] = _details_aus_html(seite, eintrag["url"])
            except Exception as fehler:
                logger.warning("%s: Detailseite %s nicht lesbar: %s", QUELLE_NAME, eintrag["url"], fehler)
        if len(im_fenster) > MAX_DETAILSEITEN:
            logger.info("%s: %d Termine ohne Detailseite (Grenze %d) – Uhrzeit bleibt leer",
                        QUELLE_NAME, len(im_fenster) - MAX_DETAILSEITEN, MAX_DETAILSEITEN)
        events = _termine_aus_html(html, heute, enddatum, details)
        if not events:
            logger.warning("%s: 0 Termine gefunden – Seitenstruktur geändert?", QUELLE_NAME)
        logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
        return events
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
