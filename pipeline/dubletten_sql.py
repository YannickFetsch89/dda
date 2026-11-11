"""
dubletten_sql.py – DiesDasDüsseldorf
Erzeugt SQL, das bereits gespeicherte Dubletten (ab heute) aufräumt – schreibt selbst NICHTS in die Datenbank.
Das SQL führt der Auftraggeber im Supabase-SQL-Editor aus.

Regeln wie in der Pipeline (pipeline/deduplication.py): gleicher Tag, gleicher Ortskern, fast gleicher Titel und
gleiche Uhrzeit – bei verschiedenen Quellen auch Einlass/Beginn (≤ 2 Std.) oder fehlende Uhrzeit. Absage-Zusätze
(„ENTFÄLLT! …“) werden erkannt.

Je Paar:
- Behalten wird der Eintrag des Veranstalters (sonst der ältere). Er bekommt fehlende Felder (Bild, Beschreibung,
  Preis, Adresse) und – bei Abweichung – die Uhrzeit des Veranstalters bzw. die Absage.
- Die Dublette wird ausgeblendet (abgelehnt = true) und ihre URL per 301 auf die behaltene Seite umgeleitet
  (event_seo_entscheidungen, wie die SEO-Entscheidungen im Dashboard). So läuft keine URL ins Leere.
- Titel mit Absage-Zusatz ohne Original: Zusatz entfernen, abgesagt = true. Der Slug (die URL) bleibt.

Aufruf: python -m pipeline.dubletten_sql [--ausgabe database/dubletten_<datum>.sql] [--jazz-schmiede]
  --jazz-schmiede: Uhrzeiten der Jazz-Schmiede (bis 11.11.2026 falsch gelesen, 11:20 statt 20:30) frisch von der
  Website holen und mitkorrigieren (eine Anfrage).
"""
import argparse
import logging
import os
import sys
from collections import defaultdict
from datetime import date

import httpx
from dotenv import load_dotenv

from pipeline.deduplication import (
    TITEL_STATUS_FELD,
    _uhrzeit,
    bester_treffer,
    ist_aggregator,
    titel_status_bereinigen,
)
from pipeline.indexnow import kategorie_web

logger = logging.getLogger(__name__)

SPALTEN = "id,slug,titel,datum,uhrzeit,ort,quelle_name,quelle_url,kategorie,abgesagt,bild_url,beschreibung,preis,adresse,erstellt_am"
FUELL_FELDER = ["bild_url", "beschreibung", "preis", "adresse"]


def events_laden(ab: str) -> list[dict]:
    """Alle sichtbaren Events ab einem Datum (seitenweise über die REST-API)."""
    load_dotenv()
    url = os.environ["SUPABASE_URL"]
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    kopf = {"apikey": key, "Authorization": f"Bearer {key}"}
    alle, start = [], 0
    while True:
        try:
            antwort = httpx.get(
                f"{url}/rest/v1/events",
                headers={**kopf, "Range": f"{start}-{start + 999}"},
                params={"select": SPALTEN, "datum": f"gte.{ab}", "abgelehnt": "eq.false", "order": "id"},
                timeout=60,
            )
            antwort.raise_for_status()
        except Exception as e:
            logger.error("Events nicht ladbar: %s", e)
            raise
        seite = antwort.json()
        alle += seite
        start += 1000
        if len(seite) < 1000:
            return alle


def jazz_schmiede_zeiten() -> dict[tuple[str, str], str]:
    """(Datum, Titel) → richtige Uhrzeit, frisch vom (korrigierten) Jazz-Schmiede-Scraper."""
    from scraper.tier2 import jazz_schmiede
    try:
        return {(e["datum"], e["titel"]): e["uhrzeit"] for e in jazz_schmiede.scrape() if e.get("uhrzeit")}
    except Exception as e:
        logger.warning("Jazz-Schmiede nicht abrufbar – Uhrzeiten bleiben: %s", e)
        return {}


def q(wert) -> str:
    """SQL-Literal."""
    if wert is None:
        return "NULL"
    if isinstance(wert, bool):
        return "true" if wert else "false"
    return "'" + str(wert).replace("'", "''") + "'"


def pfad(e: dict) -> str:
    return f"/event/{kategorie_web(e.get('kategorie'))}/{e['slug']}"


def paare_finden(events: list[dict]) -> tuple[list[tuple[dict, dict]], list[dict]]:
    """
    Liefert (behalten, dublette)-Paare und Events mit Absage-Zusatz ohne Original.
    Die Events tragen bereits den bereinigten Titel und ggf. TITEL_STATUS_FELD.
    """
    pro_tag: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        pro_tag[e["datum"]].append(e)
    paare, allein_mit_zusatz = [], []
    for tag in sorted(pro_tag):
        # Veranstalter zuerst, Einträge mit Zusatz zuletzt, sonst die älteren zuerst
        reihe = sorted(pro_tag[tag], key=lambda e: (bool(e.get(TITEL_STATUS_FELD)), ist_aggregator(e), e.get("erstellt_am") or ""))
        behalten: list[dict] = []
        for e in reihe:
            treffer = bester_treffer(behalten, e)
            if treffer is not None:
                paare.append((treffer, e))
            else:
                behalten.append(e)
                if e.get(TITEL_STATUS_FELD):
                    allein_mit_zusatz.append(e)
    return paare, allein_mit_zusatz


def sql_bauen(events: list[dict], original: dict[str, dict], jazz: dict[tuple[str, str], str]) -> tuple[str, list[str]]:
    zeilen = [
        f"-- Dubletten aufräumen – DiesDasDüsseldorf, erzeugt am {date.today().isoformat()} von pipeline/dubletten_sql.py",
        "-- Im Supabase-SQL-Editor als Ganzes ausführen (eine Transaktion). Betrifft nur Events ab heute.",
        "-- Dubletten werden ausgeblendet (abgelehnt = true) und per 301 auf das behaltene Event umgeleitet.",
        "",
        "BEGIN;",
        "",
    ]
    bericht: list[str] = []

    # 1. Jazz-Schmiede-Uhrzeiten korrigieren (vor dem Abgleich, damit die Paare stimmen)
    korrekturen = 0
    for e in events:
        if e.get("quelle_name") == "Jazz-Schmiede Düsseldorf":
            richtig = jazz.get((e["datum"], original[e["id"]]["titel"]))
            if richtig and richtig != _uhrzeit(e):
                if not korrekturen:
                    zeilen.append("-- 1. Jazz-Schmiede: Uhrzeit war aus dem Datum gelesen (11:20 statt 20:30)")
                zeilen.append(f"UPDATE public.events SET uhrzeit = {q(richtig)} WHERE id = {q(e['id'])};")
                e["uhrzeit"] = richtig
                korrekturen += 1
    if korrekturen:
        zeilen.append("")
        bericht.append(f"Jazz-Schmiede-Uhrzeiten korrigiert: {korrekturen}")

    paare, allein = paare_finden(events)

    # 2. Paare zusammenführen
    if paare:
        zeilen.append("-- 2. Dubletten: behaltenes Event ergänzen, Dublette ausblenden und umleiten")
    for behalten, dublette in paare:
        b_alt, d_alt = original[behalten["id"]], original[dublette["id"]]
        zeilen.append(
            f"-- {behalten['datum']}: „{b_alt['titel'][:60]}“ [{behalten.get('quelle_name')}, {_uhrzeit(behalten) or '–'}]"
            f"  ←  „{d_alt['titel'][:60]}“ [{dublette.get('quelle_name')}, {_uhrzeit(dublette) or '–'}]"
        )
        setzen = [f"{f} = COALESCE(NULLIF(k.{f}, ''), d.{f})" for f in FUELL_FELDER]
        if not _uhrzeit(behalten) and _uhrzeit(dublette):
            setzen.append("uhrzeit = d.uhrzeit")
        elif (_uhrzeit(behalten) and _uhrzeit(dublette) and _uhrzeit(behalten) != _uhrzeit(dublette)
              and ist_aggregator(behalten) and not ist_aggregator(dublette)):
            setzen.append("uhrzeit = d.uhrzeit")
        if dublette.get("abgesagt") or dublette.get(TITEL_STATUS_FELD) == "abgesagt":
            setzen.append("abgesagt = true")
        zeilen.append(
            f"UPDATE public.events k SET {', '.join(setzen)} FROM public.events d "
            f"WHERE k.id = {q(behalten['id'])} AND d.id = {q(dublette['id'])};"
        )
        zeilen.append(f"UPDATE public.events SET abgelehnt = true WHERE id = {q(dublette['id'])};")
        if dublette.get("slug") and behalten.get("slug"):
            zeilen.append(
                "INSERT INTO public.event_seo_entscheidungen (event_id, slug, aktion, ziel) VALUES "
                f"({q(dublette['id'])}, {q(dublette['slug'])}, 'weiterleiten', {q(pfad(behalten))}) "
                "ON CONFLICT (event_id) DO UPDATE SET aktion = 'weiterleiten', ziel = EXCLUDED.ziel, entschieden_am = now();"
            )
        bericht.append(
            f"{behalten['datum']} {_uhrzeit(behalten) or '--'}/{_uhrzeit(dublette) or '--'} | "
            f"{b_alt['titel'][:45]} [{behalten.get('quelle_name')}] ← {d_alt['titel'][:45]} [{dublette.get('quelle_name')}]"
        )
    zeilen.append("")

    # 3. Absage-/Status-Zusatz ohne Original: nur Titel bereinigen (URL bleibt)
    if allein:
        zeilen.append("-- 3. Titel mit Absage-/Status-Zusatz ohne zweiten Eintrag: Zusatz entfernen (URL bleibt)")
    for e in allein:
        setzen = [f"titel = {q(e['titel'])}"]
        if e.get(TITEL_STATUS_FELD) == "abgesagt":
            setzen.append("abgesagt = true")
        zeilen.append(f"UPDATE public.events SET {', '.join(setzen)} WHERE id = {q(e['id'])};  -- war: {original[e['id']]['titel'][:70]}")
        bericht.append(f"Titel bereinigt: {original[e['id']]['titel'][:60]} → {e['titel'][:50]}")
    zeilen += [
        "",
        "COMMIT;",
        "",
        "-- Kontrolle: neue Weiterleitungen von heute",
        "SELECT slug, ziel FROM public.event_seo_entscheidungen WHERE aktion = 'weiterleiten' AND entschieden_am::date = CURRENT_DATE ORDER BY slug;",
        "",
    ]
    return "\n".join(zeilen), bericht


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="SQL zum Aufräumen gespeicherter Dubletten erzeugen")
    parser.add_argument("--ausgabe", default=f"database/dubletten_{date.today().isoformat()}.sql")
    parser.add_argument("--jazz-schmiede", action="store_true")
    args = parser.parse_args()

    events = events_laden(date.today().isoformat())
    original = {e["id"]: dict(e) for e in events}
    for e in events:
        titel_status_bereinigen(e)
    jazz = jazz_schmiede_zeiten() if args.jazz_schmiede else {}
    sql, bericht = sql_bauen(events, original, jazz)
    with open(args.ausgabe, "w", encoding="utf-8") as f:
        f.write(sql)
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(bericht))
    logger.info("SQL geschrieben: %s (%d Einträge)", args.ausgabe, len(bericht))


if __name__ == "__main__":
    main()
