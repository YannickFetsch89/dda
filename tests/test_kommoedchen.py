"""Tests für den Kom(m)ödchen-Abruf über unseren Server (python -m unittest tests.test_kommoedchen).
Die Website weist GitHub-Server ab (Sucuri, 503); der Workflow legt die Seite in data/kommoedchen/spielplan.html."""
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from scraper.tier2 import kommoedchen

SEITE = """<html><body>
<div class="day-event-wrapper" data-date="2099-12-01">
  <a href="/programm/ensemble/"><h3>Kom(m)ödchen-Ensemble: Test</h3></a>
  <span class="time">20:00 Uhr</span>
</div>
</body></html>"""


class VorabTest(unittest.TestCase):
    def setUp(self):
        self.ordner = tempfile.TemporaryDirectory()
        self.datei = Path(self.ordner.name) / "spielplan.html"

    def tearDown(self):
        self.ordner.cleanup()

    def test_frische_datei_wird_gelesen(self):
        self.datei.write_text(SEITE, encoding="utf-8")
        self.assertEqual(kommoedchen._vorab_html(self.datei), SEITE)

    def test_fehlend_alt_oder_leer_gibt_none(self):
        self.assertIsNone(kommoedchen._vorab_html(self.datei))                 # fehlt
        self.datei.write_text("", encoding="utf-8")
        self.assertIsNone(kommoedchen._vorab_html(self.datei))                 # leer (curl fehlgeschlagen)
        self.datei.write_text(SEITE, encoding="utf-8")
        alt = time.time() - kommoedchen.VORAB_HOECHSTALTER_S - 60
        os.utime(self.datei, (alt, alt))
        self.assertIsNone(kommoedchen._vorab_html(self.datei))                 # zu alt

    def test_scrape_ruft_nicht_direkt_ab_wenn_datei_da(self):
        with mock.patch.object(kommoedchen, "_vorab_html", return_value=SEITE), \
                mock.patch.object(kommoedchen, "seite_abrufen", side_effect=AssertionError("kein Direktabruf")):
            kommoedchen.scrape()

    def test_scrape_ohne_datei_ruft_direkt_ab(self):
        with mock.patch.object(kommoedchen, "_vorab_html", return_value=None), \
                mock.patch.object(kommoedchen, "seite_abrufen", return_value=SEITE) as abruf:
            kommoedchen.scrape()
        abruf.assert_called_once()


def _spielplan(tag: str) -> str:
    """Auszug aus dem echten Spielplan (24.11.2026): ein Termin mit, einer ohne Ticket-Button."""
    return f"""<html><body>
<div class="day-event-wrapper" data-date="{tag}"><div class="day-event-item">
  <div class="event--date-time"><span class="date-time">20:00 Uhr</span></div>
  <div class="event--description-wrapper"><div class="description-details"><div class="description-titles">
    <a href="https://www.kommoedchen.de/spielplan/noe_eine_entgleisung/">
      <div class="subtitle">Kom(m)ödchen-Ensemble</div><div class="title">Noë. Eine Entgleisung</div></a>
  </div></div></div>
  <div class="event--ticket"><a class="btn default external-events" target="_blank"
    href="https://tickets.kommoedchen.de/selection/event/seat?perfId=10229867157761&amp;productId=10229401280598&amp;lang=de">Tickets</a></div>
</div></div>
<div class="day-event-wrapper" data-date="{tag}"><div class="day-event-item">
  <div class="event--date-time"><span class="date-time">18:00 Uhr</span></div>
  <div class="description-titles"><a href="/spielplan/ausverkauft/"><div class="title">Ausverkauft</div></a></div>
</div></div>
</body></html>"""


class TicketUrlTest(unittest.TestCase):
    def test_ticket_button_wird_ticket_url(self):
        from datetime import date, timedelta
        tag = (date.today() + timedelta(days=3)).isoformat()
        with mock.patch.object(kommoedchen, "_vorab_html", return_value=_spielplan(tag)):
            events = kommoedchen.scrape()
        self.assertEqual(len(events), 2)
        mit, ohne = events
        self.assertEqual(mit["ticket_url"], "https://tickets.kommoedchen.de/selection/event/seat"
                                            "?perfId=10229867157761&productId=10229401280598&lang=de")
        self.assertEqual(mit["quelle_url"], "https://www.kommoedchen.de/spielplan/noe_eine_entgleisung/")
        self.assertIsNone(ohne["ticket_url"])


if __name__ == "__main__":
    unittest.main()
