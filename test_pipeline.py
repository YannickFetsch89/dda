"""
test_pipeline.py – DiesDasDüsseldorf
Testlauf: Scraper + Supabase-Speicherung + KI-Aufbereitung
Ohne Instagram-Posting.
"""
import logging
import sys
from datetime import date

from config import LOG_LEVEL
from database.client import events_speichern
from scraper.tier1 import (
    rausgegangen,
    ticketmaster,
    eventbrite,
    kulturportal,
    visitduesseldorf,
)
from scraper.tier2 import (
    tonhalle,
    zakk,
    oper_am_rhein,
    schauspielhaus,
    dlive,
)
from pipeline import categorizer, caption_generator

# Logging konfigurieren
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def test_pipeline_ausfuehren():
    logger.info("=== TEST-PIPELINE GESTARTET (ohne Instagram-Posting) ===")
    logger.info("Datum: %s", date.today().isoformat())
    alle_events = []

    # --- Schritt 1: Scraper ---
    logger.info("--- Schritt 1: Scraper ---")

    scraper_liste = [
        ("Rausgegangen",              rausgegangen.scrape),
        ("Ticketmaster",              ticketmaster.scrape),
        ("Eventbrite",                eventbrite.scrape),
        ("Kulturportal Düsseldorf",   kulturportal.scrape),
        ("VisitDüsseldorf",           visitduesseldorf.scrape),
        ("Tonhalle Düsseldorf",       tonhalle.scrape),
        ("zakk",                      zakk.scrape),
        ("Deutsche Oper am Rhein",    oper_am_rhein.scrape),
        ("Düsseldorfer Schauspielhaus", schauspielhaus.scrape),
        ("d-live",                    dlive.scrape),
    ]

    for name, scrape_fn in scraper_liste:
        try:
            events = scrape_fn()
            logger.info("  %-30s → %d Events", name, len(events))
            alle_events.extend(events)
        except Exception as e:
            logger.error("  %-30s → FEHLER: %s", name, str(e))

    logger.info("Scraper gesamt: %d Events gesammelt", len(alle_events))

    # --- Schritt 2: Supabase ---
    logger.info("--- Schritt 2: Supabase ---")
    stats = events_speichern(alle_events)
    logger.info(
        "Ergebnis – Neu: %d | Duplikate: %d | Fehler: %d",
        stats["gespeichert"], stats["duplikate"], stats["fehler"]
    )

    # --- Schritt 3: Kategorisierung ---
    logger.info("--- Schritt 3: Kategorisierung (Claude Haiku) ---")
    anzahl = categorizer.kategorisieren(limit=50)
    logger.info("Kategorisiert: %d Events", anzahl)

    # --- Schritt 4: Caption-Generierung ---
    logger.info("--- Schritt 4: Caption-Generierung (Claude Sonnet) ---")
    anzahl = caption_generator.captions_generieren(limit=20)
    logger.info("Captions generiert: %d Events", anzahl)

    logger.info("=== TEST-PIPELINE ABGESCHLOSSEN ===")


if __name__ == "__main__":
    test_pipeline_ausfuehren()
