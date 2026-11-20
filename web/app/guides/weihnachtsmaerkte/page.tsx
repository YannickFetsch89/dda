// Guide-Hub Weihnachtsmärkte (Plan docs/plan-weihnachtsmaerkte-2026-11-17.md, 5.2; Stufe 1a)
//
// Aufbau (18.11.2026): Hero, Einleitung, Liste mit Filtern, kleine Märkte, Karte, Sonderzeiten, Linkliste, FAQ.
// Erste HTML-Antwort mit Inhalt: Hero, Einleitung, Liste mit Zeitraum und Badges, Sonderzeiten-Tabelle und FAQ stehen
// außerhalb der Suspense-Grenze bzw. als deren Fallback. „Heute geöffnet“ rechnet nur der Browser (Plan E5). Nur der
// gewählte Tag (?tag=YYYY-MM-DD) wartet auf searchParams und wird auf dem Server gerechnet (noindex, Canonical auf den Hub).
export const instant = false;
import { ROBOTS_INDEX, seitenAlternates } from "@/lib/seo";
import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { BildImg } from "@/components/client";
import { GuideKarteLazy } from "@/components/guide-karte-lazy";
import { GuideEinleitung, GuideSeoText } from "@/components/guide-text";
import { MagazinLesetipp } from "@/components/magazin-verweise";
import { Icon } from "@/components/karten";
import { OrtLinkListe } from "@/components/ort-karten";
import { WM_BILD, WmKarte } from "@/components/wm-karte";
import { istGueltigerTag, plusTage } from "@/lib/datum";
import { umschalten, zahl } from "@/lib/guide-filter";
import { eventPoolLaden } from "@/lib/daten";
import { kanonischerStadtteil } from "@/lib/landing";
import { eventPfad } from "@/lib/pfade";
import { ScrollReihe } from "@/components/scroll-reihe";
import { KalenderToggle } from "@/components/datum-waehler";
import { jsonLdText } from "@/lib/json-ld";
import {
  GEBIETE, SAISON_STANDARD, WM_BASIS as BASIS, WM_STANDARD, aktuelleSaison, badgeChips, gebietVon, wmFilterAktiv, wmFilterHref, wmFilterLesen,
  wmFiltern, wmSortieren, kurzMaerkte, type WmFilter, datumKurz, datumLang, faqWerte, heroZahlen, hubJahr, istMarkt, listenReihenfolge, rolleText,
  sonderTage, sonderZelle, sortieren, wm, wmPfad,
} from "@/lib/weihnachtsmaerkte";
import { heuteKurz, saisonTag, weihnachtsmaerkteLaden } from "@/lib/weihnachtsmaerkte-daten";
import { weihnachtsmaerkteListeJsonLd } from "@/lib/weihnachtsmaerkte-json-ld";
import type { DddOrt, EventPool } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type SP = Record<string, string | string[] | undefined>;

const tagAus = (sp: SP): string | null => {
  const t = Array.isArray(sp.tag) ? sp.tag[0] : sp.tag;
  return istGueltigerTag(t) ? t : null;
};

const BILD_ALT = "Weihnachtsmarkt in Düsseldorf am Abend: beleuchtete Buden und Besucher";

export async function generateMetadata(props: { searchParams: Promise<SP> }): Promise<Metadata> {
  const gefiltert = Object.keys(await props.searchParams).length > 0;
  // Jahr nur während der Saison (5.8); saisonTag ist tagesgenau gecacht, die Funktion liest ohnehin searchParams
  const jahr = hubJahr(await weihnachtsmaerkteLaden(), await saisonTag());
  const titel = `Weihnachtsmärkte in Düsseldorf${jahr ? ` ${jahr}` : ""}: Öffnungszeiten, Karte & Sonderzeiten`;
  const beschreibung =
    "Alle Weihnachtsmärkte in Düsseldorf, Neuss und Ratingen: wer heute geöffnet hat, Sonderzeiten an Totensonntag und Weihnachten, Eisbahn, Riesenrad, Anfahrt.";
  return {
    title: titel,
    description: beschreibung,
    // Canonical immer auf den Hub, auch bei ?tag= (nicht über seitenMetadaten – der Helfer streicht ihn bei noindex)
    alternates: seitenAlternates(BASIS),
    robots: gefiltert ? { index: false, follow: true } : ROBOTS_INDEX,
    openGraph: { title: titel, description: beschreibung, url: BASIS, type: "website", siteName: "dies.das.düsseldorf", locale: "de_DE", images: [{ url: WM_BILD, alt: BILD_ALT }] },
    // Eigenes Twitter-Bild – sonst greift das Standardbild des Layouts (SEO-Prüfung 19.11.2026)
    twitter: { card: "summary_large_image", title: titel, description: beschreibung, images: [{ url: WM_BILD, alt: BILD_ALT }] },
  };
}

function Hero({ alle, jahr }: { alle: DddOrt[]; jahr: string | null }) {
  const h = heroZahlen(alle);
  const attraktionen = alle.filter((o) => wm(o).attraktion).map((o) => rolleText(o));
  const dazu = attraktionen.length ? `, dazu ${[...new Set(attraktionen)].join(" und ")}` : "";
  return (
    <section className="gd-hero gd-hero--abend wm-hero">
      <div className="gd-hero__bild">
        <BildImg src={WM_BILD} alt={BILD_ALT} icon="wm:markt" eager />
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

/**
 * Zeile „Wann“ im Filterkasten (Auftraggeber 18.11.2026): Heute (ohne Parameter), Morgen, Samstag und Sonntag nur im
 * dynamischen Teil, feste Sondertage und der Kalender der übrigen Seiten (statt des Browser-Datumsfelds).
 */
function TagesZeile({ tag, heute, jahr }: { tag: string | null; heute: string | null; jahr: number }) {
  const eintraege: { label: string; datum: string | null }[] = [{ label: "Heute", datum: null }];
  if (heute) {
    eintraege.push({ label: "Morgen", datum: plusTage(heute, 1) });
    const bisSamstag = (6 - new Date(`${heute}T12:00:00Z`).getUTCDay() + 7) % 7 || 7;
    eintraege.push({ label: "Samstag", datum: plusTage(heute, bisSamstag) });
    const bisSonntag = (7 - new Date(`${heute}T12:00:00Z`).getUTCDay()) % 7 || 7;
    eintraege.push({ label: "Sonntag", datum: plusTage(heute, bisSonntag) });
  }
  // Feste Tage ohne Totensonntag, dafür mit 1. Weihnachtstag (Auftraggeber 18.11.2026)
  for (const t of sonderTage(jahr)) if (["Heiligabend", "1. Weihnachtstag", "2. Weihnachtstag", "Silvester"].includes(t.name)) eintraege.push({ label: t.name, datum: t.datum });
  // Ein im Kalender gewählter Tag, der keinem Chip entspricht, markiert den Kalender-Knopf
  const eigenerTag = !!tag && !eintraege.some((e) => e.datum === tag);
  return (
    <div className="gd-zeile wm-tage">
      <span className="gd-zeile__label">Wann</span>
      <ScrollReihe className="gd-zeile__chips" label="Tag wählen">
        {eintraege.map((e) => {
          const aktiv = (e.datum ?? null) === tag;
          return (
            <Link key={e.label} href={e.datum ? `${BASIS}?tag=${e.datum}` : BASIS} scroll={false} className={`gd-chip gd-chip--gross${aktiv ? " gd-chip--an" : ""}`} aria-current={aktiv || undefined}>
              {e.label}{e.datum && !["Morgen", "Samstag", "Sonntag"].includes(e.label) ? <span className="gd-chip__zahl">{datumLang(e.datum).slice(0, 6)}</span> : null}
            </Link>
          );
        })}
      </ScrollReihe>
      <KalenderToggle
        heute={heute ?? tag ?? `${jahr}-11-19`}
        ziel={BASIS}
        param="tag"
        min={`${jahr}-11-01`}
        max={`${jahr + 1}-01-15`}
        gewaehlt={tag ?? undefined}
        mitZeitraum={false}
        scroll={false}
        klasse="wm-tage__kalender"
        knopfKlasse={`gd-chip gd-chip--gross${eigenerTag ? " gd-chip--an" : ""}`}
      />
    </div>
  );
}

function SonderzeitenTabelle({ alle, jahr }: { alle: DddOrt[]; jahr: number }) {
  const tage = sonderTage(jahr);
  const zeilen = listenReihenfolge(alle).flatMap((g) => [g.gruppe, ...g.teile]).filter((o) => !wm(o).gruppe || wm(o).attraktion);
  return (
    <section className="container wm-sonder" aria-labelledby="wm-sonder-titel">
      <h2 className="d" id="wm-sonder-titel">Sonderzeiten auf einen Blick</h2>
      <p className="muted">Die Teilmärkte der Innenstadt haben die Zeiten der Innenstadt.</p>
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
                    // Außerhalb der Saison („–“) ebenfalls „geschlossen“ – übersichtlicher (Auftraggeber 18.11.2026)
                    const roh = sonderZelle(wm(o).saisons, t.datum);
                    const z = roh === "–" ? "geschlossen" : roh;
                    return <td key={t.datum} data-label={t.name} className={`wm-zelle wm-zelle--${z === "geschlossen" ? "zu" : z === "nicht veröffentlicht" ? "offen-unbekannt" : "auf"}`}>{z}</td>;
                  })}
                  <td data-label="Letzter Tag" className="wm-zelle--letzter">{s ? datumKurz(s.bis) : "geschlossen"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

/** Kleine Weihnachtsmärkte an einzelnen Tagen aus dem Eventkalender (4.5, Stufe 1b); entfällt ohne Treffer. */
function KurzMaerkte({ liste }: { liste: ReturnType<typeof kurzMaerkte<EventPool["events"][number]>> }) {
  if (!liste.length) return null;
  return (
    <section className="container wm-kurz" aria-labelledby="wm-kurz-titel">
      <h2 className="d" id="wm-kurz-titel">Kleine Weihnachtsmärkte an einzelnen Tagen</h2>
      <p className="muted">Basare, Adventsmärkte von Vereinen und Kirchengemeinden und andere Märkte, die nur einen oder wenige Tage stattfinden – aus unserem Eventkalender.</p>
      <ul>
        {liste.map((e) => (
          <li key={e.id}>
            {/* Ganze Karte klickbar (Auftraggeber 18.11.2026) */}
            <Link href={eventPfad(e)} className="wm-kurz__karte">
              <span className="wm-kurz__titel">{e.titel}</span>
              <span className="muted">{[datumKurz(e.datum), e.uhrzeit ? `${e.uhrzeit} Uhr` : null, e.ort].filter(Boolean).join(" · ")}</span>
            </Link>
          </li>
        ))}
      </ul>
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

function Chip({ href, aktiv, children, icon }: { href: string; aktiv: boolean; children: React.ReactNode; icon?: string }) {
  return (
    <Link href={href} scroll={false} className={`gd-chip gd-chip--gross ${aktiv ? "gd-chip--an" : ""}`} aria-current={aktiv || undefined}>
      {icon && <Icon name={icon} />}
      {children}
    </Link>
  );
}

/** Filterkasten: Tag, Badges (UND), Gebiet, „an diesem Tag geöffnet“. Keine Sortierwahl – immer „empfohlen“ (18.11.2026). Filter-URLs noindex. */
function Filter({ alle, f, tag, bezugTag, heute, jahr }: { alle: DddOrt[]; f: WmFilter; tag: string | null; bezugTag: string; heute: string | null; jahr: number }) {
  const href = (a: Partial<WmFilter>) => wmFilterHref(f, a, tag);
  const fuerBadges = wmFiltern(alle.filter((o) => !wm(o).ist_gruppe), alle, f, bezugTag, ["badges"]);
  const chips = badgeChips(fuerBadges, alle, f.badges);
  const vorhanden = new Set(alle.map(gebietVon));
  const gebiete = GEBIETE.filter((g) => vorhanden.has(g.wert));
  return (
    <div className="gd-filter wm-filter" id="gd-filter" tabIndex={-1}>
      <div className="gd-filter__innen">
        <TagesZeile tag={tag} heute={heute} jahr={jahr} />
        {chips.length > 0 && (
          <div className="gd-zeile">
            <span className="gd-zeile__label">Was es gibt</span>
            <ScrollReihe className="gd-zeile__chips" label="Besonderheiten">
              {chips.map((c) => (
                <Chip key={c.wert} href={href({ badges: umschalten(f.badges, c.wert) })} aktiv={f.badges.includes(c.wert)} icon={f.badges.includes(c.wert) ? "check" : c.icon}>
                  {c.label}<span className="gd-chip__zahl">{c.anzahl}</span>
                </Chip>
              ))}
            </ScrollReihe>
          </div>
        )}
        {gebiete.length > 1 && (
          <div className="gd-zeile">
            <span className="gd-zeile__label">Wo</span>
            <ScrollReihe className="gd-zeile__chips" label="Gebiet">
              <Chip href={href({ gebiet: null })} aktiv={!f.gebiet}>Alle</Chip>
              {gebiete.map((g) => <Chip key={g.wert} href={href({ gebiet: f.gebiet === g.wert ? null : g.wert })} aktiv={f.gebiet === g.wert}>{g.label}</Chip>)}
            </ScrollReihe>
          </div>
        )}
        <div className="gd-zeile">
          <span className="gd-zeile__label">Öffnung</span>
          <ScrollReihe className="gd-zeile__chips" label="Öffnung">
            <Chip href={href({ offen: !f.offen })} aktiv={f.offen} icon={f.offen ? "check" : "schedule"}>
              {tag ? "An diesem Tag geöffnet" : "Heute geöffnet"}
            </Chip>
          </ScrollReihe>
        </div>
      </div>
    </div>
  );
}

function Legende() {
  return (
    <ul className="wm-legende" aria-label="Farben auf der Karte">
      <li><span className="wm-legende__punkt wm-legende__punkt--offen" aria-hidden />Heute geöffnet</li>
      <li><span className="wm-legende__punkt wm-legende__punkt--zu" aria-hidden />Heute geschlossen</li>
      <li><span className="wm-legende__punkt wm-legende__punkt--saison" aria-hidden />Noch nicht oder nicht mehr in der Saison</li>
      <li><span className="wm-legende__punkt wm-legende__punkt--unbekannt" aria-hidden />Zeit nicht veröffentlicht</li>
    </ul>
  );
}

/**
 * Aufbau (Auftraggeber 18.11.2026): alle Märkte mit Filtern → kleine Märkte an einzelnen Tagen (`kurz`) → Karte.
 * Kein eigener Top-5-Block mehr (bei rund acht Märkten doppelt); die Top-5-Ränge sortieren die Liste weiter nach vorn.
 */
function Ansicht({ alle, tag, heute, f: roh, kurz }: { alle: DddOrt[]; tag: string | null; heute: string | null; f: WmFilter; kurz?: React.ReactNode }) {
  const jahr = Number(heroZahlen(alle).jahr ?? SAISON_STANDARD);
  // Immer nach Empfehlung sortiert (Sortierwahl entfernt, Auftraggeber 18.11.2026); alte ?sort=-Links wirken nicht mehr
  const f: WmFilter = { ...roh, sort: WM_STANDARD.sort };
  // Bezugstag der Filter: gewählter Tag, sonst heute (ohne Uhr im Fallback: Filter „geöffnet“ ist dort nie aktiv)
  const bezugTag = tag ?? heute ?? "";
  const gefiltert = wmFilterAktiv(f);
  const ergebnis = gefiltert ? wmSortieren(wmFiltern(alle.filter((o) => !wm(o).ist_gruppe), alle, f, bezugTag), f.sort) : [];
  const abfrage = wmFilterHref(f, {}, tag).split("?")[1] ?? "";
  return (
    <>
      <div className="container">
        {tag && <p className="gd-status"><span>Zeiten für {datumKurz(tag)}{tag.slice(0, 4)}</span><Link href={BASIS} scroll={false} className="gd-status__reset">Zurück zu heute</Link></p>}
        <Filter alle={alle} f={f} tag={tag} bezugTag={bezugTag} heute={heute} jahr={jahr} />
        {gefiltert ? (
          <>
            <div className="gd-status">
              <span>{zahl(ergebnis.length)} {ergebnis.length === 1 ? "Eintrag" : "Einträge"}</span>
              <Link href={tag ? `${BASIS}?tag=${tag}` : BASIS} scroll={false} className="gd-status__reset">Filter zurücksetzen</Link>
            </div>
            {ergebnis.length ? (
              <div className="gd-grid gd-grid--3 wm-treffer" role="list">{ergebnis.map((o) => <WmKarte key={o.id} o={o} alle={alle} tag={tag} />)}</div>
            ) : (
              <div className="gd-leer">Kein Markt passt zu diesen Filtern. <Link href={BASIS} scroll={false}>Filter zurücksetzen</Link></div>
            )}
          </>
        ) : (
          <Liste alle={alle} tag={tag} />
        )}
      </div>
      {kurz}
      <div className="container">
        <h2 className="d wm-zwischentitel">Alle Märkte auf der Karte</h2>
        <Legende />
        <GuideKarteLazy quelle={`/api/guide-karte?hub=weihnachtsmaerkte${abfrage ? `&${abfrage}` : ""}`} />
      </div>
    </>
  );
}

async function GefilterteAnsicht({ searchParams, alle, kurz }: { searchParams: Promise<SP>; alle: DddOrt[]; kurz: React.ReactNode }) {
  const sp = await searchParams;
  const tag = tagAus(sp);
  await connection(); // Uhr erst zur Anfrage lesen (Morgen/Samstag, „heute geöffnet“), nie beim Vorrendern
  return <Ansicht alle={alle} tag={tag} heute={await heuteKurz()} f={wmFilterLesen(sp)} kurz={kurz} />;
}

export default async function Weihnachtsmaerkte(props: { searchParams: Promise<SP> }) {
  const alle = sortieren(await weihnachtsmaerkteLaden());
  const jahr = Number(heroZahlen(alle).jahr ?? "2026");
  const maerkte = alle.filter(istMarkt);
  // Kleine Märkte (Eventkalender) zwischen Liste und Karte – eigene Suspense-Grenze, die Liste wartet nicht darauf
  // Kleine Märkte schon im ersten HTML (ohne JavaScript sichtbar, Cursor-Prüfung 19.11.2026): der Event-Pool ist gecacht
  const pool = await eventPoolLaden();
  const kurz = <KurzMaerkte liste={kurzMaerkte(pool.events, alle, pool.heute, kanonischerStadtteil)} />;
  return (
    <div className="gd-seite wm-seite">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(weihnachtsmaerkteListeJsonLd(alle, SITE_URL)) }} />
      <Hero alle={alle} jahr={hubJahr(alle, await saisonTag())} />
      <div className="container">
        <GuideEinleitung seite="weihnachtsmaerkte" werte={{ anzahl: zahl(maerkte.length) }} />
        <MagazinLesetipp guide="weihnachtsmaerkte" />
      </div>
      <Suspense fallback={<Ansicht alle={alle} tag={null} heute={null} f={WM_STANDARD} kurz={kurz} />}>
        <GefilterteAnsicht searchParams={props.searchParams} alle={alle} kurz={kurz} />
      </Suspense>
      <SonderzeitenTabelle alle={alle} jahr={jahr} />
      <div className="container">
        <OrtLinkListe orte={alle} alleHref={BASIS} max={200} pfad={wmPfad} typLabel={rolleText} einheit="Märkte und Attraktionen" />
      </div>
      <GuideSeoText seite="weihnachtsmaerkte" werte={{ anzahl: zahl(maerkte.length), ...faqWerte(alle, wmFilterHref(WM_STANDARD, { badges: ["familien"] })) }} />
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
