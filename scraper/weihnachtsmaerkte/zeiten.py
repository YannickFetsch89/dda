"""
zeiten.py – DiesDasDüsseldorf
Öffnungszeiten der Weihnachtsmärkte als reine, getestete Funktionen (Plan docs/plan-weihnachtsmaerkte-2026-11-17.md,
Abschnitte 3.2 und 4.3). Kein Netz, keine Datenbank.

Kurzschrift in data/weihnachtsmaerkte/saison-2026.csv:
  zeiten:  "Mo-Do 11:00-20:00; Fr-Sa 11:00-21:00; So 11:00-20:00"   (Tagesbereiche oder Einzeltage, kommagetrennt erlaubt)
  sonder:  "2026-11-22 zu; 2026-12-24 11:00-15:00"
Gespeichert wird strukturiert: zeiten = [{tage: ["mo",…], von, bis}], sonder = [{datum, geschlossen: true} | {datum, von, bis}].
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import date, timedelta

TAGE = ["mo", "di", "mi", "do", "fr", "sa", "so"]
TAG_NAMEN = {"mo": "Mo", "di": "Di", "mi": "Mi", "do": "Do", "fr": "Fr", "sa": "Sa", "so": "So"}

_ZEIT = r"([01]\d|2[0-3]):([0-5]\d)"
_SPANNE = re.compile(rf"^{_ZEIT}-{_ZEIT}$")
_DATUM = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ZeitFehler(ValueError):
    """Nicht lesbare oder unzulässige Zeitangabe – die Saison wird dann nicht geschrieben."""


def _spanne(text: str) -> tuple[str, str]:
    m = _SPANNE.match(text.strip())
    if not m:
        raise ZeitFehler(f"Zeitspanne nicht lesbar: „{text}“ (erwartet HH:MM-HH:MM)")
    von, bis = f"{m.group(1)}:{m.group(2)}", f"{m.group(3)}:{m.group(4)}"
    if bis <= von:
        # Weihnachtsmärkte schließen nicht nach Mitternacht – eine solche Angabe ist ein Tippfehler
        raise ZeitFehler(f"Ende nicht nach Beginn bzw. über Mitternacht: „{text}“")
    return von, bis


def _tage(text: str) -> list[str]:
    tage: list[str] = []
    for teil in text.split(","):
        teil = teil.strip().lower()
        if "-" in teil:
            a, b = (x.strip() for x in teil.split("-", 1))
            if a not in TAGE or b not in TAGE or TAGE.index(a) > TAGE.index(b):
                raise ZeitFehler(f"Tagesbereich nicht lesbar: „{teil}“")
            tage += TAGE[TAGE.index(a): TAGE.index(b) + 1]
        elif teil in TAGE:
            tage.append(teil)
        else:
            raise ZeitFehler(f"Wochentag nicht lesbar: „{teil}“")
    return tage


def zeiten_lesen(text: str) -> list[dict]:
    """Kurzschrift → [{tage, von, bis}]. Leer → []. Jeder Wochentag höchstens einmal."""
    text = (text or "").strip()
    if not text:
        return []
    ergebnis: list[dict] = []
    gesehen: set[str] = set()
    for block in text.split(";"):
        block = block.strip()
        if not block:
            continue
        teile = block.rsplit(" ", 1)
        if len(teile) != 2:
            raise ZeitFehler(f"Block nicht lesbar: „{block}“ (erwartet „Mo-Do 11:00-20:00“)")
        tage = _tage(teile[0])
        doppelt = gesehen.intersection(tage)
        if doppelt:
            raise ZeitFehler(f"Wochentag doppelt: {', '.join(sorted(doppelt))}")
        gesehen.update(tage)
        von, bis = _spanne(teile[1])
        ergebnis.append({"tage": tage, "von": von, "bis": bis})
    return ergebnis


def sonder_lesen(text: str, von: str | None = None, bis: str | None = None) -> list[dict]:
    """Kurzschrift → [{datum, geschlossen: True} | {datum, von, bis}]. Datum muss im Zeitraum liegen (falls angegeben)."""
    text = (text or "").strip()
    if not text:
        return []
    ergebnis: list[dict] = []
    gesehen: set[str] = set()
    for block in text.split(";"):
        block = block.strip()
        if not block:
            continue
        teile = block.split(None, 1)
        if len(teile) != 2 or not _DATUM.match(teile[0]):
            raise ZeitFehler(f"Sonderzeit nicht lesbar: „{block}“ (erwartet „2026-12-24 11:00-15:00“ oder „2026-11-22 zu“)")
        datum = teile[0]
        try:
            date.fromisoformat(datum)
        except ValueError as fehler:
            raise ZeitFehler(f"Kein gültiges Datum: {datum}") from fehler
        if von and datum < von or bis and datum > bis:
            raise ZeitFehler(f"Sonderdatum {datum} liegt außerhalb des Zeitraums {von} bis {bis}")
        if datum in gesehen:
            raise ZeitFehler(f"Sonderdatum doppelt: {datum}")
        gesehen.add(datum)
        if teile[1].strip().lower() == "zu":
            ergebnis.append({"datum": datum, "geschlossen": True})
        else:
            v, b = _spanne(teile[1])
            ergebnis.append({"datum": datum, "von": v, "bis": b})
    return sorted(ergebnis, key=lambda s: s["datum"])


def zeitraum_pruefen(von: str, bis: str) -> None:
    for d in (von, bis):
        if not d or not _DATUM.match(d):
            raise ZeitFehler(f"Datum fehlt oder ist nicht lesbar: „{d}“")
        date.fromisoformat(d)
    if von > bis:
        raise ZeitFehler(f"Zeitraum verkehrt: {von} nach {bis}")


def kurzschrift(zeiten: list[dict]) -> str:
    """[{tage, von, bis}] → „Mo-Do 11:00-20:00; Fr-Sa 11:00-21:00“ (zusammenhängende Tage als Bereich)."""
    bloecke = []
    for z in sorted(zeiten, key=lambda z: TAGE.index(z["tage"][0])):
        indizes = sorted(TAGE.index(t) for t in z["tage"])
        gruppen: list[list[int]] = []
        for i in indizes:
            if gruppen and i == gruppen[-1][-1] + 1:
                gruppen[-1].append(i)
            else:
                gruppen.append([i])
        tage_text = ",".join(
            TAG_NAMEN[TAGE[g[0]]] if len(g) == 1 else f"{TAG_NAMEN[TAGE[g[0]]]}-{TAG_NAMEN[TAGE[g[-1]]]}" for g in gruppen
        )
        bloecke.append(f"{tage_text} {z['von']}-{z['bis']}")
    return "; ".join(bloecke)


def sonder_kurzschrift(sonder: list[dict]) -> str:
    return "; ".join(
        f"{s['datum']} zu" if s.get("geschlossen") else f"{s['datum']} {s['von']}-{s['bis']}" for s in sonder
    )


# ---------------------------------------------------------------------------
# Ableitung aus Toubiz-Terminen (Entwurf, nie ungeprüft übernommen)
# ---------------------------------------------------------------------------

def _wochentag(datum: str) -> str:
    return TAGE[date.fromisoformat(datum).weekday()]


def aus_terminen(termine: list[dict]) -> dict:
    """
    termine = [{datum, von, bis}] offene Tage und [{datum, geschlossen: True}] ausdrücklich geschlossene Tage. Ergebnis:
      von/bis (erster/letzter offener Termin), zeiten (je Wochentag die häufigste Zeit, gleiche Zeiten zusammengefasst),
      sonder (Termine mit abweichender Zeit und ausdrücklich geschlossene Tage als „zu“),
      luecken (Tage im Zeitraum, deren Wochentag eine Zeit hat, aber ohne jeden Termin).
    Lücken werden NIE als „zu“ geschrieben (Plan E4) – sie sind nur ein Prüf-Hinweis. „closed“ dagegen ist ein Beleg.
    """
    geschlossen = sorted({t["datum"] for t in termine if t.get("datum") and t.get("geschlossen")})
    termine = sorted((t for t in termine if t.get("datum") and t.get("von") and t.get("bis") and not t.get("geschlossen")),
                     key=lambda t: t["datum"])
    if not termine:
        return {"von": None, "bis": None, "zeiten": [], "sonder": [], "luecken": []}
    je_tag: dict[str, Counter] = {t: Counter() for t in TAGE}
    for t in termine:
        je_tag[_wochentag(t["datum"])][(t["von"], t["bis"])] += 1
    woche: dict[str, tuple[str, str]] = {}
    for tag, zaehler in je_tag.items():
        if zaehler:
            # häufigste Zeit; bei Gleichstand die frühere Öffnung/spätere Schließung nicht bevorzugen → stabile Sortierung
            woche[tag] = sorted(zaehler.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    # gleiche Zeiten zusammenfassen
    nach_zeit: dict[tuple[str, str], list[str]] = {}
    for tag in TAGE:
        if tag in woche:
            nach_zeit.setdefault(woche[tag], []).append(tag)
    zeiten = [{"tage": tage, "von": v, "bis": b} for (v, b), tage in nach_zeit.items()]
    sonder = [
        {"datum": t["datum"], "von": t["von"], "bis": t["bis"]}
        for t in termine if woche.get(_wochentag(t["datum"])) != (t["von"], t["bis"])
    ]
    von, bis = termine[0]["datum"], termine[-1]["datum"]
    # Geschlossene Tage im Zeitraum als Sonderzeile „zu“ (außerhalb des Zeitraums ohne Bedeutung)
    sonder = sorted(sonder + [{"datum": d, "geschlossen": True} for d in geschlossen if von <= d <= bis],
                    key=lambda s: s["datum"])
    vorhanden = {t["datum"] for t in termine} | set(geschlossen)
    luecken = []
    tag = date.fromisoformat(von)
    while tag <= date.fromisoformat(bis):
        iso = tag.isoformat()
        if iso not in vorhanden and TAGE[tag.weekday()] in woche:
            luecken.append(iso)
        tag += timedelta(days=1)
    return {"von": von, "bis": bis, "zeiten": zeiten, "sonder": sonder, "luecken": luecken}


# ---------------------------------------------------------------------------
# Feiertage und Öffnung an einem Tag (gleiche Regeln wie web/lib/weihnachtsmaerkte.ts, gemeinsame Fixture)
# ---------------------------------------------------------------------------

def totensonntag(jahr: int) -> date:
    """Sonntag vor dem 1. Advent = fünfter Sonntag vor dem 25.12. (2026: 22.11., 2027: 21.11.)."""
    weihnachten = date(jahr, 12, 25)
    # 4. Advent = letzter Sonntag vor dem 25.12. (fällt der 25.12. auf einen Sonntag, ist der 4. Advent der 18.12.)
    vierter = weihnachten - timedelta(days=(weihnachten.weekday() + 1) % 7 or 7)
    return vierter - timedelta(weeks=4)


def feiertag(datum: str) -> str | None:
    d = date.fromisoformat(datum)
    if d == totensonntag(d.year):
        return "Totensonntag"
    return {
        (12, 24): "Heiligabend", (12, 25): "1. Weihnachtstag", (12, 26): "2. Weihnachtstag",
        (12, 31): "Silvester", (1, 1): "Neujahr",
    }.get((d.month, d.day))


def saison_fuer(saisons: dict, datum: str) -> tuple[str | None, str]:
    """
    (Schlüssel, Lage) der Saison für ein Datum (Plan 4.3 Schritt 1): Lage "in" (von ≤ datum ≤ bis), "vor" oder "nach".
    Nur Saisons mit Zeitraum zählen. Liegt das Datum in keiner: vor dem frühesten von → "vor" gegen diese Saison,
    sonst "nach" gegen die Saison mit dem spätesten bis davor.
    """
    mit_zeitraum = [(k, s) for k, s in (saisons or {}).items() if s.get("von") and s.get("bis")]
    if not mit_zeitraum:
        return None, "unbekannt"
    for k, s in mit_zeitraum:
        if s["von"] <= datum <= s["bis"]:
            return k, "in"
    frueheste = min(mit_zeitraum, key=lambda ks: ks[1]["von"])
    if datum < frueheste[1]["von"]:
        return frueheste[0], "vor"
    davor = [ks for ks in mit_zeitraum if ks[1]["bis"] < datum]
    letzte = max(davor or mit_zeitraum, key=lambda ks: ks[1]["bis"])
    # Liegt das Datum zwischen zwei Saisons, gilt die nächste als „vor“
    spaeter = [ks for ks in mit_zeitraum if ks[1]["von"] > datum]
    if davor and spaeter:
        naechste = min(spaeter, key=lambda ks: ks[1]["von"])
        return naechste[0], "vor"
    return letzte[0], "nach"


def oeffnung_am(saisons: dict, datum: str) -> dict:
    """Zustand an einem Tag: vor_saison | nach_saison | zu | offen | unbekannt (Plan 4.3)."""
    schluessel, lage = saison_fuer(saisons, datum)
    if schluessel is None:
        return {"zustand": "unbekannt"}
    s = saisons[schluessel]
    if lage == "vor":
        return {"zustand": "vor_saison", "ab": s["von"]}
    if lage == "nach":
        return {"zustand": "nach_saison", "bis": s["bis"]}
    if not s.get("zeiten"):
        return {"zustand": "unbekannt"}
    grund = feiertag(datum)
    for so in s.get("sonder") or []:
        if so["datum"] == datum:
            if so.get("geschlossen"):
                return {"zustand": "zu", "grund": grund}
            return {"zustand": "offen", "von": so["von"], "bis": so["bis"], "grund": grund}
    if grund:
        return {"zustand": "unbekannt", "grund": grund}
    tag = _wochentag(datum)
    for z in s["zeiten"]:
        if tag in z["tage"]:
            return {"zustand": "offen", "von": z["von"], "bis": z["bis"]}
    return {"zustand": "zu"}
