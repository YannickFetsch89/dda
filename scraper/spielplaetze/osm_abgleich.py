"""
osm_abgleich.py – DiesDasDüsseldorf
OSM-Abgleich für den Guide „Spielplätze“ (Plan: docs/plan-spielplaetze-2026-11-12.md, Abschnitte 4.2 und 4.5).

Eine Overpass-Abfrage holt Spielplätze (leisure=playground), Geräte (playground=*) und Sportflächen (leisure=pitch mit
sport; sport=table_tennis) im Stadtgebiet. Zwischenspeicher data/spielplaetze/osm.json (nie veröffentlicht).
Übernommen werden nur Eigenschaften (ODbL): Geräte, Sportflächen, min_age/max_age, wheelchair, fee (nur städtisch), access.
Einträge mit quelle "sichtung" (ausstattung.csv) oder "zitat" (Profil) werden nie überschrieben.

Nutzung:
  python -m scraper.spielplaetze.osm_abgleich --dry-run      # rechnet, schreibt Bericht und Prüf-CSV, nicht die Datenbank
  python -m scraper.spielplaetze.osm_abgleich                # schreibt in die Datenbank
  python -m scraper.spielplaetze.osm_abgleich --neu-laden    # Overpass neu abfragen (sonst Zwischenspeicher)
"""
import argparse
import csv
import json
import logging
import math
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logger = logging.getLogger(__name__)

_DATEN = Path(__file__).resolve().parents[2] / "data" / "spielplaetze"
OSM_JSON = _DATEN / "osm.json"
BERICHT = _DATEN / "osm_bericht.md"
PRUEF_CSV = _DATEN / "osm_pruefung.csv"

OVERPASS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter")
# Neutraler Programmname: overpass-api.de lehnt Browser-artige User-Agents mit 406 ab
USER_AGENT = "osm-spielplatz-abgleich/1.0 (python-httpx)"
VERSUCHE = 6
BBOX = (51.12, 6.68, 51.36, 6.95)  # Süd, West, Nord, Ost – Düsseldorf mit Rand

TREFFER_M = 60.0      # Mittelpunkt eines OSM-Spielplatzes zum Stadt-Punkt
GERAET_PUNKT_M = 30.0  # Geräte um einen OSM-Spielplatz-Punkt
SPORT_M = 40.0         # Sportfläche zum Stadt-Punkt oder zur Spielplatzfläche

GERAETE_MAPPING = {
    "sandpit": "sandkasten", "swing": "schaukel", "basketswing": "schaukel", "baby_swing": "schaukel",
    "slide": "rutsche", "climbingwall": "klettern", "climbingframe": "klettern", "climbing_net": "klettern",
    "water": "wasserspiel", "pump": "wasserspiel", "splash_pad": "wasserspiel", "zipwire": "seilbahn",
    "springy": "federwippe", "seesaw": "wippe", "roundabout": "karussell", "balancebeam": "balancierbalken",
}
SPORT_MAPPING = {
    "table_tennis": "tischtennis", "soccer": "fussball", "basketball": "basketball",
    "volleyball": "volleyball", "beachvolleyball": "volleyball", "skateboard": "skaten",
}
SPORT_ABFRAGE = "soccer|basketball|table_tennis|volleyball|beachvolleyball|skateboard|multi"
NICHT_OEFFENTLICH = {"private", "no", "customers"}
GESCHUETZT = {"sichtung", "zitat"}  # diese Quellen überschreibt OSM nie
ROLLSTUHL = {"yes": "ja", "limited": "teilweise", "no": "nein"}


# ---------------------------------------------------------------------------
# Geometrie (lokale Projektion in Metern, für Abstände unter einem Kilometer genau genug)
# ---------------------------------------------------------------------------

def _xy(lat: float, lon: float, lat0: float) -> tuple[float, float]:
    return (lon * 111320.0 * math.cos(math.radians(lat0)), lat * 110574.0)


def abstand_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Abstand in Metern zwischen (lat, lon)-Paaren."""
    ax, ay = _xy(*a, a[0])
    bx, by = _xy(*b, a[0])
    return math.hypot(ax - bx, ay - by)


def im_ring(punkt: tuple[float, float], ring: list[tuple[float, float]]) -> bool:
    """Ray-Casting; ring als [(lat, lon), …]."""
    lat, lon = punkt
    drin, j = False, len(ring) - 1
    for i in range(len(ring)):
        yi, xi = ring[i]
        yj, xj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            drin = not drin
        j = i
    return drin


def _abstand_strecke(p, a, b, lat0) -> float:
    px, py = _xy(*p, lat0)
    ax, ay = _xy(*a, lat0)
    bx, by = _xy(*b, lat0)
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def abstand_zu_form(punkt: tuple[float, float], form: dict) -> float:
    """Abstand eines Punkts zu einer Form (Fläche: drinnen = 0, sonst zum Rand; Linie: zur Linie; Punkt: zum Punkt)."""
    if form["art"] == "punkt":
        return abstand_m(punkt, form["mitte"])
    loecher = form.get("loecher") or []
    if form["art"] == "flaeche" and any(im_ring(punkt, r) for r in form["ringe"]) \
            and not any(im_ring(punkt, r) for r in loecher):
        return 0.0
    besten = math.inf
    for r in form["ringe"] + loecher:
        for a, b in zip(r, r[1:]):
            besten = min(besten, _abstand_strecke(punkt, a, b, punkt[0]))
    return besten


def abstand_formen(a: dict, b: dict) -> float:
    """Kleinster Abstand zweier Formen (über die Eckpunkte beider Formen; drinnen = 0)."""
    punkte_a = [a["mitte"]] if a["art"] == "punkt" else [p for r in a["ringe"] for p in r]
    punkte_b = [b["mitte"]] if b["art"] == "punkt" else [p for r in b["ringe"] for p in r]
    return min(min(abstand_zu_form(p, b) for p in punkte_a), min(abstand_zu_form(p, a) for p in punkte_b))


def form_aus_element(el: dict) -> dict | None:
    """Overpass-Element (out geom) → {art: punkt|flaeche|linie, ringe (außen), loecher (innen), mitte}."""
    if el["type"] == "node":
        return {"art": "punkt", "ringe": [], "loecher": [], "mitte": (el["lat"], el["lon"])}
    ringe, loecher = [], []
    if el["type"] == "way" and el.get("geometry"):
        ringe = [[(g["lat"], g["lon"]) for g in el["geometry"]]]
    elif el["type"] == "relation":
        for m in el.get("members") or []:
            if m.get("type") == "way" and m.get("geometry"):
                ring = [(g["lat"], g["lon"]) for g in m["geometry"]]
                if m.get("role") in ("outer", ""):
                    ringe.append(ring)
                elif m.get("role") == "inner":
                    loecher.append(ring)
    ringe = [r for r in ringe if len(r) >= 2]
    loecher = [r for r in loecher if len(r) >= 4 and r[0] == r[-1]]
    if not ringe:
        return None
    alle = [p for r in ringe for p in r]
    mitte = (sum(p[0] for p in alle) / len(alle), sum(p[1] for p in alle) / len(alle))
    geschlossen = all(len(r) >= 4 and r[0] == r[-1] for r in ringe)
    return {"art": "flaeche" if geschlossen else "linie", "ringe": ringe, "loecher": loecher if geschlossen else [],
            "mitte": mitte}


# ---------------------------------------------------------------------------
# OSM-Daten aufbereiten
# ---------------------------------------------------------------------------

def _werte(text: str | None) -> list[str]:
    return [w.strip() for w in (text or "").split(";") if w.strip()]


def osm_aufbereiten(daten: dict) -> dict:
    """Overpass-Antwort → {spielplaetze, geraete, sport} mit Formen und Tags."""
    spielplaetze, geraete, sport = [], [], []
    for el in daten.get("elements") or []:
        tags = el.get("tags") or {}
        form = form_aus_element(el)
        if not form:
            continue
        obj = {"id": f"{el['type']}/{el['id']}", "tags": tags, "form": form, "stand": el.get("timestamp")}
        if tags.get("leisure") == "playground":
            spielplaetze.append(obj)
        if tags.get("playground"):
            geraete.append(obj)
        if (tags.get("leisure") == "pitch" and tags.get("sport")) or "table_tennis" in _werte(tags.get("sport")):
            sport.append(obj)
    return {"spielplaetze": spielplaetze, "geraete": geraete, "sport": sport}


def zuordnen(punkt: tuple[float, float], spielplaetze: list[dict]) -> tuple[dict | None, str]:
    """
    4.2: Punkt in genau einer OSM-Fläche → Treffer. In keiner: genau ein Kandidat mit Mittelpunkt ≤ 60 m → Treffer.
    Zwei Flächen um den Punkt oder mehrere Kandidaten → mehrdeutig. Rückgabe (Treffer, Art).
    """
    drin = [s for s in spielplaetze if s["form"]["art"] == "flaeche" and abstand_zu_form(punkt, s["form"]) == 0.0]
    if len(drin) == 1:
        return drin[0], "in_flaeche"
    if len(drin) > 1:
        return None, "mehrdeutig"
    nah = [s for s in spielplaetze if abstand_m(punkt, s["form"]["mitte"]) <= TREFFER_M]
    if len(nah) == 1:
        return nah[0], "nah"
    return (None, "mehrdeutig") if nah else (None, "kein_treffer")


def geraete_des_treffers(treffer: dict, geraete: list[dict]) -> list[str]:
    """Rohwerte playground=* in der Fläche (Mittelpunkt des Geräts) bzw. ≤ 30 m um einen OSM-Punkt; dazu Tags am Treffer selbst."""
    roh = []
    for g in geraete:
        if g["id"] == treffer["id"]:
            continue
        if treffer["form"]["art"] == "flaeche":
            passt = abstand_zu_form(g["form"]["mitte"], treffer["form"]) == 0.0
        else:
            passt = abstand_m(g["form"]["mitte"], treffer["form"]["mitte"]) <= GERAET_PUNKT_M
        if passt:
            roh += _werte(g["tags"].get("playground"))
    roh += _werte(treffer["tags"].get("playground"))
    return sorted(roh)


def sport_in_der_naehe(punkt: tuple[float, float], treffer: dict | None, sport: list[dict]) -> tuple[list[str], list[str]]:
    """Sportflächen ≤ 40 m vom Punkt oder von der Spielplatzfläche; nicht öffentliche ausgenommen. Rückgabe (Rohwerte, Belege)."""
    roh, belege = [], []
    stadt_form = {"art": "punkt", "ringe": [], "mitte": punkt}
    for s in sport:
        if s["tags"].get("access") in NICHT_OEFFENTLICH:
            continue
        d = abstand_formen(stadt_form, s["form"])
        if treffer and treffer["form"]["art"] == "flaeche":
            d = min(d, abstand_formen(treffer["form"], s["form"]))
        if d <= SPORT_M:
            for w in _werte(s["tags"].get("sport")):
                roh.append(w)
                belege.append(f"{s['id']} sport={w}")
    return sorted(set(roh)), belege


# ---------------------------------------------------------------------------
# Planung (rein): neue Felder je Zeile
# ---------------------------------------------------------------------------

def zeile_auswerten(zeile: dict, osm: dict) -> dict:
    """Rechnet für eine Spielplatz-Zeile alle OSM-Felder aus (ohne Datenbank)."""
    sp = (zeile.get("extras") or {}).get("spielplatz") or {}
    abenteuer = sp.get("quelle") == "abenteuer"
    punkt = (zeile["latitude"], zeile["longitude"])
    treffer, art = zuordnen(punkt, osm["spielplaetze"])
    tags = treffer["tags"] if treffer else {}
    geraete_roh = geraete_des_treffers(treffer, osm["geraete"]) if treffer else []
    sport_roh, sport_belege = sport_in_der_naehe(punkt, treffer, osm["sport"])

    # Merkmale aus OSM (nur „ja“ – OSM belegt keine Abwesenheit)
    osm_merkmale = {}
    for w in geraete_roh:
        if w in GERAETE_MAPPING:
            osm_merkmale.setdefault(GERAETE_MAPPING[w], f"{treffer['id']} playground={w}")
    for beleg in sport_belege:
        wert = beleg.split("sport=", 1)[1]
        if wert in SPORT_MAPPING:
            osm_merkmale.setdefault(SPORT_MAPPING[wert], beleg)

    ausstattung = {k: v for k, v in (sp.get("ausstattung") or {}).items() if (v or {}).get("quelle") != "osm"}
    konflikte = []
    for merkmal, beleg in sorted(osm_merkmale.items()):
        vorhanden = ausstattung.get(merkmal)
        if vorhanden and vorhanden.get("quelle") in GESCHUETZT:
            if vorhanden.get("wert") != "ja":
                konflikte.append(f"{merkmal}: {vorhanden['quelle']}={vorhanden.get('wert')}, OSM=ja")
            continue
        ausstattung[merkmal] = {"wert": "ja", "quelle": "osm", "beleg": beleg}

    extras = {k: v for k, v in (sp.get("extras") or {}).items() if not (k == "rollstuhl" and (v or {}).get("quelle") == "osm")}
    rollstuhl = ROLLSTUHL.get(tags.get("wheelchair", ""))
    if rollstuhl:
        vorhanden = extras.get("rollstuhl")
        if vorhanden and vorhanden.get("quelle") in GESCHUETZT:
            if vorhanden.get("wert") != rollstuhl:
                konflikte.append(f"rollstuhl: {vorhanden['quelle']}={vorhanden.get('wert')}, OSM={rollstuhl}")
        else:
            extras["rollstuhl"] = {"wert": rollstuhl, "quelle": "osm", "beleg": f"{treffer['id']} wheelchair={tags['wheelchair']}"}

    codes = [c for c in sp.get("pruefung") or [] if c not in ("access_private", "zuordnung_mehrdeutig")]
    if art == "mehrdeutig":
        codes.append("zuordnung_mehrdeutig")
    access = tags.get("access", "")
    if access in ({"private", "customers"} if abenteuer else {"private"}):
        codes.append("access_private")

    neu = {
        "ausstattung": ausstattung,
        "extras": extras,
        "pruefung": sorted(set(codes)),
        "osm": None if not treffer else {
            "id": treffer["id"], "tags_stand": treffer["stand"], "zuordnung": art,
            **({"min_age": tags["min_age"]} if tags.get("min_age") else {}),
            **({"max_age": tags["max_age"]} if tags.get("max_age") else {}),
            "geraete_roh": geraete_roh, "sport_roh": sport_roh,
        },
    }
    if not treffer and sport_roh:
        neu["osm"] = {"id": None, "tags_stand": None, "zuordnung": art, "geraete_roh": [], "sport_roh": sport_roh}
    fee_hinweis = ""
    if not abenteuer:
        fee = tags.get("fee")
        neu["eintritt"] = {"yes": "ja", "no": "nein"}.get(fee)
    elif tags.get("fee") in ("yes", "no") and {"yes": "ja", "no": "nein"}[tags["fee"]] != sp.get("eintritt"):
        fee_hinweis = f"OSM fee={tags['fee']} weicht von abenteuer.csv ab"
    return {"zeile": zeile, "neu": neu, "art": art, "treffer": treffer, "konflikte": konflikte, "fee_hinweis": fee_hinweis}


def unbenutzte_osm_plaetze(ergebnisse: list[dict], osm: dict, zeilen: list[dict], stadtteile: list[dict]) -> list[dict]:
    """
    OSM-Spielplätze ohne Treffer auf eine Zeile – nur auflisten (Kandidaten für neuere Plätze), nichts anlegen.
    Nur öffentliche (kein access=private/no/customers) innerhalb der Düsseldorfer Stadtteile.
    """
    from scraper.spielplaetze.stadt_import import polygon_treffer

    benutzt = {e["treffer"]["id"] for e in ergebnisse if e["treffer"]}
    punkte = [(z["latitude"], z["longitude"]) for z in zeilen]
    frei = []
    for s in osm["spielplaetze"]:
        if s["id"] in benutzt or s["tags"].get("access") in NICHT_OEFFENTLICH:
            continue
        if not polygon_treffer(s["form"]["mitte"][0], s["form"]["mitte"][1], stadtteile):
            continue
        if any(abstand_m(p, s["form"]["mitte"]) <= TREFFER_M for p in punkte):
            continue  # nahe an einem Platz (z. B. mehrdeutig) – kein neuer Kandidat
        frei.append(s)
    return frei


# ---------------------------------------------------------------------------
# Ein- und Ausgabe
# ---------------------------------------------------------------------------

def overpass_laden(neu: bool) -> dict:
    if OSM_JSON.exists() and not neu:
        return json.loads(OSM_JSON.read_text(encoding="utf-8"))
    s, w, n, o = BBOX
    abfrage = f"""[out:json][timeout:180];
(
  nwr["leisure"="playground"]({s},{w},{n},{o});
  nwr["playground"]({s},{w},{n},{o});
  nwr["leisure"="pitch"]["sport"~"{SPORT_ABFRAGE}"]({s},{w},{n},{o});
  nwr["sport"~"table_tennis"]({s},{w},{n},{o});
);
out tags geom meta;"""
    letzter_fehler = None
    for versuch in range(VERSUCHE):
        url = OVERPASS[versuch % len(OVERPASS)]
        try:
            r = httpx.post(url, data={"data": abfrage}, headers={"User-Agent": USER_AGENT}, timeout=240)
            if r.status_code in (429, 502, 503, 504):
                raise httpx.HTTPStatusError(f"HTTP {r.status_code}", request=r.request, response=r)
            r.raise_for_status()
            daten = r.json()
            _DATEN.mkdir(parents=True, exist_ok=True)
            OSM_JSON.write_text(json.dumps(daten, ensure_ascii=False), encoding="utf-8")
            logger.info("Overpass: %d Elemente geladen (%s)", len(daten.get("elements") or []), url)
            return daten
        except (httpx.HTTPError, ValueError) as e:
            letzter_fehler = e
            if versuch == VERSUCHE - 1:
                break
            pause = min(60 * (2 ** versuch), 600)
            logger.warning("Overpass-Versuch %d fehlgeschlagen (%s): %s – neuer Versuch in %d s", versuch + 1, url, e, pause)
            time.sleep(pause)
    raise RuntimeError(f"Overpass nicht erreichbar: {letzter_fehler}")


def bericht_schreiben(ergebnisse: list[dict], frei: list[dict], osm: dict, heute: str) -> str:
    def anteil(gruppe):
        n = len(gruppe)
        if not n:
            return "–"
        filter_geraete = ("sandkasten", "schaukel", "rutsche", "klettern", "wasserspiel", "seilbahn",
                          "tischtennis", "fussball", "basketball")
        anzahl = [sum(1 for k, v in e["neu"]["ausstattung"].items() if k in filter_geraete and v.get("wert") == "ja")
                  for e in gruppe]
        eins, zwei = sum(a >= 1 for a in anzahl), sum(a >= 2 for a in anzahl)
        return f"{n} Plätze: ≥ 1 Gerät {eins} ({eins / n:.0%}), ≥ 2 Geräte {zwei} ({zwei / n:.0%})"

    stadt = [e for e in ergebnisse if (e["zeile"]["extras"].get("spielplatz") or {}).get("quelle") != "abenteuer"]
    abenteuer = [e for e in ergebnisse if e not in stadt]
    arten = Counter(e["art"] for e in ergebnisse)
    merkmale = Counter(k for e in ergebnisse for k, v in e["neu"]["ausstattung"].items() if v.get("quelle") == "osm")
    zeilen = [
        f"# OSM-Abgleich Spielplätze – {heute}", "",
        f"OSM-Daten: {len(osm['spielplaetze'])} Spielplätze, {len(osm['geraete'])} Geräte-Objekte, "
        f"{len(osm['sport'])} Sportflächen im Stadtgebiet.", "",
        "## Zuordnung", "",
        f"- in einer OSM-Fläche: {arten['in_flaeche']}", f"- OSM-Mittelpunkt ≤ 60 m: {arten['nah']}",
        f"- mehrdeutig (nichts übernommen): {arten['mehrdeutig']}", f"- kein OSM-Spielplatz: {arten['kein_treffer']}", "",
        "## Abdeckung (Filter-Geräte inkl. Sport, Quelle OSM)", "",
        f"- städtisch: {anteil(stadt)}", f"- Abenteuer: {anteil(abenteuer)}", "",
        "## Merkmale aus OSM", "",
        *[f"- {k}: {v}" for k, v in sorted(merkmale.items(), key=lambda x: -x[1])], "",
        f"- Altersangabe in OSM (min_age/max_age): {sum(1 for e in ergebnisse if e['neu']['osm'] and (e['neu']['osm'].get('min_age') or e['neu']['osm'].get('max_age')))}",
        f"- Rollstuhl aus OSM: {sum(1 for e in ergebnisse if (e['neu']['extras'].get('rollstuhl') or {}).get('quelle') == 'osm')}",
        f"- Mehrzweck-Sportfläche (`sport=multi`, nicht zugeordnet): {sum(1 for e in ergebnisse if 'multi' in ((e['neu']['osm'] or {}).get('sport_roh') or []))}",
        f"- `access_private`: {sum(1 for e in ergebnisse if 'access_private' in e['neu']['pruefung'])}",
        f"- Eintritt laut OSM `fee=yes`: {sum(1 for e in ergebnisse if e['neu'].get('eintritt') == 'ja')}", "",
        f"## OSM-Spielplätze ohne Stadt-Platz in 60 m ({len(frei)}, davon {sum(1 for s in frei if s['tags'].get('name'))} mit Namen)", "",
        "Nur Liste – Kandidaten für neuere Plätze oder fehlende Zeilen in `abenteuer.csv`. Nur öffentliche (ohne",
        "`access=private/no/customers`) innerhalb Düsseldorfs; viele davon sind trotzdem Hof- oder Kita-Spielplätze.", "",
        *[f"- {s['id']} {s['tags'].get('name', '(ohne Namen)')} – {s['form']['mitte'][0]:.5f}, {s['form']['mitte'][1]:.5f}"
          for s in sorted(frei, key=lambda s: s["tags"].get("name", "~"))],
    ]
    BERICHT.write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    return "\n".join(zeilen[:24])


def pruef_csv_schreiben(ergebnisse: list[dict]) -> None:
    with PRUEF_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["schluessel", "name", "stadtteil", "zuordnung", "osm_id", "geraete_osm", "sport_osm", "codes", "konflikte", "hinweis"])
        for e in ergebnisse:
            z, sp = e["zeile"], e["zeile"]["extras"]["spielplatz"]
            schluessel = sp.get("schluessel") or ((sp.get("teile") or [{}])[0].get("objektschluessel", ""))
            osm = e["neu"]["osm"] or {}
            w.writerow([schluessel, z["name"], z.get("stadtteil") or "", e["art"], osm.get("id") or "",
                        ", ".join(osm.get("geraete_roh") or []), ", ".join(osm.get("sport_roh") or []),
                        ", ".join(e["neu"]["pruefung"]), "; ".join(e["konflikte"]), e["fee_hinweis"]])


def schreiben(db, ergebnisse: list[dict]) -> int:
    """Nur die OSM-Felder in extras.spielplatz ändern – extras direkt vorher frisch lesen. Nie aktiv, Name, Slug."""
    fehler = 0
    for e in ergebnisse:
        zid = e["zeile"]["id"]
        try:
            aktuell = (db.table("orte").select("extras").eq("id", zid).execute().data or [{}])[0].get("extras") or {}
            sp = {**(aktuell.get("spielplatz") or {}), **e["neu"]}
            db.table("orte").update({"extras": {**aktuell, "spielplatz": sp}}).eq("id", zid).execute()
        except Exception as ex:  # noqa: BLE001 – jede Zeile einzeln
            fehler += 1
            logger.error("Fehler bei %s: %s", e["zeile"]["slug"], ex)
    return fehler


def abgleichen(dry_run: bool, neu_laden: bool) -> None:
    osm = osm_aufbereiten(overpass_laden(neu_laden))
    from database.client import get_supabase_client
    from scraper.orte.google_places import alle_zeilen

    db = get_supabase_client()
    zeilen = alle_zeilen(db, "orte", "id, name, slug, stadtteil, latitude, longitude, extras",
                         lambda q: q.eq("typ", "spielplatz"))
    ergebnisse = [zeile_auswerten(z, osm) for z in zeilen]
    from scraper.spielplaetze.stadt_import import STADTTEIL_DATEI, stadtteile_lesen

    stadtteile = stadtteile_lesen(json.loads(STADTTEIL_DATEI.read_text(encoding="utf-8")))
    frei = unbenutzte_osm_plaetze(ergebnisse, osm, zeilen, stadtteile)
    kurz = bericht_schreiben(ergebnisse, frei, osm, date.today().isoformat())
    pruef_csv_schreiben(ergebnisse)
    logger.info("Bericht: %s, Prüf-CSV: %s%s\n%s", BERICHT, PRUEF_CSV, " [Dry-Run, Datenbank unverändert]" if dry_run else "", kurz)
    if not dry_run:
        logger.info("Geschrieben: %d Zeilen, %d Fehler", len(ergebnisse), schreiben(db, ergebnisse))


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Spielplätze: OSM-Abgleich")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--neu-laden", action="store_true", help="Overpass neu abfragen")
    args = parser.parse_args()
    abgleichen(args.dry_run, args.neu_laden)


if __name__ == "__main__":
    main()
