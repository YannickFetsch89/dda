"""
google_lauf.py – DiesDasDüsseldorf
Google-Lauf für den Weihnachtsmarkt-Guide (Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, 4.4 und 4.6, Schritt 7b/7c).

Entscheidung des Auftraggebers (17.11.2026): Google-Fotos und Google-Score trotz der EWR-Bedingungen nutzen, Score nur intern.
Deshalb so sparsam wie möglich:
- In orte wird nur google_place_id und der fertige Score (Teilwerte, google_bezug, stand) gespeichert – nie rating/userRatingCount.
- Rohwerte (Sterne, Anzahl, Google-Namen) stehen nur im lokalen Bericht data/weihnachtsmaerkte/score_bericht.md (gitignored,
  nach der Score-Freigabe löschen).
- Foto-Kandidaten und Vorschaubilder bleiben lokal (data/weihnachtsmaerkte/google/, gitignored), bis der Auftraggeber sie
  gesichtet hat (keine erkennbaren Gesichter). Das Foto setzt dann nur die Foto-SQL (Auftraggeber führt sie aus).

Nutzung:
  python -m scraper.weihnachtsmaerkte.google_lauf suchen --dry-run   # nennt Einträge und Kosten, fragt nichts ab
  python -m scraper.weihnachtsmaerkte.google_lauf suchen             # Textsuche (kostet), place_id + Score + Bericht + Kandidaten
  python -m scraper.weihnachtsmaerkte.google_lauf fotos [--dry-run]  # Vorschaubilder der Kandidaten laden (kostet)
  python -m scraper.weihnachtsmaerkte.google_lauf sql --sichtung DATEI   # Foto-SQL aus der Sichtung erzeugen
"""
from __future__ import annotations

import argparse
import json
import logging
import math
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
DATEN = _WURZEL / "data" / "weihnachtsmaerkte"
GOOGLE = DATEN / "google"                 # Rohantworten, Kandidaten, Vorschaubilder (gitignored)
FOTOS = GOOGLE / "fotos"
KANDIDATEN = GOOGLE / "kandidaten.json"
BERICHT = DATEN / "score_bericht.md"      # Rohwerte nur hier (gitignored, E12)

API_BASE = "https://places.googleapis.com/v1"
PREIS_SUCHE = 0.035   # USD je Textsuche mit Bewertung (Enterprise), Preisseite 11.11.2026
PREIS_FOTO = 0.007    # USD je Place Photo
MAX_FOTOS = 10
VORSCHAU_BREITE = 800
MAX_ABSTAND_M = 300.0
FELDER = "places.id,places.displayName,places.location,places.rating,places.userRatingCount,places.photos,places.primaryType,places.googleMapsUri"
TYP = "weihnachtsmarkt"

# Google-Eintrag ist der Markt selbst (Bewertungen meinen den Markt), wenn der Name so klingt – sonst der Ort (Schloss, Arcaden)
# Nur Namen mit Weihnachts-/Winterbezug zählen als Markt – „Carlsplatz Markt“ oder „Bilk S“ sind andere Orte (Lauf 17.11.)
_MARKT_WORT = re.compile(r"weihnacht|winter|advent|christ|nikolaus|zauber|on ice|eisbahn|riesenrad|wheel of|roncalli", re.I)
# Gezieltere Suchtexte, wo der Name allein nichts oder Falsches findet (Lauf 17.11.)
SUCHTEXT = {
    "innenstadt": "Weihnachtsmarkt Düsseldorf Marktplatz Rathaus",
    "altstadt-markt": "Weihnachtsmarkt Flinger Straße Düsseldorf",
    "maerchen-markt": "Weihnachtsmarkt Schadowplatz Düsseldorf",
    "bilk-arcaden": "Weihnachtsmarkt Düsseldorf Arcaden Bilk",
    "areal-boehler": "Weihnachtszauber Areal Böhler Düsseldorf",
}
_FUELL = {"der", "die", "das", "dem", "den", "am", "an", "im", "in", "auf", "und", "duesseldorf", "dusseldorf", "deg", "the"}
ANGEBOT = ("eisbahn", "riesenrad", "karussell", "kindereisenbahn", "kinderprogramm", "puppenbuehne", "buehnenprogramm",
           "kunsthandwerk", "krippe")


# ---------------------------------------------------------------------------
# Reine Funktionen (getestet)
# ---------------------------------------------------------------------------

def woerter(text: str) -> set[str]:
    t = (text or "").lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    return {w for w in re.split(r"[^a-z0-9]+", t) if len(w) >= 3 and w not in _FUELL}


def abstand_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def treffer_waehlen(name: str, lat: float, lng: float, orte: list[dict]) -> tuple[dict | None, str]:
    """Nur Orte ≤ 300 m; dann der mit den meisten gemeinsamen Namenswörtern (Gleichstand: mehr Bewertungen)."""
    nah = []
    for o in orte:
        loc = o.get("location") or {}
        if loc.get("latitude") is None:
            continue
        if abstand_m((lat, lng), (loc["latitude"], loc["longitude"])) <= MAX_ABSTAND_M:
            nah.append(o)
    if not nah:
        return None, "kein_treffer"
    eigene = woerter(name)
    bewertet = sorted(nah, key=lambda o: (-len(eigene & woerter((o.get("displayName") or {}).get("text", ""))),
                                          -(o.get("userRatingCount") or 0)))
    beste = bewertet[0]
    if eigene & woerter((beste.get("displayName") or {}).get("text", "")):
        return beste, "name"
    return (beste, "einziger") if len(nah) == 1 else (None, "mehrdeutig")


def google_bezug(treffer: dict | None) -> str:
    if not treffer:
        return "kein"
    return "markt" if _MARKT_WORT.search((treffer.get("displayName") or {}).get("text", "")) else "ort"


def oeffnungstage(saison: dict | None) -> int:
    """Zahl der Tage mit Wochenzeit im Zeitraum, ohne Sondertage „zu“."""
    from datetime import date as d, timedelta

    if not saison or not saison.get("von") or not saison.get("bis") or not saison.get("zeiten"):
        return 0
    tage = {t for z in saison["zeiten"] for t in z["tage"]}
    zu = {s["datum"] for s in saison.get("sonder") or [] if s.get("geschlossen")}
    namen = ["mo", "di", "mi", "do", "fr", "sa", "so"]
    n, tag, ende = 0, d.fromisoformat(saison["von"]), d.fromisoformat(saison["bis"])
    while tag <= ende:
        if namen[tag.weekday()] in tage and tag.isoformat() not in zu:
            n += 1
        tag += timedelta(days=1)
    return n


def score_berechnen(eintraege: list[dict], google: dict[str, dict]) -> dict[str, dict]:
    """
    Plan 4.6 (Cursor-Prüfung 1/2): Teilwerte 0–1, gewichtet, ×10, eine Nachkommastelle, begrenzt 0–10.
    eintraege: {schluessel, attraktion, ist_gruppe, merkmale, art, saison, eintritt, anfahrt, teile_merkmale}
    google: schluessel → {bezug, rating, anzahl} (nur für die Rechnung, wird nicht gespeichert).
    Attraktionen bekommen keinen Score.
    """
    # Plan 4.6 mit Randfällen (Cursor-Check Stufe 1b): Markt-Treffer = google_bezug „markt“ (auch mit 0 Bewertungen);
    # kein Markt-Treffer → Beliebtheit 0,5 ohne Reichweite; Markt-Treffer, aber alle n = 0 → Bayes 0,5, Reichweite 0
    def _n(g: dict) -> int | None:
        return int(g["anzahl"]) if g.get("bezug") == "markt" and isinstance(g.get("anzahl"), (int, float)) else (0 if g.get("bezug") == "markt" else None)

    markt_treffer = {s: g for s, g in google.items() if g.get("bezug") == "markt"}
    markt = {s: g for s, g in markt_treffer.items() if (_n(g) or 0) > 0 and g.get("rating") is not None}
    C = sum(g["rating"] for g in markt.values()) / len(markt) if markt else None
    n_max = max((_n(g) or 0 for g in markt.values()), default=0)
    m = 100
    ergebnis = {}
    for e in eintraege:
        if e.get("attraktion"):
            continue
        g = google.get(e["schluessel"]) or {}
        n = _n(g)
        if not markt_treffer:
            bayes, reichweite = 0.5, None                        # kein einziger Markt-Treffer
        elif n_max == 0:
            bayes, reichweite = 0.5, 0.0                         # Treffer, aber niemand hat Bewertungen
        elif n is not None and C is not None:
            rating = g.get("rating") if n > 0 and g.get("rating") is not None else C
            B = (n * rating + m * C) / (n + m)
            bayes = min(1.0, max(0.0, (B - 3.5) / 1.5))
            reichweite = math.log10(n + 1) / math.log10(n_max + 1)
        else:
            bayes, reichweite = 0.5, 0.5                         # Ort statt Markt: neutral
        if reichweite is None:   # kein einziger Markt-Treffer: Reichweite entfällt, Gewicht geht an Bayes
            beliebtheit = bayes
        else:
            beliebtheit = (bayes * 0.30 + reichweite * 0.15) / 0.45
        merk = {**(e.get("teile_merkmale") or {}), **(e.get("merkmale") or {})}
        punkte = sum(1.0 if (merk.get(k) or {}).get("wert") == "ja" else 0.5 if (merk.get(k) or {}).get("wert") == "teilweise" else 0.0
                     for k in ANGEBOT)
        if "kunsthandwerk" in (e.get("art") or []) and (merk.get("kunsthandwerk") or {}).get("wert") != "ja":
            punkte += 1.0
        angebot = min(1.0, punkte / 4)
        tage = min(1.0, oeffnungstage(e.get("saison")) / 35)
        eintritt = {"frei": 1.0, "kostenpflichtig": 0.0}.get(((e.get("eintritt") or {}).get("wert")), 0.5)
        nutzwert = (tage * 10 + eintritt * 5) / 15
        erreichbarkeit = 1.0 if (e.get("anfahrt") or {}).get("haltestellen") else 0.5
        summe = beliebtheit * 0.45 + angebot * 0.25 + nutzwert * 0.15 + erreichbarkeit * 0.15
        ergebnis[e["schluessel"]] = {
            "wert": round(min(10.0, max(0.0, summe * 10)), 1),
            "teile": {"beliebtheit": round(beliebtheit, 3), "angebot": round(angebot, 3), "nutzwert": round(nutzwert, 3),
                      "erreichbarkeit": round(erreichbarkeit, 3)},
            "google_bezug": g.get("bezug") or "kein",
        }
    return ergebnis


def doppelte_aufloesen(google: dict[str, dict], lage: dict[str, tuple[float, float]], treffer_je: dict) -> list[str]:
    """Schlüssel, die einen Google-Eintrag abgeben müssen: bei gleicher place_id behält ihn nur der nächstgelegene Eintrag."""
    nach_id: dict[str, list[str]] = {}
    for s, g in google.items():
        nach_id.setdefault(g["place_id"], []).append(s)
    weg = []
    for pid, liste in nach_id.items():
        if len(liste) < 2:
            continue
        def dist(s):
            loc = (treffer_je[s][0] or {}).get("location") or {}
            return abstand_m(lage[s], (loc.get("latitude", 0.0), loc.get("longitude", 0.0)))
        liste.sort(key=dist)
        weg += liste[1:]
    return sorted(weg)


def foto_kandidaten(treffer: dict | None) -> list[dict]:
    aus = []
    for f in ((treffer or {}).get("photos") or [])[:MAX_FOTOS]:
        autor = (f.get("authorAttributions") or [{}])[0]
        aus.append({"name": f.get("name"), "breite": f.get("widthPx"), "hoehe": f.get("heightPx"),
                    "autor": autor.get("displayName"), "autor_url": autor.get("uri")})
    return [f for f in aus if f["name"]]


def sql_aus_sichtung(sichtung: dict, kandidaten: dict, heute: str) -> str:
    """Foto-SQL wie bei Spielplätzen/Clubs; Schlüssel = extras.weihnachtsmarkt.schluessel. sichtung: {schluessel: {foto, grund}}."""
    zeilen = [f"-- Weihnachtsmarkt-Fotos (Sichtung {heute}) – im Supabase SQL-Editor ausführen.",
              "-- Nur Fotos ohne erkennbare Gesichter (Entscheidung W4). foto_manuell schützt die Auswahl vor späteren Läufen.", ""]
    for s in sorted(sichtung):
        wahl = sichtung[s]
        if wahl.get("foto") is None:
            zeilen.append(f"-- {s}: kein Foto – {wahl.get('grund', '')}")
            continue
        f = kandidaten[s][wahl["foto"]]
        foto = json.dumps({k: f[k] for k in ("name", "breite", "hoehe", "autor", "autor_url")}, ensure_ascii=False)
        autor = (f.get("autor") or "Google").replace("'", "''")
        fokus = f", 'bild_fokus', '{wahl['fokus']}'" if re.fullmatch(r"(100|[1-9]?\d)%", str(wahl.get("fokus") or "")) else ""
        zeilen.append(f"-- {s}: Foto von {f.get('autor') or 'Google'} – {wahl.get('grund', '')}")
        zeilen.append(
            "UPDATE public.orte SET bild_attribution = '" + autor + "', bild_url = NULL, extras = extras || jsonb_build_object("
            f"'google_foto', '{foto.replace(chr(39), chr(39) * 2)}'::jsonb, 'foto_manuell', '{heute}', "
            f"'foto_version', COALESCE((extras->>'foto_version')::int + 1, 1){fokus}) "
            f"WHERE typ = '{TYP}' AND extras->'weihnachtsmarkt'->>'schluessel' = '{s}';")
    return "\n".join(zeilen) + "\n"


# ---------------------------------------------------------------------------
# Google und Datenbank
# ---------------------------------------------------------------------------

def _headers(felder: str) -> dict:
    from config import GOOGLE_PLACES_API_KEY

    return {"Content-Type": "application/json", "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY or "", "X-Goog-FieldMask": felder}


def textsuche(text: str, lat: float, lng: float) -> list[dict]:
    body = {"textQuery": text, "languageCode": "de", "regionCode": "DE", "maxResultCount": 5,
            "locationBias": {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": 500.0}}}
    for versuch in range(3):
        time.sleep(0.5)
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


def eintraege_laden(db) -> list[dict]:
    from scraper.orte.google_places import alle_zeilen

    zeilen = alle_zeilen(db, "orte", "id, name, slug, stadtteil, latitude, longitude, aktiv, extras",
                         lambda q: q.eq("typ", TYP))
    return sorted([z for z in zeilen if z.get("latitude") is not None], key=lambda z: z["name"])


def _stadt(z: dict) -> str:
    return z["stadtteil"] if z.get("stadtteil") in ("Neuss", "Ratingen") else "Düsseldorf"


def suchen(dry_run: bool) -> None:
    from database.client import get_supabase_client

    db = get_supabase_client()
    zeilen = eintraege_laden(db)
    offen = [z for z in zeilen if not (GOOGLE / f"{z['extras'][TYP]['schluessel']}.json").exists()]
    logger.info("%d Einträge, davon %d noch ohne Abfrage → Kosten ca. %.2f $ (Freikontingent 1.000 Textsuchen/Monat)%s",
                len(zeilen), len(offen), len(offen) * PREIS_SUCHE, " [Dry-Run, keine Abfrage]" if dry_run else "")
    if dry_run:
        return
    GOOGLE.mkdir(parents=True, exist_ok=True)
    for z in offen:
        s = z["extras"][TYP]["schluessel"]
        try:
            orte = textsuche(SUCHTEXT.get(s) or f"{z['name']} {_stadt(z)}", z["latitude"], z["longitude"])
            (GOOGLE / f"{s}.json").write_text(json.dumps(orte, ensure_ascii=False), encoding="utf-8")
            logger.info("%s: %d Google-Orte", z["name"], len(orte))
        except Exception as e:  # noqa: BLE001
            logger.error("Textsuche für %s fehlgeschlagen: %s", z["name"], e)

    google, kandidaten, treffer_je = {}, {}, {}
    for z in zeilen:
        s = z["extras"][TYP]["schluessel"]
        datei = GOOGLE / f"{s}.json"
        if not datei.exists():
            continue
        orte = json.loads(datei.read_text(encoding="utf-8"))
        t, art = treffer_waehlen(z["name"], z["latitude"], z["longitude"], orte)
        treffer_je[s] = (t, art, orte)
        # Nur echte Markt-Einträge zählen (Bewertungen und Fotos meinen sonst einen anderen Ort)
        if t and google_bezug(t) != "markt":
            art = f"{art}_ohne_marktbezug"
            treffer_je[s] = (t, art, orte)
            t = None
        if t:
            google[s] = {"bezug": google_bezug(t), "rating": t.get("rating"), "anzahl": t.get("userRatingCount"), "place_id": t["id"]}
            kandidaten[s] = foto_kandidaten(t)

    # Derselbe Google-Eintrag für mehrere Einträge (z. B. Schadowplatz für Märchen- und Schadow-Markt): nur der nächstgelegene
    for s_doppelt in doppelte_aufloesen(google, {z["extras"][TYP]["schluessel"]: (z["latitude"], z["longitude"]) for z in zeilen}, treffer_je):
        google.pop(s_doppelt, None)
        kandidaten.pop(s_doppelt, None)
        t, art, orte = treffer_je[s_doppelt]
        treffer_je[s_doppelt] = (t, f"{art}_doppelt", orte)

    # Score (Teile der Gruppe zählen beim Angebot mit; Attraktionen ohne Score)
    nach_schluessel = {z["extras"][TYP]["schluessel"]: z for z in zeilen}
    eintraege = []
    for z in zeilen:
        wm = z["extras"][TYP]
        teile = [t["extras"][TYP] for t in zeilen if t["extras"][TYP].get("gruppe") == wm["schluessel"]] if wm.get("ist_gruppe") else []
        teile_merkmale = {k: v for t in teile for k, v in (t.get("merkmale") or {}).items()}
        saisons = wm.get("saisons") or {}
        saison = max((v for v in saisons.values() if v.get("bis")), key=lambda v: v["bis"], default=None)
        eintraege.append({"schluessel": wm["schluessel"], "attraktion": wm.get("attraktion"), "ist_gruppe": wm.get("ist_gruppe"),
                          "merkmale": wm.get("merkmale"), "art": wm.get("art"), "saison": saison, "eintritt": wm.get("eintritt"),
                          "anfahrt": wm.get("anfahrt"), "teile_merkmale": teile_merkmale})
    scores = score_berechnen(eintraege, google)
    heute = date.today().isoformat()

    geschrieben = 0
    for s, z in nach_schluessel.items():
        g = google.get(s)
        try:
            aktuell = (db.table("orte").select("extras").eq("id", z["id"]).execute().data or [{}])[0].get("extras") or {}
            wm = dict(aktuell.get(TYP) or {})
            if s in scores:
                alt = wm.get("score") or {}
                wm["score"] = {**scores[s], "stand": heute, **({"manuell": alt["manuell"]} if "manuell" in alt else {})}
            update = {"extras": {**aktuell, TYP: wm}}
            # einzige dauerhaft gespeicherte Google-Angabe; ohne Markt-Treffer wieder leeren (falsche Zuordnung entfernen)
            update["google_place_id"] = g["place_id"] if g else None
            db.table("orte").update(update).eq("id", z["id"]).execute()
            geschrieben += 1
        except Exception as e:  # noqa: BLE001
            logger.error("Speichern für %s fehlgeschlagen: %s", z["name"], e)

    KANDIDATEN.write_text(json.dumps(kandidaten, ensure_ascii=False, indent=1), encoding="utf-8")
    bericht_schreiben(zeilen, treffer_je, google, scores)
    logger.info("Fertig: %d Einträge geschrieben, %d mit Google-Treffer, %d Foto-Kandidaten; Bericht %s",
                geschrieben, len(google), sum(len(k) for k in kandidaten.values()), BERICHT)


def bericht_schreiben(zeilen, treffer_je, google, scores) -> None:
    """Lokaler Prüfbericht mit Rohwerten (gitignored, E12) – nach der Score-Freigabe löschen."""
    z_sort = sorted(zeilen, key=lambda z: -(scores.get(z["extras"][TYP]["schluessel"]) or {}).get("wert", -1))
    aus = ["# Score-Bericht Weihnachtsmärkte (lokal, nicht einchecken, nach Freigabe löschen)", "",
           "Rohwerte von Google stehen nur hier. In der Datenbank liegen nur place_id und der fertige Score.",
           "Prüfen: Passt der Google-Eintrag (google_bezug „markt“ = Bewertungen meinen den Markt)? Bei Bedarf `score_manuell`",
           "und `top5_rang` in data/weihnachtsmaerkte/maerkte.csv setzen und den Import erneut laufen lassen.", "",
           "| Rang | Eintrag | Score | Beliebtheit | Angebot | Nutzwert | Erreichb. | Google-Name | Bezug | Sterne | Anzahl | Zuordnung |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, z in enumerate(z_sort, 1):
        s = z["extras"][TYP]["schluessel"]
        sc = scores.get(s)
        t, art, _ = treffer_je.get(s, (None, "nicht abgefragt", []))
        g = google.get(s) or {}
        teile = (sc or {}).get("teile", {})
        aus.append(f"| {i if sc else '–'} | {z['name']} | {sc['wert'] if sc else 'Attraktion'} | {teile.get('beliebtheit', '')} | "
                   f"{teile.get('angebot', '')} | {teile.get('nutzwert', '')} | {teile.get('erreichbarkeit', '')} | "
                   f"{((t or {}).get('displayName') or {}).get('text', '')} | {g.get('bezug', 'kein')} | {g.get('rating') or ''} | "
                   f"{g.get('anzahl') or ''} | {art} |")
    BERICHT.write_text("\n".join(aus) + "\n", encoding="utf-8")


def fotos_laden(dry_run: bool) -> None:
    from config import GOOGLE_PLACES_API_KEY

    kandidaten = json.loads(KANDIDATEN.read_text(encoding="utf-8"))
    offen = [(s, i, f) for s, liste in kandidaten.items() for i, f in enumerate(liste) if not (FOTOS / s / f"{i}.jpg").exists()]
    logger.info("%d Fotos zu laden → Kosten ca. %.2f $%s", len(offen), len(offen) * PREIS_FOTO, " [Dry-Run]" if dry_run else "")
    if dry_run:
        return
    fehler = 0
    for s, i, f in offen:
        try:
            time.sleep(0.2)
            r = httpx.get(f"{API_BASE}/{f['name']}/media", params={"maxWidthPx": VORSCHAU_BREITE},
                          headers={"X-Goog-Api-Key": GOOGLE_PLACES_API_KEY or ""}, timeout=30, follow_redirects=True)
            r.raise_for_status()
            (FOTOS / s).mkdir(parents=True, exist_ok=True)
            (FOTOS / s / f"{i}.jpg").write_bytes(r.content)
        except Exception as e:  # noqa: BLE001
            fehler += 1
            logger.error("Foto %s/%d fehlgeschlagen: %s", s, i, e)
    logger.info("Fotos fertig: %d geladen, %d Fehler", len(offen) - fehler, fehler)


def sql_schreiben(sichtung_datei: Path) -> None:
    sichtung = json.loads(sichtung_datei.read_text(encoding="utf-8"))
    kandidaten = json.loads(KANDIDATEN.read_text(encoding="utf-8"))
    heute = date.today().isoformat()
    ziel = _WURZEL / "database" / f"weihnachtsmarkt_fotos_{heute}.sql"
    ziel.write_text(sql_aus_sichtung(sichtung, kandidaten, heute), encoding="utf-8")
    logger.info("Foto-SQL: %s (%d mit Foto)", ziel, sum(1 for v in sichtung.values() if v.get("foto") is not None))


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    p = argparse.ArgumentParser(description="Weihnachtsmärkte: Google-Lauf (place_id, Score intern, Foto-Kandidaten)")
    p.add_argument("befehl", choices=["suchen", "fotos", "sql"])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--sichtung", type=Path)
    a = p.parse_args()
    if a.befehl == "suchen":
        suchen(a.dry_run)
    elif a.befehl == "fotos":
        fotos_laden(a.dry_run)
    else:
        if not a.sichtung:
            p.error("--sichtung DATEI fehlt")
        sql_schreiben(a.sichtung)


if __name__ == "__main__":
    main()
