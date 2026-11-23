// Admin-Bereich – Events (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.4, Stufe 1d).
import type { Metadata } from "next";
import { EventListe } from "./liste";

export const metadata: Metadata = { title: "Events" };

export default function AdminEvents() {
  return <EventListe />;
}
