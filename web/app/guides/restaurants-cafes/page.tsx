// Guide-Hub Restaurants & Cafés (Design-Handoff v2, Ansichten 12, 14, 15)
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { BildImg } from "@/components/client";
import { GuideSticky, type StickyLink } from "@/components/guide-sticky";
import { Icon, SkeletonKarten } from "@/components/karten";
import { OrtKartenGrid } from "@/components/ort-karten";
import {
  FILTER_TAGS, SEITE, SORTIERUNGEN, filterHref, filterLesen, filtern, kueche, preisZeichen,
  sortieren, umschalten, zaehlen, zahl, type GuideFilter,
} from "@/lib/guide-filter";
import { slugify } from "@/lib/kueche";
import { orteLaden, ortBildUrl } from "@/lib/orte";
import type { DddOrt } from "@/lib/typen";

const BASIS = "/guides/restaurants-cafes";
const TYPEN = ["restaurant", "cafe"] as const;

export const metadata: Metadata = {
  title: "Restaurants & Cafés in Düsseldorf",
  description:
    "Die besten Restaurants und Cafés in Düsseldorf, Neuss und Ratingen – kuratiert nach Bewertung, filterbar nach Stadtteil, Küche, Preis und Ausstattung.",
  alternates: { canonical: BASIS },
};

type SP = Record<string, string | string[] | undefined>;

/** Hero mit Foto des aktuell bestempfohlenen Ortes. */
function Hero({ orte }: { orte: DddOrt[] }) {
  const alle = sortieren(orte, "empfohlen");
  const titel = alle.find((o) => ortBildUrl(o));
  return (
    <section className="gd-hero">
      {titel && (
        <div className="gd-hero__bild">
          <BildImg src={ortBildUrl(titel)} alt="" icon="restaurant" eager />
        </div>
      )}
      <div className="gd-hero__verlauf" aria-hidden />
      <div className="gd-hero__inhalt container">
        <nav className="gd-krumen gd-krumen--hell" aria-label="Brotkrumen">
          <Link href="/">Start</Link><span>/</span><span>Düsseldorf entdecken</span><span>/</span>
          <span aria-current="page">Restaurants &amp; Cafés</span>
        </nav>
        <h1 className="d">Restaurants &amp; Cafés</h1>
        <p>{alle.length ? `${zahl(alle.length)} Empfehlungen – handverlesen für Düsseldorf` : "Kuratierte Empfehlungen – bald verfügbar"}</p>
      </div>
      {titel?.bild_attribution && <span className="gd-hero__credit">Foto: {titel.name} · {titel.bild_attribution}</span>}
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

async function Inhalt({ searchParams }: { searchParams: Promise<SP> }) {
  // Orte einmal laden (gecached) und an Hero und Liste weitergeben
  const [sp, alle] = await Promise.all([searchParams, orteLaden([...TYPEN])]);
  const f = filterLesen(sp);
  const href = (a: Partial<GuideFilter>) => filterHref(BASIS, f, a);

  const ergebnis = sortieren(filtern(alle, f), f.sort);
  const sichtbar = ergebnis.slice(0, f.anzahl);
  const rest = ergebnis.length - sichtbar.length;

  // Zählwerte: jeweils ohne den eigenen Filter, damit man sieht, was ein Wechsel bringt
  const fuerTyp = filtern(alle, f, ["typ"]);
  const stadtteile = zaehlen(filtern(alle, f, ["stadtteil"]), (o) => o.stadtteil);
  const kuechen = zaehlen(filtern(alle, f, ["kueche"]), (o) => kueche(o)?.name);
  const stadtteilName = stadtteile.find((s) => s.slug === f.stadtteil)?.name ?? f.stadtteil;
  const kuecheName = kuechen.find((k) => k.slug === f.kueche)?.name ?? null;
  const tagName = new Map(FILTER_TAGS.map((t) => [slugify(t), t]));

  const typTabs = [
    { label: "Alle", wert: null, icon: undefined, anzahl: fuerTyp.length },
    { label: "Restaurants", wert: "restaurant" as const, icon: "restaurant", anzahl: fuerTyp.filter((o) => o.typ === "restaurant").length },
    { label: "Cafés", wert: "cafe" as const, icon: "local_cafe", anzahl: fuerTyp.filter((o) => o.typ === "cafe").length },
  ];

  // Aktive Filter (Status-Zeile und Sticky-Leiste)
  const aktiv: StickyLink[] = [
    ...(f.stadtteil ? [{ label: stadtteilName ?? "", href: href({ stadtteil: null }) }] : []),
    ...(f.kueche ? [{ label: kuecheName ?? f.kueche, href: href({ kueche: null }) }] : []),
    ...f.preise.map((p) => ({ label: preisZeichen(p), href: href({ preise: f.preise.filter((x) => x !== p) }) })),
    ...f.tags.map((t) => ({ label: tagName.get(t) ?? t, href: href({ tags: f.tags.filter((x) => x !== t) }) })),
  ];
  const hatFilter = !!f.typ || aktiv.length > 0;
  const status = [
    `${zahl(ergebnis.length)} ${ergebnis.length === 1 ? "Ergebnis" : "Ergebnisse"}${f.stadtteil ? ` in ${stadtteilName}` : ""}`,
    ...(f.typ ? [f.typ === "cafe" ? "Cafés" : "Restaurants"] : []),
    ...aktiv.filter((a) => a.label !== stadtteilName).map((a) => a.label),
  ].join(" · ");
  const sortLabel = SORTIERUNGEN.find((s) => s.wert === f.sort)?.label ?? "Empfohlen";
  const sortOptionen = SORTIERUNGEN.map((s) => ({ label: s.label, href: href({ sort: s.wert }), aktiv: s.wert === f.sort }));

  return (
    <>
      <Hero orte={alle} />
      <GuideSticky
        zielId="gd-filter"
        typen={typTabs.map((t) => ({ label: t.label, icon: t.icon, href: href({ typ: t.wert }), aktiv: f.typ === t.wert }))}
        chips={aktiv}
        sortLabel={sortLabel}
        sortOptionen={sortOptionen}
      />

      <div className="gd-filter" id="gd-filter">
        <div className="container gd-filter__innen">
          <div className="gd-typen">
            {typTabs.map((t) => (
              <Link key={t.label} href={href({ typ: t.wert })} scroll={false} className={`gd-typ-tab ${f.typ === t.wert ? "gd-chip--an" : ""}`} aria-current={f.typ === t.wert || undefined}>
                {t.icon && <Icon name={t.icon} />}
                {t.label}
                <span className="gd-chip__zahl">{zahl(t.anzahl)}</span>
              </Link>
            ))}
          </div>

          <div className="gd-zeile">
            <span className="gd-zeile__label">Stadtteil</span>
            <div className="gd-zeile__chips">
              <Chip href={href({ stadtteil: null })} aktiv={!f.stadtteil}>Alle</Chip>
              {stadtteile.map((s) => (
                <Chip key={s.slug} href={href({ stadtteil: f.stadtteil === s.slug ? null : s.slug })} aktiv={f.stadtteil === s.slug}>
                  {s.name}<span className="gd-chip__zahl">{s.anzahl}</span>
                </Chip>
              ))}
            </div>
          </div>

          <div className="gd-zeile">
            <span className="gd-zeile__label">Filter</span>
            <div className="gd-zeile__chips">
              <details className="gd-dropdown">
                <summary className={`gd-chip gd-chip--gross ${f.kueche ? "gd-chip--an" : ""}`}>
                  <Icon name="ramen_dining" />{kuecheName ?? "Küche"}<Icon name="expand_more" />
                </summary>
                <div className="gd-menue">
                  <Link href={href({ kueche: null })} scroll={false} className={!f.kueche ? "is-aktiv" : ""}>Alle Küchen</Link>
                  {kuechen.map((k) => (
                    <Link key={k.slug} href={href({ kueche: k.slug })} scroll={false} className={f.kueche === k.slug ? "is-aktiv" : ""}>
                      {k.name}<span className="muted">{k.anzahl}</span>
                    </Link>
                  ))}
                </div>
              </details>
              <span className="gd-trenner gd-trenner--hoch" aria-hidden />
              {[1, 2, 3].map((p) => (
                <Chip key={p} href={href({ preise: umschalten(f.preise, p) })} aktiv={f.preise.includes(p)}>{preisZeichen(p)}</Chip>
              ))}
              <span className="gd-trenner gd-trenner--hoch" aria-hidden />
              {FILTER_TAGS.map((t) => {
                const s = slugify(t);
                return <Chip key={s} href={href({ tags: umschalten(f.tags, s) })} aktiv={f.tags.includes(s)}>{t}</Chip>;
              })}
            </div>
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
          </div>
        </div>
      </div>

      <div className="container">
        <div className="gd-status">
          <span>{status}</span>
          {hatFilter && <Link href={BASIS} scroll={false} className="gd-status__reset">Filter zurücksetzen</Link>}
        </div>

        {sichtbar.length > 0 ? (
          <OrtKartenGrid orte={sichtbar} />
        ) : (
          <div className="gd-leer">
            Keine Treffer mit diesen Filtern. <Link href={BASIS} scroll={false}>Filter zurücksetzen</Link>
          </div>
        )}

        {rest > 0 && (
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

export default function RestaurantsCafes(props: { searchParams: Promise<SP> }) {
  return (
    <div className="gd-seite">
      <Suspense
        fallback={
          <>
            <section className="gd-hero" />
            <div className="container" style={{ paddingTop: 24 }}>
              <SkeletonKarten anzahl={6} hoehe={360} />
            </div>
          </>
        }
      >
        <Inhalt searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}
