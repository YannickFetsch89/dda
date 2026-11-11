// /ueber – Entitäts-Dokument (SEO-/GEO-Plan Nov. 2026, Maßnahme 8): was die Seite ist, wie die Daten entstehen,
// wie Guides ausgewählt werden, wer verantwortlich ist. Zahlen live aus Pool und Guides, nicht geschätzt.
import type { Metadata } from "next";
import Link from "next/link";
import { JsonLd, Krumen } from "@/components/landing";
import { eventPoolLaden } from "@/lib/daten";
import { hubOrte } from "@/lib/guide-stadtteile";
import { brotkrumenJsonLd } from "@/lib/kneipen-json-ld";
import { MARKE_SATZ, seitenMetadaten } from "@/lib/seo";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

export const metadata: Metadata = seitenMetadaten({
  pfad: "/ueber",
  titel: "Über dies.das.düsseldorf",
  beschreibung: MARKE_SATZ,
});

const zahl = (n: number) => n.toLocaleString("de-DE");

export default async function Ueber() {
  const [pool, restaurants, kneipen, clubs] = await Promise.all([
    eventPoolLaden(),
    hubOrte("restaurants-cafes"),
    hubOrte("kneipen-bars"),
    hubOrte("clubs"),
  ]);
  // Quellen = verschiedene Datenquellen der aktuell geladenen Events (Veranstalter-Kalender, Portale, APIs)
  const quellen = new Set(pool.alle.map((e) => e.quelle_name).filter(Boolean)).size;
  const echt = pool.quelle === "supabase";
  const krumen = [{ name: "Start", pfad: "/" }, { name: "Über uns", pfad: "/ueber" }];

  return (
    <div className="container sektion rechtliches landing">
      <JsonLd daten={brotkrumenJsonLd(SITE_URL, krumen)} />
      <Krumen teile={krumen} />
      <h1 className="d">Über dies.das.düsseldorf</h1>
      <p className="landing__text">{MARKE_SATZ}</p>
      <p>
        Unter <b>diesdas.events</b> findest du, was heute, morgen und am Wochenende in Düsseldorf los ist – nach Tag, Kategorie und Stadtteil.
        Dazu kommen Guides zu Restaurants und Cafés, Kneipen und Bars sowie Clubs in Düsseldorf, Neuss und Ratingen.
      </p>

      <h2>Wie die Daten entstehen</h2>
      <p>
        Ein automatischer Lauf sammelt die Termine regelmäßig aus Veranstalter-Kalendern, Spielplänen, Veranstaltungsportalen und offenen
        Schnittstellen{echt ? <> – aktuell aus <b>{zahl(quellen)} Quellen</b> mit <b>{zahl(pool.alle.length)} Terminen</b> in den nächsten Wochen</> : ""}.
        Doppelte Einträge werden zusammengeführt, Kategorien und Kurzbeschreibungen mit KI vorbereitet. Jede Eventseite nennt ihre Quelle und
        verlinkt auf den Original-Eintrag beim Veranstalter; maßgeblich sind immer dessen Angaben.
      </p>
      <p>
        Fehlt ein Event? Über <Link href="/event-melden">Event melden</Link> kannst du es uns schicken.
      </p>

      <h2>Wie die Guides ausgewählt werden</h2>
      <p>
        In den Guides stehen nur Orte, die einen Qualitäts-Score aus Bewertungen, Beliebtheit und Angaben zum Ort erreichen
        {echt ? <> – derzeit {zahl(restaurants.length)} Restaurants und Cafés, {zahl(kneipen.length)} Kneipen und Bars und {zahl(clubs.length)} Clubs</> : ""}.
        Clubs prüfen wir zusätzlich von Hand, bevor sie erscheinen. Bezahlte Platzierungen gibt es nicht.
      </p>

      <h2>Wer dahintersteht</h2>
      <p>
        dies.das.düsseldorf wird von Rocktician e.&thinsp;K. in Düsseldorf betrieben. Alle Angaben zum Anbieter stehen im{" "}
        <Link href="/impressum">Impressum</Link>. Neues gibt es auch auf{" "}
        <a href="https://www.instagram.com/dies.das.duesseldorf/" target="_blank" rel="noopener">Instagram</a>.
      </p>
    </div>
  );
}
