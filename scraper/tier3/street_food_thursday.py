"""
street_food_thursday.py – DiesDasDüsseldorf
Scraper für den Street Food Thursday im Stahlwerk Düsseldorf.

Der Street Food Thursday ist ein monatliches Streetfood-Event im Stahlwerk &
Treibgut (Ronsdorfer Str. 134), seit 2014, kostenloser Eintritt, 17–22 Uhr.
Laut offizieller Website findet er "jeden ersten Donnerstag im Monat" statt,
und zwar saisonal (2026: Opening 5. März, Finale im Oktober). Im Winter ist
Saisonpause.

Strategie:
1. Offizielle Termine-Seite laden (streetfood-duesseldorf.de/termine)
   - Hinweis "Saison XXXX ist beendet" → Saisonpause, leere Liste (INFO-Log)
   - Konkrete Termine auf der Seite → diese übernehmen
2. Fallback (nur wenn die Seite nicht lesbar ist): erster Donnerstag im Monat,
   nur in den Saisonmonaten März–Oktober (WARNING-Log, da berechnet)

Quellen:
  - Offizielle Website: https://www.streetfood-duesseldorf.de/termine
  - Venue: https://stahlwerk.de

Erstellt: 2026-04-02
Überarbeitet: 2026-11-04 – Rhythmus auf 1. Donnerstag korrigiert (vorher 2.),
                            offizielle Termine-Seite statt Stahlwerk-Startseite,
                            Saisonende-Erkennung
"""
import logging
import re
from datetime import date, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

QUELLE_NAME = "Street Food Thursday Düsseldorf"
ORT_STANDARD = "Stahlwerk Düsseldorf"
ADRESSE_STANDARD = "Ronsdorfer Str. 134, 40233 Düsseldorf"
KATEGORIE_STANDARD = "food"
QUELLE_URL = "https://www.streetfood-duesseldorf.de/termine"

# Saisonmonate (2026: Opening 5. März, Finale Oktober)
EVENT_MONATE = [3, 4, 5, 6, 7, 8, 9, 10]

# Wochentag: Donnerstag (3 = Donnerstag in Python weekday())
EVENT_WOCHENTAG = 3

# Laut offizieller Website: "jeden ersten Donnerstag im Monat"
EVENT_WOCHE_IM_MONAT = 1

# Uhrzeit laut Veranstalter: 17:00–22:00 Uhr
EVENT_UHRZEIT = "17:00"

BESCHREIBUNG = (
    "Monatliches Streetfood-Event im Stahlwerk & Treibgut Düsseldorf: lokale und "
    "regionale Food Trucks und mobile Küchen, eigener veganer Bereich, DJ-Teams. "
    "Eintritt frei, 17–22 Uhr."
)

MONATE = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5,
    "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
    "november": 11, "dezember": 12,
}

# "Die Street Food Saison 2026 ist beendet"
SAISON_BEENDET_REGEX = re.compile(r"saison\s+(\d{4})\s+ist\s+beendet", re.IGNORECASE)

# "05.03.2026" / "5.3.2026" / "5. März 2026"
DATUM_NUMERISCH_REGEX = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")
DATUM_TEXT_REGEX = re.compile(r"\b(\d{1,2})\.\s*([a-zäöü]+)\s+(\d{4})\b", re.IGNORECASE)


def _n_ter_wochentag(jahr: int, monat: int, wochentag: int, n: int) -> date:
    """
    Berechnet den n-ten Wochentag eines Monats (z.B. 1. Donnerstag).

    Args:
        jahr:      Jahr
        monat:     Monat
        wochentag: Python-Wochentag (0 = Montag, 3 = Donnerstag)
        n:         1 = erster, 2 = zweiter, …

    Returns:
        Datum des n-ten Wochentags
    """
    erster_tag = date(jahr, monat, 1)
    erster_treffer = erster_tag + timedelta(days=(wochentag - erster_tag.weekday()) % 7)
    return erster_treffer + timedelta(weeks=n - 1)


def _berechnete_termine(heute: date, enddatum: date) -> list[date]:
    """
    Berechnet die Termine (n-ter Donnerstag im Monat) in den Saisonmonaten
    innerhalb des Zeitraums [heute, enddatum].

    Args:
        heute:    Heutiges Datum
        enddatum: Ende des Vorschauzeitraums

    Returns:
        Sortierte Liste von Terminen
    """
    termine = []
    jahr, monat = heute.year, heute.month
    while date(jahr, monat, 1) <= enddatum:
        if monat in EVENT_MONATE:
            termin = _n_ter_wochentag(jahr, monat, EVENT_WOCHENTAG, EVENT_WOCHE_IM_MONAT)
            if heute <= termin <= enddatum:
                termine.append(termin)
        monat += 1
        if monat > 12:
            monat, jahr = 1, jahr + 1
    return termine


def _termine_aus_text(text: str) -> list[date]:
    """
    Extrahiert alle Datumsangaben aus dem Seitentext.

    Args:
        text: Sichtbarer Text der Termine-Seite

    Returns:
        Sortierte, eindeutige Liste von Daten
    """
    gefunden: set[date] = set()
    for tag, monat, jahr in DATUM_NUMERISCH_REGEX.findall(text):
        try:
            gefunden.add(date(int(jahr), int(monat), int(tag)))
        except ValueError:
            continue
    for tag, monat_name, jahr in DATUM_TEXT_REGEX.findall(text):
        monat = MONATE.get(monat_name.lower())
        if not monat:
            continue
        try:
            gefunden.add(date(int(jahr), monat, int(tag)))
        except ValueError:
            continue
    return sorted(gefunden)


def _event_erstellen(termin: date) -> dict:
    """
    Baut ein Event-Dict für einen Termin.

    Args:
        termin: Datum des Street Food Thursday

    Returns:
        Event-Dict im DiesDasDüsseldorf Standard-Format
    """
    return {
        "titel": "Street Food Thursday",
        "datum": termin.isoformat(),
        "uhrzeit": EVENT_UHRZEIT,
        "ort": ORT_STANDARD,
        "adresse": ADRESSE_STANDARD,
        "kategorie": KATEGORIE_STANDARD,
        "beschreibung": BESCHREIBUNG,
        "preis": "kostenlos",
        "quelle_name": QUELLE_NAME,
        "quelle_url": QUELLE_URL,
        "bild_url": None,
        "instagram_caption": None,
        "datum_bis": None,
        "ist_wiederkehrend": True,
        "status": "neu",
    }


def _termine_von_website(heute: date, enddatum: date) -> Optional[list[date]]:
    """
    Liest die offiziellen Termine von streetfood-duesseldorf.de.

    Args:
        heute:    Heutiges Datum
        enddatum: Ende des Vorschauzeitraums

    Returns:
        Liste der Termine im Zeitraum (leer = bewusst keine Termine, z.B. Saisonpause)
        oder None, wenn die Seite nicht lesbar ist bzw. nichts Auswertbares enthält
    """
    html = seite_abrufen(QUELLE_URL, logger)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()
    text = " ".join(soup.get_text(" ").split())

    beendet = SAISON_BEENDET_REGEX.search(text)
    if beendet:
        logger.info(
            "Scraper %s: Außerhalb der Saison – keine Termine (Website: \"Saison %s ist beendet\")",
            QUELLE_NAME, beendet.group(1),
        )
        return []

    alle_termine = _termine_aus_text(text)
    if not alle_termine:
        return None

    im_zeitraum = [t for t in alle_termine if heute <= t <= enddatum]
    if not im_zeitraum:
        logger.info(
            "Scraper %s: %d Termine auf der Website, keiner im Vorschauzeitraum (Saisonpause)",
            QUELLE_NAME, len(alle_termine),
        )
    return im_zeitraum


def scrape() -> list[dict]:
    """
    Gibt Street-Food-Thursday-Events für den Vorschauzeitraum zurück.

    Strategie:
    1. Offizielle Termine-Seite (inkl. Erkennung des Saisonendes)
    2. Fallback: Berechnung des ersten Donnerstags im Monat (März–Oktober)

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    termine: Optional[list[date]] = None
    try:
        termine = _termine_von_website(heute, enddatum)
    except Exception as fehler:
        logger.error("Website-Scraping fehlgeschlagen: %s", str(fehler))

    if termine is None:
        termine = _berechnete_termine(heute, enddatum)
        if termine:
            logger.warning(
                "Scraper %s: Website nicht auswertbar – %d Termine aus Muster berechnet "
                "(1. Donnerstag im Monat, März–Oktober)",
                QUELLE_NAME, len(termine),
            )
        else:
            logger.info(
                "Scraper %s: Website nicht auswertbar; Außerhalb der Saison (März–Oktober) – keine Termine",
                QUELLE_NAME,
            )

    events = [_event_erstellen(termin) for termin in termine]
    logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse:
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print()
