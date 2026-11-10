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

Aufruf (Probelauf, schreibt nichts in die Datenbank):
    python -m pipeline.beschreibung_quellen --probe 20
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
    from scraper.orte.google_places import API_BASE, _headers

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
    WEBSITE_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
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


def probe(anzahl: int) -> None:
    import anthropic

    ORDNER.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic()
    webseiten, cache = orte_webseiten(), _cache_laden()
    ergebnisse = []
    for nr, event in enumerate(stichprobe(anzahl), 1):
        logger.info("[%d/%d] %s (%s)", nr, anzahl, event["titel"][:50], event.get("ort"))
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
        ergebnisse.append(eintrag)
        (ORDNER / "probe.json").write_text(json.dumps(ergebnisse, ensure_ascii=False, indent=1), encoding="utf-8")
    bericht_schreiben(ergebnisse)


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


def bericht_schreiben(ergebnisse: list[dict]) -> None:
    """Markdown zum Gegenlesen: alter Text, Quelle, neuer Text, Prüfwerte."""
    frei = [e for e in ergebnisse if e.get("freigegeben")]
    zeilen = [f"# Probelauf Event-Beschreibungen ({len(ergebnisse)} Rausgegangen-Events)\n",
              f"- Quelle gefunden: {sum(1 for e in ergebnisse if e.get('quelle_url'))}",
              f"  - über Website des Orts: {sum(1 for e in ergebnisse if e.get('weg') == 'Website des Orts')}",
              f"  - über Websuche: {sum(1 for e in ergebnisse if e.get('weg') == 'Websuche')}",
              f"- Neuer Text freigegeben (passt, belegt, eigener Wortlaut): {len(frei)}\n"]
    for e in ergebnisse:
        zeilen.append(f"## {e['titel']}\n{e['datum']} · {e['ort']}\n")
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
    (ORDNER / "probe.md").write_text("\n".join(zeilen), encoding="utf-8")
    print("\n".join(zeilen[:5]))
    print(f"Bericht: {ORDNER / 'probe.md'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Event-Beschreibungen aus Veranstalter-Quellen (Probelauf)")
    parser.add_argument("--probe", type=int, default=20, help="Anzahl Events im Probelauf")
    parser.add_argument("--nur-umschreiben", action="store_true", help="Quellen des letzten Probelaufs neu umschreiben")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for laut in ("httpx", "anthropic"):
        logging.getLogger(laut).setLevel(logging.WARNING)
    if args.nur_umschreiben:
        nur_umschreiben()
    else:
        probe(args.probe)


if __name__ == "__main__":
    main()
