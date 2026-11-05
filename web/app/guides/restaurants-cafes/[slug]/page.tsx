// Guide-Detail Restaurant/Café (Design-Handoff v2, Ansichten 16 und 17)
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";
import { BildImg, Reihe } from "@/components/client";
import { EventKarte, Icon } from "@/components/karten";
import { OrtKartenGrid, typIcon, typLabel } from "@/components/ort-karten";
import { eventPoolLaden } from "@/lib/daten";
import { kueche, sortieren, sterne, zahl } from "@/lib/guide-filter";
import { slugify } from "@/lib/kueche";
import { ortBildAutorUrl, ortBildUrl, ortLaden, orteLaden, sichereUrl, slugDekodieren } from "@/lib/orte";
import type { DddOrt } from "@/lib/typen";

const BASIS = "/guides/restaurants-cafes";
type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata(props: Props): Promise<Metadata> {
  const slug = slugDekodieren((await props.params).slug);
  const ort = slug ? await ortLaden(slug) : null;
  if (!ort) return { title: "Nicht gefunden" };
  const bild = ortBildUrl(ort);
  return {
    title: `${ort.name} – ${typLabel(ort.typ)} in ${ort.stadtteil ?? "Düsseldorf"}`,
    description:
      ort.beschreibung ??
      `${ort.name}: ${typLabel(ort.typ)} in ${ort.stadtteil ?? "Düsseldorf"}${ort.google_rating ? `, ${sterne(ort.google_rating)} Sterne` : ""}. Empfohlen von dies.das.düsseldorf.`,
    alternates: { canonical: `${BASIS}/${encodeURIComponent(ort.slug)}` },
    openGraph: bild ? { images: [{ url: bild }] } : undefined,
  };
}

const PREIS_TEXT: Record<string, string> = { "€": "günstig", "€€": "mittleres Preisniveau", "€€€": "gehoben" };

const WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"];
const ZEITRAUM = /(\d{1,2}):(\d{2})\s*[–-]\s*(\d{1,2}):(\d{2})/g;

/**
 * Google-Öffnungszeiten ("Montag: 12:00–22:00 Uhr | Dienstag: …") → Zeilen, dazu die von heute (Berlin).
 * Reicht ein Zeitraum des Vortags über Mitternacht ("Freitag: 18:00–02:00") und ist es jetzt davor,
 * gilt das Lokal als noch geöffnet – sonst stünde samstags um 01:00 oft "Geschlossen" da.
 */
function oeffnungszeiten(text: string | null, jetzt: Date) {
  const tage = (text ?? "").split("|").map((z) => z.trim()).filter(Boolean).map((z) => {
    const i = z.indexOf(":");
    return i > 0 ? { tag: z.slice(0, i).trim(), zeit: z.slice(i + 1).trim() } : { tag: "", zeit: z };
  });
  const teile = Object.fromEntries(
    new Intl.DateTimeFormat("de-DE", { timeZone: "Europe/Berlin", weekday: "long", hour: "2-digit", minute: "2-digit", hourCycle: "h23" })
      .formatToParts(jetzt).map((p) => [p.type, p.value]),
  );
  const heuteName = teile.weekday;
  const minuten = Number(teile.hour) * 60 + Number(teile.minute);
  const vortag = WOCHENTAGE[(WOCHENTAGE.indexOf(heuteName) + 6) % 7];

  let nochBis: string | null = null;
  for (const m of (tage.find((t) => t.tag === vortag)?.zeit ?? "").matchAll(ZEITRAUM)) {
    const start = Number(m[1]) * 60 + Number(m[2]);
    const ende = Number(m[3]) * 60 + Number(m[4]);
    if (ende < start && minuten < ende) nochBis = `${m[3].padStart(2, "0")}:${m[4]}`;
  }
  return { heute: tage.find((t) => t.tag === heuteName)?.zeit ?? null, nochBis, tage };
}

function InfoZeile({ icon, l1, l2, children }: { icon: string; l1: React.ReactNode; l2?: React.ReactNode; children?: React.ReactNode }) {
  return (
    <div className="gd-info__zeile">
      <Icon name={icon} />
      <div>
        <span>{l1}</span>
        {l2 && <span className="muted">{l2}</span>}
        {children}
      </div>
    </div>
  );
}

/** Öffnungszeiten hängen vom heutigen Wochentag ab – daher erst zur Anfragezeit (eigene Suspense-Grenze). */
async function Oeffnungszeiten({ text }: { text: string }) {
  await connection();
  const oz = oeffnungszeiten(text, new Date());
  const heute = oz.heute ? `Heute: ${oz.heute}` : "Öffnungszeiten";
  return (
    <InfoZeile icon="schedule" l1={oz.nochBis ? `Noch geöffnet bis ${oz.nochBis} Uhr` : heute} l2={oz.nochBis ? heute : undefined}>
      <details className="gd-oz">
        <summary>Alle Öffnungszeiten</summary>
        <dl>
          {oz.tage.map((t) => (
            <div key={t.tag + t.zeit}><dt>{t.tag}</dt><dd>{t.zeit}</dd></div>
          ))}
        </dl>
      </details>
    </InfoZeile>
  );
}

function domain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

async function EventsInDerNaehe({ ort }: { ort: DddOrt }) {
  if (!ort.stadtteil) return null;
  const pool = await eventPoolLaden();
  const events = pool.events
    .filter((e) => e.stadtteil === ort.stadtteil && !e.abgesagt && (e.datum >= pool.heute || (e.datum_bis ?? "") >= pool.heute))
    .sort((a, b) => a.datum.localeCompare(b.datum) || (a.uhrzeit ?? "").localeCompare(b.uhrzeit ?? ""))
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

async function Aehnliche({ ort }: { ort: DddOrt }) {
  const k = kueche(ort)?.slug;
  // Eigener Typ zuerst (Imbiss-Seite → andere Imbisse), innerhalb bleibt die Empfohlen-Reihenfolge (stabile Sortierung)
  const eigenerTypZuerst = (o: DddOrt) => (o.typ === ort.typ ? 0 : 1);
  const alle = sortieren(await orteLaden(["restaurant", "imbiss", "cafe"]), "empfohlen")
    .filter((o) => o.id !== ort.id)
    .sort((a, b) => eigenerTypZuerst(a) - eigenerTypZuerst(b));
  // Erst gleiche Küche im selben Stadtteil, dann gleiche Küche, dann gleicher Stadtteil und Typ
  const passend = [
    ...alle.filter((o) => k && kueche(o)?.slug === k && o.stadtteil === ort.stadtteil),
    ...alle.filter((o) => k && kueche(o)?.slug === k),
    ...alle.filter((o) => o.stadtteil === ort.stadtteil && o.typ === ort.typ),
    ...alle.filter((o) => o.stadtteil === ort.stadtteil),
  ];
  const auswahl = [...new Map(passend.map((o) => [o.id, o])).values()].slice(0, 4);
  if (!auswahl.length) return null;
  return (
    <section className="gd-abschnitt">
      <div className="gd-abschnitt__kopf">
        <h2 className="d">Das könnte dir auch gefallen</h2>
        <Link href={ort.stadtteil ? `${BASIS}?stadtteil=${slugify(ort.stadtteil)}` : BASIS} className="link">
          {ort.stadtteil ? `Alle in ${ort.stadtteil}` : "Alle Restaurants"}
        </Link>
      </div>
      <OrtKartenGrid orte={auswahl} spalten={4} />
    </section>
  );
}

export default async function OrtDetail(props: Props) {
  const slug = slugDekodieren((await props.params).slug);
  const ort = slug ? await ortLaden(slug) : null;
  if (!ort || !["restaurant", "imbiss", "cafe"].includes(ort.typ)) notFound();

  const bild = ortBildUrl(ort);
  const autorUrl = ortBildAutorUrl(ort);
  const kuecheName = kueche(ort)?.name ?? (typeof ort.extras.kueche === "string" ? ort.extras.kueche : null);
  const highlightGericht = typeof ort.extras.highlight_gericht === "string" ? ort.extras.highlight_gericht : null;
  // Links aus der Datenbank nur als http(s) nach außen geben
  const webseite = sichereUrl(ort.webseite);
  const reservierung = sichereUrl(ort.extras.reservierung_url);
  const mapsUrl =
    sichereUrl(ort.extras.google_maps_url) ||
    (ort.latitude != null && ort.longitude != null
      ? `https://www.google.com/maps/search/?api=1&query=${ort.latitude},${ort.longitude}`
      : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${ort.name} ${ort.adresse ?? ""}`)}`);
  const [strasse, ...ortTeil] = (ort.adresse ?? "").split(", ");
  const typZeile = [typLabel(ort.typ), ort.preis_niveau, ort.stadtteil].filter(Boolean).join(" · ");
  const details = [
    kuecheName && { label: "Küche", wert: kuecheName },
    highlightGericht && { label: "Highlight-Gericht", wert: highlightGericht },
  ].filter(Boolean) as { label: string; wert: string }[];

  return (
    <div className="container gd-detail gd-seite">
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link><span>/</span>
        <Link href={BASIS}>Restaurants &amp; Cafés</Link><span>/</span>
        <span aria-current="page">{ort.name}</span>
      </nav>

      {bild && (
        <div className="gd-detail__hero">
          <BildImg src={bild} alt={ort.name} icon={typIcon(ort.typ)} eager />
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
          <span className="gd-typ gd-typ--gross"><Icon name={typIcon(ort.typ)} />{typZeile}</span>
          <h1 className="d">{ort.name}</h1>
          {ort.highlight && <blockquote className="gd-zitat">{ort.highlight}</blockquote>}
          {ort.beschreibung && <p className="gd-detail__text">{ort.beschreibung}</p>}
          {ort.tags.length > 0 && (
            <div className="gd-detail__tags">{ort.tags.map((t) => <span key={t} className="gd-tag gd-tag--gross">{t}</span>)}</div>
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
          {reservierung && (
            <a href={reservierung} target="_blank" rel="noopener" className="gd-knopf">
              <Icon name="event_available" />Tisch reservieren
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
        </aside>
      </div>

      <Suspense fallback={null}>
        <EventsInDerNaehe ort={ort} />
      </Suspense>
      <Suspense fallback={null}>
        <Aehnliche ort={ort} />
      </Suspense>
    </div>
  );
}
