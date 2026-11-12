"""
Beschreibungen für Events aus eigenen Quellen statt geratener Titel-Texte.

Rausgegangen-Detailseiten dürfen wir nicht abrufen (robots.txt sperrt alles). Für Events ohne echte
Beschreibung suchen wir deshalb die Seite des Veranstalters:

  1. Website des Veranstaltungsorts: aus unserer Orte-Tabelle oder per Google-Places-Textsuche
  2. Auf dieser Website die Seite zum Event (Links mit passenden Titelwörtern, Programmseiten)
  3. Sonst: Websuche über die Claude-API (gesperrte Seiten ausgeschlossen), Seiten rufen wir selbst ab
  4. Haiku schreibt aus dem gefundenen Text eine neue Beschreibung – gleicher Inhalt, eigener Wortlaut.
     Fakten müssen mit wörtlichen Belegen aus der Quelle gestützt sein; längere wörtliche Übernahmen
     werden verworfen.

Überall gilt: robots.txt wird geprüft, mindestens 2 s zwischen Abrufen.

Veranstalter-Events (Schauspielhaus, Oper, Stadtbüchereien, Kunstpalast …, seit 12.11.2026): Die Event-Seite ist
schon bekannt (quelle_url) – keine Suche nötig. Ein Text pro Stück (gleicher Titel am gleichen Ort), übertragen
auf alle Termine. Ersetzt wird nur ein fehlender, kurzer (< 200 Zeichen) oder kürzerer Text.

Aufruf:
    python -m pipeline.beschreibung_quellen --probe 20                 # Probelauf Rausgegangen, schreibt nichts
    python -m pipeline.beschreibung_quellen --probe-veranstalter 20    # Probelauf Veranstalter-Events, schreibt nichts
    python -m pipeline.beschreibung_quellen --nachziehen 400           # offene Rausgegangen-Events (mit Sicherung)
    python -m pipeline.beschreibung_quellen --veranstalter 800         # offene Veranstalter-Stücke (mit Sicherung)
Im Lauf: beschreibungen_nachziehen(...) und veranstalter_nachziehen(...) nach der Kategorisierung (main.py).
"""
import argparse
import json
import logging
import random
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

from scraper.orte.bars_einordnen import belegt  # noqa: E402

logger = logging.getLogger("beschreibung_quellen")

MODELL = "claude-haiku-5-5"
ORDNER = Path("data/beschreibung_quellen")
WEBSITE_CACHE = ORDNER / "ort_websites.json"

# Seiten, die wir nicht abrufen dürfen oder die nichts Brauchbares liefern (Login, Bot-Sperre)
GESPERRT = (
    "rausgegangen.de", "duesseldorf.de", "facebook.com", "instagram.com", "tiktok.com", "x.com", "twitter.com",
    "youtube.com", "google.com", "linkedin.com",
)
PROGRAMM_LINK = re.compile(
    r"programm|veranstaltung|event|termin|kalender|spielplan|tickets?|kurse?|workshops?|fuehrung|führung|agenda|whats-?on",
    re.IGNORECASE,
)
_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
_FUELL = {"der", "die", "das", "und", "mit", "von", "fuer", "the", "and", "ein", "eine", "im", "in", "am", "an",
          "zu", "zum", "zur", "auf", "of", "a", "duesseldorf", "live", "black", "box", "filmmuseum"}


# ── Hilfen ────────────────────────────────────────────────────────────────────────────────────────

def _woerter(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower().translate(_UMLAUTE))


def titel_woerter(titel: str) -> set[str]:
    """Unterscheidende Titelwörter (nur vor einem „|“ – danach hängt Rausgegangen Reihe/Spielort an)."""
    kopf = re.split(r"\s+\|\s+", titel or "")[0]
    return {w for w in _woerter(kopf) if w not in _FUELL and len(w) > 2}


def _gesperrt(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in GESPERRT)


_robots_cache: dict[str, object] = {}


def robots_erlaubt(url: str) -> bool:
    """robots.txt der Domain prüfen (je Domain einmal geladen). Nicht erreichbar = erlaubt."""
    from urllib import robotparser

    basis = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    if basis not in _robots_cache:
        rp = robotparser.RobotFileParser()
        try:
            antwort = httpx.get(basis + "/robots.txt", timeout=15, follow_redirects=True,
                                headers={"User-Agent": "Mozilla/5.0"})
            rp.parse(antwort.text.splitlines() if antwort.status_code < 400 else [])
        except Exception:
            rp.parse([])
        _robots_cache[basis] = rp
    return _robots_cache[basis].can_fetch("*", url)


def seite_laden(url: str) -> str | None:
    """HTML einer erlaubten Seite (Rate Limiting über seite_abrufen, 2 s)."""
    from scraper.utils.http_client import seite_abrufen

    if _gesperrt(url) or not robots_erlaubt(url):
        logger.info("Nicht abrufbar (gesperrt/robots): %s", url)
        return None
    return seite_abrufen(url, logger, wartezeit=2.0)


def seiten_text(html: str) -> str:
    """Lesbarer Text einer Seite ohne Navigation, Kopf- und Fußbereich."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "form", "svg"]):
        tag.decompose()
    haupt = soup.find("main") or soup.find("article") or soup.body or soup
    zeilen = [z.strip() for z in haupt.get_text("\n", strip=True).splitlines()]
    return "\n".join(z for z in zeilen if z)


def titel_treffer(text: str, woerter: set[str]) -> float:
    """Anteil der Titelwörter, die im Text vorkommen."""
    if not woerter:
        return 0.0
    vorhanden = set(_woerter(text))
    return len(woerter & vorhanden) / len(woerter)


# ── 1. Website des Veranstaltungsorts ──────────────────────────────────────────────────────────────

def _cache_laden() -> dict:
    try:
        return json.loads(WEBSITE_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def ort_website(ort: str, adresse: str | None, orte_webseiten: dict[str, str], cache: dict) -> str | None:
    """Website zum Ort: Orte-Tabelle, sonst Google-Places-Textsuche (Ergebnis wird zwischengespeichert)."""
    schluessel = re.sub(r"[^a-z0-9]", "", (ort or "").lower().translate(_UMLAUTE))
    if schluessel in orte_webseiten:
        return orte_webseiten[schluessel]
    if schluessel in cache:
        return cache[schluessel]
    from scraper.orte.google_places import API_BASE, GOOGLE_PLACES_API_KEY, _headers

    if not GOOGLE_PLACES_API_KEY:
        return None  # z.B. im GitHub-Lauf ohne Places-Schlüssel – dann bleibt die Websuche
    website = None
    try:
        anfrage = f"{ort}, {adresse}" if adresse else f"{ort} Düsseldorf"
        time.sleep(0.5)
        antwort = httpx.post(
            f"{API_BASE}/places:searchText",
            json={"textQuery": anfrage, "languageCode": "de", "maxResultCount": 1,
                  "locationBias": {"circle": {"center": {"latitude": 51.2277, "longitude": 6.7735}, "radius": 20000}}},
            headers=_headers("places.displayName,places.websiteUri"),
            timeout=30,
        )
        antwort.raise_for_status()
        orte = antwort.json().get("places") or []
        if orte:
            website = orte[0].get("websiteUri")
    except Exception as e:
        logger.warning("Places-Suche für '%s' fehlgeschlagen: %s", ort, e)
    cache[schluessel] = website
    try:
        WEBSITE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        WEBSITE_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError as e:
        logger.warning("Website-Zwischenspeicher nicht schreibbar: %s", e)
    return website


# ── 2. Event-Seite auf der Website ─────────────────────────────────────────────────────────────────

def _links(html: str, basis: str) -> list[tuple[str, str]]:
    from bs4 import BeautifulSoup

    domain = urlparse(basis).netloc.removeprefix("www.")
    ergebnis, gesehen = [], set()
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        ziel = urljoin(basis, a["href"]).split("#")[0]
        if urlparse(ziel).netloc.removeprefix("www.") != domain or ziel in gesehen:
            continue
        if re.search(r"\.(pdf|jpe?g|png|zip)$", ziel, re.IGNORECASE) or ziel.startswith("mailto:"):
            continue
        gesehen.add(ziel)
        ergebnis.append((ziel, a.get_text(" ", strip=True)))
    return ergebnis


def event_seite_auf_website(website: str, event: dict, max_abrufe: int = 5) -> tuple[str, str] | None:
    """Sucht auf der Website die Seite zum Event. Rückgabe (url, text) oder None."""
    woerter = titel_woerter(event["titel"])
    if not woerter:
        return None
    abrufe = 0
    warteschlange = [website]
    besucht: set[str] = set()
    programmseiten: list[str] = []
    while warteschlange and abrufe < max_abrufe:
        url = warteschlange.pop(0)
        if url in besucht:
            continue
        besucht.add(url)
        html = seite_laden(url)
        abrufe += 1
        if not html:
            continue
        text = seiten_text(html)
        # Detailseite: Titel steht drin und die Seite ist nicht nur eine lange Übersicht
        if url != website and titel_treffer(text, woerter) >= 0.75 and len(text) < 15000:
            return url, text
        kandidaten = []
        for ziel, linktext in _links(html, url):
            if ziel in besucht:
                continue
            treffer = titel_treffer(linktext + " " + ziel.replace("-", " ").replace("_", " "), woerter)
            if treffer >= 0.6:
                kandidaten.append((treffer, ziel))
            elif PROGRAMM_LINK.search(linktext + " " + urlparse(ziel).path) and ziel not in programmseiten:
                programmseiten.append(ziel)
        kandidaten.sort(reverse=True)
        # Passende Links zuerst, danach Programmseiten (dort stehen die Event-Links)
        warteschlange = [z for _, z in kandidaten[:2]] + warteschlange + programmseiten[:2]
        programmseiten = programmseiten[2:]
    return None


# ── 3. Websuche ────────────────────────────────────────────────────────────────────────────────────

def websuche(client, event: dict) -> list[str]:
    """URLs aus einer Websuche (Claude-API) zum Event – ohne gesperrte Seiten."""
    anfrage = (f"Suche die Seite des Veranstalters oder Veranstaltungsorts zu diesem Event in Düsseldorf: "
               f"„{event['titel']}“, {event['datum']}, Ort: {event.get('ort')}. Eine einzige Suche genügt.")
    try:
        antwort = client.messages.create(
            model=MODELL, max_tokens=1024,
            messages=[{"role": "user", "content": anfrage}],
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 1,
                    "blocked_domains": ["rausgegangen.de", "duesseldorf.de"],
                    "user_location": {"type": "approximate", "city": "Düsseldorf", "country": "DE",
                                      "timezone": "Europe/Berlin"}}],
        )
    except Exception as e:
        logger.warning("Websuche für '%s' fehlgeschlagen: %s", event["titel"][:40], e)
        return []
    urls = []
    for block in antwort.content:
        if getattr(block, "type", "") == "web_search_tool_result" and isinstance(block.content, list):
            for r in block.content:
                url = getattr(r, "url", None)
                if url and not _gesperrt(url) and url not in urls:
                    urls.append(url)
    return urls


def event_seite_aus_suche(client, event: dict) -> tuple[str, str] | None:
    woerter = titel_woerter(event["titel"])
    for url in websuche(client, event)[:4]:
        html = seite_laden(url)
        if not html:
            continue
        text = seiten_text(html)
        if titel_treffer(text, woerter) >= 0.75:
            return url, text
    return None


# ── 4. Umschreiben ─────────────────────────────────────────────────────────────────────────────────

SCHEMA = {
    "type": "object",
    "properties": {
        "passt": {"type": "boolean", "description": "Beschreibt die Quelle genau dieses Event?"},
        "grund": {"type": "string"},
        "beschreibung": {"type": "string"},
        "belege": {"type": "array", "items": {"type": "string"},
                   "description": "Kurze wörtliche Zitate aus der Quelle, die die Fakten der Beschreibung stützen"},
    },
    "required": ["passt", "grund", "beschreibung", "belege"],
    "additionalProperties": False,
}

SYSTEM = """Du schreibst Event-Beschreibungen für dies.das.düsseldorf, einen Düsseldorfer Event-Guide.
Du bekommst die Eckdaten eines Events und den Text einer Webseite (Veranstalter oder Veranstaltungsort).

1. Prüfe zuerst, ob die Seite genau dieses Event beschreibt (gleicher Titel/Inhalt; bei Reihen der gleiche
   Termin oder ein Text, der für alle Termine gilt). Wenn nicht: passt=false, beschreibung leer.
2. Wenn ja, schreib eine neue Beschreibung auf Deutsch:
   - Nur Inhalte aus der Quelle. Nichts erfinden, nichts ergänzen, keine Bewertungen, die dort nicht stehen.
   - Eigener Wortlaut: keine Sätze oder längeren Wortfolgen aus der Quelle übernehmen, nur den Inhalt.
     Eigennamen, Werktitel und Namen von Mitwirkenden dürfen wörtlich bleiben.
   - Locker und einladend, keine Werbesprache, kein Clickbait, Du-Form.
   - Kein Verweis auf „diese Seite“, Links, Buttons oder den Ticketkauf dort – der Text steht bei uns,
     nicht auf der Quellseite. Anmelde- oder Ticket-Hinweise nur, wenn die Quelle sie ausdrücklich nennt.
   - Gut gegliedert: ein kurzer Einstieg, dann bei Bedarf Absätze (Leerzeile dazwischen) oder eine kurze
     Liste mit „• “ für Programmpunkte, Mitwirkende oder Hinweise. Emojis sparsam als Gliederung
     (z.B. 🎬 🎶 🎨 📍 🎟️ 👉), kein Muss.
   - Länge nach Inhalt der Quelle: wenig Inhalt = kurz (2–3 Sätze), viel Inhalt = ausführlicher
     (bis etwa 1200 Zeichen). Datum, Uhrzeit, Ort und Preis nicht wiederholen, die zeigt die Seite schon –
     außer es gibt Besonderheiten (z.B. Einlass, Altersfreigabe, Sprache, Anmeldung nötig).
3. belege: 2–6 kurze wörtliche Zitate (je 3–15 Wörter) aus der Quelle, die die wichtigsten Fakten stützen."""


MAX_UEBERNAHME = 7  # höchstens so viele Wörter am Stück wörtlich aus der Quelle


def _uebernahmen(text: str, quelle: str) -> list[tuple[int, int]]:
    """Wörtlich übernommene Wortfolgen als (Startindex im Text, Länge), längste je Startposition."""
    a, b = _woerter(text), _woerter(quelle)
    positionen: dict[str, list[int]] = {}
    for j, w in enumerate(b):
        positionen.setdefault(w, []).append(j)
    treffer = []
    for i, w in enumerate(a):
        beste = 0
        for j in positionen.get(w, []):
            n = 0
            while i + n < len(a) and j + n < len(b) and a[i + n] == b[j + n]:
                n += 1
            beste = max(beste, n)
        if beste:
            treffer.append((i, beste))
    return treffer


def laengste_uebernahme(text: str, quelle: str) -> int:
    """Länge (in Wörtern) der längsten wörtlich übernommenen Wortfolge."""
    return max((n for _, n in _uebernahmen(text, quelle)), default=0)


def zu_lange_uebernahmen(text: str, quelle: str) -> list[str]:
    """Wortfolgen über MAX_UEBERNAHME Wörtern, die wörtlich aus der Quelle stammen (für die Nachbesserung)."""
    woerter = _woerter(text)
    stellen, bis = [], -1
    for i, n in _uebernahmen(text, quelle):
        if n > MAX_UEBERNAHME and i > bis:
            stellen.append(" ".join(woerter[i:i + n]))
            bis = i + n
    return stellen


def umschreiben(client, event: dict, url: str, quelltext: str) -> dict:
    """Haiku schreibt die Beschreibung; Ergebnis mit Prüfungen (Belege, wörtliche Übernahme)."""
    eingabe = (f"Event: {event['titel']}\nDatum: {event['datum']} {event.get('uhrzeit') or ''}\n"
               f"Ort: {event.get('ort')}\nQuelle: {url}\n\nText der Quelle:\n{quelltext[:9000]}")
    verlauf = [{"role": "user", "content": eingabe}]
    daten: dict = {}
    for versuch in range(2):
        antwort = client.messages.create(
            model=MODELL, max_tokens=2500, system=SYSTEM,
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=verlauf,
        )
        roh = next(b.text for b in antwort.content if b.type == "text")
        daten = json.loads(roh)
        stellen = zu_lange_uebernahmen(daten.get("beschreibung") or "", quelltext)
        if not daten.get("passt") or not stellen:
            break
        # Zweiter Durchgang: wörtlich übernommene Stellen neu formulieren lassen
        daten["nachgebessert"] = True
        verlauf += [
            {"role": "assistant", "content": roh},
            {"role": "user", "content": "Diese Stellen sind wörtlich aus der Quelle übernommen. Formuliere sie mit "
                                        "eigenen Worten um (gleicher Inhalt, Namen und Titel dürfen bleiben) und gib "
                                        "die vollständige Antwort erneut aus:\n- " + "\n- ".join(stellen)},
        ]
    belege = daten.get("belege") or []
    daten["belege_ok"] = sum(1 for z in belege if belegt(z, quelltext))
    daten["belege_gesamt"] = len(belege)
    daten["uebernahme_woerter"] = laengste_uebernahme(daten.get("beschreibung") or "", quelltext)
    # Freigabe: passt, mind. 2 Belege wörtlich gefunden, höchstens 7 Wörter am Stück übernommen
    daten["freigegeben"] = bool(daten.get("passt") and (daten.get("beschreibung") or "").strip()
                                and daten["belege_ok"] >= 2 and daten["uebernahme_woerter"] <= MAX_UEBERNAHME)
    return daten


# ── Ablauf ─────────────────────────────────────────────────────────────────────────────────────────

def stichprobe(anzahl: int, seed: int = 7) -> list[dict]:
    """Zufällige Rausgegangen-Events, je Ort höchstens eines."""
    from database.client import get_supabase_client
    from pipeline.rausgegangen_nachziehen import _rausgegangen_eintraege

    alle = _rausgegangen_eintraege(get_supabase_client())
    random.Random(seed).shuffle(alle)
    gewaehlt, orte = [], set()
    for e in alle:
        if e.get("ort") not in orte:
            orte.add(e.get("ort"))
            gewaehlt.append(e)
        if len(gewaehlt) == anzahl:
            break
    return gewaehlt


def orte_webseiten() -> dict[str, str]:
    from database.client import get_supabase_client

    db, ergebnis, start = get_supabase_client(), {}, 0
    while True:
        seite = db.table("orte").select("name,webseite").range(start, start + 999).execute().data or []
        for o in seite:
            if o.get("webseite"):
                ergebnis[re.sub(r"[^a-z0-9]", "", o["name"].lower().translate(_UMLAUTE))] = o["webseite"]
        if len(seite) < 1000:
            return ergebnis
        start += 1000


def event_bearbeiten(client, event: dict, webseiten: dict[str, str], cache: dict) -> dict:
    """Quelle suchen und Beschreibung schreiben. Ergebnis-Dict mit 'freigegeben', 'beschreibung', 'quelle_url'."""
    eintrag = {"id": event["id"], "slug": event.get("slug"), "titel": event["titel"], "datum": event["datum"],
               "ort": event.get("ort"), "bisher": event.get("beschreibung"), "weg": None}
    website = ort_website(event.get("ort") or "", event.get("adresse"), webseiten, cache)
    eintrag["ort_website"] = website
    fund = None
    if website and not _gesperrt(website):
        fund = event_seite_auf_website(website, event)
        if fund:
            eintrag["weg"] = "Website des Orts"
    if not fund:
        fund = event_seite_aus_suche(client, event)
        if fund:
            eintrag["weg"] = "Websuche"
    if fund:
        url, text = fund
        eintrag["quelle_url"] = url
        eintrag["quelltext"] = text[:9000]
        try:
            eintrag.update(umschreiben(client, event, url, text))
        except Exception as e:
            eintrag["fehler"] = f"{type(e).__name__}: {e}"
    return eintrag


def probe(anzahl: int) -> None:
    import anthropic

    ORDNER.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic()
    webseiten, cache = orte_webseiten(), _cache_laden()
    ergebnisse = []
    for nr, event in enumerate(stichprobe(anzahl), 1):
        logger.info("[%d/%d] %s (%s)", nr, anzahl, event["titel"][:50], event.get("ort"))
        ergebnisse.append(event_bearbeiten(client, event, webseiten, cache))
        (ORDNER / "probe.json").write_text(json.dumps(ergebnisse, ensure_ascii=False, indent=1), encoding="utf-8")
    bericht_schreiben(ergebnisse)


def offene_rausgegangen_events(db, limit: int) -> list[dict]:
    """Künftige Rausgegangen-Events, für die noch keine Beschreibungsquelle gesucht wurde (früheste zuerst)."""
    from datetime import date

    antwort = (
        db.table("events")
        .select("id,titel,ort,adresse,datum,uhrzeit,slug,beschreibung,quelle_name,quelle_url")
        .gte("datum", date.today().isoformat())
        .is_("beschreibung_gesucht_am", "null")
        .or_("quelle_name.ilike.*rausgegangen*,quelle_url.ilike.*rausgegangen.de*")
        .order("datum")
        .limit(limit)
        .execute()
    )
    return antwort.data or []


def beschreibungen_nachziehen(limit: int = 40, sicherung: bool = False) -> int:
    """
    Sucht für Rausgegangen-Events eine Veranstalter-Quelle und ersetzt die Beschreibung, wenn der neue Text
    alle Prüfungen besteht. Ohne Fund bleibt der bisherige Text. Jedes bearbeitete Event bekommt
    beschreibung_gesucht_am, damit es nicht erneut gesucht wird.

    Returns:
        Anzahl der Events mit neuer Beschreibung
    """
    import anthropic
    from datetime import datetime, timezone

    from database.client import get_supabase_client

    db = get_supabase_client()
    events = offene_rausgegangen_events(db, limit)
    if not events:
        logger.info("Beschreibungen: keine offenen Rausgegangen-Events")
        return 0
    client = anthropic.Anthropic()
    webseiten, cache = orte_webseiten(), _cache_laden()
    sicherungsdatei = ORDNER / f"sicherung_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
    neu = 0
    for nr, event in enumerate(events, 1):
        logger.info("Beschreibung [%d/%d]: %s (%s)", nr, len(events), event["titel"][:50], event.get("ort"))
        try:
            eintrag = event_bearbeiten(client, event, webseiten, cache)
        except Exception as e:
            logger.error("Beschreibung für '%s' fehlgeschlagen: %s", event["titel"][:40], e)
            continue
        update = {"beschreibung_gesucht_am": datetime.now(timezone.utc).isoformat()}
        if eintrag.get("freigegeben"):
            update["beschreibung"] = eintrag["beschreibung"].strip()
            update["beschreibung_quelle"] = eintrag["quelle_url"]
        try:
            if sicherung and "beschreibung" in update:
                ORDNER.mkdir(parents=True, exist_ok=True)
                with sicherungsdatei.open("a", encoding="utf-8") as f:
                    zeile = {"id": event["id"], "beschreibung": event.get("beschreibung")}
                    f.write(json.dumps(zeile, ensure_ascii=False) + "\n")
            db.table("events").update(update).eq("id", event["id"]).execute()
            if "beschreibung" in update:
                neu += 1
                logger.info("Neue Beschreibung (%d Zeichen) aus %s", len(update["beschreibung"]), eintrag["quelle_url"])
        except Exception as e:
            logger.error("Speichern der Beschreibung für '%s' fehlgeschlagen: %s", event["titel"][:40], e)
    logger.info("Beschreibungen: %d von %d Events mit neuem Text", neu, len(events))
    return neu


# ── Veranstalter-Events: Quelle ist die eigene Event-Seite ────────────────────────────────────────────

# Ein vorhandener Text wird nur ersetzt, wenn er fehlt, kurz ist oder der neue länger ist
KURZ = 200


def _seiten_pfad(url: str) -> str:
    """Event-Seite ohne Abfrage und ohne Monats-Segment: /programm/spielplan/2026-11/blutbuch/3072/ → …/blutbuch/3072"""
    teile = urlparse(url or "")
    pfad = "/".join(t for t in teile.path.split("/") if t and not re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", t))
    return f"{teile.netloc.removeprefix('www.')}/{pfad}"


def _stueck_schluessel(event: dict) -> tuple[str, str, str]:
    """
    Ein Stück = gleicher Titel am gleichen Ort UND dieselbe Seite beim Veranstalter. Allgemeine Titel wie
    „Öffentliche Führung“ (Kunstpalast: eine Seite je Ausstellung) bleiben so getrennt; Termine desselben Stücks
    in verschiedenen Monaten (Schauspielhaus) landen zusammen.
    """
    return (" ".join(_woerter(event.get("titel") or "")), " ".join(_woerter(event.get("ort") or "")),
            _seiten_pfad(event.get("quelle_url") or ""))


def stuecke_bilden(events: list[dict]) -> list[list[dict]]:
    """Gruppiert Termine nach Stück, früheste Stücke zuerst; innerhalb des Stücks nach Datum. (rein, testbar)"""
    gruppen: dict[tuple[str, str, str], list[dict]] = {}
    for e in events:
        if not e.get("quelle_url") or not _stueck_schluessel(e)[0]:
            continue
        gruppen.setdefault(_stueck_schluessel(e), []).append(e)
    stuecke = [sorted(g, key=lambda e: (e.get("datum") or "", e.get("uhrzeit") or "")) for g in gruppen.values()]
    return sorted(stuecke, key=lambda g: g[0].get("datum") or "")


def ersetzen_erlaubt(alt: str | None, neu: str) -> bool:
    """Neuer Quellentext ersetzt den bisherigen, wenn der fehlt, kurz ist (meist geratener KI-Text) oder kürzer ist."""
    alt = (alt or "").strip()
    return bool(neu.strip()) and (len(alt) < KURZ or len(neu.strip()) > len(alt))


def offene_veranstalter_events(db) -> list[dict]:
    """
    Künftige Events, die nicht von Rausgegangen stammen (dort ist die Detailseite gesperrt), eine eigene Event-URL
    haben, noch keinen Quellentext tragen und noch nicht gesucht wurden.
    """
    from datetime import date

    events, start = [], 0
    while True:
        seite = (
            db.table("events")
            .select("id,titel,ort,datum,uhrzeit,slug,beschreibung,quelle_name,quelle_url")
            .gte("datum", date.today().isoformat())
            .eq("abgelehnt", False)
            .is_("beschreibung_gesucht_am", "null")
            .is_("beschreibung_quelle", "null")
            .not_.is_("quelle_url", "null")
            .not_.ilike("quelle_name", "*rausgegangen*")
            .not_.ilike("quelle_url", "*rausgegangen.de*")
            .order("datum")
            .range(start, start + 999)
            .execute()
        ).data or []
        events += seite
        start += 1000
        if len(seite) < 1000:
            return events


def stueck_bearbeiten(client, stueck: list[dict]) -> dict:
    """Erste abrufbare Event-URL des Stücks laden und umschreiben. Ergebnis wie event_bearbeiten."""
    event = stueck[0]
    eintrag = {"id": event["id"], "titel": event["titel"], "datum": event["datum"], "ort": event.get("ort"),
               "bisher": event.get("beschreibung"), "weg": "Event-Seite des Veranstalters", "termine": len(stueck)}
    woerter = titel_woerter(event["titel"])
    for url in list(dict.fromkeys(e["quelle_url"] for e in stueck))[:2]:
        html = seite_laden(url)
        if not html:
            continue
        text = seiten_text(html)
        # Zu wenig Text oder Titel nicht auf der Seite: nicht dieses Event (z. B. nur ein Kalender per JavaScript)
        if len(text) < 200 or (woerter and titel_treffer(text, woerter) < 0.5):
            continue
        eintrag["quelle_url"] = url
        eintrag["quelltext"] = text[:9000]
        try:
            eintrag.update(umschreiben(client, event, url, text))
        except Exception as e:
            eintrag["fehler"] = f"{type(e).__name__}: {e}"
        break
    return eintrag


def veranstalter_nachziehen(max_stuecke: int = 150, sicherung: bool = False, probe: bool = False,
                            max_sekunden: int | None = None) -> int:
    """
    Beschreibungen für Veranstalter-Events aus der eigenen Event-Seite – ein Text pro Stück, für alle Termine.
    probe=True: nichts schreiben, nur Bericht (data/beschreibung_quellen/probe_veranstalter.md).
    max_sekunden: Zeitbudget (im Scraper-Lauf, der Workflow hat insgesamt 45 Minuten) – danach aufhören,
    der Rest kommt im nächsten Lauf (noch nicht gesuchte Termine bleiben offen).

    Returns:
        Anzahl der Termine mit neuer Beschreibung
    """
    import anthropic
    from datetime import datetime, timezone

    from database.client import get_supabase_client

    db = get_supabase_client()
    stuecke = stuecke_bilden(offene_veranstalter_events(db))
    if probe:
        # Breite Stichprobe: je Quelle höchstens zwei Stücke
        gewaehlt, je_quelle = [], {}
        for st in stuecke:
            q = st[0].get("quelle_name")
            if je_quelle.get(q, 0) < 2:
                gewaehlt.append(st)
                je_quelle[q] = je_quelle.get(q, 0) + 1
        stuecke = gewaehlt
    stuecke = stuecke[:max_stuecke]
    if not stuecke:
        logger.info("Beschreibungen: keine offenen Veranstalter-Events")
        return 0
    client = anthropic.Anthropic()
    sicherungsdatei = ORDNER / f"sicherung_veranstalter_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
    ergebnisse, neu = [], 0
    beginn = time.monotonic()
    for nr, stueck in enumerate(stuecke, 1):
        if max_sekunden and time.monotonic() - beginn > max_sekunden:
            logger.info("Beschreibungen (Veranstalter): Zeitbudget erreicht nach %d Stücken", nr - 1)
            break
        logger.info("Stück [%d/%d]: %s (%s, %d Termine)", nr, len(stuecke), stueck[0]["titel"][:50],
                    stueck[0].get("ort"), len(stueck))
        try:
            eintrag = stueck_bearbeiten(client, stueck)
        except Exception as e:
            logger.error("Beschreibung für '%s' fehlgeschlagen: %s", stueck[0]["titel"][:40], e)
            continue
        eintrag["quelle_name"] = stueck[0].get("quelle_name")
        ergebnisse.append(eintrag)
        if probe:
            continue
        jetzt = datetime.now(timezone.utc).isoformat()
        for e in stueck:
            update = {"beschreibung_gesucht_am": jetzt}
            if eintrag.get("freigegeben") and ersetzen_erlaubt(e.get("beschreibung"), eintrag["beschreibung"]):
                update["beschreibung"] = eintrag["beschreibung"].strip()
                update["beschreibung_quelle"] = eintrag["quelle_url"]
            try:
                if sicherung and "beschreibung" in update:
                    ORDNER.mkdir(parents=True, exist_ok=True)
                    with sicherungsdatei.open("a", encoding="utf-8") as f:
                        f.write(json.dumps({"id": e["id"], "beschreibung": e.get("beschreibung")}, ensure_ascii=False) + "\n")
                db.table("events").update(update).eq("id", e["id"]).execute()
                neu += "beschreibung" in update
            except Exception as ex:
                logger.error("Speichern der Beschreibung für '%s' fehlgeschlagen: %s", e["titel"][:40], ex)
    if probe:
        bericht_schreiben(ergebnisse, datei="probe_veranstalter.md", art="Veranstalter-Stücke")
    logger.info("Beschreibungen (Veranstalter): %d Termine mit neuem Text aus %d Stücken", neu, len(stuecke))
    return neu


def nur_umschreiben() -> None:
    """Gefundene Quellen aus probe.json erneut umschreiben (ohne neue Suche/Abrufe)."""
    import anthropic

    client = anthropic.Anthropic()
    ergebnisse = json.loads((ORDNER / "probe.json").read_text(encoding="utf-8"))
    for e in ergebnisse:
        if e.get("quelltext"):
            for feld in ("passt", "grund", "beschreibung", "belege", "nachgebessert", "fehler"):
                e.pop(feld, None)
            try:
                e.update(umschreiben(client, e, e["quelle_url"], e["quelltext"]))
            except Exception as ex:
                e["fehler"] = f"{type(ex).__name__}: {ex}"
    (ORDNER / "probe.json").write_text(json.dumps(ergebnisse, ensure_ascii=False, indent=1), encoding="utf-8")
    bericht_schreiben(ergebnisse)


def bericht_schreiben(ergebnisse: list[dict], datei: str = "probe.md", art: str = "Rausgegangen-Events") -> None:
    """Markdown zum Gegenlesen: alter Text, Quelle, neuer Text, Prüfwerte."""
    ORDNER.mkdir(parents=True, exist_ok=True)
    frei = [e for e in ergebnisse if e.get("freigegeben")]
    zeilen = [f"# Probelauf Event-Beschreibungen ({len(ergebnisse)} {art})\n",
              f"- Quelle gefunden: {sum(1 for e in ergebnisse if e.get('quelle_url'))}",
              f"  - über Website des Orts: {sum(1 for e in ergebnisse if e.get('weg') == 'Website des Orts')}",
              f"  - über Websuche: {sum(1 for e in ergebnisse if e.get('weg') == 'Websuche')}",
              f"  - Event-Seite des Veranstalters: {sum(1 for e in ergebnisse if e.get('quelle_url') and e.get('weg') == 'Event-Seite des Veranstalters')}",
              f"- Neuer Text freigegeben (passt, belegt, eigener Wortlaut): {len(frei)}\n"]
    for e in ergebnisse:
        zeilen.append(f"## {e['titel']}\n{e['datum']} · {e['ort']}" + (f" · {e['quelle_name']}" if e.get("quelle_name") else "")
                      + (f" · {e['termine']} Termine" if e.get("termine") else "") + "\n")
        zeilen.append(f"**Bisher:** {e.get('bisher') or '–'}\n")
        if not e.get("quelle_url"):
            zeilen.append(f"**Keine Quelle gefunden** (Website des Orts: {e.get('ort_website') or 'keine'})\n")
            continue
        zeilen.append(f"**Quelle ({e['weg']}):** {e['quelle_url']}\n")
        if e.get("fehler"):
            zeilen.append(f"**Fehler:** {e['fehler']}\n")
            continue
        status = ("✅ freigegeben" if e.get("freigegeben") else "❌ nicht freigegeben") +             (" (nachgebessert)" if e.get("nachgebessert") else "")
        zeilen.append(f"**{status}** – passt: {e.get('passt')}, Belege: {e.get('belege_ok')}/{e.get('belege_gesamt')}, "
                      f"längste wörtliche Übernahme: {e.get('uebernahme_woerter')} Wörter. {e.get('grund') or ''}\n")
        if e.get("beschreibung"):
            zeilen.append("**Neu:**\n\n" + "\n".join("> " + z for z in e["beschreibung"].splitlines()) + "\n")
    (ORDNER / datei).write_text("\n".join(zeilen), encoding="utf-8")
    print("\n".join(zeilen[:6]))
    print(f"Bericht: {ORDNER / datei}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Event-Beschreibungen aus Veranstalter-Quellen (Probelauf)")
    parser.add_argument("--probe", type=int, default=20, help="Anzahl Events im Probelauf")
    parser.add_argument("--nur-umschreiben", action="store_true", help="Quellen des letzten Probelaufs neu umschreiben")
    parser.add_argument("--nachziehen", type=int, metavar="N",
                        help="N offene Rausgegangen-Events bearbeiten und in die Datenbank schreiben (mit Sicherung)")
    parser.add_argument("--probe-veranstalter", type=int, metavar="N", help="Probelauf: N Veranstalter-Stücke, schreibt nichts")
    parser.add_argument("--veranstalter", type=int, metavar="N",
                        help="N offene Veranstalter-Stücke bearbeiten und in die Datenbank schreiben (mit Sicherung)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for laut in ("httpx", "anthropic"):
        logging.getLogger(laut).setLevel(logging.WARNING)
    if args.probe_veranstalter:
        veranstalter_nachziehen(max_stuecke=args.probe_veranstalter, probe=True)
    elif args.veranstalter:
        veranstalter_nachziehen(max_stuecke=args.veranstalter, sicherung=True)
    elif args.nachziehen:
        beschreibungen_nachziehen(limit=args.nachziehen, sicherung=True)
    elif args.nur_umschreiben:
        nur_umschreiben()
    else:
        probe(args.probe)


if __name__ == "__main__":
    main()
