"""Prüft die Startbeiträge mit den Pipeline-Prüfungen (a)–(i) und schreibt das SQL (Plan Redaktion, Schritt 6).

Aufruf aus dem Repo-Stamm:  .venv/Scripts/python.exe -m docs.magazin-startbeitraege.sql_erzeugen  geht wegen des
Bindestrichs nicht – deshalb:  .venv/Scripts/python.exe docs/magazin-startbeitraege/sql_erzeugen.py <vorschau-datei>

Ausgabe:
- database/magazin_startbeitraege_2026-11-20.sql           – legt beide Beiträge als „in_pruefung“ an (mit Vorschau-Hash)
- database/magazin_startbeitraege_freigabe_2026-11-20.sql  – veröffentlicht beide nach der Durchsicht
- <vorschau-datei> (außerhalb des Repos)                     – Vorschau-Links mit Schlüssel (nie committen)
Bricht ab, wenn eine Prüfung rot ist. Schreibt nichts in die Datenbank.
"""
import hashlib
import json
import secrets
import sys
from datetime import date, datetime, timezone
from pathlib import Path

STAMM = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STAMM))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.magazin import Entwurf, pruefen  # noqa: E402
from beitraege import BEITRAEGE  # noqa: E402

LAUNCH_ZEIT = "2026-11-19 10:00:00+01"  # „Datiere die Veröffentlichung auf gestern“ (Auftraggeber, 20.11.2026)


def sql_text(s: str | None) -> str:
    return "NULL" if s is None else "'" + s.replace("'", "''") + "'"


def sql_array(werte: list[str]) -> str:
    return "ARRAY[" + ", ".join(sql_text(w) for w in werte) + "]::text[]" if werte else "'{}'::text[]"


def sql_json(wert) -> str:
    return sql_text(json.dumps(wert, ensure_ascii=False)) + "::jsonb"


def inhalt(b: dict) -> str:
    teile = []
    for a in b["abschnitte"]:
        if a["ueberschrift"]:
            teile.append(f"## {a['ueberschrift']}")
        teile.append(a["text_md"].strip())
    return "\n\n".join(teile) + "\n"


def main() -> int:
    vorschau_datei = Path(sys.argv[1])
    jetzt = datetime.now(timezone.utc).isoformat()
    zeilen, links, rot = [], [], False
    for b in BEITRAEGE:
        e = Entwurf(titel=b["titel"], teaser=b["teaser"], kurzfassung=b["kurzfassung"], abschnitte=b["abschnitte"],
                    faq=b["faq"])
        # Stadtleben ohne Zeitraum: Prüfzeitraum = Veröffentlichungstag → jedes Datum im Kopf wäre ein Befund
        von = b["gueltig_von"] or date(2026, 11, 19)
        bis = b["gueltig_bis"] or date(2026, 11, 19)
        p = pruefen(e, b["rubrik"], von, bis, [], b["hero_bild"])
        p["lauf"] = "claude-code-session"
        woerter = len("\n".join(a["text_md"] for a in b["abschnitte"]).split())
        print(f"{b['slug']}: Prüfung {p['ergebnis']}, {woerter} Wörter, Titel {len(b['titel'])}, "
              f"Teaser {len(b['teaser'])}, SEO-Titel {len(b['seo_titel'] or '')}")
        for punkt in p["punkte"]:
            print("   ", punkt)
        rot = rot or p["ergebnis"] != "gruen"
        bid, schluessel = b["id"], secrets.token_urlsafe(32)
        links.append(f"{b['titel']}\nhttps://diesdas.events/magazin/vorschau/{bid}?s={schluessel}\n")
        ki = {"modell": "claude-opus-5-5", "art": "claude-code-session", "profil": b["autor_slug"],
              "prompt_version": "manuell-2026-11-20", "datenbasis": "Weihnachtsmarkt-Guide (orte, Stand 17.–19.11.2026)"
              if b["rubrik"] == "saison" else "Plan Redaktion, Seiten von dies.das.düsseldorf", "zeitpunkt": jetzt}
        werte = {
            "id": sql_text(bid), "slug": sql_text(b["slug"]), "rubrik": sql_text(b["rubrik"]),
            "autor_slug": sql_text(b["autor_slug"]), "titel": sql_text(b["titel"]), "seo_titel": sql_text(b["seo_titel"]),
            "teaser": sql_text(b["teaser"]), "inhalt_md": sql_text(inhalt(b)), "kurzfassung": sql_array(b["kurzfassung"]),
            "faq": sql_json(b["faq"]), "hero_bild": sql_text(b["hero_bild"]), "hero_alt": sql_text(b["hero_alt"]),
            "hero_nachweis": sql_text(b["hero_nachweis"]), "hero_ki": "FALSE", "status": "'in_pruefung'",
            "gueltig_von": sql_text(b["gueltig_von"] and b["gueltig_von"].isoformat()),
            "gueltig_bis": sql_text(b["gueltig_bis"] and b["gueltig_bis"].isoformat()),
            "naechste_pruefung": sql_text(b["naechste_pruefung"] and b["naechste_pruefung"].isoformat()),
            "event_ids": "'{}'::uuid[]", "ort_slugs": sql_array(b["ort_slugs"]), "quellen": sql_json(b["quellen"]),
            "ki_entwurf": sql_json(ki), "pruefung": sql_json(p),
            "vorschau_hash": sql_text(hashlib.sha256(schluessel.encode()).hexdigest()),
        }
        spalten = ", ".join(werte)
        aendern = ", ".join(f"{k} = EXCLUDED.{k}" for k in werte if k not in ("id", "slug"))
        zeilen.append(
            f"-- {b['titel']}\nINSERT INTO public.magazin_beitraege ({spalten})\nVALUES ({', '.join(werte.values())})\n"
            f"ON CONFLICT (slug) DO UPDATE SET {aendern}\nWHERE public.magazin_beitraege.status <> 'veroeffentlicht';\n")
    if rot:
        print("Mindestens eine Prüfung ist rot – kein SQL geschrieben.")
        return 1

    kopf = (
        "-- Magazin: die ersten beiden Beiträge (Plan docs/plan-redaktion-2026-11-19.md, Schritt 6, 20.11.2026)\n"
        "-- Erzeugt von docs/magazin-startbeitraege/sql_erzeugen.py aus docs/magazin-startbeitraege/beitraege.py –\n"
        "-- Texte dort ändern und neu erzeugen, nicht hier. Beide Prüfungen (a)–(i) grün.\n"
        "-- Legt die Beiträge als „in_pruefung“ an (sichtbar nur über den Vorschau-Link). Veröffentlicht wird erst mit\n"
        "-- database/magazin_startbeitraege_freigabe_2026-11-20.sql nach der Durchsicht. Wiederholbar, solange nicht\n"
        "-- veröffentlicht (ON CONFLICT … WHERE status <> 'veroeffentlicht'); dann gilt ein neuer Vorschau-Link.\n\n"
        "BEGIN;\n\n")
    kontrolle = (
        "\nCOMMIT;\n\n-- Kontrollabfrage – erwartet zwei Zeilen mit „ok“\n"
        "SELECT slug, status, pruefung ->> 'ergebnis' AS pruefung,\n"
        "       CASE WHEN status = 'in_pruefung' AND pruefung ->> 'ergebnis' = 'gruen' AND vorschau_hash IS NOT NULL\n"
        "            THEN 'ok' ELSE 'FEHLER' END AS kontrolle\n"
        "FROM public.magazin_beitraege\n"
        f"WHERE slug IN ({', '.join(sql_text(b['slug']) for b in BEITRAEGE)})\nORDER BY slug;\n")
    (STAMM / "database" / "magazin_startbeitraege_2026-11-20.sql").write_text(
        kopf + "\n".join(zeilen) + kontrolle, encoding="utf-8")

    l, w = BEITRAEGE[0]["slug"], BEITRAEGE[1]["slug"]
    freigabe = (
        "-- Magazin: Startbeiträge veröffentlichen (Plan Redaktion, Schritt 6) – ERST nach der Durchsicht der Vorschau.\n"
        "-- Der Trigger magazin_status_pruefen lässt das nur im SQL-Editor/Table-Editor (Rolle postgres) zu, nur aus\n"
        "-- „in_pruefung“, nur mit grüner Prüfung und allen Pflichtfeldern. Die Pipeline (service_role) kann es nicht.\n"
        f"-- Der Launch-Beitrag ist auf gestern datiert (Wunsch des Auftraggebers), der Weihnachtsmarkt-Beitrag auf jetzt.\n"
        "-- Sichtbar wird beides nach ein paar Minuten (Cache); solange MAGAZIN_VERLINKT aus ist, bleiben die Seiten\n"
        "-- noindex und unverlinkt.\n\n"
        "BEGIN;\n\n"
        "UPDATE public.magazin_beitraege\n"
        f"SET status = 'veroeffentlicht', veroeffentlicht_am = '{LAUNCH_ZEIT}', freigegeben_von = 'Yannick Fetsch'\n"
        f"WHERE slug = {sql_text(l)} AND status = 'in_pruefung';\n\n"
        "UPDATE public.magazin_beitraege\n"
        "SET status = 'veroeffentlicht', veroeffentlicht_am = now(), freigegeben_von = 'Yannick Fetsch'\n"
        f"WHERE slug = {sql_text(w)} AND status = 'in_pruefung';\n\n"
        "COMMIT;\n\n-- Kontrollabfrage – erwartet zwei Zeilen mit „ok“\n"
        "SELECT slug, status, veroeffentlicht_am, freigegeben_von, freigegeben_am,\n"
        "       CASE WHEN status = 'veroeffentlicht' AND vorschau_hash IS NULL AND freigegeben_am IS NOT NULL\n"
        "            THEN 'ok' ELSE 'FEHLER' END AS kontrolle\n"
        "FROM public.magazin_beitraege\n"
        f"WHERE slug IN ({sql_text(l)}, {sql_text(w)})\nORDER BY slug;\n")
    (STAMM / "database" / "magazin_startbeitraege_freigabe_2026-11-20.sql").write_text(freigabe, encoding="utf-8")
    vorschau_datei.write_text("Vorschau-Links der Startbeiträge (gelten nach dem Ausführen von "
                              "database/magazin_startbeitraege_2026-11-20.sql; nie weitergeben)\n\n" + "\n".join(links),
                              encoding="utf-8")
    print("SQL und Vorschau-Links geschrieben.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
