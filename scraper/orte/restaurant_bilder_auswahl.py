"""
restaurant_bilder_auswahl.py – DiesDasDüsseldorf
Lokale Auswahlseite für die Guide-Bilder und die dies.das-Wertung (Wünsche des Auftraggebers, 26.11.2026).

Aufbau:
- Reiter Restaurants · Cafés · Imbisse · Kneipen & Bars, je Seite 50 Betriebe (immer klar, wo man ist).
- Je Betrieb zwei Bildrollen: **Ambiente** (= Titelbild auf der Website) und **Essen & Getränke** (zweites Bild,
  wird gespeichert, angezeigt erst nach einem kleinen Umbau der Website). Vorausgewählt ist der KI-Vorschlag
  (Innenraum vor Essen, Querformat zuerst). „Heutiges Bild behalten“ lässt das Titelbild unverändert.
- dies.das-Wertung (Plan docs/plan-restaurantguide-2026-11-26.md, A2): Grund aus dem bisherigen Score (extras.vorab_score)
  plus Ambiente-Zuschlag der KI (nur wenn sicher; Kneipen & Bars bewertet der Auftraggeber selbst). Freifeld zum
  Überschreiben – leer = gerechneter Wert.
- Gespeichert werden nur Betriebe mit ✓ (angeklickt, Wert eingetragen oder „Auswahl passt“).

Was beim Speichern passiert (ein Update je Betrieb, sofort live; Website-Cache bis etwa 10 Minuten):
- Titelbild Google → extras.google_foto, bild_url leer, Nachweis = Autor. Titelbild Website → bild_url = Bildadresse der
  Website (die Website holt es über den eigenen Bild-Proxy), Nachweis = Domain, extras.bild_link. Dazu foto_manuell
  (schützt vor Skript-Läufen), foto_version + 1, bild_fokus aus der KI.
- Zweites Bild → extras.bild_zweit = {art: google|eigen, …}.
- Website-Bilder werden zusätzlich als WebP unter web/public/ort-bilder/restaurants/ abgelegt; nach dem nächsten Deploy
  stellt `--nach-deploy` auf die eigene Datei um.
- extras.ambiente (KI), extras.ddd_wertung_hand (Freifeld, sonst entfernt), extras.ddd_wertung (gilt).
- Vorher/Nachher in data/restaurant_bilder/protokoll.jsonl; `--zurueck <slug>` stellt den Stand vor der Runde her.

Nutzung (im Repo-Stamm, Python aus DD/.venv):
  python -m scraper.orte.restaurant_bilder_auswahl [--trocken]       → http://127.0.0.1:3650
  python -m scraper.orte.restaurant_bilder_auswahl --nach-deploy
  python -m scraper.orte.restaurant_bilder_auswahl --zurueck <slug>
"""
from __future__ import annotations

import argparse
import html
import json
import logging
import math
import os
import sys
import threading
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlencode, urlparse

import httpx
from dotenv import load_dotenv

load_dotenv(Path("web/.env.local"))
load_dotenv()

from scraper.orte.ortsbilder import abrufen, umwandeln  # noqa: E402
from scraper.orte.restaurant_bilder import ALLE, ERGEBNIS, TYPEN, VORSCHAU, auswaehlen, ist_inhaber, vorschau_speichern  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

ORDNER = Path("data/restaurant_bilder")
AUSWAHL = ORDNER / "auswahl.json"
UMSTELLEN = ORDNER / "umstellen.json"
PROTOKOLL = ORDNER / "protokoll.jsonl"
ZIEL = Path("web/public/ort-bilder/restaurants")
WEB_PFAD = "/ort-bilder/restaurants"
PORT = 3650
JE_SEITE = 50
TROCKEN = False   # --trocken: nichts schreiben, nur protokollieren, was gesetzt würde
ALLE_SPERRE = threading.Lock()   # alle.json wird beim Nachladen von Google-Fotos geschrieben
# Google-Bildserver: Fotos von dort nie per Link übernehmen (Urheber unbekannt, nicht dauerhaft speichern) – Kacheln nutzen
GOOGLE_HOSTS = ("googleusercontent.com", "ggpht.com", "gstatic.com", "google.com", "googleapis.com")
QUELLE_TEXT = {"website": "Website", "google_inhaber": "Google · Inhaber", "google_nutzer": "Google · Gast"}
REITER = [("restaurant", "Restaurants"), ("cafe", "Cafés"), ("imbiss", "Imbisse"), ("kneipe", "Kneipen & Bars"),
          ("baeckerei", "Bäckereien (nicht im Guide)")]
# Art direkt umstellen (27.11.2026); Bäckereien bleiben im Datenbestand, erscheinen aber nicht auf der Website
ARTEN = {"restaurant": "Restaurant", "cafe": "Café", "imbiss": "Imbiss", "baeckerei": "Bäckerei (nicht im Guide)"}
# Eigenes Merkmal extras.kindercafe (27.11.2026): Eltern-Kind-/Kindercafé mit Spielbereich – nicht Googles „Kinderfreundlich“
KINDERCAFE_ARTEN = ("cafe", "restaurant", "imbiss")
AMBIENTE_MOTIVE = ("innenraum", "aussen", "terrasse")
ESSEN_MOTIVE = ("essen", "getraenk")


# ── Hilfen ────────────────────────────────────────────────────────────────────

def db():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def json_lesen(pfad: Path, standard):
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else standard


def json_schreiben(pfad: Path, daten) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pfad.with_suffix(".tmp")
    tmp.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(pfad)


def protokollieren(eintrag: dict) -> None:
    PROTOKOLL.parent.mkdir(parents=True, exist_ok=True)
    with PROTOKOLL.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"zeit": datetime.now().isoformat(timespec="seconds"), **eintrag}, ensure_ascii=False) + "\n")


def eintraege() -> list[dict]:
    """Ergebnisse des Gesamtlaufs (sonst der Stichprobe), nur Orte mit Kandidaten, nach Name sortiert."""
    roh = json_lesen(ALLE, None) or json_lesen(ERGEBNIS, [])
    return sorted([e for e in roh if e.get("kandidaten")], key=lambda e: e["name"].lower())


def ist_quer(k: dict) -> bool:
    return (k.get("breite") or 0) >= (k.get("hoehe") or 1) * 1.1


def komma(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


# ── dies.das-Wertung (Plan A2) ────────────────────────────────────────────────

def wertung(vorab: float | None, ambiente: dict | None, typ: str) -> dict:
    """Grund 6–9 aus dem Google-Bayes-Mittel, Ambiente-Zuschlag ±1 (nur sicher, nicht bei Kneipen), gesamt 5–10."""
    grund = 6.0 + ((vorab or 4.3) - 4.3) / 0.6 * 3.0
    grund = max(6.0, min(9.0, grund))
    amb = ambiente or {}
    zuschlag = 0.0
    if typ != "kneipe" and amb.get("sicher") and isinstance(amb.get("note"), (int, float)):
        zuschlag = max(-1.0, min(1.0, (amb["note"] - 5) * 0.3))
    wert = round(max(5.0, min(10.0, grund + zuschlag)), 1)
    return {"grund": round(grund, 1), "zuschlag": round(zuschlag, 1), "wert": wert,
            "pruefen": typ != "kneipe" and not amb.get("sicher")}


def hand_lesen(text: str) -> float | None:
    """Freifeld: '' → None; '8,5' / '8.5' → 8.5 (1–10). Ungültig → ValueError."""
    text = (text or "").strip().replace(",", ".")
    if not text:
        return None
    wert = float(text)
    if not (1.0 <= wert <= 10.0) or math.isnan(wert):
        raise ValueError("Wert muss zwischen 1 und 10 liegen")
    return round(wert, 1)


# ── Vorschläge ────────────────────────────────────────────────────────────────

def vorschlag(e: dict) -> tuple[int | str, int | str]:
    """(Titel/Ambiente, Essen): Kandidaten-Index oder 'heute' bzw. 'keins'."""
    k = e["kandidaten"]
    titel = auswaehlen(k)
    t = "heute" if titel is None or titel.get("heute") else k.index(titel)
    essen = [x for x in k if (x.get("ki") or {}).get("motiv") in ESSEN_MOTIVE and x.get("punkte", 0) >= 6 and x is not titel
             and not (x.get("ki") or {}).get("text_oder_logo")]
    essen = [x for x in essen if ist_quer(x)] or essen
    rang = {"website": 0, "google_inhaber": 1, "google_nutzer": 2}
    beste = sorted(essen, key=lambda x: (rang[x["quelle"]], -x["punkte"]))[0] if essen else None
    return t, (k.index(beste) if beste else "keins")


# ── Schreiben ─────────────────────────────────────────────────────────────────

def ort_lesen(client, ort_id: str) -> dict:
    zeilen = client.table("orte").select("id, slug, name, typ, bild_url, bild_attribution, extras").eq("id", ort_id).execute().data
    if not zeilen:
        raise RuntimeError("Ort nicht gefunden")
    return zeilen[0]


def stand(ort: dict) -> dict:
    x = ort.get("extras") or {}
    return {"bild_url": ort.get("bild_url"), "bild_attribution": ort.get("bild_attribution"),
            **{f: x.get(f) for f in ("google_foto", "bild_link", "bild_fokus", "foto_manuell", "bild_zweit", "ambiente",
                                     "ddd_wertung", "ddd_wertung_hand")}}


def erster_stand(slug: str) -> dict | None:
    """Stand vor der ersten Änderung dieser Runde (nach dem letzten Zurücksetzen)."""
    if not PROTOKOLL.exists():
        return None
    eigene = [json.loads(z) for z in PROTOKOLL.read_text(encoding="utf-8").splitlines() if z.strip()]
    eigene = [e for e in eigene if e.get("slug") == slug]
    ab = max((i for i, e in enumerate(eigene) if e["aktion"] == "zurueck"), default=-1)
    return next((e["vorher"] for e in eigene[ab + 1:] if e["aktion"] == "speichern"), None)


def kopie_ablegen(ort_id: str, slug: str, rolle: str, url: str) -> str:
    """Website-Bild als eigene WebP-Datei für den nächsten Deploy ablegen und vormerken."""
    if TROCKEN:
        return "Trockenlauf"
    daten = abrufen(url)
    if not daten:
        return "eigene Datei nicht ladbar – bleibt über den Bild-Proxy"
    name = f"{slug}.webp" if rolle == "titel" else f"{slug}-essen.webp"
    umwandeln(daten, ZIEL / name)
    liste = json_lesen(UMSTELLEN, {})
    liste[f"{ort_id}:{rolle}"] = {"ort_id": ort_id, "slug": slug, "rolle": rolle, "pfad": f"{WEB_PFAD}/{name}", "quelle_url": url}
    json_schreiben(UMSTELLEN, liste)
    return "eigene Datei abgelegt"


def vormerkung_loeschen(ort_id: str, rolle: str) -> None:
    if TROCKEN:
        return
    liste = json_lesen(UMSTELLEN, {})
    alt = liste.pop(f"{ort_id}:{rolle}", None)
    if alt:
        json_schreiben(UMSTELLEN, liste)
        datei = ZIEL / Path(alt["pfad"]).name
        if datei.exists():
            datei.unlink()


def link_kandidat(url: str, e: dict) -> dict:
    """Eigener Bildlink (z. B. von der Website des Betriebs): prüfen, ob dort wirklich ein ausreichend großes Bild liegt,
    und wie ein Website-Kandidat behandeln. Nachweis = Domain der Website des Betriebs (sonst des Bild-Servers)."""
    from scraper.orte.restaurant_bilder import bildmasse
    url = (url or "").strip()
    teile = urlparse(url)
    host = (teile.hostname or "").lower()
    if teile.scheme not in ("http", "https") or not host or host in ("localhost", "127.0.0.1") or host.endswith((".local", ".localhost")):
        raise ValueError("Link muss mit https:// beginnen")
    if host.endswith(GOOGLE_HOSTS):
        raise ValueError("Google-Fotos bitte nicht per Link, sondern über „Alle Google-Fotos laden“ wählen "
                         "(nur so steht der richtige Urheber im Nachweis)")
    daten = abrufen(url)
    masse = bildmasse(daten) if daten else None
    if not masse:
        raise ValueError("Unter dem Link liegt kein Bild")
    if masse[0] < 600:
        raise ValueError(f"Bild zu klein ({masse[0]}×{masse[1]} px)")
    web = e.get("webseite") or ""
    nachweis = (urlparse(web).hostname or host).removeprefix("www.")
    return {"quelle": "website", "url": url, "seite": web, "nachweis": nachweis, "breite": masse[0], "hoehe": masse[1], "ki": {}}


def bild_signatur(daten: bytes) -> list[int]:
    """Grober Fingerabdruck eines Bildes (16×16 Graustufen) – erkennt dasselbe Foto in anderer Größe/Komprimierung."""
    import io
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(daten)) as b:
        return list(ImageOps.exif_transpose(b).convert("L").resize((16, 16)).tobytes())


def bild_abstand(a: list[int], b: list[int]) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def google_fotos_laden(ort_id: str) -> list[int]:
    """Alle Google-Fotos eines Ortes (bis zu 10, mit Urheber) als zusätzliche Kandidaten in alle.json.
    Schon vorhandene Fotos (gleicher Fingerabdruck) werden übersprungen. Gibt die neuen Kandidaten-Indizes zurück."""
    key = os.environ["GOOGLE_PLACES_API_KEY"]
    zeile = db().table("orte").select("name, slug, google_place_id").eq("id", ort_id).execute().data
    if not zeile or not zeile[0].get("google_place_id"):
        raise RuntimeError("kein Google-Eintrag für diesen Betrieb")
    ort = zeile[0]
    try:
        r = httpx.get(f"https://places.googleapis.com/v1/places/{ort['google_place_id']}",
                      headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": "photos"}, timeout=20)
    except Exception as f:
        raise RuntimeError(f"Google nicht erreichbar ({type(f).__name__})") from None
    if r.status_code != 200:
        raise RuntimeError(f"Google-Fotoliste: HTTP {r.status_code}")
    fotos = r.json().get("photos") or []
    with ALLE_SPERRE:
        roh = json_lesen(ALLE, [])
        e = next((x for x in roh if x["id"] == ort_id), None)
        if e is None:
            raise RuntimeError("Betrieb nicht in alle.json")
        vorhanden = []
        for k in e["kandidaten"]:
            datei = VORSCHAU / k.get("vorschau", "")
            if datei.is_file():
                try:
                    vorhanden.append(bild_signatur(datei.read_bytes()))
                except Exception:
                    pass
        neu = []
        for f in fotos:
            try:
                m = httpx.get(f"https://places.googleapis.com/v1/{f['name']}/media", params={"maxWidthPx": 1200, "key": key},
                              timeout=30, follow_redirects=True)
            except Exception as fehler:   # Fehlermeldung enthielte den Schlüssel – nur den Typ loggen
                logger.warning("%s: Google-Foto nicht ladbar (%s)", ort["name"], type(fehler).__name__)
                continue
            if m.status_code != 200 or not m.headers.get("content-type", "").startswith("image/"):
                continue
            sig = bild_signatur(m.content)
            if any(bild_abstand(sig, v) < 6 for v in vorhanden):
                continue
            vorhanden.append(sig)
            autor = (f.get("authorAttributions") or [{}])[0]
            datei = VORSCHAU / "bilder" / f"{ort['slug']}-g{len(e['kandidaten'])}.webp"
            vorschau_speichern(m.content, datei)
            e["kandidaten"].append({
                "quelle": "google_inhaber" if ist_inhaber(autor.get("displayName") or "", ort["name"]) else "google_nutzer",
                "google_foto": f["name"], "breite": f.get("widthPx"), "hoehe": f.get("heightPx"),
                "autor": autor.get("displayName"), "autor_url": autor.get("uri"), "nachweis": autor.get("displayName"),
                "ki": {}, "punkte": 0, "vorschau": f"bilder/{datei.name}", "nachgeladen": True})
            neu.append(len(e["kandidaten"]) - 1)
        if neu:
            json_schreiben(ALLE, roh)
    logger.info("%s: %d Google-Fotos nachgeladen", ort["name"], len(neu))
    return neu


def google_links_reparieren() -> int:
    """Früher per Link übernommene Google-Fotos dem passenden Google-Foto (mit Urheber) zuordnen und richtig setzen."""
    alle_ein = [json.loads(z) for z in PROTOKOLL.read_text(encoding="utf-8").splitlines() if z.strip()] if PROTOKOLL.exists() else []
    letzte = {e["ort_id"]: e for e in alle_ein if e["aktion"] == "speichern"}
    auswahl = json_lesen(AUSWAHL, {})
    client = db()
    for ort_id, p in letzte.items():
        wahl = dict(auswahl.get(ort_id) or p["wahl"])
        wahl.pop("zeit", None)
        betroffen = [r for r in ("tl", "el") if wahl.get(r) and (urlparse(wahl[r]).hostname or "").endswith(GOOGLE_HOSTS)]
        if not betroffen:
            continue
        google_fotos_laden(ort_id)
        e = next(x for x in eintraege() if x["id"] == ort_id)
        neue_wahl = dict(wahl)
        for rolle in betroffen:
            daten = abrufen(wahl[rolle])
            if not daten:
                logger.warning("%s: Link %s nicht mehr ladbar", e["name"], rolle)
                continue
            sig = bild_signatur(daten)
            beste, abstand = None, 999.0
            for i, k in enumerate(e["kandidaten"]):
                if k["quelle"] == "website" or not (VORSCHAU / k.get("vorschau", "")).is_file():
                    continue
                d = bild_abstand(sig, bild_signatur((VORSCHAU / k["vorschau"]).read_bytes()))
                if d < abstand:
                    beste, abstand = i, d
            if beste is None or abstand > 12:
                logger.warning("%s: kein passendes Google-Foto für %s gefunden (bester Abstand %.1f)", e["name"], rolle, abstand)
                continue
            k = e["kandidaten"][beste]
            logger.info("%s: %s → Google-Foto von %s (Abstand %.1f)", e["name"], rolle, k.get("autor"), abstand)
            neue_wahl["t" if rolle == "tl" else "e"] = beste
            neue_wahl[rolle] = None
        if neue_wahl == wahl:
            continue
        ort_speichern(client, e, {"t": neue_wahl["t"], "e": neue_wahl["e"], "w": neue_wahl.get("w"),
                                  "tl": neue_wahl.get("tl"), "el": neue_wahl.get("el")}, wahl)
        if not TROCKEN:
            auswahl[ort_id] = {**neue_wahl, "zeit": datetime.now().strftime("%d.%m. %H:%M")}
            json_schreiben(AUSWAHL, auswahl)
    return 0


def bild_daten(k: dict) -> dict:
    if k["quelle"] == "website":
        seite = k.get("seite") or ""
        return {"art": "eigen", "bild_url": k["url"], "nachweis": (k.get("nachweis") or "")[:200],
                "link": seite if seite.startswith("https://") else None}
    autor_url = k.get("autor_url") if (k.get("autor_url") or "").startswith("https://") else None
    return {"art": "google", "google_foto": {"name": k["google_foto"], "breite": k.get("breite"), "hoehe": k.get("hoehe"),
                                             "autor": k.get("autor"), "autor_url": autor_url}, "nachweis": (k.get("autor") or "")[:200]}


def ort_speichern(client, e: dict, wahl: dict, bisher: dict | None) -> str:
    """Ein Betrieb: Titelbild, zweites Bild, Ambiente und Wertung in EINEM Update. Gibt einen Hinweis zurück."""
    ort = ort_lesen(client, e["id"])
    vorher = stand(ort)
    extras = dict(ort.get("extras") or {})
    aenderung: dict = {}
    hinweise = []
    k = e["kandidaten"]

    # Titelbild (Ambiente) – ein eigener Link geht vor
    t = wahl["t"]
    if wahl.get("tl"):
        t = "link"
    elif t != "heute" and k[t].get("heute"):
        t = "heute"
    if (t, wahl.get("tl")) != ((bisher or {}).get("t", "heute"), (bisher or {}).get("tl")):
        if t == "heute":
            alt = erster_stand(ort["slug"]) or vorher   # früher gewähltes Bild zurücknehmen
            aenderung["bild_url"], aenderung["bild_attribution"] = alt.get("bild_url"), alt.get("bild_attribution")
            for f in ("google_foto", "bild_link", "bild_fokus", "foto_manuell"):
                if alt.get(f) is None:
                    extras.pop(f, None)
                else:
                    extras[f] = alt[f]
            vormerkung_loeschen(e["id"], "titel")
        else:
            kt = link_kandidat(wahl["tl"], e) if t == "link" else k[t]
            b = bild_daten(kt)
            extras.pop("bild_fokus", None)
            fokus = (kt.get("ki") or {}).get("fokus")
            if fokus in ("oben", "unten"):
                extras["bild_fokus"] = fokus
            extras["foto_manuell"] = date.today().isoformat()
            if b["art"] == "eigen":
                extras.pop("google_foto", None)
                if b["link"]:
                    extras["bild_link"] = b["link"]
                else:
                    extras.pop("bild_link", None)
                aenderung["bild_url"], aenderung["bild_attribution"] = b["bild_url"], b["nachweis"] or None
                hinweise.append(kopie_ablegen(e["id"], ort["slug"], "titel", b["bild_url"]))
            else:
                extras.pop("bild_link", None)
                extras["google_foto"] = b["google_foto"]
                aenderung["bild_url"], aenderung["bild_attribution"] = None, b["nachweis"] or None
                vormerkung_loeschen(e["id"], "titel")
        extras["foto_version"] = int(extras.get("foto_version") or 0) + 1

    # Zweites Bild (Essen & Getränke)
    s = "link" if wahl.get("el") else wahl["e"]
    if s == "keins":
        extras.pop("bild_zweit", None)
        vormerkung_loeschen(e["id"], "zweit")
    elif (s, wahl.get("el")) != ((bisher or {}).get("e"), (bisher or {}).get("el")):
        b = bild_daten(link_kandidat(wahl["el"], e) if s == "link" else k[s])
        extras["bild_zweit"] = {kk: v for kk, v in b.items() if v is not None}
        if b["art"] == "eigen":
            hinweise.append(kopie_ablegen(e["id"], ort["slug"], "zweit", b["bild_url"]))
        else:
            vormerkung_loeschen(e["id"], "zweit")

    # Art umstellen (von Hand → typ_fest, damit imbiss_einteilen.py sie nicht zurücksetzt)
    neue_art = wahl.get("a")
    if neue_art and neue_art in ARTEN and neue_art != ort["typ"] and ort["typ"] in ARTEN:
        aenderung["typ"] = neue_art
        extras["typ_fest"] = True
        if neue_art == "imbiss":
            extras["imbiss_grund"] = f"von Hand ({date.today().strftime('%d.%m.%Y')})"
        else:
            extras.pop("imbiss_grund", None)

    # Kindercafé (nur gesendet, wenn der Haken geändert wurde)
    if wahl.get("k") is not None:
        if wahl["k"]:
            extras["kindercafe"] = True
        else:
            extras.pop("kindercafe", None)

    # Ambiente (KI) und dies.das-Wertung
    if e.get("ambiente"):
        extras["ambiente"] = {**e["ambiente"], "quelle": "ki", "stand": date.today().isoformat()}
    hand = wahl["w"]
    if hand is None:
        extras.pop("ddd_wertung_hand", None)
    else:
        extras["ddd_wertung_hand"] = hand
    extras["ddd_wertung"] = hand if hand is not None else wertung(e.get("vorab_score"), e.get("ambiente"), e["typ"])["wert"]

    aenderung["extras"] = extras
    nachher = {**vorher, **{f: aenderung[f] for f in ("bild_url", "bild_attribution", "typ") if f in aenderung},
               **{f: extras.get(f) for f in ("google_foto", "bild_link", "bild_fokus", "foto_manuell", "bild_zweit", "ambiente",
                                            "ddd_wertung", "ddd_wertung_hand", "kindercafe")}}
    if TROCKEN:
        logger.info("TROCKEN %s: %s", ort["slug"], json.dumps({f: v for f, v in nachher.items() if v != vorher.get(f)}, ensure_ascii=False)[:600])
        return "Trockenlauf"
    client.table("orte").update(aenderung).eq("id", e["id"]).execute()
    protokollieren({"ort_id": e["id"], "slug": ort["slug"], "aktion": "speichern", "wahl": wahl, "vorher": {**vorher, "typ": ort["typ"]},
                    "nachher": nachher})
    if "typ" in aenderung:   # Reiter der Auswahlseite nachziehen
        with ALLE_SPERRE:
            roh = json_lesen(ALLE, [])
            for x in roh:
                if x["id"] == e["id"]:
                    x["typ"] = aenderung["typ"]
            json_schreiben(ALLE, roh)
    return "; ".join(h for h in hinweise if h)


def speichern(daten: dict) -> dict:
    alle = {e["id"]: e for e in eintraege()}
    auswahl = json_lesen(AUSWAHL, {})
    client = db()
    gespeichert, fehler = 0, []
    for ort_id, roh in daten.items():
        e = alle.get(ort_id)
        if not e or not isinstance(roh, dict):
            continue
        try:
            wahl = {"t": "heute" if roh.get("t") in (None, "heute") else int(roh["t"]),
                    "e": "keins" if roh.get("e") in (None, "keins") else int(roh["e"]),
                    "w": hand_lesen(str(roh.get("w") or "")),
                    "a": roh.get("a") if roh.get("a") in ARTEN else None,
                    "k": roh.get("k") if isinstance(roh.get("k"), bool) else None,
                    "tl": str(roh.get("tl") or "").strip() or None,
                    "el": str(roh.get("el") or "").strip() or None}
            for feld in ("t", "e"):
                if isinstance(wahl[feld], int) and not (0 <= wahl[feld] < len(e["kandidaten"])):
                    raise ValueError("unbekanntes Bild")
            ort_speichern(client, e, wahl, auswahl.get(ort_id))
            gespeichert += 1
        except Exception as f:  # noqa: BLE001 – Fehler je Ort melden, Rest weiter speichern
            logger.warning("%s: %s", e["name"], f)
            fehler.append(f"{e['name']} ({f})")
            continue
        if not TROCKEN:
            auswahl[ort_id] = {**wahl, "zeit": datetime.now().strftime("%d.%m. %H:%M")}
            json_schreiben(AUSWAHL, auswahl)
    meldung = f"{gespeichert} Betriebe gespeichert" + (" (Trockenlauf, nichts geschrieben)" if TROCKEN else "") + \
              (f" · Fehler: {'; '.join(fehler)}" if fehler else "")
    logger.info(meldung)
    return {"meldung": meldung}


def nach_deploy() -> int:
    """Website-Bilder (Titel und zweites Bild) auf die eigene Datei umstellen – nur wenn die Datei live erreichbar ist."""
    client, liste = db(), json_lesen(UMSTELLEN, {})
    fertig = 0
    for schluessel, v in list(liste.items()):
        try:
            r = httpx.head(f"https://diesdas.events{v['pfad']}", timeout=20, follow_redirects=True)
        except Exception as f:
            logger.warning("%s: Prüfung fehlgeschlagen (%s)", v["slug"], type(f).__name__)
            continue
        if r.status_code != 200:
            logger.warning("%s: %s ist live noch nicht da (HTTP %s) – erst deployen", v["slug"], v["pfad"], r.status_code)
            continue
        ort = ort_lesen(client, v["ort_id"])
        extras = dict(ort.get("extras") or {})
        if v["rolle"] == "titel":
            if ort.get("bild_url") != v["quelle_url"]:
                liste.pop(schluessel)
                continue
            extras["foto_version"] = int(extras.get("foto_version") or 0) + 1
            aenderung = {"bild_url": v["pfad"], "extras": extras}
        else:
            zweit = dict(extras.get("bild_zweit") or {})
            if zweit.get("bild_url") != v["quelle_url"]:
                liste.pop(schluessel)
                continue
            zweit["bild_url"] = v["pfad"]
            extras["bild_zweit"] = zweit
            aenderung = {"extras": extras}
        client.table("orte").update(aenderung).eq("id", v["ort_id"]).execute()
        protokollieren({"ort_id": v["ort_id"], "slug": v["slug"], "aktion": "umstellen", "vorher": {"rolle": v["rolle"], "url": v["quelle_url"]},
                        "nachher": {"url": v["pfad"]}})
        liste.pop(schluessel)
        fertig += 1
    json_schreiben(UMSTELLEN, liste)
    logger.info("Umgestellt: %d, offen: %d", fertig, len(liste))
    return 0


def zurueck(slug: str) -> int:
    """Betrieb auf den Stand vor der ersten Änderung dieser Runde zurücksetzen (Bilder, Ambiente, Wertung)."""
    alt = erster_stand(slug)
    if not alt:
        logger.error("Keine Änderung für %s im Protokoll", slug)
        return 1
    client = db()
    zeile = client.table("orte").select("id, slug, bild_url, bild_attribution, extras").eq("slug", slug).execute().data
    if not zeile:
        logger.error("Ort %s nicht gefunden", slug)
        return 1
    ort = zeile[0]
    extras = dict(ort.get("extras") or {})
    for f in ("google_foto", "bild_link", "bild_fokus", "foto_manuell", "bild_zweit", "ambiente", "ddd_wertung", "ddd_wertung_hand"):
        if alt.get(f) is None:
            extras.pop(f, None)
        else:
            extras[f] = alt[f]
    extras["foto_version"] = int(extras.get("foto_version") or 0) + 1
    client.table("orte").update({"bild_url": alt.get("bild_url"), "bild_attribution": alt.get("bild_attribution"), "extras": extras}).eq("id", ort["id"]).execute()
    for rolle in ("titel", "zweit"):
        vormerkung_loeschen(ort["id"], rolle)
    auswahl = json_lesen(AUSWAHL, {})
    if auswahl.pop(ort["id"], None):
        json_schreiben(AUSWAHL, auswahl)
    protokollieren({"ort_id": ort["id"], "slug": slug, "aktion": "zurueck", "vorher": stand(ort), "nachher": alt})
    logger.info("%s: zurückgesetzt", slug)
    return 0


# ── Seite ─────────────────────────────────────────────────────────────────────

def kachel_text(k: dict, vt, ve, i: int | None = None) -> str:
    ki = k.get("ki") or {}
    fmt = "quer" if ist_quer(k) else ("hoch" if (k.get("hoehe") or 0) > (k.get("breite") or 0) * 1.1 else "quadrat")
    hinweis = " · <b>Vorschlag Ambiente</b>" if i is not None and i == vt else (" · <b>Vorschlag Essen</b>" if i is not None and i == ve else "")
    wer = f" · {html.escape(k.get('autor') or '')}" if k.get("nachgeladen") else ""
    note = f" · Note {ki.get('note')}" if ki.get("note") is not None else " · nachgeladen"
    return f"{QUELLE_TEXT[k['quelle']]}{wer} · {ki.get('motiv', '')} · {fmt}{note}{hinweis}"


def kachel(e: dict, i: int | str, bild: str, unter: str, t_wahl, e_wahl, nur_titel: bool = False) -> str:
    oid = e["id"]
    an_t = "an-t" if t_wahl == i else ""
    an_e = "an-e" if e_wahl == i else ""
    knoepfe = f'<label class="w t"><input type="radio" name="t-{oid}" value="{i}" {"checked" if t_wahl == i else ""}>Ambiente</label>'
    if not nur_titel:
        knoepfe += f'<label class="w e"><input type="radio" name="e-{oid}" value="{i}" {"checked" if e_wahl == i else ""}>Essen</label>'
    return f'<div class="kachel {an_t} {an_e}"><img src="{html.escape(bild)}" loading="lazy"><span class="unter">{unter}</span><span class="knoepfe">{knoepfe}</span></div>'


def abschnitt(e: dict, gespeichert: dict | None, ort_db: dict | None) -> str:
    vt, ve = vorschlag(e)
    t_wahl = gespeichert["t"] if gespeichert else vt
    e_wahl = gespeichert["e"] if gespeichert else ve
    kacheln = [kachel(e, "heute", f"/heute/{e['slug']}", "Heutiges Bild behalten", t_wahl, e_wahl, nur_titel=True)]
    for i, k in enumerate(e["kandidaten"]):
        if k.get("heute"):
            continue
        kacheln.append(kachel(e, i, f"/{k['vorschau']}", kachel_text(k, vt, ve, i), t_wahl, e_wahl))
    kein = f'<label class="kein {"an-e" if e_wahl == "keins" else ""}"><input type="radio" name="e-{e["id"]}" value="keins" {"checked" if e_wahl == "keins" else ""}>Kein Essensbild</label>'
    amb = e.get("ambiente") or {}
    w = wertung(e.get("vorab_score"), amb, e["typ"])
    hand = gespeichert.get("w") if gespeichert else (ort_db or {}).get("ddd_wertung_hand")
    if e["typ"] == "kneipe":
        erklaerung = f"Grund {komma(w['grund'])} (bisheriger Score) · Ambiente bewertest du selbst (KI meint {amb.get('note', '–')}/10)"
    else:
        zuschlag = f"{'+' if w['zuschlag'] >= 0 else '−'}{komma(abs(w['zuschlag']))}"
        erklaerung = (f"Grund {komma(w['grund'])} (bisheriger Score) · Ambiente {zuschlag} (KI {amb.get('note', '–')}/10, "
                      f"{'sicher' if amb.get('sicher') else '<span class=rot>unsicher – bitte prüfen</span>'})")
    art_feld = ""
    if e["typ"] in ARTEN:
        optionen = "".join(f'<option value="{w}" {"selected" if w == e["typ"] else ""}>{t}</option>' for w, t in ARTEN.items())
        art_feld = f'<label class="art">Art <select class="art-wahl" data-alt="{e["typ"]}">{optionen}</select></label>'
    if e["typ"] in KINDERCAFE_ARTEN:
        kc = bool((ort_db or {}).get("kindercafe"))
        art_feld += (f'<label class="art kc"><input type="checkbox" class="kc-wahl" data-alt="{"1" if kc else ""}" '
                     f'{"checked" if kc else ""}> Kindercafé</label>')
    tl = (gespeichert or {}).get("tl") or ""
    el = (gespeichert or {}).get("el") or ""
    status = f'<span class="ok">gespeichert {html.escape(gespeichert.get("zeit", ""))}</span>' if gespeichert else ""
    web = f'<a href="{html.escape(e["webseite"])}" target="_blank" rel="noopener">Website</a>' if e.get("webseite") else "keine Website"
    return f"""<section data-id="{e['id']}"><h2>{html.escape(e['name'])} <small>{html.escape(e.get('stadtteil') or '')} · {web}</small> {status}
<button type="button" class="passt">Auswahl passt</button> {art_feld}</h2>
<div class="wertung">dies.das-Wertung <b>{komma(w['wert'])}</b> <span class="muted">{erklaerung}</span>
<label>eigener Wert <input class="hand" type="text" inputmode="decimal" placeholder="leer = {komma(w['wert'])}" value="{'' if hand is None else komma(float(hand))}" size="5"></label></div>
<p class="amb">{html.escape(amb.get('begruendung', ''))}</p>
<div class="kacheln">{''.join(kacheln)}</div><div class="zeile2">{kein} <button type="button" class="google">Alle Google-Fotos laden</button> <span class="google-info muted"></span></div>
<div class="links">
<label class="link"><span>Eigenes <b>Ambientebild</b> per Link (geht vor):</span><input class="link-t" type="url" placeholder="https://… direkter Link zum Bild" value="{html.escape(tl)}"><img class="vor" src="{html.escape(tl)}" alt=""></label>
<label class="link"><span>Eigenes <b>Essensbild</b> per Link (geht vor):</span><input class="link-e" type="url" placeholder="https://… direkter Link zum Bild" value="{html.escape(el)}"><img class="vor" src="{html.escape(el)}" alt=""></label>
</div></section>"""


def seite(typ: str, nr: int) -> str:
    alle = eintraege()
    auswahl = json_lesen(AUSWAHL, {})
    reiter = []
    for wert, name in REITER:
        liste = [e for e in alle if e["typ"] == wert]
        fertig = sum(1 for e in liste if e["id"] in auswahl)
        reiter.append(f'<a class="{"aktiv" if wert == typ else ""}" href="/?{urlencode({"typ": wert})}">{name} <span>{fertig}/{len(liste)}</span></a>')
    liste = [e for e in alle if e["typ"] == typ]
    seiten = max(1, math.ceil(len(liste) / JE_SEITE))
    nr = max(1, min(nr, seiten))
    teil = liste[(nr - 1) * JE_SEITE: nr * JE_SEITE]
    try:   # eigener Wert, der schon in der Datenbank steht (nur diese Seite abfragen)
        zeilen = db().table("orte").select("id, hand:extras->ddd_wertung_hand, kc:extras->kindercafe").in_("id", [e["id"] for e in teil]).execute().data
        ort_db = {z["id"]: {"ddd_wertung_hand": z.get("hand"), "kindercafe": z.get("kc") is True} for z in zeilen}
    except Exception as f:  # noqa: BLE001 – Seite auch ohne Datenbank anzeigen
        logger.warning("Datenbank nicht lesbar (%s)", type(f).__name__)
        ort_db = {}
    def seitenlinks() -> str:
        links = []
        for s in range(1, seiten + 1):
            stueck = liste[(s - 1) * JE_SEITE: s * JE_SEITE]
            fertig = sum(1 for e in stueck if e["id"] in auswahl)
            klasse = "aktiv" if s == nr else ("voll" if fertig == len(stueck) and stueck else "")
            links.append(f'<a class="{klasse}" href="/?{urlencode({"typ": typ, "seite": s})}">{s}<small>{fertig}/{len(stueck)}</small></a>')
        return f'<nav class="seiten">Seite {nr} von {seiten}: {"".join(links)}</nav>'
    name_typ = dict(REITER)[typ]
    try:   # Läuft der Bilderlauf noch? Dann verschieben sich die alphabetischen Seiten.
        gesamt = (db().table("orte").select("id", count="exact").in_("typ", list(TYPEN)).eq("aktiv", True)
                  .gte("qualitaets_score", 7).limit(1).execute().count) or 0
    except Exception:  # noqa: BLE001
        gesamt = 0
    lauf = (f'<p class="lauf">Der Bilderlauf ist noch nicht fertig: {len(alle)} von {gesamt} Betrieben bearbeitet. Bis zum Ende '
            f'kommen laufend Betriebe dazu, und die Seiten verschieben sich. Am besten erst danach loslegen.</p>') if gesamt and len(alle) < gesamt - 5 else ""
    inhalt = "".join(abschnitt(e, auswahl.get(e["id"]), ort_db.get(e["id"])) for e in teil) or "<p>Für diese Art liegen noch keine Ergebnisse vor (Bilderlauf läuft noch?).</p>"
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bilder · {name_typ} · Seite {nr}</title><style>
body{{font-family:system-ui,sans-serif;margin:0 auto;max-width:1320px;padding:0 16px 90px;background:#fafaf7;color:#1d1d1b}}
.kopf{{position:sticky;top:0;z-index:5;background:#fafaf7;padding:10px 0 8px;border-bottom:1px solid #e2e2dc}}
.reiter{{display:flex;gap:6px;flex-wrap:wrap}} .reiter a{{padding:7px 12px;border-radius:999px;border:1px solid #ccc;text-decoration:none;color:#1d1d1b;font-weight:600}}
.reiter a.aktiv{{background:#1d1d1b;color:#fff;border-color:#1d1d1b}} .reiter span{{font-weight:400;font-size:12px;opacity:.75}}
.seiten{{margin-top:8px;font-size:13px;display:flex;gap:4px;flex-wrap:wrap;align-items:center}}
.seiten a{{padding:3px 8px;border:1px solid #ddd;border-radius:6px;text-decoration:none;color:#1d1d1b}} .seiten a.aktiv{{background:#c9a227;border-color:#c9a227;font-weight:700}}
.seiten a.voll{{background:#e3f1e7}} .seiten small{{display:block;font-size:10px;color:#666}}
h1{{font-size:20px;margin:8px 0}} h2{{font-size:17px;margin:26px 0 4px}} small{{font-weight:400;color:#666}}
.wertung{{font-size:14px;margin:4px 0;display:flex;gap:10px;flex-wrap:wrap;align-items:center}} .wertung b{{font-size:18px}}
.wertung input{{font-size:14px;padding:3px 6px;border:1px solid #bbb;border-radius:6px;width:5em}} .muted{{color:#555;font-size:13px}}
.rot{{color:#b3261e}} .lauf{{background:#fff4d6;border:1px solid #e6c65c;border-radius:8px;padding:8px 12px;font-size:14px}} .amb{{font-size:13px;color:#555;margin:0 0 8px}}
.kacheln{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}}
.kachel{{border-radius:10px;padding:4px;border:3px solid transparent;background:#fff;position:relative}}
.kachel.an-t{{border-color:#c9a227}} .kachel.an-e{{border-color:#2f6fd6}} .kachel.an-t.an-e{{border-color:#c9a227 #2f6fd6 #2f6fd6 #c9a227}}
.kachel img{{width:100%;aspect-ratio:16/10;object-fit:cover;border-radius:7px;display:block;background:#ddd}}
.unter{{display:block;font-size:12px;color:#555;padding:4px 2px}} .knoepfe{{display:flex;gap:6px}}
.w,.kein{{font-size:12px;border:1px solid #bbb;border-radius:6px;padding:3px 8px;cursor:pointer;user-select:none}}
.w input,.kein input{{position:absolute;opacity:0;pointer-events:none}}
.w.t:has(input:checked){{background:#c9a227;border-color:#c9a227;font-weight:700}} .w.e:has(input:checked){{background:#2f6fd6;border-color:#2f6fd6;color:#fff;font-weight:700}}
.google{{font-size:12px;border:1px solid #888;background:#fff;border-radius:6px;padding:3px 8px;cursor:pointer;margin-left:8px}}
.art{{font-size:12px;font-weight:400;margin-left:8px}} .art select{{font-size:12px;padding:2px 4px}}
.kc:has(input:checked){{background:#e8f0fe;border-radius:6px;padding:2px 6px;font-weight:700}}
.art select.geaendert{{background:#fff4d6;border-color:#e6c65c;font-weight:700}}
.kein:has(input:checked){{background:#2f6fd6;color:#fff;border-color:#2f6fd6}} .zeile2{{margin-top:8px}}
.links{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}} .link{{font-size:13px;display:flex;flex-direction:column;gap:4px}}
.link input{{font-size:13px;padding:5px 8px;border:1px solid #bbb;border-radius:6px}} .link .vor{{max-width:220px;max-height:140px;object-fit:cover;border-radius:6px}}
.link .vor[src=""]{{display:none}} @media (max-width:700px){{.links{{grid-template-columns:1fr}}}}
.ok{{font-size:12px;color:#1b7f3b;font-weight:600}} section{{border-bottom:1px solid #e2e2dc;padding-bottom:14px}}
.passt{{font-size:12px;margin-left:8px;border:1px solid #c9a227;background:#fff;border-radius:6px;padding:3px 8px;cursor:pointer}}
section.geprueft .passt{{background:#c9a227;font-weight:700}} section.geprueft h2::after{{content:" ✓";color:#1b7f3b}}
.leiste{{position:fixed;left:0;right:0;bottom:0;background:#1d1d1b;color:#fff;padding:12px 16px;display:flex;gap:16px;align-items:center;justify-content:center;z-index:6}}
.leiste button{{background:#c9a227;color:#1d1d1b;border:0;border-radius:8px;padding:10px 18px;font-weight:700;font-size:15px;cursor:pointer}}
.leiste button:disabled{{opacity:.5}}
</style></head><body>
<div class="kopf"><nav class="reiter">{''.join(reiter)}</nav>{seitenlinks()}</div>
{lauf}<h1>{name_typ} · Seite {nr} von {seiten}</h1>
<p class="muted">Gold = <b>Ambiente</b> (Titelbild), Blau = <b>Essen &amp; Getränke</b> (zweites Bild). Vorausgewählt ist der KI-Vorschlag.
Gespeichert werden nur Betriebe mit ✓ (Bild angeklickt, eigener Wert eingetragen oder „Auswahl passt“). Leeres Wertfeld = gerechneter Wert.</p>
{inhalt}
{seitenlinks()}
<div class="leiste"><span id="info"></span><button id="speichern">Speichern und hochladen</button></div>
<script>
function zaehlen(){{var n=document.querySelectorAll('section.geprueft').length;
  document.getElementById('info').textContent=n+' Betriebe auf dieser Seite zum Speichern markiert';document.getElementById('speichern').disabled=!n}}
function markieren(el){{el.closest('section').classList.add('geprueft');zaehlen()}}
function rahmen(s){{s.querySelectorAll('.kachel').forEach(function(k){{
  var t=k.querySelector('.w.t input'),e=k.querySelector('.w.e input');
  k.classList.toggle('an-t',!!(t&&t.checked));k.classList.toggle('an-e',!!(e&&e.checked))}})}}
function radiosVerbinden(wurzel){{wurzel.querySelectorAll('input[type=radio]').forEach(function(r){{
  if(r.dataset.v)return;r.dataset.v='1';r.addEventListener('click',function(){{rahmen(r.closest('section'));markieren(r)}})}})}}
radiosVerbinden(document);
document.querySelectorAll('.google').forEach(function(b){{b.addEventListener('click',async function(){{
  var s=b.closest('section'),info=s.querySelector('.google-info');b.disabled=true;info.textContent='lädt … (bis zu 10 Fotos, etwa 10–20 Sekunden)';
  try{{var a=await fetch('/google?id='+encodeURIComponent(s.dataset.id),{{method:'POST'}});var d=await a.json();
    s.querySelector('.kacheln').insertAdjacentHTML('beforeend',d.html||'');radiosVerbinden(s);info.textContent=d.meldung;}}
  catch(e){{info.textContent='Fehler: '+e;b.disabled=false}}
}})}});
document.querySelectorAll('.hand').forEach(function(i){{i.addEventListener('input',function(){{markieren(i)}})}});
document.querySelectorAll('.art-wahl').forEach(function(a){{a.addEventListener('change',function(){{
  a.classList.toggle('geaendert',a.value!==a.dataset.alt);markieren(a)}})}});
document.querySelectorAll('.kc-wahl').forEach(function(c){{c.addEventListener('change',function(){{markieren(c)}})}});
document.querySelectorAll('.link input').forEach(function(i){{i.addEventListener('input',function(){{
  var v=i.value.trim(),img=i.parentNode.querySelector('.vor');img.src=(v.indexOf('https://')===0||v.indexOf('http://')===0)?v:'';markieren(i)}})}});
document.querySelectorAll('.passt').forEach(function(b){{b.addEventListener('click',function(){{b.closest('section').classList.toggle('geprueft');zaehlen()}})}});
zaehlen();
window.addEventListener('beforeunload',function(ev){{if(document.querySelector('section.geprueft')){{ev.preventDefault();ev.returnValue=''}}}});
document.getElementById('speichern').addEventListener('click',async function(){{
  var b=this,info=document.getElementById('info'),daten={{}};
  document.querySelectorAll('section.geprueft').forEach(function(s){{var id=s.dataset.id;
    var t=s.querySelector('input[name="t-'+id+'"]:checked'),e=s.querySelector('input[name="e-'+id+'"]:checked');
    daten[id]={{t:t?t.value:'heute',e:e?e.value:'keins',w:s.querySelector('.hand').value,
      tl:s.querySelector('.link-t').value,el:s.querySelector('.link-e').value,
      a:s.querySelector('.art-wahl')?s.querySelector('.art-wahl').value:null}};
    var kc=s.querySelector('.kc-wahl');if(kc&&kc.checked!==(kc.dataset.alt==='1'))daten[id].k=kc.checked}});
  b.disabled=true;info.textContent='Speichere … (Website-Bilder werden dabei geladen, das dauert etwas)';
  try{{var a=await fetch('/speichern',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(daten)}});var d=await a.json();
    info.textContent=d.meldung;document.querySelectorAll('section.geprueft').forEach(function(s){{s.classList.remove('geprueft')}});
    setTimeout(function(){{location.reload()}},2500);}}
  catch(e){{info.textContent='Fehler: '+e;b.disabled=false}}
}});
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # Zugriffe nicht einzeln loggen
        pass

    def senden(self, status: int, inhalt: bytes, art: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", art)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(inhalt)

    def do_GET(self):  # noqa: N802
        teile = urlparse(self.path)
        pfad = unquote(teile.path)
        if pfad == "/":
            q = parse_qs(teile.query)
            typ = (q.get("typ") or ["restaurant"])[0]
            typ = typ if typ in dict(REITER) else "restaurant"
            try:
                nr = int((q.get("seite") or ["1"])[0])
            except ValueError:
                nr = 1
            return self.senden(200, seite(typ, nr).encode("utf-8"), "text/html; charset=utf-8")
        if pfad.startswith("/bilder/"):
            datei = (VORSCHAU / pfad.lstrip("/")).resolve()
            if VORSCHAU.resolve() in datei.parents and datei.is_file():
                return self.senden(200, datei.read_bytes(), "image/webp")
        if pfad.startswith("/heute/"):
            slug = pfad.split("/", 2)[2]
            try:
                r = httpx.get(f"https://diesdas.events/ort-foto/{slug}", timeout=30, follow_redirects=True)
                if r.status_code == 200:
                    return self.senden(200, r.content, r.headers.get("content-type", "image/jpeg"))
            except Exception:
                pass
        self.senden(404, b"nicht gefunden", "text/plain")

    def do_POST(self):  # noqa: N802
        if self.path.startswith("/google?"):
            ort_id = (parse_qs(urlparse(self.path).query).get("id") or [""])[0]
            try:
                neu = google_fotos_laden(ort_id)
                e = next(x for x in eintraege() if x["id"] == ort_id)
                kacheln = "".join(kachel(e, i, f"/{e['kandidaten'][i]['vorschau']}", kachel_text(e["kandidaten"][i], None, None), None, None)
                                  for i in neu)
                antwort = {"meldung": f"{len(neu)} weitere Google-Fotos" if neu else "keine weiteren Google-Fotos", "html": kacheln}
                return self.senden(200, json.dumps(antwort, ensure_ascii=False).encode(), "application/json")
            except Exception as f:  # noqa: BLE001
                return self.senden(500, json.dumps({"meldung": f"Fehler: {f}", "html": ""}, ensure_ascii=False).encode(), "application/json")
        if self.path != "/speichern":
            return self.senden(404, b"", "text/plain")
        laenge = int(self.headers.get("Content-Length") or 0)
        try:
            daten = json.loads(self.rfile.read(laenge) or b"{}")
            antwort = speichern(daten if isinstance(daten, dict) else {})
            self.senden(200, json.dumps(antwort, ensure_ascii=False).encode(), "application/json")
        except Exception as f:  # noqa: BLE001
            logger.exception("Speichern fehlgeschlagen")
            self.senden(500, json.dumps({"meldung": f"Fehler: {f}"}, ensure_ascii=False).encode(), "application/json")


def main():
    global TROCKEN
    p = argparse.ArgumentParser(description="Guide-Bilder und dies.das-Wertung auswählen und live setzen")
    p.add_argument("--nach-deploy", action="store_true")
    p.add_argument("--zurueck", metavar="SLUG")
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--trocken", action="store_true", help="nichts schreiben (Test)")
    p.add_argument("--google-links-reparieren", action="store_true", help="per Link übernommene Google-Fotos richtig zuordnen")
    args = p.parse_args()
    TROCKEN = args.trocken
    if args.nach_deploy:
        return nach_deploy()
    if args.zurueck:
        return zurueck(args.zurueck)
    if args.google_links_reparieren:
        return google_links_reparieren()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    logger.info("Auswahlseite: http://127.0.0.1:%d%s (Strg+C beendet)", args.port, " – TROCKENLAUF" if TROCKEN else "")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
