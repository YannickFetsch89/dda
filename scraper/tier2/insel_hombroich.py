"""
insel_hombroich.py – DiesDasDüsseldorf
Scraper für die Stiftung Insel Hombroich in Neuss (Museum Insel Hombroich und Raketenstation Hombroich).
Quelle: WordPress-Plugin „The Events Calendar“, REST-API https://www.inselhombroich.de/wp-json/tribe/events/v1/events
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V1, Welle A).

robots.txt (geprüft am 24.11.2026): „User-agent: * / Disallow: /wp-admin/ / Allow: /wp-admin/admin-ajax.php“ –
die REST-API (/wp-json/…) ist erlaubt, kein Crawl-delay. Wir halten mindestens 2 s zwischen den Anfragen ein.

Besonderheiten der API:
- Die Website ist zweisprachig (WPML): jeder Termin steht einmal deutsch und einmal englisch in der API. Wir fragen
  nur die deutschen Veranstaltungs-Kategorien ab (KATEGORIEN_DE: „Veranstaltung“ mit allen Unterkategorien wie
  Konzert, Lesung, Führung, Screening, Offenes Gastatelier sowie „Führung“) und verwerfen beim Lesen zusätzlich alles,
  was eine englische Kategorie trägt („event“, „ausstellung-en“, „permanent-exhibition“ oder Elternkategorie 71).
- Ausstellungen stehen als täglicher Eintrag mit Öffnungszeiten im Kalender (z. B. „Wachhaus #23“ jeden Tag
  10–18 Uhr). Das sind keine Einzeltermine – Einträge nur mit Ausstellungs-Kategorie werden ausgelassen.
- Die Veranstaltungsorte haben in der API keine Adresse, nur Namen wie „Turmgebäude, Raketenstation“. Steht
  „Raketenstation“ im Ortsnamen, ist der Ort „Raketenstation Hombroich“, sonst „Museum Insel Hombroich“. Adressen von
  der Anreise-Seite der Website (/de/besuch/anreise/, 24.11.2026).
- Orte fremder Häuser (Skulpturenhalle Neuss der Thomas Schütte Stiftung, Langen Foundation) werden ausgelassen –
  sie gehören weder zum Museum noch zur Raketenstation (bisher nur Ausstellungen dort).

Erstellt: 2026-11-24
"""
import json
import logging
import re
from datetime import date
from typing import Optional
from urllib.parse import urlparse

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen
from scraper.utils.wp_tribe import PFAD, PRO_SEITE, termin_aus_tribe

logger = logging.getLogger(__name__)

QUELLE_NAME = "Insel Hombroich"
BASIS_URL = "https://www.inselhombroich.de"
PROGRAMM_URL = "https://www.inselhombroich.de/de/besuch/kalender/"

ORT_RAKETENSTATION = "Raketenstation Hombroich"
ADRESSE_RAKETENSTATION = "Raketenstation Hombroich 4, 41472 Neuss"
ORT_MUSEUM = "Museum Insel Hombroich"
ADRESSE_MUSEUM = "Minkel 2, 41472 Neuss"

# Deutsche Kategorien in der Tribe-API: 22 = „Veranstaltung“ (die API liefert Unterkategorien mit), 43 = „Führung“
KATEGORIEN_DE = "22,43"
# Englische Kategorien (zweite Sprachfassung desselben Termins)
SLUGS_ENGLISCH = {"event", "ausstellung-en", "permanent-exhibition"}
ELTERN_ENGLISCH = 71
# Reine Ausstellungs-Kategorien (tägliche Öffnungszeiten, keine Einzeltermine)
SLUGS_AUSSTELLUNG = {"ausstellung-de", "ausstellung-en", "dauerausstellung", "permanent-exhibition"}
# Orte anderer Häuser, die im Kalender der Stiftung mit auftauchen
FREMDE_ORTE = re.compile(r"skulpturenhalle|langen foundation", re.I)

MAX_SEITEN = 15
WARTEZEIT = 2.0

_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus|cancelled|canceled)\b", re.I)


def _kategorien(e: dict) -> list[dict]:
    return [c for c in (e.get("categories") or []) if isinstance(c, dict)]


def _ist_englisch(e: dict) -> bool:
    """True, wenn der Eintrag die englische Sprachfassung ist."""
    return any(c.get("slug") in SLUGS_ENGLISCH or c.get("parent") == ELTERN_ENGLISCH for c in _kategorien(e))


def _nur_ausstellung(e: dict) -> bool:
    """True, wenn der Eintrag ausschließlich Ausstellungs-Kategorien trägt (Öffnungstag einer Ausstellung)."""
    slugs = {c.get("slug") for c in _kategorien(e)}
    return bool(slugs) and slugs <= SLUGS_AUSSTELLUNG


def _ortsnamen(e: dict) -> list[str]:
    """Alle Ortsnamen des Eintrags (venue ist ein Objekt, eine Liste von Objekten oder leer)."""
    venue = e.get("venue")
    liste = venue if isinstance(venue, list) else [venue] if isinstance(venue, dict) else []
    return [str(v.get("venue") or "").strip() for v in liste if isinstance(v, dict) and v.get("venue")]


def _ort_und_adresse(e: dict) -> Optional[tuple[str, str]]:
    """(ort, adresse) nach der Regel Raketenstation/Museum – None bei Orten fremder Häuser."""
    namen = _ortsnamen(e)
    if any("raketenstation" in n.lower() for n in namen):
        return ORT_RAKETENSTATION, ADRESSE_RAKETENSTATION
    if any(FREMDE_ORTE.search(n) for n in namen):
        return None
    return ORT_MUSEUM, ADRESSE_MUSEUM


def _kategorie(titel: str, e: dict) -> str:
    """Kinder/Familie → family, Konzerte → musik, Workshops → community, sonst (Führungen, Lesungen …) kultur."""
    slugs = {c.get("slug") for c in _kategorien(e)}
    t = titel.lower()
    if re.search(r"kinder|famili", t):
        return "family"
    if "konzert" in slugs or re.search(r"konzert|festival", t):
        return "musik"
    if re.search(r"workshop|werkstatt|mitmach", t):
        return "community"
    return "kultur"


def _eigenes_bild(url: Optional[str]) -> Optional[str]:
    """Nur Bilder von der Website der Stiftung übernehmen."""
    if not url:
        return None
    host = urlparse(url).netloc.lower()
    return url if host == "inselhombroich.de" or host.endswith(".inselhombroich.de") else None


def _termine_aus_api(events: list[dict], heute: date, enddatum: date) -> list[dict]:
    """Rohe Einträge der Tribe-API → Event-Dicts im Projektformat (nur deutsche Einzeltermine im Zeitfenster)."""
    ergebnis: list[dict] = []
    gesehen: set[tuple] = set()
    for e in events:
        if not isinstance(e, dict):
            continue
        if e.get("status") not in (None, "publish") or e.get("hide_from_listings"):
            continue
        if _ist_englisch(e) or _nur_ausstellung(e):
            continue
        roh = termin_aus_tribe(e)
        if not roh:
            continue
        titel = roh["titel"]
        if _ABGESAGT.search(titel):
            logger.debug("Insel Hombroich: abgesagt, ausgelassen: %s", titel)
            continue
        try:
            start = date.fromisoformat(roh["start"])
        except ValueError:
            continue
        if start < heute or start > enddatum:
            continue
        ort_adresse = _ort_und_adresse(e)
        if not ort_adresse:
            logger.debug("Insel Hombroich: Ort eines anderen Hauses, ausgelassen: %s (%s)", titel, _ortsnamen(e))
            continue
        ort, adresse = ort_adresse
        uhrzeit = roh["uhrzeit"]
        if uhrzeit == "00:00":
            uhrzeit = None
        schluessel = (titel.lower(), roh["start"], uhrzeit)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        datum_bis = roh["ende"] if roh.get("ende") and roh["ende"] > roh["start"] else None
        event = {
            "titel": titel,
            "datum": roh["start"],
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": adresse,
            "kategorie": _kategorie(titel, e),
            "beschreibung": None,
            "preis": roh.get("preis"),
            "quelle_name": QUELLE_NAME,
            "quelle_url": roh.get("url") or PROGRAMM_URL,
            "bild_url": _eigenes_bild(roh.get("bild_url")),
            "bild_generiert": False,
            "status": "neu",
        }
        if datum_bis:
            event["datum_bis"] = datum_bis
        ergebnis.append(event)
    return ergebnis


def _api_abrufen(von: date, bis: date) -> Optional[list[dict]]:
    """Alle deutschen Veranstaltungs-Einträge zwischen von und bis (seitenweise, höchstens MAX_SEITEN Anfragen).
    None, wenn schon die erste Seite nicht erreichbar war."""
    alle: list[dict] = []
    for seite in range(1, MAX_SEITEN + 1):
        url = (f"{BASIS_URL}{PFAD}?start_date={von.isoformat()}&end_date={bis.isoformat()}"
               f"&per_page={PRO_SEITE}&page={seite}&categories={KATEGORIEN_DE}")
        text = seite_abrufen(url, logger, wartezeit=WARTEZEIT)
        if text is None:
            return None if seite == 1 else alle
        try:
            daten = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Insel Hombroich: keine JSON-Antwort von %s", url)
            return None if seite == 1 else alle
        alle.extend(daten.get("events") or [])
        if seite >= int(daten.get("total_pages") or 1):
            break
    return alle


def scrape() -> list[dict]:
    """Scrapt die Veranstaltungen der Stiftung Insel Hombroich (Museum Insel und Raketenstation)."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        roh = _api_abrufen(heute, enddatum)
        if roh is None:
            logger.error("Scraper %s: Tribe-API nicht erreichbar", QUELLE_NAME)
            return []
        events = _termine_aus_api(roh, heute, enddatum)
        if not events:
            logger.warning("Scraper %s: 0 Termine bei erreichbarer API (%d Rohdaten) – Seitenstruktur geändert?",
                           QUELLE_NAME, len(roh))
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
