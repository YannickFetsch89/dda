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

from pipeline.deduplication import kategorie_ersetzen
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

# Spalten die noch nicht in der DB existieren – werden aus Inserts/Selects herausgefiltert
# Nachtragen via Supabase Dashboard: ALTER TABLE events ADD COLUMN instagram_location_id TEXT;
# post_typ (feed | reel) setzen einige Tier-3-Scraper, die Pipeline nutzt es aber noch nicht
_NICHT_IN_DB: set[str] = {"instagram_location_id", "post_typ"}

# Erkennung von Rausgegangen-Bildern (imageflow.rausgegangen.de / s3/.../rausgegangen)
_RAUSGEGANGEN_MUSTER = re.compile(r"rausgegangen", re.IGNORECASE)


def _ist_rausgegangen_bild(bild_url: Optional[str]) -> bool:
    """Erkennt ob eine Bild-URL von Rausgegangen stammt."""
    return bool(bild_url and _RAUSGEGANGEN_MUSTER.search(bild_url))


def _anreicherungs_update_bauen(bestehendes: dict, neu: dict, neue_quelle: Optional[str] = None) -> dict:
    """
    Berechnet welche Felder eines bestehenden DB-Eintrags angereichert werden sollen.

    Regeln:
    - Feld wird ergänzt wenn im bestehenden Eintrag None/leer und im neuen Eintrag belegt
    - bild_url: Rausgegangen-Bild wird durch nicht-Rausgegangen-Bild ersetzt,
      auch wenn bereits vorhanden

    Args:
        bestehendes: Aktueller DB-Eintrag
        neu: Neu eingehender Event

    Returns:
        Dict mit Feldern die aktualisiert werden sollen (leer = kein Update nötig)
    """
    update: dict = {}

    for feld in _ANREICHERBARE_FELDER:
        db_wert = bestehendes.get(feld)
        neu_wert = neu.get(feld)

        if feld == "bild_url":
            # Rausgegangen-Bild durch bessere Quelle ersetzen
            if _ist_rausgegangen_bild(db_wert) and neu_wert and not _ist_rausgegangen_bild(neu_wert):
                update[feld] = neu_wert
            elif not db_wert and neu_wert:
                update[feld] = neu_wert
        elif feld == "kategorie" and kategorie_ersetzen(db_wert, neu_wert, neue_quelle):
            # z.B. Kalender lieferte "kultur", Führungs-Scraper weiß: "stadtfuehrung"
            update[feld] = neu_wert
        else:
            if not db_wert and neu_wert:
                update[feld] = neu_wert

    return update


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
            .select("id,slug,uhrzeit," + ",".join(f for f in _ANREICHERBARE_FELDER if f != "uhrzeit"))
            .like("slug", f"{basis}%")
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
    gespeichert = 0
    duplikate = 0
    angereichert = 0
    fehler = 0

    for event in events:
        # Server-seitige Felder, noch nicht existierende DB-Spalten und interne Felder ("_scraper") entfernen
        datensatz = {
            k: v for k, v in event.items()
            if k not in _IGNORE_FELDER and k not in _NICHT_IN_DB and not k.startswith("_")
        }

        titel = event.get("titel", "?")
        datum = event.get("datum", "?")
        ort = event.get("ort", "?")

        try:
            # Schritt 1: Prüfen ob Event bereits in DB vorhanden – gleicher Titel + Datum + Ort und
            # gleiche Uhrzeit (oder bei einem fehlt sie). Andere Uhrzeit = weiterer Termin am selben Tag.
            treffer = (
                db.table("events")
                .select("id," + ",".join(_ANREICHERBARE_FELDER))
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
                # Neues Event: direkt einfügen
                db.table("events").insert(datensatz).execute()
                gespeichert += 1
                neu_pro_quelle[event.get("_scraper") or event.get("quelle_name") or "?"] += 1

            else:
                # Duplikat: Anreicherung prüfen
                duplikate += 1
                update = _anreicherungs_update_bauen(
                    bestehendes, datensatz, event.get("_scraper") or event.get("quelle_name")
                )

                if update:
                    db.table("events").update(update).eq("id", bestehendes["id"]).execute()
                    angereichert += 1
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
