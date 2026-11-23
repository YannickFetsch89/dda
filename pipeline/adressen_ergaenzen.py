"""
adressen_ergaenzen.py – DiesDasDüsseldorf
Adressen für Rausgegangen-Events aus eigenen Daten.

Rausgegangen-Detailseiten (mit Adresse im JSON-LD) dürfen wir nicht abrufen: Die robots.txt sperrt alle
unbekannten Crawler (Entscheidung C4, docs/plan-clubs-2026-11-11.md). Die Kachel der Startseite nennt meist nur
den Ortsnamen. Die Adresse kommt deshalb aus Daten, die wir schon haben – ohne einen einzigen Abruf:

  0. Zugeordneter Ort (events.ort_id aus Schritt 1d, Ortsseiten-Plan): dessen Adresse aus der Orte-Tabelle.
     Ketten (mehrere Filialen) ausgenommen.
  1. Adressbuch nach Ortsnamen: Orte-Tabelle (Guides) und Events aller Quellen, die für denselben Ort eine
     Adresse liefern. Abgleich über den einheitlichen Ortsnamen (pipeline/ortsnamen.py), nicht unscharf.
     Nennen die Quellen für einen Ort verschiedene Straßen, bleibt die Adresse leer (mehrdeutig).
     Steckt ein Ortsname (ab zwei Wörtern) ganz in einem längeren bekannten Namen, gilt dessen Adresse – nur
     wenn alle solchen Namen dieselbe Adresse haben („Areal Böhler“ → „Weihnachtszauber Areal Böhler“).
  2. Dasselbe Event bei einer anderen Quelle: gleiches Datum, fast gleicher Titel (wie die Dubletten-Erkennung),
     Adresse eindeutig.
  3. OpenStreetMap (Nominatim) für Orte, die in unseren Daten nicht vorkommen – höchstens OSM_JE_LAUF Orte je Lauf,
     nur eindeutige Treffer mit passendem Namen und PLZ im Gebiet (Auftraggeber 20.11.2026, statt Google Places).

Allgemeine Ortsangaben („Düsseldorf“, „Altstadt“, Stadtteilnamen, „Online“) bekommen nie eine Adresse.
Bestehende Adressen werden nie überschrieben.

Im Lauf: adressen_schritt(events) nach der Deduplizierung, vor der Stadtteil-Zuordnung (main.py, Schritt 1e2).

Aufruf:
    python -m pipeline.adressen_ergaenzen                 # Probelauf: künftige Rausgegangen-Events ohne Adresse
    python -m pipeline.adressen_ergaenzen --sql           # UPDATE-Datei für den Bestand (führt der Auftraggeber aus)
    python -m pipeline.adressen_ergaenzen --osm --sql     # dazu OpenStreetMap für die übrigen Orte (2 s je Ort)
"""
import argparse
import logging
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Optional

from pipeline.deduplication import _titel_passt, ist_rausgegangen, titel_kern
from pipeline.ortsnamen import einheitlicher_name, schluessel
from pipeline.stadtteil_mapper import PLZ_STADTTEIL, VENUE_STADTTEIL, stadtteil_ermitteln

logger = logging.getLogger(__name__)

# Wie weit zurück Events als Adressquelle dienen (Orte ändern selten ihre Adresse)
ADRESSBUCH_TAGE_ZURUECK = 365

# Ortsangaben, die keinen bestimmten Ort meinen (Schlüssel wie pipeline/ortsnamen.schluessel)
_ALLGEMEINE_ORTE: set[str] = {
    "", "altstadt", "innenstadt", "stadtmitte", "online", "zoom", "livestream", "tba", "tbd",
    "verschiedene orte", "diverse orte", "verschiedene locations", "treffpunkt", "stadtgebiet",
    "nrw", "rheinufer",
} | {schluessel(s) for s in set(PLZ_STADTTEIL.values()) | set(VENUE_STADTTEIL.values())}

_PLZ = re.compile(r"\b(4[01]\d{3})\b")
_HAUSNUMMER = re.compile(r"[A-Za-zÄÖÜäöüß.]\s?\d{1,4}\s?[a-zA-Z]?\b")
# Anhänge, die manche Quellen an die Adresse hängen: „…, Germany“, „Düsseldorf-Stadtbezirk 1“
_LAND = re.compile(r",?\s*(?:Germany|Deutschland)\b", re.IGNORECASE)
_STADTBEZIRK = re.compile(r"[-\s]+Stadtbezirk\s+\d+", re.IGNORECASE)


def ist_adresse(adresse: Optional[str], ort: Optional[str] = None) -> bool:
    """Brauchbare Adresse: PLZ oder Straße mit Hausnummer – und nicht nur der Ortsname („Savoy Theater, Düsseldorf“)."""
    if not adresse or not adresse.strip():
        return False
    if ort and schluessel(adresse) == schluessel(ort):
        return False
    return bool(_PLZ.search(adresse) or _HAUSNUMMER.search(adresse.split(",")[0]))


def adresse_bereinigen(adresse: str) -> str:
    """Einheitliche Form: ohne Land und „Stadtbezirk“, ohne doppelte PLZ-Angabe, einfache Leerzeichen."""
    a = _STADTBEZIRK.sub("", _LAND.sub("", adresse))
    a = re.sub(r"\s+", " ", a).strip(" ,")
    # „40210 Düsseldorf-KAP1“ → „40210 Düsseldorf“ (Gebäudename gehört nicht in die Stadt)
    a = re.sub(r"(\b\d{5}\s+D(?:ü|ue|u)sseldorf)-[A-Za-z0-9]+$", r"\1", a)
    # „Konrad-Adenauer-Platz 14, 40210 Düsseldorf 40210 Düsseldorf“ → einmal
    a = re.sub(r"(\b\d{5}\s+[A-Za-zÄÖÜäöüß-]+)(?:\s+\1)+$", r"\1", a)
    return a


def _adress_kern(adresse: str) -> str:
    """Vergleichsschlüssel einer Adresse: Straße und Hausnummer (erstes Stück), „Str.“ = „Straße“."""
    erstes = adresse.split(",")[0].lower()
    erstes = re.sub(r"\bstr\.?(?=\s|\d|$)", "straße", erstes)
    erstes = re.sub(r"str\.(?=\s|\d|$)", "straße", erstes)
    erstes = erstes.replace("strasse", "straße")
    # Hinter der Hausnummer abschneiden („Ronsdorfer Str. 134 Düsseldorf“ = „Ronsdorfer Straße 134, 40233 …“);
    # Adressen ohne Straße (nur „40210 Düsseldorf“) bleiben ganz und zählen über die PLZ
    m = re.match(
        r"^(\D*?[a-zäöüß.]\s?\d{1,4}(?:\s?[a-z](?![a-zäöüß]))?(?:\s?[-–/]\s?\d{1,4}(?:[a-z](?![a-zäöüß]))?)?)(?!\d)",
        erstes,
    )
    if m:
        erstes = m.group(1)
    return re.sub(r"[^a-z0-9äöüß]", "", erstes)


def _beste_adresse(kandidaten: Counter) -> Optional[str]:
    """
    Eine Adresse aus mehreren Nennungen: Alle müssen dieselbe Straße + Hausnummer meinen, sonst None.
    Bevorzugt die Schreibweise mit PLZ, dann die häufigste, dann die kürzeste.
    """
    if not kandidaten:
        return None
    gruppen: dict[str, Counter] = defaultdict(Counter)
    for adresse, anzahl in kandidaten.items():
        gruppen[_adress_kern(adresse)][adresse] += anzahl
    # Nur PLZ ohne Straße („40210 Düsseldorf“) widerspricht keiner Straßenadresse mit derselben PLZ
    nur_plz = {k for k in gruppen if re.fullmatch(r"\d{5}[a-zäöüß]*", k)}
    strassen = [k for k in gruppen if k not in nur_plz]
    if len(strassen) > 1:
        return None
    if strassen:
        plz_strasse = {p.group(1) for a in gruppen[strassen[0]] for p in [_PLZ.search(a)] if p}
        plz_nur = {k[:5] for k in nur_plz}
        if plz_nur and plz_strasse and not plz_nur <= plz_strasse:
            return None
        auswahl = gruppen[strassen[0]]
    elif len(nur_plz) == 1:
        auswahl = gruppen[next(iter(nur_plz))]
    else:
        return None
    return min(auswahl, key=lambda a: (not _PLZ.search(a), -auswahl[a], len(a)))


def _ort_schluessel(ort: Optional[str]) -> str:
    return schluessel(einheitlicher_name(ort) or "")


def adressbuch_bauen(orte: list[dict], events: list[dict]) -> dict[str, str]:
    """
    Ortsschlüssel → Adresse aus der Orte-Tabelle (name, adresse) und gespeicherten Events (ort, adresse).
    Nur eindeutige Adressen; allgemeine Ortsangaben fehlen absichtlich.
    """
    nennungen: dict[str, Counter] = defaultdict(Counter)
    for eintrag, feld in [(o, "name") for o in orte] + [(e, "ort") for e in events]:
        name = eintrag.get(feld)
        adresse = eintrag.get("adresse")
        if not ist_adresse(adresse, name):
            continue
        k = _ort_schluessel(name)
        if k in _ALLGEMEINE_ORTE:
            continue
        nennungen[k][adresse_bereinigen(adresse)] += 1
    buch = {}
    for k, kandidaten in nennungen.items():
        beste = _beste_adresse(kandidaten)
        if beste:
            buch[k] = beste
    return buch


def titel_index_bauen(events: list[dict]) -> dict[str, list[dict]]:
    """Datum → Events anderer Quellen mit Adresse (für den Abgleich über Titel + Datum)."""
    index: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        if e.get("datum") and not ist_rausgegangen(e) and ist_adresse(e.get("adresse"), e.get("ort")):
            index[e["datum"]].append(e)
    return index


def ort_adressen_bauen(index) -> dict[str, str]:
    """ort_id → Adresse aus dem Orte-Index der Ortszuordnung (pipeline/ort_zuordnung.OrteIndex); ohne Ketten."""
    if index is None:
        return {}
    adressen = {}
    for zid, z in index.zeilen.items():
        if zid in index.kette or not ist_adresse(z.get("adresse"), z.get("name")):
            continue
        adressen[zid] = adresse_bereinigen(z["adresse"])
    return adressen


def adresse_finden(
    event: dict, adressbuch: dict[str, str], titel_index: dict[str, list[dict]],
    ort_adressen: Optional[dict[str, str]] = None,
) -> tuple[Optional[str], Optional[str]]:
    """(adresse, herkunft) für ein Event ohne Adresse; herkunft ist "ort_id", "ort" oder "titel"."""
    oid = event.get("ort_id")
    if ort_adressen and oid and oid in ort_adressen:
        return ort_adressen[oid], "ort_id"
    k = _ort_schluessel(event.get("ort"))
    if k not in _ALLGEMEINE_ORTE and k in adressbuch:
        return adressbuch[k], "ort"
    # Ortsname steckt ganz in einem längeren bekannten Namen („Areal Böhler“ ⊂ „Weihnachtszauber Areal Böhler“):
    # nur ab zwei Wörtern und nur, wenn alle solchen Namen dieselbe Adresse haben
    if len(k.split()) >= 2 and k not in _ALLGEMEINE_ORTE:
        enthalten = Counter(a for bk, a in adressbuch.items() if bk != k and f" {k} " in f" {bk} ")
        beste = _beste_adresse(enthalten) if len({_adress_kern(a) for a in enthalten}) == 1 else None
        if beste:
            return beste, "ort"
    # Dasselbe Event bei einer anderen Quelle – mindestens zwei unterscheidende Titelwörter
    if len(titel_kern(event.get("titel") or "")) >= 2:
        treffer = Counter(
            adresse_bereinigen(a["adresse"]) for a in titel_index.get(event.get("datum") or "", [])
            if _titel_passt(a, event)
        )
        beste = _beste_adresse(treffer)
        if beste:
            return beste, "titel"
    return None, None


def adressen_ergaenzen(
    events: list[dict], adressbuch: dict[str, str], titel_index: dict[str, list[dict]],
    ort_adressen: Optional[dict[str, str]] = None,
) -> Counter:
    """Setzt event["adresse"] für Rausgegangen-Events ohne Adresse (an Ort und Stelle). Gibt die Herkunft gezählt zurück."""
    zaehler: Counter = Counter()
    for event in events:
        if not ist_rausgegangen(event) or event.get("adresse"):
            continue
        adresse, herkunft = adresse_finden(event, adressbuch, titel_index, ort_adressen)
        if adresse:
            event["adresse"] = adresse
            zaehler[herkunft] += 1
        else:
            zaehler["ohne"] += 1
    return zaehler


# ── OpenStreetMap (Nominatim) für Orte, die in unseren Daten nicht vorkommen ────────────────────────────────────────
# Entscheidung des Auftraggebers 20.11.2026: OpenStreetMap statt Google Places (Google-EEA-Bedingungen verbieten das
# Speichern von Adressen). OSM-Daten dürfen gespeichert werden (ODbL, Quellenangabe „© OpenStreetMap-Mitwirkende“).
# Nominatim-Regeln: erkennbarer User-Agent, höchstens 1 Anfrage/s (wir: 2 s, Projektregel), kein Massenabruf –
# deshalb je Lauf höchstens OSM_JE_LAUF Orte; gefundene Adressen landen in den Events und dienen danach als
# Adressbuch (kein zweiter Abruf für denselben Ort).
NOMINATIM = "https://nominatim.openstreetmap.org/search"
NOMINATIM_UA = "DiesDasDuesseldorf-Adressen/1.0 (+https://diesdas.events)"
OSM_PAUSE_S = 2.0
OSM_JE_LAUF = 60
# Düsseldorf, Neuss, Ratingen (lon_links, lat_oben, lon_rechts, lat_unten)
OSM_VIEWBOX = "6.60,51.37,6.95,51.10"
# Wörter, die allein keinen Ort ausmachen (für den Namensabgleich mit dem OSM-Treffer)
_NAMENS_FUELLWOERTER = {
    "düsseldorf", "duesseldorf", "dusseldorf", "neuss", "ratingen", "the", "und", "and", "der", "die", "das", "im",
    "am", "an", "in", "bei", "zum", "zur", "von", "bar", "cafe", "café", "club", "restaurant", "studio", "haus",
    "halle", "raum", "hof", "platz", "straße", "strasse", "str", "gmbh", "ev", "e.v",
}


def _namens_woerter(text: str) -> set[str]:
    woerter = re.findall(r"[a-zäöüß0-9]+", (text or "").lower())
    return {w for w in woerter if len(w) >= 3 and w not in _NAMENS_FUELLWOERTER}


def _plz_im_gebiet(plz: Optional[str]) -> bool:
    from pipeline.gebiet import PLZ_BEREICHE
    return bool(plz and plz.isdigit() and any(a <= int(plz) <= b for a, b in PLZ_BEREICHE))


def osm_adresse_aus_treffer(ort: str, treffer: list[dict]) -> Optional[str]:
    """
    Adresse aus Nominatim-Treffern (jsonv2, addressdetails=1): nur Treffer, deren Name ein kennzeichnendes Wort des
    Ortsnamens enthält (bei Ein-Wort-Namen: genau gleicher Name), mit Straße und PLZ im Gebiet. Zeigen mehrere
    passende Treffer auf verschiedene Straßen, bleibt es leer (mehrdeutig, z. B. mehrere Kirchen „St. Joseph“).
    """
    kern = _namens_woerter(ort)
    if not kern:
        return None
    kandidaten = []
    for t in treffer or []:
        name = t.get("name") or (t.get("display_name") or "").split(",")[0]
        treffer_woerter = _namens_woerter(name)
        if not kern & treffer_woerter:
            continue
        # Ein-Wort-Namen („Cuvée“, „St. Joseph“) nur bei genau gleichem Namen – sonst zu viele Zufallstreffer
        if len(kern) == 1 and treffer_woerter != kern:
            continue
        a = t.get("address") or {}
        strasse = a.get("road") or a.get("pedestrian") or a.get("square") or a.get("footway")
        plz = a.get("postcode")
        if not strasse or not _plz_im_gebiet(plz):
            continue
        stadt = a.get("city") or a.get("town") or "Düsseldorf"
        nr = a.get("house_number")
        kandidaten.append(f"{strasse}{' ' + nr if nr else ''}, {plz} {stadt}")
    if not kandidaten:
        return None
    return _beste_adresse(Counter(kandidaten))


def osm_suchen(ort: str) -> list[dict]:
    """Nominatim-Suche nach dem Ortsnamen im Gebiet (ein Abruf, Backoff bei 429). Fehler → leere Liste."""
    import time

    import httpx

    warte = OSM_PAUSE_S
    for _ in range(4):
        try:
            antwort = httpx.get(
                NOMINATIM,
                params={"q": ort, "format": "jsonv2", "addressdetails": 1, "limit": 5, "countrycodes": "de",
                        "viewbox": OSM_VIEWBOX, "bounded": 1},
                headers={"User-Agent": NOMINATIM_UA}, timeout=30,
            )
            if antwort.status_code == 429:
                time.sleep(warte)
                warte *= 2
                continue
            antwort.raise_for_status()
            return antwort.json() or []
        except Exception as e:
            logger.error("OpenStreetMap-Suche für „%s“ fehlgeschlagen: %s", ort, e)
            return []
    return []


def osm_ergaenzen(events: list[dict], max_orte: int = OSM_JE_LAUF) -> Counter:
    """
    Rausgegangen-Events ohne Adresse: je Ortsname eine OSM-Suche (höchstens max_orte), Adresse setzen, wenn eindeutig.
    Allgemeine Ortsangaben und Orte, die schon wie eine Adresse aussehen, werden nicht gesucht.
    """
    import time

    offen: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        if not ist_rausgegangen(e) or e.get("adresse"):
            continue
        k = _ort_schluessel(e.get("ort"))
        if k in _ALLGEMEINE_ORTE or ist_adresse(e.get("ort")):
            continue
        offen[k].append(e)
    zaehler: Counter = Counter()
    for i, (k, gruppe) in enumerate(list(offen.items())[:max_orte]):
        if i:
            time.sleep(OSM_PAUSE_S)
        ort = gruppe[0].get("ort") or ""
        adresse = osm_adresse_aus_treffer(ort, osm_suchen(ort))
        zaehler["gesucht"] += 1
        if adresse:
            zaehler["gefunden"] += 1
            for e in gruppe:
                e["adresse"] = adresse
                zaehler["events"] += 1
    zaehler["uebrig"] = max(0, len(offen) - max_orte)
    return zaehler


def _alle(abfrage) -> list[dict]:
    """Seitenweise laden (Supabase liefert höchstens 1.000 Zeilen pro Abfrage)."""
    zeilen: list[dict] = []
    start = 0
    while True:
        teil = abfrage().range(start, start + 999).execute().data or []
        zeilen += teil
        if len(teil) < 1000:
            return zeilen
        start += 1000


def daten_laden(db) -> tuple[list[dict], list[dict]]:
    """Orte mit Adresse und Events (letztes Jahr bis Zukunft) mit Adresse aus der Datenbank."""
    ab = (date.today() - timedelta(days=ADRESSBUCH_TAGE_ZURUECK)).isoformat()
    orte = _alle(lambda: db.table("orte").select("name,adresse").not_.is_("adresse", "null"))
    events = _alle(
        lambda: db.table("events").select("titel,datum,ort,adresse,quelle_name,quelle_url")
        .not_.is_("adresse", "null").gte("datum", ab)
    )
    return orte, events


def adressen_schritt(events: list[dict]) -> list[dict]:
    """Pipeline-Schritt: lädt die eigenen Daten einmal und ergänzt Adressen. Fehler brechen den Lauf nicht ab."""
    try:
        from database.client import get_supabase_client
        orte, bestand = daten_laden(get_supabase_client())
    except Exception as e:
        logger.error("Adressen ergänzen: eigene Daten nicht ladbar – Schritt übersprungen: %s", e)
        return events
    # Events dieses Laufs zählen mit (z. B. Adressen aus Rausgegangen-Kacheln oder Veranstalter-Scrapern)
    adressbuch = adressbuch_bauen(orte, bestand + events)
    from pipeline.ort_zuordnung import aktueller_index
    zaehler = adressen_ergaenzen(events, adressbuch, titel_index_bauen(bestand + events),
                                 ort_adressen_bauen(aktueller_index()))
    osm = osm_ergaenzen(events)
    if osm["gesucht"]:
        logger.info("Adressen aus OpenStreetMap: %d von %d Orten gefunden (%d Events), %d Orte auf den nächsten Lauf "
                    "verschoben", osm["gefunden"], osm["gesucht"], osm["events"], osm["uebrig"])
    logger.info(
        "Adressen ergänzt (Rausgegangen): %d über den zugeordneten Ort, %d über den Ortsnamen, %d über Titel+Datum, "
        "%d weiter ohne Adresse",
        zaehler["ort_id"], zaehler["ort"], zaehler["titel"], max(0, zaehler["ohne"] - osm["events"]),
    )
    return events


def _sql_text(wert: str) -> str:
    return "'" + wert.replace("'", "''") + "'"


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="Adressen für Rausgegangen-Events aus eigenen Daten")
    parser.add_argument("--sql", nargs="?", const=f"database/adressen_rausgegangen_{date.today().isoformat()}.sql",
                        help="UPDATE-Datei für künftige Rausgegangen-Events ohne Adresse schreiben (ändert die DB nicht)")
    parser.add_argument("--osm", action="store_true",
                        help="übrige Orte zusätzlich bei OpenStreetMap suchen (2 s je Ort)")
    args = parser.parse_args()

    from database.client import get_supabase_client
    db = get_supabase_client()
    orte, bestand = daten_laden(db)
    heute = date.today().isoformat()
    offen = [
        e for e in _alle(
            lambda: db.table("events").select("id,titel,datum,ort,ort_id,adresse,stadtteil,quelle_name,quelle_url")
            .gte("datum", heute).is_("adresse", "null")
        )
        if ist_rausgegangen(e)
    ]
    adressbuch = adressbuch_bauen(orte, bestand)
    from pipeline.ort_zuordnung import index_laden
    zaehler = adressen_ergaenzen(offen, adressbuch, titel_index_bauen(bestand), ort_adressen_bauen(index_laden(db)))
    if args.osm:
        osm = osm_ergaenzen(offen, max_orte=500)
        zaehler["osm"] = osm["events"]
        print(f"OpenStreetMap: {osm['gefunden']} von {osm['gesucht']} Orten gefunden ({osm['events']} Events)")
    gefunden = [e for e in offen if e.get("adresse")]
    print(f"Künftige Rausgegangen-Events ohne Adresse: {len(offen)}")
    print(f"  Adresse gefunden: {len(gefunden)} (zugeordneter Ort {zaehler['ort_id']}, Ortsname {zaehler['ort']}, "
          f"Titel+Datum {zaehler['titel']})")
    for e in gefunden[:25]:
        print(f"  {e['datum']} | {e['ort'][:40]:40} | {e['adresse']}")
    ohne = Counter(e["ort"] for e in offen if not e.get("adresse"))
    print("Häufigste Orte weiter ohne Adresse:")
    for ort, n in ohne.most_common(25):
        print(f"  {n:3} {ort}")

    if args.sql:
        zeilen = [
            f"-- Adressen für Rausgegangen-Events aus eigenen Daten – erzeugt am {heute} von pipeline/adressen_ergaenzen.py"
            + (" (mit OpenStreetMap, © OpenStreetMap-Mitwirkende, ODbL)" if args.osm else ""),
            "-- Setzt nur leere Felder (adresse IS NULL, stadtteil IS NULL). Keine Rausgegangen-Abrufe.",
            "BEGIN;",
        ]
        for e in gefunden:
            zeilen.append(f"UPDATE events SET adresse = {_sql_text(e['adresse'])} WHERE id = '{e['id']}' AND adresse IS NULL;")
            stadtteil = None if e.get("stadtteil") else stadtteil_ermitteln(e.get("ort") or "", e["adresse"], e.get("quelle_name"))
            if stadtteil:
                zeilen.append(
                    f"UPDATE events SET stadtteil = {_sql_text(stadtteil)} WHERE id = '{e['id']}' AND stadtteil IS NULL;"
                )
        zeilen.append("COMMIT;")
        with open(args.sql, "w", encoding="utf-8") as f:
            f.write("\n".join(zeilen) + "\n")
        print(f"SQL geschrieben: {args.sql} ({len(gefunden)} Events)")


if __name__ == "__main__":
    main()
