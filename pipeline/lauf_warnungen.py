"""
lauf_warnungen.py – DiesDasDüsseldorf
Warnregeln W1–W6 für die Scraper-Läufe und Warn-Mail nach dem Lauf (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.3).

Dieselben Regeln rechnet das Cockpit in TypeScript (web/lib/admin/warnregeln.ts). Beide prüfen gegen
tests/fixtures/lauf_warnungen.json.

Warn-Mail (E8): Am Ende jedes Laufs (pipeline/lauf_report.py, abschliessen) geht bei W1, W2, W4 oder W6 oder bei einem
abgebrochenen Lauf EINE Mail an hallo@diesdas.events. Versand über denselben SMTP-Weg wie die Geburtstagsmails
(Umgebung SMTP_HOST, SMTP_PORT, SMTP_BENUTZER, SMTP_PASSWORT). Fehlen sie, wird nur geloggt.
"""
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from statistics import median
from typing import Any, Optional

logger = logging.getLogger(__name__)

LAUF_ALT_TAGE = 4
LAUF_HAENGT_MINUTEN = 90
# Diese Regeln lösen die Mail aus (W3 und W5 nur im Cockpit: W3 ist nur gelb, W5 kann der laufende Job nicht sehen)
MAIL_REGELN = {"W1", "W2", "W4", "W6"}
EMPFAENGER = "hallo@diesdas.events"
COCKPIT_URL = "https://admin.diesdas.events/admin/scraper"


@dataclass
class Warnung:
    regel: str
    stufe: str  # rot | gelb
    quelle: Optional[str]
    text: str


def _zeit(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def warnungen_berechnen(laeufe: list[dict], ergebnisse: list[dict], jetzt: datetime) -> list[Warnung]:
    """Gleiche Logik wie warnungenBerechnen in web/lib/admin/warnregeln.ts."""
    warnungen: list[Warnung] = []
    sortiert = sorted(laeufe, key=lambda l: l["gestartet_am"], reverse=True)
    neuester = sortiert[0] if sortiert else None

    # W5
    if neuester is None:
        warnungen.append(Warnung("W5", "rot", None, "Es gibt noch keinen Scraper-Lauf."))
    else:
        alter = jetzt - _zeit(neuester["gestartet_am"])
        if neuester["status"] == "laeuft" and alter > timedelta(minutes=LAUF_HAENGT_MINUTEN):
            warnungen.append(Warnung("W5", "rot", None, f"Der Lauf läuft seit über {LAUF_HAENGT_MINUTEN} Minuten."))
        elif alter > timedelta(days=LAUF_ALT_TAGE):
            warnungen.append(Warnung("W5", "rot", None, f"Seit über {LAUF_ALT_TAGE} Tagen kein Scraper-Lauf."))

    beendet = [l for l in sortiert if l["status"] != "laeuft"]
    if not beendet:
        return warnungen
    letzter = beendet[0]

    # W6
    if (letzter.get("speicher_fehler") or 0) > 0:
        warnungen.append(Warnung("W6", "gelb", None, f"{letzter['speicher_fehler']} Events konnten nicht gespeichert werden."))

    position = {l["id"]: i for i, l in enumerate(beendet)}
    je_quelle: dict[str, list[dict]] = {}
    for e in ergebnisse:
        if e["lauf_id"] in position:
            je_quelle.setdefault(e["quelle"], []).append(e)

    for quelle in sorted(je_quelle):
        liste = sorted(je_quelle[quelle], key=lambda e: position[e["lauf_id"]])
        aktuell = liste[0]
        if aktuell["lauf_id"] != letzter["id"]:
            continue
        # Im letzten Lauf übersprungen (z. B. im Admin abgeschaltet): keine Regel, auch nicht W4 (Cursor-Prüfung 5b)
        if aktuell["status"] == "uebersprungen":
            continue
        frueher = liste[1:]

        if aktuell["status"] == "fehler":  # W1
            text = f"Fehler: {aktuell['meldung']}" if aktuell.get("meldung") else "Fehler im letzten Lauf."
            warnungen.append(Warnung("W1", "rot", quelle, text))

        if aktuell["status"] == "leer":  # W2
            gut = sum(1 for e in frueher[:3] if e["status"] == "ok" and e["anzahl"] > 0)
            if gut >= 2:
                warnungen.append(Warnung("W2", "rot", quelle, "Keine Events, obwohl die Quelle zuletzt welche hatte."))

        if aktuell["status"] == "ok":  # W3
            basis = [e["anzahl"] for e in frueher if e["status"] in ("ok", "leer")][:5]
            m = median(basis) if basis else 0
            if basis and m >= 10 and aktuell["anzahl"] < 0.4 * m:
                warnungen.append(Warnung("W3", "gelb", quelle, f"Nur {aktuell['anzahl']} Events statt üblicher {round(m)}."))

        zaehlend = [e for e in liste if e["status"] not in ("saisonal", "uebersprungen")][:3]  # W4
        if len(zaehlend) == 3 and all(e["status"] != "ok" for e in zaehlend):
            warnungen.append(Warnung("W4", "rot", quelle, "Seit 3 Läufen ohne Erfolg."))

    return warnungen


def _mail_bauen(warnungen: list[Warnung], lauf: dict) -> EmailMessage:
    from pipeline.geburtstag_mails import ABSENDER

    abgebrochen = lauf.get("status") == "fehler"
    betreff = "Scraper-Lauf abgebrochen" if abgebrochen else f"Scraper-Lauf: {len(warnungen)} Warnung(en)"
    zeilen = [f"Lauf vom {lauf.get('gestartet_am', '')[:16].replace('T', ' ')} UTC"]
    if abgebrochen:
        zeilen.append(f"Abgebrochen: {lauf.get('fehlermeldung') or 'ohne Meldung'}")
    for w in warnungen:
        zeilen.append(f"- {w.regel} {w.quelle or 'Lauf'}: {w.text}")
    if lauf.get("github_run_url"):
        zeilen.append(f"\nLog: {lauf['github_run_url']}")
    zeilen.append(f"Cockpit: {COCKPIT_URL}")

    m = EmailMessage()
    m["From"] = ABSENDER
    m["To"] = EMPFAENGER
    m["Subject"] = f"[dies.das] {betreff}"
    m["Date"] = formatdate(localtime=False)
    m["Message-ID"] = make_msgid(domain="diesdas.events")
    m.set_content("\n".join(zeilen))
    return m


def warnmail_nach_lauf(db: Any, lauf_id: str, jetzt: Optional[datetime] = None) -> bool:
    """
    Rechnet die Warnungen für den eben beendeten Lauf und schickt bei Bedarf eine Mail. Wirft nie: Ein Fehler hier
    darf den Lauf nicht kippen. Gibt True zurück, wenn eine Mail rausging.
    """
    jetzt = jetzt or datetime.now(timezone.utc)
    try:
        laeufe = (
            db.table("scraper_laeufe")
            .select("id, gestartet_am, beendet_am, status, speicher_fehler, github_run_url, fehlermeldung")
            .order("gestartet_am", desc=True)
            .limit(8)
            .execute()
            .data
            or []
        )
        ids = [l["id"] for l in laeufe]
        ergebnisse = (
            db.table("scraper_ergebnisse").select("lauf_id, quelle, status, anzahl, meldung").in_("lauf_id", ids).limit(2000).execute().data
            or []
        ) if ids else []
        lauf = next((l for l in laeufe if l["id"] == lauf_id), None)
        if lauf is None:
            return False
        warnungen = [w for w in warnungen_berechnen(laeufe, ergebnisse, jetzt) if w.regel in MAIL_REGELN]
        if not warnungen and lauf.get("status") != "fehler":
            logger.info("Warnregeln: keine Warnung für die Mail")
            return False
        for w in warnungen:
            logger.warning("Warnregel %s %s: %s", w.regel, w.quelle or "Lauf", w.text)

        host, benutzer, passwort = os.getenv("SMTP_HOST"), os.getenv("SMTP_BENUTZER"), os.getenv("SMTP_PASSWORT")
        if not (host and benutzer and passwort):
            logger.warning("Warn-Mail nicht verschickt: SMTP-Zugang fehlt in der Umgebung")
            return False
        from pipeline.geburtstag_mails import Versender

        with Versender(host, int(os.getenv("SMTP_PORT") or 587), benutzer, passwort) as v:
            v.senden(_mail_bauen(warnungen, lauf))
        logger.info("Warn-Mail an %s verschickt (%d Warnung(en))", EMPFAENGER, len(warnungen))
        return True
    except Exception as e:
        logger.warning("Warn-Mail nach dem Lauf fehlgeschlagen: %s", e)
        return False
