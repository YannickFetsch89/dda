"""
geburtstag_mails.py – DiesDasDüsseldorf
Versandjob der Geburtstagsmail (Plan docs/plan-geburtstagsmail-2026-11-20.md, Kontenplan Schritt 9a / 13a).

Ablauf je Lauf (täglich über .github/workflows/geburtstag.yml):
  1. Empfänger des Tages (Europe/Berlin) über geburtstag_empfaenger(tag) – Einwilligung (d), nicht gesperrt,
     Mindestalter bestätigt, Geburtstag heute (29.2. → 28.2.), in diesem Jahr noch keine Mail.
  2. Event-Tipps über die interne Website-Route /api/intern/geburtstag-tipps (G2). Fällt sie aus, geht die Mail
     ohne Tipp-Block raus.
  3. Je Empfänger: beanspruchen (geburtstag_beanspruchen, gegen Doppelversand), Mailadresse aus auth.users,
     Mail bauen (Text + HTML, List-Unsubscribe nach RFC 8058), über SMTP senden. Scheitert der Versand, gibt
     geburtstag_freigeben den alten Stand zurück, der nächste Lauf am selben Tag versucht es erneut.

Aufrufe:
    python -m pipeline.geburtstag_mails senden            # echter Versand, nur mit GEBURTSTAG_AKTIV=1
    python -m pipeline.geburtstag_mails probe             # zählt nur die Empfänger von heute, schreibt nichts
    python -m pipeline.geburtstag_mails test --an ADRESSE [--nutzer ID]   # Beispielmail, schreibt nichts

Umgebung: SUPABASE_URL, SUPABASE_SERVICE_KEY, SMTP_HOST, SMTP_PORT (587 STARTTLS oder 465 TLS), SMTP_BENUTZER,
SMTP_PASSWORT, GEBURTSTAG_TOKEN_SCHLUESSEL, GEBURTSTAG_JOB_SCHLUESSEL, optional SITE_URL, GEBURTSTAG_AKTIV.
Ins Log kommen nur Anzahlen – nie Mailadressen, nie Nutzer-IDs.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import html
import logging
import os
import smtplib
import ssl
from dataclasses import dataclass, field
from datetime import date, datetime
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path
from typing import Any, Callable, Optional
from zoneinfo import ZoneInfo

import httpx

logger = logging.getLogger(__name__)

SITE_URL = os.getenv("SITE_URL", "https://diesdas.events").rstrip("/")
# Absender = das SMTP-Postfach, über das verschickt wird (Mitteilung des Auftraggebers vom 20.11.2026: hallo@).
# Viele Mailserver lehnen einen Absender ab, der nicht zum angemeldeten Postfach passt.
ABSENDER = formataddr(("dies.das.düsseldorf", "hallo@diesdas.events"))
ANTWORT_AN = "hallo@diesdas.events"
BETREFF = "Alles Gute zum Geburtstag!"
VORLAGE = Path(__file__).parent / "vorlagen" / "geburtstag.html"
ZWECK = "geburtstag:"
TIPPS_TIMEOUT = 30.0
BERLIN = ZoneInfo("Europe/Berlin")


# ── Token (G4) ─────────────────────────────────────────────────────────────────────────────────────

def abmelde_token(nutzer_id: str, schluessel: str) -> str:
    """"<id>.<HMAC-SHA256(schluessel, "geburtstag:" + id), base64url ohne =>" – gleich wie web/lib/konto/geburtstag.ts."""
    mac = hmac.new(schluessel.encode("utf-8"), (ZWECK + nutzer_id).encode("utf-8"), hashlib.sha256).digest()
    return f"{nutzer_id}.{base64.urlsafe_b64encode(mac).decode('ascii').rstrip('=')}"


def abmelde_urls(token: str) -> tuple[str, str]:
    """(Seite mit Button, One-Click-Adresse für List-Unsubscribe)."""
    return f"{SITE_URL}/konto/geburtstag-abmelden#t={token}", f"{SITE_URL}/api/konto/geburtstag-abmelden/{token}"


# ── Mail bauen ─────────────────────────────────────────────────────────────────────────────────────

def _tipp_zeile(t: dict) -> tuple[str, str]:
    """Eine Tipp-Zeile als (HTML, Text). Uhrzeit HH:MM → „20:00 Uhr · Ort“, ohne Uhrzeit nur der Ort."""
    titel = str(t.get("titel") or "").strip()
    ort = str(t.get("ort") or "").strip()
    uhrzeit = t.get("uhrzeit")
    meta = " · ".join(x for x in [f"{uhrzeit} Uhr" if uhrzeit else "", ort] if x)
    pfad = str(t.get("pfad") or "/")
    url = SITE_URL + (pfad if pfad.startswith("/") else "/" + pfad)
    zeile_html = (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 8px;">'
        '<tr><td class="tipp" style="background:#F7F8FA;border:1px solid #E2E8F0;border-radius:8px;padding:12px 14px;'
        "font-family:-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;\">"
        f'<div class="tipp-titel" style="font-size:16px;font-weight:700;line-height:1.35;"><a href="{html.escape(url, quote=True)}" '
        f'style="color:#1B2540;text-decoration:none;">{html.escape(titel)}</a></div>'
        + (f'<div class="leise" style="font-size:14px;line-height:1.5;color:#718096;">{html.escape(meta)}</div>' if meta else "")
        + "</td></tr></table>"
    )
    zeile_text = f"- {titel}" + (f" ({meta})" if meta else "") + f"\n  {url}"
    return zeile_html, zeile_text


def mail_bauen(an: str, tipps: list[dict], token: str, vorlage: Optional[str] = None) -> EmailMessage:
    """Mail mit Text- und HTML-Teil (G9), Abmeldelink und List-Unsubscribe-Kopfzeilen (G4)."""
    seite, one_click = abmelde_urls(token)
    tipps = [t for t in tipps if isinstance(t, dict) and t.get("titel")][:3]
    zeilen = [_tipp_zeile(t) for t in tipps]

    if zeilen:
        block_html = (
            '<p class="titel" style="margin:8px 0 12px;font-family:-apple-system, \'Segoe UI\', Roboto, Helvetica, Arial, '
            'sans-serif;font-size:16px;font-weight:700;line-height:1.4;color:#1B2540;">Falls du heute noch etwas vorhast:</p>'
            + "".join(h for h, _ in zeilen)
            + '<div style="height:12px;line-height:12px;">&nbsp;</div>'
        )
        block_text = "Falls du heute noch etwas vorhast:\n\n" + "\n\n".join(t for _, t in zeilen) + "\n\n"
    else:
        block_html, block_text = "", ""

    roh = vorlage if vorlage is not None else VORLAGE.read_text(encoding="utf-8")
    inhalt_html = roh.replace("{{TIPPS}}", block_html).replace("{{ABMELDEN_URL}}", html.escape(seite, quote=True))
    inhalt_text = (
        "Alles Gute zum Geburtstag!\n\n"
        "Hallo!\n\n"
        "Heute ist dein Tag, und wir gratulieren dir herzlich. Wir wünschen dir ein schönes neues Lebensjahr, "
        "mit vielen guten Abenden in Düsseldorf.\n\n"
        f"{block_text}"
        f"Alles für heute: {SITE_URL}/heute\n\n"
        "Feier schön!\nDein Team von dies.das.düsseldorf\n\n"
        "--\n"
        "Du bekommst diese Mail, weil du in deinem Konto der Geburtstagsmail zugestimmt hast.\n"
        f"Keine Geburtstagsmails mehr: {seite}\n"
        f"Einstellungen im Konto: {SITE_URL}/konto/datenschutz\n\n"
        "dies.das.düsseldorf · Rocktician e. K., Erkrather Str. 401, 40231 Düsseldorf\n"
        f"Impressum: {SITE_URL}/impressum · Datenschutz: {SITE_URL}/datenschutz\n"
    )

    m = EmailMessage()
    m["Subject"] = BETREFF
    m["From"] = ABSENDER
    m["To"] = an
    m["Reply-To"] = ANTWORT_AN
    m["Date"] = formatdate(localtime=False, usegmt=True)
    m["Message-ID"] = make_msgid(domain="diesdas.events")
    m["List-Unsubscribe"] = f"<{one_click}>"
    m["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    m["Auto-Submitted"] = "auto-generated"
    m.set_content(inhalt_text)
    m.add_alternative(inhalt_html, subtype="html")
    return m


# ── Tipps über die Website (G2) ────────────────────────────────────────────────────────────────────

@dataclass
class TippAntwort:
    datum: Optional[str] = None
    allgemein: list[dict] = field(default_factory=list)
    tipps: dict[str, list[dict]] = field(default_factory=dict)


def tipps_holen(nutzer: list[str], schluessel: Optional[str], post: Optional[Callable] = None) -> Optional[TippAntwort]:
    """POST /api/intern/geburtstag-tipps. Jeder Fehler → None (die Mail geht dann ohne Tipp-Block raus)."""
    if not schluessel:
        logger.warning("Geburtstagsmail: GEBURTSTAG_JOB_SCHLUESSEL fehlt – Mails ohne Tipps")
        return None
    post = post or httpx.post
    try:
        r = post(f"{SITE_URL}/api/intern/geburtstag-tipps", json={"nutzer": nutzer[:200]},
                 headers={"x-geburtstag-schluessel": schluessel}, timeout=TIPPS_TIMEOUT)
        if r.status_code != 200:
            logger.warning(f"Geburtstagsmail: Tipps-Route antwortet {r.status_code} – Mails ohne Tipps")
            return None
        d = r.json()
    except Exception as e:  # Netz, Zeitüberschreitung, kein JSON
        logger.warning(f"Geburtstagsmail: Tipps nicht abrufbar ({type(e).__name__}) – Mails ohne Tipps")
        return None
    if not isinstance(d, dict):
        return None
    tipps = d.get("tipps") if isinstance(d.get("tipps"), dict) else {}
    allgemein = d.get("allgemein") if isinstance(d.get("allgemein"), list) else []
    return TippAntwort(datum=d.get("datum"), allgemein=allgemein, tipps=tipps)


# ── Versand ────────────────────────────────────────────────────────────────────────────────────────

class Versender:
    """SMTP-Verbindung für einen Lauf (Port 465 TLS, sonst STARTTLS)."""

    def __init__(self, host: str, port: int, benutzer: str, passwort: str):
        self.host, self.port, self.benutzer, self.passwort = host, port, benutzer, passwort
        self.smtp: Optional[smtplib.SMTP] = None

    def __enter__(self) -> "Versender":
        kontext = ssl.create_default_context()
        if self.port == 465:
            self.smtp = smtplib.SMTP_SSL(self.host, self.port, context=kontext, timeout=30)
        else:
            self.smtp = smtplib.SMTP(self.host, self.port, timeout=30)
            self.smtp.starttls(context=kontext)
        self.smtp.login(self.benutzer, self.passwort)
        return self

    def senden(self, m: EmailMessage) -> None:
        assert self.smtp is not None
        self.smtp.send_message(m)

    def __exit__(self, *_: Any) -> None:
        if self.smtp is not None:
            try:
                self.smtp.quit()
            except Exception:
                pass


def heute_berlin(jetzt: Optional[datetime] = None) -> date:
    return (jetzt or datetime.now(BERLIN)).astimezone(BERLIN).date()


def _mailadresse(db, nutzer_id: str) -> Optional[str]:
    """Bestätigte Mailadresse aus auth.users oder None."""
    try:
        antwort = db.auth.admin.get_user_by_id(nutzer_id)
        user = getattr(antwort, "user", None)
    except Exception:
        return None
    if not user or not getattr(user, "email", None) or not getattr(user, "email_confirmed_at", None):
        return None
    return str(user.email)


def empfaenger_ids(daten: Any) -> list[str]:
    """Antwort von geburtstag_empfaenger (SETOF uuid): Liste von Strings oder von {"geburtstag_empfaenger": id}."""
    ids: list[str] = []
    for x in daten or []:
        wert = x.get("geburtstag_empfaenger") if isinstance(x, dict) else x
        if isinstance(wert, str) and len(wert) == 36:
            ids.append(wert)
    return ids


def _eins(daten: Any) -> dict:
    """Erste Zeile einer RPC-Antwort (Liste oder Objekt)."""
    if isinstance(daten, list):
        return daten[0] if daten and isinstance(daten[0], dict) else {}
    return daten if isinstance(daten, dict) else {}


def versenden(db, tag: date, versender, tipps_quelle: Callable[[list[str]], Optional[TippAntwort]],
              token_schluessel: str) -> dict[str, int]:
    """
    Ein Lauf für den Tag `tag`. db: Supabase-Client (Dienst), versender: Objekt mit senden(EmailMessage).
    Gibt Zahlen zurück (gefunden, gesendet, uebersprungen, fehlgeschlagen) – ohne Adressen oder IDs.
    """
    ids = empfaenger_ids(db.rpc("geburtstag_empfaenger", {"tag": tag.isoformat()}).execute().data)
    zahlen = {"gefunden": len(ids), "gesendet": 0, "uebersprungen": 0, "fehlgeschlagen": 0}
    if not ids:
        return zahlen

    antwort = tipps_quelle(ids)
    # Tipps nur, wenn die Route denselben Tag meint (Zeitzone, Lauf über Mitternacht)
    if antwort is not None and antwort.datum != tag.isoformat():
        logger.warning("Geburtstagsmail: Tipps für einen anderen Tag – Mails ohne Tipps")
        antwort = None

    for nutzer_id in ids:
        beansprucht = _eins(db.rpc("geburtstag_beanspruchen", {"nutzer": nutzer_id, "tag": tag.isoformat()}).execute().data)
        if not beansprucht.get("beansprucht"):
            zahlen["uebersprungen"] += 1  # schon gesendet (paralleler Lauf) oder inzwischen abgemeldet
            continue
        vorher = beansprucht.get("vorher")
        adresse = _mailadresse(db, nutzer_id)
        try:
            if not adresse:
                raise ValueError("keine bestätigte Mailadresse")
            tipps = antwort.tipps.get(nutzer_id, []) if antwort else []
            versender.senden(mail_bauen(adresse, tipps, abmelde_token(nutzer_id, token_schluessel)))
            zahlen["gesendet"] += 1
        except Exception as e:
            zahlen["fehlgeschlagen"] += 1
            logger.warning(f"Geburtstagsmail: Versand gescheitert ({type(e).__name__}) – wird freigegeben")
            try:
                db.rpc("geburtstag_freigeben", {"nutzer": nutzer_id, "tag": tag.isoformat(), "vorher": vorher}).execute()
            except Exception as e2:
                logger.error(f"Geburtstagsmail: Freigeben gescheitert ({type(e2).__name__})")
    return zahlen


# ── Einstieg ───────────────────────────────────────────────────────────────────────────────────────

def _umgebung(name: str) -> str:
    wert = os.getenv(name, "").strip()
    if not wert:
        raise SystemExit(f"Umgebungsvariable {name} fehlt")
    return wert


def _versender() -> Versender:
    return Versender(_umgebung("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587")), _umgebung("SMTP_BENUTZER"),
                     _umgebung("SMTP_PASSWORT"))


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="Geburtstagsmail (Versand, Probelauf, Testmail)")
    p.add_argument("aufgabe", choices=["senden", "probe", "test"])
    p.add_argument("--an", help="test: Empfängeradresse der Beispielmail")
    p.add_argument("--nutzer", help="test: Tipps und Abmelde-Token für diese Nutzer-ID (sonst allgemeine Tipps)")
    a = p.parse_args(argv)

    from database.client import get_supabase_client  # erst hier: Tests brauchen keine Datenbank

    tag = heute_berlin()
    db = get_supabase_client()
    job_schluessel = os.getenv("GEBURTSTAG_JOB_SCHLUESSEL")

    if a.aufgabe == "probe":
        ids = empfaenger_ids(db.rpc("geburtstag_empfaenger", {"tag": tag.isoformat()}).execute().data)
        logger.info(f"Geburtstagsmail Probelauf {tag.isoformat()}: {len(ids)} Empfänger, nichts gesendet")
        return 0

    token_schluessel = _umgebung("GEBURTSTAG_TOKEN_SCHLUESSEL")

    if a.aufgabe == "test":
        if not a.an:
            raise SystemExit("test braucht --an ADRESSE")
        antwort = tipps_holen([a.nutzer] if a.nutzer else [], job_schluessel)
        tipps = (antwort.tipps.get(a.nutzer, []) if a.nutzer else antwort.allgemein) if antwort else []
        # Ohne --nutzer ein Token, das zu keinem Konto passt (der Link zeigt dann „ungültig“)
        token = abmelde_token(a.nutzer or "00000000-0000-4000-8000-000000000000", token_schluessel)
        with _versender() as v:
            v.senden(mail_bauen(a.an, tipps, token))
        logger.info(f"Geburtstagsmail Testmail gesendet ({len(tipps)} Tipps), nichts in der Datenbank geändert")
        return 0

    if os.getenv("GEBURTSTAG_AKTIV", "") != "1":
        logger.info("Geburtstagsmail: GEBURTSTAG_AKTIV ist nicht 1 – kein Versand")
        return 0
    with _versender() as v:
        zahlen = versenden(db, tag, v, lambda ids: tipps_holen(ids, job_schluessel), token_schluessel)
    logger.info(f"Geburtstagsmail {tag.isoformat()}: {zahlen['gefunden']} gefunden, {zahlen['gesendet']} gesendet, "
                f"{zahlen['uebersprungen']} übersprungen, {zahlen['fehlgeschlagen']} fehlgeschlagen")
    return 1 if zahlen["fehlgeschlagen"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
