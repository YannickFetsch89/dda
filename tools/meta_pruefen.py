"""
meta_pruefen.py – DiesDasDüsseldorf
Prüfskript für die Meta-Einrichtung (Plan docs/plan-social-2026-11-25.md, Schritt 0, Abschnitt 9 Punkt 6).
Anleitung: docs/meta-einrichtung-anleitung.md

Liest META_TOKEN (Systembenutzer-Token) und optional META_PAGE_ID / META_IG_ID aus secrets/meta.env
(gitignored, Vorlage secrets/meta.env.example). Der Token wird nie ausgegeben und nie in eine URL geschrieben
(Kopf „Authorization: Bearer …“), damit er auch in Fehlermeldungen nicht auftaucht.

Aufrufe:
  py tools/meta_pruefen.py                                   # Grundprüfung, veröffentlicht nichts
  py tools/meta_pruefen.py --test-bild <jpeg-url>            # Bild-Container anlegen, NICHT veröffentlichen
  py tools/meta_pruefen.py --test-reel <mp4-url>             # Reel-Container anlegen, Status abwarten, NICHT veröffentlichen
  py tools/meta_pruefen.py --test-story <jpeg-url> --wirklich-veroeffentlichen
                                                            # Test-Story: ÖFFENTLICH für 24 Stunden
  py tools/meta_pruefen.py --video-bauen <a.jpg> <b.jpg> <ziel.mp4>
                                                            # 6-s-Testvideo mit den Reel-Parametern aus E11 bauen
                                                            # und prüfen (braucht ffmpeg lokal)

Nicht veröffentlichte Container verfallen bei Meta nach 24 Stunden von selbst.
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

import httpx
from dotenv import dotenv_values

WURZEL = Path(__file__).resolve().parent.parent
ENV_DATEI = WURZEL / "secrets" / "meta.env"

# Graph-API-Version: beim Bau des Social-Jobs gegen die aktuelle Meta-Doku prüfen (Plan Abschnitt 8)
GRAPH = "https://graph.facebook.com/v27.0"

# Rechte aus Plan Abschnitt 9 Punkt 3
PFLICHT_RECHTE = [
    "instagram_basic", "instagram_content_publish", "pages_show_list", "pages_read_engagement",
    "pages_manage_posts", "business_management", "ads_read",
]

# Reel-Parameter wie Plan E11 (Meta: H.264, 4:2:0, progressiv, geschlossene GOP, moov vorn, keine Edit-List, AAC ≤ 48 kHz)
def ffmpeg_reel_befehl(bilder: list[str], ziel: str, sekunden_je_bild: float = 3.0) -> list[str]:
    befehl = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for bild in bilder:
        befehl += ["-loop", "1", "-t", str(sekunden_je_bild), "-i", bild]
    befehl += ["-f", "lavfi", "-t", str(sekunden_je_bild * len(bilder)), "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    teile = "".join(
        f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{i}];"
        for i in range(len(bilder))
    )
    kette = "".join(f"[v{i}]" for i in range(len(bilder)))
    befehl += [
        "-filter_complex", f"{teile}{kette}concat=n={len(bilder)}:v=1:a=0[v]",
        "-map", "[v]", "-map", f"{len(bilder)}:a",
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30",
        "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", "-flags", "+cgop",
        "-c:a", "aac", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart", "-use_editlist", "0",
        ziel,
    ]
    return befehl


def mp4_atome(pfad: str) -> list[str]:
    """Liest die Atom-Namen der obersten Ebene und sucht zusätzlich nach 'elst' irgendwo in der Datei."""
    daten = Path(pfad).read_bytes()
    namen, pos = [], 0
    while pos + 8 <= len(daten):
        groesse, name = struct.unpack(">I4s", daten[pos:pos + 8])
        if groesse == 1:
            groesse = struct.unpack(">Q", daten[pos + 8:pos + 16])[0]
        elif groesse == 0:
            groesse = len(daten) - pos
        namen.append(name.decode("latin-1"))
        if groesse < 8:
            break
        pos += groesse
    if b"elst" in daten:
        namen.append("elst!")
    return namen


def video_pruefen(pfad: str) -> list[str]:
    """Gibt eine Liste von Problemen zurück (leer = in Ordnung)."""
    probleme = []
    atome = mp4_atome(pfad)
    if "moov" not in atome or "mdat" not in atome or atome.index("moov") > atome.index("mdat"):
        probleme.append(f"moov steht nicht vor mdat (Atome: {atome})")
    if "elst!" in atome:
        probleme.append("Datei enthält eine Edit-List (elst)")
    if shutil.which("ffprobe"):
        aus = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,pix_fmt,sample_rate,channels:format=duration",
             "-of", "default=nw=1", pfad], capture_output=True, text=True, check=False).stdout
        for erwartet in ("codec_name=h264", "pix_fmt=yuv420p", "codec_name=aac", "sample_rate=48000"):
            if erwartet not in aus:
                probleme.append(f"ffprobe: {erwartet} fehlt")
        dauer = next((float(z.split("=")[1]) for z in aus.splitlines() if z.startswith("duration=")), 0.0)
        if not 3 <= dauer <= 90:
            probleme.append(f"Dauer {dauer:.1f} s außerhalb 3–90 s")
    else:
        probleme.append("ffprobe nicht gefunden – Codec/Dauer nicht geprüft")
    return probleme


# ── Graph-API ────────────────────────────────────────────────────────────────────────────────────

class Meta:
    def __init__(self, token: str):
        self.client = httpx.Client(timeout=30, headers={"Authorization": f"Bearer {token}"})

    def get(self, pfad: str, **params) -> dict:
        return self._antwort(self.client.get(f"{GRAPH}/{pfad}", params=params))

    def post(self, pfad: str, token: str | None = None, **params) -> dict:
        kopf = {"Authorization": f"Bearer {token}"} if token else None
        return self._antwort(self.client.post(f"{GRAPH}/{pfad}", data=params, headers=kopf))

    @staticmethod
    def _antwort(antwort: httpx.Response) -> dict:
        try:
            daten = antwort.json()
        except ValueError:
            return {"error": {"message": f"keine JSON-Antwort (HTTP {antwort.status_code})"}}
        return daten


def fehlertext(daten: dict) -> str | None:
    f = daten.get("error")
    if not f:
        return None
    return f"{f.get('message', '?')} (Code {f.get('code', '?')}, Untercode {f.get('error_subcode', '-')})"


def zeile(ok: bool, text: str) -> bool:
    print(f"  {'✓' if ok else '✗'} {text}")
    return ok


def grundpruefung(meta: Meta, token: str, page_id: str | None, ig_id: str | None) -> tuple[str | None, str | None, str | None]:
    """Prüft Token, Rechte, Seite, Instagram-Konto und Limit. Gibt (page_id, ig_id, seiten_token) zurück."""
    print("\n1. Token und Rechte")
    info = meta.get("debug_token", input_token=token)
    daten = info.get("data", {})
    if not zeile(bool(daten.get("is_valid")), f"Token gültig ({fehlertext(info) or daten.get('type', '?')})"):
        return None, None, None
    ablauf = daten.get("expires_at", 0)
    zeile(ablauf == 0, "läuft nie ab" if ablauf == 0 else f"läuft ab am {time.strftime('%d.%m.%Y', time.localtime(ablauf))}")
    rechte = set(daten.get("scopes", []))
    for recht in PFLICHT_RECHTE:
        zeile(recht in rechte, f"Recht {recht}")

    print("\n2. Facebook-Seite und Instagram-Konto")
    if not page_id:
        seiten = meta.get("me/accounts", fields="id,name,instagram_business_account")
        if fehlertext(seiten):
            zeile(False, f"Seiten nicht lesbar: {fehlertext(seiten)}")
            return None, None, None
        for s in seiten.get("data", []):
            print(f"    Seite: {s.get('name')}  META_PAGE_ID={s.get('id')}  "
                  f"META_IG_ID={(s.get('instagram_business_account') or {}).get('id', '–')}")
        if len(seiten.get("data", [])) != 1:
            print("    → Bitte META_PAGE_ID in secrets/meta.env eintragen und erneut starten.")
            return None, None, None
        page_id = seiten["data"][0]["id"]
    seite = meta.get(page_id, fields="name,link,instagram_business_account,access_token")
    if not zeile(not fehlertext(seite), f"Seite {seite.get('name', page_id)} lesbar ({fehlertext(seite) or seite.get('link', '')})"):
        return None, None, None
    seiten_token = seite.get("access_token")
    zeile(bool(seiten_token), "Seiten-Token abrufbar (wird nicht angezeigt)")
    ig_von_seite = (seite.get("instagram_business_account") or {}).get("id")
    ig_id = ig_id or ig_von_seite
    if not zeile(bool(ig_id), f"Instagram-Konto mit der Seite verknüpft (META_IG_ID={ig_id or '–'})"):
        return page_id, None, seiten_token
    if ig_von_seite and ig_id != ig_von_seite:
        zeile(False, f"META_IG_ID {ig_id} passt nicht zur Seite ({ig_von_seite})")

    seiten_meta = Meta(seiten_token) if seiten_token else meta
    konto = seiten_meta.get(ig_id, fields="username,name")
    zeile(not fehlertext(konto) and konto.get("username") == "dies.das.duesseldorf",
          f"Instagram @{konto.get('username', '?')} ({fehlertext(konto) or 'erwartet: @dies.das.duesseldorf'})")
    limit = seiten_meta.get(f"{ig_id}/content_publishing_limit", fields="config,quota_usage")
    eintrag = (limit.get("data") or [{}])[0]
    zeile(not fehlertext(limit),
          f"Veröffentlichungs-Limit: {eintrag.get('quota_usage', '?')} von {(eintrag.get('config') or {}).get('quota_total', '?')} in 24 h"
          + (f" ({fehlertext(limit)})" if fehlertext(limit) else ""))
    return page_id, ig_id, seiten_token


def container_warten(meta: Meta, container: str, minuten: int = 10) -> str:
    ende = time.time() + minuten * 60
    status = "?"
    while time.time() < ende:
        antwort = meta.get(container, fields="status_code,status")
        status = antwort.get("status_code") or fehlertext(antwort) or "?"
        print(f"    Status: {status}")
        if status in ("FINISHED", "ERROR", "EXPIRED", "PUBLISHED") or fehlertext(antwort):
            if status == "ERROR":
                print(f"    Meta meldet: {antwort.get('status', '')}")
            return status
        time.sleep(15)
    return status


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Meta-Einrichtung prüfen (Social-Plan Schritt 0)")
    p.add_argument("--test-bild", metavar="JPEG_URL", help="Bild-Container anlegen, nicht veröffentlichen")
    p.add_argument("--test-reel", metavar="MP4_URL", help="Reel-Container anlegen und Status abwarten, nicht veröffentlichen")
    p.add_argument("--test-story", metavar="JPEG_URL", help="Test-Story veröffentlichen (öffentlich, 24 h)")
    p.add_argument("--wirklich-veroeffentlichen", action="store_true", help="Pflicht für --test-story")
    p.add_argument("--video-bauen", nargs=3, metavar=("BILD_A", "BILD_B", "ZIEL_MP4"), help="Testvideo bauen und prüfen")
    p.add_argument("--env", default=str(ENV_DATEI), help="Pfad zur meta.env (Standard: secrets/meta.env im Repo)")
    args = p.parse_args(argv)

    if args.video_bauen:
        if not shutil.which("ffmpeg"):
            print("ffmpeg nicht gefunden. Ohne ffmpeg kann das Testvideo nicht gebaut werden.")
            return 1
        a, b, ziel = args.video_bauen
        subprocess.run(ffmpeg_reel_befehl([a, b], ziel), check=True)
        probleme = video_pruefen(ziel)
        print("Testvideo in Ordnung." if not probleme else "Probleme:\n  - " + "\n  - ".join(probleme))
        return 0 if not probleme else 1

    werte = {**dotenv_values(args.env), **{k: v for k, v in os.environ.items() if k.startswith("META_")}}
    token = (werte.get("META_TOKEN") or "").strip()
    if not token:
        print(f"META_TOKEN fehlt. Bitte in {args.env} eintragen (Vorlage: secrets/meta.env.example).")
        return 1
    meta = Meta(token)
    page_id, ig_id, seiten_token = grundpruefung(
        meta, token, (werte.get("META_PAGE_ID") or "").strip() or None, (werte.get("META_IG_ID") or "").strip() or None)
    if not (ig_id and seiten_token):
        print("\nGrundprüfung nicht bestanden – Tests übersprungen.")
        return 1
    seite = Meta(seiten_token)  # Instagram mit Facebook-Login: Aufrufe mit dem Seiten-Token (Plan E13)

    if args.test_bild:
        print("\n3. Test-Container Bild (wird nicht veröffentlicht)")
        antwort = seite.post(f"{ig_id}/media", image_url=args.test_bild)
        if zeile(not fehlertext(antwort), f"Container angelegt ({fehlertext(antwort) or antwort.get('id')})"):
            zeile(container_warten(seite, antwort["id"], 2) == "FINISHED", "Meta hat das Bild angenommen")

    if args.test_reel:
        print("\n4. Test-Container Reel (wird nicht veröffentlicht)")
        antwort = seite.post(f"{ig_id}/media", media_type="REELS", video_url=args.test_reel, share_to_feed="false")
        if zeile(not fehlertext(antwort), f"Container angelegt ({fehlertext(antwort) or antwort.get('id')})"):
            zeile(container_warten(seite, antwort["id"]) == "FINISHED", "Meta hat das Video angenommen")

    if args.test_story:
        print("\n5. Test-Story (öffentlich für 24 Stunden)")
        if not args.wirklich_veroeffentlichen:
            print("  Übersprungen: --wirklich-veroeffentlichen fehlt.")
        else:
            antwort = seite.post(f"{ig_id}/media", media_type="STORIES", image_url=args.test_story)
            if zeile(not fehlertext(antwort), f"Story-Container angelegt ({fehlertext(antwort) or antwort.get('id')})"):
                if container_warten(seite, antwort["id"], 2) == "FINISHED":
                    veroeffentlicht = seite.post(f"{ig_id}/media_publish", creation_id=antwort["id"])
                    zeile(not fehlertext(veroeffentlicht),
                          f"Story veröffentlicht ({fehlertext(veroeffentlicht) or veroeffentlicht.get('id')}) – bitte in der App ansehen")

    print("\nFertig. IDs (nicht geheim) für GitHub-Variablen: "
          f"META_PAGE_ID={page_id}  META_IG_ID={ig_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
