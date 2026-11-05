"""
test_imbiss.py – DiesDasDüsseldorf
Prüft die Einteilung Restaurant ↔ Schnellimbiss (scraper/orte/imbiss.py) an echten Grenzfällen.
Ausführen: python -m pytest tests/test_imbiss.py  (oder direkt: python tests/test_imbiss.py)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scraper.orte.imbiss import imbiss_grund, typ_verfeinern  # noqa: E402

RES = {"reservable": True, "takeout": True}
OHNE = {"reservable": False, "takeout": True}
NUR_TAKEOUT = {"takeout": True}

FAELLE = [
    # (Name, Primärtyp, Preis, Ausstattung, Imbiss?)
    ("Dene & Gör", "turkish_restaurant", "€", NUR_TAKEOUT, True),
    ("Palace of Kebap", "kebab_shop", "€", NUR_TAKEOUT, True),
    ("Antalya DÖNER", "turkish_restaurant", "€", RES, True),          # Name eindeutig, trotz Reservierung
    ("Marias Schlemmerimbiss", "gyro_restaurant", "€€", NUR_TAKEOUT, True),
    ("SmashBrothers", "hamburger_restaurant", "€€", NUR_TAKEOUT, True),
    ("Pizzeria Toscana", "pizza_restaurant", "€€", NUR_TAKEOUT, True),
    ("Milonga Food Truck", "argentinian_restaurant", "€€", NUR_TAKEOUT, True),
    ("Bob & Mary", "hamburger_restaurant", "€€", RES, False),          # Burger-Restaurant mit Reservierung
    ("What's Beef", "hamburger_restaurant", "€€", RES, False),
    ("Pizzeria Amici", "pizza_restaurant", "€€", RES, False),
    ("La Grilladine", "moroccan_restaurant", "€€", NUR_TAKEOUT, False),  # „Grill“ nur als ganzes Wort
    ("LUMERO Pizzeria & Aperitivo", "italian_restaurant", "€€", NUR_TAKEOUT, False),
    ("Pizzeria Da Christian", "pizza_restaurant", "€€", {}, False),     # keine Google-Angaben → kein Rückschluss
    ("Ghirloni Eismanufaktur", "korean_restaurant", "€", NUR_TAKEOUT, False),
    ("Takumi", "ramen_restaurant", "€€", NUR_TAKEOUT, False),
    ("Saray Restaurant", "turkish_restaurant", "€€", RES, False),
]


def test_faelle():
    for name, typ, preis, ausstattung, erwartet in FAELLE:
        assert bool(imbiss_grund(name, typ, preis, ausstattung)) is erwartet, name


def test_typ_verfeinern_laesst_andere_typen_in_ruhe():
    assert typ_verfeinern({"typ": "cafe", "name": "Döner Café", "extras": {}}) == "cafe"
    assert typ_verfeinern({"typ": "restaurant", "name": "Döner Ecke", "extras": {}}) == "imbiss"


if __name__ == "__main__":
    test_faelle()
    test_typ_verfeinern_laesst_andere_typen_in_ruhe()
    print("Imbiss-Regeln: alle Tests bestanden")
