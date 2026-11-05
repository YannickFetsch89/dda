"""
bookingkit.py – DiesDasDüsseldorf
Gemeinsamer Baustein für Anbieter, die ihre Termine über bookingkit verkaufen
(viele Stadtführungen, Touren, Workshops).

Bookingkit-Widgets laden ihre Inhalte als JSONP („BookingKitApp.insertBkContent({"html": …})“)
von https://<cluster>.bookingkit.de/onPage/… – laut robots.txt von bookingkit ist /onPage/
ausdrücklich erlaubt. Darin steckt schema.org-JSON-LD mit allen Terminen:

  1. /onPage/calendar?v=<vendor>&month=M&year=Y
       → Kalender eines Monats; jeder Tag mit Terminen verlinkt auf
         /onPage/eventsByDate/?cw=<widget>&date=YYYY-MM-DD
  2. /onPage/eventsByDate/?…&date=…
       → alle Termine des Tages als JSON-LD (@type Event: name, startDate, offers.price,
         offers.availability, image, location → @id eines TouristAttraction mit Adresse)
  3. /onPage/detail?e=<event_id>&v=<vendor>
       → Tourbeschreibung (div.bk-detail-desc)

Die Vendor-ID steht im Quelltext der Anbieterseite (Skript *.widget.bookingkit.net/bkscript/…
oder Widerruf-Link selfservice.bookingkit.com/vendor/<vendor>/…).

Erstellt: 2026-11-05
"""
import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from scraper.utils.http_client import STANDARD_HEADERS

WARTEZEIT = 2.0  # Sekunden zwischen zwei Anfragen (Scraping-Regel)
MAX_VERSUCHE = 3


@dataclass
class BookingkitTermin:
    """Ein buchbarer Termin aus dem bookingkit-Kalender."""

    event_id: str          # Tour-ID bei bookingkit (gleich für alle Termine einer Tour)
    titel: str             # Tourname ohne angehängte Uhrzeit/Datum
    start: datetime        # Beginn mit Zeitzone
    preis: Optional[float]
    ausgebucht: bool
    bild_url: Optional[str]
    adresse: Optional[str]  # Treffpunkt laut bookingkit, z.B. "Immermannstraße 41, 40210 Düsseldorf, Deutschland"


def _jsonp_html(text: str) -> Optional[str]:
    """
    Holt das HTML aus einer JSONP-Antwort „BookingKitApp.insertBkContent({...})“.
    Bevorzugt das Argument von insertBkContent; sonst das erste parsebare Objekt mit "html".
    """
    aufruf = text.find("insertBkContent(")
    anfaenge = [aufruf + len("insertBkContent(")] if aufruf != -1 else []
    anfaenge += [i for i, z in enumerate(text) if z == "{"][:20]
    decoder = json.JSONDecoder()
    for anfang in anfaenge:
        if anfang >= len(text) or text[anfang] != "{":
            continue
        try:
            daten, _ende = decoder.raw_decode(text, anfang)
        except json.JSONDecodeError:
            continue
        if isinstance(daten, dict) and isinstance(daten.get("html"), str):
            return daten["html"]
    return None


def _json_ld(soup: BeautifulSoup) -> list[dict]:
    """Alle Objekte aus den JSON-LD-Blöcken (@graph aufgelöst)."""
    objekte: list[dict] = []
    for skript in soup.find_all("script", type="application/ld+json"):
        try:
            daten = json.loads(skript.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(daten, dict) and isinstance(daten.get("@graph"), list):
            objekte += [o for o in daten["@graph"] if isinstance(o, dict)]
        elif isinstance(daten, dict):
            objekte.append(daten)
    return objekte


class BookingkitClient:
    """Liest Termine eines bookingkit-Anbieters (mit Rate Limiting und Backoff bei 429)."""

    def __init__(self, vendor: str, logger: logging.Logger, basis: str = "https://eu5.bookingkit.de"):
        self.vendor = vendor
        self.basis = basis.rstrip("/")
        self.logger = logger
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "BookingkitClient":
        self._client = httpx.AsyncClient(headers=STANDARD_HEADERS, timeout=30, follow_redirects=True)
        return self

    async def __aexit__(self, *_args) -> None:
        if self._client:
            await self._client.aclose()

    async def _html(self, pfad_oder_url: str) -> Optional[str]:
        """Ruft einen /onPage/-Endpunkt ab und gibt das enthaltene HTML zurück."""
        url = pfad_oder_url
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = self.basis + url
        for versuch in range(MAX_VERSUCHE):
            await asyncio.sleep(WARTEZEIT * (2 ** versuch if versuch else 1))
            try:
                antwort = await self._client.get(url)
                if antwort.status_code == 429:
                    self.logger.warning("bookingkit: 429 (zu viele Anfragen) – warte und versuche erneut")
                    continue
                antwort.raise_for_status()
                return _jsonp_html(antwort.text)
            except httpx.HTTPStatusError as fehler:
                self.logger.error("bookingkit: HTTP %s bei %s", fehler.response.status_code, url)
                return None
            except httpx.HTTPError as fehler:
                self.logger.warning("bookingkit: Netzwerkfehler bei %s (%s)", url, fehler)
        return None

    async def tage_mit_terminen(self, monate: list[tuple[int, int]]) -> list[tuple[date, str]]:
        """Liefert (Datum, eventsByDate-URL) für alle Tage mit Terminen in den angegebenen (Jahr, Monat)."""
        tage: dict[date, str] = {}
        for jahr, monat in monate:
            html = await self._html(f"/onPage/calendar?v={self.vendor}&month={monat}&year={jahr}")
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            for link in soup.select('a[data-href*="eventsByDate"]'):
                url = link.get("data-href", "")
                treffer = re.search(r"[?&]date=(\d{4}-\d{2}-\d{2})", url)
                if treffer:
                    tage.setdefault(date.fromisoformat(treffer.group(1)), url.replace("&amp;", "&"))
        return sorted(tage.items())

    async def termine_am_tag(self, url: str) -> list[BookingkitTermin]:
        """Alle Termine eines Tages aus dem JSON-LD der Tagesliste."""
        html = await self._html(url)
        if not html:
            return []
        objekte = _json_ld(BeautifulSoup(html, "html.parser"))
        # Adresse kann ein Objekt (PostalAddress) oder schon ein Text sein
        adressen: dict = {}
        for o in objekte:
            if o.get("@type") == "Event":
                continue
            adresse = o.get("address")
            if isinstance(adresse, dict):
                adressen[o.get("@id")] = adresse.get("streetAddress")
            elif isinstance(adresse, str):
                adressen[o.get("@id")] = adresse
        termine: list[BookingkitTermin] = []
        for o in objekte:
            if o.get("@type") != "Event" or not o.get("startDate"):
                continue
            try:
                start = datetime.fromisoformat(o["startDate"])
            except ValueError:
                continue
            # @id = "<event_id>-YYYY-MM-DD-HH-MM-SS"
            event_id = str(o.get("@id", "")).split("-")[0]
            # Name endet auf " | HH:MM DD.MM.YYYY" – das gehört nicht in den Titel
            titel = re.sub(r"\s*\|\s*\d{1,2}:\d{2}\s+\d{2}\.\d{2}\.\d{4}\s*$", "", o.get("name", "")).strip()
            angebot = o.get("offers") or {}
            try:
                preis = float(angebot["price"]) if angebot.get("price") not in (None, "") else None
            except (TypeError, ValueError):
                preis = None
            ort = o.get("location") or {}
            termine.append(BookingkitTermin(
                event_id=event_id,
                titel=titel,
                start=start,
                preis=preis,
                ausgebucht=str(angebot.get("availability", "")).endswith(("OutOfStock", "SoldOut")),
                bild_url=o.get("image") if isinstance(o.get("image"), str) else None,
                adresse=adressen.get(ort.get("@id")) if isinstance(ort, dict) else None,
            ))
        return termine

    async def beschreibung(self, event_id: str) -> Optional[str]:
        """Beschreibungstext einer Tour (erster Absatz-Block, ohne Listen und Zwischenüberschriften)."""
        html = await self._html(f"/onPage/detail?e={event_id}&v={self.vendor}")
        if not html:
            return None
        block = BeautifulSoup(html, "html.parser").select_one(".bk-detail-desc")
        if not block:
            return None
        for weg in block.select("ul, ol, h3, script, style"):
            weg.decompose()
        # Überschriften enden ohne Satzzeichen – sonst kleben sie am folgenden Satz
        for ueberschrift in block.select("h1, h2, h4, h5, h6"):
            text = re.sub(r"\s+", " ", ueberschrift.get_text(" ")).strip()
            ueberschrift.string = text if not text or text[-1] in ".!?:“\"" else f"{text}."
        return re.sub(r"\s+", " ", block.get_text(" ")).strip() or None
