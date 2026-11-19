"""
ort_zuordnung.py – DiesDasDüsseldorf
Zuordnung Event → Ort (`events.ort_id`), Plan docs/plan-locations-2026-11-18.md, Abschnitt 3.4.

Eine Funktion für Pipeline (Schritt 1d in main.py) und Nachtrag (SQL-Datei für den Bestand), damit beide nie
verschieden zuordnen:

- Treffer: einheitlicher Ortsname (pipeline/ortsnamen.py) gleich einem Eintrag in `event_orte` einer AKTIVEN Zeile
  (`extras.club.event_orte` bei Clubs, `extras.spielstaette.event_orte` bei Spielstätten), bei Guides auch gleich
  `orte.name` – jeweils normalisiert.
- Mehrere Zeilen → keine ID (mehrdeutig). „nicht im …“ (nicht_im_ort) und EVENT_ORTE_AUSSCHLUSS ergeben nie einen
  Treffer. Ketten nur, wenn die Event-Adresse zur Adresse der Zeile passt.
- Automatische Läufe setzen oder ersetzen eine ort_id nur mit einem Treffer; sie schreiben nie NULL über einen
  vorhandenen Wert. Eine Zuordnung lösen geht nur über ausdrückliches SQL (Plan 3.4).

Aufruf im Repo-Stamm (nur lesend):
    python -m pipeline.ort_zuordnung --sql      → database/ort_id_nachtrag_<datum>.sql
    python -m pipeline.ort_zuordnung --pruefen  → Kennzahlen über den ganzen Bestand
"""
from __future__ import annotations

import argparse
import logging
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from pipeline.ortsnamen import einheitlicher_name

logger = logging.getLogger(__name__)

# Schreibweisen, die nie (wieder) zu einem Club gehören – auch wenn event_orte() sie im Kalender findet
# (Plan 3.4: „Eine Zuordnung lösen“). Club-Slug → {Schreibweise: Begründung}. Wird von clubs_profil.event_orte()
# und von ort_zuordnen() beachtet.
EVENT_ORTE_AUSSCHLUSS: dict[str, dict[str, str]] = {
    "koe-club-duesseldorf-friedrichstadt": {
        "Theater an der Kö": "Theater an der Kö ist ein eigenes Haus, kein Teil des Kö-Clubs (Plan 3.2, 19.11.2026)",
    },
}

# Ketten mit vielen Filialen und einer `orte`-Zeile: Zuordnung nur bei passender Adresse (Plan 3.2, 3.4)
KETTE = re.compile(r"^(starbucks|(caf[eé] )?extrablatt|alex)\b", re.I)

_NICHT_IM_AUSNAHME = re.compile(r"\b(sondern|aber|dafuer)\b")


def woerter(text: Optional[str]) -> list[str]:
    """Kleinbuchstaben, Umlaute ausgeschrieben, nur Buchstaben/Ziffern (gleich wie in clubs_profil)."""
    t = (text or "").lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.findall(r"[a-z0-9]+", t)


def nicht_im_ort(ort: Optional[str], hausnamen: Iterable[str]) -> bool:
    """
    „zakk – nicht im zakk“: findet ausdrücklich nicht in diesem Haus statt (Plan 3.4). Gemeinsame Regel für
    clubs_profil.event_orte() und ort_zuordnen(). `hausnamen` sind Wortfolgen des Hauses („zakk“, „pitcher“).
    „Pitcher, nicht im Freien“ und „nicht im Saal, sondern im Pitcher Club“ gehören zum Ort.
    """
    text = f" {' '.join(woerter(ort))} "
    for name in hausnamen:
        n = " ".join(woerter(name))
        if not n:
            continue
        m = re.search(rf" nicht im((?: \w+){{0,4}}) {re.escape(n)} ", text)
        if m and not _NICHT_IM_AUSNAHME.search(m.group(1)):
            return True
    return False


def ausgeschlossen(slug: Optional[str], ort: Optional[str]) -> bool:
    """Steht die Schreibweise in EVENT_ORTE_AUSSCHLUSS dieser Zeile?"""
    liste = EVENT_ORTE_AUSSCHLUSS.get(slug or "") or {}
    k = schluessel(ort)
    return any(schluessel(s) == k for s in liste)


def schluessel(name: Optional[str]) -> str:
    """Normalisierter Vergleichsschlüssel eines Ortsnamens (einheitlicher Name, ASCII, ohne Stadtnamen)."""
    t = einheitlicher_name(name) or (name or "")
    t = unicodedata.normalize("NFKC", t).lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"\b(duesseldorf|dusseldorf)\b", " ", t)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


_STRASSE_NR = re.compile(r"([a-zäöüß][a-zäöüß .\-]*?)\s*(\d+\s*[a-z]?)\b", re.I)


def _strasse_nr(adresse: Optional[str]) -> Optional[tuple[str, str]]:
    """Erste Straße mit Hausnummer, normalisiert („Schadowstraße 84“ → („schadowstr“, „84“))."""
    for m in _STRASSE_NR.finditer(adresse or ""):
        strasse = " ".join(woerter(m.group(1)))
        strasse = re.sub(r"(strasse|str)$", "str", strasse.replace(" ", ""))
        if len(strasse) >= 4 and not strasse.isdigit():
            return strasse, m.group(2).replace(" ", "").lower()
    return None


def adresse_passt(a: Optional[str], b: Optional[str]) -> bool:
    """Gleiche Straße und Hausnummer (für Ketten). Fehlt eine Seite, passt es nicht."""
    x, y = _strasse_nr(a), _strasse_nr(b)
    return bool(x and y and x == y)


@dataclass
class OrteIndex:
    """Aktive `orte`-Zeilen, vorbereitet für die Zuordnung."""
    namen: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))  # Schlüssel → Zeilen-IDs
    zeilen: dict[str, dict] = field(default_factory=dict)                            # ID → Zeile
    haus: dict[str, str] = field(default_factory=dict)                               # ID → Haus-ID
    kette: set[str] = field(default_factory=set)                                     # IDs von Ketten

    @classmethod
    def aus_zeilen(cls, zeilen: Iterable[dict]) -> "OrteIndex":
        idx = cls()
        for z in zeilen:
            if not z.get("aktiv") or not z.get("id"):
                continue  # inaktive Zeilen werden erkannt, aber nie zugeordnet
            idx.zeilen[z["id"]] = z
            idx.haus[z["id"]] = z.get("parent_id") or z["id"]
            if KETTE.search(z.get("name") or ""):
                idx.kette.add(z["id"])
            extras = z.get("extras") or {}
            schreibweisen: list[str] = []
            if z.get("typ") != "spielstaette":
                schreibweisen.append(z.get("name") or "")
            for profil in (extras.get("club"), extras.get("spielstaette")):
                if isinstance(profil, dict):
                    schreibweisen.extend(profil.get("event_orte") or [])
            for s in schreibweisen:
                if not s or ausgeschlossen(z.get("slug"), s):
                    continue
                k = schluessel(s)
                if k and z["id"] not in idx.namen[k]:
                    idx.namen[k].append(z["id"])
        return idx


def ort_zuordnen(event: dict, index: OrteIndex) -> tuple[Optional[str], str]:
    """
    ID der passenden Zeile und Status: „treffer“, „kein“ oder „mehrdeutig“.
    """
    ort = event.get("ort")
    k = schluessel(ort)
    if not k:
        return None, "kein"
    kandidaten = []
    for zid in index.namen.get(k, []):
        z = index.zeilen[zid]
        if nicht_im_ort(ort, [z.get("name") or "", *(woerter_kern(z.get("name")))]):
            continue
        if zid in index.kette and not adresse_passt(event.get("adresse"), z.get("adresse")):
            continue
        kandidaten.append(zid)
    # Saal vor Haus: steht „zakk – Halle“ im event_orte des Clubs und des Saals, gewinnt der Saal (Plan 3.4 „Säle“)
    if len(kandidaten) > 1:
        kinder = [z for z in kandidaten if index.haus[z] != z and index.haus[z] in kandidaten]
        if len(kinder) == 1 and all(z == kinder[0] or z == index.haus[kinder[0]] for z in kandidaten):
            kandidaten = kinder
    if len(kandidaten) == 1:
        return kandidaten[0], "treffer"
    return None, ("mehrdeutig" if kandidaten else "kein")


def woerter_kern(name: Optional[str]) -> list[str]:
    """Erstes Wort des Namens als zusätzlicher Hausname für nicht_im_ort („zakk“ aus „zakk Flingern“)."""
    w = woerter(name)
    return [w[0]] if w and len(w[0]) >= 3 else []


# ── Pipeline ────────────────────────────────────────────────────────────────────────────────────────────────────

_INDEX: Optional[OrteIndex] = None


def aktueller_index() -> Optional[OrteIndex]:
    """Index des laufenden Pipeline-Laufs (None, wenn Schritt 1d nicht lief – dann gilt der Namensvergleich)."""
    return _INDEX


def _seitenweise(db, tabelle: str, spalten: str, filter_fn=None) -> list[dict]:
    zeilen, start = [], 0
    while True:
        q = db.table(tabelle).select(spalten)
        if filter_fn:
            q = filter_fn(q)
        teil = q.range(start, start + 999).execute().data or []
        zeilen.extend(teil)
        if len(teil) < 1000:
            return zeilen
        start += 1000


def index_laden(db) -> OrteIndex:
    """Alle `orte`-Zeilen (Service-Schlüssel, seitenweise) – einmal je Lauf."""
    global _INDEX
    zeilen = _seitenweise(db, "orte", "id, name, slug, typ, aktiv, parent_id, adresse, "
                                      "extras->club, extras->spielstaette")
    for z in zeilen:  # extras->club kommt als eigenes Feld zurück
        z["extras"] = {"club": z.pop("club", None), "spielstaette": z.pop("spielstaette", None)}
    _INDEX = OrteIndex.aus_zeilen(zeilen)
    logger.info("Ortszuordnung: %d aktive Orte, %d Schreibweisen", len(_INDEX.zeilen), len(_INDEX.namen))
    return _INDEX


def annotieren(event: dict, index: Optional[OrteIndex] = None) -> dict:
    """Interne Felder für die Dubletten-Regel (_haus_id, _kette) aus einer vorhandenen ort_id; werden nicht gespeichert."""
    index = index or _INDEX
    oid = event.get("ort_id")
    if index and oid and oid in index.haus:
        event["_haus_id"] = index.haus[oid]
        event["_kette"] = oid in index.kette
    return event


def zuordnen_alle(events: list[dict], index: OrteIndex) -> Counter:
    """Schritt 1d: setzt ort_id bei Treffern (nur neue Events des Laufs, nie NULL über einen Wert)."""
    stand: Counter = Counter()
    for e in events:
        oid, status = ort_zuordnen(e, index)
        stand[status] += 1
        if oid:
            e["ort_id"] = oid
        annotieren(e, index)
    logger.info("Ortszuordnung: %d Treffer, %d ohne Ort, %d mehrdeutig", stand["treffer"], stand["kein"],
                stand["mehrdeutig"])
    return stand


def bestand_pruefen(db, index: OrteIndex) -> Counter:
    """
    Kennzahlen über den GANZEN Bestand (Plan 3.4): gespeicherte ort_id ohne Treffer bzw. mehrdeutig. Ändert nichts.
    """
    stand: Counter = Counter()
    for e in _seitenweise(db, "events", "id, ort, adresse, ort_id", lambda q: q.not_.is_("ort_id", "null")):
        oid, status = ort_zuordnen(e, index)
        if status == "kein":
            stand["ort_id_ohne_treffer"] += 1
            logger.warning("ort_id ohne Treffer: Event %s „%s“ → %s", e["id"], e.get("ort"), e["ort_id"])
        elif status == "mehrdeutig":
            stand["ort_id_mehrdeutig"] += 1
            logger.warning("ort_id mehrdeutig: Event %s „%s“", e["id"], e.get("ort"))
        elif oid != e["ort_id"]:
            stand["ort_id_abweichend"] += 1  # der nächste Nachtrag ersetzt sie (Treffer)
    return stand


# ── Nachtrag ────────────────────────────────────────────────────────────────────────────────────────────────────

def nachtrag_aenderungen(events: list[dict], index: OrteIndex) -> dict[str, list[str]]:
    """Ziel-ID → Event-IDs, deren berechneter Treffer vom gespeicherten Wert abweicht (nie NULL)."""
    ziel: dict[str, list[str]] = defaultdict(list)
    for e in events:
        oid, _ = ort_zuordnen(e, index)
        if oid and oid != e.get("ort_id"):
            ziel[oid].append(e["id"])
    return ziel


def nachtrag_sql_text(aenderungen: dict[str, list[str]], index: OrteIndex) -> str:
    zeilen = [
        "-- Nachtrag events.ort_id für den Bestand (Plan docs/plan-locations-2026-11-18.md, 3.4, Deploy-Punkt 3)",
        f"-- Erzeugt am {date.today().isoformat()} von `python -m pipeline.ort_zuordnung --sql` (nur lesend).",
        "-- Wiederholbar: setzt nur Treffer, die vom gespeicherten Wert abweichen; schreibt nie NULL.",
        "-- Ein zweiter Lauf des Skripts nach dem Ausführen erzeugt keine Änderung mehr.",
        "",
    ]
    for oid, ids in sorted(aenderungen.items(), key=lambda x: -len(x[1])):
        z = index.zeilen[oid]
        zeilen.append(f"-- {z.get('name')} ({z.get('slug')}, {z.get('typ')}): {len(ids)} Events")
        for i in range(0, len(ids), 500):
            teil = ", ".join(f"'{x}'" for x in ids[i:i + 500])
            zeilen.append(f"UPDATE public.events SET ort_id = '{oid}' WHERE id IN ({teil});")
    zeilen += ["", "-- Kontrolle: Events mit ort_id je Typ des Orts",
               "SELECT o.typ, count(*) FROM public.events e JOIN public.orte o ON o.id = e.ort_id GROUP BY o.typ "
               "ORDER BY 2 DESC;"]
    return "\n".join(zeilen) + "\n"


def nachtrag_sql(pfad: Path) -> int:
    from database.client import get_supabase_client

    db = get_supabase_client()
    index = index_laden(db)
    events = _seitenweise(db, "events", "id, ort, adresse, ort_id")
    aenderungen = nachtrag_aenderungen(events, index)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(nachtrag_sql_text(aenderungen, index), encoding="utf-8")
    anzahl = sum(len(v) for v in aenderungen.values())
    logger.info("Nachtrag: %d Events an %d Orten → %s", anzahl, len(aenderungen), pfad)
    return anzahl


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
    except ImportError:
        pass
    parser = argparse.ArgumentParser(description="Zuordnung Event → Ort (nur lesend)")
    parser.add_argument("--sql", action="store_true", help="Nachtrag als SQL-Datei schreiben")
    parser.add_argument("--pruefen", action="store_true", help="Kennzahlen über den ganzen Bestand")
    parser.add_argument("--ausgabe", default=f"database/ort_id_nachtrag_{date.today().isoformat()}.sql")
    args = parser.parse_args()
    if args.sql:
        nachtrag_sql(Path(args.ausgabe))
    if args.pruefen:
        from database.client import get_supabase_client
        db = get_supabase_client()
        print(dict(bestand_pruefen(db, index_laden(db))))


if __name__ == "__main__":
    main()
