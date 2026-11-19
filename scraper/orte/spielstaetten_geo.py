"""
spielstaetten_geo.py – DiesDasDüsseldorf
Geo-Prüfdatei für die freigegebenen Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.12, Schritt 2).

Ablauf – jeder Schritt einzeln aufrufen, nichts wird automatisch in die Datenbank geschrieben:
  1. --kosten   Anzahl der Google-Suchen und Kostenhinweis (vor jedem Google-Lauf nennen).
  2. --google   Places Text Search je Haus → data/spielstaetten/geo_pruefung.csv (lokal, gitignored: Google-Inhalte).
                Gespeichert wird später nur die place_id; Google-Koordinaten werden gar nicht erst abgefragt.
  3. Auftraggeber trägt in der Prüfdatei „adresse_bestaetigt“ (Adresse laut Website des Hauses) und
     „bestaetigung“ = ja ein.
  4. --osm      Koordinaten aus der bestätigten Adresse über OpenStreetMap Nominatim (mind. 2 s Pause, Backoff bei
                429, User-Agent mit Projektnamen). Nur Adressen mit PLZ in Düsseldorf, Neuss, Ratingen.
  5. --sql      database/orte_spielstaetten_geo_<datum>.sql: Adresse, Stadtteil (nur aus der PLZ), Koordinaten (OSM),
                place_id. Säle werden nicht geokodiert – sie erben vom Haus (Plan 3.6).

Aufruf im Repo-Stamm:
    python -m scraper.orte.spielstaetten_geo --kosten
"""
import argparse
import csv
import json
import logging
import re
import time
from datetime import date
from pathlib import Path

import httpx

from pipeline.gebiet import PLZ_BEREICHE
from pipeline.stadtteil_mapper import PLZ_STADTTEIL
from scraper.orte.spielstaetten_kandidaten import ZIEL as KANDIDATEN

logger = logging.getLogger(__name__)

PRUEFDATEI = Path("data/spielstaetten/geo_pruefung.csv")
SPALTEN = ["slug", "name", "zeile_typ", "suchbegriff", "event_adresse", "google_name", "google_adresse", "place_id",
           "adresse_bestaetigt", "bestaetigung", "osm_lat", "osm_lon", "osm_treffer"]
GEOKODIEREN = ("haus", "standort", "filiale")   # Säle erben vom Haus (Plan 3.6)
NOMINATIM = "https://nominatim.openstreetmap.org/search"
NOMINATIM_UA = "DiesDasDuesseldorf-Ortsseiten/1.0 (+https://diesdas.events)"  # Nominatim verlangt einen erkennbaren UA
PAUSE_S = 2.0   # Projektregel (CLAUDE.md), strenger als Nominatim (1/s)
GOOGLE_FELDER = "places.id,places.displayName,places.formattedAddress"  # keine Koordinaten (Google-Bedingungen)


def plz(adresse: str | None) -> str:
    m = re.search(r"\b(4\d{4})\b", adresse or "")
    return m.group(1) if m else ""


def plz_im_gebiet(adresse: str | None) -> bool:
    p = plz(adresse)
    return bool(p) and any(a <= int(p) <= b for a, b in PLZ_BEREICHE)


def stadt_aus_plz(adresse: str | None) -> str:
    p = plz(adresse)
    if not p:
        return ""
    n = int(p)
    if 40210 <= n <= 40629:
        return "Düsseldorf"
    if 41460 <= n <= 41472:
        return "Neuss"
    if 40878 <= n <= 40885:
        return "Ratingen"
    return ""


def stadtteil_aus_plz(adresse: str | None) -> str:
    """Nur über die PLZ (Plan 3.12), nie über den Namen; Neuss und Ratingen ohne Stadtteil."""
    return PLZ_STADTTEIL.get(plz(adresse), "")


def freigegebene_haeuser() -> list[dict]:
    with KANDIDATEN.open(encoding="utf-8-sig", newline="") as f:
        return [z for z in csv.DictReader(f, delimiter=";")
                if (z.get("entscheidung") or "").strip().lower() == "ja" and z["zeile_typ"] in GEOKODIEREN
                and z.get("slug_vorschlag")
                # nur importierte Zeilen: ohne zulässige Art lehnt der Import ab (Plan 3.1)
                and (z.get("art_korrigiert") or "").strip() not in ("", "Sonstiges")]


def _lesen() -> list[dict]:
    if not PRUEFDATEI.exists():
        return []
    with PRUEFDATEI.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _schreiben(zeilen: list[dict]) -> None:
    PRUEFDATEI.parent.mkdir(parents=True, exist_ok=True)
    with PRUEFDATEI.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SPALTEN, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(zeilen)


def kosten() -> int:
    offen = [z for z in freigegebene_haeuser() if z["slug_vorschlag"] not in {p["slug"] for p in _lesen() if p.get("place_id")}]
    print(f"Google Places Text Search (Felder: {GOOGLE_FELDER}): {len(offen)} Anfragen.")
    print("SKU „Text Search Pro“: laut Google-Preisliste (Stand 2025) 5.000 Anfragen je Monat frei, darüber ca. 32 $ "
          "je 1.000 – vor dem Lauf auf der aktuellen Preisseite prüfen und mit dem Monatsverbrauch abgleichen.")
    return len(offen)


def google_suchen() -> int:
    from config import DUESSELDORF_LAT, DUESSELDORF_LNG, GOOGLE_PLACES_API_KEY

    bisher = {p["slug"]: p for p in _lesen()}
    zeilen = []
    neu = 0
    for z in freigegebene_haeuser():
        slug = z["slug_vorschlag"]
        p = bisher.get(slug) or {"slug": slug, "name": z.get("name_korrigiert") or z["haus"], "zeile_typ": z["zeile_typ"],
                                 "event_adresse": z.get("adresse") or ""}
        if not p.get("place_id"):
            p["suchbegriff"] = f"{p['name']}, Düsseldorf"
            try:
                antwort = httpx.post(
                    "https://places.googleapis.com/v1/places:searchText",
                    headers={"Content-Type": "application/json", "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
                             "X-Goog-FieldMask": GOOGLE_FELDER},
                    json={"textQuery": p["suchbegriff"], "languageCode": "de", "pageSize": 1,
                          "locationBias": {"circle": {"center": {"latitude": DUESSELDORF_LAT,
                                                                 "longitude": DUESSELDORF_LNG}, "radius": 20000.0}}},
                    timeout=30)
                antwort.raise_for_status()
                treffer = (antwort.json().get("places") or [{}])[0]
                p.update(google_name=(treffer.get("displayName") or {}).get("text", ""),
                         google_adresse=treffer.get("formattedAddress", ""), place_id=treffer.get("id", ""))
                neu += 1
            except Exception as e:
                logger.error("Google-Suche für „%s“ fehlgeschlagen: %s", p["name"], e)
            time.sleep(PAUSE_S)
        zeilen.append(p)
    _schreiben(zeilen)
    logger.info("Geo: %d Google-Suchen, Prüfdatei %s (%d Zeilen)", neu, PRUEFDATEI, len(zeilen))
    return neu


def osm_koordinaten() -> int:
    zeilen = _lesen()
    neu = 0
    for p in zeilen:
        adresse = (p.get("adresse_bestaetigt") or "").strip()
        if (p.get("bestaetigung") or "").strip().lower() != "ja" or not adresse or p.get("osm_lat"):
            continue
        if not plz_im_gebiet(adresse):
            p["osm_treffer"] = "keine PLZ in Düsseldorf/Neuss/Ratingen – keine Koordinaten (Plan 3.12)"
            continue
        warte = PAUSE_S
        for _ in range(4):
            try:
                antwort = httpx.get(NOMINATIM, params={"q": adresse, "format": "jsonv2", "limit": 1, "countrycodes": "de"},
                                    headers={"User-Agent": NOMINATIM_UA}, timeout=30)
                if antwort.status_code == 429:
                    time.sleep(warte)
                    warte *= 2
                    continue
                antwort.raise_for_status()
                treffer = (antwort.json() or [{}])[0]
                if treffer.get("lat"):
                    p.update(osm_lat=treffer["lat"], osm_lon=treffer["lon"], osm_treffer=treffer.get("display_name", ""))
                    neu += 1
                else:
                    p["osm_treffer"] = "kein Treffer"
                break
            except Exception as e:
                logger.error("Nominatim für „%s“ fehlgeschlagen: %s", adresse, e)
                break
        time.sleep(PAUSE_S)
    _schreiben(zeilen)
    logger.info("Geo: %d Koordinaten aus OpenStreetMap", neu)
    return neu


def _sql_text(wert: str | None) -> str:
    return "NULL" if not wert else "'" + wert.replace("'", "''") + "'"


def sql_text(zeilen: list[dict]) -> str:
    teile = [
        "-- Adressen, Stadtteile, Koordinaten der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.12)",
        f"-- Erzeugt am {date.today().isoformat()} von `python -m scraper.orte.spielstaetten_geo --sql` aus der lokalen",
        "-- Prüfdatei (nur Zeilen mit bestaetigung = ja). Koordinaten von OpenStreetMap (© OpenStreetMap-Mitwirkende),",
        "-- von Google nur die place_id. Stadtteil nur aus der PLZ. Wiederholbar.", "", "BEGIN;", ""]
    for p in zeilen:
        adresse = (p.get("adresse_bestaetigt") or "").strip()
        if (p.get("bestaetigung") or "").strip().lower() != "ja" or not adresse:
            continue
        koordinaten = plz_im_gebiet(adresse) and p.get("osm_lat") and p.get("osm_lon")
        profil = {"adresse_bestaetigt": {"datum": date.today().isoformat(), "quelle": "Website des Hauses"},
                  "geo_quelle": "osm" if koordinaten else None, "stadt": stadt_aus_plz(adresse) or None}
        teile.append(
            "UPDATE public.orte SET "
            f"adresse = {_sql_text(adresse)}, stadtteil = {_sql_text(stadtteil_aus_plz(adresse))}, "
            f"latitude = {p['osm_lat'] if koordinaten else 'NULL'}, longitude = {p['osm_lon'] if koordinaten else 'NULL'}, "
            f"google_place_id = COALESCE({_sql_text(p.get('place_id'))}, google_place_id), "
            "extras = jsonb_set(extras, '{spielstaette}', COALESCE(extras->'spielstaette', '{}'::jsonb) || "
            f"{_sql_text(json.dumps(profil, ensure_ascii=False))}::jsonb) "
            f"WHERE slug = {_sql_text(p['slug'])} AND typ = 'spielstaette';")
    teile += ["", "COMMIT;", "",
              "-- Kontrolle: Spielstätten mit bestätigter Adresse, mit Koordinaten",
              "SELECT count(*) FILTER (WHERE extras->'spielstaette' ? 'adresse_bestaetigt') AS bestaetigt,",
              "       count(latitude) AS mit_koordinaten FROM public.orte WHERE typ = 'spielstaette';"]
    return "\n".join(teile) + "\n"


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
    except ImportError:
        pass
    parser = argparse.ArgumentParser(description="Geo-Prüfdatei für Ortsseiten")
    gruppe = parser.add_mutually_exclusive_group(required=True)
    gruppe.add_argument("--kosten", action="store_true")
    gruppe.add_argument("--google", action="store_true")
    gruppe.add_argument("--osm", action="store_true")
    gruppe.add_argument("--sql", action="store_true")
    parser.add_argument("--ausgabe", default=f"database/orte_spielstaetten_geo_{date.today().isoformat()}.sql")
    args = parser.parse_args()
    if args.kosten:
        kosten()
    elif args.google:
        google_suchen()
    elif args.osm:
        osm_koordinaten()
    else:
        Path(args.ausgabe).write_text(sql_text(_lesen()), encoding="utf-8")
        logger.info("Geo-SQL geschrieben: %s", args.ausgabe)


if __name__ == "__main__":
    main()
