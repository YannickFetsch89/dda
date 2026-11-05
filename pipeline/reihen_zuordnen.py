"""
reihen_zuordnen.py – DiesDasDüsseldorf
Erkennt Reihen (wiederkehrende Events) und ordnet Events ihnen zu (Tabelle reihen, Spalte events.reihe_id).

Eine Reihe = gleicher bereinigter Titel am gleichen Ort an mindestens zwei verschiedenen Tagen.
„Gleicher Ort“ heißt: gleicher eigentlicher Ort (erstes Segment, z.B. „zakk – Halle“ → „zakk“) – dieselben
Regeln wie web/lib/abgelaufen.ts. Rein generische Titel („Konzert“, „Party“) bilden keine Reihe.
Jede Reihe bekommt beim Anlegen einen festen Slug – die URL /reihe/<slug> bleibt dauerhaft gleich,
auch wenn später neue Termine dazukommen oder alte ablaufen. Bestehende Zuordnungen werden nie
geändert, nur fehlende ergänzt.

Läuft als Schritt der Pipeline (main.py) mit dem Service-Key.
"""
import logging
import re
from collections import Counter, defaultdict
from datetime import date, timedelta

from database.client import get_supabase_client
from pipeline.slug_generator import _slugify, slug_mit_suffix

logger = logging.getLogger(__name__)

RUECKBLICK_TAGE = 365   # Events aus dem letzten Jahr zählen für die Reihen-Erkennung mit
MIN_TAGE = 2            # mindestens an so vielen verschiedenen Tagen
SEITE = 1000
STAPEL = 200

# Altdaten: Scraper hängten die Uhrzeit an den Titel („Japanviertel (14:00 Uhr)“) – wie web/lib/termine.ts
_ZEIT_IM_TITEL = re.compile(r"\s*[(\[]\s*\d{1,2}[:.]\d{2}\s*(?:Uhr)?\s*[)\]]\s*$", re.IGNORECASE)
# Ortsangaben ohne Aussagekraft – darüber entsteht keine Reihe (wie web/lib/abgelaufen.ts)
_ALLGEMEINE_ORTE = {"düsseldorf", "duesseldorf", "online", "diverse orte", "verschiedene orte", "tba", "n/a"}
# Titel, die allein nichts über das Event sagen – verschiedene Abende wären sonst eine „Reihe“
_GENERISCHE_TITEL = {
    "konzert", "konzerte", "party", "live", "livemusik", "live musik", "dj set", "dj", "disco", "show",
    "event", "veranstaltung", "programm", "vortrag", "lesung", "workshop", "ausstellung", "tba", "n/a",
    "geschlossene gesellschaft", "sonderveranstaltung", "gastspiel", "premiere",
}
_ORT_TRENNER = re.compile(r"\s+[–—\-/]\s+|[()]")


def basis_titel(titel: str) -> str:
    """Titel ohne angehängte Uhrzeit."""
    return _ZEIT_IM_TITEL.sub("", titel).strip() or titel


def _norm(text: str) -> str:
    """Kleinschreibung, ohne Satzzeichen, einfache Leerzeichen (wie norm() in web/lib/termine.ts)."""
    text = re.sub(r"[^\w\s-]", "", (text or "").replace("\u00ad", "").lower()).replace("_", "")
    return re.sub(r"\s+", " ", text).strip()


# Gegenden statt Orte: als erstes Segment („Rheinufer – Tonhallenufer“) taugen sie nicht als Basis
_GEGENDEN = {"rheinufer", "rheinuferpromenade", "hafen", "medienhafen", "altstadt", "carlstadt", "innenstadt", "stadtmitte"}


def _ort_schluessel(ort: str) -> str | None:
    """Ort normalisiert (Bindestrich = Leerzeichen), Wort „Düsseldorf“ entfernt; None wenn nichts bleibt."""
    s = re.sub(r"(^|\s)(düsseldorf|duesseldorf)(?=\s|$)", " ", _norm((ort or "").replace("-", " ")))
    s = re.sub(r"\s+", " ", s).strip()
    return None if len(s) < 3 or s in _ALLGEMEINE_ORTE else s


def ort_basis(ort: str) -> str | None:
    """
    Eigentlicher Ort = erstes aussagekräftiges Segment („zakk – Halle“ → „zakk“). Ist das eine Gegend
    („Rheinufer – Tonhallenufer“), zählt das nächste; besteht die Angabe nur aus einer Gegend, diese.
    """
    segmente = [s for s in (_ort_schluessel(t) for t in _ORT_TRENNER.split(ort or "")) if s]
    return next((s for s in segmente if s not in _GEGENDEN), segmente[0] if segmente else None)


def titel_schluessel(titel: str) -> str:
    """Titel ohne Uhrzeit, Bindestriche wie Leerzeichen („Jazz-Schmiede“ = „Jazz Schmiede“)."""
    return re.sub(r"\s+", " ", _norm(basis_titel(titel or "")).replace("-", " ")).strip()


def reihen_schluessel(titel: str, ort: str) -> str | None:
    """Schlüssel „titel|ort“ – None, wenn Titel oder Ort zu allgemein/kurz sind."""
    o = ort_basis(ort)
    t = titel_schluessel(titel)
    if not o or len(t) < 3 or t in _GENERISCHE_TITEL:
        return None
    return f"{t}|{o}"


def reihen_bilden(events: list[dict]) -> dict[str, list[dict]]:
    """Gruppiert Events nach Reihen-Schlüssel; nur Gruppen mit Terminen an mindestens MIN_TAGE Tagen."""
    gruppen: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        schluessel = reihen_schluessel(e.get("titel", ""), e.get("ort", ""))
        if schluessel:
            gruppen[schluessel].append(e)
    return {k: v for k, v in gruppen.items() if len({e["datum"] for e in v}) >= MIN_TAGE}


def reihe_slug(titel: str, ort: str, vergeben: set[str]) -> str:
    """Lesbarer, freier Slug aus Titel und Ort, z.B. „oeffentliche-fuehrung-kunstpalast“."""
    basis = "-".join(t for t in [_slugify(basis_titel(titel), 60), _slugify(ort, 30)] if t) or "reihe"
    return slug_mit_suffix(basis, vergeben)


def _alle_laden(abfrage_bauen) -> list[dict]:
    zeilen: list[dict] = []
    for seite in range(100):
        daten = abfrage_bauen().range(seite * SEITE, (seite + 1) * SEITE - 1).execute().data or []
        zeilen.extend(daten)
        if len(daten) < SEITE:
            break
    return zeilen


def reihen_zuordnen() -> int:
    """Legt fehlende Reihen an und ordnet Events zu. Gibt die Anzahl neu zugeordneter Events zurück."""
    db = get_supabase_client()
    ab = (date.today() - timedelta(days=RUECKBLICK_TAGE)).isoformat()
    try:
        events = _alle_laden(lambda: db.table("events").select("id, titel, ort, kategorie, datum, reihe_id")
                             .eq("abgelehnt", False).gte("datum", ab).order("id"))
        reihen = _alle_laden(lambda: db.table("reihen").select("id, slug, schluessel").order("id"))
    except Exception as e:
        logger.error("Reihen: Laden fehlgeschlagen: %s", e)
        return 0

    nach_schluessel = {r["schluessel"]: r["id"] for r in reihen}
    vergeben = {r["slug"] for r in reihen}
    gruppen = reihen_bilden(events)

    # 1) Fehlende Reihen anlegen (Titel/Ort vom jüngsten Termin, Kategorie die häufigste)
    neue = []
    for schluessel, gruppe in gruppen.items():
        if schluessel in nach_schluessel:
            continue
        vorbild = max(gruppe, key=lambda e: e["datum"])
        slug = reihe_slug(vorbild["titel"], vorbild["ort"], vergeben)
        vergeben.add(slug)
        kategorie = Counter(e.get("kategorie") for e in gruppe if e.get("kategorie")).most_common(1)
        neue.append({
            "slug": slug,
            "schluessel": schluessel,
            "titel": basis_titel(vorbild["titel"]),
            "ort": vorbild["ort"],
            "kategorie": kategorie[0][0] if kategorie else None,
        })
    for i in range(0, len(neue), STAPEL):
        try:
            # Schon vorhandene Schlüssel (z.B. paralleler Lauf) überspringen statt den Stapel zu verwerfen
            (db.table("reihen").upsert(neue[i:i + STAPEL], on_conflict="schluessel", ignore_duplicates=True)
             .execute())
        except Exception as e:
            # Z.B. Slug-Konflikt mit einem parallelen Lauf: einzeln nachziehen, nur die betroffene Reihe fehlt
            logger.warning("Reihen: Stapel fehlgeschlagen (%s) – lege einzeln an", e)
            for zeile in neue[i:i + STAPEL]:
                try:
                    db.table("reihen").upsert(zeile, on_conflict="schluessel", ignore_duplicates=True).execute()
                except Exception as e2:
                    logger.error("Reihen: %s nicht angelegt: %s", zeile["slug"], e2)
    if neue:
        try:
            reihen = _alle_laden(lambda: db.table("reihen").select("id, slug, schluessel").order("id"))
            nach_schluessel = {r["schluessel"]: r["id"] for r in reihen}
        except Exception as e:
            logger.error("Reihen: Neu laden fehlgeschlagen: %s", e)

    # 2) Events ohne Reihe zuordnen (bestehende Zuordnungen bleiben unangetastet)
    zugeordnet = 0
    for schluessel, gruppe in gruppen.items():
        reihe_id = nach_schluessel.get(schluessel)
        offen = [e["id"] for e in gruppe if not e.get("reihe_id")]
        if not reihe_id or not offen:
            continue
        for i in range(0, len(offen), STAPEL):
            try:
                (db.table("events").update({"reihe_id": reihe_id})
                 .in_("id", offen[i:i + STAPEL]).is_("reihe_id", "null").execute())
                zugeordnet += len(offen[i:i + STAPEL])
            except Exception as e:
                logger.error("Reihen: Zuordnung fehlgeschlagen (%s): %s", schluessel, e)

    logger.info("Reihen: %d neu angelegt, %d Events zugeordnet (%d Reihen insgesamt)",
                len(neue), zugeordnet, len(nach_schluessel))
    return zugeordnet
