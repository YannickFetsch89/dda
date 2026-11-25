"""
ratinger_hof.py – DiesDasDüsseldorf
Scraper für den Ratinger Hof (Ratinger Str. 10, Altstadt).

Die Website https://www.ratingerhof-duesseldorf.de/ ist eine Vue-Seite ohne eigene Termine: Sie verweist mit
„concert team nrw – Bespielt den Ratinger Hof!“ auf das Programm des Betreibers unter
https://www.concertteam.de/ratinger-hof. Diese Seite lädt ihre Liste per JavaScript (App.fetchEvents) aus
/events.json/limit:<n>/page:<n>/query:location=Ratinger+Hof+Düsseldorf – genau diesen JSON-Endpunkt lesen wir
(ein Abruf, kein Playwright). Die Liste enthält Titel, Datum, Ort, Bild, Detail-URL und die Merker abgesagt/
ausverkauft, aber keine Uhrzeit. Uhrzeit (Beginn, sonst Einlass), Ticketpreis und den „Ticket bestellen“-Button
(meist eventim-light.com) lesen wir aus der Detailseite jedes Termins im Zeitfenster (2 s Pause je Abruf).
Das JSON-LD der Detailseite taugt für die Uhrzeit nicht (startDate immer 00:00).

robots.txt geprüft am 2026-11-25:
- www.ratingerhof-duesseldorf.de: „User-agent: * / Disallow:“ – nichts gesperrt.
- www.concertteam.de: keine robots.txt (HTTP 404) – nichts gesperrt.

Kategorie: Konzerte → musik; Partys/DJ-Abende (Party, DJ, Battle, Disco, Silvester, Ball, Karaoke im Titel oder
in der Detail-URL) → nightlife.

Erstellt: 2026-11-25 (Quellen-Ausbau, Schritt V2, Welle B)
"""
import logging
import re
import time
from datetime import date
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.datum import uhrzeit_parsen
from scraper.utils.http_client import STANDARD_HEADERS, _backoff, seite_abrufen
from scraper.utils.ticket_link import ticket_link_haus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Ratinger Hof"
ORT_STANDARD = "Ratinger Hof Düsseldorf"
ADRESSE_STANDARD = "Ratinger Str. 10, 40213 Düsseldorf"
PROGRAMM_URL = "https://www.concertteam.de/ratinger-hof"
LISTE_URL = "https://www.concertteam.de/events.json/limit:100/page:1/query:location=Ratinger+Hof+D%C3%BCsseldorf"
ORT_IN_LISTE = "ratinger hof"
WARTEZEIT_S = 2.0
MAX_DETAILS = 60  # Sicherheitsgrenze für Detailabrufe je Lauf

_NIGHTLIFE = re.compile(r"party|\bdj\b|dj-|battle|disco|silvester|\bball\b|karaoke", re.I)


def _kategorie(titel: str, url: str) -> str:
    """nightlife für Partys/DJ-Abende, sonst musik (Konzerte)."""
    slug = url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ")
    return "nightlife" if _NIGHTLIFE.search(f"{titel} {slug}") else "musik"


def _datum(text: str) -> Optional[str]:
    """„27.11.2026“ → „2026-11-27“."""
    treffer = re.fullmatch(r"\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*", text or "")
    if not treffer:
        return None
    try:
        return date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1))).isoformat()
    except ValueError:
        return None


def _termine_aus_liste(daten: dict, heute: date, enddatum: date) -> list[dict]:
    """Wandelt die events.json-Antwort in Event-Dicts um (ohne Uhrzeit, Preis, Ticket – die kommen aus der Detailseite)."""
    events = []
    gesehen: set[tuple] = set()
    for eintrag in (daten or {}).get("items") or []:
        try:
            if not isinstance(eintrag, dict) or eintrag.get("isCancelled"):
                continue
            if ORT_IN_LISTE not in (eintrag.get("location") or "").lower():
                continue
            titel = (eintrag.get("title") or "").strip()
            datum = _datum(eintrag.get("date") or "")
            url = (eintrag.get("url") or "").strip()
            if not titel or not datum or not url.startswith("https://www.concertteam.de/"):
                continue
            if not heute <= date.fromisoformat(datum) <= enddatum:
                continue
            schluessel = (titel.lower(), datum)
            if schluessel in gesehen:
                continue
            gesehen.add(schluessel)
            bild = ((eintrag.get("cover") or {}).get("src") or "").strip()
            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": None,
                "ort": ORT_STANDARD,
                "adresse": ADRESSE_STANDARD,
                "kategorie": _kategorie(titel, url),
                "beschreibung": None,
                "preis": None,
                "quelle_name": QUELLE_NAME,
                "quelle_url": url,
                "ticket_url": None,
                "bild_url": bild if bild.startswith("https://www.concertteam.de/") else None,
                "bild_generiert": False,
                "status": "neu",
            })
        except Exception as fehler:
            logger.error("%s: Fehler beim Lesen eines Listeneintrags: %s", QUELLE_NAME, fehler)
    return events


def _feld(soup: BeautifulSoup, name: str) -> Optional[str]:
    """Wert neben einer Beschriftung im Infoblock („Beginn“ → „20:00 Uhr“)."""
    for div in soup.find_all("div"):
        if div.get_text(strip=True) == name and not div.find("div"):
            wert = div.find_next_sibling("div")
            if wert:
                text = wert.get_text(" ", strip=True)
                return text or None
    return None


def _details_aus_html(html: str, basis_url: str) -> dict:
    """Uhrzeit (Beginn, sonst Einlass), Preis und Ticket-Link aus der Detailseite."""
    soup = BeautifulSoup(html, "html.parser")
    uhrzeit = uhrzeit_parsen(_feld(soup, "Beginn") or "") or uhrzeit_parsen(_feld(soup, "Einlass") or "")
    preis = _feld(soup, "Ticketpreis")
    ticket = None
    for a in soup.find_all("a", href=True):
        if "ticket" in a.get_text(" ", strip=True).lower() and "bestell" in a.get_text(" ", strip=True).lower():
            ticket = ticket_link_haus(a["href"], basis_url)
            if ticket:
                # Google-Suchmerker („?srsltid=…“, steht teils im Eventim-Link) weglassen
                ticket = re.sub(r"[?&]srsltid=[^&#]*$", "", ticket)
                break
    return {"uhrzeit": uhrzeit, "preis": preis if preis and len(preis) <= 60 else None, "ticket_url": ticket}


def _liste_holen() -> Optional[dict]:
    """Holt die JSON-Liste wie der Browser (Pause, Backoff bei 429)."""
    kopf = dict(STANDARD_HEADERS, Accept="application/json, */*;q=0.8", Referer=PROGRAMM_URL)
    time.sleep(WARTEZEIT_S)
    with httpx.Client(headers=kopf, timeout=30, follow_redirects=True) as client:
        antwort = client.get(LISTE_URL)
        for versuch in range(3):
            if antwort.status_code != 429:
                break
            pause = _backoff(antwort.headers.get("Retry-After"), versuch)
            logger.warning("HTTP 429 bei %s – warte %.0f s (Versuch %d von 3)", LISTE_URL, pause, versuch + 1)
            time.sleep(pause)
            antwort = client.get(LISTE_URL)
        antwort.raise_for_status()
        return antwort.json()


def scrape() -> list[dict]:
    """Scrapt das Programm des Ratinger Hofs. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        try:
            daten = _liste_holen()
        except Exception as fehler:
            logger.error("%s: Liste nicht abrufbar: %s", QUELLE_NAME, fehler)
            return []
        events = _termine_aus_liste(daten, heute, enddatum)
        if not events:
            logger.warning("%s: 0 Termine auf erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
            return []
        for event in events[:MAX_DETAILS]:
            html = seite_abrufen(event["quelle_url"], logger, wartezeit=WARTEZEIT_S)
            if not html:
                continue   # Termin bleibt ohne Uhrzeit/Preis erhalten
            try:
                event.update({k: v for k, v in _details_aus_html(html, event["quelle_url"]).items() if v})
            except Exception as fehler:
                logger.error("%s: Detailseite %s nicht lesbar: %s", QUELLE_NAME, event["quelle_url"], fehler)
        # Doppelte (gleicher Titel, Tag, Uhrzeit) nur einmal
        gesehen: set[tuple] = set()
        ergebnis = []
        for e in events:
            schluessel = (e["titel"].lower(), e["datum"], e["uhrzeit"])
            if schluessel not in gesehen:
                gesehen.add(schluessel)
                ergebnis.append(e)
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []
    logger.info("Scraper %s fertig: %d Termine", QUELLE_NAME, len(ergebnis))
    return ergebnis


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    for e in scrape()[:5]:
        print(e)
