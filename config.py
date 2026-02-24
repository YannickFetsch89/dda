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
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN")
MEETUP_API_KEY = os.getenv("MEETUP_API_KEY")

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
SCRAPER_VORSCHAU_TAGE = 14  # Wie viele Tage in die Zukunft Events gesammelt werden

# --- Scheduler ---
SCHEDULER_UHRZEIT = "06:00"  # Täglicher Start der Pipeline

# --- Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = "logs"
