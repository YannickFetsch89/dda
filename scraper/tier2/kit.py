"""
kit.py – DiesDasDüsseldorf
Scraper für KIT – Kunst im Tunnel (Mannesmannufer): Führungen, Workshops, Eröffnungen, Familientage.

Quelle: https://www.kunst-im-tunnel.de/programm/kalender/ – die Seite ist eine Vue-App auf WordPress; das
ausgelieferte HTML enthält nur Titel ohne Datum. Die Termine kommen deshalb aus der WordPress-REST-API
(/wp-json/wp/v2/posts, kein „The Events Calendar“): Jeder Kalendereintrag ist ein Beitrag mit dem ACF-Feld „date“
(Unix-Zeitstempel, als Ortszeit gespeichert: 1795802400 = 27.11.2026 18:00) und optional „date_end“.
Der Beitragstext beginnt mit Wochentag, Datum, Uhrzeit und Eintritt („Freitag, 27. November 2026 / 18 Uhr /
Eintritt frei“).

robots.txt (geprüft 24.11.2026): gesperrt nur /wp/wp-admin/ – Kalender und /wp-json/ erlaubt.

Regeln:
- „closed“-Einträge (Schließtage) und Termine außerhalb des KIT („in der Kunsthalle“ im Textanfang, außer „findet
  im KIT statt“) entfallen; durchgestrichener Text (<s>, <del>) zählt nicht.
- Datum: aus dem ACF-Feld; nennt der Text „Wochentag, T. Monat JJJJ“ mit passendem Wochentag ein anderes Datum,
  gilt der Text (24.11.2026: ACF 12.12., Text „Samstag, 19. Dezember 2026“ – Reihe jeweils am 3. Samstag).
- Uhrzeit: aus dem ACF-Feld (00:00 → aus dem Text, sonst None).
- Preis: „Eintritt frei“/„kostenlos“/„kostenfrei“ → „kostenlos“, Betrag („12 Euro“) → „12 €“, „im Eintritt
  inbegriffen“ → „im Eintritt inbegriffen“.
- Kategorie: kultur; Familientage und Kinderangebote family.

Erstellt: 2026-11-24
"""
import html as html_lib
import json
import logging
import re
from datetime import date, datetime, timezone
from typing import Optional
from urllib.parse import urljoin

from config import vorschau_ende
from scraper.utils.datum import MONAT_MAP
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://www.kunst-im-tunnel.de"
KALENDER_URL = "https://www.kunst-im-tunnel.de/programm/kalender/"
API_URL = "https://www.kunst-im-tunnel.de/wp-json/wp/v2/posts"
QUELLE_NAME = "KIT – Kunst im Tunnel"
ORT_STANDARD = "KIT - Kunst im Tunnel"
ADRESSE_STANDARD = "Mannesmannufer 1, 40213 Düsseldorf"
KATEGORIE_STANDARD = "kultur"

PRO_SEITE = 100
MAX_SEITEN = 15
PAUSE_S = 2.0   # Projektregel: mindestens 2 Sekunden zwischen Anfragen

WOCHENTAGE = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]
_TEXT_DATUM = re.compile(r"\b(Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag),\s*(\d{1,2})\.\s*"
                         r"([A-Za-zÄÖÜäöü]+)\s+(\d{4})", re.I)
_TEXT_UHRZEIT = re.compile(r"\b(\d{1,2})(?:[.:](\d{2}))?\s*(?:[–-]\s*\d{1,2}(?:[.:]\d{2})?\s*)?Uhr\b", re.I)
_GESCHLOSSEN = re.compile(r"^\s*(closed|geschlossen)\b", re.I)
_AUSWAERTS = re.compile(r"\bin der Kunsthalle\b", re.I)
_IM_KIT = re.compile(r"findet (?:wieder |doch )?im KIT statt", re.I)
_DURCHGESTRICHEN = re.compile(r"<(s|del|strike)\b[^>]*>.*?</\1>", re.I | re.S)
_ABGESAGT = re.compile(r"\babgesagt\b|\bentfällt\b|\bfällt aus\b", re.I)
_FAMILIE = re.compile(r"familie|kinder", re.I)
_KOSTENLOS = re.compile(r"eintritt frei|kostenlos|kostenfrei|teilnahme frei", re.I)
_BETRAG = re.compile(r"(\d+(?:,\d{2})?)\s*(?:Euro|EUR|€)", re.I)
_INBEGRIFFEN = re.compile(r"im Eintritt inbegriffen", re.I)


def _klartext(html: str) -> str:
    """HTML → einfacher Text (Absätze und Zeilenumbrüche als Leerzeichen)."""
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


def _acf_zeit(wert) -> tuple[Optional[str], Optional[str]]:
    """ACF-Zeitstempel (Ortszeit als UTC gespeichert) → (Datum, Uhrzeit); Uhrzeit None bei 00:00."""
    try:
        zeitpunkt = datetime.fromtimestamp(int(wert), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None, None
    uhrzeit = zeitpunkt.strftime("%H:%M")
    return zeitpunkt.date().isoformat(), (None if uhrzeit == "00:00" else uhrzeit)


def _datum_aus_text(text: str) -> Optional[str]:
    """„Samstag, 19. Dezember 2026“ am Textanfang → „2026-12-19“, nur wenn der Wochentag zum Datum passt."""
    m = _TEXT_DATUM.search((text or "")[:200])
    if not m:
        return None
    monat = MONAT_MAP.get(m.group(3).lower())
    if not monat:
        return None
    try:
        tag = date(int(m.group(4)), monat, int(m.group(2)))
    except ValueError:
        return None
    return tag.isoformat() if WOCHENTAGE[tag.weekday()] == m.group(1).lower() else None


def _uhrzeit_aus_text(text: str) -> Optional[str]:
    """„18 Uhr“, „15–16 Uhr“, „12.15–14.15 Uhr“ im Textanfang → Beginn."""
    m = _TEXT_UHRZEIT.search((text or "")[:200])
    if not m or int(m.group(1)) > 23:
        return None
    return f"{int(m.group(1)):02d}:{m.group(2) or '00'}"


def _preis(text: str) -> Optional[str]:
    anfang = (text or "")[:300]
    if _KOSTENLOS.search(anfang):
        return "kostenlos"
    m = _BETRAG.search(anfang)
    if m:
        return f"{m.group(1)} €"
    if _INBEGRIFFEN.search(anfang):
        return "im Eintritt inbegriffen"
    return None


def _termin_aus_beitrag(beitrag: dict) -> Optional[dict]:
    """Ein Event-Dict aus einem REST-Beitrag (ohne Zeitfenster-Prüfung) oder None."""
    titel = _klartext((beitrag.get("title") or {}).get("rendered", ""))
    inhalt_html = (beitrag.get("content") or {}).get("rendered", "")
    # Durchgestrichenes gilt nicht mehr („<s>in der Kunsthalle</s> ACHTUNG ORTSWECHSEL: … im KIT“)
    text = _klartext(_DURCHGESTRICHEN.sub(" ", inhalt_html))
    if not titel or _GESCHLOSSEN.search(titel) or _ABGESAGT.search(f"{titel} {text[:300]}"):
        return None
    if _AUSWAERTS.search(text[:400]) and not _IM_KIT.search(text[:400]):
        logger.info("KIT: „%s“ findet nicht im KIT statt – übersprungen", titel)
        return None

    acf = beitrag.get("acf") or {}
    datum, uhrzeit = _acf_zeit(acf.get("date"))
    text_datum = _datum_aus_text(text)
    if text_datum and text_datum != datum:
        logger.info("KIT: „%s“ – Datum im Feld %s, im Text %s; Text gilt", titel, datum, text_datum)
        datum = text_datum
    if not datum:
        return None
    if not uhrzeit:
        uhrzeit = _uhrzeit_aus_text(text)

    link = (beitrag.get("link") or "").strip()
    quelle_url = urljoin(BASE_URL, link) if link else KALENDER_URL

    bild_url = None
    m = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", inhalt_html or "")
    if m:
        src = urljoin(BASE_URL, html_lib.unescape(m.group(1)))
        bild_url = src if src.startswith(BASE_URL) else None

    return {
        "titel": titel,
        "datum": datum,
        "uhrzeit": uhrzeit,
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": "family" if _FAMILIE.search(titel) else KATEGORIE_STANDARD,
        "beschreibung": None,
        "preis": _preis(text),
        "quelle_name": QUELLE_NAME,
        "quelle_url": quelle_url,
        "bild_url": bild_url,
        "bild_generiert": False,
        "status": "neu",
    }


def _termine_aus_json(daten, heute: date, enddatum: date) -> list[dict]:
    """Alle Termine einer REST-Antwort (Liste von Beiträgen) im Fenster heute … enddatum (rein, testbar)."""
    if isinstance(daten, str):
        daten = json.loads(daten)
    events, gesehen = [], set()
    for beitrag in daten if isinstance(daten, list) else []:
        if not isinstance(beitrag, dict):
            continue
        event = _termin_aus_beitrag(beitrag)
        if not event or not (heute <= date.fromisoformat(event["datum"]) <= enddatum):
            continue
        schluessel = (event["titel"], event["datum"], event["uhrzeit"])
        if schluessel not in gesehen:
            gesehen.add(schluessel)
            events.append(event)
    events.sort(key=lambda e: (e["datum"], e["uhrzeit"] or ""))
    return events


def _seiten_url(seite: int) -> str:
    return (f"{API_URL}?per_page={PRO_SEITE}&page={seite}&orderby=date&order=desc"
            "&_fields=id,link,title,acf,content")


def scrape() -> list[dict]:
    """
    Scrapt den KIT-Kalender über die WordPress-REST-API (Beiträge, neueste zuerst; weitere Seiten nur, solange
    eine volle Seite noch kommende Termine enthält). Wirft nie; bei Fehlern leere Liste.
    """
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    events: list[dict] = []
    try:
        gesehen: set[tuple] = set()
        for seite in range(1, MAX_SEITEN + 1):
            text = seite_abrufen(_seiten_url(seite), logger, wartezeit=PAUSE_S)
            if text is None:
                if seite == 1:
                    logger.error("%s: REST-API nicht erreichbar", QUELLE_NAME)
                    return []
                break
            daten = json.loads(text)
            if not isinstance(daten, list):
                logger.error("%s: unerwartete Antwort der REST-API", QUELLE_NAME)
                break
            neu = _termine_aus_json(daten, heute, enddatum)
            for event in neu:
                schluessel = (event["titel"], event["datum"], event["uhrzeit"])
                if schluessel not in gesehen:
                    gesehen.add(schluessel)
                    events.append(event)
            # weitere Seite nur, wenn diese voll war und noch kommende Termine enthielt
            kommende = [b for b in daten if isinstance(b, dict) and (_acf_zeit((b.get("acf") or {}).get("date"))[0]
                                                                      or "") >= heute.isoformat()]
            if len(daten) < PRO_SEITE or not kommende:
                break
        events.sort(key=lambda e: (e["datum"], e["uhrzeit"] or ""))
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []

    if not events:
        logger.warning("%s: 0 Termine bei erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
    logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
