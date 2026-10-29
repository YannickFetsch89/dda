import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { Icon } from "@/components/karten";
import { GoogleKarte, ZurueckButton, TeilenButton, TeilenLeiste } from "@/components/client";

export const metadata: Metadata = {
  title: "Kegelnde Karpfen bei Juttas Forelle",
  description: "Kegeln in lockerer Runde mit maximalsportlichem Ehrgeiz – Altbier inklusive. Nur für autorisierte Karpfen.",
  robots: { index: false, follow: false },
  openGraph: {
    title: "Kegelnde Karpfen bei Juttas Forelle",
    description: "Kegeln in lockerer Runde – Altbier darf nicht fehlen. Champions-League-Saison in Vorbereitung.",
    images: ["/img/karpfen/querkant.jpg"],
  },
};

const PFAD = "/events/kegelnde-karpfen-bei-juttasforelle-202609-29";
const ADRESSE = "Juttas Forelle, Sonnenstraße 56, 40227 Düsseldorf";

function routenLink(adresse: string) {
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(adresse)}`;
}

export default function KegelndeKarpfenSeite() {
  return (
    <article>
      <div className="detail-hero">
        <div className="bild" style={{ position: "relative", minHeight: 400, overflow: "hidden" }}>
          <Image
            src="/img/karpfen/hochkant.jpg"
            alt="Kegelnde Karpfen auf der Bahn bei Juttas Forelle"
            fill
            priority
            style={{ objectFit: "cover" }}
          />
        </div>
        <div className="detail-hero__btns">
          <ZurueckButton />
          <div>
            <TeilenButton titel="Kegelnde Karpfen bei Juttas Forelle" pfad={PFAD} />
          </div>
        </div>
      </div>

      <div className="detail-sheet">
        <div className="container detail-raster">
          <div style={{ display: "flex", flexDirection: "column", gap: 28, minWidth: 0 }}>
            <header>
              <span className="badge" style={{ background: "#c9a84c", color: "#1b2540" }}>
                <Icon name="sports" />
                Kegeln
              </span>
              <h1 className="detail__titel d">Kegelnde Karpfen bei Juttas Forelle</h1>

              <div className="infozeilen">
                <div className="infozeile">
                  <span className="infozeile__kachel">
                    <Icon name="calendar_today" />
                  </span>
                  <div>
                    <b>Heute, 29. Oktober 2026</b>
                    <span>20:00 Uhr</span>
                  </div>
                </div>
                <div className="infozeile">
                  <span className="infozeile__kachel">
                    <Icon name="location_on" />
                  </span>
                  <div>
                    <b>Juttas Forelle</b>
                    <span>Sonnenstraße 56, 40227 Düsseldorf · Oberbilk</span>
                  </div>
                </div>
                <div className="infozeile">
                  <span className="infozeile__kachel">
                    <Icon name="confirmation_number" />
                  </span>
                  <div>
                    <b>Nur mit Einladung</b>
                    <span>Kein öffentlicher Eintritt</span>
                  </div>
                </div>
              </div>
            </header>

            <GoogleKarte adresse={ADRESSE} routeUrl={routenLink(ADRESSE)} />

            <section className="detail__abschnitt">
              <h2 className="d">Worum geht&apos;s</h2>
              <p>
                Die Kegelnden Karpfen laden zur lockeren Runde auf die Bahn – mit maximalem
                sportlichem Ehrgeiz und minimalem Talent. Das Ziel ist klar: kommende Saison
                Champions League. Ob die Gegner Kegel oder andere Mannschaften sind, wird noch
                geklärt. Fest steht: Altbier fließt, Sprüche klopfen und wer alle Neune trifft,
                darf den Rest des Abends als „El Capitán" angesprochen werden.
              </p>
              <div style={{ position: "relative", width: "100%", aspectRatio: "16/10", borderRadius: 12, overflow: "hidden", margin: "16px 0" }}>
                <Image
                  src="/img/karpfen/querkant.jpg"
                  alt="Die Kegelnden Karpfen in Aktion"
                  fill
                  style={{ objectFit: "cover" }}
                />
              </div>
              <p>
                Dresscode: Kegelhemd optional, Siegeswille Pflicht. Trainingslager findet an der
                Theke statt.
              </p>
            </section>

            <section className="detail__abschnitt" style={{
              background: "var(--ddd-gold-tint)",
              borderRadius: 12,
              padding: 20,
              border: "1px solid var(--ddd-gold)",
            }}>
              <h2 className="d" style={{ fontSize: 18, marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
                <Icon name="warning" />
                Wichtiger Hinweis
              </h2>
              <p style={{ margin: 0, lineHeight: 1.7 }}>
                Eintritt ist nur autorisierten Personen gestattet. Es besteht die Möglichkeit,
                geteert und gefedert zu werden, wenn man keine gültige Einladung vorweisen kann.
                Die Kegelnden Karpfen übernehmen keine Haftung für Feder-Rückstände in der Kleidung.
              </p>
            </section>
          </div>

          <aside className="detail-seite" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <section className="detail__abschnitt">
              <h2 className="d" style={{ fontSize: 22 }}>
                Teilen
              </h2>
              <TeilenLeiste titel="Kegelnde Karpfen bei Juttas Forelle" pfad={PFAD} />
            </section>
            <Link className="link" href="/entdecken?stadtteil=oberbilk&datum=woche">
              Mehr in Oberbilk <Icon name="arrow_forward" />
            </Link>
          </aside>
        </div>
      </div>
    </article>
  );
}
