"""
toubiz_lesen.py – DiesDasDüsseldorf
Liest die Visit-Düsseldorf-Eventseiten der Weihnachtsmärkte und erzeugt einen ENTWURF der Saisondaten
(Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, Abschnitt 3.2). Schreibt nichts in die Datenbank.

Jede /event/-Seite enthält das komplette Toubiz-Event als JSON im Attribut data-tb-detail-event (robots.txt erlaubt /event/).
Daraus: Termine (dates[] mit startAt/endAt), Geo, Adresse, freier Eintritt, Text (nur intern als Beleg).

Ergebnis:
  data/weihnachtsmaerkte/toubiz.json               Zwischenspeicher (gitignored)
  data/weihnachtsmaerkte/saison-2026-entwurf.csv   Entwurf je Markt: von, bis, zeiten, sonder, Lücken, Geo, Adresse
  Log: Abweichungen gegen data/weihnachtsmaerkte/saison-2026.csv (geänderte Zeiten der Veranstalter erkennen)

Lücken (Tage ohne Termin, deren Wochentag sonst geöffnet ist) werden NIE als „zu“ geschrieben – nur als Hinweis.

Nutzung:
  python -m scraper.weihnachtsmaerkte.toubiz_lesen            # alle Märkte mit toubiz_url aus maerkte.csv
  python -m scraper.weihnachtsmaerkte.toubiz_lesen --nur winter-village,bilk-arcaden
  python -m scraper.weihnachtsmaerkte.toubiz_lesen --cache    # nichts laden, nur aus dem Zwischenspeicher auswerten
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scraper.utils.http_client import STANDARD_HEADERS  # noqa: E402
from scraper.weihnachtsmaerkte.zeiten import (  # noqa: E402
    ZeitFehler, aus_terminen, kurzschrift, sonder_kurzschrift, sonder_lesen, zeiten_lesen,
)

logger = logging.getLogger(__name__)

DATEN = Path(__file__).resolve().parents[2] / "data" / "weihnachtsmaerkte"
MAERKTE_CSV = DATEN / "maerkte.csv"
SAISON_CSV = DATEN / "saison-2026.csv"
ENTWURF_CSV = DATEN / "saison-2026-entwurf.csv"
CACHE = DATEN / "toubiz.json"
WARTEZEIT = 2.5  # Sekunden zwischen Abrufen derselben Domain (Projektregel ≥ 2 s)
ERLAUBTE_DOMAIN = "https://www.visitduesseldorf.de/"


# ---------------------------------------------------------------------------
# Auswertung (rein)
# ---------------------------------------------------------------------------

def json_aus_seite(seite: str) -> dict | None:
    """Toubiz-Objekt aus dem HTML (Event: data-tb-detail-event, POI: data-tb-detail-article)."""
    for attr in ("data-tb-detail-event", "data-tb-detail-article"):
        m = re.search(attr + r"='([^']*)'", seite) or re.search(attr + r'="([^"]*)"', seite)
        if m:
            try:
                return json.loads(html.unescape(m.group(1)))
            except json.JSONDecodeError:
                return None
    return None


def _text(roh) -> str:
    if not roh:
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(roh)))).strip()


def roh_auszug(obj: dict) -> dict:
    """Nur die Felder, die der Entwurf braucht (der Zwischenspeicher bleibt klein)."""
    adresse = ((obj.get("locationData") or {}).get("address")) or ((obj.get("location") or {}).get("address")) or {}
    termine = []
    for d in obj.get("dates") or obj.get("datesCache") or []:
        if not d.get("date") or not d.get("active", True) or d.get("isCancelled"):
            continue
        # Ausdrücklich geschlossener Tag ist ein Beleg für „zu“ (Plan 3.2) – anders als ein fehlender Tag (nur Hinweis)
        if d.get("closed"):
            termine.append({"datum": d["date"], "geschlossen": True})
            continue
        termine.append({"datum": d["date"], "von": (d.get("startAt") or "")[:5], "bis": (d.get("endAt") or "")[:5],
                        "hinweis": _text(d.get("additionalInformation"))})
    return {
        "name": obj.get("name"),
        "updatedAt": obj.get("updatedAt"),
        "geo": obj.get("geocoordinates") or ((obj.get("location") or {}).get("geocoordinates")),
        "adresse": {k: adresse.get(k) for k in ("name", "street", "streetNumber", "zip", "city")},
        "frei": (obj.get("price") or {}).get("freeEntry"),
        "termine": termine,
        "intro": _text(obj.get("intro"))[:1500],
        "beschreibung": _text(obj.get("description"))[:4000],
        "canceled": obj.get("canceled"),
    }


def adresse_text(a: dict) -> str:
    strasse = " ".join(x for x in (a.get("street"), a.get("streetNumber")) if x).strip()
    ort = " ".join(x for x in (a.get("zip"), a.get("city")) if x).strip()
    return ", ".join(x for x in (a.get("name") if a.get("name") and a.get("name") != strasse else None, strasse, ort) if x)


def entwurf_zeile(schluessel: str, url: str, roh: dict) -> dict:
    abgeleitet = aus_terminen(roh.get("termine") or [])
    geo = roh.get("geo") or {}
    hinweise = sorted({t["hinweis"] for t in roh.get("termine") or [] if t.get("hinweis")})
    return {
        "schluessel": schluessel,
        "von": abgeleitet["von"] or "",
        "bis": abgeleitet["bis"] or "",
        "zeiten": kurzschrift(abgeleitet["zeiten"]),
        "sonder": sonder_kurzschrift(abgeleitet["sonder"]),
        "luecken": " ".join(abgeleitet["luecken"]),
        "termine": sum(1 for t in roh.get("termine") or [] if not t.get("geschlossen")),
        "lat": geo.get("latitude") or "",
        "lng": geo.get("longitude") or "",
        "adresse": adresse_text(roh.get("adresse") or {}),
        "eintritt_frei": "" if roh.get("frei") is None else ("ja" if roh.get("frei") else "nein"),
        "termin_hinweise": " | ".join(hinweise),
        "abgesagt": "ja" if roh.get("canceled") else "",
        "toubiz_stand": roh.get("updatedAt") or "",
        "url": url,
    }


def abweichungen(entwurf: dict, gespeichert: dict) -> list[str]:
    """Vergleicht den Entwurf mit der geprüften Zeile aus saison-2026.csv (nur Felder, die beide haben)."""
    meldungen = []
    for feld in ("von", "bis"):
        if gespeichert.get(feld) and entwurf.get(feld) and gespeichert[feld] != entwurf[feld]:
            meldungen.append(f"{feld}: geprüft {gespeichert[feld]}, Toubiz jetzt {entwurf[feld]}")
    try:
        if gespeichert.get("zeiten") and entwurf.get("zeiten") and \
                zeiten_lesen(gespeichert["zeiten"]) != zeiten_lesen(entwurf["zeiten"]):
            meldungen.append(f"zeiten: geprüft „{gespeichert['zeiten']}“, Toubiz jetzt „{entwurf['zeiten']}“")
        if entwurf.get("sonder"):
            geprueft = {s["datum"]: s for s in sonder_lesen(gespeichert.get("sonder") or "")}
            for s in sonder_lesen(entwurf["sonder"]):
                if geprueft.get(s["datum"]) != s:
                    meldungen.append(f"Sonderzeit {s['datum']} laut Toubiz {s.get('von')}-{s.get('bis')} fehlt oder weicht ab")
    except ZeitFehler as fehler:
        meldungen.append(f"Vergleich nicht möglich: {fehler}")
    return meldungen


# ---------------------------------------------------------------------------
# Ablauf
# ---------------------------------------------------------------------------

def csv_lesen(pfad: Path) -> list[dict]:
    if not pfad.exists():
        return []
    with pfad.open(encoding="utf-8", newline="") as f:
        return [{k: (v or "").strip() for k, v in z.items()} for z in csv.DictReader(f)]


def cache_laden() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def abrufen(client: httpx.Client, url: str) -> str | None:
    for versuch in range(3):
        time.sleep(WARTEZEIT * (2 ** versuch))
        try:
            antwort = client.get(url)
            if antwort.status_code == 429:
                logger.warning("429 bei %s – warte länger", url)
                continue
            antwort.raise_for_status()
            return antwort.text
        except httpx.HTTPStatusError as fehler:
            logger.error("HTTP %s bei %s", fehler.response.status_code, url)
            return None
        except httpx.HTTPError as fehler:
            logger.warning("Netzwerkfehler bei %s (%s)", url, fehler)
    return None


def main() -> None:
    p = argparse.ArgumentParser(description="Visit-Düsseldorf-Termine der Weihnachtsmärkte lesen (nur Entwurf)")
    p.add_argument("--nur", help="kommagetrennte Schlüssel")
    p.add_argument("--cache", action="store_true", help="nichts laden, nur den Zwischenspeicher auswerten")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    maerkte = [m for m in csv_lesen(MAERKTE_CSV) if m.get("toubiz_url")]
    if args.nur:
        nur = {s.strip() for s in args.nur.split(",")}
        maerkte = [m for m in maerkte if m["schluessel"] in nur]
    if not maerkte:
        logger.error("Keine Märkte mit toubiz_url in %s", MAERKTE_CSV)
        sys.exit(1)

    cache = cache_laden()
    if not args.cache:
        with httpx.Client(headers=STANDARD_HEADERS, timeout=60, follow_redirects=True) as client:
            for m in maerkte:
                url = m["toubiz_url"]
                if not url.startswith(ERLAUBTE_DOMAIN):
                    logger.error("%s: nur visitduesseldorf.de wird gelesen, nicht %s", m["schluessel"], url)
                    continue
                seite = abrufen(client, url)
                obj = json_aus_seite(seite) if seite else None
                if not obj:
                    logger.warning("%s: kein Toubiz-JSON gelesen – Zwischenspeicher bleibt", m["schluessel"])
                    continue
                cache[m["schluessel"]] = {"url": url, "gelesen": datetime.now().isoformat(timespec="seconds"), **roh_auszug(obj)}
                logger.info("%s: %d Termine gelesen (inkl. geschlossener Tage)", m["schluessel"], len(cache[m["schluessel"]]["termine"]))
        DATEN.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

    gespeichert = {z["schluessel"]: z for z in csv_lesen(SAISON_CSV)}
    zeilen = []
    for m in maerkte:
        roh = cache.get(m["schluessel"])
        if not roh:
            continue
        zeile = entwurf_zeile(m["schluessel"], roh["url"], roh)
        zeilen.append(zeile)
        if zeile["luecken"]:
            logger.info("%s: Lücken im Terminplan (kein Beleg für „zu“): %s", m["schluessel"], zeile["luecken"])
        for meldung in abweichungen(zeile, gespeichert.get(m["schluessel"], {})):
            logger.warning("%s: ABWEICHUNG %s", m["schluessel"], meldung)
    if zeilen:
        with ENTWURF_CSV.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(zeilen[0].keys()))
            w.writeheader()
            w.writerows(zeilen)
        logger.info("Entwurf geschrieben: %s (%d Märkte)", ENTWURF_CSV, len(zeilen))


if __name__ == "__main__":
    main()
