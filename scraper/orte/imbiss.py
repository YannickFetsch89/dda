"""
imbiss.py – DiesDasDüsseldorf
Einteilung Restaurant ↔ Schnellimbiss (Ort-Typ "imbiss") anhand der Google-Daten.

Hintergrund (2026-11-05): Der Guide sortiert nach Bewertungen; Dönerläden mit Tausenden Bewertungen
standen damit ganz oben zwischen „richtigen“ Restaurants. Schnellimbisse bekommen deshalb einen
eigenen Typ und einen eigenen Filter. Cafés werden nicht geprüft.

Regeln (in dieser Reihenfolge):
  1. Google-Primärtyp ist eindeutig ein Imbiss (kebab_shop, gyro_restaurant, fast_food_restaurant …)
  2. Der Name ist eindeutig ein Imbiss (Döner, Kebap, Imbiss, Lahmacun, Falafel, Köfte, Currywurst …)
  3. Keine Reservierung (Google: reservable = false ODER keine Angabe, aber Takeaway), keine
     Restaurant-Signale (Cocktails, Preisniveau €€€) und
       - der Name deutet auf einen Imbiss (Grill, Burger, Pizzeria, Pommes, Frittenwerk …) oder
       - der Primärtyp ist Burger/Pizza/Türkisch/Taco (hamburger_, pizza_, turkish_, taco_restaurant) oder
       - das Preisniveau ist „€“ – nur, wenn Google ausdrücklich „nicht reservierbar“ sagt
  Alles andere bleibt Restaurant – z.B. Burger-Restaurants mit Reservierung (Bob & Mary, What's Beef).
"""
import re
from typing import Optional

IMBISS_TYPEN = {
    "kebab_shop", "gyro_restaurant", "fast_food_restaurant", "sandwich_shop", "falafel_restaurant",
    "meal_takeaway", "snack_bar", "food_court", "hot_dog_stand", "hot_dog_restaurant", "chicken_wings_restaurant",
}
# Ohne Reservierung: diese Primärtypen sind in Düsseldorf fast immer Imbiss/Lieferdienst
TYPEN_OHNE_RESERVIERUNG = {"hamburger_restaurant", "pizza_restaurant", "turkish_restaurant", "taco_restaurant"}
# Namens-Hinweise auf Pizza zählen nur bei diesen Typen (sonst z.B. „LUMERO Pizzeria & Aperitivo“, italienisch)
PIZZA_TYPEN = {"pizza_restaurant", "restaurant", "fast_food_restaurant", None}

NAME_EINDEUTIG = re.compile(
    # „Imbiss“ nur als ganzes Wort (nicht „Imbisskultur Bistro“); Döner, Köfte usw. auch als Wortteil
    r"d[öo]e?ner|kebab|kebap|\bimbi(?:ss|ß)\b|lahmacun|k[öo]e?fte|ç?i[gğ]\s?k[öo]fte|shawarma|schawarma|"
    r"d[üu]r[üu]m|falafel|currywurst|schnellimbi(?:ss|ß)|schnellrestaurant|food\s?truck",
    re.I,
)
# „Grill“ nur als ganzes Wort bzw. Grillstube/-haus (nicht „La Grilladine“)
NAME_HINWEIS = re.compile(
    r"\bgrill\b|grillstube|grillhaus|grillh(?:ä|ae)hnchen|fried\s?chicken|burger|pommes|frittenwerk|fritten|snack|"
    r"gyros|smash|baguett|b[aá]nh\s?m[iì]",
    re.I,
)
NAME_PIZZA = re.compile(r"pizzeria|pizza", re.I)
# Eisdielen tauchen bei Google teils unter Restaurant-Typen auf – weder Imbiss noch hier zu bewerten
NAME_KEIN_IMBISS = re.compile(r"eis(manufaktur|café|cafe|diele)|gelato|gelateria", re.I)


def _reservierung(ausstattung: dict) -> str:
    """
    "ja" (reservierbar) · "nein" (Google sagt ausdrücklich: nicht reservierbar) ·
    "unklar" (keine Reservierungsangabe, aber Takeaway – typisch für Imbisse, aber kein Beweis) ·
    "unbekannt" (gar keine Angaben).
    """
    wert = ausstattung.get("reservable")
    if wert is True:
        return "ja"
    if wert is False:
        return "nein"
    return "unklar" if ausstattung.get("takeout") is True else "unbekannt"


def _restaurant_signale(preis_niveau: Optional[str], ausstattung: dict) -> bool:
    """Cocktails oder gehobene Preise sprechen gegen einen Schnellimbiss (z.B. Burger-Restaurants mit Bar)."""
    return ausstattung.get("servesCocktails") is True or preis_niveau == "€€€"


def imbiss_grund(name: str, primaertyp: Optional[str], preis_niveau: Optional[str],
                 ausstattung: Optional[dict]) -> Optional[str]:
    """
    Prüft, ob ein Restaurant ein Schnellimbiss ist.

    Returns:
        Kurzer Grund (z.B. "Google-Typ kebab_shop") oder None, wenn es ein Restaurant bleibt.
    """
    name = name or ""
    ausstattung = ausstattung or {}
    if NAME_KEIN_IMBISS.search(name):
        return None
    if primaertyp in IMBISS_TYPEN:
        return f"Google-Typ {primaertyp}"
    treffer = NAME_EINDEUTIG.search(name)
    if treffer:
        return f"Name „{treffer.group(0)}“"
    reservierung = _reservierung(ausstattung)
    if reservierung in ("ja", "unbekannt") or _restaurant_signale(preis_niveau, ausstattung):
        return None
    # Ab hier: nicht reservierbar ("nein") oder Takeaway ohne Reservierungsangabe ("unklar")
    zusatz = "keine Reservierung" if reservierung == "nein" else "Takeaway, keine Reservierungsangabe"
    treffer = NAME_HINWEIS.search(name) or (NAME_PIZZA.search(name) if primaertyp in PIZZA_TYPEN else None)
    if treffer:
        return f"Name „{treffer.group(0)}“, {zusatz}"
    if primaertyp in TYPEN_OHNE_RESERVIERUNG:
        return f"Google-Typ {primaertyp}, {zusatz}"
    # Nur der Preis ist zu schwach – zählt bloß, wenn Google ausdrücklich „nicht reservierbar“ sagt
    if preis_niveau == "€" and reservierung == "nein":
        return "Preisniveau €, keine Reservierung"
    return None


def typ_verfeinern(ort: dict) -> str:
    """Restaurant → "imbiss", wenn die Regeln greifen; andere Typen bleiben unverändert."""
    if ort.get("typ") != "restaurant":
        return ort.get("typ")
    extras = ort.get("extras") or {}
    grund = imbiss_grund(ort.get("name"), extras.get("google_primaertyp"), ort.get("preis_niveau"),
                         extras.get("google_ausstattung"))
    return "imbiss" if grund else "restaurant"
