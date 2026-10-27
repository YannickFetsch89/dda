// Wochenende-Special (Design-Ansicht 05)
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Bild, Icon, KatBadge, Leer, eventPfad } from "@/components/karten";
import { eventPoolLaden } from "@/lib/daten";
import { wochenendProgramm } from "@/lib/ableitungen";
import { kurzDatum, tagMonat } from "@/lib/datum";

export const metadata: Metadata = {
  title: "Unser Wochenend-Programm",
  description: "Neun Tipps für das Wochenende in Düsseldorf, drei pro Tag.",
};

export default function Wochenende(props: PageProps<"/wochenende">) {
  return (
    <Suspense
      fallback={
        <section className="wk-hero">
          <div className="container">
            <h1 className="d">Unser Wochenend-Programm</h1>
          </div>
        </section>
      }
    >
      <WochenendeInhalt searchParams={props.searchParams} />
    </Suspense>
  );
}

async function WochenendeInhalt({ searchParams }: Pick<PageProps<"/wochenende">, "searchParams">) {
  const sp = await searchParams;
  const pool = await eventPoolLaden();
  const tage = wochenendProgramm(pool);

  // Standard-Tab: heute, falls gerade Wochenende ist, sonst der erste noch kommende Tag
  const gewaehlt =
    tage.find((t) => t.kurz.toLowerCase() === String(sp.tag ?? "").toLowerCase()) ?? tage.find((t) => t.tag === pool.heute) ?? tage.find((t) => !t.vergangen) ?? tage[0];

  return (
    <>
      <section className="wk-hero">
        <div className="container">
          <span className="overline overline--gold">
            {tagMonat(tage[0].tag)} – {tagMonat(tage[2].tag)}
          </span>
          <h1 className="d">Unser Wochenend-Programm</h1>
          <p>Neun Tipps aus der Redaktion, drei pro Tag. Jeden Donnerstag neu.</p>
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
                    {e.uhrzeit} · {e.ort}
                  </span>
                </div>
                <Bild e={e} eager={i === 0}>
                  <KatBadge slug={e.kategorie} />
                </Bild>
                <h2 className="d">
                  <Link href={eventPfad(e)}>{e.titel}</Link>
                </h2>
                {e.beschreibung && <p>{e.beschreibung}</p>}
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
