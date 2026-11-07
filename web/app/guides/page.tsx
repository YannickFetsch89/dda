// "Düsseldorf entdecken" – Übersicht aller Guide-Hubs (Design-Handoff v2, Ansichten 10 und 11)
// Fertige Hubs sind verlinkt (mit echter Anzahl), die übrigen erscheinen als "Bald verfügbar".
// Kachelbilder: KI-generiert, liegen als WebP unter public/guides/<slug>.webp
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Icon } from "@/components/karten";
import { zahl } from "@/lib/guide-filter";
import { orteLaden } from "@/lib/orte";
import { kneipenLaden } from "@/lib/kneipen-daten";

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
  { slug: "clubs", label: "Clubs", icon: "nightlife", teaser: "Düsseldorfs Nachtleben von Techno bis Hip-Hop", einheit: "Tipps", fertig: false },
  { slug: "spielplaetze", label: "Spielplätze", icon: "toys", teaser: "Der perfekte Spielplatz für jedes Alter", einheit: "Plätze", fertig: false },
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

/** Kacheln mit echten Zahlen (Daten gecached über orteLaden). */
async function Kacheln() {
  // Jeder Hub zählt seine eigenen Orte (Kneipen nicht in die Restaurant-Zahl mischen)
  const [restaurants, kneipen] = await Promise.all([orteLaden(["restaurant", "imbiss", "cafe"]), kneipenLaden()]);
  return <KachelListe anzahl={{ "restaurants-cafes": restaurants.length, "kneipen-bars": kneipen.length }} />;
}

export default function GuidesUebersicht() {
  return (
    <div className="gd-seite">
      <header className="gd-entdecken container">
        <nav className="gd-krumen" aria-label="Brotkrumen">
          <Link href="/">Start</Link><span>/</span><span aria-current="page">Düsseldorf entdecken</span>
        </nav>
        <h1 className="d">Düsseldorf entdecken</h1>
        <div className="gd-entdecken__linie" aria-hidden />
        <p>Kuratierte Tipps für Restaurants, Cafés, Kneipen, Clubs, Spielplätze und Ausflüge – von uns für euch.</p>
      </header>
      <div className="container">
        <Suspense fallback={<KachelListe anzahl={{}} />}>
          <Kacheln />
        </Suspense>
      </div>
    </div>
  );
}
