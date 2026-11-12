// Reihe (wiederkehrendes Event): dauerhafte URL /reihe/<slug> mit dem nächsten und allen kommenden Terminen.
// Die Seite bleibt auch ohne kommende Termine erreichbar (HTTP 200) und verweist dann auf aktuelle Events.
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { EventKarte, Icon, KatBadge, Leer, ListenZeile } from "@/components/karten";
import { reiheLaden } from "@/lib/reihen";
import { jsonLdText } from "@/lib/json-ld";
import { reiheJsonLd } from "@/lib/listen-json-ld";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
import { tagKurz, tagLang } from "@/lib/datum";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const d = await reiheLaden(decodeURIComponent(slug));
  if (!d) return { title: "Reihe nicht gefunden" };
  const naechster = d.kommende[0];
  return {
    title: `${d.reihe.titel} – alle Termine`,
    description: naechster
      ? `Alle Termine von „${d.reihe.titel}“ (${d.reihe.ort}). Nächster Termin: ${tagLang(naechster.datum)}${naechster.uhrzeit ? `, ${naechster.uhrzeit} Uhr` : ""}.`
      : `Termine von „${d.reihe.titel}“ (${d.reihe.ort}) in Düsseldorf.`,
    alternates: { canonical: `/reihe/${d.reihe.slug}` },
  };
}

// Ohne äußere Suspense-Grenze (Muster der Guide-Details): Titel und Termine stehen im ersten HTML.
// Unbekannte Reihen beantwortet schon proxy.ts mit 404; notFound() bleibt als Rückfall.
export const instant = false;

export default function ReiheSeite(props: Props) {
  return <ReiheInhalt params={props.params} />;
}

async function ReiheInhalt({ params }: Props) {
  const { slug } = await params;
  const d = await reiheLaden(decodeURIComponent(slug));
  if (!d) notFound();
  const { reihe, kommende, letzter, heute } = d;
  const [naechster, ...weitere] = kommende;

  const jsonLd = reiheJsonLd(SITE_URL, reihe, kommende);

  return (
    <div className="container sektion reihe-seite">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(jsonLd) }} />
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link>
        <span>/</span>
        <Link href="/entdecken">Entdecken</Link>
        <span>/</span>
        <span aria-current="page">{reihe.titel}</span>
      </nav>
      {/* Kategorie des nächsten Termins (aktueller als die beim Anlegen der Reihe gespeicherte) */}
      <KatBadge slug={naechster?.kategorie ?? letzter?.kategorie ?? reihe.kategorie} />
      <h1 className="d">{reihe.titel}</h1>
      <p className="reihe__unterzeile">
        <Icon name="event_repeat" /> Wiederkehrendes Event · {reihe.ort}
        {kommende.length > 0 && ` · ${kommende.length} ${kommende.length === 1 ? "kommender Termin" : "kommende Termine"}`}
      </p>

      {naechster ? (
        <>
          <section className="reihe__abschnitt" aria-labelledby="reihe-naechster">
            <h2 className="d" id="reihe-naechster">Nächster Termin</h2>
            <div className="raster" role="list">
              <EventKarte e={naechster} heute={heute} variante="grid" />
            </div>
          </section>
          {weitere.length > 0 && (
            <section className="reihe__abschnitt" aria-labelledby="reihe-weitere">
              <h2 className="d" id="reihe-weitere">Weitere Termine</h2>
              <div className="reihe__termine">
                {weitere.map((e) => (
                  <ListenZeile key={e.id} e={e} zeit={tagKurz(e.datum)} />
                ))}
              </div>
            </section>
          )}
        </>
      ) : (
        <Leer titel="Gerade sind keine weiteren Termine bekannt">
          <p>
            {letzter ? `Der letzte Termin war am ${tagLang(letzter.datum)}. ` : ""}
            Sobald neue Termine angekündigt sind, findest du sie hier.
          </p>
          <Link className="btn btn--gold" href="/entdecken">
            Aktuelle Events in Düsseldorf entdecken
          </Link>
        </Leer>
      )}
    </div>
  );
}
