// /konto/interessen – gespeicherte Interessen als Chips, Einwilligung (a) (Plan Mein Bereich 3.6)
import type { Metadata } from "next";
import { InteressenSeite } from "@/components/konto-bereich";
import { fragebogenDaten } from "../fragebogen-daten";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Interessen", robots: KONTO_ROBOTS };

export default async function Interessen() {
  return (
    <KontoRahmen titel="Interessen">
      <InteressenSeite daten={await fragebogenDaten()} />
    </KontoRahmen>
  );
}
