"""
http_client.py – DiesDasDüsseldorf
Gemeinsamer HTTP-Hilfsclient für alle Scraper.
Kapselt Rate Limiting, Standard-Browser-Headers und einheitliche Fehlerbehandlung.
Erstellt: 2026-02-24
"""
import time
from typing import Optional

import httpx

# Standard Browser-Headers für alle Scraper-Anfragen
STANDARD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}


def seite_abrufen(url: str, logger=None, wartezeit: float = 2.0) -> Optional[str]:
    """
    Ruft eine URL ab und gibt den HTML-Inhalt zurück.
    Enthält Rate Limiting, Standard-Headers und Fehlerbehandlung.

    Args:
        url:       Ziel-URL die abgerufen werden soll
        logger:    Logger-Instanz für Fehlermeldungen (optional)
        wartezeit: Wartezeit in Sekunden vor dem Request (Rate Limiting)

    Returns:
        HTML-Inhalt als String oder None bei Fehler
    """
    time.sleep(wartezeit)  # Rate Limiting

    try:
        with httpx.Client(headers=STANDARD_HEADERS, timeout=30, follow_redirects=True) as client:
            try:
                response = client.get(url)
                response.raise_for_status()
                return response.text
            except httpx.TimeoutException:
                if logger:
                    logger.error("Timeout beim Abrufen von %s", url)
                return None
            except httpx.HTTPStatusError as fehler:
                if logger:
                    logger.error(
                        "HTTP Fehler %s beim Abrufen von %s",
                        fehler.response.status_code, url,
                    )
                return None
    except Exception as fehler:
        if logger:
            logger.error("Unerwarteter Fehler beim Abrufen von %s: %s", url, str(fehler))
        return None
