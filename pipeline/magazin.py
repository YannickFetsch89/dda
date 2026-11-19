"""
magazin.py – DiesDasDüsseldorf
Magazin-Pipeline (Plan docs/plan-redaktion-2026-11-19.md, Schritt 3): Entwürfe für die laufenden Rubriken,
IndexNow-Meldung veröffentlichter Beiträge und täglicher Prüflauf.

Grundsatz (Plan T5): Die Pipeline schreibt nur Entwürfe (Status „entwurf“ oder „in_pruefung“). Veröffentlichen kann
nur der Auftraggeber im Supabase-Table-Editor – ein Datenbank-Trigger lehnt „veroeffentlicht“ von service_role ab.

Ablauf eines Entwurfs (Plan 4.2):
  1. Autor (Pseudonym) zur Rubrik aus magazin_autoren – ohne Autor kein Lauf (keine Kosten).
  2. Gleiche Rubrik und gleicher Zeitraum schon vorhanden → Abbruch (Prüfung g).
  3. Datenauswahl über die geschützte Website-Route /api/magazin/auswahl (T11). Jeder Fehler → Abbruch ohne Zeile,
     ohne Modellaufruf, ohne Kostenreservierung. Leere Auswahl → kein Entwurf, Hinweis im Log.
  4. Kostendeckel $10/Monat aus magazin_ki_kosten (Plan 4.4), Reservierung vor dem Aufruf.
  5. Ressort-Agent: Claude Opus 5.5 mit dem Schreibprofil des Pseudonyms (T7), strukturiertes JSON.
  6. Automatische Prüfungen (a)–(i), Ergebnis in „pruefung“; grün → in_pruefung, rot → entwurf.
  7. Entwurf speichern, Kosten messen, Vorschau-Link (mit Einmal-Schlüssel) ins Log.

Nutzung:
  python -m pipeline.magazin entwurf --rubrik wochenvorschau [--von 2026-11-30] [--dry-run]
  python -m pipeline.magazin entwurf --rubrik monats-tipps [--von 2026-12-01] [--dry-run]
  python -m pipeline.magazin melden [--dry-run]
  python -m pipeline.magazin pruefen [--dry-run]
Entwürfe nur mit MAGAZIN_AKTIV=1 (GitHub-Variable); --dry-run ruft weder das Modell noch schreibt es.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import secrets
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Protocol
from zoneinfo import ZoneInfo

import httpx

logger = logging.getLogger(__name__)

BERLIN = ZoneInfo("Europe/Berlin")
SITE_URL = os.getenv("SITE_URL", "https://diesdas.events").rstrip("/")
FEED_URL = f"{SITE_URL}/magazin/feed.xml"

# Modell (entschieden 19.11.2026): Claude Opus 5.5, $4 / $20 je 1 Mio. Tokens (Plan 4.4)
MODELL = "claude-opus-5-5"
PREIS_EIN = 4.0 / 1_000_000
PREIS_AUS = 20.0 / 1_000_000
DECKEL_USD = 10.0
SCHAETZUNG_USD = {"wochenvorschau": 0.22, "monats-tipps": 0.29}
PROMPT_VERSION = "2026-11-19.1"
AUSWAHL_TIMEOUT = 30
PROFIL_ORDNER = Path(__file__).with_name("magazin_profile")

RUBRIKEN_AUTOMATISCH = ("wochenvorschau", "monats-tipps")
RUBRIK_ERSATZ = {  # wie web/lib/magazin-bilder.ts (RUBRIK_ERSATZ)
    "wochenvorschau": "/fallback/theater-1.webp",
    "monats-tipps": "/fallback/theater-2.webp",
    "saison": "/fallback/theater-3.webp",
    "nachtleben": "/fallback/nacht-der-museen-2.webp",
    "genuss": "/fallback/sprachcafe-3.webp",
    "familie": "/fallback/ostern-3.webp",
    "stadtleben": "/fallback/sprachcafe-1.webp",
}
# Wie CHECK magazin_hero_pfad (database/magazin_2026-11-19.sql) und web/lib/magazin-bilder.ts
HERO_PFAD = re.compile(r"^/(magazin-bilder/[a-z0-9-]+|fallback|ort-bilder/weihnachtsmaerkte)/[a-z0-9-]+\.(webp|jpg|png)$")
FREMDFOTO = "/ort-bilder/weihnachtsmaerkte/koe-on-ice.webp"
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober",
          "November", "Dezember"]
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


# ── Zeiträume und Slugs ────────────────────────────────────────────────────────────────────────────

def heute_berlin() -> date:
    return datetime.now(BERLIN).date()


def zeitraum(rubrik: str, von: date | None = None, heute: date | None = None) -> tuple[date, date]:
    """Wochenvorschau: nächster Montag bis Sonntag. Monats-Tipps: nächster Monat (Plan 4.2 Punkt 1)."""
    heute = heute or heute_berlin()
    if rubrik == "wochenvorschau":
        start = von or heute + timedelta(days=(7 - heute.weekday()) % 7 or 7)
        if start.weekday() != 0:
            raise ValueError(f"Wochenvorschau muss an einem Montag beginnen, nicht {start}")
        return start, start + timedelta(days=6)
    if rubrik == "monats-tipps":
        start = von or (heute.replace(day=1) + timedelta(days=32)).replace(day=1)
        if start.day != 1:
            raise ValueError(f"Monats-Tipps beginnen am 1. eines Monats, nicht {start}")
        ende = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return start, ende
    raise ValueError(f"Keine automatische Rubrik: {rubrik}")


def slug_fuer(rubrik: str, von: date, bis: date) -> str:
    """Slugs nach Plan 5.1."""
    def tag(d: date) -> str:
        return f"{d.day}-{MONATE[d.month - 1].lower().replace('ä', 'ae')}"
    if rubrik == "wochenvorschau":
        return f"events-duesseldorf-{tag(von)}-bis-{tag(bis)}-{bis.year}"
    return f"top-events-duesseldorf-{MONATE[von.month - 1].lower().replace('ä', 'ae')}-{von.year}"


# ── Datenbank (austauschbar für Tests) ─────────────────────────────────────────────────────────────

class Datenbank(Protocol):
    def autor_fuer(self, rubrik: str) -> dict | None: ...
    def ausgabe_vorhanden(self, rubrik: str, von: str) -> bool: ...
    def monatskosten(self, seit_iso: str) -> float: ...
    def kosten_eintragen(self, eintrag: dict) -> str: ...
    def kosten_aktualisieren(self, kosten_id: str, werte: dict) -> None: ...
    def beitrag_anlegen(self, zeile: dict) -> str: ...
    def zu_melden(self) -> list[dict]: ...
    def gemeldet_setzen(self, beitrag_id: str, wert: str | None) -> None: ...
    def veroeffentlichte(self) -> list[dict]: ...
    def events_status(self, ids: list[str]) -> dict[str, dict]: ...
    def pruefung_setzen(self, beitrag_id: str, pruefung: dict) -> None: ...


class SupabaseDatenbank:
    """Echte Datenbank über den Service-Schlüssel (database/client.py)."""

    def __init__(self, client=None):
        if client is None:
            from database.client import get_supabase_client
            client = get_supabase_client()
        self.c = client

    def autor_fuer(self, rubrik: str) -> dict | None:
        r = (self.c.table("magazin_autoren").select("slug, name, schwerpunkt, rubriken").eq("aktiv", True)
             .contains("rubriken", [rubrik]).order("slug").limit(1).execute())
        return r.data[0] if r.data else None

    def ausgabe_vorhanden(self, rubrik: str, von: str) -> bool:
        r = (self.c.table("magazin_beitraege").select("id").eq("rubrik", rubrik).eq("gueltig_von", von)
             .neq("status", "zurueckgezogen").limit(1).execute())
        return bool(r.data)

    def monatskosten(self, seit_iso: str) -> float:
        r = self.c.table("magazin_ki_kosten").select("kosten_usd").gte("zeitpunkt", seit_iso).execute()
        return float(sum(float(z["kosten_usd"]) for z in (r.data or [])))

    def kosten_eintragen(self, eintrag: dict) -> str:
        return self.c.table("magazin_ki_kosten").insert(eintrag).execute().data[0]["id"]

    def kosten_aktualisieren(self, kosten_id: str, werte: dict) -> None:
        self.c.table("magazin_ki_kosten").update(werte).eq("id", kosten_id).execute()

    def beitrag_anlegen(self, zeile: dict) -> str:
        return self.c.table("magazin_beitraege").insert(zeile).execute().data[0]["id"]

    def zu_melden(self) -> list[dict]:
        r = (self.c.table("magazin_beitraege")
             .select("id, slug, rubrik, status, veroeffentlicht_am, aktualisiert_am, gemeldet_am")
             .in_("status", ["veroeffentlicht", "zurueckgezogen"]).execute())
        return r.data or []

    def gemeldet_setzen(self, beitrag_id: str, wert: str | None) -> None:
        self.c.table("magazin_beitraege").update({"gemeldet_am": wert}).eq("id", beitrag_id).execute()

    def veroeffentlichte(self) -> list[dict]:
        r = (self.c.table("magazin_beitraege")
             .select("id, slug, rubrik, inhalt_md, event_ids, gueltig_bis, naechste_pruefung, veroeffentlicht_am")
             .eq("status", "veroeffentlicht").execute())
        return r.data or []

    def events_status(self, ids: list[str]) -> dict[str, dict]:
        if not ids:
            return {}
        r = self.c.table("events").select("id, abgesagt, abgelehnt").in_("id", ids).execute()
        return {z["id"]: z for z in (r.data or [])}

    def pruefung_setzen(self, beitrag_id: str, pruefung: dict) -> None:
        self.c.table("magazin_beitraege").update({"pruefung": pruefung}).eq("id", beitrag_id).execute()


# ── Auswahl über die Website-Route (T11) ───────────────────────────────────────────────────────────

class AuswahlFehler(Exception):
    """Route nicht erreichbar oder Antwort unbrauchbar → Lauf dieser Rubrik endet ohne Kosten."""


def auswahl_holen(rubrik: str, von: date, bis: date, schluessel: str | None, post: Callable | None = None) -> dict:
    """POST /api/magazin/auswahl. Status ≠ 200, Zeitüberschreitung, kaputtes JSON, fehlende Felder → AuswahlFehler."""
    if not schluessel:
        raise AuswahlFehler("MAGAZIN_JOB_SCHLUESSEL fehlt")
    post = post or httpx.post
    try:
        antwort = post(f"{SITE_URL}/api/magazin/auswahl",
                       json={"rubrik": rubrik, "von": von.isoformat(), "bis": bis.isoformat()},
                       headers={"x-magazin-schluessel": schluessel}, timeout=AUSWAHL_TIMEOUT)
    except Exception as e:  # Zeitüberschreitung, Netzfehler
        raise AuswahlFehler(f"Auswahl-Route nicht erreichbar: {e}") from e
    if antwort.status_code != 200:
        raise AuswahlFehler(f"Auswahl-Route antwortet {antwort.status_code}")
    try:
        daten = antwort.json()
    except Exception as e:
        raise AuswahlFehler("Auswahl-Route liefert kein gültiges JSON") from e
    if not isinstance(daten, dict) or daten.get("rubrik") != rubrik or daten.get("von") != von.isoformat() \
            or daten.get("bis") != bis.isoformat() or not isinstance(daten.get("kandidaten"), list):
        raise AuswahlFehler("Auswahl-Antwort ohne rubrik/von/bis/kandidaten")
    for k in daten["kandidaten"]:
        if not isinstance(k, dict) or not UUID.match(str(k.get("id", ""))):
            raise AuswahlFehler("Auswahl-Antwort mit ungültiger Event-ID")
    return daten


# ── Prüfungen (Plan 4.2 Schritt 3) ─────────────────────────────────────────────────────────────────

UHRZEIT = re.compile(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b(?!\.)|\bUhr\b")
PREIS = re.compile(r"€|\bEuro\b|\bEUR\b|\bkostenlos\b|\beintritt frei\b", re.I)
AUSVERKAUFT = re.compile(r"ausverkauft|restlos", re.I)
DATUM_MONAT = re.compile(r"\b(\d{1,2})\.\s*(" + "|".join(MONATE) + r")\b")
DATUM_ZAHL = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})?")
CLICKBAIT = re.compile(r"unglaublich|du wirst nicht glauben|ihr werdet nicht glauben|geheimtipp,? den keiner kennt|"
                       r"schockierend|der wahnsinn|muss man gesehen haben", re.I)
ICH_FORM = re.compile(r"\b(ich|mich|mir|mein|meine|meinen|meinem|meiner|meines)\b", re.I)
GOOGLE = re.compile(r"google|sterne-bewertung|\bbewertet mit\b|\d[,.]\d\s*sterne", re.I)
HUB_KOEPFE = ("Weihnachtsmärkte in Düsseldorf", "Clubs in Düsseldorf", "Restaurants & Cafés", "Kneipen & Bars",
              "Spielplätze in Düsseldorf")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]*)\)")
INTERNE_PRAEFIXE = ("/heute", "/morgen", "/wochenende", "/entdecken", "/guides", "/kategorie/", "/stadtteil",
                    "/kostenlos", "/magazin", "/reihe/")
WOERTER = {"wochenvorschau": (600, 1800), "monats-tipps": (600, 1800)}


def daten_im_text(text: str, jahr: int) -> list[date]:
    """Alle Datumsangaben (Tag + Monatsname, TT.MM.) als Kalendertage; unmögliche werden übersprungen."""
    tage: list[date] = []
    for m in DATUM_MONAT.finditer(text):
        try:
            tage.append(date(jahr, MONATE.index(m.group(2)) + 1, int(m.group(1))))
        except ValueError:
            pass
    for m in DATUM_ZAHL.finditer(text):
        j = int(m.group(3)) if m.group(3) else jahr
        j = j + 2000 if j < 100 else j
        try:
            tage.append(date(j, int(m.group(2)), int(m.group(1))))
        except ValueError:
            pass
    return tage


def link_ok(ziel: str, event_pfade: set[str]) -> bool:
    """Externe Links nur https://, interne nur auf bekannte Seiten, Tagesseiten und ausgewählte Events (Prüfung c)."""
    if ziel.startswith("https://"):
        return True
    if not ziel.startswith("/") or ziel.startswith("//") or ".." in ziel:
        return False
    if ziel == "/" or ziel in event_pfade or re.fullmatch(r"/tag/\d{4}-\d{2}-\d{2}", ziel):
        return True
    return ziel.startswith(INTERNE_PRAEFIXE)


@dataclass
class Entwurf:
    """Antwort des Ressort-Agenten (strukturiertes JSON) plus Kontext."""
    titel: str
    teaser: str
    kurzfassung: list[str]
    abschnitte: list[dict]
    faq: list[dict] = field(default_factory=list)


def pruefen(e: Entwurf, rubrik: str, von: date, bis: date, kandidaten: list[dict], hero: str,
            erlaubte_heros: set[str] | None = None) -> dict:
    """Prüfungen (a)–(i). Ergebnis {ergebnis: gruen|rot, punkte: [...]}. (g) prüft der Lauf vor dem Modellaufruf."""
    punkte: list[str] = []
    ids = {k["id"] for k in kandidaten}
    pfade = {k.get("pfad", "") for k in kandidaten}
    fliesstext = "\n".join(a.get("text_md", "") for a in e.abschnitte)
    # (a) nur Events aus der Auswahl
    fremd = sorted({i for a in e.abschnitte for i in a.get("event_ids", []) if i not in ids})
    if fremd:
        punkte.append(f"(a) Event-IDs außerhalb der Auswahl: {', '.join(fremd)}")
    # FAQ (Frage und Antwort) zählt wie Fließtext: Sie steht sichtbar auf der Seite und im FAQPage-JSON-LD
    # (Cursor-Gesamtprüfung 19.11.2026)
    faq_text = "\n".join(f"{f.get('frage', '')}\n{f.get('antwort', '')}" for f in (e.faq or []))
    fliess_mit_faq = "\n".join(x for x in (fliesstext, faq_text) if x)
    # (b) Uhrzeiten, Preise, „ausverkauft“ nirgends; Daten nur in Titel/Teaser/Überschriften/Kurzfassung und im Zeitraum
    alles = "\n".join([e.titel, e.teaser, *e.kurzfassung, *(a.get("ueberschrift", "") for a in e.abschnitte), fliess_mit_faq])
    for name, muster in (("Uhrzeit", UHRZEIT), ("Preis", PREIS), ("„ausverkauft“", AUSVERKAUFT)):
        treffer = muster.search(alles)
        if treffer:
            punkte.append(f"(b) {name} im Text: „{treffer.group(0)}“")
    if daten_im_text(fliess_mit_faq, von.year):
        punkte.append("(b) Datumsangabe im Fließtext oder in der FAQ (Daten stehen in den Karten)")
    kopf = "\n".join([e.titel, e.teaser, *e.kurzfassung, *(a.get("ueberschrift", "") for a in e.abschnitte)])
    for d in daten_im_text(kopf, von.year):
        # Jahreswechsel (z. B. 28.12.–03.01.): „2. Januar“ ohne Jahr gehört zum Folgejahr
        naechstes = d.replace(year=d.year + 1) if not (d.month == 2 and d.day == 29) else d
        if not (von <= d <= bis or von <= naechstes <= bis):
            punkte.append(f"(b) Datum {d.isoformat()} außerhalb des Zeitraums {von}–{bis}")
    # (c) Links
    for m in LINK.finditer(fliess_mit_faq):
        if not link_ok(m.group(2), pfade):
            punkte.append(f"(c) Link nicht erlaubt oder unbekannt: {m.group(2)}")
    # (d) Längen
    if not (1 <= len(e.titel) <= 90):
        punkte.append(f"(d) Titel hat {len(e.titel)} Zeichen (höchstens 90)")
    if not (80 <= len(e.teaser) <= 160):
        punkte.append(f"(d) Teaser hat {len(e.teaser)} Zeichen (80–160)")
    if not (3 <= len(e.kurzfassung) <= 5):
        punkte.append(f"(d) Kurzfassung hat {len(e.kurzfassung)} Punkte (3–5)")
    unten, oben = WOERTER.get(rubrik, (600, 1800))
    woerter = len(fliesstext.split())
    if not (unten <= woerter <= oben):
        punkte.append(f"(d) Text hat {woerter} Wörter ({unten}–{oben})")
    # (e) Clickbait und Ich-Formen des Pseudonyms
    if CLICKBAIT.search(alles):
        punkte.append(f"(e) Clickbait: „{CLICKBAIT.search(alles).group(0)}“")
    # Ich-Form nur in der Stimme des Pseudonyms – FAQ-Fragen stehen in der Stimme der Leser („Wo finde ich …?“)
    stimme = "\n".join([e.titel, e.teaser, *e.kurzfassung, *(a.get("ueberschrift", "") for a in e.abschnitte), fliesstext,
                        *(f.get("antwort", "") for f in (e.faq or []))])
    if ICH_FORM.search(stimme):
        punkte.append(f"(e) Ich-Form: „{ICH_FORM.search(stimme).group(0)}“")
    # (f) keine Google-Inhalte
    if GOOGLE.search(alles):
        punkte.append(f"(f) Google-Inhalt: „{GOOGLE.search(alles).group(0)}“")
    # (h) Titel nicht mit dem Kopfbegriff eines Guides
    if any(e.titel.startswith(k) for k in HUB_KOEPFE):
        punkte.append("(h) Titel beginnt mit dem Kopfbegriff eines Guides (E5)")
    # (i) Aufmacherbild
    erlaubte = erlaubte_heros if erlaubte_heros is not None else set(RUBRIK_ERSATZ.values())
    if hero.startswith("/fallback/") and hero not in erlaubte:
        punkte.append(f"(i) Aufmacherbild nicht erlaubt: {hero}")
    elif not HERO_PFAD.match(hero) or hero == FREMDFOTO:
        # Wie der CHECK magazin_hero_pfad: nur erlaubte Ordner, Fremdfoto koe-on-ice nie (Plan 3.1, 7.2)
        punkte.append(f"(i) Aufmacherbild nicht erlaubt: {hero}")
    return {"ergebnis": "rot" if punkte else "gruen", "punkte": punkte, "zeitpunkt": datetime.now(timezone.utc).isoformat()}


# ── Text zusammensetzen ────────────────────────────────────────────────────────────────────────────

def inhalt_bauen(e: Entwurf, ids: set[str]) -> tuple[str, list[str]]:
    """Abschnitte → eingeschränktes Markdown mit {{event:…}}-Einbettungen (nur IDs aus der Auswahl)."""
    teile: list[str] = []
    eingebettet: list[str] = []
    for a in e.abschnitte:
        if a.get("ueberschrift"):
            teile.append(f"## {a['ueberschrift'].strip()}")
        if a.get("text_md"):
            teile.append(a["text_md"].strip())
        for i in a.get("event_ids", []):
            if i in ids and i not in eingebettet:
                teile.append(f"{{{{event:{i}}}}}")
                eingebettet.append(i)
    return "\n\n".join(teile) + "\n", eingebettet


# ── Ressort-Agent (Claude) ─────────────────────────────────────────────────────────────────────────

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["titel_vorschlaege", "teaser", "kurzfassung", "abschnitte", "faq"],
    "properties": {
        "titel_vorschlaege": {"type": "array", "items": {"type": "string"}},
        "teaser": {"type": "string"},
        "kurzfassung": {"type": "array", "items": {"type": "string"}},
        "abschnitte": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False, "required": ["ueberschrift", "text_md", "event_ids"],
                "properties": {"ueberschrift": {"type": "string"}, "text_md": {"type": "string"},
                               "event_ids": {"type": "array", "items": {"type": "string"}}},
            },
        },
        "faq": {
            "type": "array",
            "items": {"type": "object", "additionalProperties": False, "required": ["frage", "antwort"],
                      "properties": {"frage": {"type": "string"}, "antwort": {"type": "string"}}},
        },
    },
}

REGELN = """Du schreibst einen Beitrag für das Magazin von dies.das.düsseldorf. Der Auftraggeber prüft und gibt frei.

Regeln (verbindlich):
- Ansprache ihr/euch, locker und konkret, keine Werbesprache, kein Clickbait.
- Nutze NUR die mitgelieferten Daten. Erfinde nichts: kein Line-up, keine Preise, keine Verfügbarkeit.
- Im Fließtext (text_md) KEINE Uhrzeiten, KEINE Datumsangaben, KEINE Preise und nie „ausverkauft“ oder „restlos“.
  Diese Fakten zeigen die eingebetteten Event-Karten. Datumsangaben sind nur in Titel, Teaser, Überschriften und
  Kurzfassung erlaubt und nur innerhalb des Zeitraums der Ausgabe.
- Betten Events nur über ihre ID in event_ids ein; nur IDs aus der Liste.
- Superlative nur mit Begründung. Keine Bewertungen oder Sterne, nichts aus Google.
- Das Pseudonym spricht nie in der Ich-Form und erzählt keine eigenen Erlebnisse, Ausbildung oder Herkunft.
- Der Titel beginnt nie mit „Weihnachtsmärkte in Düsseldorf“, „Clubs in Düsseldorf“, „Restaurants & Cafés“,
  „Kneipen & Bars“ oder „Spielplätze in Düsseldorf“.
- Interne Links nur als [Text](/pfad) auf Seiten wie /wochenende, /guides/…, /tag/JJJJ-MM-TT oder die Event-Pfade
  aus der Liste. Externe Links nur https://.
- Länge: Titel 40–70 Zeichen (höchstens 90), Teaser 80–160 Zeichen, Kurzfassung 3–5 Punkte, Fließtext
  insgesamt 600–1800 Wörter. Drei Titelvorschläge, der beste zuerst. FAQ 0–3 Fragen.
"""

VORLAGEN = {
    "wochenvorschau": "Rubrik Wochenvorschau „Was ist los in Düsseldorf?“: Highlight der Woche zuerst, dann die Tage "
                      "Montag bis Sonntag mit je 2–3 Events (Überschrift je Tag, z. B. „Montag, 30. November“), "
                      "zum Schluss ein Hinweis auf [das Wochenende](/wochenende).",
    "monats-tipps": "Rubrik Monats-Tipps „Top-Events im <Monat>“: Top-Event des Monats zuerst, dann Abschnitte nach "
                    "Stimmung (Konzerte, Bühne, Familie, Ausgehen …) mit 10–15 Events insgesamt.",
}


def profil_laden(autor_slug: str) -> str:
    """Schreibprofil des Pseudonyms (T7): <autor>.md, sonst die Vorlage _standard.md."""
    for name in (f"{autor_slug}.md", "_standard.md"):
        p = PROFIL_ORDNER / name
        if p.exists():
            if name == "_standard.md":
                logger.warning("Kein Schreibprofil für %s – nutze _standard.md", autor_slug)
            return p.read_text(encoding="utf-8")
    return ""


def eingabe_bauen(rubrik: str, von: date, bis: date, auswahl: dict, autor: dict) -> str:
    besonders = auswahl.get("highlight") or auswahl.get("top")
    return json.dumps({
        "rubrik": rubrik, "zeitraum": {"von": von.isoformat(), "bis": bis.isoformat()},
        "pseudonym": autor.get("name"), "highlight_oder_top_event_id": besonders,
        "events": [{k: e.get(k) for k in ("id", "titel", "datum", "datum_bis", "uhrzeit", "ort", "stadtteil",
                                          "kategorie", "preis", "beschreibung", "pfad")} for e in auswahl["kandidaten"]],
    }, ensure_ascii=False)


@dataclass
class KiAntwort:
    daten: dict
    tokens_ein: int
    tokens_aus: int
    modell: str


def claude_aufrufen(system: str, eingabe: str) -> KiAntwort:
    """Ein Aufruf, strukturiertes JSON (output_config), adaptives Denken (Standard bei Opus 5.5), effort medium."""
    import anthropic
    client = anthropic.Anthropic()
    antwort = client.messages.create(
        model=MODELL, max_tokens=16000, system=system,
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": eingabe}],
        # Server-seitiger Ausweich bei einer Ablehnung (Sicherheitsklassifikator): dieselbe Anfrage läuft dann auf einem
        # passenden anderen Modell weiter. Über extra_* gesendet, weil das gepinnte SDK den Parameter evtl. nicht kennt.
        extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
        extra_body={"fallbacks": "default"},
    )
    if antwort.stop_reason == "refusal":
        raise RuntimeError("Das Modell hat den Entwurf abgelehnt (stop_reason refusal)")
    if antwort.stop_reason == "max_tokens":
        raise RuntimeError("Antwort abgeschnitten (max_tokens)")
    roh = next(b.text for b in antwort.content if b.type == "text")
    return KiAntwort(json.loads(roh), antwort.usage.input_tokens, antwort.usage.output_tokens, antwort.model)


# ── Lauf: Entwurf ──────────────────────────────────────────────────────────────────────────────────

def monatsbeginn_utc(jetzt: datetime | None = None) -> str:
    j = (jetzt or datetime.now(BERLIN)).astimezone(BERLIN)
    return j.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc).isoformat()


def entwurf_erstellen(db: Datenbank, rubrik: str, von: date | None = None, *, dry_run: bool = False,
                      schluessel: str | None = None, post: Callable | None = None,
                      ki: Callable[[str, str], KiAntwort] | None = None, heute: date | None = None) -> str | None:
    """Ein Entwurf für eine laufende Rubrik. Rückgabe: Vorschau-URL oder None (nichts angelegt)."""
    start, ende = zeitraum(rubrik, von, heute)
    autor = db.autor_fuer(rubrik)
    if not autor:
        logger.warning("Magazin %s %s: kein aktiver Autor für die Rubrik – kein Entwurf (E15)", rubrik, start)
        return None
    if db.ausgabe_vorhanden(rubrik, start.isoformat()):
        logger.info("Magazin %s %s: Ausgabe existiert schon – kein zweiter Entwurf (Prüfung g)", rubrik, start)
        return None
    try:
        auswahl = auswahl_holen(rubrik, start, ende, schluessel if schluessel is not None else os.getenv("MAGAZIN_JOB_SCHLUESSEL"), post)
    except AuswahlFehler as e:
        logger.error("Magazin %s %s: %s – Abbruch ohne Entwurf und ohne Kosten", rubrik, start, e)
        raise
    if not auswahl["kandidaten"]:
        logger.info("Magazin %s %s: keine passenden Events – kein Entwurf", rubrik, start)
        return None
    schaetzung = SCHAETZUNG_USD[rubrik]
    bisher = db.monatskosten(monatsbeginn_utc())
    if bisher + schaetzung > DECKEL_USD:
        logger.error("Magazin: Kostendeckel erreicht (%.2f $ + %.2f $ > %.2f $) – kein Aufruf", bisher, schaetzung, DECKEL_USD)
        return None
    system = "\n\n".join(x for x in (REGELN, VORLAGEN[rubrik], profil_laden(autor["slug"])) if x)
    eingabe = eingabe_bauen(rubrik, start, ende, auswahl, autor)
    if dry_run:
        logger.info("[Dry-Run] %s %s–%s: %d Kandidaten, Autor %s, geschätzt %.2f $ (Monat bisher %.2f $)",
                    rubrik, start, ende, len(auswahl["kandidaten"]), autor["slug"], schaetzung, bisher)
        return None
    kosten_id = db.kosten_eintragen({"art": "reserviert", "kosten_usd": schaetzung, "modell": MODELL})
    try:
        antwort = (ki or claude_aufrufen)(system, eingabe)
    except Exception:
        logger.exception("Magazin %s %s: Modellaufruf fehlgeschlagen (Reservierung bleibt stehen)", rubrik, start)
        raise
    kosten = round(antwort.tokens_ein * PREIS_EIN + antwort.tokens_aus * PREIS_AUS, 4)
    d = antwort.daten
    titel = (d.get("titel_vorschlaege") or ["Ohne Titel"])[0].strip()
    e = Entwurf(titel=titel, teaser=(d.get("teaser") or "").strip(), kurzfassung=[s.strip() for s in d.get("kurzfassung") or []],
                abschnitte=d.get("abschnitte") or [], faq=d.get("faq") or [])
    hero = RUBRIK_ERSATZ[rubrik]
    pruefung = pruefen(e, rubrik, start, ende, auswahl["kandidaten"], hero)
    inhalt, eingebettet = inhalt_bauen(e, {k["id"] for k in auswahl["kandidaten"]})
    vorschau = secrets.token_urlsafe(32)
    zeile = {
        "slug": slug_fuer(rubrik, start, ende), "rubrik": rubrik, "autor_slug": autor["slug"],
        "titel": e.titel[:90], "teaser": e.teaser if 80 <= len(e.teaser) <= 160 else None,
        "inhalt_md": inhalt, "kurzfassung": e.kurzfassung if 3 <= len(e.kurzfassung) <= 5 else None,
        "faq": e.faq or None, "hero_bild": hero, "hero_alt": f"Symbolbild zur Rubrik {rubrik}",
        "hero_nachweis": "Symbolbild", "gueltig_von": start.isoformat(), "gueltig_bis": ende.isoformat(),
        "event_ids": eingebettet, "ort_slugs": [], "quellen": [],
        # Nie „veroeffentlicht“ – das setzt nur der Auftraggeber (Plan T5)
        "status": "in_pruefung" if pruefung["ergebnis"] == "gruen" else "entwurf",
        "pruefung": pruefung,
        "vorschau_hash": hashlib.sha256(vorschau.encode()).hexdigest(),
        "ki_entwurf": {"modell": antwort.modell, "profil": autor["slug"], "prompt_version": PROMPT_VERSION,
                       "tokens_ein": antwort.tokens_ein, "tokens_aus": antwort.tokens_aus, "kosten_usd": kosten,
                       "titel_vorschlaege": d.get("titel_vorschlaege") or [],
                       "eingabe_hash": hashlib.sha256(eingabe.encode()).hexdigest(),
                       "zeitpunkt": datetime.now(timezone.utc).isoformat()},
    }
    beitrag_id = db.beitrag_anlegen(zeile)
    db.kosten_aktualisieren(kosten_id, {"art": "gemessen", "kosten_usd": kosten, "beitrag_id": beitrag_id,
                                        "modell": antwort.modell, "tokens_ein": antwort.tokens_ein,
                                        "tokens_aus": antwort.tokens_aus})
    url = f"{SITE_URL}/magazin/vorschau/{beitrag_id}?s={vorschau}"
    logger.info("Magazin %s %s: Entwurf angelegt (Prüfung %s, %.4f $). Vorschau: %s",
                rubrik, start, pruefung["ergebnis"], kosten, url)
    for p in pruefung["punkte"]:
        logger.info("  Prüfung: %s", p)
    return url


# ── Lauf: IndexNow (Plan 5.8, T6) ──────────────────────────────────────────────────────────────────

def feed_aktiv(get: Callable | None = None) -> bool:
    """Der Feed antwortet nur mit Schalter an mit 200 (T9). Fehler/Zeitüberschreitung → nicht melden."""
    try:
        return (get or httpx.get)(FEED_URL, timeout=15).status_code == 200
    except Exception as e:
        logger.warning("Magazin-Feed nicht erreichbar: %s", e)
        return False


def melden_lauf(db: Datenbank, *, dry_run: bool = False, get: Callable | None = None,
                melden: Callable[[list[str]], int] | None = None, jetzt: datetime | None = None) -> int:
    """Neu sichtbare oder inhaltlich geänderte Beiträge melden; zurückgezogene, die gemeldet waren, ebenfalls."""
    if not feed_aktiv(get):
        logger.info("Magazin: Feed nicht aktiv (Schalter aus) – keine IndexNow-Meldung")
        return 0
    if melden is None:
        from pipeline.indexnow import melden as melden_indexnow
        melden = lambda urls: melden_indexnow(urls, dry_run=dry_run)  # noqa: E731
    jetzt = jetzt or datetime.now(timezone.utc)
    neu, zurueck = [], []
    for b in db.zu_melden():
        if b["status"] == "veroeffentlicht":
            sichtbar = b.get("veroeffentlicht_am") and datetime.fromisoformat(b["veroeffentlicht_am"]) <= jetzt
            stand = b.get("aktualisiert_am") or b.get("veroeffentlicht_am")
            if sichtbar and (not b.get("gemeldet_am") or (stand and stand > b["gemeldet_am"])):
                neu.append(b)
        elif b["status"] == "zurueckgezogen" and b.get("gemeldet_am"):
            zurueck.append(b)
    if not neu and not zurueck:
        return 0
    urls = [f"{SITE_URL}/magazin/{b['slug']}" for b in neu + zurueck]
    urls += [f"{SITE_URL}/magazin"] + sorted({f"{SITE_URL}/magazin/rubrik/{b['rubrik']}" for b in neu + zurueck})
    gemeldet = melden(urls)
    if gemeldet and not dry_run:
        for b in neu:
            db.gemeldet_setzen(b["id"], jetzt.isoformat())
        for b in zurueck:
            db.gemeldet_setzen(b["id"], None)
    logger.info("Magazin: %d URLs gemeldet (%d neu/geändert, %d zurückgezogen)", gemeldet, len(neu), len(zurueck))
    return gemeldet


# ── Lauf: täglicher Prüflauf (Plan 5.12) ───────────────────────────────────────────────────────────

EINBETTUNG_EVENT = re.compile(r"\{\{\s*event\s*:\s*([0-9a-fA-F-]{36})\s*\}\}")


def pruef_lauf(db: Datenbank, *, dry_run: bool = False, heute: date | None = None) -> int:
    """Veröffentlichte Beiträge: abgesagte/gelöschte Events, tote Links, fällige Überarbeitung, abgelaufen."""
    heute = heute or heute_berlin()
    beitraege = db.veroeffentlichte()
    ids = sorted({i for b in beitraege for i in (b.get("event_ids") or [])})
    status = db.events_status(ids)
    rot = 0
    for b in beitraege:
        punkte = []
        for i in b.get("event_ids") or []:
            s = status.get(i)
            if not s or s.get("abgelehnt"):
                punkte.append(f"Event {i} existiert nicht mehr")
            elif s.get("abgesagt"):
                punkte.append(f"Event {i} ist abgesagt")
        for m in LINK.finditer(b.get("inhalt_md") or ""):
            if not link_ok(m.group(2), set()) and not m.group(2).startswith("/event/"):
                punkte.append(f"Link prüfen: {m.group(2)}")
        if b.get("naechste_pruefung") and b["naechste_pruefung"] <= heute.isoformat():
            punkte.append(f"Überarbeitung fällig seit {b['naechste_pruefung']}")
        if b.get("gueltig_bis") and b["rubrik"] in RUBRIKEN_AUTOMATISCH and b["gueltig_bis"] < heute.isoformat():
            punkte.append("Ausgabe abgelaufen (Hinweisbox aktiv, nach 30 Tagen noindex)")
        ergebnis = {"ergebnis": "rot" if any(not p.startswith("Ausgabe abgelaufen") for p in punkte) else "gruen",
                    "punkte": punkte, "lauf": "taeglich", "zeitpunkt": datetime.now(timezone.utc).isoformat()}
        if ergebnis["ergebnis"] == "rot":
            rot += 1
            logger.warning("Magazin-Prüflauf %s: %s", b["slug"], "; ".join(punkte))
        if not dry_run:
            db.pruefung_setzen(b["id"], ergebnis)
    logger.info("Magazin-Prüflauf: %d Beiträge geprüft, %d mit Befund", len(beitraege), rot)
    return rot


# ── Kommandozeile ──────────────────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="Magazin-Pipeline (Entwurf, IndexNow, Prüflauf)")
    sub = p.add_subparsers(dest="aufgabe", required=True)
    e = sub.add_parser("entwurf")
    e.add_argument("--rubrik", choices=RUBRIKEN_AUTOMATISCH, required=True)
    e.add_argument("--von", type=date.fromisoformat)
    e.add_argument("--dry-run", action="store_true")
    for name in ("melden", "pruefen"):
        sub.add_parser(name).add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    if a.aufgabe == "entwurf" and not a.dry_run and os.getenv("MAGAZIN_AKTIV") != "1":
        logger.info("MAGAZIN_AKTIV ist nicht 1 – keine Entwürfe (nur --dry-run)")
        return 0
    db = SupabaseDatenbank()
    try:
        if a.aufgabe == "entwurf":
            entwurf_erstellen(db, a.rubrik, a.von, dry_run=a.dry_run)
        elif a.aufgabe == "melden":
            melden_lauf(db, dry_run=a.dry_run)
        else:
            pruef_lauf(db, dry_run=a.dry_run)
    except AuswahlFehler:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
