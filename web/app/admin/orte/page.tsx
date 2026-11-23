// Admin-Bereich – Orte (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.7, Stufe 3a).
import type { Metadata } from "next";
import { OrteListe } from "./liste";

export const metadata: Metadata = { title: "Orte" };

export default function AdminOrte() {
  return <OrteListe />;
}
