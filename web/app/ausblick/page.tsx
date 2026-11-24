// Ausblick (Plan docs/plan-quellen-ausbau-2026-11-23.md, 6.1/6.4, Schritt W2): große Events von Tag 61 bis 365,
// nach Monaten, Filter Kategorie. Nur Quellen mit Rang 1–2 und Orte mit Ortsseite (lib/ausblick.ts).
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { EventKarte, Icon, Leer } from "@/components/karten";
import { ausblickKategorien, ausblickLaden } from "@/lib/ausblick";
import { monatName, nachMonat } from "@/lib/datum";
import { jsonLdText } from "@/lib/json-ld";
import { kategorie as kategorieInfo } from "@/lib/kategorien";
import { eventListeJsonLd } from "@/lib/listen-json-ld";
import { hatParameter, seitenMetadaten } from "@/lib/seo";
import type { DddEvent } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
const PFAD = "/ausblick";

function seitenTitel(letzter: string | null): string {
  return letzter ? `Ausblick: Große Events in Düsseldorf bis ${monatName(letzter)}` : "Ausblick: Große Events in Düsseldorf";
}

export async function generateMetadata(props: PageProps<"/ausblick">): Promise<Metadata> {
  const { letzter, events } = await ausblickLaden();
  return seitenMetadaten({
    pfad: PFAD,
    titel: seitenTitel(letzter),
    beschreibung: "Konzerte, Shows, Theater und Sport in Düsseldorf, Neuss und Ratingen in den nächsten Monaten – zum Vormerken, nach Monat sortiert.",
    // Gefilterte Ansicht (?kategorie=) und eine leere Seite nicht indexieren
    noindex: hatParameter(await props.searchParams) || events.length === 0,
  });
}

// Standardansicht (ohne Filter) im ersten HTML aus dem Cache; nur die Filter-Variante wartet auf searchParams
// (Muster wie /wochenende).
export default async function Ausblick(props: PageProps<"/ausblick">) {
  const daten = await ausblickLaden();
  return (
    <Suspense fallback={<AusblickAnsicht {...daten} />}>
      <MitFilter searchParams={props.searchParams} daten={daten} />
    </Suspense>
  );
}

type Daten = Awaited<ReturnType<typeof ausblickLaden>>;

async function MitFilter({ searchParams, daten }: Pick<PageProps<"/ausblick">, "searchParams"> & { daten: Daten }) {
  const sp = await searchParams;
  return <AusblickAnsicht {...daten} filter={typeof sp.kategorie === "string" ? sp.kategorie : undefined} />;
}

function AusblickAnsicht({ heute, events, letzter, filter }: Daten & { filter?: string }) {
  const kategorien = ausblickKategorien(events);
  const aktiv = filter && kategorien.some((k) => k.slug === filter) ? filter : undefined;
  const liste: DddEvent[] = aktiv ? events.filter((e) => e.kategorie === aktiv) : events;
  const titel = seitenTitel(letzter);
  const jsonLd = eventListeJsonLd(SITE_URL, titel, [{ name: "Start", pfad: "/" }, { name: "Ausblick", pfad: PFAD }], liste);

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <section className="wk-hero">
        <div className="container">
          <span className="overline overline--gold">Zum Vormerken</span>
          <h1 className="d">{titel}</h1>
          <p>
            Große Konzerte, Shows, Theater und Sport später im Jahr – direkt von den Häusern und Ticketanbietern. Was in den
            nächsten zwei Monaten passiert, findest du unter <Link href="/entdecken">Entdecken</Link>.
          </p>
        </div>
      </section>

      <div className="container">
        {kategorien.length > 1 && (
          <nav className="chip-wolke ausblick-filter" aria-label="Kategorie wählen">
            <Link href={PFAD} className="chip" aria-current={!aktiv ? "true" : undefined} scroll={false}>
              Alle <small>{events.length}</small>
            </Link>
            {kategorien.map((k) => (
              <Link key={k.slug} href={`${PFAD}?kategorie=${encodeURIComponent(k.slug)}`} className="chip" aria-current={k.slug === aktiv ? "true" : undefined} scroll={false}>
                {kategorieInfo(k.slug).name} <small>{k.anzahl}</small>
              </Link>
            ))}
          </nav>
        )}

        {liste.length ? (
          nachMonat(liste).map((g) => (
            <section key={g.monat} className="sektion" aria-labelledby={`ab-${g.termine[0].datum.slice(0, 7)}`}>
              <div className="sektionskopf">
                <h2 className="d" id={`ab-${g.termine[0].datum.slice(0, 7)}`}>{g.monat}</h2>
              </div>
              <div className="raster" role="list">
                {g.termine.map((e) => <EventKarte key={e.id} e={e} heute={heute} variante="grid" />)}
              </div>
            </section>
          ))
        ) : (
          <div className="sektion">
            <Leer titel="Gerade stehen hier noch keine Termine.">
              <Link href="/entdecken" className="link">
                Alle Events der nächsten Wochen <Icon name="arrow_forward" />
              </Link>
            </Leer>
          </div>
        )}
      </div>
    </>
  );
}
