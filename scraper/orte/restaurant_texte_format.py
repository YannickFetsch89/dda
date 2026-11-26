"""
restaurant_texte_format.py – DiesDasDüsseldorf
Bringt die Texte des Restaurant-Guides (Restaurants, Cafés, Imbisse) in die neue Form: Absätze an
sinnvollen Stellen und einige Schlagwörter in **fett** (Wunsch des Auftraggebers, 26.11.2026).

Der Wortlaut bleibt garantiert gleich: Die KI liefert nur, NACH welchen Sätzen ein Absatz beginnt und
welche wörtlichen Stellen fett werden. Eingesetzt wird beides im Code; am Ende wird geprüft, dass der
Text ohne „**“ und Umbrüche genau dem alten entspricht. Texte, die das nicht erfüllen, fallen heraus.
Kurze Texte (weniger als 5 Sätze) werden NICHT verlängert, sie bekommen nur Fett (Absätze erst ab 5 Sätzen).

Schreibt nichts in die Datenbank. Liest Supabase (nur lesen) mit den Schlüsseln aus web/.env.local.

Nutzung (im Repo-Stamm, Python aus DD/.venv):
  python -m scraper.orte.restaurant_texte_format --max 10          → nur die ersten 10 (Test)
  python -m scraper.orte.restaurant_texte_format                   → alle sichtbaren Orte
  python -m scraper.orte.restaurant_texte_format --nur-ausgabe     → aus vorhandenen Ergebnissen neu bauen
Ergebnis: data/restaurant_texte/ergebnis.json, docs/restaurant-texte-vorschau-<datum>.md,
          database/orte_texte_restaurants_<datum>.sql (mit Sicherungstabelle, Ausführung durch den Auftraggeber)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path("web/.env.local"))
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

MODELL = "claude-opus-5-5"
TYPEN = ("restaurant", "cafe", "imbiss")
MIN_SCORE_WEBSITE = 7
ORDNER = Path("data/restaurant_texte")
ERGEBNIS = ORDNER / "ergebnis.json"
MIN_SAETZE_ABSATZ = 5

SCHEMA = {
    "type": "object",
    "properties": {
        "absatz_nach": {"type": "array", "items": {"type": "integer"}},
        "fett": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["absatz_nach", "fett"],
    "additionalProperties": False,
}

SYSTEM = """Du gestaltest Texte für den Düsseldorfer Stadtguide dies.das.düsseldorf neu, OHNE ein Wort zu ändern.
Du bekommst einen Text über ein Restaurant, Café oder einen Imbiss, aufgeteilt in nummerierte Sätze.

Gib zurück:
- „absatz_nach“: Nummern der Sätze, NACH denen ein neuer Absatz beginnen soll. Nur bei Texten ab 5 Sätzen,
  dann 1 oder 2 Einträge (also 2 oder 3 Absätze), jeder Absatz mit mindestens 2 Sätzen. Absätze gehören an
  inhaltliche Wechsel (z. B. Essen → Atmosphäre/Service → für wen es passt). Bei weniger als 5 Sätzen: [].
- „fett“: 3 bis 5 Schlagwörter (bei Texten unter 5 Sätzen 2 bis 3), die ein Leser beim Überfliegen sehen soll:
  Spezialitäten, Küche, besondere Merkmale, für wen es passt. Jedes Schlagwort ist eine WÖRTLICHE Stelle aus
  dem Text (genau so geschrieben, 1 bis 4 Wörter), nicht der Name des Lokals, keine Füllwörter, keine
  Überschneidungen, höchstens eines pro Satz, verteilt über den Text.
"""

_ABK = re.compile(r"\b(z\.B|z\. B|u\.a|ca|bzw|Str|Nr|inkl|d\.h|usw|etc|St|Dr)\.", re.I)
_PLATZHALTER = "⁣"


def saetze(text: str) -> list[str]:
    """Teilt in Sätze; Abkürzungen (z. B., ca., Str.) beenden keinen Satz. Leerraum bleibt am Satzende erhalten."""
    geschuetzt = _ABK.sub(lambda m: m.group(0)[:-1] + _PLATZHALTER, text.strip())
    teile = re.split(r"(?<=[.!?…])\s+(?=[A-ZÄÖÜ„\"0-9])", geschuetzt)
    return [t.replace(_PLATZHALTER, ".") for t in teile if t.strip()]


def normal(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("**", "")).strip()


def anwenden(text: str, absatz_nach: list[int], fett: list[str]) -> tuple[str | None, list[str]]:
    """Setzt Absätze und Fett ein. Gibt (neuer Text oder None, Mängel) zurück."""
    maengel: list[str] = []
    s = saetze(text)
    n = len(s)
    # Absätze nur ab 5 Sätzen, jeder Absatz mindestens 2 Sätze
    grenzen = sorted({a for a in absatz_nach if isinstance(a, int) and 2 <= a <= n - 2}) if n >= MIN_SAETZE_ABSATZ else []
    grenzen = [g for i, g in enumerate(grenzen) if i == 0 or g - grenzen[i - 1] >= 2][:2]
    # Fett: wörtliche, nicht überlappende Stellen; höchstens eine je Satz (bei 1–2 Sätzen bis zu 3 je Satz)
    je_satz_max = 1 if n >= 3 else 3
    fett_je_satz: dict[int, list[str]] = {}
    for f in fett:
        f = (f or "").strip().strip("*").strip()
        if not f or len(f.split()) > 5 or len(f) > 45:
            maengel.append(f"Schlagwort verworfen: {f!r}")
            continue
        def frei(i: int, satz: str) -> bool:
            schon = fett_je_satz.get(i, [])
            return (len(schon) < je_satz_max and re.search(rf"(?<!\w){re.escape(f)}(?!\w)", satz) is not None
                    and not any(f in x or x in f for x in schon))
        treffer = next((i for i, satz in enumerate(s) if frei(i, satz)), None)
        if treffer is None:
            maengel.append(f"nicht wörtlich gefunden: {f!r}")
            continue
        fett_je_satz.setdefault(treffer, []).append(f)
    if sum(len(v) for v in fett_je_satz.values()) < (1 if n < 3 else 2):
        maengel.append("weniger als 2 Schlagwörter")
        return None, maengel
    neue_saetze = []
    for i, satz in enumerate(s):
        for f in fett_je_satz.get(i, []):
            satz = re.sub(rf"(?<!\w){re.escape(f)}(?!\w)", lambda m: f"**{m.group(0)}**", satz, count=1)
        neue_saetze.append(satz)
    absaetze, aktuell = [], []
    for i, satz in enumerate(neue_saetze, start=1):
        aktuell.append(satz)
        if i in grenzen:
            absaetze.append(" ".join(aktuell))
            aktuell = []
    absaetze.append(" ".join(aktuell))
    neu = "\n\n".join(absaetze)
    if normal(neu) != normal(text):
        maengel.append("Wortlaut weicht ab")
        return None, maengel
    return neu, maengel


def ki_anfrage(client, text: str) -> tuple[dict, dict]:
    s = saetze(text)
    nutzer = f"Anzahl Sätze: {len(s)}\n\n" + "\n".join(f"[{i}] {satz}" for i, satz in enumerate(s, start=1))
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
    roh = next(b.text for b in antwort.content if b.type == "text")
    return json.loads(roh), {"ein": antwort.usage.input_tokens, "aus": antwort.usage.output_tokens}


def orte_laden() -> list[dict]:
    from supabase import create_client
    db = create_client(os.environ["SUPABASE_URL"], os.environ.get("SUPABASE_SERVICE_KEY") or os.environ["SUPABASE_KEY"])
    zeilen, seite = [], 0
    while True:
        teil = (db.table("orte").select("id, name, slug, typ, beschreibung, qualitaets_score")
                .in_("typ", list(TYPEN)).eq("aktiv", True).gte("qualitaets_score", MIN_SCORE_WEBSITE)
                .order("id").range(seite * 1000, seite * 1000 + 999).execute().data or [])
        zeilen += teil
        if len(teil) < 1000:
            break
        seite += 1
    return [z for z in zeilen if (z.get("beschreibung") or "").strip() and "**" not in z["beschreibung"]]


def sql_wert(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def ausgabe_bauen(ergebnisse: dict, orte: dict, heute: str) -> tuple[Path, Path, int]:
    ok = {i: e for i, e in ergebnisse.items() if e.get("neu")}
    stempel = heute.replace("-", "_")
    sql = [
        f"-- Restaurant-Guide: Texte mit Absätzen und Fett (Wortlaut unverändert), erzeugt {heute}",
        "-- Erst NACH dem Deploy der Detailseite ausführen (sonst stehen live Sternchen im Text).",
        "-- Aktualisiert nur Zeilen, deren Text noch genau dem alten entspricht. Zurück: siehe Ende der Datei.",
        "begin;",
        f"create table if not exists orte_texte_sicherung_{stempel} as",
        f"  select id, beschreibung, now() as gesichert_am from orte where id in (",
        ",\n".join(f"    '{i}'" for i in ok) + ");",
    ]
    for i, e in ok.items():
        # Nur ändern, wenn der Text seit dem Lauf gleich geblieben ist (md5 statt des ganzen alten Textes → halbe Dateigröße)
        alt_md5 = hashlib.md5(e["alt"].encode("utf-8")).hexdigest()
        sql.append(f"update orte set beschreibung = {sql_wert(e['neu'])} where id = '{i}' and md5(beschreibung) = '{alt_md5}';")
    sql += [
        "commit;",
        "",
        "-- Prüfung: so viele Texte haben jetzt Fett",
        f"select count(*) as mit_fett from orte where id in (select id from orte_texte_sicherung_{stempel}) and beschreibung like '%**%';",
        "",
        "-- Zurück (nur bei Bedarf):",
        f"-- update orte o set beschreibung = s.beschreibung from orte_texte_sicherung_{stempel} s where o.id = s.id;",
    ]
    sql_pfad = Path(f"database/orte_texte_restaurants_{heute}.sql")
    sql_pfad.write_text("\n".join(sql) + "\n", encoding="utf-8")
    md = [f"# Restaurant-Texte: Vorschau ({heute})", "",
          f"{len(ok)} Texte neu gesetzt, {len(ergebnisse) - len(ok)} ausgelassen.", ""]
    raus = [(i, e) for i, e in ergebnisse.items() if not e.get("neu")]
    if raus:
        md += ["## Ausgelassen", ""] + [f"- {orte.get(i, {}).get('name', i)}: {'; '.join(e.get('maengel') or [e.get('fehler', '?')])}" for i, e in raus] + [""]
    md += ["## Texte", ""]
    for i, e in sorted(ok.items(), key=lambda x: orte.get(x[0], {}).get("name", "")):
        o = orte.get(i, {})
        md += [f"### {o.get('name')} ({o.get('typ')})", "", e["neu"], ""]
    md_pfad = Path(f"docs/restaurant-texte-vorschau-{heute}.md")
    md_pfad.write_text("\n".join(md), encoding="utf-8")
    return sql_pfad, md_pfad, len(ok)


def main():
    p = argparse.ArgumentParser(description="Restaurant-Texte: Absätze und Fett (Wortlaut unverändert)")
    p.add_argument("--max", type=int, default=0, help="nur die ersten N Orte (Test)")
    p.add_argument("--nur-ausgabe", action="store_true", help="keine KI-Anfragen, nur SQL/Vorschau neu bauen")
    p.add_argument("--parallel", type=int, default=6)
    args = p.parse_args()

    ORDNER.mkdir(parents=True, exist_ok=True)
    ergebnisse = json.loads(ERGEBNIS.read_text(encoding="utf-8")) if ERGEBNIS.exists() else {}
    orte_liste = orte_laden()
    orte = {o["id"]: o for o in orte_liste}
    logger.info("Sichtbare Orte mit Text ohne Fett: %d (schon bearbeitet: %d)", len(orte_liste), len(ergebnisse))

    if not args.nur_ausgabe:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        offen = [o for o in orte_liste if o["id"] not in ergebnisse or ergebnisse[o["id"]].get("alt") != o["beschreibung"]
                 or not ergebnisse[o["id"]].get("neu")]
        if args.max:
            offen = offen[: args.max]
        verbrauch = []

        def arbeit(o: dict) -> tuple[str, dict]:
            try:
                antwort, v = ki_anfrage(client, o["beschreibung"])
                verbrauch.append(v)
                neu, maengel = anwenden(o["beschreibung"], antwort.get("absatz_nach", []), antwort.get("fett", []))
                return o["id"], {"alt": o["beschreibung"], "neu": neu, "maengel": maengel, "ki": antwort}
            except Exception as fehler:  # noqa: BLE001 – jeder Fehler wird je Ort protokolliert
                logger.warning("%s: %s", o["name"], fehler)
                return o["id"], {"alt": o["beschreibung"], "neu": None, "fehler": str(fehler)}

        with ThreadPoolExecutor(max_workers=args.parallel) as pool:
            for n, fertig in enumerate(as_completed([pool.submit(arbeit, o) for o in offen]), start=1):
                i, e = fertig.result()
                ergebnisse[i] = e
                if n % 25 == 0 or n == len(offen):
                    ERGEBNIS.write_text(json.dumps(ergebnisse, ensure_ascii=False, indent=1), encoding="utf-8")
                    logger.info("%d/%d bearbeitet", n, len(offen))
        ein = sum(v["ein"] for v in verbrauch)
        aus = sum(v["aus"] for v in verbrauch)
        logger.info("Token: %d ein, %d aus (≈ %.2f $ bei 4 $/20 $ je Mio.)", ein, aus, ein / 1e6 * 4 + aus / 1e6 * 20)

    sql_pfad, md_pfad, anzahl = ausgabe_bauen({i: e for i, e in ergebnisse.items() if i in orte}, orte, date.today().isoformat())
    logger.info("Fertig: %d Texte → %s, Vorschau %s", anzahl, sql_pfad, md_pfad)


if __name__ == "__main__":
    sys.exit(main())
