"""
deduplication.py – DiesDasDüsseldorf
In-Memory-Deduplizierung der Event-Liste vor dem Datenbank-Schreiben.

Zwei Regeln:
1. Doppelte Events (gleicher Titel + Datum + Ort) werden gemergt statt
   verworfen: Fehlende Felder des ersten Eintrags werden aus dem
   Duplikat ergänzt.
2. Beim bild_url wird ein Rausgegangen-Bild immer durch ein Bild einer
   anderen Quelle ersetzt, sofern vorhanden.

Erstellt: 2026-03-05
"""
import logging
import re
from typing import Optional

from pipeline.ortsnamen import einheitlicher_name, ortsname_vereinheitlichen

logger = logging.getLogger(__name__)

# Felder die bei Duplikaten ergänzt werden dürfen (wenn None/leer)
_ANREICHERBARE_FELDER: list[str] = [
    "abgesagt",  # False → True, wenn eine Quelle die Absage meldet (z. B. „ENTFÄLLT!“ im Titel)
    "adresse",
    "uhrzeit",
    "beschreibung",
    "preis",
    "bild_url",
    "instagram_location_id",
    "kategorie",
]

# Erkennung von Rausgegangen-Bildern
_RAUSGEGANGEN_MUSTER = re.compile(r"rausgegangen", re.IGNORECASE)


def _ist_rausgegangen_bild(bild_url: Optional[str]) -> bool:
    """
    Erkennt ob eine Bild-URL von Rausgegangen stammt.

    Rausgegangen nutzt imageflow.rausgegangen.de als CDN
    und s3.eu-central-1.amazonaws.com/rausgegangen als Ursprung.

    Args:
        bild_url: Zu prüfende Bild-URL

    Returns:
        True wenn die URL von Rausgegangen stammt
    """
    if not bild_url:
        return False
    return bool(_RAUSGEGANGEN_MUSTER.search(bild_url))


# "stadtfuehrung" ersetzt beim Zusammenführen eine allgemeine Kategorie aus einem Kalender
# (z.B. Visit-Düsseldorf-Kalender "kultur" → Führungs-Scraper "stadtfuehrung").
# Eine thematische Kategorie (food, nightlife, outdoor) nur, wenn die Kategorie von einer Quelle
# stammt, die ausschließlich Führungen liefert. Solche Scraper setzen dafür im Event das interne
# Feld KATEGORIE_FEST_FELD = True (wird nicht gespeichert) – keine Kopplung über Quellennamen.
KATEGORIE_FEST_FELD = "_kategorie_fest"
_ALLGEMEINE_KATEGORIEN = {"kultur", "sonstiges"}
_THEMEN_KATEGORIEN = {"food", "nightlife", "outdoor"}


def kategorie_ersetzen(bisher: Optional[str], neu: Optional[str], neu_fest: bool = False) -> bool:
    """True, wenn die neue Kategorie die bisherige ersetzen soll (statt nur leere Felder zu füllen)."""
    if neu != "stadtfuehrung" or not bisher or bisher == neu:
        return False
    if bisher in _ALLGEMEINE_KATEGORIEN:
        return True
    return bisher in _THEMEN_KATEGORIEN and neu_fest


def _uhrzeit(event: dict) -> Optional[str]:
    """Uhrzeit als HH:MM ("20:00:00" → "20:00"), leer → None."""
    wert = event.get("uhrzeit")
    return str(wert)[:5] if wert else None


# ── Ähnlichkeit: dasselbe Event aus zwei Quellen mit abweichendem Titel oder Ortsnamen ─────────
# Beispiele (2026-11-09): „Sibel Schick im Gespräch“ in „zakk - Zentrum für Aktion, Kultur und
# Kommunikation“ und „zakk – Studio“; „European Outdoor Film Tour 2026 - EOFT“ und „… 26/27 – EOFT“
# im Savoy Theater – jeweils gleiche Zeit.

# Wörter, die einen Ort nicht unterscheiden (Raum- und Gattungsbezeichnungen, Stadt)
_ORT_FUELLWOERTER = {
    "zentrum", "fuer", "und", "the", "das", "der", "die", "im", "in", "am", "an", "auf", "von", "duesseldorf",
    "dusseldorf", "neuss", "ratingen", "halle", "saal", "studio", "raum", "buehne", "club", "bar", "kulturzentrum",
    "theater", "kino", "e", "v", "ev", "gmbh", "stadtbuecherei", "zentralbibliothek", "foyer", "kleiner", "grosser",
    "kleine", "grosse", "obergeschoss", "eg", "og",
}
# Wörter, die einen Titel nicht unterscheiden
_TITEL_FUELLWOERTER = {
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "und", "im", "in", "am", "an", "mit", "von", "zu", "zum",
    "zur", "auf", "fuer", "the", "a", "an", "of", "and", "feat", "ft", "live", "tour", "presents", "praesentiert",
}
_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _woerter(text: str) -> list[str]:
    """Kleinschreibung, Umlaute ausgeschrieben, nur Buchstaben/Ziffern als Wörter."""
    return re.findall(r"[a-z0-9]+", (text or "").lower().translate(_UMLAUTE))


def ort_kern(ort: str) -> set[str]:
    """Unterscheidende Wörter eines Ortsnamens („zakk – Studio“ → {"zakk"})."""
    return {w for w in _woerter(ort) if w not in _ORT_FUELLWOERTER and len(w) > 1}


def titel_kern(titel: str) -> set[str]:
    """Unterscheidende Wörter eines Titels ohne Zahlen und Füllwörter („… Tour 26/27 – EOFT“ → {…, "eoft"})."""
    return {w for w in _woerter(titel) if w not in _TITEL_FUELLWOERTER and not w.isdigit() and len(w) > 1}


# Trenner zwischen Titel und Zusatz („S.O.S. EISBERG | Filmreihe … – Black Box im Filmmuseum“)
# bzw. Original- und deutschem Titel („RONJA RÖVARDOTTER · RONJA RÄUBERTOCHTER“)
_TITEL_TRENNER = re.compile(r"\s+[|·]\s+")


def _titel_teile(titel: str) -> list[set[str]]:
    """Kernwörter der einzelnen Titelteile (nur wenn der Titel Trenner enthält)."""
    teile = [titel_kern(t) for t in _TITEL_TRENNER.split(titel or "")]
    return [t for t in teile if t] if len(teile) > 1 else []


def _teile_passen(a: set[str], b: set[str]) -> bool:
    """Gleicher Titelteil – auch wenn einer ein einzelnes, längeres Wort ist („BACKROOMS“ ⊂ „BACKROOMS (Extended Cut)“)."""
    if a == b:
        return True
    klein, gross = sorted((a, b), key=len)
    return klein <= gross and (len(klein) >= 2 or len(next(iter(klein))) >= 5)


def _ort_passt(a: dict, b: dict) -> bool:
    """Gemeinsamer Ortskern („zakk – Studio“ ~ „zakk - Zentrum für …“); ohne Kern muss der Ortsname gleich sein."""
    # Gleicher einheitlicher Name (pipeline/ortsnamen.py) = gleicher Ort – auch ohne gemeinsames Kernwort
    # („Zentrum für Aktion, Kultur und Kommunikation“ ~ „zakk“, „Dusseldorf, Germany“ ~ „Düsseldorf“)
    if einheitlicher_name(a.get("ort")) and einheitlicher_name(a.get("ort")) == einheitlicher_name(b.get("ort")):
        return True
    ort_a, ort_b = ort_kern(a.get("ort") or ""), ort_kern(b.get("ort") or "")
    if ort_a and ort_b:
        return bool(ort_a & ort_b)
    return _woerter(a.get("ort") or "") == _woerter(b.get("ort") or "")


def _titel_passt(a: dict, b: dict) -> bool:
    """Fast gleicher Titel (Schreibweise, Zusatz, Original-/deutscher Titel, Jahresangabe)."""
    titel_a, titel_b = titel_kern(a.get("titel") or ""), titel_kern(b.get("titel") or "")
    if not titel_a or not titel_b:
        return False
    if titel_a == titel_b:
        return True
    # Titel mit Zusatz bzw. Original-/deutschem Titel: Teile einzeln vergleichen
    teile_a = _titel_teile(a.get("titel") or "") or [titel_a]
    teile_b = _titel_teile(b.get("titel") or "") or [titel_b]
    if (len(teile_a) > 1 or len(teile_b) > 1) and any(_teile_passen(x, y) for x in teile_a for y in teile_b):
        return True
    klein, gross = sorted((titel_a, titel_b), key=len)
    # Ein Titel enthält den anderen ganz („Sibel Schick“ ⊂ „Sibel Schick im Gespräch“) – mindestens 2 Wörter
    if len(klein) >= 2 and klein <= gross:
        return True
    return len(titel_a & titel_b) / len(titel_a | titel_b) >= 0.75


# Quellen, die Termine nur weitergeben: Die Uhrzeit ist dort oft der Einlass statt des Beginns
# (Shinedown: d-live 19:30, Rausgegangen 18:30) – bei Abweichungen gilt die Zeit des Veranstalters.
_AGGREGATOR_MUSTER = re.compile(
    r"rausgegangen|visitd(?:ue|ü)sseldorf|allevents|resident advisor|ra\.co|prinz|kulturportal|eventfinder|meinestadt"
    r"|eventbrite|ticketmaster|songkick",
    re.IGNORECASE,
)
# Wie weit dürfen Uhrzeiten zweier Quellen auseinanderliegen und trotzdem dasselbe Event meinen (Einlass/Beginn)?
ZEIT_TOLERANZ_MINUTEN = 120


def ist_aggregator(event: dict) -> bool:
    """True für Sammel-Quellen (Rausgegangen, Visit Düsseldorf, AllEvents …), False für Veranstalter-Scraper."""
    return bool(_AGGREGATOR_MUSTER.search(f"{event.get('quelle_name') or ''} {event.get('quelle_url') or ''}"))


def _quelle(event: dict) -> str:
    return (event.get("quelle_name") or "").strip().lower()


def zeit_abstand(a: dict, b: dict) -> Optional[int]:
    """Abstand der Uhrzeiten in Minuten; None, wenn bei einem die Uhrzeit fehlt."""
    za, zb = _uhrzeit(a), _uhrzeit(b)
    if not za or not zb:
        return None
    try:
        ha, ma = (int(x) for x in za.split(":"))
        hb, mb = (int(x) for x in zb.split(":"))
    except ValueError:
        return None
    return abs((ha * 60 + ma) - (hb * 60 + mb))


def aehnliches_event(a: dict, b: dict) -> bool:
    """
    Dasselbe Event trotz abweichender Schreibweise? Gleiches Datum, gemeinsamer Ortskern, fast gleicher Titel – und:
    - gleiche Uhrzeit, oder
    - verschiedene Quellen: Uhrzeiten höchstens ZEIT_TOLERANZ_MINUTEN auseinander (Einlass vs. Beginn) oder eine fehlt,
    - oder ein Titel trug einen Absage-/Status-Zusatz („ENTFÄLLT! …“) und bei einem fehlt die Uhrzeit.
    Dieselbe Quelle mit anderer Uhrzeit bleibt ein weiterer Termin.
    """
    if not a.get("datum") or a.get("datum") != b.get("datum"):
        return False
    if not _ort_passt(a, b):
        return False
    andere_quelle = bool(_quelle(a) and _quelle(b) and _quelle(a) != _quelle(b))
    if not (_titel_passt(a, b) or (andere_quelle and _bandname_enthalten(a, b))):
        return False
    zeit_a, zeit_b = _uhrzeit(a), _uhrzeit(b)
    if zeit_a and zeit_a == zeit_b:
        return True
    if andere_quelle:
        abstand = zeit_abstand(a, b)
        return abstand is None or abstand <= ZEIT_TOLERANZ_MINUTEN
    return bool((a.get(TITEL_STATUS_FELD) or b.get(TITEL_STATUS_FELD)) and (not zeit_a or not zeit_b))


# Einzelwörter, die als ganzer Titel zu allgemein sind, um einen längeren Titel sicher zuzuordnen
_ALLGEMEINE_EINZELTITEL = {
    "konzert", "party", "fuehrung", "workshop", "lesung", "vortrag", "ausstellung", "flohmarkt", "markt",
    "vernissage", "kabarett", "comedy", "karaoke", "quiz", "brunch", "tanzabend", "disco",
}


def _bandname_enthalten(a: dict, b: dict) -> bool:
    """
    Ein Titel ist ein einzelnes, prägnantes Wort und steckt im längeren Titel der anderen Quelle:
    „SHINEDOWN“ (Rausgegangen) ~ „SHINEDOWN – Dance Kid Dance Act II – Düsseldorf, Mitsubishi Electric Halle“
    (AllEvents). Nur zwischen verschiedenen Quellen und bei gleichem Ort/Tag (prüft aehnliches_event).
    """
    titel_a, titel_b = titel_kern(a.get("titel") or ""), titel_kern(b.get("titel") or "")
    if not titel_a or not titel_b:
        return False
    klein, gross = sorted((titel_a, titel_b), key=len)
    if len(klein) != 1:
        return False
    wort = next(iter(klein))
    return len(wort) >= 5 and wort not in _ALLGEMEINE_EINZELTITEL and wort in gross


def bester_treffer(bestand: list[dict], event: dict) -> Optional[dict]:
    """
    Das passendste Event eines Tagesbestands: gleiche Uhrzeit vor naher Uhrzeit.
    Liegen mehrere Termine derselben Quelle in Reichweite (Matinee 18:00 und Abend 20:00, Aggregator 19:00),
    ist die Zuordnung mehrdeutig – dann bleibt das Event lieber getrennt, statt mit dem falschen zu verschmelzen.
    """
    treffer = [k for k in bestand if k is not event and aehnliches_event(k, event)]
    exakte = [k for k in treffer if _uhrzeit(k) and _uhrzeit(k) == _uhrzeit(event)]
    if exakte:
        return exakte[0]
    pro_quelle: dict[str, int] = {}
    for k in treffer:
        pro_quelle[_quelle(k)] = pro_quelle.get(_quelle(k), 0) + 1
    eindeutig = [k for k in treffer if pro_quelle[_quelle(k)] == 1]

    def abstand(k: dict) -> int:
        a = zeit_abstand(k, event)
        return 999 if a is None else a

    return min(eindeutig, key=abstand) if eindeutig else None


# ── Absage- und Status-Zusätze im Titel ─────────────────────────────────────────────────────────
# Beispiele: „ENTFÄLLT! 11.11.2026 | "Kinder sicher im Internet" in Bilk“, „Leider abgesagt: Sarah Kuttner …“,
# „! ENTFÄLLT ! Musikstudio …“, „VERLEGT AUF 11.11.2026 Musikstudio …“, „AUSGEBUCHT! 09.12.2026 | 3D-Druckstifte …“,
# „Swiss & Die Anderen – Punk Lebt Tour 2026 (AUSVERKAUFT)“. Ohne Bereinigung entstand ein zweites Event.
TITEL_STATUS_FELD = "_titel_status"  # intern, wird nicht gespeichert: "abgesagt" | "voll"
_STATUS_PRAEFIX = re.compile(
    r"^[\s!*]*(?:(?P<abgesagt>leider\s+abgesagt|abgesagt|entf(?:ä|ae)llt|f(?:ä|ae)llt\s+aus|verlegt(?:\s+auf)?)"
    r"|(?P<voll>ausgebucht|ausverkauft))(?![a-zäöüß])[\s!:]*(?:\d{1,2}\.\d{1,2}\.(?:\d{2,4})?)?[\s|:–—-]*",
    re.IGNORECASE,
)
_STATUS_SUFFIX = re.compile(
    r"\s*[(\[]\s*(?:(?P<abgesagt>abgesagt|entf(?:ä|ae)llt)|(?P<voll>ausverkauft|ausgebucht))\s*[)\]]\s*$",
    re.IGNORECASE,
)


def titel_status_bereinigen(event: dict) -> dict:
    """
    Entfernt Absage-/Status-Zusätze aus dem Titel. „Entfällt/abgesagt/verlegt“ markiert das Event als abgesagt
    (für diesen Termin), „ausverkauft/ausgebucht“ wird nur entfernt. Ändert das Event an Ort und Stelle.
    """
    titel = event.get("titel") or ""
    for muster in (_STATUS_PRAEFIX, _STATUS_SUFFIX):
        m = muster.search(titel)
        if not m:
            continue
        rest = (titel[: m.start()] + titel[m.end():]).strip()
        if not rest:
            continue  # nur der Zusatz – Titel lieber stehen lassen
        status = "abgesagt" if m.group("abgesagt") else "voll"
        logger.debug("Titel-Zusatz entfernt (%s): '%s' → '%s'", status, titel[:60], rest[:60])
        titel = rest
        event["titel"] = titel
        if status == "abgesagt":
            event["abgesagt"] = True
        if event.get(TITEL_STATUS_FELD) != "abgesagt":
            event[TITEL_STATUS_FELD] = status
    return event


_KOSTENLOS = re.compile(
    r"^(?:eintritt[: ]*frei|freier eintritt|kostenlos|kostenfrei|gratis|umsonst|frei|free|0(?:[,.]0{1,2})? ?€|€ ?0)$",
    re.IGNORECASE,
)


def preis_normalisieren(preis: Optional[str]) -> Optional[str]:
    """Einheitliche Schreibweise: „Eintritt frei“, „gratis“, „0,00 €“ … → „kostenlos“; sonst unverändert."""
    if not preis:
        return preis
    return "kostenlos" if _KOSTENLOS.match(preis.strip()) else preis


def _normalisiere_schluessel(titel: str, datum: str, ort: str) -> str:
    """
    Erstellt einen normalisierten Deduplizierungs-Schlüssel.

    Kleinschreibung, Leerzeichen-Normalisierung und Sonderzeichen-Entfernung
    reduzieren Falsch-Negative (z. B. Groß-/Kleinschreibung, Leerzeichen).

    Args:
        titel: Event-Titel
        datum: Event-Datum (ISO 8601)
        ort: Venue-Name

    Returns:
        Normalisierter Schlüssel-String
    """
    def _norm(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[^\w\s\-äöüß]", "", s)
        return s

    return f"{_norm(titel)}|{datum}|{_norm(ort)}"


def ist_rausgegangen(event: dict) -> bool:
    """True, wenn ein Event (bzw. DB-Eintrag) Rausgegangen als Quelle hat."""
    name = (event.get("quelle_name") or "").lower()
    url = (event.get("quelle_url") or "").lower()
    return "rausgegangen" in name or "rausgegangen.de" in url


def _events_mergen(basis: dict, duplikat: dict) -> dict:
    """
    Mergt zwei Events: Fehlende Felder der Basis werden aus dem Duplikat ergänzt.
    Bei bild_url: Rausgegangen-Bilder werden durch andere Quellen ersetzt.

    Vorrang: Trifft ein Rausgegangen-Eintrag auf dasselbe Event aus einer anderen Quelle,
    wird die andere Quelle zur Basis (Link, Quelle, Bild, Beschreibung, Preis, Adresse).
    Rausgegangen füllt danach nur noch Felder auf, die dort fehlen.

    Args:
        basis: Primärer Event-Eintrag (wird angereichert)
        duplikat: Zweiter Event-Eintrag (Lieferant fehlender Daten)

    Returns:
        Angereicherter Event-Dict
    """
    if ist_rausgegangen(basis) and not ist_rausgegangen(duplikat):
        logger.debug(
            "Quelle getauscht: Rausgegangen → '%s' für '%s'",
            duplikat.get("quelle_name", "?"), (duplikat.get("titel") or "")[:40],
        )
        basis, duplikat = duplikat, basis

    merged = dict(basis)

    # Uhrzeit: Bei Abweichung gilt die des Veranstalters (Aggregatoren nennen oft den Einlass)
    if (_uhrzeit(duplikat) and _uhrzeit(basis) and _uhrzeit(basis) != _uhrzeit(duplikat)
            and ist_aggregator(basis) and not ist_aggregator(duplikat)):
        merged["uhrzeit"] = duplikat["uhrzeit"]

    for feld in _ANREICHERBARE_FELDER:
        basis_wert = basis.get(feld)
        dupli_wert = duplikat.get(feld)

        if feld == "bild_url":
            # Rausgegangen-Bild durch bessere Quelle ersetzen
            if _ist_rausgegangen_bild(basis_wert) and dupli_wert and not _ist_rausgegangen_bild(dupli_wert):
                merged["bild_url"] = dupli_wert
                logger.debug(
                    "Bild ersetzt: Rausgegangen → '%s' (%s)",
                    duplikat.get("quelle_name", "?"), dupli_wert[:60],
                )
            elif not basis_wert and dupli_wert:
                merged["bild_url"] = dupli_wert
        elif feld == "kategorie" and kategorie_ersetzen(
            basis_wert, dupli_wert, bool(duplikat.get(KATEGORIE_FEST_FELD))
        ):
            merged["kategorie"] = dupli_wert
            # Herkunft der Kategorie mitnehmen – entscheidet später auch beim Abgleich mit der DB
            merged[KATEGORIE_FEST_FELD] = bool(duplikat.get(KATEGORIE_FEST_FELD))
        else:
            # Feld ergänzen wenn leer
            if not basis_wert and dupli_wert:
                merged[feld] = dupli_wert
                logger.debug(
                    "Feld '%s' ergänzt von '%s': %s",
                    feld, duplikat.get("quelle_name", "?"), str(dupli_wert)[:60],
                )

    return merged


def deduplizieren(events: list[dict]) -> list[dict]:
    """
    Dedupliziert eine Event-Liste in-Memory mit Merge-Logik.

    Duplikate (gleicher Titel + Datum + Ort) werden nicht verworfen,
    sondern in den ersten Eintrag gemergt. Fehlende Felder werden
    ergänzt, Rausgegangen-Bilder durch bessere Quellen ersetzt. Liefert eine andere
    Quelle dasselbe Event wie Rausgegangen, wird sie zur Hauptquelle (siehe _events_mergen).

    Verschiedene Uhrzeiten am selben Tag sind KEINE Duplikate, sondern weitere
    Termine (z.B. Führungen um 11 und 14 Uhr) und bleiben getrennt. Fehlt bei
    einem der beiden die Uhrzeit, gilt es als dasselbe Event.

    Args:
        events: Rohe Event-Liste aus allen Scrapern

    Returns:
        Deduplizierte und angereicherte Event-Liste
    """
    if not events:
        return []

    reihenfolge: list[str] = []
    index: dict[str, dict] = {}
    varianten: dict[str, list[str]] = {}  # Titel|Datum|Ort → Schlüssel der einzelnen Uhrzeiten
    pro_datum: dict[str, list[str]] = {}  # Datum → Schlüssel (für den Ähnlichkeitsvergleich)
    duplikat_anzahl = 0
    angereichert_anzahl = 0

    for event in events:
        # Eine Schreibweise pro Spielstätte (pipeline/ortsnamen.py) – vor allen Vergleichen
        ortsname_vereinheitlichen(event)
        titel_status_bereinigen(event)
        titel = event.get("titel") or ""
        datum = event.get("datum") or ""
        ort = event.get("ort") or ""

        if not titel or not datum:
            # Pflichtfelder fehlen – trotzdem aufnehmen
            schluessel = f"_unvollstaendig_{id(event)}"
        else:
            basis = _normalisiere_schluessel(titel, datum, ort)
            zeit = _uhrzeit(event)
            # Gleiche Uhrzeit (oder eine fehlt) = dasselbe Event, sonst weiterer Termin am selben Tag
            schluessel = next(
                (k for k in varianten.get(basis, []) if zeit is None or _uhrzeit(index[k]) in (None, zeit)),
                None,
            )
            if schluessel is None:
                # Abweichende Schreibweise aus einer anderen Quelle (Titel/Ort leicht anders, gleiche Zeit)?
                kandidaten = pro_datum.get(datum, [])
                treffer = bester_treffer([index[k] for k in kandidaten], event)
                schluessel = next((k for k in kandidaten if index[k] is treffer), None) if treffer else None
            if schluessel is None:
                schluessel = f"{basis}|{zeit or '-'}|{len(varianten.get(basis, []))}"
                varianten.setdefault(basis, []).append(schluessel)
                pro_datum.setdefault(datum, []).append(schluessel)

        if schluessel not in index:
            index[schluessel] = event
            reihenfolge.append(schluessel)
        else:
            # Duplikat gefunden: mergen statt verwerfen
            duplikat_anzahl += 1
            vorher = dict(index[schluessel])
            index[schluessel] = _events_mergen(index[schluessel], event)
            nachher = index[schluessel]

            # Prüfen ob tatsächlich etwas angereichert wurde
            veraenderte_felder = [
                f for f in ["quelle_name", *_ANREICHERBARE_FELDER]
                if vorher.get(f) != nachher.get(f)
            ]
            if veraenderte_felder:
                angereichert_anzahl += 1
                logger.info(
                    "Duplikat angereichert: '%s' (%s) – Felder ergänzt: %s (Quelle: %s)",
                    titel[:40], datum,
                    ", ".join(veraenderte_felder),
                    event.get("quelle_name", "?"),
                )
            else:
                logger.debug(
                    "Duplikat verworfen (keine neuen Daten): '%s' (%s) von '%s'",
                    titel[:40], datum, event.get("quelle_name", "?"),
                )

    ergebnis = [index[s] for s in reihenfolge]

    logger.info(
        "Deduplizierung: %d → %d Events (%d Duplikate, %d angereichert)",
        len(events), len(ergebnis), duplikat_anzahl, angereichert_anzahl,
    )
    return ergebnis
