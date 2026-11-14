// Kategorieseite /kategorie/{slug} (SEO-/GEO-Plan Nov. 2026, Phase B, Maßnahme 5): H1, fester Text, Satz mit der
// Live-Zahl, Feinfilter, die kommenden Events und Querverweise – alles im ersten HTML (ohne Suspense).
// Unbekannte Slugs beantwortet proxy.ts mit 404; ein einzelner Filter /entdecken?kategorie=… leitet per 301 hierher.
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { EventListe, JsonLd, Krumen, LinkChips } from "@/components/landing";
import { Icon } from "@/components/karten";
import { unterkategorienZaehlen } from "@/lib/ableitungen";
import { eventPoolLaden } from "@/lib/daten";
import { KATEGORIEN, kategorie, katStil } from "@/lib/kategorien";
import { KATEGORIE_TEXTE } from "@/lib/landing-texte";
import { LANDING_TAGE, MIN_EINTRAEGE, kategorieGueltig, unterkategoriePfad } from "@/lib/landing";
import { kategorieEvents, unterkategorieIndexierbar } from "@/lib/landing-listen";
import { eventListeJsonLd } from "@/lib/listen-json-ld";
import { seitenMetadaten } from "@/lib/seo";
import { aufzaehlung } from "@/lib/tagestext";
import type { KategorieSlug } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

type Props = { params: Promise<{ slug: string }> };

// Wie die Guide-Details: params oben lesen, ohne äußere Suspense-Grenze
export const instant = false;

/** Passende Guides bzw. Seiten zu einer Kategorie (nur, was es gibt). */
const EXTRA_LINKS: Partial<Record<KategorieSlug, { name: string; pfad: string }[]>> = {
  food: [{ name: "Restaurants & Cafés", pfad: "/guides/restaurants-cafes" }],
  nightlife: [{ name: "Club-Guide", pfad: "/guides/clubs" }, { name: "Kneipen & Bars", pfad: "/guides/kneipen-bars" }],
  musik: [{ name: "Club-Guide", pfad: "/guides/clubs" }],
  // familie: Spielplätze vorübergehend nicht verlinkt (SPIELPLAETZE_VERLINKT in lib/landing.ts)
};

const kommende = kategorieEvents;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  if (!kategorieGueltig(slug)) return { title: "Seite nicht gefunden" };
  const k = kategorie(slug);
  const pool = await eventPoolLaden();
  const anzahl = kommende(pool, slug).length;
  return seitenMetadaten({
    pfad: `/kategorie/${slug}`,
    titel: `${k.name} in Düsseldorf`,
    beschreibung: `${k.name} in Düsseldorf: ${anzahl} Events in den nächsten ${LANDING_TAGE} Tagen. ${KATEGORIE_TEXTE[slug]?.[0] ?? ""}`.slice(0, 300),
    // Dünne Seite (weniger als fünf kommende Events): für Besucher da, aber nicht im Index
    noindex: anzahl < MIN_EINTRAEGE,
  });
}

export default async function KategorieSeite({ params }: Props) {
  const { slug } = await params;
  if (!kategorieGueltig(slug)) notFound();
  const k = kategorie(slug);
  const pool = await eventPoolLaden();
  const events = kommende(pool, slug);
  const pfad = `/kategorie/${slug}`;

  // Feinfilter mit Treffern (KI-Zuordnung) – als Chips und für den Satz
  const unter = unterkategorienZaehlen(events, slug);
  const haeufigste = [...unter].sort((a, b) => b.anzahl - a.anzahl).slice(0, 3).map((u) => u.name);
  const satz =
    pool.quelle !== "supabase"
      ? null
      : events.length === 0
        ? `In den nächsten ${LANDING_TAGE} Tagen ist in Düsseldorf in dieser Kategorie noch nichts eingetragen.`
        : `In den nächsten ${LANDING_TAGE} Tagen ${events.length === 1 ? "steht" : "stehen"} in Düsseldorf ${events.length === 1 ? "ein Event" : `${events.length} Events`} aus der Kategorie ${k.name} an${haeufigste.length > 1 ? `, am häufigsten ${aufzaehlung(haeufigste)}` : ""}.`;

  // Reihen dieser Kategorie mit kommenden Terminen
  const reihen = new Map<string, { name: string; pfad: string; anzahl: number }>();
  for (const e of events) {
    if (!e.reihe) continue;
    const r = reihen.get(e.reihe.slug) ?? { name: e.reihe.titel, pfad: `/reihe/${encodeURIComponent(e.reihe.slug)}`, anzahl: 0 };
    r.anzahl++;
    reihen.set(e.reihe.slug, r);
  }
  const reihenLinks = [...reihen.values()].sort((a, b) => b.anzahl - a.anzahl).slice(0, 8);

  const krumen = [{ name: "Start", pfad: "/" }, { name: k.name, pfad }];
  const jsonLd = eventListeJsonLd(SITE_URL, `${k.name} in Düsseldorf`, krumen, events);

  return (
    <div className="container sektion landing" style={katStil(slug)}>
      <JsonLd daten={jsonLd} />
      <Krumen teile={krumen} />
      <h1 className="d">{k.name} in Düsseldorf</h1>
      {(KATEGORIE_TEXTE[slug] ?? []).map((t) => (
        <p key={t} className="landing__text">{t}</p>
      ))}
      {satz && <p className="tagesatz">{satz}</p>}

      {unter.length > 0 && (
        <div className="filterleiste" aria-label="Feinfilter">
          {unter.map((u) => (
            // Indexierbare Unterkategorie: eigene Seite; sonst der Filter (noindex)
            <Link key={u.slug} href={unterkategorieIndexierbar(pool, slug, u.slug) ? unterkategoriePfad(slug, u.slug) : `/entdecken?kategorie=${slug}&unter=${u.slug}&datum=monat`} className="chip chip--tint">
              {u.name} <small>{u.anzahl}</small>
            </Link>
          ))}
        </div>
      )}

      <EventListe events={events} heute={pool.heute} leer={`Gerade keine ${k.name}-Events in den nächsten ${LANDING_TAGE} Tagen.`} />
      {events.length > 0 && (
        <p>
          <Link href={`/entdecken?kategorie=${slug}&datum=alle`} className="link">
            Alle {k.name}-Events mit Filtern <Icon name="arrow_forward" />
          </Link>
        </p>
      )}

      <LinkChips titel="Reihen" links={reihenLinks} />
      <LinkChips titel="Passend dazu" links={EXTRA_LINKS[slug] ?? []} />
      <LinkChips
        titel="Weitere Kategorien"
        links={[
          { name: "Heute", pfad: "/heute" },
          { name: "Wochenende", pfad: "/wochenende" },
          ...KATEGORIEN.filter((x) => x.slug !== slug).map((x) => ({ name: x.name, pfad: `/kategorie/${x.slug}` })),
        ]}
      />
    </div>
  );
}
