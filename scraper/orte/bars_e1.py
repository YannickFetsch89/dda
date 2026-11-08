"""
bars_e1.py – DiesDasDüsseldorf
Entscheidung E1: Brauhäuser (und Gastropubs) erscheinen in BEIDEN Guides, haben aber nur EINE URL.

  - Orte mit typ='restaurant', die die Bar-Suche als Kneipe erkennt (Gastropub, Brauhaus …):
    extras.auch_kneipe = true (+ unterart) → zusätzlich im Kneipen-Hub, Link bleibt die Restaurant-URL.
  - Neu importierte Kneipen, die Brauhäuser (Brauerei/Brewpub als Primärtyp, „Brauhaus“/„Brauerei“ im Namen)
    oder Gastropubs sind: extras.auch_restaurant = true → zusätzlich im Restaurant-Hub, Link bleibt die Kneipen-URL.
  - Der typ (= URL) eines bestehenden Orts wird nie geändert.

Der Lauf ersetzt extras zeilenweise mit dem Stand vom Lesezeitpunkt: nicht gleichzeitig mit einem
anderen Skript ausführen, das extras schreibt (flaechensuche, bars_einordnen).

Nutzung:
  python -m scraper.orte.bars_e1 [--dry-run]
"""
import argparse
import json
import logging
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scraper.orte import bars  # noqa: E402
from scraper.orte import flaechensuche as fs  # noqa: E402
from scraper.orte.google_places import alle_zeilen  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Namen, die einen Restaurant-Eintrag eindeutig als Kneipe/Brauhaus ausweisen
KNEIPEN_NAME = re.compile(r"brauhaus|brauerei|ausschank|gaststätte|kneipe|\bpub\b|bierstube|schänke|schenke", re.IGNORECASE)
# Wie MIN_QUALITAETS_SCORE in web/lib/orte.ts: ab diesem Score (und aktiv) ist ein Ort auf der Website
MIN_SCORE_WEBSITE = 7
KNEIPEN_PRIMAER = set(bars.KNEIPEN_TYPEN) | set(bars.KNEIPEN_PRIMAER_ZUSATZ)


def ist_auch_kneipe(place: dict, name: str) -> bool:
    """Restaurant, das zusätzlich in den Kneipen-Hub gehört."""
    return (place.get("primaryType") or "") in KNEIPEN_PRIMAER or bool(KNEIPEN_NAME.search(name or ""))


def ist_auch_restaurant(extras: dict, name: str) -> bool:
    """Kneipe, die zusätzlich in den Restaurant-Hub gehört (Brauhaus oder Gastropub – beide mit Küche)."""
    return (bars.ist_brauhaus(extras.get("google_primaertyp"), name)
            or extras.get("google_primaertyp") == "gastropub")


def live(o: dict) -> bool:
    """Steht der Ort auf der Website? (nur für die Ausgabe)"""
    return bool(o.get("aktiv")) and (o.get("qualitaets_score") or 0) >= MIN_SCORE_WEBSITE


def aenderung(o: dict, p: dict | None) -> dict:
    """
    Soll-extras eines Orts nach E1. Idempotent: ein zweiter Lauf auf denselben
    Daten ergibt denselben Zustand. Der typ (= URL) wird NIE geändert.

    Bestehende Restaurant-Zeilen werden nur markiert (auch_kneipe), nicht umgetypt: ob eine
    Restaurant-URL früher schon öffentlich war, lässt sich nachträglich nicht sicher feststellen –
    ein Umtypen könnte sie zum 404 machen. (Die 13 am 07.11.2026 umgetypten Brauhäuser waren
    nachweislich nie live: Score 4–6.)
    """
    ex = o.get("extras") or {}
    neu = dict(ex)
    typ = o["typ"]  # bleibt unverändert
    if p and p.get("types"):
        neu["google_typen"] = list(p["types"])
    if typ == "restaurant" and p and ist_auch_kneipe(p, o["name"]):
        neu["auch_kneipe"] = True
        if bars.ist_brauhaus(p.get("primaryType"), o["name"]):
            neu["unterart"] = "brauhaus"  # feste Regel, hat Vorrang
        elif not neu.get("unterart"):
            # Eine von der Einordnung (KI) gesetzte Unterart nicht bei jedem Lauf zurücksetzen
            neu["unterart"] = bars.unterart(p)
    elif typ == "kneipe":
        if ist_auch_restaurant(neu, o["name"]):
            neu["auch_restaurant"] = True
        if bars.ist_brauhaus(neu.get("google_primaertyp"), o["name"]):
            neu["unterart"] = "brauhaus"
    return neu


def ausfuehren(dry_run: bool) -> None:
    from database.client import get_supabase_client

    db = get_supabase_client()
    fs.hub_setzen("bars")
    daten = json.loads(Path(fs.ZWISCHENSPEICHER).read_text(encoding="utf-8"))
    kandidaten = {p["id"]: p for p in fs.kandidaten(daten)}
    orte = alle_zeilen(db, "orte", "id, name, typ, aktiv, qualitaets_score, google_place_id, extras")

    auch_kneipe, auch_restaurant, sonst = [], [], []
    for o in orte:
        ex = o.get("extras") or {}
        neu = aenderung(o, kandidaten.get(o.get("google_place_id")))
        if neu == ex:
            continue
        update = {"extras": neu}
        if neu.get("auch_kneipe") and not ex.get("auch_kneipe"):
            auch_kneipe.append((o, update))
        elif neu.get("auch_restaurant") and not ex.get("auch_restaurant"):
            auch_restaurant.append((o, update))
        else:
            sonst.append((o, update))

    print(f"\nAuch im Kneipen-Hub, bleiben Restaurant ({len(auch_kneipe)}):",
          ", ".join(f"{o['name'][:28]}{' [live]' if live(o) else ''}" for o, _ in auch_kneipe))
    print(f"\nAuch im Restaurant-Hub ({len(auch_restaurant)}):", ", ".join(o["name"][:30] for o, _ in auch_restaurant))
    print(f"\nNur Google-Typen/Unterart aktualisiert: {len(sonst)}")
    if dry_run:
        return
    for o, update in auch_kneipe + auch_restaurant + sonst:
        db.table("orte").update(update).eq("id", o["id"]).execute()
    logger.info("E1 gesetzt: %d auch_kneipe, %d auch_restaurant, %d sonst",
                len(auch_kneipe), len(auch_restaurant), len(sonst))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    ausfuehren(parser.parse_args().dry_run)


if __name__ == "__main__":
    main()
