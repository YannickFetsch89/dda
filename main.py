"""
main.py – DiesDasDüsseldorf
Einstiegspunkt: Startet die tägliche Event-Pipeline
"""
import asyncio
import logging
import sys
from datetime import date

from config import LOG_LEVEL, LOG_DIR, SCHEDULER_UHRZEIT
from database.client import events_speichern
from pipeline.lauf_report import LaufReport
from scraper.tier1 import (
    rausgegangen,
    ticketmaster,
    kulturportal,
    visitduesseldorf,
    visitduesseldorf_fuehrungen,
    meetup,
    resident_advisor,
    prinz,
    songkick,
    allevents,
    # bandsintown deaktiviert – komplette Domain per Cloudflare-WAF blockiert (HTTP 403)
    # meinestadt deaktiviert – dauerhaft durch Akamai WAF blockiert (HTTP 403)
    # eventbrite deaktiviert – API v3 abgeschaltet, Website durch Bot-Schutz blockiert
    # eventfinder deaktiviert – keine zuverlässige Datenquelle
)
from scraper.tier2 import (
    tonhalle,
    zakk,
    oper_am_rhein,
    schauspielhaus,
    dlive,
    kunstpalast,
    kunstsammlung,
    nrw_forum,
    fft_duesseldorf,
    stahlwerk,
    rudas_studios,
    mitsubishi_halle,
    kulturschlachthof_r25,
    salon_des_amateurs,
    pitcher,
    kunsthalle,
    filmmuseum,
    stadtbuechereien,
    tanzhaus_nrw,
    jazz_schmiede,
    capitol_theater,
    kommoedchen,
    startplatz,
)
from scraper.tier3 import (
    parkrun,
    sport_im_park,
    fortuna,
    deg,
    messe,
    japan_center,
    classic_remise,
    stadtstrand,
    # spontacts deaktiviert – Aktivitäten nur noch nach Login sichtbar (robots.txt sperrt Listen)
    ihk,
    startupdorf,
    street_food_thursday,
    auf_ins_viertel,
)

# Logging konfigurieren
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"{LOG_DIR}/pipeline.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Alle Quellen in Ausführungsreihenfolge: (Anzeigename, Tier, scrape-Funktion).
# Der Anzeigename erscheint so im Log und im Scraper-Report des Dashboards –
# bei Umbenennung reißt dort der Verlauf der Quelle ab.
QUELLEN = [
    # Tier 1: Aggregatoren und APIs
    ("Ticketmaster", 1, ticketmaster.scrape),
    ("Kulturportal Düsseldorf", 1, kulturportal.scrape),
    ("VisitDüsseldorf", 1, visitduesseldorf.scrape),
    ("VisitDüsseldorf Führungen", 1, visitduesseldorf_fuehrungen.scrape),  # Stadtführungen aus den Event-Seiten
    ("Meetup.com", 1, meetup.scrape),
    ("Resident Advisor", 1, resident_advisor.scrape),
    ("PRINZ.de Düsseldorf", 1, prinz.scrape),
    ("Songkick", 1, songkick.scrape),
    ("AllEvents.in Düsseldorf", 1, allevents.scrape),
    # Tier 2: Venue-eigene Kalender
    ("Tonhalle Düsseldorf", 2, tonhalle.scrape),
    ("zakk", 2, zakk.scrape),
    ("Deutsche Oper am Rhein", 2, oper_am_rhein.scrape),
    ("Düsseldorfer Schauspielhaus", 2, schauspielhaus.scrape),
    ("d-live", 2, dlive.scrape),
    ("Kunstpalast Düsseldorf", 2, kunstpalast.scrape),
    ("Kunstsammlung NRW (K20/K21)", 2, kunstsammlung.scrape),
    ("NRW-Forum Düsseldorf", 2, nrw_forum.scrape),
    ("FFT Düsseldorf", 2, fft_duesseldorf.scrape),
    ("Stahlwerk Düsseldorf", 2, stahlwerk.scrape),
    ("Rudas Studios Düsseldorf", 2, rudas_studios.scrape),
    ("Mitsubishi Electric HALLE", 2, mitsubishi_halle.scrape),
    ("Kulturschlachthof R25", 2, kulturschlachthof_r25.scrape),
    ("Salon des Amateurs", 2, salon_des_amateurs.scrape),
    ("Pitcher Rock HQ", 2, pitcher.scrape),
    ("Kunsthalle Düsseldorf", 2, kunsthalle.scrape),
    ("Filmmuseum Düsseldorf", 2, filmmuseum.scrape),
    ("Stadtbüchereien Düsseldorf", 2, stadtbuechereien.scrape),
    ("Tanzhaus NRW", 2, tanzhaus_nrw.scrape),
    ("Jazz-Schmiede Düsseldorf", 2, jazz_schmiede.scrape),
    ("Capitol Theater Düsseldorf", 2, capitol_theater.scrape),
    ("Kom(m)ödchen Düsseldorf", 2, kommoedchen.scrape),
    ("STARTPLATZ Düsseldorf", 2, startplatz.scrape),
    # Tier 3: Nischen- und Spezialquellen
    ("Parkrun Volksgarten Düsseldorf", 3, parkrun.scrape),
    ("Sport im Park Düsseldorf", 3, sport_im_park.scrape),
    ("Fortuna Düsseldorf", 3, fortuna.scrape),
    ("DEG Eishockey Düsseldorf", 3, deg.scrape),
    ("Messe Düsseldorf", 3, messe.scrape),
    ("EKŌ-Haus der Japanischen Kultur", 3, japan_center.scrape),  # Ersatz für das Japan Center (Domain tot)
    ("Classic Remise Düsseldorf", 3, classic_remise.scrape),
    ("Stadtstrand Düsseldorf", 3, stadtstrand.scrape),
    ("IHK Düsseldorf", 3, ihk.scrape),
    ("StartupDorf Meetup", 3, startupdorf.scrape),
    ("Street Food Thursday", 3, street_food_thursday.scrape),
    ("Auf ins Viertel", 3, auf_ins_viertel.scrape),  # kulinarische Stadtführungen (bookingkit)
    # Rausgegangen zuletzt: Events, die eine andere Quelle schon liefert, behalten diese als Quelle –
    # Rausgegangen ergänzt nur noch fehlende Felder (Vorrang-Regel in pipeline/deduplication.py)
    ("Rausgegangen", 1, rausgegangen.scrape),
]


async def pipeline_ausfuehren():
    """
    Führt die vollständige Pipeline aus und protokolliert sie im Lauf-Report:
    1. Scraper starten (Tier 1, 2, 3)
    2. Duplikate entfernen, Stadtteile zuordnen, speichern
    3. Events kategorisieren
    4. Instagram Captions generieren
    5. Posts veröffentlichen
    """
    logger.info("=== DiesDasDüsseldorf Pipeline gestartet ===")
    logger.info("Datum: %s", date.today().isoformat())

    report = LaufReport()
    report.starten()

    try:
        await _schritte_ausfuehren(report)
    except Exception as e:
        logger.exception("Pipeline abgebrochen: %s", e)
        report.abschliessen(fehlermeldung=f"{type(e).__name__}: {e}")
        raise

    report.abschliessen()
    logger.info("=== Pipeline abgeschlossen ===")


async def _schritte_ausfuehren(report: LaufReport):
    """Die eigentlichen Pipeline-Schritte (Fehler werden in pipeline_ausfuehren protokolliert)."""
    from datetime import datetime, timezone
    lauf_start = datetime.now(timezone.utc)  # für IndexNow: welche Events hat dieser Lauf angelegt?
    # Schritt 1: Scraper ausführen (nacheinander, jeder einzeln abgesichert)
    logger.info("--- Schritt 1: Scraper ---")
    alle_events = []
    aktueller_tier = 0
    for name, tier, funktion in QUELLEN:
        if tier != aktueller_tier:
            aktueller_tier = tier
            logger.info("--- Tier-%d-Scraper ---", tier)
        alle_events.extend(await report.scraper_ausfuehren(name, tier, funktion))

    logger.info("Scraper gesamt: %d Events gesammelt", len(alle_events))
    report.kennzahl(events_gesammelt=len(alle_events))

    # Schritt 1d: In-Memory-Deduplizierung mit Merge-Logik
    logger.info("--- Schritt 1d: In-Memory-Deduplizierung ---")
    from pipeline.deduplication import deduplizieren
    alle_events = deduplizieren(alle_events)
    report.kennzahl(events_nach_dedup=len(alle_events))

    # Schritt 1e: Stadtteil-Zuordnung
    logger.info("--- Schritt 1e: Stadtteil-Zuordnung ---")
    from pipeline.stadtteil_mapper import stadtteil_batch_zuordnen
    alle_events = stadtteil_batch_zuordnen(alle_events)

    # Schritt 2: In Supabase speichern (mit DB-seitiger Anreicherung)
    logger.info("--- Schritt 2: Datenbank ---")
    stats = events_speichern(alle_events)
    logger.info(
        "Ergebnis – Neu gespeichert: %d | Duplikate: %d | Angereichert: %d | Fehler: %d",
        stats["gespeichert"], stats["duplikate"], stats.get("angereichert", 0), stats["fehler"]
    )
    report.kennzahl(
        neu_gespeichert=stats["gespeichert"],
        duplikate=stats["duplikate"],
        angereichert=stats.get("angereichert", 0),
        speicher_fehler=stats["fehler"],
    )
    report.neu_pro_quelle_setzen(stats.get("neu_pro_quelle") or {})

    # Schritt 2a: Reihen (wiederkehrende Events) erkennen und zuordnen – für /reihe/<slug>
    logger.info("--- Schritt 2a: Reihen zuordnen ---")
    try:
        from pipeline.reihen_zuordnen import reihen_zuordnen
        reihen_zuordnen()
    except Exception as e:
        logger.error("Reihen-Zuordnung fehlgeschlagen: %s", e)

    # Schritt 2b: Löschfrist „Event melden“ (vor den KI-Schritten, damit ein späterer Abbruch sie nicht verhindert)
    logger.info("--- Schritt 2b: Alte Event-Meldungen löschen ---")
    try:
        from pipeline.meldungen_aufraeumen import meldungen_aufraeumen
        meldungen_aufraeumen()
    except Exception as e:
        logger.error("Meldungen-Aufräumen fehlgeschlagen: %s", e)

    # Schritt 3: Kategorisierung
    logger.info("--- Schritt 3: Kategorisierung ---")
    from pipeline import categorizer
    # 300 pro Lauf: bei 60 Tagen Vorschau und Lauf alle 3 Tage kommen deutlich mehr neue Events
    anzahl_kategorisiert = categorizer.kategorisieren(limit=300)
    logger.info("Kategorisierung: %d Events verarbeitet", anzahl_kategorisiert)
    report.kennzahl(kategorisiert=anzahl_kategorisiert)

    # Schritt 3a: Unterkategorien (Feinfilter, z.B. Musik → Klassik/Jazz/DJ) per KI, gebündelt je 25 Events
    logger.info("--- Schritt 3a: Unterkategorien ---")
    try:
        from pipeline.unterkategorien import nachtragen
        nachtragen(limit=600)
    except Exception as e:
        logger.error("Unterkategorien fehlgeschlagen: %s", e)

    # Schritt 3b: Beschreibungen für Rausgegangen-Events aus Veranstalter-Quellen (umgeschrieben)
    logger.info("--- Schritt 3b: Beschreibungen aus Veranstalter-Quellen ---")
    try:
        from pipeline.beschreibung_quellen import beschreibungen_nachziehen
        # Nur ins Log – Kennzahlen sind Spalten in scraper_laeufe, eine neue bräuchte erst eine DB-Spalte
        beschreibungen_nachziehen(limit=40)
    except Exception as e:
        logger.error("Beschreibungen aus Veranstalter-Quellen fehlgeschlagen: %s", e)

    # Schritt 3c: Club-Scores aus dem aktuellen Eventkalender neu berechnen (ohne KI, kostenlos) –
    # Programm-Wert und die Schreibweisen der Orte für „Nächste Events hier“ bleiben so aktuell
    logger.info("--- Schritt 3c: Club-Scores ---")
    try:
        from scraper.orte.clubs_profil import scores_neu
        scores_neu(dry_run=False, ausgabe=False)
    except Exception as e:
        logger.error("Club-Scores fehlgeschlagen: %s", e)

    # Schritt 3d: Neue Event-URLs per IndexNow an Bing melden (ChatGPT-Suche/Copilot nutzen den Bing-Index)
    logger.info("--- Schritt 3d: IndexNow ---")
    try:
        from pipeline.indexnow import nach_lauf_melden
        nach_lauf_melden(lauf_start)
    except Exception as e:
        logger.error("IndexNow fehlgeschlagen: %s", e)

    # Schritt 4: Caption-Generierung
    logger.info("--- Schritt 4: Caption-Generierung ---")
    from pipeline import caption_generator
    anzahl_captions = caption_generator.captions_generieren(limit=50)
    logger.info("Captions generiert: %d Events aufbereitet", anzahl_captions)
    report.kennzahl(captions=anzahl_captions)

    # Schritt 5: Instagram-Posting
    logger.info("--- Schritt 5: Instagram-Posting ---")
    from pipeline import publisher
    anzahl_gepostet = publisher.posten(limit=5)
    logger.info("Instagram: %d Events gepostet", anzahl_gepostet)
    report.kennzahl(gepostet=anzahl_gepostet)


def scheduler_starten():
    """Startet den APScheduler für tägliche Ausführung."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()
    stunde, minute = SCHEDULER_UHRZEIT.split(":")
    scheduler.add_job(
        pipeline_ausfuehren,
        trigger="cron",
        hour=int(stunde),
        minute=int(minute),
        id="tägliche_pipeline",
    )
    scheduler.start()
    logger.info("Scheduler gestartet – Pipeline läuft täglich um %s Uhr", SCHEDULER_UHRZEIT)
    return scheduler


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DiesDasDüsseldorf Pipeline")
    parser.add_argument(
        "--jetzt",
        action="store_true",
        help="Pipeline sofort einmalig ausführen (ohne Scheduler)",
    )
    args = parser.parse_args()

    if args.jetzt:
        logger.info("Einmaliger Lauf gestartet (--jetzt Flag gesetzt)")
        asyncio.run(pipeline_ausfuehren())
    else:
        scheduler = scheduler_starten()
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Pipeline-Scheduler beendet.")
            scheduler.shutdown()
