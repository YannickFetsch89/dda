"""
meldungen.py – DiesDasDüsseldorf Admin-Dashboard
Tabs „Meldungen“ (über die Website eingereichte Events prüfen, bearbeiten, freigeben/ablehnen)
und „Newsletter“ (Anmeldungen ansehen und als CSV herunterladen).

Freigabe einer Meldung:
  1. Bild aus dem privaten Bucket „event-meldungen“ in den öffentlichen Bucket „event-bilder“ kopieren
  2. Event in „events“ anlegen (Slug wie die Pipeline, Stadtteil über den Stadtteil-Mapper,
     status = 'neu' mit Beschreibung → die Pipeline erstellt später wie gewohnt die Instagram-Caption)
  3. Meldung auf „freigegeben“ setzen und mit dem Event verknüpfen
Ablehnen: Meldung auf „abgelehnt“ setzen (mit Grund) und das Bild aus dem privaten Bucket löschen.

Alles läuft mit dem Login des Admins (RLS: database/meldungen_newsletter_2026-11-05.sql).
"""
import csv
import io
import logging
import re
from datetime import date, datetime, time, timezone

import streamlit as st
from supabase import Client

from pipeline.slug_generator import slug_fuer_event, slug_mit_suffix
from pipeline.stadtteil_mapper import stadtteil_batch_zuordnen

logger = logging.getLogger(__name__)

KATEGORIEN = ["kultur", "musik", "food", "sport", "outdoor", "stadtfuehrung", "community",
              "nightlife", "family", "dating", "sonstiges"]
QUELLE_NAME = "Event-Meldung"
QUELLE_STANDARD_URL = "https://diesdas.events/event-melden"


def _kuerzen(text: str, laenge: int = 300) -> str:
    """Beschreibung auf die Event-Höchstlänge kürzen, möglichst am Satzende."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= laenge:
        return text
    stueck = text[: laenge - 1]
    ende = max(stueck.rfind(". "), stueck.rfind("! "), stueck.rfind("? "))
    if ende >= laenge // 2:
        return stueck[: ende + 1]
    return stueck[: stueck.rfind(" ")].rstrip(" ,;:–-") + "…"


def _admin_id(db: Client) -> str | None:
    try:
        return db.auth.get_user().user.id
    except Exception:
        return None


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bild_vorschau(db: Client, pfad: str | None) -> None:
    if not pfad:
        st.caption("Kein Bild hochgeladen.")
        return
    try:
        signiert = db.storage.from_("event-meldungen").create_signed_url(pfad, 3600)
        url = signiert.get("signedURL") or signiert.get("signedUrl") or signiert.get("signed_url")
        if url:
            st.image(url, use_container_width=True)
        else:
            st.caption("Bild nicht abrufbar.")
    except Exception as e:
        st.caption(f"Bild nicht abrufbar ({e}).")


def _bild_veroeffentlichen(db: Client, meldung: dict) -> str | None:
    """Kopiert das Meldungsbild in den öffentlichen Bucket und gibt die öffentliche URL zurück."""
    pfad = meldung.get("bild_pfad")
    if not pfad or not meldung.get("bild_rechte"):
        return None
    endung = pfad.rsplit(".", 1)[-1].lower()
    typ = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(endung, "image/jpeg")
    daten = db.storage.from_("event-meldungen").download(pfad)
    ziel = f"meldungen/{meldung['id']}.{endung}"
    db.storage.from_("event-bilder").upload(ziel, daten, {"content-type": typ, "upsert": "false"})
    return db.storage.from_("event-bilder").get_public_url(ziel)


def _freigeben(db: Client, meldung: dict, werte: dict) -> str:
    """Legt das Event an und markiert die Meldung als freigegeben. Gibt die Event-ID zurück."""
    bild_url = _bild_veroeffentlichen(db, meldung)
    event = {
        "titel": werte["titel"],
        "datum": werte["datum"].isoformat(),
        "datum_bis": werte["datum_bis"].isoformat() if werte["datum_bis"] else None,
        "uhrzeit": werte["uhrzeit"].strftime("%H:%M") if werte["uhrzeit"] else None,
        "ort": werte["ort"],
        "adresse": werte["adresse"] or None,
        "kategorie": werte["kategorie"],
        "beschreibung": _kuerzen(werte["beschreibung"]),
        "preis": werte["preis"] or None,
        "quelle_name": QUELLE_NAME,
        "quelle_url": werte["link"] or QUELLE_STANDARD_URL,
        "bild_url": bild_url,
        "bild_generiert": False,
        "post_typ": "feed",
        "status": "neu",
    }
    event = stadtteil_batch_zuordnen([event])[0]
    basis = slug_fuer_event(event)
    vergeben = {z["slug"] for z in (db.table("events").select("slug").like("slug", f"{basis}*").execute().data or [])}
    event["slug"] = slug_mit_suffix(basis, vergeben)

    neu = db.table("events").insert(event).execute().data
    event_id = neu[0]["id"] if neu else None
    db.table("event_meldungen").update({
        "status": "freigegeben",
        "event_id": event_id,
        "bearbeitet_am": _jetzt(),
        "bearbeitet_von": _admin_id(db),
    }).eq("id", meldung["id"]).execute()
    return event_id


def _ablehnen(db: Client, meldung: dict, grund: str) -> None:
    db.table("event_meldungen").update({
        "status": "abgelehnt",
        "ablehngrund": grund or None,
        "bearbeitet_am": _jetzt(),
        "bearbeitet_von": _admin_id(db),
    }).eq("id", meldung["id"]).execute()
    if meldung.get("bild_pfad"):
        try:
            db.storage.from_("event-meldungen").remove([meldung["bild_pfad"]])
        except Exception as e:
            logger.warning("Bild der abgelehnten Meldung nicht gelöscht: %s", e)


def _meldung_karte(db: Client, m: dict) -> None:
    rolle = "Veranstalter" if m.get("kontakt_rolle") == "veranstalter" else "Tipp von Besucher"
    kopf = f"{m['datum']} · {m['titel']}  —  eingereicht {m['erstellt_am'][:16].replace('T', ' ')}"
    with st.expander(kopf, expanded=False):
        links, rechts = st.columns([3, 2])
        with rechts:
            _bild_vorschau(db, m.get("bild_pfad"))
            if m.get("bild_pfad"):
                st.caption("✅ Bildrechte bestätigt" if m.get("bild_rechte") else "⚠️ Bildrechte NICHT bestätigt – Bild wird nicht übernommen")
            st.markdown(f"**Kontakt:** {m.get('kontakt_name') or '–'} · {m['kontakt_email']} · {rolle}")
            if m.get("anmerkung"):
                st.markdown(f"**Anmerkung:** {m['anmerkung']}")
            if m.get("link"):
                st.markdown(f"**Link:** {m['link']}")
        with links, st.form(f"meldung_{m['id']}"):
            titel = st.text_input("Titel", m["titel"], max_chars=150)
            kat_index = KATEGORIEN.index(m["kategorie"]) if m["kategorie"] in KATEGORIEN else len(KATEGORIEN) - 1
            kategorie = st.selectbox("Kategorie", KATEGORIEN, index=kat_index)
            c1, c2, c3 = st.columns(3)
            datum = c1.date_input("Datum", date.fromisoformat(m["datum"]))
            datum_bis = c2.date_input("Bis (optional)", date.fromisoformat(m["datum_bis"]) if m.get("datum_bis") else None)
            uhrzeit = c3.time_input("Uhrzeit (optional)", time.fromisoformat(m["uhrzeit"][:5]) if m.get("uhrzeit") else None)
            ort = st.text_input("Ort", m["ort"], max_chars=150)
            adresse = st.text_input("Adresse", m.get("adresse") or "", max_chars=200)
            preis = st.text_input("Preis", m.get("preis") or "", max_chars=80)
            link = st.text_input("Link", m.get("link") or "", max_chars=500)
            beschreibung = st.text_area("Beschreibung (wird auf 300 Zeichen gekürzt)", m["beschreibung"], height=160)
            st.caption(f"Vorschau gekürzt: {_kuerzen(beschreibung)}")
            grund = st.text_input("Ablehngrund (nur intern)", "")
            b1, b2 = st.columns(2)
            freigeben = b1.form_submit_button("✅ Freigeben & veröffentlichen", type="primary", use_container_width=True)
            ablehnen = b2.form_submit_button("❌ Ablehnen", use_container_width=True)

        if freigeben:
            if not titel.strip() or not ort.strip() or len(beschreibung.strip()) < 20:
                st.error("Titel, Ort und eine Beschreibung (mind. 20 Zeichen) sind Pflicht.")
                return
            try:
                event_id = _freigeben(db, m, {
                    "titel": titel.strip(), "kategorie": kategorie, "datum": datum, "datum_bis": datum_bis,
                    "uhrzeit": uhrzeit, "ort": ort.strip(), "adresse": adresse.strip(), "preis": preis.strip(),
                    "link": link.strip(), "beschreibung": beschreibung,
                })
                st.success(f"Freigegeben – Event angelegt ({event_id}).")
                st.rerun()
            except Exception as e:
                logger.error("Freigabe fehlgeschlagen: %s", e)
                st.error(f"Freigabe fehlgeschlagen: {e}")
        if ablehnen:
            try:
                _ablehnen(db, m, grund.strip())
                st.info("Meldung abgelehnt.")
                st.rerun()
            except Exception as e:
                st.error(f"Ablehnen fehlgeschlagen: {e}")


def tab_meldungen(db: Client) -> None:
    st.subheader("📨 Event-Meldungen von der Website")
    try:
        offen = (db.table("event_meldungen").select("*").eq("status", "neu")
                 .order("erstellt_am").limit(100).execute().data or [])
    except Exception as e:
        st.error(f"Meldungen konnten nicht geladen werden ({e}). Wurde database/meldungen_newsletter_2026-11-05.sql ausgeführt?")
        return
    if not offen:
        st.success("Keine offenen Meldungen. 🎉")
    else:
        st.caption(f"{len(offen)} offene Meldung(en) – älteste zuerst.")
        for m in offen:
            _meldung_karte(db, m)

    with st.expander("Zuletzt bearbeitet"):
        erledigt = (db.table("event_meldungen").select("titel, datum, status, bearbeitet_am, ablehngrund, event_id")
                    .neq("status", "neu").order("bearbeitet_am", desc=True).limit(30).execute().data or [])
        if erledigt:
            st.dataframe(erledigt, use_container_width=True, hide_index=True)
        else:
            st.caption("Noch nichts bearbeitet.")


def tab_newsletter(db: Client) -> None:
    st.subheader("✉️ Newsletter-Anmeldungen")
    try:
        anmeldungen = (db.table("newsletter_anmeldungen").select("email, quelle, erstellt_am, bestaetigt_am, abgemeldet_am")
                       .order("erstellt_am", desc=True).limit(5000).execute().data or [])
    except Exception as e:
        st.error(f"Anmeldungen konnten nicht geladen werden ({e}). Wurde database/meldungen_newsletter_2026-11-05.sql ausgeführt?")
        return
    aktiv = [a for a in anmeldungen if not a.get("abgemeldet_am")]
    c1, c2 = st.columns(2)
    c1.metric("Aktive Anmeldungen", len(aktiv))
    c2.metric("Davon bestätigt (Double-Opt-in)", sum(1 for a in aktiv if a.get("bestaetigt_am")))
    st.caption("Double-Opt-in folgt später – bis dahin sind Anmeldungen unbestätigt.")
    if anmeldungen:
        puffer = io.StringIO()
        schreiber = csv.DictWriter(puffer, fieldnames=list(anmeldungen[0].keys()), delimiter=";")
        schreiber.writeheader()
        schreiber.writerows(anmeldungen)
        st.download_button("CSV herunterladen", puffer.getvalue().encode("utf-8-sig"),
                           file_name=f"newsletter_{date.today().isoformat()}.csv", mime="text/csv")
        st.dataframe(anmeldungen[:200], use_container_width=True, hide_index=True)
