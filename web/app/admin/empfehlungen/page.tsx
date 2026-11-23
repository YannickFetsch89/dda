// Admin-Bereich – Empfehlungen (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.5, Stufe 1e).
import type { Metadata } from "next";
import { Suspense } from "react";
import { Empfehlungen } from "./empfehlungen";

export const metadata: Metadata = { title: "Empfehlungen" };

export default function AdminEmpfehlungen() {
  return (
    <Suspense fallback={<p className="admin-unterzeile">Wird geladen …</p>}>
      <Empfehlungen />
    </Suspense>
  );
}
