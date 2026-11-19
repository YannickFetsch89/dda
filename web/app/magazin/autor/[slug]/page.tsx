// Autorenseite eines redaktionellen Pseudonyms (Plan 2.3 Punkt 4). Offen gekennzeichnet: Pseudonym, KI-Werkzeuge,
// KI-generiertes Profilbild, verantwortliche Person. Unbekannte oder inaktive Autoren: 404 aus proxy.ts.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BeitragKarte } from "@/components/magazin";
import { jsonLdText } from "@/lib/json-ld";
import { autorPfad, pseudonymText, RUBRIK_NAME } from "@/lib/magazin";
import { autorenLaden, beitraegeLaden } from "@/lib/magazin-daten";
import { autorJsonLd } from "@/lib/magazin-json-ld";
import { MAGAZIN_VERLINKT } from "@/lib/schalter";
import { seitenMetadaten } from "@/lib/seo";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
type Props = { params: Promise<{ slug: string }> };

async function laden(props: Props) {
  const { slug } = await props.params;
  return (await autorenLaden()).find((a) => a.slug === slug) ?? null;
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const autor = await laden(props);
  if (!autor) return { title: "Nicht gefunden" };
  return seitenMetadaten({
    pfad: autorPfad(autor),
    titel: `${autor.name} – redaktionelles Pseudonym`,
    beschreibung: `${autor.name} schreibt im Magazin von dies.das.düsseldorf über ${autor.schwerpunkt}. Redaktionelles Pseudonym, Beiträge von der Redaktion geprüft.`,
    noindex: !MAGAZIN_VERLINKT,
  });
}

export default function AutorSeite(props: Props) {
  return <AutorInhalt params={props.params} />;
}

async function AutorInhalt({ params }: Props) {
  const autor = await laden({ params });
  if (!autor) notFound();
  const beitraege = (await beitraegeLaden()).filter((b) => b.autor_slug === autor.slug).slice(0, 30);
  return (
    <div className="container sektion mz-autorseite">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdText(autorJsonLd(SITE_URL, autorPfad(autor))) }} />
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link>
        <span>/</span>
        <Link href="/magazin">Magazin</Link>
        <span>/</span>
        <Link href="/magazin/redaktion">Unsere Redaktion</Link>
      </nav>
      <header className="mz-autorkopf">
        {autor.bild && (
          <figure className="mz-autorkopf__bild">
            {/* eslint-disable-next-line @next/next/no-img-element -- statisches Profilbild aus public/ */}
            <img src={autor.bild} alt={`Illustration zu ${autor.name}`} width={160} height={160} />
            {autor.bild_ki && <figcaption>KI-generiertes Profilbild</figcaption>}
          </figure>
        )}
        <div>
          <h1 className="d">{autor.name}</h1>
          <p className="mz-teaser">{autor.kurzbeschreibung}</p>
          <p className="mz-autorkopf__fach">
            Schwerpunkt: {autor.schwerpunkt}
            {autor.rubriken.length ? ` · Rubriken: ${autor.rubriken.map((r) => RUBRIK_NAME[r]).join(", ")}` : ""}
          </p>
        </div>
      </header>
      <aside className="mz-pseudonym" aria-label="Redaktionelles Pseudonym">
        <strong>Redaktionelles Pseudonym</strong>
        <p>{pseudonymText(autor.name)}</p>
        <p>
          <Link href="/magazin/redaktion">Unsere Redaktion</Link> · <Link href="/impressum">Impressum</Link>
        </p>
      </aside>
      <section className="sektion" aria-labelledby="mz-autor-beitraege">
        <h2 id="mz-autor-beitraege" className="d">Beiträge</h2>
        {beitraege.length ? (
          <div className="mz-liste" role="list">
            {beitraege.map((b) => <BeitragKarte key={b.id} b={b} />)}
          </div>
        ) : (
          <p>Noch keine Beiträge.</p>
        )}
      </section>
    </div>
  );
}
