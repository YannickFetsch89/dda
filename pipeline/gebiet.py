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
3. der Ort auf der Liste bekannter auswärtiger Orte steht (z. B. Neanderthal Museum in Mettmann).
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
]
# Mehrdeutig (normales Wort oder Teil von Düsseldorfer Namen): nur als eigener Abschnitt
STAEDTE_ABSCHNITT = ["Köln", "Koeln", "Cologne", "Essen", "Mülheim", "Frankfurt"]

# Bekannte Orte außerhalb, deren Name keine Stadt nennt (normalisiert: klein, ohne Satzzeichen)
AUSWAERTIGE_ORTE = {
    "neanderthal museum", "schloss dyck", "visiodrom", "fzw", "szene 10", "cabaret queue",
    "kulturraffinerie k714", "kulturfabrik krefeld", "galerie für zeitgenössische kunst",
    # Nachtrag 18.11.2026: Stadt nur als Wortteil oder Adjektiv im Namen
    "grugahalle", "theater essen süd", "zeche carl", "kokerei zollverein", "theaterhagen", "wuppertaler miniaturland",
}

_PLZ = re.compile(r"(?<!\d)(\d{5})(?!\d)")
_EINDEUTIG = re.compile(r"\b(" + "|".join(re.escape(s) for s in STAEDTE_EINDEUTIG) + r")\b", re.I)
# Abschnitt: am Anfang oder nach Komma/Klammer/Strich/PLZ, danach Ende, Komma, Klammer oder Strich mit Leerzeichen
_ABSCHNITT = re.compile(
    r"(?:^|[,(/|]\s*|\s[–—-]\s+|\d{5}\s+)(" + "|".join(re.escape(s) for s in STAEDTE_ABSCHNITT) + r")"
    r"(?=\s*(?:$|[,)/|]|\s[–—-]\s|\s*\())",
    re.I,
)


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
