"""
flaechensuche.py – DiesDasDüsseldorf
Flächendeckende Suche nach Restaurants und Cafés in Düsseldorf über die Google Places API (New).

Problem: Nearby Search liefert pro Anfrage höchstens 20 Orte und hat keine weiteren Seiten.
Ein einziger großer Kreis um die Stadtmitte findet daher nur die 20 bekanntesten Orte.

Lösung (Quadtree): Das Stadtgebiet wird in Zellen zerlegt. Liefert eine Zelle die vollen 20
Treffer, gibt es dort vermutlich mehr – die Zelle wird geviertelt und erneut abgefragt.
Zellen mit weniger als 20 Treffern sind vollständig. So wird nur dort fein gesucht, wo es dicht ist.

Ablauf in zwei Schritten (getrennt, damit vor dem teureren Teil geprüft werden kann):
  1. suchen       – Flächensuche, Kandidaten landen im lokalen Zwischenspeicher (nicht in der DB).
                    Unterbrochene Läufe werden fortgesetzt.
  2. importieren  – lädt für die besten Kandidaten die Details (Beschreibung, Foto, Ausstattung)
                    und speichert sie in der Tabelle `orte` (aktiv = false, mit Vorab-Score).
  auswertung      – zeigt, was im Zwischenspeicher liegt (kostenlos).

Nutzung:
  python -m scraper.orte.flaechensuche suchen [--max-anfragen 900] [--neu]
  python -m scraper.orte.flaechensuche auswertung
  python -m scraper.orte.flaechensuche importieren [--max 900] [--min-score 1] [--dry-run]

Kosten: Preise unten in PREIS_*. Google gewährt je Abfrageart 1.000 kostenlose Abrufe pro Monat;
die Schätzungen hier rechnen konservativ OHNE Freikontingent.
"""
import argparse
import json
import logging
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import (  # noqa: E402
    GOOGLE_PLACES_API_KEY,
    GOOGLE_PLACES_MIN_BEWERTUNGEN,
    GOOGLE_PLACES_MIN_RATING,
)
from pipeline.slug_generator import slug_mit_suffix  # noqa: E402
from scraper.orte.google_places import (  # noqa: E402
    API_BASE,
    _AUSSCHLUSS_TYPEN,
    ort_aus_place,
    place_details,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ── Konfiguration ─────────────────────────────────────────────────────────────

# Rechteck um das Stadtgebiet Düsseldorf (etwas großzügiger; Orte außerhalb werden über die Adresse aussortiert)
GEBIET = {"sued": 51.124, "nord": 51.353, "west": 6.688, "ost": 6.940}
START_ZELLE_KM = 3.0      # Kantenlänge der Startzellen
MIN_ZELLE_KM = 0.3        # feiner wird nicht geteilt
MAX_TREFFER = 20          # Obergrenze der API pro Anfrage

SUCH_TYPEN = ["restaurant", "cafe", "coffee_shop"]

# Felder der Suche: nur was zum Filtern nötig ist (Enterprise-Stufe, ohne teure Atmosphere-Felder)
SUCH_FELDER = ",".join(f"places.{f}" for f in (
    "id", "displayName", "formattedAddress", "location", "rating", "userRatingCount",
    "primaryType", "types", "businessStatus",
))

# Preise in USD pro 1.000 Abrufe (Stand Nov. 2026, ohne Freikontingent von je 1.000/Monat)
PREIS_SUCHE = 35.0
PREIS_DETAILS = 25.0

ZWISCHENSPEICHER = Path(__file__).resolve().parents[2] / "data" / "orte" / "flaechensuche.json"

# Primärtypen, die als Café gelten; Restaurants: "restaurant" oder "*_restaurant" und einige Sonderfälle
CAFE_TYPEN = {
    "cafe", "coffee_shop", "tea_house", "dessert_shop", "ice_cream_shop", "confectionery",
    "chocolate_shop", "juice_shop", "donut_shop", "bagel_shop", "acai_shop", "cat_cafe", "bakery",
    "pastry_shop", "coffee_roastery",
}
RESTAURANT_SONDERTYPEN = {
    "bar_and_grill", "diner", "deli", "bistro", "gastropub", "food_court",
    "steak_house", "brewpub", "sandwich_shop", "kebab_shop",
}
# Bewusst NICHT enthalten: meal_takeaway, snack_bar, pizza_delivery (Imbiss/Lieferdienst),
# bar, pub, beer_garden (kommen in den Kneipen-Guide)

# Ketten werden nicht ausgeschlossen, aber im Vorab-Score nach hinten sortiert
KETTEN = re.compile(
    r"\b(starbucks|mcdonald|burger king|kfc|subway|vapiano|l'osteria|cafe extrablatt|coffee fellows|"
    r"back ?werk|kamps|dean ?& ?david|hans im gl[üu]ck|peter pane|five guys|nordsee|tchibo|"
    r"woolworth|ikea|rossmann|domino|pizza hut|call a pizza|smashburger|wienerwald|block house|"
    r"maredo|alex|enchilada|sausalitos|bulls ?& ?bears|coffee ?shop company|balzac|einstein kaffee|"
    r"espresso house|yormas|ditsch|le crobag|kochl[öo]ffel|cinnamood|jim block|dunkin)\b",
    re.IGNORECASE,
)

DUESSELDORF_ADRESSE = re.compile(r"\b40\d{3}\s+Düsseldorf\b")


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _km_zu_grad(km: float, breite: float) -> tuple[float, float]:
    """Kilometer → (Grad Breite, Grad Länge) an der gegebenen geographischen Breite."""
    return km / 111.32, km / (111.32 * math.cos(math.radians(breite)))


def _startzellen() -> list[dict]:
    """Zerlegt das Gebiet in quadratische Startzellen."""
    d_lat, d_lng = _km_zu_grad(START_ZELLE_KM, (GEBIET["sued"] + GEBIET["nord"]) / 2)
    zellen = []
    lat = GEBIET["sued"]
    while lat < GEBIET["nord"]:
        lng = GEBIET["west"]
        while lng < GEBIET["ost"]:
            zellen.append({"lat": lat + d_lat / 2, "lng": lng + d_lng / 2, "km": START_ZELLE_KM})
            lng += d_lng
        lat += d_lat
    return zellen


def _viertel(zelle: dict) -> list[dict]:
    """Teilt eine Zelle in vier gleich große Unterzellen."""
    km = zelle["km"] / 2
    d_lat, d_lng = _km_zu_grad(km / 2, zelle["lat"])
    return [
        {"lat": zelle["lat"] + s_lat * d_lat, "lng": zelle["lng"] + s_lng * d_lng, "km": km}
        for s_lat in (-1, 1) for s_lng in (-1, 1)
    ]


def _zell_schluessel(zelle: dict) -> str:
    return f"{zelle['lat']:.5f},{zelle['lng']:.5f},{zelle['km']:.4f}"


def ort_typ(place: dict) -> str | None:
    """Ordnet den Google-Primärtyp unserem Typ zu (None = weder Restaurant noch Café)."""
    primaer = place.get("primaryType") or ""
    if primaer in CAFE_TYPEN:
        return "cafe"
    if primaer == "restaurant" or primaer.endswith("_restaurant") or primaer in RESTAURANT_SONDERTYPEN:
        return "restaurant"
    return None


def ist_kandidat(place: dict) -> tuple[bool, str]:
    """Prüft, ob ein Suchtreffer in den Kandidaten-Pool gehört. Gibt (ja/nein, Grund) zurück."""
    if place.get("businessStatus") not in (None, "OPERATIONAL"):
        return False, "geschlossen"
    if not DUESSELDORF_ADRESSE.search(place.get("formattedAddress") or ""):
        return False, "außerhalb"
    if set(place.get("types") or []) & _AUSSCHLUSS_TYPEN:
        return False, "Ausschlusstyp"
    if not ort_typ(place):
        return False, "kein Restaurant/Café"
    if (place.get("rating") or 0) < GOOGLE_PLACES_MIN_RATING:
        return False, "Bewertung zu niedrig"
    if (place.get("userRatingCount") or 0) < GOOGLE_PLACES_MIN_BEWERTUNGEN:
        return False, "zu wenige Bewertungen"
    return True, "ok"


def vorab_score(place: dict) -> tuple[int, float, bool]:
    """
    Vorab-Score 1–10 für die Kuration.

    Grundlage ist eine gewichtete Bewertung (Bayes-Mittel): Viele Bewertungen machen den
    Sternedurchschnitt verlässlicher; 4,9★ bei 35 Bewertungen zählt weniger als 4,7★ bei 2.000.
    Ketten werden auf höchstens 3 begrenzt.

    Returns:
        (score 1–10, gewichtete Bewertung, ist_kette)
    """
    r = float(place.get("rating") or 0)
    n = int(place.get("userRatingCount") or 0)
    m, c = 150, 4.2  # Gewicht und Durchschnitt, zu dem wenige Bewertungen hingezogen werden
    gewichtet = (n / (n + m)) * r + (m / (n + m)) * c
    score = round((gewichtet - 3.9) / (4.8 - 3.9) * 9 + 1)
    score = max(1, min(10, score))
    name = (place.get("displayName") or {}).get("text", "")
    kette = bool(KETTEN.search(name))
    if kette:
        score = min(score, 3)
    return score, round(gewichtet, 3), kette


# ── Zwischenspeicher ──────────────────────────────────────────────────────────

def speicher_laden() -> dict:
    if ZWISCHENSPEICHER.exists():
        return json.loads(ZWISCHENSPEICHER.read_text(encoding="utf-8"))
    return {}


def speicher_schreiben(daten: dict) -> None:
    ZWISCHENSPEICHER.parent.mkdir(parents=True, exist_ok=True)
    tmp = ZWISCHENSPEICHER.with_suffix(".tmp")
    tmp.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
    tmp.replace(ZWISCHENSPEICHER)


# ── Schritt 1: Flächensuche ───────────────────────────────────────────────────

def _zelle_abfragen(client: httpx.Client, zelle: dict) -> list[dict]:
    """Eine Nearby-Search-Anfrage für eine Zelle (Kreis um den Mittelpunkt, deckt das Quadrat ab)."""
    radius_m = zelle["km"] * 1000 * math.sqrt(2) / 2
    body = {
        "includedTypes": SUCH_TYPEN,
        "maxResultCount": MAX_TREFFER,
        "locationRestriction": {"circle": {
            "center": {"latitude": zelle["lat"], "longitude": zelle["lng"]},
            "radius": round(radius_m, 1),
        }},
        "languageCode": "de",
        "regionCode": "DE",
    }
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY, "X-Goog-FieldMask": SUCH_FELDER}
    for versuch in range(4):
        time.sleep(0.5)  # Rate Limiting
        resp = client.post(f"{API_BASE}/places:searchNearby", json=body, headers=headers)
        if resp.status_code == 429:
            warten = 2 ** (versuch + 2)
            logger.warning("HTTP 429 – warte %d s", warten)
            time.sleep(warten)
            continue
        resp.raise_for_status()
        return resp.json().get("places", [])
    raise RuntimeError("Zu viele HTTP-429-Antworten, Suche unterbrochen")


def suchen(max_anfragen: int, neu: bool = False) -> dict:
    """Führt die Flächensuche aus bzw. setzt eine unterbrochene fort."""
    daten = {} if neu else speicher_laden()
    if not daten:
        daten = {
            "gestartet": datetime.now(timezone.utc).isoformat(),
            "warteschlange": _startzellen(),
            "erledigt": [],
            "anfragen": 0,
            "gesaettigt_min": 0,
            "orte": {},
        }
        logger.info("Neue Flächensuche: %d Startzellen à %.1f km", len(daten["warteschlange"]), START_ZELLE_KM)
    else:
        logger.info(
            "Setze Flächensuche fort: %d Anfragen bisher, %d Zellen offen, %d Orte gefunden",
            daten["anfragen"], len(daten["warteschlange"]), len(daten["orte"]),
        )

    erledigt = set(daten["erledigt"])
    anfragen_dieser_lauf = 0

    with httpx.Client(timeout=30) as client:
        while daten["warteschlange"] and anfragen_dieser_lauf < max_anfragen:
            zelle = daten["warteschlange"].pop(0)
            schluessel = _zell_schluessel(zelle)
            if schluessel in erledigt:
                continue
            try:
                treffer = _zelle_abfragen(client, zelle)
            except httpx.HTTPStatusError as e:
                daten["warteschlange"].insert(0, zelle)
                speicher_schreiben(daten)
                logger.error("API-Fehler, Suche angehalten (Fortsetzen möglich): %s", e.response.text[:300])
                break
            daten["anfragen"] += 1
            anfragen_dieser_lauf += 1

            in_ddf = 0
            for p in treffer:
                if DUESSELDORF_ADRESSE.search(p.get("formattedAddress") or ""):
                    in_ddf += 1
                daten["orte"][p["id"]] = p

            # Volle Zelle mit Düsseldorfer Treffern → vierteln (außerhalb der Stadt nicht weiter verfeinern)
            if len(treffer) >= MAX_TREFFER and in_ddf > 0:
                if zelle["km"] / 2 >= MIN_ZELLE_KM:
                    daten["warteschlange"].extend(_viertel(zelle))
                else:
                    daten["gesaettigt_min"] += 1

            erledigt.add(schluessel)
            daten["erledigt"].append(schluessel)
            if daten["anfragen"] % 10 == 0:
                speicher_schreiben(daten)
                logger.info(
                    "  %d Anfragen | %d Zellen offen | %d Orte gefunden",
                    daten["anfragen"], len(daten["warteschlange"]), len(daten["orte"]),
                )

    speicher_schreiben(daten)
    fertig = not daten["warteschlange"]
    logger.info(
        "Suche %s: %d Anfragen gesamt (ca. %.2f $ ohne Freikontingent), %d Orte gefunden%s",
        "abgeschlossen" if fertig else "pausiert (Limit erreicht – erneut aufrufen zum Fortsetzen)",
        daten["anfragen"], daten["anfragen"] * PREIS_SUCHE / 1000, len(daten["orte"]),
        f", {daten['gesaettigt_min']} Kleinstzellen waren noch voll" if daten["gesaettigt_min"] else "",
    )
    return daten


# ── Auswertung ────────────────────────────────────────────────────────────────

def kandidaten(daten: dict) -> list[dict]:
    """Alle Treffer, die die Filter bestehen, mit Typ und Vorab-Score, beste zuerst."""
    liste = []
    for p in daten.get("orte", {}).values():
        ok, _ = ist_kandidat(p)
        if not ok:
            continue
        score, gewichtet, kette = vorab_score(p)
        liste.append({**p, "_typ": ort_typ(p), "_score": score, "_gewichtet": gewichtet, "_kette": kette})
    liste.sort(key=lambda p: (p["_kette"], -p["_gewichtet"]))
    return liste


def auswertung() -> None:
    """Zeigt Umfang und Zusammensetzung des Kandidaten-Pools (kostenlos, nur Zwischenspeicher)."""
    from collections import Counter

    daten = speicher_laden()
    if not daten:
        logger.info("Noch keine Flächensuche gelaufen.")
        return
    gruende = Counter(ist_kandidat(p)[1] for p in daten["orte"].values())
    liste = kandidaten(daten)
    from pipeline.stadtteil_mapper import stadtteil_ermitteln

    print(f"\nAnfragen: {daten['anfragen']} (ca. {daten['anfragen'] * PREIS_SUCHE / 1000:.2f} $) | "
          f"offene Zellen: {len(daten['warteschlange'])}")
    print(f"Treffer gesamt: {len(daten['orte'])}")
    for grund, n in gruende.most_common():
        print(f"  {grund:24s} {n:5d}")
    print(f"\nKandidaten: {len(liste)}  (Restaurants: {sum(p['_typ'] == 'restaurant' for p in liste)}, "
          f"Cafés: {sum(p['_typ'] == 'cafe' for p in liste)}, davon Ketten: {sum(p['_kette'] for p in liste)})")
    print("Vorab-Score:", dict(sorted(Counter(p["_score"] for p in liste).items(), reverse=True)))
    stadtteile = Counter(stadtteil_ermitteln(p["displayName"]["text"], p.get("formattedAddress")) or "?" for p in liste)
    print("Stadtteile:", ", ".join(f"{s} {n}" for s, n in stadtteile.most_common(15)), "…")
    print(f"Details für alle Kandidaten: ca. {len(liste) * PREIS_DETAILS / 1000:.2f} $ (ohne Freikontingent)\n")
    print("Top 15:")
    for p in liste[:15]:
        print(f"  {p['_score']:2d}  {p['displayName']['text'][:40]:40s} {p['_typ']:10s} "
              f"★{p.get('rating')} ({p.get('userRatingCount')})")


# ── Schritt 2: Import ─────────────────────────────────────────────────────────

def importieren(max_anzahl: int, min_score: int, dry_run: bool) -> dict:
    """Lädt Details für die besten neuen Kandidaten und speichert sie inaktiv in `orte`."""
    from database.client import get_supabase_client

    daten = speicher_laden()
    if not daten:
        logger.error("Kein Zwischenspeicher – zuerst 'suchen' ausführen.")
        return {}
    if daten.get("warteschlange"):
        logger.warning("Flächensuche ist noch nicht abgeschlossen (%d Zellen offen).", len(daten["warteschlange"]))

    db = get_supabase_client()
    bestehend = db.table("orte").select("google_place_id, slug").execute().data or []
    bekannte_ids = {o["google_place_id"] for o in bestehend if o.get("google_place_id")}
    vergebene_slugs = {o["slug"] for o in bestehend}

    neu = [p for p in kandidaten(daten) if p["id"] not in bekannte_ids and p["_score"] >= min_score]
    auswahl = neu[:max_anzahl]
    logger.info(
        "%d neue Kandidaten (Score ≥ %d), importiere %d → Details ca. %.2f $ (ohne Freikontingent)%s",
        len(neu), min_score, len(auswahl), len(auswahl) * PREIS_DETAILS / 1000, " [Dry-Run]" if dry_run else "",
    )
    if dry_run:
        for p in auswahl[:25]:
            print(f"  {p['_score']:2d}  {p['displayName']['text'][:45]:45s} {p['_typ']}")
        if len(auswahl) > 25:
            print(f"  … und {len(auswahl) - 25} weitere")
        return {"geplant": len(auswahl)}

    gespeichert = fehler = 0
    for i, p in enumerate(auswahl, 1):
        name = p["displayName"]["text"]
        try:
            place = {**p, **place_details(p["id"])}
            ort = ort_aus_place(place, p["_typ"])
            if not ort:
                continue
            ort["typ"] = p["_typ"]
            ort["slug"] = slug_mit_suffix(ort["slug"], vergebene_slugs)
            ort["qualitaets_score"] = p["_score"]
            ort["extras"] = {
                **ort.get("extras", {}),
                "vorab_score": p["_gewichtet"],
                "kette": p["_kette"],
                "google_primaertyp": p.get("primaryType"),
                "quelle": "flaechensuche",
            }
            db.table("orte").insert(ort).execute()
            vergebene_slugs.add(ort["slug"])
            gespeichert += 1
        except Exception as e:
            fehler += 1
            logger.error("Fehler bei '%s': %s", name, e)
        if i % 25 == 0:
            logger.info("  %d/%d verarbeitet (%d gespeichert, %d Fehler)", i, len(auswahl), gespeichert, fehler)

    logger.info("Import fertig: %d gespeichert | %d Fehler", gespeichert, fehler)
    return {"gespeichert": gespeichert, "fehler": fehler}


def main():
    parser = argparse.ArgumentParser(description="Flächendeckende Restaurant-/Café-Suche für Düsseldorf")
    befehle = parser.add_subparsers(dest="befehl", required=True)

    p_suchen = befehle.add_parser("suchen", help="Flächensuche ausführen/fortsetzen")
    p_suchen.add_argument("--max-anfragen", type=int, default=900, help="Höchstzahl Suchanfragen in diesem Lauf")
    p_suchen.add_argument("--neu", action="store_true", help="Zwischenspeicher verwerfen und neu beginnen")

    befehle.add_parser("auswertung", help="Kandidaten-Pool anzeigen (kostenlos)")

    p_import = befehle.add_parser("importieren", help="Details laden und in Supabase speichern")
    p_import.add_argument("--max", type=int, default=900, help="Höchstzahl Orte (= Detail-Abrufe)")
    p_import.add_argument("--min-score", type=int, default=1, help="Nur Kandidaten ab diesem Vorab-Score")
    p_import.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts abrufen oder speichern")

    args = parser.parse_args()
    if args.befehl != "auswertung" and not GOOGLE_PLACES_API_KEY:
        logger.error("GOOGLE_PLACES_API_KEY fehlt in .env")
        sys.exit(1)

    if args.befehl == "suchen":
        suchen(args.max_anfragen, args.neu)
    elif args.befehl == "auswertung":
        auswertung()
    else:
        importieren(args.max, args.min_score, args.dry_run)


if __name__ == "__main__":
    main()
