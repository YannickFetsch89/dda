"""
quellen.py – DiesDasDüsseldorf
Quellen an/aus (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.10, Stufe 5b).

Im Admin-Bereich (Scraper → Quellen) lässt sich jede Quelle aus QUELLEN in main.py abschalten. Das steht in
public.quellen_einstellungen (database/admin_quellen_2026-11-24.sql). main.py liest die Tabelle zu Beginn des Laufs
und überspringt abgeschaltete Quellen; im Scraper-Report erscheinen sie als „uebersprungen“ (zählt nicht für W4).
Ist die Tabelle nicht lesbar, laufen alle Quellen wie bisher.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def abgeschaltet_aus_zeilen(zeilen: list[dict]) -> dict[str, str]:
    """{Quelle: Grund} aller Zeilen mit aktiv = false (rein, testbar)."""
    return {str(z["quelle"]): (z.get("grund") or "").strip() for z in zeilen or [] if z.get("quelle") and z.get("aktiv") is False}


def quellen_abgeschaltet(db=None) -> dict[str, str]:
    """Abgeschaltete Quellen aus der Datenbank; bei jedem Fehler {} (dann laufen alle)."""
    try:
        if db is None:
            from database.client import get_supabase_client
            db = get_supabase_client()
        zeilen = db.table("quellen_einstellungen").select("quelle, aktiv, grund").eq("aktiv", False).execute().data or []
        ergebnis = abgeschaltet_aus_zeilen(zeilen)
        if ergebnis:
            logger.info("Im Admin-Bereich abgeschaltet: %s", ", ".join(sorted(ergebnis)))
        return ergebnis
    except Exception as e:  # noqa: BLE001 – Lauf darf daran nie scheitern
        logger.warning("Quellen-Einstellungen nicht lesbar (admin_quellen_2026-11-24.sql ausgeführt?) – alle Quellen laufen: %s", e)
        return {}


def meldung(grund: Optional[str]) -> str:
    return f"Im Admin-Bereich abgeschaltet{': ' + grund if grund else ''}"[:500]
