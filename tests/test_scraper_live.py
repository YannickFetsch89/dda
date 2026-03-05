"""
test_scraper_live.py – DiesDasDüsseldorf
Live-Integration-Tests für alle Scraper.

Ruft jeden Scraper einmal auf und prüft:
- Kein Absturz (kein Exception)
- Rückgabe ist eine Liste
- Falls Events vorhanden: Pflichtfelder gesetzt und Datentypen korrekt

Ausführen:
    python tests/test_scraper_live.py
"""
import importlib
import logging
import sys
from datetime import date

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

PFLICHTFELDER = ["titel", "datum", "ort", "kategorie", "quelle_name", "quelle_url", "status"]
GUELTIGE_KATEGORIEN = {
    "kultur", "musik", "food", "sport", "outdoor",
    "community", "nightlife", "family", "dating", "sonstiges",
}
GUELTIGE_STATUS = {"neu", "aufbereitet", "gepostet", "fehler"}

SCRAPER_MODULE = [
    "scraper.tier1.eventfinder",
    "scraper.tier1.meetup",
    "scraper.tier2.kunstpalast",
    "scraper.tier2.kunstsammlung",
    "scraper.tier2.nrw_forum",
    "scraper.tier2.fft_duesseldorf",
    "scraper.tier2.stahlwerk",
    "scraper.tier2.rudas_studios",
]


def event_validieren(event: dict) -> list[str]:
    """Prüft ein einzelnes Event auf Pflichtfelder und Datentypen."""
    fehler = []
    heute = date.today()

    for feld in PFLICHTFELDER:
        if not event.get(feld):
            fehler.append(f"Pflichtfeld '{feld}' fehlt oder leer")

    if event.get("datum"):
        try:
            d = date.fromisoformat(event["datum"])
            if d < heute:
                fehler.append(f"Datum '{event['datum']}' liegt in der Vergangenheit")
        except ValueError:
            fehler.append(f"Datum '{event['datum']}' ist kein gültiges ISO-Format")

    if event.get("kategorie") and event["kategorie"] not in GUELTIGE_KATEGORIEN:
        fehler.append(f"Ungültige Kategorie: '{event['kategorie']}'")

    if event.get("status") and event["status"] not in GUELTIGE_STATUS:
        fehler.append(f"Ungültiger Status: '{event['status']}'")

    if event.get("beschreibung") and len(event["beschreibung"]) > 300:
        fehler.append(f"Beschreibung zu lang: {len(event['beschreibung'])} Zeichen (max. 300)")

    return fehler


def scraper_testen(modul_pfad: str) -> dict:
    """Lädt und führt einen einzelnen Scraper aus."""
    ergebnis = {
        "modul": modul_pfad,
        "status": "unbekannt",
        "anzahl_events": 0,
        "fehler": [],
        "beispiel_event": None,
    }

    try:
        modul = importlib.import_module(modul_pfad)
    except ImportError as e:
        ergebnis["status"] = "import_fehler"
        ergebnis["fehler"].append(f"Import fehlgeschlagen: {e}")
        return ergebnis

    if not hasattr(modul, "scrape"):
        ergebnis["status"] = "kein_scrape"
        ergebnis["fehler"].append("Modul hat keine scrape()-Funktion")
        return ergebnis

    try:
        events = modul.scrape()
    except Exception as e:
        ergebnis["status"] = "laufzeit_fehler"
        ergebnis["fehler"].append(f"scrape() Exception: {type(e).__name__}: {e}")
        return ergebnis

    if not isinstance(events, list):
        ergebnis["status"] = "falscher_typ"
        ergebnis["fehler"].append(f"scrape() gab {type(events).__name__} zurück, erwartet list")
        return ergebnis

    ergebnis["anzahl_events"] = len(events)

    validierungsfehler = []
    for i, event in enumerate(events[:3]):
        for f in event_validieren(event):
            validierungsfehler.append(f"Event #{i+1}: {f}")
    ergebnis["fehler"].extend(validierungsfehler)

    if events:
        e = events[0]
        ergebnis["beispiel_event"] = {k: e.get(k) for k in PFLICHTFELDER + ["uhrzeit", "bild_url"]}

    if not ergebnis["fehler"]:
        ergebnis["status"] = "ok" if events else "leer"
    else:
        ergebnis["status"] = "validierungsfehler"

    return ergebnis


def alle_scraper_testen() -> int:
    """Führt alle Scraper-Tests aus und gibt eine Zusammenfassung aus."""
    print("=" * 70)
    print("DiesDasDüsseldorf – Live-Test aller Scraper")
    print(f"Datum: {date.today().isoformat()}")
    print("=" * 70)

    ergebnisse = []
    for modul in SCRAPER_MODULE:
        print(f"\n► Teste: {modul} ...", flush=True)
        ergebnis = scraper_testen(modul)
        ergebnisse.append(ergebnis)

        symbol = {
            "ok": "[OK]",
            "leer": "[LEER]",
            "import_fehler": "[FEHLER]",
            "kein_scrape": "[FEHLER]",
            "laufzeit_fehler": "[FEHLER]",
            "falscher_typ": "[FEHLER]",
            "validierungsfehler": "[WARNUNG]",
        }.get(ergebnis["status"], "[?]")

        print(f"  {symbol} Status: {ergebnis['status']} | Events: {ergebnis['anzahl_events']}")

        for f in ergebnis["fehler"][:3]:
            print(f"     -> {f}")

        if ergebnis["beispiel_event"]:
            e = ergebnis["beispiel_event"]
            print(f"     Beispiel: {e.get('titel', '?')} | {e.get('datum', '?')} | {e.get('ort', '?')}")

    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    ok = sum(1 for r in ergebnisse if r["status"] == "ok")
    leer = sum(1 for r in ergebnisse if r["status"] == "leer")
    fehler_count = sum(1 for r in ergebnisse if r["status"] not in ("ok", "leer", "validierungsfehler"))
    warnungen = sum(1 for r in ergebnisse if r["status"] == "validierungsfehler")
    gesamt_events = sum(r["anzahl_events"] for r in ergebnisse)

    print(f"  Scraper gesamt:  {len(ergebnisse)}")
    print(f"  Erfolgreich:     {ok}")
    print(f"  Leer:            {leer}")
    print(f"  Warnungen:       {warnungen}")
    print(f"  Fehler:          {fehler_count}")
    print(f"  Events gesamt:   {gesamt_events}")
    print("=" * 70)

    return 0 if fehler_count == 0 else 1


if __name__ == "__main__":
    sys.exit(alle_scraper_testen())
