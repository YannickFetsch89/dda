"""
seo_aufraeumen.py – Dashboard-Tab „SEO-Aufräumen“
Listet Events, die seit mehr als 12 Monaten vorbei sind. Pro Event (oder gesammelt) entscheidet ein
Admin: behalten, 301-Weiterleitung (Reihe, Ortssuche oder Kategorie – nie die Startseite) oder 410 Gone.
Gespeichert wird in event_seo_entscheidungen; die Website (web/proxy.ts) liefert es aus.
Nichts passiert automatisch – Grundlage sind die Search-Console-Daten.
"""
import csv
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


def kandidaten_laden(db: Client, heute: date) -> list[dict]:
    """Events, deren letzter Tag mehr als 12 Monate zurückliegt (älteste zuerst)."""
    grenze = (heute - timedelta(days=ABGELAUFEN_SEIT_TAGE)).isoformat()
    events: list[dict] = []
    for seite in range(MAX_KANDIDATEN // SEITE):
        daten = (db.table("events").select("id, titel, datum, datum_bis, ort, kategorie, slug, reihe:reihen(slug)")
                 .eq("abgelehnt", False).not_.is_("slug", "null")
                 .or_(f"datum_bis.lt.{grenze},and(datum_bis.is.null,datum.lt.{grenze})")
                 .order("datum").order("id").range(seite * SEITE, (seite + 1) * SEITE - 1)
                 .execute().data or [])
        events.extend(daten)
        if len(daten) < SEITE:
            break
    return events


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
    try:
        events = kandidaten_laden(db, date.today())
        entscheidungen = {z["event_id"]: z for z in (db.table("event_seo_entscheidungen")
                                                       .select("event_id, aktion, ziel").execute().data or [])}
    except Exception as e:
        st.error(f"Daten konnten nicht geladen werden (SQL database/event_seo_2026-11-05.sql ausgeführt?): {e}")
        return

    offen = [e for e in events if e["id"] not in entscheidungen]
    a, b, c = st.columns(3)
    a.metric("Seit > 12 Monaten vorbei", len(events))
    b.metric("Noch offen", len(offen))
    c.metric("Entschieden", len(events) - len(offen))
    if not events:
        st.info("Noch keine Events, die seit mehr als 12 Monaten vorbei sind.")
        return
    if len(events) >= MAX_KANDIDATEN:
        st.warning(f"Es werden nur die ältesten {MAX_KANDIDATEN} Events gezeigt. Erst diese entscheiden – "
                   "danach erscheinen die nächsten.")

    st.download_button("CSV für den Abgleich mit der Search Console", _csv(events, entscheidungen),
                       file_name=f"seo-kandidaten-{date.today().isoformat()}.csv", mime="text/csv")

    nur_offen = st.checkbox("Nur noch nicht entschiedene zeigen", value=True)
    liste = offen if nur_offen else events
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
    # Key hängt an den Schaltern: sonst behält die Tabelle alte Häkchen, wenn „Alle auswählen“ wechselt
    bearbeitet = st.data_editor(tabelle, hide_index=True, use_container_width=True,
                                key=f"seo_tabelle_{int(alle)}_{int(nur_offen)}",
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
                       "Hinweis: Google wertet eine 301 als dauerhaft – Zurücknehmen wirkt für Besucher sofort, "
                       "bei Google erst nach dem nächsten Crawl.")
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
