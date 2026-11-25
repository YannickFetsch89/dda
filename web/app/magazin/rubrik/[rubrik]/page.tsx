// Magazin-Rubrik (Plan 5.1): wochenvorschau, monats-tipps, saison, stadtleben. Unbekannte Rubriken: 404 aus proxy.ts.
export const instant = false;
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { RubrikLinks } from "@/components/magazin";
import { FrischAusDerRedaktion } from "@/components/magazin-filter";
import { Icon } from "@/components/karten";
import { jsonLdText } from "@/lib/json-ld";
import { sammlungJsonLd } from "@/lib/magazin-json-ld";
import { karteDaten, RUBRIK_ICON } from "@/lib/magazin-uebersicht";
import { Leer } from "@/components/karten";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";
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
      {/* CollectionPage + ItemList + Brotkrumen wie auf der Übersicht (25.11.2026) */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: jsonLdText(
            sammlungJsonLd(
              SITE_URL,
              {
                pfad: rubrikPfad(rubrik),
                name: `${RUBRIK_NAME[rubrik]} – Magazin`,
                beschreibung: RUBRIK_TEXT[rubrik],
                krumen: [{ name: "Start", pfad: "/" }, { name: "Magazin", pfad: "/magazin" }, { name: RUBRIK_NAME[rubrik], pfad: rubrikPfad(rubrik) }],
              },
              beitraege,
            ),
          ),
        }}
      />
      <nav className="gd-krumen" aria-label="Brotkrumen">
        <Link href="/">Start</Link>
        <span>/</span>
        <Link href="/magazin">Magazin</Link>
        <span>/</span>
        <span aria-current="page">{RUBRIK_NAME[rubrik]}</span>
      </nav>
      <h1 className="d mz-rubrik-h1">
        <span className="mzt-kachel__icon"><Icon name={RUBRIK_ICON[rubrik]} /></span>
        {RUBRIK_NAME[rubrik]}
      </h1>
      <p className="mz-teaser">{RUBRIK_TEXT[rubrik]}</p>
      <RubrikLinks aktiv={rubrik} />
      {beitraege.length ? (
        <FrischAusDerRedaktion karten={beitraege.map(karteDaten)} pillen={[]} />
      ) : (
        <Leer titel="In dieser Rubrik gibt es noch keine Beiträge">
          <Link className="btn btn--gold" href="/magazin">Zum Magazin</Link>
        </Leer>
      )}
    </div>
  );
}
