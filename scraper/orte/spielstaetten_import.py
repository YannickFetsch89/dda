"""
spielstaetten_import.py – DiesDasDüsseldorf
Schritt 2 des Plans docs/plan-locations-2026-11-18.md: Import der freigegebenen Zeilen aus
data/spielstaetten/kandidaten.csv als SQL-Datei (Deploy-Punkt 3). Schreibt nichts in die Datenbank – der
Auftraggeber führt die Datei aus.

Regeln (Plan 3.1, 3.3, 3.6):
- Nur Zeilen mit `entscheidung = ja`. Häuser, Standorte, Filialen und Dachseiten brauchen `art_korrigiert`
  („Sonstiges“ ist nicht zulässig). Säle erben die Art vom Haus, wenn sie leer ist.
- Typ `spielstaette`, `aktiv = true` ausdrücklich (Standard ist false – sonst 404 im Proxy).
- Slug aus `slug_vorschlag`; abgelehnt bei Kollision mit einer vorhandenen Zeile oder einem Slug aus
  `ort_weiterleitungen` (Plan 3.3 Punkt 7). Säle brauchen ein Haus (parent_id) – sonst abgelehnt.
- `extras.spielstaette.event_orte`: alle Schreibweisen des Hauses aus den Events (wie die Kandidatenliste), ohne
  „nicht im …“ und ohne die Schreibweisen der Säle mit eigener Zeile.

Aufruf im Repo-Stamm (nur lesend):
    python -m scraper.orte.spielstaetten_import   → database/orte_spielstaetten_import_<datum>.sql
"""
import argparse
import csv
import json
import logging
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from scraper.orte.spielstaetten_kandidaten import (
    BUECHEREI_NETZ,
    KAP1,
    ZIEL as CSV,
    _norm,
    _seitenweise,
    haus_und_saal,
    namen_zaehlen,
    nicht_im,
    saal_aus_liste,
    standort_aus_liste,
)

logger = logging.getLogger(__name__)

SEITE = ("haus", "saal", "standort", "filiale")


def _sql_text(wert: str | None) -> str:
    return "NULL" if wert is None else "'" + wert.replace("'", "''") + "'"


def seitenname(z: dict) -> str:
    """Anzeigename: korrigierter Name, sonst Haus bzw. „Haus – Saal“ („D’haus Central“ + „Central 1“ → „D’haus Central 1“)."""
    if z.get("name_korrigiert"):
        return z["name_korrigiert"].strip()
    if z["zeile_typ"] != "saal":
        return z["haus"]
    haus, saal = z["gehoert_zu"], z["haus"]
    letztes = haus.split()[-1] if haus.split() else ""
    if letztes and saal.lower().startswith(letztes.lower() + " "):
        return f"{haus[: -len(letztes)]}{saal}"
    return f"{haus} – {saal}"


def zeilen_pruefen(zeilen: list[dict], vergeben: set[str], weitergeleitet: set[str],
                   guide_slugs: dict[str, str]) -> tuple[list[dict], list[str]]:
    """Freigegebene Zeilen, die importiert werden dürfen, und Ablehnungen mit Grund (rein, testbar)."""
    ok, abgelehnt = [], []
    haus_ok: dict[str, str] = {}   # Haus-Name → Slug (neue Spielstätte) …
    for z in zeilen:
        if z["zeile_typ"] == "haus" and (z.get("entscheidung") or "").strip().lower() == "ja":
            haus_ok[z["haus"]] = z["slug_vorschlag"]
    neue_slugs: set[str] = set()
    for z in zeilen:
        if (z.get("entscheidung") or "").strip().lower() != "ja" or z["zeile_typ"] not in SEITE:
            continue
        name = z["haus"] if z["zeile_typ"] == "haus" else f"{z['gehoert_zu']} › {z['haus']}"
        art = (z.get("art_korrigiert") or "").strip()
        slug = (z.get("slug_vorschlag") or "").strip()
        if z["zeile_typ"] != "saal" and (not art or art == "Sonstiges"):
            abgelehnt.append(f"{name}: keine zulässige Art in art_korrigiert")
            continue
        if not slug:
            abgelehnt.append(f"{name}: kein Slug")
            continue
        if slug in vergeben or slug in neue_slugs:
            abgelehnt.append(f"{name}: Slug „{slug}“ schon vergeben – Auftraggeber entscheidet (Plan 3.3 Punkt 7)")
            continue
        if slug in weitergeleitet:
            abgelehnt.append(f"{name}: Slug „{slug}“ steht in ort_weiterleitungen")
            continue
        eltern = None
        if z["zeile_typ"] in ("saal", "standort"):
            eltern = haus_ok.get(z["gehoert_zu"]) or guide_slugs.get(_norm(z["gehoert_zu"]))
            if not eltern:
                abgelehnt.append(f"{name}: kein freigegebenes Haus – Saal/Standort ohne parent_id (Plan 3.4)")
                continue
        neue_slugs.add(slug)
        ok.append({**z, "_eltern_slug": eltern, "_art": art, "_name": seitenname(z)})
    return ok, abgelehnt


def event_orte_zuordnen(namen: dict[str, dict], freigegeben: list[dict]) -> dict[str, list[str]]:
    """Slug → Schreibweisen (einheitliche Ortsnamen) für extras.spielstaette.event_orte."""
    alle = set(namen)
    unter: dict[tuple[str, str], str] = {}     # (Haus, Saal/Standort/Filiale) → Slug
    haus: dict[str, str] = {}                  # Haus → Slug (nur neue Spielstätten)
    for z in freigegeben:
        if z["zeile_typ"] == "haus":
            haus[z["haus"]] = z["slug_vorschlag"]
        else:
            unter[(z["gehoert_zu"], z["haus"])] = z["slug_vorschlag"]
    ergebnis: dict[str, list[str]] = defaultdict(list)
    for name in sorted(namen):
        if nicht_im(name):
            continue
        h, teil = haus_und_saal(name, alle)
        kandidaten_haus = next((x for x in haus if _norm(x) == _norm(h)), None) or \
            next((x for (x, _) in unter if _norm(x) == _norm(h)), None)
        if not kandidaten_haus:
            continue
        ziel = None
        if teil:
            if kandidaten_haus == BUECHEREI_NETZ and KAP1[1].match(name):
                ziel = unter.get((kandidaten_haus, KAP1[0]))
            else:
                s = standort_aus_liste(kandidaten_haus, teil) or saal_aus_liste(kandidaten_haus, teil)
                ziel = unter.get((kandidaten_haus, s)) if s else None
        ziel = ziel or haus.get(kandidaten_haus)
        if ziel:
            ergebnis[ziel].append(name)
    return ergebnis


def sql_text(freigegeben: list[dict], event_orte: dict[str, list[str]], abgelehnt: list[str]) -> str:
    teile = [
        "-- Import der freigegebenen Ortsseiten (Plan docs/plan-locations-2026-11-18.md, Schritt 2, Deploy-Punkt 3)",
        f"-- Erzeugt am {date.today().isoformat()} von `python -m scraper.orte.spielstaetten_import` aus",
        "-- data/spielstaetten/kandidaten.csv (nur Zeilen mit entscheidung = ja). Wiederholbar (ON CONFLICT DO NOTHING).",
        "-- Voraussetzung: database/orte_spielstaetten_2026-11-19.sql ist ausgeführt.",
        f"-- Importiert: {len(freigegeben)} Zeilen. Abgelehnt: {len(abgelehnt)}.",
    ]
    teile += [f"--   abgelehnt: {a}" for a in abgelehnt]
    teile += ["", "BEGIN;", ""]
    # Häuser zuerst, dann Säle/Standorte mit parent_id über den Slug
    for z in sorted(freigegeben, key=lambda x: x["zeile_typ"] in ("saal", "standort")):
        profil = {"art": z["_art"] or None, "zeile_typ": z["zeile_typ"],
                  "event_orte": event_orte.get(z["slug_vorschlag"], []),
                  "freigabe": z.get("bemerkung_auftraggeber") or "", "import": date.today().isoformat()}
        eltern = (f"(SELECT id FROM public.orte WHERE slug = {_sql_text(z['_eltern_slug'])})"
                  if z["_eltern_slug"] else "NULL")
        teile.append(
            "INSERT INTO public.orte (name, slug, typ, aktiv, parent_id, extras) VALUES ("
            f"{_sql_text(z['_name'])}, {_sql_text(z['slug_vorschlag'])}, 'spielstaette', true, {eltern}, "
            f"jsonb_build_object('spielstaette', {_sql_text(json.dumps(profil, ensure_ascii=False))}::jsonb)"
            ") ON CONFLICT (slug) DO NOTHING;")
    teile += ["", "COMMIT;", "",
              "-- Kontrolle: Spielstätten, davon Säle/Standorte mit Haus, ohne Schreibweisen",
              "SELECT count(*) AS spielstaetten, count(parent_id) AS mit_haus,",
              "       count(*) FILTER (WHERE jsonb_array_length(extras->'spielstaette'->'event_orte') = 0) AS ohne_schreibweisen",
              "FROM public.orte WHERE typ = 'spielstaette';"]
    return "\n".join(teile) + "\n"


def import_erzeugen(ausgabe: Path) -> int:
    from database.client import get_supabase_client

    db = get_supabase_client()
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        zeilen = list(csv.DictReader(f, delimiter=";"))
    orte = _seitenweise(db, "orte", "name, slug, typ, aktiv")
    try:
        weitergeleitet = {w["alter_slug"] for w in _seitenweise(db, "ort_weiterleitungen", "alter_slug")}
    except Exception as e:  # Tabelle fehlt, solange das Schema-SQL nicht lief
        raise SystemExit(f"Abbruch: ort_weiterleitungen nicht lesbar – zuerst database/orte_spielstaetten_2026-11-19.sql "
                         f"ausführen ({e})")
    vergeben = {o["slug"] for o in orte if o.get("slug")}
    guide_slugs = {_norm(o["name"]): o["slug"] for o in orte if o.get("aktiv") and o["typ"] != "spielstaette"}
    freigegeben, abgelehnt = zeilen_pruefen(zeilen, vergeben, weitergeleitet, guide_slugs)
    heute = date.today()
    events = _seitenweise(db, "events", "ort, adresse, stadtteil, datum, datum_bis, abgelehnt, quelle_name",
                          lambda q: q.gte("datum", (heute - timedelta(days=365)).isoformat()))
    namen, _ = namen_zaehlen(events, heute)
    ausgabe.write_text(sql_text(freigegeben, event_orte_zuordnen(namen, freigegeben), abgelehnt), encoding="utf-8")
    logger.info("Import: %d Zeilen → %s, %d abgelehnt", len(freigegeben), ausgabe, len(abgelehnt))
    for a in abgelehnt:
        logger.warning("abgelehnt: %s", a)
    return len(freigegeben)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
    except ImportError:
        pass
    parser = argparse.ArgumentParser(description="Import freigegebener Ortsseiten als SQL-Datei (nur lesend)")
    parser.add_argument("--ausgabe", default=f"database/orte_spielstaetten_import_{date.today().isoformat()}.sql")
    import_erzeugen(Path(parser.parse_args().ausgabe))


if __name__ == "__main__":
    main()
