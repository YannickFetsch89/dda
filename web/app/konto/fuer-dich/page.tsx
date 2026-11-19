// /konto/fuer-dich – persönliche Vorschläge in vier Abschnitten (Plan Mein Bereich 3.3)
import type { Metadata } from "next";
import { FuerDichSeite } from "@/components/mein-bereich";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Für dich", robots: KONTO_ROBOTS };

export default function FuerDich() {
  return (
    <KontoRahmen titel="Für dich" breit>
      <FuerDichSeite />
    </KontoRahmen>
  );
}
