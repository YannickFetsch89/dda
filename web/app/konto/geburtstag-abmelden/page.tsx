// /konto/geburtstag-abmelden#t=<Token> – Geburtstagsmail abbestellen (Plan Geburtstagsmail G4, Kontenplan 13a).
// Statische Hülle (noindex), das Token liest erst der Browser aus dem Fragment; es geht nie an den Server, bevor
// jemand auf den Button klickt.
import type { Metadata } from "next";
import { GeburtstagAbmelden } from "@/components/geburtstag-abmelden";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Geburtstagsmail abbestellen", robots: KONTO_ROBOTS };

export default function GeburtstagAbmeldenSeite() {
  return (
    <KontoRahmen titel="Geburtstagsmail" zurueck={false}>
      <GeburtstagAbmelden />
    </KontoRahmen>
  );
}
