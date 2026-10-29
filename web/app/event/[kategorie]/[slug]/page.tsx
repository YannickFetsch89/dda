// Event-Detail via SEO-Slug: /event/{kategorie}/{slug}
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { GoogleKarte, HerzButton, Reihe, TeilenButton, TeilenLeiste, ZurueckButton } from "@/components/client";
import { Bild, EventKarte, Icon, KatBadge, SkeletonKarten, eventPfad } from "@/components/karten";
import { eventLaden, eventPoolLaden } from "@/lib/daten";
import { filtern, istKostenlos, nachBeliebtheit } from "@/lib/ableitungen";
import { kurzDatum, plusTage, tagLang } from "@/lib/datum";
import { stadtteilName } from "@/lib/stadtteile";
import { symbolbild } from "@/lib/symbolbild";

type Props = { params: Promise<{ kategorie: string; slug: string }> };

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const e = await eventLaden(decodeURIComponent(slug));
  if (!e) return { title: "Event nicht gefunden" };
  const beschreibung = e.beschreibung ?? `${tagLang(e.datum)}${e.uhrzeit ? `, ${e.uhrzeit} Uhr` : ""} · ${e.ort}`;
  return {
    title: e.titel,
    description: beschreibung,
    openGraph: { title: e.titel, description: beschreibung, images: [e.bild_url ?? symbolbild(e)].filter((b): b is string => !!b) },
  };
}

export default function EventSeite(props: Props) {
  return (
    <Suspense
      fallback={
        <>
          <div className="skeleton" style={{ height: 330, borderRadius: 0 }} />
          <div className="container sektion">
            <SkeletonKarten anzahl={2} hoehe={120} />
          </div>
        </>
      }
    >
      <EventInhalt params={props.params} />
    </Suspense>
  );
}

function routenLink(adresse: string) {
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(adresse)}`;
}

async function EventInhalt({ params }: { params: Promise<{ kategorie: string; slug: string }> }) {
  const { slug } = await params;
  const e = await eventLaden(decodeURIComponent(slug));
  if (!e) notFound();

  const pool = await eventPoolLaden();
  const { heute } = pool;
  const aehnliche = filtern(pool.events, { von: plusTage(e.datum, -7) < heute ? heute : plusTage(e.datum, -7), bis: plusTage(e.datum, 7), kategorie: e.kategorie })
    .filter((x) => x.id !== e.id)
    .sort(nachBeliebtheit)
    .slice(0, 8);

  const adresse = e.adresse ?? `${e.ort}, Düsseldorf`;
  const zeitText = e.datum_bis && e.datum_bis !== e.datum ? `${tagLang(e.datum, false)} bis ${kurzDatum(e.datum_bis)}` : tagLang(e.datum);
  const pfad = eventPfad(e);

  return (
    <article>
      <div className="detail-hero">
        <Bild e={e} eager vollstaendig />
        <div className="detail-hero__btns">
          <ZurueckButton />
          <div>
            <TeilenButton titel={e.titel} pfad={pfad} />
            <HerzButton id={e.id} titel={e.titel} gross />
          </div>
        </div>
      </div>

      <div className="detail-sheet">
        <div className="container detail-raster">
          <div style={{ display: "flex", flexDirection: "column", gap: 28, minWidth: 0 }}>
            <header>
              <KatBadge slug={e.kategorie} />
              <h1 className="detail__titel d">{e.titel}</h1>
              {e.abgesagt && (
                <p className="abgesagt-hinweis" role="status">
                  <Icon name="event_busy" />
                  <span>
                    <b>Dieses Event wurde abgesagt.</b> Ob es einen Ersatztermin gibt oder Tickets erstattet werden, erfährst du beim Veranstalter.
                  </span>
                </p>
              )}
              <div className="infozeilen">
                <div className="infozeile">
                  <span className="infozeile__kachel">
                    <Icon name="calendar_today" />
                  </span>
                  <div>
                    <b>{zeitText}</b>
                    <span>{e.uhrzeit ? `${e.uhrzeit} Uhr` : "Uhrzeit siehe Veranstalter"}</span>
                  </div>
                </div>
                <div className="infozeile">
                  <span className="infozeile__kachel">
                    <Icon name="location_on" />
                  </span>
                  <div>
                    <b>{e.ort}</b>
                    <span>
                      {e.adresse ?? "Düsseldorf"}
                      {e.stadtteil ? ` · ${stadtteilName(e.stadtteil)}` : ""}
                    </span>
                  </div>
                </div>
                <div className="infozeile">
                  <span className="infozeile__kachel">
                    <Icon name="confirmation_number" />
                  </span>
                  <div>
                    <b>{e.preis ?? "Preis siehe Veranstalter"}</b>
                    {istKostenlos(e) && <span>Kein Eintritt</span>}
                  </div>
                </div>
              </div>
            </header>

            <GoogleKarte adresse={adresse} routeUrl={routenLink(adresse)} />

            {e.beschreibung && (
              <section className="detail__abschnitt">
                <h2 className="d">Worum geht&apos;s</h2>
                <p>{e.beschreibung}</p>
              </section>
            )}
          </div>

          <aside className="detail-seite" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {e.quelle_url && (
              <a className="btn btn--gold btn--gross btn--block" href={e.quelle_url} target="_blank" rel="noopener">
                Zur Veranstalter-Seite
                <Icon name="open_in_new" />
              </a>
            )}
            <section className="detail__abschnitt">
              <h2 className="d" style={{ fontSize: 22 }}>
                Teilen
              </h2>
              <TeilenLeiste titel={e.titel} pfad={pfad} />
            </section>
            {e.quelle_name && <p className="quelle">Quelle: {e.quelle_name}</p>}
            {e.stadtteil && (
              <Link className="link" href={`/entdecken?stadtteil=${encodeURIComponent(e.stadtteil)}&datum=woche`}>
                Mehr in {stadtteilName(e.stadtteil)} <Icon name="arrow_forward" />
              </Link>
            )}
          </aside>
        </div>

        {aehnliche.length > 0 && (
          <section className="container sektion">
            <div className="sektionskopf">
              <h2 className="d">Ähnliche Events</h2>
              <Link href={`/entdecken?kategorie=${e.kategorie}&datum=woche`}>Alle</Link>
            </div>
            <Reihe breite={200} label="Ähnliche Events">
              {aehnliche.map((x) => (
                <EventKarte key={x.id} e={x} heute={heute} variante="reihe" />
              ))}
            </Reihe>
          </section>
        )}
      </div>
    </article>
  );
}
