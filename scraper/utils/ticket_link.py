"""
ticket_link.py – DiesDasDüsseldorf
Baustein: Ticket-Link des Hauses erkennen (Plan docs/plan-quellen-ausbau-2026-11-23.md, 5.5.2, Schritt P1).

Venue-Scraper speichern im Feld `ticket_url` den Link zum Ticketverkauf, den das Haus selbst nennt – beim Anbieter
(Eventim, Reservix, ADticket, Ticketmaster …) oder im eigenen Ticketshop (tickets.<haus>.de). `quelle_url` bleibt die
Seite des Termins. Die Website baut daraus später (Schritt P2) bei bekanntem Anbieter einen Partner-Link; bis dahin
ist es ein normaler Link.

ticket_link(url, basis)   → absolute URL, wenn sie zu einem Ticketverkauf führt, sonst None
ticket_link_aus(element, basis) → erster Ticket-Link unter einem BeautifulSoup-Element
anbieter(url)             → Anzeigename des Anbieters („Eventim“, „Reservix“ … oder „eigener Shop“) für die Kennzahl
"""
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

# Domain (ohne „www.“, Endung zählt mit) → Anbieter. Reihenfolge egal; Subdomains zählen mit (nachtresidenz.ticket.io).
ANBIETER: dict[str, str] = {
    "eventim.de": "Eventim",
    "eventim-light.com": "Eventim",
    "eventim.com": "Eventim",
    "reservix.de": "Reservix",
    "reservix.net": "Reservix",
    "adticket.de": "ADticket",
    "ticketmaster.de": "Ticketmaster",
    "ticketmaster.com": "Ticketmaster",
    "ticket.io": "ticket.io",
    "neanderticket.de": "Neanderticket",
    "yesticket.org": "YesTicket",
    "stagedates.com": "Stagedates",
    "eventbrite.de": "Eventbrite",
    "eventbrite.com": "Eventbrite",
    "pretix.eu": "pretix",
    "tixforgigs.com": "TixforGigs",
    "westticket.de": "Westticket",
    "ticket-regional.de": "Ticket Regional",
    "myticket.de": "myticket",
    "vivenushop.com": "vivenu",
    "vivenu.com": "vivenu",
    "tickettailor.com": "Ticket Tailor",
    "rodrigue.de": "Rodrigue",
    "fienta.com": "Fienta",
    # Gefunden bei d.live und Mitsubishi Electric HALLE (Ticket-Button des Hauses, 24.11.2026)
    "livenation.de": "Live Nation",
    "koelnticket.de": "KölnTicket",
    "ticket-onlineshop.com": "ticket-onlineshop",
    "printyourticket.de": "printyourticket",
    "online-ticket.de": "online-ticket",
    "tickethead.io": "Tickethead",
    "atgtickets.com": "ATG Tickets",
    "rausgegangen.de": None,  # kein Ticketverkauf des Hauses, sondern Aggregator – nie als ticket_url
}

# Eigener Ticketshop: Host beginnt mit „ticket(s)“, „karten“ oder „shop“ (tickets.apollo-variete.com,
# karten.tas-neuss.de)
_EIGENER_SHOP = re.compile(r"^(?:www\.)?(?:e?tickets?|karten|shop|webshop)\.", re.IGNORECASE)


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def _anbieter_domain(host: str) -> Optional[str]:
    """Passende Domain aus ANBIETER für einen Host (auch Subdomains), sonst None."""
    for domain in ANBIETER:
        if host == domain or host.endswith("." + domain):
            return domain
    return None


def anbieter(url: Optional[str]) -> Optional[str]:
    """Anzeigename des Ticketanbieters einer URL – „eigener Shop“ für tickets.<haus>, None für keinen Ticket-Link."""
    host = _host(url or "")
    if not host:
        return None
    domain = _anbieter_domain(host)
    if domain:
        return ANBIETER[domain]
    return "eigener Shop" if _EIGENER_SHOP.match(host) else None


def ticket_link(url: Optional[str], basis: Optional[str] = None) -> Optional[str]:
    """Absolute http(s)-URL, wenn sie zu einem Ticketverkauf führt (Anbieter-Domain oder eigener Ticketshop)."""
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if url.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None
    absolut = urljoin(basis, url) if basis else url
    if not absolut.startswith(("http://", "https://")):
        return None
    return absolut if anbieter(absolut) else None


def ticket_link_aus(element, basis: Optional[str] = None) -> Optional[str]:
    """Erster Ticket-Link (<a href>) unter einem BeautifulSoup-Element, sonst None."""
    if element is None:
        return None
    for a in element.find_all("a", href=True):
        treffer = ticket_link(a["href"], basis)
        if treffer:
            return treffer
    return None
