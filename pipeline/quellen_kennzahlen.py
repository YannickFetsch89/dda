"""
quellen_kennzahlen.py – DiesDasDüsseldorf
Kennzahlen zur Abdeckung der Quellen (Plan docs/plan-quellen-ausbau-2026-11-23.md, 4.3 und 4.5, Schritt R2).

- luecken_berechnen(events): Rausgegangen-Events dieses Laufs an Orten, deren Haus wir direkt abfragen (eine
  Rang-1-Quelle hat in diesem Lauf Events an demselben Haus geliefert), ohne Treffer dieser Quelle am selben Tag
  → {Ort: Anzahl}. Grundlage der Warnregel W7 (mehr als 3 an einem Ort). Abgeschaltete und saisonal leere Quellen
  liefern keine Events und zählen deshalb nicht als „direkt abgefragt“.
- bestand_zaehlen(db): sichtbare Events ab heute und davon die, die nur Rausgegangen kennt (Spalte quellen; alte
  Zeilen ohne Liste über quelle_name).

Beide werfen nicht; main.py schreibt die Werte über den Lauf-Report in scraper_laeufe
(kuenftige_events, nur_rausgegangen, luecken – database/quellen_spalte_2026-11-24.sql).
"""
import logging
from collections import Counter
from datetime import date
from typing import Optional

from pipeline.quellen_rang import HAUS, QUELLEN_FELD, nur_rausgegangen, quellen_der_zeile, quellen_rang

logger = logging.getLogger(__name__)

SEITENGROESSE = 1000


def _haus(event: dict) -> Optional[str]:
    """Schlüssel des Hauses aus der Ortszuordnung (pipeline/ort_zuordnung.py): Haus-ID, sonst die eigene ort_id."""
    return event.get("_haus_id") or event.get("ort_id")


def luecken_berechnen(events: list[dict]) -> dict[str, int]:
    """{Ort: Anzahl} der Rausgegangen-Events an direkt abgefragten Häusern ohne Treffer der Direktquelle."""
    direkt: set[str] = set()
    direkt_am_tag: set[tuple[str, str]] = set()
    for e in events:
        haus = _haus(e)
        if haus and quellen_rang(e) == HAUS:
            direkt.add(haus)
            direkt_am_tag.add((haus, e.get("datum") or ""))
    luecken: Counter = Counter()
    for e in events:
        haus = _haus(e)
        if not haus or haus not in direkt or (haus, e.get("datum") or "") in direkt_am_tag:
            continue
        liste = e.get(QUELLEN_FELD) or quellen_der_zeile(e)
        if nur_rausgegangen(liste):
            luecken[(e.get("ort") or "?").strip()] += 1
    return dict(luecken.most_common())


def bestand_zaehlen(db, heute: Optional[str] = None) -> tuple[Optional[int], Optional[int]]:
    """(künftige Events, davon nur Rausgegangen); bei einem Fehler (None, None)."""
    heute = heute or date.today().isoformat()
    gesamt, nur_rg, start = 0, 0, 0
    try:
        while True:
            zeilen = (
                db.table("events").select("id,quelle_name,quelle_url,quellen")
                .eq("abgelehnt", False).gte("datum", heute)
                .order("id").range(start, start + SEITENGROESSE - 1).execute().data or []
            )
            for z in zeilen:
                gesamt += 1
                if nur_rausgegangen(quellen_der_zeile(z)):
                    nur_rg += 1
            if len(zeilen) < SEITENGROESSE:
                return gesamt, nur_rg
            start += SEITENGROESSE
    except Exception as fehler:
        logger.error("Kennzahl „nur Rausgegangen“ nicht berechenbar: %s", fehler)
        return None, None


def ticket_links_zaehlen(events: list[dict]) -> tuple[int, Counter]:
    """
    Ticket-Links dieses Laufs (Plan Quellen-Ausbau 5.5.2, Schritt P1): (Events mit ticket_url, Anzahl je Anbieter).
    Anbieter nach Domain (scraper/utils/ticket_link.py); unbekannte Domains zählen als „andere“.
    """
    from scraper.utils.ticket_link import anbieter

    je_anbieter: Counter = Counter()
    for event in events:
        url = event.get("ticket_url")
        if url:
            je_anbieter[anbieter(url) or "andere"] += 1
    return sum(je_anbieter.values()), je_anbieter
