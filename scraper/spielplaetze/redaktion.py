"""
redaktion.py – DiesDasDüsseldorf
Felder von extras.spielplatz, die im Admin-Bereich gepflegt werden (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.7,
Stufe 3b, Entscheidung Q6 vom 23.11.2026: Dashboard führend für „bestätigt“ und „ausgeschlossen“).

Die Funktion admin_spielplatz_setzen (database/admin_guides_2026-11-23.sql) trägt jedes geänderte Feld in
extras.spielplatz.redaktion ein. Die Importe (stadt_import.py, abenteuer_import.py) übernehmen diese Felder danach
aus der Datenbank statt aus korrekturen.csv bzw. abenteuer.csv.
"""
from __future__ import annotations

# Nur diese Felder darf der Admin-Bereich übernehmen (Schutz gegen beliebige Einträge in „redaktion“)
REDAKTION_FELDER = ("bestaetigt", "ausgeschlossen")


def redaktion_behalten(sp_neu: dict, sp_aktuell: dict | None) -> dict:
    """extras.spielplatz nach dem Import: Felder aus sp_aktuell["redaktion"] kommen aus der Datenbank (sp_aktuell)."""
    sp_aktuell = sp_aktuell or {}
    geschuetzt = [f for f in (sp_aktuell.get("redaktion") or []) if f in REDAKTION_FELDER]
    ergebnis = {**sp_neu, **{f: sp_aktuell.get(f) for f in geschuetzt}}
    if sp_aktuell.get("redaktion"):
        ergebnis["redaktion"] = sp_aktuell["redaktion"]
    return ergebnis
