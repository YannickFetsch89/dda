"""
bars_e1.py – DiesDasDüsseldorf
Entscheidung E1: Brauhäuser (und Gastropubs) erscheinen in BEIDEN Guides, haben aber nur EINE URL.

  - Orte mit typ='restaurant', die die Bar-Suche als Kneipe erkennt (Gastropub, Brauhaus …):
    extras.auch_kneipe = true (+ unterart) → zusätzlich im Kneipen-Hub, Link bleibt die Restaurant-URL.
  - Neu importierte Kneipen, die Brauhäuser sind (Brauerei/Brewpub, „Brauhaus“, „Brauerei“ im Namen):
    extras.auch_restaurant = true → zusätzlich im Restaurant-Hub, Link bleibt die Kneipen-URL.

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
BRAUHAUS_NAME = re.compile(r"brauhaus|brauerei", re.IGNORECASE)
# Wie MIN_QUALITAETS_SCORE in web/lib/orte.ts: ab diesem Score (und aktiv) ist ein Ort auf der Website
MIN_SCORE_WEBSITE = 7
KNEIPEN_PRIMAER = set(bars.KNEIPEN_TYPEN) | set(bars.KNEIPEN_PRIMAER_ZUSATZ)


def ist_auch_kneipe(place: dict, name: str) -> bool:
    """Restaurant, das zusätzlich in den Kneipen-Hub gehört."""
    return (place.get("primaryType") or "") in KNEIPEN_PRIMAER or bool(KNEIPEN_NAME.search(name or ""))


def ist_auch_restaurant(ort: dict) -> bool:
    """Kneipe, die zusätzlich in den Restaurant-Hub gehört (Brauhaus mit Küche)."""
    ex = ort.get("extras") or {}
    return ex.get("google_primaertyp") in ("brewery", "brewpub") or bool(BRAUHAUS_NAME.search(ort.get("name") or ""))


def ausfuehren(dry_run: bool) -> None:
    from database.client import get_supabase_client

    db = get_supabase_client()
    fs.hub_setzen("bars")
    daten = json.loads(Path(fs.ZWISCHENSPEICHER).read_text(encoding="utf-8"))
    kandidaten = {p["id"]: p for p in fs.kandidaten(daten)}
    orte = alle_zeilen(db, "orte", "id, name, typ, aktiv, qualitaets_score, google_place_id, extras")

    def live(o: dict) -> bool:
        """Steht der Ort schon auf der Website? Dann darf sich seine URL (= typ) nicht ändern."""
        return bool(o.get("aktiv")) and (o.get("qualitaets_score") or 0) >= MIN_SCORE_WEBSITE

    umtypen, auch_kneipe, auch_restaurant = [], [], []
    for o in orte:
        ex = o.get("extras") or {}
        p = kandidaten.get(o.get("google_place_id"))
        if o["typ"] == "restaurant" and p and ist_auch_kneipe(p, o["name"]):
            brauhaus = (p.get("primaryType") in ("brewery", "brewpub")) or bool(BRAUHAUS_NAME.search(o["name"]))
            if brauhaus and not live(o):
                # Nie live gewesenes Brauhaus → Haupt-Hub Kneipen, zusätzlich im Restaurant-Hub
                umtypen.append((o, {"typ": "kneipe", "extras": {**ex, "auch_restaurant": True, "auch_kneipe": False,
                                                                  "unterart": "brauhaus", "hub": "bars"}}))
            elif not ex.get("auch_kneipe"):
                auch_kneipe.append((o, {"extras": {**ex, "auch_kneipe": True, "unterart": bars.unterart(p)}}))
        elif o["typ"] == "kneipe" and ist_auch_restaurant(o) and not ex.get("auch_restaurant"):
            auch_restaurant.append((o, {"extras": {**ex, "auch_restaurant": True}}))

    print(f"Umtypen Restaurant → Kneipe, nie live ({len(umtypen)}):", ", ".join(o["name"][:30] for o, _ in umtypen))
    print(f"\nAuch im Kneipen-Hub, bleiben Restaurant ({len(auch_kneipe)}):",
          ", ".join(f"{o['name'][:28]}{' [live]' if live(o) else ''}" for o, _ in auch_kneipe))
    print(f"\nAuch im Restaurant-Hub ({len(auch_restaurant)}):", ", ".join(o["name"][:30] for o, _ in auch_restaurant))
    if dry_run:
        return
    for o, aenderung in umtypen + auch_kneipe + auch_restaurant:
        db.table("orte").update(aenderung).eq("id", o["id"]).execute()
    logger.info("E1 gesetzt: %d umgetypt, %d auch_kneipe, %d auch_restaurant", len(umtypen), len(auch_kneipe), len(auch_restaurant))


def main():
    parser = argparse.ArgumentParser(description="Brauhäuser/Gastropubs in beiden Guides (E1)")
    parser.add_argument("--dry-run", action="store_true")
    ausfuehren(parser.parse_args().dry_run)


if __name__ == "__main__":
    main()
