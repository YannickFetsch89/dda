"""Tests für den DEG-Spielplan (python -m unittest tests.test_deg). Seit etwa 18.11.2026 sind die Spielkarten
<div>-Elemente statt <a>; der Scraper fand dadurch 0 Heimspiele."""
import unittest
from datetime import date

from scraper.tier3.deg import _heimspiele_aus_spielplan


def karte(tag, klassen, heim, gast, datum, spiel_id, link=None):
    href = f' href="{link}"' if tag == "a" and link else ""
    innen = f'<a href="{link}">Tickets</a>' if tag == "div" and link else ""
    return (f'<{tag} class="scoreboard-item {klassen}" data-game-id="{spiel_id}"{href}>'
            f'<span class="sb-gameday">Spieltag 20</span>'
            f'<div class="sb-name">{heim}</div><div class="sb-name">{gast}</div>'
            f'<div class="sb-date">{datum}</div>{innen}</{tag}>')


SEITE = "".join([
    karte("div", "is-home", "DEG", "SCB", "29.11.2026 17.00 Uhr", "aaa",
          "https://www.deg-eishockey.de/gamecenter/aaa/"),
    karte("div", "is-home", "DEG", "EVL", "01.12.2026 19.30 Uhr", "bbb",
          "https://www.ticket-onlineshop.com/ols/deg/event/677002"),
    karte("div", "is-away", "FRB", "DEG", "27.11.2026 19.30 Uhr", "ccc"),
    karte("div", "is-completed is-home", "DEG", "ECK", "20.11.2026 19.30 Uhr", "ddd"),
    karte("a", "is-home", "DEG", "MEM", "23.12.2026 19.30 Uhr", "eee", "/gamecenter/eee/"),
])


class DegTest(unittest.TestCase):
    def test_heimspiele_aus_div_und_a(self):
        spiele = _heimspiele_aus_spielplan(SEITE, date(2026, 11, 23), date(2027, 1, 31))
        self.assertEqual([(s["datum"], s["gast_kuerzel"]) for s in spiele],
                         [("2026-11-29", "SCB"), ("2026-12-01", "EVL"), ("2026-12-23", "MEM")])
        self.assertEqual(spiele[0]["uhrzeit"], "17:00")
        self.assertEqual(spiele[0]["url"], "https://www.deg-eishockey.de/gamecenter/aaa/")
        self.assertEqual(spiele[2]["url"], "https://www.deg-eishockey.de/gamecenter/eee/")


if __name__ == "__main__":
    unittest.main()
