"""
kleine_weihnachtsmaerkte.py – DiesDasDüsseldorf
Feste Einträge für kleine Weihnachtsmärkte, die keine andere Quelle liefert (Auftraggeber 19.11.2026).

Gepflegt in data/weihnachtsmaerkte/kleine_maerkte.csv (eine Zeile je Markt, Angaben mit Quelle):
  titel, datum, datum_bis, uhrzeit, ort, adresse, kategorie, preis, beschreibung, quelle_name, quelle_url, bild_url
bild_url: eigenes Foto unter web/public/ort-bilder/… als Pfad (/ort-bilder/events/name.webp) oder https-Adresse, sonst leer.
Vergangene Märkte (Ende vor heute) werden übersprungen. Kein Abruf im Netz – die Angaben stehen in der Datei.
Auf der Website erscheinen die Märkte in „Kleine Weihnachtsmärkte an einzelnen Tagen“ (web/lib/weihnachtsmaerkte.ts
kurzMaerkte), über den Titel oder über data/weihnachtsmaerkte/event_einschluss.csv.
"""
import csv
import logging
import re
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

QUELLE_NAME = "Kleine Weihnachtsmärkte (Redaktion)"
DATEI = Path(__file__).resolve().parents[2] / "data" / "weihnachtsmaerkte" / "kleine_maerkte.csv"
KATEGORIEN = {"kultur", "musik", "food", "sport", "outdoor", "community", "nightlife", "family", "dating", "sonstiges"}


def zeile_zu_event(z: dict, heute: date) -> dict | None:
    """Eine CSV-Zeile als Event-Objekt (Pflichtfelder geprüft), None bei Fehlern oder vergangenen Märkten."""
    titel, datum, ort = (z.get("titel") or "").strip(), (z.get("datum") or "").strip(), (z.get("ort") or "").strip()
    if not titel or not datum or not ort:
        logger.warning("Kleiner Weihnachtsmarkt ohne Titel, Datum oder Ort übersprungen: %s", z)
        return None
    try:
        start = date.fromisoformat(datum)
        ende = date.fromisoformat(z["datum_bis"]) if (z.get("datum_bis") or "").strip() else start
    except ValueError:
        logger.warning("Kleiner Weihnachtsmarkt mit ungültigem Datum übersprungen: %s", titel)
        return None
    if ende < heute:
        return None
    bild_url = (z.get("bild_url") or "").strip() or None
    if bild_url and not (re.fullmatch(r"/ort-bilder/[a-z0-9-]+/[a-z0-9-]+\.(webp|jpg|png)", bild_url) or bild_url.startswith("https://")):
        logger.warning("Ungültige Bildadresse bei %s – ohne Bild", titel)
        bild_url = None
    kategorie = (z.get("kategorie") or "").strip() or "sonstiges"
    if kategorie not in KATEGORIEN:
        logger.warning("Unbekannte Kategorie %s bei %s – sonstiges", kategorie, titel)
        kategorie = "sonstiges"
    return {
        "titel": titel,
        "datum": datum,
        "datum_bis": z["datum_bis"].strip() if (z.get("datum_bis") or "").strip() else None,
        "uhrzeit": (z.get("uhrzeit") or "").strip() or None,
        "ort": ort,
        "adresse": (z.get("adresse") or "").strip() or None,
        "kategorie": kategorie,
        "beschreibung": (z.get("beschreibung") or "").strip() or None,
        "preis": (z.get("preis") or "").strip() or None,
        "quelle_name": (z.get("quelle_name") or "").strip() or QUELLE_NAME,
        "quelle_url": (z.get("quelle_url") or "").strip() or None,
        "bild_url": bild_url,
        "bild_generiert": False,
        "post_typ": "feed",
        "instagram_caption": None,
        "status": "neu",
    }


def scrape() -> list[dict]:
    """Alle noch kommenden kleinen Weihnachtsmärkte aus der Pflegedatei."""
    try:
        with DATEI.open(encoding="utf-8-sig", newline="") as f:
            zeilen = list(csv.DictReader(f))
    except Exception as fehler:
        logger.error("Pflegedatei %s nicht lesbar: %s", DATEI, fehler)
        return []
    heute = date.today()
    events = [e for e in (zeile_zu_event(z, heute) for z in zeilen) if e]
    logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    for e in scrape():
        print(e["datum"], e["titel"], "|", e["ort"], "|", e["quelle_url"])
