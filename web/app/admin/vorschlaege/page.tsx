// Admin-Bereich – Vorschläge der Pipeline (Plan docs/plan-admin-dashboard-2026-11-23.md, 3.5, Stufe 1d).
import type { Metadata } from "next";
import { VorschlagListe } from "./liste";

export const metadata: Metadata = { title: "Vorschläge" };

export default function AdminVorschlaege() {
  return <VorschlagListe />;
}
