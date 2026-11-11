// Guide-Hub Clubs (Design-Handoff v2, Ansicht 22; Plan docs/plan-clubs-2026-11-11.md)
//
// Erste HTML-Antwort mit Inhalt (SEO/GEO): Hero und die UNGEFILTERTE Ansicht stehen im statischen Shell.
// Nur die filterabhängige Ansicht wartet in <Suspense> auf searchParams – ihr Fallback ist die ungefilterte.
// Wenige Orte → alle Karten auf einer Seite (kein „Weitere laden“), keine Kartenansicht.
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { BildImg } from "@/components/client";
import { ClubKarte } from "@/components/club-karte";
import { Icon } from "@/components/karten";
import { ScrollReihe } from "@/components/scroll-reihe";
import {
  CLUB_ARTEN, CLUB_SORTIERUNGEN, CLUB_STANDARD, EINTRITT_STUFEN, clubArt, clubFilterHref, clubFilterLesen,
  clubHatParameter, clubsFiltern, clubsSortieren, eintrittStufe, genreName, genresZaehlen, type ClubArt, type ClubFilter,
} from "@/lib/clubs";
import { clubsLaden, naechsteEvents } from "@/lib/clubs-daten";
import { clubsListeJsonLd } from "@/lib/clubs-json-ld";
import { eventPoolLaden } from "@/lib/daten";
import { stadtteileText, umschalten, zaehlen, zahl } from "@/lib/guide-filter";
import { jsonLdText } from "@/lib/json-ld";
import type { DddEvent, DddOrt } from "@/lib/typen";

const BASIS = "/guides/clubs";
const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type SP = Record<string, string | string[] | undefined>;

const BESCHREIBUNG =
  "Clubs, Kulturhäuser und Partylocations in Düsseldorf, Neuss und Ratingen – mit Musikrichtungen, Partyreihen, Eintritt und den nächsten Events.";
/** Eintritts-Filter erst, wenn genug Orte einen belegten Preis haben. */
const MIN_FUER_EINTRITT = 6;

export async function generateMetadata(props: { searchParams: Promise<SP> }): Promise<Metadata> {
  const gefiltert = clubHatParameter(await props.searchParams);
  return {
    title: "Clubs in Düsseldorf",
    description: BESCHREIBUNG,
    alternates: { canonical: BASIS },
    robots: gefiltert ? { index: false, follow: true } : undefined,
    openGraph: { title: "Clubs in Düsseldorf", description: BESCHREIBUNG, url: BASIS, type: "website", siteName: "dies.das.düsseldorf", locale: "de_DE", images: [{ url: "/guides/clubs.webp" }] },
  };
}

function Hero({ orte }: { orte: DddOrt[] }) {
  return (
    <section className="gd-hero cl-hero">
      <div className="gd-hero__bild">
        <BildImg src="/guides/clubs.webp" alt="" icon="nightlife" eager />
      </div>
      <div className="cl-hero__licht" aria-hidden />
      <div className="gd-hero__inhalt container">
        <nav className="gd-krumen gd-krumen--hell" aria-label="Brotkrumen">
          <Link href="/">Start</Link><span>/</span><Link href="/guides">Düsseldorf entdecken</Link><span>/</span>
          <span aria-current="page">Clubs</span>
        </nav>
        <h1 className="d">Clubs in Düsseldorf</h1>
        <p>{orte.length ? `${zahl(orte.length)} Clubs und Partyorte – von Techno bis Schlager` : "Kuratierte Empfehlungen – bald verfügbar"}</p>
      </div>
    </section>
  );
}

function Chip({ href, aktiv, children, icon, gross = false }: { href: string; aktiv: boolean; children: React.ReactNode; icon?: string; gross?: boolean }) {
  return (
    <Link href={href} scroll={false} className={`${gross ? "cl-genre-chip" : "gd-chip gd-chip--gross"} ${aktiv ? (gross ? "cl-genre-chip--an" : "gd-chip--an") : ""}`} aria-current={aktiv || undefined}>
      {icon && <Icon name={icon} />}
      {children}
    </Link>
  );
}

function Ansicht({ alle, f, naechste }: { alle: DddOrt[]; f: ClubFilter; naechste: Map<string, DddEvent> }) {
  const href = (a: Partial<ClubFilter>) => clubFilterHref(BASIS, f, a);
  const ergebnis = clubsSortieren(clubsFiltern(alle, f), f.sort);

  const fuerArt = clubsFiltern(alle, f, ["arten"]);
  const artUmschalten = (w: ClubArt) => {
    const neu = umschalten(f.arten, w);
    return neu.length === CLUB_ARTEN.length ? [] : neu;
  };
  const artTabs = [
    { label: "Alle", icon: undefined as string | undefined, anzahl: fuerArt.length, href: href({ arten: [] }), aktiv: !f.arten.length },
    ...CLUB_ARTEN.map((a) => ({
      label: a.mehrzahl, icon: a.icon, anzahl: fuerArt.filter((o) => clubArt(o) === a.wert).length,
      href: href({ arten: artUmschalten(a.wert) }), aktiv: f.arten.includes(a.wert),
    })),
  ].filter((t) => t.anzahl > 0 || t.aktiv);
  const genres = genresZaehlen(clubsFiltern(alle, f, ["genres"])).filter((g) => g.anzahl > 0 || f.genres.includes(g.slug));
  const stadtteile = zaehlen(clubsFiltern(alle, f, ["stadtteile"]), (o) => o.stadtteil);
  const mitPreis = alle.filter((o) => eintrittStufe(o)).length;
  const stadtteilName = (slug: string) => stadtteile.find((s) => s.slug === slug)?.name ?? slug;

  const status = [
    `${zahl(ergebnis.length)} ${ergebnis.length === 1 ? "Ergebnis" : "Ergebnisse"}${stadtteileText(f.stadtteile, stadtteilName)}`,
    ...(f.arten.length ? [CLUB_ARTEN.filter((a) => f.arten.includes(a.wert)).map((a) => a.mehrzahl).join(" & ")] : []),
    ...(f.genres.length ? [f.genres.map(genreName).join(" oder ")] : []),
    ...(f.eintritt ? [EINTRITT_STUFEN.find((s) => s.wert === f.eintritt)!.label] : []),
  ].join(" · ");
  const gefiltert = f.arten.length > 0 || f.genres.length > 0 || f.stadtteile.length > 0 || f.eintritt !== null;
  const sortLabel = CLUB_SORTIERUNGEN.find((s) => s.wert === f.sort)?.label ?? "Empfohlen";

  return (
    <>
      <div className="gd-filter gd-filter--abend cl-filter" id="gd-filter" tabIndex={-1}>
        <div className="container gd-filter__innen">
          <ScrollReihe className="cl-genres" label="Musikrichtung">
            {genres.map((g) => (
              <Chip key={g.slug} gross href={href({ genres: umschalten(f.genres, g.slug) })} aktiv={f.genres.includes(g.slug)} icon={g.icon}>
                {g.name}<span className="gd-chip__zahl">{g.anzahl}</span>
              </Chip>
            ))}
          </ScrollReihe>

          {artTabs.length > 2 && (
            <ScrollReihe className="gd-typen" label="Art">
              {artTabs.map((t) => (
                <Link key={t.label} href={t.href} scroll={false} className={`gd-typ-tab ${t.aktiv ? "gd-chip--an" : ""}`} aria-current={t.aktiv || undefined}>
                  {t.icon && <Icon name={t.icon} />}
                  {t.label}
                  <span className="gd-chip__zahl">{zahl(t.anzahl)}</span>
                </Link>
              ))}
            </ScrollReihe>
          )}

          <div className="gd-zeile">
            <span className="gd-zeile__label">Stadtteil</span>
            <ScrollReihe className="gd-zeile__chips" label="Stadtteile">
              <Chip href={href({ stadtteile: [] })} aktiv={!f.stadtteile.length}>Alle</Chip>
              {stadtteile.map((s) => (
                <Chip key={s.slug} href={href({ stadtteile: umschalten(f.stadtteile, s.slug) })} aktiv={f.stadtteile.includes(s.slug)}>
                  {s.name}<span className="gd-chip__zahl">{s.anzahl}</span>
                </Chip>
              ))}
            </ScrollReihe>
          </div>

          {mitPreis >= MIN_FUER_EINTRITT && (
            <div className="gd-zeile">
              <span className="gd-zeile__label">Eintritt</span>
              <ScrollReihe className="gd-zeile__chips" label="Eintritt" aktivZeigen={false}>
                {EINTRITT_STUFEN.map((s) => (
                  <Chip key={s.wert} href={href({ eintritt: f.eintritt === s.wert ? null : s.wert })} aktiv={f.eintritt === s.wert}>{s.label}</Chip>
                ))}
              </ScrollReihe>
            </div>
          )}

          <div className="gd-filter__fuss">
            <details className="gd-sort">
              <summary>
                <Icon name="sort" className="muted" />
                <span className="gd-sort__label muted">Sortieren:</span>
                <b>{sortLabel}</b>
                <Icon name="expand_more" />
              </summary>
              <div className="gd-menue">
                {CLUB_SORTIERUNGEN.map((s) => (
                  <Link key={s.wert} href={href({ sort: s.wert })} scroll={false} className={s.wert === f.sort ? "is-aktiv" : ""}>{s.label}</Link>
                ))}
              </div>
            </details>
          </div>
        </div>
      </div>

      <div className="container">
        <div className="gd-status">
          <span>{status}</span>
          {gefiltert && <Link href={BASIS} scroll={false} className="gd-status__reset">Filter zurücksetzen</Link>}
        </div>
        {ergebnis.length === 0 ? (
          <div className="gd-leer">
            Kein Club mit diesen Filtern. <Link href={BASIS} scroll={false}>Filter zurücksetzen</Link>
          </div>
        ) : (
          <div className="cl-grid" role="list">
            {ergebnis.map((o) => <ClubKarte key={o.id} o={o} naechstes={naechste.get(o.id)} />)}
          </div>
        )}
        <p className="cl-hinweis muted">
          Musikrichtungen, Reihen und Preise stammen aus den Websites der Clubs, Stadtmagazinen und unserem Eventkalender –
          jede Angabe mit Quelle geprüft. Die Reihenfolge „Empfohlen“ folgt unserem Club-Score aus Programm, Szene,
          Profil und Beliebtheit.
        </p>
      </div>
    </>
  );
}

async function GefilterteAnsicht({ searchParams, alle, naechste }: { searchParams: Promise<SP>; alle: DddOrt[]; naechste: Map<string, DddEvent> }) {
  return <Ansicht alle={alle} f={clubFilterLesen(await searchParams)} naechste={naechste} />;
}

export default async function Clubs(props: { searchParams: Promise<SP> }) {
  const [orte, pool] = await Promise.all([clubsLaden(), eventPoolLaden()]);
  const alle = clubsSortieren(orte, "empfohlen");
  const naechste = new Map<string, DddEvent>();
  for (const o of alle) {
    const [e] = naechsteEvents(o, pool, 1);
    if (e) naechste.set(o.id, e);
  }
  return (
    <div className="gd-seite gd-seite--abend cl-seite">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(clubsListeJsonLd(alle, SITE_URL, BASIS)) }} />
      <Hero orte={alle} />
      <Suspense fallback={<Ansicht alle={alle} f={CLUB_STANDARD} naechste={naechste} />}>
        <GefilterteAnsicht searchParams={props.searchParams} alle={alle} naechste={naechste} />
      </Suspense>
    </div>
  );
}
