"""
japan_center.py – DiesDasDüsseldorf
Scraper für japanische Kulturveranstaltungen in Düsseldorf.

Hintergrund (Stand 2026-11):
  Die ursprüngliche Quelle japan-duesseldorf.de ist tot: Die Domain leitet per
  HTTP 301 auf einen fachfremden Online-Shop (buehlot-bad-shop.de) um, das
  HTTPS-Zertifikat passt nicht zum Hostnamen. Dort gibt es keine Events mehr.

  Ersatzquelle ist das EKŌ-Haus der Japanischen Kultur (Düsseldorf-Niederkassel),
  das zentrale japanische Kulturzentrum der Stadt. Die Website nutzt das
  WordPress-Plugin „Events Manager“; Termine stehen als statisches HTML
  (`div.em-event.em-item`) auf den Kategorie-Seiten unter /veranstaltungen/.

  Warum nicht der iCal-Feed (eko-haus.de/events.ics)? Er ist auf 50 Einträge
  begrenzt, enthält jeden Termin dreisprachig (DE/EN/JA) und reicht deshalb nur
  ca. 2 Wochen in die Zukunft. Die Übersichtsseite /veranstaltungen/ zeigt nur
  20 Einträge; die einzelnen Kategorie-Seiten sind vollständig.

Strategie:
1. Übersichtsseite + Kategorie-Seiten laden (Rate Limiting 2 s)
2. Events-Manager-Karten parsen, über die Detail-URL deduplizieren
3. Nur Termine, die im Zeitfenster beginnen; laufende Kurse/Reihen, reine
   Online-Termine und ausgebuchte Termine werden übersprungen

URL: https://eko-haus.de/veranstaltungen/
Adresse: Brüggener Weg 6, 40547 Düsseldorf
Erstellt: 2026-03-06 · Überarbeitet: 2026-11-04 (Quelle tot → EKŌ-Haus)
"""
import asyncio
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE

logger = logging.getLogger(__name__)

LISTE_URL = "https://eko-haus.de/veranstaltungen/"
BASE_URL = "https://eko-haus.de"
QUELLE_NAME = "EKŌ-Haus der Japanischen Kultur"
ORT_STANDARD = "EKŌ-Haus der Japanischen Kultur"
ADRESSE_STANDARD = "Brüggener Weg 6, 40547 Düsseldorf"
KATEGORIE = "kultur"

# Übersicht + Kategorie-Seiten (die Übersicht allein ist auf 20 Einträge begrenzt)
SEITEN_URLS = [
    LISTE_URL,
    "https://eko-haus.de/veranstaltungen/kultur/",
    "https://eko-haus.de/veranstaltungen/fuehrungen/",
    "https://eko-haus.de/veranstaltungen/austellungen/",
    "https://eko-haus.de/veranstaltungen/kurse-workshops/",
    "https://eko-haus.de/veranstaltungen/wissenschaft-bildung/",
    "https://eko-haus.de/veranstaltungen/buddhistische-veranstaltungen/",
]

# Wartezeit zwischen zwei Requests (Rate Limiting, Sekunden)
WARTEZEIT = 2.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

# Kategorie-Mapping für japanische Kulturveranstaltungen (Titel + EKŌ-Kategorie)
KATEGORIE_MAPPING = {
    "konzert": "musik", "musik": "musik", "koto": "musik", "shamisen": "musik",
    "party": "nightlife", "club": "nightlife",
    "festival": "kultur", "fest": "kultur",
    "ausstellung": "kultur", "kunst": "kultur", "kultur": "kultur",
    "film": "kultur", "kino": "kultur", "teezeremonie": "kultur",
    "führung": "kultur",
    "workshop": "community", "kurs": "community", "vortrag": "community",
    "seminar": "community", "kolloquium": "community", "symposi": "community",
    "kinder": "family", "familie": "family",
    "essen": "food", "food": "food", "sushi": "food", "kochen": "food",
}


def _kategorie_erkennen(text: str) -> str:
    """
    Erkennt die passende Kategorie anhand des Titels oder der EKŌ-Kategorie.

    Args:
        text: Titel und/oder Kategorie-Text des Events

    Returns:
        Gültige Kategorie
    """
    if not text:
        return KATEGORIE
    text_klein = text.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if schluessel in text_klein:
            return kategorie
    return KATEGORIE


def _beschreibung_kuerzen(text: str) -> str:
    """
    Kürzt eine Beschreibung auf maximal 300 Zeichen.

    Args:
        text: Roher Beschreibungstext

    Returns:
        Beschreibung mit maximal 300 Zeichen
    """
    if not text:
        return ""
    bereinigt = " ".join(text.split())
    return bereinigt[:300]


def _datum_aus_text(text: str) -> Optional[date]:
    """
    Wandelt "TT.MM.JJJJ" in ein date-Objekt um.

    Args:
        text: Text mit deutschem Datum

    Returns:
        date oder None
    """
    treffer = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text or "")
    if not treffer:
        return None
    try:
        return date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1)))
    except ValueError:
        return None


def _uhrzeit_aus_text(text: str) -> Optional[str]:
    """
    Liest die Startzeit aus "13:00 - 14:30". "0:00" bedeutet beim EKŌ-Haus
    "ganztägig / keine Angabe" und wird zu None.

    Args:
        text: Inhalt der Zeitzeile

    Returns:
        Uhrzeit als HH:MM oder None
    """
    treffer = re.search(r"(\d{1,2}):(\d{2})", text or "")
    if not treffer:
        return None
    stunde, minute = int(treffer.group(1)), int(treffer.group(2))
    if stunde == 0 and minute == 0:
        return None
    if 0 <= stunde <= 23 and 0 <= minute <= 59:
        return f"{stunde:02d}:{minute:02d}"
    return None


def _preis_aus_kosten(kosten: str) -> Optional[str]:
    """
    Wandelt die Kostenangabe in das Preisformat um ("kostenlos", "ab 12€").

    Args:
        kosten: Text nach "Kosten:", z.B. "Erwachsene 12,00 €; Schüler: 10,00 €"

    Returns:
        Preis-String oder None
    """
    if not kosten:
        return None
    if "kostenlos" in kosten.lower() or "frei" in kosten.lower():
        return "kostenlos"
    # Zuschläge ("zzgl. Materialkosten 55,00 €") gehören nicht zum Grundpreis
    grundpreis = re.split(r"zzgl\.?|zuzüglich", kosten, flags=re.IGNORECASE)[0]
    betraege = []
    for euro, cent in re.findall(r"(\d+)(?:,(\d{2}))?\s*€", grundpreis):
        betraege.append(float(f"{euro}.{cent or '00'}"))
    if not betraege:
        return None
    minimum = min(betraege)
    if minimum.is_integer():
        return f"ab {int(minimum)}€"
    return f"ab {minimum:.2f}€".replace(".", ",")


def _attribute_lesen(karte) -> dict[str, str]:
    """
    Liest die "Schlüssel: Wert"-Zeilen (att-line) einer Event-Karte.

    Args:
        karte: BeautifulSoup-Element der Event-Karte

    Returns:
        Dict, z.B. {"veranstaltungsform": "Präsenz", "kosten": "kostenlos", ...}
    """
    attribute: dict[str, str] = {}
    for zeile in karte.select(".att-line"):
        text = " ".join(zeile.get_text(" ", strip=True).split())
        if ":" in text:
            schluessel, wert = text.split(":", 1)
            attribute[schluessel.strip().lower()] = wert.strip()
    return attribute


def _events_aus_html(
    html: str, heute: date, enddatum: date, gesehene_urls: set[str]
) -> list[dict]:
    """
    Parst die Events-Manager-Karten einer EKŌ-Haus-Seite.

    Args:
        html:          HTML-Quelltext der Seite
        heute:         Aktuelles Datum
        enddatum:      Maximales Datum für Events
        gesehene_urls: Bereits verarbeitete Detail-URLs (wird ergänzt)

    Returns:
        Liste von Event-Dicts
    """
    soup = BeautifulSoup(html, "html.parser")
    karten = soup.select("div.em-event.em-item")
    logger.debug("EKŌ-Haus: %d Event-Karten auf der Seite", len(karten))

    events = []
    for karte in karten:
        try:
            titel_el = karte.select_one(".em-item-title")
            if not titel_el:
                continue
            titel = " ".join(titel_el.get_text(" ", strip=True).split())
            if not titel or len(titel) < 3:
                continue

            link_el = titel_el.find("a", href=True) or karte.select_one("a.em-item-read-more[href]")
            quelle_url = urljoin(BASE_URL, link_el["href"]) if link_el else LISTE_URL
            if quelle_url in gesehene_urls:
                continue

            datum_el = karte.select_one(".em-event-date")
            datum_text = datum_el.get_text(" ", strip=True) if datum_el else ""
            start = _datum_aus_text(datum_text)
            if not start:
                continue

            # Nur Termine, die im Zeitfenster beginnen. Laufende Kurse/Reihen
            # (Start in der Vergangenheit) würden sonst täglich neu auftauchen.
            if start < heute or start > enddatum:
                continue

            attribute = _attribute_lesen(karte)
            form = attribute.get("veranstaltungsform", "").lower()
            if form == "online":
                logger.debug("Reiner Online-Termin übersprungen: %s", titel)
                continue
            if "ausgebucht" in (attribute.get("anmeldebeginn", "") + " " + titel).lower():
                logger.debug("Ausgebuchter Termin übersprungen: %s", titel)
                continue

            gesehene_urls.add(quelle_url)

            zeit_el = karte.select_one(".em-event-time")
            uhrzeit = _uhrzeit_aus_text(zeit_el.get_text(" ", strip=True) if zeit_el else "")

            raum_el = karte.select_one(".em-event-location")
            raum = " ".join(raum_el.get_text(" ", strip=True).split()) if raum_el else ""

            kat_el = karte.select_one(".em-event-categories")
            eko_kategorie = " ".join(kat_el.get_text(" ", strip=True).split()) if kat_el else ""

            bild_el = karte.select_one(".em-item-image img")
            bild_url = None
            if bild_el:
                bild_url = bild_el.get("data-src") or bild_el.get("src")
                if bild_url and bild_url.startswith("/"):
                    bild_url = urljoin(BASE_URL, bild_url)
                if bild_url and not bild_url.startswith("http"):
                    bild_url = None

            teile = []
            if eko_kategorie:
                teile.append(eko_kategorie)
            if raum:
                teile.append(f"Ort: {raum}")
            if attribute.get("ausführende"):
                teile.append(f"Mit: {attribute['ausführende']}")
            if form == "hybrid":
                teile.append("auch online")
            if attribute.get("anmeldung"):
                # Nur Hinweis, keine E-Mail-Adresse in die Beschreibung übernehmen
                teile.append("Anmeldung erforderlich")
            ende = _datum_aus_text(datum_text.split("-", 1)[1]) if "-" in datum_text else None
            if ende and ende > start:
                teile.append(f"bis {ende.strftime('%d.%m.%Y')}")
            beschreibung = _beschreibung_kuerzen(" · ".join(teile)) or None

            events.append({
                "titel": titel,
                "datum": start.isoformat(),
                "uhrzeit": uhrzeit,
                "ort": ORT_STANDARD,
                "adresse": ADRESSE_STANDARD,
                "kategorie": _kategorie_erkennen(f"{titel} {eko_kategorie}"),
                "beschreibung": beschreibung,
                "preis": _preis_aus_kosten(attribute.get("kosten", "")),
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "bild_generiert": False,
                "post_typ": "feed",
                "instagram_caption": None,
                "status": "neu",
            })

        except Exception as fehler:
            logger.error("Fehler beim Parsen einer Event-Karte: %s", str(fehler))
            continue

    return events


async def scrape() -> list[dict]:
    """
    Scrapt japanische Kulturveranstaltungen des EKŌ-Hauses Düsseldorf.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    events: list[dict] = []
    gesehene_urls: set[str] = set()
    geladene_seiten = 0

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            for url in SEITEN_URLS:
                wartezeit = WARTEZEIT
                html = None
                for versuch in range(3):
                    await asyncio.sleep(wartezeit)
                    try:
                        antwort = await client.get(url)
                        if antwort.status_code == 429:
                            wartezeit *= 2
                            logger.warning("HTTP 429 bei %s – warte %.0f s (Versuch %d)", url, wartezeit, versuch + 1)
                            continue
                        antwort.raise_for_status()
                        html = antwort.text
                    except httpx.HTTPStatusError as fehler:
                        logger.error("HTTP Fehler %s beim Abrufen von %s", fehler.response.status_code, url)
                    except Exception as fehler:
                        logger.error("Fehler beim Abrufen von %s: %s", url, str(fehler))
                    break

                if not html:
                    continue
                geladene_seiten += 1
                neue = _events_aus_html(html, heute, enddatum, gesehene_urls)
                logger.debug("%s: %d neue Events", url, len(neue))
                events.extend(neue)
    except Exception as fehler:
        logger.error("Scraper %s: unerwarteter Fehler: %s", QUELLE_NAME, str(fehler))

    if not geladene_seiten:
        logger.warning("Scraper %s: Keine Seite geladen – leere Liste wird zurückgegeben", QUELLE_NAME)

    events.sort(key=lambda e: (e["datum"], e["uhrzeit"] or ""))
    logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json as _json
    ergebnisse = asyncio.run(scrape())
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
