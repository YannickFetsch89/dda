"""
visitduesseldorf_fuehrungen.py – DiesDasDüsseldorf
Öffentliche Stadtführungen von Visit Düsseldorf (Altstadt-Führung, Kurzführungen, Nachtwächter,
Opernhaus-, Kirchen- und Bunkerführungen, Themen- und Krimitouren …).

Hintergrund (Stand 2026-11):
  Die Übersicht „Öffentliche Touren“ ist ein JavaScript-Widget (Toubiz). Jede Event-Seite
  (/event/<slug>) enthält aber serverseitig das komplette Event als JSON im Attribut
  data-tb-detail-event – inklusive aller Termine (datesCache), Kategorie, Preis, Treffpunkt
  und Bild. Der bestehende Scraper visitduesseldorf.py liest den allgemeinen Kalender und
  erwischt Führungen kaum.

Ablauf:
  1. sitemap.xml lesen (881 /event/-Seiten mit lastmod)
  2. Kandidaten über den Slug vorfiltern (fuehrung, rundgang, tour, nachtwaechter …)
  3. Nur Seiten neu laden, deren lastmod sich seit dem letzten Lauf geändert hat – jede Seite
     ist ca. 1,8 MB groß. Zwischenspeicher: data/visitduesseldorf/fuehrungen.json (nicht im Git)
  4. Übernommen wird, was Toubiz als „Führung“ einordnet; Museumsführungen nicht
     (die liefern die Museums-Scraper, sonst entstünden Duplikate), Konzert-„Tours“ ebenfalls nicht.

robots.txt: /event/ und /sitemap.xml sind erlaubt (gesperrt sind nur /duesseldorf/offer, Warenkorb, /neos/).
Erstellt: 2026-11-05
"""
import asyncio
import html
import json
import logging
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import httpx

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import STANDARD_HEADERS

logger = logging.getLogger(__name__)

QUELLE_NAME = "VisitDüsseldorf"
BASE_URL = "https://www.visitduesseldorf.de"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
KATEGORIE = "stadtfuehrung"
WARTEZEIT = 2.0
CACHE_DATEI = Path(__file__).resolve().parents[2] / "data" / "visitduesseldorf" / "fuehrungen.json"

# Vorfilter über den Slug (die eigentliche Entscheidung trifft die Toubiz-Kategorie)
KANDIDAT_MUSTER = re.compile(
    r"f(ue|ü)hrung|rundgang|rundfahrt|spaziergang|nachtw(ae|ä)chter|stadtrallye|tour|krimi|true-crime", re.I
)
# Toubiz-Kategorien, die als Stadtführung zählen bzw. ausgeschlossen werden
FUEHRUNG_KATEGORIEN = {"führung", "stadtführung", "stadtrundgang", "stadtrundfahrt", "rundfahrt", "themenführung"}
AUSSCHLUSS_KATEGORIEN = {"museumsführung", "konzert"}

# Selbstgeführte Smartphone-Rallyes stehen täglich im Kalender, sind aber keine Führung.
# Führungen DURCH ein Museum/eine Ausstellung gehören zu kultur (liefern die Museums-Scraper) –
# ein Museum als Wegpunkt („Rundgang vom Museum zum Rhein“) bleibt eine Stadtführung.
AUSSCHLUSS_TITEL = re.compile(
    r"rallye|escape"
    r"|museumsf(?:ü|ue)hrung|ausstellungsf(?:ü|ue)hrung|kurator\*?(?:innen)?f(?:ü|ue)hrung"
    r"|f(?:ü|ue)hrung\s+(?:im|in\s+der|durch\s+(?:das|die|den))\s[^,:]*?(?:museum|ausstellung)",
    re.I,
)

# Straße + Hausnummer, danach optional „, 40213 Düsseldorf“ (Ortsteil nur mit Bindestrich,
# damit kein folgendes Wort wie „Treffpunkt“ als Ort gilt). Straßenformen:
#   „Am Marktplatz 12“, „Zum Goldenen Ring 1“ (Präfix + ein/zwei Wörter) · „Rheinstraße 3-5“,
#   „Heinrich-Heine-Allee 16A“ (ein Wort mit Straßen-Endung) · „Apollo Platz 1“ · „Markt 5“
ADRESSE_MUSTER = re.compile(
    r"((?:(?:Am|An der|An den|Auf der|Auf dem|Im|In der|Zum|Zur|Unter den)\s[A-ZÄÖÜ][\wäöüß\-]*(?:\s[A-ZÄÖÜ][\wäöüß\-]*)?"
    r"|[A-ZÄÖÜ][\wäöüß\-]*(?i:straße|strasse|str\.|platz|allee|weg|ufer|gasse|markt|ring|damm|wall)"
    r"|[A-ZÄÖÜ][\wäöüß\-]*\s(?:Platz|Straße|Allee|Weg|Ufer|Markt)"
    r"|Markt|Wall|Ring)"
    r"\s*\d+(?:\s?-\s?\d+|\s?[a-zA-Z]\b)?)"
    r"(?:\s*,?\s*(\d{5})(?:\s+([A-ZÄÖÜ][\wäöüß]+(?:-[A-ZÄÖÜ][\wäöüß]+)*))?)?"
)


# ---------------------------------------------------------------------------
# Zwischenspeicher
# ---------------------------------------------------------------------------

# Bei Änderung des gespeicherten Rohformats erhöhen → alle Seiten werden einmal neu geladen
CACHE_VERSION = 3


def _cache_laden() -> dict:
    """{url: {"lastmod": str, "roh": dict | None}} – leer bei fehlender Datei oder alter Version."""
    try:
        daten = json.loads(CACHE_DATEI.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(daten, dict) or daten.get("version") != CACHE_VERSION:
        return {}
    return daten.get("seiten") or {}


def _cache_speichern(cache: dict) -> None:
    try:
        CACHE_DATEI.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_DATEI.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": CACHE_VERSION, "seiten": cache}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(CACHE_DATEI)
    except OSError as fehler:
        logger.warning("%s: Zwischenspeicher nicht schreibbar: %s", QUELLE_NAME, fehler)


# ---------------------------------------------------------------------------
# Auswertung einer Event-Seite
# ---------------------------------------------------------------------------

def _text(html_text: Optional[str]) -> str:
    """HTML → einfacher Text."""
    if not html_text:
        return ""
    ohne_tags = re.sub(r"<[^>]+>", " ", html_text)
    return re.sub(r"\s+", " ", html.unescape(ohne_tags)).strip()


def _kuerzen(text: str, laenge: int = 300) -> Optional[str]:
    if not text:
        return None
    if len(text) <= laenge:
        return text
    stueck = text[: laenge - 1]
    satzende = max(stueck.rfind(". "), stueck.rfind("! "), stueck.rfind("? "))
    if satzende >= laenge // 2:
        return stueck[: satzende + 1]
    return stueck[: stueck.rfind(" ")].rstrip(" ,;:–-") + "…"


def _treffpunkt(event: dict) -> tuple[str, Optional[str]]:
    """(Ort, Adresse) aus dem Treffpunkt-Text bzw. der Ortsangabe."""
    treff = _text(event.get("additionalMeetingPointInformation"))
    treff = re.split(r"\b(?:Endpunkt|Ende|Ziel)\s*:", treff, maxsplit=1, flags=re.I)[0]
    while True:  # „Treffpunkt: Startpunkt: …“ → „…“
        kuerzer = re.sub(r"^\s*(?:Treffpunkt|Startpunkt|Start|Beginn)\s*:?\s*", "", treff, flags=re.I)
        if kuerzer == treff:
            break
        treff = kuerzer
    treff = treff.strip(" :-–,;")
    adresse = None
    ort = treff
    if treff:
        treffer = ADRESSE_MUSTER.search(treff)
        if treffer:
            strasse, plz = treffer.group(1).strip(), treffer.group(2)
            stadt = (treffer.group(3) or "Düsseldorf").strip()
            adresse = f"{strasse}, {plz} {stadt}" if plz else f"{strasse}, {stadt}"
            ort = (treff[: treffer.start()] + " " + treff[treffer.end():]).strip(" -–,;:")
            ort = re.sub(r"\s{2,}", " ", ort)
    ort = re.sub(r"(\s*,\s*)+", ", ", ort).strip(" ,")  # „Apollo Varieté, , unterhalb“ → „…, unterhalb“
    if ort.startswith("(") and ort.endswith(")"):  # „(vor der Neanderkirche)“ → „vor der Neanderkirche“
        ort = ort[1:-1].strip()
    # Veranstaltungsort (z.B. „Deutsche Oper am Rhein“) bzw. Ortsangabe als Rückfall
    veranstaltungsort = event.get("location") or {}
    for adr in ((veranstaltungsort.get("address") or {}), ((event.get("locationData") or {}).get("address") or {})):
        if not adresse and adr.get("street"):
            adresse = f"{adr['street']} {adr.get('streetNumber') or ''}".strip()
            if adr.get("zip"):
                adresse += f", {adr['zip']} {adr.get('city') or 'Düsseldorf'}"
    if not ort:
        ort = veranstaltungsort.get("name") or (f"Treffpunkt {adresse.split(',')[0]}" if adresse else "")
    ort = ort[:120] if ort else ""
    return (ort or "Treffpunkt laut Visit Düsseldorf"), adresse


def _preis(event: dict) -> Optional[str]:
    preis = event.get("price") or {}
    if preis.get("freeEntry"):
        return "kostenlos"
    werte = [p.get("price") for p in preis.get("marketingPrices") or [] if isinstance(p.get("price"), (int, float))]
    if not werte:
        return None
    betrag = f"{min(werte):.2f}".replace(".", ",").replace(",00", "") + " €"
    return f"ab {betrag}" if len(werte) > 1 or preis.get("marketingPricePrefix") else betrag


def _ist_fuehrung(event: dict) -> bool:
    kategorien = {n.lower() for n in (event.get("category") or {}).get("rootlineNames") or []}
    kategorien |= {(k.get("name") or "").lower() for k in event.get("secondaryCategories") or []}
    return bool(kategorien & FUEHRUNG_KATEGORIEN) and not (kategorien & AUSSCHLUSS_KATEGORIEN)


def _event_lesen(seite: str, url: str) -> Optional[dict]:
    """
    Liest das Event-JSON einer Seite und behält nur die Rohfelder, die die Auswertung braucht
    (gleiche Feldnamen wie bei Toubiz). Ausgewertet wird erst in _event_aufbereiten – so wirken
    Änderungen an Filter/Adresserkennung sofort, ohne alle Seiten neu zu laden.
    """
    treffer = re.search(r"data-tb-detail-event='([^']*)'", seite) or re.search(r'data-tb-detail-event="([^"]*)"', seite)
    if not treffer:
        logger.warning("%s: Kein Event-JSON auf %s", QUELLE_NAME, url)
        return None
    try:
        event = json.loads(html.unescape(treffer.group(1)))
    except json.JSONDecodeError:
        logger.warning("%s: Event-JSON nicht lesbar auf %s", QUELLE_NAME, url)
        return None
    felder = (
        "name", "canceled", "trashed", "additionalMeetingPointInformation", "description", "intro", "price",
    )
    roh = {k: event.get(k) for k in felder}
    roh["category"] = {"rootlineNames": (event.get("category") or {}).get("rootlineNames") or []}
    roh["secondaryCategories"] = [{"name": k.get("name")} for k in event.get("secondaryCategories") or []]
    roh["locationData"] = {"address": (event.get("locationData") or {}).get("address") or {}}
    ort = event.get("location") or {}
    roh["location"] = {"name": ort.get("name"), "address": ort.get("address") or {}}
    roh["mainImage"] = {"url": (event.get("mainImage") or {}).get("url")}
    roh["datesCache"] = [
        {k: d.get(k) for k in ("date", "startAt", "active", "isCancelled", "closed", "soldOut")}
        for d in event.get("datesCache") or []
    ]
    return roh


def _event_aufbereiten(event: dict) -> Optional[dict]:
    """Rohfelder → Führung mit Ort, Adresse, Preis, Terminen (None = keine öffentliche Führung)."""
    if not _ist_fuehrung(event) or event.get("canceled") or event.get("trashed"):
        return None
    if AUSSCHLUSS_TITEL.search(event.get("name") or ""):
        return None
    ort, adresse = _treffpunkt(event)
    termine = [
        {"datum": d.get("date"), "uhrzeit": (d.get("startAt") or "")[:5] or None}
        for d in event.get("datesCache") or []
        if d.get("date") and d.get("active", True) and not d.get("isCancelled") and not d.get("closed") and not d.get("soldOut")
    ]
    return {
        "titel": (event.get("name") or "").strip(),
        "ort": ort,
        "adresse": adresse,
        "beschreibung": _kuerzen(_text(event.get("description")) or _text(event.get("intro"))),
        "preis": _preis(event),
        "bild_url": (event.get("mainImage") or {}).get("url"),
        "termine": termine,
    }


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

async def _abrufen(client: httpx.AsyncClient, url: str) -> Optional[str]:
    for versuch in range(3):
        await asyncio.sleep(WARTEZEIT * (2 ** versuch))
        try:
            antwort = await client.get(url)
            if antwort.status_code == 429:
                logger.warning("%s: 429 bei %s – warte länger", QUELLE_NAME, url)
                continue
            antwort.raise_for_status()
            return antwort.text
        except httpx.HTTPStatusError as fehler:
            logger.error("%s: HTTP %s bei %s", QUELLE_NAME, fehler.response.status_code, url)
            return None
        except httpx.HTTPError as fehler:
            logger.warning("%s: Netzwerkfehler bei %s (%s)", QUELLE_NAME, url, fehler)
    return None


def _kandidaten(sitemap: str) -> dict[str, str]:
    """/event/-URLs mit passendem Slug → neuestes lastmod."""
    ergebnis: dict[str, str] = {}
    for eintrag in re.findall(r"<url>(.*?)</url>", sitemap, flags=re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", eintrag)
        if not loc or "/event/" not in loc.group(1):
            continue
        url = html.unescape(loc.group(1).strip())
        if not KANDIDAT_MUSTER.search(url.rsplit("/event/", 1)[-1]):
            continue
        lastmod = (re.search(r"<lastmod>([^<]+)</lastmod>", eintrag) or [None, ""])[1]
        ergebnis[url] = max(ergebnis.get(url, ""), lastmod)
    return ergebnis


async def scrape() -> list[dict]:
    """
    Scrapt öffentliche Führungstermine von Visit Düsseldorf.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s Führungen", QUELLE_NAME)

    cache = _cache_laden()
    neu_geladen = 0
    sitemap_ok = False
    try:
        async with httpx.AsyncClient(headers=STANDARD_HEADERS, timeout=60, follow_redirects=True) as client:
            sitemap = await _abrufen(client, SITEMAP_URL)
            kandidaten = _kandidaten(sitemap) if sitemap else {}
            # Nur einer vollständigen Sitemap trauen (Fehlerseite mit Status 200 oder abgeschnittene
            # Antwort würde sonst den Zwischenspeicher leeren)
            sitemap_ok = bool(sitemap) and "</urlset>" in sitemap and bool(kandidaten)
            if not sitemap_ok:
                logger.error("%s: Sitemap fehlt oder ist unvollständig – nutze den Zwischenspeicher", QUELLE_NAME)
                kandidaten = {**{url: e.get("lastmod", "") for url, e in cache.items()}, **kandidaten}
            logger.info("%s: %d Kandidaten in der Sitemap", QUELLE_NAME, len(kandidaten))

            for url, lastmod in kandidaten.items():
                alt = cache.get(url)
                if alt and lastmod in (alt.get("lastmod"), alt.get("fehl_lastmod")):
                    continue  # unverändert bzw. dieser Seitenstand war schon unlesbar
                seite = await _abrufen(client, url)
                if seite is None:
                    continue  # Netzfehler: alten Stand behalten, nächster Lauf versucht erneut
                roh = _event_lesen(seite, url)
                if roh is None:
                    # Seite ohne lesbares Event-JSON: alten Stand (roh) behalten, diesen Seitenstand
                    # aber merken – erst bei neuem lastmod wird die 1,8-MB-Seite erneut geladen
                    cache[url] = {**(alt or {"lastmod": "", "roh": None}), "fehl_lastmod": lastmod}
                    continue
                cache[url] = {"lastmod": lastmod, "roh": roh}
                neu_geladen += 1
                if neu_geladen % 10 == 0:
                    _cache_speichern(cache)
    except Exception as fehler:
        logger.error("%s: Abruf abgebrochen (%s) – nutze Zwischenspeicher", QUELLE_NAME, fehler)
        sitemap_ok = False

    # Seiten, die nicht mehr in der (vollständigen) Sitemap stehen, vergessen
    if sitemap_ok:
        cache = {url: eintrag for url, eintrag in cache.items() if url in kandidaten}
    _cache_speichern(cache)

    # Termine im Zeitfenster sammeln
    roh: list[tuple[str, dict, dict]] = []
    fuehrungen = 0
    for url, eintrag in cache.items():
        event = _event_aufbereiten(eintrag["roh"]) if eintrag.get("roh") else None
        if not event or not event.get("titel"):
            continue
        fuehrungen += 1
        for termin in event["termine"]:
            try:
                tag = date.fromisoformat(termin["datum"])
            except (TypeError, ValueError):
                continue
            if heute <= tag <= enddatum:
                roh.append((url, event, termin))

    # Gleiche Führung kann auf mehreren Seiten stehen → über Titel + Termin entdoppeln.
    # Mehrere Uhrzeiten am selben Tag bleiben einzelne Events (Website: „Diverse Uhrzeiten“).
    gesehen = set()
    events = []
    for url, event, termin in sorted(roh, key=lambda r: (r[2]["datum"], r[2]["uhrzeit"] or "")):
        schluessel = (event["titel"].lower(), termin["datum"], termin["uhrzeit"])
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        events.append({
            "titel": event["titel"],
            "datum": termin["datum"],
            "uhrzeit": termin["uhrzeit"],
            "ort": event["ort"],
            "adresse": event["adresse"],
            "kategorie": KATEGORIE,
            "beschreibung": event["beschreibung"],
            "preis": event["preis"],
            "quelle_name": QUELLE_NAME,
            "quelle_url": url,
            "bild_url": event["bild_url"],
            "bild_generiert": False,
            "post_typ": "feed",
            "instagram_caption": None,
            "instagram_location_id": None,
            "status": "neu",
        })

    logger.info(
        "%s Führungen: %d Seiten neu geladen, %d Führungen bekannt, %d Termine bis %s",
        QUELLE_NAME, neu_geladen, fuehrungen, len(events), enddatum.isoformat(),
    )
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ergebnis = asyncio.run(scrape())
    print(json.dumps(ergebnis[:4], ensure_ascii=False, indent=2))
    print("Führungen:", sorted({e["titel"].split(" (")[0] for e in ergebnis}))
    print(f"… insgesamt {len(ergebnis)} Termine")
