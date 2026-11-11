// Gemeinsame Bausteine der Landingpages (Kategorie, Stadtteil, Guide-Stadtteil) – SEO-/GEO-Plan Phase B.
// Alles ohne Suspense: H1, Text, Satz mit der Live-Zahl und die Einträge stehen im ersten HTML.
import Link from "next/link";
import { EventKarte, Icon, Leer, ListenZeile } from "./karten";
import { tagKurz } from "@/lib/datum";
import { jsonLdText } from "@/lib/json-ld";
import type { DddEvent } from "@/lib/typen";

export interface Krume {
  name: string;
  pfad?: string;
}

/** Sichtbare Brotkrumen (dieselben Stationen wie die BreadcrumbList im JSON-LD). */
export function Krumen({ teile }: { teile: Krume[] }) {
  return (
    <nav className="gd-krumen" aria-label="Brotkrumen">
      {teile.map((t, i) => (
        <span key={t.name} style={{ display: "contents" }}>
          {i > 0 && <span>/</span>}
          {t.pfad && i < teile.length - 1 ? <Link href={t.pfad}>{t.name}</Link> : <span aria-current="page">{t.name}</span>}
        </span>
      ))}
    </nav>
  );
}

export function JsonLd({ daten }: { daten: unknown }) {
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(daten) }} />;
}

/** Querverweise als schlichte Link-Chips. */
export function LinkChips({ titel, links }: { titel: string; links: { name: string; pfad: string; anzahl?: number }[] }) {
  if (!links.length) return null;
  return (
    <section className="sektion landing__links" aria-label={titel}>
      <h2 className="d">{titel}</h2>
      <div className="filterleiste">
        {links.map((l) => (
          <Link key={l.pfad} href={l.pfad} className="chip">
            {l.name}
            {l.anzahl !== undefined && <small>{l.anzahl}</small>}
          </Link>
        ))}
      </div>
    </section>
  );
}

/** Kommende Events: die ersten als Karten, der Rest als kompakte Zeilen (wenig HTML, alles als Text). */
export function EventListe({ events, heute, karten = 8, max = 80, leer }: { events: DddEvent[]; heute: string; karten?: number; max?: number; leer: string }) {
  if (!events.length) {
    return (
      <div className="sektion">
        <Leer titel={leer}>
          <Link href="/heute" className="link">
            Was heute in Düsseldorf los ist <Icon name="arrow_forward" />
          </Link>
        </Leer>
      </div>
    );
  }
  const oben = events.slice(0, karten);
  const rest = events.slice(karten, max);
  return (
    <>
      <div className="sektion raster" role="list">
        {oben.map((e) => (
          <EventKarte key={e.id} e={e} heute={heute} variante="grid" />
        ))}
      </div>
      {rest.length > 0 && (
        <div className="sektion reihe__termine">
          {rest.map((e) => (
            <ListenZeile key={e.id} e={e} zeit={tagKurz(e.datum)} />
          ))}
        </div>
      )}
    </>
  );
}
