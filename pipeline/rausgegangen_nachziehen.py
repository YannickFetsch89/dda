"""
rausgegangen_nachziehen.py – DiesDasDüsseldorf
Abgelöst durch pipeline/quellen_nachziehen.py (Plan docs/plan-quellen-ausbau-2026-11-23.md, 4.2 Punkt 4, Schritt N1):
Das Umhängen gilt jetzt für jede strikt bessere Quelle nach Rang, nicht nur weg von Rausgegangen. Dieses Modul bleibt
als dünner Aufruf, damit ältere Verweise in der Doku weiter funktionieren.

Aufruf (gleiche Schalter wie quellen_nachziehen):
    python -m pipeline.rausgegangen_nachziehen [--zwischenspeicher] [--schreiben]
"""
from datetime import date

from database.client import _abgleich_spalten
from pipeline.quellen_nachziehen import main


def _rausgegangen_eintraege(db) -> list[dict]:
    """Alle künftigen Events, deren Quelle Rausgegangen ist (seitenweise) – genutzt von beschreibung_quellen.stichprobe."""
    eintraege: list[dict] = []
    heute = date.today().isoformat()
    start = 0
    while True:
        antwort = (
            db.table("events")
            .select("id,titel,ort,datum,slug," + _abgleich_spalten())
            .gte("datum", heute)
            .or_("quelle_name.ilike.*rausgegangen*,quelle_url.ilike.*rausgegangen.de*")
            .order("id")
            .range(start, start + 999)
            .execute()
        )
        seite = antwort.data or []
        eintraege.extend(seite)
        if len(seite) < 1000:
            return eintraege
        start += 1000


if __name__ == "__main__":
    main()
