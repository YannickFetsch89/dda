import type { Metadata } from "next";
import { PasswortVergessenSeite } from "@/components/konto-zugang";
import { KONTO_ROBOTS, KontoRahmen } from "../rahmen";

export const metadata: Metadata = { title: "Passwort vergessen", robots: KONTO_ROBOTS };

export default function PasswortVergessen() {
  return (
    <KontoRahmen titel="Passwort vergessen" unter="Wir schicken dir einen Link, mit dem du ein neues Passwort festlegst">
      <PasswortVergessenSeite />
    </KontoRahmen>
  );
}
