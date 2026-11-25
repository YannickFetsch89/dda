// Partner-Links (Plan docs/plan-quellen-ausbau-2026-11-23.md, 5.5.5, Schritt P2)
import { describe, expect, it } from "vitest";
import { aktivePartner, anbieterVon, aufzaehlung, ohneFremdeKennung, partnerKonfig, partnerLink, partnerLinksAktiv } from "@/lib/tickets";

const AN = partnerKonfig({
  PARTNERLINKS_AKTIV: "1",
  AWIN_PUBLISHER_ID: "123456",
  TICKETMASTER_PARTNER_OK: "0",
  TICKETMASTER_PARTNER_VORLAGE: "https://ticketmaster.evyy.net/c/1/2/3?u={url}",
  TIQETS_PARTNER_ID: "ddd",
  GYG_PARTNER_ID: "ABC123",
});

describe("Konfiguration", () => {
  it("ohne Schalter alles aus", () => {
    const aus = partnerKonfig({ AWIN_PUBLISHER_ID: "123456" });
    expect(aus.aktiv).toBe(false);
    expect(partnerLink("https://www.eventim.de/event/x-1/", aus)).toEqual({ url: "https://www.eventim.de/event/x-1/", partner: false });
    expect(partnerLinksAktiv(aus)).toBe(false);
  });

  it("ungültige Kennungen und Vorlagen werden ignoriert", () => {
    const k = partnerKonfig({ PARTNERLINKS_AKTIV: "true", AWIN_PUBLISHER_ID: "12 34", TICKETMASTER_PARTNER_VORLAGE: "http://x/?u={url}" });
    expect(k.awinPublisher).toBeNull();
    expect(k.ticketmasterVorlage).toBeNull();
    expect(partnerLinksAktiv(k)).toBe(false);
  });
});

describe("Anbieter erkennen", () => {
  it("nur Hauptdomains", () => {
    expect(anbieterVon("https://www.eventim.de/event/x/")).toBe("eventim");
    expect(anbieterVon("https://www.reservix.de/tickets-x/e1")).toBe("reservix");
    expect(anbieterVon("https://pitcher.reservix.de/e/1")).toBeNull(); // Haus-Shop auf Subdomain
    expect(anbieterVon("https://www.eventim-light.com/de/a/1")).toBeNull();
    expect(anbieterVon("https://webshop.operamrhein.de/eventim.webshop/x")).toBeNull();
    expect(anbieterVon("kaputt")).toBeNull();
  });
});

describe("Partner-Link bauen", () => {
  it("Awin-Deeplink mit Programm, Publisher und Ziel ohne fremde Kennung", () => {
    const l = partnerLink("https://www.eventim.de/noapp/event/x-21016047/?affiliate=SAV&utm_campaign=Savoy&utm_source=SAV", AN);
    expect(l.partner).toBe(true);
    const u = new URL(l.url);
    expect(u.origin + u.pathname).toBe("https://www.awin1.com/cread.php");
    expect(u.searchParams.get("awinmid")).toBe("11388");
    expect(u.searchParams.get("awinaffid")).toBe("123456");
    expect(u.searchParams.get("ued")).toBe("https://www.eventim.de/noapp/event/x-21016047/");
    expect(new URL(partnerLink("https://www.adticket.de/e.html", AN).url).searchParams.get("awinmid")).toBe("18490");
    expect(new URL(partnerLink("https://www.reservix.de/e/1", AN).url).searchParams.get("awinmid")).toBe("31293");
  });

  it("Ticketmaster erst mit Bestätigung", () => {
    expect(partnerLink("https://www.ticketmaster.de/event/1", AN).partner).toBe(false);
    const ok = partnerKonfig({ PARTNERLINKS_AKTIV: "1", TICKETMASTER_PARTNER_OK: "1", TICKETMASTER_PARTNER_VORLAGE: "https://ticketmaster.evyy.net/c/1/2/3?u={url}" });
    expect(partnerLink("https://www.ticketmaster.de/event/1", ok)).toEqual({
      url: "https://ticketmaster.evyy.net/c/1/2/3?u=https%3A%2F%2Fwww.ticketmaster.de%2Fevent%2F1",
      partner: true,
    });
  });

  it("Tiqets und GetYourGuide mit Partner-Parameter", () => {
    expect(partnerLink("https://www.tiqets.com/de/x?partner=fremd", AN).url).toBe("https://www.tiqets.com/de/x?partner=ddd");
    expect(partnerLink("https://www.getyourguide.de/x-t1/", AN).url).toBe("https://www.getyourguide.de/x-t1/?partner_id=ABC123");
  });

  it("unbekannte Anbieter und eigene Shops bleiben normal", () => {
    expect(partnerLink("https://tickets.kommoedchen.de/e/1", AN)).toEqual({ url: "https://tickets.kommoedchen.de/e/1", partner: false });
    expect(partnerLink("javascript:alert(1)", AN).partner).toBe(false);
  });

  it("fremde Kennungen entfernen, eigene Parameter behalten", () => {
    expect(ohneFremdeKennung("https://x.de/e?id=5&utm_medium=dp&affiliate=SAV&ref=abc")).toBe("https://x.de/e?id=5");
  });
});

describe("Kennzeichnung", () => {
  it("nennt nur aktive Programme", () => {
    expect(aktivePartner(AN)).toEqual({ awin: true, ticketmaster: false, tiqets: true, getyourguide: true });
    expect(aufzaehlung(["A", "B", "C"])).toBe("A, B und C");
    expect(aufzaehlung(["A"])).toBe("A");
  });
});

describe("Cockpit-Kennzahl Ticket-Links", () => {
  it("zählt Ticket-Links und partnerfähige je Anbieter", async () => {
    const { ticketLinkKennzahl } = await import("@/lib/tickets");
    const k = ticketLinkKennzahl([
      { ticket_url: "https://www.eventim.de/e/1" }, { ticket_url: "https://www.eventim.de/e/2" },
      { ticket_url: "https://www.reservix.de/e/3" }, { ticket_url: "https://tickets.kommoedchen.de/x" },
      { ticket_url: null }, {},
    ]);
    expect(k).toEqual({ mit: 4, von: 6, partnerfaehig: 3, jeAnbieter: [{ anbieter: "eventim", anzahl: 2 }, { anbieter: "reservix", anzahl: 1 }] });
  });
});

describe("URLs mit Benutzername (Cursor-Gesamtprüfung 25.11.)", () => {
  it("werden nie als Ticket-Ziel oder Admin-Eingabe angenommen", async () => {
    const { sichereUrl } = await import("@/lib/orte");
    const { ticketZiel } = await import("@/lib/ticket-button");
    const { eingabenPruefen } = await import("@/lib/admin/events");
    expect(sichereUrl("https://www.eventim.de@evil.com/phish")).toBeNull();
    expect(sichereUrl("https://www.eventim.de/e/1")).toBe("https://www.eventim.de/e/1");
    expect(ticketZiel({ quelle_name: "zakk", quelle_url: "https://www.zakk.de/e", ticket_url: "https://www.eventim.de@evil.com/x" })).toBeNull();
    expect(eingabenPruefen({ ticket_url: "https://user:pw@www.reservix.de/e" }).ok).toBe(false);
  });
});
