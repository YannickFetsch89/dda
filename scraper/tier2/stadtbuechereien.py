"""
stadtbuechereien.py – DiesDasDüsseldorf
Scraper für die Stadtbüchereien Düsseldorf: Veranstaltungen und Events.

Strategie:
1. Primär: JSON-LD structured data (schema.org/Event)
2. Fallback: HTML-Parsing der städtischen Website – .event-list, .veranstaltung, article-Tags

URL: https://www.duesseldorf.de/stadtbuechereien/veranstaltungen
Adresse: Konrad-Adenauer-Platz 1, 40210 Düsseldorf
Erstellt: 2026-03-06
"""
import json
import logging
import re
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen
from scraper.utils.datum import datum_entfernen  # noqa: E402

logger = logging.getLogger(__name__)

BASE_URL = "https://www.duesseldorf.de"
LISTE_URL = "https://www.duesseldorf.de/stadtbuechereien/veranstaltungen"
QUELLE_NAME = "Stadtbüchereien Düsseldorf"
ORT_STANDARD = "Stadtbüchereien Düsseldorf"
ADRESSE_STANDARD = "Konrad-Adenauer-Platz 1, 40210 Düsseldorf"
KATEGORIE_STANDARD = "community"

MONAT_MAP: dict[str, int] = {
    "januar": 1, "februar": 2, "märz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8,
    "september": 9, "oktober": 10, "november": 11, "dezember": 12,
}
MONAT_KURZ_MAP: dict[str, int] = {
    "jan": 1, "feb": 2, "mär": 3, "mar": 3, "apr": 4,
    "mai": 5, "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "okt": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}

KATEGORIE_MAPPING = {
    "konzert": "musik", "musik": "musik", "live": "musik",
    "party": "nightlife", "club": "nightlife",
    "theater": "kultur", "ausstellung": "kultur", "kunst": "kultur",
    "kino": "kultur", "film": "kultur", "lesung": "kultur",
    "workshop": "community", "vortrag": "community", "talk": "community",
    "meetup": "community", "kurs": "community", "führung": "community",
    "kinder": "family", "jugend": "family", "familie": "family",
    "festival": "musik",
}


def _datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt verschiedene Datumsformate in ISO 8601 (YYYY-MM-DD) um.

    Args:
        text: Roher Datumstext

    Returns:
        ISO-Datum oder None
    """
    if not text:
        return None

    heute = date.today()
    bereinigt = text.strip()
    bereinigt_klein = bereinigt.lower()

    try:
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(int(treffer.group(1)), int(treffer.group(2)), int(treffer.group(3))).isoformat()

        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(int(treffer.group(3)), int(treffer.group(2)), int(treffer.group(1))).isoformat()

        treffer = re.search(r"(\d{1,2})\.?\s+([a-zäöüß]+)\s+(\d{4})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat = MONAT_MAP.get(treffer.group(2).lower())
            jahr = int(treffer.group(3))
            if monat:
                return date(jahr, monat, tag).isoformat()

        treffer = re.search(r"(\d{1,2})\.\s*([a-zäöü]{3})", bereinigt_klein)
        if treffer:
            tag = int(treffer.group(1))
            monat = MONAT_KURZ_MAP.get(treffer.group(2)[:3])
            if monat:
                kandidat = date(heute.year, monat, tag)
                if kandidat < heute - timedelta(days=1):
                    kandidat = date(heute.year + 1, monat, tag)
                return kandidat.isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning("Datum konnte nicht geparst werden: '%s' – %s", text, fehler)
        return None

    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """
    Extrahiert Uhrzeit im Format HH:MM aus Text.

    Args:
        text: Roher Text

    Returns:
        Uhrzeit als HH:MM oder None
    """
    if not text:
        return None
    treffer = re.search(r"\b(\d{1,2})[:\.](\d{2})\s*(?:Uhr)?", datum_entfernen(text), re.IGNORECASE)
    if treffer:
        stunde, minute = int(treffer.group(1)), int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"
    return None


def _kategorie_erkennen(text: str) -> str:
    """
    Mappt Texte auf DiesDasDüsseldorf-Kategorien.

    Args:
        text: Kategorie- oder Titeltext

    Returns:
        Gültige Kategorie
    """
    if not text:
        return KATEGORIE_STANDARD
    text_klein = text.lower()
    for schluessel, kategorie in KATEGORIE_MAPPING.items():
        if schluessel in text_klein:
            return kategorie
    return KATEGORIE_STANDARD


def _events_aus_json_ld(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    Primärstrategie: JSON-LD structured data extrahieren.

    Args:
        soup: Geparste HTML-Seite
        heute: Heute-Datum für Filterung

    Returns:
        Liste von Event-Dicts
    """
    events = []
    gesehene_schluessel: set[str] = set()

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            daten = json.loads(script.string or "{}")
        except (json.JSONDecodeError, AttributeError):
            continue

        eintraege = daten if isinstance(daten, list) else [daten]
        for eintrag in eintraege:
            if not isinstance(eintrag, dict):
                continue
            if eintrag.get("@type") not in ("Event", "ExhibitionEvent", "VisualArtsEvent", "MusicEvent"):
                continue

            titel = eintrag.get("name", "").strip()
            if not titel:
                continue

            datum_roh = eintrag.get("startDate") or eintrag.get("startDateTime")
            datum = _datum_parsen(str(datum_roh)) if datum_roh else None
            if not datum or date.fromisoformat(datum) < heute:
                continue

            ende_roh = eintrag.get("endDate")
            datum_bis = _datum_parsen(str(ende_roh)) if ende_roh else None

            uhrzeit = _uhrzeit_parsen(str(datum_roh))

            url_roh = eintrag.get("url")
            quelle_url = str(url_roh) if url_roh else LISTE_URL
            if quelle_url.startswith("/"):
                quelle_url = urljoin(BASE_URL, quelle_url)

            beschreibung_roh = eintrag.get("description")
            beschreibung = str(beschreibung_roh).strip()[:300] if beschreibung_roh else None

            bild_roh = eintrag.get("image")
            if isinstance(bild_roh, list) and bild_roh:
                bild_roh = bild_roh[0]
            if isinstance(bild_roh, dict):
                bild_url = bild_roh.get("url") or bild_roh.get("contentUrl")
            elif isinstance(bild_roh, str) and bild_roh.startswith("http"):
                bild_url = bild_roh
            else:
                bild_url = None

            kategorie = _kategorie_erkennen(titel)

            schluessel = f"{titel}_{datum}"
            if schluessel in gesehene_schluessel:
                continue
            gesehene_schluessel.add(schluessel)

            events.append({
                "titel": titel,
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ORT_STANDARD,
                "adresse": ADRESSE_STANDARD,
                "kategorie": kategorie,
                "beschreibung": beschreibung,
                "preis": None,
                "quelle_name": QUELLE_NAME,
                "quelle_url": quelle_url,
                "bild_url": bild_url,
                "instagram_caption": None,
                "datum_bis": datum_bis,
                "ist_wiederkehrend": False,
                "status": "neu",
            })

    return events


def _events_aus_html(soup: BeautifulSoup, heute: date) -> list[dict]:
    """
    Fallback: HTML-Parsing der städtischen Website.

    Stadtbüchereien-Struktur (Stand 2026-10):
    Jedes Event ist ein Block mit:
    - Optionaler Kategorie-Label ("Für Kids", "Digitales & Gaming")
    - Datum als "DD.MM.YYYY"
    - Link zu /newsdetail/<slug> mit Titel
    - Optionale Uhrzeitangabe
    - "Mehr"-Link

    Args:
        soup: Geparste HTML-Seite
        heute: Heute-Datum für Filterung

    Returns:
        Liste von Event-Dicts
    """
    events = []
    gesehene_schluessel: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if "/newsdetail/" not in href:
            continue

        titel_roh = link.get_text(strip=True)
        if not titel_roh or titel_roh.lower() == "mehr" or len(titel_roh) < 5:
            continue

        titel = re.sub(r"^\d{1,2}\.\d{1,2}\.\d{4}\s*[\-–|]\s*", "", titel_roh)
        titel = re.sub(r"^\d{1,2}\.\d{1,2}\.\d{4}\s*", "", titel)
        titel = titel.strip(" |–-")
        if not titel or len(titel) < 3:
            continue

        datum = None
        datum_treffer = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", titel_roh)
        if datum_treffer:
            datum = _datum_parsen(datum_treffer.group(0))

        if not datum:
            parent = link.parent
            if parent:
                parent_text = parent.get_text(" ", strip=True)
                datum_treffer = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", parent_text)
                if datum_treffer:
                    datum = _datum_parsen(datum_treffer.group(0))

        if not datum or date.fromisoformat(datum) < heute:
            continue

        parent = link.parent
        block_text = parent.get_text(" ", strip=True) if parent else ""
        uhrzeit = _uhrzeit_parsen(block_text)

        quelle_url = urljoin(BASE_URL, href)

        bild_url = None
        if parent:
            bild_el = parent.find("img")
            if bild_el:
                bild_src = bild_el.get("src") or bild_el.get("data-src")
                if bild_src:
                    bild_url = urljoin(BASE_URL, bild_src) if not bild_src.startswith("http") else bild_src

        kategorie = _kategorie_erkennen(titel)

        schluessel = f"{titel}_{datum}"
        if schluessel in gesehene_schluessel:
            continue
        gesehene_schluessel.add(schluessel)

        events.append({
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ORT_STANDARD,
            "adresse": ADRESSE_STANDARD,
            "kategorie": kategorie,
            "beschreibung": None,
            "preis": None,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "datum_bis": None,
            "ist_wiederkehrend": False,
            "status": "neu",
        })

    return events


# ── Filiale (Plan docs/plan-locations-2026-11-18.md, 3.15, Schritt 2a) ─────────────────────────────────────────
# Die Detailseite nennt am Ende den Ort: „Stadtbücherei Rath, Westfalenstraße 24“, „Kinderbücherei Hassels, …“ oder
# einen Raum der Zentralbibliothek („Im Musikstudio der Zentralbibliothek, Konrad-Adenauer-Platz 1“).
ZENTRALBIBLIOTHEK = "Zentralbibliothek KAP1"
ADRESSE_ZENTRAL = "Konrad-Adenauer-Platz 1, 40210 Düsseldorf"
PAUSE_DETAIL_S = 2.0   # Projektregel: mindestens 2 Sekunden zwischen Anfragen
_FILIALE = re.compile(r"\b(Stadt|Kinder)?[Bb]ücherei\s+([A-ZÄÖÜ][\wäöüß\-]+)(?:\s*,\s*([A-ZÄÖÜ][^,«]{2,40}?\s\d+\s?[a-zA-Z]?)\b)?")
_ZENTRAL = re.compile(r"Zentralbibli\w*|\bKAP\s?1\b|Konrad-Adenauer-Platz 1", re.I)
_FFT = re.compile(r"\bIm FFT\b|\bFFT Düsseldorf\b")
# Feste Adressen der Filialen: die Detailseiten haben Tippfehler („Friedriechstraße“, „Luegalle“) oder nennen nur
# den Namen. Unbekannte Filialen behalten die Adresse von der Seite.
FILIAL_ADRESSEN = {
    "Stadtbücherei Benrath": "Urdenbacher Allee 6, Düsseldorf",
    "Stadtbücherei Bilk": "Friedrichstraße 127, Düsseldorf",
    "Stadtbücherei Derendorf": "Blücherstraße 10, Düsseldorf",
    "Stadtbücherei Eller": "Gertrudisplatz 16, Düsseldorf",
    "Stadtbücherei Flingern": "Hoffeldstraße 69, Düsseldorf",
    "Stadtbücherei Garath": "Fritz-Erler-Straße 21, Düsseldorf",
    "Stadtbücherei Gerresheim": "Heyestraße 4, Düsseldorf",
    "Stadtbücherei Kaiserswerth": "Kaiserswerther Markt 22, Düsseldorf",
    "Stadtbücherei Oberkassel": "Luegallee 65, Düsseldorf",
    "Stadtbücherei Rath": "Westfalenstraße 24, Düsseldorf",
    "Stadtbücherei Unterbach": "Breidenplatz 8, Düsseldorf",
    "Stadtbücherei Unterrath": "Eckenerstraße 1, Düsseldorf",
    "Stadtbücherei Wersten": "Liebfrauenstraße 1, Düsseldorf",
}


def _mit_adresse(name: str, adresse: str = "") -> tuple[str, str]:
    """Filiale mit fester Adresse, sonst die Adresse von der Detailseite (oder leer)."""
    return name, FILIAL_ADRESSEN.get(name) or adresse


def filiale_aus_text(text: str) -> Optional[tuple[str, str]]:
    """
    Ort und Adresse aus dem Text einer Detailseite (rein, testbar). Ausgewertet wird das Ende der Seite (vor
    „« zurück“), weil dort der Veranstaltungsort steht; Erwähnungen anderer Filialen im Text zählen nicht.
    None, wenn kein Ort erkennbar ist.
    """
    ende = (text or "").split("« zurück")[0][-400:]
    if _FFT.search(ende):
        return "FFT Düsseldorf", ADRESSE_ZENTRAL   # Veranstaltung der Bücherei im FFT (KAP1, Foyer)
    treffer = list(_FILIALE.finditer(ende))
    if treffer:
        m = treffer[-1]
        art = "Kinderbücherei" if m.group(1) == "Kinder" else "Stadtbücherei"
        strasse = (m.group(3) or "").strip()
        return _mit_adresse(f"{art} {m.group(2)}", f"{strasse}, Düsseldorf" if strasse else "")
    if _ZENTRAL.search(ende):
        return ZENTRALBIBLIOTHEK, ADRESSE_ZENTRAL
    return None


def filiale_aus_titel(titel: str, filialen: set[str]) -> Optional[str]:
    """Rückfall ohne Detailseite: „… in Bilk“ im Titel, nur für bekannte Filialen."""
    m = re.search(r"\bin\s+([A-ZÄÖÜ][\wäöüß\-]+)\s*$", titel or "")
    return f"Stadtbücherei {m.group(1)}" if m and m.group(1) in filialen else None


def _filialen_aus_liste(html: str) -> set[str]:
    """Filialnamen aus den Kategorien der Liste („Veranstaltungen in der Bücherei Rath“)."""
    return set(re.findall(r"Veranstaltungen in der (?:Kinder)?[Bb]ücherei ([A-ZÄÖÜ][\wäöüß\-]+)", html or ""))


def _bekannte_orte() -> dict[str, tuple[str, str]]:
    """Schon zugeordnete Detailseiten aus der Datenbank (quelle_url → Ort, Adresse) – spart erneute Abrufe."""
    try:
        from database.client import get_supabase_client
        zeilen = (get_supabase_client().table("events").select("quelle_url, ort, adresse")
                  .eq("quelle_name", QUELLE_NAME).neq("ort", ORT_STANDARD)
                  .gte("datum", (date.today() - timedelta(days=30)).isoformat()).limit(5000).execute().data or [])
        return {z["quelle_url"]: (z["ort"], z.get("adresse") or "") for z in zeilen if z.get("quelle_url")}
    except Exception as fehler:
        logger.warning("Bekannte Bücherei-Orte nicht ladbar (alle Detailseiten werden abgerufen): %s", fehler)
        return {}


def filialen_zuordnen(events: list[dict], filialen: set[str], bekannt: dict[str, tuple[str, str]]) -> None:
    """Setzt ort/adresse je Event: bekannt → Detailseite → Titel → Standard (Netz)."""
    import time
    abgerufen = 0
    for e in events:
        url = e.get("quelle_url") or ""
        treffer = bekannt.get(url)
        if not treffer and "/newsdetail/" in url:
            if abgerufen:
                time.sleep(PAUSE_DETAIL_S)
            abgerufen += 1
            html = seite_abrufen(url, logger)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                treffer = filiale_aus_text((soup.find("main") or soup).get_text(" ", strip=True))
        if not treffer:
            name = filiale_aus_titel(e.get("titel") or "", filialen)
            treffer = _mit_adresse(name) if name else None
        if treffer:
            e["ort"] = treffer[0]
            if treffer[1]:
                e["adresse"] = treffer[1]
    logger.info("Bücherei-Filialen: %d Detailseiten abgerufen, %d Events zugeordnet", abgerufen,
                sum(1 for e in events if e["ort"] != ORT_STANDARD))


def scrape() -> list[dict]:
    """
    Scrapt Veranstaltungen der Stadtbüchereien Düsseldorf.

    Strategie:
    1. JSON-LD structured data
    2. HTML-Parsing als Fallback
    3. Filiale je Event aus der Detailseite (Plan Locations 3.15), schon bekannte aus der Datenbank

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
    """
    heute = date.today()
    enddatum = vorschau_ende(QUELLE_NAME, heute)
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = seite_abrufen(LISTE_URL, logger)
        if html is None:
            return []

        soup = BeautifulSoup(html, "html.parser")

        events = _events_aus_json_ld(soup, heute)
        logger.info("JSON-LD: %d Events gefunden", len(events))

        if not events:
            logger.warning("JSON-LD leer – versuche HTML-Parsing")
            events = _events_aus_html(soup, heute)
            logger.info("HTML-Fallback: %d Events gefunden", len(events))

        events = [e for e in events if date.fromisoformat(e["datum"]) <= enddatum]
        filialen_zuordnen(events, _filialen_aus_liste(html), _bekannte_orte())
        logger.info("Scraper %s fertig: %d Events", QUELLE_NAME, len(events))
        return events

    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(fehler))
        return []


def _sql(wert: Optional[str]) -> str:
    return "NULL" if wert is None else "'" + wert.replace("'", "''") + "'"


def nachtrag_sql(pfad: str) -> int:
    """
    Einmaliger Nachtrag (nur lesend, schreibt eine SQL-Datei): kommende, schon gespeicherte Bücherei-Events mit dem
    Netz-Namen bekommen ihre Filiale – sonst legte der erste Lauf des neuen Scrapers jedes Event ein zweites Mal an
    (anderer Ort = kein Dubletten-Treffer). Reihen-Schlüssel werden mitgezogen, wenn alle kommenden Termine einer Reihe
    in dieselbe Filiale gehen und der neue Schlüssel frei ist (wie pipeline/ortsnamen.py); sonst bleibt die Reihe.
    """
    import time
    from collections import defaultdict
    from database.client import get_supabase_client
    from pipeline.reihen_zuordnen import reihen_schluessel

    db = get_supabase_client()

    def alle(tabelle: str, spalten: str, filter_fn=None) -> list[dict]:
        zeilen, start = [], 0
        while True:
            q = db.table(tabelle).select(spalten)
            if filter_fn:
                q = filter_fn(q)
            teil = q.range(start, start + 999).execute().data or []
            zeilen += teil
            if len(teil) < 1000:
                return zeilen
            start += 1000

    events = alle("events", "id, titel, datum, uhrzeit, quelle_url, reihe_id",
                  lambda q: q.eq("quelle_name", QUELLE_NAME).eq("ort", ORT_STANDARD).gte("datum", date.today().isoformat()))
    reihen = {r["id"]: r for r in alle("reihen", "id, schluessel")}
    vorhandene_schluessel = {r["schluessel"] for r in reihen.values()}
    filialen = _filialen_aus_liste(seite_abrufen(LISTE_URL, logger) or "")
    zuweisung: dict[str, tuple[str, str]] = {}
    for i, e in enumerate(events):
        if i:
            time.sleep(PAUSE_DETAIL_S)
        html = seite_abrufen(e["quelle_url"], logger) if "/newsdetail/" in (e.get("quelle_url") or "") else None
        treffer = None
        if html:
            soup = BeautifulSoup(html, "html.parser")
            treffer = filiale_aus_text((soup.find("main") or soup).get_text(" ", strip=True))
        if not treffer:
            name = filiale_aus_titel(e["titel"], filialen)
            treffer = _mit_adresse(name) if name else None
        if treffer:
            zuweisung[e["id"]] = treffer

    neue_schluessel: dict[str, set[str]] = defaultdict(set)
    for e in events:
        if e.get("reihe_id") and e["id"] in zuweisung:
            k = reihen_schluessel(e["titel"], zuweisung[e["id"]][0])
            if k:
                neue_schluessel[e["reihe_id"]].add(k)
    reihen_update = {rid: next(iter(ks)) for rid, ks in neue_schluessel.items()
                     if len(ks) == 1 and next(iter(ks)) not in vorhandene_schluessel}
    reihen_bleiben = len(neue_schluessel) - len(reihen_update)

    je_ort: dict[tuple[str, str], list[str]] = defaultdict(list)
    for eid, (ort, adresse) in zuweisung.items():
        je_ort[(ort, adresse)].append(eid)
    zeilen = [
        "-- Stadtbüchereien: Filiale für kommende, schon gespeicherte Events (Plan docs/plan-locations-2026-11-18.md,",
        f"-- 3.15, Schritt 2a). Erzeugt am {date.today().isoformat()} von `python -m scraper.tier2.stadtbuechereien --sql`.",
        "-- VOR dem Deploy des neuen Bücherei-Scrapers ausführen, sonst entstehen Doppel-Einträge.",
        f"-- {len(zuweisung)} von {len(events)} Events bekommen eine Filiale; {len(reihen_update)} Reihen-Schlüssel werden",
        f"-- angepasst, {reihen_bleiben} Reihen bleiben (Termine in mehreren Filialen oder Schlüssel schon vergeben).",
        "", "BEGIN;", ""]
    for (ort, adresse), ids in sorted(je_ort.items()):
        liste = ", ".join(_sql(x) for x in sorted(ids))
        setzen = f"ort = {_sql(ort)}" + (f", adresse = {_sql(adresse)}" if adresse else "")
        zeilen.append(f"UPDATE public.events SET {setzen} WHERE id IN ({liste}) AND ort = {_sql(ORT_STANDARD)};")
    if reihen_update:
        zeilen += ["", "-- Reihen-Schlüssel (titel|ort) an die Filiale anpassen – Slugs bleiben"]
        zeilen += [f"UPDATE public.reihen SET schluessel = {_sql(k)} WHERE id = {_sql(rid)};"
                   for rid, k in sorted(reihen_update.items())]
    zeilen += ["", "COMMIT;", "", "-- Kontrolle: kommende Bücherei-Events je Ort",
               "SELECT ort, count(*) FROM public.events WHERE quelle_name = 'Stadtbüchereien Düsseldorf' "
               "AND datum >= current_date GROUP BY ort ORDER BY 2 DESC;"]
    with open(pfad, "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen) + "\n")
    logger.info("Bücherei-Nachtrag: %d/%d Events, %d Reihen → %s", len(zuweisung), len(events), len(reihen_update), pfad)
    return len(zuweisung)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import sys
    if "--sql" in sys.argv:
        from dotenv import load_dotenv
        load_dotenv(".env")
        nachtrag_sql(f"database/stadtbuechereien_filialen_{date.today().isoformat()}.sql")
        sys.exit(0)
    import json as _json
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for e in ergebnisse[:3]:
        print(_json.dumps(e, ensure_ascii=False, indent=2))
        print()
