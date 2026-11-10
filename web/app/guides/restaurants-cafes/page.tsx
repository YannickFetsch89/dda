// Guide-Hub Restaurants & Cafés (Design-Handoff v2, Ansichten 12, 14, 15)
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { BildImg } from "@/components/client";
import { GuideSticky, type StickyLink } from "@/components/guide-sticky";
import { ScrollReihe } from "@/components/scroll-reihe";
import { Icon, SkeletonKarten } from "@/components/karten";
import { GuideKarteLazy } from "@/components/guide-karte-lazy";
import { OrtKartenGrid, OrtLinkListe } from "@/components/ort-karten";
import { Fragebogen, type FragebogenDaten } from "@/components/fragebogen";
import {
  ALLE_TYPEN, FILTER_TAGS, SEITE, SORTIERUNGEN, STANDARD_TYPEN, filterHref, filterLesen, filtern, kueche,
  PREIS_STUFEN, preisStufeOrt, sortieren, stadtteileText, typUmschalten, typenStandard, umschalten, zaehlen, zahl, type GuideFilter, type OrtTyp,
} from "@/lib/guide-filter";
import { slugify } from "@/lib/kueche";
import { orteLaden } from "@/lib/orte";
import { brauhaeuserFuerRestaurants } from "@/lib/kneipen-daten";
import type { DddOrt } from "@/lib/typen";

const BASIS = "/guides/restaurants-cafes";
const TYPEN = ["restaurant", "imbiss", "cafe"] as const;
const TYP_NAME: Record<OrtTyp, string> = { restaurant: "Restaurants", imbiss: "Schnellimbiss", cafe: "Cafés" };

/** Kompakte Daten für die Live-Zählwerte im Fragebogen (Nachschlagetabellen + Tupel je Ort). */
function fragebogenDaten(orte: DddOrt[]): FragebogenDaten {
  const stadtteile = zaehlen(orte, (o) => o.stadtteil).map(({ slug, name }) => ({ slug, name }));
  const kuechen = zaehlen(orte, (o) => kueche(o)?.name).map(({ slug, name }) => ({ slug, name }));
  // Für Cafés sinnvolle Wünsche (Cocktails/Reservierbar gehören eher zu Restaurants und Bars)
  const tags = ["Frühstück", "Brunch", "Terrasse", "Vegetarisch", "Hunde willkommen", "Kinderfreundlich"].map((t) => ({ slug: slugify(t), name: t }));
  const stIndex = new Map(stadtteile.map((s, i) => [s.name, i]));
  const kIndex = new Map(kuechen.map((k, i) => [k.slug, i]));
  return {
    stadtteile,
    kuechen,
    tags,
    orte: orte.map((o) => {
      const typ: OrtTyp = o.typ === "kneipe" ? "restaurant" : (o.typ as OrtTyp);
      const maske = tags.reduce((m, t, i) => (o.tags.includes(t.name) ? m | (1 << i) : m), 0);
      return [ALLE_TYPEN.indexOf(typ), stIndex.get(o.stadtteil ?? "") ?? -1, kIndex.get(kueche(o)?.slug ?? "") ?? -1, preisStufeOrt(o), maske];
    }),
  };
}

export const metadata: Metadata = {
  title: "Restaurants & Cafés in Düsseldorf",
  description:
    "Die besten Restaurants und Cafés in Düsseldorf, Neuss und Ratingen – kuratiert nach Bewertung, filterbar nach Stadtteil, Küche, Preis und Ausstattung.",
  alternates: { canonical: BASIS },
};

type SP = Record<string, string | string[] | undefined>;

/** Hero mit dem eigenen Guide-Bild (wie die Kachel auf /guides) – kein Foto eines einzelnen Ortes. */
function Hero({ orte }: { orte: DddOrt[] }) {
  return (
    <section className="gd-hero">
      <div className="gd-hero__bild">
        <BildImg src="/guides/restaurants-cafes.webp" alt="" icon="restaurant" eager />
      </div>
      <div className="gd-hero__verlauf" aria-hidden />
      <div className="gd-hero__inhalt container">
        <nav className="gd-krumen gd-krumen--hell" aria-label="Brotkrumen">
          <Link href="/">Start</Link><span>/</span><Link href="/guides">Düsseldorf entdecken</Link><span>/</span>
          <span aria-current="page">Restaurants &amp; Cafés</span>
        </nav>
        <h1 className="d">Restaurants &amp; Cafés</h1>
        <p>{orte.length ? `${zahl(orte.length)} Empfehlungen – handverlesen für Düsseldorf` : "Kuratierte Empfehlungen – bald verfügbar"}</p>
      </div>
    </section>
  );
}

function Chip({ href, aktiv, children, klein = false }: { href: string; aktiv: boolean; children: React.ReactNode; klein?: boolean }) {
  return (
    <Link href={href} scroll={false} className={`gd-chip ${klein ? "" : "gd-chip--gross"} ${aktiv ? "gd-chip--an" : ""}`} aria-current={aktiv || undefined}>
      {children}
    </Link>
  );
}

/** Ansicht-Umschalter Grid/Karte (Segmented Control). */
function Ansicht({ ansichten }: { ansichten: { label: string; icon: string; href: string; aktiv: boolean }[] }) {
  return (
    <div className="gd-umschalter" role="group" aria-label="Ansicht">
      {ansichten.map((a) => (
        <Link key={a.label} href={a.href} scroll={false} className={a.aktiv ? "is-aktiv" : ""} aria-current={a.aktiv || undefined}>
          <Icon name={a.icon} /><span className="gd-umschalter__label">{a.label}</span>
        </Link>
      ))}
    </div>
  );
}

async function Inhalt({ searchParams, alle }: { searchParams: Promise<SP>; alle: DddOrt[] }) {
  // Orte einmal laden (gecached) und an Hero und Liste weitergeben
  // Brauhäuser aus dem Kneipen-Hub erscheinen zusätzlich hier (E1) – ihr Link bleibt die Kneipen-URL
  const sp = await searchParams;
  const f = filterLesen(sp);
  const href = (a: Partial<GuideFilter>) => filterHref(BASIS, f, a);

  const ergebnis = sortieren(filtern(alle, f), f.sort);
  const sichtbar = ergebnis.slice(0, f.anzahl);
  const rest = ergebnis.length - sichtbar.length;

  // Zählwerte: jeweils ohne den eigenen Filter, damit man sieht, was ein Wechsel bringt
  const fuerTyp = filtern(alle, f, ["typen"]);
  const fuerPreis = filtern(alle, f, ["preise"]);
  const stadtteile = zaehlen(filtern(alle, f, ["stadtteile"]), (o) => o.stadtteil);
  const kuechen = zaehlen(filtern(alle, f, ["kuechen"]), (o) => kueche(o)?.name);
  const stadtteilName = (slug: string) => stadtteile.find((s) => s.slug === slug)?.name ?? slug;
  const kuecheName = (slug: string) => kuechen.find((k) => k.slug === slug)?.name ?? slug;
  const tagName = new Map(FILTER_TAGS.map((t) => [slugify(t), t]));
  const anzahlTyp = (t: OrtTyp) => fuerTyp.filter((o) => (o.typ === "kneipe" ? "restaurant" : o.typ) === t).length;

  // Art: Mehrfachauswahl (Standard Restaurants + Cafés), „Alle“ wählt alle drei
  const alleGewaehlt = f.typen.length === ALLE_TYPEN.length;
  const typTabs = [
    { label: "Alle", icon: undefined, anzahl: fuerTyp.length, href: href({ typen: [...ALLE_TYPEN] }), aktiv: alleGewaehlt },
    ...(["restaurant", "cafe", "imbiss"] as OrtTyp[]).map((t) => ({
      label: TYP_NAME[t],
      icon: { restaurant: "restaurant", cafe: "local_cafe", imbiss: "lunch_dining" }[t],
      anzahl: anzahlTyp(t),
      // Aus „Alle“ heraus wählt ein Klick genau diese Art; sonst schaltet er sie zu oder ab
      href: href({ typen: alleGewaehlt ? [t] : typUmschalten(f.typen, t) }),
      aktiv: !alleGewaehlt && f.typen.includes(t),
    })),
  ];

  // Aktive Filter (Status-Zeile und Sticky-Leiste)
  const aktiv: StickyLink[] = [
    ...f.stadtteile.map((s) => ({ label: stadtteilName(s), href: href({ stadtteile: f.stadtteile.filter((x) => x !== s) }) })),
    ...f.kuechen.map((k) => ({ label: kuecheName(k), href: href({ kuechen: f.kuechen.filter((x) => x !== k) }) })),
    ...f.preise.map((p) => ({ label: PREIS_STUFEN.find((s) => s.wert === p)?.label ?? String(p), href: href({ preise: f.preise.filter((x) => x !== p) }) })),
    ...f.tags.map((t) => ({ label: tagName.get(t) ?? t, href: href({ tags: f.tags.filter((x) => x !== t) }) })),
  ];
  const hatFilter = !typenStandard(f.typen) || aktiv.length > 0;
  const typText = alleGewaehlt ? "Alle Arten" : ALLE_TYPEN.filter((t) => f.typen.includes(t)).map((t) => TYP_NAME[t]).join(" & ");
  const status = [
    `${zahl(ergebnis.length)} ${ergebnis.length === 1 ? "Ergebnis" : "Ergebnisse"}${stadtteileText(f.stadtteile, stadtteilName)}`,
    typText,
    ...aktiv.slice(f.stadtteile.length).map((a) => a.label),
  ].join(" · ");
  const kuecheLabel = !f.kuechen.length ? "Küche" : f.kuechen.length === 1 ? kuecheName(f.kuechen[0]) : `${kuecheName(f.kuechen[0])} +${f.kuechen.length - 1}`;
  const sortLabel = SORTIERUNGEN.find((s) => s.wert === f.sort)?.label ?? "Empfohlen";
  const sortOptionen = SORTIERUNGEN.map((s) => ({ label: s.label, href: href({ sort: s.wert }), aktiv: s.wert === f.sort }));
  const ansichten = [
    { label: "Karte", icon: "map", href: href({ ansicht: "karte" }), aktiv: f.ansicht === "karte" },
    { label: "Grid", icon: "grid_view", href: href({ ansicht: "grid" }), aktiv: f.ansicht === "grid" },
  ];
  const zuruecksetzen = href({ typen: [...STANDARD_TYPEN], stadtteile: [], kuechen: [], preise: [], tags: [] });
  // Aktuelle Filter als Query (ohne Basis) für die Kartenpunkte
  const abfrage = href({}).split("?")[1] ?? "";
  return (
    <>
      <GuideSticky
        zielId="gd-filter"
        typen={typTabs.map((t) => ({ label: t.label, icon: t.icon, href: t.href, aktiv: t.aktiv }))}
        chips={aktiv}
        sortLabel={sortLabel}
        sortOptionen={sortOptionen}
        ansichten={ansichten}
      />

      <div className="gd-filter" id="gd-filter" tabIndex={-1}>
        <div className="container gd-filter__innen">
          <ScrollReihe className="gd-typen" label="Art">
            {typTabs.map((t) => (
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

          <div className="gd-zeile">
            <span className="gd-zeile__label">Filter</span>
            {/* Küche steht außerhalb der scrollenden Chip-Reihe, damit das Menü nicht abgeschnitten wird */}
            <details className="gd-dropdown">
                <summary className={`gd-chip gd-chip--gross ${f.kuechen.length ? "gd-chip--an" : ""}`}>
                  <Icon name="ramen_dining" />{kuecheLabel}<Icon name="expand_more" />
                </summary>
                <div className="gd-menue">
                  <Link href={href({ kuechen: [] })} scroll={false} className={!f.kuechen.length ? "is-aktiv" : ""}>Alle Küchen</Link>
                  {/* Mehrfachauswahl: Klick schaltet eine Küche zu oder ab */}
                  {kuechen.map((k) => (
                    <Link key={k.slug} href={href({ kuechen: umschalten(f.kuechen, k.slug) })} scroll={false} className={f.kuechen.includes(k.slug) ? "is-aktiv" : ""}>
                      {f.kuechen.includes(k.slug) && <Icon name="check" />}{k.name}<span className="muted">{k.anzahl}</span>
                    </Link>
                  ))}
                </div>
            </details>
            <ScrollReihe className="gd-zeile__chips" label="Filter" aktivZeigen={false}>
              <span className="gd-trenner gd-trenner--hoch gd-nur-breit" aria-hidden />
              {/* Preis pro Person (Mehrfachauswahl), Zahl = Treffer mit dieser Stufe bei den übrigen Filtern */}
              {PREIS_STUFEN.map((s) => (
                <Chip key={s.wert} href={href({ preise: umschalten(f.preise, s.wert) })} aktiv={f.preise.includes(s.wert)}>
                  {s.wert === 4 && <Icon name="star" />}{s.label}<span className="gd-chip__zahl">{fuerPreis.filter((o) => preisStufeOrt(o) === s.wert).length}</span>
                </Chip>
              ))}
              <span className="gd-trenner gd-trenner--hoch" aria-hidden />
              {FILTER_TAGS.map((t) => {
                const s = slugify(t);
                return <Chip key={s} href={href({ tags: umschalten(f.tags, s) })} aktiv={f.tags.includes(s)}>{t}</Chip>;
              })}
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
                {sortOptionen.map((s) => (
                  <Link key={s.label} href={s.href} scroll={false} className={s.aktiv ? "is-aktiv" : ""}>{s.label}</Link>
                ))}
              </div>
            </details>
            <Ansicht ansichten={ansichten} />
          </div>
        </div>
      </div>

      <div className="container">
        <div className="gd-status">
          <span>{status}</span>
          {hatFilter && <Link href={zuruecksetzen} scroll={false} className="gd-status__reset">Filter zurücksetzen</Link>}
        </div>

        {ergebnis.length === 0 ? (
          <div className="gd-leer">
            Keine Treffer mit diesen Filtern. <Link href={zuruecksetzen} scroll={false}>Filter zurücksetzen</Link>
          </div>
        ) : f.ansicht === "karte" ? (
          <>
            {/* Kartenpunkte lädt die Karte selbst nach (/api/guide-karte) – hält die erste Antwort klein */}
            <GuideKarteLazy quelle={`/api/guide-karte?hub=restaurants${abfrage ? `&${abfrage}` : ""}`} />
            <OrtLinkListe orte={ergebnis} alleHref={href({ ansicht: "grid" })} zusatz={(o) => kueche(o)?.name} />
          </>
        ) : (
          <OrtKartenGrid orte={sichtbar} />
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

export default async function RestaurantsCafes(props: { searchParams: Promise<SP> }) {
  // Orte einmal laden ("use cache") – Hero und Empfehlungs-Leiste stehen damit im statischen Teil und sind
  // sofort da; nur Filterleiste und Ergebnisse warten auf die Filter aus der URL.
  // Brauhäuser aus dem Kneipen-Hub erscheinen zusätzlich hier (E1) – ihr Link bleibt die Kneipen-URL
  const [eigene, brauhaeuser] = await Promise.all([orteLaden([...TYPEN]), brauhaeuserFuerRestaurants()]);
  const alle = [...eigene, ...brauhaeuser];
  return (
    <div className="gd-seite gd-seite--leiste">
      <Hero orte={alle} />
      {/* Schmale Leiste „dies.das empfiehlt dir was“ – bleibt beim Scrollen oben, öffnet den Fragebogen */}
      <Fragebogen basis={BASIS} daten={fragebogenDaten(alle)} />
      <Suspense
        fallback={
          <div className="container" style={{ paddingTop: 24 }}>
            <SkeletonKarten anzahl={3} hoehe={300} />
          </div>
        }
      >
        <Inhalt searchParams={props.searchParams} alle={alle} />
      </Suspense>
    </div>
  );
}
