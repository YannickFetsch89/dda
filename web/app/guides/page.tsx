// "Düsseldorf entdecken" – Übersicht aller Guide-Hubs (Design-Handoff v2, Ansichten 10 und 11)
// Fertige Hubs sind verlinkt (mit echter Anzahl und Foto), die übrigen erscheinen als "Bald verfügbar".
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { BildImg } from "@/components/client";
import { Icon } from "@/components/karten";
import { sortieren, zahl } from "@/lib/guide-filter";
import { orteLaden, ortBildUrl } from "@/lib/orte";

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
  { slug: "kneipen-bars", label: "Kneipen & Bars", icon: "sports_bar", teaser: "Altbier, Cocktails und gemütliche Ecken", einheit: "Tipps", fertig: false },
  { slug: "clubs", label: "Clubs", icon: "nightlife", teaser: "Düsseldorfs Nachtleben von Techno bis Hip-Hop", einheit: "Tipps", fertig: false },
  { slug: "spielplaetze", label: "Spielplätze", icon: "toys", teaser: "Der perfekte Spielplatz für jedes Alter", einheit: "Plätze", fertig: false },
  { slug: "ausfluege", label: "Ausflüge", icon: "hiking", teaser: "Raus aus der Stadt – unter einer Stunde erreichbar", einheit: "Ziele", fertig: false },
  { slug: "wochenendtipps", label: "Wochenendtipps", icon: "local_activity", teaser: "Ein Wochenende weg – unter 4 Stunden Anfahrt", einheit: "Trips", fertig: false },
];

function HubKachel({ hub, anzahl, bild }: { hub: Hub; anzahl: number | null; bild: string | null }) {
  const inhalt = (
    <>
      <div className="gd-hub__bild">
        <div className="gd-hub__motiv">
          {bild ? <BildImg src={bild} alt="" icon={hub.icon} /> : <Icon name={hub.icon} className="gd-hub__platzhalter" />}
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
  return hub.fertig ? (
    <Link href={`/guides/${hub.slug}`} className="gd-hub" role="listitem">{inhalt}</Link>
  ) : (
    <div className="gd-hub gd-hub--bald" role="listitem">{inhalt}</div>
  );
}

/** Kacheln mit echten Zahlen und Foto (Daten gecached über orteLaden). */
async function Kacheln() {
  const restaurants = sortieren(await orteLaden(["restaurant", "cafe"]), "empfohlen");
  const titelbild = restaurants.map(ortBildUrl).find(Boolean) ?? null;
  return (
    <div className="gd-hubs" role="list">
      {HUBS.map((hub) => (
        <HubKachel
          key={hub.slug}
          hub={hub}
          anzahl={hub.slug === "restaurants-cafes" ? restaurants.length : null}
          bild={hub.slug === "restaurants-cafes" ? titelbild : null}
        />
      ))}
    </div>
  );
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
        <Suspense
          fallback={
            <div className="gd-hubs" role="list">
              {HUBS.map((hub) => <HubKachel key={hub.slug} hub={hub} anzahl={null} bild={null} />)}
            </div>
          }
        >
          <Kacheln />
        </Suspense>
      </div>
    </div>
  );
}
