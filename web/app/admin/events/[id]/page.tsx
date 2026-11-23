// Admin-Bereich – Event bearbeiten (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.4, Stufe 1d).
import type { Metadata } from "next";
import { Suspense } from "react";
import { EventBearbeiten } from "./bearbeiten";

export const metadata: Metadata = { title: "Event bearbeiten" };

export default function AdminEvent() {
  return (
    <Suspense fallback={<p className="admin-unterzeile">Wird geladen …</p>}>
      <EventBearbeiten />
    </Suspense>
  );
}
