"""
imbiss_einteilen.py – DiesDasDüsseldorf
Teilt die vorhandenen Restaurants in "restaurant" und "imbiss" (Schnellimbiss) ein – Regeln in imbiss.py.

  python -m scraper.orte.imbiss_einteilen              Probelauf: zeigt, was sich ändern würde
  python -m scraper.orte.imbiss_einteilen --ausfuehren  schreibt typ = 'imbiss' (+ extras.imbiss_grund)

Voraussetzung: database/orte_typ_imbiss_2026-11-05.sql wurde ausgeführt (Typ 'imbiss' erlaubt).
Orte mit extras.typ_fest = true (von Hand eingeordnet) werden nie angefasst. Cafés werden nicht geprüft.
Auch die Gegenrichtung wird angeboten: ein früher als Imbiss markierter Ort, den die Regeln nicht mehr
als Imbiss sehen, wird wieder Restaurant.
"""
import argparse
import logging
import sys

from database.client import get_supabase_client
from scraper.orte.google_places import alle_zeilen
from scraper.orte.imbiss import imbiss_grund

logger = logging.getLogger(__name__)


def einteilen(ausfuehren: bool) -> dict:
    db = get_supabase_client()
    orte = alle_zeilen(
        db, "orte", "id, name, typ, preis_niveau, aktiv, extras",
        lambda q: q.in_("typ", ["restaurant", "imbiss"]),
    )
    aenderungen = []
    for o in orte:
        extras = o.get("extras") or {}
        if extras.get("typ_fest"):
            continue
        grund = imbiss_grund(o["name"], extras.get("google_primaertyp"), o.get("preis_niveau"),
                             extras.get("google_ausstattung"))
        neu = "imbiss" if grund else "restaurant"
        if neu != o["typ"]:
            aenderungen.append((o, neu, grund))

    zu_imbiss = [a for a in aenderungen if a[1] == "imbiss"]
    zu_restaurant = [a for a in aenderungen if a[1] == "restaurant"]
    print(f"Orte geprüft: {len(orte)} | → Schnellimbiss: {len(zu_imbiss)} | → Restaurant: {len(zu_restaurant)}")
    for o, neu, grund in sorted(aenderungen, key=lambda a: a[0]["name"]):
        sichtbar = "" if o.get("aktiv") else " (inaktiv)"
        print(f"  {o['typ']:10s} → {neu:10s} {o['name'][:45]:45s}{sichtbar}  {grund or ''}")

    if not ausfuehren:
        print("\nProbelauf – nichts geschrieben. Mit --ausfuehren übernehmen.")
        return {"geplant": len(aenderungen), "geschrieben": 0}

    geschrieben = fehler = 0
    for o, neu, grund in aenderungen:
        # extras unmittelbar vor dem Schreiben frisch lesen – parallel laufende Skripte
        # (z.B. google_places --aktualisieren) schreiben dasselbe JSON-Feld; nur imbiss_grund ändern
        try:
            frisch = db.table("orte").select("extras").eq("id", o["id"]).limit(1).execute().data
            extras = dict((frisch[0].get("extras") if frisch else o.get("extras")) or {})
        except Exception as e:
            fehler += 1
            logger.error("Ort '%s' nicht gelesen: %s", o["name"], e)
            continue
        if extras.get("typ_fest"):
            continue  # inzwischen von Hand festgelegt
        if grund:
            extras["imbiss_grund"] = grund
        else:
            extras.pop("imbiss_grund", None)
        try:
            db.table("orte").update({"typ": neu, "extras": extras}).eq("id", o["id"]).execute()
            geschrieben += 1
        except Exception as e:
            fehler += 1
            logger.error("Ort '%s' nicht umgestellt: %s", o["name"], e)
    print(f"\nGeschrieben: {geschrieben} | Fehler: {fehler}")
    return {"geplant": len(aenderungen), "geschrieben": geschrieben, "fehler": fehler}


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Restaurants in Restaurant/Schnellimbiss einteilen")
    parser.add_argument("--ausfuehren", action="store_true", help="Änderungen in Supabase schreiben")
    ergebnis = einteilen(parser.parse_args().ausfuehren)
    sys.exit(1 if ergebnis.get("fehler") else 0)
