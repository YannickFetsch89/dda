// "Düsseldorf entdecken" – Übersicht aller Guide-Hubs (Design-Handoff v2, Ansichten 10 und 11)
// Fertige Hubs sind verlinkt (mit echter Anzahl), die übrigen erscheinen als "Bald verfügbar".
// Kachelbilder: KI-generiert, liegen als WebP unter public/guides/<slug>.webp
import type { Metadata } from "next";
import Link from "next/link";

import { GuideEinleitung, GuideSeoText } from "@/components/guide-text";
import { Icon } from "@/components/karten";
import { zahl } from "@/lib/guide-filter";
import { orteLaden } from "@/lib/orte";
import { brauhaeuserFuerRestaurants, kneipenLaden } from "@/lib/kneipen-daten";
import { clubsLaden } from "@/lib/clubs-daten";
import { spielplaetzeLaden } from "@/lib/spielplaetze-daten";

export const metadata: Metadata = {
  title: "Düsseldorf entdecken – Guides",
  description:
    "Kuratierte Tipps für Restaurants, Cafés, Kneipen, Clubs, Spielplätze und Ausflüge in Düsseldorf – von dies.das.düsseldorf.",
  alternates: { canonical: "/guides" },
};

interface Hub {
  slug: string;
  label: string;
  icon: string;
  teaser: string;
  einheit: string;
  fertig: boolean;
}

// Reihenfolge und Texte laut data/guides.json im Design-Handoff
const HUBS: Hub[] = [
  { slug: "restaurants-cafes", label: "Restaurants & Cafés", icon: "restaurant", teaser: "Die besten Adressen zum Essen und Kaffeetrinken", einheit: "Tipps", fertig: true },
  { slug: "kneipen-bars", label: "Kneipen & Bars", icon: "sports_bar", teaser: "Altbier, Cocktails und gemütliche Ecken", einheit: "Tipps", fertig: true },
  { slug: "clubs", label: "Clubs", icon: "nightlife", teaser: "Düsseldorfs Nachtleben von Techno bis Hip-Hop", einheit: "Tipps", fertig: true },
  { slug: "spielplaetze", label: "Spielplätze", icon: "toys", teaser: "Der perfekte Spielplatz für jedes Alter", einheit: "Plätze", fertig: true },
  { slug: "ausfluege", label: "Ausflüge", icon: "hiking", teaser: "Raus aus der Stadt – unter einer Stunde erreichbar", einheit: "Ziele", fertig: false },
  { slug: "wochenend-trips", label: "Wochenend-Trips", icon: "local_activity", teaser: "Ein Wochenende weg – unter 4 Stunden Anfahrt", einheit: "Trips", fertig: false },
];

function HubKachel({ hub, anzahl, oben }: { hub: Hub; anzahl: number | null; oben: boolean }) {
  const inhalt = (
    <>
      <div className="gd-hub__bild">
        <div className="gd-hub__motiv">
          <Icon name={hub.icon} className="gd-hub__platzhalter" />
          {/* eslint-disable-next-line @next/next/no-img-element -- statisches, bereits optimiertes WebP */}
          <img
            src={`/guides/${hub.slug}.webp`}
            alt=""
            width={1400}
            height={768}
            loading={oben ? "eager" : "lazy"}
            fetchPriority={oben ? "high" : undefined}
            decoding="async"
          />
        </div>
        <div className="gd-hub__verlauf" aria-hidden />
        <div className="gd-hub__kopf">
          <h2 className="d">{hub.label}</h2>
          <span className="gd-hub__icon"><Icon name={hub.icon} /></span>
        </div>
      </div>
      <div className="gd-hub__fuss">
        <span className="gd-hub__teaser">{hub.teaser}</span>
        {hub.fertig ? (
          <span className="gd-hub__zahl">
            <span className="gd-hub__badge">{anzahl != null ? `${zahl(anzahl)} ${hub.einheit}` : hub.einheit}</span>
            <span className="gd-hub__pfeil" aria-hidden>→</span>
          </span>
        ) : (
          <span className="gd-hub__badge gd-hub__badge--bald">Bald verfügbar</span>
        )}
      </div>
    </>
  );
  // Echte Liste (ul/li), der Link behält seine Rolle
  return (
    <li>
      {hub.fertig ? (
        <Link href={`/guides/${hub.slug}`} className="gd-hub">{inhalt}</Link>
      ) : (
        <div className="gd-hub gd-hub--bald">{inhalt}</div>
      )}
    </li>
  );
}

function KachelListe({ anzahl }: { anzahl: Record<string, number> }) {
  return (
    <ul className="gd-hubs">
      {HUBS.map((hub, i) => (
        <HubKachel key={hub.slug} hub={hub} anzahl={anzahl[hub.slug] ?? null} oben={i < 2} />
      ))}
    </ul>
  );
}

/** Anzahl je Hub (Daten gecached über orteLaden) – jede Kachel zählt genau das, was ihr Hub zeigt
 * (Restaurant-Hub inkl. Brauhäuser, Kneipen-Hub inkl. Restaurants mit auch_kneipe). */
async function anzahlLaden(): Promise<Record<string, number>> {
  const [restaurants, brauhaeuser, kneipen, clubs, spielplaetze] = await Promise.all([
    orteLaden(["restaurant", "imbiss", "cafe"]), brauhaeuserFuerRestaurants(), kneipenLaden(), clubsLaden(), spielplaetzeLaden(),
  ]);
  return {
    "restaurants-cafes": restaurants.length + brauhaeuser.length, "kneipen-bars": kneipen.length, clubs: clubs.length,
    spielplaetze: spielplaetze.length,
  };
}

export default async function GuidesUebersicht() {
  const anzahl = await anzahlLaden();
  const werte = {
    restaurants: zahl(anzahl["restaurants-cafes"] ?? 0), kneipen: zahl(anzahl["kneipen-bars"] ?? 0), clubs: zahl(anzahl.clubs ?? 0),
    spielplaetze: zahl(anzahl.spielplaetze ?? 0),
  };
  return (
    <div className="gd-seite">
      <header className="gd-entdecken container">
        <nav className="gd-krumen" aria-label="Brotkrumen">
          <Link href="/">Start</Link><span>/</span><span aria-current="page">Düsseldorf entdecken</span>
        </nav>
        <h1 className="d">Düsseldorf entdecken</h1>
        <div className="gd-entdecken__linie" aria-hidden />
        <GuideEinleitung seite="uebersicht" werte={werte} />
      </header>
      <div className="container">
        <KachelListe anzahl={anzahl} />
      </div>
      <GuideSeoText seite="uebersicht" />
    </div>
  );
}
