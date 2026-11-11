// Event-Detail via SEO-Slug: /event/{kategorie}/{slug}
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { GoogleKarte, HerzButton, Reihe, TeilenButton, TeilenLeiste, ZurueckButton } from "@/components/client";
import { Bild, EventKarte, Icon, KatBadge, eventPfad } from "@/components/karten";
import { eventLaden, eventPoolLaden } from "@/lib/daten";
import { filtern, istKostenlos, istOnline, nachBeliebtheit } from "@/lib/ableitungen";
import { kurzDatum, plusTage, tagLang } from "@/lib/datum";
import { stadtteilName } from "@/lib/stadtteile";
import { symbolbild } from "@/lib/symbolbild";
import { eventBildUrl } from "@/lib/bilder";
import { anzeigeTitel, termineAmTag, terminSchluessel } from "@/lib/termine";
import { istAbgelaufen, kommendeEmpfehlungen, ortSchluessel } from "@/lib/abgelaufen";
import { eventJsonLd, jsonLdText } from "@/lib/json-ld";
import { AbgelaufenHinweis } from "@/components/abgelaufen-hinweis";
import { BeschreibungText } from "@/components/beschreibung-text";
import { kurzBeschreibung } from "@/lib/beschreibung";
import { seitenMetadaten } from "@/lib/seo";
import { kategorie as kategorieInfo } from "@/lib/kategorien";
import { inStadtteil, kategoriePfad, stadtteilPfad } from "@/lib/landing";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

type Props = { params: Promise<{ kategorie: string; slug: string }> };

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const e = await eventLaden(decodeURIComponent(slug));
  if (!e) return { title: "Event nicht gefunden" };
  const beschreibung = kurzBeschreibung(e.beschreibung, 160) ?? `${tagLang(e.datum)}${e.uhrzeit ? `, ${e.uhrzeit} Uhr` : ""} · ${e.ort}`;
  const titel = anzeigeTitel(e.titel, e.ort);
  // Vergangene Events: Seite bleibt (HTTP 200), aber 30 Tage nach dem letzten Event-Tag noindex (Maßnahme 13)
  // „heute“ aus dem gecachten Pool wie /tag/[datum] (kein new Date() beim Rendern)
  const { heute } = await eventPoolLaden();
  const langeVorbei = (e.datum_bis ?? e.datum) < plusTage(heute, -30);
  return seitenMetadaten({ pfad: eventPfad(e), titel, beschreibung, bild: eventBildUrl(e) ?? symbolbild(e), noindex: langeVorbei });
}

// Ohne äußere Suspense-Grenze (Muster der Guide-Details): H1, Termin, Ort und Beschreibung stehen im ersten HTML.
// Unbekannte Slugs beantwortet schon proxy.ts mit 404; notFound() bleibt als Rückfall.
export const instant = false;

export default function EventSeite(props: Props) {
  return <EventInhalt params={props.params} />;
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
  // Weitere Uhrzeiten desselben Events am selben Tag (je Uhrzeit eine eigene Event-Seite)
  const termine = termineAmTag(pool.alle, e);
  const titel = anzeigeTitel(e.titel, e.ort);
  // „Zum Termin um …“ nur, wenn dieser Termin einen eigenen Link hat (sonst führen alle Uhrzeiten zur selben Seite)
  const eigenerTerminLink = termine.length > 0 && !!e.quelle_url && termine.filter((t) => t.quelle_url === e.quelle_url).length === 1;
  const eigenerSchluessel = terminSchluessel(e);
  // Abgelaufen: Seite bleibt (HTTP 200, indexierbar), zeigt aber einen Hinweis und kommende Events
  const abgelaufen = istAbgelaufen(e, heute);
  const empfehlungen = abgelaufen ? kommendeEmpfehlungen(e, pool.events, heute) : [];
  // „Weitere Events an diesem Ort“ nur, wenn die Suche dort auch kommende Events findet (keine leere Seite)
  const ortHatMehr =
    !!ortSchluessel(e.ort) &&
    filtern(pool.events, { von: heute, bis: plusTage(heute, 59), suche: e.ort, mitLanglaeufern: true }).some((x) => x.id !== e.id);
  const ortSuche = ortHatMehr ? `/entdecken?q=${encodeURIComponent(e.ort)}&datum=alle` : null;
  const aehnliche = abgelaufen ? [] : filtern(pool.events, { von: plusTage(e.datum, -7) < heute ? heute : plusTage(e.datum, -7), bis: plusTage(e.datum, 7), kategorie: e.kategorie })
    .filter((x) => x.id !== e.id && terminSchluessel(x) !== eigenerSchluessel)
    .sort(nachBeliebtheit)
    .slice(0, 8);

  const online = istOnline(e);
  const adresse = e.adresse ?? `${e.ort}, Düsseldorf`;
  const zeitText = e.datum_bis && e.datum_bis !== e.datum ? `${tagLang(e.datum, false)} bis ${kurzDatum(e.datum_bis)}` : tagLang(e.datum);
  const pfad = eventPfad(e);
  const jsonLd = eventJsonLd(e, `${SITE_URL}${pfad}`, SITE_URL);

  return (
    <article>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <div className="detail-hero">
        <Bild e={e} eager vollstaendig alt={`${titel}, ${e.ort}`} symbolAlt={`Symbolbild: ${titel}`} />
        <div className="detail-hero__btns">
          <ZurueckButton />
          <div>
            <TeilenButton titel={titel} pfad={pfad} />
            <HerzButton id={e.id} titel={titel} gross />
          </div>
        </div>
      </div>

      <div className="detail-sheet">
        <div className="container detail-raster">
          <div style={{ display: "flex", flexDirection: "column", gap: 28, minWidth: 0 }}>
            <header>
              <AbgelaufenHinweis abgelaufen={abgelaufen} />
              {abgelaufen && (kategoriePfad(e.kategorie) || stadtteilPfad(e.stadtteil)) && (
                <p className="abgelaufen-links">
                  {kategoriePfad(e.kategorie) && (
                    <Link className="link" href={kategoriePfad(e.kategorie)!}>
                      Kommende {kategorieInfo(e.kategorie).name}-Events <Icon name="arrow_forward" />
                    </Link>
                  )}
                  {stadtteilPfad(e.stadtteil) && (
                    <Link className="link" href={stadtteilPfad(e.stadtteil)!}>
                      Was {inStadtteil(e.stadtteil!)} los ist <Icon name="arrow_forward" />
                    </Link>
                  )}
                </p>
              )}
              {/* Badge verlinkt die Kategorieseite – die Kante sagt Crawlern, wozu das Event gehört */}
              {kategoriePfad(e.kategorie) ? (
                <Link href={kategoriePfad(e.kategorie)!} className="badge-link" aria-label={`Alle Events: ${kategorieInfo(e.kategorie).name}`}>
                  <KatBadge slug={e.kategorie} />
                </Link>
              ) : (
                <KatBadge slug={e.kategorie} />
              )}
              <h1 className="detail__titel d">{titel}</h1>
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
                    <b>
                      <time dateTime={e.datum_bis && e.datum_bis !== e.datum ? e.datum : `${e.datum}${e.uhrzeit ? `T${e.uhrzeit}` : ""}`}>{zeitText}</time>
                    </b>
                    <span>
                      {termine.length > 0
                        ? `${e.uhrzeit} Uhr · ${termine.length} Termine an diesem Tag`
                        : e.uhrzeit
                          ? `${e.uhrzeit} Uhr`
                          : "Uhrzeit siehe Veranstalter"}
                    </span>
                  </div>
                </div>
                <div className="infozeile">
                  <span className="infozeile__kachel">
                    <Icon name={online ? "videocam" : "location_on"} />
                  </span>
                  <div>
                    <b>{e.ort}</b>
                    <span>
                      {online ? "Online-Veranstaltung" : (e.adresse ?? "Düsseldorf")}
                      {!online && e.stadtteil ? " · " : ""}
                      {!online && e.stadtteil && (stadtteilPfad(e.stadtteil) ? <Link href={stadtteilPfad(e.stadtteil)!}>{stadtteilName(e.stadtteil)}</Link> : stadtteilName(e.stadtteil))}
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
              {e.reihe && (
                <Link className="link reihen-link" href={`/reihe/${encodeURIComponent(e.reihe.slug)}`}>
                  <Icon name="event_repeat" /> Alle Termine dieser Reihe <Icon name="arrow_forward" />
                </Link>
              )}
              {termine.length > 0 && (
                <div className="uhrzeit-wahl" role="group" aria-labelledby="uhrzeit-wahl-label">
                  <span className="uhrzeit-wahl__label" id="uhrzeit-wahl-label">Uhrzeit wählen</span>
                  <div className="uhrzeit-wahl__chips">
                    {termine.map((t) =>
                      t.id === e.id ? (
                        <span key={t.id} className="chip" aria-current="true">
                          {t.uhrzeit ?? "ohne Uhrzeit"}
                        </span>
                      ) : (
                        <Link
                          key={t.id}
                          href={eventPfad(t)}
                          className={`chip${t.abgesagt ? " chip--abgesagt" : ""}`}
                          aria-label={`${t.uhrzeit ?? "ohne Uhrzeit"} Uhr${t.abgesagt ? " (abgesagt)" : ""}`}
                          replace
                          scroll={false}
                        >
                          {t.uhrzeit ?? "ohne Uhrzeit"}
                        </Link>
                      ),
                    )}
                  </div>
                </div>
              )}
            </header>

            {!online && <GoogleKarte adresse={adresse} routeUrl={routenLink(adresse)} />}

            {e.beschreibung && (
              <section className="detail__abschnitt">
                <h2 className="d">Worum geht&apos;s</h2>
                <BeschreibungText text={e.beschreibung} />
              </section>
            )}
          </div>

          <aside className="detail-seite" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {e.quelle_url && !abgelaufen && (
              <a className="btn btn--gold btn--gross btn--block" href={e.quelle_url} target="_blank" rel="noopener">
                {eigenerTerminLink && e.uhrzeit ? `Zum Termin um ${e.uhrzeit} Uhr` : "Zur Veranstalter-Seite"}
                <Icon name="open_in_new" />
              </a>
            )}
            {/* Abgelaufen: kein Ticket-Button mehr, nur ein schlichter Verweis auf den Original-Eintrag */}
            {e.quelle_url && abgelaufen && (
              <a className="link" href={e.quelle_url} target="_blank" rel="noopener">
                Original-Eintrag beim Veranstalter <Icon name="open_in_new" />
              </a>
            )}
            <section className="detail__abschnitt">
              <h2 className="d" style={{ fontSize: 22 }}>
                Teilen
              </h2>
              <TeilenLeiste titel={titel} pfad={pfad} />
            </section>
            {e.quelle_name && <p className="quelle">Quelle: {e.quelle_name}</p>}
            {ortSuche && (
              <Link className="link" href={ortSuche}>
                Weitere Events an diesem Ort <Icon name="arrow_forward" />
              </Link>
            )}
            {e.stadtteil && (
              <Link className="link" href={stadtteilPfad(e.stadtteil) ?? `/entdecken?stadtteil=${encodeURIComponent(e.stadtteil)}&datum=woche`}>
                Mehr {inStadtteil(e.stadtteil)} <Icon name="arrow_forward" />
              </Link>
            )}
          </aside>
        </div>

        {empfehlungen.length > 0 && (
          <section className="container sektion" aria-labelledby="kommende-events">
            <div className="sektionskopf">
              <h2 className="d" id="kommende-events">Kommende Events</h2>
              <Link href="/entdecken">Alle</Link>
            </div>
            <Reihe breite={200} label="Kommende Events">
              {empfehlungen.map((x) => (
                <EventKarte key={x.id} e={x} heute={heute} variante="reihe" />
              ))}
            </Reihe>
          </section>
        )}

        {aehnliche.length > 0 && (
          <section className="container sektion">
            <div className="sektionskopf">
              <h2 className="d">Ähnliche Events</h2>
              <Link href={kategoriePfad(e.kategorie) ?? `/entdecken?kategorie=${e.kategorie}&datum=woche`}>Alle</Link>
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
