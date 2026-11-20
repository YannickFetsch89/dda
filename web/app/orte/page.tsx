// Übersicht /orte (Plan docs/plan-locations-2026-11-18.md, 3.8, 3.11): A–Z und Suche, Filter nach Art, Stadt und
// Stadtteil über Query-Parameter. Canonical immer /orte; gefilterte Ansichten noindex – beides von Hand gesetzt, nicht
// über seitenMetadaten (dessen noindex-Flag streicht den Canonical). Kein 301 auf eigene Landingpages.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { GuideKarteLazy } from "@/components/guide-karte-lazy";
import { Icon } from "@/components/karten";
import { brotkrumenJsonLd } from "@/lib/kneipen-json-ld";
import { jsonLdText } from "@/lib/json-ld";
import { ROBOTS_INDEX, seitenAlternates } from "@/lib/seo";
import {
  ARTEN, ORTE_BASIS, artInfo, buchstabe, filterAktiv, filterLesen, orteFiltern, ortSeitePfad, profil, stadtVon,
  type OrteFilter,
} from "@/lib/spielstaetten";
import { spielstaettenLaden, type Spielstaette } from "@/lib/spielstaetten-daten";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type SP = Record<string, string | string[] | undefined>;
const TITEL = "Veranstaltungsorte in Düsseldorf";
const BESCHREIBUNG =
  "Theater, Konzertsäle, Museen, Kinos, Clubs und Kulturzentren in Düsseldorf, Neuss und Ratingen – mit Programm, Adresse und Karte.";
const LEER: OrteFilter = { art: null, stadt: null, stadtteil: null, q: null };

export async function generateMetadata(props: { searchParams: Promise<SP> }): Promise<Metadata> {
  const gefiltert = Object.values(await props.searchParams).some((v) => v !== undefined && v !== "");
  return {
    title: TITEL,
    description: BESCHREIBUNG,
    alternates: seitenAlternates(ORTE_BASIS),
    robots: gefiltert ? { index: false, follow: true } : ROBOTS_INDEX,
    openGraph: { title: TITEL, description: BESCHREIBUNG, url: ORTE_BASIS, type: "website", siteName: "dies.das.düsseldorf", locale: "de_DE" },
  };
}

function abfrage(f: OrteFilter): string {
  const p = new URLSearchParams();
  if (f.art) p.set("art", f.art);
  if (f.stadt) p.set("stadt", f.stadt);
  if (f.stadtteil) p.set("stadtteil", f.stadtteil);
  if (f.q) p.set("q", f.q);
  return p.toString();
}

function Ansicht({ alle, f, fehler }: { alle: Spielstaette[]; f: OrteFilter; fehler: boolean }) {
  const haeuser = alle.filter((o) => !o.parentId);
  const kinder = new Map<string, Spielstaette[]>();
  for (const o of alle) if (o.parentId) kinder.set(o.parentId, [...(kinder.get(o.parentId) ?? []), o]);
  const treffer = orteFiltern(haeuser, f);
  const stadtteile = [...new Set(haeuser.filter((o) => stadtVon(o) === "Düsseldorf" && o.stadtteil).map((o) => o.stadtteil!))].sort((a, b) => a.localeCompare(b, "de"));
  const arten = ARTEN.filter((a) => haeuser.some((o) => profil(o).art === a.wert));
  const gruppen = new Map<string, Spielstaette[]>();
  for (const o of treffer) gruppen.set(buchstabe(o.name), [...(gruppen.get(buchstabe(o.name)) ?? []), o]);
  const q = abfrage(f);

  return (
    <>
      <form className="os-filter" action={ORTE_BASIS} method="get">
        <label className="os-filter__feld">
          <span>Suche</span>
          <input type="search" name="q" defaultValue={f.q ?? ""} placeholder="Name eines Ortes" />
        </label>
        <label className="os-filter__feld">
          <span>Art</span>
          <select name="art" defaultValue={f.art ?? ""}>
            <option value="">Alle Arten</option>
            {arten.map((a) => <option key={a.slug} value={a.slug}>{a.wert}</option>)}
          </select>
        </label>
        <label className="os-filter__feld">
          <span>Stadt</span>
          <select name="stadt" defaultValue={f.stadt ?? ""}>
            <option value="">Alle</option>
            {["Düsseldorf", "Neuss", "Ratingen"].map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label className="os-filter__feld">
          <span>Stadtteil (Düsseldorf)</span>
          <select name="stadtteil" defaultValue={f.stadtteil ?? ""}>
            <option value="">Alle Stadtteile</option>
            {stadtteile.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <button type="submit" className="gd-knopf gd-knopf--navy"><Icon name="filter_list" />Anzeigen</button>
        {filterAktiv(f) && <Link href={ORTE_BASIS} className="link">Filter zurücksetzen</Link>}
      </form>

      {fehler && <p className="muted">Die Liste ist gerade unvollständig. Bitte später noch einmal versuchen.</p>}
      <p className="muted os-zahl">{treffer.length} Orte</p>

      {treffer.length > 0 && (
        <section className="gd-abschnitt">
          <h2 className="d">Karte</h2>
          <GuideKarteLazy quelle={`/api/guide-karte?hub=orte${q ? `&${q}` : ""}`} />
        </section>
      )}

      <nav className="os-az" aria-label="Buchstaben">
        {[...gruppen.keys()].map((b) => <a key={b} href={`#b-${b}`}>{b}</a>)}
      </nav>
      {[...gruppen.entries()].map(([b, orte]) => (
        <section key={b} id={`b-${b}`} className="os-gruppe">
          <h2 className="os-gruppe__buchstabe">{b}</h2>
          <ul className="os-orte">
            {orte.map((o) => {
              const info = artInfo(profil(o).art);
              return (
                <li key={o.id}>
                  <Link href={ortSeitePfad(o.slug)} className="os-ort">
                    <Icon name={info.icon} />
                    <span className="os-ort__name">{o.name}</span>
                    <span className="muted os-ort__zusatz">{[info.wert, o.stadtteil ?? stadtVon(o)].filter(Boolean).join(" · ")}</span>
                  </Link>
                  {(kinder.get(o.id) ?? []).length > 0 && (
                    <ul className="os-orte os-orte--saele">
                      {kinder.get(o.id)!.map((k) => <li key={k.id}><Link href={ortSeitePfad(k.slug)}>{k.name}</Link></li>)}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      ))}
      {!treffer.length && <p className="muted">Keine Orte zu dieser Auswahl.</p>}
    </>
  );
}

async function GefilterteAnsicht({ searchParams, alle, fehler }: { searchParams: Promise<SP>; alle: Spielstaette[]; fehler: boolean }) {
  return <Ansicht alle={alle} f={filterLesen(await searchParams)} fehler={fehler} />;
}

export default async function OrteSeite(props: { searchParams: Promise<SP> }) {
  const { orte, fehler } = await spielstaettenLaden();
  const jsonLd = brotkrumenJsonLd(SITE_URL, [{ name: "Start", pfad: "/" }, { name: "Orte", pfad: ORTE_BASIS }]);
  return (
    <div className="container gd-seite os-seite">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link><span>/</span><span aria-current="page">Orte</span>
      </nav>
      <h1 className="d">{TITEL}</h1>
      <p className="os-einleitung">
        Wo in Düsseldorf, Neuss und Ratingen etwas los ist: Theater, Säle, Museen, Kinos und Kulturorte mit ihrem
        Programm aus unserem Eventkalender. Restaurants, Kneipen, Clubs und Spielplätze findest du in den <Link href="/guides">Guides</Link>.
      </p>
      <Suspense fallback={<Ansicht alle={orte} f={LEER} fehler={fehler} />}>
        <GefilterteAnsicht searchParams={props.searchParams} alle={orte} fehler={fehler} />
      </Suspense>
    </div>
  );
}
