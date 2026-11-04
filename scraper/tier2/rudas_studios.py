"""
rudas_studios.py – DiesDasDüsseldorf
Scraper für den Club Rudas Studios Düsseldorf (Medienhafen).

Hintergrund (Stand 2026-11-04):
Die alte Domain rudas-studios.de zeigt nur noch eine IONOS-Platzhalterseite
("Diese Domain ist bereits registriert"), www.rudas-studios.de existiert im
DNS nicht mehr. Der Club ist auf https://rudas-studios.com umgezogen.
Dort gibt es kein JSON-LD; Tickets laufen über einen eingebetteten
stagedates.com-Shop (Veranstalter-ID siehe STAGEDATES_PROMOTER_ID).

Strategie (alle Quellen werden kombiniert, Duplikate pro Datum entfernt –
ein Club hat i.d.R. ein Event pro Nacht):
1. stagedates.com JSON-API des Ticketshops (strukturiert, mit Uhrzeit/Preis)
2. Resident Advisor (Venue-ID 26232) über den gemeinsamen RA-Helfer
3. Statische Partyreihen-Liste auf rudas-studios.com/events/
   (Elementor, Format "07 NOV" + Überschrift, ohne Jahr)

robots.txt: rudas-studios.com und stagedates.com erlauben alles.

URL: https://rudas-studios.com
Adresse: Zollhof 11, 40221 Düsseldorf
Erstellt: 2026-03-05
Überarbeitet: 2026-11-04 (Domain-Umzug, stagedates-API + RA statt JSON-LD)
"""
import json
import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.datum import MONAT_KURZ_MAP
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ra_venue import ra_venue_scrapen

logger = logging.getLogger(__name__)

BASE_URL = "https://rudas-studios.com"
LISTE_URL = "https://rudas-studios.com/events/"
QUELLE_NAME = "Rudas Studios Düsseldorf"
ORT_STANDARD = "Rudas Studios Düsseldorf"
ADRESSE_STANDARD = "Zollhof 11, 40221 Düsseldorf"

# stagedates-Ticketshop (aus dem iframe auf rudas-studios.com/events/)
STAGEDATES_PROMOTER_ID = "5a026a2a-5af3-43df-b779-8d6d264b268f"
STAGEDATES_API_URL = (
    "https://stagedates.com/events/api/events"
    f"?promoterId={STAGEDATES_PROMOTER_ID}&size=100"
)
STAGEDATES_EVENT_URL = "https://stagedates.com/events/{slug}-{code}"

# Resident Advisor Venue-ID der Rudas Studios
RA_VENUE_ID = 26232

KATEGORIE_STANDARD = "nightlife"  # Rudas Studios ist ein Club


def _leeres_event(titel: str, datum: str) -> dict:
    """
    Erzeugt ein Event-Dict mit Standardwerten für die Rudas Studios.

    Args:
        titel: Event-Titel
        datum: ISO-Datum (YYYY-MM-DD)

    Returns:
        Event-Dict im DiesDasDüsseldorf-Format
    """
    return {
        "titel": titel,
        "datum": datum,
        "uhrzeit": None,
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": KATEGORIE_STANDARD,
        "beschreibung": None,
        "preis": None,
        "quelle_name": QUELLE_NAME,
        "quelle_url": LISTE_URL,
        "bild_url": None,
        "instagram_caption": None,
        "datum_bis": None,
        "ist_wiederkehrend": False,
        "status": "neu",
    }


def _lokale_zeit(utc_text: str, zeitzone: Optional[dict]) -> Optional[datetime]:
    """
    Wandelt einen UTC-Zeitstempel von stagedates in Düsseldorfer Ortszeit um.

    Primär über zoneinfo (Europe/Berlin), Fallback über die von der API
    mitgelieferten Offsets (rawOffset + dstOffset in Sekunden).

    Args:
        utc_text: z.B. "2026-11-07T21:30:00Z"
        zeitzone: Timezone-Objekt der API (optional)

    Returns:
        Lokales datetime oder None
    """
    try:
        zeitpunkt = datetime.fromisoformat(utc_text.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    if zeitpunkt.tzinfo is None:
        zeitpunkt = zeitpunkt.replace(tzinfo=timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        return zeitpunkt.astimezone(ZoneInfo("Europe/Berlin"))
    except Exception:
        versatz = 3600
        if isinstance(zeitzone, dict):
            versatz = int(zeitzone.get("rawOffset") or 0) + int(zeitzone.get("dstOffset") or 0)
        return zeitpunkt.astimezone(timezone(timedelta(seconds=versatz)))


def _preis_formatieren(betrag: Optional[str]) -> Optional[str]:
    """
    Formatiert einen Preis-String ("15.00") als "ab 15€" bzw. "ab 15,50€".

    Args:
        betrag: Betrag als String oder Zahl

    Returns:
        Preis-String oder None
    """
    try:
        wert = float(betrag)
    except (TypeError, ValueError):
        return None
    if wert <= 0:
        return None
    if wert.is_integer():
        return f"ab {int(wert)}€"
    return f"ab {wert:.2f}€".replace(".", ",")


def _events_aus_stagedates(heute: date, enddatum: date) -> list[dict]:
    """
    Quelle 1: Events aus der JSON-API des stagedates-Ticketshops.

    Args:
        heute:    Untere Datumsgrenze
        enddatum: Obere Datumsgrenze

    Returns:
        Liste von Event-Dicts
    """
    antwort = seite_abrufen(STAGEDATES_API_URL, logger)
    if antwort is None:
        logger.warning("Rudas: stagedates-API nicht erreichbar")
        return []
    try:
        daten = json.loads(antwort)
    except json.JSONDecodeError:
        logger.error("Rudas: stagedates-Antwort ist kein gültiges JSON")
        return []
    if isinstance(daten, dict):
        daten = daten.get("data") or daten.get("events") or []
    if not isinstance(daten, list):
        logger.error("Rudas: unerwartetes stagedates-Format (%s)", type(daten).__name__)
        return []

    events = []
    for eintrag in daten:
        try:
            if not isinstance(eintrag, dict) or eintrag.get("isDraft"):
                continue
            if "cancel" in str(eintrag.get("salesStatus") or "").lower():
                continue
            titel = (eintrag.get("title") or "").strip()
            start = _lokale_zeit(eintrag.get("startDate") or "", eintrag.get("timezone"))
            if not titel or start is None:
                continue
            datum_obj = start.date()
            if datum_obj < heute or datum_obj > enddatum:
                continue

            event = _leeres_event(titel, datum_obj.isoformat())
            event["uhrzeit"] = start.strftime("%H:%M")

            slug = eintrag.get("slug")
            code = eintrag.get("shortCode")
            if slug and code:
                event["quelle_url"] = STAGEDATES_EVENT_URL.format(slug=slug, code=code)
            event["bild_url"] = eintrag.get("coverUrl") or eintrag.get("thumbnailUrl") or None
            event["preis"] = _preis_formatieren(
                (eintrag.get("cheapestPriceMny") or {}).get("amount")
            )

            # Untertitel nur übernehmen, wenn er nicht bloß Datum/Ort wiederholt
            untertitel = (eintrag.get("subtitle") or "").strip()
            teile = []
            if untertitel and not re.search(r"\d{1,2}\.\s*[A-Za-zÄÖÜäöü]{3}", untertitel):
                teile.append(untertitel)
            if eintrag.get("minimumAge"):
                teile.append(f"Einlass ab {eintrag['minimumAge']} Jahren.")
            event["beschreibung"] = " – ".join(teile)[:300] or None

            # Falls der Veranstalter woanders feiert: tatsächlichen Ort übernehmen
            venue = eintrag.get("venue") or {}
            venue_name = (venue.get("name") or "").strip()
            if venue_name and "rudas" not in venue_name.lower():
                event["ort"] = venue_name
                strasse = " ".join(
                    x for x in (venue.get("street"), venue.get("houseNumber")) if x
                )
                stadt = " ".join(x for x in (venue.get("zipCode"), venue.get("city")) if x)
                event["adresse"] = ", ".join(x for x in (strasse, stadt) if x) or None

            events.append(event)
        except Exception as fehler:
            logger.error("Rudas: Fehler bei stagedates-Event: %s", fehler)
            continue
    return events


def _events_aus_webseite(heute: date, enddatum: date) -> list[dict]:
    """
    Quelle 3: Partyreihen-Liste auf rudas-studios.com/events/.

    Die Seite wird manuell gepflegt (Elementor) und zeigt Einträge wie
    "<p>07 NOV</p><h2>OLDSKOOL</h2>" ohne Jahresangabe. Das Jahr wird als
    nächstes passendes Datum ab heute ermittelt.

    Args:
        heute:    Untere Datumsgrenze
        enddatum: Obere Datumsgrenze

    Returns:
        Liste von Event-Dicts
    """
    html = seite_abrufen(LISTE_URL, logger)
    if html is None:
        logger.warning("Rudas: Event-Seite %s nicht erreichbar", LISTE_URL)
        return []

    soup = BeautifulSoup(html, "html.parser")
    events = []
    for spalte in soup.select(".elementor-column"):
        try:
            # Nur innerste Spalten mit genau einem Datum + einer Überschrift
            if spalte.select(".elementor-column"):
                continue
            datum_el = None
            for p in spalte.find_all("p"):
                if re.fullmatch(r"\s*\d{1,2}\.?\s+[A-Za-zÄÖÜäöü]{3}\.?\s*", p.get_text()):
                    datum_el = p
                    break
            titel_el = spalte.find(["h2", "h3"])
            if not datum_el or not titel_el:
                continue

            treffer = re.match(r"\s*(\d{1,2})\.?\s+([A-Za-zÄÖÜäöü]{3})", datum_el.get_text())
            monat = MONAT_KURZ_MAP.get(treffer.group(2).lower()) if treffer else None
            if not monat:
                continue
            tag = int(treffer.group(1))
            try:
                kandidat = date(heute.year, monat, tag)
                if kandidat < heute:
                    kandidat = date(heute.year + 1, monat, tag)
            except ValueError:
                continue
            if kandidat > enddatum:
                continue

            titel = re.sub(r"\s+", " ", titel_el.get_text(" ")).strip()
            if len(titel) < 3:
                continue
            events.append(_leeres_event(titel, kandidat.isoformat()))
        except Exception as fehler:
            logger.error("Rudas: Fehler beim Parsen der Partyreihen-Liste: %s", fehler)
            continue
    return events


def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen der Rudas Studios Düsseldorf.

    Kombiniert stagedates-Ticketshop, Resident Advisor und die Partyreihen-
    Liste der Website. Pro Datum wird nur ein Event behalten (Priorität in
    dieser Reihenfolge, da stagedates die vollständigsten Daten liefert).

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    quellen: list[tuple[str, list[dict]]] = []

    try:
        quellen.append(("stagedates", _events_aus_stagedates(heute, enddatum)))
    except Exception as fehler:
        logger.error("Rudas: stagedates-Abruf fehlgeschlagen: %s", fehler)

    try:
        ra_events = ra_venue_scrapen(
            quelle_name=QUELLE_NAME,
            ort_standard=ORT_STANDARD,
            adresse_standard=ADRESSE_STANDARD,
            ra_venue_id=RA_VENUE_ID,
            kategorie=KATEGORIE_STANDARD,
        )
        quellen.append(("Resident Advisor", ra_events))
    except Exception as fehler:
        logger.error("Rudas: RA-Abruf fehlgeschlagen: %s", fehler)

    try:
        quellen.append(("Website", _events_aus_webseite(heute, enddatum)))
    except Exception as fehler:
        logger.error("Rudas: Website-Abruf fehlgeschlagen: %s", fehler)

    events: list[dict] = []
    belegte_tage: set[str] = set()
    for name, liste in quellen:
        neu = 0
        for event in liste:
            datum = event.get("datum")
            if not datum or not event.get("titel"):
                continue
            if not (heute <= date.fromisoformat(datum) <= enddatum):
                continue
            if datum in belegte_tage:
                logger.debug("Rudas: '%s' (%s) bereits aus anderer Quelle vorhanden", event["titel"], datum)
                continue
            belegte_tage.add(datum)
            events.append(event)
            neu += 1
        logger.info("Rudas %s: %d Events gefunden, %d neu übernommen", name, len(liste), neu)

    events.sort(key=lambda e: (e["datum"], e.get("uhrzeit") or ""))
    logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:5]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
