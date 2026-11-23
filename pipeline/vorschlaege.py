"""
vorschlaege.py – DiesDasDüsseldorf
Vorschläge statt SQL-Dateien (Plan docs/plan-admin-dashboard-2026-11-23.md, 3.5, Stufe 1d).

Die Skripte für Dubletten und Gebiet schreiben ihre Treffer in public.admin_vorschlaege. Im Admin-Bereich nimmt die
Redaktion sie an oder lehnt sie ab; erst die Annahme ändert Daten (SECURITY-DEFINER-Funktionen aus
database/admin_events_2026-11-23.sql). Doppelte Vorschläge verhindert der Schlüssel (art, schluessel): Die Pipeline
schreibt mit ON CONFLICT DO NOTHING, abgelehnte bleiben so liegen und kommen nicht wieder.

Aufruf von Hand:   python -m pipeline.vorschlaege            (Dubletten und Gebiet, ab heute)
Im Lauf:           main.py, Schritt 3e (vorschlaege_erzeugen)
"""
import logging
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
    ergebnis = {"dublette": 0, "gebiet": 0}
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
        logger.info("Vorschläge geprüft: %d Dubletten-Paare, %d außerhalb des Gebiets (neue und schon bekannte)",
                    ergebnis["dublette"], ergebnis["gebiet"])
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
