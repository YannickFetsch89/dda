"""
slug_generator.py – DiesDasDüsseldorf
Erzeugt SEO-freundliche URL-Slugs aus Event-Daten.

URL-Schema: /event/{kategorie}/{slug}
Slug-Format: {titel}-{venue}-{YYYY-MM-DD}
Beispiel: beethoven-candle-light-konzert-zakk-2026-10-29
"""
import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

_UMLAUT_MAP = {
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
}

_UMLAUT_RE = re.compile("|".join(re.escape(k) for k in _UMLAUT_MAP))

_MAX_TITEL_ZEICHEN = 60
_MAX_ORT_ZEICHEN = 25


def _umlaute_ersetzen(text: str) -> str:
    """Ersetzt deutsche Umlaute durch ASCII-Äquivalente."""
    return _UMLAUT_RE.sub(lambda m: _UMLAUT_MAP[m.group()], text)


def _slugify(text: str, max_laenge: int = 0) -> str:
    """
    Wandelt einen beliebigen Text in einen URL-Slug um.

    - Deutsche Umlaute → ae, oe, ue, ss
    - Unicode-Zeichen → ASCII-Näherung
    - Sonderzeichen → Bindestrich
    - Mehrfache Bindestriche → einzelner Bindestrich
    """
    text = _umlaute_ersetzen(text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    text = text.strip("-")

    if max_laenge and len(text) > max_laenge:
        text = text[:max_laenge].rstrip("-")

    return text


def slug_erzeugen(titel: str, ort: str, datum: str) -> str:
    """
    Erzeugt einen SEO-Slug für ein Event.

    Args:
        titel: Event-Titel (z.B. "Beethoven als Candle Light Konzert")
        ort: Venue-Name (z.B. "zakk Kulturzentrum")
        datum: ISO-Datum (z.B. "2026-10-29")

    Returns:
        Slug-String (z.B. "beethoven-als-candle-light-konzert-zakk-kulturzentrum-2026-10-29")
    """
    if not titel or not datum:
        return ""

    titel_slug = _slugify(titel, _MAX_TITEL_ZEICHEN)
    ort_slug = _slugify(ort, _MAX_ORT_ZEICHEN) if ort else ""

    teile = [t for t in [titel_slug, ort_slug, datum] if t]
    return "-".join(teile)


def slug_fuer_event(event: dict) -> str:
    """Erzeugt einen Slug aus einem Event-Dict."""
    return slug_erzeugen(
        event.get("titel", ""),
        event.get("ort", ""),
        event.get("datum", ""),
    )
