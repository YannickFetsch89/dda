"""
kulturschlachthof_r25.py – DiesDasDüsseldorf
Scraper für den Kulturschlachthof R25 Düsseldorf.

Strategie:
Die eigene Website (kulturschlachthof.de) ist eine reine Platzhalterseite
ohne Programm-Informationen. Events werden über Resident Advisor
(ra.co GraphQL API, Venue-ID 133380) abgerufen.

Der Kulturschlachthof R25 ist ein Club für elektronische Musik,
Techno, House und experimentelle Sounds in Düsseldorf.

URL: https://kulturschlachthof.de
RA-Venue: https://ra.co/clubs/133380
Adresse: Reisholzer Str. 25, 40721 Hilden (Nähe Düsseldorf)
Erstellt: 2026-03-05
"""
import logging

from scraper.utils.ra_venue import ra_venue_scrapen

logger = logging.getLogger(__name__)

QUELLE_NAME = "Kulturschlachthof R25"
ORT_STANDARD = "Kulturschlachthof R25"
ADRESSE_STANDARD = "Ronsdorfer Str. 134, 40233 Düsseldorf"
RA_VENUE_ID = 133380


def scrape() -> list[dict]:
    """
    Scrapt Events des Kulturschlachthof R25 via Resident Advisor API.

    Da kulturschlachthof.de keine Programm-Informationen enthält,
    werden Events über die RA GraphQL API (Venue 133380) abgerufen.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    return ra_venue_scrapen(
        quelle_name=QUELLE_NAME,
        ort_standard=ORT_STANDARD,
        adresse_standard=ADRESSE_STANDARD,
        ra_venue_id=RA_VENUE_ID,
        kategorie="nightlife",
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json as _json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:5]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
