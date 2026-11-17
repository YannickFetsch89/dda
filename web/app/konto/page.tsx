import type { Metadata } from "next";
import { KontoSeite } from "@/components/konto-bereich";
import { KONTO_ROBOTS, KontoRahmen } from "./rahmen";

export const metadata: Metadata = { title: "Konto", robots: KONTO_ROBOTS };

export default function Konto() {
  return (
    <KontoRahmen titel="Konto">
      <KontoSeite />
    </KontoRahmen>
  );
}
