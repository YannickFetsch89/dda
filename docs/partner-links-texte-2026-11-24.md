# Partner-Links – Texte zur Freigabe durch den Anwalt (Plan Quellen-Ausbau 5.5.5, Schritt P2)

Stand 24.11.2026. Die Texte stehen im Code (`web/components/partner-links.tsx`, Eventseite
`web/app/event/[kategorie]/[slug]/page.tsx`) und erscheinen **erst**, wenn die GitHub-Variable `PARTNERLINKS_AKTIV=1`
gesetzt ist und mindestens eine Partner-Kennung hinterlegt ist. Sie nennen automatisch nur die Programme, die wirklich
aktiv sind. Unten die Fassung, wenn **alle** Programme aktiv sind.

**Bitte vor dem Einschalten freigeben:** (1) Kennzeichnung am Button, (2) Abschnitt auf /ueber, (3) Punkt in der
Datenschutzerklärung. Änderungswünsche bitte direkt im Text markieren.

## Was technisch passiert

- Ein Ticket-Button zeigt bei Eventim, Reservix und ADticket auf einen Awin-Link
  (`https://www.awin1.com/cread.php?awinmid=<Programm>&awinaffid=<unsere ID>&ued=<Ticketseite>`), bei Ticketmaster auf
  einen Impact-Link (erst nach schriftlicher Bestätigung durch Ticketmaster), bei Tiqets/GetYourGuide auf die Seite mit
  unserer Partner-Kennung im Link.
- Wir setzen **keine** eigenen Cookies, zählen **keine** Klicks und binden **keine** Skripte der Netzwerke ein. Erst
  beim Klick verbindet sich der Browser mit dem Netzwerk bzw. Anbieter.
- Die Links haben `rel="sponsored"`. Im Magazin gibt es keine Partner-Links. Die Auswahl des Buttons folgt einer
  festen Regel (zuerst der Ticketverkauf, den das Haus nennt, sonst der Ticketanbieter, der das Event führt), nicht
  der Provision; nie mehrere Anbieter mit Preisen nebeneinander.

## (1) Kennzeichnung am Button (Eventseite, du)

Button „Tickets\*“ (bzw. „Zur Veranstalter-Seite\*“, wenn die Hauptquelle selbst ein Ticketanbieter ist), direkt
darunter klein:

> \*Partner-Link: Kaufst du darüber, bekommen wir eine Provision. Der Preis bleibt gleich. [Mehr dazu](/ueber#partner-links)

## (2) Abschnitt „Partner-Links“ auf /ueber (du)

> **Partner-Links**
>
> Manche Ticket-Buttons auf unseren Eventseiten sind Partner-Links. Du erkennst sie am Sternchen: „Tickets\*“. Kaufst
> du über so einen Link ein Ticket, bekommen wir vom Anbieter eine kleine Provision. Für dich ändert sich nichts – der
> Preis bleibt gleich.
>
> Welche Events wir zeigen und empfehlen, hängt nie an einer Provision. Den Ticket-Button wählen wir nach einer festen
> Regel: zuerst der Ticketverkauf, den das Veranstaltungshaus selbst nennt, sonst der Ticketanbieter, der das Event
> führt. Mehrere Anbieter mit Preisen nebeneinander zeigen wir nicht. Im Magazin setzen wir keine Partner-Links.
>
> Unsere Partner: Eventim, Reservix, ADticket, Ticketmaster, Tiqets und GetYourGuide. Wir setzen dafür keine eigenen
> Cookies und zählen keine Klicks. Was nach dem Klick passiert, regelt der Anbieter – mehr dazu in der
> Datenschutzerklärung.

## (3) Datenschutzerklärung, Abschnitt 9 „Externe Inhalte und Drittanbieter“, neuer Punkt (Sie)

> **Partner-Links zu Ticketanbietern:** Einige Ticket-Buttons auf Event-Seiten sind Partner-Links, gekennzeichnet mit
> einem Sternchen („Tickets\*“). Sie führen zu Eventim, Reservix, ADticket, Ticketmaster, Tiqets und GetYourGuide;
> vermittelt werden sie über die Partnernetzwerke Awin (AWIN AG, Berlin) für Eventim, Reservix und ADticket und Impact
> (Impact Tech, Inc., USA) für Ticketmaster. Beim Aufruf unserer Seiten wird keine Verbindung zu diesen Anbietern
> aufgebaut; wir setzen dafür keine Cookies und erfassen keine Klicks. Erst wenn Sie auf einen solchen Link klicken,
> werden Sie über den Server des Partnernetzwerks auf die Seite des Anbieters weitergeleitet. Dabei werden Ihre
> IP-Adresse und technische Angaben Ihres Browsers übermittelt, und das Netzwerk bzw. der Anbieter kann Cookies oder
> ähnliche Techniken einsetzen, um einen Kauf unserer Website zuzuordnen. Dafür sind das Netzwerk und der Anbieter
> selbst verantwortlich; Einzelheiten finden Sie in deren Datenschutzerklärungen. Wir erhalten von den Netzwerken nur
> zusammengefasste Angaben zu Klicks und Verkäufen, keine Angaben zu Ihrer Person. Rechtsgrundlage für das
> Bereitstellen der Links ist unser berechtigtes Interesse an der Finanzierung dieses Angebots (Art. 6 Abs. 1 lit. f
> DSGVO).

Offene Fragen an den Anwalt:
- Reicht der Hinweis direkt am Button plus /ueber als Werbekennzeichnung (§ 5a Abs. 4 UWG, § 22 MStV), oder soll
  „Anzeige“/„Werbung“ ausdrücklich dastehen?
- Sollen die Anschriften der Netzwerke vollständig genannt und die Datenschutzerklärungen verlinkt werden?
- Impact sitzt in den USA: Ist ein Hinweis auf die Drittlandübermittlung nötig, obwohl wir selbst nichts übermitteln?

## Was danach in GitHub gesetzt wird (Settings → Secrets and variables → Actions → Variables)

| Variable | Wert | Wann |
|---|---|---|
| `AWIN_PUBLISHER_ID` | Publisher-ID aus dem Awin-Konto (Zahl) | nach Zusage der Programme |
| `TIQETS_PARTNER_ID`, `GYG_PARTNER_ID` | Partner-Kennung aus dem jeweiligen Portal | nach Zusage |
| `TICKETMASTER_PARTNER_VORLAGE` | Impact-Deeplink mit `{url}` an der Stelle der Zielseite, z. B. `https://ticketmaster.evyy.net/c/<ID>/<Ad>/<Programm>?u={url}` | nach Zusage |
| `TICKETMASTER_PARTNER_OK` | `1` | erst mit der schriftlichen Bestätigung von Ticketmaster |
| `PARTNERLINKS_AKTIV` | `1` | erst nach Freigabe dieser Texte – wirkt mit dem nächsten Deploy |

Zurück: `PARTNERLINKS_AKTIV` auf `0` und Deploy – dann sind alle Links wieder normal und die Texte verschwinden.
