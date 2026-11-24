// Admin-Bereich – Meldungen (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.10, Stufe 5b).
import type { Metadata } from "next";
import { MeldungenListe } from "./liste";

export const metadata: Metadata = { title: "Event-Meldungen" };

export default function AdminMeldungen() {
  return <MeldungenListe />;
}
