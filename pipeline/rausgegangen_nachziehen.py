"""
Einmaliges Nachziehen der Vorrang-Regel für bereits gespeicherte Rausgegangen-Events.

Seit der Vorrang-Regel wird ein Event, das neben Rausgegangen auch eine andere Quelle liefert,
unter dieser anderen Quelle geführt (Link „Zum Termin“, Bild, Beschreibung, Preis, Adresse);
Rausgegangen füllt nur noch Lücken. Dieses Skript wendet die Regel auf die schon gespeicherten
künftigen Rausgegangen-Events an:

  1. Alle Quellen außer Rausgegangen einmal scrapen (Zwischenspeicher in data/rausgegangen_nachziehen/)
  2. Je Rausgegangen-Eintrag dasselbe Event aus den anderen Quellen suchen
     (gleicher Titel+Ort, gleicher Slug oder ähnliches Event – jeweils gleiche bzw. fehlende Uhrzeit)
  3. Änderungen wie beim täglichen Speichern bauen (_anreicherungs_update_bauen):
     Quelle wechselt, leere Felder werden weiterhin aufgefüllt, der Slug bleibt.

Ohne --schreiben nur Probelauf (Bericht + Plan-Datei). Mit --schreiben werden die bisherigen
Werte der geänderten Felder vorher gesichert. Es wird nichts gelöscht und nichts neu angelegt.

Aufruf:
    python -m pipeline.rausgegangen_nachziehen              # scrapen + Probelauf
    python -m pipeline.rausgegangen_nachziehen --zwischenspeicher   # ohne neues Scrapen
    python -m pipeline.rausgegangen_nachziehen --zwischenspeicher --schreiben
"""
import argparse
import asyncio
import inspect
import json
import logging
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from database.client import (
    _ABGLEICH_SPALTEN,
    _anreicherungs_update_bauen,
    _uhrzeit_hhmm,
    get_supabase_client,
)
from pipeline.deduplication import (
    KATEGORIE_FEST_FELD,
    _normalisiere_schluessel,
    aehnliches_event,
    deduplizieren,
    ist_rausgegangen,
    preis_normalisieren,
)
from pipeline.slug_generator import slug_fuer_event

logger = logging.getLogger("rausgegangen_nachziehen")

ORDNER = Path("data/rausgegangen_nachziehen")
EVENTS_DATEI = ORDNER / "events_andere_quellen.json"
PLAN_DATEI = ORDNER / "plan.json"


def _rausgegangen_eintraege(db) -> list[dict]:
    """Alle künftigen Events, deren Quelle Rausgegangen ist (seitenweise geladen)."""
    eintraege: list[dict] = []
    heute = date.today().isoformat()
    start = 0
    while True:
        antwort = (
            db.table("events")
            .select("id,titel,ort,datum,slug," + _ABGLEICH_SPALTEN)
            .gte("datum", heute)
            .or_("quelle_name.ilike.*rausgegangen*,quelle_url.ilike.*rausgegangen.de*")
            .order("id")
            .range(start, start + 999)
            .execute()
        )
        seite = antwort.data or []
        eintraege.extend(seite)
        if len(seite) < 1000:
            return eintraege
        start += 1000


async def _andere_quellen_scrapen() -> list[dict]:
    """Führt alle Scraper aus main.QUELLEN außer Rausgegangen aus (jeder einzeln abgesichert)."""
    from main import QUELLEN

    alle: list[dict] = []
    for name, _tier, funktion in QUELLEN:
        if name == "Rausgegangen":
            continue
        try:
            if inspect.iscoroutinefunction(funktion):
                events = await funktion()
            else:
                events = await asyncio.to_thread(funktion)
            events = list(events or [])
            logger.info("%s: %d Events", name, len(events))
            alle.extend(events)
        except Exception as e:
            logger.error("%s abgestürzt: %s", name, e)
    return alle


def _passt(eintrag: dict, event: dict) -> bool:
    """Gleiches Event? Titel+Ort oder Slug gleich (Uhrzeit gleich oder fehlend) oder ähnlich."""
    if event.get("datum") != eintrag.get("datum"):
        return False
    a, b = _uhrzeit_hhmm(eintrag.get("uhrzeit")), _uhrzeit_hhmm(event.get("uhrzeit"))
    zeit_ok = a is None or b is None or a == b
    if zeit_ok and _normalisiere_schluessel(eintrag.get("titel") or "", eintrag["datum"], eintrag.get("ort") or "") == \
            _normalisiere_schluessel(event.get("titel") or "", event["datum"], event.get("ort") or ""):
        return True
    slug = slug_fuer_event(event)
    basis = (eintrag.get("slug") or "")
    if zeit_ok and slug and (basis == slug or (basis.startswith(slug + "-") and len(basis) - len(slug) <= 3)):
        return True
    return aehnliches_event(eintrag, event)


def plan_erstellen(eintraege: list[dict], events: list[dict]) -> list[dict]:
    """Je Rausgegangen-Eintrag die Änderung aus dem passenden Event einer anderen Quelle."""
    pro_datum: dict[str, list[dict]] = {}
    for e in events:
        if e.get("datum") and not ist_rausgegangen(e):
            pro_datum.setdefault(e["datum"], []).append(e)

    plan = []
    for eintrag in eintraege:
        treffer = next((e for e in pro_datum.get(eintrag.get("datum"), []) if _passt(eintrag, e)), None)
        if treffer is None:
            continue
        neu = {k: v for k, v in treffer.items() if not k.startswith("_")}
        if neu.get("preis"):
            neu["preis"] = preis_normalisieren(neu["preis"])
        update = _anreicherungs_update_bauen(eintrag, neu, bool(treffer.get(KATEGORIE_FEST_FELD)))
        if update:
            plan.append({
                "id": eintrag["id"], "slug": eintrag.get("slug"), "titel": eintrag.get("titel"),
                "datum": eintrag.get("datum"), "treffer_titel": treffer.get("titel"),
                "vorher": {f: eintrag.get(f) for f in update}, "update": update,
            })
    return plan


def bericht(eintraege: list[dict], plan: list[dict]) -> None:
    """Zusammenfassung des Probelaufs auf der Konsole."""
    wechsel = [p for p in plan if "quelle_name" in p["update"]]
    felder = Counter(f for p in plan for f in p["update"])
    quellen = Counter(p["update"]["quelle_name"] for p in wechsel)
    print(f"Rausgegangen-Einträge (ab heute): {len(eintraege)}")
    print(f"Davon mit anderer Quelle gefunden: {len(wechsel)} (Quellwechsel)")
    print(f"Einträge mit Änderungen insgesamt: {len(plan)}")
    print("Geänderte Felder:", dict(felder))
    print("Neue Quellen:", dict(quellen.most_common()))
    print("\nBeispiele:")
    for p in plan[:15]:
        u = p["update"]
        print(f"  {p['datum']} {p['titel'][:45]!r} ≈ {p['treffer_titel'][:45]!r} → {u.get('quelle_name', '(bleibt)')}"
              f" | Felder: {', '.join(u)}")


def schreiben(db, plan: list[dict]) -> None:
    """Sichert die bisherigen Werte und spielt die Änderungen ein."""
    sicherung = ORDNER / f"sicherung_{datetime.now():%Y%m%d_%H%M%S}.json"
    sicherung.write_text(json.dumps([{"id": p["id"], "vorher": p["vorher"]} for p in plan],
                                    ensure_ascii=False, indent=1), encoding="utf-8")
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Vorrang-Regel auf gespeicherte Rausgegangen-Events anwenden")
    parser.add_argument("--zwischenspeicher", action="store_true", help="gescrapte Events aus dem letzten Lauf nutzen")
    parser.add_argument("--schreiben", action="store_true", help="Änderungen wirklich in die Datenbank schreiben")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ORDNER.mkdir(parents=True, exist_ok=True)

    if args.zwischenspeicher:
        events = json.loads(EVENTS_DATEI.read_text(encoding="utf-8"))
    else:
        events = asyncio.run(_andere_quellen_scrapen())
        EVENTS_DATEI.write_text(json.dumps(events, ensure_ascii=False, default=str), encoding="utf-8")
    events = deduplizieren(events)

    db = get_supabase_client()
    eintraege = _rausgegangen_eintraege(db)
    plan = plan_erstellen(eintraege, events)
    PLAN_DATEI.write_text(json.dumps(plan, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    bericht(eintraege, plan)

    if args.schreiben:
        schreiben(db, plan)
    else:
        print(f"\nProbelauf – nichts geschrieben. Plan: {PLAN_DATEI}")


if __name__ == "__main__":
    main()
