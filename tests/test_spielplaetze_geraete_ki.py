"""Tests für scraper/spielplaetze/geraete_ki.py (Übernahme-Regeln und SQL)."""
from scraper.spielplaetze.geraete_ki import sql_zeile, uebernehmen

HEUTE = "2026-11-25"


def _erg(fotos=None, luft=None, zeigt=True):
    return {"fotos": {"zeigt_spielplatz": zeigt, "erkannt": fotos or [], "hinweis": ""},
            "luft": {"zeigt_spielplatz": True, "erkannt": luft or [], "hinweis": ""}}


def test_schwelle_und_vorhandenes_bleibt():
    erg = _erg(fotos=[{"merkmal": "rutsche", "konfidenz": 0.8, "beleg": "Bild 1"},
                      {"merkmal": "schaukel", "konfidenz": 0.79, "beleg": "Bild 2"},
                      {"merkmal": "sandkasten", "konfidenz": 0.95, "beleg": "Bild 0"}])
    neu = uebernehmen(erg, {"sandkasten": {"wert": "ja", "quelle": "osm"}}, HEUTE)
    assert set(neu) == {"rutsche"}
    assert neu["rutsche"]["quelle"] == "foto_ki" and neu["rutsche"]["konfidenz"] == 0.8


def test_strenge_merkmale():
    erg = _erg(fotos=[{"merkmal": "karussell", "konfidenz": 0.9, "beleg": "x"},
                      {"merkmal": "wasserspiel", "konfidenz": 0.96, "beleg": "y"}])
    assert set(uebernehmen(erg, {}, HEUTE)) == {"wasserspiel"}


def test_luftbild_nur_erlaubte_merkmale_und_fotos_zuerst():
    erg = _erg(fotos=[{"merkmal": "sandkasten", "konfidenz": 0.9, "beleg": "Foto"}],
               luft=[{"merkmal": "sandkasten", "konfidenz": 0.95, "beleg": "Luft"},
                     {"merkmal": "rutsche", "konfidenz": 0.99, "beleg": "Luft"},
                     {"merkmal": "fussball", "konfidenz": 0.85, "beleg": "Luft"}])
    neu = uebernehmen(erg, {}, HEUTE)
    assert neu["sandkasten"]["quelle"] == "foto_ki"
    assert neu["fussball"]["quelle"] == "luftbild_ki"
    assert "rutsche" not in neu


def test_fotos_ohne_spielplatz_werden_ignoriert():
    erg = _erg(fotos=[{"merkmal": "rutsche", "konfidenz": 0.99, "beleg": "x"}], zeigt=False)
    assert uebernehmen(erg, {}, HEUTE) == {}


def test_sql_vorhandenes_gewinnt():
    sql = sql_zeile("abc", "Spielplatz O'Test", {"rutsche": {"wert": "ja", "quelle": "foto_ki", "beleg": "Bild 1"}})
    assert "'::jsonb || COALESCE(extras->'spielplatz'->'ausstattung'" in sql
    assert "WHERE id = 'abc' AND typ = 'spielplatz'" in sql
