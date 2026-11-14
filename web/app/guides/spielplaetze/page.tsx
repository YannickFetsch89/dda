// Guide-Hub Spielplätze (Design-Handoff v2, Ansicht 23; Plan docs/plan-spielplaetze-2026-11-12.md, 5.2)
//
// Karte ist die Hauptansicht (Punkte über /api/guide-karte?hub=spielplaetze), darunter die Liste ALLER Plätze als Links,
// damit jede Detail-URL im ersten HTML steht. Filter-URLs: noindex, follow mit Canonical auf den Hub.
// Erste HTML-Antwort mit Inhalt: Hero, Einleitung und die ungefilterte Ansicht stehen außerhalb der Suspense-Grenze
// bzw. als deren Fallback; nur die filterabhängige Ansicht wartet auf searchParams.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { BildImg } from "@/components/client";
import { GuideKarteLazy } from "@/components/guide-karte-lazy";
import { GuideEinleitung, GuideSeoText } from "@/components/guide-text";
import { Icon } from "@/components/karten";
import { OrtLinkListe } from "@/components/ort-karten";
import { ScrollReihe } from "@/components/scroll-reihe";
import { stadtteileText, umschalten, zaehlen, zahl } from "@/lib/guide-filter";
import { jsonLdText } from "@/lib/json-ld";
import {
  ALTERSGRUPPEN, EXTRAS, GERAETE, SORTIERUNGEN, STANDARD, TYPEN, alterPasst, alterText, belegteGeraete, chips, erfasst,
  extraBelegt, extraJa, filterHref, filterLesen, filtern, geraetBelegt, geraetJa, hatParameter, ortStadtteilSlug, sortieren, spielplatz, typInfo,
  type SpielplatzFilter,
} from "@/lib/spielplaetze";
import { spielplaetzeLaden } from "@/lib/spielplaetze-daten";
import { SPIELPLATZ_BASIS as BASIS, spielplaetzeListeJsonLd, spielplatzPfad } from "@/lib/spielplaetze-json-ld";
import { stadtteilName } from "@/lib/stadtteile";
import type { DddOrt } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type SP = Record<string, string | string[] | undefined>;

const TITEL = "Spielplätze in Düsseldorf";
const BESCHREIBUNG =
  "Alle öffentlichen Spielplätze in Düsseldorf auf einer Karte – mit Altersgruppe, Ausstattung, Wasser- und Waldspielplätzen, Abenteuerspielplätzen und der Notfallnummer jedes Platzes.";

export async function generateMetadata(props: { searchParams: Promise<SP> }): Promise<Metadata> {
  const gefiltert = hatParameter(await props.searchParams);
  return {
    title: TITEL,
    description: BESCHREIBUNG,
    alternates: { canonical: BASIS },
    robots: gefiltert ? { index: false, follow: true } : undefined,
    openGraph: { title: TITEL, description: BESCHREIBUNG, url: BASIS, type: "website", siteName: "dies.das.düsseldorf", locale: "de_DE", images: [{ url: "/guides/spielplaetze.webp" }] },
  };
}

function Hero({ anzahl }: { anzahl: number }) {
  return (
    <section className="gd-hero sp-hero">
      <div className="sp-hero__bild">
        <BildImg src="/guides/spielplaetze.webp" alt="" icon="sp:spielplatz" eager />
      </div>
      <div className="gd-hero__inhalt container">
        <nav className="gd-krumen" aria-label="Brotkrumen">
          <Link href="/">Start</Link><span>/</span><Link href="/guides">Düsseldorf entdecken</Link><span>/</span>
          <span aria-current="page">Spielplätze</span>
        </nav>
        <h1 className="d">{TITEL}</h1>
        <p>{anzahl ? `${zahl(anzahl)} Spielplätze – mit Alter, Ausstattung und Notfallnummer` : "Bald verfügbar"}</p>
      </div>
    </section>
  );
}

function Chip({ href, aktiv, children, icon, className = "" }: { href: string; aktiv: boolean; children: React.ReactNode; icon?: string; className?: string }) {
  return (
    <Link href={href} scroll={false} className={`gd-chip gd-chip--gross ${className} ${aktiv ? "gd-chip--an" : ""}`} aria-current={aktiv || undefined}>
      {icon && <Icon name={icon} />}
      {children}
    </Link>
  );
}

/** Legende der Pin-Farben (Altersgruppen) mit Text. */
function Legende() {
  return (
    <ul className="sp-legende" aria-label="Farben auf der Karte">
      {ALTERSGRUPPEN.map((g) => (
        <li key={g.wert}><span className={`sp-punkt sp-punkt--${g.wert}`} aria-hidden />{g.kurz === "alle Altersgruppen" ? "Alle Altersgruppen" : g.kurz}</li>
      ))}
      <li><span className="sp-punkt sp-punkt--unbekannt" aria-hidden />Alter nicht bekannt</li>
    </ul>
  );
}

/** Zusatz in der Linkliste: Typ steht schon vorne, dahinter Alter und bis zu drei Geräte. */
function listenZusatz(o: DddOrt): string {
  const geraete = belegteGeraete(spielplatz(o)).slice(0, 3).map((g) => GERAETE.find((x) => x.wert === g)?.label);
  return [alterText(o), geraete.join(", ")].filter(Boolean).join(" · ");
}

function Ansicht({ alle, f }: { alle: DddOrt[]; f: SpielplatzFilter }) {
  const href = (a: Partial<SpielplatzFilter>) => filterHref(BASIS, f, a);
  const ergebnis = sortieren(filtern(alle, f, ortStadtteilSlug), f.sort);

  const fuerAlter = filtern(alle, f, ortStadtteilSlug, ["alter"]);
  const alterChips = ALTERSGRUPPEN.map((g) => ({ ...g, anzahl: fuerAlter.filter((o) => alterPasst(o, g.wert)).length }));
  const fuerTyp = filtern(alle, f, ortStadtteilSlug, ["typen"]);
  const typChips = TYPEN.filter((t) => t.wert !== "kinder")
    .map((t) => ({ ...t, anzahl: fuerTyp.filter((o) => typInfo(o).wert === t.wert).length }))
    .filter((t) => t.anzahl > 0 || f.typen.includes(t.wert));
  const geraetChips = chips(filtern(alle, f, ortStadtteilSlug, ["geraete"]), GERAETE, geraetJa, f.geraete, geraetBelegt);
  const extraChips = chips(filtern(alle, f, ortStadtteilSlug, ["extras"]), EXTRAS, extraJa, f.extras, extraBelegt);
  const stadtteile = zaehlen(filtern(alle, f, ortStadtteilSlug, ["stadtteile"]), (o) => (o.stadtteil ? stadtteilName(o.stadtteil) : null));
  const stadtteilAnzeige = (slug: string) => stadtteile.find((s) => s.slug === slug)?.name ?? slug;

  const status = [
    `${zahl(ergebnis.length)} ${ergebnis.length === 1 ? "Spielplatz" : "Spielplätze"}${stadtteileText(f.stadtteile, stadtteilAnzeige)}`,
    ...(f.alter ? [ALTERSGRUPPEN.find((g) => g.wert === f.alter)!.label] : []),
    ...(f.typen.length ? [TYPEN.filter((t) => f.typen.includes(t.wert)).map((t) => t.mehrzahl).join(" & ")] : []),
    ...(f.geraete.length ? [GERAETE.filter((g) => f.geraete.includes(g.wert)).map((g) => g.label).join(" + ")] : []),
    ...(f.extras.length ? [EXTRAS.filter((e) => f.extras.includes(e.wert)).map((e) => e.label).join(" + ")] : []),
  ].join(" · ");
  const gefiltert = !!f.alter || f.typen.length > 0 || f.geraete.length > 0 || f.extras.length > 0 || f.stadtteile.length > 0;
  const sortLabel = SORTIERUNGEN.find((s) => s.wert === f.sort)?.label ?? "Empfohlen";
  const abfrage = href({}).split("?")[1] ?? "";

  return (
    <>
      <div className="gd-filter sp-filter" id="gd-filter" tabIndex={-1}>
        <div className="container gd-filter__innen">
          <div className="gd-zeile">
            <span className="gd-zeile__label">Alter</span>
            <ScrollReihe className="gd-zeile__chips" label="Altersgruppe">
              <Chip href={href({ alter: null })} aktiv={!f.alter} className="sp-alter-chip">Alle Alter</Chip>
              {alterChips.map((g) => (
                <Chip key={g.wert} href={href({ alter: f.alter === g.wert ? null : g.wert })} aktiv={f.alter === g.wert} className={`sp-alter-chip sp-alter-chip--${g.wert}`}>
                  <span className={`sp-punkt sp-punkt--${g.wert}`} aria-hidden />
                  {g.wert === "alle" ? "Für alle Altersgruppen" : g.label}<span className="gd-chip__zahl">{g.anzahl}</span>
                </Chip>
              ))}
            </ScrollReihe>
          </div>

          {typChips.length > 0 && (
            <div className="gd-zeile">
              <span className="gd-zeile__label">Art</span>
              <ScrollReihe className="gd-zeile__chips" label="Art des Spielplatzes">
                <Chip href={href({ typen: [] })} aktiv={!f.typen.length}>Alle</Chip>
                {typChips.map((t) => (
                  <Chip key={t.wert} href={href({ typen: umschalten(f.typen, t.wert) })} aktiv={f.typen.includes(t.wert)} icon={t.icon}>
                    {t.mehrzahl}<span className="gd-chip__zahl">{t.anzahl}</span>
                  </Chip>
                ))}
              </ScrollReihe>
            </div>
          )}

          {geraetChips.length > 0 && (
            <div className="gd-zeile">
              <span className="gd-zeile__label">Ausstattung</span>
              <ScrollReihe className="gd-zeile__chips" label="Ausstattung">
                {geraetChips.map((g) => (
                  <Chip key={g.wert} href={href({ geraete: umschalten(f.geraete, g.wert) })} aktiv={f.geraete.includes(g.wert)} icon={g.icon}>
                    {g.label}<span className="gd-chip__zahl">{g.anzahl}</span>
                  </Chip>
                ))}
              </ScrollReihe>
            </div>
          )}

          {extraChips.length > 0 && (
            <div className="gd-zeile">
              <span className="gd-zeile__label">Extras</span>
              <ScrollReihe className="gd-zeile__chips" label="Extras">
                {extraChips.map((e) => (
                  <Chip key={e.wert} href={href({ extras: umschalten(f.extras, e.wert) })} aktiv={f.extras.includes(e.wert)} icon={f.extras.includes(e.wert) ? "check" : e.icon}>
                    {e.label}<span className="gd-chip__zahl">{e.anzahl}</span>
                  </Chip>
                ))}
              </ScrollReihe>
            </div>
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

          <div className="gd-filter__fuss">
            <details className="gd-sort">
              <summary>
                <Icon name="sort" className="muted" />
                <span className="gd-sort__label muted">Sortieren:</span>
                <b>{sortLabel}</b>
                <Icon name="expand_more" />
              </summary>
              <div className="gd-menue">
                {SORTIERUNGEN.map((s) => (
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
        <p className="sp-erfasst muted">
          <Icon name="info" />
          Ausstattung für {zahl(erfasst(ergebnis))} von {zahl(ergebnis.length)} Spielplätzen erfasst
        </p>
        {ergebnis.length === 0 ? (
          <div className="gd-leer">
            Kein Spielplatz mit diesen Filtern. Die Ausstattung ist noch nicht für alle Spielplätze erfasst.{" "}
            <Link href={BASIS} scroll={false}>Filter zurücksetzen</Link>
          </div>
        ) : (
          <>
            <Legende />
            {/* Kartenpunkte lädt die Karte selbst nach; „In der Nähe“ fragt den Standort erst nach dem Klick ab (E8) */}
            <GuideKarteLazy quelle={`/api/guide-karte?hub=spielplaetze${abfrage ? `&${abfrage}` : ""}`} naehe />
            <OrtLinkListe
              orte={ergebnis}
              alleHref={href({})}
              max={1000}
              pfad={spielplatzPfad}
              typLabel={(o) => typInfo(o).label}
              zusatz={listenZusatz}
              einheit="Spielplätze"
            />
          </>
        )}
      </div>
    </>
  );
}

async function GefilterteAnsicht({ searchParams, alle }: { searchParams: Promise<SP>; alle: DddOrt[] }) {
  return <Ansicht alle={alle} f={filterLesen(await searchParams)} />;
}

export default async function Spielplaetze(props: { searchParams: Promise<SP> }) {
  const alle = sortieren(await spielplaetzeLaden(), "empfohlen");
  return (
    <div className="gd-seite sp-seite">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(spielplaetzeListeJsonLd(alle, SITE_URL)) }} />
      <Hero anzahl={alle.length} />
      <div className="container">
        <GuideEinleitung seite="spielplaetze" werte={{ anzahl: zahl(alle.length) }} />
      </div>
      <Suspense fallback={<Ansicht alle={alle} f={STANDARD} />}>
        <GefilterteAnsicht searchParams={props.searchParams} alle={alle} />
      </Suspense>
      <GuideSeoText seite="spielplaetze" />
      <p className="container sp-quellen muted">
        Kartendaten und Ausstattung teils © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap-Mitwirkende</a>
        {" · "}Spielplatzdaten: Landeshauptstadt Düsseldorf (dl-de/zero-2.0)
      </p>
    </div>
  );
}
