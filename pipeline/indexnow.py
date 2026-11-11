"""
indexnow.py – DiesDasDüsseldorf
Meldet neue Event-URLs per IndexNow an Bing (und damit an ChatGPT-Suche/Copilot, die den Bing-Index nutzen),
außerdem /heute, die Startseite und die betroffenen Tagesseiten. Google ignoriert IndexNow.
SEO-/GEO-Plan Nov. 2026, Maßnahme 14.

Der Schlüssel ist bei IndexNow absichtlich öffentlich: Er liegt als Datei im Seitenstamm
(web/public/<schlüssel>.txt) und beweist, dass wir die Domain kontrollieren. Kein Secret.

Nutzung im täglichen Lauf: nach_lauf_melden(lauf_start) – meldet nur Events, die in diesem Lauf neu
angelegt wurden (ein Änderungsdatum je Event gibt es nicht). Nicht die ganze Sitemap, nicht stündlich.
Manuell: python -m pipeline.indexnow [--seit 2026-11-09T00:00] [--dry-run]
"""
import argparse
import logging
import os
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

INDEXNOW_SCHLUESSEL = "3c1f7dd091690cf3532f16384f129a65"
INDEXNOW_ENDPUNKT = "https://api.indexnow.org/indexnow"
SITE_URL = os.getenv("SITE_URL", "https://diesdas.events").rstrip("/")
TAGESFENSTER = 14  # wie die Sitemap: /tag/… für heute und die nächsten 13 Tage
MAX_JE_ANFRAGE = 10000


def event_url(kategorie: str, slug: str) -> str:
    return f"{SITE_URL}/event/{quote(kategorie, safe='')}/{quote(slug, safe='')}"


def urls_bauen(events: list[dict], heute: date) -> list[str]:
    """
    Event-URLs (nur kommende mit Slug) + /heute + Startseite + die Tagesseiten, auf die neue Events fallen
    (nur innerhalb des Sitemap-Fensters). Ohne Dubletten, Reihenfolge stabil.
    """
    letzter_tag = heute + timedelta(days=TAGESFENSTER - 1)
    urls: list[str] = [f"{SITE_URL}/heute", f"{SITE_URL}/"]
    tage: set[str] = set()
    for e in events:
        if not e.get("slug") or not e.get("kategorie") or not e.get("datum"):
            continue
        try:
            tag = date.fromisoformat(e["datum"])
            bis = date.fromisoformat(e["datum_bis"]) if e.get("datum_bis") else tag
        except ValueError:
            continue
        if bis < heute:
            continue  # vorbei – nicht melden
        urls.append(event_url(e["kategorie"], e["slug"]))
        t = max(tag, heute)
        while t <= min(bis, letzter_tag):
            tage.add(t.isoformat())
            t += timedelta(days=1)
    urls += [f"{SITE_URL}/tag/{t}" for t in sorted(tage)]
    return list(dict.fromkeys(urls))


def melden(urls: list[str], dry_run: bool = False) -> int:
    """URLs an IndexNow senden. Gibt die Anzahl gemeldeter URLs zurück (0 bei Fehler)."""
    if not urls:
        return 0
    if dry_run:
        logger.info("[Dry-Run] IndexNow würde %d URLs melden", len(urls))
        return len(urls)
    host = SITE_URL.split("://", 1)[-1]
    gemeldet = 0
    for i in range(0, len(urls), MAX_JE_ANFRAGE):
        teil = urls[i:i + MAX_JE_ANFRAGE]
        try:
            antwort = httpx.post(
                INDEXNOW_ENDPUNKT,
                json={"host": host, "key": INDEXNOW_SCHLUESSEL,
                      "keyLocation": f"{SITE_URL}/{INDEXNOW_SCHLUESSEL}.txt", "urlList": teil},
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=30,
            )
            # 200 = angenommen, 202 = angenommen, Schlüssel wird noch geprüft
            if antwort.status_code in (200, 202):
                gemeldet += len(teil)
            else:
                logger.warning("IndexNow lehnt ab: HTTP %s %s", antwort.status_code, antwort.text[:200])
        except Exception as e:
            logger.warning("IndexNow nicht erreichbar: %s", e)
    return gemeldet


def nach_lauf_melden(lauf_start: datetime, dry_run: bool = False) -> int:
    """Alle Events, die seit lauf_start angelegt wurden, plus Übersichtsseiten melden."""
    from database.client import get_supabase_client

    db = get_supabase_client()
    events = (db.table("events").select("kategorie, slug, datum, datum_bis")
              .eq("abgelehnt", False).gte("erstellt_am", lauf_start.isoformat())
              .limit(5000).execute().data or [])
    urls = urls_bauen(events, date.today())
    anzahl = melden(urls, dry_run)
    logger.info("IndexNow: %d neue Events → %d URLs gemeldet", len(events), anzahl)
    return anzahl


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser(description="Neue Event-URLs per IndexNow melden")
    parser.add_argument("--seit", help="ISO-Zeitpunkt (Standard: vor 24 Stunden)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    seit = datetime.fromisoformat(args.seit) if args.seit else datetime.now(timezone.utc) - timedelta(hours=24)
    if seit.tzinfo is None:
        seit = seit.replace(tzinfo=timezone.utc)
    nach_lauf_melden(seit, args.dry_run)


if __name__ == "__main__":
    main()
