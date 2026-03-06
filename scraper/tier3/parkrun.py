"""
parkrun.py – DiesDasDüsseldorf
Statischer Eintrag für den Parkrun Volksgarten Düsseldorf.

Parkrun findet jeden Samstag um 09:00 Uhr im Volksgarten statt.
Da das Datum immer vorhersehbar ist, wird kein echter Scraper benötigt –
das nächste Samstag-Datum wird dynamisch berechnet.

URL: https://www.parkrun.com.de/volksgarten/
Adresse: Volksgarten, 40219 Düsseldorf
Erstellt: 2026-03-06
"""
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

QUELLE_NAME = "Parkrun Volksgarten Düsseldorf"
QUELLE_URL = "https://www.parkrun.com.de/volksgarten/"
ORT_STANDARD = "Volksgarten Düsseldorf"
ADRESSE_STANDARD = "Volksgarten, 40219 Düsseldorf"
KATEGORIE = "sport"
PREIS = "kostenlos"
TITEL = "Parkrun Volksgarten Düsseldorf"
BESCHREIBUNG = (
    "Kostenloser 5km Lauf jeden Samstag um 09:00 Uhr im Volksgarten. "
    "Für alle Niveaus geeignet – einfach mitmachen!"
)


def _naechsten_samstag_berechnen() -> date:
    """
    Berechnet das Datum des nächsten Samstags ab heute.

    Returns:
        Datum des nächsten Samstags (einschließlich heute, wenn heute Samstag ist)
    """
    heute = date.today()
    # Wochentag: 0=Montag, 5=Samstag, 6=Sonntag
    tage_bis_samstag = (5 - heute.weekday()) % 7
    # Wenn heute bereits Samstag ist, bleibt tage_bis_samstag = 0
    return heute + timedelta(days=tage_bis_samstag)


def scrape() -> list[dict]:
    """
    Gibt das nächste Parkrun-Event im Volksgarten als statischen Eintrag zurück.

    Parkrun findet jeden Samstag um 09:00 Uhr statt. Da das Datum vorhersehbar ist,
    wird kein externer Request benötigt.

    Returns:
        Liste mit einem Event-Dict im DiesDasDüsseldorf Standard-Format.
    """
    logger.info("Starte Scraper: %s (statischer Eintrag)", QUELLE_NAME)

    try:
        naechster_samstag = _naechsten_samstag_berechnen()
        logger.info("Nächster Parkrun: %s", naechster_samstag.isoformat())

        event = {
            "titel": TITEL,
            "datum": naechster_samstag.isoformat(),
            "uhrzeit": "09:00",
            "ort": ORT_STANDARD,
            "adresse": ADRESSE_STANDARD,
            "kategorie": KATEGORIE,
            "beschreibung": BESCHREIBUNG,
            "preis": PREIS,
            "quelle_name": QUELLE_NAME,
            "quelle_url": QUELLE_URL,
            "bild_url": None,
            "bild_generiert": False,
            "post_typ": "feed",
            "instagram_caption": None,
            "status": "neu",
        }

        logger.info("Scraper %s fertig: 1 Event", QUELLE_NAME)
        return [event]

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(fehler))
        return []


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json as _json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
