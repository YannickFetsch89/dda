"""
import_maerkte.py – DiesDasDüsseldorf
Schreibt die geprüften Pflegedateien des Weihnachtsmarkt-Guides nach Supabase `orte` (typ weihnachtsmarkt)
(Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, Abschnitte 3.1 und 3.2).

Quellen (eingecheckt): data/weihnachtsmaerkte/maerkte.csv, saison-2026.csv, merkmale.csv.
- Neue Zeilen werden INAKTIV angelegt; der Import ändert aktiv und freigeschaltet_am nie (Freischalten nur per SQL,
  database/weihnachtsmaerkte_freischalten.sql).
- Zeiten werden streng geprüft (scraper/weihnachtsmaerkte/zeiten.py); ein Fehler → Saison dieser Zeile wird nicht geschrieben.
- Teilmärkte erben von/bis/zeiten/sonder FELDWEISE von der Gruppe (leere Zelle = geerbt); Attraktionen erben nie.
- Slug: Name + Stadtteil, fest ab der ersten Freischaltung; Kollisionen gegen die ganze Tabelle orte.
- Keine Google-Bewertungen (Plan E12): der Import schreibt nie rating/userRatingCount.

Nutzung:
  python -m scraper.weihnachtsmaerkte.import_maerkte --dry-run
  python -m scraper.weihnachtsmaerkte.import_maerkte
"""
from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.slug_generator import slug_mit_suffix  # noqa: E402
from scraper.orte.google_places import _slug_erzeugen  # noqa: E402
from scraper.spielplaetze.stadt_import import KATALOG as KATALOG_DUESSELDORF  # noqa: E402
from scraper.weihnachtsmaerkte.zeiten import ZeitFehler, sonder_lesen, zeiten_lesen, zeitraum_pruefen  # noqa: E402

logger = logging.getLogger(__name__)

DATEN = Path(__file__).resolve().parents[2] / "data" / "weihnachtsmaerkte"
MAERKTE_CSV = DATEN / "maerkte.csv"
MERKMALE_CSV = DATEN / "merkmale.csv"
PRUEF_CSV = DATEN / "pruefung.csv"
SAISON = "2026"
SAISON_CSV = DATEN / f"saison-{SAISON}.csv"

TYP = "weihnachtsmarkt"
KATALOG = frozenset(KATALOG_DUESSELDORF | {"Neuss", "Ratingen"})
# Kartenausschnitt (web/public/karte/region.pmtiles): bbox 6.55,51.08,6.99,51.39
LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = 6.55, 7.00, 51.08, 51.40
SCHLUESSEL_MUSTER = re.compile(r"^[a-z0-9-]+$")
ARTEN = {"klassisch", "mittelalter", "kunsthandwerk", "alternativ", "schloss", "eisbahn", "riesenrad"}
MERKMALE = {"eisbahn", "riesenrad", "karussell", "kindereisenbahn", "kinderprogramm", "puppenbuehne", "buehnenprogramm",
            "kunsthandwerk", "krippe", "tassenpfand", "barrierefrei", "wc", "ueberdacht"}
MERKMAL_QUELLEN = {"zitat", "sichtung", "auftraggeber"}
SAISON_QUELLEN = {"toubiz", "veranstalter", "auftraggeber"}
ERBFELDER = ("von", "bis", "zeiten", "sonder")
STICHTAGE = ("2026-11-22", "2026-12-24", "2026-12-26", "2026-12-31", "2027-01-01")


# ---------------------------------------------------------------------------
# Dateien lesen und prüfen (rein)
# ---------------------------------------------------------------------------

def csv_lesen(pfad: Path) -> list[dict] | None:
    if not pfad.exists():
        return None
    with pfad.open(encoding="utf-8", newline="") as f:
        return [{k: (v or "").strip() for k, v in z.items()} for z in csv.DictReader(f)]


def _ja(wert: str) -> bool:
    return wert.strip().lower() in {"ja", "x", "1", "true"}


def _zahl(text: str) -> float | None:
    try:
        return float(text.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def markt_pruefen(z: dict) -> tuple[dict | None, list[str]]:
    """Eine Zeile aus maerkte.csv → Eintrag oder (None, Fehler)."""
    fehler = []
    s = z.get("schluessel", "")
    if not SCHLUESSEL_MUSTER.match(s):
        return None, [f"Schlüssel ungültig: „{s}“"]
    if not z.get("name"):
        fehler.append(f"{s}: Name fehlt")
    if z.get("stadtteil") not in KATALOG:
        fehler.append(f"{s}: Stadtteil „{z.get('stadtteil')}“ ist kein Katalogwert")
    lat, lng = _zahl(z.get("lat", "")), _zahl(z.get("lng", ""))
    if lat is None or lng is None or not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lng <= LON_MAX):
        fehler.append(f"{s}: Koordinate fehlt oder liegt außerhalb des Kartenausschnitts ({z.get('lat')}, {z.get('lng')})")
    arten = [a for a in (z.get("art") or "").split("|") if a]
    falsch = [a for a in arten if a not in ARTEN]
    if falsch:
        fehler.append(f"{s}: unbekannte Art {falsch}")
    if _ja(z.get("ausschliessen", "")) and not z.get("grund"):
        fehler.append(f"{s}: ausschliessen ohne Grund")
    if z.get("eintritt") and z["eintritt"] not in {"frei", "kostenpflichtig"}:
        fehler.append(f"{s}: eintritt muss frei oder kostenpflichtig sein")
    if z.get("eintritt") and not z.get("eintritt_beleg"):
        fehler.append(f"{s}: eintritt ohne Beleg")
    if z.get("anfahrt_haltestellen") and not z.get("anfahrt_beleg"):
        fehler.append(f"{s}: Anfahrt ohne Beleg")
    rang = z.get("top5_rang", "")
    if rang and rang not in {"1", "2", "3", "4", "5"}:
        fehler.append(f"{s}: top5_rang muss 1–5 sein")
    manuell = _zahl(z.get("score_manuell", "")) if z.get("score_manuell") else None
    if z.get("score_manuell") and (manuell is None or not 0 <= manuell <= 10):
        fehler.append(f"{s}: score_manuell muss 0–10 sein")
    # Mehrere Muster mit „||“ getrennt (ein einfaches „|“ gehört zum regulären Ausdruck)
    muster = [m.strip() for m in (z.get("event_muster") or "").split("||") if m.strip()]
    for m in muster:
        try:
            re.compile(m)
        except re.error:
            fehler.append(f"{s}: event_muster ist kein gültiger regulärer Ausdruck: {m}")
    if fehler:
        return None, fehler
    return {
        "schluessel": s, "name": z["name"], "gruppe": z.get("gruppe") or None, "ist_gruppe": _ja(z.get("ist_gruppe", "")),
        "attraktion": _ja(z.get("attraktion", "")), "immer_im_guide": _ja(z.get("immer_im_guide", "")), "art": arten,
        "stadtteil": z["stadtteil"], "adresse": z.get("adresse") or None, "latitude": lat, "longitude": lng,
        "koord_quelle": z.get("koord_quelle") or None, "webseite": z.get("webseite") or None,
        "toubiz_url": z.get("toubiz_url") or None, "veranstalter": z.get("veranstalter") or None,
        "lage": z.get("lage") or None, "quelle_url": z.get("quelle_url") or None,
        "eintritt": {"wert": z["eintritt"], "beleg": z["eintritt_beleg"]} if z.get("eintritt") else None,
        "anfahrt": {"haltestellen": [{"name": h} for h in z["anfahrt_haltestellen"].split("|") if h], "beleg": z["anfahrt_beleg"]}
        if z.get("anfahrt_haltestellen") else None,
        "staende": {"anzahl": int(z["staende"]), "beleg": z.get("staende_beleg")} if z.get("staende", "").isdigit() and z.get("staende_beleg") else None,
        "beschreibung": z.get("beschreibung") or None, "event_muster": muster,
        "top5_rang": int(rang) if rang else None, "score_manuell": manuell,
        "ausgeschlossen": z["grund"] if _ja(z.get("ausschliessen", "")) else None,
    }, []


def saison_pruefen(z: dict) -> tuple[dict | None, list[str]]:
    """Zeile aus saison-JJJJ.csv → rohe Saison (leere Felder bleiben None, damit feldweise geerbt werden kann)."""
    s = z.get("schluessel", "")
    try:
        if (z.get("von") or z.get("bis")) and z.get("von") and z.get("bis"):
            zeitraum_pruefen(z["von"], z["bis"])
        elif z.get("von"):
            zeitraum_pruefen(z["von"], z["von"])
        elif z.get("bis"):
            zeitraum_pruefen(z["bis"], z["bis"])
        zeiten = zeiten_lesen(z["zeiten"]) if z.get("zeiten") else None
        sonder = sonder_lesen(z["sonder"]) if z.get("sonder") else None
    except ZeitFehler as fehler:
        return None, [f"{s}: {fehler} – Saison wird nicht geschrieben"]
    if z.get("quelle") not in SAISON_QUELLEN:
        return None, [f"{s}: quelle muss toubiz, veranstalter oder auftraggeber sein"]
    if not z.get("beleg") or not z.get("url") or not z.get("stand"):
        return None, [f"{s}: Saison ohne beleg/url/stand – nicht geschrieben"]
    return {"von": z.get("von") or None, "bis": z.get("bis") or None, "zeiten": zeiten, "sonder": sonder,
            "quelle": z["quelle"], "beleg": z["beleg"], "url": z["url"], "stand": z["stand"]}, []


def saison_aufloesen(eigen: dict | None, gruppe: dict | None, darf_erben: bool) -> tuple[dict | None, list[str]]:
    """
    Feldweise Erbung (Plan 3.2): leeres Feld übernimmt das Feld der Gruppe. Ergebnis wird vollständig geprüft
    (von ≤ bis, Sonderdaten im Zeitraum). None = keine Saison.
    """
    if not eigen and not (darf_erben and gruppe):
        return None, []
    eigen = eigen or {}
    geerbt = []
    saison = {}
    for feld in ERBFELDER:
        wert = eigen.get(feld)
        if wert is None and darf_erben and gruppe and gruppe.get(feld) is not None:
            wert = gruppe[feld]
            geerbt.append(feld)
        saison[feld] = wert
    saison["zeiten"] = saison["zeiten"] or []
    saison["sonder"] = saison["sonder"] or []
    quelle = eigen if eigen.get("beleg") else (gruppe or {})
    saison.update({k: quelle.get(k) for k in ("quelle", "beleg", "url", "stand")})
    if geerbt:
        saison["geerbt"] = geerbt
    if not saison["von"] or not saison["bis"]:
        return None, ["Saison ohne vollständigen Zeitraum – nicht geschrieben"]
    try:
        zeitraum_pruefen(saison["von"], saison["bis"])
    except ZeitFehler as fehler:
        return None, [str(fehler)]
    meldungen = []
    eigene_sonder = {so["datum"] for so in eigen.get("sonder") or []}
    ausserhalb = [so for so in saison["sonder"] if not saison["von"] <= so["datum"] <= saison["bis"]]
    if any(so["datum"] in eigene_sonder for so in ausserhalb):
        return None, [f"Sonderdatum außerhalb des Zeitraums {saison['von']} bis {saison['bis']}"]
    # Geerbte Sonderzeiten außerhalb des eigenen Zeitraums (z. B. vor einem späteren Start) entfallen still
    saison["sonder"] = [so for so in saison["sonder"] if saison["von"] <= so["datum"] <= saison["bis"]]
    return saison, meldungen


def merkmale_pruefen(zeilen: list[dict], schluessel: set[str]) -> tuple[dict, list[str]]:
    ergebnis: dict[str, dict] = {}
    fehler = []
    gesehen = set()
    for z in zeilen:
        s, m = z.get("schluessel"), z.get("merkmal")
        if s not in schluessel:
            fehler.append(f"merkmale.csv: unbekannter Schlüssel {s}")
            continue
        if m not in MERKMALE:
            fehler.append(f"merkmale.csv: {s}: unbekanntes Merkmal {m}")
            continue
        if (s, m) in gesehen:
            fehler.append(f"merkmale.csv: {s}/{m} doppelt")
            continue
        wert = z.get("wert")
        if wert not in {"ja", "nein"} and not (m == "barrierefrei" and wert == "teilweise"):
            fehler.append(f"merkmale.csv: {s}/{m}: Wert {wert} ungültig")
            continue
        if z.get("quelle") not in MERKMAL_QUELLEN or not z.get("beleg") or not z.get("stand"):
            fehler.append(f"merkmale.csv: {s}/{m}: Quelle, Beleg oder Stand fehlt")
            continue
        try:
            date.fromisoformat(z["stand"])
        except ValueError:
            fehler.append(f"merkmale.csv: {s}/{m}: Stand kein Datum")
            continue
        gesehen.add((s, m))
        eintrag = {"wert": wert, "quelle": z["quelle"], "beleg": z["beleg"], "stand": z["stand"]}
        if z.get("notiz"):
            eintrag["notiz"] = z["notiz"]
        if z.get("url"):
            eintrag["url"] = z["url"]
        ergebnis.setdefault(s, {})[m] = eintrag
    return ergebnis, fehler


def eintraege_bilden(maerkte: list[dict], saisons: list[dict], merkmale: list[dict]) -> tuple[dict, list[str]]:
    """Alle Dateien → {schluessel: eintrag mit extras_wm}. Ungültige Zeilen: {ungueltig: True}."""
    fehler: list[str] = []
    eintraege: dict[str, dict] = {}
    for z in maerkte:
        e, f = markt_pruefen(z)
        fehler += f
        if e is None:
            s = z.get("schluessel", "")
            if SCHLUESSEL_MUSTER.match(s):
                eintraege[s] = {"ungueltig": True}
            continue
        if e["schluessel"] in eintraege:
            fehler.append(f"{e['schluessel']}: Schlüssel doppelt")
            continue
        eintraege[e["schluessel"]] = e
    roh_saison: dict[str, dict] = {}
    for z in saisons:
        r, f = saison_pruefen(z)
        fehler += f
        if r is not None:
            roh_saison[z["schluessel"]] = r
    unbekannt = set(roh_saison) - set(eintraege)
    fehler += [f"saison-{SAISON}.csv: unbekannter Schlüssel {s}" for s in sorted(unbekannt)]
    mm, f = merkmale_pruefen(merkmale, set(eintraege))
    fehler += f
    for s, e in eintraege.items():
        if e.get("ungueltig"):
            continue
        gruppe = e["gruppe"]
        if gruppe and (gruppe not in eintraege or not eintraege[gruppe].get("ist_gruppe")):
            fehler.append(f"{s}: Gruppe {gruppe} fehlt oder ist keine Gruppenzeile")
            gruppe = None
        darf_erben = bool(gruppe) and not e["attraktion"]
        saison, f = saison_aufloesen(roh_saison.get(s), roh_saison.get(gruppe) if gruppe else None, darf_erben)
        fehler += [f"{s}: {x}" for x in f]
        if saison and saison.get("geerbt"):
            saison["geerbt_von"] = gruppe
        e["saison"] = saison
        e["merkmale"] = mm.get(s, {})
    return eintraege, fehler


def extras_bauen(e: dict, alt: dict | None) -> dict:
    """extras.weihnachtsmarkt aus dem Eintrag; übernimmt freigeschaltet_am und Score aus der Datenbank (nie aus der CSV)."""
    alt = alt or {}
    saisons = dict(alt.get("saisons") or {})
    if e.get("saison"):
        saisons[SAISON] = e["saison"]
    else:
        saisons.pop(SAISON, None)
    wm = {
        "schluessel": e["schluessel"], "gruppe": e["gruppe"], "ist_gruppe": e["ist_gruppe"], "attraktion": e["attraktion"],
        "immer_im_guide": e["immer_im_guide"], "art": e["art"], "veranstalter": e["veranstalter"],
        "quelle_url": e["quelle_url"], "toubiz_url": e["toubiz_url"], "lage": e["lage"], "koord_quelle": e["koord_quelle"],
        "eintritt": e["eintritt"], "anfahrt": e["anfahrt"], "staende": e["staende"], "merkmale": e["merkmale"],
        "saisons": saisons, "event_muster": e["event_muster"], "top5_rang": e["top5_rang"],
        "ausgeschlossen": e["ausgeschlossen"], "freigeschaltet_am": alt.get("freigeschaltet_am"),
    }
    score = dict(alt.get("score") or {})
    if e["score_manuell"] is not None:
        score["manuell"] = e["score_manuell"]
    else:
        score.pop("manuell", None)
    if score:
        wm["score"] = score
    return wm


def planen(eintraege: dict, bestehend: list[dict], andere_slugs: set[str]) -> dict:
    """Wie abenteuer_import.planen: neue Zeilen, Änderungen, Slugs (fest ab Freischaltung, Kollisionen gegen alle orte)."""
    nach_schluessel = {((z.get("extras") or {}).get(TYP) or {}).get("schluessel"): z for z in bestehend}
    neu, aenderungen, log = [], [], []
    feste = set(andere_slugs)
    zu_benennen = []
    for z in bestehend:
        wm = z["extras"][TYP]
        if wm.get("freigeschaltet_am") or eintraege.get(wm.get("schluessel"), {}).get("ungueltig") \
                or wm.get("schluessel") not in eintraege:
            feste.add(z["slug"])
    for s in sorted(set(nach_schluessel) - set(eintraege) - {None}):
        log.append(f"{s} steht nicht mehr in maerkte.csv – nichts geändert (Abschalten nur über ausschliessen)")
    for s in sorted(eintraege):
        e = eintraege[s]
        zeile = nach_schluessel.get(s)
        if e.get("ungueltig"):
            log.append(f"{s}: ungültige Zeile – " + ("nicht angelegt" if not zeile else "Datenbankzeile unverändert"))
            continue
        alt = ((zeile or {}).get("extras") or {}).get(TYP)
        spalten = {"name": e["name"], "stadtteil": e["stadtteil"], "adresse": e["adresse"], "latitude": e["latitude"],
                   "longitude": e["longitude"], "webseite": e["webseite"], "beschreibung": e["beschreibung"]}
        d = {"schluessel": s, "zeile": zeile, "spalten": spalten, "wm": extras_bauen(e, alt)}
        if alt and alt.get("freigeschaltet_am"):
            spalten["slug"] = zeile["slug"]
        else:
            zu_benennen.append(d)
        (aenderungen if zeile else neu).append(d)
    vergeben = set(feste)
    for d in sorted(zu_benennen, key=lambda d: d["schluessel"]):
        d["spalten"]["slug"] = slug_mit_suffix(_slug_erzeugen(d["spalten"]["name"], d["spalten"]["stadtteil"]), vergeben)
        vergeben.add(d["spalten"]["slug"])
    return {"neu": neu, "aenderungen": aenderungen, "log": log}


def pruef_zeilen(plan: dict) -> list[dict]:
    """Prüf-CSV: Zeitraum, Zeiten, Sonderzeiten, Zustand an den Stichtagen (gleiche Logik wie die Website)."""
    from scraper.weihnachtsmaerkte.zeiten import kurzschrift, oeffnung_am, sonder_kurzschrift

    zeilen = []
    for d in plan["neu"] + plan["aenderungen"]:
        wm = d["wm"]
        s = (wm["saisons"] or {}).get(SAISON) or {}
        zustaende = {}
        for tag in STICHTAGE:
            o = oeffnung_am(wm["saisons"], tag)
            zustaende[tag] = o["zustand"] + (f" {o['von']}-{o['bis']}" if o.get("von") else "")
        zeilen.append({
            "schluessel": d["schluessel"], "name": d["spalten"]["name"], "slug": d["spalten"]["slug"],
            "stadtteil": d["spalten"]["stadtteil"], "von": s.get("von") or "", "bis": s.get("bis") or "",
            "zeiten": kurzschrift(s.get("zeiten") or []), "sonder": sonder_kurzschrift(s.get("sonder") or []),
            "geerbt": ",".join(s.get("geerbt") or []), "quelle": s.get("url") or "", "stand": s.get("stand") or "",
            "merkmale": ",".join(sorted(wm["merkmale"])), "beschreibung": "ja" if d["spalten"]["beschreibung"] else "FEHLT",
            **{f"am_{t}": v for t, v in zustaende.items()},
            "status": "neu" if not d["zeile"] else "aktualisiert", "ausgeschlossen": wm["ausgeschlossen"] or "",
        })
    return zeilen


# ---------------------------------------------------------------------------
# Schreiben
# ---------------------------------------------------------------------------

def schreiben(db, plan: dict) -> dict:
    """Neue Zeilen inaktiv anlegen; bestehende: Spalten + extras.weihnachtsmarkt (extras frisch lesen, nie aktiv)."""
    zaehler = {"neu": 0, "aktualisiert": 0, "fehler": 0}
    for a in [a for a in plan["aenderungen"] if a["spalten"]["slug"] != a["zeile"]["slug"]]:
        db.table("orte").update({"slug": f"tmp-wm-{a['zeile']['id']}"}).eq("id", a["zeile"]["id"]).execute()
    for a in plan["aenderungen"]:
        try:
            aktuell = (db.table("orte").select("extras").eq("id", a["zeile"]["id"]).execute().data or [{}])[0].get("extras") or {}
            alt = aktuell.get(TYP) or {}
            wm = {**a["wm"], "freigeschaltet_am": alt.get("freigeschaltet_am")}  # nie überschreiben
            db.table("orte").update({"extras": {**aktuell, TYP: wm}, **a["spalten"]}).eq("id", a["zeile"]["id"]).execute()
            zaehler["aktualisiert"] += 1
        except Exception as e:  # noqa: BLE001 – jede Zeile einzeln
            zaehler["fehler"] += 1
            logger.error("Fehler bei %s: %s", a["schluessel"], e)
    for d in plan["neu"]:
        try:
            db.table("orte").insert({**d["spalten"], "typ": TYP, "aktiv": False, "qualitaets_score": None, "bild_url": None,
                                     "extras": {TYP: {**d["wm"], "freigeschaltet_am": None}}}).execute()
            zaehler["neu"] += 1
        except Exception as e:  # noqa: BLE001
            zaehler["fehler"] += 1
            logger.error("Fehler beim Anlegen von %s: %s", d["schluessel"], e)
    return zaehler


def importieren(dry_run: bool) -> None:
    from scraper.spielplaetze.stadt_import import pruef_csv_schreiben

    maerkte = csv_lesen(MAERKTE_CSV)
    if maerkte is None:
        logger.error("%s fehlt – nichts zu tun", MAERKTE_CSV)
        return
    eintraege, fehler = eintraege_bilden(maerkte, csv_lesen(SAISON_CSV) or [], csv_lesen(MERKMALE_CSV) or [])
    for f in fehler:
        logger.error("%s", f)
    from database.client import get_supabase_client
    from scraper.orte.google_places import alle_zeilen

    db = get_supabase_client()
    alle = alle_zeilen(db, "orte", "id, name, slug, typ, stadtteil, aktiv, extras")
    eigene = [z for z in alle if z["typ"] == TYP and ((z.get("extras") or {}).get(TYP) or {}).get("schluessel")]
    plan = planen(eintraege, eigene, {z["slug"] for z in alle if z not in eigene})
    for m in plan["log"]:
        logger.info("%s", m)
    pruef_csv_schreiben(pruef_zeilen(plan), PRUEF_CSV)
    logger.info("Prüf-CSV: %s", PRUEF_CSV)
    logger.info("Plan: %d neu, %d aktualisiert%s", len(plan["neu"]), len(plan["aenderungen"]),
                " [Dry-Run, nichts geschrieben]" if dry_run else "")
    if not dry_run:
        logger.info("Fertig: %s", schreiben(db, plan))


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Weihnachtsmärkte: Pflegedateien nach orte schreiben (inaktiv)")
    parser.add_argument("--dry-run", action="store_true")
    importieren(parser.parse_args().dry_run)


if __name__ == "__main__":
    main()
