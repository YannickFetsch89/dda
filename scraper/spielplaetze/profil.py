"""
profil.py – DiesDasDüsseldorf
Profile für den Guide „Spielplätze“ (Plan: docs/plan-spielplaetze-2026-11-12.md, Abschnitt 4.3) – wie das Club-Profil.

Je Platz: Websuche (Claude Haiku mit Websuche) nach öffentlichen Seiten über diesen Spielplatz, Abruf nur robots.txt-konform
mit ≥ 2 s Abstand (pipeline.beschreibung_quellen.seite_laden; nie Rausgegangen, Social Media; duesseldorf.de sperrt Bots).
Claude Sonnet ordnet ein (festes JSON-Schema). Jede Angabe braucht ein WÖRTLICHES Zitat; der Code prüft es gegen die
Quelltexte und verlangt ein passendes Stichwort (Rutsche → „rutsch“). Ohne Beleg wird die Angabe verworfen.

Geschrieben wird nur extras.spielplatz: Ausstattung/Extras mit quelle "zitat" (nie über "sichtung"; gegen "osm" gewinnt
die jüngere Quelle), Alter (belegt), Saison, Beschreibung, Highlight, profil_stand, profil. Nie aktiv, Name, Slug, Foto.

Nutzung:
  python -m scraper.spielplaetze.profil --probe --dry-run   # 10 gemischte Plätze, nichts schreiben
  python -m scraper.spielplaetze.profil --probe             # Probe schreiben + Bericht
  python -m scraper.spielplaetze.profil --runde 1|2 [--max N] [--neu]
"""
import argparse
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scraper.spielplaetze.ausstattung_import import EXTRAS, GERAETE, NEBENGERAETE  # noqa: E402

logger = logging.getLogger(__name__)

_DATEN = Path(__file__).resolve().parents[2] / "data" / "spielplaetze"
ORDNER = _DATEN / "profile"          # Rohantworten je Platz (lokal, gitignored)
BERICHT = _DATEN / "profil_bericht.md"

MODELL = "claude-sonnet-5-5"
MODELL_SUCHE = "claude-haiku-5-5"
MAX_QUELLE = 6000
MAX_SUCHSEITEN = 4
GROESSE_RUNDE_1, GROESSE_RUNDE_2 = 3000.0, 1500.0
ALTER = ["0-3", "3-6", "6-12", "alle"]

# Ein Merkmal zählt nur, wenn das Zitat ein passendes Wort enthält (sonst belegt „schöner Spielplatz“ alles)
STICHWORTE = {
    "sandkasten": r"sand", "schaukel": r"schaukel", "rutsche": r"rutsch", "klettern": r"kletter|klimm",
    "wasserspiel": r"wasser|pumpe|matsch|plansch|fontäne|fontaene|sprudel", "seilbahn": r"seilbahn",
    "tischtennis": r"tischtennis|tt-platte", "fussball": r"fu(ß|ss)ball|bolzplatz|\btore?\b|kicken",
    "basketball": r"basketball|streetball|basketballkorb|\bkorb", "federwippe": r"feder|wipptier|wippgerät",
    "wippe": r"wippe", "karussell": r"karussell|drehscheibe|drehteller|dreh", "balancierbalken": r"balancier",
    # Skaten nur als Anlage – nicht „Skateboards zum Ausleihen“
    "volleyball": r"volleyball", "skaten": r"skatepark|skateanlage|skate-?bahn|halfpipe|pumptrack|\brampe",
    "schatten": r"schatt|bäume|baeume|baum", "wc": r"\bwc\b|toilette", "eingezaeunt": r"zaun|eingezäunt|umzäunt|eingezaeunt",
    "picknick": r"picknick|grill|sitzgruppe|tische?\b", "rollstuhl": r"rollstuhl|barrierefrei|inklusiv|rolli",
}
VERNEINUNG = r"\bkein|\bnicht\b|\bohne\b|abgebaut|entfernt|gesperrt|fehlt"
ALTER_STICHWORTE = r"\d|kleinkind|schulkind|krabbel|baby|jugendlich|jahre|kinder unter|ab \w+ jahren|altersgruppe|altergruppe|alle alter"
# Keine Wertungen und keine Kritik in der Beschreibung (Plan §10: Abmahnrisiko durch Wertungen)
WERTUNG = r"\bquellen?\b|verrät|keine angaben|geheimtipp|\bsterne?\b|bewertung|\d,\d ?/ ?5|bemängel|bemaengel|kritisier|kommentar|schmutzig|dreckig|verwahrlost|ungepflegt|sauberkeit"
SAISON_STICHWORTE = r"mai|juni|juli|august|september|oktober|april|sommer|saison|winter|abgestellt|in betrieb|geöffnet|geoeffnet"

SYSTEM = """Du erstellst Profile öffentlicher Spielplätze für den Düsseldorfer Stadtguide dies.das.düsseldorf.
Du bekommst einen Spielplatz (Name, Stadtteil, Typ, Größe laut Stadt) und Quelltexte aus einer Websuche.

Grundregeln:
- Stütze dich NUR auf die Quellen. Erfinde nichts, schließe nichts aus dem Namen oder dem Typ.
- Prüfe zuerst, ob eine Quelle wirklich DIESEN Spielplatz beschreibt (Ort, Park, Straße passen). Eine Quelle über einen
  anderen Spielplatz derselben Stadt ignorierst du vollständig. „passt“: true nur, wenn mindestens eine Quelle diesen
  Platz beschreibt; „passt_grund“ kurz.
- Jede Angabe braucht ein WÖRTLICHES Zitat (5–30 Wörter, exakt wie in der Quelle, nicht umformuliert, nicht aus
  mehreren Stellen zusammengesetzt) und die Nummer der Quelle. Das Zitat muss das Gerät/Merkmal selbst nennen.
- „geraete“: Spielgeräte und Sportflächen, die die Quelle für diesen Platz nennt. wert „ja“; „nein“ nur, wenn die Quelle
  ausdrücklich sagt, dass es fehlt, abgebaut oder gesperrt ist.
- „extras“: Schatten, WC, eingezäunt, Picknick, Rollstuhl (ja/nein/teilweise), mit kurzer Notiz.
- „alter“: nur wenn die Quelle eine Altersgruppe nennt (Kleinkinder 0-3, 3-6, Schulkinder 6-12, alle Altersgruppen).
- „saison“: nur bei Wasserspiel – wann das Wasser läuft, wörtlich belegt.
- „beschreibung“: 2–4 eigene Sätze auf Deutsch, Anrede ihr/euch, locker, keine Werbesprache, keine Sterne/Bewertungen,
  keine Öffnungszeiten, keine Adresse, keine Parkplatz-Hinweise. Keine Wertungen und keine Kritik, auch nicht aus
  Kommentaren oder Bewertungen (kein „bemängelt“, „ungepflegt“, „schmutzig“). Nur, was die Quellen über diesen Platz sagen.
- Die Beschreibung spricht über den Platz, nie über die Quellen („laut Quelle“, „die Quelle verrät nichts“ gehören nicht hinein).
- Ausleihbares Spielzeug (Bälle, Skateboards, Fahrzeuge) ist kein Gerät; Skaten nur bei einer Skate-Anlage. Keine Schablone aus Name, Stadtteil
  und Größe – gibt es nichts Inhaltliches, bleibt sie leer.
- „highlight“: ein Satz (max. 100 Zeichen), was den Platz ausmacht, sonst leer.
- „quellen_datum“: je benutzter Quelle das Datum, das in der Quelle steht (YYYY-MM-DD oder YYYY-MM), sonst leer."""

SCHEMA = {
    "type": "object",
    "properties": {
        "passt": {"type": "boolean"},
        "passt_grund": {"type": "string"},
        "geraete": {"type": "array", "items": {"type": "object", "properties": {
            "geraet": {"type": "string", "enum": list(GERAETE) + list(NEBENGERAETE)},
            "wert": {"type": "string", "enum": ["ja", "nein"]},
            "zitat": {"type": "string"}, "quelle": {"type": "integer"}},
            "required": ["geraet", "wert", "zitat", "quelle"], "additionalProperties": False}},
        "extras": {"type": "array", "items": {"type": "object", "properties": {
            "merkmal": {"type": "string", "enum": list(EXTRAS)},
            "wert": {"type": "string", "enum": ["ja", "nein", "teilweise"]},
            "notiz": {"type": "string"}, "zitat": {"type": "string"}, "quelle": {"type": "integer"}},
            "required": ["merkmal", "wert", "notiz", "zitat", "quelle"], "additionalProperties": False}},
        "alter": {"type": "object", "properties": {
            "wert": {"type": "string", "enum": [""] + ALTER}, "zitat": {"type": "string"}, "quelle": {"type": "integer"}},
            "required": ["wert", "zitat", "quelle"], "additionalProperties": False},
        "saison": {"type": "object", "properties": {
            "text": {"type": "string"}, "zitat": {"type": "string"}, "quelle": {"type": "integer"}},
            "required": ["text", "zitat", "quelle"], "additionalProperties": False},
        "beschreibung": {"type": "string"},
        "highlight": {"type": "string"},
        "quellen_datum": {"type": "array", "items": {"type": "object", "properties": {
            "quelle": {"type": "integer"}, "datum": {"type": "string"}},
            "required": ["quelle", "datum"], "additionalProperties": False}},
    },
    "required": ["passt", "passt_grund", "geraete", "extras", "alter", "saison", "beschreibung", "highlight", "quellen_datum"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# Reine Funktionen
# ---------------------------------------------------------------------------

def runde(zeile: dict) -> int | None:
    """Runde 1 (4.3): Wasser, Wald, Abenteuer, Kinder ≥ 3.000 m²; Runde 2: Kinder 1.500 bis < 3.000 m². Ausgeschlossene nie."""
    sp = (zeile.get("extras") or {}).get("spielplatz") or {}
    if sp.get("ausgeschlossen"):
        return None
    if sp.get("typ") in ("wasser", "wald", "abenteuer"):
        return 1
    g = sp.get("groesse_m2") or 0
    return 1 if g >= GROESSE_RUNDE_1 else 2 if g >= GROESSE_RUNDE_2 else None


def probe_auswahl(zeilen: list[dict]) -> list[dict]:
    """10 gemischte Runde-1-Plätze: 3 Wasser, 2 Wald, 2 Abenteuer, 3 große Kinderspielplätze (fest, nach Name bzw. Größe)."""
    r1 = [z for z in zeilen if runde(z) == 1]
    typ = lambda z: z["extras"]["spielplatz"]["typ"]  # noqa: E731
    nach_name = sorted(r1, key=lambda z: z["name"])
    kinder = sorted([z for z in r1 if typ(z) == "kinder"], key=lambda z: -(z["extras"]["spielplatz"].get("groesse_m2") or 0))
    return ([z for z in nach_name if typ(z) == "wasser"][:3] + [z for z in nach_name if typ(z) == "wald"][:2]
            + [z for z in nach_name if typ(z) == "abenteuer"][:2] + kinder[:3])


def _norm(text: str) -> str:
    from scraper.orte.bars_einordnen import _norm as n

    return n(text or "")


def zitat_belegt(zitat: str, quellen: list[tuple[str, str]], nr: int) -> bool:
    """Steht das Zitat wörtlich in der genannten Quelle (oder, falls die Nummer falsch ist, in irgendeiner)?"""
    from scraper.orte.bars_einordnen import belegt

    if 1 <= nr <= len(quellen) and belegt(zitat, quellen[nr - 1][1]):
        return True
    return any(belegt(zitat, text) for _, text in quellen)


def pruefen(ki: dict, quellen: list[tuple[str, str]]) -> tuple[dict, list[str]]:
    """Prüft jede Angabe (Zitat wörtlich, passendes Stichwort, „nein“ nur mit Verneinung). Rückgabe (Profil, Verworfenes)."""
    verworfen = []
    profil = {"ausstattung": {}, "extras": {}, "alter": None, "saison": None, "beschreibung": None, "highlight": None}
    if not ki.get("passt") or not quellen:
        return profil, [f"keine passende Quelle: {ki.get('passt_grund', '')}"]

    def gueltig(art: str, schluessel: str, zitat: str, nr: int, wert: str, stichwort: str) -> bool:
        z = (zitat or "").lower()
        if not zitat_belegt(zitat, quellen, nr):
            verworfen.append(f"{art} {schluessel}: Zitat nicht wörtlich in den Quellen – „{zitat}“")
            return False
        if not re.search(stichwort, z):
            verworfen.append(f"{art} {schluessel}: Zitat nennt es nicht – „{zitat}“")
            return False
        if wert == "nein" and not re.search(VERNEINUNG, z):
            verworfen.append(f"{art} {schluessel}: „nein“ ohne Verneinung im Zitat – „{zitat}“")
            return False
        return True

    for g in ki.get("geraete") or []:
        if gueltig("Gerät", g["geraet"], g["zitat"], g["quelle"], g["wert"], STICHWORTE[g["geraet"]]):
            profil["ausstattung"][g["geraet"]] = {"wert": g["wert"], "quelle": "zitat", "beleg": g["zitat"],
                                                   "url": quellen[min(max(g["quelle"], 1), len(quellen)) - 1][0]}
    for x in ki.get("extras") or []:
        if gueltig("Extra", x["merkmal"], x["zitat"], x["quelle"], x["wert"], STICHWORTE[x["merkmal"]]):
            profil["extras"][x["merkmal"]] = {"wert": x["wert"], "notiz": x.get("notiz") or None, "quelle": "zitat",
                                              "beleg": x["zitat"]}
    a = ki.get("alter") or {}
    if a.get("wert"):
        if zitat_belegt(a["zitat"], quellen, a["quelle"]) and re.search(ALTER_STICHWORTE, a["zitat"].lower()):
            profil["alter"] = {"wert": a["wert"], "art": "belegt", "beleg": a["zitat"]}
        else:
            verworfen.append(f"Alter {a['wert']}: nicht belegt – „{a.get('zitat')}“")
    s = ki.get("saison") or {}
    if s.get("text"):
        if zitat_belegt(s["zitat"], quellen, s["quelle"]) and re.search(SAISON_STICHWORTE, s["zitat"].lower()):
            profil["saison"] = {"text": s["text"], "beleg": s["zitat"],
                                "url": quellen[min(max(s["quelle"], 1), len(quellen)) - 1][0]}
        else:
            verworfen.append(f"Saison: nicht belegt – „{s.get('zitat')}“")
    beschreibung = (ki.get("beschreibung") or "").strip()
    if beschreibung:
        if re.search(WERTUNG, beschreibung.lower()):
            verworfen.append("Beschreibung: enthält Bewertung oder Werbesprache")
        elif not 120 <= len(beschreibung) <= 900:
            verworfen.append(f"Beschreibung: Länge {len(beschreibung)} Zeichen (120–900 erlaubt)")
        else:
            profil["beschreibung"] = beschreibung
    if (ki.get("highlight") or "").strip() and profil["beschreibung"]:
        profil["highlight"] = ki["highlight"].strip()[:120]
    return profil, verworfen


def profil_stand(ki: dict) -> str | None:
    """Datum der jüngsten Quelle (YYYY-MM-DD oder YYYY-MM), sonst None."""
    daten = [d["datum"] for d in ki.get("quellen_datum") or [] if re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", d.get("datum") or "")]
    return max(daten) if daten else None


def zusammenfuehren(alt: dict, neu: dict, stand: str | None, osm_stand: str | None) -> tuple[dict, list[str]]:
    """
    Ausstattung/Extras: Zitat-Einträge des letzten Profils werden ersetzt; „sichtung“ bleibt immer.
    Gegen „osm“: gleicher Wert → OSM bleibt; anderer Wert → die jüngere Quelle gewinnt, unbekanntes Datum → OSM bleibt.
    Rückgabe (neues Feld, Konflikte für den Bericht).
    """
    ergebnis = {k: v for k, v in (alt or {}).items() if (v or {}).get("quelle") != "zitat"}
    konflikte = []
    for merkmal, eintrag in neu.items():
        vorhanden = ergebnis.get(merkmal)
        if not vorhanden:
            ergebnis[merkmal] = eintrag
        elif vorhanden.get("quelle") == "sichtung":
            if vorhanden.get("wert") != eintrag["wert"]:
                konflikte.append(f"{merkmal}: Sichtung={vorhanden.get('wert')}, Zitat={eintrag['wert']} – Sichtung bleibt")
        elif vorhanden.get("quelle") == "osm" and vorhanden.get("wert") != eintrag["wert"]:
            juenger = bool(stand and osm_stand and stand > osm_stand[:len(stand)])
            konflikte.append(f"{merkmal}: OSM={vorhanden.get('wert')}, Zitat={eintrag['wert']} – "
                             + ("Zitat ist jünger, gewinnt" if juenger else "OSM bleibt (Zitat nicht nachweislich jünger)"))
            if juenger:
                ergebnis[merkmal] = eintrag
    return ergebnis, konflikte


# ---------------------------------------------------------------------------
# Quellen und KI
# ---------------------------------------------------------------------------

def such_urls(client, zeile: dict) -> tuple[list[str], int]:
    sp = zeile["extras"]["spielplatz"]
    anfrage = (f"Finde Seiten über den öffentlichen Spielplatz „{zeile['name']}“ in Düsseldorf-{zeile.get('stadtteil') or ''}"
               f" ({ {'wasser': 'Wasserspielplatz', 'wald': 'Waldspielplatz', 'abenteuer': 'betreuter Abenteuerspielplatz'}.get(sp['typ'], 'Spielplatz') }):"
               " Spielgeräte, Ausstattung, Altersgruppe, Umbau oder Neueröffnung. Gut sind Presseartikel, Stadtteil- und"
               " Familienportale, Seiten des Trägers. Höchstens drei Suchen.")
    antwort = client.messages.create(
        model=MODELL_SUCHE, max_tokens=1024, messages=[{"role": "user", "content": anfrage}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3,
                "blocked_domains": ["rausgegangen.de", "instagram.com", "facebook.com", "tiktok.com", "youtube.com"],
                "user_location": {"type": "approximate", "city": "Düsseldorf", "country": "DE", "timezone": "Europe/Berlin"}}],
    )
    urls = []
    for block in antwort.content:
        if getattr(block, "type", "") == "web_search_tool_result" and isinstance(block.content, list):
            for r in block.content:
                url = getattr(r, "url", None)
                if url and url not in urls:
                    urls.append(url)
    suchen = getattr(getattr(antwort.usage, "server_tool_use", None), "web_search_requests", 0) or 0
    return urls, suchen


def quellen_sammeln(client, zeile: dict) -> tuple[list[tuple[str, str]], int]:
    """Seiten, die den Platz wirklich nennen (unterscheidendes Wort aus dem Namen oder der Adresse im Text)."""
    from pipeline.beschreibung_quellen import seite_laden, seiten_text
    from scraper.spielplaetze.google_abgleich import woerter

    sp = zeile["extras"]["spielplatz"]
    kennwoerter = woerter(zeile["name"]) | woerter((zeile.get("adresse") or "").split(",")[0])
    urls, suchen = such_urls(client, zeile)
    if sp.get("quelle_url"):
        urls.insert(0, sp["quelle_url"])
    quellen = []
    for url in urls:
        html = seite_laden(url)
        if not html:
            continue
        text = seiten_text(html)
        norm = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
        if not kennwoerter or any(w in norm for w in kennwoerter):
            quellen.append((url, text[:MAX_QUELLE]))
        if len(quellen) >= MAX_SUCHSEITEN:
            break
    return quellen, suchen


def ki_anfrage(client, zeile: dict, quellen: list[tuple[str, str]]) -> tuple[dict, dict]:
    sp = zeile["extras"]["spielplatz"]
    teile = [f"Name: {zeile['name']}\nStadtteil: {zeile.get('stadtteil')}\nTyp: {sp['typ']}\n"
             f"Größe laut Stadt: {sp.get('groesse_m2')} m²\nAdresse: {zeile.get('adresse') or 'unbekannt'}"]
    teile += [f"=== Quelle {i}: {url} ===\n{text}" for i, (url, text) in enumerate(quellen, 1)]
    antwort = client.messages.create(
        model=MODELL, max_tokens=4000, system=SYSTEM,
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": "\n\n".join(teile)}],
    )
    if antwort.stop_reason == "refusal":
        raise RuntimeError("Anfrage abgelehnt (refusal)")
    if antwort.stop_reason == "max_tokens":
        raise RuntimeError("Antwort abgeschnitten (max_tokens)")
    nutzung = {"ein": antwort.usage.input_tokens, "aus": antwort.usage.output_tokens}
    return json.loads(next(b.text for b in antwort.content if b.type == "text")), nutzung


# ---------------------------------------------------------------------------
# Lauf
# ---------------------------------------------------------------------------

def schreiben(db, zeile: dict, profil: dict, ki: dict, quellen: list[tuple[str, str]]) -> list[str]:
    """Nur Profilfelder in extras.spielplatz – extras direkt vorher frisch lesen."""
    aktuell = (db.table("orte").select("extras").eq("id", zeile["id"]).execute().data or [{}])[0].get("extras") or {}
    sp = dict(aktuell.get("spielplatz") or {})
    stand = profil_stand(ki)
    osm_stand = ((sp.get("osm") or {}).get("tags_stand") or "")[:10] or None
    sp["ausstattung"], k1 = zusammenfuehren(sp.get("ausstattung"), profil["ausstattung"], stand, osm_stand)
    sp["extras"], k2 = zusammenfuehren(sp.get("extras"), profil["extras"], stand, osm_stand)
    # Alter aus dem Profil ersetzt nur ein früheres Profil-Alter; ein Alter aus anderer Quelle bleibt
    if profil["alter"]:
        sp["alter"] = {**profil["alter"], "quelle": "zitat"}
    elif (sp.get("alter") or {}).get("quelle") == "zitat":
        sp["alter"] = None
    sp["saison"] = profil["saison"]
    sp["beschreibung"] = profil["beschreibung"]
    sp["highlight"] = profil["highlight"]
    sp["profil_stand"] = stand
    sp["profil"] = {"datum": date.today().isoformat(), "modell": MODELL, "quellen": [u for u, _ in quellen]}
    db.table("orte").update({"extras": {**aktuell, "spielplatz": sp}}).eq("id", zeile["id"]).execute()
    return k1 + k2


def lauf(auswahl: list[dict], dry_run: bool) -> None:
    import anthropic

    from database.client import get_supabase_client

    db = get_supabase_client() if not dry_run else None
    client = anthropic.Anthropic()
    ORDNER.mkdir(parents=True, exist_ok=True)
    bericht = [f"# Spielplatz-Profile – {date.today().isoformat()}{' (Dry-Run)' if dry_run else ''}", ""]
    summe = {"ein": 0, "aus": 0, "suchen": 0, "mit_beschreibung": 0}
    for i, z in enumerate(auswahl, 1):
        logger.info("[%d/%d] %s", i, len(auswahl), z["name"])
        try:
            quellen, suchen = quellen_sammeln(client, z)
            summe["suchen"] += suchen
            if quellen:
                ki, nutzung = ki_anfrage(client, z, quellen)
                summe["ein"] += nutzung["ein"]
                summe["aus"] += nutzung["aus"]
            else:
                ki = {"passt": False, "passt_grund": "keine abrufbare Quelle nennt den Platz"}
            profil, verworfen = pruefen(ki, quellen)
            (ORDNER / f"{z['id']}.json").write_text(json.dumps({"ki": ki, "quellen": [u for u, _ in quellen]},
                                                               ensure_ascii=False, indent=1), encoding="utf-8")
            konflikte = [] if dry_run else schreiben(db, z, profil, ki, quellen)
            summe["mit_beschreibung"] += bool(profil["beschreibung"])
            bericht += _bericht_abschnitt(z, quellen, profil, verworfen, konflikte, ki)
        except Exception as e:  # noqa: BLE001 – Platz überspringen, Lauf geht weiter
            logger.error("Profil für %s fehlgeschlagen: %s", z["name"], e)
            bericht += [f"## {z['name']}", "", f"Fehler: {e}", ""]
    bericht[1:1] = [f"{len(auswahl)} Plätze, {summe['mit_beschreibung']} mit Beschreibung. Verbrauch: {summe['suchen']} Websuchen, "
                    f"{summe['ein']} Eingabe- und {summe['aus']} Ausgabe-Token (Einordnung, ohne Suchmodell).", ""]
    BERICHT.write_text("\n".join(bericht) + "\n", encoding="utf-8")
    logger.info("Fertig: %s – Bericht %s", summe, BERICHT)


def _bericht_abschnitt(z, quellen, profil, verworfen, konflikte, ki) -> list[str]:
    sp = z["extras"]["spielplatz"]
    zeilen = [f"## {z['name']} ({z.get('stadtteil')}, {sp['typ']})", ""]
    zeilen += [f"- Quelle {i}: {u}" for i, (u, _) in enumerate(quellen, 1)] or ["- keine Quelle"]
    zeilen += ["", f"Passt: {ki.get('passt')} – {ki.get('passt_grund', '')}", ""]
    for feld in ("ausstattung", "extras"):
        for k, v in profil[feld].items():
            zeilen.append(f"- ✔ {k} = {v['wert']}: „{v['beleg']}“")
    if profil["alter"]:
        zeilen.append(f"- ✔ Alter {profil['alter']['wert']}: „{profil['alter']['beleg']}“")
    if profil["saison"]:
        zeilen.append(f"- ✔ Saison: {profil['saison']['text']} – „{profil['saison']['beleg']}“")
    zeilen += [f"- ✘ {v}" for v in verworfen] + [f"- ⚠ {k}" for k in konflikte]
    zeilen += ["", f"**Beschreibung:** {profil['beschreibung'] or '–'}", "", f"**Highlight:** {profil['highlight'] or '–'}", ""]
    return zeilen


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
    for laut in ("httpx", "anthropic"):
        logging.getLogger(laut).setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Spielplätze: Profile (KI + Websuche)")
    parser.add_argument("--probe", action="store_true", help="10 gemischte Runde-1-Plätze")
    parser.add_argument("--runde", type=int, choices=(1, 2))
    parser.add_argument("--max", type=int, default=0)
    parser.add_argument("--neu", action="store_true", help="auch Plätze mit vorhandenem Profil")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    from database.client import get_supabase_client
    from scraper.orte.google_places import alle_zeilen

    zeilen = alle_zeilen(get_supabase_client(), "orte", "id, name, slug, stadtteil, adresse, extras",
                         lambda q: q.eq("typ", "spielplatz"))
    if args.probe:
        auswahl = probe_auswahl(zeilen)
    elif args.runde:
        auswahl = sorted([z for z in zeilen if runde(z) == args.runde
                          and (args.neu or not z["extras"]["spielplatz"].get("profil"))], key=lambda z: z["name"])
    else:
        parser.error("--probe oder --runde angeben")
    if args.max:
        auswahl = auswahl[:args.max]
    logger.info("%d Plätze ausgewählt%s", len(auswahl), " [Dry-Run]" if args.dry_run else "")
    lauf(auswahl, args.dry_run)


if __name__ == "__main__":
    main()
