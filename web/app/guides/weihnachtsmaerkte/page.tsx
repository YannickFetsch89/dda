// Guide-Hub Weihnachtsmärkte (Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, 5.2; Stufe 1a)
//
// Erste HTML-Antwort mit Inhalt: Hero, Einleitung, Liste mit Zeitraum und Badges, Sonderzeiten-Tabelle und FAQ stehen
// außerhalb der Suspense-Grenze bzw. als deren Fallback. „Heute geöffnet“ rechnet nur der Browser (Plan E5). Nur der
// gewählte Tag (?tag=YYYY-MM-DD) wartet auf searchParams und wird auf dem Server gerechnet (noindex, Canonical auf den Hub).
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { BildImg } from "@/components/client";
import { GuideKarteLazy } from "@/components/guide-karte-lazy";
import { GuideEinleitung, GuideSeoText } from "@/components/guide-text";
import { Icon } from "@/components/karten";
import { OrtLinkListe } from "@/components/ort-karten";
import { WM_BILD, WmKarte } from "@/components/wm-karte";
import { istGueltigerTag, plusTage } from "@/lib/datum";
import { zahl } from "@/lib/guide-filter";
import { jsonLdText } from "@/lib/json-ld";
import {
  WM_BASIS as BASIS, aktuelleSaison, datumKurz, datumLang, faqWerte, heroZahlen, hubJahr, istMarkt, listenReihenfolge, rolleText,
  sonderTage, sonderZelle, sortieren, topFuenf, wm, wmPfad,
} from "@/lib/weihnachtsmaerkte";
import { heuteKurz, saisonTag, weihnachtsmaerkteLaden } from "@/lib/weihnachtsmaerkte-daten";
import { weihnachtsmaerkteListeJsonLd } from "@/lib/weihnachtsmaerkte-json-ld";
import type { DddOrt } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type SP = Record<string, string | string[] | undefined>;

const tagAus = (sp: SP): string | null => {
  const t = Array.isArray(sp.tag) ? sp.tag[0] : sp.tag;
  return istGueltigerTag(t) ? t : null;
};

export async function generateMetadata(props: { searchParams: Promise<SP> }): Promise<Metadata> {
  const gefiltert = Object.keys(await props.searchParams).length > 0;
  // Jahr nur während der Saison (5.8); saisonTag ist tagesgenau gecacht, die Funktion liest ohnehin searchParams
  const jahr = hubJahr(await weihnachtsmaerkteLaden(), await saisonTag());
  const titel = `Weihnachtsmärkte in Düsseldorf${jahr ? ` ${jahr}` : ""}: Öffnungszeiten, Karte & Sonderzeiten`;
  const beschreibung =
    "Alle Weihnachtsmärkte in Düsseldorf auf einen Blick: wer heute geöffnet hat, Sonderzeiten an Totensonntag und Weihnachten, Eisbahn, Riesenrad, Anfahrt.";
  return {
    title: titel,
    description: beschreibung,
    // Canonical immer auf den Hub, auch bei ?tag= (nicht über seitenMetadaten – der Helfer streicht ihn bei noindex)
    alternates: { canonical: BASIS },
    robots: gefiltert ? { index: false, follow: true } : undefined,
    openGraph: { title: titel, description: beschreibung, url: BASIS, type: "website", siteName: "dies.das.düsseldorf", locale: "de_DE", images: [{ url: WM_BILD }] },
  };
}

function Hero({ alle, jahr }: { alle: DddOrt[]; jahr: string | null }) {
  const h = heroZahlen(alle);
  const attraktionen = alle.filter((o) => wm(o).attraktion).map((o) => rolleText(o));
  const dazu = attraktionen.length ? `, dazu ${[...new Set(attraktionen)].join(" und ")}` : "";
  return (
    <section className="gd-hero gd-hero--abend wm-hero">
      <div className="gd-hero__bild">
        <BildImg src={WM_BILD} alt="" icon="storefront" eager />
      </div>
      <div className="gd-hero__verlauf" aria-hidden />
      <div className="gd-hero__inhalt container">
        <nav className="gd-krumen" aria-label="Brotkrumen">
          <Link href="/">Start</Link><span>/</span><Link href="/guides">Düsseldorf entdecken</Link><span>/</span>
          <span aria-current="page">Weihnachtsmärkte</span>
        </nav>
        <h1 className="d">Weihnachtsmärkte in Düsseldorf{jahr ? ` ${jahr}` : ""}</h1>
        <p>
          {h.anzahl && h.von && h.bis
            ? `${zahl(h.anzahl)} Märkte vom ${datumLang(h.von).slice(0, 6)} bis ${datumLang(h.bis)}${dazu}`
            : "Die Termine folgen, sobald die Veranstalter sie veröffentlichen"}
        </p>
      </div>
    </section>
  );
}

/** Tagesleiste: Heute (ohne Parameter), Morgen und Samstag nur im dynamischen Teil, feste Sondertage, Datum wählen. */
function Tagesleiste({ tag, heute, jahr }: { tag: string | null; heute: string | null; jahr: number }) {
  const eintraege: { label: string; datum: string | null }[] = [{ label: "Heute", datum: null }];
  if (heute) {
    eintraege.push({ label: "Morgen", datum: plusTage(heute, 1) });
    const bisSamstag = (6 - new Date(`${heute}T12:00:00Z`).getUTCDay() + 7) % 7 || 7;
    eintraege.push({ label: "Samstag", datum: plusTage(heute, bisSamstag) });
  }
  for (const t of sonderTage(jahr)) if (["Totensonntag", "Heiligabend", "2. Weihnachtstag", "Silvester"].includes(t.name)) eintraege.push({ label: t.name, datum: t.datum });
  return (
    <nav className="wm-tage" aria-label="Tag wählen">
      <ul>
        {eintraege.map((e) => {
          const aktiv = (e.datum ?? null) === tag;
          return (
            <li key={e.label}>
              <Link href={e.datum ? `${BASIS}?tag=${e.datum}` : BASIS} scroll={false} className={`gd-chip gd-chip--gross${aktiv ? " gd-chip--an" : ""}`} aria-current={aktiv || undefined}>
                {e.label}{e.datum && e.label !== "Morgen" && e.label !== "Samstag" ? <span className="gd-chip__zahl">{datumLang(e.datum).slice(0, 6)}</span> : null}
              </Link>
            </li>
          );
        })}
      </ul>
      <form action={BASIS} method="get" className="wm-tage__form">
        <label htmlFor="wm-tag">Datum wählen</label>
        <input id="wm-tag" type="date" name="tag" defaultValue={tag ?? undefined} min={`${jahr}-11-01`} max={`${jahr + 1}-01-15`} />
        <button type="submit" className="gd-knopf">Anzeigen</button>
      </form>
    </nav>
  );
}

function SonderzeitenTabelle({ alle, jahr }: { alle: DddOrt[]; jahr: number }) {
  const tage = sonderTage(jahr);
  const zeilen = listenReihenfolge(alle).flatMap((g) => [g.gruppe, ...g.teile]).filter((o) => !wm(o).gruppe || wm(o).attraktion);
  return (
    <section className="container wm-sonder" aria-labelledby="wm-sonder-titel">
      <h2 className="d" id="wm-sonder-titel">Sonderzeiten auf einen Blick</h2>
      <p className="muted">
        Nur Zeiten, die die Veranstalter veröffentlicht haben. „–“ heißt: An diesem Tag läuft der Markt nicht (noch nicht oder nicht mehr).
        Die Teilmärkte der Innenstadt haben die Zeiten der Innenstadt.
      </p>
      <div className="wm-sonder__rahmen">
        <table className="wm-sonder__tabelle">
          <thead>
            <tr>
              <th scope="col">Markt</th>
              {tage.map((t) => <th key={t.datum} scope="col">{t.name}<span className="muted"> {datumLang(t.datum).slice(0, 6)}</span></th>)}
              <th scope="col">Letzter Tag</th>
            </tr>
          </thead>
          <tbody>
            {zeilen.map((o) => {
              const s = aktuelleSaison(wm(o).saisons);
              return (
                <tr key={o.id}>
                  <th scope="row"><Link href={wmPfad(o)}>{o.name}</Link></th>
                  {tage.map((t) => {
                    const z = sonderZelle(wm(o).saisons, t.datum);
                    return <td key={t.datum} data-label={t.name} className={`wm-zelle wm-zelle--${z === "geschlossen" ? "zu" : z === "–" ? "leer" : z === "nicht veröffentlicht" ? "offen-unbekannt" : "auf"}`}>{z}</td>;
                  })}
                  <td data-label="Letzter Tag">{s ? datumKurz(s.bis) : "–"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Liste({ alle, tag }: { alle: DddOrt[]; tag: string | null }) {
  return (
    <div className="wm-liste">
      {listenReihenfolge(alle).map(({ gruppe, teile }) => (
        <div key={gruppe.id} className={teile.length ? "wm-gruppe" : "wm-einzeln"}>
          <WmKarte o={gruppe} alle={alle} tag={tag} />
          {teile.length > 0 && (
            <div className="wm-gruppe__teile" role="list" aria-label={`Märkte und Attraktionen: ${gruppe.name}`}>
              {teile.map((t) => <WmKarte key={t.id} o={t} alle={alle} tag={tag} klein />)}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function Ansicht({ alle, tag, heute }: { alle: DddOrt[]; tag: string | null; heute: string | null }) {
  const jahr = Number(heroZahlen(alle).jahr ?? "2026");
  // Top 5 (Stufe 1b): nur mit fünf Rängen und nur bis zum 30.12. (Plan 5.5/5.8)
  const top = heute && heute.slice(5) <= "12-30" && heute.slice(5) >= "10-01" ? topFuenf(alle) : [];
  return (
    <>
      <div className="container">
        <Tagesleiste tag={tag} heute={heute} jahr={jahr} />
        {tag && <p className="gd-status"><span>Zeiten für {datumKurz(tag)}{tag.slice(0, 4)}</span><Link href={BASIS} scroll={false} className="gd-status__reset">Zurück zu heute</Link></p>}
        {top.length === 5 && (
          <section className="wm-top" aria-labelledby="wm-top-titel">
            <h2 className="d" id="wm-top-titel">Unsere Top 5</h2>
            <div className="gd-grid gd-grid--3" role="list">{top.map((o) => <WmKarte key={o.id} o={o} alle={alle} tag={tag} />)}</div>
          </section>
        )}
        <Liste alle={alle} tag={tag} />
      </div>
    </>
  );
}

async function GefilterteAnsicht({ searchParams, alle }: { searchParams: Promise<SP>; alle: DddOrt[] }) {
  const tag = tagAus(await searchParams);
  await connection(); // Uhr erst zur Anfrage lesen (Morgen/Samstag, Top-5-Fenster), nie beim Vorrendern
  return <Ansicht alle={alle} tag={tag} heute={await heuteKurz()} />;
}

export default async function Weihnachtsmaerkte(props: { searchParams: Promise<SP> }) {
  const alle = sortieren(await weihnachtsmaerkteLaden());
  const jahr = Number(heroZahlen(alle).jahr ?? "2026");
  const maerkte = alle.filter(istMarkt);
  return (
    <div className="gd-seite wm-seite">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(weihnachtsmaerkteListeJsonLd(alle, SITE_URL)) }} />
      <Hero alle={alle} jahr={hubJahr(alle, await saisonTag())} />
      <div className="container">
        <GuideEinleitung seite="weihnachtsmaerkte" werte={{ anzahl: zahl(maerkte.length) }} />
      </div>
      <Suspense fallback={<Ansicht alle={alle} tag={null} heute={null} />}>
        <GefilterteAnsicht searchParams={props.searchParams} alle={alle} />
      </Suspense>
      <div className="container">
        <h2 className="d wm-zwischentitel">Alle Märkte auf der Karte</h2>
        <GuideKarteLazy quelle="/api/guide-karte?hub=weihnachtsmaerkte" />
        <OrtLinkListe orte={alle} alleHref={BASIS} max={200} pfad={wmPfad} typLabel={rolleText} einheit="Märkte und Attraktionen" />
      </div>
      <SonderzeitenTabelle alle={alle} jahr={jahr} />
      <GuideSeoText seite="weihnachtsmaerkte" werte={{ anzahl: zahl(maerkte.length), ...faqWerte(alle) }} />
      <div className="container wm-quellen muted">
        <p>
          <Icon name="info" /> Zeiten und Angaben laut Veranstaltern und Düsseldorf Tourismus (visitduesseldorf.de); Beschreibungen in eigenen Worten.
          Kartendaten © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap-Mitwirkende</a>.
        </p>
        <p>Angaben ohne Gewähr. Die Veranstalter können Zeiten kurzfristig ändern, etwa bei Sturm – im Zweifel vorher auf der Seite des Veranstalters nachsehen.</p>
      </div>
    </div>
  );
}
