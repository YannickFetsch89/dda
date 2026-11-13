"""
ausstattung_import.py – DiesDasDüsseldorf
Ausstattung von Hand für den Guide „Spielplätze“ (Plan: docs/plan-spielplaetze-2026-11-12.md, Abschnitt 3.2).

Der Auftraggeber trägt in data/spielplaetze/ausstattung.csv ein, was er selbst gesehen hat (z. B. eine Tischtennisplatte).
Jede gültige Zeile wird mit quelle "sichtung" nach extras.spielplatz.ausstattung bzw. extras.spielplatz.extras geschrieben.
OSM-Abgleich und Profil überschreiben solche Einträge nie. Fehlt eine Zeile, die vorher da war, entfernt der Lauf nur
diesen Sichtungs-Eintrag. Der Lauf ändert nie aktiv, Name, Slug, Stadtteil oder Prüf-Codes.

Nutzung:
  python -m scraper.spielplaetze.ausstattung_import --dry-run
  python -m scraper.spielplaetze.ausstattung_import
"""
import argparse
import csv
import logging
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logger = logging.getLogger(__name__)

AUSSTATTUNG_CSV = Path(__file__).resolve().parents[2] / "data" / "spielplaetze" / "ausstattung.csv"
QUELLE = "sichtung"

# Filter-Geräte (Chip ab 5 sichtbaren Plätzen) und Nebengeräte (nur Detailseite) – Schlüssel wie in §3 des Plans
GERAETE = ("sandkasten", "schaukel", "rutsche", "klettern", "wasserspiel", "seilbahn", "tischtennis")
NEBENGERAETE = ("federwippe", "wippe", "karussell", "balancierbalken")
EXTRAS = ("schatten", "wc", "eingezaeunt", "picknick", "rollstuhl")


def bereich(merkmal: str) -> str | None:
    """In welches Feld von extras.spielplatz das Merkmal gehört: ausstattung, extras oder None (unbekannt)."""
    if merkmal in GERAETE or merkmal in NEBENGERAETE:
        return "ausstattung"
    if merkmal in EXTRAS:
        return "extras"
    return None


def ausstattung_lesen(pfad: Path) -> tuple[list[dict] | None, list[str]]:
    """
    Liest ausstattung.csv (Trennzeichen ; oder ,). Fehlt die Datei: (None, []) = nichts ändern.
    Rückgabe: gültige Zeilen {schluessel, merkmal, wert, beleg, stand} und Fehler (ungültige Zeilen werden nicht geschrieben).
    """
    if not pfad.exists():
        return None, []
    text = pfad.read_text(encoding="utf-8-sig")
    erste = text.splitlines()[0] if text.strip() else ""
    trenner = ";" if erste.count(";") >= erste.count(",") else ","
    gueltig, fehler, gesehen = [], [], set()
    for nr, z in enumerate(csv.DictReader(text.splitlines(), delimiter=trenner), start=2):
        z = {(k or "").strip().lower(): (v or "").strip() for k, v in z.items()}
        schluessel, merkmal, wert = z.get("schluessel", ""), z.get("merkmal", "").lower(), z.get("wert", "").lower()
        if not schluessel and not merkmal:
            continue
        grund = None
        if not schluessel:
            grund = "Schlüssel fehlt"
        elif not bereich(merkmal):
            grund = f"unbekanntes Merkmal „{merkmal}“"
        elif wert not in (("ja", "nein", "teilweise") if merkmal == "rollstuhl" else ("ja", "nein")):
            grund = f"Wert „{wert}“ ist für {merkmal} nicht erlaubt"
        elif not z.get("beleg"):
            grund = "Beleg fehlt"
        else:
            try:
                date.fromisoformat(z.get("stand", ""))
            except ValueError:
                grund = f"Datum „{z.get('stand')}“ ist kein YYYY-MM-DD"
        if not grund and (schluessel, merkmal) in gesehen:
            grund = "doppelte Zeile (Schlüssel und Merkmal) – die erste gilt"
        if grund:
            fehler.append(f"ausstattung.csv Zeile {nr}: {grund} – nicht geschrieben")
            continue
        gesehen.add((schluessel, merkmal))
        gueltig.append({"schluessel": schluessel, "merkmal": merkmal, "wert": wert,
                        "beleg": z["beleg"], "stand": z["stand"]})
    return gueltig, fehler


def zeilen_schluessel(zeile: dict) -> tuple[str | None, set[str]]:
    """(Schlüssel, unter dem die Zeile in den CSV-Dateien steht; alle Schlüssel der Zeile)."""
    sp = (zeile.get("extras") or {}).get("spielplatz") or {}
    if sp.get("quelle") == "abenteuer":
        return sp.get("schluessel"), {sp.get("schluessel")} - {None}
    teile = [t["objektschluessel"] for t in sp.get("teile") or []]
    return (teile[0] if teile else None), set(teile)


def planen(eintraege: list[dict], zeilen: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Rechnet für jede Datenbankzeile die neuen Felder ausstattung/extras aus.
    Rückgabe: Änderungen [{zeile, ausstattung, extras, gesetzt, entfernt}] (nur Zeilen mit Änderung) und Fehler.
    """
    fehler = []
    nach_haupt, gruppe_von = {}, {}
    for z in zeilen:
        haupt, alle = zeilen_schluessel(z)
        if haupt:
            nach_haupt[haupt] = z
        for s in alle:
            gruppe_von[s] = haupt
    je_zeile = {}
    for e in eintraege:
        if e["schluessel"] in nach_haupt:
            je_zeile.setdefault(e["schluessel"], []).append(e)
        elif e["schluessel"] in gruppe_von:
            fehler.append(f"ausstattung.csv: {e['schluessel']} ist nicht der kleinste Schlüssel seiner Gruppe "
                          f"({gruppe_von[e['schluessel']]}) – nicht geschrieben")
        else:
            fehler.append(f"ausstattung.csv: Schlüssel {e['schluessel']} gibt es nicht – nicht geschrieben")

    aenderungen = []
    for haupt, z in nach_haupt.items():
        sp = (z.get("extras") or {}).get("spielplatz") or {}
        felder = {"ausstattung": dict(sp.get("ausstattung") or {}), "extras": dict(sp.get("extras") or {})}
        alt = {"ausstattung": dict(felder["ausstattung"]), "extras": dict(felder["extras"])}
        soll = {(bereich(e["merkmal"]), e["merkmal"]): e for e in je_zeile.get(haupt, [])}
        entfernt = []
        for feld in ("ausstattung", "extras"):
            for merkmal, wert in list(felder[feld].items()):
                if (wert or {}).get("quelle") == QUELLE and (feld, merkmal) not in soll:
                    del felder[feld][merkmal]
                    entfernt.append(merkmal)
        gesetzt = []
        for (feld, merkmal), e in soll.items():
            neu = {"wert": e["wert"], "quelle": QUELLE, "beleg": e["beleg"], "stand": e["stand"]}
            if felder[feld].get(merkmal) != neu:
                gesetzt.append(merkmal)
            felder[feld][merkmal] = neu
        if felder != alt:
            aenderungen.append({"zeile": z, **felder, "gesetzt": sorted(gesetzt), "entfernt": sorted(entfernt)})
    return aenderungen, fehler


def schreiben(db, aenderungen: list[dict]) -> int:
    """Nur ausstattung und extras in extras.spielplatz ändern – extras direkt vorher frisch lesen."""
    fehler = 0
    for a in aenderungen:
        zid = a["zeile"]["id"]
        try:
            aktuell = (db.table("orte").select("extras").eq("id", zid).execute().data or [{}])[0].get("extras") or {}
            sp = {**(aktuell.get("spielplatz") or {}), "ausstattung": a["ausstattung"], "extras": a["extras"]}
            db.table("orte").update({"extras": {**aktuell, "spielplatz": sp}}).eq("id", zid).execute()
        except Exception as e:  # noqa: BLE001 – jede Zeile einzeln
            fehler += 1
            logger.error("Fehler bei %s: %s", a["zeile"]["slug"], e)
    return fehler


def importieren(dry_run: bool) -> None:
    eintraege, fehler = ausstattung_lesen(AUSSTATTUNG_CSV)
    if eintraege is None:
        logger.info("ausstattung.csv fehlt – nichts zu tun")
        return
    from database.client import get_supabase_client
    from scraper.orte.google_places import alle_zeilen

    db = get_supabase_client()
    zeilen = alle_zeilen(db, "orte", "id, name, slug, extras", lambda q: q.eq("typ", "spielplatz"))
    aenderungen, p_fehler = planen(eintraege, zeilen)
    for f in fehler + p_fehler:
        logger.error("%s", f)
    for a in aenderungen:
        logger.info("%s: gesetzt %s, entfernt %s", a["zeile"]["name"], a["gesetzt"] or "–", a["entfernt"] or "–")
    logger.info("%d gültige Zeilen, %d Spielplätze ändern sich%s", len(eintraege), len(aenderungen),
                " [Dry-Run, nichts geschrieben]" if dry_run else "")
    if not dry_run and aenderungen:
        logger.info("Fertig, %d Fehler", schreiben(db, aenderungen))


def main():
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Spielplätze: Ausstattung von Hand (ausstattung.csv)")
    parser.add_argument("--dry-run", action="store_true")
    importieren(parser.parse_args().dry_run)


if __name__ == "__main__":
    main()
