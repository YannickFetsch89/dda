"""
spielstaetten_texte.py – DiesDasDüsseldorf
Texte der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.14, Schritt 4). Schreibt nichts in die Datenbank.

Regeln:
- Jeder Satz hat eine öffentliche Quellen-URL (Spalte `belege`, eine URL je Satz, getrennt durch „ | “).
- Auftraggeber 20.11.2026: möglichst 5–10 Sätze, aber nur Belegbares; sonst kürzer (mindestens 2).
  Gegliedert wie die Weihnachtsmärkte: Absätze durch Leerzeile, Schlagwörter **fett**.
- Keine „wir“-Texte, keine Öffnungszeiten oder Preise (veralten), nichts Erfundenes.
- Der Auftraggeber gibt jeden Text frei (Spalte `freigabe` = ja). Erst dann setzt die SQL `beschreibung` und
  `extras.spielstaette.text_freigegeben` – vorher zeigt die Seite keinen Text.

Ablauf (im Repo-Stamm):
  python -m scraper.orte.spielstaetten_texte --uebernehmen entwurf.json [...]  → data/spielstaetten/texte.csv
  python -m scraper.orte.spielstaetten_texte --pruefen                          → Befunde je Zeile
  python -m scraper.orte.spielstaetten_texte --sql                              → database/orte_texte_<datum>.sql
Ein geänderter Text verliert seine Freigabe (freigabe wird geleert).
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

TEXTE = Path("data/spielstaetten/texte.csv")
SPALTEN = ["slug", "name", "text", "belege", "webseite", "freigabe", "stand", "hinweis"]
MIN_SAETZE, MAX_SAETZE = 2, 10
TRENNER = " | "

# Abkürzungen, nach denen kein Satz endet („z. B.“, „St. Lambertus“, „ca. 1.900“, „am 3. Oktober“)
_ABKUERZUNGEN = re.compile(
    r"(?:\b[a-zäöü]\.|\b[a-z]\.\s?[a-zA-Z]\.|\b[A-ZÄÖÜ]\.|"   # „z. B.“, „u. a.“, Initiale „Horst H. Baumann“
    r"\b(?:ca|St|Nr|Dr|Prof|bzw|ggf|inkl|Jh|Str|vgl|etc|evtl|usw|sog|bspw|Mio|Mrd)\.)$")
# Ordnungszahl („am 3. Oktober“, „im 19. Jahrhundert“) – nur dann kein Satzende; „Saal 89. Als …“ endet dort
_ORDINAL = re.compile(r"\b\d{1,2}\.$")
_NACH_ORDINAL = re.compile(r"^[\"„»*(]*(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|"
                           r"Dezember|Jahrhundert\w*|Jh|Stock|Etage|Obergeschoss|OG|Bundesliga|Liga|Platz|Preis)\b")
_SATZENDE = re.compile(r"(?<=[.!?…])[\"“”»*)]*\s+(?=[\"„»*(]*[A-ZÄÖÜ0-9])")
_FETT = re.compile(r"\*\*([^*\n]+?)\*\*")
_URL = re.compile(r"^https?://\S+$")
# Hinweise, keine Fehler: veraltende Angaben (Plan 3.14)
_VERDAECHTIG = [
    (re.compile(r"\b\d{1,2}(?::\d{2})?\s*Uhr\b"), "Uhrzeit"),
    (re.compile(r"€|\bEuro\b"), "Preis"),
    (re.compile(r"\b(Spielzeit|Saison) 20\d\d", re.I), "Spielzeit/Saison"),
]
_WIR = re.compile(r"\b(wir|uns|unser\w*)\b", re.I)


def saetze(text: str) -> list[str]:
    """Sätze eines Textes (Absätze getrennt, Abkürzungen wie „z. B.“ beenden keinen Satz)."""
    ergebnis: list[str] = []
    for absatz in re.split(r"\n\s*\n", (text or "").strip()):
        teile = _SATZENDE.split(" ".join(absatz.split()))
        puffer = ""
        for i, t in enumerate(teile):
            puffer = f"{puffer} {t}".strip() if puffer else t
            naechster = teile[i + 1] if i + 1 < len(teile) else ""
            ordinal = _ORDINAL.search(puffer) and _NACH_ORDINAL.match(naechster)
            if not _ABKUERZUNGEN.search(puffer) and not ordinal:
                ergebnis.append(puffer)
                puffer = ""
        if puffer:
            ergebnis.append(puffer)
    return [s for s in ergebnis if s]


def belege_liste(belege: str | list) -> list[str]:
    if isinstance(belege, list):
        return [b.strip() for b in belege if str(b).strip()]
    return [b.strip() for b in (belege or "").split(TRENNER.strip()) if b.strip()]


def pruefen(z: dict) -> tuple[list[str], list[str]]:
    """(Fehler, Hinweise) einer Zeile. Fehler verhindern die SQL, Hinweise nicht."""
    fehler: list[str] = []
    hinweise: list[str] = []
    text = (z.get("text") or "").strip()
    if not text:
        return ["kein Text"], hinweise
    s = saetze(text)
    b = belege_liste(z.get("belege") or "")
    if not MIN_SAETZE <= len(s) <= MAX_SAETZE:
        fehler.append(f"{len(s)} Sätze (erlaubt {MIN_SAETZE}–{MAX_SAETZE})")
    if len(b) != len(s):
        fehler.append(f"{len(b)} Belege für {len(s)} Sätze")
    if any(not _URL.match(x) for x in b):
        fehler.append("Beleg ohne gültige URL")
    if text.count("**") % 2:
        fehler.append("unvollständige **Fettschrift**")
    if _WIR.search(_FETT.sub(r"\1", text)):
        fehler.append("„wir/unser“ im Text (vom Haus übernommen?)")
    if z.get("webseite") and not z["webseite"].startswith("https://"):
        fehler.append("Webseite nicht https")
    for muster, name in _VERDAECHTIG:
        if muster.search(text):
            hinweise.append(f"{name} im Text – veraltet leicht")
    if "\n\n" not in text and len(s) >= 5:
        hinweise.append("keine Absätze")
    if not _FETT.search(text):
        hinweise.append("keine Schlagwörter fett")
    return fehler, hinweise


def lesen() -> list[dict]:
    if not TEXTE.exists():
        return []
    with TEXTE.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def schreiben(zeilen: list[dict]) -> None:
    TEXTE.parent.mkdir(parents=True, exist_ok=True)
    with TEXTE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SPALTEN, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(zeilen, key=lambda z: z["slug"]))


def uebernehmen(dateien: list[Path], heute: str) -> int:
    """Entwürfe (JSON: slug, name, text, belege[], webseite, hinweis) in texte.csv übernehmen."""
    bisher = {z["slug"]: z for z in lesen()}
    n = 0
    for datei in dateien:
        for e in json.loads(datei.read_text(encoding="utf-8")):
            alt = bisher.get(e["slug"], {})
            text = (e.get("text") or "").strip().replace("\r\n", "\n")
            neu = {
                "slug": e["slug"], "name": e.get("name") or alt.get("name", ""), "text": text,
                "belege": TRENNER.join(belege_liste(e.get("belege") or [])),
                "webseite": e.get("webseite") or alt.get("webseite", ""),
                # Freigabe bleibt nur bei unverändertem Text
                "freigabe": alt.get("freigabe", "") if alt.get("text") == text else "",
                "stand": heute, "hinweis": e.get("hinweis") or "",
            }
            bisher[e["slug"]] = neu
            n += 1
    schreiben(list(bisher.values()))
    return n


def _sql(wert: str) -> str:
    return "'" + wert.replace("'", "''") + "'"


def sql_bauen(zeilen: list[dict], heute: str) -> tuple[str, int, list[str]]:
    teile = [
        "-- Texte der Ortsseiten (Plan docs/plan-locations-2026-11-18.md, 3.14, Schritt 4)",
        f"-- Erzeugt am {heute} von `python -m scraper.orte.spielstaetten_texte --sql` aus data/spielstaetten/texte.csv",
        "-- (nur Zeilen mit freigabe = ja und ohne Prüffehler). Jeder Satz hat eine Quelle (extras.spielstaette.",
        "-- text_freigegeben.quellen). Absätze per Leerzeile, **fett** zeigt die Ortsseite. Wiederholbar.",
        "", "BEGIN;", ""]
    n = 0
    uebersprungen: list[str] = []
    for z in sorted(zeilen, key=lambda z: z["slug"]):
        if (z.get("freigabe") or "").strip().lower() != "ja":
            continue
        fehler, _ = pruefen(z)
        if fehler:
            uebersprungen.append(f"{z['slug']}: {'; '.join(fehler)}")
            continue
        if "$txt$" in z["text"]:
            uebersprungen.append(f"{z['slug']}: Text enthält $txt$")
            continue
        freigabe = json.dumps({"text_freigegeben": {"datum": heute, "quellen": belege_liste(z["belege"])}}, ensure_ascii=False)
        webseite = f", webseite = COALESCE(webseite, {_sql(z['webseite'])})" if z.get("webseite") else ""
        teile.append(
            f"UPDATE public.orte SET beschreibung = $txt${z['text']}$txt${webseite},\n"
            f"  extras = jsonb_set(extras, '{{spielstaette}}', COALESCE(extras->'spielstaette', '{{}}'::jsonb) || {_sql(freigabe)}::jsonb)\n"
            f"WHERE slug = {_sql(z['slug'])} AND typ = 'spielstaette';")
        n += 1
    teile += ["", "COMMIT;", "",
              "-- Kontrolle: Ortsseiten mit freigegebenem Text",
              "SELECT count(*) FILTER (WHERE extras->'spielstaette' ? 'text_freigegeben') AS mit_text,",
              "       count(*) AS spielstaetten FROM public.orte WHERE typ = 'spielstaette';", ""]
    return "\n".join(teile), n, uebersprungen


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="Texte der Ortsseiten (nur lesend, SQL als Datei)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--uebernehmen", nargs="+", type=Path, metavar="JSON")
    g.add_argument("--pruefen", action="store_true")
    g.add_argument("--sql", action="store_true")
    p.add_argument("--ausgabe", default=f"database/orte_texte_{date.today().isoformat()}.sql")
    a = p.parse_args()
    heute = date.today().isoformat()
    if a.uebernehmen:
        logger.info("Texte: %d Entwürfe übernommen → %s", uebernehmen(a.uebernehmen, heute), TEXTE)
    elif a.pruefen:
        for z in lesen():
            fehler, hinweise = pruefen(z)
            status = "FEHLER" if fehler else "ok"
            print(f"{status:6} {z['slug']:40} {len(saetze(z['text'])):2} Sätze  {z.get('freigabe') or '-':4} "
                  f"{'; '.join(fehler + hinweise)}")
    else:
        sql, n, uebersprungen = sql_bauen(lesen(), heute)
        Path(a.ausgabe).write_text(sql, encoding="utf-8")
        logger.info("Texte-SQL: %d Texte → %s", n, a.ausgabe)
        for u in uebersprungen:
            logger.warning("übersprungen: %s", u)


if __name__ == "__main__":
    main()
