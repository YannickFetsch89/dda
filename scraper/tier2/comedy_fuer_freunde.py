"""
comedy_fuer_freunde.py – DiesDasDüsseldorf
Scraper für Comedy für Freunde – Stand-up-Reihe „Profi-Testbühne“ in Düsseldorf (Lupin Gin Bar, Ackerstraße 109).
Programmseite: https://comedy-fuer-freunde.com/duesseldorf/

WordPress mit „Modern Events Calendar“ (MEC). Die Seite zeichnet die sichtbaren Termine als JSON-LD `Event` aus
(Baustein jsonld_events). Meist ist nur der nächste Termin sichtbar (wöchentlich montags 20 Uhr).
Achtung: MEC schreibt die Startzeit im JSON-LD eine Stunde zu spät („2026-11-30T21:00:00+01:00“, sichtbar und in der
Beschreibung „Showtime 20:00“). Deshalb nehmen wir die Uhrzeit aus der sichtbaren Liste (span.event-time-inline) und
nur ersatzweise aus dem JSON-LD.
Die Reihe gibt es in mehreren Städten – übernommen werden nur Termine, deren Ortsangabe Düsseldorf ist (oder leer).
Tickets laufen über Weezevent: Der „Tickets“-Button (a.mec-booking-button) steht als normaler Link im HTML und wird
über ticket_link_haus übernommen; das Weezevent-Widget selbst wird nie abgerufen (Weezevent sperrt den Pfad per robots).

robots.txt geprüft am 2026-11-25: gesperrt nur „/?s=“, „/page/*/?s=“, „/search/“ (und AdsBot ganz) – /duesseldorf/
ist erlaubt. Kein Crawl-delay; ein Abruf je Lauf.

Kategorie: kultur (Comedy).

Erstellt: 2026-11-25 (Quellen-Ausbau, Schritt V2, Welle C)
"""
import logging
import re
from datetime import date
from typing import Optional

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.datum import datum_parsen, uhrzeit_parsen
from scraper.utils.http_client import seite_abrufen
from scraper.utils.jsonld_events import events_aus_html
from scraper.utils.ticket_link import ticket_link_haus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Comedy für Freunde"
PROGRAMM_URL = "https://comedy-fuer-freunde.com/duesseldorf/"
ORT_STANDARD = "Comedy für Freunde Club Düsseldorf"
ADRESSE_STANDARD = "Ackerstraße 109, 40233 Düsseldorf"
KATEGORIE_STANDARD = "kultur"
WARTEZEIT_S = 2.0
_EIGENE_DOMAIN = "comedy-fuer-freunde.com"


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el is not None else ""


def _in_duesseldorf(ort: Optional[str], adresse: Optional[str] = None) -> bool:
    """Leere Ortsangabe gilt als Düsseldorf (Seite /duesseldorf/); sonst muss Düsseldorf oder die Bar genannt sein."""
    text = f"{ort or ''} {adresse or ''}".strip().lower()
    if not text:
        return True
    return any(x in text for x in ("düsseldorf", "duesseldorf", "dusseldorf", "ackerstr", "lupin"))


def _listeneintraege(soup: BeautifulSoup) -> list[dict]:
    """Sichtbare MEC-Einträge: Datum (aus occurrence= im Link oder Tag/Monat), Uhrzeit, Ort, Ticket-Link, Titel."""
    eintraege = []
    for art in soup.select("article.mec-event-article"):
        titel_el = art.select_one(".mec-event-title a") or art.select_one(".mec-event-title")
        titel = _text(titel_el)
        knopf = art.select_one("a.mec-booking-button[href]") or art.select_one(".mec-event-title a[href]")
        href = knopf["href"] if knopf else ""
        treffer = re.search(r"occurrence=(\d{4}-\d{2}-\d{2})", href)
        datum = treffer.group(1) if treffer else datum_parsen(
            f"{_text(art.select_one('.event-d'))}. {_text(art.select_one('.event-f'))}")
        uhrzeit = uhrzeit_parsen(_text(art.select_one(".event-time-inline")))
        bild = art.select_one("img[src]")
        eintraege.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": _text(art.select_one(".mec-event-loc-place")),
            "preis": _text(art.select_one(".mec-price-details")),
            "ticket_url": ticket_link_haus(href, PROGRAMM_URL) if href else None,
            "bild_url": bild["src"] if bild else None,
        })
    return eintraege


def _preis(text: Optional[str]) -> Optional[str]:
    """„9,99€“ → „9,99 €“; 0 → „kostenlos“."""
    if not text:
        return None
    text = text.strip()
    if re.fullmatch(r"0+(?:[.,]0+)?\s*€?", text):
        return "kostenlos"
    return re.sub(r"\s*€", " €", text).strip() or None


def _eigenes_bild(url: Optional[str]) -> Optional[str]:
    return url if url and _EIGENE_DOMAIN in url and url.startswith("http") else None


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Liest die Termine der Programmseite (ohne Netz testbar)."""
    soup = BeautifulSoup(html or "", "html.parser")
    liste = _listeneintraege(soup)
    nach_datum: dict[str, list[dict]] = {}
    for e in liste:
        if e["datum"]:
            nach_datum.setdefault(e["datum"], []).append(e)

    roh = [t for t in events_aus_html(html or "", PROGRAMM_URL)]
    if not roh:
        # Ersatz: nur die sichtbare Liste (falls das JSON-LD fehlt)
        roh = [{"titel": e["titel"], "start": e["datum"], "uhrzeit": e["uhrzeit"], "ort": e["ort"], "adresse": None,
                "bild_url": e["bild_url"], "preis": e["preis"], "abgesagt": False} for e in liste if e["datum"]]

    events: list[dict] = []
    gesehen: set[tuple] = set()
    for t in roh:
        if t.get("abgesagt") or not t.get("start") or not t.get("titel"):
            continue
        if not _in_duesseldorf(t.get("ort"), t.get("adresse")):
            continue
        tag = date.fromisoformat(t["start"])
        if tag < heute or tag > enddatum:
            continue
        # passender Listeneintrag (gleicher Tag, möglichst gleicher Titel) liefert Uhrzeit und Ticket-Button
        kandidaten = nach_datum.get(t["start"], [])
        eintrag = next((e for e in kandidaten if e["titel"].lower() == t["titel"].lower()), None) or \
            (kandidaten[0] if kandidaten else None)
        if eintrag and eintrag["ort"] and not _in_duesseldorf(eintrag["ort"]):
            continue
        uhrzeit = (eintrag or {}).get("uhrzeit") or t.get("uhrzeit")
        schluessel = (t["titel"].lower(), t["start"], uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        events.append({
            "titel": t["titel"],
            "datum": t["start"],
            "uhrzeit": uhrzeit,
            "ort": ORT_STANDARD,
            "adresse": ADRESSE_STANDARD,
            "kategorie": KATEGORIE_STANDARD,
            "beschreibung": None,
            "preis": _preis(t.get("preis")) or _preis((eintrag or {}).get("preis")),
            "quelle_name": QUELLE_NAME,
            "quelle_url": PROGRAMM_URL,
            "ticket_url": (eintrag or {}).get("ticket_url"),
            "bild_url": _eigenes_bild(t.get("bild_url")) or _eigenes_bild((eintrag or {}).get("bild_url")),
            "bild_generiert": False,
            "status": "neu",
        })
    return events


def scrape() -> list[dict]:
    """Scrapt die Düsseldorfer Termine von Comedy für Freunde. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        html = seite_abrufen(PROGRAMM_URL, logger, wartezeit=WARTEZEIT_S)
        if html is None:
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
