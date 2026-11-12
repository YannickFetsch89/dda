"""
kasematten.py – DiesDasDüsseldorf
Scraper für die Events der Kasematten Düsseldorf (Rheinuferpromenade, Altstadt).

Die Kasematten sind fünf Gastro-Locations unter einem Dach (Café Bató, Zum Schlüssel, Frankenheim, Gosch,
Cocktailbar 112). Die Event-Seite (WordPress, Theme „Qode“) listet alle Aktionen als Blog-Karten
(`article.qodef-blog-item`): Bild, Titel mit Datum vorn („31.12.26 – Silvester 2026“, „19.09.26 – 18.10.26 – Oktoberfest“),
Kurztext. Uhrzeiten und die Beschreibung stehen nur auf der Detailseite.

Wochen-Reihen („Jeden Freitag – Freak Friday“) werden bewusst NICHT als Termine angelegt: Die Seite nennt weder
Saison noch Enddatum, und alte Einträge bleiben stehen – wöchentliche Termine wären geraten (Entscheidung
Auftraggeber offen, siehe WOECHENTLICH).

robots.txt (geprüft 12.11.2026): alles erlaubt außer /cgi-bin/. Rate Limiting über seite_abrufen (≥ 2 s).

URL: https://kasematten-duesseldorf.de/events/
Erstellt: 2026-11-12
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

LISTE_URL = "https://kasematten-duesseldorf.de/events/"
QUELLE_NAME = "Kasematten Düsseldorf"
ORT = "Kasematten Düsseldorf"
ADRESSE = "Untere Rheinwerft, 40213 Düsseldorf"
MAX_DETAILSEITEN = 10

# Wochen-Reihen ohne Datum anlegen? Aus, bis der Auftraggeber entscheidet (Saison unbekannt).
# True erzeugt nur Termine im Vorschaufenster, keine historische Saison.
WOECHENTLICH = False

_WOCHENTAGE = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]

# „31.12.26“, „11.10.2026“, auch mit Bereich „19.09.26 – 18.10.26“
_DATUM = r"(\d{1,2})\.(\d{1,2})\.(\d{2}(?:\d{2})?)"
TITEL_REGEX = re.compile(rf"^\s*{_DATUM}\s*(?:[–-]\s*{_DATUM})?\s*[–-]\s*(.+?)\s*$")
# „26.-31.10.26“ (Tag-Bereich im selben Monat)
TAGBEREICH_REGEX = re.compile(r"^\s*(\d{1,2})\.\s*[–-]\s*(\d{1,2})\.(\d{1,2})\.(\d{2}(?:\d{2})?)\s*[–-]\s*(.+?)\s*$")
WOECHENTLICH_REGEX = re.compile(r"^\s*jeden\s+(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)\b", re.I)

# Uhrzeit auf der Detailseite: „von 17 bis 24 Uhr“, „ab 19 Uhr“, „19:30 Uhr“
UHRZEIT_REGEXE = [
    re.compile(r"\bvon\s+(\d{1,2})(?:[:.](\d{2}))?\s+bis\s+\d{1,2}(?:[:.]\d{2})?\s*uhr", re.I),
    re.compile(r"\bab\s+(\d{1,2})(?:[:.](\d{2}))?\s*uhr", re.I),
    re.compile(r"\b(\d{1,2})[:.](\d{2})\s*uhr", re.I),
]

KATEGORIE_STICHWORTE = [
    ("food", re.compile(r"street\s?food|chefs in town|brunch|bbq|grill|buffet", re.I)),
    ("nightlife", re.compile(r"silvester|party|90.?s|dj|halloween|after|oktoberfest|sound|friday|night", re.I)),
]


def _jahr(roh: str) -> int:
    """„26“ → 2026, „2026“ → 2026."""
    j = int(roh)
    return j + 2000 if j < 100 else j


def _datum(tag: str, monat: str, jahr: str) -> Optional[date]:
    try:
        return date(_jahr(jahr), int(monat), int(tag))
    except ValueError:
        return None


def _jahreswechsel(von: Optional[date], bis: Optional[date]) -> tuple[Optional[date], Optional[date]]:
    """
    „31.12.26 – 01.01.26“: Ende im Januar nach Start im Dezember meint das nächste Jahr. Andere rückwärts laufende
    Bereiche („01.06.26 – 01.05.26“) sind Tippfehler und bleiben rückwärts – titel_parsen verwirft sie dann.
    """
    if not von or not bis or bis >= von or not (von.month == 12 and bis.month == 1):
        return von, bis
    try:
        return von, bis.replace(year=bis.year + 1)
    except ValueError:
        return von, None


def wochen_termine(wochentag: str, von: date, bis: date) -> list[date]:
    """Jeden passenden Wochentag im Fenster, Grenzen inklusive."""
    ziel = _WOCHENTAGE.index(wochentag)
    tage = []
    tag = von
    while tag <= bis:
        if tag.weekday() == ziel:
            tage.append(tag)
        tag += timedelta(days=1)
    return tage


def titel_parsen(titel_roh: str) -> Optional[dict]:
    """
    Zerlegt den Kartentitel in Datum, Enddatum und Titel. (rein, testbar)

    Returns:
        {"datum", "datum_bis", "titel"} – oder {"woechentlich": Wochentag, "titel"} – oder None (kein Datum erkennbar)
    """
    titel_roh = " ".join(titel_roh.split())
    w = WOECHENTLICH_REGEX.match(titel_roh)
    if w:
        rest = re.split(r"\s+[–-]\s+", titel_roh, maxsplit=1)
        return {"woechentlich": w.group(1).lower(), "titel": rest[1].strip() if len(rest) > 1 else titel_roh}
    m = TAGBEREICH_REGEX.match(titel_roh)
    if m:
        von, bis = _jahreswechsel(_datum(m.group(1), m.group(3), m.group(4)), _datum(m.group(2), m.group(3), m.group(4)))
        return {"datum": von, "datum_bis": bis, "titel": m.group(5).strip(" -–")} if von and bis and bis >= von else None
    m = TITEL_REGEX.match(titel_roh)
    if not m:
        return None
    von, bis = _jahreswechsel(
        _datum(m.group(1), m.group(2), m.group(3)),
        _datum(m.group(4), m.group(5), m.group(6)) if m.group(4) else None,
    )
    if not von or (bis and bis < von):
        return None
    return {"datum": von, "datum_bis": bis if bis and bis != von else None, "titel": m.group(7).strip(" -–")}


# „Öffnungszeiten von 11 bis 23 Uhr“ ist nicht die Startzeit der Veranstaltung
_OEFFNUNG = re.compile(r"öffnungszeiten\b.{0,180}?uhr", re.I)


def uhrzeit_finden(text: str) -> Optional[str]:
    """Erste plausible Startzeit aus dem Detailtext (HH:MM), sonst None. (rein, testbar)

    Öffnungszeiten werden ausgelassen. „von 24 …“ ist keine Startzeit; dann gilt der nächste Treffer
    desselben Musters („ab 19 Uhr“).
    """
    text = _OEFFNUNG.sub(" ", text)
    for regex in UHRZEIT_REGEXE:
        for m in regex.finditer(text):
            stunde, minute = int(m.group(1)), int(m.group(2) or 0)
            if 0 <= stunde <= 23 and 0 <= minute <= 59:
                return f"{stunde:02d}:{minute:02d}"
    return None


def kategorie_erkennen(titel: str, text: str = "") -> str:
    """Kategorie aus Stichworten in Titel, ersatzweise im Text; Standard nightlife (Partys an der Rheinpromenade)."""
    for quelle in (titel, text):
        for kategorie, regex in KATEGORIE_STICHWORTE:
            if regex.search(quelle):
                return kategorie
    return "nightlife"


def karten_parsen(html: str) -> list[dict]:
    """Alle Event-Karten der Übersicht: Titel (roh), URL, Bild, Kurztext. (rein, testbar)"""
    soup = BeautifulSoup(html, "html.parser")
    karten = []
    for artikel in soup.select("article.qodef-blog-item"):
        link = artikel.select_one(".qodef-e-title-link")
        if not link or not link.get("href"):
            continue
        bild = artikel.select_one(".qodef-e-media-image img")
        auszug = artikel.select_one(".qodef-e-excerpt")
        karten.append({
            "titel_roh": " ".join(link.get_text(" ", strip=True).split()),
            "url": link["href"],
            "bild_url": bild.get("src") if bild else None,
            "auszug": " ".join(auszug.get_text(" ", strip=True).split()) if auszug else "",
        })
    return karten


def _detail_lesen(url: str) -> tuple[str, Optional[str]]:
    """Beschreibung (max. 300 Zeichen) und Startzeit von der Detailseite."""
    html = seite_abrufen(url, logger)
    if not html:
        return "", None
    soup = BeautifulSoup(html, "html.parser")
    inhalt = soup.select_one(".elementor-widget-theme-post-content, .entry-content, article") or soup
    for t in inhalt(["script", "style", "noscript"]):
        t.decompose()
    text = " ".join(inhalt.get_text(" ", strip=True).split())
    # Seitenleiste „Neueste Beiträge“ abschneiden
    text = text.split("Neueste Beiträge")[0].strip()
    return text[:300], uhrzeit_finden(text)


async def scrape() -> list[dict]:
    """
    Scrapt die datierten Events der Kasematten Düsseldorf im Vorschauzeitraum.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
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
        logger.warning("Scraper %s: Kein HTML geladen – leere Liste", QUELLE_NAME)
        return []

    karten = karten_parsen(html)
    if not karten:
        logger.warning("Scraper %s: Keine Event-Karten (article.qodef-blog-item) – Seitenstruktur prüfen", QUELLE_NAME)
        return []

    events, details = [], 0
    for karte in karten:
        daten = titel_parsen(karte["titel_roh"])
        if not daten:
            logger.info("Kasematten: Titel ohne erkennbares Datum übersprungen: %s", karte["titel_roh"])
            continue
        if "woechentlich" in daten:
            if not WOECHENTLICH:
                logger.info("Kasematten: Wochen-Reihe nicht angelegt (Saison unbekannt): %s", karte["titel_roh"])
                continue
            termine = [(tag, None) for tag in wochen_termine(daten["woechentlich"], heute, enddatum)]
        else:
            # Mehrtägige Events zählen, solange sie noch laufen
            letzter_tag = daten["datum_bis"] or daten["datum"]
            if letzter_tag < heute or daten["datum"] > enddatum:
                continue
            termine = [(daten["datum"], daten["datum_bis"])]
        if not termine:
            continue

        beschreibung, uhrzeit = karte["auszug"][:300], None
        if details < MAX_DETAILSEITEN:
            details += 1
            try:
                text, uhrzeit = await asyncio.to_thread(_detail_lesen, karte["url"])
                beschreibung = text or beschreibung
            except Exception as fehler:
                logger.warning("Kasematten: Detailseite %s nicht lesbar: %s", karte["url"], str(fehler))

        for datum, datum_bis in termine:
            events.append({
                "titel": daten["titel"],
                "datum": datum.isoformat(),
                "datum_bis": datum_bis.isoformat() if datum_bis else None,
                "uhrzeit": uhrzeit,
                "ort": ORT,
                "adresse": ADRESSE,
                "kategorie": kategorie_erkennen(daten["titel"], beschreibung),
                "beschreibung": beschreibung,
                "preis": None,
                "quelle_name": QUELLE_NAME,
                "quelle_url": karte["url"],
                "bild_url": karte["bild_url"],
                "bild_generiert": False,
                "post_typ": "feed",
                "instagram_caption": None,
                "instagram_location_id": None,
                "status": "neu",
            })

    logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    for e in asyncio.run(scrape()):
        print(e["datum"], e.get("datum_bis"), e["uhrzeit"], e["kategorie"], "|", e["titel"], "|", e["quelle_url"])
