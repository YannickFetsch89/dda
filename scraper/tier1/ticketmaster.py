"""
ticketmaster.py – DiesDasDüsseldorf
Scraper für die Ticketmaster Discovery API: Events in Düsseldorf und Umgebung (Neuss, Ratingen).
Erstellt: 2026-02-24

Seit Schritt T1 (Plan docs/plan-quellen-ausbau-2026-11-23.md, 5.1):
- Abfrage je Kalendermonat bis zum Zeitraum der Quelle (config.vorschau_ende, 365 Tage), Umkreis 25 km um
  Düsseldorf (geoPoint), je Monat geblättert. Die API liefert je Abfrage höchstens 1.000 Treffer (size × page < 1000).
  Den Rest (Köln …) entfernt pipeline/gebiet.py.
- Mindestens 2 s zwischen Anfragen (Projektregel; die API erlaubt bis zu 5.000 Abfragen am Tag).
- Bilder nur mit GitHub-Variable TICKETMASTER_BILDER_OK=1: Die API-Bedingungen verbieten, Ticketmaster als Bild-Host
  zu nutzen; bis die schriftliche Bestätigung die Bildnutzung einschließt (docs/partner-anfragen-2026-11-24.md),
  bleibt bild_url leer (Plan 5.5.4).
"""
import logging
import re
import os
import time
from datetime import date, timedelta
from typing import Optional

import httpx

from config import vorschau_ende

logger = logging.getLogger(__name__)

QUELLE_NAME = "Ticketmaster"
API_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
# Mittelpunkt Düsseldorf als Geohash (51.2277, 6.7735) und Umkreis
GEOPUNKT = "u1hg6jsq"
RADIUS_KM = 25
# Seitengröße (API-Höchstwert 200) und Grenze der API: size × page < 1000
SEITENGROESSE = 200
MAX_TREFFER_JE_ABFRAGE = 1000
WARTEZEIT = 2.0
# So viele fehlgeschlagene Monatsfenster in Folge beenden den Abruf (API gestört – sonst kostet jedes Fenster
# drei Versuche mit Timeout)
ABBRUCH_NACH_FEHLERN = 3

# Mapping Ticketmaster-Segmente → DiesDasDüsseldorf-Kategorien
KATEGORIE_MAPPING = {
    "music": "musik",
    "sports": "sport",
    "arts & theatre": "kultur",
    "film": "kultur",
    "miscellaneous": "sonstiges",
    "family": "family",
}


def _bild_url_ermitteln(images: list[dict]) -> Optional[str]:
    """
    Wählt die beste Bild-URL aus der Ticketmaster-Bilderliste aus.
    Bevorzugt wird ein 16:9-Bild mit mindestens 640px Breite.
    Fallback: erstes verfügbares Bild.

    Args:
        images: Liste von Bild-Dicts aus der Ticketmaster-Antwort

    Returns:
        Bild-URL als String oder None wenn keine Bilder vorhanden
    """
    if not images:
        return None

    # Bevorzugtes Bild: Verhältnis 16_9, mindestens 640px Breite
    for bild in images:
        ratio = bild.get("ratio", "")
        breite = bild.get("width", 0)
        url = bild.get("url")
        if ratio == "16_9" and breite >= 640 and url:
            return url

    # Fallback: erstes verfügbares Bild
    return images[0].get("url") if images[0].get("url") else None


def _preis_formatieren(preis_bereiche: list[dict]) -> Optional[str]:
    """
    Formatiert Preisangaben aus der Ticketmaster-Antwort.
    Beispiele: "ab 25€" (wenn min==max), "25€ – 80€" (bei Preisspanne).

    Args:
        preis_bereiche: Liste von Preisbereich-Dicts aus der Ticketmaster-Antwort

    Returns:
        Formatierter Preisstring oder None wenn keine Preisinfo vorhanden
    """
    if not preis_bereiche:
        return None

    try:
        eintrag = preis_bereiche[0]
        min_preis = eintrag.get("min")
        max_preis = eintrag.get("max")

        if min_preis is None:
            return None

        # Preiswerte als ganze Zahlen formatieren wenn keine Nachkommastellen
        def preis_str(wert: float) -> str:
            if wert == int(wert):
                return f"{int(wert)}€"
            return f"{wert:.2f}€"

        if max_preis is None or min_preis == max_preis:
            return f"ab {preis_str(min_preis)}"

        return f"{preis_str(min_preis)} – {preis_str(max_preis)}"

    except (KeyError, TypeError, ValueError) as e:
        logger.warning("Preis konnte nicht formatiert werden: %s", e)
        return None


def _kategorie_erkennen(klassifizierungen: list[dict]) -> str:
    """
    Mappt Ticketmaster-Klassifizierungen auf DiesDasDüsseldorf-Kategorien.

    Args:
        klassifizierungen: Liste von Klassifizierungs-Dicts aus der API-Antwort

    Returns:
        Gültige DiesDasDüsseldorf-Kategorie
    """
    if not klassifizierungen:
        return "sonstiges"

    try:
        segment = klassifizierungen[0].get("segment", {})
        segment_name = segment.get("name", "").lower()
        return KATEGORIE_MAPPING.get(segment_name, "sonstiges")
    except (IndexError, AttributeError, KeyError):
        return "sonstiges"


_ZUSATZANGEBOT = re.compile(
    r"vip[- ]?(upgrade|package|paket|ticket upgrade)|no ticket included|kein ticket|ohne ticket|parkplatz|parking|"
    r"\bparken\b|hotel ?package|merch(andise)? ?bundle", re.IGNORECASE)


def _im_gebiet(stadt: str) -> bool:
    """Liegt die Stadt des Veranstaltungsorts in Düsseldorf, Neuss oder Ratingen? (ganzes Wort)"""
    from pipeline.gebiet import stadt_im_gebiet
    return stadt_im_gebiet(stadt)


def _event_parsen(event: dict, heute: date) -> Optional[dict]:
    """
    Wandelt ein Ticketmaster-API-Event in ein DiesDasDüsseldorf Event-Dict um.

    Args:
        event: Rohes Event-Dict aus der Ticketmaster Discovery API
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict im DiesDasDüsseldorf-Format oder None bei fehlenden Pflichtfeldern
        bzw. wenn das Event in der Vergangenheit liegt
    """
    try:
        # Titel (Pflichtfeld)
        titel = event.get("name", "").strip()
        if not titel:
            logger.warning("Event ohne Titel übersprungen.")
            return None

        # Zusatzangebote ohne eigenen Termin (Test 24.11.2026: „… | VIP Upgrades (no ticket included)“) – kein Event
        if _ZUSATZANGEBOT.search(titel):
            logger.debug("Ticketmaster: Zusatzangebot übersprungen: %s", titel)
            return None

        # Datum (Pflichtfeld)
        datum_info = event.get("dates", {}).get("start", {})
        datum = datum_info.get("localDate")
        if not datum:
            logger.warning("Kein Datum für Event '%s' – wird übersprungen.", titel)
            return None

        # Vergangene Events herausfiltern
        try:
            event_datum = date.fromisoformat(datum)
        except ValueError:
            logger.warning("Ungültiges Datumsformat '%s' für Event '%s'.", datum, titel)
            return None

        if event_datum < heute:
            return None

        # Uhrzeit (optional, ohne Sekunden)
        uhrzeit_roh = datum_info.get("localTime")
        uhrzeit = uhrzeit_roh[:5] if uhrzeit_roh else None

        # Venue-Informationen
        venues = event.get("_embedded", {}).get("venues", [])
        venue = venues[0] if venues else {}

        # Ort (Pflichtfeld)
        ort = venue.get("name", "").strip()
        if not ort:
            logger.warning("Kein Ort für Event '%s' – wird übersprungen.", titel)
            return None

        # Gebiet: Der Umkreis von 25 km reicht bis Duisburg, Krefeld, Haan … (Test 24.11.2026: 98 von 161 Events im
        # Theater am Marientor, Duisburg). Nur Orte in Düsseldorf, Neuss und Ratingen – an der Stadt des Veranstaltungsorts.
        stadt = ((venue.get("city") or {}).get("name") or "").strip()
        plz = (venue.get("postalCode") or "").strip()
        if stadt and not _im_gebiet(stadt):
            return None
        # Ohne Stadt entscheidet die PLZ; fehlt auch die, bleibt das Event draußen (Cursor-Prüfung 24.11.2026)
        if not stadt:
            from pipeline.gebiet import plz_im_gebiet
            if not plz_im_gebiet(plz):
                return None

        # Adresse (optional): Straße, PLZ Stadt – mit PLZ/Stadt greift auch der Gebietsfilter der Pipeline
        strasse = ((venue.get("address") or {}).get("line1") or "").strip()
        ort_teil = " ".join(x for x in (plz, stadt) if x)
        adresse = ", ".join(x for x in (strasse, ort_teil) if x) or None

        # Kategorie
        klassifizierungen = event.get("classifications", [])
        kategorie = _kategorie_erkennen(klassifizierungen)

        # Preis (optional)
        preis_bereiche = event.get("priceRanges", [])
        preis = _preis_formatieren(preis_bereiche)

        # Quell-URL (Pflichtfeld)
        quelle_url = event.get("url", "").strip()
        if not quelle_url:
            logger.warning("Keine URL für Event '%s' – wird übersprungen.", titel)
            return None

        # Bild-URL (optional) – nur mit ausdrücklicher Freigabe (siehe Modulkopf)
        bild_url = _bild_url_ermitteln(event.get("images", [])) if bilder_erlaubt() else None

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": adresse,
            "kategorie": kategorie,
            "beschreibung": None,
            "preis": preis,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        }

    except Exception as e:
        logger.error("Fehler beim Parsen eines Ticketmaster-Events: %s", ohne_schluessel(e))
        return None


def _api_anfrage_mit_backoff(client: httpx.Client, params: dict) -> Optional[httpx.Response]:
    """
    Führt eine API-Anfrage mit exponentiellem Backoff bei HTTP 429 durch.
    Maximal 3 Versuche mit Wartezeiten von 2s, 4s und 8s.

    Args:
        client: httpx.Client-Instanz
        params: Query-Parameter für die API-Anfrage

    Returns:
        httpx.Response bei Erfolg, None bei endgültigem Fehler
    """
    wartezeiten = [2, 4, 8]

    for versuch, wartezeit in enumerate(wartezeiten, start=1):
        try:
            response = client.get(API_URL, params=params, timeout=30)

            if response.status_code == 429:
                if versuch < len(wartezeiten):
                    logger.warning(
                        "HTTP 429 – zu viele Anfragen. Warte %ds vor Versuch %d/%d.",
                        wartezeit, versuch + 1, len(wartezeiten)
                    )
                    time.sleep(wartezeit)
                    continue
                else:
                    logger.error(
                        "HTTP 429 nach %d Versuchen – Ticketmaster-API nicht erreichbar.",
                        len(wartezeiten)
                    )
                    return None

            response.raise_for_status()
            return response

        except httpx.TimeoutException:
            logger.error("Timeout beim Abrufen der Ticketmaster API (Versuch %d/%d).",
                         versuch, len(wartezeiten))
            if versuch < len(wartezeiten):
                time.sleep(wartezeit)
        except httpx.HTTPStatusError as e:
            # Nur der Status – die Meldung von httpx enthält die URL mit dem Schlüssel
            logger.error("HTTP Fehler %s bei der Ticketmaster API", e.response.status_code)
            return None

    return None


_SCHLUESSEL_MUSTER = re.compile(r"(apikey=)[^&\s'\"]+", re.IGNORECASE)


def ohne_schluessel(text: object) -> str:
    """Text ohne API-Schlüssel – httpx-Fehlermeldungen enthalten die ganze URL mit ?apikey=… (Cursor-Prüfung 24.11.)."""
    return _SCHLUESSEL_MUSTER.sub(r"\1***", str(text))


class _SchluesselFilter(logging.Filter):
    """Entfernt den Schlüssel auch aus den „HTTP Request: GET …“-Zeilen von httpx (Lauf-Log, Artefakte)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if "apikey=" in str(record.msg) or any("apikey=" in str(a) for a in (record.args or ())):
            record.msg = ohne_schluessel(record.getMessage())
            record.args = None
        return True


logging.getLogger("httpx").addFilter(_SchluesselFilter())


def bilder_erlaubt() -> bool:
    """Ticketmaster-Bilder nur, wenn die Bildnutzung schriftlich bestätigt und TICKETMASTER_BILDER_OK=1 gesetzt ist."""
    return os.getenv("TICKETMASTER_BILDER_OK", "").strip() == "1"


def monatsfenster(heute: date, ende: date) -> list[tuple[str, str]]:
    """
    (startDateTime, endDateTime) je Kalendermonat von heute bis ende, im Format der API (UTC, ohne Millisekunden).
    Das erste Fenster beginnt zwei Stunden vor Mitternacht UTC: Ein Event heute um 00:30 Ortszeit liegt in UTC noch
    am Vortag und fiele sonst durch (Cursor-Prüfung R1–T1). Am Monatsrand überlappt nichts, die URL-Prüfung in
    scrape() verhindert doppelte Events.
    """
    fenster = []
    anfang = heute
    while anfang <= ende:
        naechster = (anfang.replace(day=1) + timedelta(days=32)).replace(day=1)
        bis = min(naechster - timedelta(days=1), ende)
        start = f"{(anfang - timedelta(days=1)).isoformat()}T22:00:00Z" if anfang == heute else f"{anfang.isoformat()}T00:00:00Z"
        fenster.append((start, f"{bis.isoformat()}T23:59:59Z"))
        anfang = naechster
    return fenster


def _seiten_holen(client: httpx.Client, basis: dict) -> list[dict]:
    """Alle Seiten einer Abfrage (höchstens MAX_TREFFER_JE_ABFRAGE Treffer), mit WARTEZEIT zwischen den Anfragen."""
    roh: list[dict] = []
    seite = 0
    while (seite + 1) * SEITENGROESSE <= MAX_TREFFER_JE_ABFRAGE:
        time.sleep(WARTEZEIT)
        response = _api_anfrage_mit_backoff(client, {**basis, "size": SEITENGROESSE, "page": seite})
        if response is None:
            raise RuntimeError("Ticketmaster API-Anfrage endgültig fehlgeschlagen")
        daten = response.json()
        roh.extend(daten.get("_embedded", {}).get("events", []))
        seiten = int(daten.get("page", {}).get("totalPages") or 0)
        seite += 1
        if seite >= seiten:
            break
    else:
        logger.warning("Ticketmaster: mehr als %d Treffer im Fenster %s – Rest fehlt",
                       MAX_TREFFER_JE_ABFRAGE, basis.get("startDateTime"))
    return roh


def scrape() -> list[dict]:
    """
    Ruft Events aus der Ticketmaster Discovery API ab – je Monat bis zum Zeitraum der Quelle.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
        Gibt eine leere Liste zurück wenn kein API-Key gesetzt ist oder
        ein Fehler aufgetreten ist.
    """
    api_key = os.getenv("TICKETMASTER_API_KEY", "")

    # Graceful Skip wenn kein API-Key konfiguriert
    if not api_key:
        logger.info(
            "TICKETMASTER_API_KEY ist nicht gesetzt – Ticketmaster-Scraper wird übersprungen."
        )
        return []

    events: list[dict] = []
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s (bis %s)", QUELLE_NAME, enddatum.isoformat())

    basis = {
        "apikey": api_key,
        "countryCode": "DE",
        "geoPoint": GEOPUNKT,
        "radius": RADIUS_KM,
        "unit": "km",
        "locale": "*",
        "sort": "date,asc",
    }
    gesehene_urls: set[str] = set()
    fehlgeschlagen: list[str] = []
    in_folge = 0

    try:
        with httpx.Client(timeout=30) as client:
            for start, ende in monatsfenster(heute, enddatum):
                # Ein fehlgeschlagenes Fenster kostet nur diesen Monat, nicht die schon gelesenen (Cursor-Prüfung R1–T1)
                try:
                    rohe_events = _seiten_holen(client, {**basis, "startDateTime": start, "endDateTime": ende})
                except Exception as fehler:
                    logger.error("Ticketmaster: Fenster %s bis %s übersprungen: %s", start[:10], ende[:10],
                                 ohne_schluessel(fehler))
                    fehlgeschlagen.append(start[:7])
                    in_folge += 1
                    if in_folge >= ABBRUCH_NACH_FEHLERN:
                        logger.error("Ticketmaster: %d Fenster in Folge ohne Antwort – Abbruch, API offenbar gestört",
                                     in_folge)
                        break
                    continue
                in_folge = 0
                for roher_event in rohe_events:
                    url = roher_event.get("url", "")
                    if url and url in gesehene_urls:
                        continue
                    if url:
                        gesehene_urls.add(url)
                    event = _event_parsen(roher_event, heute)
                    if event:
                        events.append(event)
    except Exception as e:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, ohne_schluessel(e))
        return []

    # Vorschau-Fenster: Events hinter dem Zeitraum der Quelle (vorschau_ende) ausfiltern
    events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]

    if fehlgeschlagen:
        logger.warning("Ticketmaster: %d Monatsfenster ohne Antwort (%s) – Teilergebnis",
                       len(fehlgeschlagen), ", ".join(fehlgeschlagen))
    logger.info("Scraper %s fertig: %d Events gefunden.", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    # Direkter Testlauf
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    import json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
