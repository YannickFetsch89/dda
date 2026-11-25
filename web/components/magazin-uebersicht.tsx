// Bausteine der Magazin-Übersicht (25.11.2026, nach dem Vorbild eines Ratgeber-Hubs): Hero, Themenwelten,
// Titelgeschichte, Guides, Redaktion. Reine Server-Komponenten; der Filter steht in components/magazin-filter.tsx.
import Link from "next/link";
import { Icon } from "./karten";
import { autorPfad, beitragPfad, RUBRIKEN, RUBRIK_NAME, RUBRIK_TEXT, rubrikPfad, type MagazinAutor, type MagazinBeitrag, type Rubrik } from "@/lib/magazin";
import { heroFuer } from "@/lib/magazin-bilder";
import { karteDaten, RUBRIK_ICON } from "@/lib/magazin-uebersicht";
import { SPIELPLAETZE_VERLINKT, WEIHNACHTSMAERKTE_VERLINKT } from "@/lib/schalter";

/** Kopf: Überzeile, H1 mit Gold-Akzent, Einleitung, „Gerade gefragt“ und drei Kennzahlen. */
export function MagazinHero({ anzahl }: { anzahl: number }) {
  const gefragt = [
    { href: rubrikPfad("wochenvorschau"), name: "Wochenvorschau" },
    ...(WEIHNACHTSMAERKTE_VERLINKT ? [{ href: "/guides/weihnachtsmaerkte", name: "Weihnachtsmärkte" }] : []),
    { href: "/wochenende", name: "Dieses Wochenende" },
  ];
  return (
    <section className="mzh" aria-labelledby="mzh-titel">
      <div className="container mzh__innen">
        <nav className="gd-krumen mzh__krumen" aria-label="Brotkrumen">
          <Link href="/">Start</Link>
          <span>/</span>
          <span aria-current="page">Magazin</span>
        </nav>
        <span className="overline overline--gold">Das Magazin für Düsseldorf</span>
        <h1 className="d" id="mzh-titel">
          Was Düsseldorf <span className="mzh__akzent">gerade bewegt.</span>
        </h1>
        <p className="mzh__intro">
          Wochenvorschau, Saisonthemen, Nachtleben, Genuss und Familie: Unsere Redaktion wählt aus, was sich in Düsseldorf
          lohnt, und sagt, für wen. Termine, Uhrzeiten und Preise kommen live aus unserem Eventkalender – so bleibt jeder
          Beitrag aktuell.
        </p>
        <p className="mzh__gefragt">
          <span>Gerade gefragt:</span>
          {gefragt.map((g) => (
            <Link key={g.href} href={g.href} className="mzh__chip">{g.name}</Link>
          ))}
        </p>
        <dl className="mzh__zahlen">
          <div><dt>Beiträge</dt><dd className="d">{anzahl}</dd></div>
          <div><dt>Rubriken</dt><dd className="d">{RUBRIKEN.length}</dd></div>
          <div><dt>Wochenvorschau</dt><dd className="d">jede Woche</dd></div>
        </dl>
      </div>
    </section>
  );
}

/** Themenwelten: eine Kachel je Rubrik mit Icon, Anzahl und Kurztext, verlinkt auf die Rubrik-Seite. */
export function Themenwelten({ zahl }: { zahl: Record<Rubrik, number> }) {
  return (
    <section className="sektion" aria-labelledby="mzt-titel">
      <span className="overline">Themenwelten</span>
      <h2 className="d mz-h2" id="mzt-titel">Finde dein Thema</h2>
      <div className="mzt-raster">
        {RUBRIKEN.map((r) => (
          <Link key={r} href={rubrikPfad(r)} className="mzt-kachel">
            <span className="mzt-kachel__kopf">
              <span className="mzt-kachel__icon"><Icon name={RUBRIK_ICON[r]} /></span>
              <span className="mzt-kachel__zahl">{zahl[r] === 0 ? "Bald" : zahl[r] === 1 ? "1 Beitrag" : `${zahl[r]} Beiträge`}</span>
            </span>
            <strong>{RUBRIK_NAME[r]}</strong>
            <span className="mzt-kachel__text">{RUBRIK_TEXT[r]}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}

/** Titelgeschichte: großes Bild, Rubrik, Datum, Titel, Teaser, bis zu vier nummerierte Kernpunkte („Auf einen Blick“). */
export function Titelgeschichte({ b }: { b: MagazinBeitrag }) {
  const k = karteDaten(b);
  const hero = heroFuer(b);
  const punkte = (b.kurzfassung ?? []).slice(0, 4);
  return (
    <section className="sektion" aria-labelledby="mzg-titel">
      <article className="mzg">
        <div className="mzg__bild">
          {/* eslint-disable-next-line @next/next/no-img-element -- statische, bereits optimierte Datei aus public/ */}
          <img src={hero.pfad} alt={hero.alt} width={1200} height={675} fetchPriority="high" decoding="async" />
          <span className="mzg__marke">Titelgeschichte</span>
          {hero.ki && <span className="mz-ki-marke">Symbolbild (KI-generiert)</span>}
        </div>
        <div className="mzg__text">
          <p className="mzg__meta">
            <Link href={rubrikPfad(b.rubrik)} className="mzf-chip">{k.rubrikName}</Link>
            {k.datum && <span className="mzg__stand">Stand: {k.datum}</span>}
          </p>
          <h2 className="d mzg__titel" id="mzg-titel">
            <Link href={beitragPfad(b)}>{b.titel}</Link>
          </h2>
          {b.teaser && <p className="mzg__teaser">{b.teaser}</p>}
          {punkte.length > 0 && (
            <ol className="mzg__punkte">
              {punkte.map((p, i) => (
                <li key={i}><span className="mzg__nr">{String(i + 1).padStart(2, "0")}</span>{p}</li>
              ))}
            </ol>
          )}
          <div className="mzg__fuss">
            <span>{k.lesezeit} Min. Lesezeit</span>
            <Link href={beitragPfad(b)} className="btn btn--gold">Weiterlesen <Icon name="arrow_forward" /></Link>
          </div>
        </div>
      </article>
    </section>
  );
}

const GUIDES = [
  { slug: "weihnachtsmaerkte", name: "Weihnachtsmärkte", text: "Welche Märkte heute geöffnet haben – mit Karte und Sonderzeiten", icon: "wm:markt", an: WEIHNACHTSMAERKTE_VERLINKT },
  { slug: "restaurants-cafes", name: "Restaurants & Cafés", text: "Die besten Adressen zum Essen und Kaffeetrinken", icon: "restaurant", an: true },
  { slug: "kneipen-bars", name: "Kneipen & Bars", text: "Altbier, Cocktails und gemütliche Ecken", icon: "sports_bar", an: true },
  { slug: "clubs", name: "Clubs", text: "Düsseldorfs Nachtleben von Techno bis Hip-Hop", icon: "nightlife", an: true },
  { slug: "spielplaetze", name: "Spielplätze", text: "Der passende Spielplatz für jedes Alter", icon: "sp:spielplatz", an: SPIELPLAETZE_VERLINKT },
];

/** Guides: die Hubs als Kacheln – mehr als Lesestoff, und starke interne Links. */
export function GuideKacheln() {
  return (
    <section className="sektion" aria-labelledby="mzgu-titel">
      <span className="overline">Weiterstöbern</span>
      <h2 className="d mz-h2" id="mzgu-titel">Unsere Guides für Düsseldorf</h2>
      <div className="mzt-raster mzt-raster--guides">
        {GUIDES.filter((g) => g.an).map((g) => (
          <Link key={g.slug} href={`/guides/${g.slug}`} className="mzt-kachel mzt-kachel--navy">
            <span className="mzt-kachel__icon"><span className="icon" aria-hidden data-icon={g.icon} /></span>
            <strong>{g.name}</strong>
            <span className="mzt-kachel__text">{g.text}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}

/** Redaktion: die Autorennamen mit Bild und Schwerpunkt, Link auf „Unsere Redaktion“. */
export function RedaktionLeiste({ autoren }: { autoren: MagazinAutor[] }) {
  if (!autoren.length) return null;
  return (
    <section className="sektion mzr" aria-labelledby="mzr-titel">
      <div className="sektionskopf sektionskopf--stapeln">
        <h2 className="d mz-h2" id="mzr-titel">Die Redaktion</h2>
        <Link href="/magazin/redaktion">So arbeiten wir</Link>
      </div>
      <ul className="mzr__liste">
        {[...autoren].sort((a, b) => a.name.localeCompare(b.name, "de")).map((a) => (
          <li key={a.slug}>
            <Link href={autorPfad(a)} className="mzr__autor">
              {a.bild ? (
                // eslint-disable-next-line @next/next/no-img-element -- statisches Profilbild aus public/
                <img src={a.bild} alt="" width={64} height={64} loading="lazy" />
              ) : (
                <span className="mzr__platz" aria-hidden />
              )}
              <span>
                <strong>{a.name}</strong>
                <span>{a.schwerpunkt}</span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
