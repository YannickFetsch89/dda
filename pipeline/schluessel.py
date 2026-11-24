"""
schluessel.py – DiesDasDüsseldorf
Gemeinsame Schlüssel (Secrets) wie auf der Website bereinigen: deploy.yml schreibt sie mit tr -d ' \r\n\t'
nach web/.env.local, web/lib/schluessel.ts entfernt dieselben Zeichen. Livetest 24.11.2026: Ein Zeilenumbruch im
Newsletter-Secret machte alle Bestätigungslinks ungültig.
"""
from __future__ import annotations

from typing import Optional

LEERRAUM = " \r\n\t"  # dieselben Zeichen wie tr -d in deploy.yml


def bereinigen(roh: Optional[str]) -> str:
    """Schlüssel ohne Leerzeichen, Zeilenumbrüche und Tabs (auch mitten im Wert)."""
    return "".join(z for z in (roh or "") if z not in LEERRAUM)
