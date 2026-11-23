// /newsletter/abmelden#t=<Token> – Newsletter abmelden, Adresse sofort löschen (Plan Admin-Dashboard 4.9, Stufe 4).
// Statische Hülle (noindex); das Token liest erst der Browser aus dem Fragment und schickt es beim Klick.
import type { Metadata } from "next";
import { NewsletterLink } from "@/components/newsletter-link";

export const metadata: Metadata = { title: "Newsletter abmelden", robots: { index: false, follow: false } };

export default function NewsletterAbmelden() {
  return (
    <div className="container sektion">
      <div className="konto-seite">
        <div className="seitentitel">
          <h1 className="d">Newsletter abmelden</h1>
        </div>
        <NewsletterLink aktion="abmelden" />
      </div>
    </div>
  );
}
