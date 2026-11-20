"""Tests: HTTP 429 mit exponentiellem Backoff in seite_abrufen (Projektregel; Cursor-Komplettprüfung 20.11.2026)."""
import unittest
from unittest import mock

import httpx

from scraper.utils import http_client


def _antwort(status: int, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(status, headers=headers or {}, text="<html>ok</html>", request=httpx.Request("GET", "https://x.test"))


class Backoff429Test(unittest.TestCase):
    def test_wartezeiten(self):
        self.assertEqual(http_client._backoff("5", 0), 5.0)
        self.assertEqual(http_client._backoff("9999", 0), 120.0)
        self.assertEqual(http_client._backoff(None, 0), 10.0)
        self.assertEqual(http_client._backoff("Wed, 21 Oct 2026 07:28:00 GMT", 2), 40.0)

    def test_429_dann_erfolg(self):
        antworten = [_antwort(429, {"Retry-After": "3"}), _antwort(200)]
        with mock.patch.object(httpx.Client, "get", side_effect=antworten) as get, \
                mock.patch.object(http_client.time, "sleep") as schlaf:
            self.assertEqual(http_client.seite_abrufen("https://x.test"), "<html>ok</html>")
        self.assertEqual(get.call_count, 2)
        self.assertEqual([c.args[0] for c in schlaf.call_args_list], [2.0, 3.0])

    def test_dauerhaft_429(self):
        with mock.patch.object(httpx.Client, "get", side_effect=[_antwort(429)] * 4) as get, \
                mock.patch.object(http_client.time, "sleep"):
            self.assertIsNone(http_client.seite_abrufen("https://x.test"))
        self.assertEqual(get.call_count, 4)


if __name__ == "__main__":
    unittest.main()
