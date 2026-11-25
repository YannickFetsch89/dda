"""Prüft Redaktionsbeiträge aus einer Datei mit BEITRAEGE und schreibt SQL zum Anlegen und Freigeben (ab 25.11.2026).

Wie sql_erzeugen.py (Startbeiträge), aber allgemein und mit Event-Einbettungen:
- {{event:<uuid>}} im Text → event_ids und Kandidaten der Prüfung (a), damit nur eingebettete Events zählen.
- Die Beiträge brauchen eine feste "id" (so bleiben Vorschau-Links nach erneutem Anlegen gültig).

Aufruf aus dem Repo-Stamm:
  .venv/Scripts/python.exe docs/magazin-startbeitraege/beitraege_sql.py <modul> <name> <vorschau-datei>
  z. B. beitraege_2026_11_25 magazin_beitraege_2026-11-25 C:/…/magazin-vorschau-links.txt
Ausgabe: database/<name>.sql (anlegen, in_pruefung), database/<name>_freigabe.sql (veröffentlichen, jetzt),
Vorschau-Links werden an <vorschau-datei> (außerhalb des Repos) angehängt. Bricht ab, wenn eine Prüfung rot ist.
"""
import hashlib
import importlib
import json
import re
import secrets
import sys
from datetime import date, datetime, timezone
from pathlib import Path

STAMM = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STAMM))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.magazin import Entwurf, pruefen  # noqa: E402
from sql_erzeugen import inhalt, sql_array, sql_json, sql_text  # noqa: E402

EVENT = re.compile(r"\{\{event:([0-9a-f-]{36})\}\}")


def main() -> int:
    modul, name, vorschau_datei = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    beitraege = importlib.import_module(modul).BEITRAEGE
    jetzt = datetime.now(timezone.utc).isoformat()
    zeilen, links, rot = [], [], False
    for b in beitraege:
        md = inhalt(b)
        ids = list(dict.fromkeys(EVENT.findall(md)))
        e = Entwurf(titel=b["titel"], teaser=b["teaser"], kurzfassung=b["kurzfassung"], abschnitte=b["abschnitte"], faq=b["faq"])
        # Ohne Zeitraum (zeitlos): Prüfzeitraum = heute → jedes Datum im Kopf wäre ein Befund
        von = b["gueltig_von"] or date.today()
        bis = b["gueltig_bis"] or date.today()
        p = pruefen(e, b["rubrik"], von, bis, [{"id": i, "pfad": ""} for i in ids], b["hero_bild"])
        p["lauf"] = "claude-code-session"
        woerter = len("\n".join(a["text_md"] for a in b["abschnitte"]).split())
        print(f"{b['slug']}: Prüfung {p['ergebnis']}, {woerter} Wörter, {len(ids)} Events, Titel {len(b['titel'])}, "
              f"Teaser {len(b['teaser'])}, SEO-Titel {len(b['seo_titel'] or '')}")
        for punkt in p["punkte"]:
            print("   ", punkt)
        rot = rot or p["ergebnis"] != "gruen"
        schluessel = secrets.token_urlsafe(32)
        links.append(f"{b['titel']}\nhttps://diesdas.events/magazin/vorschau/{b['id']}?s={schluessel}\n")
        ki = {"modell": "claude-opus-5-5", "art": "claude-code-session", "profil": b["autor_slug"],
              "prompt_version": f"manuell-{date.today().isoformat()}", "datenbasis": b.get("datenbasis", ""), "zeitpunkt": jetzt}
        werte = {
            "id": sql_text(b["id"]), "slug": sql_text(b["slug"]), "rubrik": sql_text(b["rubrik"]),
            "autor_slug": sql_text(b["autor_slug"]), "titel": sql_text(b["titel"]), "seo_titel": sql_text(b["seo_titel"]),
            "teaser": sql_text(b["teaser"]), "inhalt_md": sql_text(md), "kurzfassung": sql_array(b["kurzfassung"]),
            "faq": sql_json(b["faq"]), "hero_bild": sql_text(b["hero_bild"]), "hero_alt": sql_text(b["hero_alt"]),
            "hero_nachweis": sql_text(b["hero_nachweis"]), "hero_ki": "FALSE", "status": "'in_pruefung'",
            "gueltig_von": sql_text(b["gueltig_von"] and b["gueltig_von"].isoformat()),
            "gueltig_bis": sql_text(b["gueltig_bis"] and b["gueltig_bis"].isoformat()),
            "naechste_pruefung": sql_text(b["naechste_pruefung"] and b["naechste_pruefung"].isoformat()),
            "event_ids": ("ARRAY[" + ", ".join(sql_text(i) for i in ids) + "]::uuid[]") if ids else "'{}'::uuid[]",
            "ort_slugs": sql_array(b["ort_slugs"]), "quellen": sql_json(b["quellen"]),
            "ki_entwurf": sql_json(ki), "pruefung": sql_json(p),
            "vorschau_hash": sql_text(hashlib.sha256(schluessel.encode()).hexdigest()),
        }
        aendern = ", ".join(f"{k} = EXCLUDED.{k}" for k in werte if k not in ("id", "slug"))
        zeilen.append(f"-- {b['titel']}\nINSERT INTO public.magazin_beitraege ({', '.join(werte)})\n"
                      f"VALUES ({', '.join(werte.values())})\nON CONFLICT (slug) DO UPDATE SET {aendern}\n"
                      f"WHERE public.magazin_beitraege.status <> 'veroeffentlicht';\n")
    if rot:
        print("Mindestens eine Prüfung ist rot – kein SQL geschrieben.")
        return 1
    slugs = ", ".join(sql_text(b["slug"]) for b in beitraege)
    (STAMM / "database" / f"{name}.sql").write_text(
        f"-- Magazin: Redaktionsbeiträge {name} (Claude-Code-Session, Prüfungen (a)–(i) grün)\n"
        f"-- Erzeugt von docs/magazin-startbeitraege/beitraege_sql.py aus docs/magazin-startbeitraege/{modul}.py –\n"
        "-- Texte dort ändern und neu erzeugen. Legt die Beiträge als „in_pruefung“ an (nur per Vorschau-Link sichtbar),\n"
        "-- wiederholbar, solange nicht veröffentlicht. Veröffentlichen mit der Datei _freigabe.\n\nBEGIN;\n\n"
        + "\n".join(zeilen)
        + "\nCOMMIT;\n\n-- Kontrollabfrage – erwartet je Beitrag eine Zeile mit „ok“\n"
        "SELECT slug, status, pruefung ->> 'ergebnis' AS pruefung,\n"
        "       CASE WHEN status = 'in_pruefung' AND pruefung ->> 'ergebnis' = 'gruen' AND vorschau_hash IS NOT NULL\n"
        "            THEN 'ok' ELSE 'FEHLER' END AS kontrolle\n"
        f"FROM public.magazin_beitraege WHERE slug IN ({slugs}) ORDER BY slug;\n", encoding="utf-8")
    (STAMM / "database" / f"{name}_freigabe.sql").write_text(
        f"-- Magazin: {name} veröffentlichen – ERST nach der Durchsicht der Vorschau. Nur im SQL-/Table-Editor (postgres),\n"
        "-- nur aus „in_pruefung“, mit grüner Prüfung und allen Pflichtfeldern (Trigger magazin_status_pruefen).\n\nBEGIN;\n\n"
        "UPDATE public.magazin_beitraege\n"
        "SET status = 'veroeffentlicht', veroeffentlicht_am = now(), freigegeben_von = 'Yannick Fetsch'\n"
        f"WHERE slug IN ({slugs}) AND status = 'in_pruefung';\n\nCOMMIT;\n\n"
        "-- Kontrollabfrage – erwartet je Beitrag eine Zeile mit „ok“\n"
        "SELECT slug, status, veroeffentlicht_am,\n"
        "       CASE WHEN status = 'veroeffentlicht' AND vorschau_hash IS NULL THEN 'ok' ELSE 'FEHLER' END AS kontrolle\n"
        f"FROM public.magazin_beitraege WHERE slug IN ({slugs}) ORDER BY slug;\n", encoding="utf-8")
    with open(vorschau_datei, "a", encoding="utf-8") as f:
        f.write(f"\n\n{name} (angelegt {date.today().isoformat()})\n" + "\n".join(links))
    print("SQL geschrieben, Vorschau-Links angehängt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
