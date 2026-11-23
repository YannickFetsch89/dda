// Admin-Bereich – Ort bearbeiten (Plan docs/plan-admin-dashboard-2026-11-23.md, 4.7, Stufe 3a).
import type { Metadata } from "next";
import { Suspense } from "react";
import { OrtBearbeiten } from "./bearbeiten";

export const metadata: Metadata = { title: "Ort bearbeiten" };

export default function AdminOrt() {
  return (
    <Suspense fallback={<p className="admin-unterzeile">Wird geladen …</p>}>
      <OrtBearbeiten />
    </Suspense>
  );
}
