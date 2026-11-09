"""
preisspanne.py – DiesDasDüsseldorf
Preisspanne pro Person (in €) für alle Restaurants, Cafés und Schnellimbisse – unabhängig davon, ob
sie im Frontend sichtbar sind (die Datenbank soll vollständig sein).

Zwei Quellen, kombiniert:
  1. google  – Google Places „priceRange“ (startPrice/endPrice). Nur dieses Feld + priceLevel wird
               abgefragt → SKU „Place Details Enterprise“ (20 $/1.000, Stand 2026-11-09), nicht die
               teurere Enterprise+Atmosphere-Stufe des normalen Detailabrufs.
  2. ki      – Claude Haiku liest die gespeicherten Google-Bewertungen und schätzt, was eine Person
               typischerweise ausgibt – NUR mit wörtlich belegten Preisangaben (Zitate im Code geprüft).
Ergebnis in orte.extras:
  google_preisspanne  {von, bis|None, abgerufen}       Google-Rohwert (bis None = „ab …“)
  preis_bewertungen   {von, bis, belege, modell}      KI-Schätzung aus Bewertungen
  preis_pp            {von, bis, quelle}              kombinierte Spanne pro Person
Das bestehende preis_niveau (€/€€/€€€) wird hier NICHT geändert.

Alle Abrufe landen zuerst in data/orte/preisspanne.json bzw. preisspanne_ki.json (kein doppelt bezahlter Abruf, kein
Schreibkonflikt mit anderen Skripten, die extras gleichzeitig schreiben). Erst „schreiben“ überträgt
die Ergebnisse in die Datenbank.

Nutzung:
  python -m scraper.orte.preisspanne google [--max N]     # Google abrufen (kostet)
  python -m scraper.orte.preisspanne ki [--max N]         # Bewertungen auswerten (Cent-Beträge)
  python -m scraper.orte.preisspanne auswertung           # Verteilung anzeigen, nichts schreiben
  python -m scraper.orte.preisspanne schreiben [--dry-run]
"""
import argparse
import json
import logging
import re
import sys
import time
from datetime import date
from pathlib import Path
from statistics import median

import httpx
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scraper.orte.bars_einordnen import belegt, quelltext  # noqa: E402
from scraper.orte.google_places import API_BASE, _headers, alle_zeilen  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

_ORDNER = Path(__file__).resolve().parents[2] / "data" / "orte"
# Getrennte Dateien je Schritt – beide Schritte können gleichzeitig laufen, ohne sich zu überschreiben
DATEIEN = {"google": _ORDNER / "preisspanne.json", "ki": _ORDNER / "preisspanne_ki.json"}
TYPEN = ("restaurant", "cafe", "imbiss")
FELDMASKE = "priceRange,priceLevel"
MODELL = "claude-haiku-5-5"


def speicher_laden() -> dict:
    daten = {}
    for teil, datei in DATEIEN.items():
        inhalt = json.loads(datei.read_text(encoding="utf-8")) if datei.exists() else {}
        daten[teil] = inhalt.get(teil, {})
    return daten


def speicher_sichern(daten: dict, teil: str) -> None:
    """Schreibt nur den Teil eines Schritts in seine eigene Datei (atomar)."""
    datei = DATEIEN[teil]
    datei.parent.mkdir(parents=True, exist_ok=True)
    tmp = datei.with_suffix(".tmp")
    tmp.write_text(json.dumps({teil: daten[teil]}, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(datei)


def orte_laden() -> list[dict]:
    from database.client import get_supabase_client

    db = get_supabase_client()
    return [o for o in alle_zeilen(db, "orte", "id, name, typ, stadtteil, google_place_id, preis_niveau, extras")
            if o["typ"] in TYPEN]


def _betrag(money: dict | None) -> int | None:
    if not money or money.get("currencyCode", "EUR") != "EUR":
        return None
    return int(money.get("units") or 0) + (1 if int(money.get("nanos") or 0) >= 500_000_000 else 0)


# ── 1. Google ─────────────────────────────────────────────────────────────────

def google_abrufen(max_anzahl: int) -> None:
    daten = speicher_laden()
    offen = [o for o in orte_laden() if o.get("google_place_id") and o["google_place_id"] not in daten["google"]][:max_anzahl]
    logger.info("Google priceRange: %d Orte abzurufen (≈ %.2f $)", len(offen), len(offen) * 0.020)
    mit_spanne = fehler = 0
    with httpx.Client(timeout=30) as client:
        for i, o in enumerate(offen, 1):
            time.sleep(0.3)
            try:
                resp = client.get(f"{API_BASE}/places/{o['google_place_id']}", params={"languageCode": "de"},
                                  headers=_headers(FELDMASKE))
                resp.raise_for_status()
                p = resp.json()
            except Exception as e:
                fehler += 1
                logger.error("Fehler bei '%s': %s", o["name"], e)
                continue
            spanne = p.get("priceRange") or {}
            eintrag = {"von": _betrag(spanne.get("startPrice")), "bis": _betrag(spanne.get("endPrice")),
                       "level": p.get("priceLevel"), "abgerufen": date.today().isoformat()}
            daten["google"][o["google_place_id"]] = eintrag
            mit_spanne += eintrag["von"] is not None
            if i % 50 == 0:
                speicher_sichern(daten, "google")
                logger.info("  %d/%d abgerufen, %d mit Preisspanne", i, len(offen), mit_spanne)
    speicher_sichern(daten, "google")
    logger.info("Google fertig: %d abgerufen, %d mit Preisspanne, %d Fehler", len(offen) - fehler, mit_spanne, fehler)


# ── 2. KI aus Bewertungen ─────────────────────────────────────────────────────

SCHEMA = {
    "type": "object",
    "properties": {
        "hat_angaben": {"type": "boolean"},
        "von": {"type": "integer"},
        "bis": {"type": "integer"},
        "belege": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["hat_angaben", "von", "bis", "belege"],
    "additionalProperties": False,
}

SYSTEM = """Du schätzt für einen Düsseldorfer Stadtguide, wie viel eine Person an einem Ort typischerweise
ausgibt – ein normaler Besuch: im Restaurant ein Hauptgericht plus ein Getränk, im Café Kaffee plus
Kuchen oder Frühstück, im Imbiss ein Gericht plus Getränk. Grundlage sind NUR die gelieferten Texte.

- „hat_angaben“: true nur, wenn die Texte konkrete Preise in Euro nennen (z. B. „Pizza für 9,50 €“,
  „zu zweit 60 €“, „Mittagstisch 8,90“) oder eindeutige Preisaussagen machen („sehr günstig“,
  „gehobene Preise“). Sonst false, von/bis = 0, belege leer.
- „von“/„bis“: ganze Euro pro Person. Rechne Angaben für mehrere Personen auf eine Person um.
  Eine Spanne von etwa 5–15 € Breite; bei reinen Wortangaben eine vorsichtige Schätzung.
- „belege“: 1–3 WÖRTLICHE Zitate (exakt wie im Text), die die Preise oder Preisaussagen enthalten."""

PREISWORT = re.compile(r"\d|€|euro|günstig|preiswert|billig|teuer|gehoben|preis", re.IGNORECASE)


def ki_auswerten(max_anzahl: int) -> None:
    import anthropic

    daten = speicher_laden()
    client = anthropic.Anthropic()
    offen = [o for o in orte_laden() if quelltext(o) and o["id"] not in daten["ki"]][:max_anzahl]
    logger.info("KI-Auswertung: %d Orte", len(offen))
    ein = aus = treffer = 0
    for i, o in enumerate(offen, 1):
        ex = o.get("extras") or {}
        bewertungen = "\n".join(f"- {b.get('text')}" for b in (ex.get("google_bewertungen") or []) if b.get("text"))
        nutzer = (f"Name: {o['name']}\nArt: {o['typ']} (Google-Typ: {ex.get('google_primaertyp')})\n"
                  f"Google-Kurzbeschreibung: {ex.get('google_zusammenfassung') or '–'}\n\nBewertungen:\n{bewertungen or '–'}")
        try:
            antwort = client.messages.create(
                model=MODELL, max_tokens=2000, system=SYSTEM,
                output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
                messages=[{"role": "user", "content": nutzer}],
            )
            if antwort.stop_reason in ("refusal", "max_tokens"):
                raise RuntimeError(f"stop_reason {antwort.stop_reason}")
            ki = json.loads(next(b.text for b in antwort.content if b.type == "text"))
            ein += antwort.usage.input_tokens
            aus += antwort.usage.output_tokens
        except Exception as e:
            logger.error("Fehler bei '%s': %s", o["name"], e)
            continue
        quelle = quelltext(o)
        belege = [b for b in ki.get("belege") or [] if belegt(b, quelle) and PREISWORT.search(b)]
        von, bis = int(ki.get("von") or 0), int(ki.get("bis") or 0)
        gueltig = bool(ki.get("hat_angaben")) and belege and 1 <= von <= bis <= 300
        daten["ki"][o["id"]] = ({"von": von, "bis": bis, "belege": belege, "modell": MODELL, "datum": date.today().isoformat()}
                                if gueltig else {"keine": True, "datum": date.today().isoformat()})
        treffer += bool(gueltig)
        if i % 50 == 0:
            speicher_sichern(daten, "ki")
            logger.info("  %d/%d ausgewertet, %d mit belegter Preisangabe", i, len(offen), treffer)
    speicher_sichern(daten, "ki")
    logger.info("KI fertig: %d ausgewertet, %d mit belegter Preisangabe, Kosten ≈ %.3f $",
                len(offen), treffer, ein / 1e6 * 0.10 + aus / 1e6 * 0.50)


# ── 3. Kombinieren ────────────────────────────────────────────────────────────

def kombinieren(google: dict | None, ki: dict | None) -> dict | None:
    """
    Google-Spanne hat Vorrang (gleichmäßige Methodik über alle Orte). Fehlt Googles Obergrenze
    („ab 50 €“), ergänzt die KI-Schätzung sie, wenn sie darüber liegt. Ohne Google zählt die KI.
    """
    g = google if google and google.get("von") is not None else None
    k = ki if ki and not ki.get("keine") else None
    if g and k:
        bis = g["bis"] if g.get("bis") is not None else (k["bis"] if k["bis"] > g["von"] else None)
        return {"von": g["von"], "bis": bis, "quelle": "google+bewertungen"}
    if g:
        return {"von": g["von"], "bis": g.get("bis"), "quelle": "google"}
    if k:
        return {"von": k["von"], "bis": k["bis"], "quelle": "bewertungen"}
    return None


def auswertung() -> None:
    daten = speicher_laden()
    orte = orte_laden()
    zahl = {"google": 0, "google+bewertungen": 0, "bewertungen": 0, "keine": 0}
    nach_stufe: dict[str, list[float]] = {}
    for o in orte:
        pp = kombinieren(daten["google"].get(o.get("google_place_id") or ""), daten["ki"].get(o["id"]))
        if not pp:
            zahl["keine"] += 1
            continue
        zahl[pp["quelle"]] += 1
        mitte = (pp["von"] + (pp["bis"] or pp["von"] * 1.5)) / 2
        nach_stufe.setdefault(f"{o['typ']} {o.get('preis_niveau') or '–'}", []).append(mitte)
    print(f"{len(orte)} Orte | Quelle: {zahl}")
    print(f"Google abgerufen: {len(daten['google'])} | KI ausgewertet: {len(daten['ki'])}")
    for stufe, werte in sorted(nach_stufe.items()):
        werte.sort()
        print(f"  {stufe:14s} n={len(werte):4d}  Mitte p. P.: Median {median(werte):5.1f} €, "
              f"25 % {werte[len(werte) // 4]:5.1f} €, 75 % {werte[3 * len(werte) // 4]:5.1f} €")


def schreiben(dry_run: bool) -> None:
    from database.client import get_supabase_client

    db = get_supabase_client()
    daten = speicher_laden()
    geaendert = 0
    for o in orte_laden():
        ex = dict(o.get("extras") or {})
        g = daten["google"].get(o.get("google_place_id") or "")
        k = daten["ki"].get(o["id"])
        neu = dict(ex)
        if g is not None:
            neu["google_preisspanne"] = {"von": g.get("von"), "bis": g.get("bis"), "abgerufen": g.get("abgerufen")}
        if k and not k.get("keine"):
            neu["preis_bewertungen"] = {x: k[x] for x in ("von", "bis", "belege", "modell", "datum")}
        pp = kombinieren(g, k)
        if pp:
            neu["preis_pp"] = pp
        if neu != ex:
            geaendert += 1
            if not dry_run:
                db.table("orte").update({"extras": neu}).eq("id", o["id"]).execute()
    logger.info("%s: %d Orte %s", "Dry-Run" if dry_run else "Geschrieben", geaendert, "würden geändert" if dry_run else "geändert")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("schritt", choices=["google", "ki", "auswertung", "schreiben"])
    parser.add_argument("--max", type=int, default=100000)
    parser.add_argument("--dry-run", action="store_true")
    a = parser.parse_args()
    {"google": lambda: google_abrufen(a.max), "ki": lambda: ki_auswerten(a.max),
     "auswertung": auswertung, "schreiben": lambda: schreiben(a.dry_run)}[a.schritt]()


if __name__ == "__main__":
    main()
