"""
sport_im_park.py – DiesDasDüsseldorf
Scraper für das kostenlose Outdoor-Sportangebot "Sport im Park" in Düsseldorf.

"Sport im Park" ist ein saisonales Angebot (Sommersaison, ca. Mai–Oktober) mit
festen Wochenkursen in Düsseldorfer Parks. Es gibt keine einzelnen Event-Seiten,
sondern nur einen Wochenplan (Wochentag, Uhrzeit, Kurs, Park) und die Saisondaten.

Quelle: Stadtsportbund Düsseldorf (SSB) – Seite "Sport im Park".
Hinweis: Die Seite des Sportamts (duesseldorf.de/sportamt/sport-im-park) wird
NICHT abgerufen. Die robots.txt von duesseldorf.de sperrt alle nicht explizit
freigegebenen Bots ("User-agent: * / Disallow: /"). Zudem enthält die Stadtseite
keine Termine im HTML (Stundenplan nur als PDF-Flyer).

Strategie:
1. SSB-Seite laden (httpx, Rate Limiting über http_client)
2. Saisonzeitraum aus dem Text lesen ("Die Sommersaison findet vom … bis … statt")
3. Außerhalb der Saison: INFO-Log und leere Liste (kein Fehler)
4. In der Saison: Wochenplan parsen und je Kurs den nächsten Termin
   im Vorschauzeitraum erzeugen (analog zu parkrun.py)

URL: https://www.ssbduesseldorf.de/unsere-themen/sport-im-park
Erstellt: 2026-03-06
Überarbeitet: 2026-11-04 – Quelle auf SSB umgestellt (robots.txt), Saison-Erkennung,
                            Wochenplan-Parser statt JSON-LD/Karten-Parser
"""
import asyncio
import logging
import re
from datetime import date, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from config import SCRAPER_VORSCHAU_TAGE
from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

LISTE_URL = "https://www.ssbduesseldorf.de/unsere-themen/sport-im-park"
QUELLE_NAME = "Sport im Park Düsseldorf"
KATEGORIE_STANDARD = "sport"
PREIS_STANDARD = "kostenlos"

MONATE = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5,
    "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
    "november": 11, "dezember": 12,
}

WOCHENTAGE = {
    "montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3,
    "freitag": 4, "samstag": 5, "sonntag": 6,
}

# "Die Sommersaison findet vom 4. Mai bis zum 4. Oktober 2026 statt."
# "Die Sommersaison fand vom 4. Mai bis einschließlich 4. Oktober 2026 statt."
SAISON_REGEX = re.compile(
    r"saison\s+(?:findet|fand)\s+vom\s+(\d{1,2})\.\s*([a-zäöü]+)\s*(\d{4})?\s+"
    r"bis\s+(?:zum\s+|einschließlich\s+)?(\d{1,2})\.\s*([a-zäöü]+)\s+(\d{4})",
    re.IGNORECASE,
)

# "18 Uhr", "17.30 Uhr", "17:30 Uhr"
UHRZEIT_REGEX = re.compile(r"^(\d{1,2})(?:[.:](\d{2}))?\s*Uhr", re.IGNORECASE)


def _text_normalisieren(text: str) -> str:
    """
    Fasst Whitespace (inkl. geschützter Leerzeichen) zu einfachen Leerzeichen zusammen.

    Args:
        text: Roher Text

    Returns:
        Bereinigter Text
    """
    return " ".join((text or "").split())


def _beschreibung_kuerzen(text: str) -> str:
    """
    Kürzt eine Beschreibung auf maximal 300 Zeichen.

    Args:
        text: Roher Beschreibungstext

    Returns:
        Beschreibung mit maximal 300 Zeichen
    """
    if not text:
        return ""
    return _text_normalisieren(text)[:300]


def _kategorie_erkennen(text: str) -> str:
    """
    Erkennt die passende Kategorie anhand des Kurstitels.

    Args:
        text: Kurstitel

    Returns:
        Gültige Kategorie
    """
    if not text:
        return KATEGORIE_STANDARD
    text_klein = text.lower()
    outdoor_begriffe = ["wandern", "radeln", "fahrrad", "natur", "spazier"]
    for begriff in outdoor_begriffe:
        if begriff in text_klein:
            return "outdoor"
    return KATEGORIE_STANDARD


def _saison_ermitteln(soup: BeautifulSoup) -> Optional[tuple[date, date]]:
    """
    Liest den Saisonzeitraum ("Sommersaison findet vom … bis … statt") aus der Seite.

    Args:
        soup: Geparste SSB-Seite

    Returns:
        Tupel (Saisonbeginn, Saisonende) oder None, wenn nicht gefunden
    """
    text = _text_normalisieren(soup.get_text(" "))
    treffer = SAISON_REGEX.search(text)
    if not treffer:
        return None

    tag_von, monat_von_name, jahr_von, tag_bis, monat_bis_name, jahr_bis = treffer.groups()
    monat_von = MONATE.get(monat_von_name.lower())
    monat_bis = MONATE.get(monat_bis_name.lower())
    if not monat_von or not monat_bis:
        return None

    try:
        ende = date(int(jahr_bis), monat_bis, int(tag_bis))
        beginn = date(int(jahr_von or jahr_bis), monat_von, int(tag_von))
    except ValueError:
        return None
    return beginn, ende


def _kurse_parsen(soup: BeautifulSoup) -> list[dict]:
    """
    Parst den Wochenplan der SSB-Seite.

    Aufbau (je Spalte): <p><strong>Montag</strong></p>, danach je Kurs ein <p> mit
    Zeilen (per <br> getrennt): Uhrzeit, Kurstitel, Park, (Zusatz in Klammern),
    Trainer*in, Verein.

    Args:
        soup: Geparste SSB-Seite

    Returns:
        Liste von Kurs-Dicts (wochentag, uhrzeit, titel, ort, details)
    """
    ueberschrift = soup.find(
        lambda tag: tag.name in ("h2", "h3", "h4")
        and "sportangebote" in tag.get_text(" ", strip=True).lower()
    )
    if not ueberschrift:
        return []

    kurse = []
    aktueller_wochentag: Optional[int] = None

    for absatz in ueberschrift.find_all_next("p"):
        zeilen = [_text_normalisieren(z) for z in absatz.get_text("\n").split("\n")]
        zeilen = [z for z in zeilen if z]
        if not zeilen:
            continue

        # Ende des Wochenplans
        if zeilen[0].lower().startswith("weitere kurse"):
            break

        # Wochentag-Überschrift
        erster_begriff = zeilen[0].lower().rstrip(":")
        if len(zeilen) == 1 and erster_begriff in WOCHENTAGE:
            aktueller_wochentag = WOCHENTAGE[erster_begriff]
            continue

        zeit_treffer = UHRZEIT_REGEX.match(zeilen[0])
        if not zeit_treffer or aktueller_wochentag is None or len(zeilen) < 3:
            continue

        stunde = int(zeit_treffer.group(1))
        minute = int(zeit_treffer.group(2) or 0)
        if stunde > 23 or minute > 59:
            continue

        titel = zeilen[1]
        ort = zeilen[2]
        rest = zeilen[3:]
        # Umbrochene Ortsangaben wie "Räuscherweg/" + "Mitmachgarten" zusammenfügen
        if rest and ort.endswith(("/", "-")):
            ort = f"{ort}{rest[0]}" if ort.endswith("/") else f"{ort[:-1]}{rest[0]}"
            rest = rest[1:]
        # Ortszusatz wie "(Höhe Bootshaus Nautic)" an den Ort anhängen
        if rest and rest[0].startswith("("):
            ort = f"{ort} {rest[0]}"
            rest = rest[1:]

        # Silbentrennungen wie "Turn- verein" wieder zusammenfügen
        details = re.sub(r"-\s+(?=[a-zäöüß])", "", " ".join(rest))
        details = re.sub(r"^mit\s+", "", details, flags=re.IGNORECASE).strip()

        kurse.append({
            "wochentag": aktueller_wochentag,
            "uhrzeit": f"{stunde:02d}:{minute:02d}",
            "titel": titel,
            "ort": ort,
            "details": details,
        })

    return kurse


def _naechster_termin(wochentag: int, von: date, bis: date) -> Optional[date]:
    """
    Berechnet den nächsten Termin eines Wochentags im Zeitraum [von, bis].

    Args:
        wochentag: Python-Wochentag (0 = Montag)
        von:       Frühestes Datum
        bis:       Spätestes Datum

    Returns:
        Datum oder None, wenn kein Termin in den Zeitraum fällt
    """
    kandidat = von + timedelta(days=(wochentag - von.weekday()) % 7)
    return kandidat if kandidat <= bis else None


async def scrape() -> list[dict]:
    """
    Scrapt die kostenlosen Sport-im-Park-Kurse in Düsseldorf.

    Außerhalb der Sommersaison wird eine leere Liste zurückgegeben (kein Fehler,
    wird per INFO-Log als saisonal leer gekennzeichnet).

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format
        (je Kurs der nächste Termin im Vorschauzeitraum).
    """
    heute = date.today()
    enddatum = heute + timedelta(days=SCRAPER_VORSCHAU_TAGE)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = await asyncio.to_thread(seite_abrufen, LISTE_URL, logger)
    except Exception as fehler:
        logger.error("Scraper %s: Abruf von %s fehlgeschlagen: %s", QUELLE_NAME, LISTE_URL, str(fehler))
        return []

    if not html:
        logger.warning("Scraper %s: Kein HTML geladen – leere Liste wird zurückgegeben", QUELLE_NAME)
        return []

    soup = BeautifulSoup(html, "html.parser")

    saison = _saison_ermitteln(soup)
    if not saison:
        logger.warning(
            "Scraper %s: Saisonzeitraum nicht gefunden – Seitenstruktur prüfen (%s)",
            QUELLE_NAME, LISTE_URL,
        )
        return []

    saison_beginn, saison_ende = saison
    if saison_ende < heute:
        logger.info(
            "Scraper %s: Außerhalb der Saison – keine Termine (Saison %s bis %s beendet, "
            "neue Saison noch nicht veröffentlicht)",
            QUELLE_NAME, saison_beginn.isoformat(), saison_ende.isoformat(),
        )
        return []
    if saison_beginn > enddatum:
        logger.info(
            "Scraper %s: Außerhalb der Saison – keine Termine (Saison beginnt erst am %s)",
            QUELLE_NAME, saison_beginn.isoformat(),
        )
        return []

    kurse = _kurse_parsen(soup)
    if not kurse:
        logger.warning(
            "Scraper %s: Saison läuft (%s bis %s), aber kein Kursplan gefunden – Seitenstruktur prüfen",
            QUELLE_NAME, saison_beginn.isoformat(), saison_ende.isoformat(),
        )
        return []

    zeitraum_von = max(heute, saison_beginn)
    zeitraum_bis = min(enddatum, saison_ende)

    events = []
    gesehene_schluessel: set[str] = set()
    for kurs in kurse:
        termin = _naechster_termin(kurs["wochentag"], zeitraum_von, zeitraum_bis)
        if not termin:
            continue

        titel = f"Sport im Park: {kurs['titel']}"
        schluessel = f"{titel}_{termin.isoformat()}_{kurs['ort']}"
        if schluessel in gesehene_schluessel:
            continue
        gesehene_schluessel.add(schluessel)

        beschreibung = (
            f"Kostenloses Outdoor-Training „{kurs['titel']}“ im Rahmen von Sport im Park – "
            f"jede Woche, ohne Anmeldung, einfach vorbeikommen."
        )
        if kurs["details"]:
            beschreibung += f" Trainer*in/Verein: {kurs['details']}"
            if not beschreibung.endswith((".", ")")):
                beschreibung += "."

        events.append({
            "titel": titel,
            "datum": termin.isoformat(),
            "uhrzeit": kurs["uhrzeit"],
            "ort": kurs["ort"],
            "adresse": None,
            "kategorie": _kategorie_erkennen(kurs["titel"]),
            "beschreibung": _beschreibung_kuerzen(beschreibung),
            "preis": PREIS_STANDARD,
            "quelle_name": QUELLE_NAME,
            "quelle_url": LISTE_URL,
            "bild_url": None,
            "bild_generiert": False,
            "post_typ": "feed",
            "instagram_caption": None,
            "status": "neu",
        })

    logger.info(
        "Scraper %s fertig: %d Events (%d Kurse im Wochenplan, Saison %s bis %s)",
        QUELLE_NAME, len(events), len(kurse), saison_beginn.isoformat(), saison_ende.isoformat(),
    )
    return events


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json as _json
    ergebnisse = asyncio.run(scrape())
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
