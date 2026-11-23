// Admin-Bereich – Technik (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.10, Stufe 5a).
import type { Metadata } from "next";
import { TechnikAnsicht } from "./ansicht";

export const metadata: Metadata = { title: "Technik" };

export default function AdminTechnik() {
  return <TechnikAnsicht />;
}
