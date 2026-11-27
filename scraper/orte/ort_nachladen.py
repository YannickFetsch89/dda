"""
ort_nachladen.py – DiesDasDüsseldorf
Einzelnen Ort für den Restaurant-Guide gezielt nachladen (Wunsch des Auftraggebers, z. B. eine zweite Filiale,
die die Flächensuche nicht gefunden hat). Angelegt wird genau wie beim Import der Flächensuche
(flaechensuche.importieren): Place Details, ort_aus_place, Stadtteil, Slug, Vorab-Score, typ_verfeinern.

Nutzung (im Repo-Stamm, Python aus DD/.venv):
  python -m scraper.orte.ort_nachladen --suche "Kochi Bismarckstraße Düsseldorf"   → Treffer anzeigen (1 Abruf)
  python -m scraper.orte.ort_nachladen --place-id <ID> --trocken                     → nur anzeigen
  python -m scraper.orte.ort_nachladen --place-id <ID> [--aktiv]                     → anlegen (Standard inaktiv)

Der Google-Key steht nie im Log (bei Fehlern nur der Fehlertyp).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Schlüssel wie bei der Bild-Auswahlseite aus web/.env.local, bevor config/database sie lesen
load_dotenv(Path("web/.env.local"))
load_dotenv()
if not os.environ.get("SUPABASE_KEY") and os.environ.get("SUPABASE_SERVICE_KEY"):
    os.environ["SUPABASE_KEY"] = os.environ["SUPABASE_SERVICE_KEY"]
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import httpx  # noqa: E402

from pipeline.slug_generator import slug_mit_suffix  # noqa: E402
from scraper.orte import flaechensuche as fs  # noqa: E402
from scraper.orte.google_places import (  # noqa: E402
    API_BASE, _headers, _slug_erzeugen, alle_zeilen, ort_aus_place, place_details,
)
from scraper.orte.imbiss import typ_verfeinern  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

SUCH_FELDER = "places.id,places.displayName,places.formattedAddress,places.primaryType,places.rating,places.userRatingCount,places.businessStatus"


def suchen(text: str) -> list[dict]:
    """Text Search (New) – höchstens 5 Treffer im Raum Düsseldorf."""
    try:
        with httpx.Client(timeout=30) as c:
            r = c.post(f"{API_BASE}/places:searchText", headers=_headers(SUCH_FELDER),
                       json={"textQuery": text, "languageCode": "de", "regionCode": "DE", "maxResultCount": 5,
                             "locationBias": {"circle": {"center": {"latitude": 51.2277, "longitude": 6.7735}, "radius": 20000}}})
            r.raise_for_status()
            return r.json().get("places", [])
    except Exception as fehler:  # noqa: BLE001 – nur den Typ loggen (Key steht in der Anfrage)
        logger.error("Suche fehlgeschlagen (%s)", type(fehler).__name__)
        return []


def anlegen(place_id: str, aktiv: bool, trocken: bool) -> int:
    from database.client import get_supabase_client

    db = get_supabase_client()
    bestehend = alle_zeilen(db, "orte", "id, google_place_id, slug, name")
    doppelt = [o for o in bestehend if o.get("google_place_id") == place_id]
    if doppelt:
        logger.error("Schon vorhanden: %s (%s)", doppelt[0]["name"], doppelt[0]["slug"])
        return 1
    try:
        place = place_details(place_id)
    except Exception as fehler:  # noqa: BLE001
        logger.error("Place Details fehlgeschlagen (%s)", type(fehler).__name__)
        return 1
    typ = fs.ort_typ(place) or "restaurant"
    ort = ort_aus_place(place, typ)
    if not ort:
        logger.error("Ort passt nicht (Ausschlusstyp oder fehlende Daten)")
        return 1
    name = place["displayName"]["text"]
    score, gewichtet, kette = fs.vorab_score(place)
    ort["typ"] = typ
    ort["stadtteil"] = fs.ort_stadtteil(name, ort.get("adresse"), fs.stadt_von(place))
    ort["slug"] = slug_mit_suffix(_slug_erzeugen(name, ort["stadtteil"]), {o["slug"] for o in bestehend})
    ort["qualitaets_score"] = score
    ort["extras"] = {**ort.get("extras", {}), "vorab_score": gewichtet, "kette": kette,
                     "google_primaertyp": place.get("primaryType"), "quelle": "nachgeladen"}
    ort["typ"] = typ_verfeinern(ort)
    ort["aktiv"] = aktiv
    kurz = {k: ort.get(k) for k in ("name", "typ", "stadtteil", "slug", "adresse", "qualitaets_score", "aktiv", "tags")}
    print(json.dumps(kurz, ensure_ascii=False, indent=1))
    if trocken:
        logger.info("Trockenlauf – nichts gespeichert")
        return 0
    neu = db.table("orte").insert(ort).execute().data
    logger.info("Angelegt: %s (id %s)", name, neu[0]["id"] if neu else "?")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Einzelnen Ort für den Restaurant-Guide nachladen")
    p.add_argument("--suche", help="Suchtext für die Google-Textsuche")
    p.add_argument("--place-id", help="Google Place ID des anzulegenden Ortes")
    p.add_argument("--aktiv", action="store_true", help="gleich sichtbar anlegen (sonst inaktiv)")
    p.add_argument("--trocken", action="store_true", help="nichts speichern")
    a = p.parse_args()
    fs.hub_setzen("restaurants")
    if a.suche:
        for t in suchen(a.suche):
            print(f"{t['id']} | {t['displayName']['text']} | {t.get('formattedAddress')} | {t.get('primaryType')} | "
                  f"{t.get('rating')} ({t.get('userRatingCount')}) | {t.get('businessStatus')}")
        return 0
    if a.place_id:
        return anlegen(a.place_id, a.aktiv, a.trocken)
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
