"""
apollo_variete.py – DiesDasDüsseldorf
Scraper für Roncalli's Apollo Varieté (unter der Rheinkniebrücke).
URL: https://www.apollo-variete.com/apollo-shows/

Die Übersicht listet alle Shows mit Link auf die Show-Seite. Auf jeder Show-Seite steht im Kopf
(span.block__home__subtitle) die Spielzeit, entweder als Zeitraum („15. Januar – 11. April 2027“) oder als
Liste einzelner Tage („8. November 2026, 4. April, 6. Juni, 19. September und 28. Oktober 2027“).
Einzelne Vorstellungen mit Uhrzeit nennt die Website NICHT – die stehen nur im Ticketshop
tickets.apollo-variete.com, und dessen robots.txt sperrt alles („Disallow: /“). Deshalb:
  - Einzeltage → je Tag ein Termin (Uhrzeit None),
  - Zeitraum (lange Spielzeit, viele Vorstellungen) → ein Eintrag mit datum = Start (bzw. heute, wenn die Show
    schon läuft) und datum_bis = Ende.
Nennt die Show-Seite keinen künftigen Termin (veraltete Angabe), wird die Datumszeile der Show-Karte in der
Übersicht genommen – aber nur, wenn sie eindeutig ist (nicht „Bis …“, „Ab …“, „… und weitere Termine“).

robots.txt geprüft am 2026-11-24: www.apollo-variete.com „User-agent: * / Allow: /“;
tickets.apollo-variete.com „Disallow: /“ (wird nicht abgerufen).

Erstellt: 2026-11-24 (Quellen-Ausbau, Schritt V1)
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
from scraper.utils.ticket_link import ticket_link_aus

logger = logging.getLogger(__name__)

BASE_URL = "https://www.apollo-variete.com"
SHOWS_URL = "https://www.apollo-variete.com/apollo-shows/"
QUELLE_NAME = "Roncalli's Apollo Varieté"
ORT_STANDARD = "Roncalli's Apollo Varieté"
ADRESSE_STANDARD = "Apollo-Platz 1, 40213 Düsseldorf"
KATEGORIE_STANDARD = "kultur"
MAX_SHOWSEITEN = 14    # Übersicht + höchstens 14 Show-Seiten = 15 Abrufe je Lauf

# Ein Datumsbaustein: Tag, optional Monatsname, optional Jahr („23 . Oktober 2026“, „4. April“, „15.“)
_MONATSNAMEN = "|".join(sorted(MONAT_MAP, key=len, reverse=True))
_BAUSTEIN = re.compile(rf"(\d{{1,2}})\s*\.\s*(?:({_MONATSNAMEN})\b\s*)?(\d{{4}})?", re.I)
_ZEITRAUM = re.compile(r"\s(–|—|-|bis)\s")
_SHOW_LINK = re.compile(r"^https://www\.apollo-variete\.com/apollo-shows/[^/?#]+/?$")


def _bausteine(text: str) -> list[list]:
    """Zerlegt eine Datumsangabe in [Tag, Monat|None, Jahr|None]; fehlende Monate/Jahre von rechts ergänzt."""
    teile = []
    for m in _BAUSTEIN.finditer(text):
        monat = MONAT_MAP.get((m.group(2) or "").lower())
        teile.append([int(m.group(1)), monat, int(m.group(3)) if m.group(3) else None])
    monat, jahr = None, None
    for teil in reversed(teile):
        if teil[1] is None:
            teil[1] = monat
        else:
            monat = teil[1]
        if teil[2] is None:
            teil[2] = jahr
        else:
            jahr = teil[2]
    return [t for t in teile if t[1] and t[2]]


def termine_aus_angabe(text: str) -> tuple[list[date], Optional[tuple[date, date]]]:
    """
    Liest die Spielzeit-Angabe einer Show.

    Returns:
        (Einzeltage, Zeitraum) – genau eins davon ist gefüllt; ([], None) wenn nichts lesbar ist.
    """
    text = (text or "").replace("\xa0", " ").replace("&", " und ")
    teile = _bausteine(text)
    if not teile:
        return [], None
    if _ZEITRAUM.search(text) and len(teile) == 2:
        try:
            start = date(teile[0][2], teile[0][1], teile[0][0])
            ende = date(teile[1][2], teile[1][1], teile[1][0])
        except ValueError:
            return [], None
        if start > ende and start.year == ende.year:
            start = start.replace(year=start.year - 1)   # „15. Dezember – 10. Januar 2027“
        return [], (start, ende)
    tage = []
    for tag, monat, jahr in teile:
        try:
            tage.append(date(jahr, monat, tag))
        except ValueError:
            continue
    return sorted(set(tage)), None


def _show_links(html: str) -> list[str]:
    """Links auf die Show-Seiten aus der Übersicht (Reihenfolge wie auf der Seite, ohne Doppel)."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        url = urljoin(SHOWS_URL, a["href"].strip())
        if _SHOW_LINK.match(url) and url.rstrip("/") != SHOWS_URL.rstrip("/") and url not in links:
            links.append(url)
    return links


def _karten_angaben(html: str) -> dict[str, str]:
    """
    Datumszeile je Show-Karte der Übersicht (erste Zeile in div.block__content, z. B. „6. Oktober 2027“).
    Dient als Ersatz, wenn die Show-Seite selbst ein veraltetes Datum zeigt (am 24.11.2026 bei Robert Kreis:
    Show-Seite „6. Oktober 2026“, Übersicht „6. Oktober 2027“).
    """
    soup = BeautifulSoup(html, "html.parser")
    angaben: dict[str, str] = {}
    for inhalt in soup.find_all("div", class_="block__content"):
        link = next((a for a in inhalt.find_all("a", href=True)
                     if _SHOW_LINK.match(urljoin(SHOWS_URL, a["href"].strip()))), None)
        if not link:
            continue
        zeilen = [z.strip() for z in inhalt.get_text("\n").split("\n") if z.strip()]
        if zeilen:
            angaben.setdefault(urljoin(SHOWS_URL, link["href"].strip()), zeilen[0])
    return angaben


def _ersatz_tauglich(angabe: Optional[str]) -> bool:
    """Nur eindeutige Angaben aus der Übersicht übernehmen – nicht „Bis …“, „Ab …“ oder „… und weitere Termine“."""
    if not angabe:
        return False
    return not re.match(r"\s*(bis|ab)\b", angabe, re.I) and "weitere" not in angabe.lower()


def _termine_aus_html(html: str, seiten_url: str, heute: date, enddatum: date,
                      ersatz_angabe: Optional[str] = None) -> list[dict]:
    """
    Liest Titel, Spielzeit und Bild einer Show-Seite und baut die Termine (ohne Netz testbar).
    ersatz_angabe: Datumszeile der Übersicht – wird genutzt, wenn die Show-Seite keinen künftigen Termin nennt.
    """
    soup = BeautifulSoup(html, "html.parser")
    angabe_el = soup.find(class_="block__home__subtitle")
    titel_el = soup.find("h1")
    if not angabe_el or not titel_el:
        return []
    titel = re.sub(r"\s+", " ", titel_el.get_text(" ", strip=True).replace("\xad", "")).strip()
    if not titel:
        return []

    bild_url = None
    bild_el = soup.find("img", class_="block__home__background", src=True)
    if bild_el and "apollo-variete.com" in bild_el["src"]:
        bild_url = bild_el["src"]

    # Ticketshop der Show (tickets.apollo-variete.com, Plan 5.5.2, P1) – nur verlinkt, nie abgerufen (robots „Disallow: /“)
    ticket_url = ticket_link_aus(soup, seiten_url)

    def _event(datum: date, datum_bis: Optional[date] = None) -> dict:
        event = {
            "titel": titel,
            "datum": datum.isoformat(),
            "uhrzeit": None,
            "ort": ORT_STANDARD,
            "adresse": ADRESSE_STANDARD,
            "kategorie": KATEGORIE_STANDARD,
            "beschreibung": None,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": seiten_url,
            "ticket_url": ticket_url,
            "bild_url": bild_url,
            "bild_generiert": False,
            "status": "neu",
        }
        if datum_bis:
            event["datum_bis"] = datum_bis.isoformat()
        return event

    def _aus_angabe(angabe: str) -> list[dict]:
        tage, zeitraum = termine_aus_angabe(angabe)
        if zeitraum:
            start, ende = zeitraum
            if ende < heute or start > enddatum:
                return []
            return [_event(max(start, heute), ende)]
        return [_event(t) for t in tage if heute <= t <= enddatum]

    events = _aus_angabe(angabe_el.get_text(" ", strip=True))
    if not events and _ersatz_tauglich(ersatz_angabe):
        events = _aus_angabe(ersatz_angabe)
        if events:
            logger.info("%s: Datum aus der Übersicht übernommen für %s (%s)", QUELLE_NAME, seiten_url, ersatz_angabe)
    return events


def scrape() -> list[dict]:
    """Scrapt die Shows des Apollo Varietés. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    events: list[dict] = []
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        html = seite_abrufen(SHOWS_URL, logger, wartezeit=2.0)
        if html is None:
            logger.error("%s: Show-Übersicht nicht erreichbar", QUELLE_NAME)
            return []
        links = _show_links(html)
        karten = _karten_angaben(html)
        if len(links) > MAX_SHOWSEITEN:
            logger.warning("%s: %d Shows, nur die ersten %d werden gelesen", QUELLE_NAME, len(links), MAX_SHOWSEITEN)
        for url in links[:MAX_SHOWSEITEN]:
            seite = seite_abrufen(url, logger, wartezeit=2.0)
            if seite is None:
                continue
            neue = _termine_aus_html(seite, url, heute, enddatum, karten.get(url))
            if not neue:
                logger.info("%s: keine künftigen Termine auf %s", QUELLE_NAME, url)
            events.extend(neue)

        gesehen: set[tuple] = set()
        eindeutig = []
        for e in events:
            schluessel = (e["titel"].lower(), e["datum"], e["uhrzeit"])
            if schluessel not in gesehen:
                gesehen.add(schluessel)
                eindeutig.append(e)
        events = eindeutig
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
