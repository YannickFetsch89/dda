"""
main.py – DiesDasDüsseldorf
Einstiegspunkt: Startet die tägliche Event-Pipeline
"""
import asyncio
import logging
import sys
from datetime import date

from config import LOG_LEVEL, LOG_DIR, SCHEDULER_UHRZEIT
from database.client import events_speichern
from scraper.tier1 import (
    rausgegangen,
    ticketmaster,
    eventbrite,
    kulturportal,
    visitduesseldorf,
    # meinestadt deaktiviert – dauerhaft durch Akamai WAF blockiert (HTTP 403)
)

# Logging konfigurieren
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"{LOG_DIR}/pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


async def pipeline_ausfuehren():
    """
    Führt die vollständige tägliche Pipeline aus:
    1. Scraper starten (Tier 1, 2, 3)
    2. Duplikate entfernen
    3. Events kategorisieren
    4. Instagram Captions generieren
    5. Posts veröffentlichen
    """
    logger.info("=== DiesDasDüsseldorf Pipeline gestartet ===")
    heute = date.today()
    logger.info("Datum: %s", heute.isoformat())

    # Schritt 1: Scraper ausführen
    logger.info("--- Schritt 1: Scraper ---")
    alle_events = []

    events_rausgegangen = rausgegangen.scrape()
    logger.info("Rausgegangen: %d Events", len(events_rausgegangen))
    alle_events.extend(events_rausgegangen)

    events_ticketmaster = ticketmaster.scrape()
    logger.info("Ticketmaster: %d Events", len(events_ticketmaster))
    alle_events.extend(events_ticketmaster)

    events_eventbrite = eventbrite.scrape()
    logger.info("Eventbrite: %d Events", len(events_eventbrite))
    alle_events.extend(events_eventbrite)

    events_kulturportal = kulturportal.scrape()
    logger.info("Kulturportal Düsseldorf: %d Events", len(events_kulturportal))
    alle_events.extend(events_kulturportal)

    events_visitduesseldorf = visitduesseldorf.scrape()
    logger.info("VisitDüsseldorf: %d Events", len(events_visitduesseldorf))
    alle_events.extend(events_visitduesseldorf)

    # meinestadt.scrape() wurde entfernt – Quelle dauerhaft durch Akamai WAF blockiert (HTTP 403)

    logger.info("Scraper gesamt: %d Events gesammelt", len(alle_events))

    # Schritt 2: In Supabase speichern
    logger.info("--- Schritt 2: Datenbank ---")
    stats = events_speichern(alle_events)
    logger.info(
        "Ergebnis – Neu gespeichert: %d | Duplikate: %d | Fehler: %d",
        stats["gespeichert"], stats["duplikate"], stats["fehler"]
    )

    # Schritt 3: Kategorisierung
    logger.info("--- Schritt 3: Kategorisierung ---")
    from pipeline import categorizer
    anzahl_kategorisiert = categorizer.kategorisieren(limit=100)
    logger.info("Kategorisierung: %d Events verarbeitet", anzahl_kategorisiert)

    # Schritt 4: Caption-Generierung
    logger.info("--- Schritt 4: Caption-Generierung ---")
    from pipeline import caption_generator
    anzahl_captions = caption_generator.captions_generieren(limit=50)
    logger.info("Captions generiert: %d Events aufbereitet", anzahl_captions)

    # Schritt 5: Instagram-Posting
    logger.info("--- Schritt 5: Instagram-Posting ---")
    from pipeline import publisher
    anzahl_gepostet = publisher.posten(limit=5)
    logger.info("Instagram: %d Events gepostet", anzahl_gepostet)

    logger.info("=== Pipeline abgeschlossen ===")


def scheduler_starten():
    """Startet den APScheduler für tägliche Ausführung."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()
    stunde, minute = SCHEDULER_UHRZEIT.split(":")
    scheduler.add_job(
        pipeline_ausfuehren,
        trigger="cron",
        hour=int(stunde),
        minute=int(minute),
        id="tägliche_pipeline",
    )
    scheduler.start()
    logger.info("Scheduler gestartet – Pipeline läuft täglich um %s Uhr", SCHEDULER_UHRZEIT)
    return scheduler


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DiesDasDüsseldorf Pipeline")
    parser.add_argument(
        "--jetzt",
        action="store_true",
        help="Pipeline sofort einmalig ausführen (ohne Scheduler)",
    )
    args = parser.parse_args()

    if args.jetzt:
        logger.info("Einmaliger Lauf gestartet (--jetzt Flag gesetzt)")
        asyncio.run(pipeline_ausfuehren())
    else:
        scheduler = scheduler_starten()
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Pipeline-Scheduler beendet.")
            scheduler.shutdown()
