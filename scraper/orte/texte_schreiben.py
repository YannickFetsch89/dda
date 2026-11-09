"""
texte_schreiben.py – DiesDasDüsseldorf
Schreibt Beschreibung (mindestens 5 Sätze) und Teaser-Satz (orte.highlight, im Guide in Gold über dem
Text) für Orte der Guide-Hubs – mit Claude Haiku, ausschließlich aus Google-Kurzbeschreibung und
Google-Bewertungstexten.

Absicherung wie bei bars_einordnen.py:
  - Die KI nennt zu jedem Text wörtliche Zitate aus den Quelltexten; der Code prüft, dass sie dort
    wirklich stehen (mindestens 2 von 3), sonst wird der Text verworfen.
  - Länge, Satzzahl und verbotene Inhalte (Bewertungszahlen, Preise, Uhrzeiten, Superlative-Floskeln)
    werden im Code geprüft – verworfene Texte werden nicht gespeichert.

Nutzung:
  python -m scraper.orte.texte_schreiben --stichprobe 10 --ausgabe datei.md   # nichts speichern
  python -m scraper.orte.texte_schreiben --hub restaurants [--max 50] [--neu] [--dry-run]
  python -m scraper.orte.texte_schreiben --hub kneipen [--neu]
Ohne --neu nur Orte ohne extras.ki_text.
"""
import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scraper.orte.bars_einordnen import _norm, belegt, quelltext  # noqa: E402
from scraper.orte.google_places import alle_zeilen  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

MODELL = "claude-haiku-5-5"
# Preise Claude Haiku 5.5 (Prompt ≤ 100K Tokens), US-$ pro Million Tokens – nur für die Kostenanzeige
PREIS_EIN, PREIS_AUS = 0.10, 0.50
MIN_SCORE_WEBSITE = 7
TYP_NAME = {"restaurant": "Restaurant", "cafe": "Café", "imbiss": "Schnellimbiss", "kneipe": "Kneipe/Bar"}

SCHEMA = {
    "type": "object",
    "properties": {
        "beschreibung": {"type": "string"},
        "highlight": {"type": "string"},
        "belege": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["beschreibung", "highlight", "belege"],
    "additionalProperties": False,
}

SYSTEM = """Du schreibst Texte für den Düsseldorfer Stadtguide dies.das.düsseldorf.
Du bekommst Name, Art, Stadtteil, die Google-Kurzbeschreibung und mehrere Gästebewertungen eines Ortes.

Schreibe:
- „beschreibung“: 5 bis 7 Sätze (etwa 550–900 Zeichen) auf Deutsch. Locker, einladend und konkret, wie
  ein guter Tipp von Freunden. Inhalt nur aus den gelieferten Texten: Küche, typische Gerichte oder
  Getränke, Atmosphäre, Einrichtung, Service, Lage, für wen oder welchen Anlass der Ort passt.
  Erfinde nichts – keine Gerichte, Namen, Geschichte oder Details, die nicht in den Texten stehen.
  Gibt das Material wenig her, bleib bei dem, was belegt ist, und beschreibe es ausführlicher statt
  Neues hinzuzudichten. Schreib nie, dass Angaben fehlen oder etwas „nicht bekannt“ ist.
  Es ist ein Empfehlungs-Guide: lass Kritik, Beschwerden, gemischte Meinungen und einzelne negative
  Erfahrungen weg; beschreibe, was den Ort ausmacht.
  Schreib in eigener Stimme als Empfehlung („Die Schnitzel kommen knusprig auf den Tisch“), nicht als
  Bericht über Bewertungen: Formulierungen wie „Gäste loben“, „laut Bewertungen“ höchstens einmal,
  nie einzelne Gäste („ein Gast empfiehlt …“).
  Nicht erlaubt: Sterne, Bewertungszahlen, Preise und Preisniveau („teuer“, „günstig“, „Preise im
  oberen Bereich“, „Preis-Leistung“), Öffnungszeiten, Telefonnummern, Wartezeiten, Werbesprache,
  Superlative („der beste“, „einzigartig“), „Geheimtipp“, Ausrufezeichen, Anrede mit „Sie“.
  Duze die Leser höchstens sparsam. Nenne den Namen des Ortes höchstens einmal.
- „highlight“: ein einzelner Satz (höchstens 120 Zeichen), was den Ort besonders macht – ein Teaser,
  der neugierig macht. Ebenfalls nur aus den Texten, ohne Namen des Ortes.
- „belege“: genau 3 kurze WÖRTLICHE Zitate (je 4–12 Wörter, exakt wie im Text, nicht umformuliert)
  aus Kurzbeschreibung oder Bewertungen, auf die sich Beschreibung und Highlight stützen."""

VERBOTEN = re.compile(
    r"\b\d[,.]\d\b|\bsterne\b|\bgeheimtipp\b|€|\beuro\b|\b\d{1,2}[:.]\d{2}\b|\buhr\b|!|"
    r"\bder beste\b|\bdie beste\b|\bdas beste\b|\beinzigartig|"
    # Preise, Kritik, Meta-Sätze über fehlende Angaben, einzelne Gäste
    r"preis|\bteuer|\bgünstig|\bkritik|\bbemängel|\bleider\b|\bnegativ|keine (?:weiteren )?angaben|nicht bekannt|"
    r"\bein gast\b|\beine gästin\b",
    re.IGNORECASE,
)
# Unter dieser Menge Quelltext (Google-Kurzbeschreibung + Bewertungen) gibt es keinen KI-Text – das
# Material reicht nicht für 5 gehaltvolle Sätze (betrifft 2 von 683 sichtbaren Orten, Stand 09.11.2026)
MIN_QUELLTEXT = 500


def saetze(text: str) -> int:
    """Grobe Satzzahl (Satzende . ? ! vor Leerraum oder Textende)."""
    return len([s for s in re.split(r"(?<=[.?!])\s+", text.strip()) if len(s.strip()) > 2])


def pruefen(ort: dict, ki: dict) -> tuple[dict, list[str]]:
    """Prüft die KI-Antwort; gibt (Spalten, Mängel) zurück. Spalten nur ohne Mängel."""
    quelle = quelltext(ort)
    beschreibung = (ki.get("beschreibung") or "").strip()
    highlight = (ki.get("highlight") or "").strip()
    belege = [b for b in (ki.get("belege") or []) if belegt(b, quelle)]
    maengel = []
    if not 450 <= len(beschreibung) <= 1100:
        maengel.append(f"Länge {len(beschreibung)} Zeichen")
    if saetze(beschreibung) < 5:
        maengel.append(f"nur {saetze(beschreibung)} Sätze")
    if not 10 <= len(highlight) <= 140:
        maengel.append(f"Highlight {len(highlight)} Zeichen")
    for feld, text in (("Beschreibung", beschreibung), ("Highlight", highlight)):
        treffer = VERBOTEN.search(text)
        if treffer:
            maengel.append(f"{feld} enthält „{treffer.group(0)}“")
    if len(belege) < 2:
        maengel.append(f"nur {len(belege)} von 3 Zitaten belegt")
    bericht = len(re.findall(r"gäste (?:loben|schätzen|beschreiben|heben)|laut (?:gästen|bewertungen)", beschreibung, re.IGNORECASE))
    if bericht > 1:
        maengel.append(f"{bericht}× „Gäste loben/laut Bewertungen“")
    if _norm(ort["name"]) in _norm(highlight):
        maengel.append("Name im Highlight")
    return ({} if maengel else {"beschreibung": beschreibung, "highlight": highlight}), maengel


def ki_anfrage(client, ort: dict) -> tuple[dict, dict]:
    """Eine Anfrage mit festem JSON-Schema; gibt (Antwort, Token-Verbrauch) zurück."""
    ex = ort.get("extras") or {}
    bewertungen = "\n".join(f"- {b.get('text')}" for b in (ex.get("google_bewertungen") or []) if b.get("text"))
    nutzer = (
        f"Name: {ort['name']}\nArt: {TYP_NAME.get(ort['typ'], ort['typ'])} (Google-Typ: {ex.get('google_primaertyp')})\n"
        f"Stadtteil: {ort.get('stadtteil')}\n"
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
    if antwort.stop_reason == "max_tokens":
        raise RuntimeError("Antwort abgeschnitten (max_tokens)")
    text = next(b.text for b in antwort.content if b.type == "text")
    verbrauch = {"ein": antwort.usage.input_tokens, "aus": antwort.usage.output_tokens}
    return json.loads(text), verbrauch


def kosten(verbrauch: list[dict]) -> float:
    return sum(v["ein"] for v in verbrauch) / 1e6 * PREIS_EIN + sum(v["aus"] for v in verbrauch) / 1e6 * PREIS_AUS


def orte_laden(db, hub: str, nur_sichtbar: bool) -> list[dict]:
    spalten = "id, name, typ, aktiv, qualitaets_score, stadtteil, beschreibung, highlight, extras"
    orte = alle_zeilen(db, "orte", spalten)
    if hub == "kneipen":
        # Nur echte Kneipen – Restaurants mit auch_kneipe bekommen ihren Text im Restaurant-Lauf
        orte = [o for o in orte if o["typ"] == "kneipe"]
    else:
        orte = [o for o in orte if o["typ"] in ("restaurant", "cafe", "imbiss")]
    if nur_sichtbar:
        orte = [o for o in orte if o["aktiv"] and (o.get("qualitaets_score") or 0) >= MIN_SCORE_WEBSITE]
    return [o for o in orte if len(quelltext(o)) >= MIN_QUELLTEXT]


def stichprobe_waehlen(orte: list[dict], anzahl: int) -> list[dict]:
    """Gemischt: viel, mittel und wenig Bewertungstext; Restaurants und Cafés."""
    sortiert = sorted(orte, key=lambda o: len(quelltext(o)))
    cafes = [o for o in sortiert if o["typ"] == "cafe"]
    rest = [o for o in sortiert if o["typ"] != "cafe"]
    n_cafe = max(1, anzahl * 3 // 10)
    def verteilt(liste, n):
        if not liste or n <= 0:
            return []
        schritt = max(1, (len(liste) - 1) / max(1, n - 1))
        return [liste[min(len(liste) - 1, round(i * schritt))] for i in range(n)]
    return verteilt(rest, anzahl - n_cafe) + verteilt(cafes, n_cafe)


def stichprobe(anzahl: int, ausgabe: str) -> None:
    import anthropic

    from database.client import get_supabase_client

    db = get_supabase_client()
    client = anthropic.Anthropic()
    auswahl = stichprobe_waehlen(orte_laden(db, "restaurants", nur_sichtbar=True), anzahl)
    verbrauch, zeilen = [], [f"# Stichprobe Restaurant- und Café-Texte ({datetime.now():%d.%m.%Y})", "",
                             f"Modell: {MODELL}. Nichts davon ist gespeichert.", ""]
    for o in auswahl:
        try:
            ki, v = ki_anfrage(client, o)
            verbrauch.append(v)
        except Exception as e:
            zeilen += [f"## {o['name']}", f"Fehler: {e}", ""]
            continue
        _, maengel = pruefen(o, ki)
        zeilen += [
            f"## {o['name']} ({TYP_NAME.get(o['typ'])}, {o.get('stadtteil')})",
            f"Quelltext: {len(quelltext(o))} Zeichen · Prüfung: {'bestanden' if not maengel else 'VERWORFEN – ' + ', '.join(maengel)}",
            "",
            f"**Teaser (Gold):** {ki.get('highlight')}",
            "",
            ki.get("beschreibung") or "",
            "",
            f"*Bisher:* {o.get('beschreibung') or '– (kein Text)'}",
            "",
            "*Belege:* " + " | ".join(f"„{b}“" for b in ki.get("belege") or []),
            "",
        ]
        logger.info("%s: %s", o["name"], "ok" if not maengel else ", ".join(maengel))
    zeilen.insert(3, f"Verbrauch: {sum(v['ein'] for v in verbrauch)} Eingabe-, {sum(v['aus'] for v in verbrauch)} Ausgabe-Tokens "
                     f"≈ {kosten(verbrauch):.4f} $ für {len(verbrauch)} Orte ({kosten(verbrauch) / max(1, len(verbrauch)) * 1000:.2f} $ pro 1.000 Orte)\n")
    Path(ausgabe).write_text("\n".join(zeilen), encoding="utf-8")
    print(f"Stichprobe geschrieben: {ausgabe}")


def schreiben(hub: str, max_anzahl: int, neu: bool, dry_run: bool) -> dict:
    import anthropic

    from database.client import get_supabase_client

    db = get_supabase_client()
    client = anthropic.Anthropic()
    orte = orte_laden(db, hub, nur_sichtbar=False)
    offen = [o for o in orte if neu or not (o.get("extras") or {}).get("ki_text")][:max_anzahl]
    logger.info("%d Orte, davon %d zu schreiben%s", len(orte), len(offen), " [Dry-Run]" if dry_run else "")
    verbrauch, fertig, verworfen, fehler = [], 0, 0, 0
    for o in offen:
        try:
            ki, v = ki_anfrage(client, o)
            verbrauch.append(v)
            spalten, maengel = pruefen(o, ki)
            if maengel:
                # Ein zweiter Versuch – die Antworten streuen, oft passt der nächste Text
                logger.info("  %s: zweiter Versuch (%s)", o["name"], ", ".join(maengel))
                ki, v = ki_anfrage(client, o)
                verbrauch.append(v)
                spalten, maengel = pruefen(o, ki)
            if maengel:
                verworfen += 1
                logger.info("  %s: verworfen (%s)", o["name"], ", ".join(maengel))
                continue
            extras = {**(o.get("extras") or {}), "ki_text": {"modell": MODELL, "datum": datetime.now(timezone.utc).date().isoformat()}}
            if dry_run:
                print(f"{o['name'][:40]}: {spalten['highlight']}")
            else:
                db.table("orte").update({**spalten, "extras": extras}).eq("id", o["id"]).execute()
            fertig += 1
        except Exception as e:
            fehler += 1
            logger.error("Fehler bei '%s': %s", o["name"], e)
    logger.info("Texte fertig: %d geschrieben, %d verworfen, %d Fehler, Kosten ≈ %.3f $", fertig, verworfen, fehler, kosten(verbrauch))
    return {"geschrieben": fertig, "verworfen": verworfen, "fehler": fehler}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hub", choices=["restaurants", "kneipen"], default="restaurants")
    parser.add_argument("--stichprobe", type=int, help="Nur Stichprobe erzeugen (nichts speichern)")
    parser.add_argument("--ausgabe", default="stichprobe-texte.md", help="Datei für die Stichprobe")
    parser.add_argument("--max", type=int, default=5000)
    parser.add_argument("--neu", action="store_true", help="Auch Orte mit vorhandenem KI-Text neu schreiben")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.stichprobe:
        stichprobe(args.stichprobe, args.ausgabe)
    else:
        schreiben(args.hub, args.max, args.neu, args.dry_run)


if __name__ == "__main__":
    main()
