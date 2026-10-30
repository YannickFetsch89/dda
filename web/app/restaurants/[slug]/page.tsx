// Restaurant/Café Detailseite
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Icon } from "@/components/karten";
import { OrtKartenGrid, ortPfad } from "@/components/ort-karten";
import { ortLaden, orteLaden } from "@/lib/orte";
import type { DddOrt } from "@/lib/typen";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const ort = await ortLaden(decodeURIComponent(slug));
  if (!ort) return { title: "Nicht gefunden" };
  const typ = ort.typ === "cafe" ? "Café" : "Restaurant";
  return {
    title: `${ort.name} – ${typ} in ${ort.stadtteil ?? "Düsseldorf"}`,
    description: ort.beschreibung ?? `${ort.name} – ${typ} in Düsseldorf. Kuratierte Empfehlung von DiesDasDüsseldorf.`,
    openGraph: ort.bild_url ? { images: [{ url: ort.bild_url }] } : undefined,
  };
}

function InfoZeile({ icon, children }: { icon: string; children: React.ReactNode }) {
  return (
    <div className="ort-info__zeile">
      <Icon name={icon} />
      <span>{children}</span>
    </div>
  );
}

function Extras({ o }: { o: DddOrt }) {
  const e = o.extras ?? {};
  const zeilen: { label: string; wert: string }[] = [];
  if (e.kueche) zeilen.push({ label: "Küche", wert: String(e.kueche) });
  if (e.highlight_gericht) zeilen.push({ label: "Highlight-Gericht", wert: String(e.highlight_gericht) });
  if (e.terrasse === true) zeilen.push({ label: "Terrasse", wert: "Ja" });
  if (e.reservierung_url) zeilen.push({ label: "Reservierung", wert: String(e.reservierung_url) });
  if (!zeilen.length) return null;
  return (
    <div className="ort-extras">
      <h2>Details</h2>
      <dl className="ort-extras__liste">
        {zeilen.map(({ label, wert }) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{wert.startsWith("http") ? <a href={wert} target="_blank" rel="noopener">{wert}</a> : wert}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export default async function RestaurantDetail(props: Props) {
  const { slug } = await props.params;
  const ort = await ortLaden(decodeURIComponent(slug));
  if (!ort) notFound();

  const typ = ort.typ === "cafe" ? "Café" : "Restaurant";

  const alle = await orteLaden(["restaurant", "cafe"]);
  const aehnliche = alle
    .filter((o) => o.id !== ort.id && (o.stadtteil === ort.stadtteil || o.typ === ort.typ))
    .slice(0, 4);

  return (
    <div className="container">
      <nav className="breadcrumb" aria-label="Brotkrumen">
        <Link href="/">Start</Link>
        <span className="breadcrumb__sep">/</span>
        <Link href="/restaurants">Restaurants & Cafés</Link>
        <span className="breadcrumb__sep">/</span>
        <span>{ort.name}</span>
      </nav>

      <article className="ort-detail">
        {/* Hero-Bild */}
        {ort.bild_url && (
          <div className="ort-detail__hero">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={ort.bild_url} alt={ort.name} loading="eager" />
            {ort.bild_attribution && (
              <span className="ort-detail__attribution">Foto: {ort.bild_attribution}</span>
            )}
          </div>
        )}

        <div className="ort-detail__inhalt">
          <div className="ort-detail__haupt">
            <span className="ort-detail__typ">
              <Icon name={ort.typ === "cafe" ? "local_cafe" : "restaurant"} /> {typ}
              {ort.preis_niveau && <> · {ort.preis_niveau}</>}
              {ort.stadtteil && <> · {ort.stadtteil}</>}
            </span>

            <h1 className="d">{ort.name}</h1>

            {ort.highlight && <p className="ort-detail__highlight">{ort.highlight}</p>}

            {ort.beschreibung && (
              <div className="ort-detail__beschreibung">
                <p>{ort.beschreibung}</p>
              </div>
            )}

            {ort.tags.length > 0 && (
              <div className="ort-detail__tags">
                {ort.tags.map((t) => <span key={t} className="chip chip--klein">{t}</span>)}
              </div>
            )}

            <Extras o={ort} />
          </div>

          {/* Sidebar mit Infos */}
          <aside className="ort-detail__sidebar">
            <div className="ort-info">
              <h2>Infos</h2>
              {ort.adresse && <InfoZeile icon="location_on">{ort.adresse}</InfoZeile>}
              {ort.oeffnungszeiten && <InfoZeile icon="schedule">{ort.oeffnungszeiten}</InfoZeile>}
              {ort.telefon && <InfoZeile icon="phone">{ort.telefon}</InfoZeile>}
              {ort.google_rating != null && (
                <InfoZeile icon="star">
                  {ort.google_rating.toFixed(1)} / 5
                  {ort.google_bewertungen_anzahl != null && ` (${ort.google_bewertungen_anzahl} Bewertungen)`}
                </InfoZeile>
              )}
              {ort.preis_niveau && <InfoZeile icon="payments">{ort.preis_niveau}</InfoZeile>}
            </div>

            <div className="ort-info__links">
              {ort.webseite && (
                <a href={ort.webseite} target="_blank" rel="noopener" className="btn btn--navy">
                  <Icon name="language" /> Website
                </a>
              )}
              {ort.instagram && (
                <a href={`https://instagram.com/${ort.instagram.replace(/^@/, "")}`} target="_blank" rel="noopener" className="btn">
                  Instagram
                </a>
              )}
              {ort.latitude != null && ort.longitude != null && (
                <a href={`https://www.google.com/maps/search/?api=1&query=${ort.latitude},${ort.longitude}`} target="_blank" rel="noopener" className="btn">
                  <Icon name="map" /> Google Maps
                </a>
              )}
            </div>
          </aside>
        </div>
      </article>

      {/* Ähnliche Orte */}
      {aehnliche.length > 0 && (
        <section className="sektion">
          <h2 className="sektion__titel">Das könnte dir auch gefallen</h2>
          <OrtKartenGrid orte={aehnliche} />
        </section>
      )}
    </div>
  );
}
