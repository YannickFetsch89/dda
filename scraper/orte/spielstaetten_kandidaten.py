"""
spielstaetten_kandidaten.py – DiesDasDüsseldorf
Schritt 1 des Plans docs/plan-locations-2026-11-18.md (freigegeben 19.11.2026): Kandidatenliste für eigene
Ortsseiten (/orte/<slug>).

Liest die Events der letzten 12 Monate und alle kommenden (nur lesend), vereinheitlicht die Ortsnamen
(pipeline/ortsnamen.py), fasst Schreibweisen zu Häusern zusammen, ordnet Klassen zu (echter Ort, Treffpunkt, online,
allgemein, Gruppe) und gleicht mit der Tabelle `orte` ab (Guide-Seite vorhanden → keine zweite Seite, E1).

Je Haus eine Entscheidungszeile; dazu je Saal aus SAALLISTE (Plan 3.6) und je Standort (K20/K21) eine eigene Zeile.
Ketten, unsichtbare Guide-Zeilen, das Büchereinetz und Treffpunkte bekommen „keine Seite“ (Plan 7.2).

Ergebnis: data/spielstaetten/kandidaten.csv zur Sichtung durch den Auftraggeber (Spalten „entscheidung“,
„name_korrigiert“, „art_korrigiert“, „bemerkung_auftraggeber“). Schon eingetragene Entscheidungen bleiben beim
Neuerzeugen erhalten (Plan 7.2 Punkt 11). Nichts wird in die Datenbank geschrieben.

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
from pipeline.slug_generator import _slugify

logger = logging.getLogger(__name__)

ZIEL = Path("data/spielstaetten/kandidaten.csv")
MIN_EVENTS = 2              # E2: ab 2 Events (12 Monate + kommend)
SAAL_EIGENE_SEITE = 20      # E6: nur Hinweis „eigene Seite empfohlen“, filtert keine Zeile weg (Plan 3.6)
AUFTRAGGEBER_SPALTEN = ("entscheidung", "name_korrigiert", "art_korrigiert", "bemerkung_auftraggeber")

# ── Klassen ─────────────────────────────────────────────────────────────────────────────────────────────────────

# Allgemeine Angaben → keine Ortsseite
ALLGEMEIN = re.compile(r"^(düsseldorf|duesseldorf|neuss|ratingen|altstadt( düsseldorf)?|innenstadt|tba|n\.?\s*a\.?|"
                       r"online|verschiedene orte|diverse orte|stadtgebiet.*|siehe beschreibung|wird noch bekannt gegeben|"
                       r"special events|ausstellungen|führungen, touren & freizeit|travel-packages|"
                       r"düsseldorf[ ,-]+[a-zäöüß-]+)$", re.I)
# Treffpunkte von Führungen und Rundgängen → keine Ortsseite (7.2 Punkt 3: Tourist-Information)
TREFFPUNKT = re.compile(
    r"(treffpunkt|ausgang|eingang|^vor (dem|der|den)\b|\bvor dem\b|u-bahnhof|s-bahnhof|s- und u-bahnhof|s-und u-bahnhof|"
    r"u-bahn station|hauptbahnhof|\bhbf\b|^düsseldorf, |denkmal|monument|skulptur|wochenmarkt|trödel|krimi-trail|"
    r"schnitzeljagd|startort|exact location|tourist-information|tourist information|touristinformation)", re.I)
# Straße oder Platz als Ortsangabe; ein nachgestellter Stadtname zählt nicht („Marktplatz Düsseldorf“, 7.2 Punkt 2)
STRASSE = re.compile(r"(straße|strasse|str\.|allee|platz|weg|ufer|gasse|ecke)(\s*\d+[a-z]?)?$|^\S+(straße|strasse)\b", re.I)
STADT_AM_ENDE = re.compile(r"[\s,]+(düsseldorf|duesseldorf|neuss|ratingen)$", re.I)
# Wort für einen Ort, nur am Wortende („Turnhalle“, „Kulturzentrum“ ja; „saal“ in „Hansaallee“ nein, 7.2 Punkt 1)
ORTSWORT = re.compile(r"(theater|haus|museum|galerie|bar|caf[eé]|club|kirche|halle|studio|kino|bühne|saal|zentrum|"
                      r"restaurant|hotel|laden|store|markt)\b", re.I)
ONLINE = re.compile(r"\(online\)|^online\b|livestream|zoom", re.I)
PARK = re.compile(r"^(hofgarten|volksgarten|südpark|nordpark|rheinpark|rheinufer|rheintreppe|rheinwiesen)\b", re.I)

# Ketten mit vielen Filialen und einer `orte`-Zeile: keine stadtweite Seite (Plan 3.2, 7.2 Punkt 14), als Wortanfang
KETTE = re.compile(r"^(starbucks|(caf[eé] )?extrablatt|alex)\b", re.I)


def nicht_im(name: str) -> bool:
    """
    „zakk – nicht im zakk“: findet ausdrücklich nicht im Haus statt. Gleiche Regel wie in event_orte()
    (scraper/orte/clubs_profil.py): „Pitcher, nicht im Freien“ und „nicht im Saal, sondern im …“ gehören zum Ort.
    In Schritt 2 wandert die Regel in die gemeinsame Funktion nicht_im_ort (Plan 3.4).
    """
    m = re.search(r"\bnicht im\b(.*)$", name, re.I)
    if not m or re.search(r"\b(sondern|aber|dafür)\b", m.group(1), re.I):
        return False
    rest, links = _norm(m.group(1)), _norm(name[:m.start()])
    # Nur wenn der Ort hinter „nicht im“ der Ort vorne ist („zakk – nicht im zakk“), nicht „Pitcher, nicht im Freien“
    return bool(rest) and bool(links) and (rest in links or links.split()[0] == rest.split()[0])


def klasse(name: str) -> str:
    if ALLGEMEIN.match(name.strip()):
        return "allgemein"
    if ONLINE.search(name):
        return "online"
    if TREFFPUNKT.search(name) or PARK.match(name):
        return "treffpunkt"
    ohne_stadt = STADT_AM_ENDE.sub("", name.strip())
    if STRASSE.search(ohne_stadt) and not ORTSWORT.search(ohne_stadt):
        return "treffpunkt"
    return "ort"


# ── Arten ───────────────────────────────────────────────────────────────────────────────────────────────────────

# Ausdrückliche Art für Häuser ohne Art-Wort im Namen (Plan 7.2 Punkt 15/18), Name normalisiert → Art. Vorschlag,
# der Auftraggeber bestätigt in „art_korrigiert“.
ART_NAMEN: dict[str, tuple[str, str]] = {
    "gerhart hauptmann haus": ("Kultur-/Bürgerzentrum", ""),
    "zentrum plus holthausen": ("Kultur-/Bürgerzentrum", ""),
    "eko haus der japanischen kultur": ("Kultur-/Bürgerzentrum", ""),
    "haus spilles": ("Kultur-/Bürgerzentrum", "Art prüfen"),
    "rigpa zentrum": ("Kirche/Gemeinde", "Art prüfen (buddhistisches Zentrum)"),
    "heine haus literaturhaus": ("Kultur-/Bürgerzentrum", ""),
    "asg bildungsforum": ("Bibliothek/Bildung", ""),
    "nilsson initiativen haus": ("Kultur-/Bürgerzentrum", ""),
    "rathaus": ("Öffentliches Gebäude", "Art bestätigen (Abschnitt 9)"),
    "alter bahnhof oberkassel": ("Gastronomie/Eventlocation", "Art und Adresse prüfen (Abschnitt 9)"),
}

# Café im Haus einer Institution vor allen anderen Arten („Xafe in KAP 1 Zentralbibliothek“, 7.2 Punkt 12)
CAFE_VORRANG = re.compile(r"(^|\s)(café|cafe|xafe|kaffeebar)\b", re.I)

ARTEN: list[tuple[str, re.Pattern]] = [(a, re.compile(p, re.I)) for a, p in [
    ("Oper/Theater/Bühne", r"theater|bühne|schauspiel|oper|kom\(m\)ödchen|varieté|variete|kabarett|cabaret|comedy|"
                           r"marionetten|tanzhaus|fft|ballett|kleinkunst|\bflin\b"),
    ("Museum/Ausstellung", r"museum|kunsthalle|kunstpalast|kunstsammlung|\bk20\b|\bk21\b|nrw-forum|palais|\bkit\b|"
                           r"galerie|gallery|sammlung|ausstellung|aquazoo|planetarium|schloss|kunstverein|\bbbk\b"),
    ("Kurs/Studio/Sport", r"billard|turnhalle|sporthalle"),
    ("Konzert/Halle/Arena", r"\bhalle\b|arena|\bdome\b|stadion|tonhalle|robert-schumann-saal|jazz|stahlwerk|messe\b"),
    ("Kino", r"kino|filmmuseum|filmwerkstatt|filmstudio|\bufa\b|ufa-palast|metropol|bambi|cinema|cinestar|black box"),
    ("Club/Bar/Kneipe", r"club|klub|bar\b|pub\b|kneipe|brauerei|brauhaus|lounge|disco|nachtresidenz|bunker|"
                        r"zakk|pitcher|kulturschlachthof|rudas|ratinger hof|salon des amateurs"),
    ("Bibliothek/Bildung", r"bibliothek|bücherei|library|volkshochschule|vhs|hochschule|akademie|universität|ihk"),
    ("Kirche/Gemeinde", r"kirche|gemeinde|basilika|kloster|synagoge|moschee|maxhaus|pfarr"),
    ("Kurs/Studio/Sport", r"yoga|studio|keramik|atelier|tanzstudio|boulder|sport|fitness|badminton|kurs|werkstatt|"
                          r"malstudio|craft|cageball|parkrun"),
    ("Café/Restaurant", r"café|cafe|restaurant|delikatessen|bistro|trattoria|kaffee|brettspielcafé"),
    # Eng gefasst (7.2 Punkt 6/18): kein freies „haus“, „forum“, „zentrum“ – sonst Rathaus, Pfarrzentrum, Billardzentrum
    ("Kultur-/Bürgerzentrum", r"kulturzentrum|bürgerzentrum|stadtteilzentrum|bürgerhaus|gemeindehaus|kulturhaus|"
                              r"klanghaus|literaturhaus|\btreff\b|quartier|kulturraum|salzmannbau"),
]]


def art_vorschlag(name: str, zusatz: str = "") -> tuple[str, str]:
    """Art und ggf. Prüfhinweis. Erst die Namensliste, dann Café-Vorrang, dann die Muster (Name vor Saalnamen)."""
    k = _norm(name)
    for schluessel, (art, hinweis) in ART_NAMEN.items():
        if k == schluessel or k.startswith(schluessel + " "):
            return art, hinweis
    if CAFE_VORRANG.search(name):
        return "Café/Restaurant", ""
    for text in (name, f"{name} {zusatz}"):
        for art, muster in ARTEN:
            if muster.search(text):
                return art, ""
    return "Sonstiges", ""


# ── Häuser, Säle, Standorte, Dubletten ──────────────────────────────────────────────────────────────────────────

# Häuser mit Sälen, deren Namen keinen gemeinsamen Anfang haben
HAUS_REGELN: list[tuple[re.Pattern, str]] = [(re.compile(p, re.I), h) for p, h in [
    # Das Central ist eine eigene Spielstätte des Schauspielhauses am Hauptbahnhof (Worringer Straße 140,
    # visitduesseldorf.de „D'haus Central“), mit den Sälen Central 1, Central 2, Central Brücke. Entscheidung
    # 19.11.2026: eigenes Haus mit eigener Adresse und Karte, kein Saal des Hauses am Gustaf-Gründgens-Platz.
    (r"^central( \d| brücke)?$|\bim central\b|^d.haus central$", "D’haus Central"),
    (r"^düsseldorfer schauspielhaus\b|^d.haus\b|^junges schauspiel\b", "Düsseldorfer Schauspielhaus"),
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
    (r"^stadtbüchereien\b|^zentralbibliothek\b|^düsseldorf city libraries$", "Stadtbüchereien Düsseldorf"),
]]
# Teile hinter einem Trenner, die nur der Name des Hauses selbst sind – weder Saal noch Hinweis „Saal?“
KEIN_SAAL: dict[str, re.Pattern] = {
    "Düsseldorfer Schauspielhaus": re.compile(r"[–—-]\s+d.haus$", re.I),
    "Opernhaus Düsseldorf": re.compile(r"^deutsche oper am rhein$", re.I),
    "D’haus Central": re.compile(r"\bim central\b|^central$", re.I),
}
# Stadtname einer Nachbarstadt als ganzes Wort im Namen („Mayersche Essen“): der Gebietsfilter erkennt ihn nur als
# eigenen Abschnitt (pipeline/gebiet.py). Keine Seite, Prüfung im Gebietsfilter-Nachtrag (Schritt 2, Plan 3.16).
NACHBARSTADT = re.compile(r"\b(essen|köln|koeln|mülheim|frankfurt)\b", re.I)
TRENNER = re.compile(r"\s+[–—-]\s+|\s+/\s+")

# Saalliste je Haus (Plan 3.6): Saal → Muster auf den vereinheitlichten Ortsnamen. Nur diese Säle bekommen eine
# eigene Entscheidungszeile; jeder andere Teil hinter einem Trenner bleibt Schreibweise des Hauses (7.2 Punkt 21).
SAALLISTE: dict[str, list[tuple[str, re.Pattern]]] = {h: [(s, re.compile(p, re.I)) for s, p in liste] for h, liste in {
    "zakk": [("Halle", r"^zakk\s+[–—-]\s+halle$"), ("Club", r"^zakk\s+[–—-]\s+club$"),
             ("Studio", r"^zakk\s+[–—-]\s+studio$"), ("Tanzraum", r"^zakk\s+[–—-]\s+tanzraum$"),
             ("Raum 4", r"^zakk\s+[–—-]\s+raum 4$"), ("Kneipe", r"^zakk\s+[–—-]\s+kneipe$")],
    "FFT Düsseldorf": [("Bühne I", r"^(fft düsseldorf\s+[–—-]\s+)?bühne i$"),
                       ("Bühne II", r"^(fft düsseldorf\s+[–—-]\s+)?bühne ii$")],
    "Düsseldorfer Schauspielhaus": [
        ("Großes Haus", r"großes haus"), ("Kleines Haus", r"kleines haus"), ("Foyer", r"schauspielhaus.*foyer"),
        ("Junges Schauspiel", r"junges schauspiel"), ("Unterhaus", r"unterhaus")],
    "D’haus Central": [("Central 1", r"^central 1$"), ("Central 2", r"^central 2$"),
                       ("Central Brücke", r"^central brücke$")],
    "Tonhalle Düsseldorf": [("Mendelssohn-Saal", r"mendelssohn-saal"), ("Rotunde", r"rotunde"),
                            ("Trautvetter-Brückner-Saal", r"trautvetter"), ("Terrace", r"terrace")],
    "Opernhaus Düsseldorf": [("Foyer", r"^opernhaus düsseldorf.*foyer")],
    "Capitol Theater": [("Club Saal", r"club saal")],
    "Balletthaus": [("Studio 1", r"studio 1\b"), ("Studio 2", r"studio 2\b")],
    "Filmmuseum Düsseldorf": [("Black Box", r"black box")],
}.items()}

# Standorte eines Dachs: eigene Zeilen statt Säle (K20/K21, Plan 3.6), Dachzeile nur mit Entscheidung in Abschnitt 9
STANDORTE: dict[str, list[tuple[str, re.Pattern]]] = {
    "Kunstsammlung NRW": [("K20 Grabbeplatz", re.compile(r"^k20\b", re.I)), ("K21 Ständehaus", re.compile(r"^k21\b", re.I))],
}

# Bücherei: das Netz bekommt keine Seite, die Zentralbibliothek KAP1 eine eigene Filialzeile (Plan 3.15, 7.2 Punkt 20)
BUECHEREI_NETZ = "Stadtbüchereien Düsseldorf"
KAP1 = ("Zentralbibliothek KAP1", re.compile(r"^zentralbibliothek kap ?1$", re.I))

# Dubletten, die vor der Sichtung zusammengeführt werden (Plan 3.7): Muster auf den Namen → gemeinsames Haus
DUBLETTEN: list[tuple[re.Pattern, str]] = [
    # „Holocafé Düsseldorf“ (mit é) hat die Adresse Am Wehrhahn 41: getrennt bis zur Prüfung, eigener Name, damit die
    # Normalisierung (é → e) es nicht mit den Immermannstraße-Schreibweisen zusammenlegt
    (re.compile(r"^holocaf(é|é) düsseldorf$", re.I), "Holocafé am Wehrhahn"),
    (re.compile(r"^holo ?cafe( düsseldorf)?$|^holocafe immermannstraße 7$", re.I), "Holocafe"),
    (re.compile(r"^(cafe bar )?la pail+ette\b", re.I), "La Paillette"),
    # Entscheidung 19.11.2026 (Arten der 89): doppelte Zeilen desselben Orts
    (re.compile(r"^es365( art center)?$", re.I), "ES365 Art Center"),
    (re.compile(r"^tribe( hotel)? düsseldorf$", re.I), "TRIBE Hotel Düsseldorf"),
    (re.compile(r"^wp8( künstlerverein)?$", re.I), "WP8 Künstlerverein"),
]
# Getrennt bis zur Prüfung (Plan 3.7, 7.2 Punkte 9 und 13): Name normalisiert → Prüfhinweis
PRUEFHINWEISE: dict[str, str] = {
    "bambi": "Dublette? Bambi-Kino liegt an der Klosterstraße, hier Ehrenhof 2 (NRW-Forum) – Adresse prüfen",
    "bambi filmstudio": "Dublette? Adresse Klosterstraße prüfen (zweite Bambi-Zeile)",
    "holocafe": "zusammengeführt: Holo Cafe, Holocafe Düsseldorf, Holocafe Immermannstraße 7 (Plan 3.7)",
    "holocafe am wehrhahn": "getrennt bis zur Prüfung: zweiter Standort des Holocafe? (Plan 3.7)",
    "xafe in kap 1 zentralbibliothek": "gleiche Adresse wie Zentralbibliothek, nicht zusammenlegen",
}
# Offene Einzelentscheidungen (Plan Abschnitt 9): keine Seite und kein 308, bis entschieden
ABSCHNITT_9: dict[str, str] = {
    "theater an der koe": "eigene Ortsseite? Verknüpfung mit dem Kö-Club wird in jedem Fall gelöst (Abschnitt 9, 3.2)",
}
# Entschieden vom Auftraggeber am 19.11.2026 (Abschnitt 9): Name normalisiert → (Vorschlag oder leer, Hinweis)
ENTSCHIEDEN: dict[str, tuple[str, str]] = {
    "stone im ratinger hof": ("keine Seite (geschlossen)",
                              "seit Jahren geschlossen – Events werden auf „Ratinger Hof“ umgeschrieben (Schritt 2)"),
    "bilker bunker": ("", "eigener Ort trotz gleicher Adresse wie Schleuse Zwei (Entscheidung 19.11.2026)"),
    "schleuse zwei": ("", "eigener Ort trotz gleicher Adresse wie Bilker Bunker (Entscheidung 19.11.2026)"),
}
# Kein Haus, keine Seite (Plan 3.7)
KEIN_HAUS = re.compile(r"gustaf-gründgens-platz", re.I)


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", t or "").lower()
    t = t.translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")  # „ō“, „é“ → o, e
    t = re.sub(r"\b(duesseldorf|dusseldorf)\b", " ", t)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


SLUG_HAUS: dict[str, str] = {"D’haus Central": "dhaus-central"}  # sonst „d-haus-central“ (Apostroph)


def slug_vorschlag(name: str) -> str:
    """Slug wie _slug_erzeugen(name, stadtteil) in scraper/orte/google_places.py – ohne Stadtteil, solange er nicht
    bestätigt ist (Plan 3.3 Punkt 7; der Anhang folgt erst mit der bestätigten Adresse in Schritt 2)."""
    return SLUG_HAUS.get(name) or _slugify(name)


def saal_slug(haus_slug: str, haus: str, saal: str) -> str:
    """Haus-Slug plus Saal; ein Saalname, der mit dem letzten Wort des Hauses beginnt, ohne Dopplung
    („D’haus Central“ + „Central 1“ → dhaus-central-1)."""
    letztes = _norm(haus).split()[-1] if _norm(haus) else ""
    teil = _norm(saal)
    if letztes and teil.startswith(letztes + " "):
        teil = teil[len(letztes) + 1:]
    return f"{haus_slug}-{_slugify(teil)}"


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
    """Haus und Teilname aus einem (vereinheitlichten) Ortsnamen; ohne Teil ist der zweite Wert leer."""
    for muster, haus in DUBLETTEN:
        if muster.search(name):
            return haus, ""
    for muster, haus in HAUS_REGELN:
        if muster.search(name):
            saal = "" if _norm(name) == _norm(haus) else name
            return haus, saal
    teile = TRENNER.split(name, maxsplit=1)
    if len(teile) == 2 and ALLGEMEIN.match(teile[0].strip()):
        return teile[1].strip(), ""
    if len(teile) == 2:
        links = teile[0].strip()
        # Nur trennen, wenn der linke Teil selbst als Ort vorkommt oder mehrere Teile hat (sonst „Auf ins Viertel – …“)
        if links in alle_namen or sum(1 for n in alle_namen if n.startswith(links + " ")) >= 2:
            return links, name
    return name, ""


def saal_aus_liste(haus: str, teilname: str) -> str:
    """Saal aus der Saalliste (Plan 3.6) – sonst leer (Teil bleibt Schreibweise des Hauses)."""
    for saal, muster in SAALLISTE.get(haus, []):
        if muster.search(teilname):
            return saal
    return ""


def standort_aus_liste(haus: str, teilname: str) -> str:
    for standort, muster in STANDORTE.get(haus, []):
        if muster.search(teilname):
            return standort
    return ""


# ── Entscheidungen erhalten ─────────────────────────────────────────────────────────────────────────────────────

def zeilen_schluessel(name: str, gehoert_zu: str = "") -> str:
    """Schlüssel einer Entscheidungszeile: Haus (bzw. Saal/Standort) plus Haus, normalisiert, Dubletten aufgelöst."""
    for muster, haus in DUBLETTEN:
        if muster.search(name):
            name = haus
    return f"{_norm(name)}|{_norm(gehoert_zu)}"


def entscheidungen_lesen(pfad: Path) -> dict[str, list[dict]]:
    """Schon eingetragene Entscheidungen der bisherigen CSV, je Schlüssel (mehrere bei zusammengeführten Dubletten)."""
    if not pfad.exists():
        return {}
    alt: dict[str, list[dict]] = defaultdict(list)
    with pfad.open(encoding="utf-8-sig", newline="") as f:
        for z in csv.DictReader(f, delimiter=";"):
            werte = {s: (z.get(s) or "").strip() for s in AUFTRAGGEBER_SPALTEN}
            if any(werte.values()):
                alt[zeilen_schluessel(z.get("haus") or "", z.get("gehoert_zu") or "")].append(werte)
    return alt


def entscheidungen_uebernehmen(zeilen: list[dict], alt: dict[str, list[dict]]) -> int:
    """Übernimmt Entscheidungen; widersprechen sich mehrere (Dubletten), bleibt die Zeile leer mit Hinweis."""
    uebernommen = 0
    for z in zeilen:
        kandidaten = alt.get(zeilen_schluessel(z["haus"], z["gehoert_zu"])) or []
        verschieden = {tuple(k[s] for s in AUFTRAGGEBER_SPALTEN) for k in kandidaten}
        if len(verschieden) == 1:
            z.update(kandidaten[0])
            uebernommen += 1
        elif len(verschieden) > 1:
            z["hinweis"] = "; ".join(x for x in [z["hinweis"], "Entscheidung prüfen (Dubletten widersprechen sich)"] if x)
    return uebernommen


# ── Liste ───────────────────────────────────────────────────────────────────────────────────────────────────────

def _haus_neu() -> dict:
    return {"alle": 0, "kommend": 0, "teile": Counter(), "roh": Counter(), "adresse": Counter(), "stadtteil": Counter(),
            "quelle": Counter(), "klassen": Counter(), "nicht_im": Counter()}


def _plz(adresse: str) -> str:
    return (re.search(r"\b(4\d{4})\b", adresse or "") or [None, ""])[1]


def zeilen_bauen(namen: dict[str, dict], guide: dict[str, str], guide_slugs: dict[str, str],
                 vergebene_slugs: set[str]) -> list[dict]:
    """Entscheidungszeilen aus den Ortsnamen (rein, testbar). `namen`: vereinheitlichter Name → Zähler."""
    alle_namen = set(namen)
    haeuser: dict[str, dict] = defaultdict(_haus_neu)
    unterzeilen: dict[tuple[str, str, str], dict] = defaultdict(_haus_neu)  # (Haus, Saal/Standort, Typ)
    schreibung: dict[str, Counter] = defaultdict(Counter)
    for name, n in namen.items():
        haus, _ = haus_und_saal(name, alle_namen)
        schreibung[_norm(haus)][haus] += n["alle"]

    for name, n in namen.items():
        haus, teil = haus_und_saal(name, alle_namen)
        haus = schreibung[_norm(haus)].most_common(1)[0][0]  # „salon des amateurs“ → „Salon des Amateurs“
        h = haeuser[haus]
        if nicht_im(name):
            h["nicht_im"][name] += n["alle"]  # zählt nicht zum Programm des Hauses (Plan 3.4)
            continue
        h["alle"] += n["alle"]
        h["kommend"] += n["kommend"]
        for feld in ("roh", "adresse", "stadtteil", "quelle"):
            h[feld].update(n[feld])
        kl = klasse(name)
        # Meetup-Gruppe ohne Ort: Der „Ort“ ist der Gruppenname (z. B. „NEU #GoFreizeitGO“), kein Veranstaltungsort
        if kl == "ort" and not n["adresse"] and set(n["quelle"]) == {"Meetup.com"}:
            kl = "gruppe"
        h["klassen"][kl] += n["alle"]
        if teil:
            h["teile"][teil] += n["alle"]
        unter = None
        if haus == BUECHEREI_NETZ and KAP1[1].match(name):
            unter = (haus, KAP1[0], "filiale")
        elif teil and (s := standort_aus_liste(haus, teil)):
            unter = (haus, s, "standort")
        elif teil and (s := saal_aus_liste(haus, teil)):
            unter = (haus, s, "saal")
        if unter:
            u = unterzeilen[unter]
            u["alle"] += n["alle"]
            u["kommend"] += n["kommend"]
            for feld in ("roh", "adresse", "stadtteil", "quelle"):
                u[feld].update(n[feld])

    # Dubletten-Hinweis: gleiche Adresse bei verschiedenen Häusern
    nach_adresse: dict[str, list[str]] = defaultdict(list)
    for haus, h in haeuser.items():
        if h["adresse"]:
            a = _norm(re.sub(r",?\s*(germany|deutschland)$", "", h["adresse"].most_common(1)[0][0], flags=re.I))
            if len(a) > 8:
                nach_adresse[a].append(haus)

    zeilen: list[dict] = []
    for haus, h in haeuser.items():
        if h["alle"] < MIN_EVENTS:
            continue
        kl = h["klassen"].most_common(1)[0][0]
        k = _norm(haus)
        g = guide.get(k) or next((guide[_norm(s)] for s in h["teile"] if _norm(s) in guide), "")
        adresse = h["adresse"].most_common(1)[0][0] if h["adresse"] else ""
        hinweis: list[str] = []
        if adresse:
            a = _norm(re.sub(r",?\s*(germany|deutschland)$", "", adresse, flags=re.I))
            gleich = [x for x in nach_adresse.get(a, []) if x != haus]
            if gleich:
                hinweis.append("gleiche Adresse wie: " + ", ".join(sorted(gleich)[:4]))
        else:
            hinweis.append("Adresse fehlt")
        art, art_hinweis = art_vorschlag(haus, " ".join(h["teile"]))
        if art_hinweis:
            hinweis.append(art_hinweis)
        if k in PRUEFHINWEISE:
            hinweis.append(PRUEFHINWEISE[k])
        if h["nicht_im"]:
            hinweis.append("nicht mitgezählt: " + "; ".join(f"{s} ({c})" for s, c in h["nicht_im"].most_common()))

        entschieden_vorschlag, entschieden_hinweis = ENTSCHIEDEN.get(k, ("", ""))
        if entschieden_hinweis:
            hinweis.append(entschieden_hinweis)
        if entschieden_vorschlag:
            vorschlag = entschieden_vorschlag
        elif KEIN_HAUS.search(haus):
            vorschlag = "keine Seite (kein Haus)"
        elif NACHBARSTADT.search(haus) and kl == "ort":
            vorschlag = "keine Seite (außerhalb?)"
            hinweis.append("Stadtname im Namen – Gebietsfilter prüfen (Schritt 2, Plan 3.16)")
        elif kl != "ort":
            vorschlag = f"keine Seite ({kl})"
        elif KETTE.search(haus):
            vorschlag = "keine Seite (Kette)"
        elif k in ABSCHNITT_9:
            vorschlag = "offen: Abschnitt 9"
            hinweis.append(ABSCHNITT_9[k])
        elif haus == BUECHEREI_NETZ:
            vorschlag = "keine Seite (Büchereinetz)"
            hinweis.append("E7 je Filiale: Quelle liefert die Filiale noch nicht; KAP1 als eigene Zeile")
        elif g.startswith("in orte, unsichtbar"):
            vorschlag = "keine Seite (Guide unsichtbar)"
            hinweis.append("ort_id ja, keine Seite")
        elif g.startswith("Guide") or g.startswith("Club"):
            vorschlag = "Guide-Seite vorhanden: Events dort zeigen, /orte leitet weiter"
        elif haus in STANDORTE:
            vorschlag = "Dachseite? (Abschnitt 9)"
        else:
            vorschlag = "neue Ortsseite"

        # Slug: Guide-Haus behält seinen gespeicherten Slug (Säle bauen darauf auf), sonst Vorschlag aus dem Namen
        haus_slug = guide_slugs.get(k) or slug_vorschlag(haus)
        kein_saal = KEIN_SAAL.get(haus)
        nicht_gelistet = [f"{t} ({c})" for t, c in h["teile"].most_common()
                          if c >= MIN_EVENTS and haus in SAALLISTE and not saal_aus_liste(haus, t)
                          and not standort_aus_liste(haus, t) and not (kein_saal and kein_saal.search(t))]
        if nicht_gelistet:
            hinweis.append("Saal? in Saalliste aufnehmen: " + "; ".join(nicht_gelistet[:4]))

        # Slug-Spalte: Vorschlag für neue Seiten, gespeicherter Slug bei Guide-Häusern, sonst leer
        if vorschlag in ("neue Ortsseite", "Dachseite? (Abschnitt 9)"):
            slug = haus_slug
        elif vorschlag.startswith("Guide-Seite"):
            slug = guide_slugs.get(k) or ""
        else:
            slug = ""
        zeilen.append(_zeile(haus, "", "haus", vorschlag, art, h, adresse, g, slug, hinweis))

        # Säle, Standorte, Filiale als eigene Entscheidungszeilen
        for (u_haus, name, typ), u in sorted(unterzeilen.items(), key=lambda x: -x[1]["alle"]):
            if u_haus != haus or u["alle"] < MIN_EVENTS:
                continue
            u_hinweis = []
            if typ == "saal":
                u_vorschlag = "Saalseite?"
                if u["alle"] >= SAAL_EIGENE_SEITE:
                    u_hinweis.append("eigene Seite empfohlen (ab 20 Events)")
                u_slug = saal_slug(haus_slug, haus, name)
                u_art = ""  # erbt vom Haus, wenn „art_korrigiert“ leer bleibt (Plan 3.6)
                u_hinweis.append("erbt Adresse, Koordinaten, Stadtteil und Art vom Haus")
            elif typ == "standort":
                u_vorschlag = "neue Ortsseite (Standort)"
                u_slug = slug_vorschlag(name)
                u_art = art
            else:
                u_vorschlag = "neue Ortsseite (Filiale)"
                u_slug = slug_vorschlag(name)
                u_art = "Bibliothek/Bildung"
                u_hinweis.append("Adresse bestätigen (Plan 3.15)")
            u_adresse = u["adresse"].most_common(1)[0][0] if u["adresse"] else ""
            zeilen.append(_zeile(name, haus, typ, u_vorschlag, u_art, u, u_adresse, "", u_slug, u_hinweis))

    # Slug-Kollisionen: mit vorhandenen `orte`-Slugs und untereinander (Plan 3.3 Punkt 7) – nur Hinweis
    gesehen: Counter = Counter(z["slug_vorschlag"] for z in zeilen if z["slug_vorschlag"])
    for z in zeilen:
        s = z["slug_vorschlag"]
        if not s or z["guide_status"]:
            continue
        if s in vergebene_slugs or gesehen[s] > 1:
            z["hinweis"] = "; ".join(x for x in [z["hinweis"], f"Slug-Kollision: {s}"] if x)

    reihenfolge = {"neue Ortsseite": 0, "Saalseite?": 0, "neue Ortsseite (Standort)": 0, "neue Ortsseite (Filiale)": 0,
                   "offen: Abschnitt 9": 1, "Dachseite? (Abschnitt 9)": 1,
                   "Guide-Seite vorhanden: Events dort zeigen, /orte leitet weiter": 2}
    # Unterzeilen bleiben direkt unter ihrem Haus
    gruppen: dict[str, list[dict]] = defaultdict(list)
    for z in zeilen:
        gruppen[z["gehoert_zu"] or z["haus"]].append(z)
    sortiert = sorted(gruppen.values(), key=lambda g: (reihenfolge.get(g[0]["vorschlag"], 3),
                                                       -g[0]["events_12m_und_kommend"], g[0]["haus"].lower()))
    return [z for g in sortiert for z in g]


def _zeile(name: str, gehoert_zu: str, typ: str, vorschlag: str, art: str, h: dict, adresse: str, guide_status: str,
           slug: str, hinweis: list[str]) -> dict:
    return {
        "haus": name,
        "zeile_typ": typ,
        "gehoert_zu": gehoert_zu,
        "vorschlag": vorschlag,
        "art_vorschlag": art,
        "events_12m_und_kommend": h["alle"],
        "events_kommend": h["kommend"],
        "saele": "; ".join(f"{s} ({n})" for s, n in h["teile"].most_common()) if typ == "haus" else "",
        "adresse": adresse,
        "plz": _plz(adresse),
        "stadtteil": h["stadtteil"].most_common(1)[0][0] if h["stadtteil"] else "",
        "guide_status": guide_status,
        "slug_vorschlag": slug,
        "schreibweisen": "; ".join(r for r, _ in h["roh"].most_common(8)),
        "quellen": "; ".join(f"{q} ({n})" for q, n in h["quelle"].most_common(3)),
        "hinweis": "; ".join(hinweis),
        "entscheidung": "",
        "name_korrigiert": "",
        "art_korrigiert": "",
        "bemerkung_auftraggeber": "",
    }


def namen_zaehlen(events: list[dict], heute: date) -> tuple[dict[str, dict], int]:
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
    return namen, ausserhalb


def guide_abgleich(orte: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    """Guide-Status je normalisiertem Namen und gespeicherter Slug sichtbarer Guide-Häuser (E1)."""
    guide: dict[str, str] = {}
    slugs: dict[str, str] = {}
    for o in orte:
        if o["typ"] == "spielstaette":
            # Schon importierte Ortsseite (Schritt 2): kein Guide; Vorschlag bleibt, Slug ist der gespeicherte
            guide[_norm(o["name"])] = f"Spielstätte: {o['slug']}"
            slugs[_norm(o["name"])] = o["slug"]
            continue
        sichtbar = o.get("aktiv") and ((o.get("qualitaets_score") or 0) >= 7
                                        or o["typ"] in ("spielplatz", "weihnachtsmarkt", "club"))
        k = _norm(o["name"])
        stand = f"Guide ({o['typ']}): {o['slug']}" if sichtbar else f"in orte, unsichtbar ({o['typ']})"
        if k not in guide or sichtbar:
            guide[k] = stand
            if sichtbar:
                slugs[k] = o["slug"]
        club = o.get("club") or {}
        if isinstance(club, dict):
            for eo in club.get("event_orte") or []:
                ek = _norm(einheitlicher_name(eo) or eo)
                guide[ek] = f"Club: {o['slug']}"
                slugs.setdefault(ek, o["slug"])
    return guide, slugs


def liste_erzeugen(ziel: Path = ZIEL) -> int:
    from database.client import get_supabase_client

    db = get_supabase_client()
    heute = date.today()
    von = (heute - timedelta(days=365)).isoformat()
    events = _seitenweise(db, "events", "ort, adresse, stadtteil, datum, datum_bis, abgelehnt, quelle_name",
                          lambda q: q.gte("datum", von))
    orte = _seitenweise(db, "orte", "name, slug, typ, aktiv, qualitaets_score, extras->club")
    logger.info("Kandidaten: %d Events seit %s, %d Orte-Zeilen", len(events), von, len(orte))

    namen, ausserhalb = namen_zaehlen(events, heute)
    guide, guide_slugs = guide_abgleich(orte)
    zeilen = zeilen_bauen(namen, guide, guide_slugs, {o["slug"] for o in orte if o.get("slug")})
    uebernommen = entscheidungen_uebernehmen(zeilen, entscheidungen_lesen(ziel))

    ziel.parent.mkdir(parents=True, exist_ok=True)
    with ziel.open("w", encoding="utf-8-sig", newline="") as f:  # mit BOM, damit Excel die Umlaute richtig zeigt
        w = csv.DictWriter(f, fieldnames=list(zeilen[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(zeilen)
    zaehler = Counter(z["vorschlag"].split(" (")[0] for z in zeilen)
    logger.info("Kandidaten: %d Zeilen geschrieben nach %s – %s; %d Entscheidungen übernommen; "
                "%d Events außerhalb übersprungen", len(zeilen), ziel, dict(zaehler), uebernommen, ausserhalb)
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
