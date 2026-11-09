// Guide-Hub Kneipen & Bars (Design-Handoff v2, Ansichten 18 und 19)
//
// Erste HTML-Antwort mit Inhalt (SEO/GEO): Hero und die UNGEFILTERTE Ansicht stehen im statischen Shell
// (Daten über orteLaden, "use cache"). Nur die filterabhängige Ansicht wartet in <Suspense> auf
// searchParams – ihr Fallback ist genau diese ungefilterte Ansicht. Standard ist die Kartenansicht;
// die Karte selbst entsteht im Browser, darunter stehen alle Orte als Linkliste im HTML.
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { BildImg } from "@/components/client";
import { GuideSticky, type StickyLink } from "@/components/guide-sticky";
import { ScrollReihe } from "@/components/scroll-reihe";
import { Icon } from "@/components/karten";
import { KneipenKarte } from "@/components/kneipen-karte";
import { GuideKarteLazy } from "@/components/guide-karte-lazy";
import { OrtLinkListe, kartenOrte } from "@/components/ort-karten";
import { SEITE, SORTIERUNGEN, sortieren, stadtteileText, zaehlen, zahl } from "@/lib/guide-filter";
import {
  ARTEN, MIN_FUER_SCHALTER, SPEZIALITAETEN, VIBES, unterart, filterHref, filterLesen, filtern, happyHour, hatParameter,
  merkmalZaehlen, raucher, spezialitaeten, vibes, type KneipenFilter, type Unterart,
} from "@/lib/kneipen";
import { kneipenLaden } from "@/lib/kneipen-daten";
import { umschalten } from "@/lib/guide-filter";
import { jsonLdText } from "@/lib/json-ld";
import { kneipenListeJsonLd } from "@/lib/kneipen-json-ld";
import type { DddOrt } from "@/lib/typen";

const BASIS = "/guides/kneipen-bars";
const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type SP = Record<string, string | string[] | undefined>;

const BESCHREIBUNG =
  "Die besten Kneipen und Bars in Düsseldorf, Neuss und Ratingen – von der Altbier-Kneipe bis zur Cocktailbar, filterbar nach Stadtteil, Spezialität und Atmosphäre.";

export async function generateMetadata(props: { searchParams: Promise<SP> }): Promise<Metadata> {
  // Gefilterte, sortierte oder weitergeblätterte Ansichten nicht indexieren – Canonical ist immer die Hub-URL
  const gefiltert = hatParameter(await props.searchParams);
  return {
    title: "Kneipen & Bars in Düsseldorf",
    description: BESCHREIBUNG,
    alternates: { canonical: BASIS },
    robots: gefiltert ? { index: false, follow: true } : undefined,
    openGraph: { title: "Kneipen & Bars in Düsseldorf", description: BESCHREIBUNG, url: BASIS, type: "website", siteName: "dies.das.düsseldorf", locale: "de_DE" },
  };
}

const STANDARD: KneipenFilter = { arten: [], stadtteile: [], spez: [], vibe: [], hh: false, raucher: false, sort: "empfohlen", anzahl: SEITE, ansicht: "karte" };

/** Hero (dunkler, abendlicher Ton) mit dem eigenen Guide-Bild (wie die Kachel auf /guides). */
function Hero({ orte }: { orte: DddOrt[] }) {
  return (
    <section className="gd-hero gd-hero--abend">
      <div className="gd-hero__bild">
        <BildImg src="/guides/kneipen-bars.webp" alt="" icon="sports_bar" eager />
      </div>
      <div className="gd-hero__verlauf" aria-hidden />
      <div className="gd-hero__inhalt container">
        <nav className="gd-krumen gd-krumen--hell" aria-label="Brotkrumen">
          <Link href="/">Start</Link><span>/</span><Link href="/guides">Düsseldorf entdecken</Link><span>/</span>
          <span aria-current="page">Kneipen &amp; Bars</span>
        </nav>
        <h1 className="d">Kneipen &amp; Bars</h1>
        <p>{orte.length ? `${zahl(orte.length)} Empfehlungen – von der Altbier-Kneipe bis zur Cocktailbar` : "Kuratierte Empfehlungen – bald verfügbar"}</p>
      </div>
    </section>
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

/** Filterleiste, Status und Liste für einen Filterzustand (auch der ungefilterte Standard im Shell). */
function Ansicht({ alle, f }: { alle: DddOrt[]; f: KneipenFilter }) {
  const href = (a: Partial<KneipenFilter>) => filterHref(BASIS, f, a);
  const ergebnis = sortieren(filtern(alle, f), f.sort);
  const sichtbar = ergebnis.slice(0, f.anzahl);
  const rest = ergebnis.length - sichtbar.length;

  // Zählwerte jeweils ohne den eigenen Filter
  // Art: Mehrfachauswahl; keine Auswahl (oder alle drei) = „Alle“
  const fuerArt = filtern(alle, f, ["arten"]);
  const artUmschalten = (w: Unterart) => {
    const neu = umschalten(f.arten, w);
    return neu.length === ARTEN.length ? [] : neu;
  };
  const artTabs = [
    { label: "Alle", icon: undefined as string | undefined, anzahl: fuerArt.length, href: href({ arten: [] }), aktiv: !f.arten.length },
    ...ARTEN.map((a) => ({
      label: a.mehrzahl, icon: a.icon, anzahl: fuerArt.filter((o) => unterart(o) === a.wert).length,
      href: href({ arten: artUmschalten(a.wert) }), aktiv: f.arten.includes(a.wert),
    })),
  ];
  const stadtteile = zaehlen(filtern(alle, f, ["stadtteile"]), (o) => o.stadtteil);
  const spezZahl = merkmalZaehlen(filtern(alle, f, ["spez"]), SPEZIALITAETEN, spezialitaeten).filter((s) => s.anzahl > 0 || f.spez.includes(s.slug));
  const vibeZahl = merkmalZaehlen(filtern(alle, f, ["vibe"]), VIBES, vibes).filter((v) => v.anzahl > 0 || f.vibe.includes(v.slug));
  // Schalter erst bei genügend belegten Angaben (E6)
  const hhAnzahl = alle.filter((o) => happyHour(o)).length;
  const raucherAnzahl = alle.filter((o) => raucher(o)).length;
  const stadtteilName = (slug: string) => stadtteile.find((s) => s.slug === slug)?.name ?? slug;
  const nameVon = (liste: { slug: string; name: string }[], slug: string) => liste.find((x) => x.slug === slug)?.name ?? slug;

  const aktiv: StickyLink[] = [
    ...f.stadtteile.map((s) => ({ label: stadtteilName(s), href: href({ stadtteile: f.stadtteile.filter((x) => x !== s) }) })),
    ...f.spez.map((s) => ({ label: nameVon(spezZahl, s), href: href({ spez: f.spez.filter((x) => x !== s) }) })),
    ...f.vibe.map((v) => ({ label: nameVon(vibeZahl, v), href: href({ vibe: f.vibe.filter((x) => x !== v) }) })),
    ...(f.hh ? [{ label: "Happy Hour", href: href({ hh: false }) }] : []),
    ...(f.raucher ? [{ label: "Raucherbereich", href: href({ raucher: false }) }] : []),
  ];
  const status = [
    `${zahl(ergebnis.length)} ${ergebnis.length === 1 ? "Ergebnis" : "Ergebnisse"}${stadtteileText(f.stadtteile, stadtteilName)}`,
    ...(f.arten.length ? [ARTEN.filter((a) => f.arten.includes(a.wert)).map((a) => a.mehrzahl).join(" & ")] : []),
    ...aktiv.slice(f.stadtteile.length).map((a) => a.label),
  ].join(" · ");
  const sortLabel = SORTIERUNGEN.find((s) => s.wert === f.sort)?.label ?? "Empfohlen";
  const sortOptionen = SORTIERUNGEN.map((s) => ({ label: s.label, href: href({ sort: s.wert }), aktiv: s.wert === f.sort }));
  // Karte ist der Standard; die Ansicht bleibt beim Zurücksetzen der Filter erhalten
  const zuruecksetzen = f.ansicht === "grid" ? `${BASIS}?ansicht=grid` : BASIS;
  const ansichten = [
    { label: "Karte", icon: "map", href: href({ ansicht: "karte" }), aktiv: f.ansicht === "karte" },
    { label: "Grid", icon: "grid_view", href: href({ ansicht: "grid" }), aktiv: f.ansicht === "grid" },
  ];

  return (
    <>
      <GuideSticky
        zielId="gd-filter"
        typen={artTabs.map((t) => ({ label: t.label, icon: t.icon, href: t.href, aktiv: t.aktiv }))}
        chips={aktiv}
        sortLabel={sortLabel}
        sortOptionen={sortOptionen}
        ansichten={ansichten}
      />

      <div className="gd-filter gd-filter--abend" id="gd-filter" tabIndex={-1}>
        <div className="container gd-filter__innen">
          <ScrollReihe className="gd-typen" label="Art">
            {artTabs.map((t) => (
              <Link key={t.label} href={t.href} scroll={false} className={`gd-typ-tab ${t.aktiv ? "gd-chip--an" : ""}`} aria-current={t.aktiv || undefined}>
                {t.icon && <Icon name={t.icon} />}
                {t.label}
                <span className="gd-chip__zahl">{zahl(t.anzahl)}</span>
              </Link>
            ))}
          </ScrollReihe>

          <div className="gd-zeile">
            <span className="gd-zeile__label">Stadtteil</span>
            <ScrollReihe className="gd-zeile__chips" label="Stadtteile">
              <Chip href={href({ stadtteile: [] })} aktiv={!f.stadtteile.length}>Alle</Chip>
              {/* Mehrfachauswahl: Klick schaltet einen Stadtteil zu oder ab */}
              {stadtteile.map((s) => (
                <Chip key={s.slug} href={href({ stadtteile: umschalten(f.stadtteile, s.slug) })} aktiv={f.stadtteile.includes(s.slug)}>
                  {s.name}<span className="gd-chip__zahl">{s.anzahl}</span>
                </Chip>
              ))}
            </ScrollReihe>
          </div>

          {spezZahl.length > 0 && (
            <div className="gd-zeile">
              <span className="gd-zeile__label">Spezialität</span>
              <ScrollReihe className="gd-zeile__chips" label="Spezialitäten" aktivZeigen={false}>
                {spezZahl.map((s) => (
                  <Chip key={s.slug} href={href({ spez: umschalten(f.spez, s.slug) })} aktiv={f.spez.includes(s.slug)}>
                    {s.name}<span className="gd-chip__zahl">{s.anzahl}</span>
                  </Chip>
                ))}
              </ScrollReihe>
            </div>
          )}

          {vibeZahl.length > 0 && (
            <div className="gd-zeile">
              <span className="gd-zeile__label">Vibe</span>
              <ScrollReihe className="gd-zeile__chips" label="Atmosphäre" aktivZeigen={false}>
                {vibeZahl.map((v) => (
                  <Chip key={v.slug} href={href({ vibe: umschalten(f.vibe, v.slug) })} aktiv={f.vibe.includes(v.slug)}>
                    {v.name}<span className="gd-chip__zahl">{v.anzahl}</span>
                  </Chip>
                ))}
              </ScrollReihe>
            </div>
          )}

          {(hhAnzahl >= MIN_FUER_SCHALTER || raucherAnzahl >= MIN_FUER_SCHALTER) && (
            <div className="gd-zeile gd-schalter">
              {hhAnzahl >= MIN_FUER_SCHALTER && <Chip href={href({ hh: !f.hh })} aktiv={f.hh} icon="schedule">Happy Hour</Chip>}
              {raucherAnzahl >= MIN_FUER_SCHALTER && <Chip href={href({ raucher: !f.raucher })} aktiv={f.raucher} icon="smoking_rooms">Raucherbereich</Chip>}
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
                {sortOptionen.map((s) => (
                  <Link key={s.label} href={s.href} scroll={false} className={s.aktiv ? "is-aktiv" : ""}>{s.label}</Link>
                ))}
              </div>
            </details>
            <div className="gd-umschalter" role="group" aria-label="Ansicht">
              {ansichten.map((a) => (
                <Link key={a.label} href={a.href} scroll={false} className={a.aktiv ? "is-aktiv" : ""} aria-current={a.aktiv || undefined}>
                  <Icon name={a.icon} /><span className="gd-umschalter__label">{a.label}</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="container">
        <div className="gd-status">
          <span>{status}</span>
          {(aktiv.length > 0 || f.arten.length > 0) && <Link href={zuruecksetzen} scroll={false} className="gd-status__reset">Filter zurücksetzen</Link>}
        </div>

        {ergebnis.length === 0 ? (
          <div className="gd-leer">
            Keine Bar mit diesen Filtern. <Link href={zuruecksetzen} scroll={false}>Filter zurücksetzen</Link>
          </div>
        ) : f.ansicht === "karte" ? (
          <>
            <GuideKarteLazy orte={kartenOrte(ergebnis)} />
            <OrtLinkListe orte={ergebnis} zusatz={(o) => spezialitaeten(o).join(", ")} />
          </>
        ) : (
          <div className="gd-grid gd-grid--3 gd-grid--abend" role="list">
            {sichtbar.map((o) => <KneipenKarte key={o.id} o={o} />)}
          </div>
        )}

        {f.ansicht === "grid" && rest > 0 && (
          <div className="gd-mehr">
            <Link href={href({ anzahl: f.anzahl + SEITE })} scroll={false} className="gd-mehr__knopf">
              Weitere {Math.min(SEITE, rest)} laden
            </Link>
            <span className="muted">{zahl(sichtbar.length)} von {zahl(ergebnis.length)}</span>
          </div>
        )}
      </div>
    </>
  );
}

async function GefilterteAnsicht({ searchParams, alle }: { searchParams: Promise<SP>; alle: DddOrt[] }) {
  return <Ansicht alle={alle} f={filterLesen(await searchParams)} />;
}

export default async function KneipenBars(props: { searchParams: Promise<SP> }) {
  const alle = sortieren(await kneipenLaden(), "empfohlen");
  return (
    <div className="gd-seite gd-seite--abend">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: jsonLdText(kneipenListeJsonLd(alle.slice(0, 30), SITE_URL, BASIS)) }}
      />
      <Hero orte={alle} />
      <Suspense fallback={<Ansicht alle={alle} f={STANDARD} />}>
        <GefilterteAnsicht searchParams={props.searchParams} alle={alle} />
      </Suspense>
    </div>
  );
}
