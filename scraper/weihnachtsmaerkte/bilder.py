"""
bilder.py – DiesDasDüsseldorf
Eigene Bilder für den Weihnachtsmarkt-Guide (z. B. vom Veranstalter geliefert, Auftraggeber 17.11.2026).

Ablauf:
1. Originaldatei nach data/weihnachtsmaerkte/bilder-roh/ legen (gitignored – Originale bleiben lokal).
2. Zeile in data/weihnachtsmaerkte/bilder.csv ergänzen:
     schluessel  – Schlüssel aus maerkte.csv (z. B. nordstrasse)
     datei       – Dateiname in bilder-roh/
     nachweis    – Bildnachweis genau so, wie der Rechteinhaber ihn wünscht (ohne „Foto:“ – das setzt die Website davor);
                   leer bei eigenen Fotos des Auftraggebers (dann zeigt die Website keinen Nachweis)
     link        – optional: https-Link im Bildnachweis (z. B. Seite des Veranstalters)
     erlaubnis   – Pflicht: wer wann schriftlich erlaubt hat (z. B. „E-Mail Veranstalter 18.11.2026“)
     fokus       – optional: Bildausschnitt „oben“, „unten“ oder „35%“
3. python -m scraper.weihnachtsmaerkte.bilder --dry-run   # prüft nur
   python -m scraper.weihnachtsmaerkte.bilder [--nur a,b] # WebP nach web/public/ort-bilder/weihnachtsmaerkte/ + SQL
4. Bilder committen/deployen, danach die SQL im Supabase SQL-Editor ausführen (erst dann zeigt die Website sie –
   vorher zeigt bild_url auf eine Datei, die live noch fehlt).

Das eigene Bild hat auf der Website Vorrang vor dem Google-Foto (lib/orte.ts ortBildUrl); das Google-Foto bleibt als
Rückfall in extras.google_foto stehen. Zurück zum Google-Foto: bild_url und bild_attribution leeren.
"""
from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logger = logging.getLogger(__name__)

_WURZEL = Path(__file__).resolve().parents[2]
DATEN = _WURZEL / "data" / "weihnachtsmaerkte"
BILDER_CSV = DATEN / "bilder.csv"
ROH = DATEN / "bilder-roh"
MAERKTE_CSV = DATEN / "maerkte.csv"
ZIEL = _WURZEL / "web" / "public" / "ort-bilder" / "weihnachtsmaerkte"
WEB_PFAD = "/ort-bilder/weihnachtsmaerkte"  # nicht unter /guides/<hub>/ – dort prüft proxy.ts jeden Pfad als Detailseite

MAX_BREITE = 1600
QUALITAET = 80
MAX_BYTES = 380_000  # größere WebP-Dateien mit geringerer Qualität neu speichern (Cursor-Prüfung 19.11.2026)
_SCHLUESSEL = re.compile(r"[a-z0-9-]+")
_FOKUS = re.compile(r"oben|unten|(100|[1-9]?\d)%")
_ENDUNGEN = {".jpg", ".jpeg", ".png", ".webp"}


def csv_lesen(pfad: Path) -> list[dict]:
    if not pfad.exists():
        return []
    with pfad.open(encoding="utf-8-sig", newline="") as f:
        return [{k: (v or "").strip() for k, v in z.items() if k} for z in csv.DictReader(f)]


def nachweis_bereinigen(text: str) -> str:
    """„Foto: X“ → „X“ (die Website setzt „Foto:“ selbst davor)."""
    return re.sub(r"^\s*(foto|bild)\s*:\s*", "", text, flags=re.I).strip()


def zeilen_pruefen(zeilen: list[dict], bekannte: set[str], roh: Path) -> tuple[list[dict], list[str]]:
    """Gültige Zeilen und Fehlertexte. Ohne schriftliche Erlaubnis oder Nachweis wird nichts übernommen."""
    gut, fehler, gesehen = [], [], set()
    for nr, z in enumerate(zeilen, start=2):
        s = z.get("schluessel", "")
        wo = f"Zeile {nr} ({s or 'ohne Schlüssel'})"
        if not _SCHLUESSEL.fullmatch(s):
            fehler.append(f"{wo}: Schlüssel fehlt oder hat ungültige Zeichen")
            continue
        if s not in bekannte:
            fehler.append(f"{wo}: Schlüssel steht nicht in maerkte.csv")
            continue
        if s in gesehen:
            fehler.append(f"{wo}: Schlüssel doppelt")
            continue
        datei = z.get("datei", "")
        if not datei or Path(datei).name != datei or Path(datei).suffix.lower() not in _ENDUNGEN:
            fehler.append(f"{wo}: Datei fehlt oder ist kein JPG/PNG/WebP-Dateiname")
            continue
        if not (roh / datei).is_file():
            fehler.append(f"{wo}: {datei} liegt nicht in {roh.name}/")
            continue
        nachweis = nachweis_bereinigen(z.get("nachweis", ""))
        # Leer = eigenes Foto des Auftraggebers, ohne Nachweis (Auftraggeber 18.11.2026)
        if len(nachweis) > 120:
            fehler.append(f"{wo}: Bildnachweis ist länger als 120 Zeichen")
            continue
        if not z.get("erlaubnis"):
            fehler.append(f"{wo}: Erlaubnis fehlt – ohne schriftliche Erlaubnis kein Bild")
            continue
        link = z.get("link", "")
        if link and not re.fullmatch(r"https://[^\s'\"<>]+", link):
            fehler.append(f"{wo}: Link muss mit https:// beginnen")
            continue
        if link and not nachweis:
            fehler.append(f"{wo}: Link ohne Bildnachweis wird nirgends gezeigt")
            continue
        fokus = z.get("fokus", "")
        if fokus and not _FOKUS.fullmatch(fokus):
            fehler.append(f"{wo}: Fokus nur „oben“, „unten“ oder z. B. „35%“")
            continue
        gesehen.add(s)
        gut.append({"schluessel": s, "datei": datei, "nachweis": nachweis, "link": link, "erlaubnis": z["erlaubnis"], "fokus": fokus})
    return gut, fehler


def _sql_text(wert: str) -> str:
    return "'" + wert.replace("'", "''") + "'"


def sql_bauen(zeilen: list[dict], heute: str) -> str:
    """UPDATE je Markt: eigenes Bild + Nachweis setzen, alten Fokus/Link verwerfen, Bildversion hochzählen."""
    teile = [
        f"-- Eigene Weihnachtsmarkt-Bilder ({heute}) – erst NACH dem Deploy der Bilddateien im Supabase SQL-Editor ausführen.",
        "-- Erlaubnis je Bild steht im Kommentar (Quelle: data/weihnachtsmaerkte/bilder.csv).",
        "",
    ]
    for z in zeilen:
        neu = [f"'foto_manuell', {_sql_text(heute)}", "'foto_version', COALESCE((extras->>'foto_version')::int + 1, 1)"]
        if z["link"]:
            neu.append(f"'bild_link', {_sql_text(z['link'])}")
        if z["fokus"]:
            neu.append(f"'bild_fokus', {_sql_text(z['fokus'])}")
        teile.append(f"-- {z['schluessel']}: Foto: {z['nachweis'] or '(eigenes, ohne Nachweis)'} – Erlaubnis: {z['erlaubnis']}".replace("\n", " "))
        teile.append(
            f"UPDATE public.orte SET bild_url = {_sql_text(f'{WEB_PFAD}/{z['schluessel']}.webp')}, "
            f"bild_attribution = {_sql_text(z['nachweis']) if z['nachweis'] else 'NULL'}, "
            f"extras = (extras - 'bild_link' - 'bild_fokus') || jsonb_build_object({', '.join(neu)}) "
            f"WHERE typ = 'weihnachtsmarkt' AND extras->'weihnachtsmarkt'->>'schluessel' = {_sql_text(z['schluessel'])} "
            "RETURNING slug, bild_url, bild_attribution;"
        )
    return "\n".join(teile) + "\n"


def bild_umwandeln(quelle: Path, ziel: Path) -> tuple[int, int]:
    """Drehung aus EXIF übernehmen, auf höchstens MAX_BREITE verkleinern, als WebP ohne Metadaten speichern."""
    from PIL import Image, ImageOps

    with Image.open(quelle) as roh:
        bild = ImageOps.exif_transpose(roh).convert("RGB")
    if bild.width > MAX_BREITE:
        bild = bild.resize((MAX_BREITE, round(bild.height * MAX_BREITE / bild.width)), Image.LANCZOS)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    qualitaet = QUALITAET
    bild.save(ziel, "WEBP", quality=qualitaet, method=6)
    while ziel.stat().st_size > MAX_BYTES and qualitaet > 60:
        qualitaet -= 5
        bild.save(ziel, "WEBP", quality=qualitaet, method=6)
    return bild.width, bild.height


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="Weihnachtsmärkte: eigene Bilder umwandeln und SQL erzeugen")
    p.add_argument("--dry-run", action="store_true", help="nur prüfen, nichts schreiben")
    p.add_argument("--nur", help="nur diese Schlüssel (kommagetrennt) umwandeln und in die SQL schreiben")
    a = p.parse_args()

    bekannte = {z["schluessel"] for z in csv_lesen(MAERKTE_CSV) if z.get("schluessel")}
    zeilen, fehler = zeilen_pruefen(csv_lesen(BILDER_CSV), bekannte, ROH)
    for f in fehler:
        logger.error(f)
    if fehler:
        logger.error("%d Fehler – bitte bilder.csv korrigieren, nichts geschrieben", len(fehler))
        sys.exit(1)
    if a.nur:
        # Nur neue Bilder – schon eingespielte nicht noch einmal umwandeln und ihre Bildversion nicht erneut hochzählen
        gewuenscht = {s.strip() for s in a.nur.split(",") if s.strip()}
        unbekannt = gewuenscht - {z["schluessel"] for z in zeilen}
        if unbekannt:
            logger.error("--nur: nicht in bilder.csv: %s", ", ".join(sorted(unbekannt)))
            sys.exit(1)
        zeilen = [z for z in zeilen if z["schluessel"] in gewuenscht]
    if not zeilen:
        logger.info("bilder.csv enthält keine Bilder")
        return
    if a.dry_run:
        for z in zeilen:
            logger.info("ok: %s ← %s (Foto: %s)", z["schluessel"], z["datei"], z["nachweis"])
        return
    for z in zeilen:
        try:
            breite, hoehe = bild_umwandeln(ROH / z["datei"], ZIEL / f"{z['schluessel']}.webp")
            logger.info("%s: %d×%d → %s/%s.webp", z["schluessel"], breite, hoehe, WEB_PFAD, z["schluessel"])
        except Exception as e:  # noqa: BLE001
            logger.error("%s: Bild nicht umgewandelt: %s", z["schluessel"], e)
            sys.exit(1)
    heute = date.today().isoformat()
    sql = _WURZEL / "database" / f"weihnachtsmarkt_bilder_{heute}.sql"
    nr = 2
    while sql.exists():  # eine schon (vielleicht ausgeführte) SQL vom selben Tag nie überschreiben
        sql = _WURZEL / "database" / f"weihnachtsmarkt_bilder_{heute}_{nr}.sql"
        nr += 1
    sql.write_text(sql_bauen(zeilen, heute), encoding="utf-8")
    logger.info("SQL: %s (%d Bilder) – erst nach dem Deploy ausführen", sql.relative_to(_WURZEL), len(zeilen))


if __name__ == "__main__":
    main()
