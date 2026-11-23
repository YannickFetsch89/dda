// Admin-Bereich – Anmelden (Plan Admin-Dashboard 3.3). Danach immer der Zwei-Faktor-Code.
import type { Metadata } from "next";
import { AnmeldeFormular } from "./formular";

export const metadata: Metadata = { title: "Anmelden" };

export default function AdminAnmelden() {
  return (
    <div className="admin-anmeldung">
      <AnmeldeFormular />
    </div>
  );
}
