"""
savoy_theater.py – DiesDasDüsseldorf
Scraper für das Savoy Theater (Graf-Adolf-Straße).
Programmseite: https://savoy-theater.de/

Die WordPress-Seite lädt die Veranstaltungsliste per JavaScript nach: jQuery schickt das Filterformular
(#va-filter, action=getevents) per POST an /wp-admin/admin-ajax.php und bekommt JSON {"html": …, "max_page": n}
mit je 5 Terminen (div.va-box) zurück. Ein GET liefert immer nur Seite 1 (die Parameter werden nur aus POST
gelesen), deshalb fragen wir die Seiten wie der Browser per POST ab – nur lesend, ohne Filter, ohne Login.
Die Detailseiten /veranstaltung/<slug>/ sind leer (kein Datum, kein Text), Tickets laufen über Eventim.
Die Liste enthält auch Gastspiele des Savoy-Veranstalters an anderen Orten (z. B. Mitsubishi Electric Halle,
Tonhalle) – wir übernehmen nur Termine, deren Ortsangabe „Savoy“ enthält.

robots.txt geprüft am 2026-11-24: „Disallow: /wp-admin/“, aber ausdrücklich „Allow: /wp-admin/admin-ajax.php“
– der Abruf ist erlaubt.

Kategorie: Die Box nennt kein Genre. Konzerte/Musik → musik (Stichwörter in Künstler/Titel, bzw. „Konzert“ im
Text ohne Comedy-/Kabarett-/Lesungs-Hinweis), alles andere (Comedy, Kabarett, Lesung, Show, Film-Tour) → kultur.

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1)
"""
import logging
import re
import time
from datetime import date
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.datum import datum_parsen, uhrzeit_parsen
from scraper.utils.http_client import STANDARD_HEADERS, _backoff
from scraper.utils.ticket_link import ticket_link, ticket_link_aus

logger = logging.getLogger(__name__)

BASE_URL = "https://savoy-theater.de/"
AJAX_URL = "https://savoy-theater.de/wp-admin/admin-ajax.php"
QUELLE_NAME = "Savoy Theater"
ORT_STANDARD = "Savoy Theater"
ADRESSE_STANDARD = "Graf-Adolf-Straße 47, 40215 Düsseldorf"
MAX_SEITEN = 35  # 5 Termine je Seite; 31 Seiten reichten am 24.11.2026 für das 365-Tage-Fenster
WARTEZEIT_S = 2.0

# Musik-Hinweise im Künstler-/Titelfeld (stark)
_MUSIK_STARK = re.compile(
    r"orchestra|orchester|\bband\b|\bsingt\b|sing\(t\)|mitsing|\bsings\b|gospel|\bchor\b|a ?cappella|tribute|"
    r"revival|quartett|\btrio\b|philharmon|konzert|in concert|unplugged|symphon|sinfoni|big ?band|swing",
    re.I,
)
# Hinweise im Beschreibungstext: Musik gegen Comedy/Kabarett/Lesung/Show – es zählt die Mehrheit
_MUSIK_TEXT = re.compile(
    r"konzert\w*|live-?band|\bband\b|a ?cappella|gospel|orchest\w*|\bhits\b|\blieder\b|\bsongs?\b|\balbum\b|"
    r"\bmusik\b|chorleiter|sängerin|sänger\b",
    re.I,
)
_KEINE_MUSIK = re.compile(
    r"comedy|comedian|kabarett\w*|stand-?up|\blesung\b|\bliest\b|zauber\w*|\bmagie\b|magier|hypnose|"
    r"reportage|vortrag|podcast|theaterstück|komödie|puppen\w*|\bfilm\b",
    re.I,
)


def _kategorie(kuenstler: str, titel: str, text: str) -> str:
    """musik für Konzerte, sonst kultur (Comedy, Kabarett, Lesung, Show, Film)."""
    kopf = f"{kuenstler} {titel}"
    if re.search(r"comedian harmonists", kopf, re.I):   # Gesangsensemble, trotz „Comedian“
        return "musik"
    if _KEINE_MUSIK.search(kopf):
        return "kultur"
    if _MUSIK_STARK.search(kopf):
        return "musik"
    if len(_MUSIK_TEXT.findall(text)) > len(_KEINE_MUSIK.findall(text)):
        return "musik"
    return "kultur"


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


def _event_aus_box(box, heute: date, enddatum: date) -> Optional[dict]:
    """Wandelt eine Veranstaltungsbox (div.va-box) in ein Event-Dict um."""
    # Nur Termine im Savoy Theater (die Liste enthält auch andere Spielorte)
    ort_text = _text(box.find(class_="venue"))
    if ort_text and "savoy" not in ort_text.lower():
        return None

    tag_text = _text(box.find(class_="day-big")).rstrip(".")
    monat_jahr = _text(box.find(class_="month-year"))
    datum = datum_parsen(f"{tag_text}. {monat_jahr}") if tag_text and monat_jahr else None
    if not datum:
        return None
    tag = date.fromisoformat(datum)
    if tag < heute or tag > enddatum:
        return None

    # Abgesagte Termine: Ticket-Button mit Klasse „abgesagt“ (ausverkaufte bleiben)
    for knopf in box.find_all("a", class_="ticket-button"):
        if "abgesagt" in (knopf.get("class") or []) or "abgesagt" in _text(knopf).lower():
            return None

    kuenstler = _text(box.find(class_="va-performer"))
    programm = _text(box.find(class_="va-title"))
    if kuenstler and programm and programm.lower() != kuenstler.lower():
        # „GRENZGANG Live-Show:“ + „Nomade auf Zeit“ → mit Leerzeichen statt Gedankenstrich verbinden
        titel = f"{kuenstler} {programm}" if kuenstler.endswith(":") else f"{kuenstler} – {programm}"
    else:
        titel = kuenstler or programm
    if not titel:
        return None

    uhrzeit = uhrzeit_parsen(_text(box.find(class_="day-time")))

    bild_url = None
    bild_el = box.find(class_="thumb-container")
    if bild_el:
        treffer = re.search(r"url\(\s*['\"]?([^'\")]+)", bild_el.get("style") or "")
        if treffer and "savoy-theater.de" in treffer.group(1):
            bild_url = treffer.group(1).strip()

    return {
        "titel": titel,
        "datum": datum,
        "uhrzeit": uhrzeit,
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": _kategorie(kuenstler, programm, _text(box.find(class_="va-text"))),
        "beschreibung": None,
        "preis": None,
        "quelle_name": QUELLE_NAME,
        "quelle_url": BASE_URL,
        "ticket_url": ticket_link_aus(box, BASE_URL),  # Eventim-Button des Termins (Plan 5.5.2, P1)
        "bild_url": bild_url,
        "bild_generiert": False,
        "status": "neu",
    }


def _termine_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """Liest die Termine aus dem HTML-Teil einer Antwort (ohne Netz testbar)."""
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for box in soup.find_all("div", class_="va-box"):
        try:
            event = _event_aus_box(box, heute, enddatum)
        except Exception as fehler:
            logger.error("%s: Fehler beim Lesen einer Veranstaltung: %s", QUELLE_NAME, fehler)
            continue
        if event:
            events.append(event)
    return events


def _letztes_datum(html: str) -> Optional[date]:
    """Spätestes Datum einer Listenseite (auch fremde Spielorte) – zum Abbrechen hinter dem Fensterende."""
    soup = BeautifulSoup(html, "html.parser")
    daten = []
    for box in soup.find_all("div", class_="va-box"):
        d = datum_parsen(f"{_text(box.find(class_='day-big')).rstrip('.')}. {_text(box.find(class_='month-year'))}")
        if d:
            daten.append(date.fromisoformat(d))
    return max(daten) if daten else None


def _seite_holen(client: httpx.Client, seite: int) -> Optional[dict]:
    """Holt eine Listenseite per POST (wie der Browser), mit Pause und Backoff bei 429."""
    daten = {"action": "getevents", "termine": "", "genre": "", "search": "", "home": "1", "page": str(seite)}
    time.sleep(WARTEZEIT_S)
    try:
        antwort = client.post(AJAX_URL, data=daten)
        for versuch in range(3):
            if antwort.status_code != 429:
                break
            pause = _backoff(antwort.headers.get("Retry-After"), versuch)
            logger.warning("HTTP 429 bei %s – warte %.0f s (Versuch %d von 3)", AJAX_URL, pause, versuch + 1)
            time.sleep(pause)
            antwort = client.post(AJAX_URL, data=daten)
        antwort.raise_for_status()
        return antwort.json()
    except Exception as fehler:
        logger.error("%s: Listenseite %d nicht abrufbar: %s", QUELLE_NAME, seite, fehler)
        return None


def _ohne_doppelte(events: list[dict]) -> list[dict]:
    """Gleicher Titel, Tag und Uhrzeit nur einmal."""
    gesehen: set[tuple] = set()
    ergebnis = []
    for e in events:
        schluessel = (e["titel"].lower(), e["datum"], e["uhrzeit"])
        if schluessel not in gesehen:
            gesehen.add(schluessel)
            ergebnis.append(e)
    return ergebnis


def scrape() -> list[dict]:
    """Scrapt die Veranstaltungsliste des Savoy Theaters. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    events: list[dict] = []
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        kopf = dict(STANDARD_HEADERS, Accept="application/json, text/javascript, */*; q=0.01",
                    Referer=BASE_URL, **{"X-Requested-With": "XMLHttpRequest"})
        with httpx.Client(headers=kopf, timeout=30, follow_redirects=True) as client:
            max_seite = 1
            seite = 1
            while seite <= min(max_seite, MAX_SEITEN):
                antwort = _seite_holen(client, seite)
                if antwort is None:
                    if seite == 1:
                        return []
                    break
                html = antwort.get("html") or ""
                try:
                    max_seite = int(antwort.get("max_page") or 1)
                except (TypeError, ValueError):
                    max_seite = 1
                if "keine Veranstaltung" in html and "va-box" not in html:
                    break
                events.extend(_termine_aus_html(html, heute, enddatum))
                letztes = _letztes_datum(html)
                if letztes and letztes > enddatum:
                    break
                seite += 1
            if max_seite > MAX_SEITEN and seite > MAX_SEITEN:
                logger.info("%s: Seitenlimit %d erreicht (%d Seiten verfügbar)", QUELLE_NAME, MAX_SEITEN, max_seite)

        events = _ohne_doppelte(events)
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
