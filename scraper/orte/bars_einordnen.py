"""
bars_einordnen.py – DiesDasDüsseldorf
Ordnet Kneipen & Bars ein: Spezialitäten, Vibes, Happy Hour, Raucherbereich, Beschreibung, Highlight.

Zweistufig:
  1. Regeln aus Google-Signalen (Primärtyp, servesCocktails, outdoorSeating …) – sicher, ohne KI.
  2. KI (Claude Haiku) für das, was Google nicht liefert – NUR mit wörtlichem Textbeleg.
     Der Code prüft, dass jedes Zitat wirklich in Google-Zusammenfassung oder Bewertungen steht;
     ohne Beleg wird die Angabe verworfen (Entscheidung E6: belegt reicht, keine manuelle Bestätigung).

Nutzung:
  python -m scraper.orte.bars_einordnen [--dry-run] [--max 50] [--neu]
Nur Orte mit typ='kneipe' ohne extras.ki_einordnung (mit --neu: alle).
"""
import argparse
import json
import logging
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scraper.orte.bars import ist_brauhaus  # noqa: E402
from scraper.orte.google_places import alle_zeilen  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

MODELL = "claude-haiku-5-5"

SPEZIALITAETEN = ["Craft Beer", "Cocktails", "Altbier", "Wein", "Whisky"]
VIBES = ["Gemütlich", "Gesellig", "Draußen sitzen", "Sportsbar"]
# Diese Angaben darf die KI nur mit Textbeleg setzen (die übrigen kommen sicher aus Google-Signalen)
KI_MIT_BELEG = {"Craft Beer", "Altbier", "Whisky", "Wein", "Cocktails", "Gemütlich", "Gesellig", "Sportsbar", "Draußen sitzen"}

# Düsseldorfer Hausbrauereien (Altbier) – feste Regel über den Namen
HAUSBRAUEREIEN = re.compile(r"\b(uerige|f[üu]chschen|schumacher|schl[üu]ssel|k[üu]rzer|brauerei|hausbrauerei)\b", re.IGNORECASE)


# ── Regeln aus Google-Signalen ────────────────────────────────────────────────

def _signal(extras: dict, feld: str) -> bool:
    return (extras.get("google_bar") or {}).get(feld) is True or (extras.get("google_ausstattung") or {}).get(feld) is True


def regeln(ort: dict) -> tuple[set[str], set[str]]:
    """(Spezialitäten, Vibes) allein aus Google-Daten und Name."""
    ex = ort.get("extras") or {}
    p = ex.get("google_primaertyp") or ""
    spez, vibes = set(), set()
    if p == "cocktail_bar" or _signal(ex, "servesCocktails"):
        spez.add("Cocktails")
    if p == "wine_bar":
        spez.add("Wein")
    if p == "brewpub":
        spez.add("Craft Beer")
    if HAUSBRAUEREIEN.search(ort.get("name") or "") and ort.get("stadtteil") not in ("Neuss", "Ratingen"):
        spez.add("Altbier")
    if _signal(ex, "outdoorSeating") or p == "beer_garden":
        vibes.add("Draußen sitzen")
    # „Gut zum Sportschauen“ allein macht aus einer Wein- oder Cocktailbar keine Sportsbar
    if p == "sports_bar" or (_signal(ex, "goodForWatchingSports") and p not in ("bar", "cocktail_bar", "wine_bar", "lounge_bar")):
        vibes.add("Sportsbar")
    # „Gut für Gruppen“ setzt Google bei fast jeder Bar – als Merkmal wertlos. Gesellig nur bei Live-Musik
    # (sonst über die KI mit Textbeleg)
    if _signal(ex, "liveMusic"):
        vibes.add("Gesellig")
    return spez, vibes


# ── Belegprüfung ──────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    """Für den Textvergleich: Kleinschreibung, einheitliche Anführungszeichen/Striche, einfacher Leerraum."""
    t = unicodedata.normalize("NFKC", text or "").lower()
    t = re.sub(r"[„“”«»\"']", "", t)
    t = re.sub(r"[‐‑‒–—]", "-", t)
    return re.sub(r"\s+", " ", t).strip()


def belegt(zitat: str | None, quelltext: str, min_laenge: int = 8) -> bool:
    """Steht das Zitat (mind. min_laenge Zeichen) wörtlich im Quelltext?"""
    z = _norm(zitat or "")
    return len(z) >= min_laenge and z in _norm(quelltext)


def quelltext(ort: dict) -> str:
    """Alles, worauf sich die KI stützen darf: Google-Zusammenfassung und Bewertungstexte."""
    ex = ort.get("extras") or {}
    teile = [ex.get("google_zusammenfassung") or ""]
    teile += [b.get("text") or "" for b in ex.get("google_bewertungen") or []]
    return "\n".join(t for t in teile if t)


# ── KI ────────────────────────────────────────────────────────────────────────

SCHEMA = {
    "type": "object",
    "properties": {
        "unterart": {"type": "string", "enum": ["kneipe", "bar"]},
        "merkmale": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "wert": {"type": "string", "enum": SPEZIALITAETEN + VIBES},
                    "zitat": {"type": "string"},
                },
                "required": ["wert", "zitat"],
                "additionalProperties": False,
            },
        },
        "happy_hour_zeit": {"type": "string"},
        "happy_hour_zitat": {"type": "string"},
        "raucher": {"type": "string", "enum": ["innen", "aussen", "unbekannt"]},
        "raucher_zitat": {"type": "string"},
        "beschreibung": {"type": "string"},
        "highlight": {"type": "string"},
    },
    "required": ["unterart", "merkmale", "happy_hour_zeit", "happy_hour_zitat", "raucher", "raucher_zitat",
                 "beschreibung", "highlight"],
    "additionalProperties": False,
}

SYSTEM = """Du ordnest Kneipen und Bars in Düsseldorf für den Stadtguide dies.das.düsseldorf ein.
Du bekommst Name, Google-Typ, Stadtteil, die Google-Kurzbeschreibung und einige Bewertungstexte.

Regeln:
- Stütze dich NUR auf die gelieferten Texte. Erfinde nichts.
- „merkmale“: nur Merkmale, die ein Text klar belegt. Zu jedem Merkmal ein WÖRTLICHES Zitat (5–20 Wörter,
  exakt so wie im Text, nicht umformuliert). Ohne passende Textstelle: Merkmal weglassen.
  Altbier nur bei einer ausgesprochenen Altbier-Kneipe oder Hausbrauerei, nicht weil es Alt „auch gibt“.
- Happy Hour: nur wenn ein Text eine Happy Hour mit Uhrzeit nennt. Dann „happy_hour_zeit“ kurz wie
  „17–19 Uhr“ und „happy_hour_zitat“ wörtlich mit der Uhrzeit. Sonst beide leer lassen.
- Raucher: „innen“ nur, wenn ein Text sagt, dass drinnen geraucht werden darf (z.B. „Raucherkneipe“);
  „aussen“ nur, wenn ein Text ausdrücklich einen Raucherbereich draußen nennt. Ein Biergarten oder eine
  Terrasse allein ist KEIN Raucherbereich. Sonst „unbekannt“ und Zitat leer.
- „unterart“: „kneipe“ (Kneipe, Pub, Biergarten, Sportsbar) oder „bar“ (Cocktail-, Wein-, Lounge-Bar).
  Brauhäuser erkennt der Code selbst.
- „beschreibung“: 150–300 Zeichen auf Deutsch, locker und einladend, keine Werbesprache, keine
  Superlative, kein „Geheimtipp“, keine Sterne/Bewertungszahlen, keine Öffnungszeiten oder Preise.
  Nur Dinge, die in den Texten stehen.
- „highlight“: ein Satz (max. 120 Zeichen), was den Ort besonders macht – ebenfalls nur aus den Texten."""


def ki_anfrage(client, ort: dict) -> dict:
    """Eine Anfrage an Claude mit festem JSON-Schema; gibt das geparste JSON zurück."""
    ex = ort.get("extras") or {}
    bewertungen = "\n".join(f"- {b.get('text')}" for b in (ex.get("google_bewertungen") or []) if b.get("text"))
    nutzer = (
        f"Name: {ort['name']}\nGoogle-Typ: {ex.get('google_primaertyp')}\nStadtteil: {ort.get('stadtteil')}\n"
        f"Google-Kurzbeschreibung: {ex.get('google_zusammenfassung') or '–'}\n\nBewertungen:\n{bewertungen or '–'}"
    )
    antwort = client.messages.create(
        model=MODELL,
        max_tokens=4000,
        system=SYSTEM,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": nutzer}],
    )
    if antwort.stop_reason == "refusal":
        raise RuntimeError("Anfrage abgelehnt (refusal)")
    text = next(b.text for b in antwort.content if b.type == "text")
    return json.loads(text)


def zusammenfuehren(ort: dict, ki: dict | None) -> tuple[dict, dict, list[str]]:
    """
    Regeln + belegte KI-Angaben → (extras-Ergänzung, Spalten-Ergänzung, verworfene Angaben).
    Nur Werte aus den festen Listen; jede KI-Angabe nur mit geprüftem Zitat.
    """
    quelle = quelltext(ort)
    spez, vibes = regeln(ort)
    verworfen: list[str] = []
    extras: dict = {}
    spalten: dict = {}

    if ki:
        for m in ki.get("merkmale") or []:
            wert = m.get("wert")
            if wert not in SPEZIALITAETEN + VIBES:
                continue
            if not belegt(m.get("zitat"), quelle):
                verworfen.append(f"{wert} (Zitat nicht im Text)")
                continue
            (spez if wert in SPEZIALITAETEN else vibes).add(wert)

        zeit, zitat = (ki.get("happy_hour_zeit") or "").strip(), ki.get("happy_hour_zitat") or ""
        if zeit:
            ziffern = re.findall(r"\d{1,2}", zeit)
            if belegt(zitat, quelle) and ziffern and all(z in _norm(zitat) for z in ziffern):
                extras["happy_hour"] = {"text": zeit, "beleg": zitat.strip(), "quelle": "ki"}
            else:
                verworfen.append(f"Happy Hour {zeit} (kein Beleg)")

        raucher, r_zitat = ki.get("raucher"), ki.get("raucher_zitat") or ""
        if raucher in ("innen", "aussen"):
            if belegt(r_zitat, quelle):
                extras["raucher"] = {"wert": raucher, "beleg": r_zitat.strip(), "quelle": "ki"}
            else:
                verworfen.append(f"Raucher {raucher} (kein Beleg)")

        if ki.get("unterart") in ("kneipe", "bar"):
            extras["unterart"] = ki["unterart"]
    # Brauhaus ist eine feste Regel (Primärtyp/Name) und hat Vorrang vor der KI
    if ist_brauhaus((ort.get("extras") or {}).get("google_primaertyp"), ort.get("name")):
        extras["unterart"] = "brauhaus"
        beschreibung = (ki.get("beschreibung") or "").strip()
        if 60 <= len(beschreibung) <= 400:
            spalten["beschreibung"] = beschreibung
        highlight = (ki.get("highlight") or "").strip()
        if 10 <= len(highlight) <= 160:
            spalten["highlight"] = highlight

    extras["spezialitaeten"] = [s for s in SPEZIALITAETEN if s in spez]
    extras["vibes"] = [v for v in VIBES if v in vibes]
    return extras, spalten, verworfen


# ── Lauf ──────────────────────────────────────────────────────────────────────

def einordnen(max_anzahl: int, dry_run: bool, neu: bool) -> dict:
    import anthropic

    from database.client import get_supabase_client

    db = get_supabase_client()
    # Kneipen und Restaurants, die zusätzlich im Kneipen-Hub stehen (Brauhäuser, Gastropubs – E1)
    orte = [o for o in alle_zeilen(db, "orte", "id, name, typ, stadtteil, extras")
            if o["typ"] == "kneipe" or (o.get("extras") or {}).get("auch_kneipe")]
    offen = [o for o in orte if neu or not (o.get("extras") or {}).get("ki_einordnung")][:max_anzahl]
    logger.info("%d Kneipen/Bars, davon %d einzuordnen%s", len(orte), len(offen), " [Dry-Run]" if dry_run else "")
    client = anthropic.Anthropic()
    fertig = fehler = 0
    for o in offen:
        try:
            ki = ki_anfrage(client, o) if quelltext(o) else None
            extras, spalten, verworfen = zusammenfuehren(o, ki)
            if verworfen:
                logger.info("  %s: verworfen %s", o["name"], ", ".join(verworfen))
            neu_extras = {**(o.get("extras") or {}), **extras,
                          "ki_einordnung": {"modell": MODELL if ki else None,
                                            "datum": datetime.now(timezone.utc).date().isoformat(),
                                            "verworfen": verworfen}}
            if dry_run:
                print(f"{o['name'][:40]:40s} {extras.get('unterart', '?'):6s} {extras['spezialitaeten']} {extras['vibes']} "
                      f"HH={extras.get('happy_hour', {}).get('text')} R={extras.get('raucher', {}).get('wert')}")
                if spalten.get("beschreibung"):
                    print("   ", spalten["beschreibung"])
            else:
                db.table("orte").update({"extras": neu_extras, **spalten}).eq("id", o["id"]).execute()
            fertig += 1
        except Exception as e:
            fehler += 1
            logger.error("Fehler bei '%s': %s", o["name"], e)
    logger.info("Einordnung fertig: %d eingeordnet, %d Fehler", fertig, fehler)
    return {"eingeordnet": fertig, "fehler": fehler}


def brauhaeuser_nachziehen(dry_run: bool) -> int:
    """Unterart „brauhaus“ für alle Orte des Kneipen-Hubs nach der festen Regel setzen (ohne KI, kostenlos)."""
    from database.client import get_supabase_client

    db = get_supabase_client()
    orte = [o for o in alle_zeilen(db, "orte", "id, name, typ, extras")
            if o["typ"] == "kneipe" or (o.get("extras") or {}).get("auch_kneipe")]
    treffer = [o for o in orte
               if ist_brauhaus((o.get("extras") or {}).get("google_primaertyp"), o["name"])
               and (o.get("extras") or {}).get("unterart") != "brauhaus"]
    print(f"Brauhaus ({len(treffer)}):", ", ".join(o["name"][:30] for o in treffer))
    if not dry_run:
        for o in treffer:
            db.table("orte").update({"extras": {**(o.get("extras") or {}), "unterart": "brauhaus"}}).eq("id", o["id"]).execute()
    return len(treffer)


def main():
    parser = argparse.ArgumentParser(description="Kneipen & Bars einordnen (Regeln + KI mit Belegprüfung)")
    parser.add_argument("--max", type=int, default=1000, help="Höchstzahl Orte")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts speichern (KI wird aufgerufen)")
    parser.add_argument("--neu", action="store_true", help="Auch bereits eingeordnete Orte neu einordnen")
    parser.add_argument("--nur-brauhaus", action="store_true", help="Nur Unterart „brauhaus“ nach Regel nachziehen (ohne KI)")
    args = parser.parse_args()
    if args.nur_brauhaus:
        brauhaeuser_nachziehen(args.dry_run)
    else:
        einordnen(args.max, args.dry_run, args.neu)


if __name__ == "__main__":
    main()
