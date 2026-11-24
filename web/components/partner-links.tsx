// Kennzeichnung der Partner-Links (Plan docs/plan-quellen-ausbau-2026-11-23.md, 5.5.5, Schritt P2): Abschnitt auf
// /ueber (du, Anker #partner-links) und Punkt in der Datenschutzerklärung (Sie). Beide erscheinen nur, wenn
// mindestens ein Partnerprogramm wirklich Links umbaut, und nennen nur diese Programme.
// Texte: Entwurf docs/partner-links-texte-2026-11-24.md – vor PARTNERLINKS_AKTIV=1 vom Anwalt freizugeben.
import { aktivePartner, aufzaehlung } from "@/lib/tickets";

function anbieterTeile(): { ticket: string[]; touren: string[] } {
  const p = aktivePartner();
  return {
    ticket: [
      ...(p.awin ? ["Eventim", "Reservix", "ADticket"] : []),
      ...(p.ticketmaster ? ["Ticketmaster"] : []),
    ],
    touren: [...(p.tiqets ? ["Tiqets"] : []), ...(p.getyourguide ? ["GetYourGuide"] : [])],
  };
}

/** Abschnitt auf /ueber (du-Ansprache wie die Konto-Seiten). */
export function PartnerLinksUeber() {
  const { ticket, touren } = anbieterTeile();
  const alle = [...ticket, ...touren];
  if (!alle.length) return null;
  return (
    <section id="partner-links" className="container ue-abschnitt">
      <span className="overline overline--gold">Transparenz</span>
      <h2 className="d ue-h2">Partner-Links</h2>
      <p>
        Manche Ticket-Buttons auf unseren Eventseiten sind Partner-Links. Du erkennst sie am Sternchen: „Tickets*“. Kaufst
        du über so einen Link ein Ticket, bekommen wir vom Anbieter eine kleine Provision. Für dich ändert sich nichts –
        der Preis bleibt gleich.
      </p>
      <p>
        Welche Events wir zeigen und empfehlen, hängt nie an einer Provision. Den Ticket-Button wählen wir nach einer
        festen Regel: zuerst der Ticketverkauf, den das Veranstaltungshaus selbst nennt, sonst der Ticketanbieter, der
        das Event führt. Mehrere Anbieter mit Preisen nebeneinander zeigen wir nicht. Im Magazin setzen wir keine
        Partner-Links.
      </p>
      <p>
        Unsere Partner: {aufzaehlung(alle)}. Wir setzen dafür keine eigenen Cookies und zählen keine Klicks. Was nach dem
        Klick passiert, regelt der Anbieter – mehr dazu in der <a href="/datenschutz#partner-links">Datenschutzerklärung</a>.
      </p>
    </section>
  );
}

/** Punkt in Abschnitt 9 „Externe Inhalte und Drittanbieter“ der Datenschutzerklärung (Sie-Form). */
export function PartnerLinksDatenschutz() {
  const p = aktivePartner();
  const { ticket, touren } = anbieterTeile();
  const alle = [...ticket, ...touren];
  if (!alle.length) return null;
  const netzwerke = [
    ...(p.awin ? ["Awin (AWIN AG, Berlin) für Eventim, Reservix und ADticket"] : []),
    ...(p.ticketmaster ? ["Impact (Impact Tech, Inc., USA) für Ticketmaster"] : []),
  ];
  return (
    <li id="partner-links">
      <b>Partner-Links zu Ticketanbietern:</b> Einige Ticket-Buttons auf Event-Seiten sind Partner-Links, gekennzeichnet
      mit einem Sternchen („Tickets*“). Sie führen zu {aufzaehlung(alle)}
      {netzwerke.length ? `; vermittelt werden sie über die Partnernetzwerke ${aufzaehlung(netzwerke)}` : ""}. Beim
      Aufruf unserer Seiten wird keine Verbindung zu diesen Anbietern aufgebaut; wir setzen dafür keine Cookies und
      erfassen keine Klicks. Erst wenn Sie auf einen solchen Link klicken, werden Sie
      {netzwerke.length ? " über den Server des Partnernetzwerks" : ""} auf die Seite des Anbieters weitergeleitet.
      Dabei werden Ihre IP-Adresse und technische Angaben Ihres Browsers übermittelt, und das Netzwerk bzw. der
      Anbieter kann Cookies oder ähnliche Techniken einsetzen, um einen Kauf unserer Website zuzuordnen. Dafür sind
      das Netzwerk und der Anbieter selbst verantwortlich; Einzelheiten finden Sie in deren Datenschutzerklärungen.
      Wir erhalten von den Netzwerken nur zusammengefasste Angaben zu Klicks und Verkäufen, keine Angaben zu Ihrer
      Person. Rechtsgrundlage für das Bereitstellen der Links ist unser berechtigtes Interesse an der Finanzierung
      dieses Angebots (Art. 6 Abs. 1 lit. f DSGVO).
    </li>
  );
}
