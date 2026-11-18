"""
spielstaetten_kandidaten.py – DiesDasDüsseldorf
Schritt 1 des Plans docs/plan-locations-2026-11-18.md: Kandidatenliste für eigene Ortsseiten (/orte/<slug>).

Liest die Events der letzten 12 Monate und alle kommenden (nur lesend), vereinheitlicht die Ortsnamen
(pipeline/ortsnamen.py), fasst Säle zu Häusern zusammen, ordnet Klassen zu (echter Ort, Treffpunkt, online,
allgemein) und gleicht mit der Tabelle `orte` ab (Guide-Seite vorhanden → keine zweite Seite, E1 eine URL je Ort).

Ergebnis: data/spielstaetten/kandidaten.csv zur Sichtung durch den Auftraggeber (Spalten „entscheidung“,
„name_korrigiert“, „art_korrigiert“, „bemerkung_auftraggeber“ leer zum Ausfüllen). Nichts wird in die Datenbank
geschrieben.

Aufruf im Repo-Stamm:
    python -m scraper.orte.spielstaetten_kandidaten
"""
import argparse
import csv
import logging
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from pipeline.gebiet import grund_ausserhalb
from pipeline.ortsnamen import einheitlicher_name

logger = logging.getLogger(__name__)

ZIEL = Path("data/spielstaetten/kandidaten.csv")
MIN_EVENTS = 2              # E2: ab 2 Events (12 Monate + kommend), je Haus
SAAL_EIGENE_SEITE = 20      # E6: Säle mit vielen Events bekommen zusätzlich eine eigene Seite (Vorschlag)

# Allgemeine Angaben, Treffpunkte, Straßen, Plätze → keine Ortsseite (Stadtführungen, Rundgänge)
ALLGEMEIN = re.compile(r"^(düsseldorf|duesseldorf|neuss|ratingen|altstadt( düsseldorf)?|innenstadt|tba|n\.?\s*a\.?|"
                       r"online|verschiedene orte|diverse orte|stadtgebiet.*|siehe beschreibung|wird noch bekannt gegeben|"
                       r"special events|ausstellungen|führungen, touren & freizeit|travel-packages|"
                       r"düsseldorf[ ,-]+[a-zäöüß-]+)$", re.I)
TREFFPUNKT = re.compile(
    r"(treffpunkt|ausgang|eingang|^vor (dem|der|den)\b|\bvor dem\b|u-bahnhof|s-bahnhof|s- und u-bahnhof|s-und u-bahnhof|"
    r"u-bahn station|hauptbahnhof|\bhbf\b|^düsseldorf, |denkmal|monument|skulptur|wochenmarkt|trödel|krimi-trail|"
    r"schnitzeljagd|startort|exact location)", re.I)
# Straße oder Platz als Ortsangabe – aber nicht, wenn ein Wort für einen Ort im Namen steht („Theater an der Luegallee“)
STRASSE = re.compile(r"(straße|strasse|str\.|allee|platz|weg|ufer|gasse|ecke)(\s*\d+[a-z]?)?$|^\S+(straße|strasse)\b", re.I)
ORTSWORT = re.compile(r"theater|haus|museum|galerie|bar\b|caf[eé]|club|kirche|halle|studio|kino|bühne|saal|zentrum|"
                      r"restaurant|hotel|laden|store|markt\b", re.I)
ONLINE = re.compile(r"\(online\)|^online\b|livestream|zoom", re.I)
PARK = re.compile(r"^(hofgarten|volksgarten|südpark|nordpark|rheinpark|rheinufer|rheintreppe|rheinwiesen)\b", re.I)

# Häuser mit Sälen, deren Namen keinen gemeinsamen Anfang haben (Rest: Trenner „ – “, „ — “, „ - “, „ / “)
HAUS_REGELN: list[tuple[re.Pattern, str]] = [(re.compile(p, re.I), h) for p, h in [
    (r"^düsseldorfer schauspielhaus\b|^central( \d| brücke)?$|^d.haus\b|im central|^junges schauspiel\b",
     "Düsseldorfer Schauspielhaus"),
    (r"^schauspielhaus\b", "Düsseldorfer Schauspielhaus"),
    (r"^fft\b|^bühne i{1,2}$", "FFT Düsseldorf"),
    (r"^stahlwerk\b", "Stahlwerk"),
    (r"^zakk\b", "zakk"),
    (r"^tonhalle\b|mendelssohn-saal", "Tonhalle Düsseldorf"),
    (r"^k20\b|^k21\b|kunstsammlung nrw", "Kunstsammlung NRW"),
    (r"^filmmuseum\b|^black box\b", "Filmmuseum Düsseldorf"),
    (r"^opernhaus düsseldorf\b|^deutsche oper am rhein$", "Opernhaus Düsseldorf"),
    (r"^balletthaus\b", "Balletthaus"),
    (r"^capitol theater\b", "Capitol Theater"),
    (r"^rudas studios\b", "Rudas Studios"),
    (r"^stadtbüchereien\b|^zentralbibliothek\b", "Stadtbüchereien Düsseldorf"),
]]
TRENNER = re.compile(r"\s+[–—-]\s+|\s+/\s+")

# Art (Vorschlag aus Stichwörtern; der Auftraggeber korrigiert in „art_korrigiert“)
ARTEN: list[tuple[str, re.Pattern]] = [(a, re.compile(p, re.I)) for a, p in [
    ("Oper/Theater/Bühne", r"theater|bühne|schauspiel|oper|kom\(m\)ödchen|varieté|variete|kabarett|cabaret|comedy|"
                           r"marionetten|tanzhaus|fft|ballett|kleinkunst|flin"),
    ("Museum/Ausstellung", r"museum|kunsthalle|kunstpalast|kunstsammlung|\bk20\b|\bk21\b|nrw-forum|palais|\bkit\b|"
                           r"galerie|gallery|sammlung|ausstellung|aquazoo|planetarium|schloss|kunstverein|\bbbk\b"),
    ("Konzert/Halle/Arena", r"\bhalle\b|arena|\bdome\b|stadion|tonhalle|robert-schumann-saal|jazz|stahlwerk|messe\b"),
    ("Kino", r"kino|filmmuseum|filmwerkstatt|filmstudio|\bufa\b|ufa-palast|metropol|bambi|cinema|cinestar|black box"),
    ("Club/Bar/Kneipe", r"club|klub|bar\b|pub\b|kneipe|brauerei|brauhaus|lounge|disco|nachtresidenz|bunker|"
                        r"zakk|pitcher|kulturschlachthof|rudas|ratinger hof|salon des amateurs"),
    ("Bibliothek/Bildung", r"bibliothek|bücherei|library|volkshochschule|vhs|hochschule|akademie|universität|ihk"),
    ("Kirche/Gemeinde", r"kirche|gemeinde|basilika|kloster|synagoge|moschee|maxhaus"),
    ("Kurs/Studio/Sport", r"yoga|studio|keramik|atelier|tanzstudio|boulder|sport|fitness|badminton|kurs|werkstatt|"
                          r"malstudio|craft|cageball|parkrun"),
    ("Café/Restaurant", r"café|cafe|restaurant|delikatessen|bistro|trattoria|kaffee|brettspielcafé"),
    ("Kultur-/Bürgerzentrum", r"zentrum|bürgerhaus|forum|haus\b|treff|quartier|kulturraum|salzmannbau"),
]]


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", t or "").lower()
    t = t.translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    t = re.sub(r"\b(duesseldorf|dusseldorf)\b", " ", t)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def klasse(name: str) -> str:
    if ALLGEMEIN.match(name.strip()):
        return "allgemein"
    if ONLINE.search(name):
        return "online"
    if TREFFPUNKT.search(name) or PARK.match(name):
        return "treffpunkt"
    if STRASSE.search(name) and not ORTSWORT.search(name):
        return "treffpunkt"
    return "ort"


def art_vorschlag(name: str) -> str:
    for art, muster in ARTEN:
        if muster.search(name):
            return art
    return "Sonstiges"


def _seitenweise(db, tabelle: str, spalten: str, filter_fn=None) -> list[dict]:
    zeilen, start = [], 0
    while True:
        q = db.table(tabelle).select(spalten)
        if filter_fn:
            q = filter_fn(q)
        teil = q.range(start, start + 999).execute().data or []
        zeilen.extend(teil)
        if len(teil) < 1000:
            return zeilen
        start += 1000


def haus_und_saal(name: str, alle_namen: set[str]) -> tuple[str, str]:
    """Haus und Saal aus einem (vereinheitlichten) Ortsnamen; ohne Saal ist der Saal leer."""
    for muster, haus in HAUS_REGELN:
        if muster.search(name):
            saal = "" if _norm(name) == _norm(haus) else name
            return haus, saal
    teile = TRENNER.split(name, maxsplit=1)
    if len(teile) == 2 and ALLGEMEIN.match(teile[0].strip()):
        return teile[1].strip(), ""
    if len(teile) == 2:
        links = teile[0].strip()
        # Nur trennen, wenn der linke Teil selbst als Ort vorkommt oder mehrere Säle hat (sonst „Auf ins Viertel – …“)
        if links in alle_namen or sum(1 for n in alle_namen if n.startswith(links + " ")) >= 2:
            return links, name
    return name, ""


def liste_erzeugen(ziel: Path = ZIEL) -> int:
    from database.client import get_supabase_client

    db = get_supabase_client()
    heute = date.today()
    von = (heute - timedelta(days=365)).isoformat()
    events = _seitenweise(db, "events", "ort, adresse, stadtteil, datum, datum_bis, abgelehnt, quelle_name",
                          lambda q: q.gte("datum", von))
    orte = _seitenweise(db, "orte", "name, slug, typ, aktiv, qualitaets_score, extras->club")
    logger.info("Kandidaten: %d Events seit %s, %d Orte-Zeilen", len(events), von, len(orte))

    # Guide-Abgleich (E1): sichtbarer Guide-Ort, Club-Verknüpfung, in `orte` aber unsichtbar
    guide: dict[str, str] = {}
    for o in orte:
        sichtbar = o.get("aktiv") and ((o.get("qualitaets_score") or 0) >= 7
                                        or o["typ"] in ("spielplatz", "weihnachtsmarkt", "club"))
        k = _norm(o["name"])
        stand = f"Guide ({o['typ']}): {o['slug']}" if sichtbar else f"in orte, unsichtbar ({o['typ']})"
        if k not in guide or sichtbar:
            guide[k] = stand
        club = o.get("club") or {}
        if isinstance(club, dict):
            for eo in club.get("event_orte") or []:
                guide[_norm(einheitlicher_name(eo) or eo)] = f"Club: {o['slug']}"

    namen: dict[str, dict] = defaultdict(lambda: {"alle": 0, "kommend": 0, "roh": Counter(), "adresse": Counter(),
                                                    "stadtteil": Counter(), "quelle": Counter()})
    ausserhalb = 0
    for e in events:
        if e.get("abgelehnt") or not (e.get("ort") or "").strip():
            continue
        if grund_ausserhalb(e):
            ausserhalb += 1
            continue
        roh = e["ort"].strip()
        name = einheitlicher_name(roh) or roh
        n = namen[name]
        n["alle"] += 1
        if (e.get("datum_bis") or e["datum"]) >= heute.isoformat():
            n["kommend"] += 1
        n["roh"][roh] += 1
        if e.get("adresse"):
            n["adresse"][e["adresse"]] += 1
        if e.get("stadtteil"):
            n["stadtteil"][e["stadtteil"]] += 1
        n["quelle"][e.get("quelle_name") or "?"] += 1

    alle_namen = set(namen)
    haeuser: dict[str, dict] = defaultdict(lambda: {"alle": 0, "kommend": 0, "saele": Counter(), "roh": Counter(),
                                                     "adresse": Counter(), "stadtteil": Counter(), "quelle": Counter(),
                                                     "klassen": Counter()})
    schreibung: dict[str, Counter] = defaultdict(Counter)
    for name, n in namen.items():
        haus, _ = haus_und_saal(name, alle_namen)
        schreibung[_norm(haus)][haus] += n["alle"]
    for name, n in namen.items():
        haus, saal = haus_und_saal(name, alle_namen)
        haus = schreibung[_norm(haus)].most_common(1)[0][0]  # „salon des amateurs“ → „Salon des Amateurs“
        h = haeuser[haus]
        h["alle"] += n["alle"]
        h["kommend"] += n["kommend"]
        if saal:
            h["saele"][saal] += n["alle"]
        h["roh"].update(n["roh"])
        h["adresse"].update(n["adresse"])
        h["stadtteil"].update(n["stadtteil"])
        h["quelle"].update(n["quelle"])
        kl = klasse(name)
        # Meetup-Gruppe ohne Ort: Der „Ort“ ist der Gruppenname (z. B. „NEU #GoFreizeitGO“), kein Veranstaltungsort
        if kl == "ort" and not n["adresse"] and set(n["quelle"]) == {"Meetup.com"}:
            kl = "gruppe"
        h["klassen"][kl] += n["alle"]

    # Dubletten-Hinweis: gleiche Adresse bei verschiedenen Häusern
    nach_adresse: dict[str, list[str]] = defaultdict(list)
    for haus, h in haeuser.items():
        if h["adresse"]:
            a = _norm(re.sub(r",?\s*(germany|deutschland)$", "", h["adresse"].most_common(1)[0][0], flags=re.I))
            if len(a) > 8:
                nach_adresse[a].append(haus)

    zeilen = []
    for haus, h in haeuser.items():
        if h["alle"] < MIN_EVENTS:
            continue
        kl = h["klassen"].most_common(1)[0][0]
        g = guide.get(_norm(haus)) or next((guide[_norm(s)] for s in h["saele"] if _norm(s) in guide), "")
        adresse = h["adresse"].most_common(1)[0][0] if h["adresse"] else ""
        plz = (re.search(r"\b(4\d{4})\b", adresse) or [None, ""])[1]
        gleich = []
        if adresse:
            a = _norm(re.sub(r",?\s*(germany|deutschland)$", "", adresse, flags=re.I))
            gleich = [x for x in nach_adresse.get(a, []) if x != haus]
        if kl != "ort":
            vorschlag = f"keine Seite ({kl})"
        elif g.startswith("Guide") or g.startswith("Club"):
            vorschlag = "Guide-Seite vorhanden: Events dort zeigen, /orte leitet weiter"
        else:
            vorschlag = "neue Ortsseite"
        saele = "; ".join(f"{s} ({n}{', eigene Seite' if n >= SAAL_EIGENE_SEITE else ''})"
                          for s, n in h["saele"].most_common())
        bemerkung = []
        if gleich:
            bemerkung.append("gleiche Adresse wie: " + ", ".join(sorted(gleich)[:4]))
        if not adresse:
            bemerkung.append("Adresse fehlt")
        if haus == "Stadtbüchereien Düsseldorf":
            bemerkung.append("E7 je Filiale: Quelle liefert die Filiale noch nicht (alle mit KAP1-Adresse)")
        zeilen.append({
            "haus": haus,
            "vorschlag": vorschlag,
            "art_vorschlag": art_vorschlag(haus + " " + " ".join(h["saele"])),
            "events_12m_und_kommend": h["alle"],
            "events_kommend": h["kommend"],
            "saele": saele,
            "adresse": adresse,
            "plz": plz,
            "stadtteil": h["stadtteil"].most_common(1)[0][0] if h["stadtteil"] else "",
            "guide_status": g,
            "schreibweisen": "; ".join(r for r, _ in h["roh"].most_common(8)),
            "quellen": "; ".join(f"{q} ({n})" for q, n in h["quelle"].most_common(3)),
            "hinweis": "; ".join(bemerkung),
            "entscheidung": "",
            "name_korrigiert": "",
            "art_korrigiert": "",
            "bemerkung_auftraggeber": "",
        })
    reihenfolge = {"neue Ortsseite": 0, "Guide-Seite vorhanden: Events dort zeigen, /orte leitet weiter": 1}
    zeilen.sort(key=lambda z: (reihenfolge.get(z["vorschlag"], 2), -z["events_12m_und_kommend"], z["haus"].lower()))

    ziel.parent.mkdir(parents=True, exist_ok=True)
    with ziel.open("w", encoding="utf-8-sig", newline="") as f:  # mit BOM, damit Excel die Umlaute richtig zeigt
        w = csv.DictWriter(f, fieldnames=list(zeilen[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    zaehler = Counter(z["vorschlag"].split(" (")[0] for z in zeilen)
    logger.info("Kandidaten: %d Häuser ab %d Events geschrieben nach %s – %s; %d Events außerhalb übersprungen",
                len(zeilen), MIN_EVENTS, ziel, dict(zaehler), ausserhalb)
    return len(zeilen)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
    except ImportError:
        pass
    parser = argparse.ArgumentParser(description="Kandidatenliste für Ortsseiten (nur lesend)")
    parser.add_argument("--ausgabe", default=str(ZIEL))
    liste_erzeugen(Path(parser.parse_args().ausgabe))


if __name__ == "__main__":
    main()
