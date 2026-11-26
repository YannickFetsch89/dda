"""
restaurant_bilder_auswahl.py – DiesDasDüsseldorf
Lokale Auswahlseite für die Restaurant-Bilder (Wunsch des Auftraggebers, 26.11.2026): Je Betrieb alle Kandidaten
aus restaurant_bilder.py zum Anklicken, dazu „heutiges Bild behalten“. Der Button „Speichern und hochladen“ setzt
die gewählten Bilder sofort in der Datenbank – die Website zeigt sie nach spätestens etwa 10 Minuten (Cache).

Was beim Speichern passiert (wie admin_ort_bild_setzen im Admin, Stufe 3b):
- Google-Foto: extras.google_foto = {name, breite, hoehe, autor, autor_url}, bild_url leer, Nachweis = Autor.
- Website-Bild: bild_url = Bildadresse der Website (die Website holt es über den eigenen Bild-Proxy /ort-foto/…,
  der Browser spricht nie mit der fremden Seite), Nachweis = Domain, extras.bild_link = Website.
  Zusätzlich wird das Bild als WebP unter web/public/ort-bilder/restaurants/<slug>.webp abgelegt und in
  data/restaurant_bilder/umstellen.json vermerkt. Nach dem nächsten Deploy stellt
  `--nach-deploy` diese Orte auf die eigene Datei um (unabhängig von der fremden Website).
- Immer: extras.foto_manuell = heute (schützt vor Skript-Läufen), foto_version + 1, bild_fokus aus der KI (oben/unten).
- Jede Änderung mit Vorher/Nachher in data/restaurant_bilder/protokoll.jsonl (Rückweg: --zurueck <slug>).

Läuft nur lokal (127.0.0.1), schreibt mit dem Service-Schlüssel aus web/.env.local.

Nutzung (im Repo-Stamm, Python aus DD/.venv):
  python -m scraper.orte.restaurant_bilder_auswahl                 → http://127.0.0.1:3650
  python -m scraper.orte.restaurant_bilder_auswahl --nach-deploy   → Website-Bilder auf eigene Dateien umstellen
  python -m scraper.orte.restaurant_bilder_auswahl --zurueck <slug>
"""
from __future__ import annotations

import argparse
import html
import json
import logging
import os
import sys
import time
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from dotenv import load_dotenv

load_dotenv(Path("web/.env.local"))
load_dotenv()

from scraper.orte.ortsbilder import abrufen, umwandeln  # noqa: E402
from scraper.orte.restaurant_bilder import ERGEBNIS, VORSCHAU, auswaehlen  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

ORDNER = Path("data/restaurant_bilder")
AUSWAHL = ORDNER / "auswahl.json"
UMSTELLEN = ORDNER / "umstellen.json"
PROTOKOLL = ORDNER / "protokoll.jsonl"
ZIEL = Path("web/public/ort-bilder/restaurants")
WEB_PFAD = "/ort-bilder/restaurants"
PORT = 3650
TROCKEN = False   # --trocken: nichts schreiben, nur protokollieren, was gesetzt würde
QUELLE_TEXT = {"website": "Website", "google_inhaber": "Google · Inhaber", "google_nutzer": "Google · Gast"}


def db():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def json_lesen(pfad: Path, standard):
    return json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else standard


def json_schreiben(pfad: Path, daten) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pfad.with_suffix(".tmp")
    tmp.write_text(json.dumps(daten, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(pfad)


def protokollieren(eintrag: dict) -> None:
    with PROTOKOLL.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"zeit": datetime.now().isoformat(timespec="seconds"), **eintrag}, ensure_ascii=False) + "\n")


# ── Schreiben in die Datenbank ────────────────────────────────────────────────

def ort_lesen(client, ort_id: str) -> dict:
    zeilen = client.table("orte").select("id, slug, name, bild_url, bild_attribution, extras").eq("id", ort_id).execute().data
    if not zeilen:
        raise RuntimeError("Ort nicht gefunden")
    return zeilen[0]


def neue_extras(ort: dict, fokus: str | None) -> dict:
    extras = dict(ort.get("extras") or {})
    extras.pop("bild_fokus", None)
    extras["foto_manuell"] = date.today().isoformat()
    extras["foto_version"] = int(extras.get("foto_version") or 0) + 1
    if fokus in ("oben", "unten"):
        extras["bild_fokus"] = fokus
    return extras


def bild_setzen(client, ort_id: str, k: dict) -> dict:
    """Setzt einen Kandidaten als Bild des Ortes. Gibt {ok, hinweis} zurück."""
    ort = ort_lesen(client, ort_id)
    vorher = {"bild_url": ort.get("bild_url"), "bild_attribution": ort.get("bild_attribution"),
              "google_foto": (ort.get("extras") or {}).get("google_foto"), "bild_link": (ort.get("extras") or {}).get("bild_link"),
              "bild_fokus": (ort.get("extras") or {}).get("bild_fokus"), "foto_manuell": (ort.get("extras") or {}).get("foto_manuell")}
    extras = neue_extras(ort, (k.get("ki") or {}).get("fokus"))
    hinweis = ""
    if k["quelle"] == "website":
        url = k["url"]
        if not url.startswith(("https://", "http://")):
            raise RuntimeError("ungültige Bildadresse")
        extras.pop("google_foto", None)
        seite = k.get("seite") or ""
        if seite.startswith("https://"):
            extras["bild_link"] = seite
        else:
            extras.pop("bild_link", None)
        aenderung = {"bild_url": url, "bild_attribution": (k.get("nachweis") or "")[:200] or None, "extras": extras}
        # Eigene Kopie für den nächsten Deploy (danach --nach-deploy)
        daten = abrufen(url)
        if daten and TROCKEN:
            hinweis = "Datei ladbar (Trockenlauf, nicht abgelegt)"
        elif daten:
            umwandeln(daten, ZIEL / f"{ort['slug']}.webp")
            liste = json_lesen(UMSTELLEN, {})
            liste[ort_id] = {"slug": ort["slug"], "pfad": f"{WEB_PFAD}/{ort['slug']}.webp", "quelle_url": url}
            json_schreiben(UMSTELLEN, liste)
            hinweis = "eigene Datei abgelegt (nach dem nächsten Deploy umstellen)"
        else:
            hinweis = "eigene Datei nicht ladbar – bleibt über den Bild-Proxy"
    else:
        name = k.get("google_foto") or ""
        if not name.startswith("places/"):
            raise RuntimeError("ungültiger Google-Fotoname")
        extras.pop("bild_link", None)
        extras["google_foto"] = {"name": name, "breite": k.get("breite"), "hoehe": k.get("hoehe"),
                                 "autor": k.get("autor"), "autor_url": k.get("autor_url") if (k.get("autor_url") or "").startswith("https://") else None}
        aenderung = {"bild_url": None, "bild_attribution": (k.get("autor") or "")[:200] or None, "extras": extras}
        # Eine ältere eigene Kopie darf nach dem Deploy nicht wieder umstellen
        liste = json_lesen(UMSTELLEN, {})
        if not TROCKEN and liste.pop(ort_id, None):
            json_schreiben(UMSTELLEN, liste)
    if TROCKEN:
        logger.info("TROCKEN %s: %s", ort["slug"], json.dumps({kk: v for kk, v in aenderung.items() if kk != "extras"}
                                                              | {"google_foto": extras.get("google_foto"), "bild_link": extras.get("bild_link"),
                                                                 "bild_fokus": extras.get("bild_fokus"), "foto_version": extras["foto_version"]}, ensure_ascii=False))
        return {"ok": True, "hinweis": "Trockenlauf"}
    client.table("orte").update(aenderung).eq("id", ort_id).execute()
    protokollieren({"ort_id": ort_id, "slug": ort["slug"], "aktion": "bild", "quelle": k["quelle"], "vorher": vorher,
                    "nachher": {kk: v for kk, v in aenderung.items() if kk != "extras"} | {"google_foto": extras.get("google_foto"),
                                                                                         "bild_link": extras.get("bild_link")}})
    return {"ok": True, "hinweis": hinweis}


def nach_deploy() -> int:
    """Website-Bilder auf die eigene Datei umstellen – nur wenn die Datei live erreichbar ist."""
    client, liste = db(), json_lesen(UMSTELLEN, {})
    fertig = 0
    for ort_id, e in list(liste.items()):
        try:
            r = httpx.head(f"https://diesdas.events{e['pfad']}", timeout=20, follow_redirects=True)
        except Exception as fehler:
            logger.warning("%s: Prüfung fehlgeschlagen (%s)", e["slug"], type(fehler).__name__)
            continue
        if r.status_code != 200:
            logger.warning("%s: %s ist live noch nicht da (HTTP %s) – erst deployen", e["slug"], e["pfad"], r.status_code)
            continue
        ort = ort_lesen(client, ort_id)
        if ort.get("bild_url") != e["quelle_url"]:
            logger.info("%s: Bild wurde inzwischen geändert – nicht umgestellt", e["slug"])
            liste.pop(ort_id)
            continue
        extras = dict(ort.get("extras") or {})
        extras["foto_version"] = int(extras.get("foto_version") or 0) + 1
        client.table("orte").update({"bild_url": e["pfad"], "extras": extras}).eq("id", ort_id).execute()
        protokollieren({"ort_id": ort_id, "slug": e["slug"], "aktion": "umstellen", "vorher": {"bild_url": e["quelle_url"]},
                        "nachher": {"bild_url": e["pfad"]}})
        liste.pop(ort_id)
        fertig += 1
    json_schreiben(UMSTELLEN, liste)
    logger.info("Umgestellt: %d, offen: %d", fertig, len(liste))
    return 0


def zurueck(slug: str) -> int:
    """Ort auf den Stand vor der ersten Bildänderung dieser Runde zurücksetzen (aus dem Protokoll)."""
    eintraege = [json.loads(z) for z in PROTOKOLL.read_text(encoding="utf-8").splitlines()] if PROTOKOLL.exists() else []
    eigene = [e for e in eintraege if e["slug"] == slug]
    # Erste Bildänderung nach dem letzten Zurücksetzen = Stand vor dieser Runde
    ab = max((i for i, e in enumerate(eigene) if e["aktion"] == "zurueck"), default=-1)
    letzter = next((e for e in eigene[ab + 1:] if e["aktion"] == "bild"), None)
    if not letzter:
        logger.error("Keine Bildänderung für %s im Protokoll", slug)
        return 1
    client = db()
    ort = ort_lesen(client, letzter["ort_id"])
    v = letzter["vorher"]
    extras = dict(ort.get("extras") or {})
    for feld in ("google_foto", "bild_link", "bild_fokus", "foto_manuell"):
        if v.get(feld) is None:
            extras.pop(feld, None)
        else:
            extras[feld] = v[feld]
    extras["foto_version"] = int(extras.get("foto_version") or 0) + 1
    client.table("orte").update({"bild_url": v.get("bild_url"), "bild_attribution": v.get("bild_attribution"), "extras": extras}).eq("id", letzter["ort_id"]).execute()
    liste = json_lesen(UMSTELLEN, {})
    if liste.pop(letzter["ort_id"], None):
        json_schreiben(UMSTELLEN, liste)
    protokollieren({"ort_id": letzter["ort_id"], "slug": slug, "aktion": "zurueck", "vorher": {}, "nachher": v})
    logger.info("%s: zurückgesetzt", slug)
    return 0


# ── Seite ─────────────────────────────────────────────────────────────────────

def seite() -> str:
    ergebnisse = json_lesen(ERGEBNIS, [])
    auswahl = json_lesen(AUSWAHL, {})
    abschnitte = []
    for e in ergebnisse:
        if not e.get("kandidaten"):
            continue
        vorschlag = auswaehlen(e["kandidaten"])
        vorschlag_nr = e["kandidaten"].index(vorschlag) if vorschlag else None
        gespeichert = auswahl.get(e["id"])
        markiert = gespeichert["wahl"] if gespeichert else ("heute" if vorschlag is None or vorschlag.get("heute") else vorschlag_nr)
        kacheln = [f"""<label class="kachel {'an' if markiert == 'heute' else ''}"><input type="radio" name="{e['id']}" value="heute" {'checked' if markiert == 'heute' else ''}>
<img src="/heute/{html.escape(e['slug'])}" loading="lazy"><span>Heutiges Bild behalten</span></label>"""]
        for i, k in enumerate(e["kandidaten"]):
            if k.get("heute"):
                continue
            ki = k.get("ki") or {}
            format_text = "quer" if (k.get("breite") or 0) >= (k.get("hoehe") or 1) * 1.2 else ("hoch" if (k.get("hoehe") or 0) > (k.get("breite") or 0) * 1.1 else "quadrat")
            kacheln.append(f"""<label class="kachel {'an' if markiert == i else ''}"><input type="radio" name="{e['id']}" value="{i}" {'checked' if markiert == i else ''}>
<img src="/{html.escape(k['vorschau'])}" loading="lazy"><span>{QUELLE_TEXT[k['quelle']]} · {ki.get('motiv', '')} · {format_text}<br>Note {ki.get('note', '–')}{' · Vorschlag' if i == vorschlag_nr else ''}</span></label>""")
        amb = e.get("ambiente") or {}
        status = f'<span class="ok">gespeichert {html.escape(gespeichert.get("zeit", ""))}</span>' if gespeichert else ""
        web = f'<a href="{html.escape(e["webseite"])}" target="_blank" rel="noopener">Website</a>' if e.get("webseite") else "keine Website"
        abschnitte.append(f"""<section data-id="{e['id']}"><h2>{html.escape(e['name'])} <small>{e['typ']} · {html.escape(e.get('stadtteil') or '')} · {web}</small> {status}
<button type="button" class="passt">Auswahl passt</button></h2>
<p class="amb">Ambiente {amb.get('note', '–')}/10 {'(sicher)' if amb.get('sicher') else '(unsicher)'} – {html.escape(amb.get('begruendung', ''))}</p>
<div class="kacheln">{''.join(kacheln)}</div></section>""")
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bilder auswählen</title><style>
body{{font-family:system-ui,sans-serif;margin:0 auto;max-width:1280px;padding:16px 16px 90px;background:#fafaf7;color:#1d1d1b}}
h1{{font-size:22px}} h2{{font-size:17px;margin:26px 0 4px}} small{{font-weight:400;color:#666}} .amb{{font-size:13px;color:#444;margin:0 0 8px}}
.kacheln{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}}
.kachel{{display:block;cursor:pointer;border-radius:10px;padding:4px;border:3px solid transparent;background:#fff}}
.kachel.an{{border-color:#c9a227}} .kachel input{{position:absolute;opacity:0}}
.kachel img{{width:100%;aspect-ratio:16/10;object-fit:cover;border-radius:7px;display:block;background:#ddd}}
.kachel span{{display:block;font-size:12px;color:#555;padding:4px 2px 0}}
.ok{{font-size:12px;color:#1b7f3b;font-weight:600}} section{{border-bottom:1px solid #e2e2dc;padding-bottom:14px}}
.leiste{{position:fixed;left:0;right:0;bottom:0;background:#1d1d1b;color:#fff;padding:12px 16px;display:flex;gap:16px;align-items:center;justify-content:center}}
.leiste button{{background:#c9a227;color:#1d1d1b;border:0;border-radius:8px;padding:10px 18px;font-weight:700;font-size:15px;cursor:pointer}}
.leiste button:disabled{{opacity:.5}}
.passt{{font-size:12px;margin-left:8px;border:1px solid #c9a227;background:#fff;border-radius:6px;padding:3px 8px;cursor:pointer}}
section.geprueft .passt{{background:#c9a227;font-weight:700}} section.geprueft h2::after{{content:" ✓";color:#1b7f3b}}
</style></head><body>
<h1>Bilder auswählen ({len(abschnitte)} Betriebe)</h1>
<p>Vorausgewählt (Goldrahmen) ist der Vorschlag der KI (Innenraum vor Essen). Klick auf ein anderes Bild, um es zu wählen, oder auf
„Auswahl passt“, wenn der Vorschlag stimmt. Gespeichert werden <b>nur Betriebe mit ✓</b>. So kannst du die Liste in Etappen
durchgehen. „Heutiges Bild behalten“ ändert nichts. „Speichern und hochladen“ setzt die Bilder sofort live (Website-Cache bis etwa 10 Minuten).</p>
{''.join(abschnitte)}
<div class="leiste"><span id="info"></span><button id="speichern">Speichern und hochladen</button></div>
<script>
function zaehlen(){{var n=document.querySelectorAll('section.geprueft').length;
  document.getElementById('info').textContent=n+' Betriebe zum Speichern markiert';document.getElementById('speichern').disabled=!n}}
// Auch ein Klick auf das schon vorausgewählte Bild zählt als Bestätigung (dort feuert kein change)
document.querySelectorAll('.kachel input').forEach(function(r){{r.addEventListener('click',function(){{
  r.closest('.kacheln').querySelectorAll('.kachel').forEach(function(k){{k.classList.toggle('an',k.contains(r))}});
  r.closest('section').classList.add('geprueft');zaehlen();
}})}});
document.querySelectorAll('.passt').forEach(function(b){{b.addEventListener('click',function(){{
  b.closest('section').classList.toggle('geprueft');zaehlen();
}})}});
zaehlen();
document.getElementById('speichern').addEventListener('click',async function(){{
  var b=this,info=document.getElementById('info'),wahl={{}};
  document.querySelectorAll('section.geprueft').forEach(function(s){{var r=s.querySelector('input:checked');if(r)wahl[s.dataset.id]=r.value}});
  b.disabled=true;info.textContent='Speichere … (Website-Bilder werden dabei geladen, das dauert etwas)';
  try{{var a=await fetch('/speichern',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(wahl)}});var d=await a.json();
    info.textContent=d.meldung;setTimeout(function(){{location.reload()}},2500);}}
  catch(e){{info.textContent='Fehler: '+e;b.disabled=false}}
}});
</script></body></html>"""


def speichern(wahl: dict) -> dict:
    ergebnisse = {e["id"]: e for e in json_lesen(ERGEBNIS, [])}
    auswahl = json_lesen(AUSWAHL, {})
    client = db()
    geaendert, gleich, fehler = 0, 0, []
    for ort_id, wert in wahl.items():
        e = ergebnisse.get(ort_id)
        if not e:
            continue
        neu = "heute" if wert == "heute" else int(wert)
        if auswahl.get(ort_id, {}).get("wahl") == neu:
            gleich += 1
            continue
        # Wird ein früher gespeichertes Bild auf „heute“ zurückgenommen, gilt wieder der Stand vor dem ersten Speichern
        if neu == "heute":
            if ort_id in auswahl and auswahl[ort_id]["wahl"] != "heute" and not TROCKEN:
                zurueck(e["slug"])
                geaendert += 1
        else:
            k = e["kandidaten"][neu]
            if k.get("heute"):
                neu = "heute"
            else:
                try:
                    bild_setzen(client, ort_id, k)
                    geaendert += 1
                except Exception as f:  # noqa: BLE001 – Fehler je Ort melden, Rest weiter speichern
                    logger.warning("%s: %s", e["name"], f)
                    fehler.append(e["name"])
                    continue
        if TROCKEN:
            continue
        auswahl[ort_id] = {"wahl": neu, "zeit": datetime.now().strftime("%d.%m. %H:%M")}
        json_schreiben(AUSWAHL, auswahl)
    meldung = f"{geaendert} Bilder gesetzt, {gleich} unverändert" + (f", Fehler bei: {', '.join(fehler)}" if fehler else "")
    logger.info(meldung)
    return {"meldung": meldung}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # Zugriffe nicht einzeln loggen
        pass

    def senden(self, status: int, inhalt: bytes, art: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", art)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(inhalt)

    def do_GET(self):  # noqa: N802
        pfad = unquote(urlparse(self.path).path)
        if pfad == "/":
            return self.senden(200, seite().encode("utf-8"), "text/html; charset=utf-8")
        if pfad.startswith("/bilder/"):
            datei = (VORSCHAU / pfad.lstrip("/")).resolve()
            if VORSCHAU.resolve() in datei.parents and datei.is_file():
                return self.senden(200, datei.read_bytes(), "image/webp")
        if pfad.startswith("/heute/"):
            slug = pfad.split("/", 2)[2]
            try:
                r = httpx.get(f"https://diesdas.events/ort-foto/{slug}", timeout=30, follow_redirects=True)
                if r.status_code == 200:
                    return self.senden(200, r.content, r.headers.get("content-type", "image/jpeg"))
            except Exception:
                pass
        self.senden(404, b"nicht gefunden", "text/plain")

    def do_POST(self):  # noqa: N802
        if self.path != "/speichern":
            return self.senden(404, b"", "text/plain")
        laenge = int(self.headers.get("Content-Length") or 0)
        try:
            wahl = json.loads(self.rfile.read(laenge) or b"{}")
            antwort = speichern(wahl if isinstance(wahl, dict) else {})
            self.senden(200, json.dumps(antwort, ensure_ascii=False).encode(), "application/json")
        except Exception as f:  # noqa: BLE001
            logger.exception("Speichern fehlgeschlagen")
            self.senden(500, json.dumps({"meldung": f"Fehler: {f}"}, ensure_ascii=False).encode(), "application/json")


def main():
    p = argparse.ArgumentParser(description="Restaurant-Bilder auswählen und live setzen")
    p.add_argument("--nach-deploy", action="store_true")
    p.add_argument("--zurueck", metavar="SLUG")
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--trocken", action="store_true", help="nichts schreiben (Test)")
    args = p.parse_args()
    global TROCKEN
    TROCKEN = args.trocken
    if args.nach_deploy:
        return nach_deploy()
    if args.zurueck:
        return zurueck(args.zurueck)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    logger.info("Auswahlseite: http://127.0.0.1:%d (Strg+C beendet)", args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
