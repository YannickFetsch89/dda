"""
geraete_ki.py – DiesDasDüsseldorf
Spielgeräte per KI aus Besucherfotos (Google, lokal unter data/spielplaetze/fotos*/) und dem NRW-Luftbild
(Geobasis NRW, Orthofoto DOP, dl-de/zero-2.0) erkennen (Auftraggeber 25.11.2026, Pilot an 40 Plätzen gegen OSM).

Regeln (Auftraggeber):
- Übernommen wird nur ab Konfidenz 0,8. Karussell und Wasserspiel erst ab 0,95 (im Pilot oft falsch).
- Luftbild nur für Merkmale, die man von oben sicher erkennt: Sandkasten, Bolzplatz, Basketball, Tischtennis.
- Vorhandene Angaben (Sichtung, Zitat, OSM) bleiben unangetastet; die KI ergänzt nur fehlende Merkmale
  (quelle "foto_ki" bzw. "luftbild_ki", mit Beleg und Konfidenz). Nur „ja“, nie „nein“.
- Schreibt nicht direkt in die Datenbank, sondern eine SQL-Datei (führt der Auftraggeber aus).

Nutzung (aus dem Projektordner):
  python -m scraper.spielplaetze.geraete_ki erkennen --dry-run   # Plätze und geschätzte Kosten
  python -m scraper.spielplaetze.geraete_ki erkennen             # KI-Abfragen (kostet), Ergebnis je Platz im Zwischenspeicher
  python -m scraper.spielplaetze.geraete_ki sql                  # SQL aus dem Zwischenspeicher erzeugen
"""
import argparse
import base64
import json
import logging
import sys
import time
from datetime import date
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logger = logging.getLogger(__name__)

_WURZEL = Path(__file__).resolve().parents[2]
_DATEN = _WURZEL / "data" / "spielplaetze"
FOTO_ORDNER = (_DATEN / "fotos", _DATEN / "fotos_runde3")
CACHE = _DATEN / "geraete_ki"          # KI-Antworten je Platz (gitignored)

MODELL = "claude-opus-5-5"
MAX_FOTOS = 10
SCHWELLE = 0.8
SCHWELLE_STRENG = {"karussell": 0.95, "wasserspiel": 0.95}
LUFT_MERKMALE = {"sandkasten", "fussball", "basketball", "tischtennis"}
PARALLEL = 4
KOSTEN_JE_PLATZ = 0.065  # USD, Pilot 25.11.2026: 2,57 $ für 40 Plätze (Fotos + Luftbild)
WMS = "https://www.wms.nrw.de/geobasis/wms_nw_dop"

MERKMALE = ["sandkasten", "schaukel", "rutsche", "klettern", "wasserspiel", "seilbahn", "tischtennis", "fussball",
            "basketball", "federwippe", "wippe", "karussell", "balancierbalken", "volleyball", "skaten"]
SCHEMA = {
    "type": "object",
    "properties": {
        "zeigt_spielplatz": {"type": "boolean"},
        "erkannt": {"type": "array", "items": {
            "type": "object",
            "properties": {"merkmal": {"type": "string", "enum": MERKMALE},
                           "konfidenz": {"type": "number"},
                           "beleg": {"type": "string"}},
            "required": ["merkmal", "konfidenz", "beleg"], "additionalProperties": False}},
        "hinweis": {"type": "string"},
    },
    "required": ["zeigt_spielplatz", "erkannt", "hinweis"], "additionalProperties": False,
}
REGELN = (
    "Nenne nur Spielgeräte und Sportflächen, die du tatsächlich siehst. Konfidenz ehrlich kalibrieren: "
    "0.9–1.0 = eindeutig erkennbar (Form und Funktion klar), 0.8–0.89 = sehr wahrscheinlich, 0.5–0.79 = wahrscheinlich, "
    "unter 0.5 = nur vermutet. Lieber weglassen als raten. Merkmale: sandkasten (Sandfläche zum Spielen), schaukel, "
    "rutsche, klettern (nur eigenes Klettergerät: Klettergerüst, Kletternetz, Kletterwand, Kletterspinne, Hangelstrecke – "
    "nicht jeder Spielturm mit Leiter), wasserspiel (Pumpe, Matschanlage, Wasserlauf), seilbahn, tischtennis (Platte), "
    "fussball (Bolzplatz oder Tore), basketball (Korb), federwippe (Federtier), wippe (Balkenwippe), karussell (Drehscheibe, "
    "Karussell, Netzkarussell), balancierbalken, volleyball, skaten. Beleg: kurz, woran du es erkennst und in welchem Bild."
)
SYSTEM_FOTOS = ("Du prüfst Fotos eines öffentlichen Spielplatzes in Düsseldorf (Fotos von Besuchern; einzelne Fotos können "
                "von einem anderen Ort stammen – dann ignorieren). " + REGELN)
SYSTEM_LUFT = ("Du prüfst ein senkrechtes Luftbild (Orthofoto, ca. 10 cm pro Pixel, Norden oben) um den Mittelpunkt eines "
               "öffentlichen Spielplatzes in Düsseldorf. Von oben sind viele Geräte nur als Umriss oder Schatten sichtbar, "
               "unter Bäumen gar nicht. " + REGELN)


# ---------------------------------------------------------------------------
# Reine Funktionen
# ---------------------------------------------------------------------------

def schwelle(merkmal: str) -> float:
    return SCHWELLE_STRENG.get(merkmal, SCHWELLE)


def uebernehmen(ergebnis: dict, vorhanden: dict, heute: str) -> dict:
    """
    Neue Ausstattungs-Einträge aus einem KI-Ergebnis {"fotos": {...}, "luft": {...}}: nur Merkmale, die noch fehlen,
    ab Schwelle; Fotos vor Luftbild; Luftbild nur für LUFT_MERKMALE.
    """
    neu: dict = {}
    quellen = (("fotos", "foto_ki", None), ("luft", "luftbild_ki", LUFT_MERKMALE))
    for schluessel, quelle, erlaubt in quellen:
        antwort = ergebnis.get(schluessel) or {}
        if not antwort.get("zeigt_spielplatz", True):
            continue
        for g in antwort.get("erkannt") or []:
            m, k = g.get("merkmal"), float(g.get("konfidenz") or 0)
            if m not in MERKMALE or (erlaubt and m not in erlaubt) or k < schwelle(m):
                continue
            if m in vorhanden or m in neu:
                continue
            neu[m] = {"wert": "ja", "quelle": quelle, "beleg": (g.get("beleg") or "")[:300],
                      "konfidenz": round(k, 2), "stand": heute}
    return neu


def sql_zeile(zid: str, name: str, neu: dict) -> str:
    """Bestehende Einträge gewinnen immer: neu || vorhanden (rechte Seite überschreibt bei gleichen Schlüsseln)."""
    wert = json.dumps(neu, ensure_ascii=False).replace("'", "''")
    return (f"-- {name}: {', '.join(sorted(neu))}\n"
            f"UPDATE public.orte SET extras = jsonb_set(extras, '{{spielplatz,ausstattung}}', "
            f"'{wert}'::jsonb || COALESCE(extras->'spielplatz'->'ausstattung', '{{}}'::jsonb)) "
            f"WHERE id = '{zid}' AND typ = 'spielplatz';")


# ---------------------------------------------------------------------------
# Abfragen
# ---------------------------------------------------------------------------

def fotos_des_platzes(zid: str) -> list[Path]:
    dateien: list[Path] = []
    for ordner in FOTO_ORDNER:
        dateien += sorted((ordner / zid).glob("*.jpg"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0)
    return dateien[:MAX_FOTOS]


def luftbild(lat: float, lon: float) -> bytes | None:
    d_lat, d_lon = 0.00045, 0.00072  # ca. 100 m × 100 m
    params = {"SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap", "LAYERS": "nw_dop_rgb", "STYLES": "",
              "CRS": "EPSG:4326", "BBOX": f"{lat - d_lat},{lon - d_lon},{lat + d_lat},{lon + d_lon}",
              "WIDTH": "1000", "HEIGHT": "1000", "FORMAT": "image/jpeg"}
    for versuch in range(3):
        try:
            r = httpx.get(WMS, params=params, timeout=60)
            r.raise_for_status()
            return r.content
        except httpx.HTTPError as e:
            logger.warning("Luftbild fehlgeschlagen (%s) – neuer Versuch", e)
            time.sleep(5 * (versuch + 1))
    return None


def _bild(daten: bytes) -> dict:
    """Bild-Block; Typ aus den ersten Bytes (manche Google-Vorschaubilder sind PNG trotz .jpg)."""
    typ = "image/png" if daten[1:4] == b"PNG" else "image/webp" if daten[8:12] == b"WEBP" else "image/jpeg"
    return {"type": "image", "source": {"type": "base64", "media_type": typ, "data": base64.b64encode(daten).decode()}}


def fragen(client, system: str, bilder: list[dict], text: str) -> dict | None:
    for versuch in range(3):
        try:
            a = client.messages.create(model=MODELL, max_tokens=4000, system=system,
                                       output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
                                       messages=[{"role": "user", "content": bilder + [{"type": "text", "text": text}]}])
            roh = next(b.text for b in a.content if b.type == "text")
            return json.loads(roh)
        except Exception as e:  # noqa: BLE001 – Platz überspringen, beim nächsten Lauf erneut
            logger.warning("KI-Abfrage fehlgeschlagen (%s) – neuer Versuch", e)
            time.sleep(5 * (versuch + 1))
    return None


def plaetze_laden(db) -> list[dict]:
    from scraper.orte.google_places import alle_zeilen

    zeilen = alle_zeilen(db, "orte", "id, name, slug, latitude, longitude, aktiv, extras", lambda q: q.eq("typ", "spielplatz"))
    return sorted([z for z in zeilen if z.get("aktiv") and z.get("latitude") is not None
                   and not ((z.get("extras") or {}).get("spielplatz") or {}).get("ausgeschlossen")], key=lambda z: z["name"])


def erkennen(dry_run: bool) -> None:
    from database.client import get_supabase_client

    plaetze = plaetze_laden(get_supabase_client())
    offen = [z for z in plaetze if not (CACHE / f"{z['id']}.json").exists()]
    logger.info("%d Plätze, davon %d noch ohne KI-Ergebnis → Kosten ca. %.2f $%s", len(plaetze), len(offen),
                len(offen) * KOSTEN_JE_PLATZ, " [Dry-Run, keine Abfrage]" if dry_run else "")
    if dry_run:
        return
    import anthropic

    from concurrent.futures import ThreadPoolExecutor

    client = anthropic.Anthropic()
    CACHE.mkdir(parents=True, exist_ok=True)

    def ein_platz(nr_z: tuple[int, dict]) -> None:
        i, z = nr_z
        fotos = fotos_des_platzes(z["id"])
        ergebnis: dict = {"name": z["name"], "fotos_anzahl": len(fotos), "fotos": None, "luft": None}
        if fotos:
            ergebnis["fotos"] = fragen(client, SYSTEM_FOTOS, [_bild(p.read_bytes()) for p in fotos],
                                       f"Spielplatz: {z['name']}. {len(fotos)} Fotos, nummeriert in Reihenfolge ab 0.")
        lb = luftbild(z["latitude"], z["longitude"])
        if lb:
            ergebnis["luft"] = fragen(client, SYSTEM_LUFT, [_bild(lb)], f"Spielplatz: {z['name']}. Mittelpunkt in der Bildmitte.")
        if (fotos and ergebnis["fotos"] is None) or (lb and ergebnis["luft"] is None):
            logger.error("[%d/%d] %s: Abfrage unvollständig – wird beim nächsten Lauf wiederholt", i, len(offen), z["name"])
            return
        (CACHE / f"{z['id']}.json").write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1), encoding="utf-8")
        logger.info("[%d/%d] %s: %d Fotos, Luftbild %s", i, len(offen), z["name"], len(fotos), "ja" if lb else "nein")

    # Vier Plätze gleichzeitig: einzeln dauert ein Platz rund 40 Sekunden (zwei KI-Abfragen + Luftbild)
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        list(pool.map(ein_platz, enumerate(offen, 1)))


def sql_schreiben() -> None:
    from database.client import get_supabase_client

    heute = date.today().isoformat()
    zeilen = [f"-- Spielgeräte aus KI-Erkennung (Besucherfotos + NRW-Luftbild), {heute} – im Supabase SQL-Editor ausführen.",
              f"-- Ab Konfidenz {SCHWELLE} (Karussell/Wasserspiel ab 0.95), Luftbild nur {', '.join(sorted(LUFT_MERKMALE))}.",
              "-- Nur fehlende Merkmale; vorhandene Angaben (Sichtung, Zitat, OSM) gewinnen immer.", "", "BEGIN;", ""]
    zaehler: dict[str, int] = {}
    plaetze_mit = 0
    for z in plaetze_laden(get_supabase_client()):
        datei = CACHE / f"{z['id']}.json"
        if not datei.exists():
            continue
        vorhanden = ((z.get("extras") or {}).get("spielplatz") or {}).get("ausstattung") or {}
        neu = uebernehmen(json.loads(datei.read_text(encoding="utf-8")), vorhanden, heute)
        if not neu:
            continue
        plaetze_mit += 1
        for m, e in neu.items():
            zaehler[f"{m} ({e['quelle']})"] = zaehler.get(f"{m} ({e['quelle']})", 0) + 1
        zeilen.append(sql_zeile(z["id"], z["name"], neu))
    zeilen += ["", "COMMIT;", "",
               f"-- {plaetze_mit} Plätze ergänzt: " + ", ".join(f"{k} {v}" for k, v in sorted(zaehler.items()))]
    ziel = _WURZEL / "database" / f"spielplatz_geraete_ki_{heute}.sql"
    ziel.write_text("\n".join(zeilen) + "\n", encoding="utf-8")
    logger.info("SQL: %s – %d Plätze, %d neue Merkmale", ziel, plaetze_mit, sum(zaehler.values()))


def main():
    from dotenv import load_dotenv

    load_dotenv(_WURZEL / ".env")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Spielplätze: Geräte per KI aus Fotos und Luftbild")
    sub = parser.add_subparsers(dest="befehl", required=True)
    e = sub.add_parser("erkennen")
    e.add_argument("--dry-run", action="store_true")
    sub.add_parser("sql")
    args = parser.parse_args()
    if args.befehl == "erkennen":
        erkennen(args.dry_run)
    else:
        sql_schreiben()


if __name__ == "__main__":
    main()
