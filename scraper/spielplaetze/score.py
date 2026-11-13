"""
score.py – DiesDasDüsseldorf
Schritt 6 des Spielplatz-Plans (docs/plan-spielplaetze-2026-11-12.md, Abschnitte 4.5, 5.4 und Schritt 6).

- Alter: belegt (Profil-Zitat, OSM min_age/max_age, Stadtname) oder vermutlich aus den Geräten (Formel 4.5).
- Score (intern, 0–1) und Top-Badge (beste 20 % der indexierbaren, nicht ausgeschlossenen, danach aktiven Plätze).
- freischaltbar(): dieselbe Bedingung wie database/spielplaetze_freischalten.sql – für die Vorschau „Anschalten/Abschalten“.

Geschrieben werden nur extras.spielplatz.alter, score und top (extras frisch lesen). Nie aktiv oder freigeschaltet_am:
freischalten und abschalten nur über die SQL-Datei, die der Auftraggeber ausführt.

Nutzung:
  python -m scraper.spielplaetze.score --dry-run     # rechnet, schreibt nichts
  python -m scraper.spielplaetze.score               # schreibt Alter, Score, Top
  python -m scraper.spielplaetze.score vorschau      # zeigt, welche Slugs die Freischalt-SQL an- bzw. abschaltet
"""
import argparse
import csv
import json
import logging
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logger = logging.getLogger(__name__)

_WURZEL = Path(__file__).resolve().parents[2]
VORSCHAU_CSV = _WURZEL / "data" / "spielplaetze" / "freischalt_vorschau.csv"
SQL_DATEI = _WURZEL / "database" / "spielplaetze_freischalten.sql"

FILTER_GERAETE = ("sandkasten", "schaukel", "rutsche", "klettern", "wasserspiel", "seilbahn", "tischtennis", "fussball", "basketball")
ALTER_GERAETE = ("sandkasten", "schaukel", "rutsche", "klettern", "wasserspiel", "seilbahn",
                 "federwippe", "wippe", "karussell", "balancierbalken")  # ohne Sportflächen (4.5)
KLEINKIND = {"sandkasten", "federwippe", "babyschaukel"}
GROSSKIND = {"klettern", "seilbahn"}
EXTRAS_SCORE = ("schatten", "wc", "eingezaeunt", "picknick")
BELEG_QUELLEN = ("osm", "zitat", "sichtung")
SPERRT_IMMER = ("name_unklar", "kein_stadtteil")
SPERRT_OHNE_BESTAETIGUNG = ("access_private", "gruppe_gemischt")
STADT_DATENSTAND = "2020-09-25"


# ---------------------------------------------------------------------------
# Freischaltung (muss zur SQL-Datei passen)
# ---------------------------------------------------------------------------

def sperrender_code(sp: dict) -> bool:
    pruefung = set(sp.get("pruefung") or [])   # fehlendes Feld wie leer (COALESCE in der SQL)
    bestaetigt = set(sp.get("bestaetigt") or [])
    return bool(pruefung & set(SPERRT_IMMER)) or bool((pruefung & set(SPERRT_OHNE_BESTAETIGUNG)) - bestaetigt)


def freischaltbar(zeile: dict) -> bool:
    """Anschalten: inaktiv, kein Ausschluss, kein sperrender Code (gilt auch für abgeschaltete Zeilen)."""
    sp = (zeile.get("extras") or {}).get("spielplatz") or {}
    return not zeile.get("aktiv") and not sp.get("ausgeschlossen") and not sperrender_code(sp)


def abzuschalten(zeile: dict) -> bool:
    """Abschalten: aktiv und ausgeschlossen."""
    sp = (zeile.get("extras") or {}).get("spielplatz") or {}
    return bool(zeile.get("aktiv")) and bool(sp.get("ausgeschlossen"))


def danach_aktiv(zeile: dict) -> bool:
    return (bool(zeile.get("aktiv")) and not abzuschalten(zeile)) or freischaltbar(zeile)


# ---------------------------------------------------------------------------
# Indexierbarkeit (5.4) – dieselbe Fixture prüft später auch istIndexierbar in TypeScript
# ---------------------------------------------------------------------------

def belegte_geraete(sp: dict, auswahl=FILTER_GERAETE) -> set[str]:
    return {k for k, v in (sp.get("ausstattung") or {}).items()
            if k in auswahl and (v or {}).get("wert") == "ja" and (v or {}).get("quelle") in BELEG_QUELLEN and (v or {}).get("beleg")}


def ist_indexierbar(sp: dict) -> bool:
    return bool((sp.get("beschreibung") or "").strip()) and len(belegte_geraete(sp)) >= 2


# ---------------------------------------------------------------------------
# Alter (4.5)
# ---------------------------------------------------------------------------

def _band_aus_spanne(min_alter: float | None, max_alter: float | None) -> str | None:
    if min_alter is None and max_alter is None:
        return None
    if max_alter is not None and max_alter <= 3:
        return "0-3"
    if min_alter is not None and min_alter >= 6:
        return "6-12"
    if min_alter is not None and max_alter is not None and min_alter >= 3 and max_alter <= 6:
        return "3-6"
    return "alle"  # Spanne über mehr als ein Band


def _zahl(text) -> float | None:
    m = re.match(r"\s*(\d+(?:[.,]\d+)?)", str(text or ""))
    return float(m.group(1).replace(",", ".")) if m else None


def alter_osm(sp: dict) -> dict | None:
    osm = sp.get("osm") or {}
    band = _band_aus_spanne(_zahl(osm.get("min_age")), _zahl(osm.get("max_age")))
    if not band:
        return None
    return {"wert": band, "art": "belegt", "quelle": "osm",
            "beleg": f"OSM min_age={osm.get('min_age', '–')}, max_age={osm.get('max_age', '–')}",
            "stand": (osm.get("tags_stand") or "")[:10] or None}


def alter_stadtname(sp: dict) -> dict | None:
    namen = " ".join(t.get("stadt_name", "") for t in sp.get("teile") or []).lower()
    klein, schul = "kleinkind" in namen, "schulkind" in namen
    if not (klein or schul):
        return None
    wert = "alle" if klein and schul else "0-3" if klein else "6-12"
    return {"wert": wert, "art": "belegt", "quelle": "stadt", "beleg": "Bezeichnung der Stadt", "stand": STADT_DATENSTAND}


def alter_vermutet(sp: dict) -> dict | None:
    """Ohne Beleg: erste zutreffende Zeile der Formel 4.5. Babyschaukel (OSM baby_swing) zählt als eigenes Kleinkindgerät."""
    geraete = belegte_geraete(sp, ALTER_GERAETE) | {k for k, v in (sp.get("ausstattung") or {}).items()
                                                   if k in ALTER_GERAETE and (v or {}).get("wert") == "ja"}
    if "baby_swing" in ((sp.get("osm") or {}).get("geraete_roh") or []):
        geraete.add("babyschaukel")
    if len(geraete) < 2:
        return None
    if geraete & KLEINKIND and geraete & GROSSKIND:
        wert = "alle"
    elif geraete <= KLEINKIND:
        wert = "0-3"
    elif geraete & GROSSKIND:
        wert = "6-12"
    elif geraete & {"sandkasten", "rutsche", "schaukel"}:
        wert = "3-6"
    else:
        return None
    return {"wert": wert, "art": "vermutlich", "quelle": "geraete"}


def alter_bestimmen(sp: dict) -> dict | None:
    """Belegt vor vermutlich. Mehrere Belege mit unterschiedlichem Wert: die jüngere Quelle (Zitat ohne Datum zählt als ältestes)."""
    zitat = sp.get("alter_zitat") or ((sp.get("alter") or {}) if (sp.get("alter") or {}).get("quelle") == "zitat" else None)
    if zitat:
        zitat = {**zitat, "stand": sp.get("profil_stand")}
    belege = [b for b in (zitat, alter_osm(sp), alter_stadtname(sp)) if b]
    if belege:
        return sorted(belege, key=lambda b: b.get("stand") or "", reverse=True)[0]
    return alter_vermutet(sp)


# ---------------------------------------------------------------------------
# Score (4.5) und Top
# ---------------------------------------------------------------------------

def perzentil_menge(zeilen: list[dict]) -> list[float]:
    """Städtische Plätze: nicht ausgeschlossen und (freischaltbar ohne Sperr-Code oder schon aktiv)."""
    menge = []
    for z in zeilen:
        sp = z["extras"]["spielplatz"]
        if sp.get("quelle") != "stadt-duesseldorf" or sp.get("ausgeschlossen") or sp.get("groesse_m2") is None:
            continue
        if z.get("aktiv") or not sperrender_code(sp):
            menge.append(float(sp["groesse_m2"]))
    return sorted(menge)


def perzentil(wert: float, menge: list[float]) -> float:
    if len(menge) < 2:
        return 0.5
    unter = sum(1 for m in menge if m < wert)
    gleich = sum(1 for m in menge if m == wert)
    return max(0.0, min(1.0, (unter + max(gleich - 1, 0) / 2) / (len(menge) - 1)))


def google_teilwert(sp: dict) -> float:
    """Bayes-Mittel wie beim Club-Score, auf 0–1. Ohne Google 0,5."""
    g = sp.get("google") or {}
    r, n = g.get("rating"), int(g.get("anzahl") or 0)
    if not r or not n:
        return 0.5
    gewichtet = (n / (n + 100)) * float(r) + (100 / (n + 100)) * 3.8
    return max(0.0, min(1.0, (gewichtet - 3.0) / (4.6 - 3.0)))


def score(zeile: dict, menge: list[float]) -> float:
    sp = zeile["extras"]["spielplatz"]
    ausstattung = min(1.0, len(belegte_geraete(sp)) / 6)
    stadt = sp.get("quelle") == "stadt-duesseldorf"
    in_menge = stadt and not sp.get("ausgeschlossen") and sp.get("groesse_m2") is not None \
        and (zeile.get("aktiv") or not sperrender_code(sp))
    groesse = perzentil(float(sp["groesse_m2"]), menge) if in_menge else 0.5
    besonderheit = 1.0 if sp.get("typ") in ("wasser", "wald", "abenteuer") else 0.0
    if ((sp.get("extras") or {}).get("rollstuhl") or {}).get("wert") == "ja":
        besonderheit = min(1.0, besonderheit + 0.5)
    extras = sum(1 for k in EXTRAS_SCORE if ((sp.get("extras") or {}).get(k) or {}).get("wert") == "ja") / len(EXTRAS_SCORE)
    return round(0.35 * ausstattung + 0.20 * groesse + 0.20 * besonderheit + 0.15 * google_teilwert(sp) + 0.10 * extras, 4)


def top_ids(zeilen: list[dict], scores: dict) -> set[str]:
    """Beste 20 % (mindestens 1, aufgerundet) unter indexierbaren, nicht ausgeschlossenen, danach aktiven Plätzen."""
    kandidaten = [z for z in zeilen if danach_aktiv(z) and not z["extras"]["spielplatz"].get("ausgeschlossen")
                  and ist_indexierbar(z["extras"]["spielplatz"])]
    if not kandidaten:
        return set()
    anzahl = max(1, math.ceil(len(kandidaten) * 0.2))
    besten = sorted(kandidaten, key=lambda z: (-scores[z["id"]], z["name"]))[:anzahl]
    return {z["id"] for z in besten}


def berechnen(zeilen: list[dict]) -> dict:
    menge = perzentil_menge(zeilen)
    scores = {z["id"]: score(z, menge) for z in zeilen}
    top = top_ids(zeilen, scores)
    return {z["id"]: {"score": scores[z["id"]], "top": z["id"] in top, "alter": alter_bestimmen(z["extras"]["spielplatz"])}
            for z in zeilen}


# ---------------------------------------------------------------------------
# Lauf
# ---------------------------------------------------------------------------

def _laden():
    from database.client import get_supabase_client
    from scraper.orte.google_places import alle_zeilen

    db = get_supabase_client()
    return db, alle_zeilen(db, "orte", "id, name, slug, aktiv, extras", lambda q: q.eq("typ", "spielplatz"))


def schreiben(db, zeilen: list[dict], ergebnis: dict) -> int:
    fehler = 0
    for z in zeilen:
        neu = ergebnis[z["id"]]
        try:
            aktuell = (db.table("orte").select("extras").eq("id", z["id"]).execute().data or [{}])[0].get("extras") or {}
            sp = dict(aktuell.get("spielplatz") or {})
            alt_alter = sp.get("alter") or {}
            if alt_alter.get("quelle") == "zitat" and (neu["alter"] or {}).get("quelle") != "zitat":
                sp["alter_zitat"] = alt_alter  # Profil-Zitat aufheben, wenn eine jüngere Quelle gewinnt
            sp.update({"alter": neu["alter"], "score": neu["score"], "top": neu["top"]})
            db.table("orte").update({"extras": {**aktuell, "spielplatz": sp}}).eq("id", z["id"]).execute()
        except Exception as e:  # noqa: BLE001 – jede Zeile einzeln
            fehler += 1
            logger.error("Fehler bei %s: %s", z["slug"], e)
    return fehler


def lauf(dry_run: bool) -> None:
    db, zeilen = _laden()
    ergebnis = berechnen(zeilen)
    alter = [e["alter"] for e in ergebnis.values()]
    logger.info("%d Plätze: Top %d; Alter belegt %d, vermutlich %d, ohne %d; indexierbar %d%s",
                len(zeilen), sum(e["top"] for e in ergebnis.values()),
                sum(1 for a in alter if a and a["art"] == "belegt"), sum(1 for a in alter if a and a["art"] == "vermutlich"),
                sum(1 for a in alter if not a), sum(1 for z in zeilen if ist_indexierbar(z["extras"]["spielplatz"])),
                " [Dry-Run, nichts geschrieben]" if dry_run else "")
    if not dry_run:
        logger.info("Geschrieben, %d Fehler", schreiben(db, zeilen, ergebnis))


def vorschau() -> None:
    _, zeilen = _laden()
    an = sorted((z for z in zeilen if freischaltbar(z)), key=lambda z: z["slug"])
    ab = sorted((z for z in zeilen if abzuschalten(z)), key=lambda z: z["slug"])
    gesperrt = [z for z in zeilen if not z["aktiv"] and not freischaltbar(z)]
    VORSCHAU_CSV.parent.mkdir(parents=True, exist_ok=True)
    with VORSCHAU_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["aenderung", "slug", "name", "grund"])
        for z in an:
            w.writerow(["anschalten", z["slug"], z["name"], ""])
        for z in ab:
            w.writerow(["abschalten", z["slug"], z["name"], z["extras"]["spielplatz"].get("ausgeschlossen")])
        for z in gesperrt:
            sp = z["extras"]["spielplatz"]
            w.writerow(["bleibt inaktiv", z["slug"], z["name"], sp.get("ausgeschlossen") or ", ".join(sp.get("pruefung") or [])])
    logger.info("Vorschau: %d anschalten, %d abschalten, %d bleiben inaktiv – %s", len(an), len(ab), len(gesperrt), VORSCHAU_CSV)


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Spielplätze: Alter, Score, Top, Freischalt-Vorschau")
    parser.add_argument("befehl", nargs="?", choices=("vorschau",))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.befehl == "vorschau":
        vorschau()
    else:
        lauf(args.dry_run)


if __name__ == "__main__":
    main()
