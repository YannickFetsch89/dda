"""
app.py – DiesDasDüsseldorf Admin-Dashboard
Streamlit-basiertes Backend zur Verwaltung von Events vor dem Instagram-Posting.

Prinzip: Opt-out statt Opt-in.
Alle aufbereiteten Events werden automatisch gepostet – außer sie werden
hier aktiv abgelehnt. Featured-Tiers können manuell vergeben werden.

Starten: streamlit run dashboard/app.py
"""
import os
import sys
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

# Projektpfad hinzufügen damit Imports funktionieren
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# ── Konfiguration ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="DiesDasDüsseldorf – Admin",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)

KATEGORIE_EMOJI = {
    "musik":     "🎵",
    "kultur":    "🎭",
    "food":      "🍔",
    "sport":     "⚽",
    "outdoor":   "🌿",
    "community": "🤝",
    "nightlife": "🌙",
    "family":    "👨‍👩‍👧",
    "dating":    "💘",
    "sonstiges": "📌",
}

FEATURED_LABEL = {
    "tipp_des_tages":       ("⭐", "Tipp des Tages"),
    "highlight_der_woche":  ("🔥", "Highlight der Woche"),
    "top_event_des_monats": ("👑", "Top-Event des Monats"),
}


# ── Datenbankverbindung ───────────────────────────────────────────────────────

@st.cache_resource
def get_db() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        st.error("SUPABASE_URL / SUPABASE_KEY fehlen in .env")
        st.stop()
    return create_client(url, key)


def events_laden(
    von: date,
    bis: date,
    nur_abgelehnte: bool = False,
    nur_featured: bool = False,
) -> list[dict]:
    """Lädt Events aus Supabase für den angegebenen Zeitraum."""
    db = get_db()
    try:
        q = (
            db.table("events")
            .select(
                "id, titel, datum, uhrzeit, ort, kategorie, beschreibung, "
                "preis, quelle_name, quelle_url, bild_url, instagram_caption, "
                "status, abgelehnt, tipp_des_tages, highlight_der_woche, "
                "top_event_des_monats, erstellt_am"
            )
            .gte("datum", von.isoformat())
            .lte("datum", bis.isoformat())
            .order("datum", desc=False)
            .order("uhrzeit", desc=False)
            .limit(500)
        )

        if nur_abgelehnte:
            q = q.eq("abgelehnt", True)
        else:
            if not nur_featured:
                q = q.eq("abgelehnt", False)

        if nur_featured:
            # Mindestens eines der Featured-Felder muss True sein
            q = (
                db.table("events")
                .select(
                    "id, titel, datum, uhrzeit, ort, kategorie, beschreibung, "
                    "preis, quelle_name, quelle_url, bild_url, instagram_caption, "
                    "status, abgelehnt, tipp_des_tages, highlight_der_woche, "
                    "top_event_des_monats, erstellt_am"
                )
                .or_("tipp_des_tages.eq.true,highlight_der_woche.eq.true,top_event_des_monats.eq.true")
                .order("datum", desc=False)
                .limit(200)
            )

        return q.execute().data or []
    except Exception as e:
        st.error(f"Datenbankfehler: {e}")
        return []


def stats_laden() -> dict:
    """Lädt Gesamtstatistiken aus der Datenbank."""
    db = get_db()
    heute = date.today()
    try:
        gesamt = db.table("events").select("id", count="exact").execute().count or 0
        aufbereitet = db.table("events").select("id", count="exact").eq("status", "aufbereitet").eq("abgelehnt", False).execute().count or 0
        gepostet = db.table("events").select("id", count="exact").eq("status", "gepostet").execute().count or 0
        abgelehnt = db.table("events").select("id", count="exact").eq("abgelehnt", True).execute().count or 0
        featured = db.table("events").select("id", count="exact").or_(
            "tipp_des_tages.eq.true,highlight_der_woche.eq.true,top_event_des_monats.eq.true"
        ).execute().count or 0
        heute_count = db.table("events").select("id", count="exact").eq("datum", heute.isoformat()).eq("abgelehnt", False).execute().count or 0
        return {
            "gesamt": gesamt,
            "aufbereitet": aufbereitet,
            "gepostet": gepostet,
            "abgelehnt": abgelehnt,
            "featured": featured,
            "heute": heute_count,
        }
    except Exception as e:
        return {"gesamt": 0, "aufbereitet": 0, "gepostet": 0, "abgelehnt": 0, "featured": 0, "heute": 0}


def feld_toggeln(event_id: str, feld: str, wert: bool) -> bool:
    """Setzt ein Boolean-Feld eines Events in der Datenbank."""
    db = get_db()
    try:
        db.table("events").update({feld: wert}).eq("id", event_id).execute()
        return True
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren: {e}")
        return False


# ── UI-Komponenten ────────────────────────────────────────────────────────────

def featured_badge(event: dict) -> str:
    """Erstellt einen Badge-Text für Featured-Events."""
    badges = []
    for feld, (emoji, label) in FEATURED_LABEL.items():
        if event.get(feld):
            badges.append(f"{emoji} {label}")
    return "  ·  ".join(badges)


def event_karte(event: dict, key_prefix: str):
    """Rendert eine Event-Karte mit allen Aktionsbuttons."""
    eid = event["id"]
    titel = event.get("titel", "–")
    datum_str = event.get("datum", "")
    uhrzeit = event.get("uhrzeit", "")
    ort = event.get("ort", "–")
    kategorie = event.get("kategorie", "sonstiges")
    beschreibung = event.get("beschreibung") or ""
    caption = event.get("instagram_caption") or ""
    bild_url = event.get("bild_url") or ""
    quelle = event.get("quelle_name", "")
    preis = event.get("preis") or ""
    abgelehnt = event.get("abgelehnt", False)
    status = event.get("status", "")

    emoji = KATEGORIE_EMOJI.get(kategorie, "📌")
    badge = featured_badge(event)

    # Datum formatieren
    try:
        d = date.fromisoformat(datum_str)
        datum_anzeige = d.strftime("%a, %d.%m.%Y")
    except Exception:
        datum_anzeige = datum_str

    uhrzeit_anzeige = uhrzeit[:5] if uhrzeit else ""
    zeitangabe = f"{datum_anzeige}  {uhrzeit_anzeige}".strip()

    # Rahmenfarbe je Status
    if abgelehnt:
        border = "#e74c3c"
    elif badge:
        border = "#f39c12"
    else:
        border = "#2ecc71"

    with st.container(border=True):
        # Header-Zeile
        col_info, col_bild = st.columns([3, 1])

        with col_info:
            st.markdown(f"### {emoji} {titel}")
            st.caption(f"📅 {zeitangabe}  ·  📍 {ort}  ·  🏷️ {kategorie.capitalize()}  ·  📰 {quelle}" +
                       (f"  ·  💶 {preis}" if preis else ""))
            if badge:
                st.markdown(f"**{badge}**")
            if abgelehnt:
                st.warning("🚫 Abgelehnt – wird nicht gepostet")
            if beschreibung:
                st.markdown(f"_{beschreibung[:200]}_")

        with col_bild:
            if bild_url:
                st.image(bild_url, use_container_width=True)

        # Caption-Expander
        if caption:
            with st.expander("Instagram-Caption anzeigen"):
                st.text(caption)

        # Aktionsbuttons
        st.divider()
        btn_cols = st.columns(5)

        # Ablehnen / Freigeben
        with btn_cols[0]:
            if abgelehnt:
                if st.button("✅ Freigeben", key=f"{key_prefix}_freigeben_{eid}", use_container_width=True):
                    if feld_toggeln(eid, "abgelehnt", False):
                        st.success("Freigegeben!")
                        st.cache_data.clear()
                        st.rerun()
            else:
                if st.button("🚫 Ablehnen", key=f"{key_prefix}_ablehnen_{eid}", use_container_width=True, type="secondary"):
                    if feld_toggeln(eid, "abgelehnt", True):
                        st.warning("Abgelehnt.")
                        st.cache_data.clear()
                        st.rerun()

        # Tipp des Tages
        with btn_cols[1]:
            ist_tipp = event.get("tipp_des_tages", False)
            label = "⭐ Tipp ✓" if ist_tipp else "⭐ Tipp des Tages"
            btn_type = "primary" if ist_tipp else "secondary"
            if st.button(label, key=f"{key_prefix}_tipp_{eid}", use_container_width=True, type=btn_type):
                if feld_toggeln(eid, "tipp_des_tages", not ist_tipp):
                    st.cache_data.clear()
                    st.rerun()

        # Highlight der Woche
        with btn_cols[2]:
            ist_highlight = event.get("highlight_der_woche", False)
            label = "🔥 Highlight ✓" if ist_highlight else "🔥 Highlight der Woche"
            btn_type = "primary" if ist_highlight else "secondary"
            if st.button(label, key=f"{key_prefix}_highlight_{eid}", use_container_width=True, type=btn_type):
                if feld_toggeln(eid, "highlight_der_woche", not ist_highlight):
                    st.cache_data.clear()
                    st.rerun()

        # Top-Event des Monats
        with btn_cols[3]:
            ist_top = event.get("top_event_des_monats", False)
            label = "👑 Top-Event ✓" if ist_top else "👑 Top-Event des Monats"
            btn_type = "primary" if ist_top else "secondary"
            if st.button(label, key=f"{key_prefix}_top_{eid}", use_container_width=True, type=btn_type):
                if feld_toggeln(eid, "top_event_des_monats", not ist_top):
                    st.cache_data.clear()
                    st.rerun()

        # Quelle-Link
        with btn_cols[4]:
            quelle_url = event.get("quelle_url", "")
            if quelle_url:
                st.link_button("🔗 Original", quelle_url, use_container_width=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar_rendern():
    with st.sidebar:
        st.title("🎭 DiesDasDüsseldorf")
        st.caption("Admin-Dashboard")
        st.divider()

        # Stats
        stats = stats_laden()
        st.metric("Heute geplant", stats["heute"])
        st.metric("Bereit zum Posten", stats["aufbereitet"])
        st.metric("Bereits gepostet", stats["gepostet"])

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Abgelehnt", stats["abgelehnt"])
        with col2:
            st.metric("Featured", stats["featured"])

        st.divider()

        # Datumsfilter
        st.subheader("Zeitraum")
        heute = date.today()
        von = st.date_input("Von", value=heute, key="filter_von")
        bis = st.date_input("Bis", value=heute + timedelta(days=13), key="filter_bis")

        st.divider()

        # Kategoriefilter
        st.subheader("Kategorie")
        alle_kategorien = ["Alle"] + list(KATEGORIE_EMOJI.keys())
        kategorie_filter = st.selectbox("Filtern nach", alle_kategorien, key="filter_kategorie")

        st.divider()

        # Pipeline-Steuerung
        st.subheader("Pipeline")
        if st.button("🔄 Jetzt neu scrapen", use_container_width=True, type="primary"):
            with st.spinner("Pipeline läuft..."):
                try:
                    import subprocess
                    result = subprocess.run(
                        ["python", "main.py", "--jetzt"],
                        capture_output=True,
                        text=True,
                        timeout=600,
                        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    )
                    if result.returncode == 0:
                        st.success("Pipeline abgeschlossen!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Fehler: {result.stderr[-500:]}")
                except subprocess.TimeoutExpired:
                    st.error("Timeout – Pipeline läuft im Hintergrund weiter.")
                except Exception as e:
                    st.error(f"Fehler: {e}")

        return von, bis, kategorie_filter


# ── Hauptansicht ──────────────────────────────────────────────────────────────

def events_filtern_nach_kategorie(events: list[dict], kategorie: str) -> list[dict]:
    if kategorie == "Alle":
        return events
    return [e for e in events if e.get("kategorie") == kategorie]


def tab_tagesplaner(von: date, bis: date, kategorie_filter: str):
    """Zeigt Events tageweise gruppiert im Vorschauzeitraum."""
    events = events_laden(von, bis)
    events = events_filtern_nach_kategorie(events, kategorie_filter)

    if not events:
        st.info("Keine Events im gewählten Zeitraum gefunden.")
        return

    # Nach Datum gruppieren
    tage: dict[str, list[dict]] = {}
    for event in events:
        d = event.get("datum", "")
        tage.setdefault(d, []).append(event)

    for datum_str, tages_events in tage.items():
        try:
            d = date.fromisoformat(datum_str)
            ist_heute = d == date.today()
            ist_morgen = d == date.today() + timedelta(days=1)
            label = d.strftime("%A, %d. %B %Y")
            if ist_heute:
                label = f"📍 Heute – {label}"
            elif ist_morgen:
                label = f"➡️ Morgen – {label}"

            anzahl_frei = sum(1 for e in tages_events if not e.get("abgelehnt"))
            anzahl_abg = sum(1 for e in tages_events if e.get("abgelehnt"))
        except Exception:
            label = datum_str
            anzahl_frei = len(tages_events)
            anzahl_abg = 0

        badge_str = f"✅ {anzahl_frei} geplant"
        if anzahl_abg:
            badge_str += f"  ·  🚫 {anzahl_abg} abgelehnt"

        with st.expander(f"**{label}**  —  {badge_str}", expanded=ist_heute or ist_morgen):
            for event in tages_events:
                event_karte(event, key_prefix="tagesplaner")


def tab_event_liste(von: date, bis: date, kategorie_filter: str):
    """Zeigt alle Events als scrollbare Liste mit Filteroptionen."""
    status_filter = st.radio(
        "Status",
        ["Alle (nicht abgelehnt)", "Nur Featured", "Nur Abgelehnte"],
        horizontal=True,
        key="status_filter",
    )

    nur_abgelehnte = status_filter == "Nur Abgelehnte"
    nur_featured = status_filter == "Nur Featured"
    events = events_laden(von, bis, nur_abgelehnte=nur_abgelehnte, nur_featured=nur_featured)
    events = events_filtern_nach_kategorie(events, kategorie_filter)

    st.caption(f"{len(events)} Events gefunden")

    for event in events:
        event_karte(event, key_prefix="liste")


def tab_featured(von: date, bis: date):
    """Zeigt alle als Featured markierten Events."""
    events = events_laden(von, bis, nur_featured=True)

    if not events:
        st.info("Noch keine Featured-Events ausgewählt.")
        st.markdown("""
        **So funktioniert es:**
        - **⭐ Tipp des Tages** – Ein besonders empfehlenswertes Event, täglich auswählbar
        - **🔥 Highlight der Woche** – Das beste Event der Woche
        - **👑 Top-Event des Monats** – Das absolute Highlight im Monat

        Featured-Events werden beim Instagram-Posting bevorzugt behandelt (zuerst gepostet).
        Du kannst die Markierungen jederzeit im Tagesplaner oder der Event-Liste setzen.
        """)
        return

    # Gruppiert nach Tier
    for feld, (emoji, label) in FEATURED_LABEL.items():
        tier_events = [e for e in events if e.get(feld)]
        if not tier_events:
            continue

        st.subheader(f"{emoji} {label}")
        for event in tier_events:
            event_karte(event, key_prefix=f"featured_{feld}")


# ── Hauptprogramm ─────────────────────────────────────────────────────────────

def main():
    von, bis, kategorie_filter = sidebar_rendern()

    st.title("🎭 DiesDasDüsseldorf – Event-Planer")

    tab1, tab2, tab3 = st.tabs([
        "📅 Tagesplaner",
        "📋 Event-Liste",
        "⭐ Featured Events",
    ])

    with tab1:
        tab_tagesplaner(von, bis, kategorie_filter)

    with tab2:
        tab_event_liste(von, bis, kategorie_filter)

    with tab3:
        tab_featured(von, bis)


if __name__ == "__main__":
    main()
