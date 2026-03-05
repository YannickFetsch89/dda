"""
datum.py – DiesDasDüsseldorf
Zentrale Datums- und Uhrzeitparser für alle Scraper.

Alle Scraper nutzen nahezu identische _datum_parsen()- und _uhrzeit_parsen()-
Implementierungen. Dieses Modul stellt eine einzige, kanonische Version
bereit und eliminiert so den Duplikat-Code.

Erstellt: 2026-03-05
"""
import logging
import re
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Vollständige Monatsnamen (Deutsch + gebräuchliche Englisch-Überschneidungen)
MONAT_MAP: dict[str, int] = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
    # Englisch (für Scraper wie Tonhalle-Webshop, der beide Sprachen liefern kann)
    "january": 1, "february": 2, "march": 3, "june": 6,
    "july": 7, "october": 10,
}

# Abgekürzte Monatsnamen (Deutsch + Englisch)
MONAT_KURZ_MAP: dict[str, int] = {
    "jan": 1, "feb": 2, "mär": 3, "mar": 3, "apr": 4,
    "mai": 5, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}


def datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt verschiedene Datumsformate in ISO 8601 (YYYY-MM-DD) um.

    Unterstützte Formate (in Prioritätsreihenfolge):
      - "2026-02-24"               → "2026-02-24"  (ISO bereits vorhanden)
      - "24.02.2026"               → "2026-02-24"  (deutsches Format)
      - "24. Februar 2026"         → "2026-02-24"  (ausgeschrieben)
      - "Sonntag 8. März 2026"     → "2026-03-08"  (mit Wochentag)
      - "Sunday 8 March 2026"      → "2026-03-08"  (englisch)
      - "24.02."                   → nächstes passendes Datum (ohne Jahr)
      - "24. Feb" / "24. Feb."     → nächstes passendes Datum (Kurzform)

    Args:
        text: Roher Datumstext von der Webseite

    Returns:
        Datum als ISO-String (YYYY-MM-DD) oder None bei Fehler
    """
    if not text:
        return None

    heute = date.today()
    bereinigt = text.strip()
    bereinigt_klein = bereinigt.lower()

    try:
        # Format: "2026-02-24" (ISO bereits vorhanden)
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(1)),
                int(treffer.group(2)),
                int(treffer.group(3)),
            ).isoformat()

        # Format: "24.02.2026"
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(3)),
                int(treffer.group(2)),
                int(treffer.group(1)),
            ).isoformat()

        # Format: "24. Februar 2026" / "Sonntag 8. März 2026" / "Sunday 8 March 2026"
        # Erkennt: optional Wochentag + Tag + Punkt(optional) + Monatsname + Jahr
        treffer = re.search(
            r"(\d{1,2})\.?\s+([a-zäöüß]+)\s+(\d{4})",
            bereinigt_klein,
        )
        if treffer:
            tag = int(treffer.group(1))
            monat_name = treffer.group(2).lower()
            jahr = int(treffer.group(3))
            monat = MONAT_MAP.get(monat_name)
            if monat:
                try:
                    return date(jahr, monat, tag).isoformat()
                except ValueError:
                    pass

        # Format ohne Jahr: "24.02." – nächstes passendes Datum ermitteln
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.", bereinigt)
        if treffer:
            tag = int(treffer.group(1))
            monat = int(treffer.group(2))
            jahr = heute.year
            try:
                kandidat = date(jahr, monat, tag)
            except ValueError:
                return None
            if kandidat < heute - timedelta(days=1):
                kandidat = date(jahr + 1, monat, tag)
            return kandidat.isoformat()

        # Format ohne Jahr: "24. Feb" oder "24. Feb." (Kurzform)
        treffer = re.search(r"(\d{1,2})\.\s*([a-zäöü]{3})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat_kurz = treffer.group(2)[:3].lower()
            monat = MONAT_KURZ_MAP.get(monat_kurz)
            if monat:
                jahr = heute.year
                try:
                    kandidat = date(jahr, monat, tag)
                except ValueError:
                    return None
                if kandidat < heute - timedelta(days=1):
                    kandidat = date(jahr + 1, monat, tag)
                return kandidat.isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning(
            "Datum konnte nicht geparst werden: '%s' – %s", text, fehler
        )
        return None

    return None


def uhrzeit_parsen(text: str) -> Optional[str]:
    """
    Extrahiert eine Uhrzeit (HH:MM) aus einem beliebigen Text.

    Unterstützte Formate: "19:30", "20.00", "20:00 Uhr", "20 Uhr"

    Bei ISO-Timestamps (z.B. "2026-03-05T20:00:00") wird die Zeit nach "T"
    extrahiert.

    Args:
        text: Roher Text mit möglicher Zeitangabe

    Returns:
        Uhrzeit als HH:MM-String oder None
    """
    if not text:
        return None

    # ISO-Timestamp: "T20:00" direkt extrahieren
    treffer = re.search(r"T(\d{2}):(\d{2})", text)
    if treffer:
        stunde, minute = int(treffer.group(1)), int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"

    # Standard HH:MM oder HH.MM (mit optionalem "Uhr")
    treffer = re.search(
        r"\b(\d{1,2})[:\.](\d{2})\s*(?:Uhr)?", text, re.IGNORECASE
    )
    if treffer:
        stunde = int(treffer.group(1))
        minute = int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"

    # Sonderfall zakk-Format: "20 Uhr" ohne Minuten
    treffer = re.search(r"\b(\d{1,2})\s+Uhr\b", text, re.IGNORECASE)
    if treffer:
        stunde = int(treffer.group(1))
        if 0 <= stunde <= 23:
            return f"{stunde:02d}:00"

    return None
