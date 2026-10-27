"""
stadtteil_mapper.py – DiesDasDüsseldorf
Ordnet Events automatisch einem Düsseldorfer Stadtteil zu.
Priorität: 1) Venue-Name → 2) PLZ → 3) Straßenname → 4) None
"""
import logging
import re

logger = logging.getLogger(__name__)

# Priorität 1: Bekannte Venues → Stadtteil
VENUE_STADTTEIL: dict[str, str] = {
    "Tonhalle Düsseldorf": "Pempelfort",
    "Tonhalle": "Pempelfort",
    "Deutsche Oper am Rhein": "Pempelfort",
    "Oper am Rhein": "Pempelfort",
    "Düsseldorfer Schauspielhaus": "Pempelfort",
    "Schauspielhaus": "Pempelfort",
    "D'haus": "Pempelfort",
    "Kunstpalast": "Pempelfort",
    "NRW-Forum": "Pempelfort",
    "FFT Düsseldorf": "Pempelfort",
    "Forum Freies Theater": "Pempelfort",
    "Nachtresidenz": "Pempelfort",
    "zakk": "Flingern",
    "Capitol Theater": "Flingern",
    "Tanzhaus NRW": "Flingern",
    "Pitcher": "Flingern",
    "Weltkunstzimmer": "Flingern",
    "Atelier am Eck": "Flingern",
    "Stahlwerk": "Lierenfeld",
    "Rudas Studios": "Lierenfeld",
    "Kulturschlachthof R25": "Lierenfeld",
    "Kulturschlachthof": "Lierenfeld",
    "Salon des Amateurs": "Altstadt",
    "Kunstsammlung NRW": "Altstadt",
    "K20": "Altstadt",
    "Kunsthalle Düsseldorf": "Altstadt",
    "Filmmuseum": "Altstadt",
    "Black Box Kino": "Altstadt",
    "Kom(m)ödchen": "Altstadt",
    "Kommödchen": "Altstadt",
    "Komödchen": "Altstadt",
    "Japan Center": "Altstadt",
    "Japanisches Kulturzentrum": "Altstadt",
    "Robert-Schumann-Saal": "Altstadt",
    "Savoy Theater": "Altstadt",
    "Marionetten-Theater": "Altstadt",
    "Heinrich-Heine-Institut": "Altstadt",
    "Haus der Universität": "Altstadt",
    "Maxhaus": "Altstadt",
    "Brauerei Kürzer": "Altstadt",
    "Uerige": "Altstadt",
    "Füchschen": "Altstadt",
    "Stadtstrand": "Altstadt",
    "Stone": "Altstadt",
    "K21": "Friedrichstadt",
    "Stadtbücherei": "Friedrichstadt",
    "Zentralbibliothek": "Friedrichstadt",
    "IHK Düsseldorf": "Friedrichstadt",
    "IHK": "Friedrichstadt",
    "Tube Club": "Friedrichstadt",
    "Sub": "Friedrichstadt",
    "Jazz-Schmiede": "Bilk",
    "Palais Wittgenstein": "Bilk",
    "STARTPLATZ": "Hafen",
    "Startplatz": "Hafen",
    "Mitsubishi Electric HALLE": "Stockum",
    "Mitsubishi Electric Halle": "Stockum",
    "PSD BANK DOME": "Stockum",
    "Merkur Spiel-Arena": "Stockum",
    "ISS DOME": "Stockum",
    "ESPRIT arena": "Stockum",
    "Messe Düsseldorf": "Stockum",
    "Classic Remise": "Mörsenbroich",
    "Volksgarten": "Oberbilk",
    "KIT": "Unterbilk",
    "KIT – Kunst im Tunnel": "Unterbilk",
}

# Sortiert nach Länge (längster Key zuerst) für präziseres Matching
_VENUE_KEYS_SORTED = sorted(VENUE_STADTTEIL.keys(), key=len, reverse=True)

# Priorität 2: PLZ → Stadtteil
PLZ_STADTTEIL: dict[str, str] = {
    "40210": "Stadtmitte",
    "40211": "Pempelfort",
    "40212": "Stadtmitte",
    "40213": "Altstadt",
    "40215": "Friedrichstadt",
    "40217": "Unterbilk",
    "40219": "Unterbilk",
    "40221": "Hafen",
    "40223": "Bilk",
    "40225": "Bilk",
    "40227": "Oberbilk",
    "40229": "Eller",
    "40231": "Lierenfeld",
    "40233": "Flingern",
    "40235": "Flingern",
    "40237": "Düsseltal",
    "40239": "Düsseltal",
    "40468": "Derendorf",
    "40470": "Mörsenbroich",
    "40472": "Rath",
    "40474": "Golzheim",
    "40476": "Derendorf",
    "40477": "Pempelfort",
    "40479": "Pempelfort",
    "40489": "Kaiserswerth",
    "40545": "Oberkassel",
    "40547": "Lörick",
    "40549": "Heerdt",
    "40589": "Holthausen",
    "40591": "Wersten",
    "40593": "Benrath",
    "40595": "Garath",
    "40597": "Benrath",
    "40599": "Hassels",
    "40625": "Gerresheim",
    "40627": "Vennhausen",
    "40629": "Grafenberg",
}

_PLZ_REGEX = re.compile(r"\b(40\d{3})\b")

# Priorität 3: Bekannte Straßen/Gebiete → Stadtteil
STRASSEN_STADTTEIL: dict[str, str] = {
    "Königsallee": "Stadtmitte",
    "Kö ": "Stadtmitte",
    "Schadowstraße": "Stadtmitte",
    "Bolkerstraße": "Altstadt",
    "Ratinger Straße": "Altstadt",
    "Rheinufer": "Altstadt",
    "Burgplatz": "Altstadt",
    "Marktplatz": "Altstadt",
    "Flinger Straße": "Altstadt",
    "Medienhafen": "Hafen",
    "Speditionstr": "Hafen",
    "Zollhof": "Hafen",
    "Erkrather Str": "Flingern",
    "Ackerstraße": "Flingern",
    "Birkenstraße": "Flingern",
    "Hermannplatz": "Flingern",
    "Grafenberger Allee": "Düsseltal",
    "Rethelstraße": "Düsseltal",
    "Luegallee": "Oberkassel",
    "Belsenplatz": "Oberkassel",
    "Nordstraße": "Pempelfort",
    "Ehrenhof": "Pempelfort",
    "Münsterstraße": "Derendorf",
    "Oberbilker Allee": "Oberbilk",
    "Friedrichstraße": "Friedrichstadt",
    "Bilker Allee": "Bilk",
    "Universitätsstraße": "Bilk",
    "Aachener Straße": "Bilk",
}


def stadtteil_ermitteln(ort: str, adresse: str | None = None) -> str | None:
    """
    Ermittelt den Düsseldorfer Stadtteil für ein Event.

    Args:
        ort: Venue-Name (z.B. "Tonhalle Düsseldorf")
        adresse: Straßenadresse mit PLZ (z.B. "Ehrenhof 1, 40479 Düsseldorf")

    Returns:
        Stadtteil-Name oder None wenn nicht zuordenbar
    """
    if not ort:
        return None

    ort_lower = ort.lower()

    # Priorität 1: Venue-Name Lookup (längster Match zuerst)
    for venue_key in _VENUE_KEYS_SORTED:
        if venue_key.lower() in ort_lower:
            return VENUE_STADTTEIL[venue_key]

    # Priorität 2: PLZ aus Adresse
    if adresse:
        plz_match = _PLZ_REGEX.search(adresse)
        if plz_match:
            plz = plz_match.group(1)
            if plz in PLZ_STADTTEIL:
                return PLZ_STADTTEIL[plz]

    # Priorität 3: Straßennamen in Adresse oder Ort
    texte = [ort]
    if adresse:
        texte.append(adresse)
    kombiniert = " ".join(texte)

    for strasse, stadtteil in STRASSEN_STADTTEIL.items():
        if strasse.lower() in kombiniert.lower():
            return stadtteil

    return None


def stadtteil_batch_zuordnen(events: list[dict]) -> list[dict]:
    """
    Weist allen Events in der Liste einen Stadtteil zu (in-place).
    Bereits gesetzte Stadtteile werden nicht überschrieben.
    """
    zugeordnet = 0
    for event in events:
        if event.get("stadtteil"):
            continue
        stadtteil = stadtteil_ermitteln(
            event.get("ort", ""),
            event.get("adresse"),
        )
        if stadtteil:
            event["stadtteil"] = stadtteil
            zugeordnet += 1

    logger.info(
        "Stadtteil-Zuordnung: %d von %d Events zugeordnet",
        zugeordnet, len(events),
    )
    return events
