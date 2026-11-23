"""
vorschlaege.py – DiesDasDüsseldorf
Vorschläge statt SQL-Dateien (Plan docs/plan-admin-dashboard-2026-11-23.md, 3.5, Stufe 1d).

Die Skripte für Dubletten und Gebiet schreiben ihre Treffer in public.admin_vorschlaege. Im Admin-Bereich nimmt die
Redaktion sie an oder lehnt sie ab; erst die Annahme ändert Daten (SECURITY-DEFINER-Funktionen aus
database/admin_events_2026-11-23.sql). Doppelte Vorschläge verhindert der Schlüssel (art, schluessel): Die Pipeline
schreibt mit ON CONFLICT DO NOTHING, abgelehnte bleiben so liegen und kommen nicht wieder.

Stufe 3c (Orte): drei weitere Arten statt der SQL-Dateien von pipeline/ortsnamen.py --sql, pipeline/ort_zuordnung.py
--sql und pipeline/adressen_ergaenzen.py --sql: „ortsname“ (Schreibweise vereinheitlichen, je alter → neuer Name),
„ort_id“ (Zuordnung Event → Ort, je Event), „adresse“ (Adresse aus eigenen Daten, je Event). Events mit dem Feld in
redaktion_felder bekommen keinen Vorschlag (Plan 4.4, Stufe 3); die Annahme prüft das noch einmal
(database/admin_vorschlaege_orte_2026-11-23.sql).

Aufruf von Hand:   python -m pipeline.vorschlaege            (alle Arten)
Im Lauf:           main.py, Schritt 3e (vorschlaege_erzeugen)
"""
import logging
import re
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

STAPEL = 500


def dubletten_vorschlaege(events: list[dict], original: dict[str, dict], lauf_id: Optional[str] = None) -> list[dict]:
    """Ein Vorschlag je Paar (behalten, dublette) – gleiche Regeln wie pipeline/dubletten_sql.py."""
    from pipeline.deduplication import TITEL_STATUS_FELD, _uhrzeit, ist_aggregator
    from pipeline.dubletten_sql import paare_finden, pfad

    paare, _ = paare_finden(events)
    zeilen = []
    for behalten, dublette in paare:
        if not (behalten.get("slug") and dublette.get("slug")):
            continue
        ub, ud = _uhrzeit(behalten), _uhrzeit(dublette)
        uhrzeit_uebernehmen = bool((not ub and ud) or (ub and ud and ub != ud and ist_aggregator(behalten) and not ist_aggregator(dublette)))
        absage = bool(dublette.get("abgesagt") or dublette.get(TITEL_STATUS_FELD) == "abgesagt")
        tb, td = original[behalten["id"]]["titel"], original[dublette["id"]]["titel"]
        zeilen.append({
            "art": "dublette",
            "ziel_tabelle": "events",
            "ziel_id": dublette["id"],
            "schluessel": f"{behalten['id']}:{dublette['id']}",
            "vorschlag": {
                "behalten": behalten["id"],
                "dublette": dublette["id"],
                "uhrzeit_uebernehmen": uhrzeit_uebernehmen,
                "absage": absage,
                "ziel": pfad(behalten),
                "datum": behalten.get("datum"),
                "behalten_titel": tb,
                "dublette_titel": td,
                "behalten_quelle": behalten.get("quelle_name"),
                "dublette_quelle": dublette.get("quelle_name"),
                "behalten_uhrzeit": ub,
                "dublette_uhrzeit": ud,
                "ort": behalten.get("ort"),
            },
            "begruendung": f"Gleicher Tag und Ort, fast gleicher Titel: „{td[:80]}“ ({dublette.get('quelle_name')}) "
                           f"ist dasselbe wie „{tb[:80]}“ ({behalten.get('quelle_name')}).",
            "quelle_lauf": lauf_id,
        })
    return zeilen


def gebiet_vorschlaege(events: list[dict], lauf_id: Optional[str] = None) -> list[dict]:
    """Ein Vorschlag je Event außerhalb von Düsseldorf, Neuss und Ratingen (Regeln aus pipeline/gebiet.py)."""
    from pipeline.gebiet import grund_ausserhalb

    zeilen = []
    for e in events:
        grund = grund_ausserhalb(e)
        if not grund:
            continue
        zeilen.append({
            "art": "gebiet",
            "ziel_tabelle": "events",
            "ziel_id": e["id"],
            "schluessel": e["id"],
            "vorschlag": {
                "event": e["id"],
                "titel": e.get("titel"),
                "datum": e.get("datum"),
                "ort": e.get("ort"),
                "adresse": e.get("adresse"),
                "quelle": e.get("quelle_name"),
                "grund": grund,
            },
            "begruendung": f"Außerhalb des Gebiets ({grund}).",
            "quelle_lauf": lauf_id,
        })
    return zeilen


def _geschuetzt(e: dict, feld: str) -> bool:
    return feld in (e.get("redaktion_felder") or [])


def ortsname_vorschlaege(events: list[dict], reihen: list[dict], lauf_id: Optional[str] = None) -> list[dict]:
    """
    Ein Vorschlag je alter → neuer Ortsname (Regeln wie pipeline/ortsnamen.py sql_erzeugen): Events mit Eintrag „ort“
    in redaktion_felder bleiben, ebenso solche, die sonst mit einem anderen Termin zusammenfielen.

    Reihen (Cursor-Prüfung 3c, Befund 2): Jede Reihe mit der alten Schreibweise bekommt den neuen Ort nur zusammen mit
    dem passenden Schlüssel „titel|ort“ (vorschlag.reihen: [{id, schluessel}], schluessel None = bleibt gleich).
    Reihen mit einem geschützten Event bleiben ganz beim alten Namen. Wäre ein neuer Schlüssel schon vergeben oder
    doppelt, entfällt der Vorschlag für diesen Namen (Log).
    Der Schlüssel des Vorschlags ist hier noch „alt→neu“; ortsname_schreiben hängt nach einer Annahme „#2“ usw. an.
    """
    from pipeline.ortsnamen import umbenennungen
    from pipeline.reihen_zuordnen import reihen_schluessel

    zuweisung, _ = umbenennungen(events)
    nach_id = {e["id"]: e for e in events}
    gruppen: dict[tuple[str, str], list[str]] = {}
    for eid, neu in zuweisung.items():
        e = nach_id[eid]
        if _geschuetzt(e, "ort"):
            continue
        gruppen.setdefault((e["ort"], neu), []).append(eid)
    geschuetzte_reihen = {e["reihe_id"] for e in events if e.get("reihe_id") and _geschuetzt(e, "ort")}
    vorhanden = {r["schluessel"] for r in reihen}
    zeilen = []
    for (alt, neu), ids in sorted(gruppen.items()):
        reihen_aenderung: list[dict] = []
        for r in sorted((r for r in reihen if r.get("ort") == alt and r["id"] not in geschuetzte_reihen), key=lambda r: r["id"]):
            neu_k = reihen_schluessel(r.get("titel") or "", neu)
            reihen_aenderung.append({"id": r["id"], "schluessel": neu_k if neu_k and neu_k != r.get("schluessel") else None})
        neue_k = [x["schluessel"] for x in reihen_aenderung if x["schluessel"]]
        if any(k in vorhanden for k in neue_k) or len(set(neue_k)) < len(neue_k):
            logger.warning("Ortsname „%s“ → „%s“: Reihen-Schlüssel schon vergeben – kein Vorschlag, bitte klären", alt, neu)
            continue
        zeilen.append({
            "art": "ortsname",
            "ziel_tabelle": "events",
            "ziel_id": None,
            "schluessel": f"{alt}→{neu}"[:290],
            "vorschlag": {"alt": alt, "neu": neu, "events": sorted(ids), "reihen": reihen_aenderung},
            "begruendung": f"Schreibweise vereinheitlichen: „{alt[:80]}“ → „{neu[:80]}“ ({len(ids)} Events, Liste in "
                           f"pipeline/ortsnamen.py).",
            "quelle_lauf": lauf_id,
        })
    return zeilen


def ortsname_plan(zeilen: list[dict], bestehend: list[dict]) -> tuple[list[dict], list[tuple[str, dict, str]]]:
    """
    Wie die Ortsnamen-Vorschläge in die Tabelle kommen (rein, testbar; Cursor-Prüfung 3c, Befund 1):
    - schon ein OFFENER Vorschlag für alt→neu → dessen Events und Reihen werden aktualisiert (neue Events kommen dazu);
    - einmal ABGELEHNT → nichts (die Ablehnung gilt für die Schreibweise);
    - nur ANGENOMMENE, aber noch Events mit alter Schreibweise → neuer Vorschlag „alt→neu#2“, „#3“ …;
    - sonst neu mit „alt→neu“.
    bestehend: Zeilen {id, schluessel, status} der Art ortsname. Rückgabe: (neu anlegen, [(id, vorschlag, begründung)]).
    """
    nach_basis: dict[str, list[dict]] = {}
    for b in bestehend:
        nach_basis.setdefault(re.sub(r"#\d+$", "", b["schluessel"]), []).append(b)
    anlegen, aktualisieren = [], []
    for z in zeilen:
        vorher = nach_basis.get(z["schluessel"], [])
        offen = [b for b in vorher if b["status"] == "offen"]
        if any(b["status"] == "abgelehnt" for b in vorher):
            continue
        if offen:
            aktualisieren.append((offen[0]["id"], z["vorschlag"], z["begruendung"]))
        elif vorher:
            anlegen.append({**z, "schluessel": f"{z['schluessel']}#{len(vorher) + 1}"})
        else:
            anlegen.append(z)
    return anlegen, aktualisieren


def ortsname_schreiben(db, zeilen: list[dict]) -> int:
    """Ortsnamen-Vorschläge anlegen bzw. offene aktualisieren (ortsname_plan)."""
    bestehend = _seiten(db, "admin_vorschlaege", "id,schluessel,status", lambda q: q.eq("art", "ortsname"))
    anlegen, aktualisieren = ortsname_plan(zeilen, bestehend)
    vorschlaege_schreiben(db, anlegen)
    for vid, vorschlag, begruendung in aktualisieren:
        db.table("admin_vorschlaege").update({"vorschlag": vorschlag, "begruendung": begruendung}) \
            .eq("id", vid).eq("status", "offen").execute()
    return len(anlegen) + len(aktualisieren)


def ort_id_vorschlaege(events: list[dict], index, lauf_id: Optional[str] = None) -> list[dict]:
    """Ein Vorschlag je Event, dessen berechnete Ortszuordnung vom gespeicherten Wert abweicht (nie NULL)."""
    from pipeline.ort_zuordnung import ort_zuordnen

    zeilen = []
    for e in events:
        if _geschuetzt(e, "ort_id"):
            continue
        oid, _ = ort_zuordnen(e, index)
        if not oid or oid == e.get("ort_id"):
            continue
        z = index.zeilen.get(oid) or {}
        zeilen.append({
            "art": "ort_id",
            "ziel_tabelle": "events",
            "ziel_id": e["id"],
            "schluessel": f"{e['id']}:{oid}",
            "vorschlag": {"event": e["id"], "ort_id": oid, "ort_name": z.get("name"), "ort_slug": z.get("slug"),
                          "ort_typ": z.get("typ"), "bisher": e.get("ort_id"), "titel": e.get("titel"),
                          "datum": e.get("datum"), "ort": e.get("ort")},
            "begruendung": f"„{(e.get('ort') or '')[:80]}“ gehört zu {z.get('name')} ({z.get('typ')})"
                           + (" – ersetzt eine andere Zuordnung" if e.get("ort_id") else "") + ".",
            "quelle_lauf": lauf_id,
        })
    return zeilen


def adresse_vorschlaege(events: list[dict], lauf_id: Optional[str] = None) -> list[dict]:
    """Ein Vorschlag je Event, das in adressen_ergaenzen eine Adresse bekommen hat (events sind schon ergänzt)."""
    from pipeline.stadtteil_mapper import stadtteil_ermitteln

    zeilen = []
    for e in events:
        if not e.get("adresse") or _geschuetzt(e, "adresse"):
            continue
        stadtteil = None
        if not e.get("stadtteil") and not _geschuetzt(e, "stadtteil"):
            stadtteil = stadtteil_ermitteln(e.get("ort") or "", e["adresse"], e.get("quelle_name"))
        zeilen.append({
            "art": "adresse",
            "ziel_tabelle": "events",
            "ziel_id": e["id"],
            "schluessel": e["id"],
            "vorschlag": {"event": e["id"], "adresse": e["adresse"], "stadtteil": stadtteil, "titel": e.get("titel"),
                          "datum": e.get("datum"), "ort": e.get("ort")},
            "begruendung": f"Adresse aus eigenen Daten für „{(e.get('ort') or '')[:80]}“"
                           + (f", Stadtteil {stadtteil}" if stadtteil else "") + ".",
            "quelle_lauf": lauf_id,
        })
    return zeilen


def _seiten(db, tabelle: str, spalten: str, filter_fn=None) -> list[dict]:
    """Seitenweise laden (Supabase liefert höchstens 1.000 Zeilen pro Abfrage)."""
    zeilen, start = [], 0
    while True:
        q = db.table(tabelle).select(spalten)
        if filter_fn:
            q = filter_fn(q)
        teil = q.order("id").range(start, start + 999).execute().data or []
        zeilen.extend(teil)
        if len(teil) < 1000:
            return zeilen
        start += 1000


def _orte_vorschlaege(db, lauf_id: Optional[str]) -> dict[str, int]:
    """Stufe 3c: Ortsnamen, Ortszuordnung, Adressen – jede Art für sich, ein Fehler bricht die anderen nicht ab."""
    ergebnis = {"ortsname": 0, "ort_id": 0, "adresse": 0}
    heute = date.today().isoformat()
    try:
        events = _seiten(db, "events", "id,titel,datum,uhrzeit,ort,reihe_id,abgelehnt,redaktion_felder")
        reihen = _seiten(db, "reihen", "id,schluessel,ort,titel")
        ergebnis["ortsname"] = ortsname_schreiben(db, ortsname_vorschlaege(events, reihen, lauf_id))
    except Exception as e:
        logger.error("Ortsnamen-Vorschläge nicht erzeugt: %s", e)
    try:
        from pipeline.ort_zuordnung import index_laden

        index = index_laden(db)
        events = _seiten(db, "events", "id,titel,datum,ort,adresse,ort_id,redaktion_felder",
                         lambda q: q.gte("datum", heute).eq("abgelehnt", False))
        ergebnis["ort_id"] = vorschlaege_schreiben(db, ort_id_vorschlaege(events, index, lauf_id))
    except Exception as e:
        logger.error("Ortszuordnungs-Vorschläge nicht erzeugt: %s", e)
    try:
        from pipeline.adressen_ergaenzen import (adressbuch_bauen, adressen_ergaenzen, daten_laden,
                                                 ort_adressen_bauen, titel_index_bauen)
        from pipeline.deduplication import ist_rausgegangen
        from pipeline.ort_zuordnung import index_laden

        orte, bestand = daten_laden(db)
        offen = [e for e in _seiten(db, "events", "id,titel,datum,ort,ort_id,adresse,stadtteil,quelle_name,quelle_url,"
                                                   "redaktion_felder",
                                    lambda q: q.gte("datum", heute).is_("adresse", "null").eq("abgelehnt", False))
                 if ist_rausgegangen(e) and not _geschuetzt(e, "adresse")]
        adressen_ergaenzen(offen, adressbuch_bauen(orte, bestand), titel_index_bauen(bestand),
                           ort_adressen_bauen(index_laden(db)))
        ergebnis["adresse"] = vorschlaege_schreiben(db, adresse_vorschlaege(offen, lauf_id))
    except Exception as e:
        logger.error("Adress-Vorschläge nicht erzeugt: %s", e)
    return ergebnis


def vorschlaege_schreiben(db, zeilen: list[dict]) -> int:
    """Schreibt neue Vorschläge; bestehende (auch abgelehnte) bleiben unverändert."""
    for i in range(0, len(zeilen), STAPEL):
        db.table("admin_vorschlaege").upsert(zeilen[i:i + STAPEL], on_conflict="art,schluessel", ignore_duplicates=True).execute()
    return len(zeilen)


def _alle_sichtbaren(db) -> list[dict]:
    """Alle sichtbaren Events ohne untere Datumsgrenze – wie gebiet.py --sql, damit auch Langläufer mit Start vor
    heute geprüft werden (Cursor-Prüfung Stufe 1d)."""
    zeilen, start = [], 0
    while True:
        teil = (db.table("events").select("id, titel, datum, ort, adresse, quelle_name")
                .eq("abgelehnt", False).order("id").range(start, start + 999).execute().data or [])
        zeilen.extend(teil)
        if len(teil) < 1000:
            return zeilen
        start += 1000


def vorschlaege_erzeugen(lauf_id: Optional[str] = None) -> dict[str, int]:
    """Dubletten (ab heute) und Gebiet (ganzer sichtbarer Bestand). Wirft nie, auch nicht beim Import; meldet ins Log."""
    ergebnis = {"dublette": 0, "gebiet": 0, "ortsname": 0, "ort_id": 0, "adresse": 0}
    try:
        from database.client import get_supabase_client
        from pipeline.deduplication import titel_status_bereinigen
        from pipeline.dubletten_sql import events_laden

        db = get_supabase_client()
        events = events_laden(date.today().isoformat())
        original = {e["id"]: dict(e) for e in events}
        for e in events:
            titel_status_bereinigen(e)
        ergebnis["dublette"] = vorschlaege_schreiben(db, dubletten_vorschlaege(events, original, lauf_id))
        ergebnis["gebiet"] = vorschlaege_schreiben(db, gebiet_vorschlaege(_alle_sichtbaren(db), lauf_id))
        ergebnis.update(_orte_vorschlaege(db, lauf_id))
        logger.info("Vorschläge geprüft: %d Dubletten-Paare, %d außerhalb des Gebiets, %d Ortsnamen, %d Ortszuordnungen, "
                    "%d Adressen (neue und schon bekannte)", ergebnis["dublette"], ergebnis["gebiet"],
                    ergebnis["ortsname"], ergebnis["ort_id"], ergebnis["adresse"])
    except Exception as e:
        logger.error("Vorschläge konnten nicht erzeugt werden (admin_grundlagen_2026-11-23.sql ausgeführt?): %s", e)
    return ergebnis


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    logging.getLogger("httpx").setLevel(logging.WARNING)
    vorschlaege_erzeugen()


if __name__ == "__main__":
    main()
