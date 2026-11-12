"""
unterkategorien.py – DiesDasDüsseldorf
Feinfilter je Kategorie (z.B. Musik → Klassik, Jazz & Soul, DJ & Elektronisch): Claude Haiku ordnet jedes kommende
Event genau einer Unterkategorie seiner Kategorie zu. Die Liste steht in web/lib/unterkategorien.json (eine Quelle
für Website und Pipeline). Ergebnis in events.unterkategorie (Slug, „keine“ = geprüft, nichts passt).

Gebündelt: bis zu 25 Events derselben Kategorie je Anfrage – die Nachpflege von rund 2.000 Events braucht so
etwa 80 Anfragen. Fehlt die DB-Spalte noch (SQL database/unterkategorie_2026-11-11.sql), bricht der Schritt
mit einer Meldung ab, ohne den Lauf zu stören.

Pipeline: nach der Kategorisierung (main.py, Schritt 3a). Manuell: python -m pipeline.unterkategorien [--limit N] [--dry-run]
"""
import argparse
import json
import logging
import os
import re
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

LISTE_PFAD = Path(__file__).resolve().parent.parent / "web" / "lib" / "unterkategorien.json"
MODELL = "claude-haiku-4-5-20251001"  # wie die Kategorisierung (pipeline/categorizer.py)
KEINE = "keine"
BUENDEL = 25
WARTEZEIT_SEKUNDEN = 1


def liste_laden() -> dict[str, list[dict]]:
    """Unterkategorien je Website-Kategorie (ohne den Hinweis-Eintrag)."""
    daten = json.loads(LISTE_PFAD.read_text(encoding="utf-8"))
    return {k: v for k, v in daten.items() if not k.startswith("_")}


def kategorie_web(wert: str | None) -> str:
    """DB-Kategorie wie auf der Website („family“ → „familie“)."""
    w = (wert or "").strip().lower()
    return "familie" if w == "family" else w


def prompt_bauen(kategorie: str, optionen: list[dict], events: list[dict]) -> str:
    """Eine Anfrage für bis zu BUENDEL Events derselben Kategorie."""
    liste = "\n".join(f"- {o['slug']}: {o['name']} ({o['hinweis']})" for o in optionen)
    zeilen = []
    for nr, e in enumerate(events, 1):
        beschreibung = re.sub(r"\s+", " ", e.get("beschreibung") or "")[:220]
        zeilen.append(f"{nr}. {e.get('titel') or ''} | Ort: {e.get('ort') or '-'} | {beschreibung}")
    return f"""Ordne Düsseldorfer Events der Kategorie „{kategorie}“ jeweils genau EINER Unterkategorie zu.

Unterkategorien (Slug: Name (Beispiele)):
{liste}

Wähle die am besten passende. „{KEINE}“ nur, wenn das Event erkennbar zu keiner davon gehört (z.B. weil es gar nicht in diese Kategorie passt).

Events:
{chr(10).join(zeilen)}

Antworte ausschließlich mit einer Zeile je Event im Format „Nummer: slug“, z.B. „1: {optionen[0]['slug']}“."""


def antwort_lesen(text: str, anzahl: int, erlaubt: set[str]) -> dict[int, str]:
    """„3: jazz“ → {3: "jazz"}; unbekannte Slugs werden zu „keine“, fehlende Nummern fehlen."""
    ergebnis: dict[int, str] = {}
    for zeile in text.splitlines():
        m = re.match(r"^\s*(\d+)\s*[:.)\-]\s*([a-z0-9\-]+)", zeile.strip().lower())
        if not m:
            continue
        nr, slug = int(m.group(1)), m.group(2)
        if 1 <= nr <= anzahl:
            ergebnis[nr] = slug if slug in erlaubt else KEINE
    return ergebnis


def bestimmen(client, events: list[dict], listen: dict[str, list[dict]]) -> dict[str, str]:
    """Event-ID → Unterkategorie-Slug (oder „keine“). Events ohne Liste (z.B. „sonstiges“) bekommen „keine“."""
    nach_kat: dict[str, list[dict]] = {}
    ergebnis: dict[str, str] = {}
    for e in events:
        kat = kategorie_web(e.get("kategorie"))
        if kat in listen:
            nach_kat.setdefault(kat, []).append(e)
        else:
            ergebnis[e["id"]] = KEINE
    erste = True
    for kat, liste in nach_kat.items():
        optionen = listen[kat]
        erlaubt = {o["slug"] for o in optionen} | {KEINE}
        for start in range(0, len(liste), BUENDEL):
            teil = liste[start:start + BUENDEL]
            if not erste:
                time.sleep(WARTEZEIT_SEKUNDEN)
            erste = False
            try:
                antwort = client.messages.create(
                    model=MODELL,
                    max_tokens=20 * len(teil) + 50,
                    messages=[{"role": "user", "content": prompt_bauen(kat, optionen, teil)}],
                )
                text = "".join(b.text for b in antwort.content if getattr(b, "type", "") == "text")
            except Exception as e:
                logger.warning("Unterkategorien für %d Events (%s) fehlgeschlagen: %s", len(teil), kat, e)
                continue  # beim nächsten Lauf erneut
            zuordnung = antwort_lesen(text, len(teil), erlaubt)
            for nr, e in enumerate(teil, 1):
                if nr in zuordnung:
                    ergebnis[e["id"]] = zuordnung[nr]
    return ergebnis


def nachtragen(limit: int | None = 600, dry_run: bool = False) -> int:
    """Kommende Events ohne Unterkategorie zuordnen und speichern. Gibt die Zahl der gespeicherten Zuordnungen zurück."""
    import anthropic
    from database.client import get_supabase_client

    db = get_supabase_client()
    events: list[dict] = []
    seite = 0
    while limit is None or len(events) < limit:
        try:
            antwort = (
                db.table("events")
                .select("id,titel,ort,beschreibung,kategorie")
                .is_("unterkategorie", "null")
                .eq("abgelehnt", False)
                .gte("datum", date.today().isoformat())
                .order("datum")
                .range(seite * 1000, seite * 1000 + 999)
                .execute()
            )
        except Exception as e:
            logger.error("Unterkategorien: Events nicht ladbar (fehlt die Spalte „unterkategorie“?): %s", e)
            return 0
        daten = antwort.data or []
        events += daten
        seite += 1
        if len(daten) < 1000:
            break
    if limit is not None:
        events = events[:limit]
    if not events:
        logger.info("Unterkategorien: nichts zu tun")
        return 0

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("Unterkategorien: ANTHROPIC_API_KEY fehlt")
        return 0
    client = anthropic.Anthropic(api_key=api_key)
    zuordnung = bestimmen(client, events, liste_laden())
    verteilung: dict[str, int] = {}
    for slug in zuordnung.values():
        verteilung[slug] = verteilung.get(slug, 0) + 1
    logger.info("Unterkategorien: %d von %d Events zugeordnet – %s", len(zuordnung), len(events),
                ", ".join(f"{k} {v}" for k, v in sorted(verteilung.items(), key=lambda x: -x[1])))
    if dry_run:
        return 0

    gespeichert = 0
    for event_id, slug in zuordnung.items():
        try:
            db.table("events").update({"unterkategorie": slug}).eq("id", event_id).execute()
            gespeichert += 1
        except Exception as e:
            logger.warning("Unterkategorie für %s nicht gespeichert: %s", event_id, e)
    logger.info("Unterkategorien: %d gespeichert", gespeichert)
    return gespeichert


def _titel_schluessel(titel: str) -> str:
    """Titel für den Vergleich gleicher Stücke/Reihen: Kleinschreibung, nur Buchstaben und Ziffern."""
    return re.sub(r"[^a-z0-9äöüß]+", " ", (titel or "").lower()).strip()


def vereinheitlichen(dry_run: bool = False) -> int:
    """
    Gleiche Titel derselben Kategorie bekommen dieselbe Unterkategorie (Mehrheit der Zuordnungen).
    Die KI ordnet in Bündeln zu – „Der Hobbit“ landete so mal unter Theater, mal unter Comedy. Gibt es keine klare
    Mehrheit (Gleichstand), bleibt alles, wie es ist. „keine“ zählt mit, gewinnt aber nur als echte Mehrheit.
    """
    from collections import Counter, defaultdict
    from database.client import get_supabase_client

    db = get_supabase_client()
    zeilen: list[dict] = []
    seite = 0
    while True:
        try:
            antwort = (
                db.table("events")
                .select("id,titel,kategorie,unterkategorie")
                .not_.is_("unterkategorie", "null")
                .eq("abgelehnt", False)
                .gte("datum", date.today().isoformat())
                .range(seite * 1000, seite * 1000 + 999)
                .execute()
            )
        except Exception as e:
            logger.error("Unterkategorien vereinheitlichen: Events nicht ladbar: %s", e)
            return 0
        daten = antwort.data or []
        zeilen += daten
        seite += 1
        if len(daten) < 1000:
            break

    gruppen: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for z in zeilen:
        gruppen[(z.get("kategorie") or "", _titel_schluessel(z.get("titel") or ""))].append(z)
    aenderungen: list[tuple[str, str]] = []
    for (_, schluessel), gruppe in gruppen.items():
        if not schluessel or len(gruppe) < 2:
            continue
        haeufig = Counter(z["unterkategorie"] for z in gruppe).most_common()
        if len(haeufig) < 2 or haeufig[0][1] == haeufig[1][1]:
            continue  # schon einheitlich oder keine klare Mehrheit
        sieger = haeufig[0][0]
        aenderungen += [(z["id"], sieger) for z in gruppe if z["unterkategorie"] != sieger]
    logger.info("Unterkategorien vereinheitlichen: %d Termine angeglichen", len(aenderungen))
    if dry_run:
        return 0
    for event_id, slug in aenderungen:
        try:
            db.table("events").update({"unterkategorie": slug}).eq("id", event_id).execute()
        except Exception as e:
            logger.warning("Unterkategorie für %s nicht angeglichen: %s", event_id, e)
    return len(aenderungen)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Unterkategorien (Feinfilter) per KI nachtragen")
    parser.add_argument("--limit", type=int, default=None, help="Höchstzahl Events (Standard: alle kommenden)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    nachtragen(limit=args.limit, dry_run=args.dry_run)
    vereinheitlichen(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
