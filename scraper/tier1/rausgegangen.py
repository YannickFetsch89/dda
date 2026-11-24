"""
rausgegangen.py – DiesDasDüsseldorf
Scraper für Rausgegangen.de: Events in Düsseldorf
Verwendet Playwright wegen Cloudflare-Schutz.

Abgerufen wird nur die Startseite (rausgegangen.de/duesseldorf/). Die robots.txt sperrt alle anderen Seiten
für unbekannte Crawler („User-agent: * / Disallow: /“); Detail-, Datums- oder Kategorie-Seiten rufen wir
deshalb nicht ab (Entscheidung C4, docs/plan-clubs-2026-11-11.md). Spätere Termine fehlen dadurch teils.

Adressen: Steht in der Kachel „Ort, Straße Nr, PLZ Stadt“, wird das in ort und adresse getrennt
(_ort_adresse_trennen). Alle übrigen Adressen ergänzt die Pipeline aus eigenen Daten
(pipeline/adressen_ergaenzen.py).
"""
import logging
import re
import time
from datetime import date, datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from config import vorschau_ende

logger = logging.getLogger(__name__)

BASE_URL = "https://rausgegangen.de"
LISTE_URL = "https://rausgegangen.de/duesseldorf/"
QUELLE_NAME = "Rausgegangen"

KATEGORIE_MAPPING = {
    "party": "nightlife",
    "club": "nightlife",
    "konzert": "musik",
    "musik": "musik",
    "live": "musik",
    "shows": "kultur",
    "theater": "kultur",
    "ausstellung": "kultur",
    "kunst": "kultur",
    "kino": "kultur",
    "film": "kultur",
    "oper": "kultur",
    "comedy": "kultur",
    "performance": "kultur",
    "sport": "sport",
    "outdoor": "outdoor",
    "natur": "outdoor",
    "food": "food",
    "markt": "food",
    "essen": "food",
    "aktiv": "community",
    "kreativ": "community",
    "workshop": "community",
    "meetup": "community",
    "networking": "community",
    "kinder": "family",
    "familie": "family",
    "dating": "dating",
    "singles": "dating",
}


def _datum_parsen(datum_text: str) -> Optional[str]:
    heute = date.today()
    if not datum_text:
        return None

    datum_text = datum_text.strip().lower()
    # Pipe-Teil (Uhrzeit) abschneiden
    datum_teil = datum_text.split("|")[0].strip()

    try:
        if datum_teil.startswith("heute"):
            return heute.isoformat()
        if datum_teil.startswith("morgen"):
            return (heute + timedelta(days=1)).isoformat()

        monat_map = {
            "jan": 1, "feb": 2, "mär": 3, "apr": 4,
            "mai": 5, "jun": 6, "jul": 7, "aug": 8,
            "sep": 9, "okt": 10, "nov": 11, "dez": 12,
        }

        teile = datum_teil.split(",")
        rest = teile[-1].strip() if len(teile) > 1 else datum_teil
        woerter = rest.split()
        if len(woerter) >= 2:
            tag = int(woerter[0].replace(".", ""))
            monat = monat_map.get(woerter[1][:3].lower())
            if monat is None:
                return None
            jahr = heute.year
            kandidat = date(jahr, monat, tag)
            if kandidat < heute - timedelta(days=1):
                kandidat = date(jahr + 1, monat, tag)
            return kandidat.isoformat()
    except (ValueError, IndexError):
        return None
    return None


def _uhrzeit_parsen(datum_text: str) -> Optional[str]:
    if "|" not in datum_text:
        return None
    try:
        uhrzeit_teil = datum_text.split("|")[1].strip()
        uhrzeit = uhrzeit_teil.replace("Uhr", "").strip()
        datetime.strptime(uhrzeit, "%H:%M")
        return uhrzeit
    except (ValueError, IndexError):
        return None


# Kachel-Ortsangaben, die eine Adresse enthalten (Beispiele aus der Startseite vom 18.11.2026):
#   „Flow, Mertensgasse 2, 40213 Düsseldorf“                 → Flow | Mertensgasse 2, 40213 Düsseldorf
#   „Cafe Bar La Paillette, Schirmerstraße 2, 40211 Düsseldorf-Stadtbezirk 1“
#   „Burgplatz 5-6, Düsseldorf“                              → Burgplatz 5-6 | Burgplatz 5-6, Düsseldorf
#   „Franklinstraße 41, Düsseldorf-Stadtbezirk 1, Deutschland“
#   „Düsseldorf, Schadowstraße“                              → Schadowstraße | Schadowstraße, Düsseldorf
#   „Radisson Blu Media Harbour Hotel, Düsseldorf“           → Radisson Blu Media Harbour Hotel | (keine)
# Unverändert bleiben Namen mit Komma ohne Adresse („zakk - Zentrum für Aktion, Kultur und Kommunikation“,
# „Nilsson, Initiativen Haus“, „Heinrich-Heine-Universität Düsseldorf, Hörsaal 3A“).
_STAEDTE = r"D(?:ü|ue|u)sseldorf|Neuss|Ratingen"
_STADT_TEIL = re.compile(rf"^(?:{_STAEDTE})(?:[-\s]+Stadtbezirk\s+\d+)?$", re.IGNORECASE)
_PLZ_STADT_TEIL = re.compile(r"^(\d{5})\s+(\S.*?)(?:[-\s]+Stadtbezirk\s+\d+)?$", re.IGNORECASE)
_LAND_TEIL = re.compile(r"^(?:Deutschland|Germany)$", re.IGNORECASE)
# Straße mit Hausnummer: „Mertensgasse 2“, „Burgplatz 5-6“, „Kölner Str. 12a“
_STRASSE_NR_TEIL = re.compile(r"^[A-ZÄÖÜa-zäöüß][\wÄÖÜäöüß.' -]*?\s\d{1,4}\s?[a-zA-Z]?(?:\s?[-–/]\s?\d{1,4}[a-zA-Z]?)?$")
# Straße ohne Hausnummer (nur nach „Düsseldorf, …“): „Schadowstraße“, „Corneliusplatz“, „Königsallee“
_STRASSE_TEIL = re.compile(
    r"^[A-ZÄÖÜ][\wÄÖÜäöüß.' -]*(?:straße|strasse|str\.|platz|allee|gasse|markt|weg|ufer|ring|damm|wall|promenade)$",
    re.IGNORECASE,
)


def _stadt_vereinheitlichen(stadt: str) -> str:
    """„Dusseldorf“/„Duesseldorf“ → „Düsseldorf“ (Neuss, Ratingen bleiben)."""
    return "Düsseldorf" if re.fullmatch(r"D(?:ü|ue|u)sseldorf", stadt, re.IGNORECASE) else stadt


def _ort_adresse_trennen(text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Trennt die Ortsangabe einer Kachel in (ort, adresse). Ohne erkennbare Adresse bleibt der Text als Ort
    stehen und die Adresse ist None. Eine Adresse entsteht nur mit Hausnummer oder PLZ – oder bei
    „Düsseldorf, <Straße/Platz>“ (Straßenname reicht für die Stadtteil-Zuordnung).
    """
    if not text:
        return text, None
    text = re.sub(r"\s+", " ", text).strip()
    teile = [t.strip() for t in text.split(",") if t.strip()]
    if len(teile) < 2:
        return text, None

    # Land am Ende weglassen
    while len(teile) > 1 and _LAND_TEIL.match(teile[-1]):
        teile.pop()

    # „Düsseldorf, Schadowstraße“ / „Düsseldorf, Hauptbahnhof“: Stadt vorne
    if len(teile) == 2 and _STADT_TEIL.match(teile[0]):
        rest = teile[1]
        if _STRASSE_TEIL.match(rest) or _STRASSE_NR_TEIL.match(rest):
            return rest, f"{rest}, {_stadt_vereinheitlichen(teile[0])}"
        # „Düsseldorf, Hauptbahnhof“, „Düsseldorf, Volksgarten“: bleibt (pipeline/ortsnamen.py kennt die Schreibweise)
        return text, None

    # Stadt hinten: „PLZ Stadt“ oder nur „Stadt“
    stadt = None
    m = _PLZ_STADT_TEIL.match(teile[-1])
    if m:
        stadt = f"{m.group(1)} {_stadt_vereinheitlichen(m.group(2).strip())}"
        teile.pop()
    elif _STADT_TEIL.match(teile[-1]):
        stadt = _stadt_vereinheitlichen(re.split(r"[-\s]+Stadtbezirk", teile[-1], flags=re.IGNORECASE)[0].strip())
        teile.pop()
    if stadt is None or not teile:
        return text, None

    strasse = teile[-1] if _STRASSE_NR_TEIL.match(teile[-1]) else None
    if strasse:
        name = ", ".join(teile[:-1]) or strasse
        return name, f"{strasse}, {stadt}"
    name = ", ".join(teile)
    # „Name, 40213 Düsseldorf“: PLZ ohne Straße ist noch eine brauchbare Adresse
    return name, (stadt if m else None)


def _kategorie_erkennen(kategorie_text: str) -> str:
    if not kategorie_text:
        return "sonstiges"
    schluessel = kategorie_text.strip().lower()
    for keyword, kategorie in KATEGORIE_MAPPING.items():
        if keyword in schluessel:
            return kategorie
    return "sonstiges"


def _seite_laden() -> Optional[str]:
    """Lädt die Rausgegangen-Seite mit Playwright (Cloudflare-Bypass)."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="de-DE",
            )
            page = context.new_page()
            page.goto(LISTE_URL, timeout=60000)
            time.sleep(8)
            page.wait_for_selector("[data-testid='event-tile-link']", timeout=15000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        logger.error("Playwright-Fehler beim Laden von %s: %s", LISTE_URL, e)
        return None


def _event_aus_karte(karte, heute: date) -> Optional[dict]:
    try:
        pfad = karte.get("href", "")
        if not pfad:
            return None
        quelle_url = BASE_URL + pfad if pfad.startswith("/") else pfad

        titel_el = karte.select_one("[data-testid='event-tile-name']")
        if not titel_el:
            return None
        titel = titel_el.get_text(strip=True)
        if not titel:
            return None

        datum_el = karte.select_one("[data-testid='event-tile-datetime']")
        datum_text = datum_el.get_text(strip=True) if datum_el else None
        datum = _datum_parsen(datum_text) if datum_text else None
        if not datum:
            return None

        if date.fromisoformat(datum) < heute:
            return None

        uhrzeit = _uhrzeit_parsen(datum_text) if datum_text else None

        ort_el = karte.select_one("p.text-bw-medium")
        ort, adresse = _ort_adresse_trennen(ort_el.get_text(strip=True) if ort_el else None)
        if not ort:
            return None

        preis_el = karte.select_one("p.text-primary")
        preis = preis_el.get_text(strip=True) if preis_el else None

        kat_el = karte.select_one("[data-testid='badge-category']")
        kategorie_text = kat_el.get_text(strip=True) if kat_el else ""
        kategorie = _kategorie_erkennen(kategorie_text)

        bild_url = None
        img_el = karte.select_one("picture source")
        if img_el:
            srcset = img_el.get("srcset", "")
            if srcset:
                bild_url = srcset.split(",")[0].split(" ")[0]
        if not bild_url:
            img_tag = karte.select_one("img")
            if img_tag:
                bild_url = img_tag.get("src")

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": adresse,
            "kategorie": kategorie,
            "beschreibung": None,
            "preis": preis,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        }
    except Exception as e:
        logger.error("Fehler beim Parsen einer Event-Karte: %s", str(e))
        return None


def scrape(ziel_datum: Optional[date] = None, html: Optional[str] = None) -> list[dict]:
    """
    Events der Rausgegangen-Startseite. html: bereits geladene Seite (Probelauf/Tests) – dann kein Abruf.
    """
    events = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    if html is None:
        html = _seite_laden()
    if html is None:
        return []

    soup = BeautifulSoup(html, "html.parser")
    karten = soup.select("a.event-tile")
    logger.info("%d Event-Karten gefunden", len(karten))

    gesehene_urls: set[str] = set()
    for karte in karten:
        url = karte.get("href", "")
        if url in gesehene_urls:
            continue
        gesehene_urls.add(url)
        event = _event_aus_karte(karte, heute)
        if event:
            events.append(event)

    enddatum = vorschau_ende(QUELLE_NAME, heute)
    events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]

    logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
    return events


def probelauf(html_datei: Optional[str] = None, html_speichern: Optional[str] = None) -> None:
    """
    Probelauf ohne Schreiben: Startseite (oder gespeichertes HTML) lesen, Adressen aus eigenen Daten ergänzen
    (liest die Datenbank), Stadtteile zuordnen und zählen. Pro Lauf höchstens ein Rausgegangen-Abruf.
    """
    import re as _re
    from collections import Counter

    from pipeline.adressen_ergaenzen import adressen_schritt
    from pipeline.stadtteil_mapper import stadtteil_batch_zuordnen

    html = None
    if html_datei:
        with open(html_datei, encoding="utf-8") as f:
            html = f.read()
    else:
        html = _seite_laden()
        if html and html_speichern:
            with open(html_speichern, "w", encoding="utf-8") as f:
                f.write(html)
    events = scrape(html=html) if html else []
    aus_kachel = sum(1 for e in events if e.get("adresse"))
    # Wie im Lauf (main.py): erst Ortszuordnung (1d, setzt ort_id), dann Adressen (1e2), dann Stadtteile (1f)
    try:
        from database.client import get_supabase_client
        from pipeline.ort_zuordnung import index_laden, zuordnen_alle
        zuordnen_alle(events, index_laden(get_supabase_client()))
    except Exception as e:
        print(f"  Ortszuordnung nicht möglich (weiter ohne ort_id): {e}")
    adressen_schritt(events)
    stadtteil_batch_zuordnen(events)

    plz = _re.compile(r"\b4[01]\d{3}\b")
    print(f"\n=== Probelauf Rausgegangen: {len(events)} Events ===")
    print(f"  mit Adresse:        {sum(1 for e in events if e.get('adresse'))} (davon aus der Kachel: {aus_kachel})")
    print(f"  mit PLZ:            {sum(1 for e in events if plz.search(e.get('adresse') or ''))}")
    print(f"  mit Stadtteil:      {sum(1 for e in events if e.get('stadtteil'))}")
    print(f"  Adresse oder Stadtteil: {sum(1 for e in events if e.get('adresse') or e.get('stadtteil'))}")
    ohne = Counter(e["ort"] for e in events if not e.get("adresse"))
    print("  häufigste Orte ohne Adresse:", ", ".join(f"{o} ({n})" for o, n in ohne.most_common(12)))
    weihnacht = [e for e in events if _re.search(r"weihnacht|advent|veihnacht", e["titel"], _re.IGNORECASE)]
    print(f"\n  Weihnachts-/Adventsevents: {len(weihnacht)}")
    for e in sorted(weihnacht, key=lambda e: e["datum"]):
        print(f"    {e['datum']} | {e['titel'][:55]:55} | {e['ort'][:28]:28} | {e.get('adresse') or '-'} | {e.get('stadtteil') or '-'}")


if __name__ == "__main__":
    import argparse
    import json

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Rausgegangen-Scraper")
    parser.add_argument("--probe", action="store_true", help="Probelauf mit Adressen und Zählung, schreibt nichts")
    parser.add_argument("--html", help="gespeicherte Startseite lesen statt abrufen")
    parser.add_argument("--html-speichern", help="abgerufene Startseite zusätzlich speichern")
    args = parser.parse_args()

    if args.probe:
        from dotenv import load_dotenv
        load_dotenv()
        probelauf(args.html, args.html_speichern)
    else:
        ergebnisse = scrape()
        print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
        for e in ergebnisse[:5]:
            print(json.dumps(e, ensure_ascii=False, indent=2))
            print()
