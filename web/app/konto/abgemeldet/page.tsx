// /konto/abgemeldet – Ziel nach dem Abmelden (17.11.2026, vorher ging es auf die Merkliste). Statisch, ohne Sitzung.
import type { Metadata } from "next";
import Link from "next/link";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Abgemeldet", robots: KONTO_ROBOTS };

export default function Abgemeldet() {
  return (
    <KontoRahmen titel="Abgemeldet">
      <div className="formular__danke">
        <span className="icon" aria-hidden data-icon="logout" />
        <h2 className="d">Bis bald!</h2>
        <p>Du hast dich erfolgreich ausgeloggt.</p>
        <div className="formular__aktionen">
          <Link href="/" className="btn btn--navy">Zur Startseite</Link>
          <Link href="/konto/anmelden" className="btn btn--outline">Wieder anmelden</Link>
        </div>
      </div>
    </KontoRahmen>
  );
}
