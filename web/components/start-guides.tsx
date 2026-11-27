// Guide-Reihe auf der Startseite (Auftraggeber 27.11.2026): Events und Guides gleichwertig – direkt nach Tipp und
// Picks eine Reihe „Wohin in Düsseldorf?“ mit den fertigen Guides. Ohne Zahlen, damit die Startseite keine
// Guide-Daten laden muss; Bilder sind die Kachelbilder der Guide-Übersicht.
import Link from "next/link";
import { Reihe } from "./client";
import { Icon } from "./karten";
import { HUBS } from "@/lib/guide-hubs";

export function StartGuides() {
  const hubs = HUBS.filter((h) => h.fertig);
  if (hubs.length === 0) return null;
  return (
    <section className="sektion" aria-labelledby="start-guides-titel">
      <div className="sektionskopf sektionskopf--stapeln">
        <h2 className="d" id="start-guides-titel">Wohin in Düsseldorf?</h2>
        <Link href="/guides">Alle Guides</Link>
      </div>
      <Reihe breite={220} raster5 label="Guides">
        {hubs.map((h) => (
          <div key={h.slug} role="listitem" className="st-guide-li">
          <Link href={`/guides/${h.slug}`} className="st-guide">
            <span className="st-guide__bild">
              {/* eslint-disable-next-line @next/next/no-img-element -- statisches, bereits optimiertes WebP */}
              <img src={`/guides/${h.slug}.webp`} alt="" width={1400} height={768} loading="lazy" decoding="async" />
              <span className="st-guide__icon" aria-hidden><Icon name={h.icon} /></span>
            </span>
            <span className="st-guide__text">
              <b>{h.label}</b>
              <span>{h.teaser}</span>
            </span>
          </Link>
          </div>
        ))}
      </Reihe>
    </section>
  );
}
