"""
stadt_import.py – DiesDasDüsseldorf
Stadt-Import für den Guide „Spielplätze“ (Plan: docs/plan-spielplaetze-2026-11-12.md, Abschnitte 3, 3.1, 4.1, 4.7).

Quelle: Open Data Düsseldorf, „Notfallnummern auf städtischen Spielplätzen“ (dl-de/zero-2.0), nur die WGS84-Datei.
Stadtteil per Punkt-in-Polygon gegen „Stadtteilgrenzen Düsseldorf 2025“ (WGS84).

Der Import legt neue Plätze inaktiv an und ändert bei bestehenden nur Stadtfelder. Er setzt `aktiv` und
`freigeschaltet_am` nie – freigeschaltet und abgeschaltet wird nur per SQL durch den Auftraggeber (Schritt 6).
Entscheidungen kommen nur über data/spielplaetze/korrekturen.csv zurück; data/spielplaetze/pruefung.csv ist eine Ausgabe.

Nutzung:
  python -m scraper.spielplaetze.stadt_import --dry-run      # rechnet alles, schreibt nur die Prüf-CSV
  python -m scraper.spielplaetze.stadt_import                # schreibt in die Datenbank
  python -m scraper.spielplaetze.stadt_import --neu-laden    # Stadtdateien neu herunterladen (Crawl-delay 10 s)
"""
import argparse
import csv
import json
import logging
import math
import re
import sys
import time
from collections import defaultdict
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.slug_generator import slug_mit_suffix  # noqa: E402
from scraper.orte.google_places import _slug_erzeugen  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

_DATEN = Path(__file__).resolve().parents[2] / "data" / "spielplaetze"
QUELL_ORDNER = _DATEN / "quelle"
SPIELPLATZ_DATEI = QUELL_ORDNER / "spielplaetze_wgs84.geojson"
STADTTEIL_DATEI = QUELL_ORDNER / "stadtteile_2025_wgs84.geojson"
META_DATEI = QUELL_ORDNER / "meta.json"
KORREKTUREN = _DATEN / "korrekturen.csv"
PRUEF_CSV = _DATEN / "pruefung.csv"

DOWNLOADS = {
    SPIELPLATZ_DATEI.name: "https://opendata.duesseldorf.de/sites/default/files/"
                           "Spielpl%C3%A4tze%20mit%20Notfallnummern%20WGS84.geojson",
    STADTTEIL_DATEI.name: "https://opendata.duesseldorf.de/sites/default/files/Stadtteile_2025_WGS84_EPSG4326_1.geojson",
}
QUELL_URL = "https://opendata.duesseldorf.de/dataset/notfallnummern-auf-st%C3%A4dtischen-spielpl%C3%A4tzen"
LIZENZ = "dl-de/zero-2.0"
QUELLE = "stadt-duesseldorf"
USER_AGENT = "Mozilla/5.0 (compatible; Datenabruf)"
CRAWL_DELAY = 10  # Sekunden, laut robots.txt von opendata.duesseldorf.de

# Objektart-Text → Typ (E1). Filter immer über den Text, nie über die Zahl.
HUB_OBJEKTARTEN = {"Kinderspielplatz": "kinder", "Waldkinderspielplatz": "wald", "Wasserspielplatz": "wasser"}
TYP_WORT = {"kinder": "Spielplatz", "wald": "Waldspielplatz", "wasser": "Wasserspielplatz"}
TYP_RANG = {"wasser": 0, "wald": 1, "kinder": 2}  # Wasser vor Wald vor Kinder

LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = 6.6, 7.0, 51.1, 51.4
ZUSAMMEN_M = 30.0
NUMMER_MAX_M = 150.0

STADT_CODES = ("name_unklar", "kein_stadtteil", "bezirk_abweichend", "gruppe_gemischt")
OSM_CODES = ("access_private", "zuordnung_mehrdeutig")
BESTAETIGBAR = ("access_private", "gruppe_gemischt")

# Stadtteil-Katalog – muss mit web/lib/stadtteile.ts (BEZIRKE) übereinstimmen (Test prüft das).
KATALOG = frozenset({
    "Altstadt", "Carlstadt", "Stadtmitte", "Pempelfort", "Derendorf", "Golzheim",
    "Flingern", "Flingern-Nord", "Flingern-Süd", "Düsseltal",
    "Bilk", "Unterbilk", "Hafen", "Friedrichstadt", "Oberbilk", "Hamm", "Flehe", "Volmerswerth",
    "Oberkassel", "Niederkassel", "Heerdt", "Lörick",
    "Stockum", "Lohausen", "Kaiserswerth", "Kalkum", "Angermund", "Wittlaer",
    "Rath", "Unterrath", "Mörsenbroich", "Lichtenbroich",
    "Gerresheim", "Grafenberg", "Ludenberg", "Hubbelrath", "Knittkuhl",
    "Eller", "Lierenfeld", "Vennhausen", "Unterbach",
    "Benrath", "Wersten", "Holthausen", "Hassels", "Reisholz", "Himmelgeist", "Itter", "Urdenbach",
    "Garath", "Hellerhof",
})
POLYGON_ZU_KATALOG = {"Flingern Nord": "Flingern-Nord", "Flingern Süd": "Flingern-Süd"}

# Namensbildung (4.1 Schritt 4)
_TYP_TOKEN = r"(?:waldksp|ksp|wsp)"
AKRONYME = {"NW", "NO", "SW", "SO", "WGZ", "MUFU", "DA"}
UNKLARE_TOKEN = {"MUFU", "DA"}  # Abkürzungen ohne Punkt, die wir nicht auflösen
NAMENSPARTIKEL = {"von", "vom", "van", "der", "de"}
FUNKTIONSWOERTER = {"am", "an", "auf", "bei", "dem", "den", "der", "des", "die", "das", "im", "in",
                    "vom", "von", "vor", "zum", "zur", "und"}
# Geschlossene Liste der Wörter, in denen ae/oe/ue für ä/ö/ü steht (kein allgemeines Ersetzen: Michaelplatz, Quellenbusch)
UMLAUT_WOERTER = {
    "Staendehaus": "Ständehaus", "Kuehlwetter": "Kühlwetter", "Huegel": "Hügel", "Muehlenbroich": "Mühlenbroich",
    "Roentgen": "Röntgen", "Puettkamp": "Püttkamp", "Huelsfeld": "Hülsfeld", "Buerger": "Bürger",
    "Raeuscher": "Räuscher", "Kyffhaeuser": "Kyffhäuser", "Gaerten": "Gärten", "Kaempen": "Kämpen",
    "Peenemuender": "Peenemünder", "Doeblin": "Döblin", "Saeckinger": "Säckinger",
    "Rossstr": "Roßstr",  # Roßstraße (Derendorf) – kein allgemeines ss → ß (Strassmann)
}
_BUCHSTABE = "A-Za-zÄÖÜäöüß"


# ---------------------------------------------------------------------------
# Hilfsfunktionen: Schlüssel, Abstand, Größe
# ---------------------------------------------------------------------------

def schluessel_sortierung(schluessel: str) -> tuple:
    """Objektschlüssel „01001/12“ numerisch sortieren (01001/9 vor 01001/12)."""
    teile = re.split(r"[/]", schluessel)
    return tuple((0, int(t), "") if t.isdigit() else (1, 0, t) for t in teile)


def abstand_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Haversine-Abstand in Metern zwischen (lat, lon)-Paaren."""
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371000.0 * math.asin(math.sqrt(h))


def groesse_lesen(wert) -> float | None:
    """„664,1“ → 664.1; „11.472,3“ → 11472.3; leer → None."""
    if wert is None or str(wert).strip() == "":
        return None
    text = str(wert).strip()
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return round(float(text), 1)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# 4.1 Schritt 1–2: Datei lesen
# ---------------------------------------------------------------------------

def teile_lesen(geojson: dict) -> list[dict]:
    """
    Hub-Teilflächen aus der WGS84-Datei. Features ohne Geometrie werden verworfen.
    Jeder Punkt der Datei muss im Rechteck liegen, sonst Abbruch (falsche Datei oder Projektion).
    """
    teile = []
    for f in geojson.get("features") or []:
        geo, p = f.get("geometry"), f.get("properties") or {}
        if not geo or not p or geo.get("type") != "Point":
            continue
        lon, lat = geo["coordinates"][:2]
        if not (LON_MIN <= lon <= LON_MAX and LAT_MIN <= lat <= LAT_MAX):
            raise ValueError(f"Koordinate außerhalb von Düsseldorf ({lat}, {lon}) – falsche Datei oder Projektion?")
        art_text = str(p.get("objektart") or "").strip().split(" ", 1)[-1].strip()
        typ = HUB_OBJEKTARTEN.get(art_text)
        if not typ:
            continue
        nummer = p.get("4stellige_nr")
        bezirk = p.get("stadtbezirk")
        teile.append({
            "objektschluessel": str(p.get("objektschluessel") or "").strip(),
            "stadt_name": re.sub(r"\s+", " ", str(p.get("objektbezeichnung") or "")).strip(),
            "objektart": str(p.get("objektart") or "").strip(),
            "typ": typ,
            "groesse_m2": groesse_lesen(p.get("groesse")),
            "latitude": round(float(lat), 7),
            "longitude": round(float(lon), 7),
            "nummer": str(nummer).strip() if nummer not in (None, "") else None,
            "stadtbezirk": int(bezirk) if str(bezirk or "").strip().isdigit() else None,
            "strasse_hausnr": re.sub(r"\s+", " ", str(p.get("strasse_hausnr") or "")).strip(),
        })
    return teile


# ---------------------------------------------------------------------------
# 4.1 Schritt 3: Zusammenführung
# ---------------------------------------------------------------------------

def _komponenten(teile: list[dict]) -> list[list[dict]]:
    """Teile, die über Abstände ≤ 30 m verbunden sind, bilden je eine Teilgruppe."""
    eltern = list(range(len(teile)))

    def wurzel(i):
        while eltern[i] != i:
            eltern[i] = eltern[eltern[i]]
            i = eltern[i]
        return i

    for i in range(len(teile)):
        for j in range(i + 1, len(teile)):
            if abstand_m(_punkt(teile[i]), _punkt(teile[j])) <= ZUSAMMEN_M:
                eltern[wurzel(i)] = wurzel(j)
    gruppen = defaultdict(list)
    for i, t in enumerate(teile):
        gruppen[wurzel(i)].append(t)
    return sorted(gruppen.values(), key=lambda g: min(schluessel_sortierung(t["objektschluessel"]) for t in g))


def _punkt(t: dict) -> tuple[float, float]:
    return (t["latitude"], t["longitude"])


def plaetze_bilden(teile: list[dict]) -> list[dict]:
    """
    Teile derselben Notfallnummer ≤ 30 m → ein Platz. Über 30 m bis 150 m: getrennt, Nummer bleibt.
    Irgendein Paar > 150 m: getrennt, Nummer bei allen unterdrückt. Gemischte Gruppe → Code gruppe_gemischt.
    """
    nach_nummer, ohne_nummer = defaultdict(list), []
    for t in teile:
        (nach_nummer[t["nummer"]] if t["nummer"] else ohne_nummer).append(t)
    plaetze = []
    for nummer, gruppe in nach_nummer.items():
        if len(gruppe) == 1:
            plaetze.append(_platz(gruppe, nummer, set(), []))
            continue
        komponenten = _komponenten(gruppe)
        groesster = max(abstand_m(_punkt(a), _punkt(b)) for i, a in enumerate(gruppe) for b in gruppe[i + 1:])
        behalten = groesster <= NUMMER_MAX_M
        hinweise = [] if behalten else [f"Nummer {nummer} unterdrückt (Teile bis {groesster:.0f} m auseinander)"]
        gemischt = len(komponenten) > 1 and any(len(k) > 1 for k in komponenten)
        for k in komponenten:
            plaetze.append(_platz(k, nummer if behalten else None, {"gruppe_gemischt"} if gemischt else set(), hinweise))
    for t in ohne_nummer:
        plaetze.append(_platz([t], None, set(), []))
    return sorted(plaetze, key=lambda p: schluessel_sortierung(p["schluessel"][0]))


def _platz(teile: list[dict], nummer: str | None, codes: set, hinweise: list[str]) -> dict:
    teile = sorted(teile, key=lambda t: schluessel_sortierung(t["objektschluessel"]))
    groesster = sorted(teile, key=lambda t: (-(t["groesse_m2"] or 0), schluessel_sortierung(t["objektschluessel"])))[0]
    groessen = [t["groesse_m2"] for t in teile if t["groesse_m2"] is not None]
    bezirke = [t["stadtbezirk"] for t in [groesster] + teile if t["stadtbezirk"]]
    adressen = [t["strasse_hausnr"] for t in sorted(teile, key=lambda t: -(t["groesse_m2"] or 0)) if t["strasse_hausnr"]]
    return {
        "schluessel": [t["objektschluessel"] for t in teile],
        "teile": teile,
        "typ": min((t["typ"] for t in teile), key=lambda x: TYP_RANG[x]),
        "latitude": groesster["latitude"],
        "longitude": groesster["longitude"],
        "groesse_m2": round(sum(groessen), 1) if groessen else None,
        "notfallnummer": nummer,
        "stadtbezirk_stadt": bezirke[0] if bezirke else None,
        "strasse_hausnr": adressen[0] if adressen else "",
        "codes": set(codes),
        "hinweise": list(hinweise),
    }


# ---------------------------------------------------------------------------
# 4.1 Schritt 4: Name
# ---------------------------------------------------------------------------

def _gross(teil: str) -> str:
    """Erstes Zeichen hinter Satzzeichen groß, Rest klein („KAPPESKIDS“ → „Kappeskids“)."""
    klein = teil.lower()
    for i, z in enumerate(klein):
        if z.isalpha():
            return klein[:i] + z.upper() + klein[i + 1:]
    return klein


def _schreibweise(segment: str) -> str:
    """Versalien normalisieren: „AN DER LEIMKUHLE“ → „An der Leimkuhle“, gemischte Wörter bleiben."""
    woerter = segment.split(" ")
    aus = []
    for nr, wort in enumerate(woerter):
        if not wort:
            continue
        teile = re.split(r"([\-/])", wort)
        neu = []
        for ti, t in enumerate(teile):
            buchstaben = [z for z in t if z.isalpha()]
            if t in ("-", "/") or not buchstaben or t != t.upper():
                neu.append(t)
            elif t.strip(".") in AKRONYME:
                neu.append(t)
            elif len(buchstaben) == 1:
                neu.append(t)  # „J.“, „V.“ bleiben (werden als unklar erkannt)
            elif ti > 0 and t.lower() in NAMENSPARTIKEL:
                neu.append(t.lower())  # „GRAF-VON-STAUFFENBERG“ → „Graf-von-Stauffenberg“
            else:
                neu.append(_gross(t))
        w = "".join(neu)
        if nr > 0 and wort == wort.upper() and w.lower() in FUNKTIONSWOERTER:
            w = w.lower()
        aus.append(w)
    text = " ".join(aus)
    for alt, neu_w in UMLAUT_WOERTER.items():
        text = text.replace(alt, neu_w).replace(alt.lower(), neu_w.lower())
    return text


def _strassen_aufloesen(text: str) -> str:
    """Sichere Auflösungen (geschlossen): Str. am Wortende, a.d., ggü. – dazu „strasse“ am Wortende."""
    ende = r"(?=$|[\s\d/,)\-])"
    text = re.sub(rf"(?<![{_BUCHSTABE}])Str\.{ende}", "Straße", text)
    text = re.sub(rf"(?<=[a-zäöüß])str\.{ende}", "straße", text)
    text = re.sub(rf"(?<![{_BUCHSTABE}])Str(?=\s+\d)", "Straße", text)
    text = re.sub(r"(?<=[a-zäöüß])str(?=\s+\d)", "straße", text)
    text = re.sub(r"(?<=[a-zäöüß])strasse\b", "straße", text)
    text = re.sub(r"(?<=[a-zäöüß])(straße)(?=\d)", r"\1 ", text)
    text = re.sub(r"(?<![a-zäöüß])(Straße)(?=\d)", r"\1 ", text)
    text = re.sub(r"(?i)\ba\.\s*d\.\s*", "an der ", text)
    text = re.sub(r"(?i)\bggü\.\s*", "gegenüber ", text)
    return text


def _segmente_teilen(text: str) -> list[str]:
    """An Kommas teilen, aber nicht innerhalb von „…“."""
    segmente, aktuell, in_zitat = [], "", False
    for z in text:
        if z == "„":
            in_zitat = True
        elif z == "“":
            in_zitat = False
        if z == "," and not in_zitat:
            segmente.append(aktuell)
            aktuell = ""
        else:
            aktuell += z
    segmente.append(aktuell)
    return segmente


def name_segmente(roh: str) -> tuple[list[str], list[str]]:
    """
    Stadtname → normalisierte Segmente (erstes = Ort/Park, weitere = Zusatz) und Hinweise.
    Typwörter (Ksp/Wsp/Waldksp) am Segmentanfang/-ende entfallen; der Typ kommt immer aus der Objektart.
    """
    hinweise = []
    text = re.sub(r"\s+", " ", roh).strip()
    if re.match(r"^GW\s+", text):
        text = re.sub(r"^GW\s+", "", text)
        hinweise.append("GW entfernt")
    text = re.sub(r'"([^"]+)"', r"„\1“", text)
    text = re.sub(r"'([^']{3,})'", r"„\1“", text)
    text = re.sub(r"(\w)-\s*,\s*", r"\1- und ", text)  # „LANGER-,BINNENSTR.“
    text = re.sub(r"([A-Za-zÄÖÜäöüß])-\s+(?!und\b)(?=[A-Za-zÄÖÜäöüß])", r"\1- und ", text)  # „VENN- BRINELLSTR.“
    text = re.sub(r"(\w)\s*[`´']\s*(\w)", r"\1’\2", text)
    text = re.sub(r"(\d)\s*-\s*(\d)", r"\1-\2", text)
    text = re.sub(r"\s*/\s*", "/", text)
    segmente = []
    for nr, seg in enumerate(_segmente_teilen(text)):
        seg = seg.strip()
        seg = re.sub(rf"(?i)^{_TYP_TOKEN}\b[\s\-/]*", "", seg)
        if nr == 0:  # nur im Stamm steht das Typwort auch hinten („CHRISTOPHSTRASSE KSP“)
            seg = re.sub(rf"(?i)(?:^|[\s/]+){_TYP_TOKEN}$", "", seg).strip()
        seg = re.sub(r"(?i)(?<=-)ksp\b", "Spielplatz", seg)
        seg = re.sub(r"(?i)(?<=-)wsp\b", "Wasserspielplatz", seg)
        seg = re.sub(r"(?i)\bksp\b", "Spielplatz", seg)
        seg = re.sub(r"(?i)\bwsp\b", "Wasserspielplatz", seg)
        seg = re.sub(r"„([^“]*)“", lambda m: "„" + re.sub(r",\s*", ", ", m.group(1)) + "“", seg)
        if not seg:
            continue
        seg = _strassen_aufloesen(_schreibweise(seg))
        seg = re.sub(r"\s+", " ", seg).strip()
        if seg.startswith("(") and seg.endswith(")"):
            seg = seg[1:-1].strip()
        if seg:
            segmente.append(seg)
    return segmente, hinweise


def ist_unklar(segmente: list[str]) -> bool:
    """Unklar = nach den sicheren Auflösungen bleibt eine Abkürzung mit Punkt oder ein bekanntes unklares Kürzel."""
    for seg in segmente:
        if re.search(rf"[{_BUCHSTABE}]\.(?=$|[\s/,)\-]|[{_BUCHSTABE}])", seg):
            return True
        if any(w.strip("()„“,/") in UNKLARE_TOKEN for w in re.split(r"[\s/\-]", seg)):
            return True
    return False


def name_aus_segmenten(segmente: list[str], typ: str) -> str:
    # Zusatz entfällt, wenn er schon im Stamm steht – ganz oder als Teil nach „/“ („…Straße/Heideweg (Heideweg)“)
    im_stamm = {segmente[0].lower()} | {t.strip().lower() for t in segmente[0].split("/")}
    stamm, zusatz = segmente[0], [s for s in segmente[1:] if s.lower() not in im_stamm]
    name = f"{TYP_WORT[typ]} {stamm}"
    return f"{name} ({', '.join(zusatz)})" if zusatz else name


def platz_name(platz: dict) -> tuple[str, bool, list[str]]:
    """
    Anzeigename eines Platzes aus der Normalisierung: (Name, unklar, Hinweise).
    Zusammengeführt: gemeinsamer Stamm aller Teile; ein unklarer Zusatz einzelner Teile blockiert ihn nicht.
    """
    zerlegt = [name_segmente(t["stadt_name"]) for t in platz["teile"]]
    hinweise = sorted({h for _, hs in zerlegt for h in hs})
    if len(zerlegt) == 1:
        segmente = zerlegt[0][0]
    else:
        listen = [s for s, _ in zerlegt]
        segmente = []
        for stelle in range(min(len(x) for x in listen)):
            werte = {x[stelle].lower() for x in listen}
            if len(werte) != 1:
                break
            segmente.append(listen[0][stelle])
        hinweise.append(f"zusammengeführt ({len(zerlegt)} Teile)")
        if not segmente:
            groesster = max(platz["teile"], key=lambda t: t["groesse_m2"] or 0)
            segmente = name_segmente(groesster["stadt_name"])[0]
            hinweise.append("kein gemeinsamer Namensstamm")
    if not segmente:
        return f"{TYP_WORT[platz['typ']]} ohne Namen", True, hinweise
    return name_aus_segmenten(segmente, platz["typ"]), ist_unklar(segmente), hinweise


# ---------------------------------------------------------------------------
# 4.1 Schritt 5: Stadtteil
# ---------------------------------------------------------------------------

def _im_ring(lon: float, lat: float, ring: list) -> bool:
    """Ray-Casting gegen einen Ring aus [lon, lat]-Paaren."""
    drin = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat):
            x = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < x:
                drin = not drin
        j = i
    return drin


def im_polygon(lon: float, lat: float, geometrie: dict) -> bool:
    """Punkt in (Multi-)Polygon: im Außenring eines Teilpolygons und in keinem seiner Löcher."""
    polygone = geometrie["coordinates"] if geometrie["type"] == "MultiPolygon" else [geometrie["coordinates"]]
    for poly in polygone:
        if poly and _im_ring(lon, lat, poly[0]) and not any(_im_ring(lon, lat, loch) for loch in poly[1:]):
            return True
    return False


def stadtteile_lesen(geojson: dict) -> list[dict]:
    aus = []
    for f in geojson.get("features") or []:
        p = f.get("properties") or {}
        name = str(p.get("Name") or "").strip()
        aus.append({"name": POLYGON_ZU_KATALOG.get(name, name), "nummer": str(p.get("Nummer") or ""),
                    "geometrie": f["geometry"]})
    unbekannt = [s["name"] for s in aus if s["name"] not in KATALOG]
    if unbekannt:
        raise ValueError(f"Stadtteile ohne Katalogwert: {unbekannt}")
    return aus


def polygon_treffer(lat: float, lon: float, stadtteile: list[dict]) -> dict | None:
    for s in stadtteile:
        if im_polygon(lon, lat, s["geometrie"]):
            return s
    return None


def stadtteil_bestimmen(treffer: dict | None, korrektur: str, gespeichert: str | None,
                        freigeschaltet: bool) -> tuple[str | None, set, list[str], list[str]]:
    """
    Reihenfolge: Katalogwert aus korrekturen.csv vor Polygon. Nicht-Katalogwert: Log-Fehler, Spalte bleibt,
    Polygon gilt nicht, Code kein_stadtteil. Ohne beides: freigeschaltet → gespeicherter Wert + Warnung,
    nie freigeschaltet → leer + kein_stadtteil.
    Rückgabe: (Stadtteil, Codes, Hinweise, Fehler)
    """
    korrektur = (korrektur or "").strip()
    if korrektur:
        if korrektur in KATALOG:
            return korrektur, set(), [], []
        return gespeichert, {"kein_stadtteil"}, [], [f"Stadtteil „{korrektur}“ ist kein Katalogwert"]
    if treffer:
        hinweise = []
        if freigeschaltet and gespeichert and gespeichert != treffer["name"]:
            hinweise.append(f"Stadtteil geändert: {gespeichert} → {treffer['name']}")
        return treffer["name"], set(), hinweise, []
    return (gespeichert if freigeschaltet else None), {"kein_stadtteil"}, [], []


def bezirk_abweichend(treffer: dict | None, stadtbezirk: int | None) -> bool:
    """Nur ein gesetzter, abweichender Stadtbezirk zählt; Kontrolle nur bei Polygon-Treffer."""
    if not treffer or not stadtbezirk or not treffer["nummer"][:2].isdigit():
        return False
    return int(treffer["nummer"][:2]) != stadtbezirk


# ---------------------------------------------------------------------------
# 3.1: korrekturen.csv
# ---------------------------------------------------------------------------

def korrekturen_lesen(pfad: Path) -> tuple[dict | None, list[str]]:
    """
    Liest korrekturen.csv (Trennzeichen ; oder ,). Fehlt die Datei: (None, []) = keine Korrekturen.
    Rückgabe: {schluessel: {anzeigename, ausschliessen (True/False/None=ungültig), grund, stadtteil, bestaetigt}}, Fehler
    """
    if not pfad.exists():
        return None, []
    text = pfad.read_text(encoding="utf-8-sig")
    erste = text.splitlines()[0] if text.strip() else ""
    trenner = ";" if erste.count(";") >= erste.count(",") else ","
    fehler, daten = [], {}
    for nr, z in enumerate(csv.DictReader(text.splitlines(), delimiter=trenner), start=2):
        z = {(k or "").strip().lower(): (v or "").strip() for k, v in z.items()}
        schluessel = z.get("schluessel", "")
        if not schluessel:
            continue
        if schluessel.startswith("abenteuer:"):
            fehler.append(f"Zeile {nr}: {schluessel} gehört nach abenteuer.csv – ignoriert")
            continue
        aus = z.get("ausschliessen", "").lower()
        ausschliessen = True if aus == "ja" else False if aus == "" else None
        if ausschliessen is None:
            fehler.append(f"Zeile {nr}: ausschliessen „{z.get('ausschliessen')}“ ist weder leer noch ja – Feld bleibt")
        if ausschliessen and not z.get("grund"):
            fehler.append(f"Zeile {nr}: {schluessel} ausschliessen=ja ohne Grund – Feld bleibt")
        bestaetigt = []
        for code in [c.strip() for c in z.get("bestaetigt", "").split(",") if c.strip()]:
            if code in BESTAETIGBAR:
                bestaetigt.append(code)
            elif code in ("name_unklar", "kein_stadtteil"):
                fehler.append(f"Zeile {nr}: {code} lässt sich nicht bestätigen (nur über anzeigename bzw. stadtteil) – ignoriert")
            else:
                fehler.append(f"Zeile {nr}: unbekannter Code „{code}“ in bestaetigt – ignoriert")
        if schluessel in daten:
            fehler.append(f"Zeile {nr}: {schluessel} doppelt – die erste Zeile gilt")
            continue
        daten[schluessel] = {
            "anzeigename": z.get("anzeigename", ""),
            "ausschliessen": ausschliessen,
            "grund": z.get("grund", ""),
            "stadtteil": z.get("stadtteil", ""),
            "bestaetigt": sorted(set(bestaetigt)),
        }
    return daten, fehler


def ausgeschlossen_neu(korrekturen: dict | None, eintrag: dict | None, gespeichert):
    """3.1: Datei fehlt → unverändert; ja + Grund → Grund; ja ohne Grund / ungültig → unverändert; sonst null."""
    if korrekturen is None:
        return gespeichert
    if not eintrag or eintrag["ausschliessen"] is False:
        return None
    if eintrag["ausschliessen"] is None or not eintrag["grund"]:
        return gespeichert
    return eintrag["grund"]


# ---------------------------------------------------------------------------
# Planung (rein): was der Import schreiben würde
# ---------------------------------------------------------------------------

def _gespeicherte_namen(sp: dict) -> list[str]:
    return sorted(t.get("stadt_name", "") for t in sp.get("teile") or [])


def planen(plaetze: list[dict], stadtteile: list[dict], korrekturen: dict | None, bestehend: list[dict],
           andere_slugs: set[str], heute: str, datenstand: str) -> dict:
    """
    Ordnet die Plätze den bestehenden Zeilen zu (4.7) und berechnet alle Felder nach 3.1/4.1.
    bestehend: Zeilen typ='spielplatz' mit extras.spielplatz.quelle='stadt-duesseldorf' (id, name, slug, stadtteil, extras).
    andere_slugs: Slugs aller übrigen Zeilen der Tabelle orte (auch Abenteuer).
    Rückgabe: {neu: [...], aenderungen: [...], pruefung: [...], fehler: [...], log: [...]}
    """
    fehler, log = [], []
    # Korrekturen gehören an den kleinsten Schlüssel einer Gruppe
    gruppe_von = {s: p for p in plaetze for s in p["schluessel"]}
    if korrekturen:
        for schluessel in korrekturen:
            p = gruppe_von.get(schluessel)
            if not p:
                fehler.append(f"korrekturen.csv: Schlüssel {schluessel} steht nicht in der Stadtdatei")
            elif p["schluessel"][0] != schluessel:
                fehler.append(f"korrekturen.csv: {schluessel} ist nicht der kleinste Schlüssel seiner Gruppe "
                              f"({p['schluessel'][0]}) – nicht angewendet")

    # 4.7: Zuordnung über die Schnittmenge der Objektschlüssel
    zeile_von = {}
    for z in bestehend:
        for t in (z.get("extras") or {}).get("spielplatz", {}).get("teile") or []:
            zeile_von[t["objektschluessel"]] = z["id"]
    treffer_platz = {}
    plaetze_je_zeile = defaultdict(set)
    for i, p in enumerate(plaetze):
        ids = {zeile_von[s] for s in p["schluessel"] if s in zeile_von}
        treffer_platz[i] = ids
        for zid in ids:
            plaetze_je_zeile[zid].add(i)
    nach_id = {z["id"]: z for z in bestehend}

    eintraege = []  # (index, platz, zeile|None, art)
    for i, p in enumerate(plaetze):
        ids = treffer_platz[i]
        if not ids:
            eintraege.append((i, p, None, "neu"))
        elif len(ids) == 1 and len(plaetze_je_zeile[next(iter(ids))]) == 1:
            eintraege.append((i, p, nach_id[next(iter(ids))], "aktualisiert"))
        else:
            eintraege.append((i, p, None, "konflikt"))
    getroffen = {zid for ids in treffer_platz.values() for zid in ids}

    neu, aenderungen, pruefung = [], [], []
    feste_slugs = set(andere_slugs)
    neu_zu_benennen = []  # (sortierschlüssel, datensatz)

    for i, p, zeile, art in eintraege:
        k = (korrekturen or {}).get(p["schluessel"][0])
        sp_alt = ((zeile or {}).get("extras") or {}).get("spielplatz", {})
        freigeschaltet = bool(sp_alt.get("freigeschaltet_am"))
        hinweise = list(p["hinweise"])
        if art == "konflikt":
            zeilen = sorted({nach_id[z]["slug"] for z in treffer_platz[i]})
            hinweise.append("Schlüssel treffen mehrere Zeilen bzw. eine Zeile mehrere Gruppen – nichts geändert: "
                            + ", ".join(zeilen))
            pruefung.append(_pruef_zeile(p, None, None, None, None, set(), hinweise, "konflikt", None))
            continue

        codes = set(p["codes"])
        # Name
        name_norm, unklar, name_hinweise = platz_name(p)
        hinweise += name_hinweise
        if k and k["anzeigename"]:
            name, name_quelle = k["anzeigename"], "korrektur"
        elif not freigeschaltet:
            name, name_quelle = name_norm, "stadt"
            if unklar:
                codes.add("name_unklar")
        else:
            name, name_quelle = zeile["name"], sp_alt.get("name_quelle", "stadt")
            if _gespeicherte_namen(sp_alt) != sorted(t["stadt_name"] for t in p["teile"]):
                hinweise.append("Stadtname neu")
        # Stadtteil
        treffer = polygon_treffer(p["latitude"], p["longitude"], stadtteile)
        stadtteil, st_codes, st_hinweise, st_fehler = stadtteil_bestimmen(
            treffer, (k or {}).get("stadtteil", ""), (zeile or {}).get("stadtteil"), freigeschaltet)
        codes |= st_codes
        hinweise += st_hinweise
        fehler += [f"{p['schluessel'][0]}: {f}" for f in st_fehler]
        if not (k or {}).get("stadtteil") and bezirk_abweichend(treffer, p["stadtbezirk_stadt"]):
            codes.add("bezirk_abweichend")
        if not p["strasse_hausnr"]:
            hinweise.append("keine Adresse")
        # Prüf-Codes: Stadt-Codes neu, OSM-Codes bleiben
        pruef = sorted(codes | {c for c in sp_alt.get("pruefung") or [] if c in OSM_CODES})
        if korrekturen is None:
            bestaetigt = list(sp_alt.get("bestaetigt") or [])
        else:
            bestaetigt = list((k or {}).get("bestaetigt") or [])
        ausgeschlossen = ausgeschlossen_neu(korrekturen, k, sp_alt.get("ausgeschlossen"))

        teile = [{"objektschluessel": t["objektschluessel"], "stadt_name": t["stadt_name"], "objektart": t["objektart"],
                  "groesse_m2": t["groesse_m2"], "latitude": t["latitude"], "longitude": t["longitude"]} for t in p["teile"]]
        stadtfelder = {
            "quelle": QUELLE, "lizenz": LIZENZ, "quelle_url": QUELL_URL, "datenstand": datenstand,
            "teile": teile, "typ": p["typ"], "name_quelle": name_quelle, "pruefung": pruef, "bestaetigt": bestaetigt,
            "ausgeschlossen": ausgeschlossen, "notfallnummer": p["notfallnummer"], "groesse_m2": p["groesse_m2"],
            "stadtbezirk_stadt": p["stadtbezirk_stadt"],
        }
        spalten = {
            "name": name, "stadtteil": stadtteil,
            "adresse": f"{p['strasse_hausnr']}, Düsseldorf" if p["strasse_hausnr"] else None,
            "latitude": p["latitude"], "longitude": p["longitude"],
        }
        datensatz = {"platz": p, "zeile": zeile, "art": art, "spalten": spalten, "stadtfelder": stadtfelder,
                     "hinweise": hinweise, "freigeschaltet": freigeschaltet}
        if art == "aktualisiert":
            alt_keys = {t["objektschluessel"] for t in sp_alt.get("teile") or []}
            fehlend = [f for f in sp_alt.get("fehlende_teile") or [] if f["objektschluessel"] not in p["schluessel"]]
            bekannt = {f["objektschluessel"] for f in fehlend}
            for s in sorted(alt_keys - set(p["schluessel"]), key=schluessel_sortierung):
                if s not in bekannt:
                    fehlend.append({"objektschluessel": s, "seit": heute})
            stadtfelder["fehlende_teile"] = fehlend
            datensatz["entfernen"] = ("stadt_fehlt_seit",)
        else:
            stadtfelder["fehlende_teile"] = []
        if freigeschaltet:
            spalten["slug"] = zeile["slug"]
            feste_slugs.add(zeile["slug"])
        else:
            neu_zu_benennen.append(datensatz)
        (neu if art == "neu" else aenderungen).append(datensatz)

    # Zeilen ohne Treffer: stadt_fehlt_seit setzen, sonst nichts ändern; ihr Slug bleibt reserviert
    for z in bestehend:
        if z["id"] in getroffen:
            if z["id"] not in {d["zeile"]["id"] for d in aenderungen}:
                feste_slugs.add(z["slug"])  # Konflikt-Zeilen behalten ihren Slug
            continue
        feste_slugs.add(z["slug"])
        sp = (z.get("extras") or {}).get("spielplatz", {})
        alte_teile = sp.get("teile") or []
        pruefung.append({
            "schluessel": alte_teile[0]["objektschluessel"] if alte_teile else "",
            "alle_schluessel": ", ".join(t["objektschluessel"] for t in alte_teile),
            "stadtname": " | ".join(t.get("stadt_name", "") for t in alte_teile),
            "name_alt": z["name"], "name_neu": "", "slug": z["slug"], "stadtteil": z.get("stadtteil") or "",
            "typ": sp.get("typ", ""), "notfallnummer": sp.get("notfallnummer") or "",
            "pruef_codes": ", ".join(sp.get("pruefung") or []),
            "hinweise": "kein Schlüssel mehr in der Stadtdatei – Abbau prüfen, ggf. ausschliessen=ja (Grund „abgebaut“)",
            "ausgeschlossen": sp.get("ausgeschlossen") or "", "status": "fehlt in Stadtdatei",
        })
        if not sp.get("stadt_fehlt_seit"):
            aenderungen.append({"art": "fehlt", "zeile": z, "stadtfelder": {"stadt_fehlt_seit": heute},
                                "spalten": {}, "hinweise": ["kein Schlüssel mehr in der Stadtdatei"]})
        log.append(f"Zeile {z['slug']} hat keinen Schlüssel mehr in der Stadtdatei (stadt_fehlt_seit)")

    # Slugs: feste zuerst reserviert, dann nie freigeschaltete nach kleinstem Schlüssel (4.1 Schritt 7)
    vergeben = set(feste_slugs)
    for d in sorted(neu_zu_benennen, key=lambda d: schluessel_sortierung(d["platz"]["schluessel"][0])):
        d["spalten"]["slug"] = slug_mit_suffix(_slug_erzeugen(d["spalten"]["name"], d["spalten"]["stadtteil"]), vergeben)
        vergeben.add(d["spalten"]["slug"])

    for d in neu + [a for a in aenderungen if a["art"] == "aktualisiert"]:
        sp = d["stadtfelder"]
        pruefung.append(_pruef_zeile(d["platz"], (d["zeile"] or {}).get("name"), d["spalten"]["name"],
                                     d["spalten"]["slug"], d["spalten"]["stadtteil"], set(sp["pruefung"]),
                                     d["hinweise"], d["art"], sp["ausgeschlossen"]))
    pruefung.sort(key=lambda z: schluessel_sortierung(z["schluessel"]))
    return {"neu": neu, "aenderungen": aenderungen, "pruefung": pruefung, "fehler": fehler, "log": log}


def _pruef_zeile(p, name_alt, name_neu, slug, stadtteil, codes, hinweise, status, ausgeschlossen) -> dict:
    return {
        "schluessel": p["schluessel"][0],
        "alle_schluessel": ", ".join(p["schluessel"]),
        "stadtname": " | ".join(t["stadt_name"] for t in p["teile"]),
        "name_alt": name_alt or "",
        "name_neu": name_neu or "",
        "slug": slug or "",
        "stadtteil": stadtteil or "",
        "typ": p["typ"],
        "notfallnummer": p["notfallnummer"] or "",
        "pruef_codes": ", ".join(sorted(codes)),
        "hinweise": "; ".join(hinweise),
        "ausgeschlossen": ausgeschlossen or "",
        "status": status,
    }


# ---------------------------------------------------------------------------
# Ein- und Ausgabe
# ---------------------------------------------------------------------------

def dateien_laden(neu: bool) -> None:
    """Stadtdateien herunterladen (nur wenn sie fehlen oder --neu-laden), mit Pause laut robots.txt."""
    QUELL_ORDNER.mkdir(parents=True, exist_ok=True)
    meta = json.loads(META_DATEI.read_text(encoding="utf-8")) if META_DATEI.exists() else {}
    erster = True
    for datei, url in DOWNLOADS.items():
        ziel = QUELL_ORDNER / datei
        if ziel.exists() and not neu and datei in meta:
            continue
        if not erster:
            time.sleep(CRAWL_DELAY)
        erster = False
        try:
            r = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Download fehlgeschlagen: {url}: {e}") from e
        ziel.write_bytes(r.content)
        meta[datei] = {"url": url, "last_modified": r.headers.get("last-modified"), "geladen_am": date.today().isoformat()}
        logger.info("Geladen: %s (%d Bytes, Stand %s)", datei, len(r.content), r.headers.get("last-modified"))
    META_DATEI.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def datenstand_lesen() -> str:
    meta = json.loads(META_DATEI.read_text(encoding="utf-8")) if META_DATEI.exists() else {}
    lm = (meta.get(SPIELPLATZ_DATEI.name) or {}).get("last_modified")
    if not lm:
        raise RuntimeError("Datenstand unbekannt – bitte mit --neu-laden starten")
    return parsedate_to_datetime(lm).date().isoformat()


def pruef_csv_schreiben(zeilen: list[dict], pfad: Path) -> None:
    if not zeilen:
        return
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with pfad.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(zeilen[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(zeilen)


def _extras_schreiben(db, zeile_id: str, stadtfelder: dict, spalten: dict, entfernen: tuple = ()) -> None:
    """Nur die Stadtfelder in extras.spielplatz ändern – extras direkt vorher frisch lesen."""
    aktuell = (db.table("orte").select("extras").eq("id", zeile_id).execute().data or [{}])[0].get("extras") or {}
    sp = {k: v for k, v in {**(aktuell.get("spielplatz") or {}), **stadtfelder}.items() if k not in entfernen}
    db.table("orte").update({"extras": {**aktuell, "spielplatz": sp}, **spalten}).eq("id", zeile_id).execute()


def schreiben(db, plan: dict) -> dict:
    """
    Schreibt den Plan. Neue Zeilen mit aktiv=false; bei bestehenden steht aktiv nicht in der Schreibliste.
    Ändert sich der Slug einer nie freigeschalteten Zeile, erst ein Zwischen-Slug (eindeutiger Index).
    """
    zaehler = {"neu": 0, "aktualisiert": 0, "fehlt": 0, "fehler": 0}
    aktual = [a for a in plan["aenderungen"] if a["art"] == "aktualisiert"]
    wechsel = [a for a in aktual if a["spalten"]["slug"] != a["zeile"]["slug"]]
    for a in wechsel:
        db.table("orte").update({"slug": f"tmp-spielplatz-{a['zeile']['id']}"}).eq("id", a["zeile"]["id"]).execute()
    for a in plan["aenderungen"]:
        try:
            if a["art"] == "aktualisiert":
                _extras_schreiben(db, a["zeile"]["id"], a["stadtfelder"], a["spalten"], a.get("entfernen", ()))
            else:
                _extras_schreiben(db, a["zeile"]["id"], a["stadtfelder"], {})
            zaehler[a["art"]] += 1
        except Exception as e:  # noqa: BLE001 – jede Zeile einzeln, Fehler zählen
            zaehler["fehler"] += 1
            logger.error("Fehler bei %s: %s", a["zeile"]["slug"], e)
    neue_zeilen = []
    for d in plan["neu"]:
        sp = {**d["stadtfelder"], "freigeschaltet_am": None}
        neue_zeilen.append({**d["spalten"], "typ": "spielplatz", "aktiv": False, "qualitaets_score": None,
                            "bild_url": None, "extras": {"spielplatz": sp}})
    for i in range(0, len(neue_zeilen), 50):
        teil = neue_zeilen[i:i + 50]
        try:
            db.table("orte").insert(teil).execute()
            zaehler["neu"] += len(teil)
        except Exception as e:  # noqa: BLE001 – Block fehlgeschlagen: Zeilen einzeln nachholen
            logger.warning("Block ab %d fehlgeschlagen (%s) – lege die Zeilen einzeln an", i, e)
            for z in teil:
                try:
                    db.table("orte").insert(z).execute()
                    zaehler["neu"] += 1
                except Exception as e2:  # noqa: BLE001
                    zaehler["fehler"] += 1
                    logger.error("Fehler beim Anlegen von %s: %s", z["slug"], e2)
    return zaehler


def importieren(dry_run: bool, neu_laden: bool) -> dict:
    dateien_laden(neu_laden)
    datenstand = datenstand_lesen()
    teile = teile_lesen(json.loads(SPIELPLATZ_DATEI.read_text(encoding="utf-8")))
    stadtteile = stadtteile_lesen(json.loads(STADTTEIL_DATEI.read_text(encoding="utf-8")))
    plaetze = plaetze_bilden(teile)
    korrekturen, k_fehler = korrekturen_lesen(KORREKTUREN)
    logger.info("Stadtdatei (Stand %s): %d Hub-Einträge → %d Spielplätze; Korrekturen: %s",
                datenstand, len(teile), len(plaetze),
                "Datei fehlt (keine Korrekturen)" if korrekturen is None else f"{len(korrekturen)} Einträge")

    from database.client import get_supabase_client
    from scraper.orte.google_places import alle_zeilen

    db = get_supabase_client()
    alle = alle_zeilen(db, "orte", "id, name, slug, typ, stadtteil, aktiv, extras")
    ist_stadt = lambda z: z["typ"] == "spielplatz" and ((z.get("extras") or {}).get("spielplatz") or {}).get("quelle") == QUELLE  # noqa: E731
    bestehend = [z for z in alle if ist_stadt(z)]
    andere = {z["slug"] for z in alle if not ist_stadt(z)}
    plan = planen(plaetze, stadtteile, korrekturen, bestehend, andere, date.today().isoformat(), datenstand)

    for f in k_fehler + plan["fehler"]:
        logger.error("%s", f)
    for m in plan["log"]:
        logger.info("%s", m)
    pruef_csv_schreiben(plan["pruefung"], PRUEF_CSV)
    zaehl_codes = defaultdict(int)
    for z in plan["pruefung"]:
        for c in filter(None, z["pruef_codes"].split(", ")):
            zaehl_codes[c] += 1
    logger.info("Plan: %d neu, %d aktualisiert, %d ohne Schlüssel, %d Konflikte; Prüf-Codes: %s; Prüf-CSV: %s%s",
                len(plan["neu"]), sum(a["art"] == "aktualisiert" for a in plan["aenderungen"]),
                sum(a["art"] == "fehlt" for a in plan["aenderungen"]),
                sum(z["status"] == "konflikt" for z in plan["pruefung"]), dict(zaehl_codes) or "keine",
                PRUEF_CSV, " [Dry-Run, nichts geschrieben]" if dry_run else "")
    if dry_run:
        return {"neu": len(plan["neu"]), "aenderungen": len(plan["aenderungen"])}
    ergebnis = schreiben(db, plan)
    logger.info("Import fertig: %s", ergebnis)
    return ergebnis


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Spielplätze: Stadt-Import (inaktiv)")
    parser.add_argument("--dry-run", action="store_true", help="nichts schreiben, nur Prüf-CSV")
    parser.add_argument("--neu-laden", action="store_true", help="Stadtdateien neu herunterladen")
    args = parser.parse_args()
    importieren(args.dry_run, args.neu_laden)


if __name__ == "__main__":
    main()
