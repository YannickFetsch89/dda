"""
kabarett_flin.py – DiesDasDüsseldorf
Scraper für das KaBARett FLiN (Kleinkunstbühne in Gerresheim).
Programmseite: https://www.kabarett-flin.de/spielplan-und-tickets

Die Wix-Seite liefert den Spielplan nicht im HTML aus: Er steckt in einem eingebetteten HTML-Element
(www-kabarett-flin-de.filesusr.com/html/51a94f_66b7f962ed4ea9f02e3692b6c4cf74f2.html), das nur das Kalender-
Widget des Ticketdienstleisters Neanderticket lädt (<div id="eventContainer" data-wlivewhat="all"
data-wliveclient="kabarettflin"> + neanderticket.de/js/events.js). Das Widget holt die Termine als HTML von
https://www.neanderticket.de/events/what=All;client=kabarettflin – genau diese Liste lesen wir (ein Abruf,
alle Termine der Saison; je Termin ein div.klive-terminbox mit Datum inkl. Jahr im Attribut data-datum).
Bilder liegen auf neanderticket.de (nicht auf der Website des Hauses) → bild_url None.

robots.txt geprüft am 2026-11-24:
  - www.kabarett-flin.de: „User-agent: * / Allow: /“ (nur ?lightbox= gesperrt; Crawl-delay 10 für dotbot/
    AhrefsBot – wir halten 10 s trotzdem ein).
  - www.neanderticket.de: gesperrt sind nur /__partnerkalender/, /terminkalender/…, /tellafriend/ – der
    Pfad /events/ ist erlaubt.

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1)
"""
import logging
import re
from datetime import date
from typing import Optional

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.datum import uhrzeit_parsen
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

PROGRAMM_URL = "https://www.kabarett-flin.de/spielplan-und-tickets"
WIDGET_URL = "https://www.neanderticket.de/events/what=All;client=kabarettflin"
QUELLE_NAME = "KaBARett FLiN"
ORT_STANDARD = "KaBARett FLiN"
ADRESSE_STANDARD = "Ludenberger Str. 37, 40629 Düsseldorf"
KATEGORIE_STANDARD = "kultur"
WARTEZEIT_S = 10.0   # Crawl-delay 10 aus robots.txt der Website einhalten

_DATUM = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{4})")
# Verlegte (alter Termin) und abgesagte Termine weglassen; der neue Termin steht als eigener Eintrag in der Liste
_ENTFAELLT = re.compile(r"wurde\s+(abgesagt|verlegt)|f(ä|ae)llt\s+aus|entf(ä|ae)llt", re.I)


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def _preis(box) -> Optional[str]:
    """Erste Preiszeile aus dem Ticketbereich, z. B. „EUR 33,00 / 30,00 (ermäßigt)“."""
    bereich = box.find(class_="klive-langfassung-ticketpreise")
    if not bereich:
        return None
    absatz = bereich.find("p")
    if not absatz:
        return None
    zeilen = [z.strip() for z in absatz.get_text("\n").split("\n") if z.strip()]
    if not zeilen:
        return None
    zeile = zeilen[0]
    if re.search(r"eintritt\s+frei|kostenlos|freier\s+eintritt", zeile, re.I):
        return "kostenlos"
    return zeile[:80]


def _event_aus_box(box, heute: date, enddatum: date) -> Optional[dict]:
    """Wandelt eine Terminbox des Widgets in ein Event-Dict um."""
    datum_el = box.find(attrs={"data-datum": True})
    treffer = _DATUM.search(datum_el["data-datum"]) if datum_el else None
    if not treffer:
        return None
    try:
        tag = date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1)))
    except ValueError:
        return None
    if tag < heute or tag > enddatum:
        return None

    # Hinweis „Diese Veranstaltung wurde verlegt“ / „Dieser Termin wurde abgesagt“ steht in div.klive-terminaenderung
    if any(_ENTFAELLT.search(_text(hinweis)) for hinweis in box.find_all(class_="klive-terminaenderung")):
        return None

    # Nur Termine im FLiN (das Widget kann auch Sonderveranstaltungen an anderen Orten zeigen)
    ort_text = (_text(box.find(class_="klive-location")) + " " + _text(box.find(class_="klive-city"))).lower()
    if ort_text.strip() and ("flin" not in ort_text or "düsseldorf" not in ort_text):
        return None

    kuenstler = _text(box.find(class_="klive-titel-artist"))
    programm = _text(box.find(class_="klive-titel-titel"))
    if kuenstler and programm and programm.lower() not in kuenstler.lower():
        titel = f"{kuenstler} – {programm}"
    else:
        titel = kuenstler or programm
    if not titel:
        return None

    uhrzeit = uhrzeit_parsen(_text(box.find(class_="klive-zeit")))

    return {
        "titel": titel,
        "datum": tag.isoformat(),
        "uhrzeit": uhrzeit,
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": KATEGORIE_STANDARD,
        "beschreibung": None,
        "preis": _preis(box),
        "quelle_name": QUELLE_NAME,
        "quelle_url": PROGRAMM_URL,
        "bild_url": None,
        "bild_generiert": False,
        "status": "neu",
    }


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Liest alle Termine aus dem Widget-HTML (ohne Netz testbar)."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for box in soup.find_all("div", class_="klive-terminbox"):
        try:
            event = _event_aus_box(box, heute, enddatum)
        except Exception as fehler:
            logger.error("%s: Fehler beim Lesen eines Termins: %s", QUELLE_NAME, fehler)
            continue
        if not event:
            continue
        schluessel = (event["titel"].lower(), event["datum"], event["uhrzeit"])
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        events.append(event)
    return events


def scrape() -> list[dict]:
    """Scrapt den Spielplan des KaBARett FLiN. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        html = seite_abrufen(WIDGET_URL, logger, wartezeit=WARTEZEIT_S)
        if html is None:
            logger.error("%s: Spielplan-Widget nicht erreichbar", QUELLE_NAME)
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
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Termine ===")
    for e in ergebnisse[:5]:
        print(e)
