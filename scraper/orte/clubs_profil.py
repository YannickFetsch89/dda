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
    "Techno": r"techno|rave|\bhard ?groove|\bacid|minimal|industrial",
    "House": r"house|deep ?house|tech ?house|afro ?house",
    "Elektro/Experimental": r"elektro|electro|electronic|experimental|ambient|clubmusik|elektronisch",
    "Drum & Bass": r"drum ?(and|&|n|'n') ?bass|\bdnb\b|\bd&b\b|jungle|breakbeat|dubstep|bass ?music",
    "Hip-Hop": r"hip ?-?hop|\brap\b|trap|deutschrap|urban",
    "R&B": r"r ?& ?b|rnb|r'n'b|\brnb\b|urban",
    "Afrobeats": r"afro ?beats?|amapiano|afro",
    "Reggaeton/Latin": r"reggaeton|latin|salsa|bachata|perreo|dancehall|kizomba|cumbia|latino",
    "Pop/Charts": r"\bpop\b|charts?|mainstream|hits|black ?(&|and) ?white|black music|party ?hits",
    "80er/90er/2000er": r"80er|90er|2000er|00er|80s|90s|2000s|throwback|oldies|ü ?30|ue ?30",
    "Schlager": r"schlager|malle|ballermann|après|apres|stimmungs",
    "Rock/Indie": r"rock|indie|alternative|britpop|grunge|emo",
    "Metal/Punk": r"metal|punk|hardcore|gothic|wave|dark",
    "Disco/Funk/Soul": r"disco|funk|soul|motown|boogie",
    "Jazz": r"jazz|swing",
    "Mixed": r"mixed|querbeet|gemischt|bunt gemischt|alles von|von .* bis|vielf[äa]ltig|verschiedene|open format",
}

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


_FUELL_NAME = re.compile(r"d[üu]sseldorf|\bclub\b|\bklub\b|\bbar\b|\be\.? ?v\.?|eventlocation|event location|"
                         r"nachtclub|discothek|diskothek|\bdisco\b|\bthe\b|\bder\b|\bdie\b|\bdas\b|zentrum f[üu]r|"
                         r"[-–|/&]", re.IGNORECASE)


def ort_schluessel(name: str) -> str:
    """Kern des Clubnamens zum Abgleich mit events.ort („Rudas Studios Club“ → „rudasstudios“)."""
    kern = _key(_FUELL_NAME.sub(" ", name or ""))
    # Zu kurz („Kö“ aus „Kö Club - Düsseldorf“): „Club“ behalten, nur Stadt und Trennzeichen weg
    return kern if len(kern) >= 4 else _key(re.sub(r"d[üu]sseldorf|[-–|/&]", " ", name or "", flags=re.IGNORECASE))


# Bekannte Kurzformen im Eventkalender (Google-Name → weitere Schlüssel)
ALIASE = {
    "zentrumfueraktionkulturundkommunikation": ["zakk"],
    "zakk": ["zakk"],
    "kulturschlachthof": ["kulturschlachthof", "r25"],
    "schleusezweis2": ["schleusezwei"],
    "giselle": ["giselle"],
}


# Ortsangaben im Kalender, die nichts über den Club sagen
_ALLGEMEIN = {"duesseldorf", "altstadt", "neuss", "ratingen", "kultur", "online", "innenstadt", "stadtmitte"}


def event_orte(name: str, alle_orte: set[str]) -> list[str]:
    """Schreibweisen dieses Orts im Eventkalender (für „Nächste Events hier“)."""
    eigener = ort_schluessel(name)
    # Kurzformen: Alias-Schlüssel steckt im Namen („…kommunikation (zakk)“ → „zakk“)
    aliase = [a for teil, liste in ALIASE.items() if teil in _key(name) for a in liste]
    treffer = []
    for ort in alle_orte:
        # Beide Seiten gleich normalisieren („SUB Düsseldorf“ → „sub“, „Düsseldorf“ → leer)
        k = ort_schluessel(ort)
        if not k or k in _ALLGEMEIN or re.search(r"nicht im", ort, re.IGNORECASE):
            continue
        # Gleich, oder Teiltreffer mit mind. 4 Zeichen („Stone im Ratinger Hof“) – kurze Schlüssel wie „sub“
        # nur exakt, sonst träfe „sub“ jeden Ort mit „Sub…“ im Namen
        if eigener and (k == eigener or (len(eigener) >= 4 and eigener in k) or (len(k) >= 6 and k in eigener)):
            treffer.append(ort)
        # Aliase nur am Anfang („zakk – Halle“, nicht „HHU …, am Finaltag im zakk“)
        elif any(k.startswith(a) for a in aliase):
            treffer.append(ort)
    return sorted(treffer)


def kalender_laden(db) -> list[dict]:
    """Events der letzten 180 Tage und alle kommenden (nur Felder für Profil und Score)."""
    ab = (date.today() - timedelta(days=180)).isoformat()
    return alle_zeilen(db, "events", "titel, ort, datum, kategorie, quelle_name, beschreibung",
                       lambda q: q.gte("datum", ab))


def website_quellen(start: str | None) -> list[tuple[str, str]]:
    """Startseite + passende Unterseiten derselben Domain als (url, text)."""
    from bs4 import BeautifulSoup

    if not start or _gesperrt(start):
        return []
    html = seite_laden(start)
    if not html:
        return []
    quellen = [(start, seiten_text(html)[:MAX_QUELLE])]
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
            quellen.append((url, seiten_text(teil)[:MAX_QUELLE]))
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
            quellen.append((url, text[:MAX_QUELLE]))
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


def _zahl(text: str) -> float | None:
    try:
        wert = float((text or "").replace(",", ".").strip())
        return wert if 0 <= wert <= 200 else None
    except ValueError:
        return None


def pruefen(ki: dict, quellen: list[tuple[str, str]]) -> tuple[dict, list[str]]:
    """Nur belegte Angaben übernehmen → (club-Profil, verworfene Angaben)."""
    verworfen: list[str] = []
    gesamt = "\n".join(t for _, t in quellen)

    def ok(zitat: str, was: str) -> str | None:
        h = _herkunft(zitat, quellen)
        if not h:
            verworfen.append(f"{was} (Zitat nicht in den Quellen)")
        return h

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
        if f.get("name") and (h := ok(f.get("zitat"), f"Format {f.get('name')}")):
            formate.append({"name": f["name"].strip()[:80], "rhythmus": (f.get("rhythmus") or "").strip()[:60],
                            "musik": (f.get("musik") or "").strip()[:80], "zitat": f["zitat"].strip(), "quelle": h})

    zusatz = []
    for z in ki.get("zusatz_events") or []:
        if z.get("art") in ZUSATZ and not any(x["art"] == z["art"] for x in zusatz):
            if (h := ok(z.get("zitat"), f"Zusatz {z['art']}")):
                zusatz.append({"art": z["art"], "beispiel": (z.get("beispiel") or "").strip()[:100],
                               "zitat": z["zitat"].strip(), "quelle": h})

    fakten = {}
    for k, v in (ki.get("fakten") or {}).items():
        text = (v.get("text") or "").strip()
        if text and (h := ok(v.get("zitat"), f"Fakt {k}")):
            fakten[k] = {"text": text[:120], "zitat": v["zitat"].strip(), "quelle": h}

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

    def liste(feld: str, erlaubt: list[str]) -> list[str]:
        werte = []
        for x in ki.get(feld) or []:
            if x.get("wert") in erlaubt and x["wert"] not in werte and ok(x.get("zitat"), f"{feld} {x['wert']}"):
                werte.append(x["wert"])
        return werte

    def link(url: str, muster: str) -> str | None:
        url = (url or "").strip()
        return url if re.match(muster, url) and _key(url) in _key(gesamt) else None

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
        "publikum": liste("publikum", PUBLIKUM),
        "ausstattung": liste("ausstattung", AUSSTATTUNG),
        "instagram": link(ki.get("instagram"), r"https?://(www\.)?instagram\.com/"),
        "resident_advisor": link(ki.get("resident_advisor"), r"https?://(www\.)?ra\.co/clubs/"),
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


def speichern(db, ort: dict, extras_neu: dict, spalten: dict) -> None:
    db.table("orte").update({"extras": extras_neu, **spalten}).eq("id", ort["id"]).execute()


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
            extras = {**(o.get("extras") or {}), "club": profil, "club_score": score}
            spalten = {}
            if o["typ"] == "club":
                # Eigene Club-Zeilen: Texte und Score direkt; bei auch_club bleiben die Texte des Haupt-Hubs
                beschreibung = (ki.get("beschreibung") or "").strip()
                highlight = (ki.get("highlight") or "").strip()
                if 200 <= len(beschreibung) <= 1600:
                    spalten["beschreibung"] = beschreibung
                if 10 <= len(highlight) <= 160:
                    spalten["highlight"] = highlight
                spalten["qualitaets_score"] = score["gesamt"]
                if profil["unterart"]:
                    extras["unterart"] = profil["unterart"]
            else:
                extras["club_beschreibung"] = (ki.get("beschreibung") or "").strip() or None
                extras["club_highlight"] = (ki.get("highlight") or "").strip() or None
                if profil["unterart"]:
                    extras["club_unterart"] = profil["unterart"]
            speichern(db, o, extras, spalten)
        except Exception as e:
            logger.error("Fehler bei '%s': %s", o["name"], e)


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


def freischalten(dry_run: bool) -> None:
    """
    Club-Orte sichtbar machen (die Website zeigt davon nur Score ≥ 7, lib/clubs.ts):
      - typ = club: aktiv = passt laut Profil,
      - auch_club-Orte, die in ihrem Haupt-Hub NICHT sichtbar sind (aktiv = false, z. B. zakk als
        Restaurant): zu typ = club umtypen – sie hatten noch keine öffentliche URL, es geht also keine verloren.
      - auch_club-Orte, die im Haupt-Hub aktiv sind (Pitcher, Schlager Cafe …), bleiben unverändert.
    """
    from database.client import get_supabase_client

    db = get_supabase_client()
    for o in club_orte(db):
        ex = o.get("extras") or {}
        profil, score = ex.get("club"), ex.get("club_score") or {}
        if not profil:
            continue
        passt = bool(profil.get("passt"))
        if o["typ"] == "club":
            if o.get("aktiv") != passt:
                print(f"{'aktiv  ' if passt else 'inaktiv'} {o['name']}")
                if not dry_run:
                    db.table("orte").update({"aktiv": passt}).eq("id", o["id"]).execute()
        elif not o.get("aktiv") and passt:
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


def csv_schreiben(pfad: str) -> None:
    from database.client import get_supabase_client

    db = get_supabase_client()
    with open(pfad, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Name", "Typ", "Stadtteil", "passt", "Grund", "Unterart", "Score", "Programm", "Szene", "Profil",
                    "Beliebtheit", "Events", "Genres (haupt)", "Genres (neben)", "Formate", "Zusatz", "Öffnung",
                    "Eintritt", "Dresscode", "Publikum", "Quellen", "Verworfen"])
        for o in sorted(club_orte(db), key=lambda o: -((o.get("extras") or {}).get("club_score") or {}).get("gesamt", 0)):
            ex = o.get("extras") or {}
            p, s = ex.get("club") or {}, ex.get("club_score") or {}
            w.writerow([
                o["name"], o["typ"], o.get("stadtteil"), p.get("passt"), p.get("passt_grund"), p.get("unterart"),
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
    parser.add_argument("--freischalten", action="store_true", help="Passende Club-Orte aktiv setzen (siehe freischalten)")
    args = parser.parse_args()
    if args.freischalten:
        freischalten(args.dry_run)
    elif args.csv:
        csv_schreiben(args.csv)
    elif args.nur_score:
        scores_neu(args.dry_run)
    else:
        profile_erstellen(args.max, args.nur, args.neu, args.dry_run)


if __name__ == "__main__":
    main()
