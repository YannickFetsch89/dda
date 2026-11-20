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


def _backoff(retry_after: Optional[str], versuch: int) -> float:
    """Wartezeit nach HTTP 429: Retry-After (Sekunden, höchstens 120), sonst 10, 20, 40 Sekunden."""
    try:
        if retry_after is not None:
            return min(max(float(retry_after), 1.0), 120.0)
    except ValueError:
        pass   # Datumsangabe statt Sekunden → Standard-Backoff
    return 10.0 * (2 ** versuch)


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
                # HTTP 429: exponentielles Backoff (Projektregel), Retry-After beachten, höchstens 3 weitere Versuche
                for versuch in range(3):
                    if response.status_code != 429:
                        break
                    pause = _backoff(response.headers.get("Retry-After"), versuch)
                    if logger:
                        logger.warning("HTTP 429 bei %s – warte %.0f s (Versuch %d von 3)", url, pause, versuch + 1)
                    time.sleep(pause)
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
