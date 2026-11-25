"""
google_abgleich.py – DiesDasDüsseldorf
Google-Abgleich für den Guide „Spielplätze“ (Plan: docs/plan-spielplaetze-2026-11-12.md, Abschnitt 4.4).
Runde 1 = Plätze aus 4.3; Runde 2 (Auftraggeber 16.11.2026) = alle übrigen aktiven Plätze ohne Foto, damit nicht
269 von 347 Plätzen nur die Illustration zeigen. Runde 3 (Auftraggeber 25.11.2026) = alle aktiven Plätze, die danach
noch ohne Foto sind: Umkreissuche mit 200 m plus Textsuche nach dem Namen (Google-Punkt liegt teils weiter weg);
schreibt nichts in die Datenbank, nur Kandidaten und Fotos. Jede Runde hat eigene Kandidaten-/Prüfdateien.

Je Platz eine Umkreissuche (80 m, Typ playground) über die Places API (New). Treffer nur bei Namensähnlichkeit oder
einzigem Treffer, sonst Prüf-CSV. Bewertung nur intern (extras.spielplatz.google, für den Score). Foto-Kandidaten bleiben
lokal (data/spielplaetze/google/), bis die Sichtung sie freigibt; das Foto setzt dann nur die Foto-SQL (Auftraggeber).

Nutzung:
  python -m scraper.spielplaetze.google_abgleich suchen [--runde 2|3] --dry-run     # nennt Plätze und Kosten, fragt nichts ab
  python -m scraper.spielplaetze.google_abgleich suchen [--runde 2]               # Umkreissuche (kostet), schreibt google + Kandidaten
  python -m scraper.spielplaetze.google_abgleich fotos [--runde 2] [--dry-run]    # lädt Vorschaubilder der Kandidaten (kostet)
  python -m scraper.spielplaetze.google_abgleich sql [--runde 2] --sichtung DATEI # Foto-SQL aus der Sichtung erzeugen
"""
import argparse
import csv
import json
import logging
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logger = logging.getLogger(__name__)

_WURZEL = Path(__file__).resolve().parents[2]
_DATEN = _WURZEL / "data" / "spielplaetze"
CACHE = _DATEN / "google"            # Rohantworten je Platz (Google-Inhalte, nie veröffentlicht, gitignored)
FOTOS = _DATEN / "fotos"             # Vorschaubilder für die Sichtung (gitignored)
KANDIDATEN = _DATEN / "google_kandidaten.json"
PRUEF_CSV = _DATEN / "google_pruefung.csv"


def dateien(runde: int) -> tuple[Path, Path]:
    """Kandidaten- und Prüfdatei je Runde (Runde 1 behält ihre bisherigen Namen)."""
    if runde == 1:
        return KANDIDATEN, PRUEF_CSV
    return _DATEN / f"google_kandidaten_runde{runde}.json", _DATEN / f"google_pruefung_runde{runde}.csv"

API_BASE = "https://places.googleapis.com/v1"
RADIUS_M = 80.0
RADIUS_RUNDE_3 = 200.0     # Runde 3: größerer Umkreis
TEXT_MAX_M = 400.0         # Runde 3: Treffer der Textsuche nur bis zu diesem Abstand zum Stadt-Punkt
CACHE_RUNDE_3 = _DATEN / "google_runde3"
FOTOS_RUNDE_3 = _DATEN / "fotos_runde3"
PREIS_SUCHE = 0.035    # USD je Umkreissuche mit Bewertung (Enterprise-Felder), wie flaechensuche.py
PREIS_FOTO = 0.007     # USD je Foto (Place Photo)
MAX_FOTOS = 10
VORSCHAU_BREITE = 640
GROESSE_RUNDE_1 = 3000.0
FELDER = "places.id,places.displayName,places.location,places.rating,places.userRatingCount,places.photos,places.googleMapsUri,places.primaryType"

# Wörter, die in fast jedem Spielplatznamen stehen und nichts unterscheiden
_FUELLWOERTER = {"spielplatz", "kinderspielplatz", "wasserspielplatz", "waldspielplatz", "abenteuerspielplatz",
                 "bauspielplatz", "spielplaetze", "playground", "duesseldorf", "strasse", "str", "weg", "platz",
                 "park", "der", "die", "das", "dem", "den", "am", "an", "im", "in", "auf", "und", "fuer", "zum", "zur"}


# ---------------------------------------------------------------------------
# Reine Funktionen
# ---------------------------------------------------------------------------

def ist_runde_1(zeile: dict) -> bool:
    """Runde 1 (4.3): alle Wasser, Wald und Abenteuer, Kinderspielplätze mit summierter Größe ≥ 3.000 m²; nicht ausgeschlossene."""
    sp = (zeile.get("extras") or {}).get("spielplatz") or {}
    if sp.get("ausgeschlossen"):
        return False
    if sp.get("typ") in ("wasser", "wald", "abenteuer"):
        return True
    return sp.get("typ") == "kinder" and (sp.get("groesse_m2") or 0) >= GROESSE_RUNDE_1


def ist_runde_2(zeile: dict) -> bool:
    """Runde 2: aktive, nicht ausgeschlossene Plätze außerhalb von Runde 1, die noch kein Foto haben."""
    sp = (zeile.get("extras") or {}).get("spielplatz") or {}
    extras = zeile.get("extras") or {}
    if not zeile.get("aktiv") or sp.get("ausgeschlossen") or ist_runde_1(zeile):
        return False
    return not extras.get("google_foto") and not zeile.get("bild_url")


def ist_runde_3(zeile: dict) -> bool:
    """Runde 3: alle aktiven, nicht ausgeschlossenen Plätze ohne Foto (egal ob Runde 1 oder 2)."""
    sp = (zeile.get("extras") or {}).get("spielplatz") or {}
    extras = zeile.get("extras") or {}
    if not zeile.get("aktiv") or sp.get("ausgeschlossen"):
        return False
    return not extras.get("google_foto") and not zeile.get("bild_url")


def cache_ordner(runde: int) -> Path:
    return CACHE_RUNDE_3 if runde == 3 else CACHE


def foto_ordner(runde: int) -> Path:
    """Runde 3 in eigenem Ordner: dieselben Plätze können schon Fotos aus früheren Runden unter gleichem Index haben."""
    return FOTOS_RUNDE_3 if runde == 3 else FOTOS


def _abstand_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def zusammenfuehren(lat: float, lon: float, umkreis: list[dict], text: list[dict]) -> list[dict]:
    """Runde 3: Umkreis- und Textsuche ohne Doppelte; Textsuche nur bis TEXT_MAX_M vom Stadt-Punkt."""
    aus, ids = [], set()
    for o in umkreis:
        if o.get("id") not in ids:
            ids.add(o.get("id"))
            aus.append(o)
    for o in text:
        ort = o.get("location") or {}
        if o.get("id") in ids or ort.get("latitude") is None:
            continue
        if _abstand_m(lat, lon, ort["latitude"], ort["longitude"]) > TEXT_MAX_M:
            continue
        ids.add(o.get("id"))
        aus.append(o)
    return aus


NAECHSTER_MAX_M = 60.0     # Runde 3: bei Mehrdeutigkeit der nächste Google-Spielplatz, wenn so nah am Stadt-Punkt


def naechster_treffer(lat: float, lon: float, orte: list[dict]) -> dict | None:
    """Runde 3: nächster Google-Ort mit Koordinaten, wenn höchstens NAECHSTER_MAX_M entfernt, sonst None."""
    mit_lage = [(_abstand_m(lat, lon, o["location"]["latitude"], o["location"]["longitude"]), o)
                for o in orte if (o.get("location") or {}).get("latitude") is not None]
    if not mit_lage:
        return None
    abstand, ort = min(mit_lage, key=lambda x: x[0])
    return ort if abstand <= NAECHSTER_MAX_M else None


def woerter(text: str) -> set[str]:
    """Unterscheidende Wörter eines Namens (klein, ohne Umlaute, ohne Füllwörter, ≥ 3 Zeichen)."""
    t = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"strasse\b", " strasse", t)  # „Hofgartenstraße“ → „hofgarten“
    return {w for w in re.split(r"[^a-z0-9]+", t) if len(w) >= 3 and w not in _FUELLWOERTER}


def treffer_waehlen(name: str, orte: list[dict]) -> tuple[dict | None, str]:
    """
    4.4: Treffer nur bei Namensähnlichkeit (mindestens ein gemeinsames unterscheidendes Wort) oder einzigem Treffer.
    Mehrere ähnliche: der mit den meisten gemeinsamen Wörtern, wenn eindeutig. Rückgabe (Treffer, Art).
    """
    if not orte:
        return None, "kein_treffer"
    eigene = woerter(name)
    bewertet = sorted(((len(eigene & woerter((o.get("displayName") or {}).get("text", ""))), o) for o in orte),
                      key=lambda x: -x[0])
    if bewertet[0][0] > 0:
        beste = [o for n, o in bewertet if n == bewertet[0][0]]
        if len(beste) == 1:
            return beste[0], "name"
        # Gleichstand: zuerst das passende Typwort (Wasser-/Wald-/Abenteuer- oder einfacher Spielplatz) …
        typ = _typwort(name)
        passend = [o for o in beste if _typwort((o.get("displayName") or {}).get("text", "")) == typ]
        if len(passend) == 1:
            return passend[0], "name_typ"
        # … dann bei gleichem Namen (Google führt den Ort doppelt) der Eintrag mit den meisten Bewertungen
        namen = {_norm((o.get("displayName") or {}).get("text", "")) for o in beste}
        if len(namen) == 1:
            return max(beste, key=lambda o: o.get("userRatingCount") or 0), "name_doppelt"
    if len(orte) == 1:
        return orte[0], "einziger"
    return None, "mehrdeutig"


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _typwort(text: str) -> str:
    t = text.lower()
    for wort in ("wasserspielplatz", "waldspielplatz", "abenteuerspielplatz"):
        if wort in t:
            return wort
    return "spielplatz"


def foto_kandidaten(ort: dict) -> list[dict]:
    """Bis zu 10 Fotos mit Ressourcenname, Größe und Urheber (wie _foto_info in google_places.py)."""
    aus = []
    for f in (ort.get("photos") or [])[:MAX_FOTOS]:
        autor = (f.get("authorAttributions") or [{}])[0]
        aus.append({"name": f.get("name"), "breite": f.get("widthPx"), "hoehe": f.get("heightPx"),
                    "autor": autor.get("displayName"), "autor_url": autor.get("uri")})
    return [f for f in aus if f["name"]]


def sql_aus_sichtung(sichtung: dict, kandidaten: dict, namen: dict, heute: str) -> str:
    """
    Foto-SQL wie bei den Club-Fotos (4.4): google_foto {name, breite, hoehe, autor, autor_url}, bild_attribution = autor,
    foto_manuell = Datum der Sichtung, foto_version 1 wenn leer sonst +1, bild_url bleibt null.
    sichtung: {zeilen_id: {"foto": Index oder None, "grund": Text}}.
    """
    zeilen = [f"-- Spielplatz-Fotos (Sichtung {heute}) – im Supabase SQL-Editor ausführen.",
              "-- Nur Fotos ohne erkennbare Personen. foto_manuell schützt die Auswahl vor späteren Google-Läufen.", ""]
    for zid in sorted(sichtung, key=lambda z: namen.get(z, "")):
        wahl = sichtung[zid]
        version = "'foto_version', COALESCE((extras->>'foto_version')::int + 1, 1)"
        if wahl.get("foto") is None:
            zeilen.append(f"-- {namen.get(zid, zid)}: kein Foto – {wahl.get('grund', '')}")
            continue
        f = kandidaten[zid][wahl["foto"]]
        foto = json.dumps({k: f[k] for k in ("name", "breite", "hoehe", "autor", "autor_url")}, ensure_ascii=False)
        autor = (f.get("autor") or "Google").replace("'", "''")
        zeilen.append(f"-- {namen.get(zid, zid)}: Foto von {f.get('autor') or 'Google'} – {wahl.get('grund', '')}")
        zeilen.append(
            f"UPDATE public.orte SET bild_attribution = '{autor}', bild_url = NULL, extras = extras || jsonb_build_object("
            f"'google_foto', '{foto.replace(chr(39), chr(39) * 2)}'::jsonb, 'foto_manuell', '{heute}', "
            f"{version}) WHERE id = '{zid}' AND typ = 'spielplatz';")
    return "\n".join(zeilen) + "\n"


# ---------------------------------------------------------------------------
# Google-Abfragen (mit Zwischenspeicher je Platz)
# ---------------------------------------------------------------------------

def _headers(felder: str) -> dict:
    from config import GOOGLE_PLACES_API_KEY

    return {"Content-Type": "application/json", "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY or "", "X-Goog-FieldMask": felder}


def umkreissuche(lat: float, lon: float, radius: float = RADIUS_M) -> list[dict]:
    body = {"includedTypes": ["playground"], "maxResultCount": 20, "languageCode": "de", "regionCode": "DE",
            "locationRestriction": {"circle": {"center": {"latitude": lat, "longitude": lon}, "radius": radius}}}
    time.sleep(0.5)
    for versuch in range(3):
        try:
            r = httpx.post(f"{API_BASE}/places:searchNearby", json=body, headers=_headers(FELDER), timeout=30)
            if r.status_code == 429:
                time.sleep(5 * 2 ** versuch)
                continue
            r.raise_for_status()
            return r.json().get("places") or []
        except httpx.HTTPError as e:
            if versuch == 2:
                raise
            logger.warning("Umkreissuche fehlgeschlagen (%s) – neuer Versuch", e)
            time.sleep(5 * 2 ** versuch)
    raise RuntimeError("Umkreissuche: zu viele Anfragen (429)")


def textsuche(name: str, lat: float, lon: float) -> list[dict]:
    """Runde 3: Textsuche nach dem Spielplatznamen, auf den Stadt-Punkt ausgerichtet (Places API New, searchText)."""
    body = {"textQuery": f"{name} Düsseldorf", "maxResultCount": 10, "languageCode": "de", "regionCode": "DE",
            "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lon}, "radius": 500.0}}}
    time.sleep(0.5)
    for versuch in range(3):
        try:
            r = httpx.post(f"{API_BASE}/places:searchText", json=body, headers=_headers(FELDER), timeout=30)
            if r.status_code == 429:
                time.sleep(5 * 2 ** versuch)
                continue
            r.raise_for_status()
            return r.json().get("places") or []
        except httpx.HTTPError as e:
            if versuch == 2:
                raise
            logger.warning("Textsuche fehlgeschlagen (%s) – neuer Versuch", e)
            time.sleep(5 * 2 ** versuch)
    raise RuntimeError("Textsuche: zu viele Anfragen (429)")


def plaetze_laden(db, runde: int = 1) -> list[dict]:
    from scraper.orte.google_places import alle_zeilen

    zeilen = alle_zeilen(db, "orte", "id, name, slug, stadtteil, latitude, longitude, aktiv, bild_url, extras",
                         lambda q: q.eq("typ", "spielplatz"))
    auswahl = {1: ist_runde_1, 2: ist_runde_2, 3: ist_runde_3}[runde]
    return sorted([z for z in zeilen if auswahl(z) and z.get("latitude") is not None], key=lambda z: z["name"])


def runde_1_laden(db) -> list[dict]:
    return plaetze_laden(db, 1)


def suchen(dry_run: bool, runde: int = 1) -> None:
    from database.client import get_supabase_client

    db = get_supabase_client()
    plaetze = plaetze_laden(db, runde)
    kandidaten_datei, pruef_datei = dateien(runde)
    cache = cache_ordner(runde)
    offen = [z for z in plaetze if not (cache / f"{z['id']}.json").exists()]
    je_platz = 2 if runde == 3 else 1  # Runde 3: Umkreis- und Textsuche
    logger.info("Runde %d: %d Plätze (%d städtisch, %d Abenteuer), davon %d noch ohne Abfrage → Kosten ca. %.2f $%s",
                runde, len(plaetze), sum(1 for z in plaetze if z["extras"]["spielplatz"].get("quelle") != "abenteuer"),
                sum(1 for z in plaetze if z["extras"]["spielplatz"].get("quelle") == "abenteuer"),
                len(offen), len(offen) * PREIS_SUCHE * je_platz, " [Dry-Run, keine Abfrage]" if dry_run else "")
    if dry_run:
        return
    cache.mkdir(parents=True, exist_ok=True)
    for i, z in enumerate(offen, 1):
        try:
            if runde == 3:
                umkreis = umkreissuche(z["latitude"], z["longitude"], RADIUS_RUNDE_3)
                orte = zusammenfuehren(z["latitude"], z["longitude"], umkreis, textsuche(z["name"], z["latitude"], z["longitude"]))
            else:
                orte = umkreissuche(z["latitude"], z["longitude"])
            (cache / f"{z['id']}.json").write_text(json.dumps(orte, ensure_ascii=False), encoding="utf-8")
            logger.info("[%d/%d] %s: %d Google-Orte", i, len(offen), z["name"], len(orte))
        except Exception as e:  # noqa: BLE001 – Platz überspringen, beim nächsten Lauf erneut
            logger.error("Umkreissuche für %s fehlgeschlagen: %s", z["name"], e)

    kandidaten, pruef, geschrieben = {}, [], 0
    for z in plaetze:
        datei = cache / f"{z['id']}.json"
        if not datei.exists():
            continue
        orte = json.loads(datei.read_text(encoding="utf-8"))
        if runde == 3:
            # Die Textsuche liefert auch Schulen, Parkplätze, Slackline-Anlagen – nur echte Spielplätze zählen
            orte = [o for o in orte if o.get("primaryType") == "playground"]
        treffer, art = treffer_waehlen(z["name"], orte)
        if runde == 3 and art == "mehrdeutig":
            # Runde 3: mehrere Spielplätze im größeren Umkreis → der nächste, wenn er höchstens 60 m entfernt liegt
            treffer = naechster_treffer(z["latitude"], z["longitude"], orte)
            art = "naechster" if treffer else art
        google = None
        if treffer:
            google = {"place_id": treffer["id"], "name": (treffer.get("displayName") or {}).get("text"),
                      "rating": treffer.get("rating"), "anzahl": treffer.get("userRatingCount"), "zuordnung": art}
            kandidaten[z["id"]] = foto_kandidaten(treffer)
        pruef.append({"name": z["name"], "stadtteil": z.get("stadtteil") or "", "zuordnung": art,
                      "google_name": (google or {}).get("name") or "", "rating": (google or {}).get("rating") or "",
                      "anzahl": (google or {}).get("anzahl") or "", "fotos": len(kandidaten.get(z["id"], [])),
                      "alle_google_orte": " | ".join((o.get("displayName") or {}).get("text", "") for o in orte)})
        if runde == 3:
            continue  # Runde 3 schreibt nichts in die Datenbank – das Foto setzt nur die Foto-SQL nach der Sichtung
        try:
            aktuell = (db.table("orte").select("extras").eq("id", z["id"]).execute().data or [{}])[0].get("extras") or {}
            sp = {**(aktuell.get("spielplatz") or {}), "google": google}
            db.table("orte").update({"extras": {**aktuell, "spielplatz": sp}}).eq("id", z["id"]).execute()
            geschrieben += 1
        except Exception as e:  # noqa: BLE001
            logger.error("Speichern für %s fehlgeschlagen: %s", z["name"], e)
    kandidaten_datei.write_text(json.dumps(kandidaten, ensure_ascii=False, indent=1), encoding="utf-8")
    with pruef_datei.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pruef[0].keys()) if pruef else ["name"], delimiter=";")
        w.writeheader()
        w.writerows(pruef)
    arten = {a: sum(1 for p in pruef if p["zuordnung"] == a) for a in ("name", "einziger", "naechster", "mehrdeutig", "kein_treffer")}
    logger.info("Zuordnung: %s; %d Plätze mit Foto-Kandidaten (%d Fotos); %d Zeilen geschrieben; Prüf-CSV %s",
                arten, sum(1 for k in kandidaten.values() if k), sum(len(k) for k in kandidaten.values()), geschrieben, pruef_datei)


def fotos_laden(dry_run: bool, runde: int = 1) -> None:
    """Vorschaubilder (640 px) der Kandidaten für die Sichtung laden – nur lokal, nie veröffentlicht."""
    from config import GOOGLE_PLACES_API_KEY

    kandidaten = json.loads(dateien(runde)[0].read_text(encoding="utf-8"))
    fotos = foto_ordner(runde)
    offen = [(zid, i, f) for zid, liste in kandidaten.items() for i, f in enumerate(liste)
             if not (fotos / zid / f"{i}.jpg").exists()]
    logger.info("%d Fotos zu laden → Kosten ca. %.2f $%s", len(offen), len(offen) * PREIS_FOTO,
                " [Dry-Run, nichts geladen]" if dry_run else "")
    if dry_run:
        return
    fehler = 0
    for n, (zid, i, f) in enumerate(offen, 1):
        try:
            time.sleep(0.2)
            r = httpx.get(f"{API_BASE}/{f['name']}/media", params={"maxWidthPx": VORSCHAU_BREITE},
                          headers={"X-Goog-Api-Key": GOOGLE_PLACES_API_KEY or ""}, timeout=30, follow_redirects=True)
            r.raise_for_status()
            (fotos / zid).mkdir(parents=True, exist_ok=True)
            (fotos / zid / f"{i}.jpg").write_bytes(r.content)
            if n % 50 == 0:
                logger.info("%d/%d Fotos geladen", n, len(offen))
        except Exception as e:  # noqa: BLE001
            fehler += 1
            logger.error("Foto %s/%d fehlgeschlagen: %s", zid, i, e)
    logger.info("Fotos fertig: %d geladen, %d Fehler", len(offen) - fehler, fehler)


def sql_schreiben(sichtung_datei: Path, runde: int = 1) -> None:
    from database.client import get_supabase_client

    sichtung = json.loads(sichtung_datei.read_text(encoding="utf-8"))
    kandidaten = json.loads(dateien(runde)[0].read_text(encoding="utf-8"))
    db = get_supabase_client()
    namen = {z["id"]: z["name"] for z in plaetze_laden(db, runde)}
    heute = date.today().isoformat()
    ziel = _WURZEL / "database" / (f"spielplatz_fotos_{heute}.sql" if runde == 1 else f"spielplatz_fotos_runde{runde}_{heute}.sql")
    ziel.write_text(sql_aus_sichtung(sichtung, kandidaten, namen, heute), encoding="utf-8")
    logger.info("Foto-SQL: %s (%d mit Foto, %d ohne)", ziel, sum(1 for s in sichtung.values() if s.get("foto") is not None),
                sum(1 for s in sichtung.values() if s.get("foto") is None))


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Spielplätze: Google-Abgleich (Runde 1 oder 2)")
    sub = parser.add_subparsers(dest="befehl", required=True)
    s = sub.add_parser("suchen")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--runde", type=int, choices=(1, 2, 3), default=1)
    f = sub.add_parser("fotos")
    f.add_argument("--dry-run", action="store_true")
    f.add_argument("--runde", type=int, choices=(1, 2, 3), default=1)
    q = sub.add_parser("sql")
    q.add_argument("--sichtung", type=Path, required=True)
    q.add_argument("--runde", type=int, choices=(1, 2, 3), default=1)
    args = parser.parse_args()
    if args.befehl == "suchen":
        suchen(args.dry_run, args.runde)
    elif args.befehl == "fotos":
        fotos_laden(args.dry_run, args.runde)
    else:
        sql_schreiben(args.sichtung, args.runde)


if __name__ == "__main__":
    main()
