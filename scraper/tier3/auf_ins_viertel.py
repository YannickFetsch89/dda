"""
auf_ins_viertel.py – DiesDasDüsseldorf
Scraper für „Auf ins Viertel“ – kulinarische Stadtführungen (Altstadt, Carlsplatz, Flingern,
Japanviertel, Lorettoviertel, Benrath, Altstadt Pub Crawl; außerdem Ratingen, Neuss, Krefeld).

Hintergrund (Stand 2026-11):
  aufinsviertel.de ist WordPress ohne Event-Plugin; die Termine kommen ausschließlich aus einem
  bookingkit-Widget (Vendor 4a875f656df0e3fd0ee1710c75947854). Gelesen wird deshalb der
  bookingkit-Kalender (siehe scraper/utils/bookingkit.py): Kalender je Monat → Tagesliste mit
  JSON-LD (Titel, Beginn, Preis, ausgebucht, Bild, Treffpunkt) → Tourbeschreibung je Tour.
  robots.txt: aufinsviertel.de erlaubt alles außer /wp-admin/, bookingkit erlaubt /onPage/.

Es werden nur Touren in Düsseldorf übernommen (Treffpunkt-Adresse), ausgebuchte Termine
werden übersprungen. Kategorie aller Touren: stadtfuehrung. Mehrere Termine einer Tour am
selben Tag werden als einzelne Events mit eigener Uhrzeit geliefert (Website: „Diverse Uhrzeiten“).

Quelle (Link für Besucher): die Tour-Seite auf aufinsviertel.de mit Buchungs-Widget.
Erstellt: 2026-11-05
"""
import logging
import re
from datetime import date, timedelta
from typing import Optional

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.bookingkit import BookingkitClient, BookingkitTermin

logger = logging.getLogger(__name__)

QUELLE_NAME = "Auf ins Viertel"
VENDOR = "4a875f656df0e3fd0ee1710c75947854"
BASIS_URL = "https://aufinsviertel.de"
UEBERSICHT_URL = f"{BASIS_URL}/alle-stadtfuehrungen/"

# bookingkit-Tour-ID → Tour-Seite (aus den data-e-Attributen der Seiten, Stand 2026-11-05).
# Neue Touren landen ohne Eintrag auf der Übersichtsseite – dann hier ergänzen.
TOUR_SEITEN = {
    "ff6eee47dfff17f6cd436a59a0763996": "/duesseldorf-stadtfuehrungen/altstadt/",
    "8b141a43fed49b945ad9fadaefef57e9": "/duesseldorf-stadtfuehrungen/altstadt-pub-crawl/",
    "bfc1616f44410598151175639b672c04": "/duesseldorf-stadtfuehrungen/carlsplatz/",
    "b8a9d40569dd3228e36e79c8a4bf4637": "/duesseldorf-stadtfuehrungen/flingern/",
    "329e93b8e6d177ae6becc1afe578f5b9": "/duesseldorf-stadtfuehrungen/japanviertel/",
    "31ab5e1a79e7dcc1dfe40332e53cd6d3": "/duesseldorf-stadtfuehrungen/lorettoviertel/",
    "539208519843707a79f3cbbb660e8b97": "/duesseldorf-stadtfuehrungen/benrath/",
}

# Alle Touren (kulinarisch und Pub Crawl) sind geführte Rundgänge → eigene Kategorie
KATEGORIE = "stadtfuehrung"


def _in_duesseldorf(adresse: Optional[str]) -> bool:
    """
    Treffpunkt liegt in Düsseldorf: Ortsname (auch „Duesseldorf“) muss vorkommen; steht eine PLZ dabei,
    muss sie eine Düsseldorfer PLZ (40xxx) sein. Nachbarstädte (Ratingen 40878, Neuss …) fallen über
    den Ortsnamen heraus – die Website deckt bei Events nur Düsseldorf ab.
    """
    if not adresse:
        return False
    text = adresse.lower().replace("ü", "ue")
    # Wortende: „Düsseldorfer Straße“ (z.B. in Duisburg) zählt nicht als Ortsname
    if not re.search(r"duesseldorf\b", text):
        return False
    plzs = re.findall(r"\b(\d{5})\b", text)
    return not plzs or any(p.startswith("40") for p in plzs)


def _adresse_kuerzen(adresse: str) -> str:
    """„Immermannstraße 41, 40210 Düsseldorf-Stadtbezirk 1, Deutschland“ → „Immermannstraße 41, 40210 Düsseldorf“."""
    teile = [t.strip() for t in adresse.split(",") if t.strip() and t.strip() != "Deutschland"]
    teile = [re.sub(r"Düsseldorf-Stadtbezirk \d+", "Düsseldorf", t) for t in teile]
    return ", ".join(teile)


def _preis(preis: Optional[float]) -> Optional[str]:
    if preis is None:
        return None
    if preis == 0:
        return "kostenlos"
    return f"{preis:.2f}".replace(".", ",").replace(",00", "") + " €"


def _beschreibung_kuerzen(text: Optional[str]) -> Optional[str]:
    """Auf höchstens 300 Zeichen kürzen, möglichst am Satzende."""
    if not text:
        return None
    text = text.strip()
    if len(text) <= 300:
        return text
    stueck = text[:299]
    satzende = max(stueck.rfind(". "), stueck.rfind("! "), stueck.rfind("? "))
    if satzende >= 150:
        return stueck[:satzende + 1]
    return stueck[: stueck.rfind(" ")].rstrip(" ,;:–-") + "…"


def _events_bauen(termine: list[BookingkitTermin], beschreibungen: dict[str, Optional[str]]) -> list[dict]:
    """Termine in das Event-Format der Pipeline umwandeln."""
    # Mehrere Termine einer Tour am selben Tag bleiben einzelne Events mit eigener Uhrzeit
    # (Datenbank: UNIQUE titel+datum+ort+uhrzeit); die Website bündelt sie zu „Diverse Uhrzeiten“.
    events = []
    for t in termine:
        adresse = _adresse_kuerzen(t.adresse or "")
        uhrzeit = t.start.strftime("%H:%M")
        events.append({
            "titel": t.titel,
            "datum": t.start.date().isoformat(),
            "uhrzeit": uhrzeit,
            "ort": f"Auf ins Viertel – Treffpunkt {adresse.split(',')[0]}",
            "adresse": adresse,
            "kategorie": KATEGORIE,
            "_kategorie_fest": True,  # reine Führungsquelle (siehe pipeline/deduplication.py)
            "beschreibung": _beschreibung_kuerzen(beschreibungen.get(t.event_id)),
            "preis": _preis(t.preis),
            "quelle_name": QUELLE_NAME,
            "quelle_url": BASIS_URL + TOUR_SEITEN[t.event_id] if t.event_id in TOUR_SEITEN else UEBERSICHT_URL,
            "bild_url": t.bild_url,
            "bild_generiert": False,
            "post_typ": "feed",
            "instagram_caption": None,
            "instagram_location_id": None,
            "status": "neu",
        })
    return events


async def scrape() -> list[dict]:
    """
    Scrapt die buchbaren Termine von „Auf ins Viertel“ (nur Düsseldorf).

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    # Alle Monate vom aktuellen bis zum Monat des Enddatums
    monate: list[tuple[int, int]] = []
    jahr, monat = heute.year, heute.month
    while (jahr, monat) <= (enddatum.year, enddatum.month):
        monate.append((jahr, monat))
        jahr, monat = (jahr + 1, 1) if monat == 12 else (jahr, monat + 1)

    try:
        async with BookingkitClient(VENDOR, logger) as bk:
            tage = [(d, url) for d, url in await bk.tage_mit_terminen(monate) if heute <= d <= enddatum]
            logger.info("%s: %d Tage mit Terminen bis %s", QUELLE_NAME, len(tage), enddatum.isoformat())

            termine: list[BookingkitTermin] = []
            for _tag, url in tage:
                for t in await bk.termine_am_tag(url):
                    if t.ausgebucht or not _in_duesseldorf(t.adresse):
                        continue
                    if heute <= t.start.date() <= enddatum:
                        termine.append(t)

            # Beschreibung einmal je Tour holen
            beschreibungen: dict[str, Optional[str]] = {}
            for event_id in sorted({t.event_id for t in termine}):
                beschreibungen[event_id] = await bk.beschreibung(event_id)
    except Exception as fehler:
        logger.error("%s: Scraper abgebrochen: %s", QUELLE_NAME, fehler)
        return []

    # Doppelte Termine (gleiche Tour, gleiche Startzeit) entfernen
    eindeutig = {(t.event_id, t.start): t for t in termine}
    events = _events_bauen(sorted(eindeutig.values(), key=lambda t: t.start), beschreibungen)
    unbekannt = {t.event_id for t in eindeutig.values()} - TOUR_SEITEN.keys()
    if unbekannt:
        logger.warning("%s: Touren ohne eigene Seite (Link auf Übersicht): %s", QUELLE_NAME, ", ".join(sorted(unbekannt)))
    logger.info("%s: %d Events gefunden", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    import asyncio
    import json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ergebnis = asyncio.run(scrape())
    print(json.dumps(ergebnis[:5], ensure_ascii=False, indent=2))
    print(f"… insgesamt {len(ergebnis)} Events")
