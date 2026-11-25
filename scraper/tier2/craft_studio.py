"""
craft_studio.py – DiesDasDüsseldorf
Scraper für The Craft Studio (Kreativ-Workshops, Eingang Stresemannplatz 4, Düsseldorf).
Programmseite: https://www.the-craftstudio.de/workshop-kalender

Die Wix-Seite bucht ihre Workshops über Wix Bookings (nicht etermin). Die einzelnen Termine stehen nicht im
HTML; das Kalender-Widget lädt sie erst im Browser (Woche für Woche über die Pfeiltaste „Nächste Woche anzeigen“).
Deshalb öffnen wir die Seite mit Playwright (synchron, wie scraper/tier1/kulturportal.py), blättern Woche für
Woche bis zum Fensterende (mind. 2 s Pause je Woche) und lesen die JSON-Antworten mit, die die Seite dabei
selbst lädt: time-slots/event (Termine) und bookings/v2/services/query (Kurse: Seite, Preis, Bild, Kategorie).
Kein eigener API-Aufruf, kein Login, kein Formular; der Cookie-Banner wird nicht angeklickt (die Pfeiltaste
wird per dispatch_event ausgelöst).

robots.txt geprüft am 2026-11-25: „User-agent: * / Allow: /“, gesperrt nur „*?lightbox=“ – erlaubt.

Übernommen werden nur feste Workshop-Termine mit Datum (keine Gutscheine, keine Gruppen-/Firmenanfragen).
Abgesagte Termine (eventCancelled) fallen weg, ausgebuchte bleiben. Kategorie community (Entscheidung Q16:
Workshops), Kinderkurse (Kinder/Kids/Familie/„Mini Me“) → family. ticket_url = Buchungsseite des Kurses auf der
eigenen Website (booking-calendar/…), quelle_url = Kursseite (service-page/…).

Adresse: Die Website nennt „Stresemannplatz 4, 40210 Düsseldorf“ (Eingang über The Code Agency/Coffee Brew).

Erstellt: 2026-11-25 (Quellen-Ausbau, Schritt V2, Welle B)
"""
import logging
import re
import time
from datetime import date, datetime
from typing import Optional

from config import vorschau_ende
from scraper.utils.http_client import STANDARD_HEADERS
from scraper.utils.ticket_link import ticket_link_haus

logger = logging.getLogger(__name__)

QUELLE_NAME = "The Craft Studio"
ORT_STANDARD = "The Craft Studio DÜSSELDORF"
ADRESSE_STANDARD = "Stresemannplatz 4, 40210 Düsseldorf"
BASE_URL = "https://www.the-craftstudio.de"
KALENDER_URL = "https://www.the-craftstudio.de/workshop-kalender"
BILD_BASIS = "https://static.wixstatic.com/media/"
WARTEZEIT_S = 2.0
MAX_WOCHEN = 30
ANTWORT_TIMEOUT_S = 20.0

_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍⃣]")
_FAMILIE = re.compile(r"kinder|kids|famili|mini ?me", re.I)


def _titel(text: str) -> str:
    """Emojis entfernen, Leerraum glätten („🎨Acrylic Painting - Golden Glow“ → „Acrylic Painting - Golden Glow“)."""
    text = _EMOJI.sub(" ", text or "")
    text = re.sub(r"\s+-\s*|\s*-\s+", " - ", text)   # „Cozy Colours -Tassen“ → „Cozy Colours - Tassen“
    return re.sub(r"\s+", " ", text).strip(" -–")


def _dienste(dienst_antworten: list[dict]) -> dict[str, dict]:
    """serviceId → {name, seite, buchung, preis, bild, kategorie} aus den services/query-Antworten."""
    ergebnis: dict[str, dict] = {}
    for antwort in dienst_antworten or []:
        for dienst in (antwort or {}).get("services") or []:
            try:
                urls = dienst.get("urls") or {}
                preis = (((dienst.get("payment") or {}).get("fixed") or {}).get("price") or {})
                bild = (((dienst.get("media") or {}).get("mainMedia") or {}).get("image") or {}).get("id")
                ergebnis[dienst["id"]] = {
                    "name": dienst.get("name") or "",
                    "seite": (urls.get("servicePage") or {}).get("url"),
                    "buchung": (urls.get("bookingPage") or {}).get("url"),
                    "preis": f"{preis['value']} €" if preis.get("value") and preis.get("currency") == "EUR" else None,
                    "bild": BILD_BASIS + bild if bild and re.fullmatch(r"[\w~.-]+", bild) else None,
                    "kategorie": ((dienst.get("category") or {}).get("name") or ""),
                }
            except Exception as fehler:
                logger.error("%s: Kurs nicht lesbar: %s", QUELLE_NAME, fehler)
    return ergebnis


def _termine_aus_daten(slot_antworten: list[dict], dienst_antworten: list[dict], heute: date,
                       enddatum: date) -> list[dict]:
    """Wandelt die mitgelesenen JSON-Antworten in Event-Dicts um (ohne Netz testbar)."""
    dienste = _dienste(dienst_antworten)
    events, gesehen = [], set()
    for antwort in slot_antworten or []:
        for slot in (antwort or {}).get("timeSlots") or []:
            try:
                if ((slot.get("nonBookableReasons") or {}).get("eventCancelled")):
                    continue
                ort = slot.get("location") or {}
                if ort.get("locationType") not in (None, "BUSINESS") and "craft" not in (ort.get("name") or "").lower():
                    continue   # Termin an einem anderen Ort
                start = datetime.fromisoformat((slot.get("localStartDate") or "")[:19])
                if not heute <= start.date() <= enddatum:
                    continue
                dienst = dienste.get(slot.get("serviceId"), {})
                titel = _titel((slot.get("eventInfo") or {}).get("eventTitle") or dienst.get("name") or "")
                if not titel:
                    continue
                uhrzeit = None if slot.get("allDay") else start.strftime("%H:%M")
                schluessel = (titel.lower(), start.date().isoformat(), uhrzeit)
                if schluessel in gesehen:
                    continue
                gesehen.add(schluessel)
                seite = dienst.get("seite") if (dienst.get("seite") or "").startswith(BASE_URL) else None
                buchung = ticket_link_haus(dienst.get("buchung"), BASE_URL)
                familie = _FAMILIE.search(f"{titel} {dienst.get('kategorie', '')}")
                events.append({
                    "titel": titel,
                    "datum": start.date().isoformat(),
                    "uhrzeit": uhrzeit,
                    "ort": ORT_STANDARD,
                    "adresse": ADRESSE_STANDARD,
                    "kategorie": "family" if familie else "community",
                    "beschreibung": None,
                    "preis": dienst.get("preis"),
                    "quelle_name": QUELLE_NAME,
                    "quelle_url": seite or KALENDER_URL,
                    "ticket_url": buchung if buchung and buchung != (seite or KALENDER_URL) else None,
                    "bild_url": dienst.get("bild"),
                    "bild_generiert": False,
                    "status": "neu",
                })
            except Exception as fehler:
                logger.error("%s: Termin nicht lesbar: %s", QUELLE_NAME, fehler)
    return sorted(events, key=lambda e: (e["datum"], e["uhrzeit"] or ""))


def _antworten_holen(wochen: int) -> tuple[list[dict], list[dict]]:
    """Öffnet den Workshopkalender im Browser, blättert `wochen` Wochen weiter und sammelt die JSON-Antworten."""
    from playwright.sync_api import sync_playwright

    slots: list[dict] = []
    dienste: list[dict] = []

    def antwort(r):
        try:
            if "/_api/service-availability/v2/time-slots/event" in r.url and r.ok:
                slots.append(r.json())
            elif "/_api/bookings/v2/services/query" in r.url and r.ok:
                dienste.append(r.json())
        except Exception as fehler:
            logger.debug("%s: Antwort nicht lesbar: %s", QUELLE_NAME, fehler)

    def warten_auf(anzahl: int, seite) -> bool:
        ende = time.monotonic() + ANTWORT_TIMEOUT_S
        while time.monotonic() < ende:
            if len(slots) > anzahl:
                return True
            seite.wait_for_timeout(250)
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            kontext = browser.new_context(locale="de-DE", timezone_id="Europe/Berlin",
                                          user_agent=STANDARD_HEADERS["User-Agent"])
            seite = kontext.new_page()
            seite.on("response", antwort)
            seite.goto(KALENDER_URL, wait_until="load", timeout=60000)
            if not warten_auf(0, seite):
                logger.warning("%s: Kalender hat keine Termine geladen", QUELLE_NAME)
                return slots, dienste
            for woche in range(wochen):
                seite.wait_for_timeout(int(WARTEZEIT_S * 1000))
                vorher = len(slots)
                knopf = seite.locator('button[data-hook="next-arrow"]')
                if knopf.count() == 0:
                    logger.warning("%s: Pfeil „Nächste Woche“ fehlt – Seitenstruktur geändert?", QUELLE_NAME)
                    break
                knopf.first.dispatch_event("click")
                if not warten_auf(vorher, seite):
                    logger.warning("%s: Woche %d nicht geladen – Abbruch", QUELLE_NAME, woche + 2)
                    break
        finally:
            browser.close()
    return slots, dienste


def scrape() -> list[dict]:
    """Scrapt den Workshopkalender von The Craft Studio. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        wochen = min(MAX_WOCHEN, (enddatum - heute).days // 7 + 1)
        slots, dienste = _antworten_holen(wochen)
        if not slots:
            return []
        events = _termine_aus_daten(slots, dienste, heute, enddatum)
        if not events:
            logger.warning("%s: 0 Termine auf erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []
    logger.info("Scraper %s fertig: %d Termine", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    for e in scrape()[:5]:
        print(e)
