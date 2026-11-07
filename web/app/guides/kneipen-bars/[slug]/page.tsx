// Guide-Detail Kneipe/Bar (Design-Handoff v2, Ansichten 20 und 21)
// Name, Beschreibung und Adresse stehen außerhalb jeder Suspense-Grenze (erste HTML-Antwort);
// nur Öffnungszeiten (Wochentag), Events und Ähnliche Kneipen werden nachgeladen.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { BildImg, Reihe } from "@/components/client";
import { EventKarte, Icon } from "@/components/karten";
import { KneipenKarte } from "@/components/kneipen-karte";
import { InfoZeile, Oeffnungszeiten, domain } from "@/components/ort-detail";
import { eventPoolLaden } from "@/lib/daten";
import { sortieren, sterne, zahl } from "@/lib/guide-filter";
import { RAUCHER_TEXT, artInfo, happyHour, raucher, spezialitaeten, vibes } from "@/lib/kneipen";
import { kneipenLaden } from "@/lib/kneipen-daten";
import { barOrPubJsonLd, brotkrumenJsonLd } from "@/lib/kneipen-json-ld";
import { jsonLdText } from "@/lib/json-ld";
import { slugify } from "@/lib/kueche";
import { ortBildAutorUrl, ortBildUrl, ortLaden, sichereUrl, slugDekodieren } from "@/lib/orte";
import type { DddOrt } from "@/lib/typen";

const BASIS = "/guides/kneipen-bars";
const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type Props = { params: Promise<{ slug: string }> };

const artName = (o: DddOrt) => artInfo(o).label;

export async function generateMetadata(props: Props): Promise<Metadata> {
  const slug = slugDekodieren((await props.params).slug);
  const ort = slug ? await ortLaden(slug) : null;
  if (!ort || ort.typ !== "kneipe") return { title: "Nicht gefunden" };
  const bild = ortBildUrl(ort);
  const titel = `${ort.name} – ${artName(ort)} in ${ort.stadtteil ?? "Düsseldorf"}`;
  const beschreibung =
    ort.beschreibung ??
    `${ort.name}: ${artName(ort)} in ${ort.stadtteil ?? "Düsseldorf"}${ort.google_rating ? `, ${sterne(ort.google_rating)} Sterne` : ""}. Empfohlen von dies.das.düsseldorf.`;
  const pfad = `${BASIS}/${encodeURIComponent(ort.slug)}`;
  return {
    title: titel,
    description: beschreibung,
    alternates: { canonical: pfad },
    openGraph: { title: titel, description: beschreibung, url: pfad, type: "website", siteName: "dies.das.düsseldorf", locale: "de_DE", ...(bild ? { images: [{ url: bild }] } : {}) },
    twitter: { card: bild ? "summary_large_image" : "summary", title: titel, description: beschreibung, ...(bild ? { images: [bild] } : {}) },
  };
}

const PREIS_TEXT: Record<string, string> = { "€": "günstig", "€€": "mittleres Preisniveau", "€€€": "gehoben" };
// Events in der Nähe: Nightlife und Musik zuerst (Events haben keine Koordinaten → gleicher Stadtteil)
const BEVORZUGT = new Set(["nightlife", "musik"]);

async function EventsInDerNaehe({ ort }: { ort: DddOrt }) {
  if (!ort.stadtteil) return null;
  const pool = await eventPoolLaden();
  const events = pool.events
    .filter((e) => e.stadtteil === ort.stadtteil && !e.abgesagt && (e.datum >= pool.heute || (e.datum_bis ?? "") >= pool.heute))
    .sort((a, b) =>
      Number(!BEVORZUGT.has(a.kategorie)) - Number(!BEVORZUGT.has(b.kategorie)) ||
      a.datum.localeCompare(b.datum) || (a.uhrzeit ?? "").localeCompare(b.uhrzeit ?? ""))
    .slice(0, 12);
  if (!events.length) return null;
  return (
    <section className="gd-abschnitt">
      <div className="gd-abschnitt__kopf">
        <h2 className="d">Events in der Nähe</h2>
        <Link href={`/entdecken?stadtteil=${encodeURIComponent(ort.stadtteil)}`} className="link">Alle in {ort.stadtteil}</Link>
      </div>
      <Reihe breite={258} label={`Events in ${ort.stadtteil}`}>
        {events.map((e) => <EventKarte key={e.id} e={e} heute={pool.heute} variante="reihe" />)}
      </Reihe>
    </section>
  );
}

async function AehnlicheKneipen({ ort }: { ort: DddOrt }) {
  const eigene = new Set(spezialitaeten(ort));
  const alle = sortieren(await kneipenLaden(), "empfohlen").filter((o) => o.id !== ort.id);
  // Erst gleiche Spezialität im selben Stadtteil, dann gleicher Stadtteil, dann gleiche Spezialität
  const passt = (o: DddOrt) => spezialitaeten(o).some((s) => eigene.has(s));
  const auswahl = [
    ...new Map(
      [
        ...alle.filter((o) => o.stadtteil === ort.stadtteil && passt(o)),
        ...alle.filter((o) => o.stadtteil === ort.stadtteil),
        ...alle.filter(passt),
      ].map((o) => [o.id, o]),
    ).values(),
  ].slice(0, 4);
  if (!auswahl.length) return null;
  return (
    <section className="gd-abschnitt">
      <div className="gd-abschnitt__kopf">
        <h2 className="d">Ähnliche Kneipen</h2>
        <Link href={BASIS} className="link">Alle Kneipen &amp; Bars</Link>
      </div>
      <div className="gd-grid gd-grid--4 gd-grid--abend" role="list">
        {auswahl.map((o) => <KneipenKarte key={o.id} o={o} />)}
      </div>
    </section>
  );
}

export default async function KneipeDetail(props: Props) {
  const slug = slugDekodieren((await props.params).slug);
  const ort = slug ? await ortLaden(slug) : null;
  // Eine URL pro Ort: Restaurants (auch Brauhäuser mit auch_kneipe) bleiben unter /guides/restaurants-cafes
  if (!ort || ort.typ !== "kneipe") notFound();

  const bild = ortBildUrl(ort);
  const autorUrl = ortBildAutorUrl(ort);
  const webseite = sichereUrl(ort.webseite);
  const mapsUrl =
    sichereUrl(ort.extras.google_maps_url) ||
    (ort.latitude != null && ort.longitude != null
      ? `https://www.google.com/maps/search/?api=1&query=${ort.latitude},${ort.longitude}`
      : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${ort.name} ${ort.adresse ?? ""}`)}`);
  const [strasse, ...ortTeil] = (ort.adresse ?? "").split(", ");
  const spez = spezialitaeten(ort);
  const vibe = vibes(ort);
  const hh = happyHour(ort);
  const rauch = raucher(ort);
  const typZeile = [artName(ort), ort.stadtteil].filter(Boolean).join(" · ");
  const details = [
    spez.length > 0 && { label: "Spezialität", wert: spez.join(", ") },
    vibe.length > 0 && { label: "Atmosphäre", wert: vibe.join(", ") },
  ].filter(Boolean) as { label: string; wert: string }[];
  const pfad = `${BASIS}/${encodeURIComponent(ort.slug)}`;
  const jsonLd = [
    barOrPubJsonLd(ort, SITE_URL),
    brotkrumenJsonLd(SITE_URL, [
      { name: "Start", pfad: "/" },
      { name: "Kneipen & Bars", pfad: BASIS },
      { name: ort.name, pfad },
    ]),
  ];

  return (
    <div className="container gd-detail gd-seite gd-seite--abend">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link><span>/</span>
        <Link href={BASIS}>Kneipen &amp; Bars</Link><span>/</span>
        <span aria-current="page">{ort.name}</span>
      </nav>

      {bild && (
        <div className="gd-detail__hero">
          <BildImg src={bild} alt={`${ort.name}, ${artName(ort)} in ${ort.stadtteil ?? "Düsseldorf"}`} icon={artInfo(ort).icon} eager />
          {ort.bild_attribution && (
            <span className="gd-detail__credit">
              Foto:{" "}
              {autorUrl ? <a href={autorUrl} target="_blank" rel="noopener noreferrer">{ort.bild_attribution}</a> : ort.bild_attribution}
            </span>
          )}
        </div>
      )}

      <div className="gd-detail__spalten">
        <div className="gd-detail__haupt">
          <span className="gd-typ gd-typ--gross gd-typ--abend"><Icon name={artInfo(ort).icon} />{typZeile}</span>
          <h1 className="d">{ort.name}</h1>
          {ort.highlight && <blockquote className="gd-zitat">{ort.highlight}</blockquote>}
          {ort.beschreibung && <p className="gd-detail__text">{ort.beschreibung}</p>}
          {vibe.length > 0 && (
            <div className="gd-detail__tags">{vibe.map((t) => <span key={t} className="gd-tag gd-tag--gross">{t}</span>)}</div>
          )}
          {details.length > 0 && (
            <div className="gd-details">
              <h2 className="d">Details</h2>
              {details.map((d) => (
                <div key={d.label} className="gd-details__zeile"><span className="muted">{d.label}</span><b>{d.wert}</b></div>
              ))}
            </div>
          )}
        </div>

        <aside className="gd-detail__seite">
          <div className="gd-info">
            <h2>Infos</h2>
            {ort.adresse && <InfoZeile icon="location_on" l1={strasse} l2={ortTeil.join(", ") || undefined} />}
            {ort.oeffnungszeiten && (
              <Suspense fallback={<InfoZeile icon="schedule" l1="Öffnungszeiten" />}>
                <Oeffnungszeiten text={ort.oeffnungszeiten} />
              </Suspense>
            )}
            {ort.telefon && <InfoZeile icon="phone" l1={<a href={`tel:${ort.telefon.replace(/[^\d+]/g, "")}`}>{ort.telefon}</a>} />}
            {spez.length > 0 && <InfoZeile icon="sports_bar" l1={spez.join(" · ")} l2="Spezialität" />}
            {hh && <InfoZeile icon="schedule" l1={`Happy Hour ${hh}`} l2="laut Gästebewertungen" />}
            {rauch && <InfoZeile icon="smoking_rooms" l1={RAUCHER_TEXT[rauch]} l2="laut Gästebewertungen" />}
            {ort.google_rating != null && (
              <InfoZeile
                icon="star"
                l1={`${sterne(ort.google_rating)} von 5`}
                l2={ort.google_bewertungen_anzahl != null ? `${zahl(ort.google_bewertungen_anzahl)} Google-Bewertungen` : undefined}
              />
            )}
            {ort.preis_niveau && <InfoZeile icon="payments" l1={ort.preis_niveau} l2={PREIS_TEXT[ort.preis_niveau]} />}
          </div>
          {webseite && (
            <a href={webseite} target="_blank" rel="noopener" className="gd-knopf gd-knopf--navy">
              <Icon name="language" />Website<span className="gd-knopf__zusatz">{domain(webseite)}</span>
            </a>
          )}
          {ort.instagram && (
            <a href={`https://instagram.com/${encodeURIComponent(ort.instagram.replace(/^@/, ""))}`} target="_blank" rel="noopener" className="gd-knopf">
              <Icon name="photo_camera" />Instagram<span className="gd-knopf__zusatz muted">@{ort.instagram.replace(/^@/, "")}</span>
            </a>
          )}
          <a href={mapsUrl} target="_blank" rel="noopener noreferrer" className="gd-knopf">
            <Icon name="map" />Google Maps
          </a>
          {ort.stadtteil && (
            <Link href={`${BASIS}?stadtteil=${slugify(ort.stadtteil)}`} className="link">Mehr Kneipen &amp; Bars in {ort.stadtteil}</Link>
          )}
        </aside>
      </div>

      <Suspense fallback={null}>
        <EventsInDerNaehe ort={ort} />
      </Suspense>
      <Suspense fallback={null}>
        <AehnlicheKneipen ort={ort} />
      </Suspense>
    </div>
  );
}
