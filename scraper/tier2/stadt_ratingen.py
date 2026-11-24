"""
stadt_ratingen.py – DiesDasDüsseldorf
Scraper für den Veranstaltungskalender der Stadt Ratingen (Stadttheater, Museum, Medienzentrum, Vereine …).
URL: https://www.stadt-ratingen.de/veranstaltungskalender (TYPO3, Erweiterung „citko events3“)
(Plan docs/plan-quellen-ausbau-2026-11-23.md, Schritt V1, Welle A).

robots.txt (geprüft am 24.11.2026): „User-agent: * / Disallow: /typo3/ / Disallow: /typo3_src/ / Crawl-delay: 10“ –
der Kalender ist erlaubt. Wir warten deshalb 10 s zwischen den Anfragen (WARTEZEIT).

Aufbau der Seite:
- Die Liste zeigt 10 Veranstaltungen (Reihen) je Seite, sortiert nach dem nächsten Termin; jede Reihe enthält alle
  Termine (Datum „TT.MM.JJ“, meist mit Uhrzeit „16:00 - 18:00 Uhr“), den Ortsnamen mit Stadt („… in Ratingen“),
  den Veranstalter und ein Bild. Die nächste Seite steht in der Seitennavigation (Link mit cHash).
- Die Adresse steht nur auf der Detailseite (Block „Veranstaltungsort“, Absatz nach „Adresse“). Wir laden höchstens
  MAX_DETAILSEITEN Detailseiten je Lauf, und zwar je Ortsname nur eine (die Adresse gilt für alle Reihen dort);
  Orte mit den meisten Terminen zuerst. Orte ohne geladene Detailseite bekommen adresse None (die Pipeline ergänzt
  Adressen gleicher Orte, pipeline/adressen_ergaenzen.py).
- Eine Rubrik zeigt die Seite je Termin nicht an (nur als Filter im Suchformular, das per POST arbeitet). Die
  Kategorie wird deshalb über Stichwörter in Titel, Untertitel und Ort bestimmt, sonst „sonstiges“.
- Ausgelassen: Termine außerhalb von Ratingen, Wochenmärkte (Daueranlass mit Marktzeiten, kein Einzeltermin),
  Sprechstunden, „Lange Öffnung“, Ausstellungen mit vielen Öffnungstagen und Termine ohne echten Ort
  („Veranstaltungsort folgt“).

Erstellt: 2026-11-24
"""
import json
import logging
import re
from collections import Counter
from datetime import date
from typing import Optional
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ticket_link import ticket_link_haus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Stadt Ratingen Veranstaltungskalender"
BASIS_URL = "https://www.stadt-ratingen.de"
LISTE_URL = "https://www.stadt-ratingen.de/veranstaltungskalender"

WARTEZEIT = 10.0          # Crawl-delay laut robots.txt
MAX_LISTENSEITEN = 12     # derzeit 9 Seiten à 10 Reihen
MAX_DETAILSEITEN = 15

# Keine Einzeltermine: regelmäßige Märkte, Sprechstunden, Öffnungszeiten („Lange Öffnung …“)
_AUSLASSEN = re.compile(r"wochenmarkt|sprechstunde|öffnungszeit|lange öffnung", re.I)
# Platzhalter statt Ortsname („Veranstaltungsort folgt“) – ohne echten Ort kein Event
_ORT_PLATZHALTER = re.compile(r"\bfolgt\b|noch offen|wird bekannt|^n\.?\s?n\.?$", re.I)
# Ausstellungen mit vielen Öffnungstagen gelten als Dauerausstellung
_AUSSTELLUNG = re.compile(r"ausstellung", re.I)
MAX_TERMINE_AUSSTELLUNG = 10
_ABGESAGT = re.compile(r"\b(abgesagt|entfällt|fällt aus)\b", re.I)

# Stichwörter → Kategorie (Reihenfolge entscheidet; geprüft auf Titel + Untertitel)
_KATEGORIE_REGELN = [
    ("family", re.compile(r"kinder|kids|famili|jugendlich|eltern|kita\b|schüler|ferien|kasper|märchen", re.I)),
    ("food", re.compile(r"weihnachtsmarkt|bauernmarkt|adventsmarkt|street ?food|verkostung|tasting|kulinar|"
                        r"\bmarkt\b|wein|brunch|kochen", re.I)),
    ("musik", re.compile(r"konzert|musik|chor\b|chöre|orchester|jazz|band\b|lieder|sinfoni|symphon|"
                         r"gitarre|klavier|piano|singen|\bduo\b|\btrio\b|quartett|quintett", re.I)),
    ("kultur", re.compile(r"führung|lesung|vortrag|theater|kabarett|comedy|musical|schauspiel|ausstellung|"
                          r"museum|film|kino|literatur|autor|vernissage|finissage|oper|ballett|tanz|"
                          r"komödie|krimi|poetry|bühne|kom\(m\)ödchen", re.I)),
    ("community", re.compile(r"workshop|kurs\b|kurse|treff|werkstatt|schnupper|repair|upcycling|stammtisch|"
                             r"seminar|sprachcafé|café|mitmach|ehrenamt", re.I)),
    ("outdoor", re.compile(r"wanderung|spaziergang|radtour|natur|garten|exkursion|führung im wald", re.I)),
    ("sport", re.compile(r"(?<!ver)lauf\b|läufe|sport|turnier|fitness|yoga|schwimm", re.I)),
    ("nightlife", re.compile(r"party|disco|tanz in den mai|ü\d0", re.I)),
]
# Rückfall über den Ort (z. B. „Stadttheater“, „Museum Ratingen“)
_ORT_KULTUR = re.compile(r"theater|museum|galerie|bühne", re.I)

_TERMIN = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})(?:\s+(\d{1,2}):(\d{2}))?")


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el else ""


def _termine(block) -> list[tuple[str, Optional[str]]]:
    """Alle (datum, uhrzeit) aus dem Terminblock einer Reihe; Endzeit („- 18:00 Uhr“) wird ignoriert."""
    if not block:
        return []
    text = _text(block)
    termine: list[tuple[str, Optional[str]]] = []
    for m in _TERMIN.finditer(text):
        tag, monat, jahr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if jahr < 100:
            jahr += 2000
        try:
            datum = date(jahr, monat, tag).isoformat()
        except ValueError:
            continue
        uhrzeit = None
        if m.group(4):
            stunde, minute = int(m.group(4)), int(m.group(5))
            if 0 <= stunde <= 23 and 0 <= minute <= 59:
                uhrzeit = f"{stunde:02d}:{minute:02d}"
        if (datum, uhrzeit) not in termine:
            termine.append((datum, uhrzeit))
    return termine


def _ort_und_stadt(text: str) -> tuple[str, Optional[str]]:
    """„Marktplatz Innenstadt in Ratingen“ → ("Marktplatz Innenstadt", "Ratingen")."""
    m = re.match(r"^(.*?)\s+in\s+(\S[^,]*)$", text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return text.strip(), None


def _bild(el) -> Optional[str]:
    img = el.select_one(".event-image img") if el else None
    src = (img.get("src") or img.get("data-src")) if img else None
    if not src or src.startswith("data:"):
        return None
    return quote(urljoin(BASIS_URL, src), safe=":/?&=%#.,-_~+")


def _reihen_aus_liste(html: str) -> tuple[list[dict], Optional[str]]:
    """Reihen (Veranstaltungen mit allen Terminen) aus einer Listenseite und die URL der nächsten Seite."""
    soup = BeautifulSoup(html, "html.parser")
    reihen: list[dict] = []
    for zeile in soup.select("div.event-list-row"):
        titel_el = zeile.select_one(".event-title h4") or zeile.select_one("h4")
        titel = _text(titel_el)
        if not titel:
            continue
        link = zeile.select_one(".event-title a[href]") or zeile.select_one("a[href*='veranstaltung-details']")
        url = urljoin(BASIS_URL, link["href"]) if link else LISTE_URL
        ort_el = zeile.select_one("div.event-location div.event-location") or zeile.select_one("div.event-location")
        ort, stadt = _ort_und_stadt(_text(ort_el))
        reihen.append({
            "titel": titel,
            "untertitel": _text(zeile.select_one(".event-subtitle")),
            "termine": _termine(zeile.select_one(".event-nextterm")),
            "ort": ort,
            "stadt": stadt,
            "veranstalter": _text(zeile.select_one(".event-organiser")),
            "url": url,
            "bild_url": _bild(zeile),
        })
    naechste = None
    aktiv = soup.select_one(".citko-event-pagination li.page-item.active")
    if aktiv:
        folgende = aktiv.find_next_sibling("li")
        a = folgende.select_one("a[href]") if folgende else None
        if a and "disabled" not in (folgende.get("class") or []):
            naechste = urljoin(BASIS_URL, a["href"])
    return reihen, naechste


def _details_aus_html(html: str) -> dict:
    """Adresse und Preis aus einer Detailseite: {"ort", "adresse", "preis"} (Werte ggf. None)."""
    soup = BeautifulSoup(html, "html.parser")
    ergebnis = {"ort": None, "adresse": None, "preis": None, "ticket_url": None}
    # Ticket-Link der Detailseite (Plan 5.5.2, P1): die Stadt kennzeichnet ihn selbst mit a.event-ticketlink
    ticket = soup.select_one("a.event-ticketlink[href]")
    if ticket:
        href = ticket["href"].strip()
        ergebnis["ticket_url"] = ticket_link_haus(href)
    block = soup.select_one(".event-location")
    if block:
        ergebnis["ort"] = _text(block.select_one("h3")) or None
        for strong in block.select("strong"):
            if _text(strong).lower().startswith("adresse"):
                p = strong.find_next_sibling("p")
                if p:
                    teile = [re.sub(r"\s+", " ", t).strip() for t in p.stripped_strings]
                    teile = [t for t in teile if t]
                    if teile:
                        ergebnis["adresse"] = ", ".join(teile)
                break
    preise = []
    for tr in soup.select(".event-price-text tr"):
        th, td = _text(tr.find("th")), _text(tr.find("td"))
        if th and td:
            preise.append(f"{th}: {td}")
        elif td or th:
            preise.append(td or th)
    if preise:
        preis = "; ".join(preise)
        if re.search(r"(?i)\b(kostenlos|eintritt frei|freier eintritt)\b", preis) or re.fullmatch(
                r"(?i)[^0-9]*0,00\s*€", preis):
            preis = "kostenlos"
        ergebnis["preis"] = preis[:120]
    return ergebnis


def _kategorie(reihe: dict) -> str:
    text = f"{reihe['titel']} {reihe.get('untertitel') or ''}"
    for kategorie, muster in _KATEGORIE_REGELN:
        if muster.search(text):
            return kategorie
    if _ORT_KULTUR.search(reihe.get("ort") or ""):
        return "kultur"
    return "sonstiges"


def _reihe_auslassen(reihe: dict, termine_im_fenster: int) -> Optional[str]:
    """Grund, warum eine Reihe nicht übernommen wird – oder None."""
    if not reihe.get("stadt") or "ratingen" not in reihe["stadt"].lower():
        return f"nicht in Ratingen ({reihe.get('stadt') or 'ohne Stadt'})"
    if not reihe.get("ort") or _ORT_PLATZHALTER.search(reihe["ort"]):
        return f"kein Ort ({reihe.get('ort') or 'leer'})"
    text = f"{reihe['titel']} {reihe.get('untertitel') or ''}"
    if _AUSLASSEN.search(text):
        return "kein Einzeltermin"
    if _ABGESAGT.search(text):
        return "abgesagt"
    if _AUSSTELLUNG.search(text) and termine_im_fenster > MAX_TERMINE_AUSSTELLUNG:
        return "Ausstellung mit Öffnungstagen"
    return None


def _termine_aus_reihen(reihen: list[dict], heute: date, enddatum: date,
                        details: Optional[dict[str, dict]] = None) -> list[dict]:
    """Reihen → Event-Dicts (ein Event je Termin im Zeitfenster). details: Ortsname → Detaildaten."""
    details = details or {}
    events: list[dict] = []
    gesehen: set[tuple] = set()
    for reihe in reihen:
        termine = [(d, u) for d, u in reihe["termine"] if heute <= date.fromisoformat(d) <= enddatum]
        if not termine:
            continue
        grund = _reihe_auslassen(reihe, len(termine))
        if grund:
            logger.debug("Ratingen: „%s“ ausgelassen – %s", reihe["titel"], grund)
            continue
        ort = reihe["ort"]
        detail = details.get(ort) or {}
        passend = detail.get("url") == reihe["url"]
        preis = detail.get("preis") if passend else None
        ticket_url = detail.get("ticket_url") if passend else None
        kategorie = _kategorie(reihe)
        for datum, uhrzeit in termine:
            schluessel = (reihe["titel"].lower(), datum, uhrzeit)
            if schluessel in gesehen:
                continue
            gesehen.add(schluessel)
            events.append({
                "titel": reihe["titel"],
                "datum": datum,
                "uhrzeit": uhrzeit,
                "ort": ort,
                "adresse": detail.get("adresse"),
                "kategorie": kategorie,
                "beschreibung": None,
                "preis": preis,
                "quelle_name": QUELLE_NAME,
                "quelle_url": reihe["url"],
                "ticket_url": ticket_url,
                "bild_url": reihe.get("bild_url"),
                "bild_generiert": False,
                "status": "neu",
            })
    return events


def _termine_aus_html(html: str, heute: date, enddatum: date,
                      details: Optional[dict[str, dict]] = None) -> list[dict]:
    """Eine Listenseite direkt in Event-Dicts umwandeln (für Tests ohne Netz)."""
    reihen, _ = _reihen_aus_liste(html)
    return _termine_aus_reihen(reihen, heute, enddatum, details)


def _detail_kandidaten(reihen: list[dict], heute: date, enddatum: date) -> list[tuple[str, str]]:
    """(Ortsname, Detail-URL) je Ort, Orte mit den meisten Terminen im Fenster zuerst."""
    zaehler: Counter = Counter()
    erste_url: dict[str, str] = {}
    for reihe in reihen:
        n = sum(1 for d, _ in reihe["termine"] if heute <= date.fromisoformat(d) <= enddatum)
        if not n or _reihe_auslassen(reihe, n) or not reihe["ort"]:
            continue
        zaehler[reihe["ort"]] += n
        erste_url.setdefault(reihe["ort"], reihe["url"])
    return [(ort, erste_url[ort]) for ort, _ in zaehler.most_common() if erste_url[ort] != LISTE_URL]


def scrape() -> list[dict]:
    """Scrapt den Veranstaltungskalender der Stadt Ratingen."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        reihen: list[dict] = []
        url: Optional[str] = LISTE_URL
        seiten = 0
        while url and seiten < MAX_LISTENSEITEN:
            html = seite_abrufen(url, logger, wartezeit=WARTEZEIT)
            seiten += 1
            if html is None:
                if seiten == 1:
                    logger.error("Scraper %s: Kalender nicht erreichbar", QUELLE_NAME)
                    return []
                break
            neue, url = _reihen_aus_liste(html)
            reihen.extend(neue)
            # Liste ist nach dem nächsten Termin sortiert: beginnt jede Reihe erst nach dem Fenster, ist Schluss
            if neue and all(r["termine"] and min(d for d, _ in r["termine"]) > enddatum.isoformat() for r in neue):
                break
        logger.info("Ratingen: %d Reihen auf %d Listenseiten", len(reihen), seiten)

        details: dict[str, dict] = {}
        for ort, detail_url in _detail_kandidaten(reihen, heute, enddatum)[:MAX_DETAILSEITEN]:
            html = seite_abrufen(detail_url, logger, wartezeit=WARTEZEIT)
            if html is None:
                continue
            try:
                detail = _details_aus_html(html)
            except Exception as fehler:
                logger.warning("Ratingen: Detailseite nicht lesbar (%s): %s", detail_url, fehler)
                continue
            detail["url"] = detail_url
            details[ort] = detail

        events = _termine_aus_reihen(reihen, heute, enddatum, details)
        if not events:
            logger.warning("Scraper %s: 0 Termine bei erreichbarer Seite – Seitenstruktur geändert?", QUELLE_NAME)
        ohne_adresse = sum(1 for e in events if not e["adresse"])
        logger.info("Scraper %s fertig: %d Events gefunden (%d ohne Adresse, %d Detailseiten)",
                    QUELLE_NAME, len(events), ohne_adresse, len(details))
        return events
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Events gefunden ===\n")
    for ev in ergebnisse[:3]:
        print(json.dumps(ev, ensure_ascii=False, indent=2))
