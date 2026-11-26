"""
restaurant_bilder.py – DiesDasDüsseldorf
Bessere Bilder für den Restaurant-Guide (Plan docs/plan-restaurantguide-2026-11-26.md, Abschnitt B) und eine
KI-Einschätzung des Ambientes (Grundlage für die dies.das-Bewertung, Wunsch des Auftraggebers 26.11.2026).

Rangfolge der Quellen je Ort:
  1. Website des Betriebs (og:image, Bilder der Startseite und bis zu 2 Unterseiten wie Galerie/Über uns)
  2. Google-Foto, das der Betrieb selbst hochgeladen hat (Autor ≈ Name des Betriebs)
  3. Google-Foto eines Nutzers (nur als Rückfall)
Querformat wird bevorzugt. Jedes Kandidatenbild bekommt eine KI-Note (Claude, Bildeingabe, ein Aufruf je Ort mit
allen Kandidaten), dazu eine Einschätzung des Ambientes (stylisch/schick/cool/stilvoll) mit Sicherheitsangabe.

Regeln: robots.txt, mindestens 2 s zwischen Abrufen derselben Website, Projekt-User-Agent wie ortsbilder.py.
Google-Bilder werden nicht dauerhaft gespeichert (nur kleine Vorschau für die lokale Durchsicht, gitignored).
Schreibt nichts in die Datenbank und nichts nach web/public/ort-bilder (das passiert erst beim Ausrollen).

Nutzung (im Repo-Stamm, Python aus DD/.venv):
  python -m scraper.orte.restaurant_bilder --stichprobe 30      → Probelauf, Vorschau unter web/public/_probe/
  python -m scraper.orte.restaurant_bilder --nur-vorschau        → Vorschau aus vorhandenen Ergebnissen neu bauen
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import logging
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv(Path("web/.env.local"))
load_dotenv()

from scraper.orte.ortsbilder import abrufen, kopfzeilen, robots_erlaubt  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

MODELL = "claude-opus-5-5"
TYPEN = ("restaurant", "cafe", "imbiss", "kneipe")   # Kneipen & Bars seit 26.11. (Auswahlseite mit Trenner)
MIN_SCORE_WEBSITE = 7
ORDNER = Path("data/restaurant_bilder")
ERGEBNIS = ORDNER / "probe.json"
ALLE = ORDNER / "alle.json"                    # Gesamtlauf (fortsetzbar), Grundlage der Auswahlseite
VORSCHAU = ORDNER / "vorschau"                 # Vorschaubilder für die Auswahlseite (gitignored, nur lokal)
VORSCHAU_KANTE = 640
PARALLEL = 4
PAUSE_S = 2.0
MIN_BREITE = 900
MAX_WEBSITE_KANDIDATEN = 8
MAX_GOOGLE_INHABER = 3
MAX_GOOGLE_NUTZER = 2
KI_KANTE = 640                                 # längste Kante der Bilder für die KI
UNTERSEITEN = re.compile(r"galerie|gallery|impression|bilder|fotos|photos|ueber|über|about|ambiente|restaurant|cafe|location|raeume|räume", re.I)
KEIN_BILD = re.compile(r"logo|icon|favicon|sprite|placeholder|blank|pixel|badge|button|banner-ad|tripadvisor|google|facebook|instagram|"
                       r"whatsapp|payment|paypal|visa|mastercard|lieferando|wolt|ubereats|\.svg|\.gif", re.I)

SCHEMA = {
    "type": "object",
    "properties": {
        "bilder": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "nr": {"type": "integer"},
                    "note": {"type": "integer"},
                    "motiv": {"type": "string", "enum": ["essen", "getraenk", "innenraum", "aussen", "terrasse", "team_personen",
                                                          "logo_text", "speisekarte", "sonstiges"]},
                    "text_oder_logo": {"type": "boolean"},
                    "personen_im_fokus": {"type": "boolean"},
                    "stockfoto_verdacht": {"type": "boolean"},
                    "fokus": {"type": "string", "enum": ["oben", "mitte", "unten"]},
                },
                "required": ["nr", "note", "motiv", "text_oder_logo", "personen_im_fokus", "stockfoto_verdacht", "fokus"],
                "additionalProperties": False,
            },
        },
        "ambiente": {
            "type": "object",
            "properties": {
                "note": {"type": "integer"},
                "sicher": {"type": "boolean"},
                "begruendung": {"type": "string"},
            },
            "required": ["note", "sicher", "begruendung"],
            "additionalProperties": False,
        },
    },
    "required": ["bilder", "ambiente"],
    "additionalProperties": False,
}

SYSTEM = """Du bewertest Fotos für den Düsseldorfer Stadtguide dies.das.düsseldorf (Restaurants, Cafés, Imbisse, Kneipen und Bars).
Du bekommst den Namen und die Art des Lokals und nummerierte Fotos (Website des Lokals oder Google).

1. Für JEDES Foto:
   - „note“ 1–10: Wie gut eignet es sich als großes Titelbild einer Guide-Karte im Querformat? Hoch: scharf, gutes
     Licht, ansprechender Bildaufbau, zeigt das Lokal (Innenraum, Außenansicht, Terrasse) oder appetitliche Gerichte
     bzw. Getränke, macht Lust hinzugehen. Niedrig: unscharf, dunkel, schief, Collage, Screenshot, Grafik,
     Speisekarte, Text oder Logo im Bild, Personen im Fokus, beliebiges Stockfoto, nichtssagendes Detail.
   - „motiv“, „text_oder_logo“, „personen_im_fokus“, „stockfoto_verdacht“ wie im Schema.
   - „fokus“: Welcher senkrechte Bereich muss bei einem Querformat-Anschnitt sichtbar bleiben (oben/mitte/unten)?
2. „ambiente“ für das LOKAL insgesamt, nur nach dem, was die Fotos von Räumen, Terrasse oder Fassade zeigen:
   - „note“ 1–10: Wirkt das Ambiente stylisch, schick, cool oder stilvoll? 5 = gewöhnlich/solide, 8+ = deutlich
     stilvoll mit erkennbarem Konzept, 3 und weniger = unattraktiv oder heruntergekommen. Essen allein sagt nichts
     über das Ambiente.
   - „sicher“: true nur, wenn mindestens zwei aussagekräftige Fotos von Räumen/Terrasse/Fassade vorliegen und
     das Bild eindeutig ist. Sonst false.
   - „begruendung“: ein kurzer Satz auf Deutsch.
"""


# ── Hilfen ────────────────────────────────────────────────────────────────────

def normal_name(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\b(restaurant|cafe|café|bistro|imbiss|bar|düsseldorf|duesseldorf|neuss|ratingen|gmbh|ug|the|das|der|die)\b", " ", s)
    return re.sub(r"[^a-z0-9äöüß]+", "", s)


def ist_inhaber(autor: str, ortsname: str) -> bool:
    """Google-Foto vom Betrieb selbst? Der Autor heißt dann wie der Betrieb (unscharfer Vergleich)."""
    a, n = normal_name(autor), normal_name(ortsname)
    if not a or not n:
        return False
    if len(n) >= 4 and (n in a or a in n):
        return True
    return SequenceMatcher(None, a, n).ratio() >= 0.7


def bildmasse(daten: bytes) -> tuple[int, int] | None:
    from PIL import Image
    try:
        with Image.open(io.BytesIO(daten)) as b:
            return b.size
    except Exception:
        return None


def ki_vorschau(daten: bytes) -> str:
    """Bild für die KI verkleinern (JPEG, längste Kante KI_KANTE) → base64."""
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(daten)) as roh:
        b = ImageOps.exif_transpose(roh).convert("RGB")
    b.thumbnail((KI_KANTE, KI_KANTE))
    puffer = io.BytesIO()
    b.save(puffer, "JPEG", quality=80)
    return base64.standard_b64encode(puffer.getvalue()).decode()


def vorschau_speichern(daten: bytes, ziel: Path, kante: int = VORSCHAU_KANTE) -> None:
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(daten)) as roh:
        b = ImageOps.exif_transpose(roh).convert("RGB")
    b.thumbnail((kante, kante))
    ziel.parent.mkdir(parents=True, exist_ok=True)
    b.save(ziel, "WEBP", quality=72)


# ── Quelle 1: Website ─────────────────────────────────────────────────────────

def _groesste_aus_srcset(srcset: str) -> str | None:
    beste, breite = None, -1
    for teil in srcset.split(","):
        stuecke = teil.strip().split()
        if not stuecke:
            continue
        w = int(stuecke[1][:-1]) if len(stuecke) > 1 and stuecke[1].endswith("w") and stuecke[1][:-1].isdigit() else 0
        if w > breite:
            beste, breite = stuecke[0], w
    return beste


_SPERRE = threading.Lock()


def host_warten(host: str, letzter: dict) -> None:
    """Mindestens PAUSE_S zwischen zwei Abrufen derselben Website – auch bei parallelen Arbeitern (Platz reservieren)."""
    with _SPERRE:
        jetzt = time.time()
        frei = max(jetzt, letzter.get(host, 0) + PAUSE_S)
        letzter[host] = frei
    if frei > jetzt:
        time.sleep(frei - jetzt)


def seite_holen(url: str, letzter: dict) -> str | None:
    host_warten(urlparse(url).netloc, letzter)
    try:
        r = httpx.get(url, headers=kopfzeilen(url), timeout=25, follow_redirects=True)
        if r.status_code != 200 or "html" not in r.headers.get("content-type", ""):
            return None
        return r.text
    except Exception as e:
        logger.info("Website nicht ladbar: %s (%s)", url, e)
        return None


def bild_urls(html: str, basis: str) -> tuple[list[str], list[str]]:
    """(Bild-URLs in Fundreihenfolge, Unterseiten-Links derselben Domain)"""
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for meta in soup.find_all("meta", attrs={"property": ["og:image", "og:image:url"]}) + soup.find_all("meta", attrs={"name": "twitter:image"}):
        if meta.get("content"):
            urls.append(meta["content"])
    for img in soup.find_all(["img", "source"]):
        kandidat = None
        for attr in ("srcset", "data-srcset"):
            if img.get(attr):
                kandidat = _groesste_aus_srcset(img[attr])
                break
        kandidat = kandidat or img.get("data-src") or img.get("data-lazy-src") or img.get("src")
        if kandidat:
            urls.append(kandidat)
    for tag in soup.find_all(style=re.compile(r"background(-image)?\s*:", re.I)):
        urls += re.findall(r"url\(['\"]?([^'\")]+)['\"]?\)", tag["style"])
    host = urlparse(basis).netloc
    gesehen, sauber = set(), []
    for u in urls:
        if u.startswith("data:"):
            continue
        absolut = urljoin(basis, u.strip())
        if absolut in gesehen or KEIN_BILD.search(absolut) or not absolut.startswith("http"):
            continue
        gesehen.add(absolut)
        sauber.append(absolut)
    links = []
    for a in soup.find_all("a", href=True):
        ziel = urljoin(basis, a["href"]).split("#")[0]
        if urlparse(ziel).netloc == host and ziel.rstrip("/") != basis.rstrip("/") and UNTERSEITEN.search(ziel + " " + a.get_text(" ")):
            if ziel not in links:
                links.append(ziel)
    return sauber, links[:2]


def website_kandidaten(ort: dict, robots: dict, letzter: dict) -> list[dict]:
    web = (ort.get("webseite") or "").strip()
    if not web.startswith("http"):
        return []
    if not robots_erlaubt(web, robots):
        logger.info("%s: robots.txt sperrt %s", ort["name"], web)
        return []
    html = seite_holen(web, letzter)
    if not html:
        return []
    urls, unterseiten = bild_urls(html, web)
    for seite in unterseiten:
        if robots_erlaubt(seite, robots):
            h = seite_holen(seite, letzter)
            if h:
                urls += [u for u in bild_urls(h, seite)[0] if u not in urls]
    kandidaten = []
    for u in urls:
        if len(kandidaten) >= MAX_WEBSITE_KANDIDATEN:
            break
        if not robots_erlaubt(u, robots):
            continue
        host_warten(urlparse(u).netloc, letzter)
        daten = abrufen(u)
        masse = bildmasse(daten) if daten else None
        if not masse or masse[0] < MIN_BREITE:
            continue
        kandidaten.append({"quelle": "website", "url": u, "seite": web, "breite": masse[0], "hoehe": masse[1], "_daten": daten,
                           "nachweis": urlparse(web).netloc.removeprefix("www.")})
    return kandidaten


# ── Quelle 2/3: Google ────────────────────────────────────────────────────────

def google_kandidaten(ort: dict, key: str) -> tuple[list[dict], int]:
    """Bis zu MAX_GOOGLE_INHABER Inhaberfotos und MAX_GOOGLE_NUTZER Nutzerfotos (Querformat zuerst). → (Kandidaten, Abrufe)"""
    pid = ort.get("google_place_id")
    if not pid:
        return [], 0
    abrufe = 0
    try:
        r = httpx.get(f"https://places.googleapis.com/v1/places/{pid}",
                      headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": "photos"}, timeout=20)
        abrufe += 1
        if r.status_code != 200:
            logger.warning("%s: Google-Fotoliste nicht ladbar (HTTP %s)", ort["name"], r.status_code)
            return [], abrufe
        fotos = r.json().get("photos") or []
    except Exception as e:
        logger.warning("%s: Google-Fotoliste nicht ladbar (%s)", ort["name"], type(e).__name__)
        return [], abrufe
    def quer(f):
        return (f.get("widthPx") or 0) >= (f.get("heightPx") or 1) * 1.2
    inhaber, nutzer = [], []
    for f in fotos:
        autor = ((f.get("authorAttributions") or [{}])[0])
        eintrag = {"name": f.get("name"), "breite": f.get("widthPx"), "hoehe": f.get("heightPx"),
                   "autor": autor.get("displayName"), "autor_url": autor.get("uri")}
        (inhaber if ist_inhaber(eintrag["autor"] or "", ort["name"]) else nutzer).append(eintrag)
    auswahl = sorted(inhaber, key=lambda f: not quer(f))[:MAX_GOOGLE_INHABER] + sorted(nutzer, key=lambda f: not quer(f))[:MAX_GOOGLE_NUTZER]
    # Das heutige Bild (erstes Google-Foto) tritt immer mit an – ein Wechsel muss besser sein als der Ist-Zustand
    heute = next((e for e in inhaber + nutzer if e["name"] == (fotos[0].get("name") if fotos else None)), None)
    if heute and heute not in auswahl:
        auswahl.append(heute)
    kandidaten = []
    for f in auswahl:
        try:
            r = httpx.get(f"https://places.googleapis.com/v1/{f['name']}/media",
                          params={"maxWidthPx": 1200, "key": key}, timeout=30, follow_redirects=True)
            abrufe += 1
        except Exception as e:
            # Nur den Fehlertyp loggen – die Fehlermeldung enthielte die Adresse mit dem API-Schlüssel
            logger.warning("%s: Google-Foto nicht ladbar (%s)", ort["name"], type(e).__name__)
            continue
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/"):
            logger.warning("%s: Google-Foto nicht ladbar (HTTP %s)", ort["name"], r.status_code)
            continue
        quelle = "google_inhaber" if f in inhaber else "google_nutzer"
        kandidaten.append({"quelle": quelle, "google_foto": f["name"], "breite": f["breite"], "hoehe": f["hoehe"],
                           "autor": f["autor"], "autor_url": f["autor_url"], "_daten": r.content, "nachweis": f["autor"],
                           "heute": f is heute})
    return kandidaten, abrufe


# ── KI-Bewertung und Auswahl ──────────────────────────────────────────────────

def ki_bewerten(client, ort: dict, kandidaten: list[dict]) -> tuple[dict, dict]:
    inhalt: list[dict] = [{"type": "text", "text": f"Lokal: {ort['name']} ({ort['typ']}, {ort.get('stadtteil') or 'Düsseldorf'})"}]
    for i, k in enumerate(kandidaten, start=1):
        herkunft = {"website": "Website des Lokals", "google_inhaber": "Google, vom Lokal hochgeladen", "google_nutzer": "Google, von einem Gast"}[k["quelle"]]
        heute = ", heutiges Titelbild" if k.get("heute") else ""
        inhalt.append({"type": "text", "text": f"Foto {i} ({herkunft}{heute}, {k['breite']}×{k['hoehe']} px):"})
        inhalt.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": ki_vorschau(k["_daten"])}})
    antwort = client.messages.create(
        model=MODELL,
        max_tokens=8000,
        system=SYSTEM,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": inhalt}],
    )
    if antwort.stop_reason in ("refusal", "max_tokens"):
        raise RuntimeError(f"KI-Antwort unbrauchbar ({antwort.stop_reason})")
    roh = next(b.text for b in antwort.content if b.type == "text")
    return json.loads(roh), {"ein": antwort.usage.input_tokens, "aus": antwort.usage.output_tokens}


def punkte(k: dict) -> float:
    """Sortierwert innerhalb einer Quelle: KI-Note, Querformat bevorzugt, Mängel abziehen."""
    b = k.get("ki") or {}
    p = float(b.get("note", 0))
    seiten = (k["breite"] or 1) / max(1, k["hoehe"] or 1)
    p += 0.5 if 1.3 <= seiten <= 2.2 else (-1.5 if seiten < 1.0 else 0)
    p -= 3 if b.get("text_oder_logo") else 0
    p -= 1.5 if b.get("personen_im_fokus") else 0
    p -= 2 if b.get("stockfoto_verdacht") else 0
    p -= 4 if b.get("motiv") in ("logo_text", "speisekarte") else 0
    # Das Lokal selbst zeigt mehr als ein Teller (Probelauf 26.11.: donecake-Innenraum schöner als Donuts)
    p += 1 if b.get("motiv") in ("innenraum", "aussen", "terrasse") else 0
    return round(p, 2)


def auswaehlen(kandidaten: list[dict]) -> dict | None:
    """Website vor Inhaber-Google vor Nutzer-Google – jeweils nur mit Punktwert ≥ 7. Sonst das beste insgesamt, aber
    nur ab 5 Punkten; darunter bleibt das heutige Bild (Probelauf 26.11.: ein Stockfoto mit 2,5 Punkten rutschte durch).

    Vorrang (Auftraggeber 26.11.2026): Ein einigermaßen schönes Innenraumfoto (KI-Note ≥ 6, ohne Text/Logo) schlägt
    jedes Essensfoto – Essen ist nur Rückfall. Unter den Innenraumfotos gilt wieder die Rangfolge der Quellen."""
    rang = {"website": 0, "google_inhaber": 1, "google_nutzer": 2}
    innen = [k for k in kandidaten if (k.get("ki") or {}).get("motiv") == "innenraum" and (k.get("ki") or {}).get("note", 0) >= 6
             and not (k.get("ki") or {}).get("text_oder_logo")]
    # Querformat geht auch hier vor (Hochformat nur, wenn es kein Innenraumfoto im Querformat gibt)
    innen = [k for k in innen if (k["breite"] or 0) >= (k["hoehe"] or 1) * 1.1] or innen
    if innen:
        return sorted(innen, key=lambda k: (rang[k["quelle"]], -k["punkte"]))[0]
    for quelle in ("website", "google_inhaber", "google_nutzer"):
        gut = sorted([k for k in kandidaten if k["quelle"] == quelle and k["punkte"] >= 7], key=lambda k: -k["punkte"])
        if gut:
            return gut[0]
    rest = sorted(kandidaten, key=lambda k: -k["punkte"])
    if rest and rest[0]["punkte"] >= 5:
        return rest[0]
    return next((k for k in kandidaten if k.get("heute")), None)


# ── Stichprobe, Lauf, Vorschau ────────────────────────────────────────────────

def orte_laden() -> list[dict]:
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"])
    zeilen, seite = [], 0
    while True:
        teil = (db.table("orte").select("id, name, slug, typ, stadtteil, webseite, google_place_id, qualitaets_score, bild_url, bild_attribution, extras")
                .in_("typ", list(TYPEN)).eq("aktiv", True).gte("qualitaets_score", MIN_SCORE_WEBSITE)
                .order("id").range(seite * 1000, seite * 1000 + 999).execute().data or [])
        zeilen += teil
        if len(teil) < 1000:
            break
        seite += 1
    return zeilen


def stichprobe(orte: list[dict], anzahl: int) -> list[dict]:
    """Gemischt nach Art (40 % Restaurants, 35 % Cafés, 25 % Imbisse), mit und ohne Website, fester Zufall."""
    zufall = random.Random(20261126)
    anteile = {"restaurant": round(anzahl * 0.4), "cafe": round(anzahl * 0.35)}
    anteile["imbiss"] = anzahl - sum(anteile.values())
    auswahl = []
    for typ, n in anteile.items():
        liste = [o for o in orte if o["typ"] == typ]
        mit = [o for o in liste if o.get("webseite")]
        ohne = [o for o in liste if not o.get("webseite")]
        n_ohne = min(len(ohne), max(1, n // 6))
        auswahl += zufall.sample(ohne, n_ohne) + zufall.sample(mit, min(len(mit), n - n_ohne))
    return auswahl


def ort_bearbeiten(ort: dict, client, key: str, robots: dict, letzter: dict, abruf_zaehler: dict) -> dict:
    kandidaten = website_kandidaten(ort, robots, letzter)
    g, n = google_kandidaten(ort, key)
    abruf_zaehler["google"] += n
    kandidaten += g
    ergebnis = {"id": ort["id"], "name": ort["name"], "slug": ort["slug"], "typ": ort["typ"], "stadtteil": ort.get("stadtteil"),
                "webseite": ort.get("webseite"), "score": ort.get("qualitaets_score"),
                "vorab_score": (ort.get("extras") or {}).get("vorab_score"), "kandidaten": [], "gewaehlt": None, "ambiente": None}
    if not kandidaten:
        return ergebnis
    ki, verbrauch = ki_bewerten(client, ort, kandidaten)
    abruf_zaehler["ein"] += verbrauch["ein"]
    abruf_zaehler["aus"] += verbrauch["aus"]
    noten = {b["nr"]: b for b in ki.get("bilder", [])}
    for i, k in enumerate(kandidaten, start=1):
        k["ki"] = noten.get(i, {})
        k["punkte"] = punkte(k)
        datei = VORSCHAU / "bilder" / f"{ort['slug']}-{i}.webp"
        vorschau_speichern(k.pop("_daten"), datei)
        k["vorschau"] = f"bilder/{datei.name}"
    ergebnis["kandidaten"] = kandidaten
    gew = auswaehlen(kandidaten)
    ergebnis["gewaehlt"] = kandidaten.index(gew) if gew else None
    ergebnis["ambiente"] = ki.get("ambiente")
    return ergebnis


def vorschau_bauen(ergebnisse: list[dict]) -> Path:
    zeilen = []
    for e in ergebnisse:
        g = e["kandidaten"][e["gewaehlt"]] if e["gewaehlt"] is not None else None
        amb = e.get("ambiente") or {}
        quelle_text = {"website": "Website", "google_inhaber": "Google · Inhaber", "google_nutzer": "Google · Gast"}
        kand = "".join(
            f'<figure class="{"gew" if i == e["gewaehlt"] else ""}"><img src="{k["vorschau"]}" loading="lazy">'
            f'<figcaption>{quelle_text[k["quelle"]]} · {k["breite"]}×{k["hoehe"]}<br>Note {k.get("ki", {}).get("note", "–")} · '
            f'{k.get("ki", {}).get("motiv", "")} · <b>{k["punkte"]}</b>{"<br>Autor: " + (k.get("autor") or "") if k["quelle"] != "website" else ""}</figcaption></figure>'
            for i, k in enumerate(e["kandidaten"]))
        zeilen.append(f"""
<section>
  <h2>{e['name']} <small>{e['typ']} · {e.get('stadtteil') or ''} · Score {e.get('score')} · {f'<a href="{e["webseite"]}" target="_blank">Website</a>' if e.get('webseite') else 'keine Website'}</small></h2>
  <div class="vn">
    <figure><img src="/ort-foto/{e['slug']}" loading="lazy"><figcaption>Vorher (heutiges Bild)</figcaption></figure>
    <figure>{f'<img src="{g["vorschau"]}">' if g else '<div class="leer">kein Kandidat</div>'}<figcaption>Nachher: {'<b>bleibt wie heute</b> · ' if g and g.get("heute") else ''}{quelle_text[g["quelle"]] if g else '–'} {('· ' + (g.get("nachweis") or '')) if g else ''} · Ausschnitt {g.get("ki", {}).get("fokus", "") if g else ''}</figcaption></figure>
  </div>
  <p class="amb">Ambiente: <b>{amb.get('note', '–')}</b>/10 {'(sicher)' if amb.get('sicher') else '<span class="unsicher">(unsicher → du entscheidest)</span>'} – {amb.get('begruendung', '')}</p>
  <details><summary>Alle {len(e['kandidaten'])} Kandidaten</summary><div class="kand">{kand}</div></details>
</section>""")
    html = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bilder-Probelauf</title><style>
body{{font-family:system-ui,sans-serif;margin:0 auto;max-width:1200px;padding:16px;background:#fafaf7;color:#1d1d1b}}
h1{{font-size:24px}} h2{{font-size:18px;margin:28px 0 8px}} small{{font-weight:400;color:#666}}
.vn{{display:grid;grid-template-columns:1fr 1fr;gap:12px}} .vn img,.vn .leer{{width:100%;aspect-ratio:16/10;object-fit:cover;border-radius:8px;background:#ddd}}
.leer{{display:flex;align-items:center;justify-content:center;color:#666}}
figure{{margin:0}} figcaption{{font-size:12px;color:#555;margin-top:4px}}
.kand{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;margin-top:8px}}
.kand img{{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:6px}} .kand .gew img{{outline:3px solid #c9a227}}
.amb{{font-size:14px}} .unsicher{{color:#b3261e}} section{{border-bottom:1px solid #ddd;padding-bottom:12px}}
@media (max-width:640px){{.vn{{grid-template-columns:1fr}}}}
</style></head><body><h1>Bilder-Probelauf: {len(ergebnisse)} Betriebe</h1>
<p>Links das heutige Bild (live), rechts der Vorschlag. Rangfolge: Website → Google (Inhaber) → Google (Gast), Querformat bevorzugt.
Goldrahmen = gewählt. Punkte = KI-Note ± Format/Mängel. Nur lokal, nicht veröffentlicht.</p>
{''.join(zeilen)}</body></html>"""
    pfad = VORSCHAU / "index.html"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(html, encoding="utf-8")
    return pfad


def gesamtlauf(client, key: str) -> int:
    """Alle sichtbaren Orte (TYPEN), fortsetzbar: schon bearbeitete (auch aus der Stichprobe) werden übersprungen."""
    bestand = {e["id"]: e for e in (json.loads(ALLE.read_text(encoding="utf-8")) if ALLE.exists() else []) if not e.get("fehler")}
    if ERGEBNIS.exists():
        for e in json.loads(ERGEBNIS.read_text(encoding="utf-8")):
            if not e.get("fehler") and e.get("kandidaten"):
                bestand.setdefault(e["id"], e)
    orte = orte_laden()
    for o in orte:   # Grundwert für die dies.das-Wertung auch bei übernommenen Einträgen
        if o["id"] in bestand:
            bestand[o["id"]]["vorab_score"] = (o.get("extras") or {}).get("vorab_score")
            bestand[o["id"]]["typ"] = o["typ"]
    offen = [o for o in orte if o["id"] not in bestand]
    logger.info("Gesamtlauf: %d Orte, davon %d schon bearbeitet, %d offen (%d parallel)", len(orte), len(bestand), len(offen), PARALLEL)
    robots, letzter, zaehler = {}, {}, {"google": 0, "ein": 0, "aus": 0}
    sperre = threading.Lock()

    def speichern() -> None:
        tmp = ALLE.with_suffix(".tmp")
        tmp.write_text(json.dumps(list(bestand.values()), ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(ALLE)

    def arbeit(ort: dict) -> dict:
        try:
            return ort_bearbeiten(ort, client, key, robots, letzter, zaehler)
        except Exception as fehler:  # noqa: BLE001 – ein Ort darf den Lauf nicht abbrechen
            logger.warning("%s: %s", ort["name"], fehler)
            return {"id": ort["id"], "name": ort["name"], "slug": ort["slug"], "typ": ort["typ"], "kandidaten": [], "gewaehlt": None,
                    "ambiente": None, "fehler": str(fehler)}

    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        for n, f in enumerate(as_completed([pool.submit(arbeit, o) for o in offen]), start=1):
            e = f.result()
            with sperre:
                bestand[e["id"]] = e
                if n % 5 == 0 or n == len(offen):
                    speichern()
            logger.info("%d/%d %s: %d Kandidaten, Ambiente %s", n, len(offen), e["name"], len(e["kandidaten"]), (e.get("ambiente") or {}).get("note"))
    speichern()
    logger.info("Google-Abrufe: %d · KI-Token: %d ein, %d aus (≈ %.2f $)", zaehler["google"], zaehler["ein"], zaehler["aus"],
                zaehler["ein"] / 1e6 * 4 + zaehler["aus"] / 1e6 * 20)
    return 0


def main():
    p = argparse.ArgumentParser(description="Restaurant-Guide: bessere Bilder + Ambiente-Einschätzung")
    p.add_argument("--stichprobe", type=int, default=30)
    p.add_argument("--alle", action="store_true", help="alle sichtbaren Orte (fortsetzbar)")
    p.add_argument("--nur-vorschau", action="store_true")
    args = p.parse_args()
    ORDNER.mkdir(parents=True, exist_ok=True)
    if args.nur_vorschau:
        logger.info("Vorschau: %s", vorschau_bauen(json.loads(ERGEBNIS.read_text(encoding="utf-8"))))
        return 0
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    key = os.environ["GOOGLE_PLACES_API_KEY"]
    if args.alle:
        return gesamtlauf(client, key)
    auswahl = stichprobe(orte_laden(), args.stichprobe)
    logger.info("Stichprobe: %d Orte", len(auswahl))
    robots, letzter, zaehler, ergebnisse = {}, {}, {"google": 0, "ein": 0, "aus": 0}, []
    for n, ort in enumerate(auswahl, start=1):
        try:
            e = ort_bearbeiten(ort, client, key, robots, letzter, zaehler)
        except Exception as fehler:  # noqa: BLE001 – ein Ort darf den Lauf nicht abbrechen
            logger.warning("%s: %s", ort["name"], fehler)
            e = {"id": ort["id"], "name": ort["name"], "slug": ort["slug"], "typ": ort["typ"], "kandidaten": [], "gewaehlt": None,
                 "ambiente": None, "fehler": str(fehler)}
        ergebnisse.append(e)
        g = e["kandidaten"][e["gewaehlt"]]["quelle"] if e.get("gewaehlt") is not None else "–"
        logger.info("%d/%d %s: %d Kandidaten, gewählt: %s, Ambiente %s", n, len(auswahl), ort["name"], len(e["kandidaten"]), g,
                    (e.get("ambiente") or {}).get("note"))
        ERGEBNIS.write_text(json.dumps(ergebnisse, ensure_ascii=False, indent=1), encoding="utf-8")
    logger.info("Google-Abrufe: %d · KI-Token: %d ein, %d aus (≈ %.2f $)", zaehler["google"], zaehler["ein"], zaehler["aus"],
                zaehler["ein"] / 1e6 * 4 + zaehler["aus"] / 1e6 * 20)
    logger.info("Vorschau: %s", vorschau_bauen(ergebnisse))
    return 0


if __name__ == "__main__":
    sys.exit(main())
