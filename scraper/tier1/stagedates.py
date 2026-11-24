"""
stagedates.py – DiesDasDüsseldorf
Ticketplattform Stagedates: Events in Düsseldorf, Neuss und Ratingen aus der Event-Sitemap und dem JSON-LD der
Eventseiten (Plan docs/plan-quellen-ausbau-2026-11-23.md, 5.1, Schritt V1).

Prüfung 24.11.2026: robots.txt erlaubt alles und nennt selbst https://stagedates.com/sitemap-events.xml. Die
Nutzungsbedingungen (https://stagedates.com/terms-of-use → AGB Ticketkäufer der Ticket AG) regeln den Ticketkauf und
verbieten das Lesen öffentlicher Eventseiten nicht.

Ablauf:
  1. Sitemap lesen (≈ 830 Events bundesweit). Das Datum steht im Slug („…-20261225-NIFB8“) – vergangene und zu ferne
     Events (hinter vorschau_ende) werden gar nicht erst geladen.
  2. Nur Seiten laden, die noch nicht im Zwischenspeicher stehen (data/stagedates/seiten.json, im Workflow per
     actions/cache erhalten), höchstens MAX_NEU_JE_LAUF je Lauf, die nächsten Termine zuerst, 2 s Pause.
  3. Aus dem JSON-LD (Baustein scraper/utils/jsonld_events.py) nur Termine in Düsseldorf, Neuss und Ratingen.

Rang 2 (Ticketverkauf, pipeline/quellen_rang.py): Liefert das Haus dasselbe Event, wird das Haus Hauptquelle.
"""
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen
from scraper.utils.jsonld_events import events_aus_html

logger = logging.getLogger(__name__)

QUELLE_NAME = "Stagedates"
SITEMAP_URL = "https://stagedates.com/sitemap-events.xml"
CACHE_DATEI = Path(__file__).resolve().parents[2] / "data" / "stagedates" / "seiten.json"
CACHE_VERSION = 1
MAX_NEU_JE_LAUF = 150
# Seite ohne lesbaren Termin (leere Hülle, Bot-Seite …): so oft versuchen, dann erst wieder, wenn sie aus der Sitemap
# fällt (Cursor-Prüfung V1)
MAX_FEHLVERSUCHE = 2
_SLUG_DATUM = re.compile(r"-(\d{8})-[A-Za-z0-9]+/?$")


def _cache_laden() -> dict:
    try:
        daten = json.loads(CACHE_DATEI.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return daten.get("seiten") or {} if daten.get("version") == CACHE_VERSION else {}


def _cache_speichern(cache: dict) -> None:
    try:
        CACHE_DATEI.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_DATEI.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": CACHE_VERSION, "seiten": cache}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(CACHE_DATEI)
    except OSError as fehler:
        logger.warning("%s: Zwischenspeicher nicht schreibbar: %s", QUELLE_NAME, fehler)


def urls_im_fenster(sitemap: str, heute: date, enddatum: date) -> dict[str, date]:
    """Event-URLs der Sitemap, deren Datum im Slug zwischen heute und enddatum liegt."""
    ergebnis = {}
    for url in re.findall(r"<loc>([^<]+)</loc>", sitemap or ""):
        treffer = _SLUG_DATUM.search(url.strip())
        if not treffer:
            continue
        try:
            tag = datetime.strptime(treffer.group(1), "%Y%m%d").date()
        except ValueError:
            continue
        if heute <= tag <= enddatum:
            ergebnis[url.strip()] = tag
    return ergebnis


def ist_im_gebiet(termin: dict) -> bool:
    """PLZ entscheidet, sonst die Stadt als ganzes Wort – „Neusser Straße“ in Köln zählt nicht (Cursor-Prüfung 24.11.)."""
    from pipeline.gebiet import adresse_im_gebiet
    return adresse_im_gebiet(termin.get("adresse") or "", termin.get("ort") or "")


def event_aus_termin(t: dict) -> dict:
    return {
        "titel": t["titel"],
        "datum": t["start"],
        "uhrzeit": t.get("uhrzeit"),
        "ort": t.get("ort") or "Düsseldorf",
        "adresse": t.get("adresse"),
        "kategorie": "nightlife",  # überwiegend Partys und Clubnächte; die KI-Kategorisierung prüft nach
        "beschreibung": None,
        "preis": t.get("preis"),
        "quelle_name": QUELLE_NAME,
        "quelle_url": t.get("url"),
        "bild_url": t.get("bild_url"),
        "bild_generiert": False,
        "status": "neu",
    }


def scrape() -> list[dict]:
    """Stagedates-Events in Düsseldorf, Neuss und Ratingen bis zum Zeitraum der Quelle."""
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum.isoformat())
    cache = _cache_laden()
    try:
        sitemap = seite_abrufen(SITEMAP_URL, logger)
        if not sitemap or "</urlset>" not in sitemap:
            logger.error("%s: Sitemap fehlt oder ist unvollständig – nutze nur den Zwischenspeicher", QUELLE_NAME)
            kandidaten = {}
        else:
            kandidaten = urls_im_fenster(sitemap, heute, enddatum)
        neu = 0
        for url, _tag in sorted(kandidaten.items(), key=lambda kv: kv[1]):
            alt = cache.get(url) or {}
            if alt.get("termine") or alt.get("fehlversuche", 0) >= MAX_FEHLVERSUCHE:
                continue
            if neu >= MAX_NEU_JE_LAUF:
                break
            html = seite_abrufen(url, logger)
            if html is None:
                continue
            termine = events_aus_html(html, url)
            # Nur eine Seite mit Termin gilt als gelesen; eine leere Antwort wird beim nächsten Lauf erneut versucht
            cache[url] = {"termine": termine} if termine else {"termine": [], "fehlversuche": alt.get("fehlversuche", 0) + 1}
            neu += 1
            if neu % 20 == 0:
                _cache_speichern(cache)
        offen = sum(1 for u in kandidaten if not (cache.get(u) or {}).get("termine")
                    and (cache.get(u) or {}).get("fehlversuche", 0) < MAX_FEHLVERSUCHE)
        logger.info("%s: %d Events im Zeitraum, %d neu geladen, %d warten auf den nächsten Lauf",
                    QUELLE_NAME, len(kandidaten), neu, offen)
        if kandidaten:  # Vergangenes und nicht mehr Gelistetes vergessen
            cache = {u: e for u, e in cache.items() if u in kandidaten}
        _cache_speichern(cache)
    except Exception as fehler:
        logger.error("%s: Abruf abgebrochen (%s) – nutze den Zwischenspeicher", QUELLE_NAME, fehler)

    events, gesehen = [], set()
    for eintrag in cache.values():
        for t in eintrag.get("termine") or []:
            if t.get("abgesagt") or not ist_im_gebiet(t):
                continue
            try:
                tag = date.fromisoformat(t["start"])
            except (KeyError, ValueError):
                continue
            schluessel = (t["titel"].lower(), t["start"], t.get("uhrzeit"))
            if heute <= tag <= enddatum and schluessel not in gesehen:
                gesehen.add(schluessel)
                events.append(event_aus_termin(t))
    if not events:
        logger.warning("%s: keine Events in Düsseldorf, Neuss und Ratingen – Seitenstruktur geändert?", QUELLE_NAME)
    logger.info("Scraper %s fertig: %d Events in Düsseldorf, Neuss und Ratingen", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ergebnis = scrape()
    print(json.dumps(ergebnis[:3], ensure_ascii=False, indent=2), len(ergebnis))
