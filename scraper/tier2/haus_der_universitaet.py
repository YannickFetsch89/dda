"""
haus_der_universitaet.py – DiesDasDüsseldorf
Scraper für das Haus der Universität (Heinrich-Heine-Universität, Bürgeruniversität am Schadowplatz):
Vorträge, Ringvorlesungen, Lesungen, Gesprächskonzerte.
Quelle: Veranstaltungskalender https://www.hdu.hhu.de/programm/veranstaltungskalender (TYPO3 „calendarize“,
10 Termine je Seite, weitere Seiten /event-page-2 …) und je Termin die Detailseite (Ort, Preis).
Die Seite /programm aus dem Auftrag ist nur ein Einleitungstext mit Link auf diesen Kalender.
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V2, Welle B)

robots.txt (geprüft am 25.11.2026): „User-agent: *“ mit **Crawl-delay: 10**; gesperrt sind u. a. /VORSCHAU/, /ARCHIV/,
/nc/, /home/, /redaktion/, ?id=, ?L=0, ?type=98 – /programm/veranstaltungskalender(/event-page-N) und
/programm/einzeltermin/… sind erlaubt. Wir warten 10 s zwischen allen Anfragen.

Besonderheiten:
- Die Liste nennt Titel, „TT.MM.JJJJ, HH:MM - HH:MM“ und die Vortragenden, aber keinen Ort. Laut Programmseite
  finden Veranstaltungen auch auf dem Unicampus und an anderen Orten statt – deshalb lesen wir je Termin die
  Detailseite („Ort: Haus der Universität“). Termine an anderen Orten werden ausgelassen (Ortstabelle kennt sie
  nicht); fehlt die Angabe, gilt das Haus der Universität.
- Preis: „alle sind, soweit nicht anders angegeben, kostenlos“ (Programmseite) → „kostenlos“, außer die
  Detailseite nennt einen Euro-Betrag. Ohne lesbare Detailseite bleibt preis None.
- Wegen Crawl-delay 10 dauert ein Lauf etwa (Seiten + Termine) × 10 s, bei 30 Terminen gut 5 Minuten.

Erstellt: 2026-11-25
"""
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.datum import datum_parsen
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ticket_link import ticket_link_aus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Haus der Universität"
BASIS_URL = "https://www.hdu.hhu.de"
KALENDER_URL = "https://www.hdu.hhu.de/programm/veranstaltungskalender"

ORT = "Haus der Universität"
ADRESSE = "Schadowpl. 14, 40212 Düsseldorf"

WARTEZEIT = 10.0   # Crawl-delay aus robots.txt
MAX_SEITEN = 6
MAX_DETAILS = 60

_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus|verschoben)\b", re.I)


def _kategorie(titel: str) -> str:
    """Konzerte → musik, Kinder → family, Patiententag/Workshop/Diskussion → community, sonst (Vortrag …) kultur."""
    t = titel.lower()
    if re.search(r"konzert|schumann@heine|musik für|liederabend|klavierabend", t):
        return "musik"
    if re.search(r"kinder|famili", t):
        return "family"
    if re.search(r"patiententag|workshop|mitmach|sprechstunde|infotag|informationstag|stammtisch", t):
        return "community"
    return "kultur"


def _uhrzeit(text: str) -> Optional[str]:
    """Beginn aus „25.11.2026, 18:30 - 20:00“."""
    m = re.search(r"\d{4}\s*,\s*(\d{1,2})[:.](\d{2})", text or "")
    if m and int(m.group(1)) < 24:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    return None


def _termine_aus_liste(html: str, heute: date, enddatum: date) -> list[dict]:
    """Eine Kalenderseite → Event-Dicts (Ort/Preis ergänzt später die Detailseite)."""
    soup = BeautifulSoup(html, "html.parser")
    ergebnis: list[dict] = []
    for el in soup.select("div.event"):
        try:
            link = el.select_one("h3 a[href]")
            datum_el = el.select_one("h4.date")
            if not link or not datum_el:
                continue
            titel = re.sub(r"\s+", " ", link.get_text(" ", strip=True)).strip()
            datum_text = re.sub(r"\s+", " ", datum_el.get_text(" ", strip=True))
            datum = datum_parsen(datum_text)
            if not titel or not datum:
                continue
            if _ABGESAGT.search(titel):
                logger.debug("HdU: abgesagt, ausgelassen: %s", titel)
                continue
            tag = date.fromisoformat(datum)
            if tag < heute or tag > enddatum:
                continue
            ergebnis.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": _uhrzeit(datum_text),
                "ort": ORT,
                "adresse": ADRESSE,
                "kategorie": _kategorie(titel),
                "beschreibung": None,
                "preis": None,
                "quelle_name": QUELLE_NAME,
                "quelle_url": urljoin(BASIS_URL, link["href"]),
                "bild_url": None,
                "bild_generiert": False,
                "status": "neu",
                "ticket_url": None,
            })
        except Exception as fehler:
            logger.warning("HdU: Eintrag übersprungen (%s)", fehler)
    return ergebnis


def _naechste_seite(html: str) -> Optional[str]:
    """URL der nächsten Kalenderseite (Link „nächste“), sonst None."""
    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one("li.next a[href]")
    return urljoin(BASIS_URL, link["href"]) if link else None


def _details_ergaenzen(event: dict, html: str) -> bool:
    """Ort, Preis, Ticket-Link und Bild aus der Detailseite. False, wenn der Termin an einem anderen Ort ist."""
    soup = BeautifulSoup(html, "html.parser")
    ort_el = soup.select_one(".location")
    ort_text = re.sub(r"^\s*Ort:\s*", "", ort_el.get_text(" ", strip=True)) if ort_el else ""
    if ort_text and not re.search(r"haus der universit|schadowpl", ort_text, re.I):
        logger.info("HdU: anderer Ort, ausgelassen: %s (%s)", event["titel"], ort_text)
        return False
    inhalt = soup.select_one("div.col-md-8") or soup.body
    if inhalt is None:
        return True
    text = inhalt.get_text(" ", strip=True)
    m = re.search(r"((?:Eintritt|Karten|Tickets|Kosten|Teilnahme)[^.€]{0,60}€[^.]{0,30})", text)
    event["preis"] = re.sub(r"\s+", " ", m.group(1)).strip()[:120] if m else "kostenlos"
    ticket = ticket_link_aus(inhalt, event["quelle_url"])
    if ticket and ticket != event["quelle_url"]:
        event["ticket_url"] = ticket
    for img in soup.select("div.col-md-8 img[src], div.media img[src]"):
        url = urljoin(BASIS_URL, img["src"])
        if url.startswith(BASIS_URL + "/fileadmin/"):
            event["bild_url"] = url
            break
    return True


def scrape() -> list[dict]:
    """Scrapt den Veranstaltungskalender des Hauses der Universität (Kalenderseiten + Detailseiten)."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        roh: list[dict] = []
        url: Optional[str] = KALENDER_URL
        for seite in range(MAX_SEITEN):
            if not url:
                break
            html = seite_abrufen(url, logger, wartezeit=WARTEZEIT)
            if html is None:
                if seite == 0:
                    logger.error("Scraper %s: Kalender nicht erreichbar", QUELLE_NAME)
                    return []
                break
            treffer = _termine_aus_liste(html, heute, enddatum)
            roh.extend(treffer)
            # Liste ist chronologisch: ab einer Seite ohne Termine im Fenster nicht weiterblättern
            if not treffer and seite > 0:
                break
            url = _naechste_seite(html)
        if not roh:
            logger.warning("Scraper %s: 0 Termine bei erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
            return []
        events: list[dict] = []
        gesehen: set[tuple] = set()
        for i, event in enumerate(roh):
            schluessel = (event["titel"].lower(), event["datum"], event["uhrzeit"])
            if schluessel in gesehen:
                continue
            gesehen.add(schluessel)
            # Nur Termine mit gelesener Detailseite: erst dort steht der Ort – ohne sie bekäme ein Campus-Termin die
            # Adresse am Schadowplatz (Cursor-Prüfung V2). MAX_DETAILS begrenzt die Abrufe, nicht die Ortsprüfung.
            if i >= MAX_DETAILS:
                logger.info("HdU: Obergrenze von %d Detailseiten erreicht – restliche Termine im nächsten Lauf", MAX_DETAILS)
                break
            detail = seite_abrufen(event["quelle_url"], logger, wartezeit=WARTEZEIT)
            if not detail:
                logger.info("HdU: Detailseite nicht erreichbar, Termin ausgelassen: %s", event["quelle_url"])
                continue
            try:
                if not _details_ergaenzen(event, detail):
                    continue
            except Exception as fehler:
                logger.warning("HdU: Detailseite nicht lesbar, Termin ausgelassen (%s): %s", event["quelle_url"], fehler)
                continue
            events.append(event)
        logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
        return events
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for ev in ergebnisse[:3]:
        print(json.dumps(ev, ensure_ascii=False, indent=2))
