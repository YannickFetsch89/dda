"""
lauf_report.py – DiesDasDüsseldorf
Protokolliert jeden Pipeline-Lauf und das Ergebnis jeder einzelnen Quelle in Supabase
(Tabellen scraper_laeufe / scraper_ergebnisse, siehe database/scraper_report.sql).

Grundlage für den Tab "Scraper-Report" im Admin-Dashboard: Dort fällt sofort auf,
wenn eine Quelle plötzlich 0 Events liefert oder abstürzt.

Das Protokoll ist bewusst "best effort": Fehlen die Tabellen oder ist Supabase nicht
erreichbar, wird nur gewarnt – die Pipeline selbst läuft immer weiter.
"""
import asyncio
import inspect
import logging
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Interner Schlüssel, mit dem jedes Event seine Quelle durch Deduplizierung und Speicherung trägt.
# Felder mit "_" am Anfang werden vor dem Speichern entfernt (database/client.py).
SCRAPER_FELD = "_scraper"

# Log-Meldungen, an denen bewusst übersprungene bzw. saisonal leere Quellen erkannt werden
_UEBERSPRUNGEN = re.compile(r"übersprungen|nicht gesetzt|deaktiviert", re.IGNORECASE)
_SAISONAL = re.compile(r"saison", re.IGNORECASE)


class _LogSammler(logging.Handler):
    """Sammelt während eines Scraper-Aufrufs Warnungen, Fehler und Hinweise aus dem Log."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.warnungen = 0
        self.fehler = 0
        self.letzte_problem_meldung: Optional[str] = None
        self.uebersprungen = False
        self.saisonal = False
        self.saison_meldung: Optional[str] = None

    def emit(self, record: logging.LogRecord) -> None:
        try:
            meldung = record.getMessage()
        except Exception:
            return
        # Eigene Zählzeilen aus main.py ("zakk: 12 Events") nicht mitzählen
        if record.name == "__main__":
            return
        if record.levelno >= logging.ERROR:
            self.fehler += 1
            self.letzte_problem_meldung = meldung
        elif record.levelno >= logging.WARNING:
            self.warnungen += 1
            self.letzte_problem_meldung = meldung
        if _UEBERSPRUNGEN.search(meldung):
            self.uebersprungen = True
            self.letzte_problem_meldung = self.letzte_problem_meldung or meldung
        if _SAISONAL.search(meldung):
            self.saisonal = True
            self.saison_meldung = meldung


def _github_infos() -> tuple[str, Optional[str]]:
    """Ermittelt Auslöser und Link zum GitHub-Actions-Lauf (lokal: 'lokal', kein Link)."""
    ereignis = os.getenv("GITHUB_EVENT_NAME")
    if not ereignis:
        return "lokal", None
    ausloeser = {"schedule": "zeitplan", "workflow_dispatch": "manuell"}.get(ereignis, ereignis)
    server = os.getenv("GITHUB_SERVER_URL", "https://github.com")
    repo = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    url = f"{server}/{repo}/actions/runs/{run_id}" if repo and run_id else None
    return ausloeser, url


class LaufReport:
    """Erfasst einen Pipeline-Lauf samt Ergebnissen pro Quelle."""

    def __init__(self) -> None:
        self.lauf_id: Optional[str] = None
        self.ergebnisse: list[dict] = []
        self.kennzahlen: dict[str, Any] = {}
        self._db = None

    # ── Start ────────────────────────────────────────────────────────────────

    def starten(self) -> None:
        """Legt den Lauf in Supabase an (Status 'laeuft')."""
        ausloeser, url = _github_infos()
        try:
            from database.client import get_supabase_client
            self._db = get_supabase_client()
            antwort = (
                self._db.table("scraper_laeufe")
                .insert({"ausloeser": ausloeser, "github_run_url": url})
                .execute()
            )
            self.lauf_id = antwort.data[0]["id"] if antwort.data else None
            logger.info("Lauf-Report angelegt (ID %s)", self.lauf_id)
        except Exception as e:
            self.lauf_id = None
            logger.warning(
                "Lauf-Report konnte nicht angelegt werden (Tabelle scraper_laeufe fehlt? "
                "database/scraper_report.sql ausführen): %s", e,
            )

    # ── Scraper ausführen und erfassen ───────────────────────────────────────

    async def scraper_ausfuehren(self, name: str, tier: int, funktion: Callable) -> list[dict]:
        """
        Führt einen Scraper aus, misst Dauer und Ergebnis und fängt Abstürze ab.

        Synchrone Scraper laufen in einem eigenen Thread (Playwright-Sync-API
        verträgt keine laufende Event-Loop), asynchrone werden direkt awaited.

        Returns:
            Liste der Events (bei Absturz leer). Jedes Event trägt den Quellnamen
            im Feld SCRAPER_FELD, damit später "neu gespeichert" pro Quelle zählbar ist.
        """
        sammler = _LogSammler()
        wurzel = logging.getLogger()
        wurzel.addHandler(sammler)
        start = time.monotonic()
        events: list[dict] = []
        absturz: Optional[str] = None

        try:
            if inspect.iscoroutinefunction(funktion):
                events = await funktion()
            else:
                events = await asyncio.to_thread(funktion)
            events = list(events or [])
        except Exception as e:
            absturz = f"{type(e).__name__}: {e}"
            logger.error("Scraper %s abgestürzt: %s", name, absturz)
            events = []
        finally:
            wurzel.removeHandler(sammler)

        dauer = round(time.monotonic() - start, 1)
        anzahl = len(events)
        logger.info("%s: %d Events (%.1f s)", name, anzahl, dauer)

        for event in events:
            event[SCRAPER_FELD] = name

        if absturz:
            status, meldung = "fehler", absturz
        elif anzahl > 0:
            status, meldung = "ok", sammler.letzte_problem_meldung
        elif sammler.uebersprungen:
            status, meldung = "uebersprungen", sammler.letzte_problem_meldung
        elif sammler.saisonal:
            status, meldung = "saisonal", sammler.saison_meldung
        elif sammler.fehler:
            status, meldung = "fehler", sammler.letzte_problem_meldung
        else:
            status, meldung = "leer", sammler.letzte_problem_meldung

        self.ergebnisse.append({
            "quelle": name,
            "tier": tier,
            "status": status,
            "anzahl": anzahl,
            "dauer_sekunden": dauer,
            "warnungen": sammler.warnungen,
            "fehler": sammler.fehler + (1 if absturz else 0),
            "meldung": (meldung or "")[:500] or None,
        })
        return events

    # ── Kennzahlen und Abschluss ─────────────────────────────────────────────

    def kennzahl(self, **werte: Any) -> None:
        """Merkt sich Kennzahlen des Laufs (z.B. events_gesammelt=1915)."""
        self.kennzahlen.update(werte)

    def neu_pro_quelle_setzen(self, neu_pro_quelle: Counter) -> None:
        """Überträgt die Anzahl neu gespeicherter Events je Quelle aus events_speichern()."""
        for ergebnis in self.ergebnisse:
            ergebnis["neu_gespeichert"] = int(neu_pro_quelle.get(ergebnis["quelle"], 0))

    def abschliessen(self, fehlermeldung: Optional[str] = None) -> None:
        """Schreibt Kennzahlen und Ergebnisse pro Quelle nach Supabase."""
        if not self.lauf_id or self._db is None:
            return
        try:
            update = {
                **self.kennzahlen,
                "beendet_am": datetime.now(timezone.utc).isoformat(),
                "status": "fehler" if fehlermeldung else "erfolgreich",
                "fehlermeldung": (fehlermeldung or "")[:2000] or None,
            }
            self._db.table("scraper_laeufe").update(update).eq("id", self.lauf_id).execute()
            if self.ergebnisse:
                zeilen = [{**e, "lauf_id": self.lauf_id} for e in self.ergebnisse]
                self._db.table("scraper_ergebnisse").insert(zeilen).execute()
            auffaellig = [e["quelle"] for e in self.ergebnisse if e["status"] in ("leer", "fehler")]
            logger.info(
                "Lauf-Report gespeichert: %d Quellen, davon auffällig: %s",
                len(self.ergebnisse), ", ".join(auffaellig) or "keine",
            )
        except Exception as e:
            logger.warning("Lauf-Report konnte nicht gespeichert werden: %s", e)
