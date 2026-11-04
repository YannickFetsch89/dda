"""
startupdorf.py – DiesDasDüsseldorf
Playwright-Scraper für StartupDorf Meetup-Events.

Scrapt öffentliche Community-Events der StartupDorf-Gruppe auf Meetup.com.
StartupDorf ist die wichtigste Startup- und Tech-Community in Düsseldorf.

Hinweis: Die Meetup API ist kostenpflichtig – daher wird die öffentliche
Meetup-Webseite gescrapt.

Strategie (seit 2026-11 angepasst):
1. Seite per httpx laden (Meetup rendert serverseitig, kein JS nötig);
   Playwright nur noch als Fallback (wait_until="domcontentloaded" –
   "networkidle" wird bei Meetup wegen Dauer-Tracking-Requests oft nie
   erreicht und lief in CI in den Timeout).
2. Primär: __NEXT_DATA__ → __APOLLO_STATE__ (Event-, Venue-, PhotoInfo-Objekte).
   Meetup liefert im JSON-LD seit Herbst 2026 keine Events mehr, nur noch
   Organization/BreadcrumbList.
3. Fallback: JSON-LD structured data (schema.org/Event)
4. Fallback: HTML-Parsing der Event-Liste

URL: https://www.meetup.com/startupdorf/events/
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
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

LISTE_URL = "https://www.meetup.com/startupdorf/events/"
BASE_URL = "https://www.meetup.com"
QUELLE_NAME = "StartupDorf Meetup"
ORT_STANDARD = "Düsseldorf"
ADRESSE_STANDARD = None
KATEGORIE = "community"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


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


def _ort_aus_location(location_daten: dict | None) -> tuple[str, str | None]:
    """
    Extrahiert Ort und Adresse aus einem Meetup location-Objekt.

    Args:
        location_daten: location-Dict aus JSON-LD oder None

    Returns:
        Tuple aus (ort, adresse) – ort ist nie None
    """
    if not isinstance(location_daten, dict):
        return ORT_STANDARD, ADRESSE_STANDARD

    ort = location_daten.get("name") or ORT_STANDARD
    adresse_obj = location_daten.get("address")
    adresse = ADRESSE_STANDARD

    if isinstance(adresse_obj, dict):
        strasse = adresse_obj.get("streetAddress", "")
        plz = adresse_obj.get("postalCode", "")
        stadt = adresse_obj.get("addressLocality", "")
        adresse_teile = [t for t in [strasse, plz, stadt] if t]
        adresse = ", ".join(adresse_teile) if adresse_teile else ADRESSE_STANDARD
    elif isinstance(adresse_obj, str) and adresse_obj:
        adresse = adresse_obj

    return ort, adresse


def _markdown_bereinigen(text: str) -> str:
    """
    Entfernt gängige Markdown-Auszeichnungen aus Meetup-Beschreibungen.

    Args:
        text: Beschreibung im Meetup-Markdown-Format

    Returns:
        Reiner Text ohne Links-Syntax, Überschriften- und Fett-Markierungen
    """
    if not text:
        return ""
    # Links [Text](URL) → Text
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Überschriften, Fett/Kursiv, Escape-Backslashes
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    text = text.replace("**", "").replace("__", "").replace("\\", "")
    text = re.sub(r"(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)", "", text)
    return text


def _apollo_aufloesen(apollo: dict, wert) -> Optional[dict]:
    """
    Löst eine Apollo-Cache-Referenz ({"__ref": "Typ:ID"}) auf.

    Args:
        apollo: Kompletter __APOLLO_STATE__-Cache
        wert:   Referenz-Dict, bereits aufgelöstes Objekt oder None

    Returns:
        Aufgelöstes Objekt oder None
    """
    if isinstance(wert, dict):
        ref = wert.get("__ref")
        if ref:
            aufgeloest = apollo.get(ref)
            return aufgeloest if isinstance(aufgeloest, dict) else None
        return wert
    return None


def _events_aus_apollo(html: str, heute: date, enddatum: date) -> list[dict]:
    """
    Extrahiert Events aus dem Next.js-Apollo-Cache (__NEXT_DATA__).

    Meetup bettet alle Gruppen-Events (kommende und vergangene) als
    "Event:<id>"-Objekte im __APOLLO_STATE__ ein. Venue und Bild sind
    über __ref-Verweise verknüpft.

    Args:
        html: HTML-Quelltext der Seite
        heute: Aktuelles Datum
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Event-Dicts
    """
    from bs4 import BeautifulSoup

    events: list[dict] = []
    soup = BeautifulSoup(html, "html.parser")
    skript = soup.find("script", id="__NEXT_DATA__")
    if not skript or not skript.string:
        logger.warning("Kein __NEXT_DATA__ im HTML gefunden")
        return events

    try:
        daten = json.loads(skript.string)
        apollo = daten["props"]["pageProps"]["__APOLLO_STATE__"]
    except (json.JSONDecodeError, KeyError, TypeError) as fehler:
        logger.warning("__APOLLO_STATE__ nicht lesbar: %s", str(fehler))
        return events

    if not isinstance(apollo, dict):
        return events

    gesehene_ids: set[str] = set()
    for schluessel, eintrag in apollo.items():
        if not schluessel.startswith("Event:") or not isinstance(eintrag, dict):
            continue
        try:
            event_id = str(eintrag.get("id") or schluessel)
            if event_id in gesehene_ids:
                continue

            # Nur aktive Events (keine abgesagten / vergangenen / Entwürfe)
            status = str(eintrag.get("status") or "").upper()
            if status and status not in ("ACTIVE", "UPCOMING"):
                continue

            titel = str(eintrag.get("title") or "").strip()
            if not titel:
                continue

            datum_roh = str(eintrag.get("dateTime") or "")
            datum = datum_parsen(datum_roh) if datum_roh else None
            if not datum:
                continue
            datum_obj = date.fromisoformat(datum)
            if datum_obj < heute or datum_obj > enddatum:
                continue
            uhrzeit = uhrzeit_parsen(datum_roh)

            # Ort und Adresse aus verknüpfter Venue
            ort = ORT_STANDARD
            adresse = ADRESSE_STANDARD
            if eintrag.get("isOnline") or str(eintrag.get("eventType") or "").upper() == "ONLINE":
                ort = "Online"
            else:
                venue = _apollo_aufloesen(apollo, eintrag.get("venue"))
                if venue:
                    ort = (venue.get("name") or ORT_STANDARD).strip()
                    adresse_roh = (venue.get("address") or "").strip()
                    stadt = (venue.get("city") or "").strip()
                    if adresse_roh and stadt and stadt.lower() not in adresse_roh.lower():
                        adresse = f"{adresse_roh}, {stadt}"
                    else:
                        adresse = adresse_roh or ADRESSE_STANDARD

            # Bild (featuredEventPhoto bzw. displayPhoto)
            bild_url = None
            foto = (
                _apollo_aufloesen(apollo, eintrag.get("featuredEventPhoto"))
                or _apollo_aufloesen(apollo, eintrag.get("displayPhoto"))
            )
            if foto:
                kandidat = foto.get("highResUrl") or foto.get("standardUrl")
                if isinstance(kandidat, str) and kandidat.startswith("http"):
                    bild_url = kandidat

            beschreibung_roh = eintrag.get("description")
            beschreibung = (
                _beschreibung_kuerzen(_markdown_bereinigen(str(beschreibung_roh)))
                if beschreibung_roh else None
            ) or None

            url_roh = eintrag.get("eventUrl")
            quelle_url = urljoin(BASE_URL, str(url_roh)) if url_roh else LISTE_URL

            gesehene_ids.add(event_id)
            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ort,
                "adresse": adresse,
                "kategorie": KATEGORIE,
                "beschreibung": beschreibung,
                "preis": None,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "bild_generiert": False,
                "post_typ": "feed",
                "instagram_caption": None,
                "instagram_location_id": None,
                "status": "neu",
            })
        except Exception as fehler:
            logger.error("Fehler beim Parsen eines Apollo-Events (%s): %s", schluessel, str(fehler))
            continue

    events.sort(key=lambda e: (e["datum"], e["uhrzeit"] or ""))
    return events


def _events_aus_json_ld(html: str, heute: date, enddatum: date) -> list[dict]:
    """
    Extrahiert Events aus JSON-LD structured data.

    Meetup.com bettet Events als schema.org/Event in JSON-LD ein –
    das ist die zuverlässigste Extraktionsmethode.

    Args:
        html: HTML-Quelltext der Seite
        heute: Aktuelles Datum
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Event-Dicts
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
            if eintrag.get("@type") not in ("Event", "SocialEvent", "EducationEvent", "BusinessEvent"):
                continue

            titel = eintrag.get("name", "").strip()
            if not titel:
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

            bild_roh = eintrag.get("image")
            if isinstance(bild_roh, list) and bild_roh:
                bild_roh = bild_roh[0]
            if isinstance(bild_roh, dict):
                bild_url = bild_roh.get("url") or bild_roh.get("contentUrl")
            elif isinstance(bild_roh, str) and bild_roh.startswith("http"):
                bild_url = bild_roh
            else:
                bild_url = None

            # Ort aus Event-Details extrahieren, Fallback: Düsseldorf
            ort, adresse = _ort_aus_location(eintrag.get("location"))

            # Preis aus Angeboten extrahieren
            preis = None
            angebote = eintrag.get("offers", [])
            if isinstance(angebote, dict):
                angebote = [angebote]
            if angebote:
                preise = [str(a.get("price", "")) for a in angebote if a.get("price")]
                if preise:
                    preis = f"ab {preise[0]}€"

            schluessel = f"{titel}_{datum}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ort,
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
                "instagram_location_id": None,
                "status": "neu",
            })

    return events


def _events_aus_html(html: str, heute: date, enddatum: date) -> list[dict]:
    """
    Fallback: HTML-Parsing der Meetup-Event-Liste.

    Args:
        html: HTML-Quelltext der Seite
        heute: Aktuelles Datum
        enddatum: Maximales Datum für Events

    Returns:
        Liste von Event-Dicts
    """
    from bs4 import BeautifulSoup

    events = []
    gesehene_schluessel: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")

    # Meetup-typische CSS-Selektoren und allgemeine Fallbacks
    selektoren = [
        "[data-testid='event-card']", "[data-testid='event-item']",
        ".eventCard", ".event-listing", ".event-item",
        "article[class*='event']", "div[class*='event']",
        "li[class*='event']", ".groupEventListItem",
        ".list-item", "article", "li",
    ]

    karten = []
    for selektor in selektoren:
        karten = soup.select(selektor)
        if len(karten) > 1:
            logger.debug("HTML-Fallback: %d Karten mit Selektor '%s'", len(karten), selektor)
            break

    for karte in karten:
        try:
            titel_el = karte.find(["h2", "h3", "h4", "strong"])
            if not titel_el:
                continue
            titel = titel_el.get_text(strip=True)
            if not titel or len(titel) < 3:
                continue

            datum_el = karte.find("time") or karte.find(class_=re.compile(r"date|datum|zeit|time", re.I))
            if not datum_el:
                continue
            datum_text = datum_el.get("datetime") or datum_el.get_text(strip=True)
            datum = datum_parsen(datum_text)
            if not datum:
                continue
            datum_obj = date.fromisoformat(datum)
            if datum_obj < heute or datum_obj > enddatum:
                continue

            uhrzeit = uhrzeit_parsen(datum_text)

            link_el = karte.find("a", href=True)
            quelle_url = urljoin(BASE_URL, link_el["href"]) if link_el else LISTE_URL

            bild_el = karte.find("img")
            bild_url = None
            if bild_el:
                bild_url = bild_el.get("data-src") or bild_el.get("src")
                if bild_url and bild_url.startswith("/"):
                    bild_url = urljoin(BASE_URL, bild_url)
                if bild_url and not bild_url.startswith("http"):
                    bild_url = None

            beschreibung_el = karte.find("p")
            beschreibung = _beschreibung_kuerzen(beschreibung_el.get_text(strip=True)) if beschreibung_el else None

            schluessel = f"{titel}_{datum}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ORT_STANDARD,
                "adresse": ADRESSE_STANDARD,
                "kategorie": KATEGORIE,
                "beschreibung": beschreibung,
                "preis": None,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "bild_generiert": False,
                "post_typ": "feed",
                "instagram_caption": None,
                "instagram_location_id": None,
                "status": "neu",
            })

        except Exception as fehler:
            logger.error("Fehler beim Parsen einer Event-Karte: %s", str(fehler))
            continue

    return events


async def _html_mit_playwright() -> Optional[str]:
    """
    Fallback: Lädt die Gruppen-Eventseite mit Playwright (headless Chromium).

    Wartet nur auf "domcontentloaded" und das __NEXT_DATA__-Skript –
    "networkidle" wird bei Meetup durch Tracking-Requests häufig nie erreicht.

    Returns:
        HTML-Quelltext oder None bei Fehler
    """
    html = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(user_agent=USER_AGENT, locale="de-DE")
                await asyncio.sleep(2)  # Rate Limiting
                await page.goto(LISTE_URL, wait_until="domcontentloaded", timeout=45000)
                try:
                    await page.wait_for_selector(
                        "script#__NEXT_DATA__", state="attached", timeout=15000
                    )
                except Exception:
                    logger.warning("__NEXT_DATA__ nicht erschienen – verwende aktuellen DOM-Stand")
                html = await page.content()
            except Exception as fehler:
                logger.error("Playwright Fehler beim Laden von %s: %s", LISTE_URL, str(fehler))
            finally:
                await browser.close()
    except Exception as fehler:
        logger.error("Scraper %s: Playwright konnte nicht gestartet werden: %s", QUELLE_NAME, str(fehler))
    return html


async def scrape() -> list[dict]:
    """
    Scrapt öffentliche Events der StartupDorf-Gruppe auf Meetup.com.

    Die Meetup API ist kostenpflichtig und wird daher nicht genutzt.

    Strategie:
    1. HTML per httpx (serverseitig gerendert), Playwright nur als Fallback
    2. __APOLLO_STATE__ aus __NEXT_DATA__ (bevorzugt)
    3. JSON-LD structured data
    4. HTML-Fallback

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    html = None
    try:
        # seite_abrufen ist synchron (inkl. 2 s Rate Limiting) → im Thread ausführen
        html = await asyncio.to_thread(seite_abrufen, LISTE_URL, logger)
    except Exception as fehler:
        logger.error("httpx-Abruf von %s fehlgeschlagen: %s", LISTE_URL, str(fehler))

    if not html or "__NEXT_DATA__" not in html:
        logger.warning("httpx lieferte kein verwertbares HTML – versuche Playwright")
        html = await _html_mit_playwright() or html

    if not html:
        logger.warning("Scraper %s: Kein HTML geladen – leere Liste wird zurückgegeben", QUELLE_NAME)
        return []

    events = _events_aus_apollo(html, heute, enddatum)
    logger.info("Apollo-State: %d Events gefunden", len(events))

    if not events:
        events = _events_aus_json_ld(html, heute, enddatum)
        logger.info("JSON-LD: %d Events gefunden", len(events))

    if not events:
        logger.warning("JSON-LD leer – versuche HTML-Fallback")
        events = _events_aus_html(html, heute, enddatum)
        logger.info("HTML-Fallback: %d Events gefunden", len(events))

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
