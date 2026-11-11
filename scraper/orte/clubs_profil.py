"""
clubs_profil.py – DiesDasDüsseldorf
Club-Profile für den Guide-Hub „Clubs“ (Plan: docs/plan-clubs-2026-11-11.md, Abschnitt 2.3/2.4).

Je Club werden Quelltexte gesammelt (nur robots.txt-konform, ≥ 2 s Abstand, nie Rausgegangen):
  - Website (Startseite + bis zu 3 passende Unterseiten: Über uns, Club, Programm, FAQ …),
  - weitere Seiten aus einer Websuche (Claude-API; z. B. Resident Advisor, Stadtmagazine, Presse),
  - unsere Events an diesem Ort (Titel, Kategorie, Kurztext – letzte 180 Tage und kommende),
  - Google-Kurzbeschreibung und Bewertungstexte.
Claude ordnet ein (festes JSON-Schema). Jede Angabe braucht ein WÖRTLICHES Zitat; der Code prüft es gegen
die Quelltexte (belegt() aus bars_einordnen.py) – ohne Beleg wird die Angabe verworfen.

Danach berechnet club_score() den Club-Score (C2) aus nachvollziehbaren Daten.

Nutzung:
  python -m scraper.orte.clubs_profil [--max N] [--nur "Name"] [--neu] [--dry-run]
  python -m scraper.orte.clubs_profil --nur-score        # Score neu berechnen (ohne KI, kostenlos)
  python -m scraper.orte.clubs_profil --csv datei.csv    # Sichtprüfung
"""
import argparse
import csv
import json
import logging
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.beschreibung_quellen import _gesperrt, seite_laden, seiten_text  # noqa: E402
from scraper.orte.bars_einordnen import _norm as _text_norm  # noqa: E402
from scraper.orte.bars_einordnen import belegt  # noqa: E402
from scraper.orte.google_places import alle_zeilen  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("clubs_profil")
for laut in ("httpx", "anthropic"):
    logging.getLogger(laut).setLevel(logging.WARNING)

MODELL = "claude-sonnet-5-5"        # Einordnung: viel Text, viele Felder, Belegpflicht
MODELL_SUCHE = "claude-haiku-5-5"   # nur URLs finden
ORDNER = Path(__file__).resolve().parents[2] / "data" / "clubs"

UNTERARTEN = ["club", "kulturhaus", "partylocation"]
GENRES = ["Techno", "House", "Elektro/Experimental", "Drum & Bass", "Hip-Hop", "R&B", "Afrobeats",
          "Reggaeton/Latin", "Pop/Charts", "80er/90er/2000er", "Schlager", "Rock/Indie", "Metal/Punk",
          "Disco/Funk/Soul", "Jazz", "Mixed"]
ZUSATZ = ["Konzerte", "Comedy", "Lesungen", "Theater/Performance", "Kino", "Flohmarkt/Märkte", "Public Viewing",
          "Workshops/Kurse", "Ausstellungen", "Talks/Diskussion", "Quiz/Spiele", "Karaoke", "Brunch/Essen",
          "Private Feiern", "Sonstiges"]
PUBLIKUM = ["Studentisch", "Jung (18–25)", "Ü30", "Queer", "Underground", "Szene/Kenner", "Mainstream",
            "Schick", "Alternativ", "International"]
AUSSTATTUNG = ["Außenbereich", "Raucherbereich", "Barrierefrei", "Garderobe", "Mehrere Floors",
               "Starkes Soundsystem", "Essen"]
DRESSCODE = ["casual", "schick", "egal", "unbekannt"]

# Ein Genre zählt nur, wenn sein Zitat ein passendes Stichwort enthält (sonst belegt „tolle Musik“ jedes Genre)
GENRE_STICHWORTE = {
    # Wortgrenzen/Ausschlüsse: nicht „technology“, „Warehouse“, „Funktion“, „Swingerclub“, „Discothek“
    "Techno": r"\btechno(?!log)|\brave|\bhard ?groove|\bacid\b|minimal ?(techno|house|music)|\bindustrial\b",
    "House": r"(?<!ware)(?<!ware-)\bhouse|deep ?house|tech ?house|afro ?house",
    "Elektro/Experimental": r"\belektro|\belectro|electronic|experimental|\bambient\b|clubmusik|elektronisch",
    "Drum & Bass": r"drum ?(and|&|n|'n') ?bass|\bdnb\b|\bd&b\b|\bjungle\b|breakbeat|dubstep|bass ?music",
    "Hip-Hop": r"hip ?-?hop|\brap\b|\btrap\b|deutschrap|\burban\b",
    "R&B": r"\br ?& ?b\b|\brnb\b|r'n'b|\burban\b",
    "Afrobeats": r"afro ?beats?|amapiano|afro ?(house|vibes|party)",
    "Reggaeton/Latin": r"reggaeton|\blatin|salsa|bachata|perreo|dancehall|kizomba|cumbia",
    "Pop/Charts": r"\bpop\b|\bcharts?\b|mainstream|\bhits\b|black ?(&|and) ?white|black music|party ?hits",
    # Kein „Ü30“: das ist Publikum, keine Musikrichtung
    "80er/90er/2000er": r"\b(19)?[6789]0er|2000er|\b00er|\b[6789]0s\b|2000s|throwback|oldies|\bretro",
    "Schlager": r"schlager|\bmalle\b|ballermann|apr[èe]s|stimmungs(musik|hits|lieder)",
    "Rock/Indie": r"\brock|\bindie|alternative|britpop|grunge|\bemo\b",
    "Metal/Punk": r"metal|\bpunk|hardcore|\bgoth|dark ?wave|new wave|\bebm\b",
    "Disco/Funk/Soul": r"\bdisco\b|\bfunk\b|funky|\bsoul\b|motown|boogie",
    "Jazz": r"\bjazz|\bswing\b",
    # „von … bis“ nur mit Musikwort – sonst belegt „open from 23 bis 5 Uhr“ gemischte Musik
    "Mixed": r"\bmixed\b|querbeet|gemischt|open format"
             r"|von .{1,40} bis .{0,40}(musik|music|hits|sound|genre)"
             r"|(vielf[äa]ltig\w*|verschiedene\w*|bunt\w*) (musik|music|sound|genres?|stile?)",
}

# Auch Zusatz-Events, Publikum und Ausstattung brauchen ein passendes Wort im Zitat
ZUSATZ_STICHWORTE = {
    "Konzerte": r"konzert|concert|\blive|\bband|\bgig",
    "Comedy": r"comedy|kabarett|stand ?-?up|\bslam|impro",
    "Lesungen": r"lesung|reading|\bliest|autor|\bbuch|literatur|poetry",
    "Theater/Performance": r"theater|theatre|performance|\btanz|dance|b[üu]hne|\bshow",
    "Kino": r"\bkino|\bfilm|cinema|movie|screening",
    "Flohmarkt/Märkte": r"markt|market|basar|bazaar",
    "Public Viewing": r"public viewing|übertragung|leinwand|fu(ß|ss)ball|\bem\b|\bwm\b|\bspiele? live",
    "Workshops/Kurse": r"workshop|\bkurs|class|seminar|\blernen",
    "Ausstellungen": r"ausstellung|exhibition|galerie|gallery|vernissage|\bkunst|\bart\b",
    "Talks/Diskussion": r"\btalk|diskussion|vortrag|gespr[äa]ch|podium|lecture",
    "Quiz/Spiele": r"quiz|kwizz|\bspiel|\bgame|bingo",
    "Karaoke": r"karaoke|sing ?-?along|mitsing",
    "Brunch/Essen": r"brunch|\bessen|food|k[üu]che|fr[üu]hst[üu]ck|kaffee|kuchen|dinner|caf[ée]|\bspeise",
    "Private Feiern": r"privat|private|feier|geburtstag|firmen|mieten|buchbar|anmieten",
    "Sonstiges": r".",
}
PUBLIKUM_STICHWORTE = {
    "Studentisch": r"student|\buni\b|studi",
    "Jung (18–25)": r"\bjung|young|\bteen|ab 18\b|18 ?-? ?25|\bu ?25",
    "Ü30": r"[üu]e? ?30|30 ?\+|über 30|ab 30|erwachsen",
    "Queer": r"queer|\bgay|lgbt|lesb|schwul|\bdrag",
    "Underground": r"underground|subkultur|independent|\bdiy\b",
    "Szene/Kenner": r"\bszene|kenner|\bkult|institution|legend[äa]r|kuratiert|resident",
    "Mainstream": r"mainstream|\bcharts|kommerz|gro(ß|ss)raum|massen",
    "Schick": r"schick|\bedel|elegant|\bvip\b|\bchic|upscale|fancy|dresscode",
    "Alternativ": r"alternativ|\bindie|\bpunk|\bbunt|links",
    "International": r"international|english|expat|touris|aus aller welt|multikult",
}
AUSSTATTUNG_STICHWORTE = {
    "Außenbereich": r"drau(ß|ss)en|terrasse|\bgarten|au(ß|ss)en|outdoor|open ?air|biergarten|innenhof|rooftop|\bdach",
    "Raucherbereich": r"raucher|rauchen|geraucht|smok",
    "Barrierefrei": r"barrierefrei|rollstuhl|wheelchair|accessib",
    "Garderobe": r"garderobe|cloakroom|wardrobe",
    "Mehrere Floors": r"floors|\bfloor|etage|stockwerk|r[äa]ume|areas?\b|s[äa]le",
    "Starkes Soundsystem": r"\bsound|anlage|funktion ?one|speaker|\bboxen|\bbass",
    "Essen": r"\bessen|\bfood|k[üu]che|speise|snack|pizza|burger|kitchen|men[üu]",
}

# Wörter, die für den Abgleich „Anzeigetext steckt im Zitat“ nichts aussagen
_FUELLWOERTER = {"und", "oder", "mit", "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "jeden",
                 "jede", "jeder", "auch", "dazu", "meist", "etwa", "ca", "teils", "oft", "laut", "bei", "für", "fuer",
                 "von", "bis", "ab", "im", "in", "am", "an", "zu", "zum", "zur", "the", "and", "with", "for"}

SCHEMA = {
    "type": "object",
    "properties": {
        "passt": {"type": "boolean"},
        "passt_grund": {"type": "string"},
        "unterart": {"type": "string", "enum": UNTERARTEN},
        "genres": {"type": "array", "items": {"type": "object", "properties": {
            "wert": {"type": "string", "enum": GENRES},
            "anteil": {"type": "string", "enum": ["haupt", "neben"]},
            "zitat": {"type": "string"}},
            "required": ["wert", "anteil", "zitat"], "additionalProperties": False}},
        "formate": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"}, "rhythmus": {"type": "string"}, "musik": {"type": "string"},
            "zitat": {"type": "string"}},
            "required": ["name", "rhythmus", "musik", "zitat"], "additionalProperties": False}},
        "zusatz_events": {"type": "array", "items": {"type": "object", "properties": {
            "art": {"type": "string", "enum": ZUSATZ}, "beispiel": {"type": "string"}, "zitat": {"type": "string"}},
            "required": ["art", "beispiel", "zitat"], "additionalProperties": False}},
        "fakten": {"type": "object", "properties": {
            k: {"type": "object", "properties": {"text": {"type": "string"}, "zitat": {"type": "string"}},
                "required": ["text", "zitat"], "additionalProperties": False}
            for k in ("oeffnung", "eintritt", "tuer", "alter", "kapazitaet", "floors")},
            "required": ["oeffnung", "eintritt", "tuer", "alter", "kapazitaet", "floors"], "additionalProperties": False},
        "eintritt_min_euro": {"type": "string"},
        "eintritt_max_euro": {"type": "string"},
        "dresscode": {"type": "string", "enum": DRESSCODE},
        "dresscode_zitat": {"type": "string"},
        "publikum": {"type": "array", "items": {"type": "object", "properties": {
            "wert": {"type": "string", "enum": PUBLIKUM}, "zitat": {"type": "string"}},
            "required": ["wert", "zitat"], "additionalProperties": False}},
        "ausstattung": {"type": "array", "items": {"type": "object", "properties": {
            "wert": {"type": "string", "enum": AUSSTATTUNG}, "zitat": {"type": "string"}},
            "required": ["wert", "zitat"], "additionalProperties": False}},
        "instagram": {"type": "string"},
        "resident_advisor": {"type": "string"},
        "beschreibung": {"type": "string"},
        "highlight": {"type": "string"},
    },
    "required": ["passt", "passt_grund", "unterart", "genres", "formate", "zusatz_events", "fakten",
                 "eintritt_min_euro", "eintritt_max_euro", "dresscode", "dresscode_zitat", "publikum",
                 "ausstattung", "instagram", "resident_advisor", "beschreibung", "highlight"],
    "additionalProperties": False,
}

SYSTEM = """Du erstellst Club-Profile für den Düsseldorfer Stadtguide dies.das.düsseldorf.
Du bekommst zu einem Ort mehrere Quellen: Website-Seiten, Fundstellen aus einer Websuche, Events aus unserem
Kalender an diesem Ort sowie Google-Kurzbeschreibung und Bewertungen.

Grundregeln:
- Stütze dich NUR auf die Quellen. Erfinde nichts, schließe nichts aus dem Namen.
- Jede Angabe braucht ein WÖRTLICHES Zitat (5–25 Wörter, exakt wie in der Quelle, nicht umformuliert,
  nicht aus mehreren Stellen zusammengesetzt). Ohne passende Textstelle: Angabe weglassen bzw. leer lassen.
  Das Zitat muss das Angegebene selbst enthalten: bei Reihen den Namen der Reihe, bei Preisen, Zeiten und
  Kapazität die Zahlen, bei Musik das Genre-Wort.
- „passt“: true, wenn hier regelmäßig gefeiert/getanzt wird: Club/Disco, Konzert- oder Kulturhaus mit
  regelmäßigen Partys oder Partylokal. false bei Erotik-, Swinger- oder Saunaclubs, Bordellen, reinen
  Restaurants/Cafés ohne Partys, reinen Konzertsälen, geschlossenen Orten oder Partyreihen ohne festen Ort.
- „unterart“: club (Club/Disco), kulturhaus (Konzert-/Kulturzentrum mit Partys), partylocation (Partylokal,
  Kneipe/Bar/Restaurant mit regelmäßigen Partys, Schlager-/Après-Ski-Lokal).
- „genres“: Musikrichtungen, die hier gespielt/aufgelegt werden. „haupt“ = prägt den Ort (regelmäßig,
  mehrere Belege oder ausdrücklich so beschrieben), „neben“ = gelegentlich. Event-Titel aus unserem Kalender
  sind gute Belege („Techno Night …“). Mixed nur, wenn die Quelle ausdrücklich gemischte Musik nennt.
- „formate“: wiederkehrende Reihen mit Namen – vor allem Partyreihen (z. B. „Ü30-Party jeden 1. Samstag“),
  auch feste Konzert- oder Veranstaltungsreihen. Rhythmus kurz („monatlich“, „jeden Freitag“, „unregelmäßig“),
  Musik/Inhalt kurz. Keine Einzelevents.
- „zusatz_events“: was hier außer Partys passiert (Konzerte, Comedy, Lesungen …) mit einem Beispiel.
- „fakten“: oeffnung (Öffnungstage/-zeiten), eintritt (typische Preise), tuer (Türpolitik), alter
  (Mindestalter/Zielalter), kapazitaet (Personen), floors (Anzahl Floors/Räume). Text kurz und sachlich
  („meist 10–15 €“, „Fr und Sa ab 23 Uhr“, „ab 18“) – auch wenn das Zitat aus einer Beschwerde stammt. Sonst leer.
- „eintritt_min_euro“/„eintritt_max_euro“: Zahlen als Text („10“), nur wenn ein Zitat sie nennt, sonst leer.
- „dresscode“: casual, schick, egal oder unbekannt (Standard). Nicht raten.
- „instagram“/„resident_advisor“: URL nur, wenn sie in den Quellen steht, sonst leer.
- „beschreibung“: auf Deutsch, Du-Form, locker, keine Werbesprache, kein „Geheimtipp“, keine Sterne.
  Gegliedert: 2–4 kurze Absätze (Leerzeile dazwischen), gerne eine Liste mit „• “ für Partyreihen oder
  Musik, sparsam Emojis. 400–1200 Zeichen je nach Quellenlage. Keine Öffnungszeiten, Preise, Adresse.
  Nur Dinge aus den Quellen, eigene Worte (keine langen wörtlichen Passagen).
- „highlight“: ein Satz (max. 120 Zeichen), was den Ort ausmacht."""


# ── Quellen sammeln ─────────────────────────────────────────────────────────────

UNTERSEITE = re.compile(r"about|ueber|über|club|location|info|faq|tuer|tür|dresscode|programm|events?|kalender|"
                        r"party|partys|reihen|floors?|geschichte|history|story", re.IGNORECASE)
MAX_QUELLE = 6000       # Zeichen je Quelle
MAX_UNTERSEITEN = 3
MAX_SUCHSEITEN = 3


def _key(text: str) -> str:
    t = (text or "").lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.sub(r"[^a-z0-9]", "", t)


_FUELL_NAME = re.compile(r"d[üu]sseldorf|\bclub\b|\bklub\b|\bbar\b|\be\.? ?v\.?(?![a-zäöü])|eventlocation|event location|"
                         r"nachtclub|discothek|diskothek|\bdisco\b|\bthe\b|\bder\b|\bdie\b|\bdas\b|\bin\b|zentrum f[üu]r|"
                         r"[-–|/&]", re.IGNORECASE)


def ort_schluessel(name: str) -> str:
    """Kern des Clubnamens zum Abgleich mit events.ort („Rudas Studios Club“ → „rudasstudios“)."""
    kern = _key(_FUELL_NAME.sub(" ", name or ""))
    # Zu kurz („Kö“ aus „Kö Club - Düsseldorf“): „Club“ behalten, nur Stadt und Trennzeichen weg
    return kern if len(kern) >= 4 else _key(re.sub(r"d[üu]sseldorf|[-–|/&]", " ", name or "", flags=re.IGNORECASE))


# Bekannte Kurzformen im Eventkalender: Teil des Namens (Schlüssel) → Wortfolgen am Anfang der Ortsangabe
ALIASE = {
    "zentrumfueraktionkulturundkommunikation": ["zakk"],
    "zakk": ["zakk"],
    "kulturschlachthof": ["kulturschlachthof", "r25"],
    "schleusezwei": ["schleuse zwei"],
    "giselle": ["giselle"],
}


def _phrase(text: str) -> str:
    """Kernname als Wortfolge („Rudas Studios Club“ → „rudas studios“) für Ganzwort-Vergleiche."""
    return " ".join(_woerter(_FUELL_NAME.sub(" ", text or "")))


# Ortsangaben im Kalender, die nichts über den Club sagen
_ALLGEMEIN = {"duesseldorf", "altstadt", "neuss", "ratingen", "kultur", "online", "innenstadt", "stadtmitte"}


def event_orte(name: str, alle_orte: set[str]) -> list[str]:
    """Schreibweisen dieses Orts im Eventkalender (für „Nächste Events hier“)."""
    eigener, phrase = ort_schluessel(name), _phrase(name)
    # Kurzformen: Alias-Schlüssel steckt im Namen („…kommunikation (zakk)“ → „zakk“)
    aliase = [a for teil, liste in ALIASE.items() if teil in _key(name) for a in liste]
    namen = [x for x in [phrase, *aliase] if x]
    treffer = []
    for ort in alle_orte:
        # Beide Seiten gleich normalisieren („SUB Düsseldorf“ → „sub“, „Düsseldorf“ → leer)
        k = ort_schluessel(ort)
        if not k or k in _ALLGEMEIN:
            continue
        text = f" {' '.join(_woerter(ort))} "
        # „zakk – nicht im zakk“ gehört nicht dazu, „Pitcher, nicht im Freien“ schon
        if any(re.search(rf" nicht im( \w+)? {re.escape(n)} ", text) for n in namen):
            continue
        ort_phrase = _phrase(ort)
        # Gleich; sonst Teiltreffer nur ab 6 Zeichen und nur als ganze Wörter („Stone im Ratinger Hof“) –
        # sonst träfe „graf“ „Grafenberg“ und „gate“ „Southgate“
        if eigener and (k == eigener
                        or (len(eigener) >= 6 and f" {phrase} " in text)
                        or (len(k) >= 6 and f" {ort_phrase} " in f" {phrase} ")):
            treffer.append(ort)
        # Aliase nur am Anfang („zakk – Halle“, nicht „HHU …, am Finaltag im zakk“)
        elif any(text.startswith(f" {a} ") for a in aliase):
            treffer.append(ort)
    return sorted(treffer)


def kalender_laden(db) -> list[dict]:
    """Events der letzten 180 Tage und alle kommenden (nur Felder für Profil und Score)."""
    ab = (date.today() - timedelta(days=180)).isoformat()
    return alle_zeilen(db, "events", "titel, ort, datum, kategorie, quelle_name, beschreibung",
                       lambda q: q.gte("datum", ab))


def _mit_links(text: str, html: str, url: str) -> str:
    """Seitentext (gekürzt) plus Profil-Links aus dem HTML – damit link_pruefen() sie in der Quelle findet."""
    links = profil_links(html, url)
    return text[:MAX_QUELLE] + ("\nLinks: " + " ".join(links) if links else "")


def website_quellen(start: str | None) -> list[tuple[str, str]]:
    """Startseite + passende Unterseiten derselben Domain als (url, text)."""
    from bs4 import BeautifulSoup

    if not start or _gesperrt(start):
        return []
    html = seite_laden(start)
    if not html:
        return []
    quellen = [(start, _mit_links(seiten_text(html), html, start))]
    host = urlparse(start).netloc
    kandidaten = []
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        url = urljoin(start, a["href"]).split("#")[0]
        text = f"{a.get_text(' ', strip=True)} {urlparse(url).path}"
        if urlparse(url).netloc == host and url.rstrip("/") != start.rstrip("/") and UNTERSEITE.search(text):
            if url not in kandidaten and not re.search(r"\.(pdf|jpg|png|zip)$|impressum|datenschutz|agb|login|warenkorb|cart", url, re.I):
                kandidaten.append(url)
    for url in kandidaten[:MAX_UNTERSEITEN]:
        teil = seite_laden(url)
        if teil:
            quellen.append((url, _mit_links(seiten_text(teil), teil, url)))
    return quellen


def such_urls(client, name: str, stadt: str) -> list[str]:
    """Websuche nach Profil-Seiten (Resident Advisor, Stadtmagazine, Presse) – ohne gesperrte Seiten."""
    anfrage = (f"Finde Seiten über den Club/Partyort „{name}“ in {stadt}: Musikrichtungen, Partyreihen, Türpolitik. "
               f"Gut sind die Resident-Advisor-Seite des Clubs, Stadtmagazine und Presseartikel. Höchstens zwei Suchen.")
    try:
        antwort = client.messages.create(
            model=MODELL_SUCHE, max_tokens=1024,
            messages=[{"role": "user", "content": anfrage}],
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2,
                    "blocked_domains": ["rausgegangen.de", "duesseldorf.de", "instagram.com", "facebook.com",
                                        "tiktok.com", "youtube.com"],
                    "user_location": {"type": "approximate", "city": "Düsseldorf", "country": "DE",
                                      "timezone": "Europe/Berlin"}}],
        )
    except Exception as e:
        logger.warning("Websuche für '%s' fehlgeschlagen: %s", name, e)
        return []
    urls = []
    for block in antwort.content:
        if getattr(block, "type", "") == "web_search_tool_result" and isinstance(block.content, list):
            for r in block.content:
                url = getattr(r, "url", None)
                if url and not _gesperrt(url) and url not in urls:
                    urls.append(url)
    return urls


def such_quellen(client, ort: dict, website: str | None) -> list[tuple[str, str]]:
    """Seiten aus der Websuche, die den Club wirklich nennen (ohne die eigene Website)."""
    stadt = ort.get("stadtteil") if ort.get("stadtteil") in ("Neuss", "Ratingen") else "Düsseldorf"
    eigene = urlparse(website).netloc.removeprefix("www.") if website else None
    kern = ort_schluessel(ort["name"])
    quellen = []
    for url in such_urls(client, ort["name"], stadt):
        if eigene and urlparse(url).netloc.removeprefix("www.") == eigene:
            continue
        html = seite_laden(url)
        if not html:
            continue
        text = seiten_text(html)
        if kern and kern in _key(text):
            quellen.append((url, _mit_links(text, html, url)))
        if len(quellen) >= MAX_SUCHSEITEN:
            break
    return quellen


def kalender_quelle(events: list[dict]) -> str:
    """Unsere Events an diesem Ort als Quelltext (eine Zeile je Event)."""
    zeilen = []
    for e in sorted(events, key=lambda e: e["datum"]):
        kurz = re.sub(r"\s+", " ", (e.get("beschreibung") or ""))[:160]
        zeilen.append(f"{e['datum']} | {e['titel']} | {e['kategorie']} | {kurz}")
    return "\n".join(zeilen[-60:])


def google_quelle(ort: dict) -> str:
    ex = ort.get("extras") or {}
    teile = [ex.get("google_zusammenfassung") or ""]
    teile += [b.get("text") or "" for b in ex.get("google_bewertungen") or []]
    return "\n".join(t for t in teile if t)


# ── KI und Belegprüfung ─────────────────────────────────────────────────────────

def ki_anfrage(client, ort: dict, quellen: list[tuple[str, str]]) -> dict:
    teile = [f"Name: {ort['name']}\nAdresse: {ort.get('adresse')}\nGoogle-Typ: {(ort.get('extras') or {}).get('google_primaertyp')}"]
    for i, (herkunft, text) in enumerate(quellen, 1):
        teile.append(f"=== Quelle {i}: {herkunft} ===\n{text}")
    antwort = client.messages.create(
        model=MODELL, max_tokens=6000, system=SYSTEM,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": "\n\n".join(teile)}],
    )
    if antwort.stop_reason == "refusal":
        raise RuntimeError("Anfrage abgelehnt (refusal)")
    return json.loads(next(b.text for b in antwort.content if b.type == "text"))


def _herkunft(zitat: str, quellen: list[tuple[str, str]]) -> str | None:
    for herkunft, text in quellen:
        if belegt(zitat, text):
            return herkunft
    return None


# Umfeld des Zitats in derselben Quelle: Reihennamen stehen oft als Überschrift direkt über dem zitierten Satz
KONTEXT_ZEICHEN = 250


def zitat_umfeld(zitat: str, quellen: list[tuple[str, str]], radius: int = KONTEXT_ZEICHEN) -> str:
    """Zitat plus bis zu `radius` Zeichen davor und danach aus der Quelle, in der es steht (normalisiert)."""
    z = _text_norm(zitat or "")
    if not z:
        return ""
    for _, text in quellen:
        t = _text_norm(text)
        i = t.find(z)
        if i >= 0:
            return t[max(0, i - radius): i + len(z) + radius]
    return z

def _zahl(text: str) -> float | None:
    try:
        wert = float((text or "").replace(",", ".").strip())
        return wert if 0 <= wert <= 200 else None
    except ValueError:
        return None


def _woerter(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", _key_text(text))


def _key_text(text: str) -> str:
    return (text or "").lower().translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))


def anzeige_belegt(text: str, zitat: str) -> bool:
    """
    Passt der angezeigte Text zum (schon geprüften) Zitat? Alle Zahlen des Textes müssen im Zitat stehen;
    ohne Zahlen muss mindestens ein Wort (Stamm aus 4 Buchstaben) im Zitat vorkommen.
    So kann die KI nicht „meist 5 €“ mit dem Zitat „Die Tür ist streng.“ belegen.
    """
    zahlen_text = re.findall(r"\d+", text or "")
    zahlen_zitat = set(re.findall(r"\d+", zitat or ""))
    if zahlen_text:
        return all(z in zahlen_zitat for z in zahlen_text)
    staemme_zitat = {w[:4] for w in _woerter(zitat) if len(w) >= 4}
    woerter = [w for w in _woerter(text) if len(w) >= 4 and w not in _FUELLWOERTER]
    return any(w[:4] in staemme_zitat for w in woerter)


def name_im_zitat(name: str, zitat: str) -> bool:
    """Steht der Name einer Reihe im Zitat? (mind. die Hälfte seiner Wörter, ganze Wörter)"""
    woerter = [w for w in _woerter(name) if w not in _FUELLWOERTER]
    if not woerter:
        return False
    im_zitat = set(_woerter(zitat))
    return sum(w in im_zitat for w in woerter) * 2 >= len(woerter)


def profil_links(html: str, basis: str) -> list[str]:
    """Instagram- und Resident-Advisor-Links aus dem HTML (stehen meist nur im href, nicht im Text)."""
    from bs4 import BeautifulSoup

    links = []
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        url = urljoin(basis, a["href"])
        if re.search(r"(instagram\.com|ra\.co/clubs)/", url) and url not in links:
            links.append(url)
    return links[:10]


LINK_MUSTER = {
    "instagram": re.compile(r"https://(www\.)?instagram\.com/[A-Za-z0-9_.]{1,30}/?"),
    "resident_advisor": re.compile(r"https://(www\.)?ra\.co/clubs/\d{1,8}/?"),
}


def link_pruefen(url: str, art: str, gesamt: str) -> str | None:
    """Profil-Link nur exakt (ohne Query/Fragment) und nur, wenn er wörtlich in einer Quelle steht."""
    url = (url or "").strip()
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    teile = urlparse(url)
    if teile.query or teile.fragment or not LINK_MUSTER[art].fullmatch(url):
        return None
    kern = re.sub(r"^https://(www\.)?", "", url).rstrip("/").lower()
    return url if re.search(re.escape(kern) + r"(?![a-z0-9_.])", (gesamt or "").lower()) else None


def pruefen(ki: dict, quellen: list[tuple[str, str]]) -> tuple[dict, list[str]]:
    """
    Nur belegte Angaben übernehmen → (club-Profil, verworfene Angaben).
    Belegt heißt: Zitat steht wörtlich in einer Quelle UND der angezeigte Wert passt zum Zitat
    (Genre/Zusatz/Publikum/Ausstattung: Stichwort; Fakten/Beispiele: Zahlen bzw. Wortstamm; Reihen: Name).
    „passt“ ist nur ein Vorschlag – sichtbar wird ein Ort erst nach der Freigabe (club_freigegeben).
    """
    verworfen: list[str] = []
    gesamt = "\n".join(t for _, t in quellen)

    def ok(zitat: str, was: str) -> str | None:
        h = _herkunft(zitat, quellen)
        if not h:
            verworfen.append(f"{was} (Zitat nicht in den Quellen)")
        return h

    def stichwort(muster: str, zitat: str, was: str) -> bool:
        if re.search(muster, _text_norm(zitat)):
            return True
        verworfen.append(f"{was} (Zitat passt nicht)")
        return False

    genres = []
    for g in ki.get("genres") or []:
        if g.get("wert") not in GENRES or any(x["wert"] == g["wert"] for x in genres):
            continue
        if not re.search(GENRE_STICHWORTE[g["wert"]], _text_norm(g.get("zitat"))):
            verworfen.append(f"Genre {g['wert']} (Zitat nennt die Musik nicht)")
            continue
        if (h := ok(g.get("zitat"), f"Genre {g['wert']}")):
            genres.append({"wert": g["wert"], "anteil": g.get("anteil", "neben"), "zitat": g["zitat"].strip(), "quelle": h})
    # „haupt“ zuerst, Reihenfolge der festen Liste
    genres.sort(key=lambda g: (g["anteil"] != "haupt", GENRES.index(g["wert"])))

    formate = []
    for f in ki.get("formate") or []:
        name, zitat = (f.get("name") or "").strip(), f.get("zitat") or ""
        if not name or not (h := ok(zitat, f"Format {name}")):
            continue
        # Name im Zitat oder direkt daneben (Überschrift der Reihe über dem zitierten Satz)
        umfeld = zitat_umfeld(zitat, quellen)
        if not name_im_zitat(name, umfeld):
            verworfen.append(f"Format {name} (Name steht nicht beim Zitat)")
            continue
        # Rhythmus/Musik nur, wenn sie zum Zitat passen – sonst leer statt erfunden
        rhythmus, musik = (f.get("rhythmus") or "").strip(), (f.get("musik") or "").strip()
        formate.append({"name": name[:80], "rhythmus": rhythmus[:60] if anzeige_belegt(rhythmus, umfeld) else "",
                        "musik": musik[:80] if anzeige_belegt(musik, umfeld) else "", "zitat": zitat.strip(), "quelle": h})

    zusatz = []
    for z in ki.get("zusatz_events") or []:
        art, zitat = z.get("art"), z.get("zitat") or ""
        if art not in ZUSATZ or any(x["art"] == art for x in zusatz):
            continue
        if (h := ok(zitat, f"Zusatz {art}")) and stichwort(ZUSATZ_STICHWORTE[art], zitat, f"Zusatz {art}"):
            beispiel = (z.get("beispiel") or "").strip()
            zusatz.append({"art": art, "beispiel": beispiel[:100] if anzeige_belegt(beispiel, zitat_umfeld(zitat, quellen)) else "",
                           "zitat": zitat.strip(), "quelle": h})

    fakten = {}
    for k, v in (ki.get("fakten") or {}).items():
        text, zitat = (v.get("text") or "").strip(), v.get("zitat") or ""
        if not text or not (h := ok(zitat, f"Fakt {k}")):
            continue
        if not anzeige_belegt(text, zitat_umfeld(zitat, quellen)):
            verworfen.append(f"Fakt {k} „{text[:40]}“ (Text passt nicht zum Zitat)")
            continue
        fakten[k] = {"text": text[:120], "zitat": zitat.strip(), "quelle": h}

    eintritt = {}
    if "eintritt" in fakten:
        zitat = _text_norm(fakten["eintritt"]["zitat"])
        for feld in ("min", "max"):
            wert = _zahl(ki.get(f"eintritt_{feld}_euro"))
            # Die Zahl muss im Zitat stehen
            if wert is not None and re.search(rf"\b{int(wert)}\b", zitat):
                eintritt[feld] = wert

    dresscode = ki.get("dresscode") if ki.get("dresscode") in DRESSCODE else "unbekannt"
    if dresscode != "unbekannt" and not _herkunft(ki.get("dresscode_zitat"), quellen):
        verworfen.append(f"Dresscode {dresscode} (kein Beleg)")
        dresscode = "unbekannt"

    def liste(feld: str, stichworte: dict[str, str]) -> list[str]:
        werte = []
        for x in ki.get(feld) or []:
            wert, zitat = x.get("wert"), x.get("zitat") or ""
            if wert in stichworte and wert not in werte and ok(zitat, f"{feld} {wert}") \
                    and stichwort(stichworte[wert], zitat, f"{feld} {wert}"):
                werte.append(wert)
        return werte

    profil = {
        "passt": bool(ki.get("passt")),
        "passt_grund": (ki.get("passt_grund") or "")[:200],
        "unterart": ki.get("unterart") if ki.get("unterart") in UNTERARTEN else None,
        "genres": genres,
        "formate": formate[:8],
        "zusatz_events": zusatz,
        "fakten": fakten,
        "eintritt": eintritt or None,
        "dresscode": dresscode,
        "publikum": liste("publikum", PUBLIKUM_STICHWORTE),
        "ausstattung": liste("ausstattung", AUSSTATTUNG_STICHWORTE),
        "instagram": link_pruefen(ki.get("instagram"), "instagram", gesamt),
        "resident_advisor": link_pruefen(ki.get("resident_advisor"), "resident_advisor", gesamt),
    }
    return profil, verworfen


# ── Club-Score (C2) ─────────────────────────────────────────────────────────────

def _stufe(n: int, grenzen: list[tuple[int, float]]) -> float:
    wert = 0.0
    for ab, punkte in grenzen:
        if n >= ab:
            wert = punkte
    return wert


def club_score(ort: dict, profil: dict, events: list[dict], heute: date | None = None) -> dict:
    """
    Teilwerte 0–10 und Gesamtwert 1–10 (gewichtet: Programm 35 %, Profil 25 %, Beliebtheit 25 %, Szene 15 %).
    events: unsere Events an diesem Ort (letzte 180 Tage + kommende).
    """
    heute = heute or date.today()
    von, bis = (heute - timedelta(days=90)).isoformat(), (heute + timedelta(days=60)).isoformat()
    fenster = [e for e in events if von <= e["datum"] <= bis]
    party = [e for e in fenster if e.get("kategorie") in ("nightlife", "musik")]
    kalender = _stufe(len(party), [(1, 3), (3, 5), (6, 7), (11, 8.5), (20, 10)])
    # Unser Kalender kennt viele Clubnächte nicht – deshalb zählt auch das belegte Profil:
    # feste Öffnungstage, wiederkehrende Reihen, weiteres Programm
    belegt_programm = (3 if "oeffnung" in (profil.get("fakten") or {}) else 0)         + 1.5 * min(3, len(profil.get("formate") or [])) + (1 if profil.get("zusatz_events") else 0)
    programm = max(kalender, belegt_programm)
    if kalender and belegt_programm:
        programm = min(10.0, programm + 1)

    szene = 0.0
    if profil.get("resident_advisor") or any(e.get("quelle_name") == "Resident Advisor" for e in events):
        szene += 4
    if set(profil.get("publikum") or []) & {"Underground", "Szene/Kenner", "Queer", "Alternativ"}:
        szene += 2
    if len(profil.get("formate") or []) >= 3:
        szene += 2
    if profil.get("unterart") == "kulturhaus" or len(profil.get("zusatz_events") or []) >= 2:
        szene += 2
    if (ort.get("google_bewertungen_anzahl") or 0) >= 300:
        szene += 1
    szene = min(10.0, szene)

    haupt = [g for g in profil.get("genres") or [] if g["anteil"] == "haupt"]
    profilwert = (4 if haupt else 2 if profil.get("genres") else 0) + (2 if profil.get("formate") else 0) \
        + (2 if profil.get("zusatz_events") else 0) + min(2, len(profil.get("fakten") or {}) * 0.5)

    r = float(ort.get("google_rating") or 0)
    n = int(ort.get("google_bewertungen_anzahl") or 0)
    gewichtet = (n / (n + 100)) * r + (100 / (n + 100)) * 3.8 if n else 3.8
    beliebtheit = max(0.0, min(10.0, (gewichtet - 3.0) / (4.6 - 3.0) * 8)) + _stufe(n, [(100, 1), (500, 2)])
    beliebtheit = min(10.0, beliebtheit)

    # Szene schwächer gewichtet: sie bevorzugt Underground/Resident Advisor, der Guide zeigt aber auch
    # gute Mainstream-Clubs und Partylocations (Entscheidung C1)
    gesamt = 0.35 * programm + 0.15 * szene + 0.25 * profilwert + 0.25 * beliebtheit
    return {
        "gesamt": max(1, min(10, round(gesamt))),
        "programm": round(programm, 1), "szene": round(szene, 1),
        "profil": round(profilwert, 1), "beliebtheit": round(beliebtheit, 1),
        "events_90_60": len(party),
        "datum": heute.isoformat(),
    }


# ── Lauf ────────────────────────────────────────────────────────────────────────

# Nach Sichtprüfung: Orte, die trotz KI-Einordnung nicht in den Hub gehören (Name klein → Grund)
NICHT_IM_HUB = {
    "schamlos-party": "Partyreihe (mehrmals im Jahr im zakk), kein eigener Ort",
}


def manuell_korrigieren(o: dict, profil: dict) -> None:
    grund = NICHT_IM_HUB.get((o.get("name") or "").strip().lower())
    if grund:
        profil["passt"] = False
        profil["passt_grund"] = f"Manuell: {grund}"


def club_orte(db) -> list[dict]:
    spalten = ("id, name, typ, adresse, stadtteil, webseite, beschreibung, highlight, google_rating, "
               "google_bewertungen_anzahl, qualitaets_score, aktiv, extras")
    # Filter in der Abfrage – sonst kämen die extras (mit Bewertungstexten) aller ~2.000 Orte mit
    return [o for o in alle_zeilen(db, "orte", spalten, lambda q: q.or_("typ.eq.club,extras->>auch_club.eq.true"))
            if o["typ"] == "club" or (o.get("extras") or {}).get("auch_club")]


def _events_fuer(ort: dict, kalender: list[dict], alle_orte: set[str]) -> tuple[list[str], list[dict]]:
    namen = event_orte(ort["name"], alle_orte)
    return namen, [e for e in kalender if e.get("ort") in namen]


def extras_mergen(db, ort_id: str, felder: dict, spalten: dict | None = None, entfernen: bool = False) -> None:
    """
    Nur die genannten extras-Schlüssel ändern: extras direkt vorher frisch lesen und zusammenführen, damit ein
    paralleler Lauf (z. B. bars_einordnen) keine fremden Felder verliert. entfernen=True löscht die Schlüssel.
    """
    aktuell = (db.table("orte").select("extras").eq("id", ort_id).execute().data or [{}])[0].get("extras") or {}
    if entfernen:
        neu = {k: v for k, v in aktuell.items() if k not in felder}
    else:
        neu = {**aktuell, **felder}
    db.table("orte").update({"extras": neu, **(spalten or {})}).eq("id", ort_id).execute()


def speichern(db, ort: dict, extras_neu: dict, spalten: dict) -> None:
    """Club-Felder speichern – nur die Schlüssel, die sich gegenüber dem gelesenen Stand geändert haben."""
    alt = ort.get("extras") or {}
    geaendert = {k: v for k, v in extras_neu.items() if alt.get(k) != v}
    extras_mergen(db, ort["id"], geaendert, spalten)


def profile_erstellen(max_anzahl: int, nur: str | None, neu: bool, dry_run: bool) -> None:
    import anthropic

    from database.client import get_supabase_client

    db = get_supabase_client()
    client = anthropic.Anthropic()
    orte = club_orte(db)
    if nur:
        orte = [o for o in orte if nur.lower() in o["name"].lower()]
    offen = [o for o in orte if neu or nur or not (o.get("extras") or {}).get("club")][:max_anzahl]
    kalender = kalender_laden(db)
    alle_orte = {e["ort"] for e in kalender if e.get("ort")}
    logger.info("%d Club-Orte, %d zu profilieren%s", len(orte), len(offen), " [Dry-Run]" if dry_run else "")
    ORDNER.mkdir(parents=True, exist_ok=True)

    for i, o in enumerate(offen, 1):
        try:
            logger.info("[%d/%d] %s", i, len(offen), o["name"])
            namen, events = _events_fuer(o, kalender, alle_orte)
            quellen = website_quellen(o.get("webseite"))
            quellen += such_quellen(client, o, o.get("webseite"))
            if events:
                quellen.append(("Eventkalender dies.das (" + ", ".join(namen[:3]) + ")", kalender_quelle(events)))
            if google_quelle(o):
                quellen.append(("Google (Kurzbeschreibung und Bewertungen)", google_quelle(o)))
            if not quellen:
                logger.warning("  keine Quellen – übersprungen")
                continue
            ki = ki_anfrage(client, o, quellen)
            profil, verworfen = pruefen(ki, quellen)
            profil["event_orte"] = namen
            manuell_korrigieren(o, profil)
            profil["quellen"] = [h for h, _ in quellen]
            profil["verworfen"] = verworfen
            profil["modell"] = MODELL
            profil["datum"] = datetime.now(timezone.utc).date().isoformat()
            score = club_score(o, profil, events)
            # Rohdaten für spätere Prüfung (gitignored)
            (ORDNER / f"{o['id']}.json").write_text(json.dumps(
                {"name": o["name"], "quellen": quellen, "ki": ki, "profil": profil, "score": score},
                ensure_ascii=False, indent=1), encoding="utf-8")
            logger.info("  passt=%s %s | Genres %s | %d Formate | %d Zusatz | Score %s | verworfen %d",
                        profil["passt"], profil["unterart"], [g["wert"] for g in profil["genres"]],
                        len(profil["formate"]), len(profil["zusatz_events"]), score["gesamt"], len(verworfen))
            if dry_run:
                continue
            profil_speichern(db, o, ki, profil, score)
        except Exception as e:
            logger.error("Fehler bei '%s': %s", o["name"], e)


def texte_pruefen(ki: dict) -> tuple[str | None, str | None]:
    """Beschreibung (200–1600 Zeichen) und Highlight (10–160) – sonst None."""
    beschreibung = (ki.get("beschreibung") or "").strip()
    highlight = (ki.get("highlight") or "").strip()
    return (beschreibung if 200 <= len(beschreibung) <= 1600 else None,
            highlight if 10 <= len(highlight) <= 160 else None)


def profil_speichern(db, o: dict, ki: dict, profil: dict, score: dict) -> None:
    """Profil, Score und Texte speichern. Eigene Club-Zeilen: Spalten; auch_club: extras.club_* (Haupt-Hub-Texte bleiben)."""
    extras = {**(o.get("extras") or {}), "club": profil, "club_score": score}
    spalten = {}
    beschreibung, highlight = texte_pruefen(ki)
    if o["typ"] == "club":
        if beschreibung:
            spalten["beschreibung"] = beschreibung
        if highlight:
            spalten["highlight"] = highlight
        spalten["qualitaets_score"] = score["gesamt"]
        if profil["unterart"]:
            extras["unterart"] = profil["unterart"]
    else:
        extras["club_beschreibung"] = beschreibung
        extras["club_highlight"] = highlight
        if profil["unterart"]:
            extras["club_unterart"] = profil["unterart"]
    speichern(db, o, extras, spalten)


def neu_pruefen(dry_run: bool) -> None:
    """Gespeicherte KI-Antworten (data/clubs/<id>.json) mit der aktuellen Belegprüfung erneut prüfen – ohne KI."""
    from database.client import get_supabase_client

    db = get_supabase_client()
    kalender = kalender_laden(db)
    alle_orte = {e["ort"] for e in kalender if e.get("ort")}
    for o in club_orte(db):
        datei = ORDNER / f"{o['id']}.json"
        if not datei.exists():
            continue
        roh = json.loads(datei.read_text(encoding="utf-8"))
        quellen = [tuple(q) for q in roh["quellen"]]
        profil, verworfen = pruefen(roh["ki"], quellen)
        namen, events = _events_fuer(o, kalender, alle_orte)
        alt = (o.get("extras") or {}).get("club") or {}
        profil.update({"event_orte": namen, "quellen": [h for h, _ in quellen], "verworfen": verworfen,
                       "modell": alt.get("modell", MODELL), "datum": alt.get("datum")})
        manuell_korrigieren(o, profil)
        score = club_score(o, profil, events)
        vorher = len(alt.get("formate") or []), len(alt.get("fakten") or {}), len(alt.get("genres") or [])
        nachher = len(profil["formate"]), len(profil["fakten"]), len(profil["genres"])
        print(f"{o['name'][:34]:34s} Score {(o.get('extras') or {}).get('club_score', {}).get('gesamt')}→{score['gesamt']}  "
              f"Formate {vorher[0]}→{nachher[0]}  Fakten {vorher[1]}→{nachher[1]}  Genres {vorher[2]}→{nachher[2]}")
        if not dry_run:
            profil_speichern(db, o, roh["ki"], profil, score)


def scores_neu(dry_run: bool, ausgabe: bool = True) -> int:
    """Score aus gespeichertem Profil und aktuellem Kalender neu berechnen (ohne KI). Gibt die Anzahl zurück."""
    from database.client import get_supabase_client

    db = get_supabase_client()
    kalender = kalender_laden(db)
    alle_orte = {e["ort"] for e in kalender if e.get("ort")}
    anzahl = 0
    for o in club_orte(db):
        profil = (o.get("extras") or {}).get("club")
        if not profil:
            continue
        namen, events = _events_fuer(o, kalender, alle_orte)
        profil["event_orte"] = namen
        manuell_korrigieren(o, profil)
        score = club_score(o, profil, events)
        anzahl += 1
        if ausgabe:
            print(f"{o['name'][:38]:38s} {score['gesamt']:2d}  P{score['programm']:4} S{score['szene']:4} "
                  f"Pr{score['profil']:4} B{score['beliebtheit']:4}  ({score['events_90_60']} Events) passt={profil['passt']}")
        if not dry_run:
            extras = {**o["extras"], "club": profil, "club_score": score}
            speichern(db, o, extras, {"qualitaets_score": score["gesamt"]} if o["typ"] == "club" else {})
    logger.info("Club-Scores neu berechnet: %d Orte", anzahl)
    return anzahl


def ist_freigegeben(o: dict) -> bool:
    """Hat der Auftraggeber den Ort nach der Sichtprüfung freigegeben? („passt“ der KI ist nur ein Vorschlag)"""
    return isinstance((o.get("extras") or {}).get("club_freigegeben"), str)


def soll_aktiv(o: dict) -> bool:
    """typ = club: aktiv nur mit passendem Profil UND Freigabe."""
    profil = (o.get("extras") or {}).get("club") or {}
    return bool(profil.get("passt")) and ist_freigegeben(o)


def umtypen_erlaubt(o: dict) -> bool:
    """
    Inaktiven Ort eines anderen Hubs zu typ = club machen? Nur mit Freigabe, passendem Profil und
    Club-Score ≥ 7 – so ist er danach unter /guides/clubs/<slug> erreichbar. Aktive Orte anderer Hubs
    (Pitcher, Schlager Cafe …) werden nie umgetypt (eine URL pro Ort).
    """
    ex = o.get("extras") or {}
    return (o.get("typ") != "club" and not o.get("aktiv") and soll_aktiv(o)
            and (ex.get("club_score") or {}).get("gesamt", 0) >= 7)


def freischalten(dry_run: bool) -> None:
    """
    Club-Orte sichtbar machen (die Website zeigt nur Freigegebene mit Score ≥ 7, lib/clubs.ts):
      - typ = club: aktiv = passt UND freigegeben,
      - inaktive auch_club-Orte: umtypen nach umtypen_erlaubt(); die alte Haupt-URL leitet auf die Club-Seite
        um (extras.vorher_typ, siehe Restaurant-/Kneipen-Detailseite),
      - aktive auch_club-Orte bleiben unverändert.
    """
    from database.client import get_supabase_client

    db = get_supabase_client()
    for o in club_orte(db):
        ex = o.get("extras") or {}
        profil, score = ex.get("club"), ex.get("club_score") or {}
        if not profil:
            continue
        if o["typ"] == "club":
            aktiv = soll_aktiv(o)
            if o.get("aktiv") != aktiv:
                print(f"{'aktiv  ' if aktiv else 'inaktiv'} {o['name']}")
                if not dry_run:
                    db.table("orte").update({"aktiv": aktiv}).eq("id", o["id"]).execute()
        elif umtypen_erlaubt(o):
            neu_ex = {k: v for k, v in ex.items() if k not in ("auch_club", "club_unterart", "club_beschreibung", "club_highlight")}
            neu_ex["unterart"] = ex.get("club_unterart") or profil.get("unterart") or "club"
            neu_ex["hub"] = "clubs"
            neu_ex["vorher_typ"] = o["typ"]
            spalten = {"typ": "club", "aktiv": True, "qualitaets_score": score.get("gesamt"), "extras": neu_ex}
            if ex.get("club_beschreibung"):
                spalten["beschreibung"] = ex["club_beschreibung"]
            if ex.get("club_highlight"):
                spalten["highlight"] = ex["club_highlight"]
            print(f"umtypen {o['typ']} → club: {o['name']}")
            if not dry_run:
                db.table("orte").update(spalten).eq("id", o["id"]).execute()


def freigeben(namen: str, entziehen: bool, dry_run: bool) -> None:
    """Freigabe nach Sichtprüfung setzen/entziehen. namen: durch „;“ getrennt, exakter Name (Groß/klein egal)."""
    from database.client import get_supabase_client

    db = get_supabase_client()
    orte = {o["name"].strip().lower(): o for o in club_orte(db)}
    heute = datetime.now(timezone.utc).date().isoformat()
    for name in [n.strip() for n in namen.split(";") if n.strip()]:
        o = orte.get(name.lower())
        if not o:
            print(f"nicht gefunden: {name}")
            continue
        ex = {k: v for k, v in (o.get("extras") or {}).items() if k != "club_freigegeben"}
        if not entziehen:
            ex["club_freigegeben"] = heute
        print(f"{'Freigabe entzogen' if entziehen else 'freigegeben'}: {o['name']}")
        if not dry_run:
            extras_mergen(db, o["id"], {"club_freigegeben": ex.get("club_freigegeben")}, entfernen=entziehen)


def csv_schreiben(pfad: str) -> None:
    from database.client import get_supabase_client

    db = get_supabase_client()
    with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Name", "Typ", "Stadtteil", "freigegeben", "passt (KI-Vorschlag)", "Grund", "Unterart", "Score", "Programm", "Szene", "Profil",
                    "Beliebtheit", "Events", "Genres (haupt)", "Genres (neben)", "Formate", "Zusatz", "Öffnung",
                    "Eintritt", "Dresscode", "Publikum", "Quellen", "Verworfen"])
        for o in sorted(club_orte(db), key=lambda o: -((o.get("extras") or {}).get("club_score") or {}).get("gesamt", 0)):
            ex = o.get("extras") or {}
            p, s = ex.get("club") or {}, ex.get("club_score") or {}
            w.writerow([
                o["name"], o["typ"], o.get("stadtteil"), ex.get("club_freigegeben") or "", p.get("passt"),
                p.get("passt_grund"), p.get("unterart"),
                s.get("gesamt"), s.get("programm"), s.get("szene"), s.get("profil"), s.get("beliebtheit"),
                s.get("events_90_60"),
                ", ".join(g["wert"] for g in p.get("genres") or [] if g["anteil"] == "haupt"),
                ", ".join(g["wert"] for g in p.get("genres") or [] if g["anteil"] != "haupt"),
                " | ".join(f"{x['name']} ({x['rhythmus']})" for x in p.get("formate") or []),
                ", ".join(z["art"] for z in p.get("zusatz_events") or []),
                ((p.get("fakten") or {}).get("oeffnung") or {}).get("text"),
                ((p.get("fakten") or {}).get("eintritt") or {}).get("text"),
                p.get("dresscode"), ", ".join(p.get("publikum") or []),
                " ".join(p.get("quellen") or []), " | ".join(p.get("verworfen") or []),
            ])
    logger.info("CSV geschrieben: %s", pfad)


def main():
    parser = argparse.ArgumentParser(description="Club-Profile (Quellen + KI mit Belegprüfung) und Club-Score")
    parser.add_argument("--max", type=int, default=1000)
    parser.add_argument("--nur", help="Nur Orte, deren Name diesen Text enthält")
    parser.add_argument("--neu", action="store_true", help="Auch schon profilierte Orte neu profilieren")
    parser.add_argument("--dry-run", action="store_true", help="Nichts speichern (KI wird aufgerufen)")
    parser.add_argument("--nur-score", action="store_true", help="Nur Score neu berechnen (ohne KI)")
    parser.add_argument("--csv", help="Sichtprüfung als CSV schreiben")
    parser.add_argument("--freischalten", action="store_true", help="Freigegebene Club-Orte aktiv setzen (siehe freischalten)")
    parser.add_argument("--freigeben", help="Nach Sichtprüfung freigeben: exakte Namen, durch „;“ getrennt")
    parser.add_argument("--freigabe-entziehen", help="Freigabe zurücknehmen: exakte Namen, durch „;“ getrennt")
    parser.add_argument("--neu-pruefen", action="store_true", help="Gespeicherte KI-Antworten erneut prüfen (ohne KI)")
    args = parser.parse_args()
    if args.freigeben or args.freigabe_entziehen:
        freigeben(args.freigeben or args.freigabe_entziehen, bool(args.freigabe_entziehen), args.dry_run)
    elif args.neu_pruefen:
        neu_pruefen(args.dry_run)
    elif args.freischalten:
        freischalten(args.dry_run)
    elif args.csv:
        csv_schreiben(args.csv)
    elif args.nur_score:
        scores_neu(args.dry_run)
    else:
        profile_erstellen(args.max, args.nur, args.neu, args.dry_run)


if __name__ == "__main__":
    main()
