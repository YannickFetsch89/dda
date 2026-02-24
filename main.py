"""
main.py – DiesDasDüsseldorf
Einstiegspunkt: Startet die tägliche Event-Pipeline
"""
import asyncio
import logging
import sys
from datetime import date

from config import LOG_LEVEL, LOG_DIR, SCHEDULER_UHRZEIT

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

    # TODO: Scraper importieren und aufrufen (wird in Sprint 1 implementiert)
    # TODO: Deduplication aufrufen
    # TODO: Kategorisierung aufrufen
    # TODO: Caption-Generierung aufrufen
    # TODO: Instagram-Posting aufrufen

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
