"""
jsonld_events.py – DiesDasDüsseldorf
Baustein: schema.org-Events aus <script type="application/ld+json"> lesen (Plan docs/plan-quellen-ausbau-2026-11-23.md,
3.3, Schritt V1). Für Venue-Scraper und Plattformen, die ihre Termine als JSON-LD auszeichnen.

events_aus_html(html, seiten_url) liefert Rohtermine:
    {"titel", "start": "YYYY-MM-DD", "uhrzeit": "HH:MM" | None, "ende": "YYYY-MM-DD" | None, "ort", "adresse",
     "bild_url", "preis", "url", "beschreibung", "abgesagt"}
Berücksichtigt: einzelne Objekte, Listen, "@graph", verschachtelte "subEvent" (je Unter-Termin ein Eintrag) und alle
Typen, die auf "Event" enden (MusicEvent, TheaterEvent …). Ein kaputtes Skript wird übersprungen, nicht geworfen.
Die Umwandlung ins DDA-Event macht der aufrufende Scraper (Ort in der Schreibweise der Ortstabelle, Kategorie, Quelle).
"""
import html as html_lib
import json
import logging
import re
from typing import Any, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

_SKRIPT = re.compile(r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", re.S | re.I)
_DATUM = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:[T ](\d{2}):(\d{2}))?")


def _liste(wert: Any) -> list:
    if wert is None:
        return []
    return wert if isinstance(wert, list) else [wert]


def _typen(obj: dict) -> list[str]:
    return [str(t) for t in _liste(obj.get("@type"))]


def ist_event(obj: Any) -> bool:
    return isinstance(obj, dict) and any(t.endswith("Event") for t in _typen(obj))


def _alle_objekte(daten: Any) -> list[dict]:
    """Flacht Listen und @graph ab."""
    ergebnis = []
    for obj in _liste(daten):
        if not isinstance(obj, dict):
            continue
        if "@graph" in obj:
            ergebnis.extend(_alle_objekte(obj["@graph"]))
        else:
            ergebnis.append(obj)
    return ergebnis


def _text(wert: Any) -> Optional[str]:
    if isinstance(wert, list):
        wert = wert[0] if wert else None
    if isinstance(wert, dict):
        wert = wert.get("name") or wert.get("@value")
    if not isinstance(wert, str):
        return None
    ohne_tags = re.sub(r"<[^>]+>", " ", html_lib.unescape(wert))
    return re.sub(r"\s+", " ", ohne_tags).strip() or None


def _adresse(ort: Any) -> Optional[str]:
    if not isinstance(ort, dict):
        return None
    adr = ort.get("address")
    if isinstance(adr, str):
        return adr.strip() or None
    if not isinstance(adr, dict):
        return None
    strasse = (adr.get("streetAddress") or "").strip()
    plz_ort = " ".join(x for x in ((adr.get("postalCode") or "").strip(), (adr.get("addressLocality") or "").strip()) if x)
    return ", ".join(x for x in (strasse, plz_ort) if x) or None


def _preis(angebote: Any) -> Optional[str]:
    werte = []
    for a in _liste(angebote):
        if not isinstance(a, dict):
            continue
        for feld in ("price", "lowPrice"):
            try:
                werte.append(float(str(a.get(feld)).replace(",", ".")))
            except (TypeError, ValueError):
                pass
    if not werte:
        return None
    kleinster = min(werte)
    if kleinster == 0:
        return "kostenlos"
    betrag = f"{kleinster:.2f}".replace(".", ",").replace(",00", "")
    return f"ab {betrag} €" if len(set(werte)) > 1 else f"{betrag} €"


def _bild(wert: Any) -> Optional[str]:
    for b in _liste(wert):
        if isinstance(b, str) and b.startswith("http"):
            return b
        if isinstance(b, dict) and str(b.get("url") or "").startswith("http"):
            return b["url"]
    return None


def _ortszeit(wert: Any) -> tuple[Optional[str], Optional[str]]:
    """("YYYY-MM-DD", "HH:MM" | None) in Düsseldorfer Ortszeit; Zeitangaben mit Zone (…Z, +01:00) werden umgerechnet."""
    text = str(wert or "").strip()
    treffer = _DATUM.match(text)
    if not treffer:
        return None, None
    if treffer.group(2) and re.search(r"(Z|[+-]\d{2}:?\d{2})$", text):
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            zeit = datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Berlin"))
            return zeit.date().isoformat(), zeit.strftime("%H:%M")
        except ValueError:
            pass
        except Exception as fehler:  # z. B. fehlende Zeitzonen-Datenbank (tzdata) unter Windows
            logger.warning("JSON-LD: Zeitzone nicht umrechenbar (%s) – Uhrzeit bleibt wie angegeben: %s", fehler, text)
    return treffer.group(1), (f"{treffer.group(2)}:{treffer.group(3)}" if treffer.group(2) else None)


def _termin(obj: dict, eltern: Optional[dict], seiten_url: str) -> Optional[dict]:
    start, uhrzeit = _ortszeit(obj.get("startDate"))
    titel = _text(obj.get("name")) or (eltern and _text(eltern.get("name")))
    if not start or not titel:
        return None
    ende, _ = _ortszeit(obj.get("endDate"))
    ort = obj.get("location") or (eltern or {}).get("location")
    ort = _liste(ort)[0] if _liste(ort) else None
    status = str(obj.get("eventStatus") or "")
    return {
        "titel": titel,
        "start": start,
        "uhrzeit": uhrzeit if uhrzeit != "00:00" or not ende else None,
        "ende": ende,
        "ort": _text(ort.get("name")) if isinstance(ort, dict) else _text(ort),
        "adresse": _adresse(ort),
        "bild_url": _bild(obj.get("image")) or (eltern and _bild(eltern.get("image"))),
        "preis": _preis(obj.get("offers")) or (eltern and _preis(eltern.get("offers"))),
        "url": urljoin(seiten_url, str(obj.get("url") or (eltern or {}).get("url") or seiten_url)),
        "beschreibung": _text(obj.get("description")),
        "abgesagt": "Cancelled" in status or "Postponed" in status,
    }


def events_aus_daten(daten: Any, seiten_url: str = "") -> list[dict]:
    """Rohtermine aus bereits gelesenem JSON-LD (dict oder Liste)."""
    termine = []
    for obj in _alle_objekte(daten):
        if not ist_event(obj):
            continue
        unter = [u for u in _liste(obj.get("subEvent")) if ist_event(u)]
        if unter:
            termine.extend(t for u in unter if (t := _termin(u, obj, seiten_url)))
        elif (t := _termin(obj, None, seiten_url)):
            termine.append(t)
    return termine


def events_aus_html(html: str, seiten_url: str = "") -> list[dict]:
    """Rohtermine aus allen JSON-LD-Skripten einer Seite; ohne Treffer leere Liste."""
    termine = []
    for block in _SKRIPT.findall(html or ""):
        try:
            daten = json.loads(block.strip())
        except json.JSONDecodeError:
            try:  # manche Seiten liefern Steuerzeichen in Texten
                daten = json.loads(re.sub(r"[\x00-\x1f]", " ", block.strip()))
            except json.JSONDecodeError:
                logger.debug("JSON-LD nicht lesbar auf %s", seiten_url)
                continue
        termine.extend(events_aus_daten(daten, seiten_url))
    return termine
