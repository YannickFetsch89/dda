"""
zakk.py – DiesDasDüsseldorf
Scraper für zakk Düsseldorf: Events und Veranstaltungen.

Das zakk (Zentrum für Aktion, Kultur und Kommunikation) ist ein
soziokulturelles Zentrum in Düsseldorf-Flingern mit einem breiten
Kulturprogramm (Musik, Wort & Bühne, Party, Politik & Gesellschaft).

Ziel-URL: https://zakk.de/programm

DOM-Struktur der Seite (Joomla-CMS):
  <li class="single-ticket cf [tags...]" data-value="DD.MM.YYYY">
    <div class="ticket-date">          ← Datum (Fallback)
    <div class="ticket-content">
      <div class="ticket-info">
        <h2><a href="/event-detail?event=ID">Titel</a></h2>
        <h3>Untertitel</h3>
        <p>Kurzbeschreibung</p>
      </div>
      <div class="event-overview">
        <p class="event-categorie">Wort & Bühne / Musik / ...</p>
        <p class="event-time">HH Uhr<br>Einlass ...<br>Raum</p>
        <p class="event-price">VVK € XX / AK € XX / Eintritt frei</p>
      </div>
    </div>
  </li>

Bild-URL-Muster: https://zakk.de/images/quadrat/{event_id}.jpg

Erstellt: 2026-02-24
"""
import logging
import re
from datetime import date, datetime, timedelta
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from scraper.utils.http_client import seite_abrufen

logger = logging.getLogger(__name__)

BASE_URL = "https://zakk.de"
PROGRAMM_URL = "https://zakk.de/programm"
QUELLE_NAME = "zakk"
ADRESSE = "Fichtenstraße 40, 40233 Düsseldorf"

# Bild-URL-Muster: Event-ID kann direkt genutzt werden
BILD_URL_MUSTER = "https://zakk.de/images/quadrat/{event_id}.jpg"

# Mapping zakk-Kategorien → DDA-Kategorien
KATEGORIE_MAP = {
    "musik": "musik",
    "party": "nightlife",
    "wort & bühne": "kultur",
    "wort und bühne": "kultur",
    "politik & gesellschaft": "community",
    "politik und gesellschaft": "community",
    "interkultur": "community",
    "special": "community",
    "strassenfest": "community",
    "projekte": "community",
}


def _datum_parsen(text: str) -> Optional[str]:
    """
    Wandelt das zakk-Datumsformat DD.MM.YYYY in ISO 8601 um.

    Das data-value-Attribut der Seite liefert Daten in Form "24.02.2026".
    Zusätzlich werden Fallback-Formate abgedeckt.

    Args:
        text: Roher Datumstext aus dem data-value-Attribut oder dem DOM

    Returns:
        Datum als ISO-String YYYY-MM-DD oder None bei Fehler
    """
    if not text:
        return None

    bereinigt = text.strip()

    try:
        # Primärformat: "24.02.2026" (data-value Attribut)
        treffer = re.search(r"(\d{1,2})\.(\d{2})\.(\d{4})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(3)),
                int(treffer.group(2)),
                int(treffer.group(1)),
            ).isoformat()

        # Fallback: ISO-Format bereits vorhanden "2026-02-24"
        treffer = re.search(r"(\d{4})-(\d{2})-(\d{2})", bereinigt)
        if treffer:
            return date(
                int(treffer.group(1)),
                int(treffer.group(2)),
                int(treffer.group(3)),
            ).isoformat()

    except (ValueError, AttributeError) as fehler:
        logger.warning(
            "Datum konnte nicht geparst werden: '%s' – %s", text, fehler
        )
        return None

    return None


def _uhrzeit_parsen(text: str) -> Optional[str]:
    """
    Extrahiert die Anfangsuhrzeit aus dem event-time-Feld.

    Das event-time-Element enthält mehrere Zeilen:
      "20 Uhr\\nEinlass 19 Uhr\\nHalle"
    Es wird nur die erste Zeitangabe (Beginn) zurückgegeben.

    Args:
        text: Roher Zeittext aus .event-time

    Returns:
        Uhrzeit als HH:MM oder None
    """
    if not text:
        return None

    # Erste Zeitangabe aus dem Text holen (vor "Einlass" oder Raumname)
    erste_zeile = text.strip().split("\n")[0].strip()

    treffer = re.search(r"\b(\d{1,2})[:\.](\d{2})\b", erste_zeile)
    if treffer:
        stunde = int(treffer.group(1))
        minute = int(treffer.group(2))
        if 0 <= stunde <= 23 and 0 <= minute <= 59:
            return f"{stunde:02d}:{minute:02d}"

    # Fallback: "20 Uhr" ohne Minuten → "20:00"
    treffer = re.search(r"\b(\d{1,2})\s+Uhr\b", erste_zeile, re.IGNORECASE)
    if treffer:
        stunde = int(treffer.group(1))
        if 0 <= stunde <= 23:
            return f"{stunde:02d}:00"

    return None


def _raum_aus_zeittext(text: str) -> Optional[str]:
    """
    Extrahiert den Raumnamen aus dem event-time-Feld.

    Das Feld enthält z.B. "20 Uhr\\nEinlass 19 Uhr\\nHalle".
    Der Raumname steht typischerweise in der letzten Zeile.

    Args:
        text: Roher Zeittext aus .event-time

    Returns:
        Raumname (z.B. "Halle", "Club", "Tanzraum") oder None
    """
    if not text:
        return None

    zeilen = [z.strip() for z in text.strip().split("\n") if z.strip()]
    if not zeilen:
        return None

    letzte_zeile = zeilen[-1]

    # Raumname darf keine Zeitangaben enthalten
    if re.search(r"\d+\s*Uhr", letzte_zeile, re.IGNORECASE):
        return None

    # Bekannte Räume des zakk
    bekannte_raeume = {
        "Halle", "Club", "Tanzraum", "Kneipe", "Studio", "Raum 4",
        "Biergarten", "Foyer",
    }
    for raum in bekannte_raeume:
        if raum.lower() in letzte_zeile.lower():
            return raum

    # Allgemeiner Fallback: letztes Token wenn es nicht nach Zeit aussieht
    if len(letzte_zeile) < 40:
        return letzte_zeile

    return None


def _preis_bereinigen(text: str) -> Optional[str]:
    """
    Kürzt den Preistext auf einen kompakten, lesbaren Wert.

    Lange Texte wie "VVK € 21,50 / AK € 23,00 zakk Ermäßigung" werden
    auf "VVK 21,50 € / AK 23,00 €" verkürzt.
    "Eintritt frei ..." wird zu "kostenlos".

    Args:
        text: Roher Preistext aus .event-price

    Returns:
        Bereinigter Preistext oder None
    """
    if not text:
        return None

    bereinigt = text.strip()

    # Kostenlos-Varianten
    if re.match(r"^eintritt\s+frei", bereinigt, re.IGNORECASE):
        return "kostenlos"

    # Preis-Extraktion: VVK und/oder AK
    vvk_treffer = re.search(r"VVK\s*€\s*([\d,]+)", bereinigt)
    ak_treffer = re.search(r"AK\s*€\s*([\d,]+)", bereinigt)

    if vvk_treffer and ak_treffer:
        return f"VVK {vvk_treffer.group(1)} € / AK {ak_treffer.group(1)} €"
    elif vvk_treffer:
        return f"ab {vvk_treffer.group(1)} €"
    elif ak_treffer:
        return f"AK {ak_treffer.group(1)} €"

    # Fallback: Roh-Text kürzen
    if len(bereinigt) > 60:
        bereinigt = bereinigt[:60].rsplit(" ", 1)[0] + "…"

    return bereinigt or None


def _kategorie_ermitteln(zakk_kategorie: str, titel: str) -> str:
    """
    Mappt eine zakk-Kategorie auf eine DDA-Kategorie.

    Falls die zakk-Kategorie nicht im Mapping steht, wird der Titel
    nach Schlüsselwörtern durchsucht.

    Args:
        zakk_kategorie: Kategorie-Text aus .event-categorie (z.B. "Musik")
        titel: Event-Titel für Keyword-Fallback

    Returns:
        DDA-Kategorie als String (z.B. "musik", "kultur", "nightlife")
    """
    zakk_lower = zakk_kategorie.strip().lower()

    # Direktes Mapping
    for schluessel, dda_kategorie in KATEGORIE_MAP.items():
        if schluessel in zakk_lower:
            return dda_kategorie

    # Titel-Fallback für häufige Begriffe
    titel_lower = titel.lower()
    if any(w in titel_lower for w in ["konzert", "live", "band", "jazz", "rock", "pop", "folk"]):
        return "musik"
    if any(w in titel_lower for w in ["party", "club", "disco", "tanzen", "dj"]):
        return "nightlife"
    if any(w in titel_lower for w in ["lesung", "theater", "kabarett", "comedy", "literatur"]):
        return "kultur"
    if any(w in titel_lower for w in ["workshop", "seminar", "vortrag", "diskussion"]):
        return "community"
    if any(w in titel_lower for w in ["kinder", "familie", "jugend"]):
        return "family"

    return "sonstiges"


def _event_id_aus_url(href: str) -> Optional[str]:
    """
    Extrahiert die Event-ID aus einer zakk-Event-URL.

    Erwartet Formate wie:
      "/event-detail?event=15262"

    Args:
        href: Relativer oder absoluter URL-String

    Returns:
        Event-ID als String (z.B. "15262") oder None
    """
    if not href:
        return None
    try:
        geparst = urlparse(href)
        params = parse_qs(geparst.query)
        event_ids = params.get("event", [])
        if event_ids:
            return event_ids[0]
    except Exception:
        pass
    return None


def _beschreibung_zusammenbauen(h3_text: str, p_text: str) -> Optional[str]:
    """
    Kombiniert Untertitel (h3) und Beschreibungstext (p) zu einem Beschreibungstext.

    Args:
        h3_text: Untertitel des Events
        p_text:  Kurzbeschreibung aus dem <p>-Element

    Returns:
        Kombinierter Beschreibungstext (max. 300 Zeichen) oder None
    """
    teile = []
    if h3_text:
        teile.append(h3_text.strip())
    if p_text:
        teile.append(p_text.strip())

    if not teile:
        return None

    beschreibung = " – ".join(teile)
    return beschreibung[:300] or None


def _event_aus_li(li_el, heute: date) -> Optional[dict]:
    """
    Extrahiert ein Event-Dict aus einem <li class="single-ticket"> Element.

    Die zakk-Programmliste verwendet folgende Struktur pro Event:
      <li class="single-ticket cf [tags]" data-value="DD.MM.YYYY">
        <div class="ticket-date">...</div>
        <div class="ticket-content">
          <div class="ticket-info">
            <h2><a href="/event-detail?event=ID">Titel</a></h2>
            <h3>Untertitel</h3>
            <p>Kurzbeschreibung</p>
          </div>
          <div class="event-overview">
            <p class="event-categorie">Kategorie</p>
            <p class="event-time">Zeit und Raum</p>
            <p class="event-price">Preis</p>
          </div>
        </div>
      </li>

    Args:
        li_el: BeautifulSoup <li class="single-ticket"> Element
        heute: Heutiges Datum für Filterung vergangener Events

    Returns:
        Event-Dict im DDA-Format oder None wenn Pflichtfelder fehlen
        bzw. das Event bereits vergangen ist
    """
    try:
        # --- Datum: data-value Attribut ist verlässlichste Quelle ---
        datum_raw = li_el.get("data-value", "")
        datum = _datum_parsen(datum_raw)

        # Fallback: Datum aus .ticket-date Text extrahieren
        if not datum:
            datum_el = li_el.select_one(".ticket-date .date")
            if datum_el:
                # Entfernt <small>-Tags und liest sauberen Text
                datum_text = datum_el.get_text(separator=".", strip=True)
                datum = _datum_parsen(datum_text)

        if not datum:
            logger.debug(
                "Kein Datum für Event gefunden (data-value='%s')", datum_raw
            )
            return None

        # Vergangene Events überspringen
        if date.fromisoformat(datum) < heute:
            return None

        # --- Titel und Event-URL aus ticket-info ---
        info_el = li_el.select_one(".ticket-info")
        if not info_el:
            return None

        titel_link = info_el.select_one("h2 > a")
        if not titel_link:
            return None

        titel = titel_link.get_text(strip=True)
        if not titel:
            return None

        href = titel_link.get("href", "")
        event_id = _event_id_aus_url(href)
        quelle_url = urljoin(BASE_URL, href) if href else PROGRAMM_URL

        # --- Untertitel und Beschreibung ---
        h3_el = info_el.select_one("h3")
        p_el = info_el.select_one("p")
        h3_text = h3_el.get_text(strip=True) if h3_el else ""
        p_text = p_el.get_text(strip=True) if p_el else ""
        beschreibung = _beschreibung_zusammenbauen(h3_text, p_text)

        # --- Kategorie ---
        overview_el = li_el.select_one(".event-overview")
        zakk_kategorie = ""
        if overview_el:
            kat_el = overview_el.select_one(".event-categorie")
            if kat_el:
                zakk_kategorie = kat_el.get_text(strip=True)

        kategorie = _kategorie_ermitteln(zakk_kategorie, titel)

        # --- Uhrzeit und Raum aus .event-time ---
        uhrzeit = None
        raum = None
        if overview_el:
            zeit_el = overview_el.select_one(".event-time")
            if zeit_el:
                # separator='\n' stellt sicher, dass <br>-Tags als Zeilenumbrüche
                # behandelt werden und Uhrzeit/Raumname sauber trennbar sind
                zeit_text = zeit_el.get_text(separator="\n", strip=True)
                uhrzeit = _uhrzeit_parsen(zeit_text)
                raum = _raum_aus_zeittext(zeit_text)

        # Ort: "zakk" + optionaler Raum
        ort = f"zakk – {raum}" if raum else "zakk"

        # --- Preis ---
        preis = None
        if overview_el:
            preis_el = overview_el.select_one(".event-price")
            if preis_el:
                # Links entfernen (z.B. "zakk Ermäßigung")
                for link in preis_el.find_all("a"):
                    link.decompose()
                preis_text = preis_el.get_text(separator=" ", strip=True)
                preis = _preis_bereinigen(preis_text)

        # --- Bild-URL: wird aus Event-ID konstruiert ---
        bild_url = None
        if event_id:
            bild_url = BILD_URL_MUSTER.format(event_id=event_id)

        return {
            "titel": titel,
            "datum": datum,
            "uhrzeit": uhrzeit,
            "ort": ort,
            "adresse": ADRESSE,
            "kategorie": kategorie,
            "beschreibung": beschreibung,
            "preis": preis,
            "quelle_name": QUELLE_NAME,
            "quelle_url": quelle_url,
            "bild_url": bild_url,
            "instagram_caption": None,
            "status": "neu",
        }

    except Exception as fehler:
        logger.error(
            "Fehler beim Parsen eines zakk-Events: %s", str(fehler), exc_info=True
        )
        return None


def scrape() -> list[dict]:
    """
    Scrapt Events vom zakk-Programm (https://zakk.de/programm).

    Die Seite liefert alle kommenden Events in einer vollständigen HTML-Liste
    ohne Paginierung. Alle Events der nächsten Monate werden auf einer Seite
    angezeigt. Vergangene Events werden herausgefiltert.

    Duplikate innerhalb eines Scraper-Laufs werden anhand der Event-URL
    erkannt und entfernt.

    Returns:
        Liste von Event-Dicts im DiesDasDüsseldorf Standard-Format.
        Leere Liste bei Verbindungsfehlern oder unerwarteter Seitenstruktur.
    """
    events: list[dict] = []
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)

    try:
        html = seite_abrufen(PROGRAMM_URL, logger)
        if html is None:
            logger.error("Scraper %s: Seite konnte nicht abgerufen werden.", QUELLE_NAME)
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Primärsuche: alle <li class="single-ticket"> mit data-value (= echte Events)
        ticket_els = soup.select("li.single-ticket[data-value]")

        # Fallback: alle single-ticket Elemente, Monatstrennzeilen werden im
        # Parsing automatisch durch fehlendes data-value ausgesiebt
        if not ticket_els:
            ticket_els = soup.select("li.single-ticket")
            logger.info(
                "Primärsuche ohne Ergebnis – Fallback auf alle .single-ticket (%d Elemente)",
                len(ticket_els),
            )

        if not ticket_els:
            logger.warning(
                "Keine Event-Elemente gefunden auf %s – "
                "Seitenstruktur hat sich möglicherweise geändert.",
                PROGRAMM_URL,
            )
            return []

        logger.info("%d potenzielle Event-Elemente gefunden", len(ticket_els))

        # Duplikate innerhalb eines Laufs verhindern (gleiche Event-URL)
        gesehene_urls: set[str] = set()

        for li_el in ticket_els:
            event = _event_aus_li(li_el, heute)
            if event is None:
                continue

            url = event["quelle_url"]
            if url in gesehene_urls:
                logger.debug("Duplikat übersprungen: %s", url)
                continue
            gesehene_urls.add(url)

            events.append(event)

    except Exception as fehler:
        logger.error(
            "Scraper %s fehlgeschlagen: %s", QUELLE_NAME, str(fehler), exc_info=True
        )
        return []

    if len(events) == 0:
        logger.warning(
            "Scraper %s: 0 Events gefunden – "
            "Seitenstruktur hat sich möglicherweise geändert.",
            QUELLE_NAME,
        )
    else:
        logger.info("Scraper %s fertig: %d Events gefunden", QUELLE_NAME, len(events))

    return events


if __name__ == "__main__":
    # Direkter Testlauf: python -m scraper.tier2.zakk
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import json

    ergebnisse = scrape()

    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")

    if ergebnisse:
        print("--- Beispiel-Event (erstes Ergebnis) ---")
        print(json.dumps(ergebnisse[0], ensure_ascii=False, indent=2))
        print()
        if len(ergebnisse) > 1:
            print("--- Beispiel-Event (zweites Ergebnis) ---")
            print(json.dumps(ergebnisse[1], ensure_ascii=False, indent=2))
    else:
        print("Keine Events gefunden.")
