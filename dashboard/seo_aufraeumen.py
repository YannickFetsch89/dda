"""
seo_aufraeumen.py – Dashboard-Tab „SEO-Aufräumen“
Listet Events, die seit mehr als 12 Monaten vorbei sind. Pro Event (oder gesammelt) entscheidet ein
Admin: behalten, 301-Weiterleitung (Reihe, Ortssuche oder Kategorie – nie die Startseite) oder 410 Gone.
Gespeichert wird in event_seo_entscheidungen; die Website (web/proxy.ts) liefert es aus.
Nichts passiert automatisch – Grundlage sind die Search-Console-Daten.
"""
import csv
import hashlib
import io
import logging
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

import streamlit as st
from supabase import Client

logger = logging.getLogger(__name__)

SITE_URL = "https://diesdas.events"
ABGELAUFEN_SEIT_TAGE = 365
SEITE = 1000
MAX_KANDIDATEN = 5000

AKTIONEN = {
    "behalten": "Behalten (Seite bleibt, HTTP 200)",
    "reihe": "301 → Reihenseite (nur Events mit Reihe)",
    "ort": "301 → Ortssuche (/entdecken?q=<Ort>)",
    "kategorie": "301 → Kategorie (/entdecken?kategorie=…)",
    "gone": "410 Gone",
}


def web_kategorie(kategorie: str | None) -> str:
    """DB-Kategorie → Website-Slug (family → familie)."""
    k = (kategorie or "sonstiges").strip().lower()
    return "familie" if k == "family" else k


def event_url(e: dict) -> str:
    return f"{SITE_URL}/event/{quote(web_kategorie(e.get('kategorie')))}/{quote(e['slug'])}"


def _reihe_slug(e: dict) -> str | None:
    r = e.get("reihe")
    if isinstance(r, list):
        r = r[0] if r else None
    return r.get("slug") if isinstance(r, dict) else None


def ziel_fuer(e: dict, art: str) -> str | None:
    """Internes Weiterleitungsziel für ein Event – None, wenn es dafür kein Ziel gibt."""
    if art == "reihe":
        slug = _reihe_slug(e)
        return f"/reihe/{quote(slug)}" if slug else None
    if art == "ort":
        ort = (e.get("ort") or "").strip()
        return f"/entdecken?q={quote(ort)}&datum=alle" if ort else None
    if art == "kategorie":
        return f"/entdecken?kategorie={quote(web_kategorie(e.get('kategorie')))}&datum=alle"
    return None


def entscheidungen_bauen(events: list[dict], art: str, admin_id: str | None) -> tuple[list[dict], list[dict]]:
    """
    Zeilen für event_seo_entscheidungen. Gibt (zeilen, übersprungen) zurück – übersprungen sind z.B.
    Events ohne Reihe bei „301 → Reihenseite“.
    """
    jetzt = datetime.now(timezone.utc).isoformat()
    zeilen, uebersprungen = [], []
    for e in events:
        if art == "behalten":
            aktion, ziel = "behalten", None
        elif art == "gone":
            aktion, ziel = "gone", None
        else:
            aktion, ziel = "weiterleiten", ziel_fuer(e, art)
            if not ziel:
                uebersprungen.append(e)
                continue
        zeilen.append({"event_id": e["id"], "slug": e["slug"], "aktion": aktion, "ziel": ziel,
                       "entschieden_am": jetzt, "entschieden_von": admin_id})
    return zeilen, uebersprungen


def _abgelaufen_filter(heute: date) -> str:
    grenze = (heute - timedelta(days=ABGELAUFEN_SEIT_TAGE)).isoformat()
    return f"datum_bis.lt.{grenze},and(datum_bis.is.null,datum.lt.{grenze})"


def kandidaten_laden(db: Client, heute: date, ohne: set[str] | None = None,
                     max_anzahl: int = MAX_KANDIDATEN) -> tuple[list[dict], bool]:
    """
    Events, deren letzter Tag mehr als 12 Monate zurückliegt (älteste zuerst), ohne die IDs in `ohne`
    (z.B. schon entschiedene). Blättert weiter, bis max_anzahl beisammen sind.
    Returns: (events, es_gibt_noch_mehr)
    """
    ohne = ohne or set()
    events: list[dict] = []
    for seite in range(500):  # bis 500.000 Zeilen
        daten = (db.table("events").select("id, titel, datum, datum_bis, ort, kategorie, slug, reihe:reihen(slug)")
                 .eq("abgelehnt", False).not_.is_("slug", "null").or_(_abgelaufen_filter(heute))
                 .order("datum").order("id").range(seite * SEITE, (seite + 1) * SEITE - 1)
                 .execute().data or [])
        for e in daten:
            if e["id"] in ohne:
                continue
            if len(events) >= max_anzahl:
                return events, True
            events.append(e)
        if len(daten) < SEITE:
            break
    return events, False


def kandidaten_ids(db: Client, heute: date) -> set[str]:
    """IDs aller aktuellen Kandidaten (nur die Spalte id, seitenweise) – Grundlage der Kennzahlen."""
    ids: set[str] = set()
    for seite in range(500):
        daten = (db.table("events").select("id").eq("abgelehnt", False).not_.is_("slug", "null")
                 .or_(_abgelaufen_filter(heute)).order("id").range(seite * SEITE, (seite + 1) * SEITE - 1)
                 .execute().data or [])
        ids.update(z["id"] for z in daten)
        if len(daten) < SEITE:
            break
    return ids


def entscheidungen_laden(db: Client) -> dict[str, dict]:
    """Alle Entscheidungen, seitenweise (PostgREST liefert höchstens 1.000 Zeilen pro Abfrage)."""
    ergebnis: dict[str, dict] = {}
    for seite in range(500):
        daten = (db.table("event_seo_entscheidungen").select("event_id, aktion, ziel").order("event_id")
                 .range(seite * SEITE, (seite + 1) * SEITE - 1).execute().data or [])
        ergebnis.update({z["event_id"]: z for z in daten})
        if len(daten) < SEITE:
            break
    return ergebnis


def kennzahlen(kandidaten: set[str], entscheidungen: dict) -> tuple[int, int, int]:
    """(gesamt, entschieden, offen) – nur über aktuelle Kandidaten. Entscheidungen zu Events, die keine
    Kandidaten mehr sind (z.B. inzwischen abgelehnt), zählen nicht mit."""
    entschieden = len(kandidaten & set(entscheidungen))
    return len(kandidaten), entschieden, len(kandidaten) - entschieden


def tabellen_schluessel(ids: list[str], alle: bool) -> str:
    """Key des data_editor: ändert sich mit den angezeigten Zeilen – sonst blieben Häkchen nach dem
    Speichern an denselben Zeilennummern hängen und träfen die nachgerückten Events."""
    return f"seo_tabelle_{int(alle)}_" + hashlib.sha1("|".join(ids).encode()).hexdigest()[:16]


def _csv(events: list[dict], entscheidungen: dict) -> bytes:
    puffer = io.StringIO()
    w = csv.writer(puffer, delimiter=";")
    w.writerow(["url", "titel", "datum", "ort", "kategorie", "reihe", "aktion", "ziel"])
    for e in events:
        ent = entscheidungen.get(e["id"], {})
        # Formel-Injection verhindern (Titel/Orte kommen von Scrapern)
        sicher = [str(x or "") for x in [event_url(e), e["titel"], e["datum"], e.get("ort"), e.get("kategorie"),
                                          _reihe_slug(e), ent.get("aktion"), ent.get("ziel")]]
        w.writerow([("'" + s) if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s for s in sicher])
    return puffer.getvalue().encode("utf-8-sig")


def tab_seo_aufraeumen(db: Client) -> None:
    from dashboard.meldungen import _admin_id

    st.subheader("SEO-Aufräumen: lange abgelaufene Events")
    st.caption("Abgelaufene Eventseiten bleiben grundsätzlich online. Hier stehen nur Events, die seit mehr als "
               "12 Monaten vorbei sind. Entscheide anhand der Search-Console-Daten – nichts passiert automatisch. "
               "Weiterleitungen gehen nie auf die Startseite. 301 und 410 sind für Google dauerhafte Signale – "
               "nur wählen, wenn es dabei bleiben soll.")
    nur_offen = st.checkbox("Nur noch nicht entschiedene zeigen", value=True)
    heute = date.today()
    try:
        entscheidungen = entscheidungen_laden(db)
        gesamt, entschieden, offen = kennzahlen(kandidaten_ids(db, heute), entscheidungen)
        # Grenze gilt für die ANGEZEIGTEN Events – bei „nur offene“ also für noch nicht entschiedene
        liste, mehr = kandidaten_laden(db, heute, set(entscheidungen) if nur_offen else None)
    except Exception as e:
        st.error(f"Daten konnten nicht geladen werden (SQL database/event_seo_2026-11-05.sql ausgeführt?): {e}")
        return

    a, b, c = st.columns(3)
    a.metric("Seit > 12 Monaten vorbei", gesamt)
    b.metric("Entschieden", entschieden)
    c.metric("Noch offen", offen)
    if not gesamt:
        st.info("Noch keine Events, die seit mehr als 12 Monaten vorbei sind.")
        return
    if mehr:
        st.warning(f"Es werden die ältesten {MAX_KANDIDATEN} {'offenen ' if nur_offen else ''}Events gezeigt. "
                   "Nach dem Entscheiden rücken die nächsten nach.")

    st.download_button("CSV der angezeigten Events (für den Abgleich mit der Search Console)",
                       _csv(liste, entscheidungen),
                       file_name=f"seo-kandidaten-{heute.isoformat()}.csv", mime="text/csv")

    alle = st.checkbox(f"Alle {len(liste)} angezeigten auswählen", value=False)
    tabelle = [{
        "Auswahl": alle,
        "Datum": e["datum"],
        "Titel": e["titel"],
        "Ort": e.get("ort") or "",
        "Kategorie": web_kategorie(e.get("kategorie")),
        "Reihe": _reihe_slug(e) or "",
        "Entscheidung": (entscheidungen.get(e["id"]) or {}).get("aktion", ""),
        "URL": event_url(e),
    } for e in liste]
    bearbeitet = st.data_editor(tabelle, hide_index=True, use_container_width=True,
                                key=tabellen_schluessel([e["id"] for e in liste], alle),
                                disabled=["Datum", "Titel", "Ort", "Kategorie", "Reihe", "Entscheidung", "URL"],
                                column_config={"URL": st.column_config.LinkColumn("URL")})
    ausgewaehlt = [e for e, zeile in zip(liste, bearbeitet) if zeile.get("Auswahl")]

    art = st.selectbox("Entscheidung für die Auswahl", list(AKTIONEN), format_func=AKTIONEN.get)
    links, rechts = st.columns(2)
    if links.button(f"Für {len(ausgewaehlt)} Event(s) speichern", type="primary", disabled=not ausgewaehlt):
        zeilen, uebersprungen = entscheidungen_bauen(ausgewaehlt, art, _admin_id(db))
        try:
            for i in range(0, len(zeilen), 500):
                db.table("event_seo_entscheidungen").upsert(zeilen[i:i + 500], on_conflict="event_id").execute()
            st.success(f"{len(zeilen)} Entscheidung(en) gespeichert. Die Website übernimmt sie innerhalb von 10 Minuten. "
                       "Hinweis: Google wertet eine 301 als dauerhaft – Zurücknehmen wirkt für Besucher nach "
                       "spätestens 10 Minuten, bei Google erst nach dem nächsten Crawl.")
            if uebersprungen:
                st.warning(f"{len(uebersprungen)} Event(s) ohne passendes Ziel übersprungen (z.B. keine Reihe).")
        except Exception as e:
            st.error(f"Speichern fehlgeschlagen: {e}")
    if rechts.button(f"Entscheidung für {len(ausgewaehlt)} Event(s) zurücknehmen", disabled=not ausgewaehlt):
        try:
            ids = [e["id"] for e in ausgewaehlt]
            for i in range(0, len(ids), 200):
                db.table("event_seo_entscheidungen").delete().in_("event_id", ids[i:i + 200]).execute()
            st.success("Zurückgenommen – für Besucher sind die Seiten nach spätestens 10 Minuten wieder normal "
                       "erreichbar. Google übernimmt das erst beim nächsten Crawl (eine 301 kann länger nachwirken).")
        except Exception as e:
            st.error(f"Zurücknehmen fehlgeschlagen: {e}")
