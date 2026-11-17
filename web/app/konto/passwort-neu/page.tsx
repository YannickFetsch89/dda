import type { Metadata } from "next";
import { PasswortNeuSeite } from "@/components/konto-zugang";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Neues Passwort", robots: KONTO_ROBOTS };

export default function PasswortNeu() {
  return (
    <KontoRahmen titel="Neues Passwort">
      <PasswortNeuSeite />
    </KontoRahmen>
  );
}
