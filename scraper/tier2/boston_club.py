"""
boston_club.py – DiesDasDüsseldorf
Scraper für den Boston-Club e.V. (Tanzsportverein, Vennhauser Allee 135, Düsseldorf-Eller).
Programmseite: https://www.boston-club.de/Veranstaltungen.html (statisches Nicepage-HTML)

Die Seite ist von Hand gepflegt und hat drei Blöcke:
- „Sportveranstaltung“: Links „14.11. Move&Learn-Seminar“ (Datum ohne Jahr, Details nur als Bild-Popup) → sport,
  Eintritt laut Seite („Aktueller Eintrittspreis: 16,- €“), keine Uhrzeit.
- „Unsere Tanzparty“: „Die nächste Tanz- Übungsparty findet am 21.11.2026 ab 19:30 Uhr statt.“ plus
  „Termine 2027 – 23.01., 20.02., …“. Für die Folgetermine übernehmen wir die Uhrzeit der nächsten Party
  (die Seite nennt sie nur einmal). Eintritt frei → „kostenlos“. Kategorie community (Mitmach-Tanzabend im
  Vereinsheim, keine Clubnacht).
- „Unser Weihnachtsball“: nennt im Text nur den Vorverkaufsstart, das Balldatum steht nur im Bild – wird nur
  übernommen, wenn ein Datum „am TT.MM.JJJJ“ im Text steht.
Nicht übernommen: Hinweise der Startseite (Saalsperren, IHK-Prüfungen, Fremdveranstaltungen wie Jungschützenball).

robots.txt geprüft am 2026-11-25: keine robots.txt (HTTP 404) – nichts gesperrt.

Erstellt: 2026-11-25 (Quellen-Ausbau, Schritt V2, Welle B)
"""
import logging
import re
from datetime import date, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

QUELLE_NAME = "Boston Club"
ORT_STANDARD = "Boston Club"
ADRESSE_STANDARD = "Vennhauser Allee 135, 40627 Düsseldorf"
BASE_URL = "https://www.boston-club.de/"
PROGRAMM_URL = "https://www.boston-club.de/Veranstaltungen.html"
PARTY_TITEL = "Tanz-Übungsparty"
WARTEZEIT_S = 2.0

_SPORT_LINK = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})?\s*(.{3,80})$")
_PARTY = re.compile(
    r"Übungsparty\s+findet\s+am\s+(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+ab\s+(\d{1,2})[:.](\d{2}))?", re.I)
_TERMINE_JAHR = re.compile(r"Termine\s+(20\d{2})\s*(.*)", re.I | re.S)
_TAG_MONAT = re.compile(r"(\d{1,2})\.(\d{1,2})\.")
_BALL_DATUM = re.compile(r"(?<!ab dem )\bam\s+(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+ab\s+(\d{1,2})[:.](\d{2}))?", re.I)


def _tag(jahr: int, monat: int, tag: int) -> Optional[date]:
    try:
        return date(jahr, monat, tag)
    except ValueError:
        return None


def _mit_jahr(tag: int, monat: int, heute: date) -> Optional[date]:
    """Datum ohne Jahr: dieses Jahr; liegt es mehr als 60 Tage zurück, ist das nächste Jahr gemeint."""
    d = _tag(heute.year, monat, tag)
    if d and d < heute - timedelta(days=60):
        d = _tag(heute.year + 1, monat, tag)
    return d


def _event(titel: str, tag: date, uhrzeit: Optional[str], kategorie: str, preis: Optional[str],
           bild_url: Optional[str]) -> dict:
    return {
        "titel": titel,
        "datum": tag.isoformat(),
        "uhrzeit": uhrzeit,
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": kategorie,
        "beschreibung": None,
        "preis": preis,
        "quelle_name": QUELLE_NAME,
        "quelle_url": PROGRAMM_URL,
        "ticket_url": None,
        "bild_url": bild_url,
        "bild_generiert": False,
        "status": "neu",
    }


def _block(el):
    """Nächster umgebender Inhaltsblock (Nicepage: div.u-container-layout bzw. section)."""
    for eltern in el.parents:
        klassen = eltern.get("class") or []
        if "u-container-layout" in klassen or eltern.name == "section":
            return eltern
    return el


def _bild_in(block, basis: str) -> Optional[str]:
    """Erstes Bild im Block bzw. im Nachbarblock der gleichen Zeile (eigene Website)."""
    zeile = block.find_parent(class_="u-layout-row") or block
    img = zeile.find("img", src=True)
    if not img or "logo" in img["src"].lower():
        return None
    src = img["src"]
    return src if src.startswith("http") else basis + src.lstrip("./")


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Liest alle Termine aus der Veranstaltungsseite (ohne Netz testbar)."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []
    seitentext = soup.get_text(" ", strip=True)

    # 1) Sportveranstaltungen (Popup-Links „TT.MM. Titel“)
    preis_sport = None
    treffer = re.search(r"Eintrittspreis:?\s*(\d+)(?:,-|,00)?\s*€", seitentext)
    if treffer:
        preis_sport = f"{treffer.group(1)} €"
    for a in soup.select('a[href^="#popup"]'):
        text = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
        m = _SPORT_LINK.match(text)
        if not m:
            continue
        tag = (_tag(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m.group(3)
               else _mit_jahr(int(m.group(1)), int(m.group(2)), heute))
        titel = m.group(4).strip(" -–")
        if tag and titel:
            events.append(_event(titel, tag, None, "sport", preis_sport, None))

    # 2) Tanz-Übungspartys
    for p in soup.find_all("p"):
        text = re.sub(r"\s+", " ", p.get_text(" ", strip=True))
        m = _PARTY.search(text)
        if not m:
            continue
        block = _block(p)
        blocktext = re.sub(r"\s+", " ", block.get_text(" ", strip=True))
        preis = "kostenlos" if re.search(r"Eintritt ist frei|freier Eintritt|Eintritt frei", blocktext, re.I) else None
        uhrzeit = f"{int(m.group(4)):02d}:{m.group(5)}" if m.group(4) else None
        bild = _bild_in(block, BASE_URL)
        erste = _tag(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        if erste:
            events.append(_event(PARTY_TITEL, erste, uhrzeit, "community", preis, bild))
        # Folgetermine „Termine 2027 … 23.01., 20.02., …“ im selben Block
        for absatz in block.find_all("p"):
            liste = _TERMINE_JAHR.search(re.sub(r"\s+", " ", absatz.get_text(" ", strip=True)))
            if not liste:
                continue
            jahr = int(liste.group(1))
            for t, mo in _TAG_MONAT.findall(liste.group(2)):
                tag = _tag(jahr, int(mo), int(t))
                if tag:
                    events.append(_event(PARTY_TITEL, tag, uhrzeit, "community", preis, bild))
        break

    # 3) Ball (nur mit Datum im Text)
    for el in soup.find_all("p"):
        kopf = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
        titel_m = re.match(r"(?:Unser\s+)?(\w*ball)\s+(20\d{2})$", kopf, re.I)
        if not titel_m:
            continue
        blocktext = re.sub(r"\s+", " ", _block(el).get_text(" ", strip=True))
        m = _BALL_DATUM.search(blocktext)
        if m:
            tag = _tag(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            uhrzeit = f"{int(m.group(4)):02d}:{m.group(5)}" if m.group(4) else None
            if tag:
                events.append(_event(titel_m.group(1), tag, uhrzeit, "community", None, None))

    # Fenster und Doppelte
    ergebnis, gesehen = [], set()
    for e in events:
        tag = date.fromisoformat(e["datum"])
        schluessel = (e["titel"].lower(), e["datum"], e["uhrzeit"])
        if heute <= tag <= enddatum and schluessel not in gesehen:
            gesehen.add(schluessel)
            ergebnis.append(e)
    return sorted(ergebnis, key=lambda e: (e["datum"], e["uhrzeit"] or ""))


def scrape() -> list[dict]:
    """Scrapt die Veranstaltungsseite des Boston-Clubs. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        html = seite_abrufen(PROGRAMM_URL, logger, wartezeit=WARTEZEIT_S)
        if not html:
            return []
        events = _termine_aus_html(html, heute, enddatum)
        if not events:
            logger.warning("%s: 0 Termine auf erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []
    logger.info("Scraper %s fertig: %d Termine", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    for e in scrape():
        print(e)
