// Magazin-Übersicht (Plan docs/plan-redaktion-2026-11-19.md, 5.1; neu aufgebaut 25.11.2026 nach dem Vorbild eines
// Ratgeber-Hubs): Hero, Themenwelten mit Anzahl je Rubrik, Titelgeschichte mit Kernpunkten, „Frisch aus der Redaktion“
// mit Rubrik-Filter, Guides, Redaktion, Newsletter und ein kurzer Text über das Magazin.
// SEO: H1 und Einleitung mit Düsseldorf-Bezug, CollectionPage + ItemList + BreadcrumbList, viele interne Links
// (Rubriken, Guides, Autoren), alle Beiträge im ersten HTML (der Filter blendet nur aus).
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { NewsletterForm } from "@/components/client";
import { Leer } from "@/components/karten";
import { FrischAusDerRedaktion } from "@/components/magazin-filter";
import { GuideKacheln, MagazinHero, RedaktionLeiste, Themenwelten, Titelgeschichte } from "@/components/magazin-uebersicht";
import { jsonLdText } from "@/lib/json-ld";
import { RUBRIK_NAME } from "@/lib/magazin";
import { autorenLaden, beitraegeLaden, magazinHeute } from "@/lib/magazin-daten";
import { sammlungJsonLd } from "@/lib/magazin-json-ld";
import { filterRubriken, karteDaten, RUBRIK_ICON, themenZaehlen, titelgeschichte } from "@/lib/magazin-uebersicht";
import { MAGAZIN_VERLINKT } from "@/lib/schalter";
import { seitenMetadaten } from "@/lib/seo";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
const BESCHREIBUNG =
  "Das Düsseldorf-Magazin von dies.das.düsseldorf: Wochenvorschau, Monats-Tipps, Weihnachtsmärkte und Saison, Nachtleben, Genuss und Familie – ausgewählt und geprüft von der Redaktion.";

export const metadata: Metadata = seitenMetadaten({
  pfad: "/magazin",
  titel: "Magazin: Tipps und Events für Düsseldorf",
  beschreibung: BESCHREIBUNG,
  noindex: !MAGAZIN_VERLINKT,
});

export default async function MagazinSeite() {
  const [alle, autoren, heute] = await Promise.all([beitraegeLaden(), autorenLaden(), magazinHeute()]);
  const beitraege = alle.slice(0, 30);
  const titel = titelgeschichte(beitraege, heute);
  const rest = beitraege.filter((b) => b.id !== titel?.id).map(karteDaten);
  const pillen = filterRubriken(rest).map((r) => ({ rubrik: r, name: RUBRIK_NAME[r], icon: RUBRIK_ICON[r] }));
  const jsonLd = sammlungJsonLd(
    SITE_URL,
    { pfad: "/magazin", name: "Magazin für Düsseldorf", beschreibung: BESCHREIBUNG, krumen: [{ name: "Start", pfad: "/" }, { name: "Magazin", pfad: "/magazin" }] },
    beitraege,
  );
  return (
    <div className="mz-uebersicht">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <MagazinHero anzahl={alle.length} />
      <div className="container">
        <Themenwelten zahl={themenZaehlen(alle)} />
        {titel ? (
          <>
            <Titelgeschichte b={titel} />
            {rest.length > 0 && (
              <section className="sektion" aria-labelledby="mzf-titel">
                <span className="overline">Neueste Beiträge</span>
                <h2 className="d mz-h2" id="mzf-titel">Frisch aus der Redaktion</h2>
                <FrischAusDerRedaktion karten={rest} pillen={pillen} />
              </section>
            )}
          </>
        ) : (
          <Leer titel="Hier erscheinen bald die ersten Beiträge">
            <p>Bis dahin findest du alle Events im Kalender.</p>
            <Link className="btn btn--gold" href="/entdecken">Events entdecken</Link>
          </Leer>
        )}
        <GuideKacheln />
        <RedaktionLeiste autoren={autoren} />
        <section className="newsletter mz-newsletter" aria-labelledby="mz-newsletter-titel">
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}>
            <h2 className="newsletter__titel d" id="mz-newsletter-titel">Jeden Donnerstag das Wochenende im Postfach.</h2>
            <span style={{ fontSize: 14 }}>Zehn Tipps, kein Spam, jederzeit abbestellbar.</span>
          </div>
          <NewsletterForm />
        </section>
        <section className="sektion mz-ueber" aria-labelledby="mz-ueber-titel">
          <h2 className="d mz-h2" id="mz-ueber-titel">Über das Magazin</h2>
          <p>
            dies.das.düsseldorf sammelt jeden Tag Events, Orte und Termine aus Düsseldorf, Neuss und Ratingen. Im Magazin
            ordnen wir sie ein: Die <Link href="/magazin/rubrik/wochenvorschau">Wochenvorschau</Link> zeigt, was in den
            nächsten sieben Tagen los ist, die <Link href="/magazin/rubrik/monats-tipps">Monats-Tipps</Link> die stärksten
            Termine des Monats. Dazu kommen Saisonthemen wie Weihnachtsmärkte und Karneval, Nachtleben, Genuss, Familie und
            Geschichten aus den Stadtteilen.
          </p>
          <p>
            Alle Beiträge werden vor der Veröffentlichung von der <Link href="/magazin/redaktion">Redaktion</Link> geprüft.
            Neue Beiträge gibt es auch als <Link href="/rss">RSS-Feed</Link>.
          </p>
        </section>
      </div>
    </div>
  );
}
