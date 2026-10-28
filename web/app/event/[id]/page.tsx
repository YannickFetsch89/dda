// Event-Detail (Design-Ansicht 03)
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { HerzButton, Reihe, TeilenButton, TeilenLeiste, ZurueckButton } from "@/components/client";
import { Bild, EventKarte, Icon, KatBadge, SkeletonKarten, eventPfad } from "@/components/karten";
import { eventLaden, eventPoolLaden } from "@/lib/daten";
import { filtern, istKostenlos, nachBeliebtheit } from "@/lib/ableitungen";
import { kurzDatum, plusTage, tagLang } from "@/lib/datum";
import { stadtteilName } from "@/lib/stadtteile";
import { symbolbild } from "@/lib/symbolbild";

export async function generateMetadata(props: PageProps<"/event/[id]">): Promise<Metadata> {
  const { id } = await props.params;
  const e = await eventLaden(decodeURIComponent(id));
  if (!e) return { title: "Event nicht gefunden" };
  const beschreibung = e.beschreibung ?? `${tagLang(e.datum)}${e.uhrzeit ? `, ${e.uhrzeit} Uhr` : ""} · ${e.ort}`;
  return {
    title: e.titel,
    description: beschreibung,
    openGraph: { title: e.titel, description: beschreibung, images: [e.bild_url ?? symbolbild(e)].filter((b): b is string => !!b) },
  };
}

export default function EventSeite(props: PageProps<"/event/[id]">) {
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

function mapsLink(adresse: string) {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(adresse)}`;
}

async function EventInhalt({ params }: Pick<PageProps<"/event/[id]">, "params">) {
  const { id } = await params;
  const e = await eventLaden(decodeURIComponent(id));
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
        <Bild e={e} eager />
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

            <a className="karte-ausschnitt" href={mapsLink(adresse)} target="_blank" rel="noopener noreferrer" aria-label={`${adresse} in Google Maps öffnen`}>
              <span className="karte-ausschnitt__pin">
                <Icon name="location_on" />
              </span>
              <span className="karte-ausschnitt__route">
                <Icon name="directions" />
                Route
              </span>
            </a>

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
