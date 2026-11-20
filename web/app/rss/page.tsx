// Erklärseite zum RSS-Feed des Magazins (20.11.2026). Ersetzt die Idee eines XSLT-Stylesheets: Chrome entfernt XSLT laut
// Ankündigung ab Version 158 (17.11.2026), Firefox und Safari wollen folgen – ein gestylter Feed würde dort nur noch als roher Text erscheinen.
// Der Footer-Link „RSS-Feed“ zeigt hierher; der Feed selbst (/magazin/feed.xml) und der <link rel="alternate"> im <head>
// bleiben unverändert, damit Feed-Reader und Suchmaschinen ihn weiter automatisch finden.
// noindex,follow: dünne Hilfeseite ohne eigenen Suchwert, steht nicht in der Sitemap.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { FeedAdresse } from "@/components/feed-adresse";
import { beitragPfad, FEED_PFAD } from "@/lib/magazin";
import { beitraegeLaden } from "@/lib/magazin-daten";
import { seitenMetadaten } from "@/lib/seo";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

export const metadata: Metadata = seitenMetadaten({
  pfad: "/rss",
  titel: "RSS-Feed des Magazins",
  beschreibung: "Neue Beiträge aus dem Magazin von dies.das.düsseldorf automatisch im Feed-Reader – ohne Konto und ohne Newsletter.",
  noindex: true,
});

export default async function RssSeite() {
  const neueste = (await beitraegeLaden()).slice(0, 5);
  const feedUrl = `${SITE_URL}${FEED_PFAD}`;
  return (
    <div className="container sektion mz-redaktion">
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link>
        <span>/</span>
        <Link href="/magazin">Magazin</Link>
        <span>/</span>
        <span aria-current="page">RSS-Feed</span>
      </nav>
      <h1 className="d">RSS-Feed des Magazins</h1>
      <div className="mz-text">
        <p>
          Mit dem RSS-Feed bekommst du jeden neuen Beitrag aus unserem <Link href="/magazin">Magazin</Link> automatisch in
          deinen Feed-Reader – ohne Konto, ohne Newsletter und ohne dass wir etwas über dich erfahren.
        </p>

        <FeedAdresse url={feedUrl} />

        <h2 className="d">So funktioniert&apos;s</h2>
        <ol>
          <li>Öffne deinen Feed-Reader, zum Beispiel Feedly, Inoreader oder NetNewsWire – oder die Feed-Funktion deines Mail-Programms.</li>
          <li>Wähle dort „Feed hinzufügen“ oder „Abonnieren“.</li>
          <li>Füge die Adresse oben ein. Fertig – neue Beiträge erscheinen ab jetzt von selbst.</li>
        </ol>
        <p>
          Viele Reader finden den Feed auch, wenn du einfach <strong>diesdas.events</strong> eingibst.
        </p>

        <h2 className="d">Was ist RSS?</h2>
        <p>
          RSS ist ein offenes Format, mit dem Websites ihre neuen Inhalte in einer einheitlichen Form bereitstellen. Ein
          Feed-Reader sammelt diese Feeds und zeigt dir alles Neue an einem Ort – ohne Algorithmus und ohne Werbung
          dazwischen. Öffnest du die Feed-Adresse direkt im Browser, siehst du nur den technischen Inhalt (XML); das ist
          normal und für Feed-Reader gedacht.
        </p>

        {neueste.length > 0 && (
          <>
            <h2 className="d">Die neuesten Beiträge</h2>
            <ul>
              {neueste.map((b) => (
                <li key={b.id}>
                  <Link href={beitragPfad(b)}>{b.titel}</Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
