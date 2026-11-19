// /konto/willkommen – Alters-Häkchen (nur falls nötig), Interessen-Fragebogen und Abschlussseite (Plan 5.3, 8).
import type { Metadata } from "next";
import { WillkommenSeite } from "@/components/konto-bereich";
import { fragebogenDaten } from "../fragebogen-daten";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Willkommen", robots: KONTO_ROBOTS };

export default async function Willkommen() {
  return (
    <KontoRahmen titel="Willkommen">
      <WillkommenSeite daten={await fragebogenDaten()} />
    </KontoRahmen>
  );
}
