"""Tests: Filiale aus der Detailseite der Stadtbüchereien (Plan docs/plan-locations-2026-11-18.md, 3.15, Schritt 2a)."""
import unittest

from scraper.tier2.stadtbuechereien import (
    ADRESSE_ZENTRAL,
    ZENTRALBIBLIOTHEK,
    _filialen_aus_liste,
    filiale_aus_text,
    filiale_aus_titel,
)


class FilialeTest(unittest.TestCase):
    def test_filiale_mit_adresse(self):
        text = ("Kommt vorbei zur Geschichtenzeit! Der Eintritt ist frei. Stadtbücherei Rath, Westfalenstraße 24, "
                "Telefon 0211 89-94151, E-Mail stbrath @ duesseldorf.de « zurück Nach oben")
        self.assertEqual(filiale_aus_text(text), ("Stadtbücherei Rath", "Westfalenstraße 24, Düsseldorf"))
        self.assertEqual(filiale_aus_text("Keine Anmeldung erforderlich. Stadtbücherei Flingern, Hoffeldstraße 69 « zurück"),
                         ("Stadtbücherei Flingern", "Hoffeldstraße 69, Düsseldorf"))

    def test_feste_adresse_statt_tippfehler(self):
        # Quelle schreibt „Friedriechstraße“ / „Luegalle“: die feste Adresse der Filiale gewinnt
        self.assertEqual(filiale_aus_text("Stadtbücherei Bilk, Friedriechstraße 127 « zurück"),
                         ("Stadtbücherei Bilk", "Friedrichstraße 127, Düsseldorf"))
        self.assertEqual(filiale_aus_text("Stadtbücherei Oberkassel « zurück"),
                         ("Stadtbücherei Oberkassel", "Luegallee 65, Düsseldorf"))

    def test_kinderbuecherei(self):
        self.assertEqual(filiale_aus_text("Für Kinder. Kinderbücherei Hassels, Hasselsstraße 1 « zurück")[0],
                         "Kinderbücherei Hassels")

    def test_raum_der_zentralbibliothek(self):
        for ende in ("Im Musikstudio der Zentralbibliothek, Konrad-Adenauer-Platz 1 « zurück",
                     "In der Herzkammer der Zentralbibliothek, Konrad-Adenauer-Platz 1 « zurück",
                     "Im Lernstudio der Zentralbiblitohek, Konrad-Adenauer-Platz 1 « zurück"):
            self.assertEqual(filiale_aus_text(ende), (ZENTRALBIBLIOTHEK, ADRESSE_ZENTRAL))

    def test_fft_und_erwaehnung_im_text(self):
        self.assertEqual(filiale_aus_text("Im FFT Düsseldorf, Konrad-Adenauer-Platz 1, Foyer (KAP1, 1. OG) « zurück")[0],
                         "FFT Düsseldorf")
        # Eine andere Filiale weit vorne im Text zählt nicht, nur der Ort am Ende
        text = "Auch in der Stadtbücherei Bilk gibt es Termine. " + "x " * 300 + "Stadtbücherei Eller, Gumbertstraße 1 « zurück"
        self.assertEqual(filiale_aus_text(text)[0], "Stadtbücherei Eller")
        self.assertIsNone(filiale_aus_text("Ohne Ortsangabe « zurück"))

    def test_titel_rueckfall_und_liste(self):
        filialen = _filialen_aus_liste("Veranstaltungen in der Bücherei Rath Veranstaltungen in der Kinderbücherei Hassels")
        self.assertEqual(filialen, {"Rath", "Hassels"})
        self.assertEqual(filiale_aus_titel("Geschichtenzeit in Rath", filialen), "Stadtbücherei Rath")
        self.assertIsNone(filiale_aus_titel("Lesung in Japan", filialen))


if __name__ == "__main__":
    unittest.main()
