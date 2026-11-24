"""
quellen_nachziehen.py – DiesDasDüsseldorf
Einmaliges Umhängen des Bestands auf die Rangfolge der Quellen (Plan docs/plan-quellen-ausbau-2026-11-23.md, 4.2
Punkt 4, Schritt N1). Nachfolger von pipeline/rausgegangen_nachziehen.py (das alte Modul ruft dieses auf).

Seit R1 führt das tägliche Speichern ein Event unter der Quelle mit dem besten Rang (1 Haus · 2 Ticketverkauf ·
3 Portale · 4 Aggregatoren · 5 Rausgegangen, pipeline/quellen_rang.py). Dieses Skript wendet dieselbe Regel einmal
auf die schon gespeicherten künftigen Events an, deren Quelle nicht das Haus selbst ist:

  1. Alle Quellen außer Rausgegangen einmal scrapen – ohne die im Admin-Bereich abgeschalteten, mit Gebietsfilter
     und Deduplizierung wie im täglichen Lauf (Zwischenspeicher data/quellen_nachziehen/events.json).
  2. Je gespeichertem Event (Rang ≥ 2) dasselbe Event in den gescrapten suchen (gleicher Titel+Ort, gleicher Slug
     oder ähnlich – jeweils gleiche oder fehlende Uhrzeit) und davon das mit dem besten Rang nehmen.
  3. Die Änderung genau wie beim täglichen Speichern bauen (database.client._anreicherungs_update_bauen, mit Rang
     und Quellenliste): Quellenwechsel nur zu einem strikt besseren Rang und nur mit eigenem Link; leere Felder
     werden aufgefüllt; redaktion_felder, beschreibung_quelle, Slug, abgleich_* und eine vorhandene ort_id bleiben;
     ticket_url und quellen werden nie geleert.

Ohne --schreiben nur Probelauf (Bericht + Plan-Datei). Mit --schreiben werden vorher die bisherigen Werte aller
geänderten Felder gesichert (data/quellen_nachziehen/sicherung_<Zeit>.json). Es wird nichts gelöscht und nichts neu
angelegt. Rückweg: --zuruecksetzen <Sicherung> spielt die gesicherten Werte zurück.

Aufruf:
    python -m pipeline.quellen_nachziehen                              # scrapen + Probelauf
    python -m pipeline.quellen_nachziehen --zwischenspeicher           # ohne neues Scrapen
    python -m pipeline.quellen_nachziehen --zwischenspeicher --schreiben
    python -m pipeline.quellen_nachziehen --zuruecksetzen data/quellen_nachziehen/sicherung_….json
"""
import argparse
import asyncio
import json
import logging
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from database.client import (
    _TICKET_SPALTE,
    _abgleich_spalten,
    _anreicherungs_update_bauen,
    _quellen_spalte_pruefen,
    _ticket_spalte_pruefen,
    _uhrzeit_hhmm,
    get_supabase_client,
)
from pipeline.deduplication import (
    KATEGORIE_FEST_FELD,
    _normalisiere_schluessel,
    aehnliches_event,
    deduplizieren,
    preis_normalisieren,
)
from pipeline.quellen_rang import HAUS, QUELLEN_FELD, quellen_rang, rang_gespeichert
from pipeline.slug_generator import slug_fuer_event

logger = logging.getLogger("quellen_nachziehen")

ORDNER = Path("data/quellen_nachziehen")
EVENTS_DATEI = ORDNER / "events.json"
PLAN_DATEI = ORDNER / "plan.json"
SEITE = 1000


def bestand_laden(db) -> list[dict]:
    """Alle künftigen Events, deren gespeicherte Quelle nicht das Haus selbst ist (Rang ≥ 2), seitenweise."""
    eintraege: list[dict] = []
    heute = date.today().isoformat()
    start = 0
    while True:
        antwort = (
            db.table("events")
            .select("id,titel,ort,datum,slug," + _abgleich_spalten())
            .gte("datum", heute)
            .order("id")
            .range(start, start + SEITE - 1)
            .execute()
        )
        seite = antwort.data or []
        eintraege.extend(z for z in seite if rang_gespeichert(z.get("quelle_name"), z.get("quelle_url")) > HAUS)
        if len(seite) < SEITE:
            return eintraege
        start += SEITE


async def quellen_scrapen() -> list[dict]:
    """
    Alle Scraper aus main.QUELLEN außer Rausgegangen und den im Admin-Bereich abgeschalteten – über den Lauf-Report,
    damit jedes Event wie im täglichen Lauf `_scraper` und `_tier` trägt (daraus kommt der Rang).
    """
    from main import QUELLEN
    from pipeline.lauf_report import LaufReport
    from pipeline.quellen import quellen_abgeschaltet

    abgeschaltet = quellen_abgeschaltet()
    report = LaufReport()  # ohne starten(): schreibt nichts in scraper_laeufe
    alle: list[dict] = []
    for name, tier, funktion in QUELLEN:
        if name == "Rausgegangen" or name in abgeschaltet:
            logger.info("%s: übersprungen", name)
            continue
        alle.extend(await report.scraper_ausfuehren(name, tier, funktion))
    return alle


def _passt(eintrag: dict, event: dict) -> bool:
    """Gleiches Event? Titel+Ort oder Slug gleich (Uhrzeit gleich oder fehlend) oder ähnlich (wie im Speichern)."""
    if event.get("datum") != eintrag.get("datum"):
        return False
    a, b = _uhrzeit_hhmm(eintrag.get("uhrzeit")), _uhrzeit_hhmm(event.get("uhrzeit"))
    zeit_ok = a is None or b is None or a == b
    if zeit_ok and _normalisiere_schluessel(eintrag.get("titel") or "", eintrag["datum"], eintrag.get("ort") or "") == \
            _normalisiere_schluessel(event.get("titel") or "", event["datum"], event.get("ort") or ""):
        return True
    slug = slug_fuer_event(event)
    basis = eintrag.get("slug") or ""
    if zeit_ok and slug and (basis == slug or (basis.startswith(slug + "-") and len(basis) - len(slug) <= 3)):
        return True
    return aehnliches_event(eintrag, event)


def _neu_aus_treffer(treffer: dict, mit_ticket: bool) -> dict:
    """Event-Dict wie in events_speichern: ohne „_“-Felder, Quellenliste als `quellen`, Preis vereinheitlicht."""
    neu = {k: v for k, v in treffer.items() if not k.startswith("_")}
    if treffer.get(QUELLEN_FELD):
        neu["quellen"] = treffer[QUELLEN_FELD]
    if not mit_ticket or not neu.get("ticket_url"):
        neu.pop("ticket_url", None)
    if neu.get("preis"):
        neu["preis"] = preis_normalisieren(neu["preis"])
    return neu


def plan_erstellen(eintraege: list[dict], events: list[dict], mit_ticket: bool = True) -> list[dict]:
    """Je gespeichertem Event (Rang ≥ 2) die Änderung aus dem passenden gescrapten Event mit dem besten Rang."""
    pro_datum: dict[str, list[dict]] = {}
    for e in events:
        if e.get("datum"):
            pro_datum.setdefault(e["datum"], []).append(e)

    plan = []
    for eintrag in eintraege:
        rang_alt = rang_gespeichert(eintrag.get("quelle_name"), eintrag.get("quelle_url"))
        kandidaten = [e for e in pro_datum.get(eintrag.get("datum"), []) if _passt(eintrag, e)]
        if not kandidaten:
            continue
        # Bester Rang zuerst, bei gleichem Rang der mit eigenem Link
        treffer = min(kandidaten, key=lambda e: (quellen_rang(e), not e.get("quelle_url")))
        rang_neu = quellen_rang(treffer)
        update = _anreicherungs_update_bauen(
            eintrag, _neu_aus_treffer(treffer, mit_ticket), bool(treffer.get(KATEGORIE_FEST_FELD)), rang_neu
        )
        # Sicherheitsnetz: nie etwas leeren (das Speichern schreibt nur belegte Werte – hier noch einmal geprüft)
        update = {k: v for k, v in update.items() if v not in (None, "", [])}
        if update:
            plan.append({
                "id": eintrag["id"], "slug": eintrag.get("slug"), "titel": eintrag.get("titel"),
                "datum": eintrag.get("datum"), "treffer_titel": treffer.get("titel"),
                "quelle_alt": eintrag.get("quelle_name"), "rang_alt": rang_alt,
                "quelle_treffer": treffer.get("_scraper") or treffer.get("quelle_name"), "rang_treffer": rang_neu,
                "vorher": {f: eintrag.get(f) for f in update}, "update": update,
            })
    return plan


def bericht(eintraege: list[dict], plan: list[dict]) -> str:
    """Zusammenfassung des Probelaufs als Text."""
    wechsel = [p for p in plan if "quelle_name" in p["update"]]
    zeilen = [
        f"Gespeicherte künftige Events mit Quelle Rang ≥ 2: {len(eintraege)}",
        "  je Rang: " + ", ".join(f"{r}: {n}" for r, n in sorted(Counter(
            rang_gespeichert(e.get("quelle_name"), e.get("quelle_url")) for e in eintraege).items())),
        f"Quellenwechsel: {len(wechsel)}",
        "  Rang alt → neu: " + ", ".join(f"{a}→{b}: {n}" for (a, b), n in sorted(Counter(
            (p["rang_alt"], p["rang_treffer"]) for p in wechsel).items())),
        "  neue Quellen: " + ", ".join(f"{q} {n}" for q, n in Counter(
            p["update"]["quelle_name"] for p in wechsel).most_common()),
        f"Einträge mit Änderungen insgesamt (auch nur Lücken gefüllt): {len(plan)}",
        "Geänderte Felder: " + ", ".join(f"{f} {n}" for f, n in Counter(f for p in plan for f in p["update"]).most_common()),
        "",
        "Beispiele (Quellenwechsel):",
    ]
    for p in wechsel[:20]:
        zeilen.append(f"  {p['datum']} {p['titel'][:42]!r} ≈ {p['treffer_titel'][:42]!r}: "
                      f"{p['quelle_alt']} (Rang {p['rang_alt']}) → {p['update']['quelle_name']} (Rang {p['rang_treffer']})")
    return "\n".join(zeilen)


def schreiben(db, plan: list[dict]) -> Path:
    """Sichert die bisherigen Werte und spielt die Änderungen ein."""
    sicherung = ORDNER / f"sicherung_{datetime.now():%Y%m%d_%H%M%S}.json"
    sicherung.write_text(json.dumps([{"id": p["id"], "vorher": p["vorher"]} for p in plan],
                                    ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"Sicherung: {sicherung}")
    ok = fehler = 0
    for p in plan:
        try:
            db.table("events").update(p["update"]).eq("id", p["id"]).execute()
            ok += 1
        except Exception as e:
            fehler += 1
            logger.error("Update für %s fehlgeschlagen: %s", p["id"], e)
    print(f"Geschrieben: {ok} | Fehler: {fehler}")
    return sicherung


def zuruecksetzen(db, datei: Path) -> None:
    """Spielt die Werte einer Sicherung zurück (Rückweg für --schreiben)."""
    eintraege = json.loads(datei.read_text(encoding="utf-8"))
    ok = fehler = 0
    for e in eintraege:
        try:
            db.table("events").update(e["vorher"]).eq("id", e["id"]).execute()
            ok += 1
        except Exception as fehler_text:
            fehler += 1
            logger.error("Zurücksetzen für %s fehlgeschlagen: %s", e["id"], fehler_text)
    print(f"Zurückgesetzt: {ok} | Fehler: {fehler}")


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Gespeicherte Events auf die Rangfolge der Quellen umhängen (N1)")
    parser.add_argument("--zwischenspeicher", action="store_true", help="gescrapte Events aus dem letzten Lauf nutzen")
    parser.add_argument("--schreiben", action="store_true", help="Änderungen wirklich in die Datenbank schreiben")
    parser.add_argument("--zuruecksetzen", type=Path, help="Sicherung zurückspielen und beenden")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ORDNER.mkdir(parents=True, exist_ok=True)
    db = get_supabase_client()

    if args.zuruecksetzen:
        zuruecksetzen(db, args.zuruecksetzen)
        return

    if args.zwischenspeicher:
        events = json.loads(EVENTS_DATEI.read_text(encoding="utf-8"))
    else:
        events = asyncio.run(quellen_scrapen())
        EVENTS_DATEI.write_text(json.dumps(events, ensure_ascii=False, default=str), encoding="utf-8")
    from pipeline.gebiet import gebiet_filtern
    events = deduplizieren(gebiet_filtern(events))

    _quellen_spalte_pruefen(db)
    mit_ticket = _ticket_spalte_pruefen(db)
    if not mit_ticket:
        logger.error("Spalte events.ticket_url fehlt – N1 läuft erst nach P1 (database/ticket_url_2026-11-24.sql)")
        return
    eintraege = bestand_laden(db)
    plan = plan_erstellen(eintraege, events, mit_ticket=_TICKET_SPALTE["da"])
    PLAN_DATEI.write_text(json.dumps(plan, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    text = bericht(eintraege, plan)
    print(text)
    (ORDNER / "bericht.txt").write_text(text, encoding="utf-8")

    if args.schreiben:
        schreiben(db, plan)
    else:
        print(f"\nProbelauf – nichts geschrieben. Plan: {PLAN_DATEI}")


if __name__ == "__main__":
    main()
