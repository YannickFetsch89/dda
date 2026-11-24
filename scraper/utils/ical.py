"""
ical.py – DiesDasDüsseldorf
Baustein: iCal-Feeds (.ics) ohne zusätzliche Bibliothek lesen (Plan docs/plan-quellen-ausbau-2026-11-23.md, 3.3,
Schritt V1). Beispiel: The Vinyl Room (plattenparty.ics).

termine_aus_ics(text, von, bis) liefert Rohtermine wie scraper/utils/jsonld_events.py. Unterstützt: gefaltete Zeilen,
DTSTART als Datum (ganztägig) oder Zeitpunkt (UTC mit „Z“ wird nach Europe/Berlin umgerechnet, TZID und lokale Zeit
gelten als Ortszeit), STATUS:CANCELLED, RRULE mit FREQ=DAILY/WEEKLY/MONTHLY und INTERVAL, UNTIL oder COUNT sowie
EXDATE. Andere Wiederholungsregeln (BYDAY-Listen, BYSETPOS …) werden nicht ausgerollt – dann zählt nur der erste
Termin, und eine Warnung landet im Log.
"""
import logging
import re
from datetime import date, datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)
MAX_WIEDERHOLUNGEN = 400


def _entfalten(text: str) -> list[str]:
    zeilen: list[str] = []
    for zeile in (text or "").replace("\r\n", "\n").split("\n"):
        if zeile.startswith((" ", "\t")) and zeilen:
            zeilen[-1] += zeile[1:]
        else:
            zeilen.append(zeile)
    return zeilen


def _wert(text: str) -> str:
    return text.replace("\\n", " ").replace("\\N", " ").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\").strip()


def _zeitpunkt(eigenschaften: str, wert: str) -> tuple[Optional[date], Optional[str]]:
    """(Tag, "HH:MM" | None) in Ortszeit."""
    wert = wert.strip()
    if "VALUE=DATE" in eigenschaften.upper() or re.fullmatch(r"\d{8}", wert):
        try:
            return datetime.strptime(wert[:8], "%Y%m%d").date(), None
        except ValueError:
            return None, None
    try:
        zeit = datetime.strptime(wert[:15], "%Y%m%dT%H%M%S")
    except ValueError:
        return None, None
    if wert.endswith("Z"):
        from datetime import timezone
        from zoneinfo import ZoneInfo
        zeit = zeit.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Europe/Berlin")).replace(tzinfo=None)
    return zeit.date(), zeit.strftime("%H:%M")


def _vevents(zeilen: list[str]) -> list[dict[str, tuple[str, str]]]:
    events, aktuell = [], None
    for zeile in zeilen:
        if zeile == "BEGIN:VEVENT":
            aktuell = {}
        elif zeile == "END:VEVENT" and aktuell is not None:
            events.append(aktuell)
            aktuell = None
        elif aktuell is not None and ":" in zeile:
            kopf, wert = zeile.split(":", 1)
            name, _, eigenschaften = kopf.partition(";")
            name = name.upper()
            if name == "EXDATE":
                aktuell.setdefault("_EXDATE", []).append((eigenschaften, wert))
            else:
                aktuell[name] = (eigenschaften, wert)
    return events


def _wiederholungen(start: date, regel: str, exdates: set[date], bis: date) -> list[date]:
    teile = dict(t.split("=", 1) for t in regel.split(";") if "=" in t)
    freq = teile.get("FREQ", "").upper()
    if freq not in ("DAILY", "WEEKLY", "MONTHLY") or set(teile) - {"FREQ", "INTERVAL", "UNTIL", "COUNT", "WKST"}:
        logger.warning("iCal: Wiederholungsregel nicht unterstützt (%s) – nur der erste Termin", regel)
        return [start]
    schritt = max(1, int(teile.get("INTERVAL", "1") or 1))
    ende = bis
    if teile.get("UNTIL"):
        try:
            ende = min(bis, datetime.strptime(teile["UNTIL"][:8], "%Y%m%d").date())
        except ValueError:
            pass
    anzahl = min(int(teile["COUNT"]) if teile.get("COUNT", "").isdigit() else MAX_WIEDERHOLUNGEN, MAX_WIEDERHOLUNGEN)
    tage: list[date] = []
    erzeugt = 0  # COUNT zählt nur Termine, die es gibt (auch Ausfalltage per EXDATE), nicht übersprungene Monate
    for k in range(MAX_WIEDERHOLUNGEN * 2):
        if erzeugt >= anzahl:
            break
        if freq == "DAILY":
            tag: Optional[date] = start + timedelta(days=k * schritt)
        elif freq == "WEEKLY":
            tag = start + timedelta(weeks=k * schritt)
        else:
            monat = start.month - 1 + k * schritt
            try:
                tag = start.replace(year=start.year + monat // 12, month=monat % 12 + 1)
            except ValueError:  # z. B. der 31. in einem kürzeren Monat: diesen Monat auslassen (wie RFC 5545)
                tag = None
        if tag is None:
            continue
        if tag > ende:
            break
        erzeugt += 1
        if tag not in exdates:
            tage.append(tag)
    return tage


def termine_aus_ics(text: str, von: date, bis: date) -> list[dict]:
    """Alle Termine zwischen von und bis (einschließlich)."""
    termine = []
    for ev in _vevents(_entfalten(text)):
        if "DTSTART" not in ev or "SUMMARY" not in ev:
            continue
        if _wert(ev.get("STATUS", ("", ""))[1]).upper() == "CANCELLED":
            continue
        tag, uhrzeit = _zeitpunkt(*ev["DTSTART"])
        if tag is None:
            continue
        exdates = {d for e in ev.get("_EXDATE", []) for w in e[1].split(",") if (d := _zeitpunkt(e[0], w)[0])}
        tage = _wiederholungen(tag, ev["RRULE"][1], exdates, bis) if "RRULE" in ev else [tag]
        ende = _zeitpunkt(*ev["DTEND"])[0] if "DTEND" in ev else None
        # Ganztägig: DTEND ist der Tag NACH dem letzten Tag (RFC 5545) – als letzten Tag speichern
        if ende and uhrzeit is None:
            ende -= timedelta(days=1)
        for t in tage:
            if von <= t <= bis:
                termine.append({
                    "titel": _wert(ev["SUMMARY"][1]),
                    "start": t.isoformat(),
                    "uhrzeit": uhrzeit,
                    "ende": (t + (ende - tag)).isoformat() if ende and ende > tag and uhrzeit is None else None,
                    "ort": _wert(ev["LOCATION"][1]) if "LOCATION" in ev else None,
                    "adresse": None,
                    "bild_url": None,
                    "preis": None,
                    "url": _wert(ev["URL"][1]) if "URL" in ev else None,
                    "beschreibung": _wert(ev["DESCRIPTION"][1]) if "DESCRIPTION" in ev else None,
                    "abgesagt": False,
                })
    return termine
