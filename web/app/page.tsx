// Startseite V2 (Design-Ansichten 07 desktop / 08 mobil)
import Link from "next/link";
import { Suspense } from "react";
import { ClaimWort, NewsletterForm, Reihe } from "@/components/client";
import { EventKarte, Icon, KompaktKarte, Leer, ListenZeile, SkeletonKarten, ThumbZeile, Bild, GratisZeile, eventPfad } from "@/components/karten";
import { eventPoolLaden } from "@/lib/daten";
import { filtern, istKostenlos, nachBeliebtheit, nachNeu, nachZeit, neuSeit, stadtteileZaehlen, themenZaehlen, vielfaeltig, wochenendProgramm } from "@/lib/ableitungen";
import { WT_KURZ, plusTage, tagKurz, tagMonat, wochentag, zeitraumAuflösen, uhrzeitMinuten, metaZeile } from "@/lib/datum";
import { kategorie, katStil } from "@/lib/kategorien";
import { stadtteilName } from "@/lib/stadtteile";
import type { DddEvent } from "@/lib/typen";

const SCHNELLFILTER = [
  { key: "heute", label: "Heute" },
  { key: "morgen", label: "Morgen" },
  { key: "wochenende", label: "Dieses Wochenende" },
  { key: "woche", label: "Diese Woche" },
];

const REIHEN = [
  { slug: "musik", titel: "Musik" },
  { slug: "food", titel: "Food & Märkte" },
  { slug: "nightlife", titel: "Nightlife" },
] as const;

function startHref(key: string, heute: string) {
  return key === "heute" || key === heute ? "/" : `/?datum=${key}`;
}

/** Füllt eine Liste aus einem größeren Bereich auf, wenn der gewählte Zeitraum zu wenig hergibt. */
function auffuellen(primaer: DddEvent[], reserve: DddEvent[], n: number): DddEvent[] {
  if (primaer.length >= n) return primaer.slice(0, n);
  const ids = new Set(primaer.map((e) => e.id));
  return [...primaer, ...reserve.filter((e) => !ids.has(e.id))].slice(0, n);
}

export default function Startseite(props: PageProps<"/">) {
  return (
    <Suspense fallback={<StartSkeleton />}>
      <StartInhalt searchParams={props.searchParams} />
    </Suspense>
  );
}

async function StartInhalt({ searchParams }: Pick<PageProps<"/">, "searchParams">) {
  const sp = await searchParams;
  const geladen = await eventPoolLaden();
  // Abgesagte Events erscheinen nicht auf der Startseite (in Kalender/Entdecken bleiben sie markiert sichtbar)
  const pool = { ...geladen, events: geladen.events.filter((e) => !e.abgesagt) };
  const { heute } = pool;
  const z = zeitraumAuflösen(typeof sp.datum === "string" ? sp.datum : undefined, heute);
  const istHeute = z.von === heute && z.bis === heute;

  const imZeitraum = filtern(pool.events, { von: z.von, bis: z.bis });
  const woche = filtern(pool.events, { von: z.von, bis: plusTage(z.von, 6) });
  const beliebtSortiert = [...imZeitraum].sort(nachBeliebtheit);
  const wocheBeliebt = [...woche].sort(nachBeliebtheit);

  // Hero
  const neu = neuSeit(pool.events, pool.jetzt).sort(nachNeu);
  const kennzahlLabel = istHeute ? "Events heute" : z.von === z.bis ? `Events ${tagKurz(z.von)}` : `Events ${z.label.toLowerCase()}`;
  const tage = Array.from({ length: 14 }, (_, i) => {
    const tag = plusTage(heute, i);
    return { tag, anzahl: filtern(pool.events, { von: tag, bis: tag }).length };
  });

  // Tipp + Picks
  const tipp = imZeitraum.find((e) => e.tipp_des_tages) ?? beliebtSortiert.find((e) => e.bild_url) ?? beliebtSortiert[0] ?? null;
  const picks = vielfaeltig(imZeitraum, 4, new Set(tipp ? [tipp.id] : []));
  const beliebt = auffuellen(beliebtSortiert, wocheBeliebt, 5);

  // Infoboxen
  const abend = imZeitraum.filter((e) => (uhrzeitMinuten(e) ?? 0) >= 17 * 60).sort(nachZeit).slice(0, 8);
  const frisch = (neu.length ? neu : [...pool.events].sort(nachNeu)).slice(0, 6);
  const stadtteile = stadtteileZaehlen(imZeitraum.length >= 10 ? imZeitraum : woche).slice(0, 10);

  // Kostenlos + Themen (Woche ab gewähltem Tag)
  const gratisWoche = woche.filter(istKostenlos);
  const themen = themenZaehlen(woche).slice(0, 14);

  const wochenende = wochenendProgramm(pool);

  return (
    <>
      <section className="hero" aria-label="Überblick">
        <div className="container">
          <div className="hero__oben">
            <h1 className="hero__claim d">
              Was geht <span className="claim-umbruch nur-mobil" />
              <ClaimWort />
              <span className="claim-umbruch nur-mobil" /> in Düsseldorf?
            </h1>
            <div className="kennzahlen">
              <div className="kennzahl">
                <b>{imZeitraum.length}</b>
                <span>{kennzahlLabel}</span>
              </div>
              <div className="kennzahl">
                <b>{imZeitraum.filter(istKostenlos).length}</b>
                <span>kostenlos</span>
              </div>
              <div className="kennzahl">
                <b>{neu.length}</b>
                <span>neu seit gestern</span>
              </div>
            </div>
          </div>
          <nav className="datumsleiste" aria-label="Tag wählen">
            {tage.map((t, i) => (
              <Link key={t.tag} href={startHref(t.tag, heute)} aria-current={z.von === t.tag && z.bis === t.tag ? "true" : undefined} scroll={false}>
                <span className="datumsleiste__wt">{i === 0 ? "Heute" : WT_KURZ[wochentag(t.tag)]}</span>
                <span className="datumsleiste__tag">{Number(t.tag.slice(8, 10))}</span>
                <span className="datumsleiste__anz">
                  {t.anzahl}
                  <span className="nur-desktop"> Events</span>
                </span>
              </Link>
            ))}
          </nav>
          <div className="schnellfilter nur-mobil" aria-label="Zeitraum">
            {SCHNELLFILTER.map((s) => (
              <Link key={s.key} href={startHref(s.key, heute)} className="chip chip--navy" aria-current={z.key === s.key ? "true" : undefined} scroll={false}>
                {s.label}
              </Link>
            ))}
          </div>
        </div>
      </section>

      <div className="container">
        {imZeitraum.length === 0 ? (
          <div className="sektion">
            <Leer titel={istHeute ? "Heute ist es ruhig." : "An diesem Tag ist noch nichts eingetragen."}>
              <Link href="/wochenende" className="link">
                Schau mal ins Wochenende <Icon name="arrow_forward" />
              </Link>
            </Leer>
          </div>
        ) : (
          <section className="sektion startraster" aria-label="Tipp und Picks">
            {tipp && <TippDesTages e={tipp} heute={heute} />}
            <div style={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
              <div className="sektionskopf">
                <h2 className="d">Picks des Tages</h2>
                <Link href={`/entdecken?datum=${z.key}`}>Von der Redaktion</Link>
              </div>
              <div className="nur-mobil">
                <Reihe breite={280} label="Picks des Tages">
                  {picks.map((e) => (
                    <KompaktKarte key={e.id} e={e} heute={heute} />
                  ))}
                </Reihe>
              </div>
              <div className="picks-raster nur-desktop" role="list">
                {picks.map((e) => (
                  <KompaktKarte key={e.id} e={e} heute={heute} />
                ))}
              </div>
            </div>
          </section>
        )}

        {beliebt.length > 0 && (
          <section className="sektion">
            <div className="sektionskopf">
              <h2 className="d">Beliebt in Düsseldorf</h2>
              <Link href={`/entdecken?datum=${z.key === "heute" ? "woche" : z.key}&sort=beliebt`}>Alle beliebten Events</Link>
            </div>
            <Reihe breite={220} raster5 label="Beliebt in Düsseldorf">
              {beliebt.map((e, i) => (
                <EventKarte key={e.id} e={e} heute={heute} variante="rang" rang={i + 1} />
              ))}
            </Reihe>
          </section>
        )}

        <section className="sektion infoboxen">
          <div className="box">
            <div className="box__kopf">
              <h3 className="d">{istHeute ? "Heute Abend" : "Am Abend"}</h3>
              <Link href={istHeute ? "/heute" : `/tag/${z.von}`} className="link">
                Tagesplaner
              </Link>
            </div>
            {abend.length ? abend.map((e) => <ListenZeile key={e.id} e={e} mitKategorie />) : <p className="muted" style={{ padding: "10px 0 14px" }}>Für den Abend ist noch nichts eingetragen.</p>}
          </div>
          <div className="box">
            <div className="box__kopf">
              <h3 className="d">Gerade neu</h3>
              <span className="neu-label">{neu.length ? `${neu.length} NEU` : "NEU"}</span>
            </div>
            {frisch.map((e) => (
              <ThumbZeile key={e.id} e={e} heute={heute} />
            ))}
          </div>
          <div className="box box--sand">
            <div className="box__kopf">
              <h3 className="d">Nach Stadtteil</h3>
              <Link href="/stadtteile" className="link">
                <Icon name="map" />
                Karte
              </Link>
            </div>
            <div className="kachel-raster">
              {stadtteile.map((s) => (
                <Link key={s.name} className="kachel" href={`/entdecken?stadtteil=${encodeURIComponent(s.name)}&datum=${imZeitraum.length >= 10 ? z.key : "woche"}`}>
                  <span>{stadtteilName(s.name)}</span>
                  <span>{s.anzahl}</span>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {REIHEN.map((r) => {
          const k = kategorie(r.slug);
          const imBereich = imZeitraum.filter((e) => e.kategorie === r.slug);
          const bereich = imBereich.length >= 5 ? imBereich : woche.filter((e) => e.kategorie === r.slug);
          if (!bereich.length) return null;
          const datumKey = imBereich.length >= 5 ? z.key : "woche";
          return (
            <section key={r.slug} className="sektion">
              <div className="katkopf" style={katStil(r.slug)}>
                <span className="katkopf__kreis" aria-hidden>
                  <span className="icon">{k.icon}</span>
                </span>
                <h2 className="d">{r.titel}</h2>
                <div className="katkopf__subs">
                  {k.unterkategorien.map((s) => (
                    <Link key={s} href={`/entdecken?kategorie=${r.slug}&datum=${datumKey}&q=${encodeURIComponent(s.replace(/s$/, ""))}`} className="chip chip--tint">
                      {s}
                    </Link>
                  ))}
                </div>
                <Link href={`/entdecken?kategorie=${r.slug}&datum=${datumKey}`}>Alle {bereich.length}</Link>
              </div>
              <Reihe breite={190} raster5 label={r.titel}>
                {[...bereich]
                  .sort(nachBeliebtheit)
                  .slice(0, 5)
                  .map((e) => (
                    <EventKarte key={e.id} e={e} heute={heute} variante="reihe" />
                  ))}
              </Reihe>
            </section>
          );
        })}

        <section className="sektion gratis-raster">
          <div>
            <div className="sektionskopf">
              <h2 className="d">Kostenlos diese Woche</h2>
              <Link href="/entdecken?preis=kostenlos&datum=woche">Alle {gratisWoche.length}</Link>
            </div>
            {gratisWoche.length ? (
              <div className="gratis-liste" role="list">
                {[...gratisWoche]
                  .sort(nachBeliebtheit)
                  .slice(0, 6)
                  .map((e) => (
                    <GratisZeile key={e.id} e={e} heute={heute} />
                  ))}
              </div>
            ) : (
              <Leer titel="Diese Woche nichts Kostenloses gefunden." />
            )}
          </div>
          {themen.length > 0 && (
            <div>
              <div className="sektionskopf">
                <h2 className="d">Themen</h2>
              </div>
              <div className="chip-wolke">
                {themen.map((t) => (
                  <Link key={t.name} href={`/entdecken?thema=${encodeURIComponent(t.name)}&datum=woche`} className="chip">
                    {t.name}
                    <small>{t.anzahl}</small>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </section>

        <section className="sektion band" aria-label="Wochenend-Programm">
          <div className="band__kopf">
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span className="overline overline--gold">
                {tagMonat(wochenende[0].tag)} – {tagMonat(wochenende[2].tag)}
              </span>
              <h2 className="d">Unser Wochenend-Programm</h2>
            </div>
            <Link href="/wochenende" className="btn btn--gold btn--gross nur-desktop">
              Ganzes Wochenende ansehen
            </Link>
          </div>
          <div className="band__spalten">
            {wochenende.map((tag) => (
              <div key={tag.tag} className="band__spalte">
                <span className="band__tag d">
                  {tag.name} <small>{tag.tag.slice(8, 10)}.{tag.tag.slice(5, 7)}.</small>
                </span>
                {tag.events.length ? (
                  tag.events.map((e) => (
                    <div key={e.id} className="zeile">
                      <span className="zeile__zeit">{e.uhrzeit}</span>
                      <div className="zeile__text">
                        <span className="zeile__titel">
                          <Link href={eventPfad(e)}>{e.titel}</Link>
                        </span>
                        <span className="zeile__sub">
                          {e.ort}
                          {e.preis ? ` · ${e.preis}` : ""}
                        </span>
                      </div>
                      <span className="punkt punkt--ring" style={katStil(e.kategorie)} aria-hidden />
                    </div>
                  ))
                ) : (
                  <span className="zeile__sub" style={{ padding: "10px 0" }}>
                    Noch keine Tipps.
                  </span>
                )}
              </div>
            ))}
          </div>
          <Link href="/wochenende" className="btn btn--gold btn--gross nur-mobil">
            Ganzes Wochenende ansehen
          </Link>
        </section>

        <section id="newsletter" className="newsletter" style={{ marginTop: 24 }}>
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}>
            <span className="newsletter__titel d">Jeden Donnerstag das Wochenende im Postfach.</span>
            <span style={{ fontSize: 14 }}>Neun Tipps, kein Spam, jederzeit abbestellbar.</span>
          </div>
          <NewsletterForm />
        </section>
      </div>
    </>
  );
}

function TippDesTages({ e, heute }: { e: DddEvent; heute: string }) {
  const k = kategorie(e.kategorie);
  return (
    <article className="sticker" style={katStil(e.kategorie)}>
      <Bild e={e} eager>
        <span className="badge badge--tipp">
          <Icon name="star" />
          Tipp des Tages
        </span>
      </Bild>
      <div className="sticker__text">
        <span className="sticker__kat">
          <Icon name={k.icon} />
          <span className="nur-desktop">{k.name}</span>
          <span className="nur-mobil">
            {k.name}
            {e.uhrzeit ? ` · ${e.uhrzeit} Uhr` : ""} · {e.ort}
          </span>
        </span>
        <h2 className="sticker__titel d">
          <Link href={eventPfad(e)}>{e.titel}</Link>
        </h2>
        {e.beschreibung && <p className="sticker__beschreibung">{e.beschreibung}</p>}
        <div className="sticker__infos">
          <span>
            <Icon name="schedule" />
            {metaZeile(e, heute)}
            {e.uhrzeit ? " Uhr" : ""}
          </span>
          <span>
            <Icon name="location_on" />
            {e.ort}
          </span>
        </div>
        <div className="sticker__fuss">
          <span className="preis">{e.preis}</span>
          <span className="btn btn--navy">Ansehen</span>
        </div>
      </div>
    </article>
  );
}

function StartSkeleton() {
  return (
    <>
      <section className="hero">
        <div className="container">
          <h1 className="hero__claim d">
            Was geht <span className="claim-wort">heute</span> in Düsseldorf?
          </h1>
          <div className="skeleton" style={{ height: 72, marginTop: 18, opacity: 0.15 }} />
        </div>
      </section>
      <div className="container sektion">
        <SkeletonKarten anzahl={4} />
      </div>
    </>
  );
}
