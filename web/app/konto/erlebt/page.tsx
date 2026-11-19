// /konto/erlebt – vergangene gemerkte Events, nach Monat (Plan Mein Bereich 3.5)
import type { Metadata } from "next";
import { ErlebtSeite } from "@/components/mein-bereich";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Erlebt", robots: KONTO_ROBOTS };

export default function Erlebt() {
  return (
    <KontoRahmen titel="Erlebt" breit>
      <ErlebtSeite />
    </KontoRahmen>
  );
}
