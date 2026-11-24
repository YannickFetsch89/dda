"""
newsletter_bestaetigung.py – DiesDasDüsseldorf
Bestätigungsmail (Double-Opt-in) für Newsletter-Anmeldungen (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.9,
Stufe 4; Entscheidung E9: die Website legt die Anmeldung an, dieser Job schickt die Mail).

Ablauf je Lauf (alle 15 Minuten über .github/workflows/newsletter.yml, Versand nur mit NEWSLETTER_AKTIV=1):
  1. Offene Anmeldungen beanspruchen (newsletter_bestaetigung_beanspruchen, höchstens JE_LAUF, gegen Doppelversand;
     ein Anspruch ohne Zustellung, älter als 30 Minuten, wird wieder aufgenommen). Nach dem Versand
     newsletter_bestaetigung_versandt (Zustellung, zählt für die Höchstzahl von 3 Mails).
  2. Je Anmeldung: Mail mit Bestätigungslink und Link „Anmeldung verwerfen“ (Text + HTML, List-Unsubscribe nach
     RFC 8058) über SMTP. Scheitert der Versand, gibt newsletter_bestaetigung_freigeben die Anmeldung wieder frei.
  3. Unbestätigte Anmeldungen 30 Tage nach der Bestätigungsmail löschen (newsletter_aufraeumen).

Tokens: "<id>.<HMAC-SHA256(NEWSLETTER_TOKEN_SCHLUESSEL, zweck + id), base64url ohne =>" mit den Zwecken
„newsletter-bestaetigen:“ und „newsletter-abmelden:“ – gleich wie web/lib/newsletter.ts.

Aufrufe:
    python -m pipeline.newsletter_bestaetigung senden          # echter Versand, nur mit NEWSLETTER_AKTIV=1
    python -m pipeline.newsletter_bestaetigung probe           # zählt nur, schreibt nichts
    python -m pipeline.newsletter_bestaetigung test --an ADRESSE   # Beispielmail mit ungültigen Links, schreibt nichts

Umgebung: SUPABASE_URL, SUPABASE_SERVICE_KEY, SMTP_HOST, SMTP_PORT, SMTP_BENUTZER, SMTP_PASSWORT,
NEWSLETTER_TOKEN_SCHLUESSEL, optional SITE_URL, NEWSLETTER_AKTIV. Ins Log kommen nur Anzahlen – nie Mailadressen.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import html
import logging
import os
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import Any, Optional

from pipeline.geburtstag_mails import ABSENDER, ANTWORT_AN, SITE_URL, Versender

logger = logging.getLogger(__name__)

BETREFF = "Bitte bestätige deine Newsletter-Anmeldung"
ZWECK_BESTAETIGEN = "newsletter-bestaetigen:"
ZWECK_ABMELDEN = "newsletter-abmelden:"
JE_LAUF = 50
SCHRIFT = "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def token(anmeldung_id: str, zweck: str, schluessel: str) -> str:
    mac = hmac.new(schluessel.encode("utf-8"), (zweck + anmeldung_id).encode("utf-8"), hashlib.sha256).digest()
    return f"{anmeldung_id}.{base64.urlsafe_b64encode(mac).decode('ascii').rstrip('=')}"


def links(anmeldung_id: str, schluessel: str) -> dict[str, str]:
    """Bestätigen- und Abmelde-Seite (Token im Fragment, geht erst beim Klick an den Server) und One-Click-Adresse."""
    b = token(anmeldung_id, ZWECK_BESTAETIGEN, schluessel)
    a = token(anmeldung_id, ZWECK_ABMELDEN, schluessel)
    return {
        "bestaetigen": f"{SITE_URL}/newsletter/bestaetigen#t={b}",
        "abmelden": f"{SITE_URL}/newsletter/abmelden#t={a}",
        "one_click": f"{SITE_URL}/api/newsletter/abmelden/{a}",
    }


def mail_bauen(an: str, l: dict[str, str]) -> EmailMessage:
    """Bestätigungsmail mit Text- und HTML-Teil; kein Werbeinhalt (nur die Bitte um Bestätigung)."""
    text = (
        "Bitte bestätige deine Anmeldung\n\n"
        "Hallo,\n\n"
        "jemand – hoffentlich du – hat diese Adresse für den Newsletter von dies.das.düsseldorf angemeldet. "
        "Erst wenn du die Anmeldung bestätigst, bekommst du den Newsletter.\n\n"
        f"Anmeldung bestätigen: {l['bestaetigen']}\n\n"
        "Warst du das nicht? Dann ignoriere diese Mail einfach – ohne Bestätigung löschen wir die Adresse nach "
        f"30 Tagen. Sofort löschen: {l['abmelden']}\n\n"
        "Dein Team von dies.das.düsseldorf\n\n"
        "--\n"
        "dies.das.düsseldorf · Rocktician e. K., Erkrather Str. 401, 40231 Düsseldorf\n"
        f"Impressum: {SITE_URL}/impressum · Datenschutz: {SITE_URL}/datenschutz#newsletter\n"
    )
    e = lambda s: html.escape(s, quote=True)  # noqa: E731
    absatz = f'style="margin:0 0 16px;font-family:{SCHRIFT};font-size:16px;line-height:1.5;color:#1B2540;"'
    klein = f'style="margin:0 0 8px;font-family:{SCHRIFT};font-size:13px;line-height:1.5;color:#5A6378;"'
    inhalt_html = f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{e(BETREFF)}</title></head>
<body style="margin:0;padding:0;background:#F6F3EE;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#F6F3EE;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#FFFFFF;border-radius:12px;">
<tr><td style="padding:28px 24px;">
<p style="margin:0 0 20px;font-family:{SCHRIFT};font-size:20px;font-weight:700;color:#1B2540;">Bitte bestätige deine Anmeldung</p>
<p {absatz}>Hallo,</p>
<p {absatz}>jemand – hoffentlich du – hat diese Adresse für den Newsletter von dies.das.düsseldorf angemeldet. Erst wenn du die Anmeldung bestätigst, bekommst du den Newsletter.</p>
<p style="margin:24px 0;"><a href="{e(l['bestaetigen'])}" style="display:inline-block;background:#1B2540;color:#FFFFFF;font-family:{SCHRIFT};font-size:16px;font-weight:700;text-decoration:none;padding:12px 22px;border-radius:999px;">Anmeldung bestätigen</a></p>
<p {absatz}>Warst du das nicht? Dann ignoriere diese Mail einfach – ohne Bestätigung löschen wir die Adresse nach 30 Tagen. <a href="{e(l['abmelden'])}" style="color:#1B2540;">Sofort löschen</a></p>
<p {absatz}>Dein Team von dies.das.düsseldorf</p>
<p {klein}>dies.das.düsseldorf · Rocktician e. K., Erkrather Str. 401, 40231 Düsseldorf<br>
<a href="{e(SITE_URL)}/impressum" style="color:#5A6378;">Impressum</a> · <a href="{e(SITE_URL)}/datenschutz#newsletter" style="color:#5A6378;">Datenschutz</a></p>
</td></tr></table></td></tr></table>
</body></html>
"""
    m = EmailMessage()
    m["Subject"] = BETREFF
    m["From"] = ABSENDER
    m["To"] = an
    m["Reply-To"] = ANTWORT_AN
    m["Date"] = formatdate(localtime=False, usegmt=True)
    m["Message-ID"] = make_msgid(domain="diesdas.events")
    m["List-Unsubscribe"] = f"<{l['one_click']}>"
    m["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    m["Auto-Submitted"] = "auto-generated"
    m.set_content(text)
    m.add_alternative(inhalt_html, subtype="html")
    return m


def versenden(db, versender_fabrik, schluessel: str, je_lauf: int = JE_LAUF) -> dict[str, int]:
    """
    Beanspruchte Anmeldungen anschreiben; bei Fehler wieder freigeben. Die SMTP-Verbindung (versender_fabrik() →
    Kontextmanager) wird nur geöffnet, wenn es etwas zu senden gibt – der Job läuft alle 15 Minuten.
    Rückgabe: Anzahlen (nie Adressen).
    """
    zahlen = {"beansprucht": 0, "gesendet": 0, "fehlgeschlagen": 0}
    zeilen: list[dict[str, Any]] = db.rpc("newsletter_bestaetigung_beanspruchen", {"p_anzahl": je_lauf}).execute().data or []
    zahlen["beansprucht"] = len(zeilen)
    if not zeilen:
        return zahlen
    offen = list(zeilen)
    try:
        with versender_fabrik() as v:
            while offen:
                z = offen.pop(0)
                try:
                    v.senden(mail_bauen(z["email"], links(str(z["id"]), schluessel)))
                    zahlen["gesendet"] += 1
                    _versandt(db, z)
                except Exception as e:  # noqa: BLE001 – jede Mail einzeln
                    zahlen["fehlgeschlagen"] += 1
                    logger.error(f"Newsletter-Bestätigung: Versand gescheitert ({type(e).__name__})")
                    _freigeben(db, z)
    except Exception as e:  # noqa: BLE001 – Verbindung gescheitert: alle noch offenen freigeben
        logger.error(f"Newsletter-Bestätigung: SMTP nicht erreichbar ({type(e).__name__})")
        zahlen["fehlgeschlagen"] += len(offen)
        for z in offen:
            _freigeben(db, z)
    return zahlen


def _versandt(db, z: dict) -> None:
    """Zustellung merken (zählt für die Höchstzahl; ohne diesen Eintrag nähme ein späterer Lauf die Zeile nach 30 Minuten
    wieder auf – lieber eine Mail zu viel als keine)."""
    try:
        db.rpc("newsletter_bestaetigung_versandt", {"p_id": z["id"]}).execute()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Newsletter-Bestätigung: Zustellung nicht gespeichert ({type(e).__name__})")


def _freigeben(db, z: dict) -> None:
    try:
        db.rpc("newsletter_bestaetigung_freigeben", {"p_id": z["id"]}).execute()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Newsletter-Bestätigung: Freigeben gescheitert ({type(e).__name__})")


from pipeline.schluessel import LEERRAUM  # noqa: E402 – gemeinsame Regel (Website, deploy.yml)


def token_schluessel(roh: Optional[str]) -> tuple[str, int]:
    """
    Schlüssel wie auf der Website: deploy.yml schreibt NEWSLETTER_TOKEN_SCHLUESSEL ohne JEDEN Leerraum
    (tr -d ' \r\n\t', Reparatur vom 23.11.2026). Hier vorher nur strip() → steckte ein Zeilenumbruch mitten im
    Secret, rechneten Job und Website mit verschiedenen Schlüsseln und jeder Bestätigungslink war ungültig
    (Livetest 24.11.2026). Rückgabe: Schlüssel und Zahl der entfernten Zeichen IM Wert (fürs Log, ohne den Wert).
    """
    wert = roh or ""
    innen = sum(1 for z in wert.strip() if z in LEERRAUM)
    return "".join(z for z in wert if z not in LEERRAUM), innen


def _schluessel() -> str:
    schluessel, innen = token_schluessel(os.getenv("NEWSLETTER_TOKEN_SCHLUESSEL"))
    if not schluessel:
        raise SystemExit("Umgebungsvariable NEWSLETTER_TOKEN_SCHLUESSEL fehlt")
    if innen:
        logger.warning(f"Newsletter-Bestätigung: {innen} Leerzeichen/Zeilenumbrüche mitten im Schlüssel entfernt "
                       "(wie die Website) – Secret bei Gelegenheit ohne Umbruch neu speichern")
    logger.info(f"Newsletter-Bestätigung: Schlüssel mit {len(schluessel)} Zeichen")
    return schluessel


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
    p = argparse.ArgumentParser(description="Newsletter-Bestätigungsmail (Double-Opt-in)")
    p.add_argument("aufgabe", choices=["senden", "probe", "test"])
    p.add_argument("--an", help="test: Empfängeradresse der Beispielmail")
    a = p.parse_args(argv)

    if a.aufgabe == "test":
        if not a.an:
            raise SystemExit("test braucht --an ADRESSE")
        # Links mit einer ID, die es nicht gibt (die Seiten zeigen dann „ungültig oder abgelaufen“)
        l = links("00000000-0000-4000-8000-000000000000", _schluessel())
        with _versender() as v:
            v.senden(mail_bauen(a.an, l))
        logger.info("Newsletter-Bestätigung: Testmail gesendet, nichts in der Datenbank geändert")
        return 0

    from database.client import get_supabase_client  # erst hier: Tests brauchen keine Datenbank

    db = get_supabase_client()
    if a.aufgabe == "probe":
        offen = (db.table("newsletter_anmeldungen").select("id", count="exact")
                 .is_("bestaetigt_am", "null").is_("bestaetigung_zugestellt_am", "null").lt("mails_gesendet", 3)
                 .limit(1).execute().count) or 0
        _schluessel()  # nur fürs Log: Länge und ob etwas entfernt werden musste
        logger.info(f"Newsletter-Bestätigung Probelauf: {offen} Anmeldungen warten auf die Mail, nichts gesendet")
        return 0

    if os.getenv("NEWSLETTER_AKTIV", "") != "1":
        logger.info("Newsletter-Bestätigung: NEWSLETTER_AKTIV ist nicht 1 – kein Versand")
        return 0
    schluessel = _schluessel()
    zahlen = versenden(db, _versender, schluessel)
    geloescht = db.rpc("newsletter_aufraeumen", {}).execute().data or 0
    logger.info(f"Newsletter-Bestätigung: {zahlen['beansprucht']} beansprucht, {zahlen['gesendet']} gesendet, "
                f"{zahlen['fehlgeschlagen']} fehlgeschlagen, {geloescht} unbestätigte nach 30 Tagen gelöscht")
    return 1 if zahlen["fehlgeschlagen"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
