"""
bilker_bunker.py – DiesDasDüsseldorf
Scraper für den Bilker Bunker und seine Musikbar Schleuse Zwei (Aachener Str. 39).
URL: https://bilkerbunker.de/schleuse-zwei (Programm-Liste, Drupal-View mit „Mehr laden“ = ?page=1, 2, …)

robots.txt geprüft am 2026-11-24: Drupal-Standard, gesperrt sind nur /admin/, /user/…, /search/, /core/ u. ä.
→ /schleuse-zwei und ?page=N erlaubt. Kein Crawl-delay.

Hinweis: Die Startseite zeigt (Stand 24.11.2026) kein Programm mehr. Die Termine stehen auf /schleuse-zwei als
.program__item mit <time datetime>, einer Meta-Zeile („/ Einlass 19 Uhr / Beginn 20 Uhr / VVK 10 € …“) und Titel.
Je Seite drei Termine; eine zweite Liste auf derselben Seite wiederholt Konzerte (Doppelte werden entfernt).
Die Seite /ausstellungen enthält nur Fließtext (Laufzeiten, Führungstermine im Text) und wird nicht gelesen.

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1, Welle A)
"""
import json
import logging
import re
from datetime import date
from typing import Optional

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASIS_URL = "https://bilkerbunker.de"
PROGRAMM_URL = "https://bilkerbunker.de/schleuse-zwei"
QUELLE_NAME = "Bilker Bunker"
ORT_BUNKER = "Bilker Bunker"
ORT_SCHLEUSE = "Schleuse Zwei"
ADRESSE = "Aachener Str. 39, 40223 Düsseldorf"
MAX_SEITEN = 12   # höchstens ~15 Seiten je Lauf (Auftrag); 3 Termine je Seite

_UEBERSPRINGEN = re.compile(r"(?i)geschlossene gesellschaft|private veranstaltung|abgesagt|entfällt|fällt aus")
_UHRZEIT = re.compile(r"(?i)(\d{1,2})(?:[:.](\d{2}))?\s*(?:uhr|h\b|$)")
_KULTUR = re.compile(r"(?i)ausstellung|lesung|artist talk|vernissage|finissage|führung|buchpräsentation|vortrag|"
                     r"screening|filmabend")
# „VVK“ in der Meta-Zeile steht bei Konzertabenden (Barabende mit DJ sind meist frei)
_MUSIK = re.compile(r"(?i)\blive\b|konzert|release|band\b|support\b|songwriter|\bvvk\b")
_NIGHTLIFE = re.compile(r"(?i)\bdj\b|dj-set|barabend|party|rave|club|listening")
_BUNKER_RAUM = re.compile(r"(?i)ausstellungsr(a|ä|ae)um|ausstellungsfläche|hauptraum|pop-up café|bunker terrasse")
_SCHLEUSE = re.compile(r"(?i)schleuse|\bS2\b|musikbar")


def _text(el) -> str:
    return " ".join(el.get_text(" ", strip=True).split()) if el else ""


def _uhrzeit(meta: str) -> Optional[str]:
    """Beginn aus der Meta-Zeile („Einlass 19 Uhr / Beginn 20 Uhr“), sonst Einlass; None ohne Angabe."""
    teile = [t.strip() for t in meta.split("/") if t.strip()]
    for schluessel in ("beginn", "start", "einlass"):
        for teil in teile:
            if schluessel in teil.lower():
                treffer = _UHRZEIT.search(teil[teil.lower().find(schluessel):])
                if treffer and 0 <= int(treffer.group(1)) <= 23:
                    return f"{int(treffer.group(1)):02d}:{treffer.group(2) or '00'}"
    return None


def _preis(meta: str) -> Optional[str]:
    """Preisangaben der Meta-Zeile („VVK 10 € (zzgl. Geb.) / AK 15 €“); „Eintritt frei“ → kostenlos."""
    if re.search(r"(?i)eintritt frei|freier eintritt|kostenlos|eintritt: frei", meta):
        return "kostenlos"
    teile = [t.strip() for t in meta.split("/") if "€" in t]
    return " / ".join(teile) or None


def _kategorie(titel: str, rest: str) -> str:
    """Titel zuerst, dann Meta-Zeile und Kurztext: Ausstellung/Lesung → kultur, Konzert → musik, DJ/Party → nightlife."""
    for text in (titel, rest):
        for muster, kategorie in ((_KULTUR, "kultur"), (_MUSIK, "musik"), (_NIGHTLIFE, "nightlife")):
            if muster.search(text):
                return kategorie
    return "nightlife"


def _ort(text: str) -> str:
    """Schleuse Zwei (Programm der Musikbar), außer der Text nennt nur Räume des Bunkers."""
    if _BUNKER_RAUM.search(text) and not _SCHLEUSE.search(text):
        return ORT_BUNKER
    return ORT_SCHLEUSE


def _termine_aus_html(html: str, heute: date, enddatum: date, seiten_url: str = PROGRAMM_URL) -> list[dict]:
    """Alle Programm-Einträge einer Seite als Events (heute bis enddatum)."""
    soup = BeautifulSoup(html or "", "html.parser")
    events = []
    for item in soup.select(".program__item"):
        zeit = item.find("time")
        titel = _text(item.select_one(".program__title"))
        meta = _text(item.select_one(".program__meta"))
        kurz = _text(item.select_one(".program__desc"))
        if not zeit or not titel:
            continue
        treffer = re.match(r"(\d{4}-\d{2}-\d{2})", str(zeit.get("datetime") or ""))
        if not treffer:
            continue
        datum = treffer.group(1)
        if not (heute <= date.fromisoformat(datum) <= enddatum):
            continue
        if _UEBERSPRINGEN.search(f"{titel} {meta}"):
            continue
        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": _uhrzeit(meta),
            "ort": _ort(f"{titel} {meta} {kurz}"),
            "adresse": ADRESSE,
            "kategorie": _kategorie(titel, f"{meta} {kurz}"),
            "beschreibung": None,
            "preis": _preis(meta),
            "quelle_name": QUELLE_NAME,
            "quelle_url": seiten_url,   # Einträge haben keine eigene Detailseite (Akkordeon)
            "bild_url": None,
            "bild_generiert": False,
            "status": "neu",
        })
    return events


def _naechste_seite(html: str) -> Optional[str]:
    """Link „Mehr laden“ (?page=N) oder None."""
    soup = BeautifulSoup(html or "", "html.parser")
    link = soup.select_one(".pager a[rel=next]")
    href = link.get("href") if link else None
    return f"{PROGRAMM_URL}{href}" if href and href.startswith("?") else None


def _listen_daten(html: str) -> list[date]:
    """Daten der seitenweise geladenen Programm-Liste (ohne den wiederholten Konzert-Block)."""
    soup = BeautifulSoup(html or "", "html.parser")
    daten = []
    for zeit in soup.select(".views-infinite-scroll-content-wrapper .program__item time"):
        treffer = re.match(r"(\d{4}-\d{2}-\d{2})", str(zeit.get("datetime") or ""))
        if treffer:
            daten.append(date.fromisoformat(treffer.group(1)))
    return daten


def _ohne_doppelte(events: list[dict]) -> list[dict]:
    gesehen, ergebnis = set(), []
    for e in events:
        schluessel = (e["titel"].lower(), e["datum"], e["uhrzeit"])
        if schluessel not in gesehen:
            gesehen.add(schluessel)
            ergebnis.append(e)
    return sorted(ergebnis, key=lambda e: (e["datum"], e["uhrzeit"] or ""))


def scrape() -> list[dict]:
    """Scrapt das Programm von Schleuse Zwei / Bilker Bunker. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    alle: list[dict] = []
    try:
        url: Optional[str] = PROGRAMM_URL
        erreichbar = False
        for _ in range(MAX_SEITEN):
            html = seite_abrufen(url, logger, wartezeit=2.0)
            if html is None:
                break
            erreichbar = True
            alle.extend(_termine_aus_html(html, heute, enddatum))
            daten = _listen_daten(html)
            # Liste leer oder schon hinter dem Zeitfenster → keine weitere Seite laden
            if not daten or min(daten) > enddatum:
                break
            url = _naechste_seite(html)
            if not url:
                break
        if not erreichbar:
            logger.error("%s: Programmseite nicht erreichbar", QUELLE_NAME)
            return []
        events = _ohne_doppelte(alle)
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
