"""
client.py – DiesDasDüsseldorf
Supabase-Datenbankverbindung
Erstellt: 2026-02-24
"""
import logging
import os
import re
from collections import Counter
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

from pipeline.deduplication import (
    KATEGORIE_FEST_FELD,
    TITEL_STATUS_FELD,
    bester_treffer,
    kategorie_ersetzen,
    preis_normalisieren,
)
from pipeline.quellen_rang import (
    AGGREGATOR, HAUS, QUELLEN_FELD, quellen_der_zeile, quellen_eintrag, quellen_rang, quellen_vereinigen, rang_gespeichert,
)
from pipeline.slug_generator import slug_fuer_event, slug_mit_suffix

load_dotenv()

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None

# Felder die beim Upsert ignoriert werden (server-seitig gesetzt)
_IGNORE_FELDER = {"id", "erstellt_am", "gepostet_am"}

# Felder die bei bereits gespeicherten Events ergänzt werden dürfen
_ANREICHERBARE_FELDER: list[str] = [
    "abgesagt",  # False → True, wenn eine Quelle die Absage meldet
    "adresse",
    "uhrzeit",
    "beschreibung",
    "preis",
    "bild_url",
    "kategorie",
    "stadtteil",
]

# Quellenangaben, die beim Vorrang-Wechsel (zur Quelle mit besserem Rang) mitgelesen werden
_QUELL_FELDER: list[str] = ["quelle_name", "quelle_url"]

# Felder, die beim Vorrang-Wechsel von der Quelle mit besserem Rang übernommen werden,
# auch wenn sie schon belegt sind (sonst gilt überall: nur leere Felder auffüllen)
_VORRANG_FELDER: list[str] = ["bild_url", "beschreibung", "preis", "adresse"]

# Spalten, die zum Abgleich bestehender Events geladen werden
# (beschreibung_quelle: Beschreibung wurde aus einer Veranstalter-Seite umgeschrieben, siehe
# pipeline/beschreibung_quellen.py – Spalte muss in der DB existieren)
# ort_id: Ortszuordnung (Plan docs/plan-locations-2026-11-18.md, 3.4) – für die Dubletten-Regel nach Häusern und
# zum Ergänzen einer fehlenden Zuordnung. Spalte muss in der DB existieren (database/orte_spielstaetten_2026-11-19.sql).
# redaktion_felder: im Admin-Bereich geänderte Felder, die die Pipeline nie überschreibt (Plan Admin-Dashboard 4.4,
# database/admin_events_2026-11-23.sql – Spalte muss in der DB existieren).
# quellen: alle Quellen des Events (Plan Quellen-Ausbau 4.3, database/quellen_spalte_2026-11-24.sql – muss existieren).
_ABGLEICH_SPALTEN_BASIS: str = ",".join(
    _QUELL_FELDER + ["beschreibung_quelle", "ort_id", "redaktion_felder"] + _ANREICHERBARE_FELDER
)
_ABGLEICH_SPALTEN: str = _ABGLEICH_SPALTEN_BASIS + ",quellen"
# ticket_url: Ticket-Link des Hauses (Plan Quellen-Ausbau 5.5.2, Schritt P1, database/ticket_url_2026-11-24.sql)

# Fehlt die Spalte quellen (SQL database/quellen_spalte_2026-11-24.sql nicht ausgeführt), scheitert sonst JEDE Abfrage
# und jeder Insert – am 24.11.2026 hat das einen ganzen Lauf gekostet (0 gespeichert, 2.909 Fehler). events_speichern
# prüft die Spalte deshalb einmal und arbeitet ohne sie weiter.
_QUELLEN_SPALTE: dict[str, bool] = {"da": True}
# Dasselbe für events.ticket_url (Schritt P1): ohne Spalte wird ohne Ticket-Link gespeichert
_TICKET_SPALTE: dict[str, bool] = {"da": True}


def _abgleich_spalten() -> str:
    """Spalten für den Abgleich – mit quellen und ticket_url, wenn es die Spalten gibt."""
    spalten = _ABGLEICH_SPALTEN if _QUELLEN_SPALTE["da"] else _ABGLEICH_SPALTEN_BASIS
    return spalten + ",ticket_url" if _TICKET_SPALTE["da"] else spalten


def _spalte_pruefen(db, spalte: str, schalter: dict, sql_datei: str, ohne: str) -> bool:
    """Gibt es events.<spalte>? Ergebnis gilt für diesen Lauf; ohne Spalte wird ohne dieses Feld gespeichert."""
    try:
        db.table("events").select(spalte).limit(1).execute()
        schalter["da"] = True
    except Exception as fehler:
        text = str(fehler)
        # Nur eine wirklich fehlende Spalte schaltet das Feld ab; ein kurzer Netz-/Serverfehler nicht
        # (sonst liefe der ganze Lauf ohne das Feld) – Cursor-Prüfung V1
        if any(z in text for z in ("42703", "PGRST204", "does not exist", "Could not find")):
            schalter["da"] = False
            logger.error("Spalte events.%s fehlt (%s) – speichere ohne %s. SQL %s ausführen!",
                         spalte, text[:120], ohne, sql_datei)
        else:
            schalter["da"] = True
            logger.warning("Spaltenprobe events.%s fehlgeschlagen (%s) – nehme an, dass die Spalte da ist",
                           spalte, text[:120])
    return schalter["da"]


def _quellen_spalte_pruefen(db) -> bool:
    """Gibt es events.quellen? Ohne Spalte wird ohne Quellenliste gespeichert."""
    return _spalte_pruefen(db, "quellen", _QUELLEN_SPALTE, "database/quellen_spalte_2026-11-24.sql", "Quellenliste")


def _ticket_spalte_pruefen(db) -> bool:
    """Gibt es events.ticket_url? Ohne Spalte wird ohne Ticket-Link gespeichert."""
    return _spalte_pruefen(db, "ticket_url", _TICKET_SPALTE, "database/ticket_url_2026-11-24.sql", "Ticket-Link")

# Spalten die noch nicht in der DB existieren – werden aus Inserts/Selects herausgefiltert
# Nachtragen via Supabase Dashboard: ALTER TABLE events ADD COLUMN instagram_location_id TEXT;
# post_typ (feed | reel) setzen einige Tier-3-Scraper, die Pipeline nutzt es aber noch nicht
_NICHT_IN_DB: set[str] = {"instagram_location_id", "post_typ"}

# Erkennung von Rausgegangen-Bildern (imageflow.rausgegangen.de / s3/.../rausgegangen)
_RAUSGEGANGEN_MUSTER = re.compile(r"rausgegangen", re.IGNORECASE)


def _ist_rausgegangen_bild(bild_url: Optional[str]) -> bool:
    """Erkennt ob eine Bild-URL von Rausgegangen stammt."""
    return bool(bild_url and _RAUSGEGANGEN_MUSTER.search(bild_url))


def _jetzt_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _anreicherungs_update_bauen(
    bestehendes: dict, neu: dict, kategorie_fest: bool = False, rang_neu: Optional[int] = None,
) -> dict:
    """
    Berechnet welche Felder eines bestehenden DB-Eintrags angereichert werden sollen.

    Regeln:
    - Feld wird ergänzt wenn im bestehenden Eintrag None/leer und im neuen Eintrag belegt
      (gilt in jede Richtung – auch Rausgegangen füllt Lücken einer anderen Quelle)
    - bild_url: Rausgegangen-Bild wird durch nicht-Rausgegangen-Bild ersetzt,
      auch wenn bereits vorhanden
    - Vorrang (Plan Quellen-Ausbau 4.2, Schritt R1): Hat der neue Eintrag einen strikt besseren Rang
      (pipeline/quellen_rang.py) und einen eigenen Link, wechselt die Quelle (quelle_name, quelle_url); Preis,
      Adresse und Beschreibung kommen dann von der besseren Quelle, soweit sie dort belegt sind, das Bild nur, wenn
      das bisherige von Rang ≥ 4 stammt. Gleicher oder schlechterer Rang wechselt nie – so springt kein Event
      zwischen zwei Quellen hin und her. Slug, abgleich_* und ort_id bleiben.
      Ausnahme: Eine aus der Veranstalter-Seite recherchierte Beschreibung (beschreibung_quelle) bleibt.

    Args:
        bestehendes: Aktueller DB-Eintrag
        neu: Neu eingehender Event (ohne interne „_“-Felder, siehe events_speichern)
        rang_neu: Rang der Quelle des neuen Events. events_speichern rechnet ihn vor dem Entfernen von `_scraper`
            aus dem Anzeigenamen; ohne Angabe gilt der Rang des gespeicherten Namens (quelle_name).

    Returns:
        Dict mit Feldern die aktualisiert werden sollen (leer = kein Update nötig)
    """
    update: dict = {}
    if rang_neu is None:
        rang_neu = quellen_rang(neu)
    rang_alt = rang_gespeichert(bestehendes.get("quelle_name"), bestehendes.get("quelle_url"))

    # Ortszuordnung: nur ergänzen, wenn sie fehlt – nie NULL und nie eine vorhandene ersetzen (das tut nur der
    # Nachtrag mit einem Treffer des gespeicherten Namens, Plan Locations 3.4)
    if neu.get("ort_id") and not bestehendes.get("ort_id"):
        update["ort_id"] = neu["ort_id"]

    for feld in _ANREICHERBARE_FELDER:
        db_wert = bestehendes.get(feld)
        neu_wert = neu.get(feld)

        if feld == "bild_url":
            # Rausgegangen-Bild durch bessere Quelle ersetzen
            if _ist_rausgegangen_bild(db_wert) and neu_wert and not _ist_rausgegangen_bild(neu_wert):
                update[feld] = neu_wert
            elif not db_wert and neu_wert:
                update[feld] = neu_wert
        elif feld == "kategorie" and kategorie_ersetzen(db_wert, neu_wert, kategorie_fest):
            # z.B. Kalender lieferte "kultur", Führungs-Scraper weiß: "stadtfuehrung"
            update[feld] = neu_wert
        else:
            if not db_wert and neu_wert:
                update[feld] = neu_wert

    # Uhrzeit: Bei Abweichung gilt die des Veranstalters (Rang 1) – die anderen nennen oft den Einlass statt des Beginns.
    # Gleicher Rang ändert die Uhrzeit nicht.
    neue_zeit = _uhrzeit_hhmm(neu.get("uhrzeit"))
    if (neue_zeit and bestehendes.get("uhrzeit") and neue_zeit != _uhrzeit_hhmm(bestehendes.get("uhrzeit"))
            and rang_neu == HAUS and rang_alt > HAUS):
        update["uhrzeit"] = neu["uhrzeit"]

    # Quellenwechsel nur zu einem strikt besseren Rang und nur mit eigenem Link (ohne ihn zeigte „Zum Termin“ ins Leere)
    if rang_neu < rang_alt and neu.get("quelle_url"):
        for feld in _QUELL_FELDER + _VORRANG_FELDER:
            if feld == "beschreibung" and bestehendes.get("beschreibung_quelle"):
                continue  # aus der Veranstalter-Seite recherchierter Text bleibt (nur Lücken würden gefüllt)
            if feld == "bild_url" and rang_alt < AGGREGATOR:
                continue  # Bild eines Hauses, Ticketverkaufs oder Portals bleibt (leere Werte füllt die Schleife oben)
            neu_wert = neu.get(feld)
            if neu_wert and neu_wert != bestehendes.get(feld):
                update[feld] = neu_wert

    # Ticket-Link des Hauses (Plan Quellen-Ausbau 5.5.2, Schritt P1): ergänzen, wenn er fehlt. Ein vorhandener bleibt,
    # wenn die neue Quelle keinen hat (leere Werte überschreiben nie). Ersetzt wird er bei einem Quellenwechsel zu
    # einem besseren Rang und von der Quelle, die schon Hauptquelle ist (das Haus hat den Link geändert) – nie von
    # einer schlechteren oder fremden Quelle gleichen Rangs.
    neu_ticket, alt_ticket = neu.get("ticket_url"), bestehendes.get("ticket_url")
    if neu_ticket and neu_ticket != alt_ticket and (
        not alt_ticket
        or (rang_neu < rang_alt and neu.get("quelle_url"))
        or (neu.get("quelle_name") and neu.get("quelle_name") == bestehendes.get("quelle_name"))
    ):
        update["ticket_url"] = neu_ticket

    # Quellenliste (Plan Quellen-Ausbau 4.3): die Quellen des neuen Eintrags ergänzen; geschrieben wird nur bei einer
    # neuen Quelle, anderem Link/Rang, veraltetem „zuletzt“ oder wenn die Zeile noch gar keine Liste hat
    if neu.get("quellen"):
        liste, geaendert = quellen_vereinigen(quellen_der_zeile(bestehendes), neu["quellen"])
        if geaendert or not bestehendes.get("quellen"):
            update["quellen"] = liste

    # Feldschutz (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.4 Teil A, E7): Felder, die die Redaktion im
    # Admin-Bereich geändert hat, schreibt die Pipeline nie – an keiner der vier Stellen oben (ort_id-Nachtrag,
    # Schleife inkl. bild_url/kategorie/abgesagt, Uhrzeit-Block, Quellenwechsel).
    geschuetzt = set(bestehendes.get("redaktion_felder") or [])
    if geschuetzt:
        update = {k: v for k, v in update.items() if k not in geschuetzt}
    return update


def _abgleich_redaktion(db: Client, titel: str, datum: str, ort: str, uhrzeit: Optional[str]) -> Optional[dict]:
    """
    Schritt 0 (Plan Admin-Dashboard 4.4 Teil B): Findet ein Event wieder, dessen Titel, Datum, Uhrzeit oder Ort die
    Redaktion geändert hat. Dafür stehen die Werte der Quelle in abgleich_titel/_datum/_uhrzeit/_ort. Getroffen wird
    nur bei genau EINER passenden Zeile (Uhrzeit wie in Schritt 1: gleich, oder eine fehlt); sonst laufen die
    Schritte 1–3 wie bisher (Cursor-Prüfung 2, Befund 3).
    """
    treffer = (
        db.table("events")
        .select("id,abgleich_uhrzeit," + _abgleich_spalten())
        .eq("abgleich_titel", titel)
        .eq("abgleich_datum", datum)
        .eq("abgleich_ort", ort)
        .execute()
    )
    neue_zeit = _uhrzeit_hhmm(uhrzeit)
    passend = [
        z for z in (treffer.data or [])
        if neue_zeit is None or _uhrzeit_hhmm(z.get("abgleich_uhrzeit")) in (None, neue_zeit)
    ]
    if len(passend) == 1:
        logger.info("Abgleich über Redaktionsänderung (Schritt 0): '%s' (%s)", titel[:40], datum)
        return passend[0]
    return None


def _tagesbestand(db: Client, datum: str, cache: dict[str, list[dict]]) -> list[dict]:
    """Alle gespeicherten Events eines Tages (einmal je Lauf und Datum geladen) für den Ähnlichkeitsabgleich."""
    if datum not in cache:
        try:
            antwort = (
                db.table("events")
                .select("id,titel,ort,datum,slug," + _abgleich_spalten())
                .eq("datum", datum)
                .execute()
            )
            # Haus der Zuordnung für die Dubletten-Regel (ohne Index aus Schritt 1d: Namensvergleich wie bisher)
            from pipeline.ort_zuordnung import annotieren
            cache[datum] = [annotieren(z) for z in (antwort.data or [])]
        except Exception as e:
            logger.warning("Tagesbestand für %s nicht ladbar: %s", datum, str(e))
            cache[datum] = []
    return cache[datum]


def _uhrzeit_hhmm(wert: Optional[str]) -> Optional[str]:
    """Normalisiert Uhrzeiten auf HH:MM ("20:00:00" → "20:00"), leer → None."""
    if not wert:
        return None
    return str(wert)[:5]


def _slug_pruefen(db: Client, basis: str, uhrzeit: Optional[str]) -> tuple[Optional[dict], str]:
    """
    Prüft einen neuen Slug gegen bereits gespeicherte Events.

    - Gibt es unter dem Basis-Slug (oder seinen Suffix-Varianten -b, -c …) ein Event mit
      gleicher Uhrzeit (oder fehlt bei einem der beiden die Uhrzeit), ist es dasselbe Event
      aus einer anderen Quelle → dieses Event wird zur Anreicherung zurückgegeben.
    - Sonst ist es eine weitere Vorstellung am selben Tag → erster freier Slug (-b, -c …).

    Returns:
        (bestehendes_event_oder_None, freier_slug)
    """
    try:
        antwort = (
            db.table("events")
            .select("id,slug," + _abgleich_spalten())
            # PostgREST-Platzhalter "*" statt "%": ein "%" am Ende wird nicht URL-kodiert und lässt die
            # Anfrage beim Supabase-Gateway scheitern (Cloudflare 1101) – dann fehlte der Abgleich und jede
            # weitere Vorstellung am selben Tag scheiterte am eindeutigen Slug (bis 2026-11-05)
            .like("slug", f"{basis}*")
            .execute()
        )
    except Exception as e:
        logger.warning("Slug-Prüfung für '%s' fehlgeschlagen: %s", basis, str(e))
        return None, basis

    # Nur exakt den Basis-Slug und seine Suffix-Varianten berücksichtigen
    # (".like" findet auch längere Slugs, die zufällig mit dem Basis-Slug beginnen)
    muster = re.compile(rf"^{re.escape(basis)}(-[a-z]|-\d+)?$")
    kandidaten = [z for z in (antwort.data or []) if muster.match(z.get("slug") or "")]

    neue_zeit = _uhrzeit_hhmm(uhrzeit)
    for kandidat in kandidaten:
        alte_zeit = _uhrzeit_hhmm(kandidat.get("uhrzeit"))
        if neue_zeit is None or alte_zeit is None or neue_zeit == alte_zeit:
            logger.info(
                "Duplikat über Slug erkannt: '%s' (%s) – wird angereichert statt neu angelegt",
                kandidat["slug"], neue_zeit or "ohne Uhrzeit",
            )
            return kandidat, kandidat["slug"]

    vergeben = {z["slug"] for z in kandidaten}
    freier_slug = slug_mit_suffix(basis, vergeben)
    if freier_slug != basis:
        logger.info("Weitere Vorstellung am selben Tag: Slug '%s'", freier_slug)
    return None, freier_slug


def get_supabase_client() -> Client:
    """
    Gibt eine Supabase-Client-Instanz zurück (Singleton).
    Wirft einen Fehler wenn die Umgebungsvariablen fehlen.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    url = os.getenv("SUPABASE_URL")
    # Die Pipeline schreibt Events und braucht dafür den service_role-Key (umgeht RLS).
    # SUPABASE_KEY (anon) reicht seit Einführung der Rollen nur noch zum Lesen.
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not key:
        key = os.getenv("SUPABASE_KEY")
        logger.warning(
            "SUPABASE_SERVICE_KEY fehlt – nutze SUPABASE_KEY. "
            "Mit aktiver RLS schlägt das Speichern von Events damit fehl."
        )

    if not url or not key:
        raise EnvironmentError(
            "SUPABASE_URL und SUPABASE_SERVICE_KEY müssen in der .env Datei gesetzt sein."
        )

    try:
        _supabase_client = create_client(url, key)
        logger.info("Supabase-Verbindung erfolgreich hergestellt.")
    except Exception as e:
        logger.error("Supabase-Verbindung fehlgeschlagen: %s", str(e))
        raise

    return _supabase_client


def events_speichern(events: list[dict]) -> dict:
    """
    Speichert eine Liste von Events in Supabase.

    Für neue Events: INSERT.
    Für bereits vorhandene Events (Duplikat nach Titel + Datum + Ort und gleicher bzw. fehlender Uhrzeit;
    eine andere Uhrzeit ist ein weiterer Termin am selben Tag und wird neu angelegt):
      - Fehlende Felder werden aus dem neuen Eintrag ergänzt.
      - Ein Rausgegangen-Bild wird durch ein Bild einer anderen Quelle ersetzt,
        sofern der neue Eintrag ein besseres Bild mitbringt.
      - Ein Eintrag wechselt zur Quelle mit strikt besserem Rang (Vorrang-Regel, siehe
        _anreicherungs_update_bauen, pipeline/quellen_rang.py); der Slug bleibt.

    Args:
        events: Liste von Event-Dicts im DiesDasDüsseldorf-Format

    Returns:
        Dict mit Statistiken: {"gespeichert": int, "duplikate": int,
                                "angereichert": int, "fehler": int,
                                "neu_pro_quelle": Counter}
    """
    neu_pro_quelle: Counter = Counter()
    if not events:
        logger.info("Keine Events zum Speichern übergeben.")
        return {"gespeichert": 0, "duplikate": 0, "angereichert": 0, "fehler": 0, "neu_pro_quelle": neu_pro_quelle}

    db = get_supabase_client()
    _quellen_spalte_pruefen(db)
    _ticket_spalte_pruefen(db)
    gespeichert = 0
    duplikate = 0
    angereichert = 0
    fehler = 0
    tagesbestand: dict[str, list[dict]] = {}  # Datum → gespeicherte Events (für den Ähnlichkeitsabgleich)

    for event in events:
        # Server-seitige Felder, noch nicht existierende DB-Spalten und interne Felder ("_scraper") entfernen
        datensatz = {
            k: v for k, v in event.items()
            if k not in _IGNORE_FELDER and k not in _NICHT_IN_DB and not k.startswith("_")
        }
        # Alle Quellen des Events (Deduplizierung hat sie in QUELLEN_FELD gesammelt; Plan Quellen-Ausbau 4.3)
        if datensatz.get("quelle_name") and _QUELLEN_SPALTE["da"]:
            datensatz["quellen"] = event.get(QUELLEN_FELD) or [quellen_eintrag(event, _jetzt_iso())]
        # Ticket-Link nur speichern, wenn es die Spalte gibt; leere Werte gar nicht erst mitschicken
        if not _TICKET_SPALTE["da"] or not datensatz.get("ticket_url"):
            datensatz.pop("ticket_url", None)
        # Einheitliche Schreibweise für freien Eintritt („Eintritt frei“, „gratis“ … → „kostenlos“)
        if datensatz.get("preis"):
            datensatz["preis"] = preis_normalisieren(datensatz["preis"])

        titel = event.get("titel", "?")
        datum = event.get("datum", "?")
        ort = event.get("ort", "?")

        try:
            # Schritt 0: Event, das die Redaktion umbenannt oder verschoben hat (abgleich_* = Werte der Quelle)
            bestehendes = _abgleich_redaktion(db, titel, datum, ort, event.get("uhrzeit"))

            # Schritt 1: Prüfen ob Event bereits in DB vorhanden – gleicher Titel + Datum + Ort und
            # gleiche Uhrzeit (oder bei einem fehlt sie). Andere Uhrzeit = weiterer Termin am selben Tag.
            if bestehendes is None:
                treffer = (
                    db.table("events")
                    .select("id," + _abgleich_spalten())
                    .eq("titel", titel)
                    .eq("datum", datum)
                    .eq("ort", ort)
                    .execute()
                )
                neue_zeit = _uhrzeit_hhmm(event.get("uhrzeit"))
                bestehendes = next(
                    (
                        z for z in (treffer.data or [])
                        if neue_zeit is None or _uhrzeit_hhmm(z.get("uhrzeit")) in (None, neue_zeit)
                    ),
                    None,
                )

            if bestehendes is None:
                # Slug generieren falls nicht vorhanden
                if not datensatz.get("slug"):
                    slug = slug_fuer_event(event)
                    if slug:
                        datensatz["slug"] = slug

                # Schritt 2: Gleicher Slug schon vergeben? Der Slug normalisiert Groß-/Kleinschreibung,
                # Umlaute, Satzzeichen und kürzt den Ort – so fallen Duplikate aus anderen Quellen auf
                # ("DIE MÖWE" vs. "Die Möwe"). Gleiche Uhrzeit = Duplikat, andere Uhrzeit = weitere Vorstellung.
                if datensatz.get("slug"):
                    bestehendes, freier_slug = _slug_pruefen(db, datensatz["slug"], datensatz.get("uhrzeit"))
                    if bestehendes is None:
                        datensatz["slug"] = freier_slug

            if bestehendes is None:
                # Schritt 3: Dasselbe Event in anderer Schreibweise (Titel/Ortsname leicht anders, z.B. „zakk – Studio“
                # vs. „zakk - Zentrum für …“) – gleiche Uhrzeit, bei anderer Quelle auch Einlass/Beginn (≤ 2 Std.) oder
                # fehlende Uhrzeit. Der interne Titel-Status („ENTFÄLLT!“ entfernt) fließt in den Abgleich mit ein.
                abgleich = {**datensatz, TITEL_STATUS_FELD: event.get(TITEL_STATUS_FELD)}
                bestehendes = bester_treffer(_tagesbestand(db, datum, tagesbestand), abgleich)
                if bestehendes is not None:
                    logger.info("Duplikat über Ähnlichkeit erkannt: '%s' ≈ '%s' (%s)",
                                titel[:40], (bestehendes.get("titel") or "")[:40], datum)

            if bestehendes is None:
                # Neues Event: direkt einfügen
                antwort = db.table("events").insert(datensatz).execute()
                # Für den Ähnlichkeitsabgleich späterer Events dieses Laufs merken
                if datum in tagesbestand and antwort.data:
                    from pipeline.ort_zuordnung import annotieren
                    tagesbestand[datum].append(annotieren(antwort.data[0]))
                gespeichert += 1
                neu_pro_quelle[event.get("_scraper") or event.get("quelle_name") or "?"] += 1

            else:
                # Duplikat: Anreicherung prüfen
                duplikate += 1
                alte_quelle = bestehendes.get("quelle_name")
                # Rang aus dem Anzeigenamen (`_scraper`) – datensatz enthält die „_“-Felder nicht mehr
                update = _anreicherungs_update_bauen(
                    bestehendes, datensatz, bool(event.get(KATEGORIE_FEST_FELD)), quellen_rang(event)
                )

                if update:
                    db.table("events").update(update).eq("id", bestehendes["id"]).execute()
                    # Zwischengespeicherten Stand nachziehen (Tagesbestand nutzt dieselben Dicts)
                    bestehendes.update(update)
                    angereichert += 1
                    if "quelle_name" in update:
                        logger.info("Quelle gewechselt: '%s' → '%s' für '%s' (%s)",
                                    alte_quelle, update["quelle_name"], titel[:40], datum)
                    logger.info(
                        "Duplikat angereichert in DB: '%s' (%s) – Felder: %s",
                        titel[:40], datum, ", ".join(update.keys()),
                    )
                else:
                    logger.debug(
                        "Duplikat ohne neue Daten übersprungen: '%s' (%s)",
                        titel[:40], datum,
                    )

        except Exception as e:
            fehler += 1
            logger.error(
                "Fehler beim Speichern von '%s' (%s): %s",
                titel, datum, str(e),
            )

    logger.info(
        "Speicherung abgeschlossen – Neu: %d | Duplikate: %d | Angereichert: %d | Fehler: %d",
        gespeichert, duplikate, angereichert, fehler,
    )
    return {
        "gespeichert": gespeichert, "duplikate": duplikate, "angereichert": angereichert,
        "fehler": fehler, "neu_pro_quelle": neu_pro_quelle,
    }
