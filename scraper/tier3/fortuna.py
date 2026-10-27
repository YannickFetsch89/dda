"""
fortuna.py – DiesDasDüsseldorf
Playwright-Scraper für Fortuna Düsseldorf Heimspiele.

Scrapt nur Heimspiele aus dem offiziellen Spielplan.

Strategie:
1. Primär: JSON-LD structured data (schema.org/SportsEvent)
2. Fallback: HTML-Parsing der Spielplan-Tabelle

URL: https://www.f95.de/spielplan
Adresse: Arena-Straße 1, 40474 Düsseldorf
Erstellt: 2026-03-06
"""
import asyncio
import json
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from playwright.async_api import async_playwright

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import datum_parsen, uhrzeit_parsen

logger = logging.getLogger(__name__)

LISTE_URL = "https://www.f95.de/spielplan"
BASE_URL = "https://www.f95.de"
QUELLE_NAME = "Fortuna Düsseldorf"
ORT_STANDARD = "Merkur Spiel-Arena Düsseldorf"
ADRESSE_STANDARD = "Arena-Straße 1, 40474 Düsseldorf"
KATEGORIE = "sport"
PREIS_FALLBACK = "ab 15€"

# Heimspiel-Identifier – Fortuna spielt immer im eigenen Stadion
HEIMSPIEL_BEGRIFFE = [
    "merkur", "arena", "fortuna", "heimspiel", "home",
    "düsseldorf", "duesseldorf", "f95",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _ist_heimspiel(ort_text: str) -> bool:
    """
    Prüft ob ein Spiel ein Heimspiel ist anhand des Ort-Texts.

    Args:
        ort_text: Ortsbezeichnung aus der Webseite

    Returns:
        True wenn Heimspiel, False wenn Auswärtsspiel
    """
    if not ort_text:
        return True  # Im Zweifel annehmen (wird auf Fortuna-Seite gelistet)
    ort_klein = ort_text.lower()
    return any(begriff in ort_klein for begriff in HEIMSPIEL_BEGRIFFE)


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


def _events_aus_json_ld(html: str, heute: date, enddatum: date) -> list[dict]:
    """
    Extrahiert Heimspiele aus JSON-LD structured data.

    Args:
        html: HTML-Quelltext der Seite
        heute: Aktuelles Datum
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Event-Dicts (nur Heimspiele)
    """
    from bs4 import BeautifulSoup

    events = []
    gesehene_schluessel: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            daten = json.loads(script.string or "{}")
        except (json.JSONDecodeError, AttributeError):
            continue

        eintraege = daten if isinstance(daten, list) else [daten]
        for eintrag in eintraege:
            if not isinstance(eintrag, dict):
                continue
            if eintrag.get("@type") not in ("Event", "SportsEvent", "SoccerGame"):
                continue

            titel = eintrag.get("name", "").strip()
            if not titel:
                continue

            # Heimspiel-Prüfung über Ortsangabe
            ort_roh = eintrag.get("location")
            ort_name = ""
            adresse = ADRESSE_STANDARD
            if isinstance(ort_roh, dict):
                ort_name = ort_roh.get("name", "")
                adresse_roh = ort_roh.get("address")
                if isinstance(adresse_roh, dict):
                    strasse = adresse_roh.get("streetAddress", "")
                    plz = adresse_roh.get("postalCode", "")
                    stadt = adresse_roh.get("addressLocality", "Düsseldorf")
                    adresse = f"{strasse}, {plz} {stadt}".strip(", ") or ADRESSE_STANDARD
                elif isinstance(adresse_roh, str):
                    adresse = adresse_roh
            elif isinstance(ort_roh, str):
                ort_name = ort_roh

            if ort_name and not _ist_heimspiel(ort_name):
                logger.debug("Auswärtsspiel übersprungen: %s (Ort: %s)", titel, ort_name)
                continue

            datum_roh = eintrag.get("startDate") or eintrag.get("startDateTime")
            datum = datum_parsen(str(datum_roh)) if datum_roh else None
            if not datum:
                continue
            datum_obj = date.fromisoformat(datum)
            if datum_obj < heute or datum_obj > enddatum:
                continue

            uhrzeit = uhrzeit_parsen(str(datum_roh))
            url_roh = eintrag.get("url")
            quelle_url = urljoin(BASE_URL, str(url_roh)) if url_roh else LISTE_URL

            beschreibung_roh = eintrag.get("description")
            beschreibung = _beschreibung_kuerzen(str(beschreibung_roh)) if beschreibung_roh else None

            # Preis aus Angeboten
            preis = PREIS_FALLBACK
            angebote = eintrag.get("offers", [])
            if isinstance(angebote, dict):
                angebote = [angebote]
            if angebote:
                preise = [str(a.get("price", "")) for a in angebote if a.get("price")]
                if preise:
                    preis = f"ab {preise[0]}€"

            bild_roh = eintrag.get("image")
            if isinstance(bild_roh, list) and bild_roh:
                bild_roh = bild_roh[0]
            if isinstance(bild_roh, dict):
                bild_url = bild_roh.get("url") or bild_roh.get("contentUrl")
            elif isinstance(bild_roh, str) and bild_roh.startswith("http"):
                bild_url = bild_roh
            else:
                bild_url = None

            schluessel = f"{titel}_{datum}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ORT_STANDARD,
                "adresse": adresse,
                "kategorie": KATEGORIE,
                "beschreibung": beschreibung,
                "preis": preis,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "bild_generiert": False,
                "post_typ": "feed",
                "instagram_caption": None,
                "status": "neu",
            })

    return events


def _events_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """
    Fallback: HTML-Parsing des f95.de Spielplans.

    Struktur im Seitentext (Stand 2026-10):
      "Fr., 30.10.26"
      "- 19:00 Uhr"
      "Fortuna Düsseldorf"   ← Heim
      "30.10.26"              ← Datum-Wiederholung
      "19:00 Uhr"
      "SV Meppen"             ← Gast
      "Tickets sichern"

    Heimspiel = "Fortuna Düsseldorf" direkt nach der Datumszeile.

    Args:
        html: HTML-Quelltext der Seite
        heute: Aktuelles Datum
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Event-Dicts (nur Heimspiele)
    """
    from bs4 import BeautifulSoup

    events = []
    gesehene_schluessel: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)

    zeilen = [z.strip() for z in text.split("\n") if z.strip()]

    datum_muster = re.compile(
        r"^(?:Mo|Di|Mi|Do|Fr|Sa|So)\.,?\s*(\d{1,2})\.(\d{1,2})\.(\d{2,4})\*?$"
    )
    skip_words = {
        "spielbericht", "tickets sichern",
        "3. liga", "-", ":",
    }

    i = 0
    while i < len(zeilen):
        treffer = datum_muster.match(zeilen[i])
        if not treffer:
            i += 1
            continue

        tag = int(treffer.group(1))
        monat = int(treffer.group(2))
        jahr_roh = int(treffer.group(3))
        jahr = jahr_roh if jahr_roh > 100 else 2000 + jahr_roh

        try:
            datum_obj = date(jahr, monat, tag)
        except ValueError:
            i += 1
            continue

        if datum_obj < heute or datum_obj > enddatum:
            i += 1
            continue

        uhrzeit = None
        for k in range(i + 1, min(len(zeilen), i + 4)):
            zeit_match = re.search(r"(\d{1,2}):(\d{2})\s*Uhr", zeilen[k])
            if zeit_match:
                uhrzeit = f"{int(zeit_match.group(1)):02d}:{zeit_match.group(2)}"
                break

        heim = None
        gast = None
        for j in range(i + 1, min(len(zeilen), i + 10)):
            z = zeilen[j]
            z_lower = z.lower().strip()
            if z_lower in skip_words:
                continue
            if re.match(r"^\d+\.\s*spieltag$", z_lower):
                break
            if datum_muster.match(z):
                break
            if re.match(r"^\d{1,2}\.\d{1,2}\.\d{2,4}\*?$", z):
                continue
            if re.match(r"^\d{1,2}:\d{2}", z):
                continue
            if re.match(r"^\d+$", z):
                continue
            if "uhr" in z_lower:
                continue

            if not heim:
                heim = z
            elif not gast:
                gast = z
                break

        if not heim or not gast:
            i += 1
            continue

        if heim.lower() != "fortuna düsseldorf":
            i += 1
            continue

        titel = f"Fortuna Düsseldorf vs. {gast}"

        schluessel = f"{titel}_{datum_obj.isoformat()}"
        if schluessel in gesehene_schluessel:
            i += 1
            continue
        gesehene_schluessel.add(schluessel)

        events.append({
            "titel": titel,
            "datum": datum_obj.isoformat(),
            "uhrzeit": uhrzeit,
            "ort": ORT_STANDARD,
            "adresse": ADRESSE_STANDARD,
            "kategorie": KATEGORIE,
            "beschreibung": None,
            "preis": PREIS_FALLBACK,
            "quelle_name": QUELLE_NAME,
            "quelle_url": LISTE_URL,
            "bild_url": None,
            "bild_generiert": False,
            "post_typ": "feed",
            "instagram_caption": None,
            "status": "neu",
        })

        i += 1

    return events


async def scrape() -> list[dict]:
    """
    Scrapt Fortuna Düsseldorf Heimspiele vom offiziellen Spielplan.

    Strategie:
    1. JSON-LD structured data
    2. HTML-Fallback

    Returns:
        Liste von Event-Dicts (nur Heimspiele) im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    html = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers({"User-Agent": USER_AGENT})
            try:
                await page.goto(LISTE_URL, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                html = await page.content()
            except Exception as fehler:
                logger.error("Playwright Fehler beim Laden von %s: %s", LISTE_URL, str(fehler))
            finally:
                await browser.close()
    except Exception as fehler:
        logger.error("Scraper %s: Playwright konnte nicht gestartet werden: %s", QUELLE_NAME, str(fehler))

    if not html:
        logger.warning("Scraper %s: Kein HTML geladen – leere Liste wird zurückgegeben", QUELLE_NAME)
        return []

    events = _events_aus_json_ld(html, heute, enddatum)
    logger.info("JSON-LD: %d Heimspiele gefunden", len(events))

    if not events:
        logger.warning("JSON-LD leer – versuche HTML-Fallback")
        events = _events_aus_html(html, heute, enddatum)
        logger.info("HTML-Fallback: %d Heimspiele gefunden", len(events))

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
