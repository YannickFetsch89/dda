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
from zoneinfo import ZoneInfo

import httpx

logger = logging.getLogger(__name__)

INDEXNOW_SCHLUESSEL = "3c1f7dd091690cf3532f16384f129a65"
INDEXNOW_ENDPUNKT = "https://api.indexnow.org/indexnow"
SITE_URL = os.getenv("SITE_URL", "https://diesdas.events").rstrip("/")
TAGESFENSTER = 14  # wie die Sitemap: /tag/… für heute und die nächsten 13 Tage
MAX_JE_ANFRAGE = 10000
SEITENGROESSE = 1000  # Supabase liefert pro Abfrage höchstens 1.000 Zeilen

# Website-Slugs der Kategorien (web/lib/kategorien.ts); die DB speichert „family“, die Website zeigt „familie“
WEB_KATEGORIEN = {"kultur", "musik", "food", "sport", "outdoor", "stadtfuehrung", "community", "nightlife",
                  "familie", "dating", "sonstiges"}


def kategorie_web(wert: str | None) -> str:
    """Wie kategorieAusDb auf der Website – sonst meldet IndexNow eine URL, die per 308 umleitet."""
    w = (wert or "").strip().lower()
    if w == "family":
        return "familie"
    return w if w in WEB_KATEGORIEN else "sonstiges"


def heute_berlin() -> date:
    return datetime.now(ZoneInfo("Europe/Berlin")).date()


def event_url(kategorie: str, slug: str) -> str:
    return f"{SITE_URL}/event/{quote(kategorie_web(kategorie), safe='')}/{quote(slug, safe='')}"


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


# ── Ortsseiten /orte (Plan docs/plan-locations-2026-11-18.md, 3.11) ─────────────────────────────────────────────
# Erst ab Deploy-Punkt 5 an (GitHub-Variable ORTSSEITEN_MELDEN=1), vorher meldet der tägliche Lauf keine /orte-URL.
def ortsseiten_melden_an() -> bool:
    return os.getenv("ORTSSEITEN_MELDEN", "0").strip() == "1"


def ort_indexierbar(adresse_bestaetigt: bool, text_freigegeben: bool, kommende: int) -> bool:
    """Dieselbe Regel wie web/lib/spielstaetten.ts (indexierbar); beide prüfen tests/fixtures/ort_indexierbar.json."""
    return (adresse_bestaetigt or text_freigegeben) and (kommende > 0 or text_freigegeben)


def ort_url(slug: str) -> str:
    return f"{SITE_URL}/orte/{quote(slug, safe='')}"


def ortsseiten_urls(neue_ort_ids: set[str], orte: dict[str, dict]) -> list[str]:
    """
    URLs der indexierbaren Ortsseiten, deren Ort in diesem Lauf neue Events bekommen hat (rein, testbar).
    `orte`: id → {slug, typ, parent_id, aktiv, spielstaette: {adresse_bestaetigt, text_freigegeben}, adresse}.
    Ein neues Event zählt als kommendes. Saal → Saalseite und, wenn das Haus eine Spielstätte ist, die Hausseite.
    Guide-Häuser (z. B. zakk) meldet IndexNow wie heute nicht – ihre Regeln gibt es nur in TypeScript.
    """
    def flags(o: dict) -> tuple[bool, bool]:
        p = o.get("spielstaette") or {}
        return bool(p.get("adresse_bestaetigt")), bool(p.get("text_freigegeben"))

    urls: list[str] = []
    for oid in sorted(neue_ort_ids):
        o = orte.get(oid)
        if not o or o.get("typ") != "spielstaette" or not o.get("aktiv"):
            continue
        adresse, text = flags(o)
        haus = orte.get(o.get("parent_id") or "")
        if haus and not adresse:  # Säle erben die bestätigte Adresse vom Haus (Plan 3.6)
            adresse = flags(haus)[0] if haus.get("typ") == "spielstaette" else bool(haus.get("adresse"))
        if ort_indexierbar(adresse, text, 1):
            urls.append(ort_url(o["slug"]))
        if haus and haus.get("typ") == "spielstaette" and haus.get("aktiv"):
            h_adresse, h_text = flags(haus)
            if ort_indexierbar(h_adresse, h_text, 1):
                urls.append(ort_url(haus["slug"]))
    return list(dict.fromkeys(urls))


def _orte_laden(db, ids: set[str]) -> dict[str, dict]:
    """Zeilen der IDs plus ihrer Häuser (eine Stufe)."""
    def laden(menge: set[str]) -> list[dict]:
        if not menge:
            return []
        return (db.table("orte").select("id, slug, typ, aktiv, parent_id, adresse, spielstaette:extras->spielstaette")
                .in_("id", sorted(menge)).execute().data or [])
    zeilen = {z["id"]: z for z in laden(ids)}
    eltern = {z["parent_id"] for z in zeilen.values() if z.get("parent_id")} - set(zeilen)
    zeilen.update({z["id"]: z for z in laden(eltern)})
    return zeilen


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
    events: list[dict] = []
    seite = 0
    while True:  # seitenweise – sonst kämen nur die ersten 1.000 Zeilen
        teil = (db.table("events").select("kategorie, slug, datum, datum_bis, ort_id")
                .eq("abgelehnt", False).gte("erstellt_am", lauf_start.isoformat())
                .order("id").range(seite * SEITENGROESSE, seite * SEITENGROESSE + SEITENGROESSE - 1)
                .execute().data or [])
        events += teil
        if len(teil) < SEITENGROESSE:
            break
        seite += 1
    urls = urls_bauen(events, heute_berlin())
    if ortsseiten_melden_an():
        neue = {e["ort_id"] for e in events if e.get("ort_id")}
        try:
            urls += ortsseiten_urls(neue, _orte_laden(db, neue))
        except Exception as e:
            logger.warning("IndexNow: Ortsseiten nicht ermittelbar: %s", e)
    anzahl = melden(list(dict.fromkeys(urls)), dry_run)
    logger.info("IndexNow: %d neue Events → %d URLs gemeldet", len(events), anzahl)
    return anzahl


def orte_erstmeldung(dry_run: bool = False) -> int:
    """Alle indexierbaren Ortsseiten einmal melden (nach dem Deploy der Seiten). Zählt kommende Events je ort_id."""
    from database.client import get_supabase_client

    db = get_supabase_client()
    heute = heute_berlin().isoformat()
    orte, seite = [], 0
    while True:
        teil = (db.table("orte").select("id, slug, typ, aktiv, parent_id, adresse, spielstaette:extras->spielstaette")
                .eq("typ", "spielstaette").eq("aktiv", True).order("id")
                .range(seite * SEITENGROESSE, seite * SEITENGROESSE + SEITENGROESSE - 1).execute().data or [])
        orte += teil
        if len(teil) < SEITENGROESSE:
            break
        seite += 1
    zeilen = {o["id"]: o for o in orte}
    zeilen.update(_orte_laden(db, {o["parent_id"] for o in orte if o.get("parent_id")} - set(zeilen)))
    anzahl: dict[str, int] = {}
    seite = 0
    while True:
        teil = (db.table("events").select("ort_id").eq("abgelehnt", False).not_.is_("ort_id", "null")
                .or_(f"datum.gte.{heute},datum_bis.gte.{heute}").order("id")
                .range(seite * SEITENGROESSE, seite * SEITENGROESSE + SEITENGROESSE - 1).execute().data or [])
        for z in teil:
            anzahl[z["ort_id"]] = anzahl.get(z["ort_id"], 0) + 1
        if len(teil) < SEITENGROESSE:
            break
        seite += 1
    urls = [f"{SITE_URL}/orte"]
    for o in orte:
        p = o.get("spielstaette") or {}
        kinder = [k["id"] for k in orte if k.get("parent_id") == o["id"]]
        kommende = anzahl.get(o["id"], 0) + (0 if o.get("parent_id") else sum(anzahl.get(k, 0) for k in kinder))
        adresse = bool(p.get("adresse_bestaetigt"))
        haus = zeilen.get(o.get("parent_id") or "")
        if haus and not adresse:
            adresse = bool((haus.get("spielstaette") or {}).get("adresse_bestaetigt")) if haus.get("typ") == "spielstaette"                 else bool(haus.get("adresse"))
        if ort_indexierbar(adresse, bool(p.get("text_freigegeben")), kommende):
            urls.append(ort_url(o["slug"]))
    gemeldet = melden(urls, dry_run)
    logger.info("IndexNow: Erstmeldung Ortsseiten – %d URLs", gemeldet)
    return gemeldet


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser(description="Neue Event-URLs per IndexNow melden")
    parser.add_argument("--seit", help="ISO-Zeitpunkt (Standard: vor 24 Stunden)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--orte-erstmeldung", action="store_true",
                        help="Einmalig alle indexierbaren Ortsseiten melden (Deploy-Punkt 5, Plan Locations 3.11)")
    args = parser.parse_args()
    if args.orte_erstmeldung:
        orte_erstmeldung(args.dry_run)
        return
    seit = datetime.fromisoformat(args.seit) if args.seit else datetime.now(timezone.utc) - timedelta(hours=24)
    if seit.tzinfo is None:
        seit = seit.replace(tzinfo=timezone.utc)
    nach_lauf_melden(seit, args.dry_run)


if __name__ == "__main__":
    main()
