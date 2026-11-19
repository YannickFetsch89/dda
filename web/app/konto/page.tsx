// /konto – Übersicht „Mein dies.das“ (Plan Mein Bereich 3.1): Kacheln „Für mich“ und Links „Konto“.
import type { Metadata } from "next";
import { UebersichtSeite } from "@/components/mein-bereich";
import { KONTO_ROBOTS, KontoRahmen } from "./rahmen";

export const metadata: Metadata = { title: "Mein dies.das", robots: KONTO_ROBOTS };

export default function Konto() {
  return (
    <KontoRahmen titel="Mein dies.das" zurueck={false}>
      <UebersichtSeite />
    </KontoRahmen>
  );
}
