"""
auth.py – Login für das Admin-Dashboard über Supabase Auth.

Nur Konten mit der Rolle 'admin' in public.profiles kommen ins Dashboard.
Jede Browser-Sitzung bekommt einen eigenen Supabase-Client (anon-Key + Token
des angemeldeten Admins), damit alle Abfragen unter RLS laufen – der
service_role-Key wird im Dashboard bewusst nicht verwendet.
"""
import logging
import os

import streamlit as st
from supabase import create_client, Client

logger = logging.getLogger(__name__)

SITZUNG_CLIENT = "supabase_client"
SITZUNG_EMAIL = "admin_email"


def _neuer_client() -> Client:
    """Erstellt einen frischen Supabase-Client mit dem anon-Key."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        st.error("SUPABASE_URL / SUPABASE_KEY fehlen in .env")
        st.stop()
    return create_client(url, key)


def _rolle_laden(db: Client, user_id: str) -> str | None:
    """Liest die Rolle des angemeldeten Nutzers aus public.profiles."""
    try:
        antwort = db.table("profiles").select("rolle").eq("id", user_id).maybe_single().execute()
        return antwort.data.get("rolle") if antwort and antwort.data else None
    except Exception as e:
        logger.error("Rolle konnte nicht geladen werden: %s", e)
        return None


def _login_formular() -> None:
    """Zeigt das Login-Formular und meldet bei Erfolg an."""
    _, mitte, _ = st.columns([1, 2, 1])
    with mitte:
        st.title("🎭 DiesDasDüsseldorf – Admin")
        with st.form("login"):
            email = st.text_input("E-Mail", autocomplete="username")
            passwort = st.text_input("Passwort", type="password", autocomplete="current-password")
            abschicken = st.form_submit_button("Anmelden", type="primary", use_container_width=True)

        if not abschicken:
            return
        if not email or not passwort:
            st.error("Bitte E-Mail und Passwort eingeben.")
            return

        db = _neuer_client()
        try:
            antwort = db.auth.sign_in_with_password({"email": email.strip(), "password": passwort})
        except Exception as e:
            logger.warning("Login fehlgeschlagen für %s: %s", email.strip(), e)
            st.error("Anmeldung fehlgeschlagen – E-Mail oder Passwort falsch.")
            return

        if _rolle_laden(db, antwort.user.id) != "admin":
            logger.warning("Login ohne Admin-Rolle abgewiesen: %s", email.strip())
            try:
                db.auth.sign_out()
            except Exception:
                pass
            st.error("Dieses Konto hat keinen Admin-Zugang.")
            return

        logger.info("Admin angemeldet: %s", antwort.user.email)
        st.session_state[SITZUNG_CLIENT] = db
        st.session_state[SITZUNG_EMAIL] = antwort.user.email
        st.rerun()


def admin_client() -> Client:
    """
    Gibt den Supabase-Client des angemeldeten Admins zurück.
    Ist niemand angemeldet, wird das Login angezeigt und die Seite hier beendet.
    """
    db = st.session_state.get(SITZUNG_CLIENT)
    if db is not None:
        return db
    _login_formular()
    st.stop()


def abmelden_button() -> None:
    """Zeigt den angemeldeten Admin und einen Abmelden-Button (für die Sidebar)."""
    st.caption(f"Angemeldet als {st.session_state.get(SITZUNG_EMAIL, '–')}")
    if st.button("Abmelden", use_container_width=True):
        db = st.session_state.pop(SITZUNG_CLIENT, None)
        st.session_state.pop(SITZUNG_EMAIL, None)
        if db is not None:
            try:
                db.auth.sign_out()
            except Exception:
                pass
        st.rerun()
