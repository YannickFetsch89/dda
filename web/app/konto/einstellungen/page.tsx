// /konto/einstellungen – „Konto und Sicherheit“ (Plan Mein Bereich 3.7)
import type { Metadata } from "next";
import { EinstellungenSeite } from "@/components/konto-bereich";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Konto und Sicherheit", robots: KONTO_ROBOTS };

export default function Einstellungen() {
  return (
    <KontoRahmen titel="Konto und Sicherheit">
      <EinstellungenSeite />
    </KontoRahmen>
  );
}
