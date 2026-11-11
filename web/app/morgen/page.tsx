import type { Metadata } from "next";
import { seitenMetadaten } from "@/lib/seo";
import { Tagesplaner } from "@/components/tagesplaner";

// /morgen (SEO-/GEO-Plan, Phase B): dieselbe Vorlage wie /heute, um einen Tag verschoben, mit eigenem Canonical
export const metadata: Metadata = seitenMetadaten({
  pfad: "/morgen",
  titel: "Morgen in Düsseldorf",
  beschreibung: "Was morgen in Düsseldorf los ist: alle Events von morgens bis nachts.",
});

export default function Morgen() {
  return <Tagesplaner tageVoraus={1} pfad="/morgen" />;
}
