"""
stadtteil_backfill.py – DiesDasDüsseldorf
Weist allen bestehenden Events in Supabase einen Stadtteil zu,
die noch keinen haben.

Aufruf: python -m pipeline.stadtteil_backfill
"""
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database.client import get_supabase_client
from pipeline.stadtteil_mapper import stadtteil_ermitteln

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def backfill():
    """Liest alle Events ohne Stadtteil und ordnet sie zu."""
    db = get_supabase_client()

    offset = 0
    batch_size = 500
    gesamt_aktualisiert = 0
    gesamt_nicht_zuordenbar = 0

    while True:
        result = (
            db.table("events")
            .select("id, ort, adresse")
            .is_("stadtteil", "null")
            .range(offset, offset + batch_size - 1)
            .execute()
        )

        events = result.data or []
        if not events:
            break

        logger.info("Batch geladen: %d Events (Offset %d)", len(events), offset)

        for event in events:
            stadtteil = stadtteil_ermitteln(
                event.get("ort", ""),
                event.get("adresse"),
            )
            if stadtteil:
                db.table("events").update({"stadtteil": stadtteil}).eq("id", event["id"]).execute()
                gesamt_aktualisiert += 1
            else:
                gesamt_nicht_zuordenbar += 1

        if len(events) < batch_size:
            break
        offset += batch_size

    logger.info(
        "Backfill abgeschlossen: %d aktualisiert, %d nicht zuordenbar",
        gesamt_aktualisiert, gesamt_nicht_zuordenbar,
    )


if __name__ == "__main__":
    backfill()
