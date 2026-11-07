"""
bars.py – DiesDasDüsseldorf
Regeln für den Hub „Kneipen & Bars“ (und die getrennte Vorbereitung des Club-Hubs).

Alle Typen stehen in Google Places „Table A“. Achtung: Ein unbekannter Typ in includedTypes macht
die ganze Nearby Search zu HTTP 400 – deshalb z.B. kein „beer_hall“.
"""
import re

# Kneipen-artige Primärtypen → Unterart „kneipe“
KNEIPEN_TYPEN = ("pub", "irish_pub", "brewpub", "brewery", "beer_garden", "sports_bar")
# Gastropubs (Kneipe mit Küche) gehören in den Kneipen-Hub; kein eigener Suchtyp, sie kommen über bar/pub mit.
# Steht ein Gastropub schon im Restaurant-Hub, landet er auf der E1-Liste statt doppelt angelegt zu werden.
KNEIPEN_PRIMAER_ZUSATZ = ("gastropub",)
# Bar-artige Primärtypen → Unterart „bar“
BAR_TYPEN = ("bar", "cocktail_bar", "wine_bar", "lounge_bar")
# Suchtypen für den Kneipen-Hub (Oder-Verknüpfung in einer Anfrage)
SUCH_TYPEN_BARS = [*BAR_TYPEN, *KNEIPEN_TYPEN]
# Getrennte Suche für den späteren Club-Hub (eigener Zwischenspeicher, kein Import in den Kneipen-Hub)
SUCH_TYPEN_CLUBS = ["night_club"]

# Typ-Nachzug für volle Kleinstzellen: In einer gemeinsamen Anfrage (max. 20 Treffer) verdrängen
# bekannte Bars sonst Kneipen und Biergärten – deshalb getrennt je Gruppe nachfragen.
NACHZUG_BARS = [
    ["pub", "irish_pub", "brewpub", "brewery", "sports_bar"],
    list(BAR_TYPEN),
    ["beer_garden"],
]

SHISHA_TYPEN = {"hookah_bar"}
CLUB_TYPEN = {"night_club"}
HOTEL_TYPEN = {"hotel", "motel", "lodging", "resort_hotel", "extended_stay_hotel"}
# Brauhaus-Hinweise in types (auch wenn Google den Ort primär als Restaurant führt)
BRAUHAUS_TYPEN = {"brewery", "brewpub"}


def _primaer(place: dict) -> str:
    return place.get("primaryType") or ""


def _typen(place: dict) -> set[str]:
    return set(place.get("types") or [])


def ist_shisha(place: dict) -> bool:
    """Shisha-Bar (ausgeschlossen, Entscheidung E2) – auch wenn Google sie zusätzlich als „bar“ führt."""
    return _primaer(place) in SHISHA_TYPEN or bool(_typen(place) & SHISHA_TYPEN)


def ist_club(place: dict) -> bool:
    """Club (gehört in den eigenen Club-Hub, nicht in den Kneipen-Hub)."""
    return _primaer(place) in CLUB_TYPEN


def ist_bar_ort(place: dict) -> bool:
    """
    Gehört der Ort in den Kneipen-Hub?
    Ja bei Bar-/Kneipen-Primärtyp oder bei einem Brauhaus (brewery/brewpub in types), das Google
    primär als Restaurant führt. Nein bei Shisha-Bars und Clubs.
    """
    if ist_shisha(place) or ist_club(place):
        return False
    p = _primaer(place)
    if p in KNEIPEN_TYPEN or p in BAR_TYPEN or p in KNEIPEN_PRIMAER_ZUSATZ:
        return True
    return bool(_typen(place) & BRAUHAUS_TYPEN)


def hotel_erlaubt(place: dict) -> bool:
    """Hotelbar zulassen (E3): nur wenn der Primärtyp eine Bar ist – ein Hotel mit Bar-Nebentyp nicht."""
    return _primaer(place) in BAR_TYPEN or _primaer(place) in KNEIPEN_TYPEN


def ist_hotel_ohne_bar(place: dict) -> bool:
    return bool(_typen(place) & HOTEL_TYPEN) and not hotel_erlaubt(place)


# Brauhaus = eigene Unterart (eigenes Label und eigener Filter auf der Website)
BRAUHAUS_PRIMAER = {"brewery", "brewpub"}
BRAUHAUS_NAME = re.compile(r"brauhaus|brauerei|hausbrauerei|brauereiausschank", re.IGNORECASE)


def ist_brauhaus(primaertyp: str | None, name: str | None) -> bool:
    """Brauhaus/Hausbrauerei: Google-Primärtyp Brauerei/Brewpub oder eindeutiger Name.

    Bewusst NICHT über Nebentypen: Google hängt „brewery“/„brewpub“ auch an Fischrestaurants und
    Chicken-Läden (geprüft 07.11.2026: Juttas Forelle, Hitchcoq, Tonhalle Kaiserswerth).
    """
    return (primaertyp or "") in BRAUHAUS_PRIMAER or bool(BRAUHAUS_NAME.search(name or ""))


def unterart(place: dict) -> str:
    """„brauhaus“, „bar“ oder „kneipe“ aus Primärtyp und Name (Google-Place)."""
    name = (place.get("displayName") or {}).get("text") if isinstance(place.get("displayName"), dict) else place.get("name")
    if ist_brauhaus(_primaer(place), name):
        return "brauhaus"
    if _primaer(place) in BAR_TYPEN:
        return "bar"
    return "kneipe"
