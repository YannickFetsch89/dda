"""
google_places.py – DiesDasDüsseldorf
Recherchiert Restaurants und Cafés in Düsseldorf über die Google Places API (New).

Ablauf:
  1. Nearby Search: Findet Orte nach Typ im Stadtgebiet
  2. Place Details: Lädt Details, Bewertungen, Fotos pro Ort
  3. Foto-Download: Speichert das beste Foto lokal
  4. Speicherung: Schreibt alles in die Supabase-Tabelle `orte`

Nutzung:
  python -m scraper.orte.google_places [--typ restaurant|cafe] [--limit 50] [--dry-run]
"""
import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

# Projekt-Root zum Importpfad hinzufügen
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import (
    DUESSELDORF_LAT,
    DUESSELDORF_LNG,
    GOOGLE_PLACES_API_KEY,
    GOOGLE_PLACES_MIN_BEWERTUNGEN,
    GOOGLE_PLACES_MIN_RATING,
    GOOGLE_PLACES_RADIUS,
)
from database.client import get_supabase_client
from pipeline.stadtteil_mapper import stadtteil_ermitteln

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

API_BASE = "https://places.googleapis.com/v1"

# Mapping: Google primary_type → unser Typ
TYP_MAPPING = {
    "restaurant": "restaurant",
    "cafe": "cafe",
    "coffee_shop": "cafe",
    "bakery": "cafe",
    "bar": "kneipe",
    "night_club": "club",
}

# Suchbegriffe pro Typ
SUCH_TYPEN = {
    "restaurant": ["restaurant"],
    "cafe": ["cafe", "coffee_shop"],
}


def _headers(field_mask: str) -> dict:
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": field_mask,
    }


def _slug_erzeugen(name: str, stadtteil: str | None = None) -> str:
    """Erzeugt einen URL-freundlichen Slug aus dem Namen."""
    text = name.lower()
    # Umlaute ersetzen
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    # Nur Buchstaben, Zahlen, Bindestriche
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    # Doppelte Bindestriche entfernen
    text = re.sub(r"-+", "-", text)
    if stadtteil:
        st = stadtteil.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
        st = re.sub(r"[^a-z0-9]+", "-", st).strip("-")
        text = f"{text}-{st}"
    return text


def nearby_search(typ_keyword: str, page_token: str | None = None) -> dict:
    """Nearby Search (New) – findet Orte im Umkreis."""
    body = {
        "includedTypes": [typ_keyword],
        "locationRestriction": {
            "circle": {
                "center": {"latitude": DUESSELDORF_LAT, "longitude": DUESSELDORF_LNG},
                "radius": GOOGLE_PLACES_RADIUS,
            }
        },
        "maxResultCount": 20,
        "languageCode": "de",
        "regionCode": "DE",
    }
    if page_token:
        body["pageToken"] = page_token

    field_mask = "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.primaryType,places.types,places.priceLevel,places.googleMapsUri,places.websiteUri,places.nationalPhoneNumber,places.regularOpeningHours,places.photos"

    url = f"{API_BASE}/places:searchNearby"
    time.sleep(0.5)  # Rate Limiting

    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=body, headers=_headers(field_mask))
        resp.raise_for_status()
        return resp.json()


def place_details(place_id: str) -> dict:
    """Place Details (New) – lädt vollständige Infos zu einem Ort."""
    field_mask = "id,displayName,formattedAddress,location,rating,userRatingCount,primaryType,types,priceLevel,googleMapsUri,websiteUri,nationalPhoneNumber,regularOpeningHours,editorialSummary,reviews,photos"

    url = f"{API_BASE}/{place_id}"
    time.sleep(0.3)

    with httpx.Client(timeout=30) as client:
        resp = client.get(url, headers=_headers(field_mask))
        resp.raise_for_status()
        return resp.json()


def foto_url(foto_name: str, max_breite: int = 800) -> str:
    """Erzeugt eine Foto-URL aus dem Foto-Ressourcennamen."""
    return f"{API_BASE}/{foto_name}/media?maxWidthPx={max_breite}&key={GOOGLE_PLACES_API_KEY}"


def _preis_niveau(price_level: str | None) -> str | None:
    """Google priceLevel → unser PreisNiveau."""
    if not price_level:
        return None
    mapping = {
        "PRICE_LEVEL_INEXPENSIVE": "€",
        "PRICE_LEVEL_MODERATE": "€€",
        "PRICE_LEVEL_EXPENSIVE": "€€€",
        "PRICE_LEVEL_VERY_EXPENSIVE": "€€€",
    }
    return mapping.get(price_level)


def _oeffnungszeiten(hours: dict | None) -> str | None:
    """Formatiert Öffnungszeiten als lesbaren Text."""
    if not hours or "weekdayDescriptions" not in hours:
        return None
    return " | ".join(hours["weekdayDescriptions"])


def _unser_typ(place: dict, gewuenschter_typ: str) -> str:
    """Bestimmt unseren Typ basierend auf Google-Daten."""
    primary = place.get("primaryType", "")
    if primary in TYP_MAPPING:
        return TYP_MAPPING[primary]
    return gewuenschter_typ


def _adresse_bereinigen(adresse: str | None) -> str | None:
    """Entfernt 'Deutschland' am Ende der Adresse."""
    if not adresse:
        return None
    return re.sub(r",?\s*Deutschland\s*$", "", adresse).strip()


_AUSSCHLUSS_TYPEN = {
    "hotel", "motel", "lodging", "resort_hotel", "extended_stay_hotel",
    "shopping_mall", "department_store", "supermarket", "grocery_store",
    "gas_station", "hospital", "dentist", "doctor", "pharmacy",
    "car_dealer", "car_rental", "car_wash",
}


def ort_aus_place(place: dict, gewuenschter_typ: str) -> dict | None:
    """Konvertiert ein Google Place zu unserem Ort-Dict."""
    name = place.get("displayName", {}).get("text", "")
    if not name:
        return None

    # Hotels, Einkaufszentren etc. rausfiltern
    typen = set(place.get("types", []))
    if typen & _AUSSCHLUSS_TYPEN:
        return None

    rating = place.get("rating")
    bewertungen = place.get("userRatingCount", 0)

    # Filter: Mindest-Rating und Mindest-Bewertungen
    if rating is not None and rating < GOOGLE_PLACES_MIN_RATING:
        return None
    if bewertungen < GOOGLE_PLACES_MIN_BEWERTUNGEN:
        return None

    adresse = _adresse_bereinigen(place.get("formattedAddress"))
    location = place.get("location", {})
    lat = location.get("latitude")
    lng = location.get("longitude")

    stadtteil = stadtteil_ermitteln(name, adresse)

    # Bestes Foto
    fotos = place.get("photos", [])
    bild_url = None
    bild_attribution = None
    if fotos:
        bild_url = foto_url(fotos[0]["name"])
        autoren = fotos[0].get("authorAttributions", [])
        if autoren:
            bild_attribution = autoren[0].get("displayName", "Google")

    typ = _unser_typ(place, gewuenschter_typ)
    slug = _slug_erzeugen(name, stadtteil)

    ort = {
        "name": name,
        "slug": slug,
        "typ": typ,
        "adresse": adresse,
        "stadtteil": stadtteil,
        "latitude": lat,
        "longitude": lng,
        "bild_url": bild_url,
        "bild_attribution": bild_attribution,
        "preis_niveau": _preis_niveau(place.get("priceLevel")),
        "oeffnungszeiten": _oeffnungszeiten(place.get("regularOpeningHours")),
        "webseite": place.get("websiteUri"),
        "telefon": place.get("nationalPhoneNumber"),
        "google_place_id": place.get("id"),
        "google_rating": rating,
        "google_bewertungen_anzahl": bewertungen,
        "aktiv": False,  # Wird erst nach Kuration aktiviert
    }

    # Editorial Summary als Beschreibung (falls vorhanden)
    editorial = place.get("editorialSummary", {})
    if editorial and editorial.get("text"):
        ort["beschreibung"] = editorial["text"]

    return ort


def alle_orte_suchen(typ: str, limit: int = 0) -> list[dict]:
    """Sucht alle Orte eines Typs im Stadtgebiet Düsseldorf."""
    keywords = SUCH_TYPEN.get(typ, [typ])
    alle = []
    gesehen = set()

    for keyword in keywords:
        logger.info("Suche '%s' in Düsseldorf …", keyword)
        page_token = None

        while True:
            try:
                ergebnis = nearby_search(keyword, page_token)
            except httpx.HTTPStatusError as e:
                logger.error("API-Fehler bei Suche '%s': %s", keyword, e.response.text[:500])
                break
            except Exception as e:
                logger.error("Fehler bei Suche '%s': %s", keyword, e)
                break

            places = ergebnis.get("places", [])
            if not places:
                logger.info("  Keine (weiteren) Ergebnisse für '%s'", keyword)
                break

            for place in places:
                place_id = place.get("id")
                if place_id in gesehen:
                    continue
                gesehen.add(place_id)

                ort = ort_aus_place(place, typ)
                if ort:
                    alle.append(ort)
                    logger.info("  ✓ %s (%s) – ★ %s (%d)", ort["name"], ort["stadtteil"] or "?", ort["google_rating"], ort["google_bewertungen_anzahl"])

            page_token = ergebnis.get("nextPageToken")
            if not page_token:
                break

            if limit and len(alle) >= limit:
                break

        if limit and len(alle) >= limit:
            break

    if limit:
        alle = alle[:limit]

    logger.info("Insgesamt %d %s gefunden (Filter: ≥%.1f★, ≥%d Bewertungen)", len(alle), typ, GOOGLE_PLACES_MIN_RATING, GOOGLE_PLACES_MIN_BEWERTUNGEN)
    return alle


def in_supabase_speichern(orte: list[dict]) -> dict:
    """Speichert Orte in Supabase. Überspringt Duplikate (google_place_id)."""
    if not orte:
        return {"gespeichert": 0, "duplikate": 0, "fehler": 0}

    db = get_supabase_client()
    gespeichert = 0
    duplikate = 0
    fehler = 0

    for ort in orte:
        try:
            google_id = ort.get("google_place_id")
            if google_id:
                treffer = db.table("orte").select("id").eq("google_place_id", google_id).limit(1).execute()
                if treffer.data:
                    duplikate += 1
                    continue

            # Slug-Duplikat prüfen
            slug = ort.get("slug", "")
            slug_treffer = db.table("orte").select("id").eq("slug", slug).limit(1).execute()
            if slug_treffer.data:
                ort["slug"] = f"{slug}-{gespeichert + 1}"

            db.table("orte").insert(ort).execute()
            gespeichert += 1
        except Exception as e:
            fehler += 1
            logger.error("Fehler beim Speichern von '%s': %s", ort.get("name", "?"), e)

    logger.info("Speicherung: %d neu | %d Duplikate | %d Fehler", gespeichert, duplikate, fehler)
    return {"gespeichert": gespeichert, "duplikate": duplikate, "fehler": fehler}


def main():
    parser = argparse.ArgumentParser(description="Google Places Recherche für DiesDasDüsseldorf")
    parser.add_argument("--typ", choices=["restaurant", "cafe"], default="restaurant", help="Typ der Orte")
    parser.add_argument("--limit", type=int, default=0, help="Maximale Anzahl (0 = alle)")
    parser.add_argument("--dry-run", action="store_true", help="Nur suchen, nicht speichern")
    parser.add_argument("--json", action="store_true", help="Ergebnisse als JSON ausgeben")
    args = parser.parse_args()

    if not GOOGLE_PLACES_API_KEY:
        logger.error("GOOGLE_PLACES_API_KEY fehlt in .env")
        sys.exit(1)

    logger.info("Starte Google Places Recherche: typ=%s, limit=%s", args.typ, args.limit or "alle")
    orte = alle_orte_suchen(args.typ, args.limit)

    if args.json:
        print(json.dumps(orte, ensure_ascii=False, indent=2))
        return

    if args.dry_run:
        logger.info("Dry-Run: %d Orte gefunden, nichts gespeichert.", len(orte))
        for o in orte:
            print(f"  {o['name']:40s} {o.get('stadtteil', '?'):15s} ★{o.get('google_rating', '?')} ({o.get('google_bewertungen_anzahl', 0)} Bew.)")
        return

    ergebnis = in_supabase_speichern(orte)
    logger.info("Fertig. %s", ergebnis)


if __name__ == "__main__":
    main()
