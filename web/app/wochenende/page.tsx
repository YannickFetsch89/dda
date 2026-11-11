// Wochenende-Special (Design-Ansicht 05)
import type { Metadata } from "next";
import { hatParameter, seitenMetadaten } from "@/lib/seo";
import Link from "next/link";
import { Suspense } from "react";
import { Bild, Icon, KatBadge, Leer, eventPfad } from "@/components/karten";
import { eventPoolLaden } from "@/lib/daten";
import { filtern, wochenendProgramm } from "@/lib/ableitungen";
import { jsonLdText } from "@/lib/json-ld";
import { eventListeJsonLd } from "@/lib/listen-json-ld";
import { wochenendSatz } from "@/lib/tagestext";
import type { EventPool } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
import { kurzDatum, tagMonat, zeitraumAuflösen } from "@/lib/datum";
import { zeitKurz } from "@/lib/termine";
import { kurzBeschreibung } from "@/lib/beschreibung";

export async function generateMetadata(props: PageProps<"/wochenende">): Promise<Metadata> {
  return seitenMetadaten({
    pfad: "/wochenende",
    titel: "Unser Wochenend-Programm",
    beschreibung: "Neun Tipps für das Wochenende in Düsseldorf, drei pro Tag.",
    noindex: hatParameter(await props.searchParams),
  });
}

// Standardansicht (ohne ?tag=) im ersten HTML – Daten aus dem Cache. Nur die Tab-Variante wartet in Suspense auf
// searchParams; ihr Fallback ist genau diese Standardansicht (Muster der Guide-Hubs, SEO-/GEO-Plan Maßnahme 1).
export default async function Wochenende(props: PageProps<"/wochenende">) {
  const pool = await eventPoolLaden();
  return (
    <Suspense fallback={<WochenendeAnsicht pool={pool} />}>
      <MitTab searchParams={props.searchParams} pool={pool} />
    </Suspense>
  );
}

async function MitTab({ searchParams, pool }: Pick<PageProps<"/wochenende">, "searchParams"> & { pool: EventPool }) {
  const sp = await searchParams;
  return <WochenendeAnsicht pool={pool} tagWahl={typeof sp.tag === "string" ? sp.tag : undefined} />;
}

function WochenendeAnsicht({ pool, tagWahl }: { pool: EventPool; tagWahl?: string }) {
  const tage = wochenendProgramm(pool);

  // Standard-Tab: heute, falls gerade Wochenende ist, sonst der erste noch kommende Tag
  const gewaehlt =
    tage.find((t) => t.kurz.toLowerCase() === String(tagWahl ?? "").toLowerCase()) ?? tage.find((t) => t.tag === pool.heute) ?? tage.find((t) => !t.vergangen) ?? tage[0];
  // Satz aus echten Daten – dieselbe Menge wie der Link „Alle Events am Wochenende“ (/entdecken?datum=wochenende:
  // ab Samstag erst ab heute, Langläufer dabei). Nicht bei Beispieldaten (Ausfall der Datenbank).
  const z = zeitraumAuflösen("wochenende", pool.heute);
  const alleAmWochenende = filtern(pool.events, { von: z.von, bis: z.bis, mitLanglaeufern: true });
  const tipps = tage.filter((t) => !t.vergangen).reduce((n, t) => n + t.events.length, 0);
  const satz = pool.quelle === "supabase" ? wochenendSatz(z.von, z.bis, alleAmWochenende, tipps) : null;
  const jsonLd = eventListeJsonLd(
    SITE_URL,
    `Wochenend-Tipps für ${gewaehlt.name}`,
    [{ name: "Start", pfad: "/" }, { name: "Wochenende", pfad: "/wochenende" }],
    gewaehlt.events,
  );

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <section className="wk-hero">
        <div className="container">
          <span className="overline overline--gold">
            {tagMonat(tage[0].tag)} – {tagMonat(tage[2].tag)}
          </span>
          <h1 className="d">Unser Wochenend-Programm</h1>
          <p>{satz ? `${satz} ` : ""}Jeden Donnerstag neu.</p>
          <nav className="wk-tabs" aria-label="Tag wählen">
            {tage.map((t) => (
              <Link key={t.kurz} href={`/wochenende?tag=${t.kurz.toLowerCase()}`} aria-current={t.kurz === gewaehlt.kurz ? "true" : undefined} scroll={false}>
                {t.name}
                <small>{kurzDatum(t.tag)}</small>
              </Link>
            ))}
          </nav>
        </div>
      </section>

      <div className="container">
        {gewaehlt.events.length ? (
          <div className="wk-liste">
            {gewaehlt.events.map((e, i) => (
              <article key={e.id} className="wk-eintrag">
                <div className="wk-eintrag__kopf">
                  <span className="wk-eintrag__nr">{String(i + 1).padStart(2, "0")}</span>
                  <span>
                    {zeitKurz(e)} · {e.ort}
                  </span>
                </div>
                <Bild e={e} eager={i === 0}>
                  <KatBadge slug={e.kategorie} />
                </Bild>
                <h2 className="d">
                  <Link href={eventPfad(e)}>{e.titel}</Link>
                </h2>
                {e.beschreibung && <p>{kurzBeschreibung(e.beschreibung, 220)}</p>}
                <div className="wk-eintrag__fuss">
                  <span className="preis">{e.preis}</span>
                  <Link href={eventPfad(e)} className="link">
                    Details <Icon name="arrow_forward" />
                  </Link>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="sektion">
            <Leer titel={gewaehlt.vergangen ? "Dieser Tag ist schon vorbei." : "Für diesen Tag gibt es noch keine Tipps."}>
              <Link href={`/entdecken?datum=wochenende`} className="link">
                Alle Events am Wochenende <Icon name="arrow_forward" />
              </Link>
            </Leer>
          </div>
        )}
        <div className="mehr-laden">
          <Link href="/entdecken?datum=wochenende" className="btn btn--outline btn--gross">
            Alle Events am Wochenende
          </Link>
        </div>
      </div>
    </>
  );
}
