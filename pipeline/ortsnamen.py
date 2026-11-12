"""
ortsnamen.py – DiesDasDüsseldorf
Ein Name pro Spielstätte. Jede Quelle schreibt Orte anders („Mitsubishi Electric HALLE“, „Mitsubishi Electric Halle“,
„Mitsubishi Electric HALLE, Dusseldorf, North Rhine-Westphalia, Germany“). Das stört die Anzeige, den Link
„Weitere Events an diesem Ort“ und Regeln wie die Stadtteil-Zuordnung.

Grundsätze:
- Nur eine GEPFLEGTE Liste, kein unscharfes Zusammenführen. Räume im selben Haus bleiben getrennt
  („Düsseldorfer Schauspielhaus – Großes Haus“ ≠ „– Kleines Haus“, „zakk – Halle“ ≠ „zakk – Studio“,
  „Tonhalle Mendelssohn-Saal“ ≠ „Tonhalle Düsseldorf – Rotunde“), ebenso Treffpunkte und allgemeine Angaben
  („Düsseldorf“, „Altstadt“, „Bunker“).
- Abgleich über einen normalisierten Schlüssel (Groß-/Kleinschreibung, Leerzeichen, Satzzeichen, Umlaute, das Wort
  „Düsseldorf“ und der AllEvents-Anhang „…, North Rhine-Westphalia, Germany“ zählen nicht). Jede Variante steht
  ausdrücklich in der Liste.
- Allgemein für alle Orte: mehrfache Leerzeichen zusammenfassen, AllEvents-Anhang entfernen.

Namen links ohne Trenner („ – “, „ — “, „ - “, „ / “, Klammern) wählen: pipeline/reihen_zuordnen.py ort_basis schneidet
dort, sonst zählt für die Reihen nur das erste Stück. Ausnahme mit Absicht: „zakk – Halle“ (siehe dort).

Neue Variante gefunden? Unten bei der Spielstätte ergänzen und den Bestand per SQL nachziehen
(python -m pipeline.ortsnamen --sql). Den Namen links nie ohne Not ändern – er steht dann in der Datenbank.
"""
import argparse
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Einheitlicher Name → bekannte Schreibweisen (der Name selbst muss nicht noch einmal stehen)
SPIELSTAETTEN: dict[str, list[str]] = {
    # Hallen und Arenen
    "Mitsubishi Electric Halle": ["Mitsubishi Electric HALLE", "Mitsubishi Electric Halle Düsseldorf"],
    "PSD Bank Dome": ["PSD BANK DOME", "PSD BANK DOME Düsseldorf"],
    "Merkur Spiel-Arena": ["Merkur Spiel-Arena Düsseldorf"],
    "Capitol Theater": ["Capitol Theater Düsseldorf", "Capitol-Theater", "Capitol Theater - Düsseldorf"],
    "Stahlwerk": ["Stahlwerk Düsseldorf"],
    "Savoy Theater": ["Savoy Theater Düsseldorf"],
    "UFA-Palast": ["UFA Palast Düsseldorf", "UFA-Palast Düsseldorf"],
    "Metropol Kino": ["Metropol Kino Düsseldorf"],
    # Kultur
    "Tanzhaus NRW": ["Tanzhaus NRW Düsseldorf", "tanzhaus nrw"],
    "NRW-Forum": ["NRW-Forum Düsseldorf"],
    "Goethe-Museum": ["Goethe-Museum Düsseldorf", "Goethe Museum"],
    "Theatermuseum Düsseldorf": ["TMD Theatermuseum Hofgartenhaus Düsseldorf"],
    # Ohne Gedankenstrich: sonst zählte für die Reihen nur „Black Box“ als Ort (ort_basis trennt am Strich)
    "Black Box Kino im Filmmuseum": [
        "Black Box Kino im Filmmuseum Düsseldorf", "Black Box - Kino im Filmmuseum Düsseldorf",
        "Blackbox (Kino im Filmmuseum Düsseldorf)",
    ],
    "Robert-Schumann-Saal": ["Robert Schumann Saal"],
    "Zentralbibliothek KAP1": ["Düsseldorfer Zentralbibliothek im KAP1"],
    "Aquazoo Löbbecke Museum": ["Aquazoo Löbbecke"],
    "Kasematten": ["Kasematten Düsseldorf"],
    "Maxhaus": ["maxhaus"],
    "KaBARett FLiN": ["Kabarett FLiN"],
    "R25 Kulturschlachthof": ["R25-Kulturschlachthof"],
    # Ohne Trenner: „Central – D'haus“ hätte für die Reihen nur „Central“ als Ort gezählt und mit dem Ort „Central“
    # vermischt (ort_basis schneidet am Strich – Cursor-Review 12.11.)
    "D'haus im Central": ["D'haus — Central"],
    "Jazz-Schmiede": ["Jazz-Schmiede Düsseldorf", "Jazz Schmiede", "Jazz-Schmiede Düsseldorf | Jazzclub"],
    # zakk: Räume bleiben getrennt, nur der lange Name des Hauses wird zum Kurznamen. „zakk – Halle“ (mit Strich) ist die
    # bestehende Schreibweise der Reihen (Ort-Basis „zakk“); die eine Zeile „zakk Halle“ folgt ihr bewusst.
    "zakk": ["zakk - Zentrum für Aktion, Kultur und Kommunikation", "Zentrum für Aktion, Kultur und Kommunikation"],
    "zakk – Halle": ["zakk Halle"],
    # Clubs und Bars
    "Pitcher Rock HQ": ["Pitcher", "Pitcher - Rock'n'Roll Headquarter Düsseldorf"],
    "Ratinger Hof": ["Ratinger Hof Düsseldorf"],
    "Nachtresidenz": ["Nachtresidenz Düsseldorf"],
    "Velvet": ["VELVET"],
    "Ampere": ["AMPERE Düsseldorf"],
    "Klub Kulb": ["KLUB KULB"],
    "Rudas Studios": ["Rudas Studios Düsseldorf"],
    "Boston Club": ["Boston Club Düsseldorf e.V."],
    "Holy Craft Beer Bar": ["HOLY CRAFT Beer Bar"],
    "hirschchen": ["*hirschchen"],
    "Fatty's Irish Pub": ["The Irish Pub bei Fatty - Fatty's", "The Irish Pub Bei Fatty - Fatty's"],
    "BrauArt": ["BrauArt Düsseldorf"],
    "Brauerei Kürzer": ["Brauerei Kürzer (Flingern)"],
    # Sport und Freizeit
    "Cosmo Sports": ["COSMO SPORTS"],
    "Superblock Boulderhalle": ["Superblock - Boulderhalle Düsseldorf", "Superblock"],
    # Nur die Stadt (allgemeine Angabe, bleibt allgemein – aber mit Umlaut)
    "Düsseldorf": ["Dusseldorf"],
    # Plätze und Treffpunkte, die eindeutig ein Ort sind
    "Blumengroßmarkt": ["Blumengroßmarkt Düsseldorf"],
    "Rheintreppe": ["Rheintreppe Düsseldorf"],
    "Kay-und-Lore-Lorentz-Platz": ["Kay-und-Lore-Lorentz-Platz Düsseldorf"],
    "Volksgarten": ["Volksgarten Düsseldorf", "Düsseldorf, Volksgarten"],
    "Düsseldorf Hauptbahnhof": ["Düsseldorf, Hauptbahnhof", "Dusseldorf Hauptbahnhof"],
}

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
# AllEvents hängt die Region an: „…, Dusseldorf, North Rhine-Westphalia, Germany“
_ALLEVENTS_ANHANG = re.compile(r"(?:,\s*D(?:ü|ue|u)sseldorf)?,\s*North Rhine-Westphalia,\s*Germany\s*$|,\s*Germany\s*$", re.IGNORECASE)


def schluessel(ort: str) -> str:
    """Vergleichsschlüssel: klein, Umlaute ausgeschrieben, nur Buchstaben/Ziffern, ohne das Wort „Düsseldorf“."""
    t = _ALLEVENTS_ANHANG.sub("", ort or "").lower().translate(_UMLAUTE)
    woerter = [w for w in re.findall(r"[a-z0-9]+", t) if w not in ("duesseldorf", "dusseldorf")]
    return " ".join(woerter)


_NACH_SCHLUESSEL: dict[str, str] = {}
for _name, _varianten in SPIELSTAETTEN.items():
    for _v in [_name, *_varianten]:
        _k = schluessel(_v)
        if _k in _NACH_SCHLUESSEL and _NACH_SCHLUESSEL[_k] != _name:
            raise ValueError(f"Ortsnamen: Schlüssel „{_k}“ doppelt ({_NACH_SCHLUESSEL[_k]} / {_name})")
        _NACH_SCHLUESSEL[_k] = _name


def einheitlicher_name(ort: Optional[str]) -> Optional[str]:
    """Der einheitliche Name für eine Schreibweise; sonst der bereinigte Originalname (Leerzeichen, AllEvents-Anhang)."""
    if not ort:
        return ort
    bereinigt = re.sub(r"\s+", " ", _ALLEVENTS_ANHANG.sub("", ort)).strip() or ort.strip()
    return _NACH_SCHLUESSEL.get(schluessel(bereinigt), bereinigt)


def ortsname_vereinheitlichen(event: dict) -> dict:
    """Setzt event["ort"] auf den einheitlichen Namen (an Ort und Stelle)."""
    alt = event.get("ort")
    neu = einheitlicher_name(alt)
    if neu and neu != alt:
        event["ort"] = neu
        logger.debug("Ortsname vereinheitlicht: „%s“ → „%s“", alt, neu)
    return event


# ---------- SQL für den Bestand ----------

def _sql_text(wert: str) -> str:
    return "'" + wert.replace("'", "''") + "'"


def umbenennungen(events: list[dict]) -> tuple[dict[str, str], list[dict]]:
    """
    Welche Events bekommen welchen neuen Ortsnamen? (rein, testbar)

    Die Tabelle erlaubt (titel, datum, ort, uhrzeit) nur einmal (Constraint events_titel_datum_ort_uhrzeit_key).
    Ein ausgeblendeter Dubletten-Eintrag (abgelehnt, mit 301-Weiterleitung) kann nach dem Umbenennen denselben
    Schlüssel bekommen wie sein Original – dann bleibt er beim alten Namen. Reihenfolge: sichtbare Events zuerst,
    ausgeblendete zuletzt. Ohne Uhrzeit gibt es keine Kollision (NULL ist in Postgres nie gleich).

    Rückgabe: (event_id → neuer Name, ausgelassene Events)
    """
    def schluessel_von(e: dict, ort: str):
        return (e.get("titel"), e.get("datum"), ort, e.get("uhrzeit")) if e.get("uhrzeit") else None

    kandidaten = [e for e in events if e.get("ort") and einheitlicher_name(e["ort"]) != e["ort"]]
    kandidaten_ids = {e["id"] for e in kandidaten}
    # Belegt sind die Schlüssel aller Events, die ihren Namen behalten
    belegt = {k for e in events if e["id"] not in kandidaten_ids and (k := schluessel_von(e, e.get("ort")))}
    zuweisung: dict[str, str] = {}
    ausgelassen: list[dict] = []
    for e in sorted(kandidaten, key=lambda x: (bool(x.get("abgelehnt")), x["id"])):
        neu = einheitlicher_name(e["ort"])
        k = schluessel_von(e, neu)
        if k and k in belegt:
            ausgelassen.append(e)
            # Bleibt beim alten Namen – dessen Schlüssel ist damit belegt
            if (alt := schluessel_von(e, e["ort"])):
                belegt.add(alt)
            continue
        if k:
            belegt.add(k)
        zuweisung[e["id"]] = neu
    return zuweisung, ausgelassen


def sql_erzeugen(pfad: str) -> int:
    """
    Schreibt SQL, das gespeicherte Ortsnamen vereinheitlicht (Events und Reihen). Schreibt selbst nichts in die DB.
    Reihen behalten ihren Slug (URL); nur der interne Schlüssel „titel|ort“ wird nachgezogen, damit die Pipeline
    beim nächsten Lauf keine zweite Reihe anlegt.
    """
    import os
    from collections import Counter, defaultdict
    from datetime import date

    import httpx
    from dotenv import load_dotenv

    from pipeline.reihen_zuordnen import reihen_schluessel

    load_dotenv()
    url = os.environ["SUPABASE_URL"]
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    kopf = {"apikey": key, "Authorization": f"Bearer {key}"}

    def alle(tabelle: str, spalten: str, **filter_) -> list[dict]:
        zeilen, start = [], 0
        while True:
            try:
                r = httpx.get(f"{url}/rest/v1/{tabelle}", headers={**kopf, "Range": f"{start}-{start + 999}"},
                              params={"select": spalten, **filter_}, timeout=60)
                r.raise_for_status()
            except Exception as e:
                logger.error("Ortsnamen: %s nicht ladbar: %s", tabelle, e)
                raise
            seite = r.json()
            zeilen += seite
            start += 1000
            if len(seite) < 1000:
                return zeilen

    events = alle("events", "id,titel,datum,uhrzeit,ort,reihe_id,abgelehnt")
    reihen = alle("reihen", "id,slug,schluessel,ort")

    # Events: je Event-ID, unter Beachtung der Eindeutigkeitsregel (siehe umbenennungen)
    zuweisung, ausgelassen = umbenennungen(events)
    ids_je_name: dict[str, list[str]] = defaultdict(list)
    for eid, neu in zuweisung.items():
        ids_je_name[neu].append(eid)
    # Reihen: Ortsnamen → neuer Name (Reihen haben keine solche Eindeutigkeitsregel auf dem Ort)
    umbenennen: dict[str, list[str]] = defaultdict(list)
    for alt in sorted({e["ort"] for e in events if e["id"] in zuweisung} | {r["ort"] for r in reihen if r.get("ort")}):
        neu = einheitlicher_name(alt)
        if neu and neu != alt:
            umbenennen[neu].append(alt)

    # Reihen, deren Schlüssel sich durch den neuen Ortsnamen ändert
    schluessel_vorhanden = {r["schluessel"] for r in reihen}
    reihen_neu: dict[str, str] = {}
    for e in events:
        if not e.get("reihe_id") or e["id"] not in zuweisung:
            continue
        neu = zuweisung[e["id"]]
        alt_k, neu_k = reihen_schluessel(e["titel"], e["ort"]), reihen_schluessel(e["titel"], neu)
        if neu != e["ort"] and alt_k and neu_k and alt_k != neu_k:
            reihen_neu[e["reihe_id"]] = neu_k
    konflikte = [rid for rid, k in reihen_neu.items() if k in schluessel_vorhanden]
    if konflikte:
        raise RuntimeError(f"Ortsnamen: Reihen-Schlüssel existiert schon für {len(konflikte)} Reihen – erst klären")
    # Zwei Reihen, die in diesem Lauf auf denselben neuen Schlüssel laufen würden, wären ebenfalls ein Zusammenfallen
    doppelt = [k for k, n in Counter(reihen_neu.values()).items() if n > 1]
    if doppelt:
        raise RuntimeError(f"Ortsnamen: {len(doppelt)} neue Reihen-Schlüssel würden mehrfach vergeben – erst klären")

    zeilen = [
        f"-- Ortsnamen vereinheitlichen – DiesDasDüsseldorf, erzeugt am {date.today().isoformat()} von pipeline/ortsnamen.py",
        "-- Eine Schreibweise pro Spielstätte (Liste: SPIELSTAETTEN in pipeline/ortsnamen.py). Räume im selben Haus,",
        "-- Treffpunkte und allgemeine Angaben bleiben, wie sie sind. Event-Slugs (URLs) ändern sich nicht.",
        "-- Reihen behalten ihren Slug; nur ihr interner Schlüssel wird an den neuen Ortsnamen angepasst.",
        "-- Im Supabase-SQL-Editor als Ganzes ausführen.",
        "",
        "BEGIN;",
        "",
    ]
    if ausgelassen:
        zeilen.append(f"-- {len(ausgelassen)} Einträge behalten ihren alten Namen, weil sie sonst mit einem anderen Termin")
        zeilen.append("-- (gleicher Titel, Tag, Ort und Uhrzeit) zusammenfielen – meist ausgeblendete Dubletten mit Weiterleitung:")
        for e in ausgelassen:
            zeilen.append(f"--   {e['datum']} {e.get('uhrzeit') or ''} „{(e.get('titel') or '')[:50]}“ @ {e['ort']}"
                          f"{' (ausgeblendet)' if e.get('abgelehnt') else ''}")
        zeilen.append("")
    for neu, ids in sorted(ids_je_name.items()):
        for i in range(0, len(ids), 200):
            liste = ", ".join(_sql_text(x) for x in sorted(ids[i:i + 200]))
            zeilen.append(f"UPDATE public.events SET ort = {_sql_text(neu)} WHERE id IN ({liste});")
    zeilen.append("")
    for neu, alte in sorted(umbenennen.items()):
        liste = ", ".join(_sql_text(a) for a in alte)
        zeilen.append(f"UPDATE public.reihen SET ort = {_sql_text(neu)} WHERE ort IN ({liste});")
    if reihen_neu:
        zeilen += ["", "-- Reihen-Schlüssel (titel|ort) an die neuen Ortsnamen anpassen – Slugs bleiben"]
        for rid, k in sorted(reihen_neu.items()):
            zeilen.append(f"UPDATE public.reihen SET schluessel = {_sql_text(k)} WHERE id = {_sql_text(rid)};")
    zeilen += [
        "",
        "COMMIT;",
        "",
        f"-- Kontrolle 1: alte Schreibweisen – erwartet: KEINE Zeile außer den {len(ausgelassen)} oben genannten Einträgen",
        "SELECT ort, abgelehnt, COUNT(*) AS anzahl FROM public.events WHERE ort IN ("
        + ", ".join(_sql_text(a) for a in sorted({e['ort'] for e in events if e['id'] in zuweisung})) + ") GROUP BY ort, abgelehnt;",
        "",
        "-- Kontrolle 2: neue Namen mit Anzahl",
        "SELECT ort, COUNT(*) AS anzahl FROM public.events WHERE ort IN ("
        + ", ".join(_sql_text(n) for n in sorted(ids_je_name)) + ") GROUP BY ort ORDER BY anzahl DESC;",
        "",
    ]
    with open(pfad, "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen))
    logger.info("Ortsnamen: SQL geschrieben (%s) – %d Events → %d Namen, %d ausgelassen, %d Reihen-Schlüssel",
                pfad, len(zuweisung), len(ids_je_name), len(ausgelassen), len(reihen_neu))
    return len(zuweisung)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from datetime import date
    parser = argparse.ArgumentParser(description="Ortsnamen vereinheitlichen")
    parser.add_argument("--sql", action="store_true", help="SQL für den Bestand erzeugen")
    parser.add_argument("--ausgabe", default=f"database/ortsnamen_{date.today().isoformat()}.sql")
    args = parser.parse_args()
    if args.sql:
        sql_erzeugen(args.ausgabe)


if __name__ == "__main__":
    main()
