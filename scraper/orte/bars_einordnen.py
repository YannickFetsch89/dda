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

# Düsseldorfer Altbier-Hausbrauereien – feste Regel über den Hausnamen. Bewusst NICHT das Wort
# „Brauerei“: sonst würde jede Brauerei (auch Kölsch oder Craft) zur Altbier-Adresse.
# Die fünf Häuser sind vollständig (Schlösser, Frankenheim sind Marken). Filialen wie „Schumacher
# Gerresheim“ zählen mit; fremde Betriebe mit gleichem Namen (Café, Hotel …) nicht.
HAUSBRAUEREIEN = re.compile(r"\b(uerige|f[üu]chschen|schumacher|schl[üu]ssel|k[üu]rzer)\b", re.IGNORECASE)
KEINE_BRAUEREI = re.compile(r"caf[eé]|kaffee|hotel|hostel|pension|restaurant|pizzeria|imbiss|b[äa]ckerei|konditorei"
                            r"|metzgerei|eiscaf|eisdiele|friseur|apotheke", re.IGNORECASE)

# Happy Hour und Raucher brauchen wie die Merkmale ein passendes Stichwort im Zitat – sonst würde
# „seit 17 Jahren“ eine Happy Hour „17 Uhr“ oder „tolle Terrasse“ einen Raucherbereich belegen.
# Nicht „zum halben (Preis)“: trifft auch „zum halben Liter“ und „nicht zum halben Preis“.
HAPPY_HOUR_STICHWORT = r"happy ?-?hour|2[- ]?f[üu]r[- ]?1|zwei f[üu]r eins|two for one"
# Nur Formen, die das Rauchen selbst meinen – nicht Rauchbier, rauchfrei, Rauchverbot.
# Nicht „smoking“: im Deutschen meist der Anzug („im Smoking“).
RAUCHER_STICHWORT = r"raucher|rauchen|geraucht|zigarette|zigarre|aschenbecher|qualm|smoker"
# Belegt das Gegenteil (geprüft nach Entfernen der Bindestriche: „Nicht-Raucher“ = „nichtraucher“)
RAUCHER_GEGENTEIL = r"nichtraucher|rauchfrei|rauchverbot|nicht geraucht|kein raucher|keine raucher"


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
    name = ort.get("name") or ""
    if HAUSBRAUEREIEN.search(name) and not KEINE_BRAUEREI.search(name) and ort.get("stadtteil") not in ("Neuss", "Ratingen"):
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


# Ein KI-Merkmal zählt nur, wenn sein Zitat ein passendes Stichwort enthält. Sonst reicht allgemeines
# Lob („tolle Stimmung“) als Beleg – und fast jede Bar wäre „gesellig“ oder „gemütlich“.
STICHWORTE = {
    # Wortgrenzen, wo ein Stichwort sonst in anderen Wörtern steckt („principal“, „Schweinshaxe“,
    # „Kindergarten“, „besonnen“, „sportlich“, „traurig“). Nicht das bloße Wort „alt“ („sehr alt“).
    "Craft Beer": r"craft|\bipas?\b|pale ale|stout|zapfh[äa]hn|biersorten|bierauswahl|auswahl an bier|selbst ?gebraut|hausgebraut",
    "Cocktails": r"cocktail|mixolog|longdrink|gin ?tonic|aperol|negroni|mojito|spritz",
    # „Alt“ nur als Bier: nach Artikel, Marke, Bier-Adjektiv, Gefäß oder Menge („Schumacher Alt“, „das Alt
    # war lecker“, „eine Stange Alt“, „0,2 Alt“, „0,2l Alt“) – nicht „sehr alt“, „1890 alt“, „im Herbst alt“.
    # Mengen nur als Dezimalzahl oder mit Liter-Angabe; kein „Dom“ (Kölsch-Marke, in Düsseldorf die Kirche).
    "Altbier": (r"altbier|\balts\b|k[öo]bes|\balt vom fass|\b(das|ein|dem|den|sein|ihr|mein|frisch\w*|lecker\w*"
                r"|gezapft\w*|gebraut\w*|gek[üu]hlt\w*|k[üu]hl\w*|gut\w*|herb(?:e|es|em|en)?|kleine[sn]?|stange|glas"
                r"|d[üu]sseldorfer|schumacher|schuhmacher|f[üu]chschen|f[üu]chsen|frankenheim\w*|uerige|schl[üu]ssel"
                r"|k[üu]rzer|bolten|\d,\d+(?: ?l)?|\d{1,2} ?l)[- ]alt\b"),
    # nicht „Schwein“, „zum Weinen“, Tippfehler „Weinachten“ – aber „Auswahl an Weinen“ und „zum Wein“
    "Wein": r"(?<!sch)(?<!zum )wein(?!achten)|zum wein(?!en)|riesling|winzer|\bvino\b|\bwine\b",
    "Whisky": r"whisk",
    "Gemütlich": r"gem[üu]tlich|\burig|heimelig|kuschelig|wohnzimmer|kamin|kerzen",
    "Gesellig": r"gesellig|stammtisch|live ?-?musik|livemusik|\bband\b|konzert|karaoke|quiz|kicker|\bdart|billard|tanzen|\bparty|ins gespr[äa]ch|kennenlernen|schunkel",
    "Draußen sitzen": r"drau(ß|ss)en|terrasse|biergarten|\bgarten(?:lokal)?\b|au(ß|ss)enbereich|im freien|\bsonne\b",
    "Sportsbar": r"fu(ß|ss)ball|bundesliga|sportbar|sportsbar|\bsport(?!lich|wagen)|leinwand|beamer|fernseher|\btv\b|übertrag|fortuna|\bdeg\b|champions",
}


def stichwort_passt(wert: str, zitat: str | None) -> bool:
    """Enthält das Zitat ein Stichwort, das zum Merkmal passt?"""
    muster = STICHWORTE.get(wert)
    return bool(muster and re.search(muster, _norm(zitat or "")))


def _als_uhrzeit(zahl: str, text: str) -> bool:
    """Steht die Zahl im Text als Uhrzeit („17 Uhr“, „17-19“, „von 17“, „bis 20:30“) – nicht „seit 17 Jahren“?"""
    return bool(re.search(rf"(?:\bab|\bbis|\bvon|\bum|zwischen) ?{zahl}\b|\b{zahl}(?:[:.]\d\d)? ?(?:uhr|h\b|-|bis\b)", text))


def happy_hour_belegt(zeit: str, zitat: str | None, quelle: str) -> bool:
    """Zitat steht im Text, nennt „Happy Hour“ (o. ä.) und enthält alle Zahlen der Zeitangabe als Uhrzeit."""
    z = _norm(zitat or "")
    ziffern = re.findall(r"\d{1,2}", zeit or "")
    return (belegt(zitat, quelle) and bool(ziffern) and all(_als_uhrzeit(d, z) for d in ziffern)
            and bool(re.search(HAPPY_HOUR_STICHWORT, z)))


def raucher_belegt(zitat: str | None, quelle: str) -> bool:
    """
    Zitat steht im Text und eine seiner Klauseln spricht vom Rauchen, ohne das Gegenteil zu sagen.
    Klauselweise, damit „Rauchverbot drinnen, Raucherbereich draußen“ den Raucherbereich belegt.
    """
    if not belegt(zitat, quelle):
        return False
    z = _norm(zitat or "").replace("-", "")
    klauseln = re.split(r"[,;.!?]| aber | jedoch | dafür ", z)
    return any(re.search(RAUCHER_STICHWORT, k) and not re.search(RAUCHER_GEGENTEIL, k) for k in klauseln)

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
    belege: dict = {}

    if ki:
        for m in ki.get("merkmale") or []:
            wert = m.get("wert")
            if wert not in SPEZIALITAETEN + VIBES:
                continue
            if not belegt(m.get("zitat"), quelle):
                verworfen.append(f"{wert} (Zitat nicht im Text)")
                continue
            if not stichwort_passt(wert, m.get("zitat")):
                verworfen.append(f"{wert} (Zitat passt nicht zum Merkmal)")
                continue
            (spez if wert in SPEZIALITAETEN else vibes).add(wert)
            belege[wert] = m["zitat"].strip()

        zeit, zitat = (ki.get("happy_hour_zeit") or "").strip(), ki.get("happy_hour_zitat") or ""
        if zeit:
            if happy_hour_belegt(zeit, zitat, quelle):
                extras["happy_hour"] = {"text": zeit, "beleg": zitat.strip(), "quelle": "ki"}
            else:
                verworfen.append(f"Happy Hour {zeit} (kein Beleg)")

        raucher, r_zitat = ki.get("raucher"), ki.get("raucher_zitat") or ""
        if raucher in ("innen", "aussen"):
            if raucher_belegt(r_zitat, quelle):
                extras["raucher"] = {"wert": raucher, "beleg": r_zitat.strip(), "quelle": "ki"}
            else:
                verworfen.append(f"Raucher {raucher} (kein Beleg)")

        if ki.get("unterart") in ("kneipe", "bar"):
            extras["unterart"] = ki["unterart"]
        beschreibung = (ki.get("beschreibung") or "").strip()
        if 60 <= len(beschreibung) <= 400:
            spalten["beschreibung"] = beschreibung
        highlight = (ki.get("highlight") or "").strip()
        if 10 <= len(highlight) <= 160:
            spalten["highlight"] = highlight
    # Brauhaus ist eine feste Regel (Primärtyp/Name) und hat Vorrang vor der KI
    if ist_brauhaus((ort.get("extras") or {}).get("google_primaertyp"), ort.get("name")):
        extras["unterart"] = "brauhaus"
    # Restaurants, die zusätzlich im Kneipen-Hub stehen, behalten ihre Texte (Restaurant-Guide);
    # KI-Texte nur dort, wo noch keiner steht
    if ort.get("typ") != "kneipe":
        spalten = {k: v for k, v in spalten.items() if not (ort.get(k) or "").strip()}

    extras["spezialitaeten"] = [s for s in SPEZIALITAETEN if s in spez]
    extras["vibes"] = [v for v in VIBES if v in vibes]
    # Zitate aufheben: spätere Regeländerungen lassen sich dann ohne neuen KI-Lauf nachprüfen
    extras["merkmal_belege"] = belege
    return extras, spalten, verworfen


# ── Lauf ──────────────────────────────────────────────────────────────────────

def einordnen(max_anzahl: int, dry_run: bool, neu: bool) -> dict:
    import anthropic

    from database.client import get_supabase_client

    db = get_supabase_client()
    # Kneipen und Restaurants, die zusätzlich im Kneipen-Hub stehen (Brauhäuser, Gastropubs – E1)
    orte = [o for o in alle_zeilen(db, "orte", "id, name, typ, stadtteil, beschreibung, highlight, extras")
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
            # Alte Happy-Hour-/Raucher-Angaben verwerfen: bei --neu gilt nur, was diese Einordnung belegt
            alt = {k: v for k, v in (o.get("extras") or {}).items() if k not in ("happy_hour", "raucher")}
            neu_extras = {**alt, **extras,
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
