// Admin-Bereich – Cockpit (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.2, Stufe 1b).
import type { Metadata } from "next";
import { Cockpit } from "./cockpit";

export const metadata: Metadata = { title: "Cockpit" };

export default function AdminCockpit() {
  return <Cockpit />;
}
