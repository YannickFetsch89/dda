// Partner-Links für Ticket-Buttons (Plan docs/plan-quellen-ausbau-2026-11-23.md, 5.5.5, Schritt P2).
// Erkennt den Anbieter an der Domain und baut den Partner-Link aus den Variablen in web/.env.local (gesetzt vom
// Deploy aus den GitHub-Variablen). Ohne Schalter PARTNERLINKS_AKTIV=1 oder ohne Kennung bleibt jeder Link normal.
// Ticketmaster zusätzlich erst mit TICKETMASTER_PARTNER_OK=1 (schriftliche Bestätigung, 5.5.1).
// Kein eigenes Klick-Tracking, keine Cookies bei uns; ausgewertet wird in den Netzwerk-Konten.

/** Awin-Programme (öffentliche Programm-IDs, Plan 5.5) */
export const AWIN_PROGRAMME = { eventim: "11388", reservix: "31293", adticket: "18490" } as const;

export type Anbieter = keyof typeof AWIN_PROGRAMME | "ticketmaster" | "tiqets" | "getyourguide";

/**
 * Hosts je Anbieter – bewusst nur die Hauptdomains. Weiße Shops auf Subdomains (z. B. pitcher.reservix.de,
 * webshop.operamrhein.de/eventim.webshop) und Eventim Light gehören nicht sicher zum Partnerprogramm und bleiben
 * normale Links.
 */
const HOSTS: Record<Anbieter, string[]> = {
  eventim: ["eventim.de", "www.eventim.de"],
  reservix: ["reservix.de", "www.reservix.de"],
  adticket: ["adticket.de", "www.adticket.de"],
  ticketmaster: ["ticketmaster.de", "www.ticketmaster.de"],
  tiqets: ["tiqets.com", "www.tiqets.com"],
  getyourguide: ["getyourguide.de", "www.getyourguide.de", "getyourguide.com", "www.getyourguide.com"],
};

/** Fremde Kennungen, die ein Haus an seinen Link hängt (Savoy: ?affiliate=SAV&utm_…) – vor dem Partner-Link entfernen */
const FREMDE_KENNUNG = /^(utm_.*|affiliate|affiliateid|aff|affid|awc|awinaffid|awinmid|clickref|irclickid|irgwc|partner|partner_id|ref|fbclid|gclid)$/i;

export interface PartnerKonfig {
  aktiv: boolean;
  awinPublisher: string | null;
  ticketmasterOk: boolean;
  /** Impact-Deeplink-Vorlage mit {url}, z. B. https://ticketmaster.evyy.net/c/<ID>/<Ad>/<Programm>?u={url} */
  ticketmasterVorlage: string | null;
  tiqetsPartner: string | null;
  gygPartner: string | null;
}

const an = (wert: string | undefined) => ["1", "true"].includes((wert ?? "").trim().toLowerCase());
const kennung = (wert: string | undefined) => {
  const w = (wert ?? "").trim();
  return /^[A-Za-z0-9_-]{1,40}$/.test(w) ? w : null;
};

/** Konfiguration aus der Umgebung (web/.env.local). */
export function partnerKonfig(env: Record<string, string | undefined> = process.env): PartnerKonfig {
  const vorlage = (env.TICKETMASTER_PARTNER_VORLAGE ?? "").trim();
  return {
    aktiv: an(env.PARTNERLINKS_AKTIV),
    awinPublisher: kennung(env.AWIN_PUBLISHER_ID),
    ticketmasterOk: an(env.TICKETMASTER_PARTNER_OK),
    ticketmasterVorlage: /^https:\/\/[^\s{}]+\{url\}[^\s{}]*$/.test(vorlage) ? vorlage : null,
    tiqetsPartner: kennung(env.TIQETS_PARTNER_ID),
    gygPartner: kennung(env.GYG_PARTNER_ID),
  };
}

/** Anbieter einer URL (nur Hauptdomains), sonst null. */
export function anbieterVon(url: string): Anbieter | null {
  let host: string;
  try {
    host = new URL(url).hostname.toLowerCase();
  } catch {
    return null;
  }
  for (const [anbieter, hosts] of Object.entries(HOSTS) as [Anbieter, string[]][]) {
    if (hosts.includes(host)) return anbieter;
  }
  return null;
}

/** URL ohne fremde Partner-/Kampagnen-Kennungen (das Ziel des Partner-Links). */
export function ohneFremdeKennung(url: string): string {
  try {
    const u = new URL(url);
    for (const schluessel of [...u.searchParams.keys()]) if (FREMDE_KENNUNG.test(schluessel)) u.searchParams.delete(schluessel);
    return u.toString();
  } catch {
    return url;
  }
}

export interface TicketLink {
  url: string;
  /** true = Partner-Link: Kennzeichnung „Tickets*“ und rel="sponsored noopener" */
  partner: boolean;
}

/** Baut aus einem Ticket-Link den Partner-Link, wenn Schalter und Kennung es erlauben; sonst den Link unverändert. */
export function partnerLink(url: string, konfig: PartnerKonfig = partnerKonfig()): TicketLink {
  const normal = { url, partner: false };
  if (!konfig.aktiv || !/^https?:\/\//i.test(url)) return normal;
  const anbieter = anbieterVon(url);
  if (!anbieter) return normal;
  const ziel = ohneFremdeKennung(url);
  if (anbieter === "eventim" || anbieter === "reservix" || anbieter === "adticket") {
    if (!konfig.awinPublisher) return normal;
    const mid = AWIN_PROGRAMME[anbieter];
    return { url: `https://www.awin1.com/cread.php?awinmid=${mid}&awinaffid=${konfig.awinPublisher}&ued=${encodeURIComponent(ziel)}`, partner: true };
  }
  if (anbieter === "ticketmaster") {
    if (!konfig.ticketmasterOk || !konfig.ticketmasterVorlage) return normal;
    return { url: konfig.ticketmasterVorlage.replace("{url}", encodeURIComponent(ziel)), partner: true };
  }
  const [param, wert] = anbieter === "tiqets" ? ["partner", konfig.tiqetsPartner] : ["partner_id", konfig.gygPartner];
  if (!wert) return normal;
  const u = new URL(ziel);
  u.searchParams.set(param, wert);
  return { url: u.toString(), partner: true };
}

/** Ist irgendein Partner-Link möglich? (Abschnitt „Partner-Links“ auf /ueber und in der Datenschutzerklärung) */
export function partnerLinksAktiv(konfig: PartnerKonfig = partnerKonfig()): boolean {
  return konfig.aktiv && !!(konfig.awinPublisher || (konfig.ticketmasterOk && konfig.ticketmasterVorlage) || konfig.tiqetsPartner || konfig.gygPartner);
}

/** Namen der aktiven Partnerprogramme für /ueber und die Datenschutzerklärung (nur, was wirklich Links umbaut). */
export function aktivePartner(konfig: PartnerKonfig = partnerKonfig()): { awin: boolean; ticketmaster: boolean; tiqets: boolean; getyourguide: boolean } {
  return {
    awin: konfig.aktiv && !!konfig.awinPublisher,
    ticketmaster: konfig.aktiv && konfig.ticketmasterOk && !!konfig.ticketmasterVorlage,
    tiqets: konfig.aktiv && !!konfig.tiqetsPartner,
    getyourguide: konfig.aktiv && !!konfig.gygPartner,
  };
}

/** Aufzählung „A, B und C“ */
export function aufzaehlung(teile: string[]): string {
  return teile.length <= 1 ? (teile[0] ?? "") : `${teile.slice(0, -1).join(", ")} und ${teile[teile.length - 1]}`;
}

/**
 * Kennzahl fürs Admin-Cockpit (Plan Quellen-Ausbau P1/P2): Wie viele kommende Events haben einen Ticket-Link des
 * Hauses, und wie viele davon könnten ein Partner-Link werden (Hauptdomain eines Partnerprogramms)?
 */
export function ticketLinkKennzahl(events: { ticket_url?: string | null }[]): {
  mit: number;
  von: number;
  partnerfaehig: number;
  jeAnbieter: { anbieter: Anbieter; anzahl: number }[];
} {
  const zaehler = new Map<Anbieter, number>();
  let mit = 0;
  for (const e of events) {
    if (!e.ticket_url) continue;
    mit++;
    const a = anbieterVon(e.ticket_url);
    if (a) zaehler.set(a, (zaehler.get(a) ?? 0) + 1);
  }
  const jeAnbieter = [...zaehler].map(([anbieter, anzahl]) => ({ anbieter, anzahl })).sort((a, b) => b.anzahl - a.anzahl);
  return { mit, von: events.length, partnerfaehig: jeAnbieter.reduce((s, x) => s + x.anzahl, 0), jeAnbieter };
}
