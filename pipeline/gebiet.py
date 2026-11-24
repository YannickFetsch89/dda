"""
gebiet.py – DiesDasDüsseldorf
Nur Events aus Düsseldorf, Neuss und Ratingen (Entscheidung des Auftraggebers vom 18.11.2026, Plan
docs/plan-locations-2026-11-18.md, E3). Anlass: Ein Event aus Leipzig (über PRINZ.de) und Vorstellungen im
Theater Duisburg (Deutsche Oper am Rhein) standen auf der Website.

Ein Event fällt heraus, wenn
1. die Adresse eine Postleitzahl außerhalb des Gebiets enthält (Düsseldorf 40210–40629, Neuss 41460–41472,
   Ratingen 40878–40885),
2. Ort oder Adresse eine andere Stadt nennen (eindeutige Namen als ganzes Wort, z. B. „Theater Duisburg“, „…, Leipzig“;
   mehrdeutige wie „Essen“ oder „Köln“ nur als eigener Abschnitt, z. B. „…, Köln“ – so bleiben „Kölner Straße“,
   „Gemeinsam Essen“ und das Schiff der „Köln-Düsseldorfer“ drin),
3. der Ort auf der Liste bekannter auswärtiger Orte steht (z. B. Neanderthal Museum in Mettmann),
4. Ort oder Adresse mit Köln/Frankfurt als letztem Wort endet („Lanxess Arena Köln“, „Widdersdorfer Str. 198 Köln“),
   der Ort Köln/Cologne als eigenes Wort nennt („✅ Köln Meetup | Daily Events!“, „Cologne Men's Circle“ – nicht
   „Köln-Düsseldorfer“, „Kölner Straße“) oder eine Online-Gruppe einer anderen Stadt ist („Kölner Tattoo Community
   (Online)“) – Nachtrag 20.11.2026,
5. der Titel eine andere Stadt eindeutig als Veranstaltungsort nennt (Nachtrag 20.11.2026) – nur wenn die Adresse keine
   PLZ im Gebiet hat und der Titel nicht selbst Düsseldorf/Neuss/Ratingen nennt („Fortuna Düsseldorf – 1. FC Köln“
   bleibt): „Duisburg im Winterzauber“, „Hackathon … Köln“, „… in Wuppertal“, „Leipziger Weihnachtsmarkt“,
   „House of Banksy Hanau | Ticket“. Essen und Frankfurt zählen im Titel nicht (Wort bzw. Vereinsname).
Online-Events bleiben, wenn sie keine andere Stadt nennen.

Bestand bereinigen (nur lesend, schreibt eine SQL-Datei, die der Auftraggeber ausführt):
    python -m pipeline.gebiet --sql
"""
import argparse
import logging
import re
from collections import Counter
from typing import Optional

logger = logging.getLogger(__name__)

# Postleitzahlen im Gebiet
PLZ_BEREICHE = [(40210, 40629), (41460, 41472), (40878, 40885)]

# Eindeutige Städte: als ganzes Wort irgendwo in Ort oder Adresse → außerhalb
# („Duisburger Straße“ trifft nicht, weil \b nach „Duisburg“ ein Wortende verlangt)
STAEDTE_EINDEUTIG = [
    "Duisburg", "Leipzig", "Dortmund", "Wuppertal", "Krefeld", "Mönchengladbach", "Gelsenkirchen", "Bochum",
    "Oberhausen", "Mülheim an der Ruhr", "Erkrath", "Mettmann", "Monheim", "Hilden", "Langenfeld", "Meerbusch",
    "Haan", "Solingen", "Remscheid", "Leverkusen", "Kaarst", "Dormagen", "Grevenbroich", "Velbert", "Heiligenhaus",
    "Wülfrath", "Jüchen", "Willich", "Viersen", "Moers", "Bonn", "Aachen", "Berlin", "Hamburg", "München",
    "Frankfurt am Main", "Stuttgart", "Münster", "Bielefeld", "Hannover", "Dresden", "Nürnberg", "Bremen",
    "Gladbeck", "Bottrop", "Recklinghausen", "Hagen", "Wesel", "Kempen", "Tönisvorst", "Korschenbroich",
    # Nachtrag 18.11.2026 (Kandidatenliste Ortsseiten): weitere Städte aus PRINZ.de und Meetup
    "Kleve", "Winsen", "Gütersloh", "Herne", "Witten", "Unna", "Siegen", "Paderborn", "Düren", "Bergisch Gladbach",
    "Venlo", "Roermond", "Amsterdam", "Lünen", "Castrop-Rauxel", "Marl", "Dinslaken", "Emmerich", "Xanten", "Goch",
    "Geldern", "Nettetal", "Heinsberg", "Erkelenz", "Rees", "Hückeswagen", "Wermelskirchen", "Leichlingen", "Burscheid",
    # Nachtrag 19.11.2026 (Plan Locations 3.16): Ortsteile der Nachbarstädte (Erkrath, Meerbusch) als Vorsorge und
    # Mülheim als ganzes Wort („Stadthalle Mülheim“ ohne Komma rutschte durch; „Mülheimer Straße“ bleibt, weil \b
    # nach dem „m“ ein Wortende verlangt). Unterbach und Hamm sind Düsseldorfer Stadtteile und stehen NICHT hier.
    "Hochdahl", "Büderich", "Osterath", "Mülheim",
    # Nachtrag 19.11.2026 (Kandidatenliste Ortsseiten): „Lufre Event & Gastronomie, Kamp-Lintfort“ (PRINZ.de)
    "Kamp-Lintfort",
    # Nachtrag 20.11.2026 (Befund Rausgegangen/PRINZ.de): Hanau („House of Banksy Hanau“), Hürth (Gertrudenhof)
    "Hanau", "Hürth",
    # Nachtrag 20.11.2026 (Kandidatenliste Ortsseiten, PRINZ.de): Bürgerhaus Telgte, Grefrath (Kreis Viersen)
    "Telgte", "Grefrath",
]
# Mehrdeutig (normales Wort oder Teil von Düsseldorfer Namen): nur als eigener Abschnitt
STAEDTE_ABSCHNITT = ["Köln", "Koeln", "Cologne", "Essen", "Frankfurt"]

# Bekannte Orte außerhalb, deren Name keine Stadt nennt (normalisiert: klein, ohne Satzzeichen)
AUSWAERTIGE_ORTE = {
    "neanderthal museum", "schloss dyck", "visiodrom", "fzw", "szene 10", "cabaret queue",
    "kulturraffinerie k714", "kulturfabrik krefeld", "galerie für zeitgenössische kunst",
    # Nachtrag 18.11.2026: Stadt nur als Wortteil oder Adjektiv im Namen
    "grugahalle", "theater essen süd", "zeche carl", "kokerei zollverein", "theaterhagen", "wuppertaler miniaturland",
    # Nachtrag 19.11.2026 (Kandidatenliste Ortsseiten): Buchhandlung in Essen, „Essen“ ohne eigenen Abschnitt
    "mayersche essen",
    # Nachtrag 20.11.2026 (Geo-Prüfung Ortsseiten): Erlebnisbauernhof in Hürth bei Köln
    "gertrudenhof",
    # Nachtrag 20.11.2026: „Grefrather EisSport & EventPark“ (Stadt nur als Adjektiv im Namen)
    "grefrather eissport",
}

_PLZ = re.compile(r"(?<!\d)(\d{5})(?!\d)")
# Ort endet mit Köln/Frankfurt als eigenem letzten Wort („Lanxess Arena Köln“); „Köln-Düsseldorfer“ trifft nicht
_ORT_ENDE = re.compile(r"\s(Köln|Koeln|Cologne|Frankfurt)\s*$", re.I)
# Köln als eigenes Wort im Ortsnamen (nicht „Köln-Düsseldorfer“, nicht „Kölner“)
_KOELN_WORT = re.compile(r"(?<![\w-])(Köln|Koeln|Cologne)(?![\w-])", re.I)
# Online-Gruppe einer anderen Stadt: Stadtname als Adjektiv („Kölner …“, „Essener …“) bei Online-Orten
_ONLINE = re.compile(r"\bonline\b", re.I)
_STADT_ADJEKTIV = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in STAEDTE_EINDEUTIG + ["Köln", "Koeln", "Essen", "Frankfurt"]) + r")er\b"
    r"|\b(Kölsche[rn]?)\b",
    re.I,
)
# Titel: Stadtnamen, die als Veranstaltungsort gelten (ohne Essen/Frankfurt, siehe oben)
_TITEL_STAEDTE = "|".join(re.escape(s) for s in STAEDTE_EINDEUTIG + ["Köln", "Koeln", "Cologne"])
_TITEL_REGELN = [
    re.compile(r"^(" + "|".join(re.escape(s) for s in STAEDTE_EINDEUTIG) + r")\s+(?:im|in|am)\b", re.I),  # „Duisburg im …“
    re.compile(r"\bin\s+(" + _TITEL_STAEDTE + r")\b", re.I),                                             # „… in Köln“
    re.compile(r"(?:^|[\s|–—(-])(" + _TITEL_STAEDTE + r")\s*(?:\)\s*)?(?:[|–—-]\s*[^|–—-]{0,40})?$", re.I),  # Ende / „Hanau | Ticket“
    re.compile(r"\b(" + "|".join(re.escape(s) for s in STAEDTE_EINDEUTIG) + r")er\s+"
               r"(?:Weihnachtsmarkt|Christkindlmarkt|Adventsmarkt|Weihnachtszauber)", re.I),               # „Leipziger Weihnachtsmarkt“
]
_GEBIET_IM_TITEL = re.compile(r"D(?:ü|ue|u)sseldorf|Neuss|Ratingen", re.I)
_EINDEUTIG = re.compile(r"\b(" + "|".join(re.escape(s) for s in STAEDTE_EINDEUTIG) + r")\b", re.I)
# Abschnitt: am Anfang oder nach Komma/Klammer/Strich/PLZ, danach Ende, Komma, Klammer oder Strich mit Leerzeichen
_ABSCHNITT = re.compile(
    r"(?:^|[,(/|]\s*|\s[–—-]\s+|\d{5}\s+)(" + "|".join(re.escape(s) for s in STAEDTE_ABSCHNITT) + r")"
    r"(?=\s*(?:$|[,)/|]|\s[–—-]\s|\s*\())",
    re.I,
)


# Stadtname als ganzes Wort: „Neuss“ ja, „Neusser Straße“ nein (Cursor-Prüfung 24.11.2026)
_GEBIET_WORT = re.compile(r"(?<![\w-])(D(?:ü|ue|u)sseldorf|Neuss|Ratingen)(?![\w-])", re.I)


def plz_im_gebiet(plz: str) -> bool:
    """Liegt eine fünfstellige PLZ in Düsseldorf, Neuss oder Ratingen?"""
    return bool(re.fullmatch(r"\d{5}", (plz or "").strip())) and any(a <= int(plz) <= b for a, b in PLZ_BEREICHE)


def stadt_im_gebiet(text: str) -> bool:
    """Nennt der Text Düsseldorf, Neuss oder Ratingen als ganzes Wort?"""
    return bool(_GEBIET_WORT.search(text or ""))


def adresse_im_gebiet(adresse: str, ort: str = "") -> bool:
    """
    Für Quellen aus einem größeren Umkreis (Stagedates, Ticketmaster): Steht eine PLZ in der Adresse, entscheidet sie.
    Sonst muss die Stadt (letzter Abschnitt der Adresse, dann der Ortsname) als ganzes Wort im Gebiet liegen.
    """
    plzs = _PLZ.findall(adresse or "")
    if plzs:
        return plz_im_gebiet(plzs[-1])
    letzter = (adresse or "").split(",")[-1]
    return stadt_im_gebiet(letzter) or stadt_im_gebiet(ort)


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\wäöüß ]+", " ", t.lower())).strip()


def grund_ausserhalb(event: dict) -> Optional[str]:
    """Grund, warum das Event außerhalb des Gebiets liegt – oder None, wenn es bleibt."""
    ort = (event.get("ort") or "").strip()
    adresse = (event.get("adresse") or "").strip()
    for plz in _PLZ.findall(adresse):
        n = int(plz)
        if not any(a <= n <= b for a, b in PLZ_BEREICHE):
            return f"PLZ {plz}"
    for text in (ort, adresse):
        m = _EINDEUTIG.search(text)
        if m:
            return f"Stadt {m.group(1)}"
        m = _ABSCHNITT.search(text)
        if m:
            return f"Stadt {m.group(1)}"
    for text in (ort, adresse):
        m = _ORT_ENDE.search(text)
        if m:
            return f"Stadt {m.group(1)}"
    m = _KOELN_WORT.search(ort)
    if m:
        return f"Stadt {m.group(1)}"
    if _ONLINE.search(ort):
        m = _STADT_ADJEKTIV.search(ort)
        if m:
            return f"Online-Gruppe {m.group(0)}"
    titel = (event.get("titel") or "").strip()
    plz_im_gebiet = any(any(a <= int(p) <= b for a, b in PLZ_BEREICHE) for p in _PLZ.findall(adresse))
    if titel and not plz_im_gebiet and not _GEBIET_IM_TITEL.search(titel):
        for regel in _TITEL_REGELN:
            m = regel.search(titel)
            if m:
                return f"Titel nennt {m.group(1)}"
    n = _norm(ort)
    # Ganzes Wort bzw. Wortfolge irgendwo im Namen („LUTZ, theaterhagen“, „Grugahalle Essen“)
    if any(re.search(r"(^|\s)" + re.escape(o) + r"(\s|$)", n) for o in AUSWAERTIGE_ORTE):
        return "auswärtiger Ort"
    return None


def gebiet_filtern(events: list[dict]) -> list[dict]:
    """Verwirft Events außerhalb von Düsseldorf, Neuss und Ratingen (vor dem Speichern, main.py Schritt 1c)."""
    bleiben, raus = [], Counter()
    for e in events:
        grund = grund_ausserhalb(e)
        if grund:
            raus[e.get("quelle_name") or "?"] += 1
            logger.debug("Gebiet: verworfen (%s): %s – %s", grund, e.get("titel"), e.get("ort"))
        else:
            bleiben.append(e)
    if raus:
        logger.info("Gebietsfilter: %d Events außerhalb von Düsseldorf/Neuss/Ratingen verworfen (%s)",
                    sum(raus.values()), ", ".join(f"{q}: {n}" for q, n in raus.most_common()))
    return bleiben


def sql_erzeugen(pfad: str) -> int:
    """Liest alle Events (nur lesend) und schreibt DELETE-Anweisungen für die außerhalb des Gebiets."""
    from database.client import get_supabase_client

    db = get_supabase_client()
    zeilen, start = [], 0
    while True:
        teil = (db.table("events").select("id, titel, datum, ort, adresse, quelle_name")
                .range(start, start + 999).execute().data or [])
        zeilen.extend(teil)
        if len(teil) < 1000:
            break
        start += 1000
    treffer = [(e, grund_ausserhalb(e)) for e in zeilen]
    treffer = [(e, g) for e, g in treffer if g]
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(f"-- {pfad.split('/')[-1]} – DiesDasDüsseldorf\n")
        f.write("-- Events außerhalb von Düsseldorf, Neuss und Ratingen löschen (Plan Locations E3, 18.11.2026).\n")
        f.write("-- ERZEUGT von pipeline/gebiet.py (python -m pipeline.gebiet --sql). Abhängige Zeilen (Merkliste,\n")
        f.write("-- Sensibel-Kennzeichnung, SEO-Entscheidungen) löschen sich mit (ON DELETE CASCADE), Meldungen behalten\n")
        f.write("-- ihre Daten (SET NULL). Ausführen als postgres im Supabase-SQL-Editor, nicht während eines Pipeline-Laufs.\n")
        f.write(f"-- Anzahl: {len(treffer)} Events. Gründe: {dict(Counter(g.split(' ')[0] for _, g in treffer))}\n--\n")
        for e, g in treffer[:400]:
            f.write(f"--   {e['datum']} | {(e.get('ort') or '')[:60]} | {(e.get('adresse') or '')[:50]} | {g} | {e.get('quelle_name')}\n")
        f.write("\nBEGIN;\n\nDELETE FROM public.events WHERE id IN (\n")
        f.write(",\n".join(f"    '{e['id']}'" for e, _ in treffer) or "    NULL")
        f.write("\n);\n\nCOMMIT;\n\n-- Kontrolle: Zahl der gelöschten Events steht oben; danach sollte diese Abfrage 0 ergeben\n")
        ids = ", ".join(f"'{e['id']}'" for e, _ in treffer[:50]) or "NULL"
        f.write(f"SELECT count(*) AS noch_da FROM public.events WHERE id IN ({ids});\n")
    logger.info("Gebiet: SQL geschrieben (%s) – %d Events außerhalb", pfad, len(treffer))
    return len(treffer)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    from datetime import date
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    parser = argparse.ArgumentParser(description="Events außerhalb von Düsseldorf/Neuss/Ratingen")
    parser.add_argument("--sql", action="store_true", help="SQL zum Bereinigen des Bestands erzeugen")
    parser.add_argument("--ausgabe", default=f"database/gebiet_bereinigung_{date.today().isoformat()}.sql")
    args = parser.parse_args()
    if args.sql:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        sql_erzeugen(args.ausgabe)


if __name__ == "__main__":
    main()
