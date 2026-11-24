"""
quellen_rang.py – DiesDasDüsseldorf
Rangfolge der Quellen (Plan docs/plan-quellen-ausbau-2026-11-23.md, Abschnitt 4.1, Schritt R1).

Kleiner Rang = bessere Quelle. Liefern zwei Quellen dasselbe Event, wird die mit dem strikt besseren Rang die
Hauptquelle (quelle_name, quelle_url, Link „Zum Termin“) – in der Deduplizierung, beim Speichern und bei den
Dubletten-Vorschlägen.

  1  Veranstalter / Haus          Tier-2- und Tier-3-Scraper, Event-Meldungen, Redaktions-Einträge
  2  Offizieller Ticketverkauf    Ticketmaster (später Eventim, Reservix, ADticket, Stagedates)
  3  Offizielle Portale           VisitDüsseldorf, Kulturportal, Meetup.com, Resident Advisor
  4  Aggregatoren                 PRINZ.de, AllEvents.in, Songkick (alte Zeilen: Eventbrite, eventfinder …)
  5  Rausgegangen                 nur, wenn sonst nichts

Zwei Tabellen, weil der Name im Lauf und der gespeicherte Name auseinanderfallen können (Plan 4.1, Nr. 19):
- Im Lauf gilt der Anzeigename aus main.py QUELLEN (Feld `_scraper`, gesetzt in pipeline/lauf_report.py).
  Unbekannter Anzeigename: Rang 1 bei Tier 2/3, sonst 4.
- Für gespeicherte Zeilen gilt `quelle_name` (Anzeigenamen plus die QUELLE_NAME-Konstanten der Module).
  Unbekannter gespeicherter Name (z. B. CSV-Namen der kleinen Weihnachtsmärkte): Rang 3 – ein Haus oder ein
  Ticketverkauf löst ihn ab, ein Aggregator nicht.
Rausgegangen erkennt die Funktion zusätzlich an der URL. Andere Domains in `quelle_url` zählen NICHT: ein Haus, das
auf eventim.de verlinkt, bleibt Rang 1.

Dieselbe Tabelle für gespeicherte Namen steht in web/lib/quellen-rang.ts (Admin-Bereich); beide prüfen gegen
tests/fixtures/quellen_rang.json.
"""
from typing import Optional

HAUS = 1
TICKETVERKAUF = 2
PORTAL = 3
AGGREGATOR = 4
RAUSGEGANGEN = 5

# Feld im Event, in dem der Lauf-Report den Anzeigenamen der Quelle ablegt (pipeline/lauf_report.py, SCRAPER_FELD)
SCRAPER_FELD = "_scraper"
TIER_FELD = "_tier"

# Anzeigenamen aus main.py QUELLEN → Rang. Ein Test verlangt, dass jede Zeile aus QUELLEN hier steht.
RANG_ANZEIGE: dict[str, int] = {
    # Tier 1
    "Ticketmaster": TICKETVERKAUF,
    "Kulturportal Düsseldorf": PORTAL,
    "VisitDüsseldorf": PORTAL,
    "VisitDüsseldorf Führungen": PORTAL,
    "Meetup.com": PORTAL,
    "Resident Advisor": PORTAL,
    "PRINZ.de Düsseldorf": AGGREGATOR,
    "Songkick": AGGREGATOR,
    "AllEvents.in Düsseldorf": AGGREGATOR,
    "Rausgegangen": RAUSGEGANGEN,
    # Tier 2: Häuser
    "Tonhalle Düsseldorf": HAUS,
    "zakk": HAUS,
    "Deutsche Oper am Rhein": HAUS,
    "Düsseldorfer Schauspielhaus": HAUS,
    "d-live": HAUS,
    "Kunstpalast Düsseldorf": HAUS,
    "Kunstsammlung NRW (K20/K21)": HAUS,
    "NRW-Forum Düsseldorf": HAUS,
    "FFT Düsseldorf": HAUS,
    "Stahlwerk Düsseldorf": HAUS,
    "Rudas Studios Düsseldorf": HAUS,
    "Mitsubishi Electric HALLE": HAUS,
    "Kulturschlachthof R25": HAUS,
    "Salon des Amateurs": HAUS,
    "Pitcher Rock HQ": HAUS,
    "Kunsthalle Düsseldorf": HAUS,
    "Filmmuseum Düsseldorf": HAUS,
    "Stadtbüchereien Düsseldorf": HAUS,
    "Tanzhaus NRW": HAUS,
    "Jazz-Schmiede Düsseldorf": HAUS,
    "Capitol Theater Düsseldorf": HAUS,
    "Kom(m)ödchen Düsseldorf": HAUS,
    "STARTPLATZ Düsseldorf": HAUS,
    # Tier 3: Nischen- und Spezialquellen der Veranstalter
    "Parkrun Volksgarten Düsseldorf": HAUS,
    "Sport im Park Düsseldorf": HAUS,
    "Fortuna Düsseldorf": HAUS,
    "DEG Eishockey Düsseldorf": HAUS,
    "Messe Düsseldorf": HAUS,
    "EKŌ-Haus der Japanischen Kultur": HAUS,
    "Classic Remise Düsseldorf": HAUS,
    "Stadtstrand Düsseldorf": HAUS,
    "IHK Düsseldorf": HAUS,
    "StartupDorf Meetup": HAUS,
    "Street Food Thursday": HAUS,
    "Kasematten Düsseldorf": HAUS,
    "Auf ins Viertel": HAUS,
    "Kleine Weihnachtsmärkte": HAUS,
}

# Gespeicherte quelle_name → Rang: alle Anzeigenamen plus abweichende QUELLE_NAME-Konstanten, Einträge der Website
# und Namen deaktivierter Scraper (für alte Zeilen). Ein Test prüft, dass jede QUELLE_NAME-Konstante der Module in
# QUELLEN hier mit demselben Rang wie ihr Anzeigename steht.
RANG_GESPEICHERT: dict[str, int] = {
    **RANG_ANZEIGE,
    "Classic Remise": HAUS,                          # scraper/tier3/classic_remise.py
    "Street Food Thursday Düsseldorf": HAUS,         # scraper/tier3/street_food_thursday.py
    "Kleine Weihnachtsmärkte (Redaktion)": HAUS,     # scraper/tier3/kleine_weihnachtsmaerkte.py (ohne CSV-Name)
    "Event-Meldung": HAUS,                           # web/app/api/admin/meldungen/route.ts (Freigabe einer Meldung)
    # deaktivierte Scraper, nur noch alte Zeilen
    "Eventbrite": AGGREGATOR,
    "eventfinder.de": AGGREGATOR,
    "meinestadt.de": AGGREGATOR,
    "Bandsintown": AGGREGATOR,
    "Spontacts Düsseldorf": AGGREGATOR,
}

UNBEKANNT_GESPEICHERT = PORTAL


def ist_rausgegangen_quelle(quelle_name: Optional[str], quelle_url: Optional[str]) -> bool:
    """Rausgegangen am Namen oder an der URL (wie deduplication.ist_rausgegangen)."""
    return "rausgegangen" in (quelle_name or "").lower() or "rausgegangen.de" in (quelle_url or "").lower()


def rang_anzeige(anzeigename: str, tier: Optional[int] = None) -> int:
    """Rang einer Quelle im Lauf über ihren Anzeigenamen aus main.py QUELLEN."""
    if anzeigename in RANG_ANZEIGE:
        return RANG_ANZEIGE[anzeigename]
    if "rausgegangen" in anzeigename.lower():
        return RAUSGEGANGEN
    return HAUS if tier in (2, 3) else AGGREGATOR


def rang_gespeichert(quelle_name: Optional[str], quelle_url: Optional[str] = None) -> int:
    """Rang einer gespeicherten Zeile über quelle_name (unbekannt = 3), Rausgegangen auch an der URL."""
    if ist_rausgegangen_quelle(quelle_name, quelle_url):
        return RAUSGEGANGEN
    return RANG_GESPEICHERT.get((quelle_name or "").strip(), UNBEKANNT_GESPEICHERT)


def quellen_rang(event: dict) -> int:
    """
    Rang eines Events: im Lauf über `_scraper` (Anzeigename), sonst über die gespeicherte quelle_name.
    Rausgegangen per Name oder URL ist immer Rang 5.
    """
    if ist_rausgegangen_quelle(event.get("quelle_name"), event.get("quelle_url")):
        return RAUSGEGANGEN
    anzeige = event.get(SCRAPER_FELD)
    if anzeige:
        return rang_anzeige(str(anzeige), event.get(TIER_FELD))
    return rang_gespeichert(event.get("quelle_name"), event.get("quelle_url"))


def ist_sammelquelle(event: dict) -> bool:
    """True, wenn die Quelle Termine nur weitergibt (Rang ≥ 2) – dort ist die Uhrzeit oft der Einlass."""
    return quellen_rang(event) >= TICKETVERKAUF


# ── Alle Quellen eines Events (Plan Quellen-Ausbau 4.3, Schritt R2) ─────────────────────────────────────────────
# Spalte events.quellen: [{"name", "url", "rang", "zuletzt"}], höchstens ein Eintrag je Name. Im Lauf trägt jedes
# Event die Liste im internen Feld QUELLEN_FELD; die Deduplizierung vereinigt die Listen zusammengeführter Events.
QUELLEN_FELD = "_quellen"
# „zuletzt“ wird nur neu geschrieben, wenn der Eintrag älter ist – sonst gäbe jedes Duplikat in jedem Lauf ein Update
ZULETZT_AKTUALISIEREN_TAGE = 7


def quellen_eintrag(event: dict, zuletzt: str) -> dict:
    """Eintrag der eigenen Quelle eines Events (gespeicherter Name, Link, Rang, Zeitpunkt)."""
    return {"name": event.get("quelle_name"), "url": event.get("quelle_url"), "rang": quellen_rang(event), "zuletzt": zuletzt}


def quellen_vereinigen(bisher: Optional[list], neu: Optional[list]) -> tuple[list, bool]:
    """
    Vereinigt zwei Quellenlisten (je Name ein Eintrag) und sagt, ob sich gegenüber `bisher` etwas Wesentliches
    geändert hat: neuer Name, anderer Link oder Rang, oder `zuletzt` älter als ZULETZT_AKTUALISIEREN_TAGE.
    """
    from datetime import datetime, timedelta, timezone

    ergebnis = [dict(e) for e in (bisher or []) if isinstance(e, dict) and e.get("name")]
    nach_name = {e["name"]: e for e in ergebnis}
    geaendert = False
    for eintrag in neu or []:
        if not isinstance(eintrag, dict) or not eintrag.get("name"):
            continue
        alt = nach_name.get(eintrag["name"])
        if alt is None:
            kopie = dict(eintrag)
            ergebnis.append(kopie)
            nach_name[kopie["name"]] = kopie
            geaendert = True
            continue
        for feld in ("url", "rang"):
            if eintrag.get(feld) and eintrag.get(feld) != alt.get(feld):
                alt[feld] = eintrag[feld]
                geaendert = True
        if eintrag.get("zuletzt") and eintrag["zuletzt"] > (alt.get("zuletzt") or ""):
            try:
                alt_zeit = datetime.fromisoformat(str(alt.get("zuletzt")).replace("Z", "+00:00"))
                if alt_zeit.tzinfo is None:
                    alt_zeit = alt_zeit.replace(tzinfo=timezone.utc)
                veraltet = datetime.now(timezone.utc) - alt_zeit > timedelta(days=ZULETZT_AKTUALISIEREN_TAGE)
            except (TypeError, ValueError):
                veraltet = True
            alt["zuletzt"] = eintrag["zuletzt"]
            geaendert = geaendert or veraltet
    return ergebnis, geaendert


def quellen_der_zeile(zeile: dict) -> list:
    """Gespeicherte Quellenliste einer Zeile; ohne Liste (alte Zeile) die heutige Hauptquelle."""
    liste = zeile.get("quellen")
    if isinstance(liste, list) and liste:
        return liste
    if zeile.get("quelle_name"):
        return [{"name": zeile.get("quelle_name"), "url": zeile.get("quelle_url"),
                 "rang": rang_gespeichert(zeile.get("quelle_name"), zeile.get("quelle_url")), "zuletzt": None}]
    return []


def nur_rausgegangen(liste: list) -> bool:
    """True, wenn alle Quellen der Liste Rausgegangen sind (Rang 5) – und es mindestens eine gibt."""
    raenge = [e.get("rang") for e in liste if isinstance(e, dict)]
    return bool(raenge) and all(r == RAUSGEGANGEN for r in raenge)
