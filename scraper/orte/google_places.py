"""
google_places.py – DiesDasDüsseldorf
Recherchiert Restaurants und Cafés in Düsseldorf über die Google Places API (New).

Ablauf:
  1. Nearby Search: Findet Orte nach Typ im Stadtgebiet
  2. Place Details: Lädt pro Ort Beschreibung (editorialSummary), Bewertungstexte und
     Ausstattung (Terrasse, vegetarisch, Frühstück, kinderfreundlich …)
  3. Speicherung: Schreibt alles in die Supabase-Tabelle `orte` (aktiv = false)

Fotos: Gespeichert wird nur der Foto-Ressourcenname (extras.google_foto), NIE eine URL mit
API-Key – sonst stünde der Key öffentlich im HTML der Website. Die Auslieferung des Fotos
übernimmt später die Website serverseitig.

Nutzung:
  python -m scraper.orte.google_places [--typ restaurant|cafe] [--limit 50] [--dry-run]
  python -m scraper.orte.google_places --aktualisieren [--dry-run]
      → lädt für alle bereits gespeicherten Orte die Details nach und entfernt
        API-Keys aus alten Bild-URLs (kuratierte Felder bleiben unangetastet)
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
from pipeline.slug_generator import _slugify
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


def alle_zeilen(db, tabelle: str, spalten: str, filter_fn=None) -> list[dict]:
    """
    Lädt ALLE Zeilen einer Tabelle seitenweise (Supabase liefert pro Abfrage höchstens 1.000).
    Stabil sortiert nach id, damit beim Blättern nichts doppelt oder verloren geht.

    Args:
        filter_fn: optionale Funktion, die die Abfrage weiter einschränkt (z.B. lambda q: q.eq("aktiv", True))
    """
    zeilen, seite = [], 0
    while True:
        abfrage = db.table(tabelle).select(spalten)
        if filter_fn:
            abfrage = filter_fn(abfrage)
        teil = abfrage.order("id").range(seite * 1000, seite * 1000 + 999).execute().data or []
        zeilen += teil
        if len(teil) < 1000:
            return zeilen
        seite += 1


def _headers(field_mask: str) -> dict:
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": field_mask,
    }


def _slug_erzeugen(name: str, stadtteil: str | None = None) -> str:
    """Erzeugt einen URL-freundlichen Slug aus dem Namen (Umlaute → ae/oe/ue, Akzente → ASCII: Café → cafe)."""
    text = _slugify(name)
    if stadtteil:
        teil = _slugify(stadtteil)
        # Steckt der Stadtteil schon im Namen ("The Döner Brothers Neuss"), nicht doppelt anhängen
        if not (text == teil or text.endswith(f"-{teil}") or f"-{teil}-" in text):
            text = f"{text}-{teil}"
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


# Basisfelder für Place Details
_DETAIL_FELDER_BASIS = (
    "id,displayName,formattedAddress,location,rating,userRatingCount,primaryType,types,"
    "priceLevel,googleMapsUri,websiteUri,nationalPhoneNumber,regularOpeningHours,"
    "editorialSummary,reviews,photos"
)
# Ausstattungsmerkmale (Places API New, boolesche Felder) → Tag auf der Website
_AUSSTATTUNG_TAGS = {
    "outdoorSeating": "Terrasse",
    "servesBreakfast": "Frühstück",
    "servesBrunch": "Brunch",
    "servesVegetarianFood": "Vegetarisch",
    "servesCocktails": "Cocktails",
    "servesDessert": "Desserts",
    "goodForChildren": "Kinderfreundlich",
    "menuForChildren": "Kinderkarte",
    "allowsDogs": "Hunde willkommen",
    "goodForGroups": "Gruppen",
    "reservable": "Reservierbar",
    "takeout": "To go",
    "liveMusic": "Live-Musik",
}
_DETAIL_FELDER_VOLL = _DETAIL_FELDER_BASIS + "," + ",".join(_AUSSTATTUNG_TAGS)

# Wie viele Bewertungstexte als Material für die spätere KI-Beschreibung gespeichert werden
_MAX_BEWERTUNGEN = 5


def place_details(place_id: str) -> dict:
    """
    Place Details (New) – lädt vollständige Infos zu einem Ort (auf Deutsch).

    Lehnt die API die Ausstattungsfelder ab (HTTP 400), wird mit den Basisfeldern wiederholt.
    """
    url = f"{API_BASE}/places/{place_id}"
    params = {"languageCode": "de", "regionCode": "DE"}

    with httpx.Client(timeout=30) as client:
        for field_mask in (_DETAIL_FELDER_VOLL, _DETAIL_FELDER_BASIS):
            time.sleep(0.5)  # Rate Limiting
            resp = client.get(url, params=params, headers=_headers(field_mask))
            if resp.status_code == 400 and field_mask is _DETAIL_FELDER_VOLL:
                logger.warning("Details mit Ausstattungsfeldern abgelehnt, versuche Basisfelder: %s", resp.text[:300])
                continue
            resp.raise_for_status()
            return resp.json()
    return {}


def _foto_info(fotos: list[dict]) -> tuple[dict | None, str | None]:
    """
    Wählt das erste Foto und gibt (Foto-Info für extras, Attribution) zurück.

    Gespeichert wird nur der Ressourcenname ("places/…/photos/…"), keine URL mit API-Key.
    Google verlangt, dass der Urheber (authorAttributions) beim Foto angezeigt wird.
    """
    if not fotos:
        return None, None
    foto = fotos[0]
    autoren = foto.get("authorAttributions", [])
    autor = autoren[0] if autoren else {}
    info = {
        "name": foto.get("name"),
        "breite": foto.get("widthPx"),
        "hoehe": foto.get("heightPx"),
        "autor": autor.get("displayName"),
        "autor_url": autor.get("uri"),
    }
    return info, autor.get("displayName") or "Google"


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
        "bild_url": None,  # Foto wird über extras.google_foto serverseitig ausgeliefert
        "preis_niveau": _preis_niveau(place.get("priceLevel")),
        "oeffnungszeiten": _oeffnungszeiten(place.get("regularOpeningHours")),
        "webseite": place.get("websiteUri"),
        "telefon": place.get("nationalPhoneNumber"),
        "google_place_id": place.get("id"),
        "google_rating": rating,
        "google_bewertungen_anzahl": bewertungen,
        "aktiv": False,  # Wird erst nach Kuration aktiviert
    }
    ort.update(_detail_felder(place))
    return ort


def _detail_felder(place: dict) -> dict:
    """
    Wertet die Detail-Felder eines Place aus: Beschreibung, Foto, Ausstattung, Bewertungen.

    Returns:
        Teil-Dict für die orte-Tabelle (beschreibung, bild_attribution, tags, extras)
    """
    felder: dict = {}
    extras: dict = {}

    # Kurzbeschreibung von Google – Platzhalter bis zur eigenen KI-Beschreibung
    editorial = place.get("editorialSummary") or {}
    if editorial.get("text"):
        felder["beschreibung"] = editorial["text"]
        extras["google_zusammenfassung"] = editorial["text"]

    foto, attribution = _foto_info(place.get("photos", []))
    if foto:
        extras["google_foto"] = foto
        felder["bild_attribution"] = attribution

    # Ausstattung → Tags (nur Merkmale, die Google ausdrücklich mit "ja" belegt)
    tags = [tag for feld, tag in _AUSSTATTUNG_TAGS.items() if place.get(feld) is True]
    if tags:
        felder["tags"] = tags
    ausstattung = {feld: place[feld] for feld in _AUSSTATTUNG_TAGS if isinstance(place.get(feld), bool)}
    if ausstattung:
        extras["google_ausstattung"] = ausstattung
    if place.get("outdoorSeating") is True:
        extras["terrasse"] = True  # wird auf der Detailseite angezeigt

    if place.get("googleMapsUri"):
        extras["google_maps_url"] = place["googleMapsUri"]

    # Bewertungstexte als Material für die spätere KI-Beschreibung (werden nicht angezeigt)
    bewertungen = []
    for r in (place.get("reviews") or [])[:_MAX_BEWERTUNGEN]:
        text = (r.get("text") or {}).get("text") or (r.get("originalText") or {}).get("text")
        if text:
            bewertungen.append({
                "sterne": r.get("rating"),
                "text": text[:1000],
                "datum": (r.get("publishTime") or "")[:10] or None,
            })
    if bewertungen:
        extras["google_bewertungen"] = bewertungen

    felder["extras"] = extras
    return felder


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

                # Erst mit den Suchdaten filtern, dann nur für passende Orte Details laden (kostet pro Abruf)
                if not ort_aus_place(place, typ):
                    continue
                try:
                    place = {**place, **place_details(place_id)}
                except Exception as e:
                    logger.warning("  Details für '%s' nicht geladen: %s", place.get("displayName", {}).get("text", "?"), e)

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


def bestehende_aktualisieren(dry_run: bool = False) -> dict:
    """
    Lädt für alle gespeicherten Orte mit google_place_id die Details nach.

    Aktualisiert werden nur Google-Daten (Bewertung, Öffnungszeiten, Kontakt, Foto, extras).
    Kuratierte Felder (Name, Slug, Untertitel, Highlight, Score, aktiv) bleiben unangetastet;
    Beschreibung und Tags werden nur gesetzt, wenn sie noch leer sind.
    Bild-URLs mit eingebettetem API-Key werden entfernt.
    """
    db = get_supabase_client()
    orte = alle_zeilen(
        db, "orte", "id, name, google_place_id, beschreibung, tags, bild_url, extras",
        lambda q: q.not_.is_("google_place_id", "null"),
    )
    logger.info("%d Orte mit Google-ID gefunden", len(orte))
    aktualisiert = fehler = 0

    for ort in orte:
        try:
            place = place_details(ort["google_place_id"])
        except Exception as e:
            fehler += 1
            logger.error("Details für '%s' fehlgeschlagen: %s", ort["name"], e)
            continue

        details = _detail_felder(place)
        update: dict = {
            "google_rating": place.get("rating"),
            "google_bewertungen_anzahl": place.get("userRatingCount"),
            "oeffnungszeiten": _oeffnungszeiten(place.get("regularOpeningHours")),
            "webseite": place.get("websiteUri"),
            "telefon": place.get("nationalPhoneNumber"),
            "preis_niveau": _preis_niveau(place.get("priceLevel")),
            # Bestehende extras behalten (z.B. manuell gepflegte Küche), Google-Daten ergänzen
            "extras": {**(ort.get("extras") or {}), **details["extras"]},
        }
        update = {k: v for k, v in update.items() if v is not None}
        if "bild_attribution" in details:
            update["bild_attribution"] = details["bild_attribution"]
        if not ort.get("beschreibung") and details.get("beschreibung"):
            update["beschreibung"] = details["beschreibung"]
        if not ort.get("tags") and details.get("tags"):
            update["tags"] = details["tags"]
        if ort.get("bild_url") and "key=" in ort["bild_url"]:
            update["bild_url"] = None  # API-Key nicht öffentlich ausliefern

        logger.info(
            "  %s %s – Tags: %s | Beschreibung: %s | Foto: %s",
            "(Dry-Run)" if dry_run else "✓", ort["name"],
            ", ".join(update.get("tags") or ort.get("tags") or []) or "–",
            "neu" if "beschreibung" in update else ("vorhanden" if ort.get("beschreibung") else "–"),
            "ja" if details["extras"].get("google_foto") else "nein",
        )
        if dry_run:
            continue
        try:
            db.table("orte").update(update).eq("id", ort["id"]).execute()
            aktualisiert += 1
        except Exception as e:
            fehler += 1
            logger.error("Speichern für '%s' fehlgeschlagen: %s", ort["name"], e)

    logger.info("Aktualisierung: %d aktualisiert | %d Fehler", aktualisiert, fehler)
    return {"aktualisiert": aktualisiert, "fehler": fehler}


def main():
    parser = argparse.ArgumentParser(description="Google Places Recherche für DiesDasDüsseldorf")
    parser.add_argument("--typ", choices=["restaurant", "cafe"], default="restaurant", help="Typ der Orte")
    parser.add_argument("--limit", type=int, default=0, help="Maximale Anzahl (0 = alle)")
    parser.add_argument("--dry-run", action="store_true", help="Nur suchen, nicht speichern")
    parser.add_argument("--json", action="store_true", help="Ergebnisse als JSON ausgeben")
    parser.add_argument("--aktualisieren", action="store_true",
                        help="Details für alle bereits gespeicherten Orte nachladen")
    args = parser.parse_args()

    if not GOOGLE_PLACES_API_KEY:
        logger.error("GOOGLE_PLACES_API_KEY fehlt in .env")
        sys.exit(1)

    if args.aktualisieren:
        bestehende_aktualisieren(dry_run=args.dry_run)
        return

    logger.info("Starte Google Places Recherche: typ=%s, limit=%s", args.typ, args.limit or "alle")
    orte = alle_orte_suchen(args.typ, args.limit)

    if args.json:
        print(json.dumps(orte, ensure_ascii=False, indent=2))
        return

    if args.dry_run:
        logger.info("Dry-Run: %d Orte gefunden, nichts gespeichert.", len(orte))
        for o in orte:
            print(
                f"  {o['name']:40s} {o.get('stadtteil') or '?':15s} ★{o.get('google_rating', '?')} "
                f"({o.get('google_bewertungen_anzahl', 0)} Bew.) | Tags: {', '.join(o.get('tags') or []) or '–'}"
            )
        return

    ergebnis = in_supabase_speichern(orte)
    logger.info("Fertig. %s", ergebnis)


if __name__ == "__main__":
    main()
