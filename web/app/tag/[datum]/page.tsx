import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { seitenMetadaten } from "@/lib/seo";
import { Tagesplaner } from "@/components/tagesplaner";
import { istGueltigerTag, tagLang } from "@/lib/datum";
import { eventPoolLaden, fernPoolLaden, istFern } from "@/lib/daten";
import { filtern } from "@/lib/ableitungen";

export async function generateMetadata(props: PageProps<"/tag/[datum]">): Promise<Metadata> {
  const { datum } = await props.params;
  if (!istGueltigerTag(datum)) return { title: "Tag nicht gefunden" };
  // Vergangene Tage: noindex (der Pool hat dafür keine Events; ein Archiv wird erst bewusst indexiert).
  // Tage hinter Tag 60: noindex, solange der Fernpool für den Tag keine Termine hat (Plan Quellen-Ausbau 6.1)
  const { heute } = await eventPoolLaden();
  // Dieselbe Auswahl wie die Tagesliste (components/tagesplaner.tsx): auch mehrtägige Termine an Folgetagen
  const fernOhneTermine = istFern(datum, heute) && filtern((await fernPoolLaden()).events, { von: datum, bis: datum }).length === 0;
  return seitenMetadaten({
    pfad: `/tag/${datum}`,
    titel: `Events am ${tagLang(datum)}`,
    beschreibung: `Alle Events in Düsseldorf am ${tagLang(datum)}.`,
    noindex: datum < heute || fernOhneTermine,
  });
}

// params oben lesen, ohne äußere Suspense-Grenze (Muster der Guide-Details): H1, Tages-Satz und Liste stehen im
// ersten HTML. Ungültige Tage beantwortet schon proxy.ts mit 404; notFound() bleibt als Rückfall.
export const instant = false;

export default async function Tag(props: PageProps<"/tag/[datum]">) {
  const { datum } = await props.params;
  if (!istGueltigerTag(datum)) notFound();
  return <Tagesplaner tag={datum} pfad={`/tag/${datum}`} />;
}
