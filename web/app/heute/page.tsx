import type { Metadata } from "next";
import { seitenMetadaten } from "@/lib/seo";
import { Tagesplaner } from "@/components/tagesplaner";

export const metadata: Metadata = seitenMetadaten({
  pfad: "/heute",
  titel: "Heute in Düsseldorf",
  beschreibung: "Dein Tagesplaner: alle Events in Düsseldorf von morgens bis nachts.",
});

// Ohne äußere Suspense-Grenze: H1, Tages-Satz und Liste stehen im ersten HTML (SEO-/GEO-Plan, Maßnahme 1)
export default function Heute() {
  return <Tagesplaner pfad="/heute" />;
}
