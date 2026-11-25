"""
main.py – DiesDasDüsseldorf
Einstiegspunkt: Startet die tägliche Event-Pipeline
"""
import asyncio
import logging
import sys
from datetime import date

from config import LOG_LEVEL, LOG_DIR, SCHEDULER_UHRZEIT
from database.client import events_speichern, get_supabase_client
from pipeline.lauf_report import LaufReport
from scraper.tier1 import (
    rausgegangen,
    ticketmaster,
    stagedates,
    kulturportal,
    visitduesseldorf,
    visitduesseldorf_fuehrungen,
    meetup,
    resident_advisor,
    prinz,
    # songkick deaktiviert – API nur noch gegen Lizenz, Nutzungsbedingungen verbieten Scraping (Plan Quellen-Ausbau 5.1)
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
    # Welle A (Plan Quellen-Ausbau 3.2, Schritt V1)
    theater_an_der_koe,
    theater_luegallee,
    kabarett_flin,
    savoy_theater,
    apollo_variete,
    theatermuseum,
    gerhart_hauptmann_haus,
    goethe_museum,
    schloss_benrath,
    kit,
    comedy_club,
    bilker_bunker,
    tor3,
    nachtresidenz,
    ampere,
    weltkunstzimmer,
    insel_hombroich,
    stadt_ratingen,
    tas_neuss,
    # Welle B (Plan Quellen-Ausbau 3.2, Schritt V2)
    rsh_hochschule,
    haus_der_universitaet,
    philara,
    aquazoo,
    hetjens,
    filmwerkstatt,
    ratinger_hof,
    boston_club,
    craft_studio,
    oberschlesisches_landesmuseum,
    rheinisches_landestheater,
    globe_neuss,
    lvr_cromford,
    # Welle C (Plan Quellen-Ausbau, 25.11.2026)
    buergerhaeuser,
    comedy_fuer_freunde,
    heine_haus,
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
    kasematten,
    auf_ins_viertel,
    kleine_weihnachtsmaerkte,
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

# Bis zu diesem Tag kategorisiert der Lauf 1.500 statt 300 Events (Plan Quellen-Ausbau 5.3, Q13: zwei Wochen nach Z1)
KATEGORIEN_RUECKSTAND_BIS = date(2026, 12, 9)

# Alle Quellen in Ausführungsreihenfolge: (Anzeigename, Tier, scrape-Funktion).
# Der Anzeigename erscheint so im Log und im Scraper-Report des Dashboards –
# bei Umbenennung reißt dort der Verlauf der Quelle ab.
QUELLEN = [
    # Tier 1: Aggregatoren und APIs
    ("Ticketmaster", 1, ticketmaster.scrape),
    ("Stagedates", 1, stagedates.scrape),  # Ticketplattform, Sitemap + JSON-LD, Rang 2
    ("Kulturportal Düsseldorf", 1, kulturportal.scrape),
    ("VisitDüsseldorf", 1, visitduesseldorf.scrape),
    ("VisitDüsseldorf Führungen", 1, visitduesseldorf_fuehrungen.scrape),  # Stadtführungen aus den Event-Seiten
    ("Meetup.com", 1, meetup.scrape),
    ("Resident Advisor", 1, resident_advisor.scrape),
    ("PRINZ.de Düsseldorf", 1, prinz.scrape),
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
    # Welle A der Venues (Plan Quellen-Ausbau 3.2, Schritt V1) – je Haus eine Zeile, damit der Lauf-Report jedes Haus einzeln führt
    ("Theater an der Kö", 2, theater_an_der_koe.scrape),
    ("Theater an der Luegallee", 2, theater_luegallee.scrape),
    ("KaBARett FLiN", 2, kabarett_flin.scrape),
    ("Savoy Theater", 2, savoy_theater.scrape),
    ("Roncalli's Apollo Varieté", 2, apollo_variete.scrape),
    ("Theatermuseum Düsseldorf", 2, theatermuseum.scrape),
    ("Gerhart Hauptmann Haus", 2, gerhart_hauptmann_haus.scrape),
    ("Goethe-Museum", 2, goethe_museum.scrape),
    ("Schloss Benrath", 2, schloss_benrath.scrape),
    ("KIT – Kunst im Tunnel", 2, kit.scrape),
    ("Comedy Club Düsseldorf", 2, comedy_club.scrape),
    ("Bilker Bunker", 2, bilker_bunker.scrape),
    ("Tor 3", 2, tor3.scrape),
    ("Nachtresidenz", 2, nachtresidenz.scrape),
    ("Ampere", 2, ampere.scrape),
    ("Weltkunstzimmer", 2, weltkunstzimmer.scrape),
    ("Insel Hombroich", 2, insel_hombroich.scrape),
    ("Stadt Ratingen Veranstaltungskalender", 2, stadt_ratingen.scrape),
    ("Theater am Schlachthof Neuss", 2, tas_neuss.scrape),
    # Welle B (Plan Quellen-Ausbau 3.2, Schritt V2)
    ("Robert Schumann Hochschule", 2, rsh_hochschule.scrape),
    ("Haus der Universität", 2, haus_der_universitaet.scrape),
    ("Sammlung Philara", 2, philara.scrape),
    ("Aquazoo Löbbecke Museum", 2, aquazoo.scrape),
    ("Hetjens-Museum", 2, hetjens.scrape),
    ("Filmwerkstatt Düsseldorf", 2, filmwerkstatt.scrape),
    ("Ratinger Hof", 2, ratinger_hof.scrape),
    ("Boston Club", 2, boston_club.scrape),
    ("The Craft Studio", 2, craft_studio.scrape),
    ("Oberschlesisches Landesmuseum", 2, oberschlesisches_landesmuseum.scrape),
    ("Rheinisches Landestheater Neuss", 2, rheinisches_landestheater.scrape),
    ("Globe Neuss", 2, globe_neuss.scrape),
    ("LVR-Industriemuseum Cromford", 2, lvr_cromford.scrape),
    # Welle C (Plan Quellen-Ausbau, 25.11.2026)
    ("Bürgerhäuser Düsseldorf", 2, buergerhaeuser.scrape),
    ("Comedy für Freunde", 2, comedy_fuer_freunde.scrape),
    ("Heine Haus Literaturhaus", 2, heine_haus.scrape),
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
    ("Kasematten Düsseldorf", 3, kasematten.scrape),  # 5 Locations an der Rheinuferpromenade, nur datierte Events
    ("Auf ins Viertel", 3, auf_ins_viertel.scrape),  # kulinarische Stadtführungen (bookingkit)
    ("Kleine Weihnachtsmärkte", 3, kleine_weihnachtsmaerkte.scrape),  # feste Einträge aus data/weihnachtsmaerkte/kleine_maerkte.csv
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
    # Quellen an/aus aus dem Admin-Bereich (pipeline/quellen.py); ohne lesbare Tabelle laufen alle
    from pipeline.quellen import quellen_abgeschaltet
    abgeschaltet = quellen_abgeschaltet()
    for name, tier, funktion in QUELLEN:
        if tier != aktueller_tier:
            aktueller_tier = tier
            logger.info("--- Tier-%d-Scraper ---", tier)
        if name in abgeschaltet:
            logger.info("%s: im Admin-Bereich abgeschaltet – übersprungen", name)
            report.quelle_abgeschaltet(name, tier, abgeschaltet[name])
            continue
        alle_events.extend(await report.scraper_ausfuehren(name, tier, funktion))

    logger.info("Scraper gesamt: %d Events gesammelt", len(alle_events))
    report.kennzahl(events_gesammelt=len(alle_events))

    # Schritt 1c: Nur Düsseldorf, Neuss, Ratingen (Plan Locations E3, 18.11.2026 – z. B. PRINZ.de liefert die
    # ganze Region, die Oper auch Vorstellungen im Theater Duisburg)
    logger.info("--- Schritt 1c: Gebietsfilter ---")
    from pipeline.gebiet import gebiet_filtern
    alle_events = gebiet_filtern(alle_events)

    # Schritt 1d: Ortszuordnung events.ort_id (Plan Locations 3.4) – vor der Deduplizierung, damit die Dubletten-
    # Regel nach Häusern greift. Ohne Index (Fehler) läuft alles wie bisher über den Namen.
    logger.info("--- Schritt 1d: Ortszuordnung ---")
    orte_index = None
    try:
        from pipeline.ort_zuordnung import index_laden, zuordnen_alle
        orte_index = index_laden(get_supabase_client())
        zuordnung = zuordnen_alle(alle_events, orte_index)
        report.kennzahl(ort_treffer=zuordnung["treffer"], ort_mehrdeutig_neu=zuordnung["mehrdeutig"])
    except Exception as e:
        logger.error("Ortszuordnung fehlgeschlagen (weiter ohne ort_id): %s", e)

    # Schritt 1e: In-Memory-Deduplizierung mit Merge-Logik
    logger.info("--- Schritt 1e: In-Memory-Deduplizierung ---")
    from pipeline.deduplication import deduplizieren
    alle_events = deduplizieren(alle_events)
    report.kennzahl(events_nach_dedup=len(alle_events))

    # Schritt 1e2: Adressen für Rausgegangen-Events aus eigenen Daten (ort_id aus 1d, Orte-Tabelle, andere
    # Quellen) – Rausgegangen-Detailseiten sind per robots.txt gesperrt; vor der Stadtteil-Zuordnung, die PLZ nutzt
    logger.info("--- Schritt 1e2: Adressen ergänzen ---")
    from pipeline.adressen_ergaenzen import adressen_schritt
    alle_events = adressen_schritt(alle_events)

    # Schritt 1f: Stadtteil-Zuordnung
    logger.info("--- Schritt 1f: Stadtteil-Zuordnung ---")
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

    # Abdeckung der Quellen (Plan docs/plan-quellen-ausbau-2026-11-23.md, 4.3/4.5): Lücken je Ort für Warnregel W7,
    # künftige Events und wie viele davon nur Rausgegangen kennt – Spalten aus database/quellen_spalte_2026-11-24.sql
    try:
        from pipeline.quellen_kennzahlen import bestand_zaehlen, luecken_berechnen, ticket_links_zaehlen
        luecken = luecken_berechnen(alle_events)
        kuenftig, nur_rg = bestand_zaehlen(get_supabase_client())
        report.kennzahl(luecken=luecken)
        if kuenftig is not None:
            report.kennzahl(kuenftige_events=kuenftig, nur_rausgegangen=nur_rg)
        logger.info("Quellen: %s künftige Events, davon nur Rausgegangen: %s; Lücken an %d Orten",
                    kuenftig, nur_rg, len(luecken))
        # Ticket-Links des Hauses (Schritt P1): Anteil je Anbieter – Grundlage für die Partner-Links (P2)
        mit_link, je_anbieter = ticket_links_zaehlen(alle_events)
        logger.info("Ticket-Links: %d von %d Events (%.0f %%) – %s", mit_link, len(alle_events),
                    100 * mit_link / max(1, len(alle_events)),
                    ", ".join(f"{name} {n}" for name, n in je_anbieter.most_common()) or "keine")
    except Exception as e:
        logger.error("Quellen-Kennzahlen fehlgeschlagen: %s", e)

    # Ortszuordnung über den ganzen Bestand prüfen (Plan Locations 3.4): gespeicherte ort_id ohne Treffer oder
    # mehrdeutig – nur Meldung, nichts wird geändert. Eine Zahl über 0 heißt: Lösung vergessen bzw. doppelte Schreibweise.
    if orte_index is not None:
        try:
            from pipeline.ort_zuordnung import bestand_pruefen
            pruefung = bestand_pruefen(get_supabase_client(), orte_index)
            report.kennzahl(ort_id_ohne_treffer=pruefung["ort_id_ohne_treffer"],
                            ort_id_mehrdeutig=pruefung["ort_id_mehrdeutig"])
        except Exception as e:
            logger.error("Prüfung der Ortszuordnung fehlgeschlagen: %s", e)

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

    # Schritt 2c: Löschfristen der Nutzerkonten (unbestätigt, ohne Alter, unter 16; Plan Nutzerkonten 9.3)
    logger.info("--- Schritt 2c: Nutzerkonten aufräumen ---")
    try:
        from pipeline.konten_aufraeumen import konten_aufraeumen
        konten_aufraeumen()
    except Exception as e:
        logger.error("Konten-Aufräumen fehlgeschlagen: %s", e)

    # Schritt 3: Kategorisierung
    logger.info("--- Schritt 3: Kategorisierung ---")
    from pipeline import categorizer
    # 300 pro Lauf: bei 60 Tagen Vorschau und Lauf alle 3 Tage kommen deutlich mehr neue Events. Nach der Umstellung auf
    # bis zu 365 Tage je Quelle (Plan Quellen-Ausbau 5.3, Q13) zwei Wochen lang 1.500, um den Rückstand abzubauen.
    limit_kategorien = 1500 if date.today() <= KATEGORIEN_RUECKSTAND_BIS else 300
    anzahl_kategorisiert = categorizer.kategorisieren(limit=limit_kategorien)
    logger.info("Kategorisierung: %d Events verarbeitet", anzahl_kategorisiert)
    report.kennzahl(kategorisiert=anzahl_kategorisiert)

    # Schritt 3a: Unterkategorien (Feinfilter, z.B. Musik → Klassik/Jazz/DJ) per KI, gebündelt je 25 Events
    logger.info("--- Schritt 3a: Unterkategorien ---")
    try:
        from pipeline.unterkategorien import nachtragen, vereinheitlichen
        nachtragen(limit=600)
        # Gleiche Titel einer Kategorie auf dieselbe Unterkategorie bringen (die KI arbeitet in Bündeln)
        vereinheitlichen()
    except Exception as e:
        logger.error("Unterkategorien fehlgeschlagen: %s", e)

    # Schritt 3b: Beschreibungen für Rausgegangen-Events aus Veranstalter-Quellen (umgeschrieben)
    logger.info("--- Schritt 3b: Beschreibungen aus Veranstalter-Quellen ---")
    try:
        from pipeline.beschreibung_quellen import beschreibungen_nachziehen, veranstalter_nachziehen
        # Nur ins Log – Kennzahlen sind Spalten in scraper_laeufe, eine neue bräuchte erst eine DB-Spalte
        # Alle offenen Termine je Lauf (Auftraggeber 20.11.2026: „Beschreibungen sollen immer mitgenommen werden“);
        # vorher 40 Rausgegangen-Events und 10 Minuten für Veranstalter – der Rückstand wuchs. Die Grenzen hier sind
        # nur Schutz gegen Hänger, das Zeitlimit des Workflows (.github/workflows/scrape.yml) ist darauf abgestimmt.
        # Zeitbudgets (Cursor-Prüfung 24.11.2026, Welle B 25.11.): Scraper rund 65 Minuten (Probelauf 24.11.: 42 Minuten
        # ohne Rausgegangen, Welle B 12 Minuten, Rausgegangen ~10), KI-Schritte und Speichern rund 30 Minuten, dazu
        # 40 + 60 Minuten Beschreibungen → unter 200 der 240 Minuten des Workflows. Was liegen bleibt, kommt im nächsten
        # Lauf dran.
        beschreibungen_nachziehen(limit=1000, max_sekunden=2400)
        # Veranstalter-Events: Text aus der eigenen Event-Seite, ein Text pro Stück
        veranstalter_nachziehen(max_stuecke=2000, max_sekunden=3600)
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

    # Schritt 3e: Dubletten und Events außerhalb des Gebiets als Vorschläge für den Admin-Bereich
    # (Plan docs/plan-admin-dashboard-2026-11-23.md, 3.5) – ändert selbst nichts, wirft nicht
    logger.info("--- Schritt 3e: Vorschläge für den Admin-Bereich ---")
    try:
        from pipeline.vorschlaege import vorschlaege_erzeugen
        vorschlaege_erzeugen(report.lauf_id)
    except Exception as e:
        logger.error("Vorschläge fehlgeschlagen: %s", e)

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
