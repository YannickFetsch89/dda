"""
clubs.py – DiesDasDüsseldorf
Kandidaten und Import für den Guide-Hub „Clubs“ (Plan: docs/plan-clubs-2026-11-11.md).

Drei Unterarten (Entscheidung C1): club, kulturhaus (Konzert-/Kulturhaus mit regelmäßigen Partys),
partylocation (Partylokal). Gebiet: Düsseldorf, Neuss, Ratingen (C3).

Kandidaten kommen aus
  1. dem Zwischenspeicher der Flächensuche (data/orte/flaechensuche_clubs.json, Typ night_club),
  2. einer Startliste bekannter Orte (per Google Text Search aufgelöst, Ergebnis zwischengespeichert),
  3. unserem Eventkalender (Orte mit mehreren Nightlife-Events – nur als Hinweis in der Übersicht).

Nutzung:
  python -m scraper.orte.clubs kandidaten            # Übersicht, löst die Startliste auf (Text Search, Kosten!)
  python -m scraper.orte.clubs importieren [--dry-run]
"""
import argparse
import json
import logging
import re
import sys
import time
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.slug_generator import slug_mit_suffix  # noqa: E402
from scraper.orte import bars  # noqa: E402
from scraper.orte.flaechensuche import ort_stadtteil, stadt_von, vorab_score  # noqa: E402
from scraper.orte.google_places import (  # noqa: E402
    API_BASE,
    BAR_DETAIL_FELDER,
    _headers,
    _slug_erzeugen,
    alle_zeilen,
    ort_aus_place,
    place_details,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

_DATEN = Path(__file__).resolve().parents[2] / "data" / "orte"
FLAECHENSUCHE = _DATEN / "flaechensuche_clubs.json"
TEXTSUCHE = _DATEN / "clubs_textsuche.json"
PREIS_TEXTSUCHE = 32.0  # USD pro 1.000 (Text Search Pro), ohne Freikontingent
PREIS_DETAILS = 25.0

UNTERARTEN = ("club", "kulturhaus", "partylocation")

# Startliste: (Suchtext, Unterart). Geprüft 11.11.2026: mikroport.club, Odeon Tanzpalast (Krefeld) und
# Lizzy Lou (Bottrop) liegen außerhalb; Cube, Kassette, The Gate, Schlösser Quartier sind geschlossen.
# Die Unterart ist hier redaktionell gesetzt; Treffer werden über
# Text Search aufgelöst und nur übernommen, wenn der Name passt und der Ort nicht geschlossen ist.
STARTLISTE: list[tuple[str, str]] = [
    # Clubs
    ("Salon des Amateurs Düsseldorf", "club"),
    ("Rudas Studios Club Düsseldorf", "club"),
    ("Ampere Club Düsseldorf Ronsdorfer Straße", "club"),
    ("Nachtresidenz Düsseldorf", "club"),
    ("SUB Düsseldorf Club", "club"),
    ("Oh Baby Anna Düsseldorf", "club"),
    ("Bahndamm Düsseldorf Club", "club"),
    ("Gleiswerk Düsseldorf", "club"),
    ("Klub Kulb Düsseldorf", "club"),
    ("Tor 3 Düsseldorf", "club"),
    ("Kö Club Düsseldorf", "club"),
    ("Konvex Düsseldorf", "club"),
    ("Pitcher Düsseldorf Oberbilker Allee", "club"),
    ("Ratinger Hof Düsseldorf", "club"),
    ("Mauer Club Düsseldorf", "club"),
    ("Cube Club Düsseldorf", "club"),
    ("K1 Club & Bar Düsseldorf", "club"),
    ("Frank's Club Düsseldorf", "club"),
    ("Slash Club Düsseldorf", "club"),
    ("The Gate Club Düsseldorf", "club"),
    ("Mahiki Club Düsseldorf", "club"),
    ("Kassette Club Düsseldorf", "club"),
    ("Golzheimer Rheinterrasse Club", "club"),
    ("Smiley Club Düsseldorf", "club"),
    ("102 Club Düsseldorf", "club"),
    ("Velvet Club Düsseldorf", "club"),
    ("Revolution Nachtpalast", "club"),
    # Kulturhäuser mit Partys
    ("zakk Düsseldorf Fichtenstraße", "kulturhaus"),
    ("Stahlwerk Düsseldorf Ronsdorfer Straße", "kulturhaus"),
    ("Kulturschlachthof Düsseldorf", "kulturhaus"),
    ("Weltkunstzimmer Düsseldorf", "kulturhaus"),
    ("Schlösser Quartier Bohème Düsseldorf", "kulturhaus"),
    ("Tanzhaus NRW Düsseldorf", "kulturhaus"),
    ("The Eight Eventlocation Club Düsseldorf", "kulturhaus"),
    ("Graf Eventlocation Düsseldorf", "kulturhaus"),
    ("Kulturbahnhof Eller Düsseldorf", "kulturhaus"),
    # Partylocations
    ("Oberbayern Düsseldorf Altstadt", "partylocation"),
    ("Kuhstall Düsseldorf Altstadt", "partylocation"),
    ("Schlager Cafe Düsseldorf", "partylocation"),
    ("Giselle Düsseldorf Bar", "partylocation"),
    ("Schleuse Zwei Düsseldorf", "partylocation"),
    ("Wilma Wunder Düsseldorf", "partylocation"),
]

# Immer ausgeschlossen (C1): Erotik/Sauna/Swinger/Bordell, Shisha, Karaoke, DJ-Dienstleister, Tanzschulen …
AUSSCHLUSS_NAME = re.compile(
    r"erotik|bordell|sauna|swinger|privathaus|massage|lady |studio noir|domina|fetisch|bizarre|escort|girls|models"
    r"|shisha|hookah|karaoke|\bktv\b|\bdj\b|dj-service|event dj|tanzschule|streetdance|ticket|vape|zigarre|cigar"
    r"|stiftung|domizil|gr[äa]fin",  # Vereine bleiben: R25 heißt bei Google „Kultur-Schlachthof e.V.“
    re.IGNORECASE,
)
AUSSCHLUSS_TYPEN = {"massage", "beauty_salon", "sports_school", "store", "gym", "hookah_bar", "spa",
                    "sports_activity_location", "lodging", "hotel", "electrician"}
# Wer nur aus der Flächensuche kommt (nicht in der Startliste), braucht ein Mindestmaß an Bewertungen –
# sonst landen Privatpartys und Eintagsfliegen im Hub
MIN_BEWERTUNGEN_FLAECHE = 25


def _name(place: dict) -> str:
    return (place.get("displayName") or {}).get("text") or ""


def ausgeschlossen(place: dict) -> str | None:
    """Grund für den Ausschluss (C1) oder None."""
    if place.get("businessStatus") not in (None, "OPERATIONAL"):
        return "geschlossen"
    if AUSSCHLUSS_NAME.search(_name(place)):
        return "Name (Erotik/Shisha/Karaoke/Dienstleister …)"
    typen = set(place.get("types") or []) | {place.get("primaryType") or ""}
    if typen & AUSSCHLUSS_TYPEN:
        return "Typ " + ", ".join(sorted(typen & AUSSCHLUSS_TYPEN))
    if not stadt_von(place):
        return "außerhalb (nicht Düsseldorf/Neuss/Ratingen)"
    return None


def unterart_regel(place: dict) -> str:
    """Unterart aus dem Google-Typ, wenn die Startliste nichts vorgibt."""
    p = place.get("primaryType") or ""
    if p == "night_club":
        return "club"
    if p in ("event_venue", "live_music_venue", "cultural_center", "performing_arts_theater", "concert_hall"):
        return "kulturhaus"
    return "partylocation"


# ── Text Search (Startliste) ──────────────────────────────────────────────────

_SUCH_MASKE = ",".join(f"places.{f}" for f in (
    "id", "displayName", "formattedAddress", "location", "rating", "userRatingCount",
    "primaryType", "types", "businessStatus",
))


def _norm(text: str) -> str:
    t = (text or "").lower().translate(str.maketrans("äöüß", "aous"))
    return re.sub(r"[^a-z0-9]", "", t)


def name_passt(suchtext: str, place: dict) -> bool:
    """Der Treffer muss das Kernwort der Suche im Namen tragen (sonst liefert Google irgendeinen Ort)."""
    kern = suchtext.split(" Düsseldorf")[0]
    kern = re.sub(r"\b(club|bar|eventlocation|altstadt)\b", "", kern, flags=re.IGNORECASE).strip() or kern
    woerter = [w for w in re.findall(r"[\wäöüß.'/]+", kern.lower()) if len(_norm(w)) >= 3]
    name = _norm(_name(place))
    return bool(woerter) and all(_norm(w) in name for w in woerter[:2])


def textsuche(suchtext: str, cache: dict) -> dict | None:
    """Ein Treffer zur Startliste (zwischengespeichert, jede Anfrage kostet)."""
    if suchtext in cache:
        return cache[suchtext]
    from scraper.orte.google_places import GOOGLE_PLACES_API_KEY

    if not GOOGLE_PLACES_API_KEY:
        logger.error("GOOGLE_PLACES_API_KEY fehlt – Text Search nicht möglich")
        return None
    treffer = None
    try:
        time.sleep(0.5)
        antwort = httpx.post(
            f"{API_BASE}/places:searchText",
            json={"textQuery": suchtext, "languageCode": "de", "maxResultCount": 3,
                  "locationBias": {"circle": {"center": {"latitude": 51.2277, "longitude": 6.7735}, "radius": 20000}}},
            headers=_headers(_SUCH_MASKE),
            timeout=30,
        )
        antwort.raise_for_status()
        for p in antwort.json().get("places") or []:
            if name_passt(suchtext, p):
                treffer = p
                break
    except Exception as e:
        logger.warning("Text Search für '%s' fehlgeschlagen: %s", suchtext, e)
        return None  # nicht zwischenspeichern, beim nächsten Lauf erneut versuchen
    cache[suchtext] = treffer
    TEXTSUCHE.parent.mkdir(parents=True, exist_ok=True)
    TEXTSUCHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return treffer


# ── Kandidaten ────────────────────────────────────────────────────────────────

def kandidaten_sammeln(mit_textsuche: bool = True) -> tuple[list[dict], list[tuple[str, str]]]:
    """
    (Kandidaten, Ausgeschlossene) – jeder Kandidat ist ein Google-Place mit _unterart, _herkunft.
    Startliste vor Flächensuche (die redaktionelle Unterart gewinnt).
    """
    cache = json.loads(TEXTSUCHE.read_text(encoding="utf-8")) if TEXTSUCHE.exists() else {}
    gesammelt: dict[str, dict] = {}
    raus: list[tuple[str, str]] = []

    for suchtext, art in STARTLISTE:
        p = textsuche(suchtext, cache) if mit_textsuche else cache.get(suchtext)
        if not p:
            raus.append((suchtext, "kein passender Google-Treffer"))
            continue
        grund = ausgeschlossen(p)
        if grund:
            raus.append((_name(p), grund))
            continue
        gesammelt.setdefault(p["id"], {**p, "_unterart": art, "_herkunft": "Startliste"})

    flaeche = json.loads(FLAECHENSUCHE.read_text(encoding="utf-8")).get("orte", {}) if FLAECHENSUCHE.exists() else {}
    for p in flaeche.values():
        if p["id"] in gesammelt or p.get("primaryType") != "night_club":
            continue
        grund = ausgeschlossen(p)
        if not grund and (p.get("userRatingCount") or 0) < MIN_BEWERTUNGEN_FLAECHE:
            grund = f"zu wenige Bewertungen ({p.get('userRatingCount') or 0})"
        if grund:
            raus.append((_name(p), grund))
            continue
        gesammelt[p["id"]] = {**p, "_unterart": unterart_regel(p), "_herkunft": "Flächensuche"}

    liste = sorted(gesammelt.values(), key=lambda p: (UNTERARTEN.index(p["_unterart"]), -(p.get("userRatingCount") or 0)))
    return liste, raus


def nightlife_orte_im_kalender(db, min_events: int = 4) -> list[tuple[str, int]]:
    """Orte mit mehreren Nightlife-Events (letzte 120 Tage + kommende) – Hinweis auf fehlende Kandidaten."""
    ab = (date.today() - timedelta(days=120)).isoformat()
    zeilen = alle_zeilen(db, "events", "ort, kategorie, datum", lambda q: q.eq("kategorie", "nightlife").gte("datum", ab))
    zaehler = Counter(z["ort"] for z in zeilen if z.get("ort"))
    return [(o, n) for o, n in zaehler.most_common() if n >= min_events]


def uebersicht(mit_textsuche: bool) -> None:
    from database.client import get_supabase_client

    db = get_supabase_client()
    liste, raus = kandidaten_sammeln(mit_textsuche)
    bestand = {o["google_place_id"]: o for o in alle_zeilen(db, "orte", "google_place_id, name, typ, extras")
               if o.get("google_place_id")}
    print(f"\n{len(liste)} Kandidaten:")
    for p in liste:
        da = bestand.get(p["id"])
        hinweis = f"  [schon da: {da['typ']} → auch_club]" if da else ""
        print(f"  {p['_unterart']:13s} {_name(p)[:42]:42s} {p.get('primaryType') or '-':22s} "
              f"{p.get('rating') or '-'}★ {p.get('userRatingCount') or 0:5d}  {p['_herkunft']}{hinweis}")
    print(f"\nAusgeschlossen ({len(raus)}):")
    for name, grund in raus:
        print(f"  {name[:50]:50s} {grund}")
    namen = {_norm(_name(p)) for p in liste}
    print("\nNightlife-Orte im Kalender ohne Kandidat (prüfen):")
    for ort, n in nightlife_orte_im_kalender(db):
        if not any(k and (k in _norm(ort) or _norm(ort) in k) for k in namen):
            print(f"  {n:3d}  {ort}")


# ── Import ────────────────────────────────────────────────────────────────────

def importieren(dry_run: bool) -> dict:
    """Neue Kandidaten mit Details als typ='club' (inaktiv) anlegen; vorhandene Orte nur markieren (auch_club)."""
    from database.client import get_supabase_client

    db = get_supabase_client()
    liste, _ = kandidaten_sammeln(mit_textsuche=False)
    bestehend = alle_zeilen(db, "orte", "id, google_place_id, slug, typ, extras")
    nach_id = {o["google_place_id"]: o for o in bestehend if o.get("google_place_id")}
    slugs = {o["slug"] for o in bestehend}
    neu = [p for p in liste if p["id"] not in nach_id]
    markieren = [p for p in liste if p["id"] in nach_id and nach_id[p["id"]]["typ"] != "club"]
    logger.info("%d neue Clubs (Details ca. %.2f $), %d vorhandene Orte bekommen auch_club%s",
                len(neu), len(neu) * PREIS_DETAILS / 1000, len(markieren), " [Dry-Run]" if dry_run else "")
    if dry_run:
        return {"neu": len(neu), "markieren": len(markieren)}

    for p in markieren:
        o = nach_id[p["id"]]
        extras = {**(o.get("extras") or {}), "auch_club": True, "club_unterart": p["_unterart"]}
        db.table("orte").update({"extras": extras}).eq("id", o["id"]).execute()

    gespeichert = fehler = 0
    for p in neu:
        name = _name(p)
        try:
            place = {**p, **place_details(p["id"], BAR_DETAIL_FELDER)}
            ort = ort_aus_place(place, "club", hotel_erlaubt=True, bewertung_filtern=False)
            if not ort:
                logger.info("  übersprungen: %s", name)
                continue
            ort["typ"] = "club"
            ort["stadtteil"] = ort_stadtteil(name, ort.get("adresse"), stadt_von(p))
            ort["slug"] = slug_mit_suffix(_slug_erzeugen(name, ort["stadtteil"]), slugs)
            score, gewichtet, _ = vorab_score(place)
            ort["qualitaets_score"] = None  # setzt erst der Club-Score (clubs_profil.py)
            ort["extras"] = {
                **ort.get("extras", {}),
                "hub": "clubs",
                "unterart": p["_unterart"],
                "google_primaertyp": p.get("primaryType"),
                "vorab_score": gewichtet,
                "quelle": "clubs_" + ("startliste" if p["_herkunft"] == "Startliste" else "flaechensuche"),
            }
            db.table("orte").insert(ort).execute()
            slugs.add(ort["slug"])
            gespeichert += 1
        except Exception as e:
            fehler += 1
            logger.error("Fehler bei '%s': %s", name, e)
    logger.info("Import fertig: %d gespeichert, %d markiert, %d Fehler", gespeichert, len(markieren), fehler)
    return {"gespeichert": gespeichert, "markiert": len(markieren), "fehler": fehler}


def main():
    parser = argparse.ArgumentParser(description="Club-Hub: Kandidaten und Import")
    sub = parser.add_subparsers(dest="befehl", required=True)
    k = sub.add_parser("kandidaten", help="Übersicht (löst die Startliste per Text Search auf)")
    k.add_argument("--ohne-suche", action="store_true", help="Nur Zwischenspeicher, keine neuen Text-Search-Anfragen")
    i = sub.add_parser("importieren", help="Neue Clubs mit Details anlegen (inaktiv)")
    i.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.befehl == "kandidaten":
        uebersicht(not args.ohne_suche)
    else:
        importieren(args.dry_run)


if __name__ == "__main__":
    main()
