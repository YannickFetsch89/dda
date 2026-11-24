"""
schloss_benrath.py – DiesDasDüsseldorf
Scraper für die Stiftung Schloss und Park Benrath: Veranstaltungen, Führungen, Konzerte, Familienangebote.

Quelle: https://www.schloss-benrath.de/veranstaltungs-liste (TYPO3). Die Liste enthält alle Termine der nächsten
Monate auf einer Seite (Stand 24.11.2026: 407 Einträge bis Juli 2027), je Termin mit Datum, Uhrzeit, Titel, Ort im
Schlossensemble, Kategorien und Link auf /veranstaltungs-detail/v/<id>. Detailseiten werden nur gelesen, wenn Datum
oder Uhrzeit in der Liste fehlen (höchstens MAX_DETAILS je Lauf).

robots.txt (geprüft 24.11.2026): „User-agent: * / Disallow: /typo3/“ – Liste und Detailseiten erlaubt.

Aufbau je Termin (li.event-teaser):
  <a href="/veranstaltungs-detail/v/6184"> <img data-src="/fileadmin/_processed_/…jpg">
  <div class="event-teaser__dateAndTime"><span>Do., 26. November 2026 | 19:00 Uhr</span></div>
  <div class="event-teaser__title"><h3>LESUNG | Bärbel van Alen: Schneiden. Färben. Sterben</h3></div>
  <div class="event-teaser__location">Schlosscafé</div> <span class="event-teaser__category">Kostenfreie Angebote</span>
Weggelassen: „Einlass 14:00 - 15:30 Uhr“ (Zeitfenster des Schlosstickets, keine Veranstaltung).
Titel: Großgeschriebene Wörter werden normal geschrieben, „TYP | Rest“ wird „Typ: Rest“
(„FAMILIENFÜHRUNG | Super-Tiere“ → „Familienführung: Super-Tiere“, „WANDELKONZERT“ → „Wandelkonzert“;
enthält der Rest schon einen Doppelpunkt, wird mit „ – “ verbunden).

Ort: immer „Schloss Benrath“ (Schlosspark, Orangerie, Museen und Schlosscafé gehören zum Ensemble).
Kategorie: musik bei Konzert/Singen im Titel oder Kategorie „Musikjahr“; family bei Familien-/Kinder-/Ferien-Titeln
oder Kategorie „Kinder & Familien“ ohne „Führung“/„Unsere Highlights“; sonst kultur (Führungen, Vorträge, Lesungen).
Preis: Kategorie „Kostenfreie Angebote“ → „kostenlos“, sonst None.

Erstellt: 2026-11-24
"""
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.datum import MONAT_MAP
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://www.schloss-benrath.de"
LISTE_URL = "https://www.schloss-benrath.de/veranstaltungs-liste"
QUELLE_NAME = "Schloss Benrath"
ORT_STANDARD = "Schloss Benrath"
ADRESSE_STANDARD = "Benrather Schloßallee 100-108, 40597 Düsseldorf"
KATEGORIE_STANDARD = "kultur"

MAX_DETAILS = 15   # höchstens so viele Detailseiten je Lauf (nur bei fehlendem Datum/fehlender Uhrzeit)
PAUSE_S = 2.0      # Projektregel: mindestens 2 Sekunden zwischen Anfragen

_DATUM = re.compile(r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)\s+(\d{4})")
_UHRZEIT = re.compile(r"\b(\d{1,2}):(\d{2})\s*Uhr", re.I)
_EINLASS = re.compile(r"^\s*Einlass\b", re.I)
_ABGESAGT = re.compile(r"\babgesagt\b|\bentfällt\b|\bfällt aus\b", re.I)
_MUSIK = re.compile(r"konzert|singen|liederabend|\bchor\b", re.I)
_FAMILIE = re.compile(r"familie|kinder|ferien|taschenlampe", re.I)


def _datum_aus(text: str) -> Optional[str]:
    """„Do., 26. November 2026“ → „2026-11-26“."""
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


def _uhrzeit_aus(text: str) -> Optional[str]:
    m = _UHRZEIT.search(text or "")
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        return None
    return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"


def _wort(w: str) -> str:
    """Ein komplett großgeschriebenes Wort normal schreiben („FÜHRUNG“ → „Führung“), Rest unverändert."""
    buchstaben = [c for c in w if c.isalpha()]
    if len(buchstaben) >= 2 and all(c.isupper() for c in buchstaben):
        return w[0] + w[1:].lower() if w[0].isalpha() else w.capitalize()
    return w


def titel_bereinigen(roh: str) -> str:
    """„LESUNG | Bärbel van Alen“ → „Lesung: Bärbel van Alen“, „DIE LEUCHTENDEN GÄRTEN“ → „Die Leuchtenden Gärten“."""
    titel = re.sub(r"\s+", " ", roh or "").strip()
    teile = [t.strip() for t in titel.split("|") if t.strip()]
    if len(teile) > 1:
        # „LESUNG | Autorin: Buch“ → „Lesung – Autorin: Buch“ (kein doppelter Doppelpunkt)
        trenner = " – " if ":" in " ".join(teile[1:]) else ": "
        titel = teile[0] + trenner + " ".join(teile[1:])
    elif teile:
        titel = teile[0]
    return " ".join(_wort(w) for w in titel.split(" "))


def _kategorie(titel: str, kategorien: set[str]) -> str:
    if _MUSIK.search(titel) or "Musikjahr" in kategorien:
        return "musik"
    if _FAMILIE.search(titel):
        return "family"
    if "Kinder & Familien" in kategorien and not ({"Führung", "Unsere Highlights"} & kategorien):
        return "family"
    return KATEGORIE_STANDARD


def _termin_aus_teaser(teaser) -> Optional[dict]:
    """Ein Event-Dict aus einem li.event-teaser (Datum/Uhrzeit ggf. None, ohne Zeitfenster-Prüfung) oder None."""
    titel_el = teaser.select_one(".event-teaser__title")
    roh = titel_el.get_text(" ", strip=True) if titel_el else ""
    if not roh or _EINLASS.search(roh) or _ABGESAGT.search(roh):
        return None
    link = teaser.find("a", href=True)
    quelle_url = urljoin(BASE_URL, link["href"].strip()) if link else LISTE_URL
    zeit_el = teaser.select_one(".event-teaser__dateAndTime")
    zeit_text = zeit_el.get_text(" ", strip=True) if zeit_el else ""
    kategorien = {k.get_text(" ", strip=True) for k in teaser.select(".event-teaser__category")}

    bild_url = None
    img = teaser.find("img")
    if img:
        src = img.get("data-src") or img.get("src")
        if src and not src.startswith("data:"):
            src = urljoin(BASE_URL, src.strip())
            bild_url = src if src.startswith(BASE_URL) else None

    titel = titel_bereinigen(roh)
    return {
        "titel": titel,
        "datum": _datum_aus(zeit_text),
        "uhrzeit": _uhrzeit_aus(zeit_text),
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": _kategorie(roh, kategorien),
        "beschreibung": None,
        "preis": "kostenlos" if "Kostenfreie Angebote" in kategorien else None,
        "quelle_name": QUELLE_NAME,
        "quelle_url": quelle_url,
        "bild_url": bild_url,
        "bild_generiert": False,
        "status": "neu",
    }


def _rohtermine(html: str) -> list[dict]:
    """Alle Termine der Liste, Datum/Uhrzeit können fehlen (rein, testbar)."""
    soup = BeautifulSoup(html or "", "html.parser")
    return [e for e in (_termin_aus_teaser(t) for t in soup.select("li.event-teaser")) if e]


def _im_fenster(events: list[dict], heute: date, enddatum: date) -> list[dict]:
    """Nur Termine mit Datum im Fenster, doppelte (Titel, Tag, Uhrzeit) einmal."""
    ergebnis, gesehen = [], set()
    for e in events:
        if not e["datum"] or not (heute <= date.fromisoformat(e["datum"]) <= enddatum):
            continue
        schluessel = (e["titel"], e["datum"], e["uhrzeit"])
        if schluessel not in gesehen:
            gesehen.add(schluessel)
            ergebnis.append(e)
    return ergebnis


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Termine der Liste im Zeitfenster (ohne Detailseiten)."""
    return _im_fenster(_rohtermine(html), heute, enddatum)


def zeit_aus_detail(html: str) -> tuple[Optional[str], Optional[str]]:
    """Datum und Uhrzeit aus einer Detailseite (Kopfzeile „So., 29. November 2026 | 15:00 Uhr“)."""
    soup = BeautifulSoup(html or "", "html.parser")
    bereich = soup.find("main") or soup
    text = bereich.get_text(" | ", strip=True)[:2000]
    return _datum_aus(text), _uhrzeit_aus(text)


def scrape() -> list[dict]:
    """
    Scrapt die Veranstaltungsliste von Schloss Benrath (eine Seite, bei Bedarf bis zu MAX_DETAILS Detailseiten).
    Wirft nie; bei Fehlern leere Liste.
    """
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum)
    try:
        html = seite_abrufen(LISTE_URL, logger, wartezeit=PAUSE_S)
        if html is None:
            logger.error("%s: Veranstaltungsliste nicht erreichbar", QUELLE_NAME)
            return []
        roh = _rohtermine(html)

        # Detailseiten nur bei fehlendem Datum oder fehlender Uhrzeit, höchstens MAX_DETAILS
        details = 0
        for e in roh:
            if e["datum"] and e["uhrzeit"]:
                continue
            if e["datum"] and not (heute <= date.fromisoformat(e["datum"]) <= enddatum):
                continue
            if details >= MAX_DETAILS or e["quelle_url"] == LISTE_URL:
                continue
            details += 1
            detail = seite_abrufen(e["quelle_url"], logger, wartezeit=PAUSE_S)
            if detail:
                datum, uhrzeit = zeit_aus_detail(detail)
                e["datum"] = e["datum"] or datum
                e["uhrzeit"] = e["uhrzeit"] or uhrzeit
        if details:
            logger.info("%s: %d Detailseite(n) für fehlende Zeiten gelesen", QUELLE_NAME, details)

        events = _im_fenster(roh, heute, enddatum)
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
