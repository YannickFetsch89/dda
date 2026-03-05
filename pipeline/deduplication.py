"""
deduplication.py – DiesDasDüsseldorf
In-Memory-Deduplizierung der Event-Liste vor dem Datenbank-Schreiben.

Zwei Regeln:
1. Doppelte Events (gleicher Titel + Datum + Ort) werden gemergt statt
   verworfen: Fehlende Felder des ersten Eintrags werden aus dem
   Duplikat ergänzt.
2. Beim bild_url wird ein Rausgegangen-Bild immer durch ein Bild einer
   anderen Quelle ersetzt, sofern vorhanden.

Erstellt: 2026-03-05
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Felder die bei Duplikaten ergänzt werden dürfen (wenn None/leer)
_ANREICHERBARE_FELDER: list[str] = [
    "adresse",
    "uhrzeit",
    "beschreibung",
    "preis",
    "bild_url",
    "instagram_location_id",
    "kategorie",
]

# Erkennung von Rausgegangen-Bildern
_RAUSGEGANGEN_MUSTER = re.compile(r"rausgegangen", re.IGNORECASE)


def _ist_rausgegangen_bild(bild_url: Optional[str]) -> bool:
    """
    Erkennt ob eine Bild-URL von Rausgegangen stammt.

    Rausgegangen nutzt imageflow.rausgegangen.de als CDN
    und s3.eu-central-1.amazonaws.com/rausgegangen als Ursprung.

    Args:
        bild_url: Zu prüfende Bild-URL

    Returns:
        True wenn die URL von Rausgegangen stammt
    """
    if not bild_url:
        return False
    return bool(_RAUSGEGANGEN_MUSTER.search(bild_url))


def _normalisiere_schluessel(titel: str, datum: str, ort: str) -> str:
    """
    Erstellt einen normalisierten Deduplizierungs-Schlüssel.

    Kleinschreibung, Leerzeichen-Normalisierung und Sonderzeichen-Entfernung
    reduzieren Falsch-Negative (z. B. Groß-/Kleinschreibung, Leerzeichen).

    Args:
        titel: Event-Titel
        datum: Event-Datum (ISO 8601)
        ort: Venue-Name

    Returns:
        Normalisierter Schlüssel-String
    """
    def _norm(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[^\w\s\-äöüß]", "", s)
        return s

    return f"{_norm(titel)}|{datum}|{_norm(ort)}"


def _events_mergen(basis: dict, duplikat: dict) -> dict:
    """
    Mergt zwei Events: Fehlende Felder der Basis werden aus dem Duplikat ergänzt.
    Bei bild_url: Rausgegangen-Bilder werden durch andere Quellen ersetzt.

    Args:
        basis: Primärer Event-Eintrag (wird angereichert)
        duplikat: Zweiter Event-Eintrag (Lieferant fehlender Daten)

    Returns:
        Angereicherter Event-Dict
    """
    merged = dict(basis)

    for feld in _ANREICHERBARE_FELDER:
        basis_wert = basis.get(feld)
        dupli_wert = duplikat.get(feld)

        if feld == "bild_url":
            # Rausgegangen-Bild durch bessere Quelle ersetzen
            if _ist_rausgegangen_bild(basis_wert) and dupli_wert and not _ist_rausgegangen_bild(dupli_wert):
                merged["bild_url"] = dupli_wert
                logger.debug(
                    "Bild ersetzt: Rausgegangen → '%s' (%s)",
                    duplikat.get("quelle_name", "?"), dupli_wert[:60],
                )
            elif not basis_wert and dupli_wert:
                merged["bild_url"] = dupli_wert
        else:
            # Feld ergänzen wenn leer
            if not basis_wert and dupli_wert:
                merged[feld] = dupli_wert
                logger.debug(
                    "Feld '%s' ergänzt von '%s': %s",
                    feld, duplikat.get("quelle_name", "?"), str(dupli_wert)[:60],
                )

    return merged


def deduplizieren(events: list[dict]) -> list[dict]:
    """
    Dedupliziert eine Event-Liste in-Memory mit Merge-Logik.

    Duplikate (gleicher Titel + Datum + Ort) werden nicht verworfen,
    sondern in den ersten Eintrag gemergt. Fehlende Felder werden
    ergänzt, Rausgegangen-Bilder durch bessere Quellen ersetzt.

    Args:
        events: Rohe Event-Liste aus allen Scrapern

    Returns:
        Deduplizierte und angereicherte Event-Liste
    """
    if not events:
        return []

    reihenfolge: list[str] = []
    index: dict[str, dict] = {}
    duplikat_anzahl = 0
    angereichert_anzahl = 0

    for event in events:
        titel = event.get("titel") or ""
        datum = event.get("datum") or ""
        ort = event.get("ort") or ""

        if not titel or not datum:
            # Pflichtfelder fehlen – trotzdem aufnehmen
            schluessel = f"_unvollstaendig_{id(event)}"
        else:
            schluessel = _normalisiere_schluessel(titel, datum, ort)

        if schluessel not in index:
            index[schluessel] = event
            reihenfolge.append(schluessel)
        else:
            # Duplikat gefunden: mergen statt verwerfen
            duplikat_anzahl += 1
            vorher = dict(index[schluessel])
            index[schluessel] = _events_mergen(index[schluessel], event)
            nachher = index[schluessel]

            # Prüfen ob tatsächlich etwas angereichert wurde
            veraenderte_felder = [
                f for f in _ANREICHERBARE_FELDER
                if vorher.get(f) != nachher.get(f)
            ]
            if veraenderte_felder:
                angereichert_anzahl += 1
                logger.info(
                    "Duplikat angereichert: '%s' (%s) – Felder ergänzt: %s (Quelle: %s)",
                    titel[:40], datum,
                    ", ".join(veraenderte_felder),
                    event.get("quelle_name", "?"),
                )
            else:
                logger.debug(
                    "Duplikat verworfen (keine neuen Daten): '%s' (%s) von '%s'",
                    titel[:40], datum, event.get("quelle_name", "?"),
                )

    ergebnis = [index[s] for s in reihenfolge]

    logger.info(
        "Deduplizierung: %d → %d Events (%d Duplikate, %d angereichert)",
        len(events), len(ergebnis), duplikat_anzahl, angereichert_anzahl,
    )
    return ergebnis
