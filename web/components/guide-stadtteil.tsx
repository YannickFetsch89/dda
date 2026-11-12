// Guide-Stadtteilseite (/guides/{hub}/stadtteil/{slug}) – SEO-/GEO-Plan Phase B, Maßnahme 5.
// „Restaurant Unterbilk“ landet sonst nur auf einem noindex-Filter. Listet die freigegebenen Orte des Hubs in diesem
// Stadtteil, jeden mit seiner einen Guide-URL. Keine Events (die stehen auf /stadtteil/{slug}).
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { JsonLd, Krumen, LinkChips } from "./landing";
import { Icon, Leer } from "./karten";
import { ClubKarte } from "./club-karte";
import { OrtKartenGrid } from "./ort-karten";
import { brotkrumenJsonLd } from "@/lib/kneipen-json-ld";
import { hubOrtPfad, hubOrte, orteImStadtteil, stadtteileImHub, zaehltFuerIndex } from "@/lib/guide-stadtteile";
import { clubsSortieren, nachStufen } from "@/lib/clubs";
import { STADTTEIL_TEXTE } from "@/lib/landing-texte";
import { GUIDE_HUBS, MIN_EINTRAEGE, inStadtteil, bezirkSatz, guideStadtteilPfad, stadtteilAusSlug, stadtteilPfad, type GuideHub } from "@/lib/landing";
import { seitenMetadaten } from "@/lib/seo";
import { stadtteilName } from "@/lib/stadtteile";
import type { DddOrt } from "@/lib/typen";

const SITE_URL = process.env.SITE_URL ?? "https://diesdas.events";

async function laden(hub: GuideHub, slug: string) {
  const st = stadtteilAusSlug(slug, true);
  if (!st) return null;
  const alle = await hubOrte(hub);
  const imStadtteil = orteImStadtteil(alle, st);
  // Club-Hub: Top-Empfehlungen zuerst (A, B, C), sonst die Reihenfolge des Hubs
  const orte = hub === "clubs" ? nachStufen(clubsSortieren(imStadtteil, "empfohlen")).flatMap((g) => g.orte) : imStadtteil;
  // Für Index-Schwelle und ItemList zählen im Club-Hub nur indexierbare Orte (Stufe A/B)
  return { st, alle, orte, indexOrte: orte.filter(zaehltFuerIndex(hub)) };
}

export async function guideStadtteilMetadaten(hub: GuideHub, slug: string): Promise<Metadata> {
  const d = await laden(hub, slug);
  if (!d) return { title: "Seite nicht gefunden" };
  const h = GUIDE_HUBS[hub];
  const imOrt = inStadtteil(d.st);
  return seitenMetadaten({
    pfad: guideStadtteilPfad(hub, d.st),
    titel: `${h.name} ${imOrt}`,
    beschreibung: `${d.orte.length} ausgewählte ${h.mehrzahl} ${imOrt}. ${STADTTEIL_TEXTE[d.st] ?? bezirkSatz(d.st)}`.slice(0, 300),
    noindex: d.indexOrte.length < MIN_EINTRAEGE,
  });
}

function ortListeJsonLd(hub: GuideHub, name: string, orte: DddOrt[]): Record<string, unknown> | null {
  if (!orte.length) return null;
  const liste = orte.slice(0, 30);
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name,
    numberOfItems: liste.length,
    itemListElement: liste.map((o, i) => ({ "@type": "ListItem", position: i + 1, url: `${SITE_URL}${hubOrtPfad(hub, o)}`, name: o.name })),
  };
}

export async function GuideStadtteil({ hub, slug }: { hub: GuideHub; slug: string }) {
  const d = await laden(hub, slug);
  if (!d) notFound();
  const { st, alle, orte, indexOrte } = d;
  const h = GUIDE_HUBS[hub];
  const name = stadtteilName(st);
  const imOrt = inStadtteil(st);
  const pfad = guideStadtteilPfad(hub, st);
  const hubPfad = `/guides/${hub}`;

  const krumen = [
    { name: "Start", pfad: "/" },
    { name: "Düsseldorf entdecken", pfad: "/guides" },
    { name: h.name, pfad: hubPfad },
    { name, pfad },
  ];
  const liste = ortListeJsonLd(hub, `${h.name} ${imOrt}`, indexOrte);
  const jsonLd = [brotkrumenJsonLd(SITE_URL, krumen), ...(liste ? [liste] : [])];

  const andere = stadtteileImHub(hub, alle)
    .filter((x) => x.stadtteil !== st)
    .map((x) => ({ name: stadtteilName(x.stadtteil), pfad: guideStadtteilPfad(hub, x.stadtteil), anzahl: x.anzahl }));
  const eventSeite = stadtteilPfad(st);
  const satz = orte.length === 1 ? `Im Guide steht ein Ort ${imOrt}.` : `Im Guide stehen ${orte.length} ${h.mehrzahl} ${imOrt}.`;

  return (
    <div className="container sektion landing">
      <JsonLd daten={jsonLd} />
      <Krumen teile={krumen} />
      <h1 className="d">
        {h.name} {imOrt}
      </h1>
      <p className="landing__text">{STADTTEIL_TEXTE[st] ?? bezirkSatz(st)}</p>
      <p className="tagesatz">{satz}</p>
      {orte.length ? (
        <div className="sektion">
          {hub === "clubs" ? (
            <div className="cl-grid" role="list">
              {orte.map((o) => <ClubKarte key={o.id} o={o} />)}
            </div>
          ) : (
            <OrtKartenGrid orte={orte} />
          )}
        </div>
      ) : (
        <div className="sektion">
          <Leer titel={`Noch keine ${h.mehrzahl} ${imOrt} im Guide.`}>
            <Link href={hubPfad} className="link">
              Alle {h.mehrzahl} <Icon name="arrow_forward" />
            </Link>
          </Leer>
        </div>
      )}
      <LinkChips titel={`${h.name} in anderen Stadtteilen`} links={andere} />
      <LinkChips
        titel="Mehr dazu"
        links={[
          { name: `Alle ${h.mehrzahl}`, pfad: hubPfad },
          ...(eventSeite ? [{ name: `Events ${imOrt}`, pfad: eventSeite }] : []),
        ]}
      />
    </div>
  );
}

/** Auf dem Hub: Links auf die Guide-Stadtteilseiten (nur Stadtteile ab fünf Orten – die indexierten). */
export function GuideStadtteilLinks({ hub, orte }: { hub: GuideHub; orte: DddOrt[] }) {
  const links = stadtteileImHub(hub, orte).map((x) => ({ name: stadtteilName(x.stadtteil), pfad: guideStadtteilPfad(hub, x.stadtteil), anzahl: x.anzahl }));
  if (!links.length) return null;
  return (
    <div className="container">
      <LinkChips titel={`${GUIDE_HUBS[hub].name} nach Stadtteil`} links={links} />
    </div>
  );
}
