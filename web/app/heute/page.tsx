import type { Metadata } from "next";
import { Suspense } from "react";
import { Tagesplaner, TagesplanerSkeleton } from "@/components/tagesplaner";

export const metadata: Metadata = {
  title: "Heute in Düsseldorf",
  description: "Dein Tagesplaner: alle Events in Düsseldorf von morgens bis nachts.",
};

export default function Heute() {
  return (
    <Suspense fallback={<TagesplanerSkeleton />}>
      <Tagesplaner />
    </Suspense>
  );
}
