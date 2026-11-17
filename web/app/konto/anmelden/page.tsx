import type { Metadata } from "next";
import { AnmeldenSeite } from "@/components/konto-zugang";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Anmelden", robots: KONTO_ROBOTS };

export default function Anmelden() {
  return (
    <KontoRahmen titel="Anmelden" unter="Deine Merkliste auf allen Geräten – kostenlos, mit Mailadresse und Passwort">
      <AnmeldenSeite />
    </KontoRahmen>
  );
}
