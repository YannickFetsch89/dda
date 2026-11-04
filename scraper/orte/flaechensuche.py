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
    _slug_erzeugen,
    ort_aus_place,
    place_details,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# ── Konfiguration ─────────────────────────────────────────────────────────────

# Ankerpunkt des Zellenrasters (fest, damit bereits abgefragte Zellen beim Erweitern wiedererkannt werden)
GEBIET = {"sued": 51.124, "nord": 51.353, "west": 6.688, "ost": 6.940}
# Abgedecktes Rechteck: Düsseldorf plus Neuss (Westen) und Ratingen (Nordosten).
# Orte anderer Städte darin (Meerbusch, Hilden …) werden über die Adresse aussortiert.
ABDECKUNG = {"sued": 51.100, "nord": 51.370, "west": 6.580, "ost": 6.960}
# Städte, deren Restaurants/Cafés in den Guide dürfen
STAEDTE = ("Düsseldorf", "Neuss", "Ratingen")
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
    r"maredo|enchilada|sausalitos|bulls ?& ?bears|coffee ?shop company|balzac|einstein kaffee|"
    r"espresso house|yormas|ditsch|le crobag|kochl[öo]ffel|cinnamood|jim block|dunkin)\b",
    re.IGNORECASE,
)
# Kettennamen, die nur am Namensanfang eindeutig sind ("ALEX Düsseldorf", nicht "Restaurant Alex")
KETTEN_ANFANG = re.compile(r"^(alex)\b", re.IGNORECASE)


def ist_kette(name: str) -> bool:
    """Erkennt Ketten am Namen; typografische Apostrophe (’ ` ´) werden wie ' behandelt."""
    n = re.sub(r"[’`´‘]", "'", name or "").strip()
    return bool(KETTEN.search(n) or KETTEN_ANFANG.search(n))

# "40215 Düsseldorf", "41460 Neuss", "41470 Neuss-Rosellerheide", "40878 Ratingen"
STADT_ADRESSE = re.compile(r"\b\d{5}\s+(" + "|".join(STAEDTE) + r")\b")


def stadt_von(place: dict) -> str | None:
    """Stadt aus der Google-Adresse (nur die zugelassenen Städte, sonst None)."""
    treffer = STADT_ADRESSE.search(place.get("formattedAddress") or "")
    return treffer.group(1) if treffer else None


def ort_stadtteil(name: str, adresse: str | None, stadt: str | None) -> str | None:
    """Stadtteil für Düsseldorf über den Mapper; Neuss und Ratingen erscheinen als eigener 'Stadtteil'."""
    from pipeline.stadtteil_mapper import stadtteil_ermitteln
    if stadt and stadt != "Düsseldorf":
        return stadt
    return stadtteil_ermitteln(name, adresse)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _km_zu_grad(km: float, breite: float) -> tuple[float, float]:
    """Kilometer → (Grad Breite, Grad Länge) an der gegebenen geographischen Breite."""
    return km / 111.32, km / (111.32 * math.cos(math.radians(breite)))


# ── Zellen-Gitter ─────────────────────────────────────────────────────────────
# Jede Zelle ist eindeutig durch (Stufe, Zeile, Spalte) relativ zum Ankerpunkt bestimmt:
# Stufe 0 = Startzellen (3 km), jede Stufe halbiert die Kantenlänge. Unterzellen entstehen exakt
# aus den Indizes (2i, 2i+1 …) – so kann dieselbe Zelle nie mit leicht abweichenden Koordinaten
# zweimal entstehen und doppelt bezahlt werden.

_GRUND_DLAT, _GRUND_DLNG = _km_zu_grad(START_ZELLE_KM, (GEBIET["sued"] + GEBIET["nord"]) / 2)


def _gitter_zelle(stufe: int, i: int, j: int, typen: list[str] | None = None) -> dict:
    """Zelle aus Gitter-Indizes (Mittelpunkt exakt berechnet)."""
    f = 2 ** stufe
    zelle = {
        "stufe": stufe, "i": i, "j": j,
        "lat": GEBIET["sued"] + (i + 0.5) * _GRUND_DLAT / f,
        "lng": GEBIET["west"] + (j + 0.5) * _GRUND_DLNG / f,
        "km": START_ZELLE_KM / f,
    }
    if typen:
        zelle["typen"] = list(typen)
    return zelle


def _gitter_von(zelle: dict) -> tuple[int, int, int]:
    """(Stufe, Zeile, Spalte) einer Zelle – auch für alte Einträge ohne Indizes (nächster Gitterpunkt)."""
    if "stufe" in zelle:
        return zelle["stufe"], zelle["i"], zelle["j"]
    stufe = round(math.log2(START_ZELLE_KM / zelle["km"]))
    f = 2 ** stufe
    i = round((zelle["lat"] - GEBIET["sued"]) / (_GRUND_DLAT / f) - 0.5)
    j = round((zelle["lng"] - GEBIET["west"]) / (_GRUND_DLNG / f) - 0.5)
    return stufe, i, j


def _startzellen() -> list[dict]:
    """
    Zerlegt das abgedeckte Gebiet in quadratische Startzellen (Stufe 0).

    Das Raster ist am festen Ankerpunkt (GEBIET süd/west) ausgerichtet; eine Erweiterung der
    Abdeckung erzeugt dadurch exakt dieselben Zellen wie zuvor plus neue am Rand.
    """
    i_von = math.floor((ABDECKUNG["sued"] - GEBIET["sued"]) / _GRUND_DLAT)
    i_bis = math.ceil((ABDECKUNG["nord"] - GEBIET["sued"]) / _GRUND_DLAT)
    j_von = math.floor((ABDECKUNG["west"] - GEBIET["west"]) / _GRUND_DLNG)
    j_bis = math.ceil((ABDECKUNG["ost"] - GEBIET["west"]) / _GRUND_DLNG)
    return [_gitter_zelle(0, i, j) for i in range(i_von, i_bis) for j in range(j_von, j_bis)]


def _im_kreis(zelle: dict, p: dict) -> bool:
    """Liegt ein Ort im Suchkreis der Zelle?"""
    loc = p.get("location") or {}
    if "latitude" not in loc:
        return False
    d_lat_m = (loc["latitude"] - zelle["lat"]) * 111320
    d_lng_m = (loc["longitude"] - zelle["lng"]) * 111320 * math.cos(math.radians(zelle["lat"]))
    return math.hypot(d_lat_m, d_lng_m) <= zelle["km"] * 1000 * math.sqrt(2) / 2 + 1


def _zell_schluessel(zelle: dict) -> str:
    """Eindeutiger Schlüssel "Stufe:Zeile:Spalte" (bei typbezogenen Nachzügen mit ":typen")."""
    stufe, i, j = _gitter_von(zelle)
    typen = zelle.get("typen")
    return f"{stufe}:{i}:{j}" + (f":{'+'.join(typen)}" if typen else "")


def _aus_schluessel(schluessel: str) -> dict:
    """Zelle aus einem Schlüssel – neues Format "Stufe:Zeile:Spalte[:typen]" oder altes "lat,lng,km"."""
    if "," in schluessel:
        lat, lng, km = schluessel.split(",")
        return _gitter_zelle(*_gitter_von({"lat": float(lat), "lng": float(lng), "km": float(km)}))
    teile = schluessel.split(":")
    return _gitter_zelle(int(teile[0]), int(teile[1]), int(teile[2]), teile[3].split("+") if len(teile) > 3 else None)


def _viertel(zelle: dict) -> list[dict]:
    """Teilt eine Zelle in ihre vier Unterzellen der nächsten Stufe (exakt aus den Gitter-Indizes)."""
    stufe, i, j = _gitter_von(zelle)
    return [_gitter_zelle(stufe + 1, 2 * i + di, 2 * j + dj) for di in (0, 1) for dj in (0, 1)]


def _typ_nachzuege(zelle: dict) -> list[dict]:
    """
    Volle Kleinstzelle getrennt nach Restaurants und Cafés erneut abfragen: In einer gemeinsamen
    Anfrage (Limit 20) verdrängen bekannte Restaurants sonst die Cafés.
    """
    stufe, i, j = _gitter_von(zelle)
    return [_gitter_zelle(stufe, i, j, ["restaurant"]), _gitter_zelle(stufe, i, j, ["cafe", "coffee_shop"])]


def _speicher_normalisieren(daten: dict) -> None:
    """Rechnet alte Koordinaten-Schlüssel auf Gitter-Schlüssel um und entfernt Doppelte."""
    daten["erledigt"] = list(dict.fromkeys(_zell_schluessel(_aus_schluessel(s)) for s in daten.get("erledigt", [])))
    gesehen, schlange = set(daten["erledigt"]), []
    for z in daten.get("warteschlange", []):
        k = _zell_schluessel(z)
        if k not in gesehen:
            gesehen.add(k)
            schlange.append(_aus_schluessel(k))
    daten["warteschlange"] = schlange
    daten.setdefault("gesaettigt_min_zellen", [])


def _nachverfeinern(daten: dict, je_typ: bool = False) -> int:
    """
    Ergänzt die Warteschlange nach einer Änderung der Abdeckung oder der zugelassenen Städte:
      - neue Startzellen am Rand
      - Unterzellen bereits abgefragter Zellen, die voll waren (≥ 20 Orte im Kreis) und in denen
        zugelassene Orte liegen, aber noch nicht verfeinert wurden
      - mit je_typ=True: volle Kleinstzellen getrennt nach Restaurants und Cafés

    Ob eine Zelle voll war, lässt sich aus dem Zwischenspeicher ablesen: Eine nicht volle Zelle hat
    ALLE Orte ihres Kreises geliefert – liegen ≥ 20 bekannte Orte im Kreis, war sie voll.

    Returns:
        Anzahl neu eingereihter Zellen
    """
    erledigt = set(daten["erledigt"])
    geplant = {_zell_schluessel(z) for z in daten["warteschlange"]}
    orte = list(daten["orte"].values())
    neu: list[dict] = []

    def einreihen(zelle: dict) -> None:
        k = _zell_schluessel(zelle)
        if k not in erledigt and k not in geplant:
            neu.append(zelle)
            geplant.add(k)

    for zelle in _startzellen():
        einreihen(zelle)

    for s in list(erledigt):
        zelle = _aus_schluessel(s)
        if zelle.get("typen"):
            continue
        im_kreis = [p for p in orte if _im_kreis(zelle, p)]
        if len(im_kreis) < MAX_TREFFER or not any(stadt_von(p) for p in im_kreis):
            continue
        if zelle["km"] / 2 >= MIN_ZELLE_KM:
            for kind in _viertel(zelle):
                einreihen(kind)
        elif je_typ:
            for nachzug in _typ_nachzuege(zelle):
                einreihen(nachzug)

    daten["warteschlange"].extend(neu)
    return len(neu)


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
    if not stadt_von(place):
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
    kette = ist_kette(name)
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
        "includedTypes": zelle.get("typen") or SUCH_TYPEN,
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


def suchen(max_anfragen: int, neu: bool = False, je_typ: bool = False) -> dict:
    """
    Führt die Flächensuche aus bzw. setzt eine unterbrochene fort.

    je_typ=True: volle Kleinstzellen zusätzlich getrennt nach Restaurants und Cafés abfragen
    (kostet je volle Kleinstzelle zwei weitere Anfragen).
    """
    daten = {} if neu else speicher_laden()
    if not daten:
        daten = {
            "gestartet": datetime.now(timezone.utc).isoformat(),
            "warteschlange": _startzellen(),
            "erledigt": [],
            "anfragen": 0,
            "gesaettigt_min": 0,
            "gesaettigt_min_zellen": [],
            "orte": {},
        }
        logger.info("Neue Flächensuche: %d Startzellen à %.1f km", len(daten["warteschlange"]), START_ZELLE_KM)
    else:
        _speicher_normalisieren(daten)
        ergaenzt = _nachverfeinern(daten, je_typ)
        logger.info(
            "Setze Flächensuche fort: %d Anfragen bisher, %d Zellen offen (davon %d neu durch "
            "erweiterte Abdeckung/Städte%s), %d Orte gefunden",
            daten["anfragen"], len(daten["warteschlange"]), ergaenzt,
            "/Typ-Nachzüge" if je_typ else "", len(daten["orte"]),
        )

    erledigt = set(daten["erledigt"])
    anfragen_dieser_lauf = 0

    try:
        with httpx.Client(timeout=30) as client:
            while daten["warteschlange"] and anfragen_dieser_lauf < max_anfragen:
                zelle = daten["warteschlange"].pop(0)
                schluessel = _zell_schluessel(zelle)
                if schluessel in erledigt:
                    continue
                try:
                    treffer = _zelle_abfragen(client, zelle)
                except (httpx.HTTPError, RuntimeError, ValueError) as e:
                    # Zelle zurücklegen; Zwischenstand wird im finally gespeichert → Fortsetzen ohne Doppelkosten
                    daten["warteschlange"].insert(0, zelle)
                    text = e.response.text[:300] if isinstance(e, httpx.HTTPStatusError) else str(e)
                    logger.error("Suche angehalten (später fortsetzen mit 'suchen'): %s", text)
                    break
                daten["anfragen"] += 1
                anfragen_dieser_lauf += 1

                in_staedten = 0
                for p in treffer:
                    if stadt_von(p):
                        in_staedten += 1
                    daten["orte"][p["id"]] = p

                # Volle Zelle mit Treffern in zugelassenen Städten → vierteln (anderswo nicht weiter verfeinern)
                if len(treffer) >= MAX_TREFFER and in_staedten > 0:
                    if zelle["km"] / 2 >= MIN_ZELLE_KM:
                        daten["warteschlange"].extend(_viertel(zelle))
                    elif je_typ and not zelle.get("typen"):
                        daten["warteschlange"].extend(_typ_nachzuege(zelle))
                    else:
                        # Kleinstzelle bleibt unvollständig – in der Auswertung ausweisen
                        daten["gesaettigt_min"] += 1
                        daten.setdefault("gesaettigt_min_zellen", []).append(schluessel)

                erledigt.add(schluessel)
                daten["erledigt"].append(schluessel)
                if daten["anfragen"] % 10 == 0:
                    speicher_schreiben(daten)
                    logger.info(
                        "  %d Anfragen | %d Zellen offen | %d Orte gefunden",
                        daten["anfragen"], len(daten["warteschlange"]), len(daten["orte"]),
                    )
    finally:
        speicher_schreiben(daten)

    fertig = not daten["warteschlange"]
    logger.info(
        "Suche %s: %d Anfragen gesamt (ca. %.2f $ ohne Freikontingent), %d Orte gefunden%s",
        "abgeschlossen" if fertig else "pausiert (Limit/Fehler – erneut aufrufen zum Fortsetzen)",
        daten["anfragen"], daten["anfragen"] * PREIS_SUCHE / 1000, len(daten["orte"]),
        f", {daten['gesaettigt_min']} Kleinstzellen waren noch voll (unvollständig; '--je-typ' fragt sie "
        f"getrennt nach Restaurants und Cafés nach)" if daten["gesaettigt_min"] else "",
    )
    return daten


def volle_kleinstzellen(daten: dict) -> int:
    """Zählt volle Kleinstzellen, die noch nicht getrennt nach Typ nachgefragt wurden (unvollständige Abdeckung)."""
    erledigt = {_zell_schluessel(_aus_schluessel(s)) for s in daten.get("erledigt", [])}
    orte = list(daten.get("orte", {}).values())
    anzahl = 0
    for s in erledigt:
        zelle = _aus_schluessel(s)
        if zelle.get("typen") or zelle["km"] / 2 >= MIN_ZELLE_KM:
            continue
        im_kreis = [p for p in orte if _im_kreis(zelle, p)]
        if len(im_kreis) >= MAX_TREFFER and any(stadt_von(p) for p in im_kreis):
            if not all(_zell_schluessel(n) in erledigt for n in _typ_nachzuege(zelle)):
                anzahl += 1
    return anzahl


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
    print(f"\nAnfragen: {daten['anfragen']} (ca. {daten['anfragen'] * PREIS_SUCHE / 1000:.2f} $) | "
          f"offene Zellen: {len(daten['warteschlange'])}")
    print(f"Treffer gesamt: {len(daten['orte'])}")
    for grund, n in gruende.most_common():
        print(f"  {grund:24s} {n:5d}")
    print(f"\nKandidaten: {len(liste)}  (Restaurants: {sum(p['_typ'] == 'restaurant' for p in liste)}, "
          f"Cafés: {sum(p['_typ'] == 'cafe' for p in liste)}, davon Ketten: {sum(p['_kette'] for p in liste)})")
    print("Vorab-Score:", dict(sorted(Counter(p["_score"] for p in liste).items(), reverse=True)))
    print("Städte:", dict(Counter(stadt_von(p) for p in liste)), "| davon Score ≥ 7:", sum(p["_score"] >= 7 for p in liste))
    stadtteile = Counter(
        ort_stadtteil(p["displayName"]["text"], p.get("formattedAddress"), stadt_von(p)) or "?" for p in liste
    )
    print("Stadtteile:", ", ".join(f"{s} {n}" for s, n in stadtteile.most_common(15)), "…")
    print(f"Details für alle Kandidaten: ca. {len(liste) * PREIS_DETAILS / 1000:.2f} $ (ohne Freikontingent)")
    voll = volle_kleinstzellen(daten)
    if voll:
        print(f"Unvollständig: {voll} volle Kleinstzellen (dort fehlen ggf. weniger bekannte Orte). "
              f"Nachfragen getrennt nach Typ: 'suchen --je-typ' ≈ {2 * voll} Anfragen ≈ {2 * voll * PREIS_SUCHE / 1000:.2f} $")
    print()
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
            # Neuss/Ratingen: Stadt statt (falsch zugeordnetem) Düsseldorfer Stadtteil, Slug passend dazu
            ort["stadtteil"] = ort_stadtteil(name, ort.get("adresse"), stadt_von(p))
            ort["slug"] = slug_mit_suffix(_slug_erzeugen(name, ort["stadtteil"]), vergebene_slugs)
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
    scores_nachziehen(db)
    return {"gespeichert": gespeichert, "fehler": fehler}


def scores_nachziehen(db) -> int:
    """Gibt Orten ohne qualitaets_score (z.B. aus dem ersten Import) den Vorab-Score."""
    ohne = (
        db.table("orte")
        .select("id, name, google_rating, google_bewertungen_anzahl, extras")
        .is_("qualitaets_score", "null")
        .execute()
        .data or []
    )
    nachgetragen = 0
    for o in ohne:
        if o.get("google_rating") is None:
            continue
        score, gewichtet, kette = vorab_score({
            "rating": o["google_rating"],
            "userRatingCount": o.get("google_bewertungen_anzahl") or 0,
            "displayName": {"text": o["name"]},
        })
        extras = {**(o.get("extras") or {}), "vorab_score": gewichtet, "kette": kette}
        db.table("orte").update({"qualitaets_score": score, "extras": extras}).eq("id", o["id"]).execute()
        nachgetragen += 1
    if nachgetragen:
        logger.info("Vorab-Score für %d bestehende Orte nachgetragen", nachgetragen)
    return nachgetragen


def neu_bewerten(dry_run: bool) -> list[dict]:
    """
    Berechnet den Vorab-Score aller Orte neu (z.B. nach Änderung der Ketten-Erkennung).
    Ändert nur qualitaets_score und extras.vorab_score/kette – sonst nichts.

    Returns:
        Liste der geänderten Orte (Name, alt, neu, aktiv)
    """
    from database.client import get_supabase_client

    db = get_supabase_client()
    orte, seite = [], 0
    while True:
        teil = (
            db.table("orte")
            .select("id, name, aktiv, qualitaets_score, google_rating, google_bewertungen_anzahl, extras")
            .range(seite * 1000, seite * 1000 + 999)
            .execute()
            .data or []
        )
        orte += teil
        if len(teil) < 1000:
            break
        seite += 1

    geaendert = []
    for o in orte:
        if o.get("google_rating") is None:
            continue
        score, gewichtet, kette = vorab_score({
            "rating": o["google_rating"],
            "userRatingCount": o.get("google_bewertungen_anzahl") or 0,
            "displayName": {"text": o["name"]},
        })
        ex = o.get("extras") or {}
        if score == o.get("qualitaets_score") and bool(ex.get("kette")) == kette:
            continue
        geaendert.append({"name": o["name"], "alt": o.get("qualitaets_score"), "neu": score, "aktiv": o["aktiv"], "kette": kette})
        if not dry_run:
            db.table("orte").update({
                "qualitaets_score": score,
                "extras": {**ex, "vorab_score": gewichtet, "kette": kette},
            }).eq("id", o["id"]).execute()

    for g in geaendert:
        logger.info("  %s: Score %s → %s%s%s", g["name"], g["alt"], g["neu"], " (Kette)" if g["kette"] else "", " [aktiv]" if g["aktiv"] else "")
    logger.info("%d Orte %s", len(geaendert), "würden geändert (Dry-Run)" if dry_run else "neu bewertet")
    return geaendert


def main():
    parser = argparse.ArgumentParser(description="Flächendeckende Restaurant-/Café-Suche für Düsseldorf")
    befehle = parser.add_subparsers(dest="befehl", required=True)

    p_suchen = befehle.add_parser("suchen", help="Flächensuche ausführen/fortsetzen")
    p_suchen.add_argument("--max-anfragen", type=int, default=900, help="Höchstzahl Suchanfragen in diesem Lauf")
    p_suchen.add_argument("--neu", action="store_true", help="Zwischenspeicher verwerfen und neu beginnen")
    p_suchen.add_argument("--je-typ", action="store_true",
                          help="Volle Kleinstzellen getrennt nach Restaurants und Cafés nachfragen (2 Anfragen je Zelle)")

    befehle.add_parser("auswertung", help="Kandidaten-Pool anzeigen (kostenlos)")

    p_bewerten = befehle.add_parser("bewerten", help="Vorab-Score aller Orte neu berechnen (kostenlos)")
    p_bewerten.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts speichern")

    p_import = befehle.add_parser("importieren", help="Details laden und in Supabase speichern")
    p_import.add_argument("--max", type=int, default=900, help="Höchstzahl Orte (= Detail-Abrufe)")
    p_import.add_argument("--min-score", type=int, default=1, help="Nur Kandidaten ab diesem Vorab-Score")
    p_import.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts abrufen oder speichern")

    args = parser.parse_args()
    if args.befehl in ("suchen", "importieren") and not GOOGLE_PLACES_API_KEY:
        logger.error("GOOGLE_PLACES_API_KEY fehlt in .env")
        sys.exit(1)

    if args.befehl == "suchen":
        suchen(args.max_anfragen, args.neu, args.je_typ)
    elif args.befehl == "auswertung":
        auswertung()
    elif args.befehl == "bewerten":
        neu_bewerten(args.dry_run)
    else:
        importieren(args.max, args.min_score, args.dry_run)


if __name__ == "__main__":
    main()
