// Unterkategorie-Seite /kategorie/{kategorie}/{unter}, z. B. /kategorie/kultur/theater (Feinschliff-Roadmap, Paket 4).
// Slug und Name aus web/lib/unterkategorien.json, Zuordnung der Events per KI (pipeline/unterkategorien.py).
// Indexiert nur mit freigegebenem Text (lib/landing-texte.ts) UND mindestens fünf kommenden Events – sonst noindex,
// nicht in der Sitemap, und die Kategorieseite verlinkt weiter auf den Filter. Unbekannte Slugs: 404 aus proxy.ts.
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { EventListe, JsonLd, Krumen, LinkChips } from "@/components/landing";
import { Icon } from "@/components/karten";
import { eventPoolLaden } from "@/lib/daten";
import { kategorie, katStil } from "@/lib/kategorien";
import { LANDING_TAGE, kategoriePfad, unterkategorieGueltig, unterkategoriePfad } from "@/lib/landing";
import { unterkategorieEvents, unterkategorieIndexierbar, unterkategorieText } from "@/lib/landing-listen";
import { eventListeJsonLd } from "@/lib/listen-json-ld";
import { seitenMetadaten } from "@/lib/seo";
import type { KategorieSlug } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

type Props = { params: Promise<{ slug: string; unter: string }> };

export const instant = false;

function aufloesen(slug: string, unterSlug: string) {
  if (!unterkategorieGueltig(slug, unterSlug)) return null;
  const k = kategorie(slug);
  const u = k.unterkategorien.find((x) => x.slug === unterSlug)!;
  return { k, u, kat: slug as KategorieSlug };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug, unter } = await params;
  const d = aufloesen(slug, unter);
  if (!d) return { title: "Seite nicht gefunden" };
  const pool = await eventPoolLaden();
  const anzahl = unterkategorieEvents(pool, d.kat, d.u.slug).length;
  const text = unterkategorieText(d.kat, d.u.slug)?.[0] ?? "";
  return seitenMetadaten({
    pfad: unterkategoriePfad(d.kat, d.u.slug),
    titel: `${d.u.name} in Düsseldorf`,
    beschreibung: `${d.u.name} in Düsseldorf: ${anzahl} Termine in den nächsten ${LANDING_TAGE} Tagen. ${text}`.trim().slice(0, 300),
    noindex: !unterkategorieIndexierbar(pool, d.kat, d.u.slug),
  });
}

export default async function UnterkategorieSeite({ params }: Props) {
  const { slug, unter } = await params;
  const d = aufloesen(slug, unter);
  if (!d) notFound();
  const { k, u, kat } = d;
  const pool = await eventPoolLaden();
  const events = unterkategorieEvents(pool, kat, u.slug);
  const pfad = unterkategoriePfad(kat, u.slug);
  const text = unterkategorieText(kat, u.slug) ?? [];

  const satz =
    pool.quelle !== "supabase"
      ? null
      : events.length === 0
        ? `In den nächsten ${LANDING_TAGE} Tagen ist in Düsseldorf in diesem Bereich noch nichts eingetragen.`
        : `In den nächsten ${LANDING_TAGE} Tagen ${events.length === 1 ? "steht" : "stehen"} in Düsseldorf ${events.length === 1 ? "ein Termin" : `${events.length} Termine`} aus dem Bereich ${u.name} an.`;

  // Geschwister: andere Unterkategorien derselben Kategorie, nur die indexierbaren als eigene Seite
  const geschwister = k.unterkategorien
    .filter((x) => x.slug !== u.slug && unterkategorieIndexierbar(pool, kat, x.slug))
    .map((x) => ({ name: x.name, pfad: unterkategoriePfad(kat, x.slug), anzahl: unterkategorieEvents(pool, kat, x.slug).length }));

  const katPfad = kategoriePfad(kat)!;
  const krumen = [{ name: "Start", pfad: "/" }, { name: k.name, pfad: katPfad }, { name: u.name, pfad }];
  const jsonLd = eventListeJsonLd(SITE_URL, `${u.name} in Düsseldorf`, krumen, events);

  return (
    <div className="container sektion landing" style={katStil(kat)}>
      <JsonLd daten={jsonLd} />
      <Krumen teile={krumen} />
      <h1 className="d">{u.name} in Düsseldorf</h1>
      {text.map((t) => (
        <p key={t} className="landing__text">{t}</p>
      ))}
      {satz && <p className="tagesatz">{satz}</p>}

      <EventListe events={events} heute={pool.heute} leer={`Gerade keine Termine aus dem Bereich ${u.name} in den nächsten ${LANDING_TAGE} Tagen.`} />
      {events.length > 0 && (
        <p>
          <Link href={`/entdecken?kategorie=${kat}&unter=${u.slug}&datum=alle`} className="link">
            Alle Termine aus dem Bereich {u.name} mit Filtern <Icon name="arrow_forward" />
          </Link>
        </p>
      )}

      <LinkChips titel={`Mehr aus ${k.name}`} links={[{ name: `Alle ${k.name}-Events`, pfad: katPfad }, ...geschwister]} />
      <LinkChips titel="Weiter stöbern" links={[{ name: "Heute", pfad: "/heute" }, { name: "Wochenende", pfad: "/wochenende" }, { name: "Kostenlos", pfad: "/kostenlos" }]} />
    </div>
  );
}
