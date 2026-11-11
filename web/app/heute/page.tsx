import type { Metadata } from "next";
import { Suspense } from "react";
import { seitenMetadaten } from "@/lib/seo";
import { Tagesplaner, TagesplanerSkeleton } from "@/components/tagesplaner";

export const metadata: Metadata = seitenMetadaten({
  pfad: "/heute",
  titel: "Heute in Düsseldorf",
  beschreibung: "Dein Tagesplaner: alle Events in Düsseldorf von morgens bis nachts.",
});

export default function Heute() {
  return (
    <Suspense fallback={<TagesplanerSkeleton />}>
      <Tagesplaner />
    </Suspense>
  );
}
