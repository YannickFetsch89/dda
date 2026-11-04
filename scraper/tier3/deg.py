"""
deg.py – DiesDasDüsseldorf
Scraper für DEG Eishockey Heimspiele Düsseldorf.

Scrapt nur Heimspiele aus dem offiziellen Spielplan der Düsseldorfer EG.

Hintergrund (Stand 2026-11):
  Die frühere Domain deg-hockey.de existiert nicht mehr (DNS löst nicht auf).
  Der offizielle Spielplan liegt unter deg-eishockey.de/saison/spielplan/ und
  wird serverseitig als statisches HTML ausgeliefert – Playwright ist nicht nötig.
  JSON-LD enthält dort nur WebPage-Metadaten, keine Spiele.

Strategie:
1. Spielplan-Seite laden, alle Karten `a.scoreboard-item.is-home` auswerten
   (Testspiele = `is-test`, Auswärtsspiele = `is-away` werden ignoriert).
2. Für jedes Heimspiel im Zeitfenster das Game Center laden (Rate Limiting 2 s),
   um den vollen Gegnernamen und die Spielstätte zu ermitteln.
   Fällt das aus, wird das Vereinskürzel über eine statische Tabelle aufgelöst.

URL: https://www.deg-eishockey.de/saison/spielplan/
Adresse: Siegburger Str. 15, 40591 Düsseldorf
Erstellt: 2026-03-06 · Überarbeitet: 2026-11-04 (Domainwechsel, neues HTML)
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
from scraper.utils.datum import datum_parsen

logger = logging.getLogger(__name__)

LISTE_URL = "https://www.deg-eishockey.de/saison/spielplan/"
BASE_URL = "https://www.deg-eishockey.de"
QUELLE_NAME = "DEG Eishockey Düsseldorf"
ORT_STANDARD = "PSD BANK DOME Düsseldorf"
ADRESSE_STANDARD = "Siegburger Str. 15, 40591 Düsseldorf"
KATEGORIE = "sport"
PREIS_FALLBACK = "ab 10€"
HEIMTEAM = "Düsseldorfer EG"
HEIM_KUERZEL = "DEG"

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

# Fallback: Vereinskürzel → voller Name (DEL2, Saison 2026/27).
# Wird nur genutzt, wenn das Game Center nicht geladen werden kann.
TEAM_KUERZEL = {
    "BDW": "Blue Devils Weiden",
    "DRE": "Dresdner Eislöwen",
    "EBR": "Eisbären Regensburg",
    "ECK": "EC Kassel Huskies",
    "ECN": "EC Bad Nauheim",
    "EPC": "Eispiraten Crimmitschau",
    "EVL": "EV Landshut",
    "FRB": "EHC Freiburg",
    "LFX": "Lausitzer Füchse",
    "MEM": "ECDC Memmingen Indians",
    "RVT": "Ravensburg Towerstars",
    "SBR": "Starbulls Rosenheim",
    "SCB": "Bietigheim Steelers",
}


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


async def _seite_laden(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """
    Lädt eine Seite mit Rate Limiting und einfachem Backoff bei HTTP 429.

    Args:
        client: Offener httpx.AsyncClient
        url:    Ziel-URL

    Returns:
        HTML-Text oder None bei Fehler
    """
    wartezeit = WARTEZEIT
    for versuch in range(3):
        await asyncio.sleep(wartezeit)
        try:
            antwort = await client.get(url)
            if antwort.status_code == 429:
                wartezeit *= 2
                logger.warning("HTTP 429 bei %s – warte %.0f s (Versuch %d)", url, wartezeit, versuch + 1)
                continue
            antwort.raise_for_status()
            return antwort.text
        except httpx.HTTPStatusError as fehler:
            logger.error("HTTP Fehler %s beim Abrufen von %s", fehler.response.status_code, url)
            return None
        except Exception as fehler:
            logger.error("Fehler beim Abrufen von %s: %s", url, str(fehler))
            return None
    logger.error("Abbruch nach wiederholtem HTTP 429: %s", url)
    return None


def _uhrzeit_aus_datumszeile(text: str) -> Optional[str]:
    """
    Liest die Anstoßzeit aus einer Zeile wie "15.11.2026 · 17.00 Uhr".

    uhrzeit_parsen() würde hier fälschlich "15.11" als Uhrzeit erkennen,
    deshalb wird nur der Teil nach dem Datum ausgewertet.

    Args:
        text: Datumszeile der Spielkarte

    Returns:
        Uhrzeit als HH:MM oder None
    """
    treffer = re.search(r"(\d{1,2})[:.](\d{2})\s*Uhr", text, re.IGNORECASE)
    if not treffer:
        return None
    stunde, minute = int(treffer.group(1)), int(treffer.group(2))
    if 0 <= stunde <= 23 and 0 <= minute <= 59:
        return f"{stunde:02d}:{minute:02d}"
    return None


def _heimspiele_aus_spielplan(html: str, heute: date, enddatum: date) -> list[dict]:
    """
    Extrahiert die Heimspiele im Zeitfenster aus der Spielplan-Seite.

    Struktur (Stand 2026-11):
      <a href=".../gamecenter/<id>/" class="scoreboard-item is-home">
        <div class="sb-gameday">Spieltag 16</div>
        ... <div class="sb-name">DEG</div> ... <div class="sb-name">RVT</div>
        <div class="sb-date"> 15.11.2026 · 17.00 Uhr</div>
      </a>

    Args:
        html:     HTML-Quelltext der Spielplan-Seite
        heute:    Aktuelles Datum
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Roh-Dicts (datum, uhrzeit, gast_kuerzel, spieltag, url)
    """
    soup = BeautifulSoup(html, "html.parser")
    karten = soup.select("a.scoreboard-item")
    logger.debug("Spielplan: %d Spielkarten gefunden", len(karten))

    spiele = []
    gesehen: set[str] = set()
    for karte in karten:
        try:
            klassen = karte.get("class") or []
            if "is-home" not in klassen:
                continue

            namen = [n.get_text(strip=True) for n in karte.select(".sb-name")]
            if len(namen) < 2 or namen[0].upper() != HEIM_KUERZEL:
                # Heimteam steht immer links – sonst kein Heimspiel
                continue

            datum_el = karte.select_one(".sb-date")
            datum_text = datum_el.get_text(" ", strip=True) if datum_el else ""
            datum = datum_parsen(datum_text)
            if not datum:
                continue
            datum_obj = date.fromisoformat(datum)
            if datum_obj < heute or datum_obj > enddatum:
                continue

            href = karte.get("href") or ""
            url = urljoin(BASE_URL, href) if href else LISTE_URL
            if url in gesehen:
                continue
            gesehen.add(url)

            spieltag_el = karte.select_one(".sb-gameday")
            spieltag = spieltag_el.get_text(" ", strip=True) if spieltag_el else ""

            spiele.append({
                "datum": datum,
                "uhrzeit": _uhrzeit_aus_datumszeile(datum_text),
                "gast_kuerzel": namen[1],
                "spieltag": spieltag,
                "url": url,
            })
        except Exception as fehler:
            logger.error("Fehler beim Parsen einer Spielkarte: %s", str(fehler))
            continue

    return spiele


def _game_center_auswerten(html: str) -> dict:
    """
    Liest Gegnername, Spielstätte und Ticket-Link aus einer Game-Center-Seite.

    Args:
        html: HTML-Quelltext der Game-Center-Seite

    Returns:
        Dict mit optionalen Schlüsseln gast, spielstaette, ticket_url
    """
    ergebnis: dict = {}
    soup = BeautifulSoup(html, "html.parser")

    teams = [h.get_text(" ", strip=True) for h in soup.select(".gc-match .gc-team h2")]
    if len(teams) >= 2:
        ergebnis["heim"] = teams[0]
        ergebnis["gast"] = teams[1]

    for block in soup.select("dl.gc-match-info > div"):
        label = block.find("dt")
        wert = block.find("dd")
        if not label or not wert:
            continue
        if "spielstätte" in label.get_text(" ", strip=True).lower():
            ergebnis["spielstaette"] = wert.get_text(" ", strip=True)

    ticket = soup.select_one(".gc-actions a.gc-button[href]")
    if ticket:
        ergebnis["ticket_url"] = ticket["href"]

    return ergebnis


async def scrape() -> list[dict]:
    """
    Scrapt DEG Eishockey Heimspiele vom offiziellen Spielplan.

    Returns:
        Liste von Event-Dicts (nur Heimspiele) im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    events: list[dict] = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            html = await _seite_laden(client, LISTE_URL)
            if not html:
                logger.warning("Scraper %s: Spielplan nicht geladen – leere Liste wird zurückgegeben", QUELLE_NAME)
                return []

            spiele = _heimspiele_aus_spielplan(html, heute, enddatum)
            logger.info("Spielplan: %d Heimspiele im Zeitfenster", len(spiele))
            if not spiele:
                logger.warning(
                    "Keine Heimspiele gefunden – evtl. Sommerpause oder geändertes HTML (%s)", LISTE_URL
                )

            for spiel in spiele:
                details: dict = {}
                gc_html = await _seite_laden(client, spiel["url"])
                if gc_html:
                    try:
                        details = _game_center_auswerten(gc_html)
                    except Exception as fehler:
                        logger.error("Game Center nicht auswertbar (%s): %s", spiel["url"], str(fehler))

                gast = details.get("gast") or TEAM_KUERZEL.get(spiel["gast_kuerzel"], spiel["gast_kuerzel"])

                ort = ORT_STANDARD
                adresse = ADRESSE_STANDARD
                spielstaette = details.get("spielstaette", "")
                if spielstaette and "psd bank dome" not in spielstaette.lower():
                    # Heimspiel an anderem Ort (z.B. Freiluftspiel) – echten Ort übernehmen
                    logger.info("Heimspiel nicht im PSD BANK DOME: %s (%s)", spielstaette, spiel["datum"])
                    ort = spielstaette
                    adresse = None

                titel = f"{HEIMTEAM} vs. {gast}"
                beschreibung_teile = ["DEL2-Heimspiel der Düsseldorfer EG"]
                if spiel["spieltag"]:
                    beschreibung_teile.append(spiel["spieltag"])
                beschreibung = _beschreibung_kuerzen(
                    f"{' · '.join(beschreibung_teile)}: {HEIMTEAM} empfängt {gast}."
                )

                events.append({
                    "titel": titel,
                    "datum": spiel["datum"],
                    "uhrzeit": spiel["uhrzeit"],
                    "ort": ort,
                    "adresse": adresse,
                    "kategorie": KATEGORIE,
                    "beschreibung": beschreibung,
                    "preis": PREIS_FALLBACK,
                    "quelle_name": QUELLE_NAME,
                    "quelle_url": spiel["url"],
                    "bild_url": None,
                    "bild_generiert": False,
                    "post_typ": "feed",
                    "instagram_caption": None,
                    "status": "neu",
                })
    except Exception as fehler:
        logger.error("Scraper %s: unerwarteter Fehler: %s", QUELLE_NAME, str(fehler))

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
