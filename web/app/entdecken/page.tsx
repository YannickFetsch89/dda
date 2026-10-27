// Entdecken (Design-Ansicht 02): alle Events mit Filtern und Sortierung als URL-Parameter
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Bild, EventKarte, Icon, KatBadge, Leer, SkeletonKarten, eventPfad } from "@/components/karten";
import { eventPoolLaden } from "@/lib/daten";
import { TAGESZEITEN, filtern, highlights, kategorieZaehlen, nachBeliebtheit, nachNeu, nachZeit, stadtteileZaehlen, type Tageszeit } from "@/lib/ableitungen";
import { ZEITRAUM_OPTIONEN, metaZeile, zeitraumAuflösen } from "@/lib/datum";
import { KATEGORIEN, kategorie } from "@/lib/kategorien";
import { BEZIRKE, OHNE_ZUORDNUNG, stadtteilName } from "@/lib/stadtteile";

export const metadata: Metadata = {
  title: "Entdecken",
  description: "Alle Events in Düsseldorf filtern nach Datum, Kategorie, Stadtteil, Preis und Tageszeit.",
};

const PRO_SEITE = 12;
const SORTIERUNGEN = [
  { key: "beliebt", label: "Beliebt" },
  { key: "datum", label: "Datum" },
  { key: "neu", label: "Neu" },
];
const PREISE = [
  { key: "kostenlos", label: "Kostenlos" },
  { key: "bezahlt", label: "Bezahlt" },
];

type Params = Record<string, string | undefined>;

function einzeln(sp: Record<string, string | string[] | undefined>): Params {
  return Object.fromEntries(Object.entries(sp).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]));
}

/** Baut eine Entdecken-URL aus den aktuellen Parametern plus Änderungen. */
function url(aktuell: Params, aenderung: Params): string {
  const p = new URLSearchParams();
  const neu = { ...aktuell, seite: undefined, ...aenderung };
  Object.entries(neu).forEach(([k, v]) => {
    if (v) p.set(k, v);
  });
  const qs = p.toString();
  return qs ? `/entdecken?${qs}` : "/entdecken";
}

export default function Entdecken(props: PageProps<"/entdecken">) {
  return (
    <div className="container">
      <Suspense
        fallback={
          <>
            <div className="seitentitel">
              <h1 className="d">Entdecken</h1>
            </div>
            <div className="sektion">
              <SkeletonKarten anzahl={8} />
            </div>
          </>
        }
      >
        <EntdeckenInhalt searchParams={props.searchParams} />
      </Suspense>
    </div>
  );
}

async function EntdeckenInhalt({ searchParams }: Pick<PageProps<"/entdecken">, "searchParams">) {
  const p = einzeln(await searchParams);
  const pool = await eventPoolLaden();
  const { heute } = pool;

  const z = zeitraumAuflösen(p.datum ?? "woche", heute);
  const sort = SORTIERUNGEN.some((s) => s.key === p.sort) ? p.sort! : "beliebt";
  const seite = Math.max(1, Math.min(50, Number(p.seite) || 1));
  const preis = p.preis === "kostenlos" || p.preis === "bezahlt" ? p.preis : undefined;
  const tz = TAGESZEITEN.find((t) => t.key === p.tageszeit)?.key as Tageszeit | undefined;
  const bezirk = BEZIRKE.find((b) => String(b.nr) === p.bezirk);

  const basisFilter = { von: z.von, bis: z.bis, mitLanglaeufern: true, suche: p.q, thema: p.thema };
  const treffer = filtern(pool.events, { ...basisFilter, kategorie: p.kategorie, stadtteil: p.stadtteil, bezirk: bezirk?.nr, preis, tageszeit: tz });
  treffer.sort(sort === "neu" ? nachNeu : sort === "datum" ? nachZeit : nachBeliebtheit);

  // Zähler für die Dropdowns (jeweils ohne den eigenen Filter)
  const katZahlen = kategorieZaehlen(filtern(pool.events, { ...basisFilter, stadtteil: p.stadtteil, bezirk: bezirk?.nr, preis, tageszeit: tz }));
  const stadtteilListe = stadtteileZaehlen(filtern(pool.events, { ...basisFilter, kategorie: p.kategorie, preis, tageszeit: tz }));

  const gezeigt = treffer.slice(0, seite * PRO_SEITE);
  const ohneFilter = !p.kategorie && !p.stadtteil && !p.bezirk && !preis && !tz && !p.q && !p.thema;
  const { highlight, top } = highlights(pool);
  const zeigeHighlights = ohneFilter && seite === 1;

  const aktiv = {
    datum: z.label,
    kategorie: p.kategorie ? kategorie(p.kategorie).name : null,
    stadtteil: p.stadtteil ? stadtteilName(p.stadtteil) : bezirk ? `Bezirk ${bezirk.nr}` : null,
    preis: preis ? PREISE.find((x) => x.key === preis)!.label : null,
    tageszeit: tz ? TAGESZEITEN.find((t) => t.key === tz)!.name : null,
  };

  return (
    <>
      <div className="seitentitel">
        <h1 className="d">Entdecken</h1>
        <span>{treffer.length} Events</span>
      </div>

      <form id="suche" className="suchfeld" action="/entdecken" role="search">
        <Icon name="search" />
        <label className="sr-only" htmlFor="entdecken-suche">
          Suche
        </label>
        <input id="entdecken-suche" name="q" type="search" defaultValue={p.q ?? ""} placeholder="Events, Orte, Künstler …" />
        {Object.entries(p)
          .filter(([k, v]) => v && !["q", "seite"].includes(k))
          .map(([k, v]) => (
            <input key={k} type="hidden" name={k} value={v} />
          ))}
        <button type="submit" className="btn btn--navy" style={{ height: 34, borderRadius: 10 }}>
          Suchen
        </button>
      </form>

      <div className="filterleiste" role="toolbar" aria-label="Filter">
        <details className="filter-alle">
          <summary className="rund-navy" aria-label="Alle Filter">
            <Icon name="tune" />
          </summary>
          <div className="bottom-sheet" role="dialog" aria-label="Alle Filter">
            <h3 className="d">Filter</h3>
            <FilterGruppe titel="Datum">
              {ZEITRAUM_OPTIONEN.map((o) => (
                <Link key={o.key} className="chip" aria-current={z.key === o.key ? "true" : undefined} href={url(p, { datum: o.key })}>
                  {o.label}
                </Link>
              ))}
            </FilterGruppe>
            <FilterGruppe titel="Kategorie">
              {KATEGORIEN.map((k) => (
                <Link key={k.slug} className="chip" aria-current={p.kategorie === k.slug ? "true" : undefined} href={url(p, { kategorie: p.kategorie === k.slug ? undefined : k.slug })}>
                  {k.name} <small>{katZahlen[k.slug]}</small>
                </Link>
              ))}
            </FilterGruppe>
            <FilterGruppe titel="Stadtbezirk">
              {BEZIRKE.map((b) => (
                <Link key={b.nr} className="chip" aria-current={bezirk?.nr === b.nr ? "true" : undefined} href={url(p, { bezirk: bezirk?.nr === b.nr ? undefined : String(b.nr), stadtteil: undefined })}>
                  {b.name}
                </Link>
              ))}
            </FilterGruppe>
            <FilterGruppe titel="Preis">
              {PREISE.map((o) => (
                <Link key={o.key} className="chip" aria-current={preis === o.key ? "true" : undefined} href={url(p, { preis: preis === o.key ? undefined : o.key })}>
                  {o.label}
                </Link>
              ))}
            </FilterGruppe>
            <FilterGruppe titel="Tageszeit">
              {TAGESZEITEN.map((t) => (
                <Link key={t.key} className="chip" aria-current={tz === t.key ? "true" : undefined} href={url(p, { tageszeit: tz === t.key ? undefined : t.key })}>
                  {t.name}
                </Link>
              ))}
            </FilterGruppe>
            <div style={{ display: "flex", gap: 8 }}>
              <Link href="/entdecken" className="btn btn--outline" style={{ flex: 1 }}>
                Zurücksetzen
              </Link>
            </div>
          </div>
        </details>

        <Dropdown label={aktiv.datum} aktiv={z.key !== "woche"}>
          {ZEITRAUM_OPTIONEN.map((o) => (
            <Link key={o.key} href={url(p, { datum: o.key })} aria-current={z.key === o.key ? "true" : undefined}>
              {o.label}
            </Link>
          ))}
        </Dropdown>
        <Dropdown label={aktiv.kategorie ?? "Kategorie"} aktiv={!!aktiv.kategorie}>
          <Link href={url(p, { kategorie: undefined })}>Alle Kategorien</Link>
          {KATEGORIEN.map((k) => (
            <Link key={k.slug} href={url(p, { kategorie: k.slug })} aria-current={p.kategorie === k.slug ? "true" : undefined}>
              {k.name} <span>{katZahlen[k.slug]}</span>
            </Link>
          ))}
        </Dropdown>
        <Dropdown label={aktiv.stadtteil ?? "Stadtteil"} aktiv={!!aktiv.stadtteil}>
          <Link href={url(p, { stadtteil: undefined, bezirk: undefined })}>Alle Stadtteile</Link>
          {stadtteilListe.map((s) => (
            <Link key={s.name} href={url(p, { stadtteil: s.name, bezirk: undefined })} aria-current={p.stadtteil === s.name ? "true" : undefined}>
              {stadtteilName(s.name)} <span>{s.anzahl}</span>
            </Link>
          ))}
          <Link href={url(p, { stadtteil: OHNE_ZUORDNUNG, bezirk: undefined })}>{OHNE_ZUORDNUNG}</Link>
          <Link href="/stadtteile">
            Karte nach Bezirken <span>→</span>
          </Link>
        </Dropdown>
        <Dropdown label={aktiv.preis ?? "Preis"} aktiv={!!aktiv.preis}>
          <Link href={url(p, { preis: undefined })}>Alle Preise</Link>
          {PREISE.map((o) => (
            <Link key={o.key} href={url(p, { preis: o.key })} aria-current={preis === o.key ? "true" : undefined}>
              {o.label}
            </Link>
          ))}
        </Dropdown>
        <Dropdown label={aktiv.tageszeit ?? "Tageszeit"} aktiv={!!aktiv.tageszeit}>
          <Link href={url(p, { tageszeit: undefined })}>Ganzer Tag</Link>
          {TAGESZEITEN.map((t) => (
            <Link key={t.key} href={url(p, { tageszeit: t.key })} aria-current={tz === t.key ? "true" : undefined}>
              {t.name} <span>{t.bereich}</span>
            </Link>
          ))}
        </Dropdown>
        {p.thema && (
          <Link className="chip chip--aktiv" href={url(p, { thema: undefined })} aria-label={`Thema ${p.thema} entfernen`}>
            {p.thema} <Icon name="close" />
          </Link>
        )}
        {p.q && (
          <Link className="chip chip--aktiv" href={url(p, { q: undefined })} aria-label="Suche entfernen">
            „{p.q}“ <Icon name="close" />
          </Link>
        )}
      </div>

      <div className="sortierzeile">
        <nav className="segment" aria-label="Sortierung">
          {SORTIERUNGEN.map((s) => (
            <Link key={s.key} href={url(p, { sort: s.key === "beliebt" ? undefined : s.key })} aria-current={sort === s.key ? "true" : undefined} scroll={false}>
              {s.label}
            </Link>
          ))}
        </nav>
        {!ohneFilter && (
          <Link href="/entdecken" className="link">
            Filter zurücksetzen
          </Link>
        )}
      </div>

      {zeigeHighlights && highlight && (
        <article className="sektion highlight" style={{ marginTop: 20 }}>
          <Bild e={highlight} eager>
            <KatBadge slug={highlight.kategorie} variante="badge--hell" />
          </Bild>
          <div className="highlight__text">
            <span className="overline overline--gold">Highlight der Woche</span>
            <span className="meta">{metaZeile(highlight, heute)}</span>
            <h2 className="highlight__titel d">
              <Link href={eventPfad(highlight)}>{highlight.titel}</Link>
            </h2>
            <span className="highlight__ort">
              {highlight.ort}
              {highlight.preis ? ` · ${highlight.preis}` : ""}
            </span>
          </div>
        </article>
      )}

      {treffer.length === 0 ? (
        <div className="sektion">
          <Leer titel="Dazu haben wir gerade nichts gefunden.">
            <Link href="/entdecken" className="link">
              Alle Filter zurücksetzen
            </Link>
          </Leer>
        </div>
      ) : (
        <>
          <div className="sektion raster" role="list" style={{ marginTop: 20 }}>
            {gezeigt.slice(0, 4).map((e) => (
              <EventKarte key={e.id} e={e} heute={heute} variante="grid" />
            ))}
          </div>
          {zeigeHighlights && top && (
            <article className="top-monat" style={{ marginTop: "var(--gap)" }}>
              <span className="overline">Top-Event des Monats</span>
              <h2 className="top-monat__titel d">
                <Link href={eventPfad(top)}>{top.titel}</Link>
              </h2>
              {top.beschreibung && <p>{top.beschreibung}</p>}
              <div className="top-monat__fuss">
                <span>
                  {metaZeile(top, heute)} · {top.ort}
                </span>
                <span className="pfeil-rund" aria-hidden>
                  <span className="icon">arrow_forward</span>
                </span>
              </div>
            </article>
          )}
          {gezeigt.length > 4 && (
            <div className="raster" role="list" style={{ marginTop: "var(--gap)" }}>
              {gezeigt.slice(4).map((e) => (
                <EventKarte key={e.id} e={e} heute={heute} variante="grid" />
              ))}
            </div>
          )}
          <div className="mehr-laden">
            {gezeigt.length < treffer.length && (
              <Link href={url(p, { seite: String(seite + 1) })} className="btn btn--outline btn--gross" scroll={false}>
                Mehr laden
              </Link>
            )}
            <span>
              {gezeigt.length} von {treffer.length}
            </span>
          </div>
        </>
      )}
    </>
  );
}

function FilterGruppe({ titel, children }: { titel: string; children: React.ReactNode }) {
  return (
    <div className="bottom-sheet__gruppe">
      <b>{titel}</b>
      <div className="bottom-sheet__chips">{children}</div>
    </div>
  );
}

function Dropdown({ label, aktiv, children }: { label: string; aktiv: boolean; children: React.ReactNode }) {
  return (
    <details className="filter-dd">
      <summary className={aktiv ? "chip chip--aktiv" : "chip"}>
        {label}
        <Icon name="expand_more" />
      </summary>
      <div className="popover">{children}</div>
    </details>
  );
}
