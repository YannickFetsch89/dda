// /kostenlos – kostenlose Events in Düsseldorf (Feinschliff-Roadmap Nov. 2026, Paket 3). Eigene Suchanfrage, bisher nur
// als noindex-Filter erreichbar. Ein einzelner Filter /entdecken?preis=kostenlos leitet per 301 hierher (proxy.ts).
// H1, fester Text, Satz mit Zeitraum und Live-Zahl und die Liste stehen im ersten HTML.
import type { Metadata } from "next";
import Link from "next/link";
import { EventListe, JsonLd, Krumen, LinkChips } from "@/components/landing";
import { Icon } from "@/components/karten";
import { kategorieZaehlen } from "@/lib/ableitungen";
import { eventPoolLaden } from "@/lib/daten";
import { KATEGORIEN } from "@/lib/kategorien";
import { KOSTENLOS_TEXTE } from "@/lib/landing-texte";
import { LANDING_TAGE } from "@/lib/landing";
import { kostenlosEvents, kostenlosIndexierbar } from "@/lib/landing-listen";
import { eventListeJsonLd } from "@/lib/listen-json-ld";
import { seitenMetadaten } from "@/lib/seo";
import { aufzaehlung, topKategorien } from "@/lib/tagestext";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
const PFAD = "/kostenlos";

export async function generateMetadata(): Promise<Metadata> {
  const pool = await eventPoolLaden();
  const anzahl = kostenlosEvents(pool).length;
  return seitenMetadaten({
    pfad: PFAD,
    titel: "Kostenlose Events in Düsseldorf",
    beschreibung: `Kostenlose Events in Düsseldorf: ${anzahl} Termine ohne Eintritt in den nächsten ${LANDING_TAGE} Tagen. ${KOSTENLOS_TEXTE[0]}`.slice(0, 300),
    // Unter fünf Einträgen: für Besucher da, aber nicht im Index
    noindex: !kostenlosIndexierbar(pool),
  });
}

export default async function Kostenlos() {
  const pool = await eventPoolLaden();
  const events = kostenlosEvents(pool);
  const top = events.length >= 3 ? topKategorien(events) : [];
  // Der Zeitraum steht ausdrücklich im Satz: Die Kategorie-Leiste zählt sieben Tage, diese Seite 30
  const satz =
    pool.quelle !== "supabase"
      ? null
      : events.length === 0
        ? `In den nächsten ${LANDING_TAGE} Tagen ist in Düsseldorf noch kein kostenloses Event eingetragen.`
        : `In den nächsten ${LANDING_TAGE} Tagen ${events.length === 1 ? "steht" : "stehen"} in Düsseldorf ${events.length === 1 ? "ein kostenloses Event" : `${events.length} kostenlose Events`} an${top.length ? `, die meisten aus ${aufzaehlung(top)}` : ""}.`;

  const zaehler = kategorieZaehlen(events);
  const kategorien = KATEGORIEN.filter((k) => zaehler[k.slug] > 0).map((k) => ({
    name: k.name,
    pfad: `/entdecken?preis=kostenlos&kategorie=${k.slug}&datum=monat`,
    anzahl: zaehler[k.slug],
  }));

  const krumen = [{ name: "Start", pfad: "/" }, { name: "Kostenlos", pfad: PFAD }];
  const jsonLd = eventListeJsonLd(SITE_URL, "Kostenlose Events in Düsseldorf", krumen, events);

  return (
    <div className="container sektion landing">
      <JsonLd daten={jsonLd} />
      <Krumen teile={krumen} />
      <h1 className="d">Kostenlose Events in Düsseldorf</h1>
      {KOSTENLOS_TEXTE.map((t) => (
        <p key={t} className="landing__text">{t}</p>
      ))}
      {satz && <p className="tagesatz">{satz}</p>}

      {kategorien.length > 1 && (
        <div className="filterleiste" aria-label="Nach Kategorie">
          {kategorien.map((k) => (
            <Link key={k.pfad} href={k.pfad} className="chip chip--tint">
              {k.name} <small>{k.anzahl}</small>
            </Link>
          ))}
        </div>
      )}

      <EventListe events={events} heute={pool.heute} leer={`Gerade keine kostenlosen Events in den nächsten ${LANDING_TAGE} Tagen.`} />
      {events.length > 0 && (
        <p>
          <Link href="/entdecken?preis=kostenlos&datum=alle" className="link">
            Alle kostenlosen Events mit Filtern <Icon name="arrow_forward" />
          </Link>
        </p>
      )}

      <LinkChips
        titel="Weiter stöbern"
        links={[
          { name: "Heute", pfad: "/heute" },
          { name: "Wochenende", pfad: "/wochenende" },
          ...KATEGORIEN.map((k) => ({ name: k.name, pfad: `/kategorie/${k.slug}` })),
        ]}
      />
    </div>
  );
}
