"""
google_abgleich.py – DiesDasDüsseldorf
Google-Abgleich für den Guide „Spielplätze“ (Plan: docs/plan-spielplaetze-2026-11-12.md, Abschnitt 4.4), nur Runde-1-Plätze.

Je Platz eine Umkreissuche (80 m, Typ playground) über die Places API (New). Treffer nur bei Namensähnlichkeit oder
einzigem Treffer, sonst Prüf-CSV. Bewertung nur intern (extras.spielplatz.google, für den Score). Foto-Kandidaten bleiben
lokal (data/spielplaetze/google/), bis die Sichtung sie freigibt; das Foto setzt dann nur die Foto-SQL (Auftraggeber).

Nutzung:
  python -m scraper.spielplaetze.google_abgleich suchen --dry-run     # nennt Plätze und Kosten, fragt nichts ab
  python -m scraper.spielplaetze.google_abgleich suchen               # Umkreissuche (kostet), schreibt google + Kandidaten
  python -m scraper.spielplaetze.google_abgleich fotos [--dry-run]    # lädt Vorschaubilder der Kandidaten (kostet)
  python -m scraper.spielplaetze.google_abgleich sql --sichtung DATEI # Foto-SQL aus der Sichtung erzeugen
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

API_BASE = "https://places.googleapis.com/v1"
RADIUS_M = 80.0
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


def umkreissuche(lat: float, lon: float) -> list[dict]:
    body = {"includedTypes": ["playground"], "maxResultCount": 20, "languageCode": "de", "regionCode": "DE",
            "locationRestriction": {"circle": {"center": {"latitude": lat, "longitude": lon}, "radius": RADIUS_M}}}
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


def runde_1_laden(db) -> list[dict]:
    from scraper.orte.google_places import alle_zeilen

    zeilen = alle_zeilen(db, "orte", "id, name, slug, stadtteil, latitude, longitude, extras", lambda q: q.eq("typ", "spielplatz"))
    return sorted([z for z in zeilen if ist_runde_1(z)], key=lambda z: z["name"])


def suchen(dry_run: bool) -> None:
    from database.client import get_supabase_client

    db = get_supabase_client()
    plaetze = runde_1_laden(db)
    offen = [z for z in plaetze if not (CACHE / f"{z['id']}.json").exists()]
    logger.info("Runde 1: %d Plätze (%d städtisch, %d Abenteuer), davon %d noch ohne Abfrage → Kosten ca. %.2f $%s",
                len(plaetze), sum(1 for z in plaetze if z["extras"]["spielplatz"].get("quelle") != "abenteuer"),
                sum(1 for z in plaetze if z["extras"]["spielplatz"].get("quelle") == "abenteuer"),
                len(offen), len(offen) * PREIS_SUCHE, " [Dry-Run, keine Abfrage]" if dry_run else "")
    if dry_run:
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    for i, z in enumerate(offen, 1):
        try:
            orte = umkreissuche(z["latitude"], z["longitude"])
            (CACHE / f"{z['id']}.json").write_text(json.dumps(orte, ensure_ascii=False), encoding="utf-8")
            logger.info("[%d/%d] %s: %d Google-Orte", i, len(offen), z["name"], len(orte))
        except Exception as e:  # noqa: BLE001 – Platz überspringen, beim nächsten Lauf erneut
            logger.error("Umkreissuche für %s fehlgeschlagen: %s", z["name"], e)

    kandidaten, pruef, geschrieben = {}, [], 0
    for z in plaetze:
        datei = CACHE / f"{z['id']}.json"
        if not datei.exists():
            continue
        orte = json.loads(datei.read_text(encoding="utf-8"))
        treffer, art = treffer_waehlen(z["name"], orte)
        google = None
        if treffer:
            google = {"place_id": treffer["id"], "name": (treffer.get("displayName") or {}).get("text"),
                      "rating": treffer.get("rating"), "anzahl": treffer.get("userRatingCount"), "zuordnung": art}
            kandidaten[z["id"]] = foto_kandidaten(treffer)
        pruef.append({"name": z["name"], "stadtteil": z.get("stadtteil") or "", "zuordnung": art,
                      "google_name": (google or {}).get("name") or "", "rating": (google or {}).get("rating") or "",
                      "anzahl": (google or {}).get("anzahl") or "", "fotos": len(kandidaten.get(z["id"], [])),
                      "alle_google_orte": " | ".join((o.get("displayName") or {}).get("text", "") for o in orte)})
        try:
            aktuell = (db.table("orte").select("extras").eq("id", z["id"]).execute().data or [{}])[0].get("extras") or {}
            sp = {**(aktuell.get("spielplatz") or {}), "google": google}
            db.table("orte").update({"extras": {**aktuell, "spielplatz": sp}}).eq("id", z["id"]).execute()
            geschrieben += 1
        except Exception as e:  # noqa: BLE001
            logger.error("Speichern für %s fehlgeschlagen: %s", z["name"], e)
    KANDIDATEN.write_text(json.dumps(kandidaten, ensure_ascii=False, indent=1), encoding="utf-8")
    with PRUEF_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pruef[0].keys()) if pruef else ["name"], delimiter=";")
        w.writeheader()
        w.writerows(pruef)
    arten = {a: sum(1 for p in pruef if p["zuordnung"] == a) for a in ("name", "einziger", "mehrdeutig", "kein_treffer")}
    logger.info("Zuordnung: %s; %d Plätze mit Foto-Kandidaten (%d Fotos); %d Zeilen geschrieben; Prüf-CSV %s",
                arten, sum(1 for k in kandidaten.values() if k), sum(len(k) for k in kandidaten.values()), geschrieben, PRUEF_CSV)


def fotos_laden(dry_run: bool) -> None:
    """Vorschaubilder (640 px) der Kandidaten für die Sichtung laden – nur lokal, nie veröffentlicht."""
    from config import GOOGLE_PLACES_API_KEY

    kandidaten = json.loads(KANDIDATEN.read_text(encoding="utf-8"))
    offen = [(zid, i, f) for zid, liste in kandidaten.items() for i, f in enumerate(liste)
             if not (FOTOS / zid / f"{i}.jpg").exists()]
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
            (FOTOS / zid).mkdir(parents=True, exist_ok=True)
            (FOTOS / zid / f"{i}.jpg").write_bytes(r.content)
            if n % 50 == 0:
                logger.info("%d/%d Fotos geladen", n, len(offen))
        except Exception as e:  # noqa: BLE001
            fehler += 1
            logger.error("Foto %s/%d fehlgeschlagen: %s", zid, i, e)
    logger.info("Fotos fertig: %d geladen, %d Fehler", len(offen) - fehler, fehler)


def sql_schreiben(sichtung_datei: Path) -> None:
    from database.client import get_supabase_client

    sichtung = json.loads(sichtung_datei.read_text(encoding="utf-8"))
    kandidaten = json.loads(KANDIDATEN.read_text(encoding="utf-8"))
    db = get_supabase_client()
    namen = {z["id"]: z["name"] for z in runde_1_laden(db)}
    heute = date.today().isoformat()
    ziel = _WURZEL / "database" / f"spielplatz_fotos_{heute}.sql"
    ziel.write_text(sql_aus_sichtung(sichtung, kandidaten, namen, heute), encoding="utf-8")
    logger.info("Foto-SQL: %s (%d mit Foto, %d ohne)", ziel, sum(1 for s in sichtung.values() if s.get("foto") is not None),
                sum(1 for s in sichtung.values() if s.get("foto") is None))


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Spielplätze: Google-Abgleich (Runde 1)")
    sub = parser.add_subparsers(dest="befehl", required=True)
    s = sub.add_parser("suchen")
    s.add_argument("--dry-run", action="store_true")
    f = sub.add_parser("fotos")
    f.add_argument("--dry-run", action="store_true")
    q = sub.add_parser("sql")
    q.add_argument("--sichtung", type=Path, required=True)
    args = parser.parse_args()
    if args.befehl == "suchen":
        suchen(args.dry_run)
    elif args.befehl == "fotos":
        fotos_laden(args.dry_run)
    else:
        sql_schreiben(args.sichtung)


if __name__ == "__main__":
    main()
