import type { Metadata } from "next";
import { BestaetigenSeite } from "@/components/konto-zugang";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

// Kein Referrer: Das Token steht im Fragment und wird sofort entfernt (Plan 5.2)
export const metadata: Metadata = { title: "Bestätigen", robots: KONTO_ROBOTS, referrer: "no-referrer" };

export default function Bestaetigen() {
  return (
    <KontoRahmen titel="Bestätigen">
      <BestaetigenSeite />
    </KontoRahmen>
  );
}
