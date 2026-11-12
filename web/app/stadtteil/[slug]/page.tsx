// Stadtteilseite /stadtteil/{slug} (SEO-/GEO-Plan Nov. 2026, Phase B, Maßnahme 5): Events eines Stadtteils aus dem
// Katalog (lib/stadtteile.ts). Eigener erster Satz je Stadtteil (lib/landing-texte.ts), sonst der Bezirks-Satz;
// dazu die Live-Zahl, die kommenden Events, Nachbar-Stadtteile und die Guide-Stadtteilseiten, die es gibt.
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { EventListe, JsonLd, Krumen, LinkChips } from "@/components/landing";
import { Icon } from "@/components/karten";
import { filtern, nachZeit } from "@/lib/ableitungen";
import { eventPoolLaden } from "@/lib/daten";
import { plusTage } from "@/lib/datum";
import { hubOrte, stadtteileMitOrten } from "@/lib/guide-stadtteile";
import { STADTTEIL_TEXTE } from "@/lib/landing-texte";
import {
  GUIDE_HUBS, LANDING_TAGE, inStadtteil, MIN_EINTRAEGE, bezirkSatz, guideStadtteilPfad, nachbarStadtteile, stadtteilAusSlug, stadtteilPfad, type GuideHub,
} from "@/lib/landing";
import { eventListeJsonLd } from "@/lib/listen-json-ld";
import { seitenMetadaten } from "@/lib/seo";
import { bezirkVon, stadtteilName } from "@/lib/stadtteile";
import { aufzaehlung, topKategorien } from "@/lib/tagestext";
import type { EventPool } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

type Props = { params: Promise<{ slug: string }> };

export const instant = false;

function kommende(pool: EventPool, stadtteil: string) {
  return filtern(pool.events, { von: pool.heute, bis: plusTage(pool.heute, LANDING_TAGE - 1), stadtteil }).sort(nachZeit);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const st = stadtteilAusSlug(slug);
  if (!st) return { title: "Seite nicht gefunden" };
  const pool = await eventPoolLaden();
  const anzahl = kommende(pool, st).length;
  const imOrt = inStadtteil(st);
  return seitenMetadaten({
    pfad: `/stadtteil/${slug}`,
    titel: `Events ${imOrt}`,
    beschreibung: `Was ist los ${imOrt}? ${anzahl} Events in den nächsten ${LANDING_TAGE} Tagen. ${STADTTEIL_TEXTE[st] ?? bezirkSatz(st)}`.slice(0, 300),
    noindex: anzahl < MIN_EINTRAEGE,
  });
}

export default async function StadtteilSeite({ params }: Props) {
  const { slug } = await params;
  const st = stadtteilAusSlug(slug);
  if (!st) notFound();
  const name = stadtteilName(st);
  const imOrt = inStadtteil(st);
  const pool = await eventPoolLaden();
  const events = kommende(pool, st);
  const pfad = `/stadtteil/${slug}`;
  const bezirk = bezirkVon(st);

  const top = events.length >= 3 ? topKategorien(events) : [];
  const satz =
    pool.quelle !== "supabase"
      ? null
      : events.length === 0
        ? `In den nächsten ${LANDING_TAGE} Tagen ist ${imOrt} noch nichts eingetragen.`
        : `In den nächsten ${LANDING_TAGE} Tagen ${events.length === 1 ? "steht" : "stehen"} ${imOrt} ${events.length === 1 ? "ein Event" : `${events.length} Events`} an${top.length ? `, die meisten aus ${aufzaehlung(top)}` : ""}.`;

  // Nachbar-Stadtteile desselben Bezirks (mit Zahl, damit man sieht, wo etwas los ist)
  const nachbarn = nachbarStadtteile(st).map((s) => ({ name: stadtteilName(s), pfad: stadtteilPfad(s)!, anzahl: kommende(pool, s).length }));

  // Guide-Stadtteilseiten, die es für diesen Stadtteil gibt (ab fünf Orten)
  const hubs = Object.keys(GUIDE_HUBS) as GuideHub[];
  const orteJeHub = await Promise.all(hubs.map((h) => hubOrte(h)));
  const guideLinks = hubs.flatMap((h, i) => {
    const treffer = stadtteileMitOrten(orteJeHub[i]).find((x) => x.stadtteil === st);
    return treffer ? [{ name: `${GUIDE_HUBS[h].name} ${imOrt}`, pfad: guideStadtteilPfad(h, st), anzahl: treffer.anzahl }] : [];
  });

  const krumen = [{ name: "Start", pfad: "/" }, { name: "Stadtteile", pfad: "/stadtteile" }, { name, pfad }];
  const jsonLd = eventListeJsonLd(SITE_URL, `Events ${imOrt}`, krumen, events);

  return (
    <div className="container sektion landing">
      <JsonLd daten={jsonLd} />
      <Krumen teile={krumen} />
      <h1 className="d">Events {imOrt}</h1>
      <p className="landing__text">{STADTTEIL_TEXTE[st] ?? bezirkSatz(st)}</p>
      {STADTTEIL_TEXTE[st] && bezirk && <p className="landing__text muted">{bezirkSatz(st)}</p>}
      {satz && <p className="tagesatz">{satz}</p>}

      <EventListe events={events} heute={pool.heute} leer={`Gerade keine Events ${imOrt} in den nächsten ${LANDING_TAGE} Tagen.`} />
      {events.length > 0 && (
        <p>
          <Link href={`/entdecken?stadtteil=${encodeURIComponent(st)}&datum=alle`} className="link">
            Alle Events {imOrt} mit Filtern <Icon name="arrow_forward" />
          </Link>
        </p>
      )}

      <LinkChips titel={`Essen & Ausgehen ${imOrt}`} links={guideLinks} />
      <LinkChips titel={bezirk ? `Mehr im Bezirk ${bezirk.name}` : "Weitere Stadtteile"} links={nachbarn} />
      <LinkChips titel="Überblick" links={[{ name: "Alle Stadtteile", pfad: "/stadtteile" }, { name: "Heute", pfad: "/heute" }, { name: "Wochenende", pfad: "/wochenende" }]} />
    </div>
  );
}
