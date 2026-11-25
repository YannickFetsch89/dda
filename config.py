"""
config.py – DiesDasDüsseldorf
Zentrale Konfiguration. Keine Secrets hier – alle sensiblen Werte kommen aus .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# --- Claude API ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-6"

# --- Instagram ---
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")

# --- Google Places API ---
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
DUESSELDORF_LAT = 51.2277
DUESSELDORF_LNG = 6.7735
GOOGLE_PLACES_RADIUS = 10000  # 10 km
GOOGLE_PLACES_MIN_RATING = 4.0
GOOGLE_PLACES_MIN_BEWERTUNGEN = 30

# --- Scraper-Konfiguration ---
SCRAPER_CONFIG = {
    "rausgegangen": {
        "url": "https://rausgegangen.de/duesseldorf",
        "methode": "playwright",
        "intervall": "täglich",
        "timeout": 30,
    },
    "visitduesseldorf": {
        "url": "https://www.visitduesseldorf.de/erleben/veranstaltungen",
        "methode": "playwright",
        "intervall": "täglich",
        "timeout": 30,
    },
    "kulturportal": {
        "url": "https://kulturportal-duesseldorf.de",
        "methode": "playwright",
        "intervall": "täglich",
        "timeout": 60,  # Städtisches Portal, oft langsam
    },
}

# --- API-Konfiguration ---
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
MEETUP_API_KEY = os.getenv("MEETUP_API_KEY")
SONGKICK_API_KEY = os.getenv("SONGKICK_API_KEY")

# --- Instagram Caption ---
INSTAGRAM_CONFIG = {
    "max_caption_laenge": 2200,
    "min_hashtags": 5,
    "posting_uhrzeit": "08:00",
}

# --- Kategorien ---
KATEGORIEN = [
    "kultur",
    "musik",
    "food",
    "sport",
    "outdoor",
    "stadtfuehrung",
    "community",
    "nightlife",
    "family",
    "dating",
    "sonstiges",
]

# --- Scraping-Regeln ---
RATE_LIMIT_SEKUNDEN = 2  # Mindestwartezeit zwischen Requests
MAX_RETRIES = 3
BACKOFF_FAKTOR = 2  # Exponentielles Backoff
SCRAPER_VORSCHAU_TAGE = 60  # Fallback: Aggregatoren und Rausgegangen. Name bleibt für Altcode.

# Zeitraum je Quelle (Plan docs/plan-quellen-ausbau-2026-11-23.md, 5.2, Q7, Schritt Z1). Schlüssel sind die
# Anzeigenamen aus main.py QUELLEN UND jede abweichende QUELLE_NAME eines Moduls (beide mit demselben Fenster); ein
# Test prüft, dass jeder Name hier steht. Die Scraper rufen vorschau_ende(QUELLE_NAME, heute).
VORSCHAU_LANG = 365     # große Häuser, Sport, Messe, Ticketverkauf
VORSCHAU_MITTEL = 120   # übrige Häuser (Tier 2/3) und VisitDüsseldorf
VORSCHAU_KURZ = SCRAPER_VORSCHAU_TAGE  # Aggregatoren, Portale, Rausgegangen
VORSCHAU_TAGE: dict[str, int] = {
    # 365
    **{name: VORSCHAU_LANG for name in (
        "Ticketmaster", "Eventim", "Reservix", "ADticket", "Stagedates",
        "d-live", "Mitsubishi Electric HALLE", "Capitol Theater Düsseldorf", "Tonhalle Düsseldorf",
        "Deutsche Oper am Rhein", "Düsseldorfer Schauspielhaus", "Kom(m)ödchen Düsseldorf",
        "Messe Düsseldorf", "Fortuna Düsseldorf", "DEG Eishockey Düsseldorf", "Kunstsammlung NRW (K20/K21)",
        # Welle A (V1)
        "Theater an der Kö", "Theater an der Luegallee", "KaBARett FLiN", "Savoy Theater", "Roncalli's Apollo Varieté", "Schloss Benrath", "Theater am Schlachthof Neuss",
        # Welle B (V2)
        "Rheinisches Landestheater Neuss", "Globe Neuss",
    )},
    # 120
    **{name: VORSCHAU_MITTEL for name in (
        "VisitDüsseldorf", "VisitDüsseldorf Führungen",
        "zakk", "Kunstpalast Düsseldorf", "NRW-Forum Düsseldorf", "FFT Düsseldorf", "Stahlwerk Düsseldorf",
        "Rudas Studios Düsseldorf", "Kulturschlachthof R25", "Salon des Amateurs", "Pitcher Rock HQ",
        "Kunsthalle Düsseldorf", "Filmmuseum Düsseldorf", "Stadtbüchereien Düsseldorf", "Tanzhaus NRW",
        "Jazz-Schmiede Düsseldorf", "STARTPLATZ Düsseldorf",
        "Parkrun Volksgarten Düsseldorf", "Sport im Park Düsseldorf", "EKŌ-Haus der Japanischen Kultur",
        "Classic Remise Düsseldorf", "Classic Remise", "Stadtstrand Düsseldorf", "IHK Düsseldorf",
        "StartupDorf Meetup", "Street Food Thursday", "Street Food Thursday Düsseldorf", "Kasematten Düsseldorf",
        "Auf ins Viertel", "Kleine Weihnachtsmärkte", "Kleine Weihnachtsmärkte (Redaktion)", "Spontacts Düsseldorf",
        # Welle A (V1)
        "Theatermuseum Düsseldorf", "Gerhart Hauptmann Haus", "Goethe-Museum", "KIT – Kunst im Tunnel", "Comedy Club Düsseldorf", "Bilker Bunker", "Tor 3", "Nachtresidenz", "Ampere", "Weltkunstzimmer", "Insel Hombroich", "Stadt Ratingen Veranstaltungskalender",
        # Welle B (V2)
        "Robert Schumann Hochschule", "Haus der Universität", "Sammlung Philara", "Aquazoo Löbbecke Museum", "Hetjens-Museum", "Filmwerkstatt Düsseldorf", "Ratinger Hof", "Boston Club", "The Craft Studio", "Oberschlesisches Landesmuseum", "LVR-Industriemuseum Cromford",
        # Welle C
        "Bürgerhäuser Düsseldorf", "Comedy für Freunde", "Heine Haus Literaturhaus",
    )},
    # 60
    **{name: VORSCHAU_KURZ for name in (
        "Kulturportal Düsseldorf", "Meetup.com", "Resident Advisor", "PRINZ.de Düsseldorf", "Songkick",
        "AllEvents.in Düsseldorf", "Rausgegangen", "Eventbrite", "eventfinder.de", "Bandsintown", "meinestadt.de",
    )},
}


def vorschau_tage(quelle: str, tier: int | None = None) -> int:
    """
    Wie viele Tage voraus eine Quelle Events sammelt: Tabelle VORSCHAU_TAGE, sonst 120 für Tier 2/3 und 60 für Tier 1.
    Notaus (Plan 7, Rückweg): Umgebungsvariable VORSCHAU_NOTAUS=1 begrenzt jede Quelle auf 60 Tage.
    """
    tage = VORSCHAU_TAGE.get(quelle) or (VORSCHAU_MITTEL if tier in (2, 3) else VORSCHAU_KURZ)
    if os.getenv("VORSCHAU_NOTAUS", "").strip() == "1":
        tage = min(tage, SCRAPER_VORSCHAU_TAGE)
    return tage


def vorschau_ende(quelle: str, heute, tier: int | None = None):
    """Letzter Tag, bis zu dem eine Quelle Events übernimmt (heute + vorschau_tage); heute ist date oder datetime."""
    from datetime import timedelta
    return heute + timedelta(days=vorschau_tage(quelle, tier))

# --- Scheduler ---
SCHEDULER_UHRZEIT = "06:00"  # Täglicher Start der Pipeline

# --- Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = "logs"
