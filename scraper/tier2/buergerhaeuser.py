"""
buergerhaeuser.py – DiesDasDüsseldorf
Scraper für die städtischen Bürgerhäuser Düsseldorf (Quellen-Ausbau, Schritt V2, Welle C).
Übersicht: https://www.duesseldorf.de/buergerhaeuser

Die Stadt pflegt die Programme der Bürgerhäuser als TYPO3-Seiten unter duesseldorf.de. Nur vier Häuser haben eine
Programmseite mit datierten Terminen (Stand 25.11.2026):
  - Bürgerhaus Reisholz      /buergerhaeuser/reisholz/veranstaltungen
  - Bürgerhaus Bilk          /buergerhaeuser/bilk-stadtteilzentrum/veranstaltungen
  - Bürgerhaus Salzmannbau   /buergerhaeuser/salzmannbau/veranstaltungen
  - Kulturhaus Süd / Freizeitstätte Garath  /buergerhaeuser/kulturhaus-sued/programm und …/kindertheater
Benrath, Eller, Gerresheim und Wersten haben keine Veranstaltungsseite (/veranstaltungen → 404, Hauptseiten ohne
Termine; Benrath nur „Angebote und Kurse“). Baukinderkultur ist kein Haus mit eigenem Programm.

Die Seiten haben drei Vorlagen, das Modul erkennt sie am Inhalt:
  A) Monatsprogramm (Reisholz): h2 = Monat, h3 = „Wochentag, T.M.JJJJ | Uhrzeit | Eintritt“, danach <p><strong>Titel.
     Die weiteren Akkordeon-Reiter (JazzBar, Kinder, Märkte …) wiederholen Termine – nur die Monatsreiter zählen.
  B) Ein Akkordeon-Reiter je Veranstaltung/Reihe (Bilk, Salzmannbau): Titel im Reiter, Termine als Textzeilen
     („Sonntag, 29.11.2026 | 15 bis 18 Uhr | …“ oder Listen „5.3., 11.6. und 26.11.2027, 14 bis 18 Uhr“).
  C) Programmliste (Kulturhaus Süd): h3 = Titel, darunter <li>„Wochentag, T.M.JJJJ | 20 Uhr | 19 Euro“.
Wöchentliche Kurse/Proben ohne eigenes Datum („Montags, …“, „Dienstag | 15 bis 17 Uhr“), Dauerausstellungen
(„noch bis …“) und Gremiensitzungen/Sprechstunden werden weggelassen.

robots.txt geprüft am 2026-11-25 (www.duesseldorf.de): gesperrt sind nur „/*?tx_*“, „/*?cHash*“, „/typo3/“ und
„/typo3conf/“ – die Programmseiten (ohne Parameter) sind erlaubt. Kein Crawl-delay; wir warten 2,5 s je Abruf.

Kategorie nach Titel (Reihenname eingeschlossen): Märkte/Börsen/Tausch → community, Kinder-/Figurentheater/Familie →
family, Konzert/Jazz/Band/Sessions/Chor → musik, Theater/Lesung/Ausstellung/Kabarett/Film → kultur, Café/Treff/Party/
Senioren/Stadtteil → community; sonst nach Beschreibungstext (Musik gegen Kultur), sonst kultur. Die Kindertheater-Seite
des Kulturhauses Süd ist immer family.

Erstellt: 2026-11-25 (Quellen-Ausbau, Schritt V2, Welle C)
"""
import logging
import re
import unicodedata
from datetime import date
from typing import Optional

from bs4 import BeautifulSoup, NavigableString, Tag

from config import vorschau_ende
from scraper.utils.http_client import seite_abrufen
from scraper.utils.ticket_link import ticket_link_aus

logger = logging.getLogger(__name__)

QUELLE_NAME = "Bürgerhäuser Düsseldorf"
BASIS = "https://www.duesseldorf.de/buergerhaeuser/"
WARTEZEIT_S = 2.5

# Je Haus: Ort exakt wie in der Ortstabelle, Adresse, Programmseiten (URL, erzwungene Kategorie oder None)
HAEUSER: list[dict] = [
    {
        "ort": "Bürgerhaus Reisholz",
        "adresse": "Kappeler Str. 231, 40599 Düsseldorf",
        "seiten": [(BASIS + "reisholz/veranstaltungen", None)],
    },
    {
        "ort": "Bürgerhaus Bilk",
        "adresse": "Bachstraße 145, 40217 Düsseldorf",
        "seiten": [(BASIS + "bilk-stadtteilzentrum/veranstaltungen", None)],
    },
    {
        "ort": "Bürgerhaus Salzmannbau",
        "adresse": "Himmelgeister Str. 107h, 40225 Düsseldorf",
        "seiten": [(BASIS + "salzmannbau/veranstaltungen", None)],
    },
    {
        "ort": "Kulturhaus Süd / Freizeitstätte Garath",
        "adresse": "Fritz-Erler-Straße 21, 40595 Düsseldorf",
        "seiten": [
            (BASIS + "kulturhaus-sued/programm", None),
            (BASIS + "kulturhaus-sued/kindertheater", "family"),
        ],
    },
]

_WOCHENTAG = r"(?:Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag)"
# „Donnerstag, 26.11.2026“ am Anfang einer Überschrift/Zeile
_TAG_ANFANG = re.compile(rf"^\s*{_WOCHENTAG},?\s+(\d{{1,2}})\.(\d{{1,2}})\.(\d{{4}})")
# Datum oder Datumsliste mit Jahr am Ende: „5.3., 11.6. und 26.11.2027“ / „27.11.2026“
_DATUMSLISTE = re.compile(r"((?:\d{1,2}\.\d{1,2}\.,?\s*(?:und\s+)?)*)(?<!\d)(\d{1,2})\.(\d{1,2})\.(\d{4})")
_TAG_MONAT = re.compile(r"(\d{1,2})\.(\d{1,2})\.")
_MONATSKOPF = re.compile(
    r"^(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s+\d{4}$|^Vorschau$",
    re.I,
)
# Beginn: erste Zahl vor „Uhr“, „bis“, „und“ oder Strich (Einlass-Angaben werden vorher entfernt)
_ZEIT = re.compile(r"(?<![\d.,/])(\d{1,2})(?:[.:](\d{2}))?(?=\s*(?:Uhr|bis\b|und\b|–|-\s*\d))", re.I)
_EINLASS = re.compile(r"\(?\s*Einlass[^|)]*\)?", re.I)
_RAUM = re.compile(r"foyer|raum\b|saal|etage|café|cafe\b|garten|^im\s|^in\s", re.I)
_PREIS = re.compile(r"euro|€|\bfrei\b|kostenlos|kostenfrei", re.I)
_WEGLASSEN = re.compile(r"sitzung|sprechstunde", re.I)

# Kategorie-Stichwörter (Reihenfolge der Prüfung siehe _kategorie)
_K_MARKT = re.compile(r"trödel|flohmarkt|\bmarkt\b|börse|tausch", re.I)
_K_FAMILIE = re.compile(r"kinder|figurentheater|puppen|märchen|famili|haste töne", re.I)
_K_MUSIK = re.compile(
    r"konzert|jazz|\bband\b|session|\bchor\b|chöre|tribute|trommel|spotlight|soul|country|gospel|orchester|"
    r"quartett|quintett|\btrio\b|lieder|singer|musik",
    re.I,
)
_K_KULTUR = re.compile(
    r"theater|lesung|ausstellung|kabarett|comedy|\bfilm|kino|hörspiel|buch|literatur|revue|stage|slam|vortrag|"
    r"satire|kleinkunst",
    re.I,
)
_K_TREFF = re.compile(r"café|cafe|treff|party|frühstück|senior|60 plus|stadtteil|labor|fest\b|weihnachtsbaum", re.I)
_T_MUSIK = re.compile(r"konzert\w*|\bband\b|musiker\w*|lieder|songs?\b|\balbum|\brock|jazz|groove|\bsingen", re.I)
_T_KULTUR = re.compile(r"kabarett\w*|satire|comedy|\blesung|theater|programm der|ausstellung|\bfilm", re.I)


def _text(el) -> str:
    """Text eines Elements, Leerraum zusammengefasst, Umlaute als NFC (die Stadtseiten liefern teils u + Trema)."""
    if el is None:
        return ""
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip())


def _zeilen(el) -> list[str]:
    """Textzeilen eines Elements; <br> trennt Zeilen (ändert eine Kopie, nicht den Baum)."""
    kopie = BeautifulSoup(str(el), "html.parser")
    for br in kopie.find_all("br"):
        br.replace_with(NavigableString("\n"))
    roh = unicodedata.normalize("NFC", kopie.get_text(" "))
    return [z for z in (re.sub(r"\s+", " ", t).strip() for t in roh.split("\n")) if z]


def _titel_glaetten(titel: str) -> str:
    """„SPOTLIGHT | Frair, sidneyy“ → „SPOTLIGHT: Frair, sidneyy“; weitere Trenner → Gedankenstrich."""
    teile = [t.strip() for t in titel.split("|") if t.strip()]
    if not teile:
        return titel.strip()
    if len(teile) == 1:
        return teile[0]
    if ":" in titel:
        return " – ".join(teile)
    return f"{teile[0]}: " + " – ".join(teile[1:])


def _kern(titel: str) -> str:
    """Titelkern für den Abgleich doppelter Termine (Teil nach dem letzten Reihen-Trenner)."""
    letzter = re.split(r"\s\|\s|:\s|\s–\s", titel)[-1]
    return re.sub(r"[^a-z0-9äöüß]", "", letzter.lower())


def _uhrzeit(text: str) -> Optional[str]:
    """Beginn aus „20 bis 22 Uhr | Einlass: 19.30 Uhr“ → „20:00“; Einlass zählt nicht."""
    if not text:
        return None
    beginn = re.search(r"Beginn\D{0,10}(\d{1,2})(?:[.:](\d{2}))?", text, re.I)
    if beginn:
        treffer = beginn
    else:
        treffer = _ZEIT.search(_EINLASS.sub(" ", text))
    if not treffer:
        return None
    stunde, minute = int(treffer.group(1)), int(treffer.group(2) or 0)
    if 0 <= stunde <= 23 and 0 <= minute <= 59:
        return f"{stunde:02d}:{minute:02d}"
    return None


def _preis(teil: str) -> Optional[str]:
    """„Eintritt frei“ → „kostenlos“, „Eintritt: 3,50/3 Euro“ → „3,50/3 €“."""
    teil = teil.strip()
    if not teil or not _PREIS.search(teil):
        return None
    if not re.search(r"\d", teil) and re.search(r"\bfrei\b|kostenlos|kostenfrei", teil, re.I):
        return "kostenlos"
    if not re.search(r"\d", teil):
        return None
    ohne = re.sub(r"^(?:Eintritt|Teilnahme(?:gebühr)?|Preis|Karten)\s*:?\s*", "", teil, flags=re.I)
    return re.sub(r"\s*Euro\b", " €", ohne).strip() or None


def _preis_aus(teile: list[str]) -> Optional[str]:
    for teil in teile:
        if re.search(r"einlass|jahren?\b", teil, re.I) and not re.search(r"euro|€", teil, re.I):
            continue
        preis = _preis(teil)
        if preis:
            return preis
    return None


def _kategorie(titel: str, text: str, erzwungen: Optional[str] = None) -> str:
    """Kategorie nach Titel (mit Reihenname), sonst nach Beschreibung; siehe Modulkopf."""
    if erzwungen:
        return erzwungen
    if _K_MARKT.search(titel):
        return "community"
    if _K_FAMILIE.search(titel):
        return "family"
    if _K_MUSIK.search(titel):
        return "musik"
    if _K_KULTUR.search(titel):
        return "kultur"
    if _K_TREFF.search(titel):
        return "community"
    musik, kultur = len(_T_MUSIK.findall(text or "")), len(_T_KULTUR.findall(text or ""))
    if musik > kultur:
        return "musik"
    return "kultur"


def _datum(tag: int, monat: int, jahr: int) -> Optional[date]:
    try:
        return date(jahr, monat, tag)
    except ValueError:
        return None


def _daten_aus_zeile(zeile: str) -> tuple[list[date], str]:
    """Alle Daten einer Zeile (auch Listen „5.3., 11.6. und 26.11.2027“) und der Rest der Zeile ohne Daten."""
    daten: list[date] = []
    for treffer in _DATUMSLISTE.finditer(zeile):
        jahr = int(treffer.group(4))
        for t, m in _TAG_MONAT.findall(treffer.group(1) or ""):
            d = _datum(int(t), int(m), jahr)
            if d:
                daten.append(d)
        d = _datum(int(treffer.group(2)), int(treffer.group(3)), jahr)
        if d:
            daten.append(d)
    rest = _DATUMSLISTE.sub(" ", zeile)
    rest = re.sub(rf"^\s*{_WOCHENTAG}s?,?\s*", "", rest)
    return daten, rest


def _event(haus: dict, url: str, titel: str, tag: date, uhrzeit: Optional[str], preis: Optional[str],
           kategorie: str, ticket_url: Optional[str]) -> dict:
    return {
        "titel": titel,
        "datum": tag.isoformat(),
        "uhrzeit": uhrzeit,
        "ort": haus["ort"],
        "adresse": haus["adresse"],
        "kategorie": kategorie,
        "beschreibung": None,
        "preis": preis,
        "quelle_name": QUELLE_NAME,
        "quelle_url": url,
        "ticket_url": ticket_url,
        "bild_url": None,
        "bild_generiert": False,
        "status": "neu",
    }


def _geschwister_bis(start: Tag, stopp: tuple[str, ...]) -> list[Tag]:
    """Folgende Geschwister-Elemente bis zur nächsten Überschrift aus stopp."""
    ergebnis = []
    for sib in start.next_siblings:
        if isinstance(sib, Tag):
            if sib.name in stopp:
                break
            ergebnis.append(sib)
    return ergebnis


def _ticket(elemente: list[Tag], url: str) -> Optional[str]:
    for el in elemente:
        if el.name == "a" and el.get("href"):
            treffer = ticket_link_aus(BeautifulSoup(str(el), "html.parser"), url)
        else:
            treffer = ticket_link_aus(el, url)
        if treffer:
            return treffer
    return None


# --- Vorlage A: Monatsprogramm (h3 = „Wochentag, Datum | Uhrzeit | Eintritt“) --------------------------------

def _vorlage_a(soup: BeautifulSoup, haus: dict, url: str, erzwungen: Optional[str]) -> list[tuple]:
    monatskoepfe = [h for h in soup.find_all("h2") if _MONATSKOPF.match(_text(h))]
    bereiche: list[Tag] = []
    for kopf in monatskoepfe:
        if kopf.parent not in bereiche:
            bereiche.append(kopf.parent)
    if not bereiche:
        bereiche = [soup]
    termine = []
    for bereich in bereiche:
        for h3 in bereich.find_all("h3"):
            kopf = _text(h3)
            anfang = _TAG_ANFANG.match(kopf)
            if not anfang:
                continue  # „Montags, …“ (Kurs), „noch bis …“ (Ausstellung)
            tag = _datum(int(anfang.group(1)), int(anfang.group(2)), int(anfang.group(3)))
            if not tag:
                continue
            folge = _geschwister_bis(h3, ("h2", "h3"))
            titel = ""
            for p in folge:
                if p.name != "p":
                    continue
                stark = p.find("strong")
                titel = _text(stark) if stark else (_zeilen(p) or [""])[0]
                if titel:
                    break
            if not titel or _WEGLASSEN.search(titel):
                continue
            teile = [t.strip() for t in kopf[anfang.end():].split("|") if t.strip()]
            rest_kopf = kopf[anfang.end():]
            uhrzeit = None
            for teil in [t for t in rest_kopf.split("|")]:
                if "uhr" in teil.lower() and not re.match(r"\s*\(?\s*einlass", teil, re.I):
                    uhrzeit = _uhrzeit(teil)
                    if uhrzeit:
                        break
            text = " ".join(_text(p) for p in folge)
            titel = _titel_glaetten(titel)
            termine.append((tag, uhrzeit, titel, _preis_aus(teile), _kategorie(titel, text, erzwungen),
                            _ticket(folge, url)))
    return termine


# --- Vorlage B: ein Akkordeon-Reiter je Veranstaltung/Reihe --------------------------------------------------

def _vorlage_b(soup: BeautifulSoup, haus: dict, url: str, erzwungen: Optional[str]) -> list[tuple]:
    termine = []
    for panel in soup.select("div.panel"):
        kopf_el = panel.select_one(".panel-heading h4") or panel.find("h4")
        reihe = _text(kopf_el)
        koerper = panel.select_one(".panel-body") or panel
        h2 = koerper.find("h2")
        if h2 and _text(h2).lower() == reihe.lower():
            reihe = _text(h2)  # „YOUNG STAGE“ → „Young Stage“
        if not reihe or _WEGLASSEN.search(reihe):
            continue
        bloecke = koerper.find_all(["p", "li", "h2", "h3", "h5"])
        zeilen = [z for b in bloecke for z in _zeilen(b)]
        text = " ".join(zeilen)

        # Ersatz-Uhrzeit der Reihe: erst Überschriften („Termine – mittwochs, 15 bis 16.30 Uhr“), dann Textzeilen
        reihen_zeit = None
        for b in koerper.find_all(["h2", "h3"]):
            if "uhr" in _text(b).lower() and not _daten_aus_zeile(_text(b))[0]:
                reihen_zeit = _uhrzeit(_text(b))
                if reihen_zeit:
                    break
        if not reihen_zeit:
            for z in zeilen:
                if "uhr" in z.lower() and not _daten_aus_zeile(z)[0]:
                    reihen_zeit = _uhrzeit(z)
                    if reihen_zeit:
                        break
        # Ersatz-Preis der Reihe: „Der Eintritt ist frei.“, „Teilnahme kostenfrei“ oder kurze Euro-Angabe
        reihen_preis = None
        for z in zeilen:
            if _daten_aus_zeile(z)[0]:
                continue
            if (re.search(r"eintritt\s+(?:ist\s+)?frei|freier eintritt|kostenfrei|kostenlos", z, re.I)
                    and not re.search(r"euro|€", z, re.I)):  # „Kinder unter 13 Jahren: kostenfrei“ neben Euro-Preisen
                reihen_preis = "kostenlos"
                break
            erster = z.split("|")[0]
            if len(erster) <= 60:
                reihen_preis = _preis_aus([erster])
                if reihen_preis:
                    break
        ticket = ticket_link_aus(koerper, url)

        for zeile in zeilen:
            daten, rest = _daten_aus_zeile(zeile)
            if not daten:
                continue
            teile = [t.strip(" ,") for t in re.split(r"\|", rest) if t.strip(" ,")]
            uhrzeit = None
            untertitel = None
            for teil in teile:
                if "uhr" in teil.lower() and not uhrzeit:
                    uhrzeit = _uhrzeit(teil)
                elif (not _PREIS.search(teil) and not _RAUM.search(teil) and len(teil) > 8
                      and not re.search(r"\bab \d+ jahren|anmeldung", teil, re.I)):
                    untertitel = untertitel or re.sub(r"^Musik\s+", "", teil)  # „Musik Michael Carleton …“
            titel = f"{reihe}: {untertitel}" if untertitel else reihe
            preis = _preis_aus(teile) or reihen_preis
            kategorie = _kategorie(titel, text, erzwungen)
            for tag in daten:
                termine.append((tag, uhrzeit or reihen_zeit, titel, preis, kategorie, ticket))
    return termine


# --- Vorlage C: h3 = Titel, <li> = „Wochentag, Datum | Uhrzeit | Preis“ --------------------------------------

def _vorlage_c(soup: BeautifulSoup, haus: dict, url: str, erzwungen: Optional[str]) -> list[tuple]:
    termine = []
    for h3 in soup.find_all("h3"):
        kopf = _text(h3)
        if not kopf or _WEGLASSEN.search(kopf):
            continue
        folge = _geschwister_bis(h3, ("h1", "h2", "h3"))
        punkte = [li for el in folge if el.name == "ul" for li in el.find_all("li")]
        if not punkte:
            continue
        text = " ".join(_text(el) for el in folge if el.name == "p")
        ticket = _ticket(folge, url)
        for li in punkte:
            zeilen = _zeilen(li)
            if not zeilen:
                continue
            anfang = _TAG_ANFANG.match(zeilen[0])
            if not anfang:
                continue  # „Dienstag | 15 bis 17 Uhr“ (wöchentlich), Kurse, Hinweise
            tag = _datum(int(anfang.group(1)), int(anfang.group(2)), int(anfang.group(3)))
            if not tag:
                continue
            rest = zeilen[0][anfang.end():]
            teile = [t.strip(" ,") for t in rest.split("|") if t.strip(" ,")]
            uhrzeit = None
            for teil in [rest.split("|")[0]] + teile:
                if "uhr" in teil.lower() and not re.match(r"\s*\(?\s*einlass", teil.strip(" ,"), re.I):
                    uhrzeit = _uhrzeit(teil)
                    if uhrzeit:
                        break
            # Unterzeile im Listenpunkt („Das Bremer Figurentheater | Hase und Igel“) ist der genauere Titel
            titel = _titel_glaetten(zeilen[1] if len(zeilen) > 1 else kopf)
            termine.append((tag, uhrzeit, titel, _preis_aus(teile), _kategorie(f"{kopf} {titel}", text, erzwungen),
                            ticket))
    return termine


def _vorlage(soup: BeautifulSoup) -> str:
    """Erkennt die Seitenvorlage am Inhalt: A (Datum in h3), B (Akkordeon-Reiter), sonst C (Programmliste)."""
    if any(_TAG_ANFANG.match(_text(h3)) for h3 in soup.find_all("h3")):
        return "A"
    if soup.select("div.panel .panel-heading"):
        return "B"
    return "C"


def _termine_aus_html(html: str, haus: dict, url: str, heute: date, enddatum: date,
                      kategorie: Optional[str] = None) -> list[dict]:
    """Termine einer Programmseite eines Hauses (ohne Netz testbar); nur heute bis enddatum, ohne Doppelte."""
    soup = BeautifulSoup(html or "", "html.parser")
    # Nur den Inhaltsbereich lesen (Kopf/Fuß der Stadtseite enthalten Kontakt-Überschriften)
    for weg in soup.select("header, footer, nav, .modal"):
        weg.decompose()
    vorlage = _vorlage(soup)
    roh = {"A": _vorlage_a, "B": _vorlage_b, "C": _vorlage_c}[vorlage](soup, haus, url, kategorie)
    events = []
    for tag, uhrzeit, titel, preis, kat, ticket in roh:
        if tag < heute or tag > enddatum:
            continue
        events.append(_event(haus, url, titel, tag, uhrzeit, preis, kat, ticket))
    logger.debug("%s: %s – Vorlage %s, %d Termine", QUELLE_NAME, url, vorlage, len(events))
    return events


def _ohne_doppelte(events: list[dict]) -> list[dict]:
    """Gleicher Ort, Tag, Uhrzeit und Titelkern nur einmal (Reihen-Präfix wie „Kindertheater |“ zählt nicht)."""
    gesehen: set[tuple] = set()
    ergebnis = []
    for e in events:
        schluessel = (e["ort"], e["datum"], e["uhrzeit"], _kern(e["titel"]))
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        ergebnis.append(e)
    return ergebnis


def scrape() -> list[dict]:
    """Scrapt die Programmseiten der Bürgerhäuser. Wirft nie; bei Fehlern leere Liste."""
    heute = date.today()
    logger.info("Starte Scraper: %s", QUELLE_NAME)
    events: list[dict] = []
    try:
        enddatum = vorschau_ende(QUELLE_NAME, heute)
        erreichbar = 0
        for haus in HAEUSER:
            anzahl_haus = 0
            for url, kategorie in haus["seiten"]:
                html = seite_abrufen(url, logger, wartezeit=WARTEZEIT_S)
                if html is None:
                    continue
                erreichbar += 1
                try:
                    neu = _termine_aus_html(html, haus, url, heute, enddatum, kategorie)
                except Exception as fehler:
                    logger.error("%s: Seite %s nicht lesbar: %s", QUELLE_NAME, url, fehler)
                    continue
                anzahl_haus += len(neu)
                events.extend(neu)
            logger.info("%s: %s – %d Termine", QUELLE_NAME, haus["ort"], anzahl_haus)
        events = _ohne_doppelte(events)
        if erreichbar and not events:
            logger.warning("%s: 0 Termine auf erreichbaren Seiten – Seitenstruktur geändert?", QUELLE_NAME)
    except Exception as fehler:
        logger.error("Scraper %s fehlgeschlagen: %s", QUELLE_NAME, fehler)
        return []
    logger.info("Scraper %s fertig: %d Termine", QUELLE_NAME, len(events))
    return events


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ergebnisse = scrape()
    print(f"\n=== {len(ergebnisse)} Termine ===")
    for e in ergebnisse:
        print(e["datum"], e["uhrzeit"], e["ort"], "|", e["titel"], "|", e["kategorie"], "|", e["preis"],
              "|", e["ticket_url"])
