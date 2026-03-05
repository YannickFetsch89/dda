"""
salon_des_amateurs.py – DiesDasDüsseldorf
Scraper für den Salon des Amateurs Düsseldorf.

Strategie:
Die eigene Website (salonamateurs.de) ist durch Cloudflare-Schutz
für automatisierte Zugriffe gesperrt (HTTP 403). Events werden über
Resident Advisor (ra.co GraphQL API, Venue-ID 15478) abgerufen.

Der Salon des Amateurs ist ein legendärer Club in Düsseldorf
(Kunsthalle) mit Fokus auf Techno, House, Experimental und Disco.

URL: https://www.salonamateurs.de
RA-Venue: https://ra.co/clubs/15478
Adresse: Grabbeplatz 4, 40213 Düsseldorf (Kunsthalle Düsseldorf)
Erstellt: 2026-03-05
"""
import logging

from scraper.utils.ra_venue import ra_venue_scrapen

logger = logging.getLogger(__name__)

QUELLE_NAME = "Salon des Amateurs"
ORT_STANDARD = "Salon des Amateurs"
ADRESSE_STANDARD = "Grabbeplatz 4, 40213 Düsseldorf"
RA_VENUE_ID = 15478


def scrape() -> list[dict]:
    """
    Scrapt Events des Salon des Amateurs via Resident Advisor API.

    Da salonamateurs.de durch Bot-Schutz nicht zugänglich ist,
    werden Events über die RA GraphQL API (Venue 15478) abgerufen.

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
