"""
meldung_mail.py – DiesDasDüsseldorf
Bestätigungsmail an Melder, sobald ihre Meldung als Event veröffentlicht ist (Wunsch des Auftraggebers 24.11.2026):
Dank, Link zum veröffentlichten Event, Hinweis aufs nächste Melden und aufs kostenlose Konto.

Ablauf: Die Freigabe im Dashboard setzt event_meldungen.mail_status = 'offen' und startet
.github/workflows/meldung-mail.yml (dazu stündlich als Sicherheitsnetz). Je Lauf:
  1. Offene Meldungen beanspruchen (meldung_mail_beanspruchen, höchstens JE_LAUF; nur sichtbare, nicht vergangene Events).
  2. Je Meldung eine Mail (Text + HTML) über SMTP; danach meldung_mail_versandt, bei Fehler meldung_mail_freigeben
     (höchstens 3 Versuche, danach 'fehler' – im Dashboard sichtbar).
Ältere Freigaben (vor dem 24.11.2026) haben keinen mail_status und bekommen nichts.

Aufrufe:
    python -m pipeline.meldung_mail senden            # echter Versand, nur mit MELDUNG_MAIL_AKTIV=1
    python -m pipeline.meldung_mail probe             # zählt nur, schreibt nichts
    python -m pipeline.meldung_mail test --an ADRESSE # Beispielmail, schreibt nichts

Umgebung: SUPABASE_URL, SUPABASE_SERVICE_KEY, SMTP_HOST, SMTP_PORT, SMTP_BENUTZER, SMTP_PASSWORT, optional SITE_URL,
MELDUNG_MAIL_AKTIV. Ins Log kommen nur Anzahlen – nie Mailadressen oder Namen.
"""
from __future__ import annotations

import argparse
import html
import logging
import os
import time as uhr
from datetime import date, datetime, time
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from typing import Any, Optional
from urllib.parse import quote

from pipeline.geburtstag_mails import ABSENDER, ANTWORT_AN, SITE_URL, Versender

logger = logging.getLogger(__name__)

JE_LAUF = 50
VERBUCHEN_VERSUCHE = 4
SCHRIFT = "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
WOCHENTAGE = ["Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa.", "So."]
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November",
          "Dezember"]
MELDEN_PFAD = "/event-melden"
KONTO_PFAD = "/konto/anmelden?neu=1"


# ── Bausteine ──────────────────────────────────────────────────────────────────────────────────────

def web_kategorie(k: Optional[str]) -> str:
    """Wie webKategorie in web/lib/admin/seo.ts: die Datenbank sagt „family“, die Website „familie“."""
    w = (k or "sonstiges").strip().lower()
    return "familie" if w == "family" else w


def event_pfad(kategorie: Optional[str], slug: Optional[str], event_id: str) -> str:
    """Wie eventPfadSeo / eventPfad (web/lib): /event/<kategorie>/<slug>, ohne Slug /event/<id>."""
    if slug:
        return f"/event/{quote(web_kategorie(kategorie), safe='')}/{quote(slug, safe='')}"
    return f"/event/{quote(event_id, safe='')}"


def _datum(wert: Any) -> Optional[date]:
    if wert is None or wert == "":
        return None
    if isinstance(wert, date):
        return wert
    return date.fromisoformat(str(wert)[:10])


def _uhrzeit(wert: Any) -> Optional[str]:
    if wert is None or wert == "":
        return None
    if isinstance(wert, time):
        return wert.strftime("%H:%M")
    return str(wert)[:5]


def _tag(d: date, mit_jahr: bool = True) -> str:
    return f"{WOCHENTAGE[d.weekday()]}, {d.day}. {MONATE[d.month - 1]}" + (f" {d.year}" if mit_jahr else "")


def termin_text(datum: Any, datum_bis: Any = None, uhrzeit: Any = None) -> str:
    """„Sa., 5. Dezember 2026, 11:30 Uhr“ oder „Fr., 5. Dezember bis So., 7. Dezember 2026, ab 11:30 Uhr“."""
    von, bis, uhr = _datum(datum), _datum(datum_bis), _uhrzeit(uhrzeit)
    if von is None:
        return ""
    if bis and bis > von:
        text = f"{_tag(von, mit_jahr=von.year != bis.year)} bis {_tag(bis)}"
        return text + (f", ab {uhr} Uhr" if uhr else "")
    return _tag(von) + (f", {uhr} Uhr" if uhr else "")


def anrede(name: Optional[str]) -> str:
    """Name aus der Meldung wie eingegeben (kann auch ein Verein sein, deshalb kein Vorname-Raten)."""
    n = " ".join((name or "").split())[:60].strip()
    return f"Hallo {n}," if n else "Hallo,"


def mail_bauen(an: str, z: dict[str, Any], url: Optional[str] = None) -> EmailMessage:
    """Mail mit Text- und HTML-Teil. z: Zeile aus meldung_mail_beanspruchen (Angaben des veröffentlichten Events);
    url nur für die Testmail (sonst aus Kategorie und Slug)."""
    veranstalter = (z.get("kontakt_rolle") or "veranstalter") != "besucher"
    titel = " ".join(str(z.get("titel") or "").split())
    url = url or SITE_URL + event_pfad(z.get("kategorie"), z.get("slug"), str(z.get("event_id") or ""))
    termin = termin_text(z.get("datum"), z.get("datum_bis"), z.get("uhrzeit"))
    ort = " ".join(str(z.get("ort") or "").split())
    zeile_termin = " · ".join(t for t in (termin, ort) if t)
    melden_url, konto_url = SITE_URL + MELDEN_PFAD, SITE_URL + KONTO_PFAD

    betreff = f"{'Dein Event' if veranstalter else 'Das von dir gemeldete Event'} ist online: {titel}"
    if len(betreff) > 140:
        betreff = betreff[:139].rstrip() + "…"
    einleitung = ("danke, dass du uns dein Event geschickt hast! Wir haben es angeschaut und jetzt veröffentlicht:"
                  if veranstalter else
                  "danke, dass du uns dieses Event geschickt hast! Wir haben es angeschaut und jetzt veröffentlicht:")
    teilen = "Teil den Link gern mit allen, die vorbeikommen sollen."
    naechstes = ("Und wenn dein nächstes Event ansteht: Du kannst es jederzeit hier melden:" if veranstalter else
                 "Und wenn du wieder ein Event entdeckst, das bei uns noch fehlt: Du kannst es jederzeit hier melden:")
    konto = ("Übrigens: Mit einem kostenlosen Konto bei dies.das merkst du dir Events, bekommst Tipps, die zu dir "
             "passen, und hast deine Favoriten auf jedem Gerät dabei:")
    dank = "Danke, dass du dies.das nutzt. So wird der Kalender für Düsseldorf jeden Tag ein bisschen vollständiger."
    grund = "Du bekommst diese Mail einmalig, weil du über „Event melden“ ein Event bei uns eingereicht hast."

    text = (
        f"{anrede(z.get('kontakt_name'))}\n\n"
        f"{einleitung}\n\n"
        f"{titel}\n"
        + (f"{zeile_termin}\n" if zeile_termin else "")
        + f"{url}\n\n"
        f"{teilen} {naechstes} {melden_url}\n\n"
        f"{konto} {konto_url}\n\n"
        f"{dank}\n\n"
        "Viele Grüße\n"
        "dein Team von dies.das\n\n"
        "--\n"
        f"{grund}\n"
        "dies.das.düsseldorf · Rocktician e. K., Erkrather Str. 401, 40231 Düsseldorf\n"
        f"Impressum: {SITE_URL}/impressum · Datenschutz: {SITE_URL}/datenschutz#event-melden\n"
    )

    e = lambda s: html.escape(s, quote=True)  # noqa: E731
    absatz = f'style="margin:0 0 16px;font-family:{SCHRIFT};font-size:16px;line-height:1.5;color:#1B2540;"'
    klein = f'style="margin:0 0 8px;font-family:{SCHRIFT};font-size:13px;line-height:1.5;color:#5A6378;"'
    link = 'style="color:#1B2540;"'
    termin_html = (f'<p style="margin:0 0 16px;font-family:{SCHRIFT};font-size:15px;line-height:1.5;color:#5A6378;">'
                   f'{e(zeile_termin)}</p>') if zeile_termin else ""
    inhalt_html = f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{e(betreff)}</title></head>
<body style="margin:0;padding:0;background:#F6F3EE;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#F6F3EE;"><tr><td align="center" style="padding:24px 12px;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#FFFFFF;border-radius:12px;">
<tr><td style="padding:28px 24px;">
<p {absatz}>{e(anrede(z.get('kontakt_name')))}</p>
<p {absatz}>{e(einleitung)}</p>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#F6F3EE;border-radius:10px;margin:0 0 20px;"><tr><td style="padding:18px 18px 4px;">
<p style="margin:0 0 6px;font-family:{SCHRIFT};font-size:18px;font-weight:700;line-height:1.35;color:#1B2540;">{e(titel)}</p>
{termin_html}
<p style="margin:0 0 14px;"><a href="{e(url)}" style="display:inline-block;background:#1B2540;color:#FFFFFF;font-family:{SCHRIFT};font-size:16px;font-weight:700;text-decoration:none;padding:12px 22px;border-radius:999px;">Zum Event</a></p>
</td></tr></table>
<p {absatz}>{e(teilen)} {e(naechstes)} <a href="{e(melden_url)}" {link}>{e(melden_url.replace('https://', ''))}</a></p>
<p {absatz}>{e(konto)} <a href="{e(konto_url)}" {link}>Kostenloses Konto anlegen</a></p>
<p {absatz}>{e(dank)}</p>
<p {absatz}>Viele Grüße<br>dein Team von dies.das</p>
<p {klein}>{e(grund)}</p>
<p {klein}>dies.das.düsseldorf · Rocktician e. K., Erkrather Str. 401, 40231 Düsseldorf<br>
<a href="{e(SITE_URL)}/impressum" style="color:#5A6378;">Impressum</a> · <a href="{e(SITE_URL)}/datenschutz#event-melden" style="color:#5A6378;">Datenschutz</a></p>
</td></tr></table></td></tr></table>
</body></html>
"""
    m = EmailMessage()
    m["Subject"] = betreff
    m["From"] = ABSENDER
    m["To"] = an
    m["Reply-To"] = ANTWORT_AN
    m["Date"] = formatdate(localtime=False, usegmt=True)
    m["Message-ID"] = make_msgid(domain="diesdas.events")
    m["Auto-Submitted"] = "auto-generated"
    m.set_content(text)
    m.add_alternative(inhalt_html, subtype="html")
    return m


# ── Versand ────────────────────────────────────────────────────────────────────────────────────────

def versenden(db, versender_fabrik, je_lauf: int = JE_LAUF) -> dict[str, int]:
    """Beanspruchte Meldungen anschreiben; bei Fehler freigeben. SMTP nur öffnen, wenn es etwas zu senden gibt.
    Rückgabe: Anzahlen (nie Adressen)."""
    zahlen = {"beansprucht": 0, "gesendet": 0, "fehlgeschlagen": 0, "nicht_verbucht": 0}
    zeilen: list[dict[str, Any]] = db.rpc("meldung_mail_beanspruchen", {"p_anzahl": je_lauf}).execute().data or []
    zahlen["beansprucht"] = len(zeilen)
    if not zeilen:
        return zahlen
    offen = list(zeilen)
    try:
        with versender_fabrik() as v:
            while offen:
                z = offen.pop(0)
                try:
                    v.senden(mail_bauen(str(z["kontakt_email"]), z))
                    zahlen["gesendet"] += 1
                    # Mail ist raus: nur das Verbuchen wiederholen, nie die Mail (Cursor-Prüfung, gering 1)
                    if not _rpc(db, "meldung_mail_versandt", z, versuche=VERBUCHEN_VERSUCHE):
                        # Datenbank nicht erreichbar: keine weiteren Mails in diesem Lauf, die sich ebenfalls nicht
                        # verbuchen ließen (Cursor-Prüfung 24.11.2026). Die übrigen Ansprüche verfallen nach 30 Minuten,
                        # diese eine Mail kann dann höchstens noch einmal rausgehen; der Lauf endet mit Fehler.
                        zahlen["nicht_verbucht"] += 1
                        logger.error(f"Meldungs-Mail: Versand nicht verbuchbar – Lauf abgebrochen, {len(offen)} bleiben offen")
                        break
                except Exception as e:  # noqa: BLE001 – jede Mail einzeln
                    zahlen["fehlgeschlagen"] += 1
                    logger.error(f"Meldungs-Mail: Versand gescheitert ({type(e).__name__})")
                    _rpc(db, "meldung_mail_freigeben", z)
    except Exception as e:  # noqa: BLE001 – Verbindung gescheitert: alle noch offenen freigeben
        logger.error(f"Meldungs-Mail: SMTP nicht erreichbar ({type(e).__name__})")
        zahlen["fehlgeschlagen"] += len(offen)
        for z in offen:
            _rpc(db, "meldung_mail_freigeben", z)
    return zahlen


def _rpc(db, name: str, z: dict, versuche: int = 1, pause: float = 2.0) -> bool:
    for versuch in range(1, versuche + 1):
        try:
            db.rpc(name, {"p_id": z["id"]}).execute()
            return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Meldungs-Mail: {name} gescheitert, Versuch {versuch}/{versuche} ({type(e).__name__})")
            if versuch < versuche:
                uhr.sleep(pause * versuch)
    return False


def _umgebung(name: str) -> str:
    wert = os.getenv(name, "").strip()
    if not wert:
        raise SystemExit(f"Umgebungsvariable {name} fehlt")
    return wert


def _versender() -> Versender:
    return Versender(_umgebung("SMTP_HOST"), int(os.getenv("SMTP_PORT", "587")), _umgebung("SMTP_BENUTZER"),
                     _umgebung("SMTP_PASSWORT"))


BEISPIEL = {
    "kontakt_name": "Alex Beispiel",
    "kontakt_rolle": "veranstalter",
    "titel": "Beispiel: Adventsmarkt im Hinterhof",
    "datum": "2026-12-05",
    "datum_bis": None,
    "uhrzeit": "11:30",
    "ort": "Beispiel-Galerie",
    "kategorie": "community",
    "slug": None,
    "event_id": "",
}


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(description="Bestätigungsmail an Melder nach der Veröffentlichung")
    p.add_argument("aufgabe", choices=["senden", "probe", "test"])
    p.add_argument("--an", help="test: Empfängeradresse der Beispielmail")
    a = p.parse_args(argv)

    if a.aufgabe == "test":
        if not a.an:
            raise SystemExit("test braucht --an ADRESSE")
        # Beispiel ohne echtes Event: der Button führt auf die Übersicht statt auf eine Event-Seite
        m = mail_bauen(a.an, BEISPIEL, url=f"{SITE_URL}/entdecken")
        with _versender() as v:
            v.senden(m)
        logger.info("Meldungs-Mail: Testmail gesendet, nichts in der Datenbank geändert")
        return 0

    from database.client import get_supabase_client  # erst hier: Tests brauchen keine Datenbank

    db = get_supabase_client()
    if a.aufgabe == "probe":
        offen = (db.table("event_meldungen").select("id", count="exact").eq("mail_status", "offen")
                 .limit(1).execute().count) or 0
        logger.info(f"Meldungs-Mail Probelauf: {offen} Meldungen warten auf die Mail, nichts gesendet")
        return 0

    if os.getenv("MELDUNG_MAIL_AKTIV", "") != "1":
        logger.info("Meldungs-Mail: MELDUNG_MAIL_AKTIV ist nicht 1 – kein Versand")
        return 0
    zahlen = versenden(db, _versender)
    logger.info(f"Meldungs-Mail: {zahlen['beansprucht']} beansprucht, {zahlen['gesendet']} gesendet, "
                f"{zahlen['fehlgeschlagen']} fehlgeschlagen, {zahlen['nicht_verbucht']} nicht verbucht")
    return 1 if zahlen["fehlgeschlagen"] or zahlen["nicht_verbucht"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
