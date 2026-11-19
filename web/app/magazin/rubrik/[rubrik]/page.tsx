// Magazin-Rubrik (Plan 5.1): wochenvorschau, monats-tipps, saison, stadtleben. Unbekannte Rubriken: 404 aus proxy.ts.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BeitragKarte, RubrikLinks } from "@/components/magazin";
import { Leer } from "@/components/karten";
import { istRubrik, RUBRIK_NAME, RUBRIK_TEXT, rubrikPfad } from "@/lib/magazin";
import { beitraegeLaden } from "@/lib/magazin-daten";
import { MAGAZIN_VERLINKT } from "@/lib/schalter";
import { seitenMetadaten } from "@/lib/seo";

type Props = { params: Promise<{ rubrik: string }> };

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { rubrik } = await props.params;
  if (!istRubrik(rubrik)) return { title: "Nicht gefunden" };
  return seitenMetadaten({
    pfad: rubrikPfad(rubrik),
    titel: `${RUBRIK_NAME[rubrik]} – Magazin`,
    beschreibung: RUBRIK_TEXT[rubrik],
    noindex: !MAGAZIN_VERLINKT,
  });
}

export default function RubrikSeite(props: Props) {
  return <RubrikInhalt params={props.params} />;
}

async function RubrikInhalt({ params }: Props) {
  const { rubrik } = await params;
  if (!istRubrik(rubrik)) notFound();
  const beitraege = (await beitraegeLaden()).filter((b) => b.rubrik === rubrik).slice(0, 30);
  return (
    <div className="container sektion mz-uebersicht">
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link>
        <span>/</span>
        <Link href="/magazin">Magazin</Link>
        <span>/</span>
        <span aria-current="page">{RUBRIK_NAME[rubrik]}</span>
      </nav>
      <h1 className="d">{RUBRIK_NAME[rubrik]}</h1>
      <p className="mz-teaser">{RUBRIK_TEXT[rubrik]}</p>
      <RubrikLinks aktiv={rubrik} />
      {beitraege.length ? (
        <div className="mz-liste" role="list">
          {beitraege.map((b) => <BeitragKarte key={b.id} b={b} />)}
        </div>
      ) : (
        <Leer titel="In dieser Rubrik gibt es noch keine Beiträge">
          <Link className="btn btn--gold" href="/magazin">Zum Magazin</Link>
        </Leer>
      )}
    </div>
  );
}
