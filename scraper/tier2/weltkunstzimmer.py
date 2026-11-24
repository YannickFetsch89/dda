"""
weltkunstzimmer.py – DiesDasDüsseldorf
Scraper für das Weltkunstzimmer (Kunstzentrum der Hans Peter Zimmer Stiftung, Ronsdorfer Str. 77a).
URL: https://weltkunstzimmer.de/programm/
Adresse laut https://weltkunstzimmer.de/kontakt/ (abgerufen 2026-11-24): Ronsdorfer Str. 77a, 40233 Düsseldorf.

robots.txt geprüft am 2026-11-24: Yoast-Standard „User-agent: * / Disallow:“ → alles erlaubt. Kein Crawl-delay.

Methode: WordPress mit Theme „Lay“. Die Programmseite enthält alle Beiträge (auch das Archiv seit 2021) als
<a class="thumb" data-title="Titel, Wochentag TT. Monat JJJJ[, HH Uhr]" data-catid="[…]">. Datum, Zeitraum und
ggf. Uhrzeit stehen also im data-title. Fehlt die Uhrzeit, wird für Termine im Zeitfenster die Detailseite gelesen
(„Beginn: 20 Uhr“, „Eintritt: …“; höchstens MAX_DETAILSEITEN je Lauf). Mehrtägige Termine („29. – 31. Januar 2027“)
bekommen datum_bis; „25. – 26. April und 1. – 2. Mai“ wird zu zwei Terminen.
Kategorie: Sparte „Konzerte“/„Musikzimmer“ → musik, außer der Beitrag ist zugleich Ausstellung, Performance oder
Workshop; sonst kultur.

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1, Welle A)
"""
import html as html_lib
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

logger = logging.getLogger(__name__)

BASIS_URL = "https://weltkunstzimmer.de"
PROGRAMM_URL = "https://weltkunstzimmer.de/programm/"
QUELLE_NAME = "Weltkunstzimmer"
ORT = "Weltkunstzimmer"
ADRESSE = "Ronsdorfer Str. 77a, 40233 Düsseldorf"
MAX_DETAILSEITEN = 12   # höchstens ~15 Seiten je Lauf (Auftrag)
MUSIK_SPARTEN = {"konzerte", "musikzimmer"}
KULTUR_SPARTEN = {"ausstellungen", "performances", "workshops"}   # haben Vorrang vor „Konzerte“
MUSIK_IDS_RUECKFALL = {4, 25}   # falls die Filterliste fehlt (Stand 24.11.2026)
KULTUR_IDS_RUECKFALL = {3, 5, 27}

_MONATE = "|".join(sorted((m for m in MONAT_MAP if MONAT_MAP[m] and m not in ("may",)), key=len, reverse=True))
_WOCHENTAG = r"(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag|Mo|Di|Mi|Do|Fr|Sa|So)\.?,?"
# Beginn des Datumsteils: „[Wochentag] 29. [– 31.] Januar“ oder „30. und 31. Januar“
_DATUM_START = re.compile(
    rf"(?:{_WOCHENTAG}\s+)?\d{{1,2}}\.\s*(?:(?:[–-]|und|&)\s*(?:{_WOCHENTAG}\s+)?\d{{1,2}}\.\s*)?(?:{_MONATE})\b",
    re.I,
)
_TOKEN = re.compile(rf"(\d{{1,2}})\.\s*(?:({_MONATE})\b)?(?:\s+(\d{{4}}))?", re.I)
_TRENNER = re.compile(r"\s+(?:und|&)\s+", re.I)
_UHRZEIT = re.compile(r"(?i)(?:ab\s+)?(\d{1,2})(?:[:.](\d{2}))?\s*(?:[–-]\s*\d{1,2}(?:[:.]\d{2})?\s*)?Uhr")
_ABGESAGT = re.compile(r"(?i)\b(abgesagt|entfällt|fällt aus|verschoben)\b")


def _uhrzeit(text: str) -> Optional[str]:
    treffer = _UHRZEIT.search(text or "")
    if not treffer or not 0 <= int(treffer.group(1)) <= 23:
        return None
    return f"{int(treffer.group(1)):02d}:{treffer.group(2) or '00'}"


def _zerlegen(data_title: str) -> Optional[tuple[str, list[tuple[str, Optional[str]]], Optional[str]]]:
    """
    „Titel, Freitag 05. März 2027, 20 Uhr“ → ("Titel", [("2027-03-05", None)], "20:00").
    Liefert je Teil-Zeitraum (start, ende|None); None, wenn kein Datum erkennbar ist.
    """
    text = " ".join(html_lib.unescape(data_title or "").split())
    beginn = _DATUM_START.search(text)
    if not beginn:
        return None
    titel = re.sub(r"[\s,–-]+$", "", text[:beginn.start()]).strip()
    datumsteil = text[beginn.start():]
    jahre = list(re.finditer(r"\d{4}", datumsteil))
    if not titel or not jahre:
        return None
    zeitteil = datumsteil[jahre[-1].end():]
    datumsteil = datumsteil[:jahre[-1].end()]

    # Tag-Token mit Position; fehlende Monate/Jahre von rechts nach links auffüllen („29. – 31. Januar 2027“)
    token = [[t.start(), int(t.group(1)), (t.group(2) or "").lower() or None, t.group(3)]
             for t in _TOKEN.finditer(datumsteil)]
    monat, jahr = None, None
    for t in reversed(token):
        monat = t[2] or monat
        jahr = t[3] or jahr
        t[2], t[3] = monat, jahr
    grenzen = [m.start() for m in _TRENNER.finditer(datumsteil)] + [len(datumsteil)]
    zeitraeume: list[tuple[str, Optional[str]]] = []
    for nr, grenze in enumerate(grenzen):
        unten = grenzen[nr - 1] if nr else -1
        teil = [t for t in token if unten < t[0] < grenze and t[2] and t[3]]
        if not teil:
            continue
        try:
            daten = [date(int(t[3]), MONAT_MAP[t[2]], t[1]) for t in (teil[0], teil[-1])]
        except (ValueError, KeyError):
            continue
        start, ende = daten
        zeitraeume.append((start.isoformat(), ende.isoformat() if ende > start else None))
    return (titel, zeitraeume, _uhrzeit(zeitteil)) if zeitraeume else None


def _sparten(soup: BeautifulSoup) -> dict[int, str]:
    """Filter-IDs → Slug („4“ → „konzerte“) aus der Filterleiste der Seite."""
    ergebnis = {}
    for el in soup.select(".lay-thumbnailgrid-filter-anchor[data-id]"):
        try:
            ergebnis[int(el["data-id"])] = str(el.get("data-slug") or "").lower()
        except ValueError:
            pass
    return ergebnis


def _bild(a) -> Optional[str]:
    img = a.find("img")
    if not img:
        return None
    kandidaten = []
    for teil in str(img.get("data-srcset") or "").split(","):
        stuecke = teil.strip().split()
        if len(stuecke) == 2 and stuecke[1].endswith("w") and stuecke[1][:-1].isdigit():
            kandidaten.append((int(stuecke[1][:-1]), stuecke[0]))
    # Größte Variante bis 1600 px Breite (sonst die größte, sonst data-src)
    passende = [k for k in kandidaten if k[0] <= 1600] or kandidaten
    url = max(passende)[1] if passende else img.get("data-src")
    if not url:
        return None
    url = urljoin(BASIS_URL, url)
    return url if urlparse(url).netloc.endswith("weltkunstzimmer.de") else None


def _liste_aus_html(html: str) -> list[dict]:
    """Alle Beiträge der Programmseite: titel, zeitraeume, uhrzeit, url, kategorie, bild (ohne Zeitfilter)."""
    soup = BeautifulSoup(html or "", "html.parser")
    sparten = _sparten(soup)
    eintraege, gesehen = [], set()
    for a in soup.select("a.thumb[data-title][href]"):
        url = urljoin(BASIS_URL, a["href"])
        if url in gesehen:
            continue
        gesehen.add(url)
        zerlegt = _zerlegen(a["data-title"])
        if not zerlegt:
            continue
        try:
            ids = {int(x) for x in json.loads(a.get("data-catid") or "[]")}
        except (json.JSONDecodeError, TypeError, ValueError):
            ids = set()
        if sparten:
            slugs = {sparten.get(i) for i in ids}
            musik = bool(slugs & MUSIK_SPARTEN) and not slugs & KULTUR_SPARTEN
        else:
            musik = bool(ids & MUSIK_IDS_RUECKFALL) and not ids & KULTUR_IDS_RUECKFALL
        titel, zeitraeume, uhrzeit = zerlegt
        eintraege.append({"titel": titel, "zeitraeume": zeitraeume, "uhrzeit": uhrzeit, "url": url,
                          "kategorie": "musik" if musik else "kultur", "bild": _bild(a)})
    return eintraege


def _details_aus_html(html: str) -> dict:
    """Detailseite: {"uhrzeit": Beginn (sonst Einlass), "preis": Eintritt}."""
    soup = BeautifulSoup(html or "", "html.parser")
    for t in soup(["script", "style", "nav", "header", "footer"]):
        t.decompose()
    zeilen = [z.strip() for z in soup.get_text("\n").split("\n") if z.strip()]
    uhrzeit = preis = None
    for schluessel in ("beginn", "start", "einlass"):
        for zeile in zeilen:
            if zeile.lower().startswith(schluessel) and (uhrzeit := _uhrzeit(zeile)):
                break
        if uhrzeit:
            break
    for zeile in zeilen:
        if re.match(r"(?i)^(eintritt|tickets?|preis)\s*:", zeile):
            wert = zeile.split(":", 1)[1].strip()
            if re.search(r"(?i)frei|kostenlos|free", wert) and not re.search(r"\d", wert):
                preis = "kostenlos"
            elif wert:
                preis = wert[:120]
            break
    return {"uhrzeit": uhrzeit, "preis": preis}


def _termine_aus_html(html: str, heute: date, enddatum: date, details: Optional[dict] = None) -> list[dict]:
    """Programmseite (+ optional Details je URL) → Events mit Beginn zwischen heute und enddatum, ohne Doppelte."""
    details = details or {}
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for eintrag in _liste_aus_html(html):
        if _ABGESAGT.search(eintrag["titel"]):
            continue
        d = details.get(eintrag["url"]) or {}
        for start, ende in eintrag["zeitraeume"]:
            if not (heute <= date.fromisoformat(start) <= enddatum):
                continue
            uhrzeit = eintrag["uhrzeit"] or d.get("uhrzeit")
            schluessel = (eintrag["titel"].lower(), start, uhrzeit)
            if schluessel in gesehen:
                continue
            gesehen.add(schluessel)
            event = {
                "titel": eintrag["titel"],
                "datum": start,
                "uhrzeit": uhrzeit,
                "ort": ORT,
                "adresse": ADRESSE,
                "kategorie": eintrag["kategorie"],
                "beschreibung": None,
                "preis": d.get("preis"),
                "quelle_name": QUELLE_NAME,
                "quelle_url": eintrag["url"],
                "bild_url": eintrag["bild"],
                "bild_generiert": False,
                "status": "neu",
            }
            if ende:
                event["datum_bis"] = ende
            events.append(event)
    return sorted(events, key=lambda e: (e["datum"], e["uhrzeit"] or ""))


def scrape() -> list[dict]:
    """Scrapt das Programm des Weltkunstzimmers. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    try:
        html = seite_abrufen(PROGRAMM_URL, logger, wartezeit=2.0)
        if html is None:
            logger.error("%s: Programmseite nicht erreichbar", QUELLE_NAME)
            return []
        offen = [e for e in _liste_aus_html(html)
                 if any(heute <= date.fromisoformat(s) <= enddatum for s, _ in e["zeitraeume"])]
        details: dict[str, dict] = {}
        for eintrag in offen[:MAX_DETAILSEITEN]:
            try:
                seite = seite_abrufen(eintrag["url"], logger, wartezeit=2.0)
                if seite:
                    details[eintrag["url"]] = _details_aus_html(seite)
            except Exception as fehler:
                logger.warning("%s: Detailseite %s nicht lesbar: %s", QUELLE_NAME, eintrag["url"], fehler)
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
