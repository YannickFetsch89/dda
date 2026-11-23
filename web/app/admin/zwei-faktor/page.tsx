// Admin-Bereich – Zwei-Faktor-Code bzw. Einrichtung der Authenticator-App (Plan Admin-Dashboard 3.3, E2).
import type { Metadata } from "next";
import { ZweiFaktor } from "./zwei-faktor";

export const metadata: Metadata = { title: "Zwei-Faktor" };

export default function AdminZweiFaktor() {
  return (
    <div className="admin-anmeldung">
      <ZweiFaktor />
    </div>
  );
}
