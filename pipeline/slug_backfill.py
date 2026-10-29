"""
slug_backfill.py – DiesDasDüsseldorf
Generiert SEO-Slugs für alle bestehenden Events in Supabase,
die noch keinen Slug haben.

Aufruf: python -m pipeline.slug_backfill
"""
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from database.client import get_supabase_client
from pipeline.slug_generator import slug_erzeugen

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def backfill():
    """Generiert Slugs für alle Events ohne Slug."""
    db = get_supabase_client()

    offset = 0
    batch_size = 500
    gesamt_aktualisiert = 0
    gesamt_fehler = 0
    bekannte_slugs: set[str] = set()

    # Bestehende Slugs laden um Duplikate zu vermeiden
    existing = db.table("events").select("slug").not_.is_("slug", "null").execute()
    for row in (existing.data or []):
        if row.get("slug"):
            bekannte_slugs.add(row["slug"])
    logger.info("Bestehende Slugs geladen: %d", len(bekannte_slugs))

    while True:
        result = (
            db.table("events")
            .select("id, titel, ort, datum")
            .is_("slug", "null")
            .range(offset, offset + batch_size - 1)
            .execute()
        )

        events = result.data or []
        if not events:
            break

        logger.info("Batch geladen: %d Events (Offset %d)", len(events), offset)

        for event in events:
            slug = slug_erzeugen(
                event.get("titel", ""),
                event.get("ort", ""),
                event.get("datum", ""),
            )
            if not slug:
                gesamt_fehler += 1
                continue

            # Eindeutigkeit sicherstellen
            basis_slug = slug
            zaehler = 2
            while slug in bekannte_slugs:
                slug = f"{basis_slug}-{zaehler}"
                zaehler += 1

            try:
                db.table("events").update({"slug": slug}).eq("id", event["id"]).execute()
                bekannte_slugs.add(slug)
                gesamt_aktualisiert += 1
            except Exception as e:
                gesamt_fehler += 1
                logger.error(
                    "Fehler beim Slug-Update für '%s': %s",
                    event.get("titel", "?")[:40], str(e),
                )

        if len(events) < batch_size:
            break
        offset += batch_size

    logger.info(
        "Slug-Backfill abgeschlossen: %d aktualisiert, %d Fehler",
        gesamt_aktualisiert, gesamt_fehler,
    )


if __name__ == "__main__":
    backfill()
