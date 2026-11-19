// /konto/datenschutz – Einwilligungen (b)–(d), Auskunft, Links (Plan Mein Bereich 3.8)
import type { Metadata } from "next";
import { DatenschutzSeite } from "@/components/konto-bereich";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Datenschutz", robots: KONTO_ROBOTS };

export default function Datenschutz() {
  return (
    <KontoRahmen titel="Datenschutz">
      <DatenschutzSeite />
    </KontoRahmen>
  );
}
