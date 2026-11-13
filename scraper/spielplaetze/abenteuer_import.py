"""
abenteuer_import.py – DiesDasDüsseldorf
Betreute Abenteuer- und Bauspielplätze für den Guide „Spielplätze“ (Plan: docs/plan-spielplaetze-2026-11-12.md, Abschnitt 4.6).

Quelle ist die vom Auftraggeber gepflegte Datei data/spielplaetze/abenteuer.csv (nicht korrekturen.csv). Neue Zeilen werden
inaktiv angelegt (typ spielplatz, extras.spielplatz.typ und quelle "abenteuer"). Freischalten und Abschalten nur per SQL
(Schritt 6). Der Import ändert nie Profil, Foto, aktiv oder freigeschaltet_am.

Nutzung:
  python -m scraper.spielplaetze.abenteuer_import --dry-run
  python -m scraper.spielplaetze.abenteuer_import
"""
import argparse
import csv
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.slug_generator import slug_mit_suffix  # noqa: E402
from scraper.orte.google_places import _slug_erzeugen  # noqa: E402
from scraper.spielplaetze.stadt_import import (  # noqa: E402
    KATALOG, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, OSM_CODES, pruef_csv_schreiben,
)

logger = logging.getLogger(__name__)

_DATEN = Path(__file__).resolve().parents[2] / "data" / "spielplaetze"
ABENTEUER_CSV = _DATEN / "abenteuer.csv"
PRUEF_CSV = _DATEN / "abenteuer_pruefung.csv"
QUELLE = "abenteuer"
SCHLUESSEL_MUSTER = re.compile(r"^abenteuer:[a-z0-9-]+$")


# ---------------------------------------------------------------------------
# Datei lesen und prüfen (rein)
# ---------------------------------------------------------------------------

def _zahl(text: str) -> float | None:
    try:
        return float(text.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def zeile_pruefen(z: dict) -> tuple[dict | None, list[str], list[str]]:
    """
    Eine CSV-Zeile prüfen. Rückgabe (gültige Zeile oder None, Fehler, Hinweise).
    Ungültig: Pflichtfeld fehlt/falsch (schluessel, name, Koordinate im Rechteck, eintritt ja|nein, quelle_url),
    ausschliessen weder leer noch ja, ausschliessen=ja ohne Grund. Ein Nicht-Katalog-Stadtteil macht die Zeile nicht ungültig.
    """
    fehler, hinweise = [], []
    schluessel = z.get("schluessel", "")
    lat, lon = _zahl(z.get("latitude", "")), _zahl(z.get("longitude", ""))
    if not SCHLUESSEL_MUSTER.match(schluessel):
        fehler.append(f"Schlüssel „{schluessel}“ passt nicht zu abenteuer:[a-z0-9-]+")
    if not z.get("name"):
        fehler.append("Name fehlt")
    if lat is None or lon is None or not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
        fehler.append("Koordinate fehlt oder liegt nicht in Düsseldorf")
    eintritt = z.get("eintritt", "").lower()
    if eintritt not in ("ja", "nein"):
        fehler.append(f"Eintritt „{z.get('eintritt', '')}“ ist weder ja noch nein")
    if not z.get("quelle_url", "").startswith(("http://", "https://")):
        fehler.append("quelle_url fehlt")
    aus = z.get("ausschliessen", "").lower()
    if aus not in ("", "ja"):
        fehler.append(f"ausschliessen „{z.get('ausschliessen')}“ ist weder leer noch ja")
    if aus == "ja" and not z.get("grund"):
        fehler.append("ausschliessen=ja ohne Grund")
    bestaetigt = []
    for code in [c.strip() for c in z.get("bestaetigt", "").split(",") if c.strip()]:
        if code == "access_private":
            bestaetigt.append(code)
        else:
            hinweise.append(f"Code „{code}“ in bestaetigt ignoriert (nur access_private)")
    if fehler:
        return None, fehler, hinweise
    stadtteil = z.get("stadtteil", "")
    if stadtteil and stadtteil not in KATALOG:
        hinweise.append(f"Stadtteil „{stadtteil}“ ist kein Katalogwert")
    return {
        "schluessel": schluessel, "name": z["name"], "traeger": z.get("traeger", ""), "adresse": z.get("adresse", ""),
        "latitude": round(lat, 7), "longitude": round(lon, 7),
        "stadtteil": stadtteil if stadtteil in KATALOG else None, "stadtteil_ungueltig": bool(stadtteil) and stadtteil not in KATALOG,
        "oeffnungszeiten": z.get("oeffnungszeiten", ""), "eintritt": eintritt, "quelle_url": z["quelle_url"],
        "ausgeschlossen": z["grund"] if aus == "ja" else None, "bestaetigt": sorted(set(bestaetigt)),
    }, [], hinweise


def abenteuer_lesen(pfad: Path) -> tuple[dict | None, list[str]]:
    """
    Liest abenteuer.csv (Trennzeichen ; oder ,). Fehlt die Datei: (None, []).
    Rückgabe ({schluessel: gültige Zeile oder {"ungueltig": True}}, Meldungen). Doppelte Schlüssel: die erste gilt.
    """
    if not pfad.exists():
        return None, []
    text = pfad.read_text(encoding="utf-8-sig")
    erste = text.splitlines()[0] if text.strip() else ""
    trenner = ";" if erste.count(";") >= erste.count(",") else ","
    daten, meldungen = {}, []
    for nr, roh in enumerate(csv.DictReader(text.splitlines(), delimiter=trenner), start=2):
        z = {(k or "").strip().lower(): (v or "").strip() for k, v in roh.items()}
        if not any(z.values()):
            continue
        zeile, fehler, hinweise = zeile_pruefen(z)
        schluessel = z.get("schluessel", "")
        meldungen += [f"abenteuer.csv Zeile {nr} ({schluessel}): {f}" for f in fehler + hinweise]
        if schluessel in daten:
            meldungen.append(f"abenteuer.csv Zeile {nr}: {schluessel} doppelt – die erste Zeile gilt")
            continue
        daten[schluessel] = zeile if zeile else {"ungueltig": True}
    return daten, meldungen


# ---------------------------------------------------------------------------
# Planung (rein)
# ---------------------------------------------------------------------------

def planen(eintraege: dict, bestehend: list[dict], andere_slugs: set[str]) -> dict:
    """
    eintraege: Ergebnis von abenteuer_lesen; bestehend: Zeilen mit extras.spielplatz.quelle="abenteuer";
    andere_slugs: Slugs aller übrigen Zeilen der Tabelle orte.
    Rückgabe {neu, aenderungen, log}. Ungültige Zeile: neue wird nicht angelegt, bestehende bleibt vollständig unverändert.
    """
    nach_schluessel = {((z.get("extras") or {}).get("spielplatz") or {}).get("schluessel"): z for z in bestehend}
    neu, aenderungen, log = [], [], []
    feste = set(andere_slugs)
    zu_benennen = []
    for z in bestehend:
        sp = z["extras"]["spielplatz"]
        if sp.get("freigeschaltet_am") or eintraege.get(sp.get("schluessel"), {}).get("ungueltig") \
                or sp.get("schluessel") not in eintraege:
            feste.add(z["slug"])  # fester oder unveränderter Slug bleibt reserviert
    for schluessel in sorted(set(nach_schluessel) - set(eintraege) - {None}):
        log.append(f"{schluessel} steht nicht mehr in abenteuer.csv – nichts geändert (Abschalten nur über ausschliessen)")

    for schluessel in sorted(eintraege):
        e = eintraege[schluessel]
        zeile = nach_schluessel.get(schluessel)
        if e.get("ungueltig"):
            log.append(f"{schluessel}: ungültige Zeile – " + ("nicht angelegt" if not zeile else "Datenbankzeile unverändert"))
            continue
        sp_alt = ((zeile or {}).get("extras") or {}).get("spielplatz") or {}
        freigeschaltet = bool(sp_alt.get("freigeschaltet_am"))
        stadtteil = e["stadtteil"] if e["stadtteil"] else ((zeile or {}).get("stadtteil") if e["stadtteil_ungueltig"] else None)
        codes = {c for c in sp_alt.get("pruefung") or [] if c in OSM_CODES}
        if not e["stadtteil"]:
            codes.add("kein_stadtteil")
        felder = {
            "quelle": QUELLE, "schluessel": schluessel, "typ": "abenteuer", "quelle_url": e["quelle_url"],
            "traeger": e["traeger"] or None, "eintritt": e["eintritt"], "pruefung": sorted(codes),
            "bestaetigt": e["bestaetigt"], "ausgeschlossen": e["ausgeschlossen"], "name_quelle": "abenteuer",
        }
        spalten = {"name": e["name"], "stadtteil": stadtteil, "adresse": e["adresse"] or None,
                   "latitude": e["latitude"], "longitude": e["longitude"], "oeffnungszeiten": e["oeffnungszeiten"] or None}
        d = {"schluessel": schluessel, "zeile": zeile, "spalten": spalten, "felder": felder}
        if freigeschaltet:
            spalten["slug"] = zeile["slug"]
        else:
            zu_benennen.append(d)
        (aenderungen if zeile else neu).append(d)

    vergeben = set(feste)
    for d in sorted(zu_benennen, key=lambda d: d["schluessel"]):
        d["spalten"]["slug"] = slug_mit_suffix(_slug_erzeugen(d["spalten"]["name"], d["spalten"]["stadtteil"]), vergeben)
        vergeben.add(d["spalten"]["slug"])
    return {"neu": neu, "aenderungen": aenderungen, "log": log}


# ---------------------------------------------------------------------------
# Schreiben
# ---------------------------------------------------------------------------

def schreiben(db, plan: dict) -> dict:
    """Neue Zeilen inaktiv anlegen; bestehende: nur die Felder aus abenteuer.csv (extras frisch lesen, nie aktiv)."""
    zaehler = {"neu": 0, "aktualisiert": 0, "fehler": 0}
    wechsel = [a for a in plan["aenderungen"] if a["spalten"]["slug"] != a["zeile"]["slug"]]
    for a in wechsel:
        db.table("orte").update({"slug": f"tmp-spielplatz-{a['zeile']['id']}"}).eq("id", a["zeile"]["id"]).execute()
    for a in plan["aenderungen"]:
        try:
            aktuell = (db.table("orte").select("extras").eq("id", a["zeile"]["id"]).execute().data or [{}])[0].get("extras") or {}
            sp = {**(aktuell.get("spielplatz") or {}), **a["felder"]}
            db.table("orte").update({"extras": {**aktuell, "spielplatz": sp}, **a["spalten"]}).eq("id", a["zeile"]["id"]).execute()
            zaehler["aktualisiert"] += 1
        except Exception as e:  # noqa: BLE001 – jede Zeile einzeln
            zaehler["fehler"] += 1
            logger.error("Fehler bei %s: %s", a["schluessel"], e)
    for d in plan["neu"]:
        try:
            db.table("orte").insert({**d["spalten"], "typ": "spielplatz", "aktiv": False, "qualitaets_score": None,
                                     "bild_url": None, "extras": {"spielplatz": {**d["felder"], "freigeschaltet_am": None}}}).execute()
            zaehler["neu"] += 1
        except Exception as e:  # noqa: BLE001
            zaehler["fehler"] += 1
            logger.error("Fehler beim Anlegen von %s: %s", d["schluessel"], e)
    return zaehler


def importieren(dry_run: bool) -> None:
    eintraege, meldungen = abenteuer_lesen(ABENTEUER_CSV)
    for m in meldungen:
        logger.error("%s", m)
    if eintraege is None:
        logger.info("abenteuer.csv fehlt – nichts zu tun")
        return
    from database.client import get_supabase_client
    from scraper.orte.google_places import alle_zeilen

    db = get_supabase_client()
    alle = alle_zeilen(db, "orte", "id, name, slug, typ, stadtteil, aktiv, extras")
    ist_abenteuer = lambda z: z["typ"] == "spielplatz" and ((z.get("extras") or {}).get("spielplatz") or {}).get("quelle") == QUELLE  # noqa: E731
    plan = planen(eintraege, [z for z in alle if ist_abenteuer(z)], {z["slug"] for z in alle if not ist_abenteuer(z)})
    for m in plan["log"]:
        logger.info("%s", m)
    pruef_csv_schreiben([{"schluessel": d["schluessel"], "name": d["spalten"]["name"], "slug": d["spalten"]["slug"],
                          "stadtteil": d["spalten"]["stadtteil"] or "", "eintritt": d["felder"]["eintritt"],
                          "pruef_codes": ", ".join(d["felder"]["pruefung"]), "ausgeschlossen": d["felder"]["ausgeschlossen"] or "",
                          "status": "neu" if not d["zeile"] else "aktualisiert"}
                         for d in plan["neu"] + plan["aenderungen"]], PRUEF_CSV)
    logger.info("Plan: %d neu, %d aktualisiert%s", len(plan["neu"]), len(plan["aenderungen"]),
                " [Dry-Run, nichts geschrieben]" if dry_run else "")
    if not dry_run:
        logger.info("Fertig: %s", schreiben(db, plan))


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Spielplätze: Abenteuer-/Bauspielplätze aus abenteuer.csv")
    parser.add_argument("--dry-run", action="store_true")
    importieren(parser.parse_args().dry_run)


if __name__ == "__main__":
    main()
