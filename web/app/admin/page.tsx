// Admin-Bereich – Cockpit. Stufe 1a liefert nur das Gerüst; Ampeln, „Zu erledigen“ und Kennzahlen folgen in Stufe 1b
// (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.2).
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Cockpit" };

export default function AdminCockpit() {
  return (
    <>
      <h1>Cockpit</h1>
      <p className="admin-unterzeile">Der neue Admin-Bereich ist eingerichtet. Die Bereiche kommen Stufe für Stufe dazu.</p>
      <section className="admin-karte">
        <h2>Als Nächstes (Stufe 1b)</h2>
        <p>Ampeln für Scraper-Lauf, Deploy, Wächter, Geburtstagsmails und Magazin-Job, dazu „Zu erledigen“ und Kennzahlen.</p>
      </section>
      <section className="admin-karte">
        <h2>Bis dahin</h2>
        <p>
          Events, Featured, Scraper-Report, Meldungen, Newsletter und SEO-Aufräumen gibt es weiter im{" "}
          <a href="/alt/">alten Dashboard</a>.
        </p>
      </section>
    </>
  );
}
