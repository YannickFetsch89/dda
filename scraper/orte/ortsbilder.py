"""
ortsbilder.py – DiesDasDüsseldorf
Bilder der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.13, Schritt 4). Schreibt nichts in die Datenbank.

Regeln (Plan 3.13):
- Geladen wird nur die Bild-URL aus data/spielstaetten/bilder.csv: mindestens 2 s Pause, Backoff bei HTTP 429,
  User-Agent nach Projektregel, robots.txt beachtet. Kein Hotlinking, keine Portal-, Event- oder Google-Fotos.
- EXIF (auch Standort) wird entfernt, das Bild verkleinert und als WebP unter
  web/public/ort-bilder/orte/<slug>.webp gespeichert. `erlaubnis = nachtraeglich` (Freigabe holt der Auftraggeber).
- Nachweis immer sichtbar, mit Link; Wikimedia nur mit Urheber, Lizenz und Quelllink.
- Ersetzt das Skript ein vorhandenes Bild, erhöht es `version` → extras.foto_version (Cache, `?v=` ab Version 2).

bilder.csv (Semikolon): slug;bild_url;seite_url;nachweis;lizenz;link;abrufdatum;version;fokus

Ablauf (im Repo-Stamm):
  python -m scraper.orte.ortsbilder --uebernehmen entwurf.json [...]   → Zeilen aus Entwürfen (Feld „bild“)
  python -m scraper.orte.ortsbilder --laden [--nur a,b] [--neu]         → WebP-Dateien
  python -m scraper.orte.ortsbilder --sql                               → database/orte_bilder_<datum>.sql
Erst die Bilddateien deployen, dann die SQL ausführen (sonst zeigt bild_url auf eine Datei, die live fehlt).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import re
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from scraper.utils.http_client import STANDARD_HEADERS, _backoff

logger = logging.getLogger(__name__)

BILDER = Path("data/spielstaetten/bilder.csv")
ZIEL = Path("web/public/ort-bilder/orte")
WEB_PFAD = "/ort-bilder/orte"
SPALTEN = ["slug", "bild_url", "seite_url", "nachweis", "lizenz", "link", "abrufdatum", "version", "fokus"]
PAUSE_S = 2.0
MAX_BREITE = 1600
QUALITAET = 80
MAX_BYTES = 380_000
_SLUG = re.compile(r"^[a-z0-9-]+$")
_FOKUS = re.compile(r"^(oben|unten|(100|[1-9]?\d)%)$")
# Portale und Google: nie als Ortsbild (Plan 3.13)
_VERBOTEN = re.compile(r"googleusercontent|gstatic|ggpht|eventim|ticketmaster|reservix|rausgegangen|prinz\.de|"
                       r"allevents|eventbrite|meetup|facebook|fbcdn|instagram|cdninstagram", re.I)


def lesen() -> list[dict]:
    if not BILDER.exists():
        return []
    with BILDER.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def schreiben(zeilen: list[dict]) -> None:
    BILDER.parent.mkdir(parents=True, exist_ok=True)
    with BILDER.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SPALTEN, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(zeilen, key=lambda z: z["slug"]))


def pruefen(z: dict) -> list[str]:
    """Fehler einer Zeile (leer = in Ordnung)."""
    f = []
    if not _SLUG.match(z.get("slug") or ""):
        f.append("Slug ungültig")
    for feld in ("bild_url", "seite_url", "link"):
        if not (z.get(feld) or "").startswith("https://"):
            f.append(f"{feld} fehlt oder nicht https")
    if not (z.get("nachweis") or "").strip():
        f.append("Nachweis fehlt")
    if _VERBOTEN.search(z.get("bild_url") or "") or _VERBOTEN.search(z.get("seite_url") or ""):
        f.append("Portal- oder Google-Bild")
    if "wikimedia" in (z.get("bild_url") or "") and not (z.get("lizenz") or "").strip():
        f.append("Wikimedia ohne Lizenz")
    if z.get("fokus") and not _FOKUS.match(z["fokus"]):
        f.append("Fokus ungültig")
    return f


def uebernehmen(dateien: list[Path]) -> int:
    bisher = {z["slug"]: z for z in lesen()}
    n = 0
    for datei in dateien:
        for e in json.loads(datei.read_text(encoding="utf-8")):
            b = e.get("bild")
            if not b:
                continue
            alt = bisher.get(e["slug"], {})
            neu = {"slug": e["slug"], "bild_url": b.get("bild_url", ""), "seite_url": b.get("seite_url", ""),
                   "nachweis": b.get("nachweis", ""), "lizenz": b.get("lizenz", ""), "link": b.get("link", ""),
                   "abrufdatum": alt.get("abrufdatum", "") if alt.get("bild_url") == b.get("bild_url") else "",
                   "version": alt.get("version", ""), "fokus": alt.get("fokus", "")}
            bisher[e["slug"]] = neu
            n += 1
    schreiben(list(bisher.values()))
    return n


def robots_erlaubt(url: str, cache: dict[str, RobotFileParser | None]) -> bool:
    """robots.txt der Bild-Domain (fehlt sie oder ist sie nicht lesbar, gilt: erlaubt)."""
    u = urlparse(url)
    basis = f"{u.scheme}://{u.netloc}"
    if basis not in cache:
        rp = RobotFileParser()
        try:
            r = httpx.get(f"{basis}/robots.txt", headers=STANDARD_HEADERS, timeout=20, follow_redirects=True)
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except Exception as e:
            logger.warning("robots.txt von %s nicht lesbar (%s) – gilt als erlaubt", basis, e)
            rp.parse([])
        cache[basis] = rp
    rp = cache[basis]
    return rp.can_fetch(STANDARD_HEADERS["User-Agent"], url) if rp else True


def abrufen(url: str) -> bytes | None:
    """Bild laden, bei 429 mit Backoff (höchstens 3 weitere Versuche)."""
    try:
        with httpx.Client(headers=STANDARD_HEADERS, timeout=30, follow_redirects=True) as c:
            r = c.get(url)
            for versuch in range(3):
                if r.status_code != 429:
                    break
                pause = _backoff(r.headers.get("Retry-After"), versuch)
                logger.warning("HTTP 429 bei %s – warte %.0f s", url, pause)
                time.sleep(pause)
                r = c.get(url)
            r.raise_for_status()
            if not r.headers.get("content-type", "").startswith("image/"):
                logger.error("Kein Bild (%s): %s", r.headers.get("content-type"), url)
                return None
            return r.content
    except Exception as e:
        logger.error("Bild nicht ladbar: %s (%s)", url, e)
        return None


def umwandeln(daten: bytes, ziel: Path) -> tuple[int, int]:
    """Drehung aus EXIF übernehmen, verkleinern, als WebP OHNE Metadaten (kein EXIF, kein Standort) speichern."""
    from PIL import Image, ImageOps

    with Image.open(io.BytesIO(daten)) as roh:
        bild = ImageOps.exif_transpose(roh).convert("RGB")   # neues Bild: Metadaten werden nicht übernommen
    if bild.width > MAX_BREITE:
        bild = bild.resize((MAX_BREITE, round(bild.height * MAX_BREITE / bild.width)), Image.LANCZOS)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    q = QUALITAET
    bild.save(ziel, "WEBP", quality=q, method=6)
    while ziel.stat().st_size > MAX_BYTES and q > 60:
        q -= 5
        bild.save(ziel, "WEBP", quality=q, method=6)
    return bild.width, bild.height


def laden(nur: set[str] | None, neu: bool, heute: str) -> int:
    zeilen = lesen()
    robots: dict[str, RobotFileParser | None] = {}
    n = 0
    for z in zeilen:
        if nur and z["slug"] not in nur:
            continue
        datei = ZIEL / f"{z['slug']}.webp"
        if datei.exists() and not neu:
            continue
        fehler = pruefen(z)
        if fehler:
            logger.warning("%s übersprungen: %s", z["slug"], "; ".join(fehler))
            continue
        if not robots_erlaubt(z["bild_url"], robots):
            logger.warning("%s: robots.txt sperrt %s", z["slug"], z["bild_url"])
            continue
        if n:
            time.sleep(PAUSE_S)
        daten = abrufen(z["bild_url"])
        if not daten:
            continue
        ersetzt = datei.exists()
        breite, hoehe = umwandeln(daten, datei)
        z["abrufdatum"] = heute
        # Ersetzen erhöht die Version (Cache-Bruch ?v=…, Plan 3.13); das erste Bild hat Version 1
        z["version"] = str(int(z.get("version") or 1) + 1) if ersetzt else (z.get("version") or "1")
        logger.info("%s: %dx%d → %s", z["slug"], breite, hoehe, datei)
        n += 1
    schreiben(zeilen)
    return n


def _sql(wert: str) -> str:
    return "'" + wert.replace("'", "''") + "'"


def nachweis_text(z: dict) -> str:
    lizenz = (z.get("lizenz") or "").strip()
    return f"{z['nachweis'].strip()}{f' ({lizenz})' if lizenz else ''}"


def sql_bauen(zeilen: list[dict], heute: str) -> tuple[str, int]:
    teile = [
        "-- Bilder der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.13, Schritt 4)",
        f"-- Erzeugt am {heute} von `python -m scraper.orte.ortsbilder --sql` aus data/spielstaetten/bilder.csv.",
        "-- ERST nach dem Deploy der Bilddateien ausführen. Nur Zeilen mit vorhandener WebP-Datei. Wiederholbar.",
        "-- erlaubnis = nachtraeglich: Die Freigabe der Rechteinhaber holt der Auftraggeber (Plan E4).",
        "", "BEGIN;", ""]
    n = 0
    for z in sorted(zeilen, key=lambda z: z["slug"]):
        if pruefen(z) or not (ZIEL / f"{z['slug']}.webp").exists():
            continue
        extras = {"bild_link": z["link"], "bild_quelle": z["seite_url"], "bild_abruf": z.get("abrufdatum") or heute,
                  "erlaubnis": "nachtraeglich", "foto_version": int(z.get("version") or 1)}
        if z.get("fokus"):
            extras["bild_fokus"] = z["fokus"]
        pfad = f"{WEB_PFAD}/{z['slug']}.webp"
        teile.append(
            f"UPDATE public.orte SET bild_url = {_sql(pfad)}, "
            f"bild_attribution = {_sql(nachweis_text(z))},\n"
            f"  extras = extras || {_sql(json.dumps(extras, ensure_ascii=False))}::jsonb\n"
            f"WHERE slug = {_sql(z['slug'])} AND typ = 'spielstaette';")
        n += 1
    teile += ["", "COMMIT;", "", "-- Kontrolle: Ortsseiten mit eigenem Bild",
              f"SELECT count(*) FILTER (WHERE bild_url LIKE '{WEB_PFAD}/%') AS mit_bild FROM public.orte WHERE typ = 'spielstaette';",
              ""]
    return "\n".join(teile), n


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    p = argparse.ArgumentParser(description="Bilder der Ortsseiten (nur lesend, SQL als Datei)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--uebernehmen", nargs="+", type=Path, metavar="JSON")
    g.add_argument("--laden", action="store_true")
    g.add_argument("--sql", action="store_true")
    p.add_argument("--nur", default="")
    p.add_argument("--neu", action="store_true", help="vorhandene Dateien neu laden (erhöht die Version)")
    p.add_argument("--ausgabe", default=f"database/orte_bilder_{date.today().isoformat()}.sql")
    a = p.parse_args()
    heute = date.today().isoformat()
    if a.uebernehmen:
        logger.info("Bilder: %d Einträge übernommen → %s", uebernehmen(a.uebernehmen), BILDER)
    elif a.laden:
        nur = {s.strip() for s in a.nur.split(",") if s.strip()} or None
        logger.info("Bilder: %d geladen", laden(nur, a.neu, heute))
    else:
        sql, n = sql_bauen(lesen(), heute)
        Path(a.ausgabe).write_text(sql, encoding="utf-8")
        logger.info("Bilder-SQL: %d Bilder → %s", n, a.ausgabe)


if __name__ == "__main__":
    main()
