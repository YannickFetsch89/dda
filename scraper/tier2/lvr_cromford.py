"""
lvr_cromford.py – DiesDasDüsseldorf
Scraper für das LVR-Industriemuseum Textilfabrik Cromford in Ratingen.
Quelle: Suchschnittstelle hinter dem Veranstaltungskalender
https://www.lvr.de/industriemuseum/textilfabrik-cromford/programm/veranstaltungskalender/ – die Seite lädt die Termine
per JavaScript aus https://www.lvr.de/industriemuseum/.elasticsearch (Index „gomus_industriemuseum_dates“, Filter
museum.id = 86 = Textilfabrik Cromford, so in der Seite voreingestellt). Die Website des Industriemuseums ist von
industriemuseum.lvr.de nach www.lvr.de/industriemuseum/ umgezogen.
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V2, Welle B).

robots.txt (www.lvr.de, geprüft am 25.11.2026): „User-agent: * / Disallow: /technical_pages/ / Disallow: /suche/“ –
/industriemuseum/ ist erlaubt, kein Crawl-delay. industriemuseum.lvr.de leitet robots.txt auf eine 404 um.
Der Browser schickt die Parameter per POST; dieselben Parameter als GET liefern dasselbe JSON (nur lesend, eine
Anfrage je Lauf).

- Nur der Schauplatz Ratingen (Cromford): der Filter museum.id 86 schließt die anderen LVR-Standorte aus.
- Die Schnittstelle liefert keine Detailseite je Termin (url = Startseite des Ticketshops
  www.shop.industriemuseum.lvr.de) – quelle_url ist deshalb der Veranstaltungskalender, ticket_url der Shop.
- Zeit: timestamp in Millisekunden (UTC) → Ortszeit Europe/Berlin.
- Bilder liegen im go~mus-Ticketsystem des LVR (lvr.gomus.de) und werden so auch im Kalender des Hauses gezeigt –
  übernommen werden nur Bilder von lvr.gomus.de und *.lvr.de.
- Ausstellungs-/Zeitfenster-Einträge (Kategorie mit „Ausstellung“, „Zeitfenster“, „Eintritt“) sind keine
  Einzeltermine und entfallen.
- Kategorie: Familie → family, Konzert → musik, Workshop → community, sonst (Führungen, Veranstaltungen) kultur.
- Präfix „Event: “ im Titel entfällt.

Erstellt: 2026-11-25
"""
import json
import logging
import re
from datetime import date, datetime, timezone
from typing import Optional
from urllib.parse import urlencode, urlparse
from zoneinfo import ZoneInfo

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ticket_link import ticket_link

logger = logging.getLogger(__name__)

QUELLE_NAME = "LVR-Industriemuseum Cromford"
KALENDER_URL = "https://www.lvr.de/industriemuseum/textilfabrik-cromford/programm/veranstaltungskalender/"
API_URL = "https://www.lvr.de/industriemuseum/.elasticsearch"
MUSEUM_ID = "86"  # Textilfabrik Cromford (voreingestellter Filter des Kalenders, 25.11.2026)
ORT = "LVR-Industriemuseum Textilfabrik Cromford"
ADRESSE = "Cromforder Allee 24, 40878 Ratingen"
WARTEZEIT = 2.0
ANZAHL = 100
FELDER = ["id", "eventId", "dates", "events", "title", "url", "timestamp", "description", "picture.title",
          "picture.article_3x2", "subTitle", "category", "audience"]

_BERLIN = ZoneInfo("Europe/Berlin")
_KEIN_TERMIN = re.compile(r"ausstellung|zeitfenster|eintritt", re.I)
_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus)\b", re.I)
_PRAEFIX = re.compile(r"^\s*event\s*:\s*", re.I)


def api_url() -> str:
    """Abfrage-URL wie im Kalender (Index, Filter Cromford, nach Zeit aufsteigend)."""
    return API_URL + "?" + urlencode({
        "q": "*", "i": "gomus_industriemuseum_dates", "from": 0, "size": ANZAHL, "lang": "de",
        "sort": "timestamp", "sort_order": "asc", "include_fields": ",".join(FELDER),
        "filters": json.dumps({"museum.id.terms": [MUSEUM_ID]}), "send_aggregations": "false",
    })


def _kategorie(titel: str, kategorie: str) -> str:
    t = f"{titel} {kategorie}".lower()
    if re.search(r"famili|kinder", t):
        return "family"
    if "konzert" in t:
        return "musik"
    if "workshop" in t:
        return "community"
    return "kultur"


def _eigenes_bild(url: Optional[str]) -> Optional[str]:
    if not url or not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return None
    host = urlparse(url).netloc.lower()
    return url if host in ("lvr.gomus.de", "lvr.de") or host.endswith(".lvr.de") else None


def _termine_aus_json(daten: dict, heute: date, enddatum: date) -> list[dict]:
    """Antwort der Suchschnittstelle → Event-Dicts im Projektformat (nur Termine zwischen heute und enddatum)."""
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for hit in (daten or {}).get("hits") or []:
        if not isinstance(hit, dict):
            continue
        titel = _PRAEFIX.sub("", re.sub(r"\s+", " ", str(hit.get("title") or ""))).strip()
        kategorie_haus = str(hit.get("category") or "")
        if not titel or _KEIN_TERMIN.search(kategorie_haus) or _ABGESAGT.search(titel):
            continue
        try:
            zeit = datetime.fromtimestamp(int(hit.get("timestamp")) / 1000, tz=timezone.utc).astimezone(_BERLIN)
        except (TypeError, ValueError, OverflowError):
            continue
        if not heute <= zeit.date() <= enddatum:
            continue
        datum = zeit.date().isoformat()
        uhrzeit = zeit.strftime("%H:%M")
        if uhrzeit == "00:00":
            uhrzeit = None
        schluessel = (titel.lower(), datum, uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        bild = hit.get("picture") if isinstance(hit.get("picture"), dict) else {}
        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT,
            "adresse": ADRESSE,
            "kategorie": _kategorie(titel, kategorie_haus),
            "beschreibung": None,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": KALENDER_URL,
            "ticket_url": ticket_link(hit.get("url")),
            "bild_url": _eigenes_bild(bild.get("article_3x2")),
            "bild_generiert": False,
            "status": "neu",
        })
    return events


def scrape() -> list[dict]:
    """Scrapt die Veranstaltungen der Textilfabrik Cromford (LVR-Industriemuseum, Ratingen)."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        text = seite_abrufen(api_url(), logger, wartezeit=WARTEZEIT)
        if text is None:
            logger.error("Scraper %s: Suchschnittstelle nicht erreichbar", QUELLE_NAME)
            return []
        try:
            daten = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Scraper %s: keine JSON-Antwort – Seitenstruktur geändert?", QUELLE_NAME)
            return []
        events = _termine_aus_json(daten, heute, enddatum)
        if not events:
            logger.warning("Scraper %s: 0 Termine bei erreichbarer Seite (%s Treffer) – Seitenstruktur geändert?",
                           QUELLE_NAME, daten.get("number_of_hits"))
        logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
        return events
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for ev in ergebnisse[:3]:
        print(json.dumps(ev, ensure_ascii=False, indent=2))
