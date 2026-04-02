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
from scraper.tier1 import (
    rausgegangen,
    ticketmaster,
    kulturportal,
    visitduesseldorf,
    meetup,
    resident_advisor,
    prinz,
    songkick,
    allevents,
    bandsintown,
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
    spontacts,
    ihk,
    startupdorf,
    street_food_thursday,
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


async def pipeline_ausfuehren():
    """
    Führt die vollständige tägliche Pipeline aus:
    1. Scraper starten (Tier 1, 2, 3)
    2. Duplikate entfernen
    3. Events kategorisieren
    4. Instagram Captions generieren
    5. Posts veröffentlichen
    """
    logger.info("=== DiesDasDüsseldorf Pipeline gestartet ===")
    heute = date.today()
    logger.info("Datum: %s", heute.isoformat())

    # Schritt 1: Scraper ausführen
    logger.info("--- Schritt 1: Scraper ---")
    alle_events = []

    events_rausgegangen = rausgegangen.scrape()
    logger.info("Rausgegangen: %d Events", len(events_rausgegangen))
    alle_events.extend(events_rausgegangen)

    events_ticketmaster = ticketmaster.scrape()
    logger.info("Ticketmaster: %d Events", len(events_ticketmaster))
    alle_events.extend(events_ticketmaster)

    events_kulturportal = kulturportal.scrape()
    logger.info("Kulturportal Düsseldorf: %d Events", len(events_kulturportal))
    alle_events.extend(events_kulturportal)

    events_visitduesseldorf = visitduesseldorf.scrape()
    logger.info("VisitDüsseldorf: %d Events", len(events_visitduesseldorf))
    alle_events.extend(events_visitduesseldorf)

    events_meetup = meetup.scrape()
    logger.info("Meetup.com: %d Events", len(events_meetup))
    alle_events.extend(events_meetup)

    events_ra = resident_advisor.scrape()
    logger.info("Resident Advisor: %d Events", len(events_ra))
    alle_events.extend(events_ra)

    events_prinz = prinz.scrape()
    logger.info("PRINZ.de Düsseldorf: %d Events", len(events_prinz))
    alle_events.extend(events_prinz)

    events_songkick = songkick.scrape()
    logger.info("Songkick: %d Events", len(events_songkick))
    alle_events.extend(events_songkick)

    events_allevents = allevents.scrape()
    logger.info("AllEvents.in Düsseldorf: %d Events", len(events_allevents))
    alle_events.extend(events_allevents)

    events_bandsintown = bandsintown.scrape()
    logger.info("Bandsintown: %d Events", len(events_bandsintown))
    alle_events.extend(events_bandsintown)

    # meinestadt.scrape() wurde entfernt – Quelle dauerhaft durch Akamai WAF blockiert (HTTP 403)

    # Tier 2: Venue-eigene Scraper
    logger.info("--- Schritt 1b: Tier-2-Scraper ---")

    events_tonhalle = tonhalle.scrape()
    logger.info("Tonhalle Düsseldorf: %d Events", len(events_tonhalle))
    alle_events.extend(events_tonhalle)

    events_zakk = zakk.scrape()
    logger.info("zakk: %d Events", len(events_zakk))
    alle_events.extend(events_zakk)

    events_oper = oper_am_rhein.scrape()
    logger.info("Deutsche Oper am Rhein: %d Events", len(events_oper))
    alle_events.extend(events_oper)

    events_schauspielhaus = schauspielhaus.scrape()
    logger.info("Düsseldorfer Schauspielhaus: %d Events", len(events_schauspielhaus))
    alle_events.extend(events_schauspielhaus)

    events_dlive = dlive.scrape()
    logger.info("d-live: %d Events", len(events_dlive))
    alle_events.extend(events_dlive)

    events_kunstpalast = kunstpalast.scrape()
    logger.info("Kunstpalast Düsseldorf: %d Events", len(events_kunstpalast))
    alle_events.extend(events_kunstpalast)

    events_kunstsammlung = kunstsammlung.scrape()
    logger.info("Kunstsammlung NRW (K20/K21): %d Events", len(events_kunstsammlung))
    alle_events.extend(events_kunstsammlung)

    events_nrw_forum = nrw_forum.scrape()
    logger.info("NRW-Forum Düsseldorf: %d Events", len(events_nrw_forum))
    alle_events.extend(events_nrw_forum)

    events_fft = fft_duesseldorf.scrape()
    logger.info("FFT Düsseldorf: %d Events", len(events_fft))
    alle_events.extend(events_fft)

    events_stahlwerk = stahlwerk.scrape()
    logger.info("Stahlwerk Düsseldorf: %d Events", len(events_stahlwerk))
    alle_events.extend(events_stahlwerk)

    events_rudas = rudas_studios.scrape()
    logger.info("Rudas Studios Düsseldorf: %d Events", len(events_rudas))
    alle_events.extend(events_rudas)

    events_meh = mitsubishi_halle.scrape()
    logger.info("Mitsubishi Electric HALLE: %d Events", len(events_meh))
    alle_events.extend(events_meh)

    events_r25 = kulturschlachthof_r25.scrape()
    logger.info("Kulturschlachthof R25: %d Events", len(events_r25))
    alle_events.extend(events_r25)

    events_salon = salon_des_amateurs.scrape()
    logger.info("Salon des Amateurs: %d Events", len(events_salon))
    alle_events.extend(events_salon)

    events_pitcher = pitcher.scrape()
    logger.info("Pitcher Rock HQ: %d Events", len(events_pitcher))
    alle_events.extend(events_pitcher)

    events_kunsthalle = kunsthalle.scrape()
    logger.info("Kunsthalle Düsseldorf: %d Events", len(events_kunsthalle))
    alle_events.extend(events_kunsthalle)

    events_filmmuseum = filmmuseum.scrape()
    logger.info("Filmmuseum Düsseldorf: %d Events", len(events_filmmuseum))
    alle_events.extend(events_filmmuseum)

    events_stadtbuechereien = stadtbuechereien.scrape()
    logger.info("Stadtbüchereien Düsseldorf: %d Events", len(events_stadtbuechereien))
    alle_events.extend(events_stadtbuechereien)

    events_tanzhaus = tanzhaus_nrw.scrape()
    logger.info("Tanzhaus NRW: %d Events", len(events_tanzhaus))
    alle_events.extend(events_tanzhaus)

    events_jazz = jazz_schmiede.scrape()
    logger.info("Jazz-Schmiede Düsseldorf: %d Events", len(events_jazz))
    alle_events.extend(events_jazz)

    events_capitol = capitol_theater.scrape()
    logger.info("Capitol Theater Düsseldorf: %d Events", len(events_capitol))
    alle_events.extend(events_capitol)

    events_komm = kommoedchen.scrape()
    logger.info("Kom(m)ödchen Düsseldorf: %d Events", len(events_komm))
    alle_events.extend(events_komm)

    events_startplatz = startplatz.scrape()
    logger.info("STARTPLATZ Düsseldorf: %d Events", len(events_startplatz))
    alle_events.extend(events_startplatz)

    # Tier 3: Nischen- und Spezialquellen
    logger.info("--- Schritt 1c: Tier-3-Scraper ---")

    events_parkrun = parkrun.scrape()
    logger.info("Parkrun Volksgarten Düsseldorf: %d Events", len(events_parkrun))
    alle_events.extend(events_parkrun)

    events_sport_im_park = await sport_im_park.scrape()
    logger.info("Sport im Park Düsseldorf: %d Events", len(events_sport_im_park))
    alle_events.extend(events_sport_im_park)

    events_fortuna = await fortuna.scrape()
    logger.info("Fortuna Düsseldorf: %d Events", len(events_fortuna))
    alle_events.extend(events_fortuna)

    events_deg = await deg.scrape()
    logger.info("DEG Eishockey Düsseldorf: %d Events", len(events_deg))
    alle_events.extend(events_deg)

    events_messe = await messe.scrape()
    logger.info("Messe Düsseldorf: %d Events", len(events_messe))
    alle_events.extend(events_messe)

    events_japan_center = await japan_center.scrape()
    logger.info("Japan Center Düsseldorf: %d Events", len(events_japan_center))
    alle_events.extend(events_japan_center)

    events_classic_remise = await classic_remise.scrape()
    logger.info("Classic Remise Düsseldorf: %d Events", len(events_classic_remise))
    alle_events.extend(events_classic_remise)

    events_stadtstrand = await stadtstrand.scrape()
    logger.info("Stadtstrand Düsseldorf: %d Events", len(events_stadtstrand))
    alle_events.extend(events_stadtstrand)

    events_spontacts = await spontacts.scrape()
    logger.info("Spontacts Düsseldorf: %d Events", len(events_spontacts))
    alle_events.extend(events_spontacts)

    events_ihk = await ihk.scrape()
    logger.info("IHK Düsseldorf: %d Events", len(events_ihk))
    alle_events.extend(events_ihk)

    events_startupdorf = await startupdorf.scrape()
    logger.info("StartupDorf Meetup: %d Events", len(events_startupdorf))
    alle_events.extend(events_startupdorf)

    events_sft = street_food_thursday.scrape()
    logger.info("Street Food Thursday: %d Events", len(events_sft))
    alle_events.extend(events_sft)

    logger.info("Scraper gesamt: %d Events gesammelt", len(alle_events))

    # Schritt 1d: In-Memory-Deduplizierung mit Merge-Logik
    logger.info("--- Schritt 1d: In-Memory-Deduplizierung ---")
    from pipeline.deduplication import deduplizieren
    alle_events = deduplizieren(alle_events)

    # Schritt 2: In Supabase speichern (mit DB-seitiger Anreicherung)
    logger.info("--- Schritt 2: Datenbank ---")
    stats = events_speichern(alle_events)
    logger.info(
        "Ergebnis – Neu gespeichert: %d | Duplikate: %d | Angereichert: %d | Fehler: %d",
        stats["gespeichert"], stats["duplikate"], stats.get("angereichert", 0), stats["fehler"]
    )

    # Schritt 3: Kategorisierung
    logger.info("--- Schritt 3: Kategorisierung ---")
    from pipeline import categorizer
    anzahl_kategorisiert = categorizer.kategorisieren(limit=100)
    logger.info("Kategorisierung: %d Events verarbeitet", anzahl_kategorisiert)

    # Schritt 4: Caption-Generierung
    logger.info("--- Schritt 4: Caption-Generierung ---")
    from pipeline import caption_generator
    anzahl_captions = caption_generator.captions_generieren(limit=50)
    logger.info("Captions generiert: %d Events aufbereitet", anzahl_captions)

    # Schritt 5: Instagram-Posting
    logger.info("--- Schritt 5: Instagram-Posting ---")
    from pipeline import publisher
    anzahl_gepostet = publisher.posten(limit=5)
    logger.info("Instagram: %d Events gepostet", anzahl_gepostet)

    logger.info("=== Pipeline abgeschlossen ===")


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
